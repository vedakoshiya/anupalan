"""Main FastAPI REST API application for Anupalan compliance navigator.

Implements /v1/ask, /v1/instruments/{id}, /v1/chunks/{id}, /v1/feedback, and /v1/health.
"""

from datetime import date
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status

from packages.generation.src.generation.abstention_engine import AbstentionEngine
from packages.generation.src.generation.numeric_guard import NumericGuardrail
from packages.generation.src.generation.schemas import (
    AskRequest,
    AskResponse,
    Citation,
    Claim,
    FeedbackRequest,
)
from packages.generation.src.generation.verifier import CitationVerifier
from packages.query.src.query.language_detector import IndicLanguageDetector
from packages.query.src.query.transliteration_normalizer import TransliterationNormalizer
from packages.retrieval.src.retrieval.hybrid_retriever import HybridRetriever
from services.ingestion.src.chunker import StatutoryChunk, StructureAwareChunker
from services.ingestion.src.version_graph import LegalVersionGraph

app = FastAPI(
    title="Anupalan Compliance API",
    version="0.1.0",
    description="Multilingual, Citation-Grounded Compliance Navigator for Indian MSMEs",
)

# In-memory stores for runtime
CHUNKS_DB: dict[UUID, StatutoryChunk] = {}
FEEDBACK_DB: list[dict] = []
VERSION_GRAPH = LegalVersionGraph()
CORPUS_LAST_UPDATED = date(2026, 10, 26)

# Components
language_detector = IndicLanguageDetector()
normalizer = TransliterationNormalizer()
chunker = StructureAwareChunker()
abstention_engine = AbstentionEngine()
verifier = CitationVerifier()
numeric_guard = NumericGuardrail()


def get_retriever() -> HybridRetriever:
    return HybridRetriever(
        chunks=list(CHUNKS_DB.values()),
        version_graph=VERSION_GRAPH,
    )


@app.get("/v1/health")
def health_check():
    """Returns liveness and corpus status."""
    return {
        "status": "healthy",
        "corpus_updated": CORPUS_LAST_UPDATED.isoformat(),
        "indexed_chunks": len(CHUNKS_DB),
        "version": "0.1.0",
    }


@app.post("/v1/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """Processes compliance questions in Gujarati, Hindi, English, or Gujlish."""
    # 1. Language detection & normalization
    detected = language_detector.detect(request.query)
    target_lang = request.language or detected.primary_language
    normalized_query = normalizer.normalize(request.query)

    # 2. Hybrid Retrieval with temporal filter
    retriever = get_retriever()
    scored_candidates = retriever.retrieve(
        query=normalized_query,
        as_of=request.as_of,
        top_k=8,
    )

    # 3. Confidence & Abstention check
    if not scored_candidates or scored_candidates[0].rrf_score <= 0.0:
        return abstention_engine.create_abstention_response(
            language=target_lang,
            as_of=request.as_of,
            corpus_updated=CORPUS_LAST_UPDATED,
        )

    # 4. Synthesize Claims from top retrieved passage
    top = scored_candidates[0].chunk
    citations = [
        Citation(
            chunk_id=top.id,
            instrument=top.instrument_title,
            clause=top.section_path,
            effective_from=top.effective_from,
        )
    ]

    # Plain language summary & claim based on retrieved content
    summary_text = f"સત્તાવાર સૂચના મુજબ: {top.text}" if target_lang == "gu" else top.text
    claims = [
        Claim(
            text=top.text,
            citations=citations,
            confidence=0.95,
        )
    ]

    # 5. Run Verification & Numeric Guardrails
    available_chunks_map = {c.id: c for c in [s.chunk for s in scored_candidates]}
    is_valid_cit, cit_errors = verifier.verify_citations(claims, available_chunks_map)
    if not is_valid_cit:
        return abstention_engine.create_abstention_response(
            language=target_lang,
            as_of=request.as_of,
            corpus_updated=CORPUS_LAST_UPDATED,
        )

    # Numeric Guardrail Check
    for cl in claims:
        is_num_valid, _ = numeric_guard.verify_claim(cl.text, [top])
        if not is_num_valid:
            return abstention_engine.create_abstention_response(
                language=target_lang,
                as_of=request.as_of,
                corpus_updated=CORPUS_LAST_UPDATED,
            )

    next_steps = [
        "ચલણ અને એચએસએન (HSN) કોડ ચકાસો." if target_lang == "gu" else "Verify delivery challan and HSN code.",
        "તમારા સીએ (CA) સાથે ચર્ચા કરો." if target_lang == "gu" else "Confirm eligibility with your accountant.",
    ]

    return AskResponse(
        answer_id=uuid4(),
        language=target_lang,
        abstained=False,
        summary=summary_text,
        claims=claims,
        next_steps=next_steps,
        as_of=request.as_of,
        corpus_updated=CORPUS_LAST_UPDATED,
    )


@app.get("/v1/chunks/{chunk_id}")
def get_chunk(chunk_id: UUID):
    """Retrieves an exact passage chunk with section path."""
    if chunk_id not in CHUNKS_DB:
        raise HTTPException(status_code=404, detail="Chunk not found")
    c = CHUNKS_DB[chunk_id]
    return {
        "id": c.id,
        "instrument_title": c.instrument_title,
        "section_path": c.section_path,
        "text": c.text,
        "effective_from": c.effective_from.isoformat(),
        "effective_to": c.effective_to.isoformat() if c.effective_to else None,
        "jurisdiction": c.jurisdiction,
    }


@app.post("/v1/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(fb: FeedbackRequest):
    """Stores user evaluation and reason codes."""
    FEEDBACK_DB.append(fb.model_dump())
    return {"status": "recorded", "answer_id": str(fb.answer_id)}
