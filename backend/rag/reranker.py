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

from backend.settings import settings

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
        
        # 1. Try to use external API first (Infinity / TEI)
        scores = await self._call_reranker_api(query, texts)
        
        # 2. If API fails/unreachable, fallback to local sentence-transformers
        if not any(scores):
            scores = await self._call_local_reranker(query, texts)
            
        scored = []
        for doc, score in zip(documents, scores):
            scored.append({**doc, "_rerank_score": float(score)})

        scored.sort(key=lambda x: x["_rerank_score"], reverse=True)
        return scored[:top_k]

    async def _call_reranker_api(
        self, query: str, texts: list[str]
    ) -> list[float]:
        """
        Call the reranker model API.
        Returns relevance scores for each text.
        """
        # 1. Try Infinity API first (Phase 26)
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.post(
                    f"{settings.infinity_base_url}/rerank",
                    json={
                        "model": self.model,
                        "query": query,
                        "documents": texts
                    },
                )
                response.raise_for_status()
                data = response.json()
                if "results" in data:
                    # Infinity usually returns results sorted by relevance_score but they contain the original index.
                    # We need to map them back to the original order of `texts`
                    scores = [0.0] * len(texts)
                    for result in data["results"]:
                        idx = result.get("index")
                        if idx is not None and 0 <= idx < len(texts):
                            scores[idx] = result.get("relevance_score", 0.0)
                    return scores
        except Exception as e:
            logger.debug("Infinity reranker API unreachable, falling back: %s", e)

        # 2. Try Ollama API next
        try:
            pairs = [{"query": query, "text": text} for text in texts]

            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/rerank",
                    json={"model": self.model, "pairs": pairs},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("scores", [0.0] * len(texts))
        except Exception as e:
            logger.debug("Ollama Reranker API unreachable, will use local fallback: %s", e)
            return []
            
    async def _call_local_reranker(
        self, query: str, texts: list[str]
    ) -> list[float]:
        """Local fallback using sentence-transformers CrossEncoder."""
        try:
            import asyncio
            from sentence_transformers import CrossEncoder

            if not self._local_model_loaded:
                logger.info("Loading local CrossEncoder reranker: %s", self.model)
                self._local_model = CrossEncoder(self.model, max_length=512)
                self._local_model_loaded = True
                
            pairs = [[query, text] for text in texts]
            # Offload heavy ML inference to thread pool
            scores = await asyncio.to_thread(self._local_model.predict, pairs)
            return scores.tolist() if hasattr(scores, "tolist") else list(scores)
        except ImportError:
            logger.warning("sentence-transformers not installed. Reranker disabled.")
            return [0.0] * len(texts)
        except Exception as e:
            logger.error("Local reranker failed: %s", e)
            return [0.0] * len(texts)


# Global instance
reranker_service = RerankerService()
