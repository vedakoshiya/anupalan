"""Unit tests for Prometheus operational metrics collector and text exposition format."""

import unittest
from services.api.src.metrics import PrometheusMetricsCollector


class TestPrometheusMetrics(unittest.TestCase):
    def setUp(self):
        self.collector = PrometheusMetricsCollector()

    def test_record_request_and_p95(self):
        # Empty latency edge case
        self.assertEqual(self.collector.calculate_p95_latency(), 0.0)

        # Record latencies: 0.1, 0.2, 0.3, ... 1.0
        for i in range(1, 21):
            lat = i * 0.05
            self.collector.record_request("POST", "/v1/ask", 200, lat)

        self.assertEqual(len(self.collector.latencies), 20)
        p95 = self.collector.calculate_p95_latency()
        self.assertGreaterEqual(p95, 0.9)
        self.assertLessEqual(p95, 1.0)
        self.assertEqual(self.collector.http_requests[("POST", "/v1/ask", 200)], 20)

    def test_record_answer_and_feedback(self):
        self.collector.record_answer(language="gu", abstained=False)
        self.collector.record_answer(language="gu", abstained=True)
        self.collector.record_answer(language="hi", abstained=False)

        self.assertEqual(self.collector.answers_generated[("gu", False)], 1)
        self.assertEqual(self.collector.answers_generated[("gu", True)], 1)
        self.assertEqual(self.collector.answers_generated[("hi", False)], 1)

        self.collector.record_feedback(1)
        self.collector.record_feedback(1)
        self.collector.record_feedback(-1)

        self.assertEqual(self.collector.feedback_recorded["thumbs_up"], 2)
        self.assertEqual(self.collector.feedback_recorded["thumbs_down"], 1)

    def test_record_dpdp_purge(self):
        self.collector.record_dpdp_purge(5)
        self.collector.record_dpdp_purge(3)
        self.assertEqual(self.collector.dpdp_purges_total, 8)

    def test_export_prometheus_text(self):
        self.collector.record_request("POST", "/v1/ask", 200, 0.25)
        self.collector.record_answer(language="gu", abstained=False)
        self.collector.record_feedback(1)
        self.collector.record_dpdp_purge(12)

        text = self.collector.export_prometheus_text(indexed_chunks_count=42)

        self.assertIn("# HELP anupalan_http_requests_total", text)
        self.assertIn('# TYPE anupalan_http_requests_total counter', text)
        self.assertIn('anupalan_http_requests_total{method="POST",endpoint="/v1/ask",status="200"} 1', text)

        self.assertIn("# HELP anupalan_answers_total", text)
        self.assertIn('anupalan_answers_total{language="gu",abstained="false"} 1', text)

        self.assertIn("# HELP anupalan_feedback_total", text)
        self.assertIn('anupalan_feedback_total{rating="thumbs_up"} 1', text)

        self.assertIn("# HELP anupalan_indexed_chunks_total", text)
        self.assertIn("anupalan_indexed_chunks_total 42", text)

        self.assertIn("# HELP anupalan_query_latency_p95_seconds", text)
        self.assertIn("# HELP anupalan_dpdp_purged_records_total", text)
        self.assertIn("anupalan_dpdp_purged_records_total 12", text)


if __name__ == "__main__":
    unittest.main()
