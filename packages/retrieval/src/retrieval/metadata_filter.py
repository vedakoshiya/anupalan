"""Metadata and temporal filtering engine for statutory retrieval.

Enforces point-in-time statutory validity (as_of) and jurisdictional applicability
(Central vs Gujarat State) with both in-memory and SQL compilation modes.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from services.ingestion.src.chunker import StatutoryChunk


@dataclass
class FilterCriteria:
    """Filter specifications for compliance retrieval queries."""

    as_of: date
    jurisdiction: str | None = None
    subjects: list[str] | None = None
    authorities: list[str] | None = None
    chunk_types: list[str] | None = None
    min_ocr_quality: float = 0.0


class MetadataFilter:
    """Applies statutory validity, jurisdictional rules, and metadata filters."""

    def __init__(self, criteria: FilterCriteria):
        self.criteria = criteria

    def matches(self, chunk: StatutoryChunk) -> bool:
        """Evaluates whether a chunk meets all statutory filter criteria."""
        # 1. Temporal Validity: effective_from <= as_of < effective_to (if effective_to exists)
        if chunk.effective_from and chunk.effective_from > self.criteria.as_of:
            return False

        if chunk.effective_to and chunk.effective_to <= self.criteria.as_of:
            return False

        # 2. Jurisdiction: Central circulars apply nationally; state circulars apply to specified state
        if self.criteria.jurisdiction:
            target = self.criteria.jurisdiction.lower().strip()
            chunk_jur = chunk.jurisdiction.lower().strip()
            if chunk_jur != target and chunk_jur != "central":
                return False

        # 3. Subject Tag Matching (if specified, must overlap at least one subject)
        if self.criteria.subjects:
            target_subjects = {s.lower() for s in self.criteria.subjects}
            chunk_subjects = {s.lower() for s in chunk.subjects}
            if not target_subjects.intersection(chunk_subjects):
                return False

        # 4. Authority Matching (if specified)
        if self.criteria.authorities:
            target_auths = {a.lower() for a in self.criteria.authorities}
            if chunk.authority.lower() not in target_auths:
                return False

        # 5. Chunk Type Matching
        if self.criteria.chunk_types:
            if chunk.chunk_type not in self.criteria.chunk_types:
                return False

        return True

    def filter_chunks(self, chunks: list[StatutoryChunk]) -> list[StatutoryChunk]:
        """Filters an in-memory list of statutory chunks."""
        return [c for c in chunks if self.matches(c)]

    def to_sql_where(self) -> tuple[str, dict[str, Any]]:
        """Generates parameterized SQL WHERE clause and parameter dictionary.

        Compatible with PostgreSQL 16 schema in db/migrations/001_initial_schema.sql.
        """
        clauses = []
        params: dict[str, Any] = {"as_of": self.criteria.as_of}

        # Temporal filter
        clauses.append("(effective_from <= :as_of AND (effective_to IS NULL OR effective_to > :as_of))")

        # Jurisdiction filter
        if self.criteria.jurisdiction:
            params["jurisdiction"] = self.criteria.jurisdiction
            clauses.append("(jurisdiction = :jurisdiction OR jurisdiction = 'central')")

        # Authorities filter
        if self.criteria.authorities:
            params["authorities"] = tuple(self.criteria.authorities)
            clauses.append("authority IN :authorities")

        # Chunk types filter
        if self.criteria.chunk_types:
            params["chunk_types"] = tuple(self.criteria.chunk_types)
            clauses.append("chunk_type IN :chunk_types")

        # Subjects array overlap (PostgreSQL GIN array operator &&)
        if self.criteria.subjects:
            params["subjects"] = self.criteria.subjects
            clauses.append("subjects && :subjects")

        return " AND ".join(clauses), params
