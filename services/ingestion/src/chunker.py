"""Structure-aware chunker for regulatory instruments.

Splits legal documents into clause-level chunks (target 200-500 tokens)
while prepending contextual metadata headers and preserving table structures.
"""

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from uuid import UUID, uuid4


@dataclass
class StatutoryChunk:
    id: UUID
    instrument_id: UUID
    authority: str
    instrument_title: str
    section_path: str
    text: str
    context_header: str
    chunk_type: str  # 'clause' | 'table_row' | 'definition' | 'proviso'
    effective_from: date
    effective_to: date | None
    jurisdiction: str
    subjects: list[str]
    language: str
    token_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


class StructureAwareChunker:
    """Legal document chunker preserving statutory boundaries and table integrity."""

    # Heuristic for token count (approx 4 chars per token for English/Indic transliterated text)
    APPROX_CHARS_PER_TOKEN = 4

    def __init__(self, target_min_tokens: int = 50, target_max_tokens: int = 500):
        self.target_min_tokens = target_min_tokens
        self.target_max_tokens = target_max_tokens

    def build_context_header(
        self,
        authority: str,
        instrument_title: str,
        section_path: str,
        subjects: list[str],
    ) -> str:
        """Constructs canonical contextual header prepended to chunks."""
        subjects_str = ", ".join(subjects) if subjects else "general"
        return f"[Authority: {authority} | Instrument: {instrument_title} | Section: {section_path} | Subject: {subjects_str}]"

    def estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // self.APPROX_CHARS_PER_TOKEN)

    def chunk_clauses(
        self,
        instrument_id: UUID,
        authority: str,
        instrument_title: str,
        clauses: list[dict[str, Any]],
        effective_from: date,
        effective_to: date | None,
        jurisdiction: str,
        subjects: list[str],
        language: str = "en",
    ) -> list[StatutoryChunk]:
        """Splits an instrument's clauses into indexed statutory chunks."""
        chunks: list[StatutoryChunk] = []

        for item in clauses:
            path = item.get("path", "General")
            chunk_type = item.get("type", "clause")
            custom_effective_from = item.get("effective_from", effective_from)
            custom_effective_to = item.get("effective_to", effective_to)

            # If table, process row by row preserving table headers
            if chunk_type == "table":
                headers = item.get("headers", [])
                rows = item.get("rows", [])
                for row_idx, row in enumerate(rows):
                    row_text = " | ".join(f"{h}: {v}" for h, v in zip(headers, row))
                    header_str = self.build_context_header(
                        authority, instrument_title, f"{path} > Row {row_idx + 1}", subjects
                    )
                    chunks.append(
                        StatutoryChunk(
                            id=uuid4(),
                            instrument_id=instrument_id,
                            authority=authority,
                            instrument_title=instrument_title,
                            section_path=f"{path} > Row {row_idx + 1}",
                            text=row_text,
                            context_header=header_str,
                            chunk_type="table_row",
                            effective_from=custom_effective_from,
                            effective_to=custom_effective_to,
                            jurisdiction=jurisdiction,
                            subjects=subjects,
                            language=language,
                            token_count=self.estimate_tokens(row_text),
                        )
                    )
                continue

            text = item.get("text", "").strip()
            if not text:
                continue

            # Check if clause needs sub-chunking (e.g. long provisions)
            token_est = self.estimate_tokens(text)
            if token_est <= self.target_max_tokens:
                header_str = self.build_context_header(authority, instrument_title, path, subjects)
                chunks.append(
                    StatutoryChunk(
                        id=uuid4(),
                        instrument_id=instrument_id,
                        authority=authority,
                        instrument_title=instrument_title,
                        section_path=path,
                        text=text,
                        context_header=header_str,
                        chunk_type=chunk_type,
                        effective_from=custom_effective_from,
                        effective_to=custom_effective_to,
                        jurisdiction=jurisdiction,
                        subjects=subjects,
                        language=language,
                        token_count=token_est,
                    )
                )
            else:
                # Sub-chunk along provisos or numbered paragraphs without breaking mid-sentence
                sentences = re.split(r"(?<=[.!?])\s+", text)
                current_chunk: list[str] = []
                current_len = 0
                sub_idx = 1

                for sentence in sentences:
                    sent_tokens = self.estimate_tokens(sentence)
                    if current_len + sent_tokens > self.target_max_tokens and current_chunk:
                        chunk_body = " ".join(current_chunk)
                        sub_path = f"{path} (Part {sub_idx})"
                        header_str = self.build_context_header(authority, instrument_title, sub_path, subjects)
                        chunks.append(
                            StatutoryChunk(
                                id=uuid4(),
                                instrument_id=instrument_id,
                                authority=authority,
                                instrument_title=instrument_title,
                                section_path=sub_path,
                                text=chunk_body,
                                context_header=header_str,
                                chunk_type=chunk_type,
                                effective_from=custom_effective_from,
                                effective_to=custom_effective_to,
                                jurisdiction=jurisdiction,
                                subjects=subjects,
                                language=language,
                                token_count=current_len,
                            )
                        )
                        sub_idx += 1
                        current_chunk = [sentence]
                        current_len = sent_tokens
                    else:
                        current_chunk.append(sentence)
                        current_len += sent_tokens

                if current_chunk:
                    chunk_body = " ".join(current_chunk)
                    sub_path = f"{path} (Part {sub_idx})" if sub_idx > 1 else path
                    header_str = self.build_context_header(authority, instrument_title, sub_path, subjects)
                    chunks.append(
                        StatutoryChunk(
                            id=uuid4(),
                            instrument_id=instrument_id,
                            authority=authority,
                            instrument_title=instrument_title,
                            section_path=sub_path,
                            text=chunk_body,
                            context_header=header_str,
                            chunk_type=chunk_type,
                            effective_from=custom_effective_from,
                            effective_to=custom_effective_to,
                            jurisdiction=jurisdiction,
                            subjects=subjects,
                            language=language,
                            token_count=current_len,
                        )
                    )

        return chunks
