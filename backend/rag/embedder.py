"""
Sovereign AI Workbench — Embedding Service

Generates embeddings using Qwen3-Embedding-0.6B via local inference.
Small enough to coexist with a heavy model on the RTX 4060 8GB.
"""

from __future__ import annotations

import logging
from typing import Optional

from backend.settings import settings
from backend.model_gateway import model_gateway, GatewayEmbeddingRequest
from backend.models.registry import get_model
from backend.models.router import route_task, RoutingRequest, TaskType
from backend.rag.cache import embedding_cache
from backend.rag.exceptions import RetrievalServiceError

logger = logging.getLogger("sovereign.rag.embedder")

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_EMBEDDING_DIM = 384
DEFAULT_OLLAMA_URL = "http://localhost:11434"


class EmbeddingService:
    """
    Local embedding service using Ollama.
    Upgradeable to Infinity for production serving (Phase 26).
    """

    def __init__(
        self,
        model: str = DEFAULT_EMBEDDING_MODEL,
        dimension: int = DEFAULT_EMBEDDING_DIM,
        base_url: str = DEFAULT_OLLAMA_URL,
    ):
        self.model = model
        self.dimension = dimension
        self.base_url = base_url
        self._local_model = None
        self._local_model_loaded = False

    async def embed_text(self, text: str, model_id: str = None) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed_batch([text], model_id=model_id)
        return embeddings[0] if embeddings else [0.0] * self.dimension

    async def embed_batch(self, texts: list[str], model_id: str = None) -> list[list[float]]:
        """Generate embeddings for a batch of texts via Model Gateway with caching."""
        
        if not model_id:
            route = route_task(RoutingRequest(task_type=TaskType.EMBEDDING))
            model_id = route.selected_model
            
        model_info = get_model(model_id)
        if not model_info:
            raise RetrievalServiceError(f"Embedding model {model_id} not found in registry")
            
        model_version = model_info.version
        
        final_embeddings = [None] * len(texts)
        texts_to_embed = []
        indices_to_embed = []
        
        # 1. Check cache
        for idx, text in enumerate(texts):
            cached = embedding_cache.get_embedding(text, model_id, model_version)
            if cached is not None:
                final_embeddings[idx] = cached
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(idx)
                
        if not texts_to_embed:
            return final_embeddings
            
        # 2. Call gateway for cache misses
        try:
            request = GatewayEmbeddingRequest(
                model=model_id,
                input=texts_to_embed,
                timeout=30.0
            )
            response = await model_gateway.embed(request)
            
            # 3. Store in cache and populate final results
            for idx, text, emb in zip(indices_to_embed, texts_to_embed, response.embeddings):
                embedding_cache.set_embedding(text, model_id, model_version, emb)
                final_embeddings[idx] = emb
                
            return final_embeddings
        except Exception as e:
            logger.error("Embedding generation failed: %s", e)
            raise RetrievalServiceError("Knowledge search is temporarily unavailable. No external service was contacted.") from e

    async def embed_document_chunks(
        self,
        chunks: list[dict],
        text_field: str = "text",
        batch_size: int = 32,
    ) -> list[dict]:
        """
        Embed document chunks, adding the embedding vector to each chunk.
        Processes in batches for efficiency.
        """
        results = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [chunk[text_field] for chunk in batch]
            embeddings = await self.embed_batch(texts)

            for chunk, embedding in zip(batch, embeddings):
                chunk["embedding"] = embedding
                results.append(chunk)

        logger.info("Embedded %d chunks in batches of %d", len(results), batch_size)
        return results


# Global instance
embedding_service = EmbeddingService()
