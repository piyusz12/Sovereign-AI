"""
Sovereign AI Workbench — LanceDB Vector Store

Embedded vector database for the 8GB Lite profile.
Runs entirely on CPU/RAM — zero VRAM usage.

LanceDB stores data as Lance-format columnar files on disk.
No separate server process needed (unlike Qdrant).

Usage:
    from backend.rag.lancedb_store import lancedb_store

    await lancedb_store.initialize()
    await lancedb_store.add_documents(chunks_with_embeddings)
    results = await lancedb_store.search(query_embedding, top_k=5)
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import pyarrow as pa

from backend.settings import settings

logger = logging.getLogger("sovereign.rag.lancedb")

# Table name for the main document store
_DEFAULT_TABLE = "sovereign_documents"


class LanceDBStore:
    """
    Embedded vector store backed by LanceDB.

    Stores document chunks with their embeddings on disk in Lance format.
    Search is cosine-similarity over the embedding column.
    """

    def __init__(
        self,
        db_path: str | None = None,
        table_name: str = _DEFAULT_TABLE,
        embedding_dim: int | None = None,
    ):
        self._db_path = db_path or settings.lancedb_path
        self._table_name = table_name
        self._embedding_dim = embedding_dim or settings.embedding_dimension
        self._db = None
        self._table = None
        self._initialized = False

    async def initialize(self) -> None:
        """Open (or create) the LanceDB database and table."""
        if self._initialized:
            return

        import lancedb as ldb

        db_dir = Path(self._db_path)
        db_dir.mkdir(parents=True, exist_ok=True)

        # lancedb.connect is synchronous — run in executor to avoid blocking
        loop = asyncio.get_running_loop()
        self._db = await loop.run_in_executor(None, ldb.connect, str(db_dir))

        # Check if table already exists
        existing_tables = await loop.run_in_executor(
            None, self._db.table_names
        )
        if self._table_name in existing_tables:
            self._table = await loop.run_in_executor(
                None, self._db.open_table, self._table_name
            )
            logger.info(
                "Opened existing LanceDB table '%s' (%s)",
                self._table_name,
                self._db_path,
            )
        else:
            logger.info(
                "LanceDB table '%s' does not exist yet — "
                "will be created on first document insert",
                self._table_name,
            )

        self._initialized = True

    def _build_schema(self) -> pa.Schema:
        """Arrow schema for the documents table."""
        return pa.schema([
            pa.field("id", pa.string()),
            pa.field("text", pa.string()),
            pa.field(
                "vector",
                pa.list_(pa.float32(), self._embedding_dim),
            ),
            pa.field("source", pa.string()),
            pa.field("doc_id", pa.string()),
            pa.field("chunk_index", pa.int32()),
            pa.field("metadata_json", pa.string()),  # JSON-serialised metadata
        ])

    async def add_documents(
        self,
        documents: list[dict[str, Any]],
    ) -> int:
        """
        Insert document chunks into the store.

        Each document dict must have:
            - id: str
            - text: str
            - embedding: list[float]   (renamed to 'vector' internally)
            - source: str              (filename or URI)
            - doc_id: str
            - chunk_index: int
            - metadata: dict           (optional, serialised to JSON)

        Returns the number of rows added.
        """
        import json

        if not documents:
            return 0

        await self.initialize()

        rows = []
        for doc in documents:
            rows.append({
                "id": doc.get("id", ""),
                "text": doc.get("text", ""),
                "vector": doc.get("embedding", [0.0] * self._embedding_dim),
                "source": doc.get("source", ""),
                "doc_id": doc.get("doc_id", ""),
                "chunk_index": doc.get("chunk_index", 0),
                "metadata_json": json.dumps(doc.get("metadata", {})),
            })

        loop = asyncio.get_running_loop()

        if self._table is None:
            # Create the table on first insert
            self._table = await loop.run_in_executor(
                None,
                lambda: self._db.create_table(
                    self._table_name,
                    data=rows,
                    schema=self._build_schema(),
                    mode="overwrite",
                ),
            )
            logger.info(
                "Created LanceDB table '%s' with %d rows",
                self._table_name,
                len(rows),
            )
        else:
            await loop.run_in_executor(
                None,
                lambda: self._table.add(rows),
            )
            logger.info("Added %d rows to LanceDB table '%s'", len(rows), self._table_name)

        return len(rows)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter_expr: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Cosine-similarity search over stored embeddings.

        Args:
            query_embedding: The query vector.
            top_k: Number of results to return.
            filter_expr: Optional SQL-style filter (e.g. "doc_id = 'abc'").

        Returns:
            List of dicts with keys: id, text, source, doc_id, chunk_index,
            metadata_json, _distance (lower is more similar for cosine).
        """
        import json

        await self.initialize()

        if self._table is None:
            logger.warning("Search called but table has not been created yet")
            return []

        loop = asyncio.get_running_loop()

        def _do_search():
            q = (
                self._table
                .search(query_embedding)
                .metric("cosine")
                .limit(top_k)
            )
            if filter_expr:
                q = q.where(filter_expr)
            return q.to_list()

        raw_results = await loop.run_in_executor(None, _do_search)

        results = []
        for row in raw_results:
            metadata = {}
            meta_json = row.get("metadata_json", "{}")
            if meta_json:
                try:
                    metadata = json.loads(meta_json)
                except (json.JSONDecodeError, TypeError):
                    pass

            results.append({
                "id": row.get("id", ""),
                "text": row.get("text", ""),
                "source": row.get("source", ""),
                "doc_id": row.get("doc_id", ""),
                "chunk_index": row.get("chunk_index", 0),
                "metadata": metadata,
                "score": 1.0 - row.get("_distance", 1.0),  # cosine distance → similarity
            })

        return results

    async def delete_by_doc_id(self, doc_id: str) -> None:
        """Delete all chunks belonging to a document."""
        await self.initialize()
        if self._table is None:
            return

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self._table.delete(f"doc_id = '{doc_id}'"),
        )
        logger.info("Deleted chunks for doc_id='%s' from LanceDB", doc_id)

    async def count(self) -> int:
        """Return the total number of rows in the table."""
        await self.initialize()
        if self._table is None:
            return 0

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self._table.count_rows())

    async def list_doc_ids(self) -> list[str]:
        """Return a list of unique doc_ids in the store."""
        await self.initialize()
        if self._table is None:
            return []

        loop = asyncio.get_running_loop()
        df = await loop.run_in_executor(
            None,
            lambda: self._table.to_pandas()[["doc_id"]].drop_duplicates(),
        )
        return df["doc_id"].tolist()


# Global instance
lancedb_store = LanceDBStore()
