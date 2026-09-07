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
                timeout=10.0
            )
            response = await model_gateway.rerank(request)
            scores = response.scores
        except Exception as e:
            logger.info("Gateway reranker unavailable (%s); using lightweight CPU reranker.", e)
            scores = self._cpu_fast_rerank(query, texts)
            
        scored = []
        for doc, score in zip(documents, scores):
            scored.append({**doc, "_rerank_score": float(score)})

        scored.sort(key=lambda x: x["_rerank_score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _cpu_fast_rerank(query: str, documents: list[str]) -> list[float]:
        """
        Lightweight CPU cross-scoring fallback (Priority 7 in blueprint).
        Calculates term-frequency and lexical co-occurrence density
        without allocating any GPU VRAM.
        """
        import re
        import math
        tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
        if not tokens:
            return [0.5] * len(documents)

        scores = []
        for text in documents:
            lower = text.lower()
            if not lower:
                scores.append(0.0)
                continue

            matches = sum(1 for t in tokens if t in lower)
            freq = sum(lower.count(t) for t in tokens)
            length_factor = 1.0 / (1.0 + math.log(max(1, len(lower.split()))))
            score = (matches / len(tokens)) * 0.7 + min(0.3, freq * 0.05 * length_factor)
            scores.append(round(min(1.0, max(0.0, score)), 4))

        return scores



# Global instance
reranker_service = RerankerService()
