"""Retrieval store factory for Anupalan.

Provides a unified creation entrypoint that instantiates the appropriate
retrieval store (PostgreSQL + pgvector, SQLite 3 FTS5, or In-Memory).
"""

import os
from typing import Any

from packages.retrieval.src.retrieval.sqlite_store import SqliteVectorStore
from packages.retrieval.src.retrieval.vector_store import (
    BaseRetrievalStore,
    InMemoryRetrievalStore,
    PostgresPgVectorStore,
)


def create_retrieval_store(
    database_url: str | None = None,
    db_session: Any = None,
) -> BaseRetrievalStore:
    """Factory to instantiate the appropriate retrieval store backend."""
    raw_url = database_url or os.getenv("DATABASE_URL", "sqlite:///data/anupalan.db")
    url_lower = raw_url.lower()

    if url_lower.startswith(("postgresql", "postgres")):
        return PostgresPgVectorStore(db_session=db_session)
    elif url_lower.startswith("sqlite"):
        path = raw_url.replace("sqlite:///", "").replace("sqlite://", "")
        if not path or path == "/":
            path = "data/anupalan.db"
        return SqliteVectorStore(db_path=path)
    elif url_lower.startswith(("memory", "mock")):
        return InMemoryRetrievalStore()

    # Default to persistent local SQLite
    return SqliteVectorStore(db_path="data/anupalan.db")
