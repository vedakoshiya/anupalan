"""Statutory metadata extractor for legal instruments.

Extracts issuing authority, instrument type, notification numbers,
effective dates, jurisdiction, subject classification, and amendment relations (FR-005).
"""

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from services.ingestion.src.models import ParsedMetadata


class MetadataExtractor:
    """Regex and pattern-based extractor for Indian regulatory notifications and circulars."""

    AUTHORITY_PATTERNS = [
        (r"Central Board of Indirect Taxes and Customs|CBIC", "CBIC"),
        (r"Goods and Services Tax Council|GST Council", "GST Council"),
        (r"Ministry of Micro,\s*Small and Medium Enterprises|Ministry of MSME", "Ministry of MSME"),
        (r"Ministry of Finance", "Ministry of Finance"),
        (r"Government of Gujarat|Gujarat State|Commercial Tax Gujarat|SGST", "Government of Gujarat"),
    ]

    TYPE_PATTERNS = [
        (r"Notification\s+No\.?", "notification"),
        (r"Circular\s+No\.?", "circular"),
        (r"Order\s+No\.?", "order"),
        (r"\bAct\b", "act"),
        (r"\bRules?\b", "rule"),
        (r"Resolution\s+No\.?", "scheme"),
    ]

    DATE_PATTERN = re.compile(
        r"(?:dated\s+(?:the\s+)?|dated\s*:?\s*)(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4}|\d{4}-\d{2}-\d{2})",
        re.IGNORECASE,
    )

    RELATION_PATTERNS = [
        (r"amends?\s+(?:Notification|Circular)\s+No\.?\s*([0-9\/\-]+[A-Za-z\(\)\s\-]*)", "amends"),
        (r"supersedes?\s+(?:Notification|Circular)\s+No\.?\s*([0-9\/\-]+[A-Za-z\(\)\s\-]*)", "supersedes"),
        (r"in\s+clarification\s+of\s+(?:Notification|Circular)\s+No\.?\s*([0-9\/\-]+[A-Za-z\(\)\s\-]*)", "clarifies"),
        (r"rescinds?\s+(?:Notification|Circular)\s+No\.?\s*([0-9\/\-]+[A-Za-z\(\)\s\-]*)", "rescinds"),
    ]

    SUBJECT_KEYWORDS = {
        "job_work": ["job work", "jobwork", "textile job", "processing of goods", "section 143"],
        "composition": ["composition levy", "composition scheme", "section 10", "turnover limit"],
        "itc": ["input tax credit", "itc", "gstr-2b", "gstr-3b", "blocked credit", "section 16", "section 17(5)"],
        "e_way_bill": ["e-way bill", "eway bill", "rule 138", "consignment note"],
        "e_invoicing": ["e-invoicing", "einvoicing", "electronic invoice", "irp"],
        "delayed_payment": ["msmed act", "section 15", "section 16", "45 days", "section 43b(h)"],
        "gujarat_msme": ["gujarat industrial policy", "capital subsidy", "interest subsidy", "taluka category"],
    }

    def parse_date(self, date_str: str) -> date | None:
        """Parses common Indian gazette date formats."""
        clean_str = re.sub(r"(\d+)(?:st|nd|rd|th)", r"\1", date_str).replace(",", "").strip()
        for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(clean_str, fmt).date()
            except ValueError:
                continue
        return None

    def extract_metadata(
        self,
        text: str,
        filename: str = "",
        fallback_date: date | None = None,
    ) -> ParsedMetadata:
        """Extracts all statutory metadata fields from document text and filename."""
        sample = text[:3000]
        today = fallback_date or date.today()

        # 1. Authority
        authority = "CBIC"
        for pattern, auth_name in self.AUTHORITY_PATTERNS:
            if re.search(pattern, sample, re.IGNORECASE):
                authority = auth_name
                break

        # 2. Type
        inst_type = "notification"
        for pattern, t_name in self.TYPE_PATTERNS:
            if re.search(pattern, sample, re.IGNORECASE) or re.search(pattern, filename, re.IGNORECASE):
                inst_type = t_name
                break

        # 3. Notification Number
        num_match = re.search(r"(?:No\.?\s*)([0-9]{1,4}\/[0-9]{2,4}(?:-[A-Za-z\s]+(?:\([A-Za-z\s]+\))?)?)", sample)
        number = num_match.group(1).strip() if num_match else Path(filename).stem
        # Clean up any trailing words like New Delhi if whitespace was captured
        number = re.sub(r"\s+(?:New\s+Delhi|dated|dated:).*$", "", number, flags=re.IGNORECASE).strip()

        # 4. Dates
        date_match = self.DATE_PATTERN.search(sample)
        parsed_date = self.parse_date(date_match.group(1)) if date_match else None
        issued_on = parsed_date or today
        effective_from = issued_on

        # 5. Jurisdiction
        jurisdiction = "gujarat" if "Gujarat" in authority or "gujarat" in text.lower()[:1000] else "central"

        # 6. Title
        title_lines = [l.strip() for l in sample.splitlines() if len(l.strip()) > 15]
        title = title_lines[0] if title_lines else f"{inst_type.capitalize()} {number}"

        # 7. Subjects
        subjects: list[str] = []
        lower_text = text.lower()
        for sub_tag, keywords in self.SUBJECT_KEYWORDS.items():
            if any(k in lower_text for k in keywords):
                subjects.append(sub_tag)
        if not subjects:
            subjects = ["general_compliance"]

        # 8. Statutory Relations
        relations: list[dict[str, Any]] = []
        for rel_pattern, rel_type in self.RELATION_PATTERNS:
            for match in re.finditer(rel_pattern, text, re.IGNORECASE):
                target_num = match.group(1).strip()
                relations.append({
                    "relation": rel_type,
                    "target_number": target_num,
                    "effective_from": effective_from,
                })

        return ParsedMetadata(
            authority=authority,
            instrument_type=inst_type,
            number=number,
            title=title,
            jurisdiction=jurisdiction,
            issued_on=issued_on,
            effective_from=effective_from,
            subjects=subjects,
            relations=relations,
        )
