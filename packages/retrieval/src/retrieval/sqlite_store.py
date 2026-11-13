"""Persistent SQLite-backed retrieval store for Anupalan.

Combines SQLite FTS5 for full-text lexical search and binary packed float32
vector similarity search with statutory temporal metadata pre-filtering.
Enables full disk persistence without requiring external database processes.
"""

import json
import math
import sqlite3
import struct
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any, Generator
from uuid import UUID

from packages.retrieval.src.retrieval.metadata_filter import FilterCriteria
from packages.retrieval.src.retrieval.vector_store import BaseRetrievalStore
from services.ingestion.src.chunker import StatutoryChunk


class SqliteVectorStore(BaseRetrievalStore):
    """Persistent embedded retrieval store using SQLite 3 and FTS5."""

    def __init__(self, db_path: str | Path = "data/anupalan.db"):
        self.db_path = Path(db_path)
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.has_fts = True
        self._init_db()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager guaranteeing connection closing on Windows."""
        con = sqlite3.connect(str(self.db_path))
        con.row_factory = sqlite3.Row
        try:
            yield con
        finally:
            con.close()

    def _init_db(self) -> None:
        """Initializes tables and indexes if they do not exist."""
        with self._connection() as con:
            cur = con.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                instrument_id TEXT NOT NULL,
                authority TEXT NOT NULL,
                instrument_title TEXT NOT NULL,
                section_path TEXT NOT NULL,
                text TEXT NOT NULL,
                context_header TEXT NOT NULL,
                chunk_type TEXT NOT NULL,
                effective_from TEXT NOT NULL,
                effective_to TEXT,
                jurisdiction TEXT NOT NULL,
                subjects TEXT NOT NULL,
                language TEXT NOT NULL,
                token_count INTEGER NOT NULL,
                metadata TEXT NOT NULL,
                embedding BLOB
            );
            """)

            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_temporal 
            ON chunks (jurisdiction, effective_from, effective_to);
            """)

            try:
                cur.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                    chunk_id UNINDEXED,
                    content,
                    context_header
                );
                """)
                self.has_fts = True
            except Exception:
                self.has_fts = False
            con.commit()

    @staticmethod
    def _pack_vector(vec: list[float]) -> bytes:
        """Serializes list of floats to packed IEEE 754 32-bit float bytes."""
        return struct.pack(f"{len(vec)}f", *vec)

    @staticmethod
    def _unpack_vector(raw: bytes) -> list[float]:
        """Deserializes packed float bytes back to list of floats."""
        n = len(raw) // 4
        return list(struct.unpack(f"{n}f", raw))

    def add_chunks(
        self,
        chunks: list[StatutoryChunk],
        embeddings: dict[UUID, list[float]] | None = None,
    ) -> None:
        """Persists statutory chunks and their vector representations into SQLite."""
        if not chunks:
            return

        with self._connection() as con:
            cur = con.cursor()
            for c in chunks:
                emb_bytes = None
                if embeddings and c.id in embeddings:
                    emb_bytes = self._pack_vector(embeddings[c.id])

                cur.execute(
                    """
                    INSERT OR REPLACE INTO chunks (
                        id, instrument_id, authority, instrument_title, section_path,
                        text, context_header, chunk_type, effective_from, effective_to,
                        jurisdiction, subjects, language, token_count, metadata, embedding
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(c.id),
                        str(c.instrument_id),
                        c.authority,
                        c.instrument_title,
                        c.section_path,
                        c.text,
                        c.context_header,
                        c.chunk_type,
                        c.effective_from.isoformat(),
                        c.effective_to.isoformat() if c.effective_to else None,
                        c.jurisdiction,
                        json.dumps(c.subjects),
                        c.language,
                        c.token_count,
                        json.dumps(c.metadata),
                        emb_bytes,
                    ),
                )

                if self.has_fts:
                    cur.execute(
                        "INSERT OR REPLACE INTO chunks_fts (chunk_id, content, context_header) VALUES (?, ?, ?)",
                        (str(c.id), c.text, c.context_header),
                    )

            con.commit()

    def count(self) -> int:
        """Returns total indexed chunk count in the persistent store."""
        with self._connection() as con:
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM chunks")
            return cur.fetchone()[0]

    def _row_to_chunk(self, row: sqlite3.Row) -> StatutoryChunk:
        return StatutoryChunk(
            id=UUID(row["id"]),
            instrument_id=UUID(row["instrument_id"]),
            authority=row["authority"],
            instrument_title=row["instrument_title"],
            section_path=row["section_path"],
            text=row["text"],
            context_header=row["context_header"],
            chunk_type=row["chunk_type"],
            effective_from=date.fromisoformat(row["effective_from"]),
            effective_to=date.fromisoformat(row["effective_to"]) if row["effective_to"] else None,
            jurisdiction=row["jurisdiction"],
            subjects=json.loads(row["subjects"]),
            language=row["language"],
            token_count=row["token_count"],
            metadata=json.loads(row["metadata"]),
        )

    def search_lexical(
        self,
        query: str,
        criteria: FilterCriteria,
        top_k: int = 50,
    ) -> list[tuple[StatutoryChunk, float]]:
        """Executes FTS5 BM25 search combined with statutory temporal filters."""
        as_of_str = criteria.as_of.isoformat()
        clean_tokens = [w for w in query.replace('"', "").replace("'", "").split() if len(w) > 1]
        if not clean_tokens:
            return []

        fts_query = " OR ".join(clean_tokens)

        with self._connection() as con:
            cur = con.cursor()
            if self.has_fts:
                sql = """
                SELECT c.*, bm25(chunks_fts) AS rank_score
                FROM chunks_fts f
                JOIN chunks c ON f.chunk_id = c.id
                WHERE chunks_fts MATCH ?
                  AND c.effective_from <= ?
                  AND (c.effective_to IS NULL OR c.effective_to > ?)
                """
                params = [fts_query, as_of_str, as_of_str]
                if criteria.jurisdiction:
                    sql += " AND c.jurisdiction = ?"
                    params.append(criteria.jurisdiction)

                sql += " ORDER BY rank_score ASC LIMIT ?"
                params.append(top_k)

                try:
                    cur.execute(sql, params)
                    rows = cur.fetchall()
                    results: list[tuple[StatutoryChunk, float]] = []
                    for r in rows:
                        raw_rank = abs(r["rank_score"])
                        score = round(1.0 / (1.0 + raw_rank), 4)
                        results.append((self._row_to_chunk(r), score))
                    return results
                except Exception:
                    pass

            # Fallback to LIKE query if FTS query syntax error
            sql_fallback = """
            SELECT * FROM chunks 
            WHERE effective_from <= ? 
              AND (effective_to IS NULL OR effective_to > ?)
            """
            params_fb = [as_of_str, as_of_str]
            if criteria.jurisdiction:
                sql_fallback += " AND jurisdiction = ?"
                params_fb.append(criteria.jurisdiction)

            cur.execute(sql_fallback, params_fb)
            rows = cur.fetchall()
            matched = []
            for r in rows:
                content = (r["text"] + " " + r["context_header"]).lower()
                matches = sum(1 for t in clean_tokens if t.lower() in content)
                if matches > 0:
                    matched.append((self._row_to_chunk(r), round(matches / len(clean_tokens), 4)))

            matched.sort(key=lambda x: x[1], reverse=True)
            return matched[:top_k]

    def search_dense(
        self,
        query_vector: list[float],
        criteria: FilterCriteria,
        top_k: int = 50,
    ) -> list[tuple[StatutoryChunk, float]]:
        """Computes cosine similarity over persistent vector blobs under temporal constraints."""
        if not query_vector:
            return []

        as_of_str = criteria.as_of.isoformat()
        q_norm = math.sqrt(sum(x * x for x in query_vector)) or 1.0

        with self._connection() as con:
            cur = con.cursor()
            sql = """
            SELECT * FROM chunks 
            WHERE effective_from <= ? 
              AND (effective_to IS NULL OR effective_to > ?)
            """
            params = [as_of_str, as_of_str]
            if criteria.jurisdiction:
                sql += " AND jurisdiction = ?"
                params.append(criteria.jurisdiction)

            cur.execute(sql, params)
            rows = cur.fetchall()

            scored: list[tuple[StatutoryChunk, float]] = []
            for r in rows:
                raw_emb = r["embedding"]
                if raw_emb:
                    emb = self._unpack_vector(raw_emb)
                    dot = sum(q * d for q, d in zip(query_vector, emb))
                    d_norm = math.sqrt(sum(d * d for d in emb)) or 1.0
                    sim = dot / (q_norm * d_norm)
                else:
                    doc_tokens = set((r["text"] + " " + r["context_header"]).lower().split())
                    q_tokens = set(str(x) for x in query_vector[:5])
                    overlap = len(doc_tokens.intersection(q_tokens))
                    sim = min(1.0, overlap / math.sqrt(max(1, len(doc_tokens))))

                if sim > 0.0:
                    scored.append((self._row_to_chunk(r), round(sim, 4)))

            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]
