"""Unit tests for numeric guardrail, citation verifier, and abstention engine."""

import unittest
from datetime import date
from uuid import uuid4

from packages.generation.src.generation.abstention_engine import AbstentionEngine
from packages.generation.src.generation.numeric_guard import (
    NumericGuardrail,
    NumericGuardrailViolation,
)
from packages.generation.src.generation.schemas import Citation, Claim
from packages.generation.src.generation.verifier import CitationVerifier
from services.ingestion.src.chunker import StatutoryChunk


class TestGenerationAndGuards(unittest.TestCase):
    def setUp(self):
        self.chunk = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 11/2017-CT (Rate)",
            section_path="Entry 26(i)",
            text="Rate of GST on textile job work is 5% where value does not exceed 150000 rupees.",
            context_header="[Authority: CBIC | Instrument: Notif 11/2017]",
            chunk_type="clause",
            effective_from=date(2017, 7, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["textiles"],
            language="en",
            token_count=20,
        )
        self.numeric_guard = NumericGuardrail()
        self.verifier = CitationVerifier()
        self.abstention_engine = AbstentionEngine()

    def test_numeric_guard_passes_grounded_numbers(self):
        # 5% and 150000 are in the chunk text
        claim_text = "Textile job work has 5% GST for work under 150000."
        is_valid, unsupported = self.numeric_guard.verify_claim(claim_text, [self.chunk])
        self.assertTrue(is_valid)
        self.assertEqual(len(unsupported), 0)

    def test_numeric_guard_catches_hallucinated_numbers(self):
        # 18% is NOT in the chunk text (chunk has 5%)
        claim_text = "Textile job work tax rate is 18%."
        is_valid, unsupported = self.numeric_guard.verify_claim(claim_text, [self.chunk])
        self.assertFalse(is_valid)
        self.assertIn("18%", unsupported)

        with self.assertRaises(NumericGuardrailViolation):
            self.numeric_guard.validate_or_raise(claim_text, [self.chunk])

    def test_citation_verifier_validates_known_chunks(self):
        cit = Citation(
            chunk_id=self.chunk.id,
            instrument="Notification 11/2017-CT (Rate)",
            clause="Entry 26(i)",
            effective_from=date(2017, 7, 1),
        )
        claim = Claim(text="Textile job work is 5%.", citations=[cit], confidence=0.95)

        is_valid, errors = self.verifier.verify_citations(
            claims=[claim],
            available_chunks={self.chunk.id: self.chunk},
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_citation_verifier_rejects_missing_citations(self):
        claim_no_cit = Claim(text="Uncited statement.", citations=[], confidence=0.95)
        is_valid, errors = self.verifier.verify_citations(
            claims=[claim_no_cit],
            available_chunks={self.chunk.id: self.chunk},
        )
        self.assertFalse(is_valid)
        self.assertIn("zero statutory citations", errors[0])

    def test_abstention_engine_contract(self):
        resp = self.abstention_engine.create_abstention_response(
            language="gu",
            as_of=date(2026, 10, 27),
            corpus_updated=date(2026, 10, 26),
        )
        self.assertTrue(resp.abstained)
        self.assertEqual(resp.language, "gu")
        self.assertEqual(len(resp.claims), 0)
        self.assertGreater(len(resp.next_steps), 0)


if __name__ == "__main__":
    unittest.main()
