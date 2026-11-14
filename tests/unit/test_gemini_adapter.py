"""Unit tests for GeminiLLMAdapter, GeminiEmbedderAdapter, and Model Factory."""

import asyncio
import json
import unittest
from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import httpx
from pydantic import BaseModel

from packages.adapters.src.adapters.factory import (
    get_embedder_adapter,
    get_llm_adapter,
)
from packages.adapters.src.adapters.gemini_adapter import (
    GeminiAPIError,
    GeminiEmbedderAdapter,
    GeminiLLMAdapter,
)
from packages.adapters.src.adapters.local_embedder import LocalMultilingualEmbedder
from packages.generation.src.generation.generator import ComplianceGenerator
from packages.retrieval.src.retrieval.hybrid_retriever import ScoredChunk
from services.ingestion.src.chunker import StatutoryChunk


class SampleModel(BaseModel):
    answer: str
    confidence: float


class TestGeminiAdapters(unittest.TestCase):
    def test_llm_adapter_empty_key_raises(self):
        with self.assertRaises(ValueError):
            GeminiLLMAdapter(api_key="")

    def test_embedder_adapter_dimension(self):
        emb = GeminiEmbedderAdapter(api_key="test_key_xyz", dimension=768)
        self.assertEqual(emb.dimension, 768)

    def test_llm_adapter_generate_text_mocked(self):
        mock_response = httpx.Response(
            status_code=200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "Job work rate on textiles is 5% under Notification 20/2017."}
                            ]
                        }
                    }
                ]
            },
            request=httpx.Request("POST", "https://mock.gemini.api/"),
        )

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()

        adapter = GeminiLLMAdapter(api_key="valid_key", client=mock_client)
        result = asyncio.run(
            adapter.generate_text(
                system_prompt="You are a compliance assistant.",
                user_message="What is the job work rate?",
            )
        )
        self.assertIn("5%", result)

    def test_llm_adapter_rate_limit_error(self):
        mock_response = httpx.Response(
            status_code=429,
            text="Quota exceeded for Resource",
            request=httpx.Request("POST", "https://mock.gemini.api/"),
        )
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()

        adapter = GeminiLLMAdapter(api_key="valid_key", client=mock_client)
        with self.assertRaises(GeminiAPIError) as ctx:
            asyncio.run(adapter.generate_text("System", "User"))
        self.assertEqual(ctx.exception.status_code, 429)

    def test_llm_adapter_generate_structured_mocked(self):
        mock_payload = {"answer": "Presumptive tax limit is 2 Crores.", "confidence": 0.98}
        mock_response = httpx.Response(
            status_code=200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": json.dumps(mock_payload)}]
                        }
                    }
                ]
            },
            request=httpx.Request("POST", "https://mock.gemini.api/"),
        )

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()

        adapter = GeminiLLMAdapter(api_key="valid_key", client=mock_client)
        structured = asyncio.run(
            adapter.generate_structured(
                system_prompt="System",
                user_message="User",
                response_model=SampleModel,
            )
        )
        self.assertEqual(structured.answer, "Presumptive tax limit is 2 Crores.")
        self.assertEqual(structured.confidence, 0.98)

    def test_embedder_adapter_embed_query_mocked(self):
        mock_response = httpx.Response(
            status_code=200,
            json={"embedding": {"values": [0.12, -0.45, 0.88, 0.05]}},
            request=httpx.Request("POST", "https://mock.gemini.api/"),
        )

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()

        embedder = GeminiEmbedderAdapter(api_key="valid_key", client=mock_client)
        vec = asyncio.run(embedder.embed_query("What is composition scheme?"))
        self.assertEqual(len(vec), 4)
        self.assertEqual(vec[0], 0.12)

    def test_factory_offline_fallback(self):
        # Empty or default placeholder key returns None for LLM and local embedder
        llm = get_llm_adapter(api_key="")
        self.assertIsNone(llm)

        embedder = get_embedder_adapter(api_key="")
        self.assertIsInstance(embedder, LocalMultilingualEmbedder)
        self.assertEqual(embedder.dimension, 1024)

    def test_factory_live_keys(self):
        llm = get_llm_adapter(api_key="AIzaSy_TEST_KEY_12345", model="gemini-1.5-pro")
        self.assertIsInstance(llm, GeminiLLMAdapter)
        self.assertEqual(llm.model, "gemini-1.5-pro")

        embedder = get_embedder_adapter(api_key="AIzaSy_TEST_KEY_12345")
        self.assertIsInstance(embedder, GeminiEmbedderAdapter)

    def test_generator_with_mock_llm_and_fallback(self):
        chunk = StatutoryChunk(
            id=uuid4(),
            instrument_id=uuid4(),
            authority="CBIC",
            instrument_title="Notification 20/2017-CT",
            section_path="Entry 26",
            text="Textile job work GST rate is 5%.",
            context_header="[CBIC - Notification 20/2017]",
            chunk_type="clause",
            effective_from=date(2017, 8, 22),
            effective_to=None,
            jurisdiction="central",
            subjects=["job_work", "textile"],
            language="en",
            token_count=12,
        )
        cand = ScoredChunk(
            chunk=chunk,
            bm25_score=1.5,
            vector_score=0.9,
            rrf_score=0.03,
        )

        # 1. Generator with None LLM uses deterministic extraction
        gen_offline = ComplianceGenerator(llm_adapter=None)
        resp1 = gen_offline.generate_answer(
            query="Textile rate?",
            as_of=date(2024, 1, 1),
            language="en",
            candidates=[cand],
            corpus_updated=date(2026, 10, 26),
        )
        self.assertIn("According to official statutory provisions", resp1.summary)
        self.assertFalse(resp1.abstained)

        # 2. Generator with LLM adapter that raises exception falls back gracefully
        failing_mock_llm = MagicMock()
        failing_mock_llm.generate_text = AsyncMock(side_effect=Exception("API timeout"))
        gen_failing = ComplianceGenerator(llm_adapter=failing_mock_llm)
        resp2 = gen_failing.generate_answer(
            query="Textile rate?",
            as_of=date(2024, 1, 1),
            language="en",
            candidates=[cand],
            corpus_updated=date(2026, 10, 26),
        )
        self.assertIn("According to official statutory provisions", resp2.summary)
        self.assertFalse(resp2.abstained)


if __name__ == "__main__":
    unittest.main()
