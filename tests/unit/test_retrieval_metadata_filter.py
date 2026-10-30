"""Unit tests for MetadataFilter and FilterCriteria."""

import unittest
from datetime import date
from uuid import uuid4

from packages.retrieval.src.retrieval.metadata_filter import FilterCriteria, MetadataFilter
from services.ingestion.src.chunker import StatutoryChunk


class TestMetadataFilter(unittest.TestCase):
    def setUp(self):
        self.chunk_central_active = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 11/2017-CT",
            section_path="Entry 26(i)",
            text="Textile job work rate is 5%.",
            context_header="[Authority: CBIC | Instrument: Notification 11/2017]",
            chunk_type="clause",
            effective_from=date(2017, 7, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["job_work", "textiles"],
            language="en",
            token_count=10,
        )

        self.chunk_gujarat = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="Gujarat Commercial Tax",
            instrument_title="Gujarat Act No. 4 of 2019",
            section_path="Section 3",
            text="Exemption for shops with fewer than 10 workers.",
            context_header="[Authority: Gujarat | Instrument: Act 4 of 2019]",
            chunk_type="clause",
            effective_from=date(2019, 3, 7),
            effective_to=None,
            jurisdiction="gujarat",
            subjects=["labour", "shops"],
            language="gu",
            token_count=12,
        )

        self.chunk_expired = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 08/2017-CT",
            section_path="Para 1",
            text="Composition threshold 75 Lakhs.",
            context_header="[Authority: CBIC | Instrument: Notification 08/2017]",
            chunk_type="clause",
            effective_from=date(2017, 7, 1),
            effective_to=date(2019, 4, 1),
            jurisdiction="central",
            subjects=["composition"],
            language="en",
            token_count=8,
        )

        self.chunks = [self.chunk_central_active, self.chunk_gujarat, self.chunk_expired]

    def test_temporal_validity_filtering(self):
        # 2026: central active matches, expired does not
        crit_2026 = FilterCriteria(as_of=date(2026, 10, 27))
        filter_2026 = MetadataFilter(crit_2026)
        matches = filter_2026.filter_chunks(self.chunks)
        match_ids = [c.id for c in matches]
        self.assertIn(self.chunk_central_active.id, match_ids)
        self.assertNotIn(self.chunk_expired.id, match_ids)

        # 2018: expired was active then
        crit_2018 = FilterCriteria(as_of=date(2018, 1, 1))
        filter_2018 = MetadataFilter(crit_2018)
        matches_2018 = filter_2018.filter_chunks(self.chunks)
        match_ids_2018 = [c.id for c in matches_2018]
        self.assertIn(self.chunk_expired.id, match_ids_2018)
        self.assertNotIn(self.chunk_gujarat.id, match_ids_2018)

    def test_jurisdiction_filtering(self):
        # Gujarat filter includes gujarat and central chunks
        crit_guj = FilterCriteria(as_of=date(2026, 10, 27), jurisdiction="gujarat")
        filter_guj = MetadataFilter(crit_guj)
        matches = filter_guj.filter_chunks(self.chunks)
        match_ids = [c.id for c in matches]
        self.assertIn(self.chunk_central_active.id, match_ids)
        self.assertIn(self.chunk_gujarat.id, match_ids)

        # Maharashtra filter excludes Gujarat-only chunk
        crit_mh = FilterCriteria(as_of=date(2026, 10, 27), jurisdiction="maharashtra")
        filter_mh = MetadataFilter(crit_mh)
        matches_mh = filter_mh.filter_chunks(self.chunks)
        match_ids_mh = [c.id for c in matches_mh]
        self.assertIn(self.chunk_central_active.id, match_ids_mh)
        self.assertNotIn(self.chunk_gujarat.id, match_ids_mh)

    def test_subject_and_authority_filtering(self):
        crit_subj = FilterCriteria(
            as_of=date(2026, 10, 27),
            subjects=["textiles"],
            authorities=["CBIC"],
            chunk_types=["clause"],
        )
        filter_subj = MetadataFilter(crit_subj)
        matches = filter_subj.filter_chunks(self.chunks)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].id, self.chunk_central_active.id)

    def test_to_sql_where_generation(self):
        crit = FilterCriteria(
            as_of=date(2026, 10, 27),
            jurisdiction="gujarat",
            authorities=["CBIC", "GST Council"],
            chunk_types=["clause"],
            subjects=["job_work"],
        )
        filter_engine = MetadataFilter(crit)
        sql, params = filter_engine.to_sql_where()

        self.assertIn("effective_from <= :as_of", sql)
        self.assertIn("jurisdiction = :jurisdiction", sql)
        self.assertIn("authority IN :authorities", sql)
        self.assertIn("subjects && :subjects", sql)
        self.assertEqual(params["as_of"], date(2026, 10, 27))
        self.assertEqual(params["jurisdiction"], "gujarat")


if __name__ == "__main__":
    unittest.main()
