"""Dense multilingual vector embedder adapter.

Provides deterministic 1024-dimensional dense multilingual vector embeddings
adhering to BaseEmbedderAdapter (BGE-M3 / multilingual-e5 compatible interface).
"""

import hashlib
import math
import re
from typing import Any

from packages.adapters.src.adapters.interfaces import BaseEmbedderAdapter


class LocalMultilingualEmbedder(BaseEmbedderAdapter):
    """Generates 1024-dimensional L2-normalized dense embeddings.

    Uses deterministic multi-hash subword projection designed to be robust across
    English, Gujarati, Hindi, and code-mixed Gujlish texts.
    """

    def __init__(self, dimension: int = 1024):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def _tokenize(self, text: str) -> list[str]:
        # Subword and char-ngram tokenization for multilingual robustness
        cleaned = text.lower().strip()
        tokens = re.findall(r"[\w%]+", cleaned, re.UNICODE)
        ngrams: list[str] = list(tokens)
        for t in tokens:
            if len(t) >= 4:
                ngrams.extend([t[i : i + 3] for i in range(len(t) - 2)])
        return ngrams

    def _vectorize(self, text: str) -> list[float]:
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self._dim

        vector = [0.0] * self._dim
        for token in tokens:
            # Deterministic hash to map token to dimension slot with sign bit
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if (h >> 16) % 2 == 0 else -1.0
            vector[idx] += sign

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0.0:
            vector = [x / norm for x in vector]
        return vector

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Computes embeddings for a batch of documents."""
        return [self._vectorize(t) for t in texts]

    async def embed_query(self, query: str) -> list[float]:
        """Computes embedding for a single user search query."""
        return self._vectorize(query)

    def embed_sync(self, text: str) -> list[float]:
        """Synchronous helper for offline indexers and testing."""
        return self._vectorize(text)
