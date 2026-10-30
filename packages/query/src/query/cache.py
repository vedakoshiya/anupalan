"""Query caching and cost control engine for Anupalan.

Implements high-throughput, thread-safe, TTL-bounded LRU caching
keyed by normalized query and 'as-of' validity date (Spec Section 12).
"""

import hashlib
import threading
import time
from datetime import date
from typing import Any
from uuid import UUID


class ComplianceQueryCache:
    """Thread-safe LRU cache with temporal date partitioning and TTL expiry."""

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._lock = threading.RLock()
        self._cache: dict[str, dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0

    @staticmethod
    def compute_cache_key(normalized_query: str, as_of: date, language: str) -> str:
        """Derives a deterministic SHA-256 cache key across normalized query parameters."""
        raw = f"{normalized_query.strip().lower()}||{as_of.isoformat()}||{language.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, normalized_query: str, as_of: date, language: str) -> Any | None:
        """Retrieves an unexpired cached compliance response if available."""
        key = self.compute_cache_key(normalized_query, as_of, language)
        now = time.time()

        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if now - entry["timestamp"] <= self.ttl_seconds:
                    entry["hit_count"] += 1
                    # Move to end to maintain LRU ordering
                    self._cache[key] = self._cache.pop(key)
                    self._hits += 1
                    return entry["response"]
                else:
                    # Expired entry
                    del self._cache[key]

            self._misses += 1
            return None

    def set(self, normalized_query: str, as_of: date, language: str, response: Any) -> None:
        """Caches a synthesized response, evicting the least recently used entry if full."""
        key = self.compute_cache_key(normalized_query, as_of, language)
        now = time.time()

        with self._lock:
            if key in self._cache:
                self._cache.pop(key)
            elif len(self._cache) >= self.max_size:
                # Evict oldest LRU entry (first key in dict)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

            self._cache[key] = {
                "key": key,
                "response": response,
                "timestamp": now,
                "hit_count": 0,
            }

    def invalidate_answer(self, answer_id: UUID | str) -> int:
        """Administrative takedown: purges any cached response matching an answer_id."""
        target_id_str = str(answer_id)
        evicted = 0
        with self._lock:
            keys_to_remove = []
            for k, entry in self._cache.items():
                resp = entry.get("response")
                resp_id = getattr(resp, "answer_id", None) or (resp.get("answer_id") if isinstance(resp, dict) else None)
                if resp_id and str(resp_id) == target_id_str:
                    keys_to_remove.append(k)

            for k in keys_to_remove:
                del self._cache[k]
                evicted += 1

        return evicted

    def clear(self) -> None:
        """Flushes all cached entries and resets statistics."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict[str, Any]:
        """Returns runtime cache statistics and hit ratios."""
        with self._lock:
            total = self._hits + self._misses
            hit_ratio = round(self._hits / total, 4) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio": hit_ratio,
            }
