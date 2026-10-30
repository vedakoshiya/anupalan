"""Unit tests for DPDP Act 2023 compliance, PII scrubber, and rolling TTL audit logs."""

import unittest
from datetime import datetime, timedelta
from uuid import uuid4

from services.api.src.telemetry import AuditLogStore, PIIScrubber


class TestPIIScrubber(unittest.TestCase):
    def test_scrub_pan(self):
        text = "My business PAN card is ABCDE1234F for GST verification."
        scrubbed = PIIScrubber.scrub_pii(text)
        self.assertNotIn("ABCDE1234F", scrubbed)
        self.assertIn("[REDACTED_PAN]", scrubbed)
        self.assertTrue(PIIScrubber.contains_pii(text))

    def test_scrub_gstin(self):
        text = "Surat textile unit GSTIN: 24ABCDE1234F1Z5 please check status."
        scrubbed = PIIScrubber.scrub_pii(text)
        self.assertNotIn("24ABCDE1234F1Z5", scrubbed)
        self.assertIn("[REDACTED_GSTIN]", scrubbed)
        self.assertTrue(PIIScrubber.contains_pii(text))

    def test_scrub_aadhaar(self):
        text = "Proprietor Aadhaar is 2345 6789 0123 for Udyam signup."
        scrubbed = PIIScrubber.scrub_pii(text)
        self.assertNotIn("2345 6789 0123", scrubbed)
        self.assertIn("[REDACTED_AADHAAR]", scrubbed)
        self.assertTrue(PIIScrubber.contains_pii(text))

    def test_scrub_phone(self):
        text = "Call accountant at +919876543210 or 9825012345 immediately."
        scrubbed = PIIScrubber.scrub_pii(text)
        self.assertNotIn("9876543210", scrubbed)
        self.assertNotIn("9825012345", scrubbed)
        self.assertIn("[REDACTED_PHONE]", scrubbed)
        self.assertTrue(PIIScrubber.contains_pii(text))

    def test_scrub_email(self):
        text = "Send revised circular copy to audit.team@surattextile.in."
        scrubbed = PIIScrubber.scrub_pii(text)
        self.assertNotIn("audit.team@surattextile.in", scrubbed)
        self.assertIn("[REDACTED_EMAIL]", scrubbed)
        self.assertTrue(PIIScrubber.contains_pii(text))

    def test_scrub_multiple_pii_vernacular(self):
        text = "Mara GST number 24ABCDE1234F1Z5 che and phone 9825012345 par sms karo."
        scrubbed = PIIScrubber.scrub_pii(text)
        self.assertNotIn("24ABCDE1234F1Z5", scrubbed)
        self.assertNotIn("9825012345", scrubbed)
        self.assertIn("[REDACTED_GSTIN]", scrubbed)
        self.assertIn("[REDACTED_PHONE]", scrubbed)

    def test_clean_text_no_pii(self):
        text = "Job work par 5% GST lage ke 12%?"
        scrubbed = PIIScrubber.scrub_pii(text)
        self.assertEqual(scrubbed, text)
        self.assertFalse(PIIScrubber.contains_pii(text))

    def test_empty_and_none(self):
        self.assertEqual(PIIScrubber.scrub_pii(""), "")
        self.assertFalse(PIIScrubber.contains_pii(""))


class TestAuditLogStore(unittest.TestCase):
    def setUp(self):
        self.store = AuditLogStore(ttl_days=30)

    def test_record_query(self):
        session_id = uuid4()
        entry = self.store.record_query(
            query="Check status of 24ABCDE1234F1Z5",
            as_of="2026-10-26",
            language="gu",
            session_id=session_id,
        )
        self.assertEqual(self.store.count(), 1)
        self.assertIn("[REDACTED_GSTIN]", entry["query_scrubbed"])
        self.assertEqual(entry["session_id"], session_id)
        self.assertEqual(entry["language"], "gu")

    def test_purge_expired_logs_30_days(self):
        # 1. Fresh log (today)
        self.store.record_query(query="Fresh query 1", as_of="2026-10-26", language="en")
        # 2. Expired log (35 days old)
        expired_entry = {
            "id": uuid4(),
            "session_id": uuid4(),
            "query_scrubbed": "Old query",
            "as_of": "2026-09-01",
            "language": "en",
            "answer_id": None,
            "created_at": datetime.utcnow() - timedelta(days=35),
        }
        self.store.logs.append(expired_entry)
        self.assertEqual(self.store.count(), 2)

        purged = self.store.purge_expired_logs()
        self.assertEqual(purged, 1)
        self.assertEqual(self.store.count(), 1)
        self.assertEqual(self.store.logs[0]["query_scrubbed"], "Fresh query 1")

    def test_delete_session_right_to_erasure(self):
        session_to_delete = uuid4()
        other_session = uuid4()

        self.store.record_query(query="User query 1", as_of="2026-10-26", language="gu", session_id=session_to_delete)
        self.store.record_query(query="User query 2", as_of="2026-10-26", language="gu", session_id=session_to_delete)
        self.store.record_query(query="Other query", as_of="2026-10-26", language="hi", session_id=other_session)

        self.assertEqual(self.store.count(), 3)
        deleted = self.store.delete_session(session_to_delete)
        self.assertEqual(deleted, 2)
        self.assertEqual(self.store.count(), 1)
        self.assertEqual(self.store.logs[0]["session_id"], other_session)


if __name__ == "__main__":
    unittest.main()
