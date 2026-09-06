import sqlite3
import json
import logging
from typing import List, Optional
import hashlib

from backend.settings import settings

logger = logging.getLogger("sovereign.rag.cache")

class EmbeddingCache:
    def __init__(self, db_path: str = "./data/embeddings_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        chunk_hash TEXT,
                        model_id TEXT,
                        model_version TEXT,
                        embedding TEXT,
                        PRIMARY KEY (chunk_hash, model_id, model_version)
                    )
                """)
        except Exception as e:
            logger.error(f"Failed to initialize embedding cache database: {e}")

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def get_embedding(self, text: str, model_id: str, model_version: str) -> Optional[List[float]]:
        chunk_hash = self._hash_text(text)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT embedding FROM embeddings 
                    WHERE chunk_hash = ? AND model_id = ? AND model_version = ?
                """, (chunk_hash, model_id, model_version))
                result = cursor.fetchone()
                
                if result:
                    return json.loads(result[0])
        except Exception as e:
            logger.warning(f"Failed to read from embedding cache: {e}")
            
        return None

    def set_embedding(self, text: str, model_id: str, model_version: str, embedding: List[float]):
        chunk_hash = self._hash_text(text)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO embeddings (chunk_hash, model_id, model_version, embedding)
                    VALUES (?, ?, ?, ?)
                """, (chunk_hash, model_id, model_version, json.dumps(embedding)))
        except Exception as e:
            logger.warning(f"Failed to write to embedding cache: {e}")

    # Gateway-facing aliases keep cache ownership at the model boundary while
    # preserving the original embedder API above.
    def get(self, model_id: str, text: str, model_version: str | None = None) -> Optional[List[float]]:
        return self.get_embedding(text, model_id, model_version or "v1")

    def set(
        self,
        model_id: str,
        text: str,
        embedding: List[float],
        model_version: str | None = None,
    ) -> None:
        self.set_embedding(text, model_id, model_version or "v1", embedding)

embedding_cache = EmbeddingCache()
