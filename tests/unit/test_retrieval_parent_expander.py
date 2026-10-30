"""Unit tests for ParentClauseExpander."""

import unittest
from datetime import date
from uuid import uuid4

from packages.retrieval.src.retrieval.hybrid_retriever import ScoredChunk
from packages.retrieval.src.retrieval.parent_expander import ParentClauseExpander
from services.ingestion.src.chunker import StatutoryChunk


class TestParentClauseExpander(unittest.TestCase):
    def setUp(self):
        inst_id = uuid4()

        # Parent section
        self.chunk_parent = StatutoryChunk(
            id=uuid4(),
            instrument_id=inst_id,
            authority="CBIC",
            instrument_title="CGST Act 2017",
            section_path="Section 10",
            text="General conditions and eligibility for composition levy scheme.",
            context_header="[Authority: CBIC | Instrument: CGST Act | Section: Section 10]",
            chunk_type="clause",
            effective_from=date(2017, 7, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["composition"],
            language="en",
            token_count=10,
        )

        # Child sub-clause
        self.chunk_child = StatutoryChunk(
            id=uuid4(),
            instrument_id=inst_id,
            authority="CBIC",
            instrument_title="CGST Act 2017",
            section_path="Section 10 > Sub-section (1)",
            text="Registered person whose aggregate turnover did not exceed the limit may opt to pay tax.",
            context_header="[Authority: CBIC | Instrument: CGST Act | Section: Section 10 > Sub-section (1)]",
            chunk_type="clause",
            effective_from=date(2017, 7, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["composition"],
            language="en",
            token_count=16,
        )

        # Parent section with bracket notation
        self.chunk_bracket_child = StatutoryChunk(
            id=uuid4(),
            instrument_id=inst_id,
            authority="CBIC",
            instrument_title="CGST Act 2017",
            section_path="Para 3(b)",
            text="Textile processing services.",
            context_header="[Authority: CBIC | Instrument: CGST Act | Section: Para 3(b)]",
            chunk_type="clause",
            effective_from=date(2017, 7, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["textiles"],
            language="en",
            token_count=6,
        )

        self.expander = ParentClauseExpander(
            corpus_chunks=[self.chunk_parent, self.chunk_child, self.chunk_bracket_child]
        )

    def test_expand_hierarchical_subclause(self):
        expanded = self.expander.expand_chunk(self.chunk_child)
        self.assertIn("[Parent Section (Section 10)]", expanded)
        self.assertIn("General conditions and eligibility", expanded)
        self.assertIn("[Enacted Clause (Section 10 > Sub-section (1))]", expanded)
        self.assertIn("Registered person whose aggregate turnover", expanded)

    def test_expand_bracket_subclause_fallback(self):
        expanded = self.expander.expand_chunk(self.chunk_bracket_child)
        self.assertIn("[Governing Section: Para 3]", expanded)
        self.assertIn("Textile processing services", expanded)

    def test_expand_top_level_clause_unmodified(self):
        expanded = self.expander.expand_chunk(self.chunk_parent)
        self.assertEqual(expanded, self.chunk_parent.text)

    def test_expand_candidates_attaches_attribute(self):
        cand = ScoredChunk(chunk=self.chunk_child, bm25_score=0.8, vector_score=0.7, rrf_score=0.03)
        res = self.expander.expand_candidates([cand])
        self.assertIsNotNone(res[0].expanded_text)
        self.assertIn("Parent Section", res[0].expanded_text)


if __name__ == "__main__":
    unittest.main()
