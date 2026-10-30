"""Adapter interfaces and concrete implementations for Anupalan."""

from packages.adapters.src.adapters.interfaces import (
    BaseEmbedderAdapter,
    BaseLLMAdapter,
    BaseOCRAdapter,
    BaseRerankerAdapter,
    OCRExtractedPage,
    PassageCandidate,
    RerankedPassage,
)
from packages.adapters.src.adapters.local_embedder import LocalMultilingualEmbedder
from packages.adapters.src.adapters.local_reranker import LocalCrossEncoderReranker

__all__ = [
    "BaseLLMAdapter",
    "BaseEmbedderAdapter",
    "BaseRerankerAdapter",
    "BaseOCRAdapter",
    "PassageCandidate",
    "RerankedPassage",
    "OCRExtractedPage",
    "LocalMultilingualEmbedder",
    "LocalCrossEncoderReranker",
]
