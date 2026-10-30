"""Parent clause context expansion engine.

Enriches granular sub-clauses, provisos, and table rows with their surrounding
statutory parent section text, ensuring LLM generation receives full legal definitions
while citations remain pinned to exact sub-clauses.
"""

from typing import Any, Iterable
from uuid import UUID

from services.ingestion.src.chunker import StatutoryChunk


class ParentClauseExpander:
    """Expands sub-clause and proviso chunks with parent section hierarchy."""

    def __init__(self, corpus_chunks: list[StatutoryChunk] | None = None):
        self.corpus_chunks = corpus_chunks or []
        self._index_by_instrument_and_section()

    def _index_by_instrument_and_section(self) -> None:
        """Indexes corpus by instrument ID and section prefix for fast hierarchical lookup."""
        self.instrument_map: dict[UUID, list[StatutoryChunk]] = {}
        for c in self.corpus_chunks:
            self.instrument_map.setdefault(c.instrument_id, []).append(c)

    def update_corpus(self, chunks: list[StatutoryChunk]) -> None:
        self.corpus_chunks = chunks
        self._index_by_instrument_and_section()

    def _get_parent_path(self, section_path: str) -> str | None:
        """Extracts parent section from a hierarchical path.

        e.g. 'Chapter II > Section 10 > Sub-section (2)' -> 'Chapter II > Section 10'
        e.g. 'Para 3(b)' -> 'Para 3'
        """
        if " > " in section_path:
            parts = section_path.rsplit(" > ", 1)
            return parts[0].strip()
        if "(" in section_path:
            return section_path.split("(", 1)[0].strip()
        return None

    def expand_chunk(self, chunk: StatutoryChunk) -> str:
        """Generates contextualized text including parent context if applicable.

        Returns an enriched text string without mutating the original chunk text.
        """
        parent_path = self._get_parent_path(chunk.section_path)
        if not parent_path:
            return chunk.text

        # Look for a parent chunk in the same instrument
        siblings = self.instrument_map.get(chunk.instrument_id, [])
        parent_chunk = next(
            (s for s in siblings if s.id != chunk.id and (s.section_path == parent_path or parent_path in s.section_path)),
            None,
        )

        if parent_chunk and parent_chunk.text != chunk.text:
            return (
                f"[Parent Section ({parent_path})]: {parent_chunk.text}\n"
                f"[Enacted Clause ({chunk.section_path})]: {chunk.text}"
            )

        # Fallback to structural prefix
        return f"[Governing Section: {parent_path}]\n{chunk.text}"

    def expand_candidates(self, candidates: list[Any]) -> list[Any]:
        """Attaches expanded_text attribute to candidate ScoredChunk objects."""
        for cand in candidates:
            chunk = cand.chunk
            cand.expanded_text = self.expand_chunk(chunk)
        return candidates
