"""Numeric guardrail for compliance generation.

Validates that all numbers, GST rates, monetary limits, and dates in generated claims
strictly exist within the cited source passages, eliminating numeric hallucinations.
"""

import re
from typing import Any
from services.ingestion.src.chunker import StatutoryChunk


class NumericGuardrailViolation(Exception):
    """Raised when an ungrounded or hallucinated number is detected."""
    pass


class NumericGuardrail:
    """Verifies that numbers, percentages, and amounts in claims are entailed by source chunks."""

    # Patterns matching numbers, percentages, currency, and dates
    NUMBER_PATTERN = re.compile(
        r"\b\d+(?:,\d+)*(?:\.\d+)?%?|\b(?:5%|12%|18%|28%)\b",
        re.IGNORECASE,
    )

    def extract_numbers(self, text: str) -> set[str]:
        """Extracts normalized numeric tokens from text."""
        raw_matches = self.NUMBER_PATTERN.findall(text)
        normalized: set[str] = set()
        for m in raw_matches:
            # Strip commas and standardize
            clean = m.replace(",", "").strip()
            if clean:
                normalized.add(clean)
        return normalized

    def verify_claim(self, claim_text: str, cited_chunks: list[StatutoryChunk]) -> tuple[bool, list[str]]:
        """Checks if all numbers in claim_text exist in any of the cited_chunks."""
        claim_numbers = self.extract_numbers(claim_text)
        if not claim_numbers:
            return True, []

        source_numbers: set[str] = set()
        for chunk in cited_chunks:
            source_numbers.update(self.extract_numbers(chunk.text))
            source_numbers.update(self.extract_numbers(chunk.context_header))

        unsupported_numbers: list[str] = []
        for num in claim_numbers:
            if num not in source_numbers:
                unsupported_numbers.append(num)

        is_valid = len(unsupported_numbers) == 0
        return is_valid, unsupported_numbers

    def validate_or_raise(self, claim_text: str, cited_chunks: list[StatutoryChunk]) -> None:
        """Validates numbers or raises NumericGuardrailViolation."""
        is_valid, unsupported = self.verify_claim(claim_text, cited_chunks)
        if not is_valid:
            raise NumericGuardrailViolation(
                f"Numeric Guardrail Triggered! Hallucinated or unsupported numbers: {unsupported}"
            )
