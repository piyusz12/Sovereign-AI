"""
Sovereign AI Workbench — Adaptive RAG

Implements intelligent retrieval with:
- Query analysis and reformulation
- Relevance grading
- Iterative query rewriting on poor results
- Fail-closed refusal after max attempts (honest refusal)

Flow:
    Question → Query Analysis → Search → Rerank → Grade Relevance
        ├── GOOD → Answer with citations
        └── BAD → Rewrite query → Search again
                   After 3 failed attempts → "No reliable internal evidence"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from backend.rag.retriever import HybridRetriever, hybrid_retriever
from backend.rag.reranker import RerankerService, reranker_service
from backend.rag.embedder import EmbeddingService, embedding_service

logger = logging.getLogger("sovereign.rag.adaptive")

MAX_RETRIEVAL_ATTEMPTS = 2
MIN_RELEVANCE_THRESHOLD = 0.3


@dataclass
class RAGResult:
    """Result from the adaptive RAG pipeline."""
    answer: str
    sources: list[dict]
    query_rewrites: list[str]
    attempts: int
    confidence: float
    status: str  # "answered", "insufficient_evidence", "error"


class AdaptiveRAG:
    """
    Adaptive RAG pipeline with quality-aware retrieval.

    Key behaviors:
    1. Grades retrieved documents for relevance
    2. Rewrites queries when retrieval is poor
    3. Refuses to fabricate answers when evidence is insufficient
    4. Tracks all query reformulations for audit
    """

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        reranker: Optional[RerankerService] = None,
        embedder: Optional[EmbeddingService] = None,
        max_attempts: int = MAX_RETRIEVAL_ATTEMPTS,
        relevance_threshold: float = MIN_RELEVANCE_THRESHOLD,
    ):
        self.retriever = retriever or hybrid_retriever
        self.reranker = reranker or reranker_service
        self.embedder = embedder or embedding_service
        self.max_attempts = max_attempts
        self.relevance_threshold = relevance_threshold

    async def query(
        self,
        question: str,
        user_role: str = "engineering",
        department_filter: Optional[str] = None,
        top_k: int = 5,
    ) -> RAGResult:
        """
        Execute adaptive RAG pipeline.

        Args:
            question: User's question
            user_role: RBAC role for document access
            department_filter: Optional department to filter by
            top_k: Number of final documents to use

        Returns:
            RAGResult with answer, sources, and status
        """
        query_rewrites: list[str] = []
        current_query = question

        for attempt in range(1, self.max_attempts + 1):
            logger.info("RAG attempt %d/%d: '%s'", attempt, self.max_attempts, current_query)

            # Step 1: Embed the query
            query_embedding = await self.embedder.embed_text(current_query)

            # Step 2: Hybrid search with RBAC
            candidates = await self.retriever.search(
                query=current_query,
                query_embedding=query_embedding,
                top_k=20,
                user_role=user_role,
                department_filter=department_filter,
            )

            if not candidates:
                logger.info("No candidates found, attempting query rewrite")
                current_query = self._rewrite_query(question, current_query, attempt)
                query_rewrites.append(current_query)
                continue

            # Step 3: Rerank
            reranked = await self.reranker.rerank(
                query=current_query,
                documents=candidates,
                top_k=top_k,
            )

            # Step 4: Grade relevance
            relevant_docs = self._grade_relevance(reranked)

            if relevant_docs:
                # Good results — generate answer
                return RAGResult(
                    answer=self._format_answer(question, relevant_docs),
                    sources=relevant_docs,
                    query_rewrites=query_rewrites,
                    attempts=attempt,
                    confidence=self._calculate_confidence(relevant_docs),
                    status="answered",
                )

            # Poor results — rewrite query
            logger.info("Relevance below threshold, rewriting query")
            current_query = self._rewrite_query(question, current_query, attempt)
            query_rewrites.append(current_query)

        # All attempts exhausted — fail closed
        logger.warning("RAG exhausted %d attempts — refusing to fabricate", self.max_attempts)
        return RAGResult(
            answer=(
                "I do not have sufficient internal evidence to provide a reliable answer "
                "to this question. No relevant documents were found in the knowledge base "
                "after multiple search attempts. Please verify the question or upload "
                "additional relevant documents."
            ),
            sources=[],
            query_rewrites=query_rewrites,
            attempts=self.max_attempts,
            confidence=0.0,
            status="insufficient_evidence",
        )

    def _grade_relevance(self, documents: list[dict]) -> list[dict]:
        """
        Grade document relevance.
        Returns only documents above the relevance threshold.
        """
        relevant = []
        for doc in documents:
            score = doc.get("_rerank_score", doc.get("_rrf_score", 0.0))
            if score >= self.relevance_threshold:
                relevant.append(doc)
        return relevant

    def _rewrite_query(self, original: str, current: str, attempt: int) -> str:
        """
        Rewrite query for better retrieval.
        TODO Phase 19: Use LLM for intelligent query reformulation.
        For now, uses simple heuristics.
        """
        strategies = [
            # Attempt 1: Add more context words
            lambda o, c: f"{o} details specifications",
            # Attempt 2: Simplify
            lambda o, c: " ".join(o.split()[:5]),
            # Attempt 3: Rephrase
            lambda o, c: f"information about {o}",
        ]

        idx = min(attempt - 1, len(strategies) - 1)
        return strategies[idx](original, current)

    @staticmethod
    def _format_answer(question: str, sources: list[dict]) -> str:
        """
        Format answer with source citations.
        TODO Phase 19: Use LLM for answer generation.
        """
        source_texts = []
        for i, src in enumerate(sources, 1):
            doc_id = src.get("document_id", "unknown")
            page = src.get("page", "?")
            text = src.get("text", "")[:200]
            source_texts.append(f"[{i}] {doc_id} p.{page}: {text}")

        return (
            f"Based on {len(sources)} internal document(s):\n\n"
            + "\n".join(source_texts)
        )

    @staticmethod
    def _calculate_confidence(sources: list[dict]) -> float:
        """Calculate confidence score based on source quality."""
        if not sources:
            return 0.0
        scores = [
            s.get("_rerank_score", s.get("_rrf_score", 0.0)) for s in sources
        ]
        return min(sum(scores) / len(scores), 1.0)


# Global instance
adaptive_rag = AdaptiveRAG()
