"""
Tests for Phase 12 Document Ingestion Pipeline.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.documents.ingest import DocumentIngestionPipeline, IngestResult
from backend.rag.chunker import DocumentChunker
from backend.documents.parser import ParsedDocument


@pytest.fixture
def ingestion_pipeline():
    return DocumentIngestionPipeline()


@pytest.mark.asyncio
async def test_ingest_flow(ingestion_pipeline, tmp_path):
    """Test the full ingestion pipeline flow using mocks for external services."""
    
    # Create a dummy file
    dummy_file = tmp_path / "test_doc.txt"
    dummy_file.write_text("This is a test document.")
    
    # Mock parser
    mock_parsed_doc = ParsedDocument(
        sections=[],
        tables=[],
        images=[],
        metadata={"filename": "test_doc.txt", "type": ".txt"},
        page_count=1,
        raw_text="This is a test document."
    )
    
    with patch("backend.documents.parser.DoclingParser.parse", new_callable=AsyncMock) as mock_parse, \
         patch("backend.rag.embedder.EmbeddingService.embed_document_chunks", new_callable=AsyncMock) as mock_embed, \
         patch("backend.rag.retriever.HybridRetriever.upsert_chunks", new_callable=AsyncMock) as mock_upsert:
        
        mock_parse.return_value = mock_parsed_doc
        
        # Mock embedder to just return chunks with dummy embeddings
        async def dummy_embed(chunks, **kwargs):
            for c in chunks:
                c["embedding"] = [0.1, 0.2, 0.3]
            return chunks
        mock_embed.side_effect = dummy_embed
        
        # Mock retriever
        mock_upsert.return_value = True
        
        result = await ingestion_pipeline.ingest(
            file_path=str(dummy_file),
            department="engineering",
            access_level="restricted",
            description="Test upload"
        )
        
        # Assertions
        assert isinstance(result, IngestResult)
        assert result.status == "success"
        assert result.filename == "test_doc.txt"
        assert result.document_type == "text"
        assert result.pages == 1
        assert result.chunks > 0
        
        # Verify mocks were called
        mock_parse.assert_called_once_with(str(dummy_file))
        mock_embed.assert_called_once()
        mock_upsert.assert_called_once()


def test_document_chunker():
    """Test that chunker correctly splits and attaches metadata."""
    chunker = DocumentChunker(chunk_size=10, chunk_overlap=0)
    
    text = "Hello world. This is a test."
    metadata = {"doc_id": "123", "access_level": "public"}
    
    chunks = chunker.chunk_document(text, metadata)
    
    assert len(chunks) > 0
    assert chunks[0]["doc_id"] == "123"
    assert chunks[0]["access_level"] == "public"
    assert "chunk_index" in chunks[0]
