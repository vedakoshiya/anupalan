"""Unit tests for CrossEncoderReranker and LocalCrossEncoderReranker."""

import asyncio
import unittest
from datetime import date
from uuid import uuid4

from packages.adapters.src.adapters.interfaces import PassageCandidate
from packages.adapters.src.adapters.local_reranker import LocalCrossEncoderReranker
from packages.retrieval.src.retrieval.hybrid_retriever import ScoredChunk
from packages.retrieval.src.retrieval.reranker import CrossEncoderReranker
from services.ingestion.src.chunker import StatutoryChunk


class TestCrossEncoderReranker(unittest.TestCase):
    def setUp(self):
        self.cand1 = PassageCandidate(
            chunk_id=uuid4(),
            text="Textile job work GST rate is 5% under Entry 26(i).",
            context_header="[Authority: CBIC | Instrument: Notification 20/2017 | Section: Entry 26(i)]",
            lexical_score=0.8,
            dense_score=0.7,
        )

        self.cand2 = PassageCandidate(
            chunk_id=uuid4(),
            text="Exemption for supply of services by an author or artist.",
            context_header="[Authority: CBIC | Instrument: Notification 12/2017]",
            lexical_score=0.1,
            dense_score=0.2,
        )

        self.adapter = LocalCrossEncoderReranker()
        self.reranker = CrossEncoderReranker(adapter=self.adapter)

    def test_local_cross_encoder_rerank_sync(self):
        reranked = self.adapter.rerank_sync(
            query="textile job work 5%",
            candidates=[self.cand2, self.cand1],
            top_k=2,
        )
        self.assertEqual(len(reranked), 2)
        # cand1 must rank first due to strong query-text and context header alignment
        self.assertEqual(reranked[0].chunk_id, self.cand1.chunk_id)
        self.assertGreater(reranked[0].score, reranked[1].score)

    def test_local_cross_encoder_rerank_async(self):
        self.assertTrue(asyncio.iscoroutinefunction(self.adapter.rerank))
        coro = self.adapter.rerank(
            query="textile job work",
            candidates=[self.cand1, self.cand2],
            top_k=1,
        )
        coro.close()

    def test_cross_encoder_rerank_scored_chunks(self):
        chunk1 = StatutoryChunk(
            id=self.cand1.chunk_id,
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notif 20/2017",
            section_path="Entry 26",
            text=self.cand1.text,
            context_header=self.cand1.context_header,
            chunk_type="clause",
            effective_from=date(2017, 8, 22),
            effective_to=None,
            jurisdiction="central",
            subjects=["textiles"],
            language="en",
            token_count=10,
        )
        chunk2 = StatutoryChunk(
            id=self.cand2.chunk_id,
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notif 12/2017",
            section_path="Section 1",
            text=self.cand2.text,
            context_header=self.cand2.context_header,
            chunk_type="clause",
            effective_from=date(2017, 7, 1),
            effective_to=None,
            jurisdiction="central",
            subjects=["services"],
            language="en",
            token_count=10,
        )

        sc1 = ScoredChunk(chunk=chunk1, bm25_score=0.8, vector_score=0.7, rrf_score=0.03)
        sc2 = ScoredChunk(chunk=chunk2, bm25_score=0.1, vector_score=0.2, rrf_score=0.01)

        reranked = self.reranker.rerank_scored_chunks(
            query="textile job work 5%",
            candidates=[sc2, sc1],
            top_k=2,
        )

        self.assertEqual(len(reranked), 2)
        self.assertEqual(reranked[0].chunk.id, chunk1.id)
        self.assertIsNotNone(reranked[0].rerank_score)
        self.assertGreater(reranked[0].rerank_score, reranked[1].rerank_score)

    def test_rerank_empty_candidates(self):
        res = self.reranker.rerank_scored_chunks("query", [])
        self.assertEqual(res, [])


if __name__ == "__main__":
    unittest.main()
