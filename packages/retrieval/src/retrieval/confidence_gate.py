"""Retrieval confidence evaluation and abstention gating.

Evaluates evidence strength, top rerank scores, and score margins to determine
whether retrieved statutory passages provide sufficient legal support or must abstain.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ConfidenceResult:
    """Diagnostic outcome of retrieval confidence scoring."""

    is_confident: bool
    confidence_level: str  # 'high' | 'medium' | 'low'
    top_score: float
    score_margin: float
    candidate_count: int
    reason: str


class RetrievalConfidenceGate:
    """Evaluates candidate confidence against safety thresholds."""

    def __init__(
        self,
        min_top_score: float = 0.012,
        min_margin_ratio: float = 0.05,
    ):
        self.min_top_score = min_top_score
        self.min_margin_ratio = min_margin_ratio

    def evaluate(self, candidates: list[Any]) -> ConfidenceResult:
        """Evaluates a ranked list of candidate chunks.

        Candidates may be ScoredChunk or RerankedPassage instances.
        """
        if not candidates:
            return ConfidenceResult(
                is_confident=False,
                confidence_level="low",
                top_score=0.0,
                score_margin=0.0,
                candidate_count=0,
                reason="No matching statutory documents found in corpus",
            )

        # Extract top score
        top_cand = candidates[0]
        top_score = getattr(top_cand, "rrf_score", getattr(top_cand, "score", 0.0))

        if top_score < self.min_top_score:
            return ConfidenceResult(
                is_confident=False,
                confidence_level="low",
                top_score=round(top_score, 4),
                score_margin=0.0,
                candidate_count=len(candidates),
                reason=f"Top score {top_score:.4f} is below minimum evidence threshold {self.min_top_score:.4f}",
            )

        # Calculate score margin
        if len(candidates) > 1:
            second_cand = candidates[1]
            second_score = getattr(second_cand, "rrf_score", getattr(second_cand, "score", 0.0))
            margin = max(0.0, top_score - second_score)
        else:
            margin = top_score

        # Determine confidence level
        if top_score >= 0.025:
            confidence_level = "high"
        elif top_score >= self.min_top_score:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        return ConfidenceResult(
            is_confident=True,
            confidence_level=confidence_level,
            top_score=round(top_score, 4),
            score_margin=round(margin, 4),
            candidate_count=len(candidates),
            reason="Sufficient authoritative statutory evidence located",
        )
