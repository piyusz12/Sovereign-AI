"""
Sovereign AI Workbench — Reranker

Cross-encoder reranking using Qwen3-Reranker-0.6B.
Refines initial retrieval results to select the most relevant documents.

Flow: Query + 20 candidates → Reranker → Top 5
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger("sovereign.rag.reranker")

DEFAULT_RERANKER_MODEL = "qwen3-reranker:0.6b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"


class RerankerService:
    """
    Cross-encoder reranking service.
    Uses Qwen3-Reranker-0.6B via Ollama.
    Upgradeable to Infinity for production (Phase 26).
    """

    def __init__(
        self,
        model: str = DEFAULT_RERANKER_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
    ):
        self.model = model
        self.base_url = base_url

    async def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 5,
        text_field: str = "text",
    ) -> list[dict]:
        """
        Rerank documents by relevance to the query.

        Args:
            query: The search query
            documents: List of document dicts with text content
            top_k: Number of top results to return
            text_field: Key for text content in document dicts

        Returns:
            Top K documents sorted by relevance score
        """
        if not documents:
            return []

        # TODO Phase 16: Implement actual reranker API call
        # For now, use a placeholder scoring based on keyword overlap
        scored = []
        query_words = set(query.lower().split())

        for doc in documents:
            text = doc.get(text_field, "").lower()
            text_words = set(text.split())
            overlap = len(query_words & text_words)
            score = overlap / max(len(query_words), 1)
            scored.append({**doc, "_rerank_score": score})

        scored.sort(key=lambda x: x["_rerank_score"], reverse=True)
        return scored[:top_k]

    async def _call_reranker_api(
        self, query: str, texts: list[str]
    ) -> list[float]:
        """
        Call the reranker model API.
        Returns relevance scores for each text.
        """
        try:
            # Reranker API format depends on the serving backend
            # Infinity uses a different format than Ollama
            pairs = [{"query": query, "text": text} for text in texts]

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/rerank",
                    json={"model": self.model, "pairs": pairs},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("scores", [0.0] * len(texts))
        except Exception as e:
            logger.error("Reranker API call failed: %s", e)
            return [0.0] * len(texts)


# Global instance
reranker_service = RerankerService()
