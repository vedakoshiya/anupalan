"""Unit tests for Pydantic models and structured contracts (schemas.py)."""

import unittest
from datetime import date
from uuid import uuid4

from pydantic import ValidationError
from packages.generation.src.generation.schemas import (
    AskRequest,
    AskResponse,
    Citation,
    Claim,
    FeedbackRequest,
    InstrumentDetail,
    InstrumentRelation,
)


class TestSchemas(unittest.TestCase):
    def test_citation_creation_and_validation(self):
        chunk_id = uuid4()
        cit = Citation(
            chunk_id=chunk_id,
            instrument="Notification 11/2017-Central Tax (Rate)",
            clause="Entry 26(i)",
            effective_from=date(2017, 7, 1),
        )
        self.assertEqual(cit.chunk_id, chunk_id)
        self.assertEqual(cit.clause, "Entry 26(i)")
        self.assertEqual(cit.effective_from, date(2017, 7, 1))

    def test_claim_confidence_bounds(self):
        cit = Citation(
            chunk_id=uuid4(),
            instrument="Notification 20/2017-CT (Rate)",
            clause="Para 1",
            effective_from=date(2017, 8, 22),
        )
        # Valid confidence
        claim = Claim(text="Textile job work has 5% GST.", citations=[cit], confidence=0.96)
        self.assertAlmostEqual(claim.confidence, 0.96)

        # Invalid confidence > 1.0
        with self.assertRaises(ValidationError):
            Claim(text="Invalid", citations=[cit], confidence=1.5)

        # Invalid confidence < 0.0
        with self.assertRaises(ValidationError):
            Claim(text="Invalid", citations=[cit], confidence=-0.1)

    def test_ask_request_validation(self):
        # Valid request
        req = AskRequest(query="Job work par GST kevi rite lage?")
        self.assertEqual(req.query, "Job work par GST kevi rite lage?")
        self.assertEqual(req.as_of, date.today())
        self.assertIsNotNone(req.session_id)

        # Query too short (< 2 chars)
        with self.assertRaises(ValidationError):
            AskRequest(query="?")

    def test_ask_response_contract(self):
        answer_id = uuid4()
        chunk_id = uuid4()
        resp = AskResponse(
            answer_id=answer_id,
            language="gu",
            abstained=False,
            summary="જોબ વર્ક પર કાપડ માટે 5% અને અન્ય માટે 12% કે 18% દર છે.",
            claims=[
                Claim(
                    text="કાપડ જોબ વર્ક પર 5% દર લાગે છે.",
                    citations=[
                        Citation(
                            chunk_id=chunk_id,
                            instrument="Notification 20/2017-Central Tax (Rate)",
                            clause="Item (i)",
                            effective_from=date(2017, 8, 22),
                        )
                    ],
                    confidence=0.95,
                )
            ],
            next_steps=["ચલણ ચકાસો", "સમયમર્યાદા ધ્યાનમાં રાખો"],
            as_of=date(2026, 10, 27),
            corpus_updated=date(2026, 10, 26),
        )

        data = resp.model_dump()
        self.assertEqual(data["language"], "gu")
        self.assertFalse(data["abstained"])
        self.assertEqual(len(data["claims"]), 1)
        self.assertEqual(len(data["next_steps"]), 2)

    def test_feedback_request_validation(self):
        answer_id = uuid4()
        fb = FeedbackRequest(answer_id=answer_id, rating=1, comment="Helpful answer")
        self.assertEqual(fb.rating, 1)

        # Invalid rating outside {-1, 0, 1} range
        with self.assertRaises(ValidationError):
            FeedbackRequest(answer_id=answer_id, rating=5)


if __name__ == "__main__":
    unittest.main()
