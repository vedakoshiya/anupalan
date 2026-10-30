"""Unit tests for NLICitationVerifier."""

import unittest
from datetime import date
from uuid import uuid4

from packages.generation.src.generation.nli_verifier import NLICitationVerifier
from packages.generation.src.generation.schemas import Citation, Claim
from services.ingestion.src.chunker import StatutoryChunk


class TestNLICitationVerifier(unittest.TestCase):
    def setUp(self):
        self.verifier = NLICitationVerifier(min_entailment_threshold=0.75)
        self.chunk_id = uuid4()
        self.chunk = StatutoryChunk(
            id=self.chunk_id,
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 20/2017-CT",
            section_path="Entry 26(i)",
            text="Rate of GST on textile job work is 5 percent for all registered units.",
            context_header="[Authority: CBIC | Instrument: Notif 20/2017]",
            chunk_type="clause",
            effective_from=date(2017, 8, 22),
            effective_to=None,
            jurisdiction="central",
            subjects=["job_work", "textiles"],
            language="en",
            token_count=14,
        )
        self.available_chunks = {self.chunk_id: self.chunk}

    def test_verify_grounded_claim_succeeds(self):
        citation = Citation(
            chunk_id=self.chunk_id,
            instrument="Notification 20/2017-CT",
            clause="Entry 26(i)",
            effective_from=date(2017, 8, 22),
        )
        claim = Claim(
            text="Rate of GST on textile job work is 5 percent.",
            citations=[citation],
            confidence=0.9,
        )

        res = self.verifier.verify_claim(claim, 0, self.available_chunks)
        self.assertTrue(res.is_entailed)
        self.assertGreaterEqual(res.entailment_score, 0.75)
        self.assertEqual(len(res.errors), 0)

    def test_verify_claim_with_zero_citations_fails(self):
        claim = Claim(
            text="Textile job work has a reduced rate.",
            citations=[],
            confidence=0.9,
        )
        res = self.verifier.verify_claim(claim, 0, self.available_chunks)
        self.assertFalse(res.is_entailed)
        self.assertIn("zero statutory citations", res.errors[0])

    def test_verify_claim_with_invalid_chunk_id_fails(self):
        invalid_id = uuid4()
        citation = Citation(
            chunk_id=invalid_id,
            instrument="Fake Notification",
            clause="Para 1",
            effective_from=date(2017, 8, 22),
        )
        claim = Claim(
            text="Textile job work rate is 5 percent.",
            citations=[citation],
            confidence=0.9,
        )
        res = self.verifier.verify_claim(claim, 0, self.available_chunks)
        self.assertFalse(res.is_entailed)
        self.assertIn("unretrieved or invalid chunk", res.errors[0])

    def test_verify_claim_date_mismatch_fails(self):
        # Cited effective date doesn't match chunk date
        citation = Citation(
            chunk_id=self.chunk_id,
            instrument="Notification 20/2017-CT",
            clause="Entry 26(i)",
            effective_from=date(2025, 1, 1),
        )
        claim = Claim(
            text="Rate of GST on textile job work is 5 percent.",
            citations=[citation],
            confidence=0.9,
        )
        res = self.verifier.verify_claim(claim, 0, self.available_chunks)
        self.assertFalse(res.is_entailed)
        self.assertIn("Citation date mismatch", res.errors[0])

    def test_verify_answer_faithfulness_calculation(self):
        cit = Citation(
            chunk_id=self.chunk_id,
            instrument="Notification 20/2017-CT",
            clause="Entry 26(i)",
            effective_from=date(2017, 8, 22),
        )
        valid_claim = Claim(text="Rate of GST on textile job work is 5 percent.", citations=[cit], confidence=0.9)
        invalid_claim = Claim(text="Completely unrelated unsupported rule.", citations=[cit], confidence=0.9)

        is_faithful, score, verified, errors = self.verifier.verify_answer(
            claims=[valid_claim, invalid_claim],
            available_chunks=self.available_chunks,
            filter_unsupported=True,
        )

        self.assertEqual(len(verified), 1)
        self.assertEqual(score, 0.5)


if __name__ == "__main__":
    unittest.main()
