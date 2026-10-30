"""Unit tests for ComplianceGenerator orchestrator."""

import unittest
from datetime import date
from uuid import uuid4

from packages.generation.src.generation.generator import ComplianceGenerator
from packages.generation.src.generation.schemas import AskResponse
from packages.retrieval.src.retrieval.hybrid_retriever import ScoredChunk
from services.ingestion.src.chunker import StatutoryChunk


class TestComplianceGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ComplianceGenerator()
        self.chunk = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 20/2017-CT",
            section_path="Entry 26(i)",
            text="Reduced rate of GST on textile job work is 5 percent.",
            context_header="[Authority: CBIC | Instrument: Notif 20/2017]",
            chunk_type="clause",
            effective_from=date(2017, 8, 22),
            effective_to=None,
            jurisdiction="central",
            subjects=["textiles"],
            language="en",
            token_count=10,
        )
        self.candidate = ScoredChunk(
            chunk=self.chunk,
            bm25_score=0.9,
            vector_score=0.8,
            rrf_score=0.03,
        )

    def test_generate_answer_gujarati(self):
        resp = self.generator.generate_answer(
            query="Job work par GST ketlo lage?",
            as_of=date(2026, 10, 27),
            language="gu",
            candidates=[self.candidate],
            corpus_updated=date(2026, 10, 26),
        )

        self.assertIsInstance(resp, AskResponse)
        self.assertFalse(resp.abstained)
        self.assertEqual(resp.language, "gu")
        self.assertIn("સત્તાવાર પરિપત્ર", resp.summary)
        self.assertEqual(len(resp.claims), 1)
        self.assertEqual(resp.claims[0].citations[0].chunk_id, self.chunk.id)
        self.assertGreater(len(resp.next_steps), 0)
        self.assertIn("આ સિસ્ટમ માત્ર સત્તાવાર પરિપત્રો", resp.disclaimer)

    def test_generate_answer_hindi(self):
        resp = self.generator.generate_answer(
            query="Job work par GST kitna hai?",
            as_of=date(2026, 10, 27),
            language="hi",
            candidates=[self.candidate],
            corpus_updated=date(2026, 10, 26),
        )

        self.assertFalse(resp.abstained)
        self.assertEqual(resp.language, "hi")
        self.assertIn("आधिकारिक अधिसूचना", resp.summary)
        self.assertIn("यह प्रणाली केवल आधिकारिक परिपत्रों", resp.disclaimer)

    def test_empty_candidates_triggers_abstention(self):
        resp = self.generator.generate_answer(
            query="Random unknown query",
            as_of=date(2026, 10, 27),
            language="en",
            candidates=[],
            corpus_updated=date(2026, 10, 26),
        )

        self.assertTrue(resp.abstained)
        self.assertEqual(len(resp.claims), 0)
        self.assertIn("could not find sufficient", resp.summary)


if __name__ == "__main__":
    unittest.main()
