"""Query normalization, vernacular numeral resolution, and transliteration handling."""

import json
import re
from pathlib import Path


class TransliterationNormalizer:
    """Normalizes colloquial Indic spelling variants, Gujlish terms, and vernacular numbers."""

    # Explicit vernacular number mappings to standardized digits
    VERNACULAR_NUMBERS = {
        r"\b(dedh|dhed|dodh)\s*lakh\b": "150000",
        r"\b(sava)\s*lakh\b": "125000",
        r"\b(paune|pauna)\s*lakh\b": "75000",
        r"\b(chalis|chaalis|40)\s*lakh\b": "4000000",
        r"\b(pachas|50)\s*lakh\b": "5000000",
        r"\b(bees|vis|20)\s*lakh\b": "2000000",
        r"\b(das|10)\s*lakh\b": "1000000",
        r"\b(dedh|dhed)\s*crore\b": "15000000",
        r"\b(ek|1)\s*crore\b": "10000000",
        r"\b(paanch|5)\s*crore\b": "50000000",
        r"\b(paanch|5)\s*(takka|taka|percent|%)\b": "5%",
        r"\b(baar|12)\s*(takka|taka|percent|%)\b": "12%",
        r"\b(adhaar|adhar|18)\s*(takka|taka|percent|%)\b": "18%",
        r"\b(athavis|28)\s*(takka|taka|percent|%)\b": "28%",
    }

    def __init__(self, glossary_fixture_path: Path | None = None):
        self.glossary_map: dict[str, str] = {}
        self.sorted_variants: list[str] = []
        if glossary_fixture_path is None:
            # Default to canonical data fixture path if present
            default_path = Path(__file__).resolve().parents[4] / "data" / "fixtures" / "glossary_seed.json"
            if default_path.exists():
                glossary_fixture_path = default_path

        if glossary_fixture_path and glossary_fixture_path.exists():
            self._load_glossary(glossary_fixture_path)

    def _load_glossary(self, path: Path) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for entry in data:
                    canonical = entry["canonical_term"]
                    for variant in entry.get("variants", []):
                        self.glossary_map[variant.lower().strip()] = canonical
            self.sorted_variants = sorted(self.glossary_map.keys(), key=len, reverse=True)
        except Exception:
            pass

    def normalize(self, query: str) -> str:
        """Normalizes numbers, spaces, and canonical regulatory terms in query."""
        if not query:
            return ""

        cleaned = query.strip()

        # 1. Resolve vernacular numerals
        for pattern, replacement in self.VERNACULAR_NUMBERS.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        # 2. Map known glossary variants (longest phrases first)
        for variant in self.sorted_variants:
            if variant in cleaned.lower():
                # Word boundary match supporting Unicode scripts
                pat = re.compile(rf"(?<![\w\u0A80-\u0AFF\u0900-\u097F]){re.escape(variant)}(?![\w\u0A80-\u0AFF\u0900-\u097F])", re.IGNORECASE | re.UNICODE)
                cleaned = pat.sub(self.glossary_map[variant], cleaned)

        # 3. Clean spaces around punctuation
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = re.sub(r"\s+([?.!,])", r"\1", cleaned)
        return cleaned
