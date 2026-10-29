"""Benchmark evaluation metrics for retrieval, generation, and compliance guardrails.

Implements Recall@K, MRR, nDCG@K, Citation Precision, Citation Recall,
Faithfulness, Numeric Hallucination Rate, and Abstention Accuracy (Spec Section 9.2).
"""

import math
from typing import Any


def compute_recall_at_k(retrieved_ids: list[Any], gold_ids: set[Any], k: int = 5) -> float:
    """Computes Recall@K: proportion of gold documents present in top-k retrieved."""
    if not gold_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    intersection = top_k.intersection(gold_ids)
    return len(intersection) / len(gold_ids)


def compute_mrr(retrieved_ids: list[Any], gold_ids: set[Any]) -> float:
    """Computes Mean Reciprocal Rank (MRR): reciprocal rank of the first relevant document."""
    if not gold_ids:
        return 1.0
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in gold_ids:
            return 1.0 / rank
    return 0.0


def compute_ndcg_at_k(retrieved_ids: list[Any], gold_ids: set[Any], k: int = 5) -> float:
    """Computes Normalized Discounted Cumulative Gain (nDCG@K) for binary relevance."""
    if not gold_ids:
        return 1.0

    dcg = 0.0
    for rank, doc_id in enumerate(retrieved_ids[:k], start=1):
        if doc_id in gold_ids:
            dcg += 1.0 / math.log2(rank + 1)

    # Ideal DCG (all gold documents placed at top ranks)
    ideal_count = min(len(gold_ids), k)
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, ideal_count + 1))

    return (dcg / idcg) if idcg > 0.0 else 0.0


def compute_citation_precision(cited_ids: list[Any], gold_ids: set[Any]) -> float:
    """Computes Citation Precision: proportion of cited spans that are actually relevant."""
    if not cited_ids:
        # If no citations were made, precision is 1.0 if no citations were expected, else 0.0
        return 1.0 if not gold_ids else 0.0
    valid_citations = sum(1 for cid in cited_ids if cid in gold_ids)
    return valid_citations / len(cited_ids)


def compute_citation_recall(cited_ids: list[Any], gold_ids: set[Any]) -> float:
    """Computes Citation Recall: proportion of expected gold sources cited."""
    if not gold_ids:
        return 1.0
    cited_set = set(cited_ids)
    intersection = cited_set.intersection(gold_ids)
    return len(intersection) / len(gold_ids)


def compute_numeric_hallucination_rate(
    found_numbers: set[str],
    allowed_numbers: set[str],
) -> float:
    """Computes proportion of generated numbers that are unsupported/hallucinated."""
    if not found_numbers:
        return 0.0
    unsupported = found_numbers.difference(allowed_numbers)
    return len(unsupported) / len(found_numbers)


def compute_abstention_accuracy(is_abstained: bool, requires_abstention: bool) -> float:
    """Returns 1.0 if model correctly abstained (or correctly answered), else 0.0."""
    return 1.0 if (is_abstained == requires_abstention) else 0.0
