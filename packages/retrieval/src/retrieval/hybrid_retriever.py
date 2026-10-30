"""Hybrid retrieval engine combining BM25 lexical search and dense semantic vectors.

Implements Reciprocal Rank Fusion (RRF), temporal metadata pre-filtering,
cross-encoder reranking, supersession checks, and parent clause context expansion (Spec Section 2.2).
"""

import math
import re
from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from packages.retrieval.src.retrieval.confidence_gate import (
    ConfidenceResult,
    RetrievalConfidenceGate,
)
from packages.retrieval.src.retrieval.metadata_filter import FilterCriteria, MetadataFilter
from packages.retrieval.src.retrieval.parent_expander import ParentClauseExpander
from packages.retrieval.src.retrieval.reranker import CrossEncoderReranker
from packages.retrieval.src.retrieval.supersession_resolver import SupersessionResolver
from packages.retrieval.src.retrieval.vector_store import (
    BaseRetrievalStore,
    InMemoryRetrievalStore,
)
from services.ingestion.src.chunker import StatutoryChunk
from services.ingestion.src.version_graph import LegalVersionGraph


@dataclass
class ScoredChunk:
    chunk: StatutoryChunk
    bm25_score: float
    vector_score: float
    rrf_score: float
    is_superseded: bool = False
    superseded_by: str | None = None
    rerank_score: float | None = None
    expanded_text: str | None = None


