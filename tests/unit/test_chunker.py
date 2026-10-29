"""Unit tests for structure-aware chunking and contextual header injection."""

import unittest
from datetime import date
from uuid import uuid4

from services.ingestion.src.chunker import StructureAwareChunker


class TestStructureAwareChunker(unittest.TestCase):
    def setUp(self):
        self.chunker = StructureAwareChunker(target_min_tokens=20, target_max_tokens=100)
        self.instrument_id = uuid4()

    def test_contextual_header_generation(self):
        header = self.chunker.build_context_header(
            authority="CBIC",
            instrument_title="Notification 11/2017-CT (Rate)",
            section_path="Entry 26 > Para 3(b)",
            subjects=["job_work", "textiles"],
        )
        self.assertIn("Authority: CBIC", header)
        self.assertIn("Instrument: Notification 11/2017-CT (Rate)", header)
        self.assertIn("Section: Entry 26 > Para 3(b)", header)
        self.assertIn("Subject: job_work, textiles", header)

    def test_clause_chunking(self):
        clauses = [
            {
                "path": "Entry 26(i)",
                "text": "Services by way of job work in relation to all textile and textile articles.",
                "type": "clause",
            }
        ]
        chunks = self.chunker.chunk_clauses(
            instrument_id=self.instrument_id,
            authority="CBIC",
            instrument_title="Notification 11/2017-CT (Rate)",
            clauses=clauses,
            effective_from=date(2017, 7, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["job_work", "textiles"],
        )
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].chunk_type, "clause")
        self.assertEqual(chunks[0].section_path, "Entry 26(i)")
        self.assertIn("Authority: CBIC", chunks[0].context_header)

    def test_table_row_chunking(self):
        table_clause = [
            {
                "path": "Table of Rates",
                "type": "table",
                "headers": ["Item No", "Description", "Rate"],
                "rows": [
                    ["1", "Textile job work", "5%"],
                    ["2", "Engineering job work", "12%"],
                ],
            }
        ]
        chunks = self.chunker.chunk_clauses(
            instrument_id=self.instrument_id,
            authority="CBIC",
            instrument_title="Notification 11/2017-CT (Rate)",
            clauses=table_clause,
            effective_from=date(2017, 7, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["job_work"],
        )
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].chunk_type, "table_row")
        self.assertIn("Item No: 1 | Description: Textile job work | Rate: 5%", chunks[0].text)
        self.assertIn("Item No: 2 | Description: Engineering job work | Rate: 12%", chunks[1].text)


if __name__ == "__main__":
    unittest.main()
