"""Unit tests validating static fixtures, datasets, and seed consistency."""

import json
import re
import unittest
from datetime import datetime
from pathlib import Path


class TestFixturesAndSeeds(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.instruments_path = self.base_dir / "data" / "fixtures" / "core_instruments.json"
        self.glossary_path = self.base_dir / "data" / "fixtures" / "glossary_seed.json"
        self.sql_schema_path = self.base_dir / "db" / "migrations" / "001_initial_schema.sql"
        self.sql_seed_path = self.base_dir / "db" / "seeds" / "002_seed_glossary.sql"

    def test_core_instruments_fixture(self):
        self.assertTrue(self.instruments_path.exists(), "core_instruments.json must exist")
        with open(self.instruments_path, "r", encoding="utf-8") as f:
            instruments = json.load(f)

        # 1. Verify exactly 40 core instruments
        self.assertEqual(len(instruments), 40, f"Expected 40 core instruments, found {len(instruments)}")

        codes = {inst["code"] for inst in instruments}
        self.assertEqual(len(codes), 40, "All instrument codes must be unique")

        required_fields = {
            "code", "authority", "type", "number", "title",
            "jurisdiction", "issued_on", "effective_from", "language",
            "source_url", "subjects"
        }

        for inst in instruments:
            for field in required_fields:
                self.assertIn(field, inst, f"Instrument {inst.get('code')} missing field {field}")

            # Validate date formats
            datetime.strptime(inst["issued_on"], "%Y-%m-%d")
            datetime.strptime(inst["effective_from"], "%Y-%m-%d")

            # Validate jurisdiction
            self.assertIn(inst["jurisdiction"], ["central", "gujarat"])

            # Validate language array
            self.assertIsInstance(inst["language"], list)
            self.assertGreater(len(inst["language"]), 0)

            # Validate subjects array
            self.assertIsInstance(inst["subjects"], list)
            self.assertGreater(len(inst["subjects"]), 0)

            # Validate relation targets if present
            if "relation" in inst:
                rel = inst["relation"]
                self.assertIn(rel["type"], ["amends", "supersedes", "clarifies", "rescinds"])
                self.assertIn(
                    rel["target"],
                    codes,
                    f"Relation target {rel['target']} in {inst['code']} not found in catalog",
                )

    def test_glossary_fixture(self):
        self.assertTrue(self.glossary_path.exists(), "glossary_seed.json must exist")
        with open(self.glossary_path, "r", encoding="utf-8") as f:
            glossary = json.load(f)

        self.assertGreater(len(glossary), 10, "Glossary seed must contain terms")

        for item in glossary:
            self.assertIn("canonical_term", item)
            self.assertIn("variants", item)
            self.assertIsInstance(item["variants"], list)
            self.assertGreater(len(item["variants"]), 0)
            self.assertIn("language", item)
            self.assertIn("definition", item)

    def test_sql_files_exist_and_non_empty(self):
        self.assertTrue(self.sql_schema_path.exists())
        self.assertTrue(self.sql_seed_path.exists())

        schema_text = self.sql_schema_path.read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE IF NOT EXISTS instruments", schema_text)
        self.assertIn("CREATE TABLE IF NOT EXISTS chunks", schema_text)
        self.assertIn("CREATE TABLE IF NOT EXISTS glossary", schema_text)

        seed_text = self.sql_seed_path.read_text(encoding="utf-8")
        self.assertIn("INSERT INTO glossary", seed_text)


if __name__ == "__main__":
    unittest.main()
