"""Unit tests for RetrievalConfidenceGate."""

import unittest
from datetime import date
from uuid import uuid4

from packages.retrieval.src.retrieval.confidence_gate import RetrievalConfidenceGate
from packages.retrieval.src.retrieval.hybrid_retriever import ScoredChunk
from services.ingestion.src.chunker import StatutoryChunk


class TestRetrievalConfidenceGate(unittest.TestCase):
    def setUp(self):
        self.gate = RetrievalConfidenceGate(min_top_score=0.012)
        self.chunk = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notif 11/2017",
            section_path="Entry 26",
            text="Textile job work rate 5%.",
            context_header="[Authority: CBIC]",
            chunk_type="clause",
            effective_from=date(2017, 7, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["textiles"],
            language="en",
            token_count=6,
        )

    def test_empty_candidates_returns_low_confidence(self):
        result = self.gate.evaluate([])
        self.assertFalse(result.is_confident)
        self.assertEqual(result.confidence_level, "low")
        self.assertEqual(result.candidate_count, 0)

    def test_low_score_triggers_abstention_flag(self):
        cand = ScoredChunk(chunk=self.chunk, bm25_score=0.1, vector_score=0.1, rrf_score=0.005)
        result = self.gate.evaluate([cand])
        self.assertFalse(result.is_confident)
        self.assertEqual(result.confidence_level, "low")
        self.assertIn("below minimum evidence threshold", result.reason)

    def test_high_confidence_candidate(self):
        cand1 = ScoredChunk(chunk=self.chunk, bm25_score=0.9, vector_score=0.9, rrf_score=0.032)
        cand2 = ScoredChunk(chunk=self.chunk, bm25_score=0.4, vector_score=0.4, rrf_score=0.015)
        result = self.gate.evaluate([cand1, cand2])

        self.assertTrue(result.is_confident)
        self.assertEqual(result.confidence_level, "high")
        self.assertEqual(result.top_score, 0.032)
        self.assertAlmostEqual(result.score_margin, 0.017, places=3)
        self.assertEqual(result.candidate_count, 2)

    def test_medium_confidence_candidate(self):
        cand = ScoredChunk(chunk=self.chunk, bm25_score=0.5, vector_score=0.5, rrf_score=0.015)
        result = self.gate.evaluate([cand])

        self.assertTrue(result.is_confident)
        self.assertEqual(result.confidence_level, "medium")


if __name__ == "__main__":
    unittest.main()
