"""
Sovereign AI Workbench — Embedding Service

8GB Lite Profile: Uses sentence-transformers all-MiniLM-L6-v2 on CPU.
Enterprise Profile: Uses Qwen3-Embedding-0.6B via Ollama on GPU.

The active implementation is selected by `settings.vector_db_backend`:
    - "lancedb"  → LocalCPUEmbeddingService (sentence-transformers, CPU)
    - "qdrant"   → OllamaEmbeddingService   (Ollama gateway, GPU)
"""

from __future__ import annotations

import logging
from typing import Optional

from backend.settings import settings
from backend.rag.cache import embedding_cache
from backend.rag.exceptions import RetrievalServiceError

logger = logging.getLogger("sovereign.rag.embedder")


# ── CPU Embedding Service (8GB Lite Profile) ──────────────────────────────────


class LocalCPUEmbeddingService:
    """
    Embedding service using sentence-transformers on CPU.
    Zero VRAM usage — all computation on the Ryzen 7 CPU.

    Model: all-MiniLM-L6-v2 (384 dimensions, ~80MB on disk)
    """

    def __init__(
        self,
        model: str | None = None,
        dimension: int | None = None,
        device: str | None = None,
    ):
        self.model_name = model or settings.embedding_model
        self.dimension = dimension or settings.embedding_dimension
        self.device = device or getattr(settings, "embedding_device", "cpu")
        self._encoder = None

    def _load_encoder(self):
        """Lazy-load the sentence-transformers model."""
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer

            logger.info(
                "Loading embedding model '%s' on device='%s'",
                self.model_name,
                self.device,
            )
            self._encoder = SentenceTransformer(
                self.model_name, device=self.device
            )
            logger.info("Embedding model loaded successfully")
        return self._encoder

    async def embed_text(self, text: str, model_id: str = None) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed_batch([text], model_id=model_id)
        return embeddings[0] if embeddings else [0.0] * self.dimension

    async def embed_batch(
        self, texts: list[str], model_id: str = None
    ) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts using sentence-transformers.
        Uses the embedding cache to avoid recomputing.
        """
        effective_model = model_id or self.model_name
        model_version = "cpu-local"

        final_embeddings: list[list[float] | None] = [None] * len(texts)
        texts_to_embed: list[str] = []
        indices_to_embed: list[int] = []

        # 1. Check cache
        for idx, text in enumerate(texts):
            cached = embedding_cache.get_embedding(
                text, effective_model, model_version
            )
            if cached is not None:
                final_embeddings[idx] = cached
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(idx)

        if not texts_to_embed:
            return final_embeddings

        # 2. Encode on CPU
        try:
            encoder = self._load_encoder()
            vectors = encoder.encode(
                texts_to_embed,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,
            )

            for idx, text, vec in zip(
                indices_to_embed, texts_to_embed, vectors
            ):
                emb = vec.tolist()
                embedding_cache.set_embedding(
                    text, effective_model, model_version, emb
                )
                final_embeddings[idx] = emb

            return final_embeddings

        except Exception as e:
            logger.error("CPU embedding generation failed: %s", e)
            raise RetrievalServiceError(
                "Embedding generation failed on CPU. "
                "No external service was contacted."
            ) from e

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

        logger.info(
            "Embedded %d chunks in batches of %d (CPU)", len(results), batch_size
        )
        return results


# ── Ollama Embedding Service (Enterprise Profile) ────────────────────────────


class OllamaEmbeddingService:
    """
    Embedding service using Ollama (for the enterprise/Qdrant profile).
    Retained for backward compatibility when vector_db_backend="qdrant".
    """

    def __init__(
        self,
        model: str = "BAAI/bge-small-en-v1.5",
        dimension: int = 384,
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.dimension = dimension
        self.base_url = base_url

    async def embed_text(self, text: str, model_id: str = None) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed_batch([text], model_id=model_id)
        return embeddings[0] if embeddings else [0.0] * self.dimension

    async def embed_batch(
        self, texts: list[str], model_id: str = None
    ) -> list[list[float]]:
        """Generate embeddings via Model Gateway with caching."""
        from backend.model_gateway import model_gateway, GatewayEmbeddingRequest
        from backend.models.registry import get_model
        from backend.models.router import route_task, RoutingRequest, TaskType

        if not model_id:
            route = route_task(RoutingRequest(task_type=TaskType.EMBEDDING))
            model_id = route.selected_model

        model_info = get_model(model_id)
        if not model_info:
            raise RetrievalServiceError(
                f"Embedding model {model_id} not found in registry"
            )

        model_version = model_info.version

        final_embeddings = [None] * len(texts)
        texts_to_embed = []
        indices_to_embed = []

        # 1. Check cache
        for idx, text in enumerate(texts):
            cached = embedding_cache.get_embedding(
                text, model_id, model_version
            )
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
                timeout=30.0,
            )
            response = await model_gateway.embed(request)

            # 3. Store in cache and populate final results
            for idx, text, emb in zip(
                indices_to_embed, texts_to_embed, response.embeddings
            ):
                embedding_cache.set_embedding(
                    text, model_id, model_version, emb
                )
                final_embeddings[idx] = emb

            return final_embeddings
        except Exception as e:
            logger.error("Embedding generation failed: %s", e)
            raise RetrievalServiceError(
                "Knowledge search is temporarily unavailable. "
                "No external service was contacted."
            ) from e

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

        logger.info(
            "Embedded %d chunks in batches of %d", len(results), batch_size
        )
        return results


# ── Factory ──────────────────────────────────────────────────────────────────


def get_embedding_service() -> LocalCPUEmbeddingService | OllamaEmbeddingService:
    """
    Return the correct embedding service based on configuration.

    - "lancedb" backend  → LocalCPUEmbeddingService (CPU, 0 VRAM)
    - "qdrant"  backend  → OllamaEmbeddingService   (Ollama gateway)
    """
    backend = getattr(settings, "vector_db_backend", "lancedb")
    if backend == "lancedb":
        return LocalCPUEmbeddingService()
    else:
        return OllamaEmbeddingService()


# Global instance — uses the configured backend
embedding_service = get_embedding_service()

# Backward compatibility alias
EmbeddingService = LocalCPUEmbeddingService
