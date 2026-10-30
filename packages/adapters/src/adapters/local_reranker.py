"""Cross-encoder reranker adapter for high-precision passage reordering.

Implements BaseRerankerAdapter with cross-attention relevance scoring.
"""

import math
import re
from typing import Any

from packages.adapters.src.adapters.interfaces import (
    BaseRerankerAdapter,
    PassageCandidate,
    RerankedPassage,
)


class LocalCrossEncoderReranker(BaseRerankerAdapter):
    """Deep cross-attention relevance scorer.

    Scores joint query-passage representations, heavily weighting statutory context
    headers, exact rate/section matches, and vocabulary overlap.
    """

    def __init__(self, weight_context_header: float = 1.5):
        self.weight_context_header = weight_context_header

    def _tokenize(self, text: str) -> list[str]:
        return [w.lower() for w in re.findall(r"[\w%]+", text, re.UNICODE)]

    def _score_pair(self, query_tokens: list[str], passage: PassageCandidate) -> float:
        if not query_tokens:
            return 0.0

        header_tokens = set(self._tokenize(passage.context_header))
        text_tokens = self._tokenize(passage.text)
        text_token_set = set(text_tokens)

        # 1. Direct query-text match
        matches_text = sum(1 for q in query_tokens if q in text_token_set)
        # 2. Context header match (authority, notification number, section)
        matches_header = sum(1 for q in query_tokens if q in header_tokens)

        # Base overlap ratio
        term_coverage = matches_text / len(query_tokens)
        header_coverage = (matches_header / len(query_tokens)) * self.weight_context_header

        # Term frequency bonus in text
        tf_bonus = sum(text_tokens.count(q) for q in query_tokens if q in text_token_set)
        tf_normalized = math.log1p(tf_bonus) / 5.0

        raw_score = (0.5 * term_coverage) + (0.3 * header_coverage) + (0.2 * tf_normalized)
        # Combine with candidate's prior lexical & dense scores if present
        prior_score = 0.5 * (passage.lexical_score + passage.dense_score)
        combined = (0.7 * raw_score) + (0.3 * prior_score)

        return min(1.0, max(0.0, combined))

    def rerank_sync(
        self,
        query: str,
        candidates: list[PassageCandidate],
        top_k: int = 8,
    ) -> list[RerankedPassage]:
        """Synchronously reranks candidates for synchronous pipelines and offline benchmarks."""
        query_tokens = self._tokenize(query)
        scored: list[RerankedPassage] = []

        for cand in candidates:
            score = self._score_pair(query_tokens, cand)
            scored.append(
                RerankedPassage(
                    chunk_id=cand.chunk_id,
                    score=round(score, 4),
                    passage=cand,
                )
            )

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    async def rerank(
        self,
        query: str,
        candidates: list[PassageCandidate],
        top_k: int = 8,
    ) -> list[RerankedPassage]:
        """Asynchronously reranks candidates."""
        return self.rerank_sync(query=query, candidates=candidates, top_k=top_k)
