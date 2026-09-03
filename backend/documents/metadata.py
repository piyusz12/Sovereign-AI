"""
Sovereign AI Workbench — Document Metadata Extractor

Extracts and classifies document metadata for RBAC-aware storage.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("sovereign.documents.metadata")


@dataclass
class DocumentMetadata:
    """Extracted document metadata."""
    document_id: str
    filename: str
    document_type: str
    department: str
    access_level: str
    title: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    page_count: int = 0
    description: Optional[str] = None
    tags: list[str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_qdrant_payload(self) -> dict:
        """Convert to Qdrant-compatible metadata payload."""
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "document_type": self.document_type,
            "department": self.department,
            "access_level": self.access_level,
            "title": self.title or self.filename,
            "author": self.author,
            "date": self.date,
            "page_count": self.page_count,
            "tags": self.tags,
        }


class MetadataExtractor:
    """Extract metadata from documents for RBAC and retrieval."""

    def extract(
        self,
        file_path: str,
        document_id: str,
        department: str = "engineering",
        access_level: str = "engineering",
    ) -> DocumentMetadata:
        """Extract metadata from a document file."""
        path = Path(file_path)

        return DocumentMetadata(
            document_id=document_id,
            filename=path.name,
            document_type=path.suffix.lstrip("."),
            department=department,
            access_level=access_level,
            title=path.stem.replace("_", " ").replace("-", " ").title(),
        )


# Global instance
metadata_extractor = MetadataExtractor()
