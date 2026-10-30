"""DPDP Act 2023 compliance telemetry, automated PII scrubbing, and rolling TTL audit log.

Guarantees 30-day retention policies, automated PII redaction (PAN, GSTIN, Aadhaar, Phone, Email),
and immediate session-level right-to-erasure (Spec Section 4).
"""

import re
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4


class PIIScrubber:
    """Scrubs sensitive Personally Identifiable Information (PII) from queries and logs."""

    # Official regulatory pattern expressions
    GSTIN_PATTERN = re.compile(
        r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b",
        re.IGNORECASE,
    )
    PAN_PATTERN = re.compile(
        r"\b[A-Z]{5}\d{4}[A-Z]{1}\b",
        re.IGNORECASE,
    )
    AADHAAR_PATTERN = re.compile(
        r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b",
    )
    PHONE_PATTERN = re.compile(
        r"\b(?:\+91|91|0)?[6-9]\d{9}\b",
    )
    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    )

    @classmethod
    def scrub_pii(cls, text: str) -> str:
        """Redacts sensitive PII from text before logging or trace generation."""
        if not text:
            return ""

        scrubbed = text
        # 1. GSTIN (15 chars) before PAN (10 chars) to prevent partial matching
        scrubbed = cls.GSTIN_PATTERN.sub("[REDACTED_GSTIN]", scrubbed)
        # 2. PAN
        scrubbed = cls.PAN_PATTERN.sub("[REDACTED_PAN]", scrubbed)
        # 3. Aadhaar
        scrubbed = cls.AADHAAR_PATTERN.sub("[REDACTED_AADHAAR]", scrubbed)
        # 4. Indian Mobile Phone
        scrubbed = cls.PHONE_PATTERN.sub("[REDACTED_PHONE]", scrubbed)
        # 5. Email
        scrubbed = cls.EMAIL_PATTERN.sub("[REDACTED_EMAIL]", scrubbed)

        return scrubbed

    @classmethod
    def contains_pii(cls, text: str) -> bool:
        """Checks if text contains any recognized PII."""
        if not text:
            return False
        return any(
            pat.search(text) is not None
            for pat in (
                cls.GSTIN_PATTERN,
                cls.PAN_PATTERN,
                cls.AADHAAR_PATTERN,
                cls.PHONE_PATTERN,
                cls.EMAIL_PATTERN,
            )
        )


class AuditLogStore:
    """DPDP-compliant audit log store with 30-day rolling TTL and session deletion."""

    def __init__(self, ttl_days: int = 30):
        self.ttl_days = ttl_days
        self.logs: list[dict[str, Any]] = []

    def record_query(
        self,
        query: str,
        as_of: str,
        language: str,
        session_id: UUID | None = None,
        answer_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Scrubs PII and records an audit trace."""
        scrubbed_query = PIIScrubber.scrub_pii(query)
        entry = {
            "id": uuid4(),
            "session_id": session_id or uuid4(),
            "query_scrubbed": scrubbed_query,
            "as_of": as_of,
            "language": language,
            "answer_id": answer_id,
            "created_at": datetime.utcnow(),
        }
        self.logs.append(entry)
        return entry

    def purge_expired_logs(self) -> int:
        """Deletes all audit records older than the DPDP 30-day retention period."""
        cutoff = datetime.utcnow() - timedelta(days=self.ttl_days)
        initial_count = len(self.logs)
        self.logs = [log for log in self.logs if log["created_at"] >= cutoff]
        purged = initial_count - len(self.logs)
        return purged

    def delete_session(self, session_id: UUID) -> int:
        """Implements DPDP Section 12 (Right to Erasure) by purging all traces for a session."""
        initial_count = len(self.logs)
        self.logs = [log for log in self.logs if log["session_id"] != session_id]
        deleted = initial_count - len(self.logs)
        return deleted

    def count(self) -> int:
        return len(self.logs)
