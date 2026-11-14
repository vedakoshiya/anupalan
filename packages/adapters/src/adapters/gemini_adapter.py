"""Google Gemini API adapters for LLM structured generation and dense embeddings.

Implements BaseLLMAdapter and BaseEmbedderAdapter using asynchronous HTTPX
communicating directly with Google's Gemini REST endpoints.
"""

import json
import logging
from typing import Any, TypeVar
from pydantic import BaseModel, ValidationError
import httpx

from packages.adapters.src.adapters.interfaces import (
    BaseEmbedderAdapter,
    BaseLLMAdapter,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GeminiAPIError(Exception):
    """Raised when the Gemini REST API returns a non-200 status code."""

    def __init__(self, status_code: int, message: str, details: Any = None):
        super().__init__(f"Gemini API Error [{status_code}]: {message}")
        self.status_code = status_code
        self.details = details


class GeminiLLMAdapter(BaseLLMAdapter):
    """Production LLM adapter leveraging Gemini 1.5 Flash / Pro with structured JSON mode."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        timeout_seconds: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ):
        if not api_key or not api_key.strip():
            raise ValueError("Gemini API key cannot be empty.")
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.timeout_seconds = timeout_seconds
        self._client = client

    def _get_client(self) -> httpx.AsyncClient:
        return self._client or httpx.AsyncClient(timeout=self.timeout_seconds)

    async def generate_text(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> str:
        """Invokes Gemini generateContent to obtain plain text output."""
        endpoint = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            "generationConfig": {"temperature": temperature},
        }

        client = self._get_client()
        should_close = self._client is None
        try:
            resp = await client.post(endpoint, json=payload)
            if resp.status_code != 200:
                raise GeminiAPIError(resp.status_code, resp.text)

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise GeminiAPIError(204, "No candidates returned by Gemini model.")

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return ""
            return parts[0].get("text", "")
        finally:
            if should_close:
                await client.aclose()

    async def generate_structured(
        self,
        system_prompt: str,
        user_message: str,
        response_model: type[T],
        temperature: float = 0.0,
    ) -> T:
        """Invokes Gemini generateContent enforcing JSON schema and parses with Pydantic."""
        endpoint = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            "generationConfig": {
                "temperature": temperature,
                "response_mime_type": "application/json",
            },
        }

        client = self._get_client()
        should_close = self._client is None
        try:
            resp = await client.post(endpoint, json=payload)
            if resp.status_code != 200:
                raise GeminiAPIError(resp.status_code, resp.text)

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise GeminiAPIError(204, "No candidates returned by Gemini model.")

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise GeminiAPIError(204, "Empty content parts returned by Gemini model.")

            raw_text = parts[0].get("text", "{}")
            return response_model.model_validate_json(raw_text)
        finally:
            if should_close:
                await client.aclose()


class GeminiEmbedderAdapter(BaseEmbedderAdapter):
    """Dense vector embedding adapter utilizing Google text-embedding-004."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-004",
        dimension: int = 768,
        timeout_seconds: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ):
        if not api_key or not api_key.strip():
            raise ValueError("Gemini API key cannot be empty.")
        self.api_key = api_key.strip()
        self.model = model.strip()
        self._dim = dimension
        self.timeout_seconds = timeout_seconds
        self._client = client

    @property
    def dimension(self) -> int:
        return self._dim

    def _get_client(self) -> httpx.AsyncClient:
        return self._client or httpx.AsyncClient(timeout=self.timeout_seconds)

    async def embed_query(self, query: str) -> list[float]:
        """Generates dense vector representation for a query."""
        endpoint = f"{self.BASE_URL}/{self.model}:embedContent?key={self.api_key}"
        payload = {
            "model": f"models/{self.model}",
            "content": {"parts": [{"text": query}]},
        }

        client = self._get_client()
        should_close = self._client is None
        try:
            resp = await client.post(endpoint, json=payload)
            if resp.status_code != 200:
                raise GeminiAPIError(resp.status_code, resp.text)

            data = resp.json()
            embedding = data.get("embedding", {}).get("values", [])
            return embedding
        finally:
            if should_close:
                await client.aclose()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch generates dense vector representations for multiple passages."""
        if not texts:
            return []

        endpoint = f"{self.BASE_URL}/{self.model}:batchEmbedContents?key={self.api_key}"
        requests = [
            {"model": f"models/{self.model}", "content": {"parts": [{"text": t}]}}
            for t in texts
        ]
        payload = {"requests": requests}

        client = self._get_client()
        should_close = self._client is None
        try:
            resp = await client.post(endpoint, json=payload)
            if resp.status_code != 200:
                raise GeminiAPIError(resp.status_code, resp.text)

            data = resp.json()
            embeddings = [item.get("values", []) for item in data.get("embeddings", [])]
            return embeddings
        finally:
            if should_close:
                await client.aclose()
