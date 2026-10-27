"""Structured response and request schemas for Anupalan.

Enforces citation grounding, structured entailment, and DPDP-compliant payloads.
"""

from datetime import date
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Statutory citation grounding a specific claim."""

    chunk_id: UUID = Field(..., description="Unique UUID of the referenced statutory chunk")
    instrument: str = Field(..., description="Official title/number of the notification or act")
    clause: str = Field(..., description="Specific clause, proviso, or paragraph (e.g. 'Para 3(b)')")
    effective_from: date = Field(..., description="Date on which this provision became active")


class Claim(BaseModel):
    """An individual factual claim supported by citations."""

    text: str = Field(..., description="A single factual statement answering the query")
    citations: list[Citation] = Field(
        default_factory=list,
        description="Statutory citations verifying this statement. Must NOT be empty for non-disclaimer claims.",
    )
    confidence: Annotated[float, Field(ge=0.0, le=1.0, description="Entailment confidence score")]


class AskRequest(BaseModel):
    """Input payload for POST /v1/ask."""

    query: str = Field(..., min_length=2, max_length=1000, description="Natural language question")
    language: str | None = Field(
        default=None,
        description="ISO 639-1 code ('gu', 'hi', 'en'). If omitted, language is detected dynamically.",
    )
    as_of: date = Field(
        default_factory=date.today,
        description="Temporal reference date for rule validity. Defaults to today.",
    )
    session_id: UUID | None = Field(
        default_factory=uuid4,
        description="Optional session tracking ID for multi-turn clarifications.",
    )


class AskResponse(BaseModel):
    """Structured response contract matching Section 8.2 of specification."""

    answer_id: UUID = Field(default_factory=uuid4, description="Audit trace identifier for this answer")
    language: str = Field(..., description="Response language ('gu', 'hi', 'en')")
    abstained: bool = Field(
        default=False,
        description="True if confidence was too low or query fell outside compliance scope",
    )
    summary: str = Field(..., description="High-level plain language synthesis in the user's language")
    claims: list[Claim] = Field(
        default_factory=list,
        description="Granular factual propositions, each with statutory citations",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Actionable steps for the MSME owner or accountant",
    )
    as_of: date = Field(..., description="Temporal validity date evaluated")
    corpus_updated: date = Field(..., description="Latest update date of the indexed regulatory corpus")
    disclaimer: str = Field(
        default="Informational use only. Consult a registered CA for tax filing.",
        description="Statutory disclaimer for MSME compliance advice",
    )


class FeedbackRequest(BaseModel):
    """Payload for POST /v1/feedback."""

    answer_id: UUID = Field(..., description="UUID of the answer being evaluated")
    rating: int = Field(..., ge=-1, le=1, description="1 for positive (thumbs up), -1 for negative (thumbs down)")
    reason_code: str | None = Field(
        default=None,
        description="Classification of issue (e.g. 'incorrect_rate', 'outdated_rule', 'missing_clause')",
    )
    comment: str | None = Field(
        default=None,
        max_length=500,
        description="Optional user comments or correction notes",
    )


class InstrumentRelation(BaseModel):
    """Directed edge in the statutory amendment graph."""

    target_number: str = Field(..., description="Number of related instrument")
    relation: str = Field(..., description="'amends' | 'supersedes' | 'clarifies' | 'rescinds'")
    effective_from: date | None = None
    scope: str | None = None


class InstrumentDetail(BaseModel):
    """Metadata and version timeline for an official regulatory instrument."""

    id: UUID
    authority: str
    type: str
    number: str
    title: str
    jurisdiction: str
    issued_on: date
    effective_from: date | None = None
    effective_to: date | None = None
    language: list[str]
    source_url: str
    relations: list[InstrumentRelation] = Field(default_factory=list)
