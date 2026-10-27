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

        # 2. Map known glossary variants
        words = re.findall(r"[\w%]+|[^\w\s]", cleaned, re.UNICODE)
        normalized_tokens: list[str] = []
        for word in words:
            lower_word = word.lower()
            if lower_word in self.glossary_map:
                normalized_tokens.append(self.glossary_map[lower_word])
            else:
                normalized_tokens.append(word)

        normalized_query = " ".join(normalized_tokens)
        # Clean extra spaces around punctuation
        normalized_query = re.sub(r"\s+([?.!,])", r"\1", normalized_query)
        return normalized_query
