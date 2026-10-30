"""Unit tests for SupersessionResolver and Version Graph integration."""

import unittest
from datetime import date
from uuid import uuid4

from packages.retrieval.src.retrieval.hybrid_retriever import ScoredChunk
from packages.retrieval.src.retrieval.supersession_resolver import SupersessionResolver
from services.ingestion.src.chunker import StatutoryChunk
from services.ingestion.src.version_graph import InstrumentNode, LegalVersionGraph


class TestSupersessionResolver(unittest.TestCase):
    def setUp(self):
        self.graph = LegalVersionGraph()

        node_old = InstrumentNode(
            id=uuid4(),
            code="INST-GST-COMP-002",
            number="Notification 08/2017-CT",
            title="Old Composition 75L Limit",
            issued_on=date(2017, 6, 27),
            effective_from=date(2017, 7, 1),
            effective_to=date(2019, 4, 1),
        )
        node_new = InstrumentNode(
            id=uuid4(),
            code="INST-GST-COMP-003",
            number="Notification 14/2019-CT",
            title="Enhanced Composition 1.5Cr Limit",
            issued_on=date(2019, 3, 7),
            effective_from=date(2019, 4, 1),
        )

        self.graph.add_instrument(node_old)
        self.graph.add_instrument(node_new)

        self.graph.add_relation(
            from_code="INST-GST-COMP-003",
            to_code="INST-GST-COMP-002",
            relation="supersedes",
            effective_from=date(2019, 4, 1),
        )

        self.resolver = SupersessionResolver(version_graph=self.graph)

        self.chunk_old = StatutoryChunk(
            id=uuid4(),
            instrument_id=node_old.id,
            authority="CBIC",
            instrument_title="INST-GST-COMP-002 - Notification 08/2017-CT",
            section_path="Para 1",
            text="Turnover limit is 75 Lakhs.",
            context_header="[Authority: CBIC | Instrument: INST-GST-COMP-002]",
            chunk_type="clause",
            effective_from=date(2017, 7, 1),
            effective_to=date(2019, 4, 1),
            jurisdiction="central",
            subjects=["composition"],
            language="en",
            token_count=10,
        )

        self.chunk_new = StatutoryChunk(
            id=uuid4(),
            instrument_id=node_new.id,
            authority="CBIC",
            instrument_title="INST-GST-COMP-003 - Notification 14/2019-CT",
            section_path="Para 1",
            text="Turnover limit is 1.5 Crore.",
            context_header="[Authority: CBIC | Instrument: INST-GST-COMP-003]",
            chunk_type="clause",
            effective_from=date(2019, 4, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["composition"],
            language="en",
            token_count=10,
        )

    def test_detects_superseded_chunk_in_future(self):
        # As of 2026: chunk_old was superseded by INST-GST-COMP-003
        is_sup, sup_by, reason = self.resolver.resolve_chunk(self.chunk_old, as_of=date(2026, 10, 27))
        self.assertTrue(is_sup)
        self.assertEqual(sup_by, "INST-GST-COMP-003")
        self.assertIn("Superseded", reason)

        # chunk_new is active, not superseded
        is_sup_new, sup_by_new, _ = self.resolver.resolve_chunk(self.chunk_new, as_of=date(2026, 10, 27))
        self.assertFalse(is_sup_new)
        self.assertIsNone(sup_by_new)

    def test_historical_as_of_preserves_active_status(self):
        # In 2018: chunk_old was still active and NOT yet superseded
        is_sup, sup_by, _ = self.resolver.resolve_chunk(self.chunk_old, as_of=date(2018, 1, 1))
        self.assertFalse(is_sup)
        self.assertIsNone(sup_by)

    def test_annotate_candidates_demotes_superseded(self):
        sc_old = ScoredChunk(chunk=self.chunk_old, bm25_score=0.9, vector_score=0.9, rrf_score=0.04)
        sc_new = ScoredChunk(chunk=self.chunk_new, bm25_score=0.8, vector_score=0.8, rrf_score=0.03)

        # Before annotation: sc_old has higher initial score (0.04 > 0.03)
        candidates = [sc_old, sc_new]
        annotated = self.resolver.annotate_candidates(candidates, as_of=date(2026, 10, 27), demote_superseded=True)

        # After annotation: sc_old is marked superseded and demoted (0.04 * 0.5 = 0.02)
        self.assertTrue(sc_old.is_superseded)
        self.assertEqual(sc_old.superseded_by, "INST-GST-COMP-003")
        # sc_new now ranks higher (0.03 > 0.02)
        self.assertEqual(annotated[0].chunk.id, self.chunk_new.id)
        self.assertEqual(annotated[1].chunk.id, self.chunk_old.id)


if __name__ == "__main__":
    unittest.main()
