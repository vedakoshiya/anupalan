"""Immutable raw artifact storage and content-addressable deduplication.

Enforces cryptographic SHA-256 deduplication and idempotent storage
matching FR-007 and FR-008 of the specification.
"""

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import UUID, uuid4

from services.ingestion.src.models import RawDocument


class BaseStorageBackend(ABC):
    """Abstract interface for immutable document storage."""

    @abstractmethod
    def store_raw(self, filename: str, data: bytes, mime_type: str) -> tuple[RawDocument, bool]:
        """Stores bytes immutably.

        Returns (RawDocument, is_new: bool). If content hash exists, is_new is False.
        """
        pass

    @abstractmethod
    def retrieve_raw(self, storage_uri: str) -> bytes:
        """Retrieves raw document bytes from storage URI."""
        pass

    @abstractmethod
    def exists(self, content_hash: str) -> bool:
        """Checks if a document with this SHA-256 hash already exists."""
        pass


class LocalImmutableStorage(BaseStorageBackend):
    """Local filesystem storage using content-addressable SHA-256 naming."""

    def __init__(self, base_directory: Path):
        self.base_dir = Path(base_directory)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # In-memory index of content hashes to RawDocuments
        self._hash_registry: dict[str, RawDocument] = {}

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Computes cryptographic SHA-256 hash of raw byte payload."""
        return hashlib.sha256(data).hexdigest()

    def exists(self, content_hash: str) -> bool:
        if content_hash in self._hash_registry:
            return True
        # Check filesystem
        matching = list(self.base_dir.glob(f"{content_hash}.*"))
        return len(matching) > 0

    def store_raw(self, filename: str, data: bytes, mime_type: str) -> tuple[RawDocument, bool]:
        content_hash = self.compute_sha256(data)
        ext = Path(filename).suffix or ".bin"

        # Check deduplication
        if content_hash in self._hash_registry:
            return self._hash_registry[content_hash], False

        target_path = self.base_dir / f"{content_hash}{ext}"
        is_new = not target_path.exists()

        if is_new:
            target_path.write_bytes(data)

        raw_doc = RawDocument(
            id=uuid4(),
            filename=filename,
            content_hash=content_hash,
            mime_type=mime_type,
            byte_size=len(data),
            storage_uri=str(target_path.resolve()),
        )
        self._hash_registry[content_hash] = raw_doc
        return raw_doc, is_new

    def retrieve_raw(self, storage_uri: str) -> bytes:
        path = Path(storage_uri)
        if not path.exists():
            raise FileNotFoundError(f"Raw artifact not found at {storage_uri}")
        return path.read_bytes()
