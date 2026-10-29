"""Domain models and data schemas for the ingestion pipeline.

Defines schemas for raw documents, layout-parsed sections, tables,
quality metrics, and pipeline execution results.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    NATIVE_PDF = "native_pdf"
    SCANNED_PDF = "scanned_pdf"
    HTML = "html"
    DOCX = "docx"
    UNKNOWN = "unknown"


class IngestionStatus(str, Enum):
    INGESTED = "ingested"
    SKIPPED_DUPLICATE = "skipped_duplicate"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class PageQualityMetric(BaseModel):
    """Quality and OCR confidence evaluation for an individual page."""

    page_number: int = Field(..., ge=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    word_count: int = Field(default=0, ge=0)
    is_scanned: bool = Field(default=False)
    needs_review: bool = Field(default=False)
    review_reason: str | None = None


class QualityReport(BaseModel):
    """Document-level ingestion and OCR quality assessment."""

    overall_score: float = Field(..., ge=0.0, le=1.0)
    page_metrics: list[PageQualityMetric] = Field(default_factory=list)
    flagged_pages: list[int] = Field(default_factory=list)
    requires_curator_review: bool = False


class ExtractedTable(BaseModel):
    """Structured tabular data extracted from official instruments."""

    caption: str | None = None
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    page_number: int = 1


class ExtractedClause(BaseModel):
    """Individual statutory clause or proviso with contextual path."""

    path: str = Field(..., description="e.g. 'Para 3 > Clause (b)'")
    text: str = Field(..., min_length=1)
    clause_type: str = Field(default="clause", description="'clause' | 'proviso' | 'definition'")
    page_number: int = 1


class ExtractedSection(BaseModel):
    """Hierarchical section containing clauses and tables."""

    path: str
    heading: str | None = None
    clauses: list[ExtractedClause] = Field(default_factory=list)
    tables: list[ExtractedTable] = Field(default_factory=list)
    page_from: int = 1
    page_to: int = 1


class RawDocument(BaseModel):
    """Raw artifact loaded into the pipeline with cryptographic SHA-256 hash."""

    id: UUID = Field(default_factory=uuid4)
    filename: str
    content_hash: str = Field(..., description="SHA-256 cryptographic checksum")
    mime_type: str
    byte_size: int
    storage_uri: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ParsedMetadata(BaseModel):
    """Statutory metadata extracted from an official instrument."""

    authority: str = Field(..., description="CBIC, GST Council, Gujarat Dept, etc.")
    instrument_type: str = Field(..., description="notification, circular, act, etc.")
    number: str = Field(..., description="Official number/code")
    title: str = Field(...)
    jurisdiction: str = Field(default="central", description="'central' | 'gujarat'")
    issued_on: date
    effective_from: date
    effective_to: date | None = None
    languages: list[str] = Field(default_factory=lambda: ["en"])
    subjects: list[str] = Field(default_factory=list)
    relations: list[dict[str, Any]] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    """Fully parsed and structured instrument ready for chunking and version graph."""

    raw_document: RawDocument
    doc_type: DocumentType
    metadata: ParsedMetadata
    sections: list[ExtractedSection] = Field(default_factory=list)
    quality_report: QualityReport


class IngestionResult(BaseModel):
    """Execution output from an ingestion pipeline run."""

    document_id: UUID
    filename: str
    content_hash: str
    status: IngestionStatus
    chunks_created: int = 0
    quality_score: float = 1.0
    flagged_pages: list[int] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    processed_at: datetime = Field(default_factory=datetime.utcnow)
