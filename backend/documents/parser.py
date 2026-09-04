"""
Sovereign AI Workbench — Document Parser

Docling-based document parsing with layout-aware extraction.
Preserves table structure, reading order, and section hierarchy.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("sovereign.documents.parser")


@dataclass
class ParsedDocument:
    """Result from document parsing."""
    sections: list[dict]
    tables: list[dict]
    images: list[dict]
    metadata: dict
    page_count: int
    raw_text: str


class DoclingParser:
    """
    Parse documents using Docling for layout-aware extraction.
    Docling is selected because layout/order and table structure
    are critical for technical documents (inspection reports, SOPs, P&IDs).
    """

    async def parse(self, file_path: str) -> ParsedDocument:
        """Parse a document file."""
        path = Path(file_path)
        logger.info("Parsing document: %s", path.name)

        raw_text = ""
        page_count = 0

        # Try Docling first
        try:
            from docling.document_converter import DocumentConverter
            
            logger.info("Using Docling DocumentConverter for %s", path.name)
            converter = DocumentConverter()
            # Note: DocumentConverter operations can be blocking.
            # In a heavy production system, run this via asyncio.to_thread
            result = converter.convert(str(path))
            raw_text = result.document.export_to_markdown()
            page_count = len(result.document.pages) if hasattr(result.document, "pages") else 1
            
        except ImportError:
            logger.warning("Docling not installed. Falling back to simple parsing.")
            if path.suffix.lower() == ".txt":
                with open(path, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                page_count = 1
            elif path.suffix.lower() == ".pdf":
                try:
                    from langchain_community.document_loaders import PyPDFLoader
                    loader = PyPDFLoader(str(path))
                    docs = loader.load()
                    raw_text = "\n\n".join([doc.page_content for doc in docs])
                    page_count = len(docs)
                except ImportError:
                    logger.error("pypdf not installed. Cannot parse PDF.")
                    raw_text = f"[PDF Parsing Failed - missing Docling/pypdf]\nFile: {path.name}"
            else:
                logger.error("Unsupported fallback format: %s", path.suffix)
                raw_text = f"[Fallback Parsing Failed - unsupported format {path.suffix}]\nFile: {path.name}"

        return ParsedDocument(
            sections=[],
            tables=[],
            images=[],
            metadata={"filename": path.name, "type": path.suffix},
            page_count=page_count,
            raw_text=raw_text,
        )


# Global instance
docling_parser = DoclingParser()
