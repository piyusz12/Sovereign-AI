"""
Sovereign AI Workbench — Document Chunker

Intelligent document chunking that preserves section boundaries and metadata.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

logger = logging.getLogger("sovereign.documents.chunker")


class DocumentChunker:
    """
    Chunk documents intelligently for RAG.
    Preserves section boundaries, table integrity, and metadata.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_text(
        self,
        text: str,
        document_id: str,
        metadata: Optional[dict] = None,
    ) -> list[dict]:
        """
        Chunk text into overlapping segments with metadata.

        Each chunk includes:
        - chunk_id, document_id, text, page, position, metadata
        """
        if not text.strip():
            return []

        meta = metadata or {}
        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk_text = " ".join(words[start:end])

            if len(chunk_text) >= self.min_chunk_size or start + self.chunk_size >= len(words):
                chunks.append({
                    "chunk_id": f"{document_id}_chunk_{len(chunks)}",
                    "document_id": document_id,
                    "text": chunk_text,
                    "position": len(chunks),
                    "word_start": start,
                    "word_end": end,
                    **meta,
                })

            start += self.chunk_size - self.chunk_overlap

        logger.info(
            "Document %s chunked into %d chunks (size=%d, overlap=%d)",
            document_id, len(chunks), self.chunk_size, self.chunk_overlap,
        )
        return chunks

    def chunk_sections(
        self,
        sections: list[dict],
        document_id: str,
        base_metadata: Optional[dict] = None,
    ) -> list[dict]:
        """
        Chunk document sections, preserving section boundaries.
        Each section is chunked independently to avoid mixing content.
        """
        all_chunks = []
        meta = base_metadata or {}

        for section in sections:
            section_text = section.get("text", "")
            section_meta = {
                **meta,
                "section_title": section.get("title", ""),
                "section_level": section.get("level", 0),
                "page": section.get("page", None),
            }

            chunks = self.chunk_text(section_text, document_id, section_meta)
            all_chunks.extend(chunks)

        return all_chunks


# Global instance
document_chunker = DocumentChunker()
