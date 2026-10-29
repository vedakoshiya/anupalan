"""Unit tests for evaluation metrics (Recall@K, MRR, nDCG, Citation, Numeric)."""

import unittest
from eval.metrics import (
    compute_abstention_accuracy,
    compute_citation_precision,
    compute_citation_recall,
    compute_mrr,
    compute_ndcg_at_k,
    compute_numeric_hallucination_rate,
    compute_recall_at_k,
)


class TestEvalMetrics(unittest.TestCase):
    def test_recall_at_k(self):
        gold = {"doc_1", "doc_2"}
        # Both in top 5
        self.assertEqual(compute_recall_at_k(["doc_1", "doc_2", "doc_3"], gold, k=5), 1.0)
        # 1 out of 2 in top 2
        self.assertEqual(compute_recall_at_k(["doc_1", "doc_3"], gold, k=2), 0.5)
        # 0 in top 2
        self.assertEqual(compute_recall_at_k(["doc_3", "doc_4"], gold, k=2), 0.0)

    def test_mrr(self):
        gold = {"target_doc"}
        # First rank
        self.assertEqual(compute_mrr(["target_doc", "doc_2"], gold), 1.0)
        # Second rank
        self.assertEqual(compute_mrr(["doc_1", "target_doc"], gold), 0.5)
        # Fourth rank
        self.assertEqual(compute_mrr(["a", "b", "c", "target_doc"], gold), 0.25)
        # Not found
        self.assertEqual(compute_mrr(["a", "b", "c"], gold), 0.0)

    def test_ndcg_at_k(self):
        gold = {"doc_1"}
        # Perfect rank 1
        self.assertEqual(compute_ndcg_at_k(["doc_1", "doc_2"], gold, k=5), 1.0)
        # Zero match
        self.assertEqual(compute_ndcg_at_k(["doc_3", "doc_4"], gold, k=5), 0.0)
        # Rank 2 is lower than rank 1
        ndcg_rank_2 = compute_ndcg_at_k(["doc_2", "doc_1"], gold, k=5)
        self.assertLess(ndcg_rank_2, 1.0)
        self.assertGreater(ndcg_rank_2, 0.0)

    def test_citation_precision_and_recall(self):
        gold = {"chunk_A", "chunk_B"}

        # Cited A and B (100% precision, 100% recall)
        self.assertEqual(compute_citation_precision(["chunk_A", "chunk_B"], gold), 1.0)
        self.assertEqual(compute_citation_recall(["chunk_A", "chunk_B"], gold), 1.0)

        # Cited A and Irrelevant C (50% precision, 50% recall)
        self.assertEqual(compute_citation_precision(["chunk_A", "chunk_C"], gold), 0.5)
        self.assertEqual(compute_citation_recall(["chunk_A", "chunk_C"], gold), 0.5)

    def test_numeric_hallucination_rate(self):
        allowed = {"5%", "150000", "45"}

        # All numbers grounded -> 0.0 hallucination
        self.assertEqual(compute_numeric_hallucination_rate({"5%", "45"}, allowed), 0.0)

        # 1 out of 2 numbers ungrounded (e.g. 18%) -> 0.5 hallucination rate
        self.assertEqual(compute_numeric_hallucination_rate({"5%", "18%"}, allowed), 0.5)

    def test_abstention_accuracy(self):
        # Correct abstention
        self.assertEqual(compute_abstention_accuracy(is_abstained=True, requires_abstention=True), 1.0)
        # Correctly answered
        self.assertEqual(compute_abstention_accuracy(is_abstained=False, requires_abstention=False), 1.0)
        # Wrongful abstention
        self.assertEqual(compute_abstention_accuracy(is_abstained=True, requires_abstention=False), 0.0)
        # Missed abstention (hallucinated when should have abstained)
        self.assertEqual(compute_abstention_accuracy(is_abstained=False, requires_abstention=True), 0.0)


if __name__ == "__main__":
    unittest.main()
