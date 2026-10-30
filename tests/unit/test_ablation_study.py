"""Unit tests for the AblationStudyRunner."""

import tempfile
import unittest
from pathlib import Path

from eval.ablation_study import AblationConfigResult, AblationStudyRunner


class TestAblationStudy(unittest.TestCase):
    def setUp(self):
        self.runner = AblationStudyRunner()

    def test_ablation_configs(self):
        self.assertGreaterEqual(len(self.runner.CONFIGS), 5)

    def test_run_ablation_study(self):
        results = self.runner.run_ablation_study()
        self.assertEqual(len(results), len(self.runner.CONFIGS))

        for r in results:
            self.assertIsInstance(r, AblationConfigResult)
            self.assertGreater(r.retrieval_recall_at_5, 0.0)
            self.assertGreater(r.citation_precision, 0.0)
            self.assertGreater(r.avg_latency_ms, 0.0)

        # Baseline full_pipeline should outperform verifier_off in precision
        full = next(r for r in results if "Baseline" in r.config_name)
        no_verifier = next(r for r in results if "Verifier OFF" in r.config_name)
        self.assertGreater(full.citation_precision, no_verifier.citation_precision)
        self.assertLess(full.numeric_hallucination_rate, no_verifier.numeric_hallucination_rate)

    def test_save_results_and_markdown(self):
        results = self.runner.run_ablation_study()
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "ablation.json"
            md_path = Path(tmpdir) / "ABLATION.md"

            saved_json = self.runner.save_results(results, json_path=json_path)
            saved_md = self.runner.generate_markdown_report(results, md_path=md_path)

            self.assertTrue(saved_json.exists())
            self.assertTrue(saved_md.exists())


if __name__ == "__main__":
    unittest.main()
