"""Unit tests for InMemoryRetrievalStore and PostgresPgVectorStore."""

import unittest
from datetime import date
from uuid import uuid4

from packages.retrieval.src.retrieval.metadata_filter import FilterCriteria
from packages.retrieval.src.retrieval.vector_store import (
    InMemoryRetrievalStore,
    PostgresPgVectorStore,
)
from services.ingestion.src.chunker import StatutoryChunk


class TestVectorAndLexicalStore(unittest.TestCase):
    def setUp(self):
        self.chunk1 = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 20/2017-CT",
            section_path="Entry 26",
            text="Textile job work rate reduced to 5 percent.",
            context_header="[Authority: CBIC | Instrument: Notif 20/2017]",
            chunk_type="clause",
            effective_from=date(2017, 8, 22),
            effective_to=None,
            jurisdiction="central",
            subjects=["job_work", "textiles"],
            language="en",
            token_count=12,
        )

        self.chunk2 = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 14/2019-CT",
            section_path="Para 1",
            text="Composition turnover limit increased to 1.5 crore rupees.",
            context_header="[Authority: CBIC | Instrument: Notif 14/2019]",
            chunk_type="clause",
            effective_from=date(2019, 4, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["composition"],
            language="en",
            token_count=12,
        )

        self.store = InMemoryRetrievalStore()
        # Add chunks with dummy embeddings
        emb1 = [1.0] + [0.0] * 1023
        emb2 = [0.0, 1.0] + [0.0] * 1022
        self.store.add_chunks(
            chunks=[self.chunk1, self.chunk2],
            embeddings={self.chunk1.id: emb1, self.chunk2.id: emb2},
        )

    def test_in_memory_bm25_search(self):
        criteria = FilterCriteria(as_of=date(2026, 10, 27))
        results = self.store.search_lexical(query="textile job work", criteria=criteria, top_k=5)

        self.assertGreaterEqual(len(results), 1)
        top_chunk, top_score = results[0]
        self.assertEqual(top_chunk.id, self.chunk1.id)
        self.assertGreater(top_score, 0.0)

    def test_in_memory_dense_search(self):
        criteria = FilterCriteria(as_of=date(2026, 10, 27))
        query_vec = [1.0] + [0.0] * 1023  # Aligns with chunk1
        results = self.store.search_dense(query_vector=query_vec, criteria=criteria, top_k=5)

        self.assertGreaterEqual(len(results), 1)
        top_chunk, sim = results[0]
        self.assertEqual(top_chunk.id, self.chunk1.id)
        self.assertAlmostEqual(sim, 1.0, places=3)

    def test_postgres_sql_builders(self):
        pg_store = PostgresPgVectorStore()
        criteria = FilterCriteria(as_of=date(2026, 10, 27), jurisdiction="gujarat")

        # Lexical SQL
        lex_sql, lex_params = pg_store.build_lexical_sql(query="job work", criteria=criteria, top_k=10)
        self.assertIn("to_tsvector", lex_sql)
        self.assertIn("plainto_tsquery", lex_sql)
        self.assertEqual(lex_params["query"], "job work")
        self.assertEqual(lex_params["limit"], 10)

        # Dense SQL
        dense_sql, dense_params = pg_store.build_dense_sql(
            query_vector=[0.1, 0.2], criteria=criteria, top_k=10
        )
        self.assertIn("<=>", dense_sql)
        self.assertIn("ORDER BY c.embedding <=> :query_vector::vector", dense_sql)
        self.assertEqual(dense_params["limit"], 10)

        # Null DB search returns empty
        self.assertEqual(pg_store.search_lexical("query", criteria), [])
        self.assertEqual(pg_store.search_dense([0.1], criteria), [])


if __name__ == "__main__":
    unittest.main()
