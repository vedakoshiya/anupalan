"""Unit tests for the integrated IngestionPipeline orchestrator."""

import tempfile
import unittest
from pathlib import Path

from services.ingestion.src.models import IngestionStatus
from services.ingestion.src.pipeline import IngestionPipeline
from services.ingestion.src.storage import LocalImmutableStorage
from services.ingestion.src.version_graph import LegalVersionGraph


class TestIngestionPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = LocalImmutableStorage(base_directory=Path(self.temp_dir.name))
        self.version_graph = LegalVersionGraph()
        self.pipeline = IngestionPipeline(
            storage=self.storage,
            version_graph=self.version_graph,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_ingests_and_chunks(self):
        doc_data = b"""# Notification No. 11/2017-Central Tax
dated 1st July 2017
(1) Job work on textile articles shall be taxed at 5%.
| Code | Category | Rate |
|---|---|---|
| 9988 | Textiles | 5% |
"""
        result = self.pipeline.ingest_bytes("notif_11_2017.txt", doc_data)

        self.assertEqual(result.status, IngestionStatus.INGESTED)
        self.assertGreater(result.chunks_created, 0)
        self.assertEqual(result.quality_score, 0.95)
        self.assertEqual(len(result.flagged_pages), 0)

        # Verify chunks indexed
        self.assertGreater(len(self.pipeline.indexed_chunks), 0)
        # Verify node added to version graph
        self.assertIn("11/2017-Central Tax", self.version_graph.nodes)

    def test_pipeline_deduplication(self):
        doc_data = b"CBIC Notification 12/2024 dated 1st April 2024. Rate is 12%."

        # First run
        res1 = self.pipeline.ingest_bytes("notif_12.txt", doc_data)
        self.assertEqual(res1.status, IngestionStatus.INGESTED)

        # Second run with exact same content
        res2 = self.pipeline.ingest_bytes("notif_12_copy.txt", doc_data)
        self.assertEqual(res2.status, IngestionStatus.SKIPPED_DUPLICATE)
        self.assertEqual(res2.chunks_created, 0)
        self.assertEqual(res1.content_hash, res2.content_hash)

    def test_pipeline_flags_low_quality_for_review(self):
        # Corrupted payload
        corrupted_data = b"\x01\x02\x03 corrupted document scan \x00\x00\x00"
        result = self.pipeline.ingest_bytes("corrupted_scan.pdf", corrupted_data, mime_type="application/pdf")

        self.assertEqual(result.status, IngestionStatus.NEEDS_REVIEW)
        self.assertIn(1, result.flagged_pages)


if __name__ == "__main__":
    unittest.main()
