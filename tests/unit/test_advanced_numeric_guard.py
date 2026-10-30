"""Unit tests for AdvancedNumericGuardrail and vernacular monetary equivalences."""

import unittest
from datetime import date
from uuid import uuid4

from packages.generation.src.generation.advanced_numeric_guard import AdvancedNumericGuardrail
from services.ingestion.src.chunker import StatutoryChunk


class TestAdvancedNumericGuardrail(unittest.TestCase):
    def setUp(self):
        self.guard = AdvancedNumericGuardrail()
        self.chunk_jobwork = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 20/2017-CT",
            section_path="Entry 26",
            text="Reduced rate of GST on textile job work is 5%.",
            context_header="[Authority: CBIC | Instrument: Notif 20/2017]",
            chunk_type="clause",
            effective_from=date(2017, 8, 22),
            effective_to=None,
            jurisdiction="central",
            subjects=["textiles"],
            language="en",
            token_count=10,
        )

        self.chunk_composition = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 14/2019-CT",
            section_path="Para 1",
            text="The turnover limit for composition levy is increased to 15000000 (1.5 Crore rupees).",
            context_header="[Authority: CBIC | Instrument: Notif 14/2019]",
            chunk_type="clause",
            effective_from=date(2019, 4, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["composition"],
            language="en",
            token_count=14,
        )

    def test_extract_and_canonicalize_numbers(self):
        tokens_en = self.guard.extract_numbers("The rate is 5% and threshold is 1.5 crore.")
        self.assertIn("5%", tokens_en)
        self.assertIn("15000000", tokens_en)

        # Vernacular Gujarati
        tokens_gu = self.guard.extract_numbers("કાપડ જોબ વર્ક પર પાંચ ટકા જીએસટી લાગે અને દોઢ કરોડ ની લિમિટ છે.")
        self.assertIn("5%", tokens_gu)
        self.assertIn("15000000", tokens_gu)

        # Vernacular Hindi
        tokens_hi = self.guard.extract_numbers("डेढ़ करोड़ की टर्नओवर लिमिट पर पांच प्रतिशत टैक्स है।")
        self.assertIn("5%", tokens_hi)
        self.assertIn("15000000", tokens_hi)

    def test_verify_claim_matches_vernacular_equivalents(self):
        # Source chunk contains '5%', claim says 'પાંચ ટકા' (5%)
        claim_text = "કાપડ જોબ વર્ક પર પાંચ ટકા ટેક્સ લાગે છે."
        res = self.guard.verify_claim(claim_text, [self.chunk_jobwork])
        self.assertTrue(res.is_valid)
        self.assertEqual(len(res.unsupported_numbers), 0)

        # Source chunk contains '15000000' (1.5 Crore), claim says 'દોઢ કરોડ'
        claim_comp = "કોમ્પોઝિશન સ્કીમ માટે દોઢ કરોડ ની ટર્નઓવર લિમિટ છે."
        res_comp = self.guard.verify_claim(claim_comp, [self.chunk_composition])
        self.assertTrue(res_comp.is_valid)
        self.assertEqual(len(res_comp.unsupported_numbers), 0)

    def test_detects_hallucinated_number(self):
        # Source has 5%, claim hallucinates 18%
        hallucinated_claim = "કાપડ જોબ વર્ક પર 18% ટેક્સ લાગે છે."
        res = self.guard.verify_claim(hallucinated_claim, [self.chunk_jobwork])
        self.assertFalse(res.is_valid)
        self.assertIn("18%", res.unsupported_numbers)
        self.assertIn("Numeric Guardrail Violation", res.explanation)

    def test_claim_without_numbers_is_always_valid(self):
        res = self.guard.verify_claim("આ નિયમ બધા વેપારીઓને લાગુ પડે છે.", [self.chunk_jobwork])
        self.assertTrue(res.is_valid)
        self.assertEqual(len(res.claim_numbers), 0)


if __name__ == "__main__":
    unittest.main()
