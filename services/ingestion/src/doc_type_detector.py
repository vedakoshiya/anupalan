"""Document type and format detector.

Identifies Native PDF, Scanned PDF, HTML, and DOCX files using magic bytes,
stream analysis, and layout heuristics matching FR-002.
"""

import io
import re
import zipfile
from pathlib import Path
from services.ingestion.src.models import DocumentType


class DocumentTypeDetector:
    """Inspects byte payloads to classify document formats and determine OCR requirement."""

    PDF_MAGIC = b"%PDF-"
    ZIP_MAGIC = b"PK\x03\x04"

    def detect_format(self, data: bytes, filename: str = "") -> tuple[DocumentType, str]:
        """Detects DocumentType and MIME type from bytes and optional filename."""
        if not data:
            return DocumentType.UNKNOWN, "application/octet-stream"

        ext = Path(filename).suffix.lower() if filename else ""

        # 1. PDF Detection
        if data.startswith(self.PDF_MAGIC):
            is_scanned = self._is_scanned_pdf(data)
            doc_type = DocumentType.SCANNED_PDF if is_scanned else DocumentType.NATIVE_PDF
            return doc_type, "application/pdf"

        # 2. DOCX Detection (ZIP file containing word/document.xml)
        if data.startswith(self.ZIP_MAGIC):
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    if "word/document.xml" in zf.namelist():
                        return (
                            DocumentType.DOCX,
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )
            except Exception:
                pass

        # 3. HTML Detection
        head_sample = data[:2048].decode("utf-8", errors="ignore").lower()
        if "<!doctype html" in head_sample or "<html" in head_sample or "<head" in head_sample:
            return DocumentType.HTML, "text/html"

        # 4. Fallback on extension if content matches text
        if ext in (".html", ".htm"):
            return DocumentType.HTML, "text/html"
        if ext == ".docx":
            return DocumentType.DOCX, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if ext == ".pdf":
            return DocumentType.NATIVE_PDF, "application/pdf"

        return DocumentType.UNKNOWN, "application/octet-stream"

    def _is_scanned_pdf(self, data: bytes) -> bool:
        """Heuristic check: detects if a PDF has little or no extractable text streams."""
        # Check for standard PDF text-showing operators: 'BT' (Begin Text), 'Tj', 'TJ', 'ET'
        text_operator_count = len(re.findall(rb"\bBT\b", data))
        image_count = len(re.findall(rb"/Subtype\s*/Image", data))

        # If has images and practically zero text operators, it's a scanned document
        if image_count > 0 and text_operator_count < 3:
            return True

        return False
