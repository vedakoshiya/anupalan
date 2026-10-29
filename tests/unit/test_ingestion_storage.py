"""Unit tests for immutable storage backend and content-addressable deduplication."""

import tempfile
import unittest
from pathlib import Path
from services.ingestion.src.storage import LocalImmutableStorage


class TestStorageBackend(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = LocalImmutableStorage(base_directory=Path(self.temp_dir.name))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compute_sha256(self):
        data = b"Hello Anupalan Compliance Engine"
        h1 = LocalImmutableStorage.compute_sha256(data)
        h2 = LocalImmutableStorage.compute_sha256(data)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_store_raw_and_deduplicate(self):
        data = b"Notification No. 11/2017-CT Rate content"

        # First store
        raw_doc, is_new = self.storage.store_raw("notif.txt", data, "text/plain")
        self.assertTrue(is_new)
        self.assertEqual(raw_doc.byte_size, len(data))
        self.assertTrue(self.storage.exists(raw_doc.content_hash))

        # Re-store exact same data -> must return duplicate flag
        raw_doc2, is_new2 = self.storage.store_raw("notif_copy.txt", data, "text/plain")
        self.assertFalse(is_new2)
        self.assertEqual(raw_doc.content_hash, raw_doc2.content_hash)

    def test_retrieve_raw(self):
        data = b"Official Circular Content"
        raw_doc, _ = self.storage.store_raw("circ.txt", data, "text/plain")
        retrieved = self.storage.retrieve_raw(raw_doc.storage_uri)
        self.assertEqual(retrieved, data)


if __name__ == "__main__":
    unittest.main()
