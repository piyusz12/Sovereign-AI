"""
Sovereign AI Workbench — Document Ingestion Pipeline

Orchestrates the full document processing flow:
    Upload → Detect type → Docling → OCR → Tables → Sections →
    Metadata → Chunks → Embeddings → Qdrant
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("sovereign.documents.ingest")


@dataclass
class IngestResult:
    """Result from document ingestion."""
    document_id: str
    filename: str
    document_type: str
    pages: int
    chunks: int
    tables_found: int
    images_found: int
    processing_time_ms: float
    status: str


class DocumentIngestionPipeline:
    """
    Full document ingestion pipeline.

    Flow:
    1. Detect document type (PDF, DOCX, image, etc.)
    2. Extract content via Docling (layout-aware parsing)
    3. Run PaddleOCR on scanned pages
    4. Extract tables and structure
    5. Generate metadata
    6. Chunk intelligently (preserving section boundaries)
    7. Embed chunks
    8. Store in Qdrant with metadata
    """

    async def ingest(
        self,
        file_path: str,
        department: str = "engineering",
        access_level: str = "engineering",
        description: Optional[str] = None,
    ) -> IngestResult:
        """
        Ingest a document through the full pipeline.
        """
        import time
        start_time = time.time()
        
        doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
        path = Path(file_path)

        logger.info("Ingesting document: %s → %s", path.name, doc_id)

        # Step 1: Detect type
        doc_type = self._detect_type(path)

        # Imports inside method to avoid circular dependencies if any
        from backend.documents.parser import docling_parser
        from backend.rag.chunker import document_chunker
        from backend.rag.embedder import embedding_service
        from backend.rag.retriever import hybrid_retriever

        try:
            # Step 2: Parse (Docling / Fallback)
            parsed_doc = await docling_parser.parse(str(path))
            
            # Step 3: Metadata
            metadata = {
                "document_id": doc_id,
                "filename": path.name,
                "document_type": doc_type,
                "department": department,
                "access_level": access_level,
                "description": description or "",
            }
            
            # Step 4: Chunking
            chunks = document_chunker.chunk_document(parsed_doc.raw_text, metadata)
            
            # Step 5: Embedding
            embedded_chunks = await embedding_service.embed_document_chunks(chunks)
            
            # Step 6: Qdrant Storage
            success = await hybrid_retriever.upsert_chunks(embedded_chunks)
            
            processing_time = (time.time() - start_time) * 1000
            
            return IngestResult(
                document_id=doc_id,
                filename=path.name,
                document_type=doc_type,
                pages=parsed_doc.page_count,
                chunks=len(embedded_chunks),
                tables_found=len(parsed_doc.tables),
                images_found=len(parsed_doc.images),
                processing_time_ms=processing_time,
                status="success" if success else "failed_qdrant",
            )
            
        except Exception as e:
            logger.error("Failed to ingest document %s: %s", path.name, e, exc_info=True)
            return IngestResult(
                document_id=doc_id,
                filename=path.name,
                document_type=doc_type,
                pages=0,
                chunks=0,
                tables_found=0,
                images_found=0,
                processing_time_ms=(time.time() - start_time) * 1000,
                status=f"error: {str(e)}",
            )

    @staticmethod
    def _detect_type(path: Path) -> str:
        """Detect document type from extension."""
        ext_map = {
            ".pdf": "pdf",
            ".docx": "docx",
            ".xlsx": "xlsx",
            ".pptx": "pptx",
            ".png": "image",
            ".jpg": "image",
            ".jpeg": "image",
            ".tiff": "image",
            ".tif": "image",
            ".csv": "csv",
            ".txt": "text",
        }
        return ext_map.get(path.suffix.lower(), "unknown")


# Global instance
ingestion_pipeline = DocumentIngestionPipeline()
