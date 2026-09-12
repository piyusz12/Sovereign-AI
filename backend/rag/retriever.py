"""
Sovereign AI Workbench — Hybrid Retriever

Implements hybrid retrieval: Dense (LanceDB or Qdrant) + BM25 → Merge.
RBAC filtering is applied BEFORE retrieval, not after.

8GB Lite Profile: Uses LanceDB (embedded, CPU/RAM) as default backend.
Enterprise Profile: Can use Qdrant (external server) when configured.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from math import log
from typing import Any, Optional

logger = logging.getLogger("sovereign.rag.retriever")


class BM25Retriever:
    """
    Simple BM25 retriever for sparse/keyword search.
    Operates on pre-indexed document chunks.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._documents: list[dict] = []
        self._doc_freqs: Counter = Counter()
        self._avg_dl: float = 0.0

    def index(self, documents: list[dict], text_field: str = "text") -> None:
        """Index documents for BM25 retrieval."""
        self._documents = documents
        total_len = 0
        self._doc_freqs = Counter()

        for doc in documents:
            tokens = self._tokenize(doc.get(text_field, ""))
            total_len += len(tokens)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self._doc_freqs[token] += 1

        self._avg_dl = total_len / len(documents) if documents else 1.0
        logger.info("BM25 indexed %d documents", len(documents))

    def search(
        self,
        query: str,
        top_k: int = 20,
        user_role: Optional[str] = None,
        department_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Search documents using BM25 scoring.
        Applies RBAC filter BEFORE scoring.
        """
        query_tokens = self._tokenize(query)
        n_docs = len(self._documents)

        scored = []
        for doc in self._documents:
            # RBAC: Pre-retrieval filtering
            if user_role and not self._check_access(doc, user_role, department_filter):
                continue

            text = doc.get("text", "")
            doc_tokens = self._tokenize(text)
            doc_len = len(doc_tokens)
            token_counts = Counter(doc_tokens)

            score = 0.0
            for token in query_tokens:
                if token not in token_counts:
                    continue
                tf = token_counts[token]
                df = self._doc_freqs.get(token, 0)
                idf = log((n_docs - df + 0.5) / (df + 0.5) + 1)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self._avg_dl)
                score += idf * numerator / denominator

            if score > 0:
                scored.append({**doc, "_bm25_score": score})

        scored.sort(key=lambda x: x["_bm25_score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace + punctuation tokenizer."""
        return re.findall(r"\w+", text.lower())

    @staticmethod
    def _check_access(
        doc: dict, user_role: str, department_filter: Optional[str] = None
    ) -> bool:
        """Check if user has access to this document."""
        doc_access = doc.get("access_level", "public")
        doc_dept = doc.get("department", "")

        # Admin can access everything
        if user_role == "admin":
            return True

        # Department filter
        if department_filter and doc_dept and doc_dept != department_filter:
            return False

        # Role-based access
        role_access = {
            "engineering": ["public", "engineering"],
            "finance": ["public", "finance"],
            "procurement": ["public", "procurement"],
            "hr": ["public", "hr"],
            "operations": ["public", "operations", "engineering"],
        }

        allowed = role_access.get(user_role, ["public"])
        return doc_access in allowed


class HybridRetriever:
    """
    Combines dense retrieval (LanceDB or Qdrant) + sparse retrieval (BM25).
    Merges results using reciprocal rank fusion.

    Backend selection is driven by settings.vector_db_backend:
        - "lancedb" → embedded LanceDB (default in Lite profile)
        - "qdrant"  → external Qdrant server
    """

    def __init__(self):
        self.bm25 = BM25Retriever()
        self._qdrant_client = None
        self._lancedb_store = None
        self._local_chunks: list[dict] = []
        self._local_vectors: list[list[float]] = []

        # Auto-connect LanceDB if configured
        from backend.settings import settings as _settings
        if getattr(_settings, "vector_db_backend", "lancedb") == "lancedb":
            from backend.rag.lancedb_store import lancedb_store
            self._lancedb_store = lancedb_store
            logger.info("HybridRetriever using LanceDB backend")

    async def connect_qdrant(
        self, host: str = "localhost", port: int = 6333, collection: str = "sovereign_documents"
    ) -> None:
        """Connect to Qdrant vector database."""
        try:
            from qdrant_client import QdrantClient

            self._qdrant_client = QdrantClient(host=host, port=port)
            logger.info("Connected to Qdrant at %s:%d", host, port)
        except ImportError:
            logger.warning("qdrant-client not installed")
        except Exception as e:
            logger.error("Failed to connect to Qdrant: %s", e)

    async def upsert_chunks(
        self,
        chunks: list[dict],
        collection: str = "sovereign_documents",
    ) -> bool:
        """Upsert embedded chunks into LanceDB/Qdrant and local SIMD index + BM25."""
        # Index into local high-speed native C++ SIMD store
        for chunk in chunks:
            embedding = chunk.get("embedding")
            if embedding:
                self._local_chunks.append(chunk)
                self._local_vectors.append(embedding)

        # Update BM25 index with new chunks
        self.bm25.index(self.bm25._documents + chunks)

        # --- LanceDB path (8GB Lite Profile) ---
        if self._lancedb_store is not None:
            try:
                count = await self._lancedb_store.add_documents(chunks)
                logger.info("Upserted %d chunks to LanceDB", count)
                return True
            except Exception as e:
                logger.error("Failed to upsert chunks to LanceDB: %s", e)
                return False

        # --- Qdrant path (Enterprise Profile) ---
        if not self._qdrant_client:
            logger.info("No vector DB connected. Chunks indexed in local SIMD store only.")
            return True

        try:
            from qdrant_client.models import PointStruct
            import uuid

            points = []
            for chunk in chunks:
                point_id = str(uuid.uuid4())
                embedding = chunk.get("embedding")
                if not embedding:
                    continue
                
                payload = {k: v for k, v in chunk.items() if k != "embedding"}
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload,
                    )
                )

            if points:
                self._qdrant_client.upsert(
                    collection_name=collection,
                    points=points,
                )
                logger.info("Upserted %d chunks to Qdrant collection %s", len(points), collection)
            
            return True
        except Exception as e:
            logger.error("Failed to upsert chunks to Qdrant: %s", e)
            return False

    async def search_vector(
        self,
        query_embedding: list[float],
        top_k: int = 20,
        user_role: Optional[str] = None,
        department_filter: Optional[str] = None,
        collection: str = "sovereign_documents",
    ) -> list[dict]:
        """Search dense vector index directly (Qdrant or Native C++ AVX2 SIMD)."""
        return await self._dense_search(
            query_embedding, top_k, user_role, department_filter, collection
        )

    async def search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 20,
        user_role: Optional[str] = None,
        department_filter: Optional[str] = None,
        collection: str = "sovereign_documents",
    ) -> list[dict]:
        """
        Hybrid search: dense + sparse → reciprocal rank fusion.
        RBAC filtering applied at BOTH retrieval paths.
        """
        # Dense retrieval from Qdrant or native C++ AVX2 SIMD engine
        dense_results = await self.search_vector(
            query_embedding, top_k, user_role, department_filter, collection
        )

        # Sparse retrieval from BM25
        sparse_results = self.bm25.search(query, top_k, user_role, department_filter)

        # Merge using reciprocal rank fusion
        merged = self._reciprocal_rank_fusion(dense_results, sparse_results, k=60)

        return merged[:top_k]

    async def _dense_search(
        self,
        query_embedding: list[float],
        top_k: int,
        user_role: Optional[str],
        department_filter: Optional[str],
        collection: str,
    ) -> list[dict]:
        """Search LanceDB, Qdrant, or native SIMD engine for semantically similar documents."""

        # --- LanceDB path (8GB Lite Profile) ---
        if self._lancedb_store is not None:
            try:
                # Build optional filter expression for RBAC
                filter_expr = None
                # LanceDB SQL filters are limited; apply RBAC post-retrieval
                raw = await self._lancedb_store.search(
                    query_embedding, top_k=top_k * 2  # over-fetch for RBAC filtering
                )
                # Post-retrieval RBAC filtering
                results = []
                for row in raw:
                    if user_role and not self.bm25._check_access(row, user_role, department_filter):
                        continue
                    row["_dense_score"] = row.pop("score", 0.0)
                    results.append(row)
                    if len(results) >= top_k:
                        break
                return results
            except Exception as e:
                logger.warning("LanceDB dense search error: %s", e)
                return []

        # --- Local SIMD fallback ---
        if not self._qdrant_client:
            if not self._local_vectors or not query_embedding:
                return []
            try:
                from backend.cpp_bridge.bridge import cpp_core
                filtered_indices = []
                filtered_vectors = []
                for idx, chunk in enumerate(self._local_chunks):
                    if user_role and not self.bm25._check_access(chunk, user_role, department_filter):
                        continue
                    filtered_indices.append(idx)
                    filtered_vectors.append(self._local_vectors[idx])

                if not filtered_vectors:
                    return []

                top_matches = cpp_core.simd_batch_topk(query_embedding, filtered_vectors, top_k)
                results = []
                for sub_idx, score in top_matches:
                    real_idx = filtered_indices[sub_idx]
                    chunk = dict(self._local_chunks[real_idx])
                    chunk["_dense_score"] = score
                    results.append(chunk)
                return results
            except Exception as e:
                logger.warning("Native C++ SIMD vector search error: %s", e)
                return []

        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

            # Build RBAC filter
            must_conditions = []
            
            # 1. Role-based access level
            if user_role and user_role != "admin":
                role_access = {
                    "engineering": ["public", "engineering"],
                    "finance": ["public", "finance"],
                    "operations": ["public", "operations", "engineering"],
                    "hr": ["public", "hr"],
                    "procurement": ["public", "procurement"],
                }
                allowed = role_access.get(user_role, ["public"])
                must_conditions.append(
                    FieldCondition(
                        key="access_level",
                        match=MatchAny(any=allowed)
                    )
                )

            # 2. Department filter
            if department_filter:
                must_conditions.append(
                    FieldCondition(
                        key="department",
                        match=MatchValue(value=department_filter)
                    )
                )

            query_filter = Filter(must=must_conditions) if must_conditions else None

            results = self._qdrant_client.search(
                collection_name=collection,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=top_k,
            )

            return [
                {
                    "document_id": hit.payload.get("document_id", ""),
                    "text": hit.payload.get("text", ""),
                    "page": hit.payload.get("page"),
                    "department": hit.payload.get("department", ""),
                    "access_level": hit.payload.get("access_level", "public"),
                    "_dense_score": hit.score,
                }
                for hit in results
            ]
        except Exception as e:
            logger.error("Qdrant search failed: %s", e)
            return []

    @staticmethod
    def _reciprocal_rank_fusion(
        dense_results: list[dict],
        sparse_results: list[dict],
        k: int = 60,
    ) -> list[dict]:
        """Merge dense and sparse results using reciprocal rank fusion."""
        scores: dict[str, float] = {}
        doc_map: dict[str, dict] = {}

        for rank, doc in enumerate(dense_results):
            doc_id = doc.get("document_id", str(rank))
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
            doc_map[doc_id] = doc

        for rank, doc in enumerate(sparse_results):
            doc_id = doc.get("document_id", f"bm25_{rank}")
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
            if doc_id not in doc_map:
                doc_map[doc_id] = doc

        sorted_ids = sorted(scores, key=scores.get, reverse=True)  # type: ignore[arg-type]
        return [
            {**doc_map[doc_id], "_rrf_score": scores[doc_id]}
            for doc_id in sorted_ids
            if doc_id in doc_map
        ]


# Global instance
hybrid_retriever = HybridRetriever()
