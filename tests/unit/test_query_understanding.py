"""Unit tests for query understanding, language detection, and normalization."""

import unittest
from pathlib import Path

from packages.query.src.query.language_detector import IndicLanguageDetector, ScriptType
from packages.query.src.query.transliteration_normalizer import TransliterationNormalizer


class TestQueryUnderstanding(unittest.TestCase):
    def setUp(self):
        self.detector = IndicLanguageDetector()
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.fixture_path = base_dir / "data" / "fixtures" / "glossary_seed.json"
        self.normalizer = TransliterationNormalizer(glossary_fixture_path=self.fixture_path)

    def test_language_detection_native_gujarati(self):
        res = self.detector.detect("જોબ વર્ક પર જીએસટી કેટલો લાગે?")
        self.assertEqual(res.primary_language, "gu")
        self.assertEqual(res.script, ScriptType.GUJARATI)
        self.assertFalse(res.is_transliterated)

    def test_language_detection_native_hindi(self):
        res = self.detector.detect("जॉब वर्क पर जीएसटी कितना लगता है?")
        self.assertEqual(res.primary_language, "hi")
        self.assertEqual(res.script, ScriptType.DEVANAGARI)
        self.assertFalse(res.is_transliterated)

    def test_language_detection_gujlish(self):
        res = self.detector.detect("Job work par GST kevi rite lage?")
        self.assertEqual(res.primary_language, "gu")
        self.assertEqual(res.script, ScriptType.LATIN)
        self.assertTrue(res.is_transliterated)

    def test_language_detection_english(self):
        res = self.detector.detect("What is the GST rate applicable for textile job work?")
        self.assertEqual(res.primary_language, "en")
        self.assertEqual(res.script, ScriptType.LATIN)
        self.assertFalse(res.is_transliterated)

    def test_vernacular_number_normalization(self):
        query = "Mara pase dedh lakh turnover che, mane shu karvu pade?"
        normalized = self.normalizer.normalize(query)
        self.assertIn("150000", normalized)

        query_comp = "Mara mate dedh crore limit lagse?"
        normalized_comp = self.normalizer.normalize(query_comp)
        self.assertIn("15000000", normalized_comp)

        query_tax = "Textile par paanch takka lage?"
        normalized_tax = self.normalizer.normalize(query_tax)
        self.assertIn("5%", normalized_tax)


if __name__ == "__main__":
    unittest.main()
