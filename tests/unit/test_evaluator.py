"""Unit tests for the BenchmarkEvaluator and CI Quality Gate runner."""

import unittest
from eval.eval_gate import run_gate_check
from eval.evaluator import BenchmarkEvaluator, EvaluationSummary


class TestBenchmarkEvaluator(unittest.TestCase):
    def setUp(self):
        self.evaluator = BenchmarkEvaluator()

    def test_load_benchmark_datasets(self):
        golden = self.evaluator.load_dataset(self.evaluator.golden_path)
        self.assertGreater(len(golden), 0)

        temporal = self.evaluator.load_dataset(self.evaluator.temporal_path)
        self.assertGreater(len(temporal), 0)

        adversarial = self.evaluator.load_dataset(self.evaluator.adversarial_path)
        self.assertGreater(len(adversarial), 0)

    def test_run_full_benchmark(self):
        summary = self.evaluator.run_full_benchmark()
        self.assertIsInstance(summary, EvaluationSummary)
        self.assertGreater(summary.total_queries, 0)
        self.assertGreaterEqual(summary.retrieval_recall_at_5, 0.0)
        self.assertGreaterEqual(summary.citation_precision, 0.0)
        self.assertLessEqual(summary.numeric_hallucination_rate, 1.0)

    def test_ci_gate_check_passes(self):
        passed = run_gate_check()
        self.assertTrue(passed, "CI Evaluation Gate must pass without metric regressions")


if __name__ == "__main__":
    unittest.main()
