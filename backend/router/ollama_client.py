"""
Sovereign AI Workbench — Ollama Client

Async HTTP client for all Ollama REST API interactions.
Every call targets localhost only — zero external network access.

Ollama REST API reference:
    https://github.com/ollama/ollama/blob/main/docs/api.md

Usage:
    from backend.router.ollama_client import ollama_client

    models = await ollama_client.list_models()
    response = await ollama_client.chat("qwen3:14b", messages=[...])
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Optional

import httpx

from backend.settings import settings

logger = logging.getLogger("sovereign.ollama_client")


# ── Timeouts ──────────────────────────────────────────────────────────────────

METADATA_TIMEOUT = 5.0       # list, show, ps — fast operations
INFERENCE_TIMEOUT = 300.0    # chat, generate — 14B model can be slow
LOAD_TIMEOUT = 120.0         # pre-warming a model into VRAM
PULL_TIMEOUT = 1800.0        # pulling a model — can take 30min on slow networks


# ── Data Classes ──────────────────────────────────────────────────────────────


@dataclass
class OllamaModel:
    """Metadata for a model available in Ollama."""
    name: str
    size: int = 0                # bytes
    parameter_size: str = ""     # e.g. "14.8B"
    quantization_level: str = "" # e.g. "Q4_K_M"
    family: str = ""
    modified_at: str = ""
    digest: str = ""

    @property
    def size_gb(self) -> float:
        return round(self.size / (1024 ** 3), 2) if self.size else 0.0


@dataclass
class RunningModel:
    """A model currently loaded in Ollama (from /api/ps)."""
    name: str
    size: int = 0             # bytes of VRAM used
    vram_mb: int = 0          # convenience: VRAM in MB
    expires_at: str = ""
    size_vram: int = 0        # bytes in VRAM
    size_ram: int = 0         # bytes offloaded to RAM

    @property
    def vram_used_mb(self) -> int:
        """VRAM used in MB."""
        if self.size_vram > 0:
            return round(self.size_vram / (1024 ** 2))
        return round(self.size / (1024 ** 2))


@dataclass
class ChatResponse:
    """Response from a chat completion."""
    content: str
    model: str = ""
    total_duration_ns: int = 0
    load_duration_ns: int = 0
    prompt_eval_count: int = 0
    prompt_eval_duration_ns: int = 0
    eval_count: int = 0
    eval_duration_ns: int = 0
    done: bool = True
    done_reason: str = ""

    @property
    def tokens_per_sec(self) -> float:
        if self.eval_duration_ns > 0:
            return round(self.eval_count / (self.eval_duration_ns / 1e9), 2)
        return 0.0

    @property
    def first_token_ms(self) -> float:
        if self.prompt_eval_duration_ns > 0:
            return round(self.prompt_eval_duration_ns / 1e6, 2)
        return 0.0

    @property
    def total_duration_ms(self) -> float:
        return round(self.total_duration_ns / 1e6, 2) if self.total_duration_ns else 0.0


@dataclass
class GenerateResponse:
    """Response from a raw generate call."""
    response: str
    model: str = ""
    total_duration_ns: int = 0
    eval_count: int = 0
    eval_duration_ns: int = 0
    prompt_eval_duration_ns: int = 0
    done: bool = True

    @property
    def tokens_per_sec(self) -> float:
        if self.eval_duration_ns > 0:
            return round(self.eval_count / (self.eval_duration_ns / 1e9), 2)
        return 0.0


@dataclass
class StreamChunk:
    """A single chunk from a streaming response."""
    content: str = ""
    done: bool = False
    model: str = ""
    # Final chunk includes metrics
    total_duration_ns: int = 0
    eval_count: int = 0
    eval_duration_ns: int = 0
    prompt_eval_duration_ns: int = 0


# ── Ollama Client ─────────────────────────────────────────────────────────────


class OllamaClient:
    """
    Async HTTP client for the Ollama REST API.

    All requests go to localhost. No external network traffic.
    Uses httpx.AsyncClient for proper connection pooling and timeouts.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")

    def _client(self, timeout: float) -> httpx.AsyncClient:
        """Create an httpx client with the given timeout."""
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout, connect=5.0),
        )

    # ── Model Management ──────────────────────────────────────────────────

    async def list_models(self) -> list[OllamaModel]:
        """
        List all models available locally in Ollama.
        Calls GET /api/tags.
        """
        async with self._client(METADATA_TIMEOUT) as client:
            try:
                resp = await client.get("/api/tags")
                resp.raise_for_status()
                data = resp.json()

                models = []
                for m in data.get("models", []):
                    details = m.get("details", {})
                    models.append(OllamaModel(
                        name=m.get("name", ""),
                        size=m.get("size", 0),
                        parameter_size=details.get("parameter_size", ""),
                        quantization_level=details.get("quantization_level", ""),
                        family=details.get("family", ""),
                        modified_at=m.get("modified_at", ""),
                        digest=m.get("digest", ""),
                    ))
                return models
            except httpx.ConnectError:
                logger.error("Cannot connect to Ollama at %s", self.base_url)
                return []
            except Exception as e:
                logger.error("Failed to list models: %s", e)
                return []

    async def show_model(self, name: str) -> dict[str, Any]:
        """
        Get detailed metadata for a model.
        Calls POST /api/show.
        """
        async with self._client(METADATA_TIMEOUT) as client:
            resp = await client.post("/api/show", json={"name": name})
            resp.raise_for_status()
            return resp.json()

    async def model_exists(self, name: str) -> bool:
        """Check if a model is pulled and available locally."""
        models = await self.list_models()
        # Ollama stores models with tags — match base name
        for m in models:
            if m.name == name or m.name.startswith(name.split(":")[0]):
                return True
        return False

    async def pull_model(
        self,
        name: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> bool:
        """
        Pull a model from the Ollama registry.
        Calls POST /api/pull with streaming progress.

        Args:
            name: Model name (e.g. "qwen3:14b")
            progress_callback: Optional callback(status, completed, total)

        Returns:
            True if pull succeeded
        """
        logger.info("Pulling model %s...", name)
        async with self._client(PULL_TIMEOUT) as client:
            try:
                async with client.stream(
                    "POST", "/api/pull", json={"name": name, "stream": True}
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            status = data.get("status", "")
                            completed = data.get("completed", 0)
                            total = data.get("total", 0)
                            if progress_callback:
                                progress_callback(status, completed, total)
                            if status:
                                logger.debug("Pull %s: %s", name, status)
                        except json.JSONDecodeError:
                            continue

                logger.info("Model %s pulled successfully", name)
                return True
            except Exception as e:
                logger.error("Failed to pull model %s: %s", name, e)
                return False

    # ── Process Status ────────────────────────────────────────────────────

    async def ps(self) -> list[RunningModel]:
        """
        List models currently loaded in Ollama memory.
        Calls GET /api/ps.
        Returns list of RunningModel with VRAM/RAM usage.
        """
        async with self._client(METADATA_TIMEOUT) as client:
            try:
                resp = await client.get("/api/ps")
                resp.raise_for_status()
                data = resp.json()

                running = []
                for m in data.get("models", []):
                    running.append(RunningModel(
                        name=m.get("name", ""),
                        size=m.get("size", 0),
                        size_vram=m.get("size_vram", 0),
                        size_ram=m.get("size", 0) - m.get("size_vram", 0),
                        expires_at=m.get("expires_at", ""),
                    ))
                return running
            except httpx.ConnectError:
                logger.error("Cannot connect to Ollama at %s", self.base_url)
                return []
            except Exception as e:
                logger.error("Failed to get running models: %s", e)
                return []

    # ── Model Loading / Unloading ─────────────────────────────────────────

    async def load_model(self, name: str, keep_alive: str = "10m") -> bool:
        """
        Pre-warm a model into VRAM by sending an empty generate request.
        This forces Ollama to load the model without producing output.

        Args:
            name: Model name (e.g. "qwen3:14b")
            keep_alive: How long to keep the model loaded (e.g. "10m", "1h", "-1" for forever)

        Returns:
            True if model loaded successfully
        """
        logger.info("Loading model %s into VRAM (keep_alive=%s)...", name, keep_alive)
        start = time.time()

        async with self._client(LOAD_TIMEOUT) as client:
            try:
                resp = await client.post("/api/generate", json={
                    "model": name,
                    "prompt": "",
                    "keep_alive": keep_alive,
                })
                resp.raise_for_status()
                duration = round(time.time() - start, 2)
                logger.info("Model %s loaded in %.2fs", name, duration)
                return True
            except httpx.ConnectError:
                logger.error("Cannot connect to Ollama at %s", self.base_url)
                return False
            except Exception as e:
                logger.error("Failed to load model %s: %s", name, e)
                return False

    async def unload_model(self, name: str) -> bool:
        """
        Unload a model from VRAM by setting keep_alive=0.

        Args:
            name: Model name to unload

        Returns:
            True if unload request succeeded
        """
        logger.info("Unloading model %s from VRAM...", name)
        async with self._client(METADATA_TIMEOUT) as client:
            try:
                resp = await client.post("/api/generate", json={
                    "model": name,
                    "prompt": "",
                    "keep_alive": 0,
                })
                resp.raise_for_status()
                logger.info("Model %s unloaded", name)
                return True
            except Exception as e:
                logger.error("Failed to unload model %s: %s", name, e)
                return False

    # ── Inference — Chat ──────────────────────────────────────────────────

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        keep_alive: str = "10m",
    ) -> ChatResponse:
        """
        Send a chat completion request (non-streaming).
        Uses POST /api/chat with stream=False.

        Args:
            model: Model name (e.g. "qwen3:14b")
            messages: List of {"role": "...", "content": "..."} dicts
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            keep_alive: How long to keep model loaded after request

        Returns:
            ChatResponse with content and metrics
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": keep_alive,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with self._client(INFERENCE_TIMEOUT) as client:
            try:
                resp = await client.post("/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()

                message = data.get("message", {})
                return ChatResponse(
                    content=message.get("content", ""),
                    model=data.get("model", model),
                    total_duration_ns=data.get("total_duration", 0),
                    load_duration_ns=data.get("load_duration", 0),
                    prompt_eval_count=data.get("prompt_eval_count", 0),
                    prompt_eval_duration_ns=data.get("prompt_eval_duration", 0),
                    eval_count=data.get("eval_count", 0),
                    eval_duration_ns=data.get("eval_duration", 0),
                    done=data.get("done", True),
                    done_reason=data.get("done_reason", ""),
                )
            except httpx.ConnectError:
                logger.error("Cannot connect to Ollama at %s", self.base_url)
                raise ConnectionError(
                    f"Ollama not running at {self.base_url}. "
                    "Start with 'ollama serve' or check Docker."
                )
            except httpx.HTTPStatusError as e:
                logger.error("Ollama HTTP error: %s", e)
                raise
            except Exception as e:
                logger.error("Chat call failed: %s", e)
                raise

    async def chat_stream(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        keep_alive: str = "10m",
    ) -> AsyncIterator[StreamChunk]:
        """
        Send a streaming chat completion request.
        Yields StreamChunk objects as tokens are generated.

        The final chunk has done=True and includes metrics.
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "keep_alive": keep_alive,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with self._client(INFERENCE_TIMEOUT) as client:
            try:
                async with client.stream("POST", "/api/chat", json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        message = data.get("message", {})
                        chunk = StreamChunk(
                            content=message.get("content", ""),
                            done=data.get("done", False),
                            model=data.get("model", model),
                        )

                        # Final chunk includes metrics
                        if chunk.done:
                            chunk.total_duration_ns = data.get("total_duration", 0)
                            chunk.eval_count = data.get("eval_count", 0)
                            chunk.eval_duration_ns = data.get("eval_duration", 0)
                            chunk.prompt_eval_duration_ns = data.get("prompt_eval_duration", 0)

                        yield chunk

            except httpx.ConnectError:
                logger.error("Cannot connect to Ollama at %s", self.base_url)
                raise ConnectionError(
                    f"Ollama not running at {self.base_url}. "
                    "Start with 'ollama serve' or check Docker."
                )

    # ── Inference — Generate (raw) ────────────────────────────────────────

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> GenerateResponse:
        """
        Raw generate endpoint (non-chat). Used by benchmarks.
        Calls POST /api/generate with stream=False.
        """
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        async with self._client(INFERENCE_TIMEOUT) as client:
            resp = await client.post("/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()

            return GenerateResponse(
                response=data.get("response", ""),
                model=data.get("model", model),
                total_duration_ns=data.get("total_duration", 0),
                eval_count=data.get("eval_count", 0),
                eval_duration_ns=data.get("eval_duration", 0),
                prompt_eval_duration_ns=data.get("prompt_eval_duration", 0),
                done=data.get("done", True),
            )

    # ── Health Check ──────────────────────────────────────────────────────

    async def is_running(self) -> bool:
        """Check if Ollama is reachable."""
        async with self._client(METADATA_TIMEOUT) as client:
            try:
                resp = await client.get("/api/tags")
                return resp.status_code == 200
            except Exception:
                return False


# ── Global Instance ───────────────────────────────────────────────────────────

ollama_client = OllamaClient()
