"""Provider-agnostic interfaces for model, search, and OCR backends.

Enables seamless swapping between Gemini, OpenAI, open-weight HuggingFace models,
and cloud Document AI providers with zero vendor lock-in.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import BaseModel


@dataclass
class PassageCandidate:
    """Passage candidate evaluated by the reranker."""

    chunk_id: UUID
    text: str
    context_header: str
    lexical_score: float = 0.0
    dense_score: float = 0.0


@dataclass
class RerankedPassage:
    """Passage candidate with rerank confidence score."""

    chunk_id: UUID
    score: float
    passage: PassageCandidate


@dataclass
class OCRExtractedPage:
    """Layout-aware OCR results for an individual page."""

    page_number: int
    text: str
    confidence: float
    tables: list[list[str]]
    bounding_boxes: list[dict[str, Any]]


class BaseLLMAdapter(ABC):
    """Abstract interface for large language model generation."""

    @abstractmethod
    async def generate_structured(
        self,
        system_prompt: str,
        user_message: str,
        response_model: type[BaseModel],
        temperature: float = 0.0,
    ) -> BaseModel:
        """Generate structured output validated against a Pydantic schema."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> str:
        """Generate unstructured text response."""
        pass


class BaseEmbedderAdapter(ABC):
    """Abstract interface for dense multilingual vector embeddings."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension (e.g., 1024)."""
        pass

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Compute dense embeddings for a batch of documents."""
        pass

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Compute dense embedding for a single user query."""
        pass


class BaseRerankerAdapter(ABC):
    """Abstract interface for cross-encoder reranking models."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: list[PassageCandidate],
        top_k: int = 8,
    ) -> list[RerankedPassage]:
        """Rerank candidates based on deep cross-attention semantic relevance."""
        pass


class BaseOCRAdapter(ABC):
    """Abstract interface for document text & layout extraction."""

    @abstractmethod
    async def extract_document(
        self,
        document_bytes: bytes,
        mime_type: str,
    ) -> list[OCRExtractedPage]:
        """Extract layout, tables, and text with page-level confidence."""
        pass
