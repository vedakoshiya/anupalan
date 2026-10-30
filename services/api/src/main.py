"""Main FastAPI REST API application for Anupalan compliance navigator.

Implements /v1/ask, /v1/instruments/{id}, /v1/chunks/{id}, /v1/feedback, and /v1/health.
"""

from datetime import date
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status

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
generator = ComplianceGenerator()


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

    # 2. Scope, injection, and ambiguity safety gating
    must_abstain, reason = abstention_engine.should_abstain(
        query=request.query,
        normalized_query=normalized_query,
    )
    if must_abstain:
        return abstention_engine.create_abstention_response(
            language=target_lang,
            as_of=request.as_of,
            corpus_updated=CORPUS_LAST_UPDATED,
            reason=reason,
        )

    # 3. Hybrid Retrieval with temporal filter
    retriever = get_retriever()
    scored_candidates = retriever.retrieve(
        query=normalized_query,
        as_of=request.as_of,
        top_k=8,
    )

    # 4. Confidence & Abstention check on evidence strength
    if not scored_candidates or scored_candidates[0].rrf_score <= 0.012:
        return abstention_engine.create_abstention_response(
            language=target_lang,
            as_of=request.as_of,
            corpus_updated=CORPUS_LAST_UPDATED,
            reason="insufficient_evidence",
        )

    # 5. Generate and verify grounded answer with NLI verifier and advanced numeric guardrail
    return generator.generate_answer(
        query=request.query,
        as_of=request.as_of,
        language=target_lang,
        candidates=scored_candidates,
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
