"""
Sovereign AI Workbench — Document Chunker

Splits parsed documents into semantic chunks for vector embedding.
Preserves metadata (document_id, department, access_level, chunk index)
for RBAC filtering and tracking.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger("sovereign.rag.chunker")


class DocumentChunker:
    """
    Chunks document text into smaller segments suitable for embedding.
    """

    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 128):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    def chunk_document(
        self,
        text: str,
        metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Split a document's text into chunks, attaching the provided metadata
        to every chunk along with a specific chunk index.
        """
        if not text.strip():
            logger.warning("Empty text provided for chunking.")
            return []

        # Split the text
        texts = self.text_splitter.split_text(text)
        
        chunks = []
        for i, chunk_text in enumerate(texts):
            chunk = {
                "text": chunk_text,
                "chunk_index": i,
                # Merge document-level metadata
                **metadata,
            }
            chunks.append(chunk)

        logger.info("Split document into %d chunks", len(chunks))
        return chunks


# Global instance
document_chunker = DocumentChunker()
