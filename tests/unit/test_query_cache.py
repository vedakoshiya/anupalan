"""Unit tests for the ComplianceQueryCache engine."""

import time
import unittest
from datetime import date
from uuid import uuid4

from packages.query.src.query.cache import ComplianceQueryCache


class TestComplianceQueryCache(unittest.TestCase):
    def setUp(self):
        self.cache = ComplianceQueryCache(max_size=3, ttl_seconds=2)

    def test_cache_hit_and_miss(self):
        today = date(2026, 10, 26)
        query = "job work gst rate"

        # Initially a miss
        self.assertIsNone(self.cache.get(query, today, "gu"))
        self.assertEqual(self.cache.stats()["misses"], 1)

        # Store response
        sample_resp = {"answer_id": str(uuid4()), "summary": "GST is 5% on textile job work."}
        self.cache.set(query, today, "gu", sample_resp)

        # Now a hit
        cached = self.cache.get(query, today, "gu")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["summary"], sample_resp["summary"])
        self.assertEqual(self.cache.stats()["hits"], 1)
        self.assertEqual(self.cache.stats()["hit_ratio"], 0.5)

    def test_lru_eviction(self):
        d = date(2026, 10, 26)
        # Capacity is 3: add Q1, Q2, Q3
        self.cache.set("q1", d, "en", "resp1")
        self.cache.set("q2", d, "en", "resp2")
        self.cache.set("q3", d, "en", "resp3")
        self.assertEqual(self.cache.stats()["size"], 3)

        # Access Q1 to make Q2 the least recently used
        self.assertEqual(self.cache.get("q1", d, "en"), "resp1")

        # Add Q4 -> Q2 must be evicted
        self.cache.set("q4", d, "en", "resp4")
        self.assertEqual(self.cache.stats()["size"], 3)
        self.assertIsNone(self.cache.get("q2", d, "en"))
        self.assertIsNotNone(self.cache.get("q1", d, "en"))
        self.assertIsNotNone(self.cache.get("q3", d, "en"))
        self.assertIsNotNone(self.cache.get("q4", d, "en"))

    def test_ttl_expiration(self):
        short_cache = ComplianceQueryCache(max_size=10, ttl_seconds=1)
        d = date(2026, 10, 26)
        short_cache.set("exp_query", d, "en", "active_resp")

        self.assertIsNotNone(short_cache.get("exp_query", d, "en"))
        # Wait 1.1s for expiration
        time.sleep(1.1)
        self.assertIsNone(short_cache.get("exp_query", d, "en"))

    def test_invalidate_answer(self):
        d = date(2026, 10, 26)
        ans_id = uuid4()
        dummy_resp = {"answer_id": str(ans_id), "summary": "Disputed rate claim."}
        self.cache.set("query_disputed", d, "hi", dummy_resp)

        self.assertIsNotNone(self.cache.get("query_disputed", d, "hi"))
        evicted = self.cache.invalidate_answer(ans_id)
        self.assertEqual(evicted, 1)
        self.assertIsNone(self.cache.get("query_disputed", d, "hi"))

    def test_clear_and_empty_stats(self):
        d = date(2026, 10, 26)
        self.cache.set("q", d, "en", "r")
        self.cache.clear()
        stats = self.cache.stats()
        self.assertEqual(stats["size"], 0)
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["hit_ratio"], 0.0)


if __name__ == "__main__":
    unittest.main()
