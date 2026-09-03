"""
Tests — Document Processing

Verifies document ingestion, chunking, and metadata extraction.
"""

import pytest
from backend.documents.chunker import DocumentChunker
from backend.documents.metadata import MetadataExtractor


@pytest.fixture
def chunker():
    return DocumentChunker(chunk_size=50, chunk_overlap=10)


class TestDocumentChunker:
    """Test document chunking."""

    def test_basic_chunking(self, chunker):
        """Text is chunked into overlapping segments."""
        text = " ".join([f"word{i}" for i in range(200)])
        chunks = chunker.chunk_text(text, "DOC-001")
        assert len(chunks) > 1
        assert all(c["document_id"] == "DOC-001" for c in chunks)

    def test_chunk_metadata(self, chunker):
        """Chunks carry document metadata."""
        text = "This is a test document with enough words to chunk properly."
        chunks = chunker.chunk_text(text, "DOC-002", {"department": "engineering"})
        assert all(c.get("department") == "engineering" for c in chunks)

    def test_empty_text(self, chunker):
        """Empty text produces no chunks."""
        chunks = chunker.chunk_text("", "DOC-003")
        assert len(chunks) == 0

    def test_section_chunking(self, chunker):
        """Section-aware chunking preserves boundaries."""
        sections = [
            {"title": "Section 1", "text": " ".join(["word"] * 100), "level": 1},
            {"title": "Section 2", "text": " ".join(["word"] * 100), "level": 1},
        ]
        chunks = chunker.chunk_sections(sections, "DOC-004")
        assert len(chunks) > 0


class TestMetadataExtractor:
    """Test metadata extraction."""

    def test_basic_extraction(self):
        extractor = MetadataExtractor()
        meta = extractor.extract("./data/documents/report.pdf", "DOC-001")
        assert meta.document_id == "DOC-001"
        assert meta.document_type == "pdf"
        assert meta.filename == "report.pdf"

    def test_qdrant_payload(self):
        extractor = MetadataExtractor()
        meta = extractor.extract("./data/documents/test.docx", "DOC-002", department="finance")
        payload = meta.to_qdrant_payload()
        assert payload["department"] == "finance"
        assert payload["document_type"] == "docx"
