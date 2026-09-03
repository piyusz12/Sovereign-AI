"""
Sovereign AI Workbench — Embedding Service

Generates embeddings using Qwen3-Embedding-0.6B via local inference.
Small enough to coexist with a heavy model on the RTX 4060 8GB.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger("sovereign.rag.embedder")

# Default config
DEFAULT_EMBEDDING_MODEL = "qwen3-embedding:0.6b"
DEFAULT_EMBEDDING_DIM = 1024
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

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed_batch([text])
        return embeddings[0] if embeddings else [0.0] * self.dimension

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": texts},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("embeddings", [])
        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama at %s", self.base_url)
            return [[0.0] * self.dimension for _ in texts]
        except Exception as e:
            logger.error("Embedding failed: %s", e)
            return [[0.0] * self.dimension for _ in texts]

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
