"""Unit tests for hybrid retrieval, temporal pre-filtering, and RRF scoring."""

import unittest
from datetime import date
from uuid import uuid4

from packages.retrieval.src.retrieval.hybrid_retriever import HybridRetriever
from services.ingestion.src.chunker import StatutoryChunk


class TestHybridRetriever(unittest.TestCase):
    def setUp(self):
        self.chunk1 = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 11/2017-CT",
            section_path="Entry 26(i)",
            text="Textile job work rate is 5 percent for yarn and fabrics.",
            context_header="[Authority: CBIC | Instrument: Notification 11/2017 | Section: Entry 26(i)]",
            chunk_type="clause",
            effective_from=date(2017, 7, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["job_work", "textiles"],
            language="en",
            token_count=12,
        )

        # Future chunk not yet effective as of 2020
        self.chunk_future = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 99/2025-CT",
            section_path="Section 1",
            text="New rate of tax for job work.",
            context_header="[Authority: CBIC | Instrument: Notification 99/2025]",
            chunk_type="clause",
            effective_from=date(2025, 1, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["job_work"],
            language="en",
            token_count=10,
        )

        # Expired chunk (rescinded in 2019)
        self.chunk_expired = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 08/2017-CT",
            section_path="Para 1",
            text="Composition scheme threshold limit is 75 lakh rupees.",
            context_header="[Authority: CBIC | Instrument: Notification 08/2017]",
            chunk_type="clause",
            effective_from=date(2017, 7, 1),
            effective_to=date(2019, 4, 1),
            jurisdiction="central",
            subjects=["composition"],
            language="en",
            token_count=10,
        )

        self.retriever = HybridRetriever(
            chunks=[self.chunk1, self.chunk_future, self.chunk_expired],
        )

    def test_temporal_pre_filtering_excludes_future_and_expired(self):
        # Query as of 2020:
        # - chunk1 is active (2017-07-01 -> None) -> Should be retrieved
        # - chunk_future is inactive (starts 2025) -> Must be excluded
        # - chunk_expired is inactive (ended 2019) -> Must be excluded
        results = self.retriever.retrieve(
            query="job work rate composition",
            as_of=date(2020, 1, 1),
        )
        retrieved_ids = [r.chunk.id for r in results]
        self.assertIn(self.chunk1.id, retrieved_ids)
        self.assertNotIn(self.chunk_future.id, retrieved_ids)
        self.assertNotIn(self.chunk_expired.id, retrieved_ids)

    def test_temporal_pre_filtering_includes_historical_when_valid(self):
        # Query as of 2018:
        # - chunk_expired was active in 2018 -> Should be retrieved
        results = self.retriever.retrieve(
            query="composition scheme threshold",
            as_of=date(2018, 1, 1),
        )
        retrieved_ids = [r.chunk.id for r in results]
        self.assertIn(self.chunk_expired.id, retrieved_ids)


if __name__ == "__main__":
    unittest.main()
