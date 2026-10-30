"""Main FastAPI REST API application for Anupalan compliance navigator.

Implements /v1/ask, /v1/instruments/{id}, /v1/chunks/{id}, /v1/feedback,
/v1/health, /v1/sessions/{session_id}, /v1/telemetry/purge, and /metrics.
"""

import json
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from packages.generation.src.generation.abstention_engine import AbstentionEngine
from packages.generation.src.generation.generator import ComplianceGenerator
from packages.generation.src.generation.numeric_guard import NumericGuardrail
from packages.generation.src.generation.schemas import (
    AskRequest,
    AskResponse,
    Citation,
    Claim,
    FeedbackRequest,
)
from packages.generation.src.generation.verifier import CitationVerifier
from pydantic import BaseModel, Field
from packages.query.src.query.cache import ComplianceQueryCache
from packages.query.src.query.language_detector import IndicLanguageDetector
from packages.query.src.query.transliteration_normalizer import TransliterationNormalizer
from packages.retrieval.src.retrieval.hybrid_retriever import HybridRetriever
from services.api.src.metrics import PrometheusMetricsCollector
from services.api.src.telemetry import AuditLogStore, PIIScrubber
from services.ingestion.src.chunker import StatutoryChunk, StructureAwareChunker
from services.ingestion.src.version_graph import (
    InstrumentNode,
    LegalVersionGraph,
    RelationEdge,
)

app = FastAPI(
    title="Anupalan Compliance API",
    version="0.1.0",
    description="Multilingual, Citation-Grounded Compliance Navigator for Indian MSMEs",
)

# In-memory stores and state
CHUNKS_DB: dict[UUID, StatutoryChunk] = {}
INSTRUMENTS_DB: dict[str, dict[str, Any]] = {}
FEEDBACK_DB: list[dict[str, Any]] = []
VERSION_GRAPH = LegalVersionGraph()
CORPUS_LAST_UPDATED = date(2026, 10, 26)

# Operational telemetry, metrics, and query caching
audit_store = AuditLogStore(ttl_days=30)
metrics_collector = PrometheusMetricsCollector()
query_cache = ComplianceQueryCache(max_size=10000, ttl_seconds=3600)


class AdminTakedownRequest(BaseModel):
    answer_id: UUID
    reason: str
    admin_user: str = "compliance_lead"

# Core NLP, Retrieval, and Generation engines
language_detector = IndicLanguageDetector()
normalizer = TransliterationNormalizer()
chunker = StructureAwareChunker()
abstention_engine = AbstentionEngine()
verifier = CitationVerifier()
numeric_guard = NumericGuardrail()
generator = ComplianceGenerator()


def load_core_instruments(filepath: Path | None = None) -> int:
    """Pre-populates instruments and amendment relationships from the static fixture."""
    if filepath is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        filepath = base_dir / "data" / "fixtures" / "core_instruments.json"

    if not filepath.exists():
        return 0

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            instruments = json.load(f)
    except Exception:
        return 0

    count = 0
    # First pass: register all instrument nodes
    for item in instruments:
        code = item["code"]
        inst_id = uuid5(NAMESPACE_DNS, code)
        issued_on = date.fromisoformat(item["issued_on"])
        effective_from = date.fromisoformat(item["effective_from"])
        effective_to = (
            date.fromisoformat(item["effective_to"])
            if item.get("effective_to")
            else None
        )

        node = InstrumentNode(
            id=inst_id,
            code=code,
            number=item.get("number", code),
            title=item.get("title", code),
            issued_on=issued_on,
            effective_from=effective_from,
            effective_to=effective_to,
            jurisdiction=item.get("jurisdiction", "central"),
        )
        VERSION_GRAPH.add_instrument(node)

        record = {
            "id": str(inst_id),
            "code": code,
            "authority": item.get("authority", "CBIC"),
            "type": item.get("type", "notification"),
            "number": item.get("number", code),
            "title": item.get("title", code),
            "jurisdiction": item.get("jurisdiction", "central"),
            "issued_on": item["issued_on"],
            "effective_from": item["effective_from"],
            "effective_to": item.get("effective_to"),
            "source_url": item.get("source_url"),
            "language": item.get("language", ["en"]),
            "subjects": item.get("subjects", []),
        }
        INSTRUMENTS_DB[code] = record
        INSTRUMENTS_DB[str(inst_id)] = record
        count += 1

    # Second pass: register relations
    for item in instruments:
        relation = item.get("relation")
        if relation and relation.get("target") in VERSION_GRAPH.nodes:
            eff_from = date.fromisoformat(item["effective_from"])
            try:
                VERSION_GRAPH.add_relation(
                    from_code=item["code"],
                    to_code=relation["target"],
                    relation=relation.get("type", "amends"),
                    effective_from=eff_from,
                    scope=relation.get("scope"),
                )
            except Exception:
                pass

    return count


