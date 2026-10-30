"""Cross-encoder reranker for statutory hybrid retrieval.

Wraps BaseRerankerAdapter to rescore candidate passages using deep cross-attention,
optimizing the top 50 hybrid candidates down to the top 8 most legally relevant passages.
"""

from typing import Any

from packages.adapters.src.adapters.interfaces import (
    BaseRerankerAdapter,
    PassageCandidate,
    RerankedPassage,
)
from packages.adapters.src.adapters.local_reranker import LocalCrossEncoderReranker


class CrossEncoderReranker:
    """Reranks hybrid search candidates using cross-attention scoring."""

    def __init__(self, adapter: BaseRerankerAdapter | None = None):
        self.adapter = adapter or LocalCrossEncoderReranker()

    def rerank_scored_chunks(
        self,
        query: str,
        candidates: list[Any],
        top_k: int = 8,
    ) -> list[Any]:
        """Reranks a list of ScoredChunk candidates.

        Converts ScoredChunk into PassageCandidate, scores them via the adapter,
        and assigns `rerank_score` to each candidate.
        """
        if not candidates:
            return []

        passage_candidates = [
            PassageCandidate(
                chunk_id=cand.chunk.id,
                text=cand.chunk.text,
                context_header=cand.chunk.context_header,
                lexical_score=getattr(cand, "bm25_score", 0.0),
                dense_score=getattr(cand, "vector_score", 0.0),
            )
            for cand in candidates
        ]

        if hasattr(self.adapter, "rerank_sync"):
            reranked = self.adapter.rerank_sync(query=query, candidates=passage_candidates, top_k=top_k)
        else:
            import asyncio

            reranked = asyncio.run(
                self.adapter.rerank(query=query, candidates=passage_candidates, top_k=top_k)
            )

        # Map back to original candidates
        score_map = {r.chunk_id: r.score for r in reranked}
        top_chunk_ids = [r.chunk_id for r in reranked]

        top_candidates = []
        for cand in candidates:
            if cand.chunk.id in score_map:
                cand.rerank_score = score_map[cand.chunk.id]
                top_candidates.append(cand)

        # Re-sort in order of reranker score
        top_candidates.sort(key=lambda c: getattr(c, "rerank_score", 0.0), reverse=True)
        return top_candidates[:top_k]
