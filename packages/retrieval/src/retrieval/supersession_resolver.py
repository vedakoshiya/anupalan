"""Supersession and legal amendment resolution engine.

Traverses the Legal Version Graph to detect whether retrieved statutory passages
have been superseded, amended, or clarified by subsequent instruments as of a given date.
"""

from datetime import date
from typing import Any
from uuid import UUID

from services.ingestion.src.chunker import StatutoryChunk
from services.ingestion.src.version_graph import LegalVersionGraph


class SupersessionResolver:
    """Detects supersession chains and annotates statutory chunks."""

    def __init__(self, version_graph: LegalVersionGraph | None = None):
        self.version_graph = version_graph

    def _extract_instrument_code(self, chunk: StatutoryChunk) -> str | None:
        """Extracts instrument code from title or metadata header (e.g. 'INST-GST-JW-001')."""
        header = chunk.context_header + " " + chunk.instrument_title
        for part in header.split():
            cleaned = part.strip("[],:()")
            if cleaned.startswith("INST-"):
                return cleaned
        return None

    def resolve_chunk(
        self,
        chunk: StatutoryChunk,
        as_of: date,
    ) -> tuple[bool, str | None, str | None]:
        """Checks if chunk's governing instrument is superseded on as_of.

        Returns:
            (is_superseded, superseded_by_code, reason)
        """
        if not self.version_graph:
            return False, None, None

        code = self._extract_instrument_code(chunk)
        if not code or code not in self.version_graph.nodes:
            return False, None, None

        try:
            active_code = self.version_graph.resolve_in_force_instrument(base_code=code, as_of=as_of)
            if active_code and active_code != code:
                active_node = self.version_graph.nodes.get(active_code)
                title = active_node.title if active_node else active_code
                return True, active_code, f"Superseded by {active_code} ({title})"
        except KeyError:
            pass

        # Check if any incoming relation supersedes or rescinds this instrument on or before as_of
        for edge in getattr(self.version_graph, "edges", []):
            if edge.to_code == code and edge.relation in ("supersedes", "rescinds") and edge.effective_from <= as_of:
                return True, edge.from_code, f"{edge.relation.capitalize()} by {edge.from_code}"

        return False, None, None

    def annotate_candidates(
        self,
        candidates: list[Any],
        as_of: date,
        demote_superseded: bool = True,
    ) -> list[Any]:
        """Annotates a list of ScoredChunk candidates with supersession status.

        If demote_superseded is True, penalizes the rank score of superseded chunks
        so active law takes strict priority.
        """
        for cand in candidates:
            chunk = cand.chunk
            is_sup, sup_by, reason = self.resolve_chunk(chunk, as_of)
            cand.is_superseded = is_sup
            cand.superseded_by = sup_by

            if is_sup and demote_superseded:
                # Demote RRF score by 50% so active law ranks above legacy superseded versions
                cand.rrf_score *= 0.5

        # Re-sort after demotion
        candidates.sort(key=lambda c: getattr(c, "rrf_score", 0.0), reverse=True)
        return candidates
