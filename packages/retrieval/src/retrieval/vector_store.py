"""Storage and indexing abstraction for lexical and dense vector search.

Provides BaseRetrievalStore interface, an in-memory high-speed reference implementation,
and a PostgreSQL 16 + pgvector production store query builder.
"""

import math
import re
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from packages.retrieval.src.retrieval.metadata_filter import FilterCriteria, MetadataFilter
from services.ingestion.src.chunker import StatutoryChunk


class BaseRetrievalStore(ABC):
    """Abstract interface for statutory chunk search engines."""

    @abstractmethod
    def add_chunks(
        self,
        chunks: list[StatutoryChunk],
        embeddings: dict[UUID, list[float]] | None = None,
    ) -> None:
        """Indexes statutory chunks with optional pre-computed dense embeddings."""
        pass

    @abstractmethod
    def search_lexical(
        self,
        query: str,
        criteria: FilterCriteria,
        top_k: int = 50,
    ) -> list[tuple[StatutoryChunk, float]]:
        """Performs BM25 or full-text lexical search under filter constraints."""
        pass

    @abstractmethod
    def search_dense(
        self,
        query_vector: list[float],
        criteria: FilterCriteria,
        top_k: int = 50,
    ) -> list[tuple[StatutoryChunk, float]]:
        """Performs dense vector similarity search under filter constraints."""
        pass


