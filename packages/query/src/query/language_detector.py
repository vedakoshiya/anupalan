"""Language and script detection for English, Hindi, Gujarati, and Gujlish."""

import re
from dataclasses import dataclass
from enum import Enum


class ScriptType(str, Enum):
    GUJARATI = "gujarati"
    DEVANAGARI = "devanagari"
    LATIN = "latin"
    MIXED = "mixed"


@dataclass
class LanguageDetectionResult:
    primary_language: str       # 'gu', 'hi', 'en'
    script: ScriptType
    is_transliterated: bool    # True if Latin script is used for Gujarati (Gujlish) or Hindi (Hinglish)
    confidence: float


class IndicLanguageDetector:
    """Detects native Indic scripts as well as romanized Gujlish and Hinglish."""

    # Unicode ranges
    GUJARATI_PATTERN = re.compile(r"[\u0A80-\u0AFF]")
    DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")
    LATIN_PATTERN = re.compile(r"[a-zA-Z]")

    # High-signal Gujarati phonetic tokens in Latin script (Gujlish)
    GUJLISH_MARKERS = {
        "kevi", "rite", "ketlo", "ketla", "ketli", "mate", "che", "chhe", "nathi",
        "koni", "shu", "su", "karvu", "karvu", "pade", "male", "malshe", "par",
        "thi", "nathi", "tamare", "amare", "dhyan", "rakhvu", "bhav", "taka",
        "lakh", "crore", "divas", "chho", "chhe", "chhe?", "hajhi", "hati"
    }

    # High-signal Hindi phonetic tokens in Latin script (Hinglish)
    HINGLISH_MARKERS = {
        "kaise", "kya", "kitna", "kitne", "hoga", "hogi", "karna", "padega",
        "hai", "nahi", "milega", "chahiye", "kab", "kisko", "wala", "wali"
    }

    def detect(self, text: str) -> LanguageDetectionResult:
        if not text or not text.strip():
            return LanguageDetectionResult(
                primary_language="en",
                script=ScriptType.LATIN,
                is_transliterated=False,
                confidence=1.0,
            )

        guj_chars = len(self.GUJARATI_PATTERN.findall(text))
        dev_chars = len(self.DEVANAGARI_PATTERN.findall(text))
        latin_chars = len(self.LATIN_PATTERN.findall(text))
        total_indic = guj_chars + dev_chars

        # Native Gujarati script detected
        if guj_chars > 0 and guj_chars >= dev_chars and guj_chars >= latin_chars:
            return LanguageDetectionResult(
                primary_language="gu",
                script=ScriptType.GUJARATI,
                is_transliterated=False,
                confidence=min(1.0, guj_chars / max(1, len(text.replace(" ", "")))),
            )

        # Native Devanagari script detected
        if dev_chars > 0 and dev_chars >= guj_chars and dev_chars >= latin_chars:
            return LanguageDetectionResult(
                primary_language="hi",
                script=ScriptType.DEVANAGARI,
                is_transliterated=False,
                confidence=min(1.0, dev_chars / max(1, len(text.replace(" ", "")))),
            )

        # Text is primarily in Latin characters; inspect for Gujlish / Hinglish
        words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
        gujlish_matches = words.intersection(self.GUJLISH_MARKERS)
        hinglish_matches = words.intersection(self.HINGLISH_MARKERS)

        if len(gujlish_matches) > 0 and len(gujlish_matches) >= len(hinglish_matches):
            return LanguageDetectionResult(
                primary_language="gu",  # Target language is Gujarati
                script=ScriptType.LATIN,
                is_transliterated=True,
                confidence=0.85,
            )

        if len(hinglish_matches) > 0 and len(hinglish_matches) > len(gujlish_matches):
            return LanguageDetectionResult(
                primary_language="hi",  # Target language is Hindi
                script=ScriptType.LATIN,
                is_transliterated=True,
                confidence=0.85,
            )

        # Default to standard English
        return LanguageDetectionResult(
            primary_language="en",
            script=ScriptType.LATIN,
            is_transliterated=False,
            confidence=0.90,
        )