# Load initial fixtures on module load
load_core_instruments()


def get_retriever() -> HybridRetriever:
    return HybridRetriever(
        chunks=list(CHUNKS_DB.values()),
        version_graph=VERSION_GRAPH,
    )


@app.get("/v1/health")
def health_check():
    """Returns liveness, corpus status, and indexed entity counts."""
    start_t = time.time()
    res = {
        "status": "healthy",
        "corpus_updated": CORPUS_LAST_UPDATED.isoformat(),
        "indexed_chunks": len(CHUNKS_DB),
        "indexed_instruments": len(VERSION_GRAPH.nodes),
        "audit_logs_count": audit_store.count(),
        "version": "0.1.0",
    }
    metrics_collector.record_request("GET", "/v1/health", 200, time.time() - start_t)
    return res


@app.post("/v1/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """Processes compliance questions in Gujarati, Hindi, English, or Gujlish.

    Enforces DPDP Act 2023 PII scrubbing, audit logging, confidence gating,
    NLI citation verification, and numeric preservation.
    """
    start_time = time.time()
    session_id = request.session_id or uuid4()

    # 1. DPDP Compliance: Scrub PII and record query trace
    scrubbed_query = PIIScrubber.scrub_pii(request.query)

    # 2. Indic language detection and transliteration normalization
    detected = language_detector.detect(request.query)
    target_lang = request.language or detected.primary_language
    normalized_query = normalizer.normalize(request.query)

    # Record trace in audit log
    audit_store.record_query(
        query=request.query,
        as_of=request.as_of.isoformat(),
        language=target_lang,
        session_id=session_id,
    )

    # 3. Check temporal query cache (Cost and latency optimization)
    cached_response = query_cache.get(
        normalized_query=normalized_query,
        as_of=request.as_of,
        language=target_lang,
    )
    if cached_response is not None:
        metrics_collector.record_cache_hit()
        metrics_collector.record_request("POST", "/v1/ask", 200, time.time() - start_time)
        return cached_response

    metrics_collector.record_cache_miss()

    # 4. Scope, prompt injection, and ambiguity safety gating
    must_abstain, reason = abstention_engine.should_abstain(
        query=request.query,
        normalized_query=normalized_query,
    )
    if must_abstain:
        metrics_collector.record_answer(language=target_lang, abstained=True)
        metrics_collector.record_request("POST", "/v1/ask", 200, time.time() - start_time)
        return abstention_engine.create_abstention_response(
            language=target_lang,
            as_of=request.as_of,
            corpus_updated=CORPUS_LAST_UPDATED,
            reason=reason,
        )

    # 4. Hybrid Retrieval with temporal filter
    retriever = get_retriever()
    scored_candidates = retriever.retrieve(
        query=normalized_query,
        as_of=request.as_of,
        top_k=8,
    )

    # 5. Confidence & Abstention check on retrieved evidence strength
    if not scored_candidates or scored_candidates[0].rrf_score <= 0.012:
        metrics_collector.record_answer(language=target_lang, abstained=True)
        metrics_collector.record_request("POST", "/v1/ask", 200, time.time() - start_time)
        return abstention_engine.create_abstention_response(
            language=target_lang,
            as_of=request.as_of,
            corpus_updated=CORPUS_LAST_UPDATED,
            reason="insufficient_evidence",
        )

    # 6. Generate and verify grounded answer with NLI verifier and numeric guard
    response = generator.generate_answer(
        query=request.query,
        as_of=request.as_of,
        language=target_lang,
        candidates=scored_candidates,
        corpus_updated=CORPUS_LAST_UPDATED,
    )

    # 7. Store in temporal query cache
    query_cache.set(
        normalized_query=normalized_query,
        as_of=request.as_of,
        language=target_lang,
        response=response,
    )

    metrics_collector.record_answer(language=target_lang, abstained=response.abstained)
    metrics_collector.record_request("POST", "/v1/ask", 200, time.time() - start_time)
    return response


@app.get("/v1/instruments/{instrument_id}")
def get_instrument(instrument_id: str):
    """Retrieves detailed instrument metadata and statutory amendment timeline."""
    start_t = time.time()
    record = None
    node = None

    if instrument_id in INSTRUMENTS_DB:
        record = INSTRUMENTS_DB[instrument_id]
        code = record["code"]
        node = VERSION_GRAPH.nodes.get(code)
    elif instrument_id in VERSION_GRAPH.nodes:
        code = instrument_id
        node = VERSION_GRAPH.nodes[code]
        record = {
            "id": str(node.id),
            "code": node.code,
            "authority": "CBIC",
            "type": "notification",
            "number": node.number,
            "title": node.title,
            "jurisdiction": node.jurisdiction,
            "issued_on": node.issued_on.isoformat(),
            "effective_from": node.effective_from.isoformat(),
            "effective_to": node.effective_to.isoformat() if node.effective_to else None,
            "source_url": None,
            "language": ["en"],
            "subjects": [],
        }
    else:
        # Search by number matching
        for k, rec in INSTRUMENTS_DB.items():
            if rec.get("number") == instrument_id:
                record = rec
                code = rec["code"]
                node = VERSION_GRAPH.nodes.get(code)
                break

    if not record or not code:
        metrics_collector.record_request("GET", f"/v1/instruments/{instrument_id}", 404, time.time() - start_t)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument '{instrument_id}' not found",
        )

    # Query Version Graph for amendment timeline
    amended_by = [
        {"code": e.from_code, "effective_from": e.effective_from.isoformat(), "scope": e.scope}
        for e in VERSION_GRAPH.edges
        if e.to_code == code and e.relation == "amends"
    ]
    superseded_by = [
        {"code": e.from_code, "effective_from": e.effective_from.isoformat(), "scope": e.scope}
        for e in VERSION_GRAPH.edges
        if e.to_code == code and e.relation == "supersedes"
    ]
    amends = [
        {"code": e.to_code, "effective_from": e.effective_from.isoformat(), "scope": e.scope}
        for e in VERSION_GRAPH.edges
        if e.from_code == code and e.relation == "amends"
    ]
    supersedes = [
        {"code": e.to_code, "effective_from": e.effective_from.isoformat(), "scope": e.scope}
        for e in VERSION_GRAPH.edges
        if e.from_code == code and e.relation == "supersedes"
    ]
    clarifies = [
        {"code": e.to_code, "effective_from": e.effective_from.isoformat(), "scope": e.scope}
        for e in VERSION_GRAPH.edges
        if e.from_code == code and e.relation == "clarifies"
    ]

    is_active_now = VERSION_GRAPH.is_in_force_on(code, date.today())

    res = {
        **record,
        "amendment_timeline": {
            "amended_by": amended_by,
            "superseded_by": superseded_by,
            "amends": amends,
            "supersedes": supersedes,
            "clarifies": clarifies,
            "is_in_force_today": is_active_now,
        },
    }
    metrics_collector.record_request("GET", f"/v1/instruments/{instrument_id}", 200, time.time() - start_t)
    return res


@app.get("/v1/chunks/{chunk_id}")
def get_chunk(chunk_id: UUID):
    """Retrieves an exact passage chunk with section path, bounding box, and OCR score."""
    start_t = time.time()
    if chunk_id not in CHUNKS_DB:
        metrics_collector.record_request("GET", f"/v1/chunks/{chunk_id}", 404, time.time() - start_t)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk not found",
        )
    c = CHUNKS_DB[chunk_id]
    bbox = c.metadata.get(
        "bbox",
        {"page": 1, "x0": 72.0, "y0": 100.0, "x1": 540.0, "y1": 250.0},
    )
    ocr_quality = c.metadata.get("ocr_quality", 0.98)

    res = {
        "id": c.id,
        "instrument_id": c.instrument_id,
        "instrument_title": c.instrument_title,
        "section_path": c.section_path,
        "text": c.text,
        "chunk_type": c.chunk_type,
        "token_count": c.token_count,
        "effective_from": c.effective_from.isoformat(),
        "effective_to": c.effective_to.isoformat() if c.effective_to else None,
        "jurisdiction": c.jurisdiction,
        "bbox": bbox,
        "ocr_quality": ocr_quality,
        "metadata": c.metadata,
    }
    metrics_collector.record_request("GET", f"/v1/chunks/{chunk_id}", 200, time.time() - start_t)
    return res


@app.post("/v1/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(fb: FeedbackRequest):
    """Stores user evaluation and reason codes."""
    start_t = time.time()
    FEEDBACK_DB.append(fb.model_dump())
    metrics_collector.record_feedback(fb.rating)
    metrics_collector.record_request("POST", "/v1/feedback", 201, time.time() - start_t)
    return {"status": "recorded", "answer_id": str(fb.answer_id)}


@app.delete("/v1/sessions/{session_id}")
def delete_session(session_id: UUID):
    """Implements DPDP Act 2023 Section 12 (Right to Erasure) for user session traces."""
    start_t = time.time()
    purged_count = audit_store.delete_session(session_id)
    metrics_collector.record_dpdp_purge(purged_count)
    metrics_collector.record_request("DELETE", f"/v1/sessions/{session_id}", 200, time.time() - start_t)
    return {
        "status": "purged",
        "session_id": str(session_id),
        "purged_records": purged_count,
    }


@app.post("/v1/telemetry/purge")
def purge_telemetry():
    """Manual or cron-triggered DPDP 30-day retention log pruner."""
    start_t = time.time()
    purged_count = audit_store.purge_expired_logs()
    metrics_collector.record_dpdp_purge(purged_count)
    metrics_collector.record_request("POST", "/v1/telemetry/purge", 200, time.time() - start_t)
    return {
        "status": "purged",
        "purged_records": purged_count,
        "retention_days": audit_store.ttl_days,
    }


@app.post("/v1/admin/takedown", status_code=status.HTTP_200_OK)
def admin_takedown(req: AdminTakedownRequest):
    """Emergency bad-answer incident response: purges dispute from cache and logs audit trace."""
    start_t = time.time()
    evicted_count = query_cache.invalidate_answer(req.answer_id)
    audit_store.record_query(
        query=f"[INCIDENT_TAKEDOWN] Purged answer {req.answer_id}: {req.reason}",
        as_of=date.today().isoformat(),
        language="en",
        answer_id=req.answer_id,
    )
    metrics_collector.record_request("POST", "/v1/admin/takedown", 200, time.time() - start_t)
    return {
        "status": "takedown_completed",
        "answer_id": str(req.answer_id),
        "evicted_cache_entries": evicted_count,
        "reason": req.reason,
    }


@app.get("/metrics")
def get_metrics():
    """Exports Prometheus text exposition format metrics."""
    start_t = time.time()
    text_data = metrics_collector.export_prometheus_text(len(CHUNKS_DB))
    metrics_collector.record_request("GET", "/metrics", 200, time.time() - start_t)
    return Response(content=text_data, media_type="text/plain; version=0.0.4; charset=utf-8")


# Web Client Static Files and Root Endpoint
WEB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/", include_in_schema=False)
@app.get("/ui", include_in_schema=False)
def serve_ui():
    """Serves the Anupalan Web UI dashboard."""
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "app": "Anupalan Compliance Navigator",
        "message": "Web UI index.html not yet initialized.",
        "api_docs": "/docs",
    }
