"""Legal version and supersession graph manager.

Tracks statutory amendment chains, prevents circular dependencies,
and resolves the active in-force rule for any given 'as-of' date.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal
from uuid import UUID, uuid4

RelationType = Literal["amends", "supersedes", "clarifies", "rescinds"]


@dataclass
class InstrumentNode:
    id: UUID
    code: str
    number: str
    title: str
    issued_on: date
    effective_from: date
    effective_to: date | None = None
    jurisdiction: str = "central"


@dataclass
class RelationEdge:
    from_code: str
    to_code: str
    relation: RelationType
    effective_from: date
    scope: str | None = None


class LegalVersionGraph:
    """Directed Acyclic Graph (DAG) for statutory instruments and amendments."""

    def __init__(self):
        self.nodes: dict[str, InstrumentNode] = {}
        self.edges: list[RelationEdge] = []
        self._adj_list: dict[str, list[RelationEdge]] = {}

    def add_instrument(self, node: InstrumentNode) -> None:
        self.nodes[node.code] = node
        if node.code not in self._adj_list:
            self._adj_list[node.code] = []

    def add_relation(
        self,
        from_code: str,
        to_code: str,
        relation: RelationType,
        effective_from: date,
        scope: str | None = None,
    ) -> None:
        """Adds a directed statutory relationship (e.g. from_code amends to_code)."""
        if from_code not in self.nodes:
            raise KeyError(f"Source instrument {from_code} not found in graph")
        if to_code not in self.nodes:
            raise KeyError(f"Target instrument {to_code} not found in graph")

        edge = RelationEdge(
            from_code=from_code,
            to_code=to_code,
            relation=relation,
            effective_from=effective_from,
            scope=scope,
        )

        # Temporary add to verify cycle
        self.edges.append(edge)
        self._adj_list[from_code].append(edge)

        if self._has_cycle():
            # Rollback
            self.edges.pop()
            self._adj_list[from_code].pop()
            raise ValueError(f"Cycle detected! Adding edge from {from_code} to {to_code} creates an amendment loop.")

    def _has_cycle(self) -> bool:
        """Checks if the directed graph contains cycles using DFS."""
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for edge in self._adj_list.get(node, []):
                neighbour = edge.to_code
                if neighbour not in visited:
                    if dfs(neighbour):
                        return True
                elif neighbour in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node_code in self.nodes:
            if node_code not in visited:
                if dfs(node_code):
                    return True
        return False

    def get_amendments(self, instrument_code: str) -> list[RelationEdge]:
        """Returns all incoming amendments and supersessions affecting the given instrument."""
        return [
            edge
            for edge in self.edges
            if edge.to_code == instrument_code and edge.relation in ("amends", "supersedes", "rescinds")
        ]

    def resolve_in_force_instrument(self, base_code: str, as_of: date) -> str:
        """Resolves whether base_code has been superseded or amended as of a specific date."""
        if base_code not in self.nodes:
            raise KeyError(f"Instrument {base_code} not found")

        current_code = base_code
        # Find if any superseding instrument took effect on or before as_of
        superseding_edges = sorted(
            [e for e in self.edges if e.to_code == current_code and e.relation == "supersedes" and e.effective_from <= as_of],
            key=lambda e: e.effective_from,
            reverse=True,
        )

        if superseding_edges:
            current_code = superseding_edges[0].from_code

        return current_code

    def is_in_force_on(self, instrument_code: str, as_of: date) -> bool:
        """Checks if an instrument is active on a given date."""
        node = self.nodes.get(instrument_code)
        if not node:
            return False

        if node.effective_from > as_of:
            return False
        if node.effective_to and node.effective_to <= as_of:
            return False

        # Check if rescinded on or before as_of
        for edge in self.edges:
            if edge.to_code == instrument_code and edge.relation == "rescinds" and edge.effective_from <= as_of:
                return False

        return True
