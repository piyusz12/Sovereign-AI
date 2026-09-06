"""
Sovereign AI Workbench — Reranker

Cross-encoder reranking using Qwen3-Reranker-0.6B.
Refines initial retrieval results to select the most relevant documents.

Flow: Query + 20 candidates → Reranker → Top 5
"""

from __future__ import annotations

import logging
from typing import Optional

from backend.settings import settings
from backend.model_gateway import model_gateway, GatewayRerankRequest
from backend.models.registry import get_model
from backend.models.router import route_task, RoutingRequest, TaskType
from backend.rag.exceptions import RetrievalServiceError

logger = logging.getLogger("sovereign.rag.reranker")

DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-base"
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
        self._local_model = None
        self._local_model_loaded = False

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

        texts = [doc.get(text_field, "") for doc in documents]
        
        route = route_task(RoutingRequest(task_type=TaskType.RERANKING))
        model_id = route.selected_model
        
        try:
            request = GatewayRerankRequest(
                model=model_id,
                query=query,
                documents=texts,
                timeout=30.0
            )
            response = await model_gateway.rerank(request)
            scores = response.scores
        except Exception as e:
            logger.error("Reranking failed: %s", e)
            raise RetrievalServiceError("Knowledge search is temporarily unavailable. No external service was contacted.") from e
            
        scored = []
        for doc, score in zip(documents, scores):
            scored.append({**doc, "_rerank_score": float(score)})

        scored.sort(key=lambda x: x["_rerank_score"], reverse=True)
        return scored[:top_k]



# Global instance
reranker_service = RerankerService()
