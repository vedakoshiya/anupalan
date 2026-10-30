"""Unit tests for Phase 3 concrete adapters: LocalMultilingualEmbedder and LocalCrossEncoderReranker."""

import asyncio
import math
import unittest

from packages.adapters.src.adapters.interfaces import PassageCandidate
from packages.adapters.src.adapters.local_embedder import LocalMultilingualEmbedder
from packages.adapters.src.adapters.local_reranker import LocalCrossEncoderReranker
from uuid import uuid4


class TestPhase3Adapters(unittest.TestCase):
    def setUp(self):
        self.embedder = LocalMultilingualEmbedder(dimension=1024)
        self.reranker = LocalCrossEncoderReranker()

    def test_embedder_dimension_and_normalization(self):
        self.assertEqual(self.embedder.dimension, 1024)

        # Test sync embedding
        text_en = "What is the GST rate for textile job work?"
        vec = self.embedder.embed_sync(text_en)
        self.assertEqual(len(vec), 1024)

        # Verify L2 norm is approximately 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_embedder_multilingual_inputs(self):
        # Gujarati
        vec_gu = self.embedder.embed_sync("કાપડના જોબ વર્ક પર જીએસટી નો દર કેટલો છે?")
        self.assertEqual(len(vec_gu), 1024)
        norm_gu = math.sqrt(sum(x * x for x in vec_gu))
        self.assertAlmostEqual(norm_gu, 1.0, places=4)

        # Hindi
        vec_hi = self.embedder.embed_sync("कपड़ा जॉब वर्क पर जीएसटी की दर क्या है?")
        self.assertEqual(len(vec_hi), 1024)
        norm_hi = math.sqrt(sum(x * x for x in vec_hi))
        self.assertAlmostEqual(norm_hi, 1.0, places=4)

        # Empty string produces zero vector
        vec_empty = self.embedder.embed_sync("")
        self.assertEqual(vec_empty, [0.0] * 1024)

    def test_embedder_async_methods(self):
        # Verify coroutine interface methods exist and return coroutines
        self.assertTrue(asyncio.iscoroutinefunction(self.embedder.embed_query))
        self.assertTrue(asyncio.iscoroutinefunction(self.embedder.embed_texts))

        coro_q = self.embedder.embed_query("job work rate")
        coro_q.close()
        coro_docs = self.embedder.embed_texts(["doc1", "doc2"])
        coro_docs.close()

    def test_cross_encoder_rerank_scoring(self):
        cand1 = PassageCandidate(
            chunk_id=uuid4(),
            text="Textile job work rate is 5 percent.",
            context_header="[Authority: CBIC | Instrument: Notif 20/2017]",
            lexical_score=0.8,
            dense_score=0.8,
        )
        cand2 = PassageCandidate(
            chunk_id=uuid4(),
            text="Unrelated real estate construction rules.",
            context_header="[Authority: CBIC | Instrument: Notif 11/2017]",
            lexical_score=0.1,
            dense_score=0.1,
        )

        results = self.reranker.rerank_sync(
            query="textile job work 5 percent",
            candidates=[cand2, cand1],
            top_k=2,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].chunk_id, cand1.chunk_id)
        self.assertGreater(results[0].score, results[1].score)


if __name__ == "__main__":
    unittest.main()
