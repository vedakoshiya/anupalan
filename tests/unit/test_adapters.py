"""Unit tests for adapter interfaces and abstract base classes."""

import unittest
from uuid import uuid4
from pydantic import BaseModel

from packages.adapters.src.adapters.interfaces import (
    BaseEmbedderAdapter,
    BaseLLMAdapter,
    BaseOCRAdapter,
    BaseRerankerAdapter,
    PassageCandidate,
    RerankedPassage,
)


class DummyLLM(BaseLLMAdapter):
    async def generate_structured(self, system_prompt, user_message, response_model, temperature=0.0):
        return response_model(summary="dummy")

    async def generate_text(self, system_prompt, user_message, temperature=0.0):
        return "dummy text"


class DummyEmbedder(BaseEmbedderAdapter):
    @property
    def dimension(self) -> int:
        return 1024

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 1024 for _ in texts]

    async def embed_query(self, query: str) -> list[float]:
        return [0.1] * 1024


class TestAdapters(unittest.TestCase):
    def test_abstract_class_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            BaseLLMAdapter()

        with self.assertRaises(TypeError):
            BaseEmbedderAdapter()

        with self.assertRaises(TypeError):
            BaseRerankerAdapter()

        with self.assertRaises(TypeError):
            BaseOCRAdapter()

    def test_concrete_subclass_instantiation(self):
        llm = DummyLLM()
        self.assertIsInstance(llm, BaseLLMAdapter)

        embedder = DummyEmbedder()
        self.assertIsInstance(embedder, BaseEmbedderAdapter)
        self.assertEqual(embedder.dimension, 1024)

    def test_dataclasses(self):
        chunk_id = uuid4()
        cand = PassageCandidate(
            chunk_id=chunk_id,
            text="Clause 3(b) job work conditions.",
            context_header="Notification 11/2017",
            lexical_score=1.5,
            dense_score=0.85,
        )
        self.assertEqual(cand.chunk_id, chunk_id)
        self.assertEqual(cand.lexical_score, 1.5)

        reranked = RerankedPassage(chunk_id=chunk_id, score=0.94, passage=cand)
        self.assertEqual(reranked.score, 0.94)
        self.assertEqual(reranked.passage.text, cand.text)


if __name__ == "__main__":
    unittest.main()
