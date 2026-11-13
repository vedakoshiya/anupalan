"""Unit tests for DatabaseManager, SqliteVectorStore, and Retrieval Store Factory."""

import gc
import tempfile
import unittest
from datetime import date
from pathlib import Path
from uuid import uuid4

from packages.retrieval.src.retrieval.factory import create_retrieval_store
from packages.retrieval.src.retrieval.metadata_filter import FilterCriteria
from packages.retrieval.src.retrieval.sqlite_store import SqliteVectorStore
from packages.retrieval.src.retrieval.vector_store import (
    InMemoryRetrievalStore,
    PostgresPgVectorStore,
)
from services.db.connection import DatabaseManager
from services.ingestion.src.chunker import StatutoryChunk


class TestPersistentDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_anupalan.db"
        self.store = SqliteVectorStore(db_path=self.db_path)

        # Create realistic test chunk
        self.chunk_id = uuid4()
        self.inst_id = uuid4()
        self.chunk = StatutoryChunk(
            id=self.chunk_id,
            instrument_id=self.inst_id,
            authority="CBIC",
            instrument_title="Notification 14/2019-CT",
            section_path="Para 1",
            text="The turnover limit for composition scheme under Section 10 is 1.5 Crores (150 Lakhs).",
            context_header="[CBIC - Notification 14/2019 - Para 1]",
            chunk_type="clause",
            effective_from=date(2019, 4, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["composition", "gst"],
            language="en",
            token_count=20,
            metadata={"ocr_quality": 0.99},
        )

    def tearDown(self):
        del self.store
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_database_manager_sqlite_health(self):
        db_mgr = DatabaseManager(f"sqlite:///{self.db_path}")
        health = db_mgr.ping()
        self.assertTrue(health.connected)
        self.assertEqual(health.backend, "sqlite")
        self.assertTrue(health.has_vector_support)

    def test_database_manager_url_redaction(self):
        pg_url = "postgresql://anupalan_user:super_secret_password@db.cloud.internal:5432/anupalan_prod"
        db_mgr = DatabaseManager(pg_url)
        redacted = db_mgr.get_redacted_url()
        self.assertNotIn("super_secret_password", redacted)
        self.assertIn("anupalan_user:***", redacted)
        self.assertEqual(db_mgr.backend, "postgresql")

    def test_sqlite_vector_store_add_and_count(self):
        self.assertEqual(self.store.count(), 0)
        self.store.add_chunks([self.chunk])
        self.assertEqual(self.store.count(), 1)

    def test_sqlite_vector_store_lexical_search_hit(self):
        self.store.add_chunks([self.chunk])
        criteria = FilterCriteria(as_of=date(2024, 1, 1), jurisdiction="central")
        results = self.store.search_lexical(query="composition scheme turnover limit", criteria=criteria)
        self.assertGreater(len(results), 0)
        found_chunk, score = results[0]
        self.assertEqual(found_chunk.id, self.chunk_id)
        self.assertGreater(score, 0.0)

    def test_sqlite_vector_store_temporal_filter_miss(self):
        # Querying on date prior to 2019-04-01 should exclude chunk
        self.store.add_chunks([self.chunk])
        pre_amendment_criteria = FilterCriteria(as_of=date(2018, 1, 1), jurisdiction="central")
        results = self.store.search_lexical(query="composition", criteria=pre_amendment_criteria)
        self.assertEqual(len(results), 0)

    def test_sqlite_vector_store_dense_search(self):
        # 4-dimensional synthetic vector
        test_vec = [0.1, 0.5, 0.8, 0.2]
        embeddings = {self.chunk_id: test_vec}
        self.store.add_chunks([self.chunk], embeddings=embeddings)

        criteria = FilterCriteria(as_of=date(2024, 1, 1))
        # Query with similar vector
        results = self.store.search_dense(query_vector=[0.1, 0.49, 0.81, 0.19], criteria=criteria)
        self.assertGreater(len(results), 0)
        found_chunk, score = results[0]
        self.assertEqual(found_chunk.id, self.chunk_id)
        self.assertGreater(score, 0.95)

    def test_retrieval_factory_instantiation(self):
        store_sqlite = create_retrieval_store(f"sqlite:///{self.db_path}")
        self.assertIsInstance(store_sqlite, SqliteVectorStore)

        store_mem = create_retrieval_store("memory://")
        self.assertIsInstance(store_mem, InMemoryRetrievalStore)

        store_pg = create_retrieval_store("postgresql://localhost:5432/anupalan")
        self.assertIsInstance(store_pg, PostgresPgVectorStore)


if __name__ == "__main__":
    unittest.main()
