"""Unit tests for OCR quality assessment and curator review queue routing."""

import unittest
from services.ingestion.src.ocr_engine import PluggableOCREngine


class TestOCREngineAndQuality(unittest.TestCase):
    def setUp(self):
        self.engine = PluggableOCREngine(fallback_confidence=0.95)

    def test_high_quality_page(self):
        clear_text = "Government of India, Ministry of Finance. Notification No. 11/2017-Central Tax. Job work rate is 5%."
        metric = self.engine.evaluate_text_quality(page_number=1, text=clear_text)
        self.assertEqual(metric.confidence, 0.95)
        self.assertFalse(metric.needs_review)
        self.assertIsNone(metric.review_reason)

    def test_low_quality_page_flagged_for_review(self):
        # Text with heavy corrupted/unprintable characters
        corrupted_text = "Notif\x01\x02\x03\x04\x05\x06\x07\x08##@@$$%%%&&& 11/2017\x00\x00\x00"
        metric = self.engine.evaluate_text_quality(page_number=2, text=corrupted_text)
        self.assertLess(metric.confidence, 0.85)
        self.assertTrue(metric.needs_review)
        self.assertIn("corrupted", metric.review_reason.lower())

    def test_multipage_report_and_curator_routing(self):
        page1 = "Notification 11/2017 text clearly extracted."
        page2 = "\x01\x02\x03 corrupted OCR scan"
        multipage_doc = f"{page1}\x0c{page2}".encode("utf-8")

        pages, report = self.engine.extract_text_and_quality(multipage_doc, "application/pdf")
        self.assertEqual(len(pages), 2)
        self.assertEqual(len(report.page_metrics), 2)
        self.assertTrue(report.requires_curator_review)
        self.assertIn(2, report.flagged_pages)


if __name__ == "__main__":
    unittest.main()