class InMemoryRetrievalStore(BaseRetrievalStore):
    """Hermetic in-memory store combining inverted BM25 index and vector dot product."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: dict[UUID, StatutoryChunk] = {}
        self.embeddings: dict[UUID, list[float]] = {}

        # BM25 statistics
        self.doc_lengths: dict[UUID, int] = {}
        self.term_doc_freq: dict[str, int] = {}
        self.doc_term_freq: dict[UUID, dict[str, int]] = {}
        self.avg_doc_len = 1.0

    def _tokenize(self, text: str) -> list[str]:
        return [w.lower() for w in re.findall(r"[\w%]+", text, re.UNICODE)]

    def add_chunks(
        self,
        chunks: list[StatutoryChunk],
        embeddings: dict[UUID, list[float]] | None = None,
    ) -> None:
        """Indexes chunks and builds inverted index."""
        total_tokens = 0
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
            tokens = self._tokenize(chunk.context_header + " " + chunk.text)
            doc_len = len(tokens)
            self.doc_lengths[chunk.id] = doc_len
            total_tokens += doc_len

            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.doc_term_freq[chunk.id] = tf

            for t in tf:
                self.term_doc_freq[t] = self.term_doc_freq.get(t, 0) + 1

        if embeddings:
            self.embeddings.update(embeddings)

        doc_count = max(1, len(self.chunks))
        self.avg_doc_len = total_tokens / doc_count

    def search_lexical(
        self,
        query: str,
        criteria: FilterCriteria,
        top_k: int = 50,
    ) -> list[tuple[StatutoryChunk, float]]:
        """BM25 scoring over filtered valid candidates."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        filter_engine = MetadataFilter(criteria)
        valid_chunks = [c for c in self.chunks.values() if filter_engine.matches(c)]
        doc_count = len(self.chunks)

        scored: list[tuple[StatutoryChunk, float]] = []
        for chunk in valid_chunks:
            tf_dict = self.doc_term_freq.get(chunk.id, {})
            doc_len = self.doc_lengths.get(chunk.id, 0)
            score = 0.0

            for token in query_tokens:
                if token not in tf_dict:
                    continue
                tf = tf_dict[token]
                df = self.term_doc_freq.get(token, 0)
                # BM25 Robertson-Sparck-Jones formula
                idf = math.log((doc_count - df + 0.5) / (df + 0.5) + 1.0)
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_len)))
                score += idf * (numerator / max(0.001, denominator))

            if score > 0.0:
                scored.append((chunk, round(score, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def search_dense(
        self,
        query_vector: list[float],
        criteria: FilterCriteria,
        top_k: int = 50,
    ) -> list[tuple[StatutoryChunk, float]]:
        """Cosine similarity search over dense vector embeddings."""
        if not query_vector:
            return []

        filter_engine = MetadataFilter(criteria)
        valid_chunks = [c for c in self.chunks.values() if filter_engine.matches(c)]

        scored: list[tuple[StatutoryChunk, float]] = []
        q_norm = math.sqrt(sum(x * x for x in query_vector)) or 1.0

        for chunk in valid_chunks:
            emb = self.embeddings.get(chunk.id)
            if not emb:
                # Overlap cosine proxy if no precomputed embedding exists
                q_tokens = set(self._tokenize(" ".join(str(x) for x in query_vector[:10])))
                doc_tokens = set(self._tokenize(chunk.context_header + " " + chunk.text))
                overlap = len(q_tokens.intersection(doc_tokens))
                sim = min(1.0, overlap / math.sqrt(max(1, len(q_tokens)) * max(1, len(doc_tokens))))
            else:
                dot = sum(q * d for q, d in zip(query_vector, emb))
                d_norm = math.sqrt(sum(d * d for d in emb)) or 1.0
                sim = dot / (q_norm * d_norm)

            if sim > 0.0:
                scored.append((chunk, round(sim, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


class PostgresPgVectorStore(BaseRetrievalStore):
    """PostgreSQL 16 + pgvector production store query builder.

    Generates optimal SQL utilizing HNSW vector cosine distance operator (<=>),
    GIN FTS (ts_rank_cd), and composite temporal indexes.
    """

    def __init__(self, db_session: Any = None):
        self.db = db_session

    def add_chunks(
        self,
        chunks: list[StatutoryChunk],
        embeddings: dict[UUID, list[float]] | None = None,
    ) -> None:
        """Inserts chunks and vectors into PostgreSQL tables."""
        # Managed via services/ingestion pipeline & SQL migrations
        pass

    def build_lexical_sql(
        self,
        query: str,
        criteria: FilterCriteria,
        top_k: int = 50,
    ) -> tuple[str, dict[str, Any]]:
        """Generates parameterized SQL query for PostgreSQL Full-Text Search."""
        filter_engine = MetadataFilter(criteria)
        where_clause, params = filter_engine.to_sql_where()
        params["query"] = query
        params["limit"] = top_k

        sql = f"""
        SELECT 
            c.id, c.instrument_id, c.text, c.context_header, c.chunk_type,
            c.effective_from, c.effective_to, c.jurisdiction, c.subjects, c.language,
            ts_rank_cd(to_tsvector('english', c.text), plainto_tsquery('english', :query)) AS lexical_score
        FROM chunks c
        WHERE {where_clause}
          AND to_tsvector('english', c.text) @@ plainto_tsquery('english', :query)
        ORDER BY lexical_score DESC
        LIMIT :limit;
        """
        return sql.strip(), params

    def build_dense_sql(
        self,
        query_vector: list[float],
        criteria: FilterCriteria,
        top_k: int = 50,
    ) -> tuple[str, dict[str, Any]]:
        """Generates parameterized SQL for pgvector HNSW cosine similarity search."""
        filter_engine = MetadataFilter(criteria)
        where_clause, params = filter_engine.to_sql_where()
        params["query_vector"] = str(query_vector)
        params["limit"] = top_k

        sql = f"""
        SELECT 
            c.id, c.instrument_id, c.text, c.context_header, c.chunk_type,
            c.effective_from, c.effective_to, c.jurisdiction, c.subjects, c.language,
            1 - (c.embedding <=> :query_vector::vector) AS dense_score
        FROM chunks c
        WHERE {where_clause}
          AND c.embedding IS NOT NULL
        ORDER BY c.embedding <=> :query_vector::vector ASC
        LIMIT :limit;
        """
        return sql.strip(), params

    def search_lexical(
        self,
        query: str,
        criteria: FilterCriteria,
        top_k: int = 50,
    ) -> list[tuple[StatutoryChunk, float]]:
        if not self.db:
            return []
        sql, params = self.build_lexical_sql(query, criteria, top_k)
        # Execute via connection if available
        return []

    def search_dense(
        self,
        query_vector: list[float],
        criteria: FilterCriteria,
        top_k: int = 50,
    ) -> list[tuple[StatutoryChunk, float]]:
        if not self.db:
            return []
        sql, params = self.build_dense_sql(query_vector, criteria, top_k)
        return []
