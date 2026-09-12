"""
Sovereign AI Workbench — Application Settings

Centralized configuration loaded from .env file.
All endpoints are LOCAL. No cloud API keys.

Usage:
    from backend.settings import settings
"""

from __future__ import annotations

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.
    Every setting has a sensible development default.
    """

    # --- Application ---
    app_name: str = "Sovereign AI Workbench"
    app_version: str = "0.1.0"
    app_host: str = "127.0.0.1"
    app_port: int = 8080
    debug: bool = True
    log_level: str = "INFO"

    # --- Ollama ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_reasoning_model: str = "qwen3:14b"
    ollama_coding_model: str = "qwen2.5-coder:7b"
    ollama_vision_model: str = "qwen2-vl:2b"

    # --- Local inference performance profile (RTX 4060 Laptop, 8 GB VRAM) ---
    # 8GB Lite Profile: Qwen2.5-Coder-7B (~4.7GB) as primary brain,
    # Qwen2-VL-2B (~1.5GB) for vision. Context window kept at 8192
    # to leave ~1.5GB for KV cache within the VRAM budget.
    inference_context_tokens: int = 8192
    inference_output_reserve_tokens: int = 1024
    inference_max_agent_iterations: int = 5
    inference_max_tool_calls: int = 10
    inference_keep_alive: str = "5m"
    # --- CPU Computational Power & Hybrid Execution ---
    # Equal CPU computational power sharing alongside RTX 4060 GPU
    cpu_compute_threads: int = 8
    cpu_worker_concurrency: int = 8
    enable_cpu_hybrid_offload: bool = True
    enable_simd_avx2: bool = True
    compute_mode: str = "hybrid_balanced"

    # --- vLLM (Phase 25+) ---
    vllm_base_url: str = "http://localhost:8000"
    vllm_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct"

    # --- LiteLLM (Phase 24+) ---
    litellm_base_url: str = "http://localhost:4000"
    litellm_master_key: str = "sk-local-sovereign-key"

    # --- Vector Database ---
    vector_db_backend: str = "lancedb"  # "lancedb" or "qdrant"
    lancedb_path: str = "./data/lancedb"

    # --- Qdrant (used when vector_db_backend="qdrant") ---
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_collection: str = "sovereign_documents"

    # --- Embedding (CPU-only in Lite profile — saves VRAM for LLM) ---
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_device: str = "cpu"

    # --- Reranker ---
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # --- Infinity (Phase 26+) ---
    infinity_base_url: str = "http://localhost:7997"

    # --- Sandbox ---
    sandbox_image: str = "sovereign-sandbox:latest"
    sandbox_memory_limit: str = "512m"
    sandbox_cpu_limit: int = 1
    sandbox_timeout_seconds: int = 30
    sandbox_network: str = "none"

    # --- Security ---
    jwt_secret_key: str = "sovereign-ai-dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # --- Data Paths ---
    data_dir: str = "./data"
    documents_dir: str = "./data/documents"
    processed_dir: str = "./data/processed"
    embeddings_dir: str = "./data/embeddings"
    output_dir: str = "./data/output"
    audit_db_path: str = "./data/audit.db"
    audit_log_path: str = "./data/audit/audit.jsonl"

    # --- Monitoring ---
    otel_exporter: str = "console"
    sovereignty_log_file: str = "./monitoring/sovereignty.log"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @property
    def qdrant_url(self) -> str:
        """Full Qdrant REST URL."""
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    @property
    def qdrant_grpc_url(self) -> str:
        """Full Qdrant gRPC URL."""
        return f"http://{self.qdrant_host}:{self.qdrant_grpc_port}"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()


# Convenience import: `from backend.settings import settings`
settings = get_settings()
