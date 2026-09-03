"""
Tests — RAG Pipeline

Verifies retrieval, reranking, and fail-closed behavior.
"""

import pytest
from backend.rag.retriever import BM25Retriever
from backend.rag.adaptive import AdaptiveRAG


@pytest.fixture
def sample_documents():
    return [
        {
            "document_id": "INS-001",
            "text": "Inspection of valve V-204 showed corrosion on the stem",
            "department": "engineering",
            "access_level": "engineering",
            "page": 14,
        },
        {
            "document_id": "SOP-223",
            "text": "Standard operating procedure for pump maintenance requires weekly checks",
            "department": "operations",
            "access_level": "operations",
            "page": 8,
        },
        {
            "document_id": "FIN-001",
            "text": "Q3 budget allocation for engineering department",
            "department": "finance",
            "access_level": "finance",
            "page": 1,
        },
    ]


@pytest.fixture
def bm25(sample_documents):
    retriever = BM25Retriever()
    retriever.index(sample_documents)
    return retriever


class TestBM25Retriever:
    """Test BM25 sparse retrieval."""

    def test_basic_search(self, bm25):
        """BM25 returns relevant results."""
        results = bm25.search("valve corrosion inspection")
        assert len(results) > 0
        assert results[0]["document_id"] == "INS-001"

    def test_rbac_engineering(self, bm25):
        """Engineering user sees engineering and operations docs."""
        results = bm25.search("maintenance", user_role="engineering")
        # Engineering should NOT see finance docs
        doc_ids = [r["document_id"] for r in results]
        assert "FIN-001" not in doc_ids

    def test_rbac_finance_hidden(self, bm25):
        """Finance documents hidden from engineering users."""
        results = bm25.search("budget allocation", user_role="engineering")
        doc_ids = [r["document_id"] for r in results]
        assert "FIN-001" not in doc_ids

    def test_admin_sees_all(self, bm25):
        """Admin user sees all documents."""
        results = bm25.search("budget", user_role="admin")
        doc_ids = [r["document_id"] for r in results]
        assert "FIN-001" in doc_ids

    def test_empty_query(self, bm25):
        """Empty query returns no results."""
        results = bm25.search("")
        assert len(results) == 0


class TestAdaptiveRAG:
    """Test adaptive RAG behavior."""

    @pytest.mark.asyncio
    async def test_insufficient_evidence_refusal(self):
        """RAG refuses to answer when no evidence found (fail-closed)."""
        rag = AdaptiveRAG(max_attempts=2)
        result = await rag.query("something completely irrelevant xyz123")
        assert result.status == "insufficient_evidence"
        assert "sufficient internal evidence" in result.answer.lower() or "reliable" in result.answer.lower()
