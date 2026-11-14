"""Factory for instantiating model adapters (LLMs and Embedders).

Enables automatic detection of configured environment API keys, with graceful
fallback to local offline deterministic engines.
"""

import os
from packages.adapters.src.adapters.gemini_adapter import (
    GeminiEmbedderAdapter,
    GeminiLLMAdapter,
)
from packages.adapters.src.adapters.interfaces import (
    BaseEmbedderAdapter,
    BaseLLMAdapter,
)
from packages.adapters.src.adapters.local_embedder import LocalMultilingualEmbedder


def get_llm_adapter(
    api_key: str | None = None,
    model: str | None = None,
) -> BaseLLMAdapter | None:
    """Returns configured Gemini LLM adapter or None for offline deterministic fallback."""
    key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_gemini_api_key_here":
        return None

    target_model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return GeminiLLMAdapter(api_key=key, model=target_model)


def get_embedder_adapter(
    api_key: str | None = None,
) -> BaseEmbedderAdapter:
    """Returns Gemini text-embedding-004 adapter or local deterministic multilingual embedder."""
    key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_gemini_api_key_here":
        # Fall back to local 1024-dim subword embedder
        return LocalMultilingualEmbedder(dimension=1024)

    return GeminiEmbedderAdapter(api_key=key, model="text-embedding-004")
