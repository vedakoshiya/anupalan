"""Unit tests for the LoadTestRunner and burst benchmark framework."""

import tempfile
import unittest
from pathlib import Path

from benchmarks.load_test import LoadBenchmarkResult, LoadTestRunner
from services.api.src.main import load_core_instruments


class TestLoadTester(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_core_instruments()

    def setUp(self):
        self.runner = LoadTestRunner(target_p50_sla=4.0, target_p95_sla=8.0)

    def test_execute_single_query(self):
        spec = {"query": "Job work par GST kevi rite lage?", "as_of": "2026-10-26", "lang": "gu"}
        success, duration, err = self.runner._execute_single_query(spec)
        self.assertTrue(success)
        self.assertGreater(duration, 0.0)
        self.assertIsNone(err)

    def test_run_burst_benchmark(self):
        result = self.runner.run_burst_benchmark(total_queries=10, concurrency=2)
        self.assertIsInstance(result, LoadBenchmarkResult)
        self.assertEqual(result.total_queries, 10)
        self.assertEqual(result.successful_queries, 10)
        self.assertEqual(result.failed_queries, 0)
        self.assertGreater(result.actual_qps, 0.0)
        self.assertLessEqual(result.p95_latency_sec, 8.0)
        self.assertTrue(result.sla_met)

    def test_save_report(self):
        result = self.runner.run_burst_benchmark(total_queries=4, concurrency=2)
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "test_report.json"
            saved_path = self.runner.save_report(result, output_path=out_file)
            self.assertTrue(saved_path.exists())
            self.assertGreater(saved_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
