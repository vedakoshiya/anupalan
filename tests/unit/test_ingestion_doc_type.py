"""Unit tests for document format and type detection."""

import unittest
from services.ingestion.src.doc_type_detector import DocumentTypeDetector
from services.ingestion.src.models import DocumentType


class TestDocumentTypeDetector(unittest.TestCase):
    def setUp(self):
        self.detector = DocumentTypeDetector()

    def test_detect_native_pdf(self):
        # PDF with text operator 'BT' (Begin Text)
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nstream\nBT /F1 12 Tf (Job Work Text) Tj ET\nendstream\nendobj"
        doc_type, mime = self.detector.detect_format(pdf_bytes, "notification.pdf")
        self.assertEqual(doc_type, DocumentType.NATIVE_PDF)
        self.assertEqual(mime, "application/pdf")

    def test_detect_scanned_pdf(self):
        # PDF with Image XObject and zero text operators
        scanned_bytes = b"%PDF-1.5\n/Subtype /Image /Width 800 /Height 1200\nendobj"
        doc_type, mime = self.detector.detect_format(scanned_bytes, "scan.pdf")
        self.assertEqual(doc_type, DocumentType.SCANNED_PDF)
        self.assertEqual(mime, "application/pdf")

    def test_detect_html(self):
        html_bytes = b"<!DOCTYPE html><html><head><title>Circular</title></head><body>GST Rule</body></html>"
        doc_type, mime = self.detector.detect_format(html_bytes, "circular.html")
        self.assertEqual(doc_type, DocumentType.HTML)
        self.assertEqual(mime, "text/html")

    def test_detect_empty_or_unknown(self):
        doc_type, mime = self.detector.detect_format(b"", "")
        self.assertEqual(doc_type, DocumentType.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
