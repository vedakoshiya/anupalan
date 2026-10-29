"""Production Ingestion Pipeline Orchestrator for Anupalan.

Integrates immutable storage, format detection, OCR quality scoring,
layout parsing, metadata extraction, structure-aware chunking, and version graph assembly.
"""

from pathlib import Path
from uuid import UUID, uuid4

from services.ingestion.src.chunker import StatutoryChunk, StructureAwareChunker
from services.ingestion.src.doc_type_detector import DocumentTypeDetector
from services.ingestion.src.layout_parser import LayoutAwareParser
from services.ingestion.src.metadata_extractor import MetadataExtractor
from services.ingestion.src.models import (
    DocumentType,
    IngestionResult,
    IngestionStatus,
    ParsedDocument,
    RawDocument,
)
from services.ingestion.src.ocr_engine import BaseOCREngine, PluggableOCREngine
from services.ingestion.src.storage import BaseStorageBackend, LocalImmutableStorage
from services.ingestion.src.version_graph import InstrumentNode, LegalVersionGraph


class IngestionPipeline:
    """Scalable and idempotent ingestion orchestrator complying with FR-001 through FR-008."""

    def __init__(
        self,
        storage: BaseStorageBackend,
        ocr_engine: BaseOCREngine | None = None,
        version_graph: LegalVersionGraph | None = None,
    ):
        self.storage = storage
        self.ocr_engine = ocr_engine or PluggableOCREngine()
        self.version_graph = version_graph or LegalVersionGraph()
        self.detector = DocumentTypeDetector()
        self.layout_parser = LayoutAwareParser()
        self.metadata_extractor = MetadataExtractor()
        self.chunker = StructureAwareChunker()

        # In-memory indexed stores (in production, connected to PostgreSQL + pgvector)
        self.indexed_chunks: dict[UUID, StatutoryChunk] = {}
        self.ingestion_history: dict[str, IngestionResult] = {}

    def ingest_bytes(
        self,
        filename: str,
        data: bytes,
        mime_type: str | None = None,
        force_reindex: bool = False,
    ) -> IngestionResult:
        """Processes a single raw document through the full ingestion pipeline."""
        content_hash = LocalImmutableStorage.compute_sha256(data)

        # 1. Deduplication check (FR-007)
        if not force_reindex and content_hash in self.ingestion_history:
            prev_result = self.ingestion_history[content_hash]
            return IngestionResult(
                document_id=prev_result.document_id,
                filename=filename,
                content_hash=content_hash,
                status=IngestionStatus.SKIPPED_DUPLICATE,
                chunks_created=0,
                quality_score=prev_result.quality_score,
                flagged_pages=prev_result.flagged_pages,
            )

        # 2. Store raw artifact immutably (FR-008)
        detected_type, detected_mime = self.detector.detect_format(data, filename)
        final_mime = mime_type or detected_mime
        raw_doc, _ = self.storage.store_raw(filename, data, final_mime)

        # 3. OCR and Quality Evaluation (FR-003)
        pages, quality_report = self.ocr_engine.extract_text_and_quality(data, final_mime)
        full_text = "\n\n".join(pages)

        # 4. Metadata Extraction (FR-005)
        metadata = self.metadata_extractor.extract_metadata(full_text, filename)

        # 5. Layout-Aware Parsing (FR-004)
        sections = self.layout_parser.parse_pages(pages)

        # Flatten sections and clauses for structure-aware chunker
        chunk_clauses_payload = []
        for sec in sections:
            for cl in sec.clauses:
                chunk_clauses_payload.append({
                    "path": cl.path,
                    "text": cl.text,
                    "type": cl.clause_type,
                })
            for tbl in sec.tables:
                chunk_clauses_payload.append({
                    "path": f"{sec.path} > Table",
                    "type": "table",
                    "headers": tbl.headers,
                    "rows": tbl.rows,
                })

        # 6. Structure-Aware Chunking with Contextual Headers (FR-010, FR-011, FR-012)
        statutory_chunks = self.chunker.chunk_clauses(
            instrument_id=raw_doc.id,
            authority=metadata.authority,
            instrument_title=f"{metadata.instrument_type.capitalize()} {metadata.number}",
            clauses=chunk_clauses_payload,
            effective_from=metadata.effective_from,
            effective_to=metadata.effective_to,
            jurisdiction=metadata.jurisdiction,
            subjects=metadata.subjects,
        )

        for c in statutory_chunks:
            self.indexed_chunks[c.id] = c

        # 7. Update Legal Version Graph (FR-006)
        inst_node = InstrumentNode(
            id=raw_doc.id,
            code=metadata.number,
            number=metadata.number,
            title=metadata.title,
            issued_on=metadata.issued_on,
            effective_from=metadata.effective_from,
            effective_to=metadata.effective_to,
            jurisdiction=metadata.jurisdiction,
        )
        self.version_graph.add_instrument(inst_node)

        for rel in metadata.relations:
            if rel["target_number"] in self.version_graph.nodes:
                self.version_graph.add_relation(
                    from_code=metadata.number,
                    to_code=rel["target_number"],
                    relation=rel["relation"],
                    effective_from=rel["effective_from"],
                )

        status = IngestionStatus.NEEDS_REVIEW if quality_report.requires_curator_review else IngestionStatus.INGESTED

        result = IngestionResult(
            document_id=raw_doc.id,
            filename=filename,
            content_hash=content_hash,
            status=status,
            chunks_created=len(statutory_chunks),
            quality_score=quality_report.overall_score,
            flagged_pages=quality_report.flagged_pages,
        )

        self.ingestion_history[content_hash] = result
        return result

    def ingest_file(self, file_path: Path) -> IngestionResult:
        """Helper to read and ingest a local file path."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        data = path.read_bytes()
        return self.ingest_bytes(path.name, data)
