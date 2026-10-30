"""Advanced numeric, rate, and vernacular monetary guardrail for compliance generation.

Validates that all numbers, GST rates, monetary limits (Lakhs, Crores), and dates in
generated claims strictly exist in cited source passages (Spec Section 7.2).
"""

import re
from dataclasses import dataclass
from typing import Any

from services.ingestion.src.chunker import StatutoryChunk


@dataclass
class NumericVerificationResult:
    """Detailed diagnostic outcome of numeric guardrail validation."""

    is_valid: bool
    claim_numbers: set[str]
    source_numbers: set[str]
    unsupported_numbers: list[str]
    explanation: str


class AdvancedNumericGuardrail:
    """Enforces zero numeric hallucination across rates, amounts, dates, and vernaculars."""

    # Vernacular and numeric normalization map
    EQUIVALENCE_GROUPS = {
        "4000000": {"4000000", "4000000.0", "40 lakh", "40lakh", "40lakhs", "40l", "chalis lakh", "ચાલીસ લાખ", "चालीस लाख"},
        "15000000": {"15000000", "15000000.0", "1.5 crore", "1.5crore", "1.5cr", "dedh crore", "દોઢ કરોડ", "डेढ़ करोड़"},
        "7500000": {"7500000", "7500000.0", "75 lakh", "75lakh", "75lakhs", "75l"},
        "50000000": {"50000000", "50000000.0", "5 crore", "5crore", "5cr", "પાંચ કરોડ", "पांच करोड़"},
        "5%": {"5%", "5 percent", "5percent", "5 takka", "પાંચ ટકા", "૫%", "૫ ટકા", "पांच प्रतिशत", "5 प्रतिशत"},
        "12%": {"12%", "12 percent", "12percent", "12 takka", "બાર ટકા", "૧૨%", "૧૨ ટકા", "बारह प्रतिशत", "12 प्रतिशत"},
        "18%": {"18%", "18 percent", "18percent", "18 takka", "અઢાર ટકા", "૧૮%", "૧૮ ટકા", "अठारह प्रतिशत", "18 प्रतिशत"},
        "28%": {"28%", "28 percent", "28percent", "28 takka", "અઠ્યાવીસ ટકા", "૨૮%", "૨૮ ટકા", "अट्ठाइस प्रतिशत"},
        "45": {"45", "45 days", "45days", "45 divas", "૪૫ દિવસ", "45 दिन"},
        "10": {"10", "10 workers", "10 karmachari", "૧૦ કામદારો", "10 कर्मचारी"},
        "3": {"3", "3 times", "three times", "ત્રણ ગણું", "तीन गुना"},
    }

    # Regex for raw number and percentage extraction
    RAW_NUMBER_REGEX = re.compile(
        r"\b\d+(?:,\d+)*(?:\.\d+)?%?|\b(?:\d+(?:\.\d+)?)\s*(?:lakh|crore|cr|percent|takka|days|workers)\b",
        re.IGNORECASE,
    )

    def __init__(self):
        # Reverse mapping from any variant to its canonical key
        self.variant_to_canonical: dict[str, str] = {}
        for canonical, variants in self.EQUIVALENCE_GROUPS.items():
            for v in variants:
                self.variant_to_canonical[v.lower().strip()] = canonical

    def _normalize_token(self, token: str) -> str:
        clean = token.lower().replace(",", "").strip()
        # Direct dictionary match
        if clean in self.variant_to_canonical:
            return self.variant_to_canonical[clean]

        # Numeric value normalization (strip trailing .0)
        try:
            if clean.endswith("%"):
                val = float(clean[:-1])
                return f"{int(val) if val.is_integer() else val}%"
            val = float(clean)
            return str(int(val)) if val.is_integer() else str(val)
        except ValueError:
            return clean

    def extract_numbers(self, text: str) -> set[str]:
        """Extracts and canonicalizes all numeric and monetary expressions."""
        matches = self.RAW_NUMBER_REGEX.findall(text)
        extracted: set[str] = set()

        for m in matches:
            norm = self._normalize_token(m)
            extracted.add(norm)

        # Also search for vernacular word representations in text with Indic-aware boundary
        lower_text = text.lower()
        for variant, canonical in self.variant_to_canonical.items():
            pattern = rf"(?<![\w\u0A80-\u0AFF\u0900-\u097F]){re.escape(variant)}(?![\w\u0A80-\u0AFF\u0900-\u097F])"
            if re.search(pattern, lower_text, re.UNICODE | re.IGNORECASE):
                extracted.add(canonical)

        return extracted

    def verify_claim(
        self,
        claim_text: str,
        cited_chunks: list[StatutoryChunk],
    ) -> NumericVerificationResult:
        """Verifies that every number in claim_text is attested in cited_chunks."""
        claim_numbers = self.extract_numbers(claim_text)
        if not claim_numbers:
            return NumericVerificationResult(
                is_valid=True,
                claim_numbers=set(),
                source_numbers=set(),
                unsupported_numbers=[],
                explanation="Claim contains zero numeric tokens.",
            )

        source_numbers: set[str] = set()
        for c in cited_chunks:
            source_numbers.update(self.extract_numbers(c.text))
            source_numbers.update(self.extract_numbers(c.context_header))
            if hasattr(c, "expanded_text") and c.expanded_text:
                source_numbers.update(self.extract_numbers(c.expanded_text))

        unsupported = [n for n in claim_numbers if n not in source_numbers]
        is_valid = len(unsupported) == 0

        explanation = (
            "All numeric tokens are rigorously attested in cited statutory sources."
            if is_valid
            else f"Numeric Guardrail Violation: Unsupported numbers detected: {unsupported}"
        )

        return NumericVerificationResult(
            is_valid=is_valid,
            claim_numbers=claim_numbers,
            source_numbers=source_numbers,
            unsupported_numbers=unsupported,
            explanation=explanation,
        )
