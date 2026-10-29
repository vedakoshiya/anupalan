"""Unit tests validating benchmark datasets integrity, diversity, and formats."""

import json
import unittest
from datetime import datetime
from pathlib import Path


class TestBenchmarkDatasets(unittest.TestCase):
    def setUp(self):
        base_dir = Path(__file__).resolve().parent.parent.parent / "eval" / "datasets"
        self.golden_path = base_dir / "golden_set.json"
        self.temporal_path = base_dir / "temporal_set.json"
        self.adversarial_path = base_dir / "adversarial_set.json"

    def test_golden_dataset_structure(self):
        self.assertTrue(self.golden_path.exists())
        with open(self.golden_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        self.assertGreater(len(items), 10)
        languages = set()
        query_types = set()

        for q in items:
            self.assertIn("id", q)
            self.assertIn("query", q)
            self.assertGreater(len(q["query"]), 5)
            self.assertIn("language", q)
            languages.add(q["language"])
            self.assertIn("query_type", q)
            query_types.add(q["query_type"])

            # Valid ISO date
            datetime.strptime(q["as_of"], "%Y-%m-%d")
            self.assertIsInstance(q["requires_abstention"], bool)

        # Check linguistic and question diversity
        self.assertTrue({"gu", "hi", "en"}.issubset(languages))
        self.assertTrue({"single_hop", "temporal", "out_of_corpus", "ambiguous"}.issubset(query_types))

    def test_temporal_dataset_structure(self):
        self.assertTrue(self.temporal_path.exists())
        with open(self.temporal_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        self.assertGreater(len(items), 0)
        for t in items:
            self.assertIn("id", t)
            self.assertIn("query", t)
            evals = t.get("evaluations", [])
            self.assertGreaterEqual(len(evals), 2, "Temporal cases must have at least 2 date checkpoints")

            for e in evals:
                datetime.strptime(e["as_of"], "%Y-%m-%d")
                self.assertIn("expected_instrument", e)

    def test_adversarial_dataset_structure(self):
        self.assertTrue(self.adversarial_path.exists())
        with open(self.adversarial_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        self.assertGreater(len(items), 0)
        for adv in items:
            self.assertIn("id", adv)
            self.assertIn("query", adv)
            self.assertIn("expected_behavior", adv)
            self.assertIn("requires_abstention", adv)


if __name__ == "__main__":
    unittest.main()