class HybridRetriever:
    """Combines lexical and dense semantic signals with statutory temporal filters."""

    def __init__(
        self,
        chunks: list[StatutoryChunk],
        version_graph: LegalVersionGraph | None = None,
        rrf_k: int = 60,
        store: BaseRetrievalStore | None = None,
        reranker: CrossEncoderReranker | None = None,
    ):
        self.chunks = chunks
        self.version_graph = version_graph
        self.rrf_k = rrf_k
        self.store = store or InMemoryRetrievalStore()
        self.store.add_chunks(self.chunks)

        self.supersession_resolver = SupersessionResolver(version_graph=version_graph)
        self.parent_expander = ParentClauseExpander(corpus_chunks=chunks)
        self.reranker = reranker or CrossEncoderReranker()
        self.confidence_gate = RetrievalConfidenceGate()

        self._build_lexical_index()

    def _build_lexical_index(self) -> None:
        """In-memory inverted index and BM25 term frequencies for standalone retrieval."""
        self.doc_count = len(self.chunks)
        self.doc_lengths: dict[UUID, int] = {}
        self.term_doc_freq: dict[str, int] = {}
        self.doc_term_freq: dict[UUID, dict[str, int]] = {}

        total_length = 0
        for chunk in self.chunks:
            tokens = self._tokenize(chunk.context_header + " " + chunk.text)
            doc_len = len(tokens)
            self.doc_lengths[chunk.id] = doc_len
            total_length += doc_len

            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.doc_term_freq[chunk.id] = tf

            for t in tf:
                self.term_doc_freq[t] = self.term_doc_freq.get(t, 0) + 1

        self.avg_doc_len = (total_length / max(1, self.doc_count)) if self.doc_count else 1.0

    def _tokenize(self, text: str) -> list[str]:
        return [w.lower() for w in re.findall(r"[\w%]+", text, re.UNICODE)]

    def _compute_bm25(self, query_tokens: list[str], chunk_id: UUID, k1: float = 1.5, b: float = 0.75) -> float:
        score = 0.0
        doc_tf = self.doc_term_freq.get(chunk_id, {})
        doc_len = self.doc_lengths.get(chunk_id, 0)

        for token in query_tokens:
            if token not in doc_tf:
                continue
            tf = doc_tf[token]
            df = self.term_doc_freq.get(token, 0)
            idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1.0)
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_len / self.avg_doc_len))
            score += idf * (numerator / denominator)

        return score

    def _mock_dense_similarity(self, query_tokens: list[str], chunk: StatutoryChunk) -> float:
        """Computes overlap-based cosine proxy for dense semantic similarity in tests."""
        tokens = set(self._tokenize(chunk.context_header + " " + chunk.text))
        if not tokens:
            return 0.0
        overlap = sum(1 for t in query_tokens if t in tokens)
        return min(1.0, overlap / math.sqrt(max(1, len(query_tokens)) * len(tokens)))

    def retrieve(
        self,
        query: str,
        as_of: date,
        jurisdiction: str | None = None,
        top_k: int = 8,
        rerank: bool = False,
        resolve_supersessions: bool = True,
        expand_parent: bool = True,
    ) -> list[ScoredChunk]:
        """Executes filtered hybrid search across statutory chunks with temporal grounding.

        Steps:
        1. Temporal & jurisdictional pre-filtering via MetadataFilter.
        2. Lexical scoring (BM25) and Dense vector scoring.
        3. Reciprocal Rank Fusion (RRF) candidate merge.
        4. Legal Version Graph supersession resolution.
        5. Cross-Encoder reranking (optional/high precision).
        6. Parent clause context expansion.
        """
        query_tokens = self._tokenize(query)

        # 1. Pre-filter by temporal validity and jurisdiction
        criteria = FilterCriteria(as_of=as_of, jurisdiction=jurisdiction)
        filter_engine = MetadataFilter(criteria)
        valid_candidates = filter_engine.filter_chunks(self.chunks)

        if not valid_candidates:
            return []

        # 2. Score with BM25
        bm25_scores = {c.id: self._compute_bm25(query_tokens, c.id) for c in valid_candidates}
        bm25_matched = [c for c in valid_candidates if bm25_scores[c.id] > 0.0]
        bm25_matched.sort(key=lambda c: bm25_scores[c.id], reverse=True)

        # 3. Score with Dense Vectors (Proxy in unit tests / fast offline)
        dense_scores = {c.id: self._mock_dense_similarity(query_tokens, c) for c in valid_candidates}
        dense_matched = [c for c in valid_candidates if dense_scores[c.id] > 0.0]
        dense_matched.sort(key=lambda c: dense_scores[c.id], reverse=True)

        # 4. Reciprocal Rank Fusion (RRF) - Only for matched candidates
        rrf_scores: dict[UUID, float] = {}
        for rank, c in enumerate(bm25_matched):
            rrf_scores[c.id] = rrf_scores.get(c.id, 0.0) + (1.0 / (self.rrf_k + rank + 1))
        for rank, c in enumerate(dense_matched):
            rrf_scores[c.id] = rrf_scores.get(c.id, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        # 5. Assemble scored chunks (only those with positive matches)
        scored: list[ScoredChunk] = []
        for c in valid_candidates:
            bm25_s = bm25_scores[c.id]
            dense_s = dense_scores[c.id]
            rrf_s = rrf_scores.get(c.id, 0.0)

            # Skip documents with 0 evidence across both lexical and dense signals
            if bm25_s <= 0.0 and dense_s <= 0.0:
                continue

            scored.append(
                ScoredChunk(
                    chunk=c,
                    bm25_score=bm25_s,
                    vector_score=dense_s,
                    rrf_score=rrf_s,
                    is_superseded=False,
                    superseded_by=None,
                )
            )

        scored.sort(key=lambda s: s.rrf_score, reverse=True)

        # 6. Supersession Resolution via Legal Version Graph
        if resolve_supersessions and self.version_graph:
            scored = self.supersession_resolver.annotate_candidates(
                candidates=scored,
                as_of=as_of,
                demote_superseded=True,
            )

        # 7. Cross-Encoder Reranking
        if rerank and self.reranker:
            scored = self.reranker.rerank_scored_chunks(
                query=query,
                candidates=scored,
                top_k=top_k,
            )
        else:
            scored = scored[:top_k]

        # 8. Parent Clause Context Expansion
        if expand_parent:
            scored = self.parent_expander.expand_candidates(scored)

        return scored

    def evaluate_confidence(self, candidates: list[ScoredChunk]) -> ConfidenceResult:
        """Evaluates retrieval confidence of candidates via the confidence gate."""
        return self.confidence_gate.evaluate(candidates)
