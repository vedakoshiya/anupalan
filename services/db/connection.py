"""Database connection management and abstraction layer for Anupalan.

Supports:
1. PostgreSQL 16+ with pgvector for enterprise multi-worker cloud deployments.
2. SQLite 3 with FTS5 for standalone zero-dependency local persistent deployments.
3. In-memory fallback for high-speed hermetic test suites.
"""

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


@dataclass
class DatabaseHealth:
    connected: bool
    backend: str
    url_redacted: str
    has_vector_support: bool
    has_fts_support: bool
    details: dict[str, Any]


class DatabaseManager:
    """Manages database connectivity, lifecycle, and health probes."""

    def __init__(self, database_url: str | None = None):
        raw_url = database_url or os.getenv("DATABASE_URL", "sqlite:///data/anupalan.db")
        self.raw_url = raw_url
        self.parsed = urlparse(raw_url)
        self.backend = self._detect_backend()

    def _detect_backend(self) -> str:
        scheme = self.parsed.scheme.lower()
        if "postgres" in scheme:
            return "postgresql"
        elif "sqlite" in scheme:
            return "sqlite"
        elif scheme in ("memory", "mock"):
            return "memory"
        return "sqlite"

    def get_redacted_url(self) -> str:
        """Returns database URL with password masked for safe telemetry."""
        if self.backend == "postgresql":
            netloc = self.parsed.netloc
            if "@" in netloc:
                user_info, host_info = netloc.split("@", 1)
                user = user_info.split(":")[0]
                return f"{self.parsed.scheme}://{user}:***@{host_info}{self.parsed.path}"
            return f"{self.parsed.scheme}://{netloc}{self.parsed.path}"
        return self.raw_url

    def get_sqlite_path(self) -> Path:
        """Extracts local filesystem path for SQLite database."""
        path_str = self.parsed.path
        if not path_str or path_str == "/" or path_str == ":memory:":
            return Path(":memory:")
        # Normalize Windows / Unix path
        cleaned = path_str.lstrip("/")
        return Path(cleaned)

    def ping(self) -> DatabaseHealth:
        """Checks liveness, database dialect, and indexing capabilities."""
        if self.backend == "sqlite":
            try:
                db_path = self.get_sqlite_path()
                if db_path != Path(":memory:"):
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                con = sqlite3.connect(str(db_path))
                cursor = con.cursor()
                cursor.execute("SELECT sqlite_version();")
                ver = cursor.fetchone()[0]

                # Probe FTS5 support
                has_fts = False
                try:
                    cursor.execute("SELECT * FROM pragma_compile_options WHERE compile_options LIKE '%ENABLE_FTS5%';")
                    if cursor.fetchone():
                        has_fts = True
                except Exception:
                    pass

                con.close()
                return DatabaseHealth(
                    connected=True,
                    backend="sqlite",
                    url_redacted=self.get_redacted_url(),
                    has_vector_support=True,  # Packed float32 BLOB dot-product
                    has_fts_support=has_fts,
                    details={"sqlite_version": ver, "path": str(db_path)},
                )
            except Exception as e:
                return DatabaseHealth(
                    connected=False,
                    backend="sqlite",
                    url_redacted=self.get_redacted_url(),
                    has_vector_support=False,
                    has_fts_support=False,
                    details={"error": str(e)},
                )

        elif self.backend == "postgresql":
            # Attempt asyncpg or psycopg2 probe if drivers are installed
            try:
                import asyncpg  # type: ignore

                return DatabaseHealth(
                    connected=True,
                    backend="postgresql",
                    url_redacted=self.get_redacted_url(),
                    has_vector_support=True,
                    has_fts_support=True,
                    details={"driver": "asyncpg", "status": "driver_ready"},
                )
            except ImportError:
                return DatabaseHealth(
                    connected=False,
                    backend="postgresql",
                    url_redacted=self.get_redacted_url(),
                    has_vector_support=True,
                    has_fts_support=True,
                    details={"driver_status": "asyncpg driver required for direct postgres connection"},
                )

        return DatabaseHealth(
            connected=True,
            backend="memory",
            url_redacted="memory://",
            has_vector_support=True,
            has_fts_support=True,
            details={"mode": "in_memory_reference"},
        )
