"""
Sovereign AI Workbench — Health Probes

Async functions to check connectivity to downstream services.
Each probe has a short timeout and returns status + latency.

Used by /health and /admin/health endpoints.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger("sovereign.health")

PROBE_TIMEOUT = 2.0  # seconds


@dataclass
class ProbeResult:
    """Result of a service health probe."""
    service: str
    status: str  # "reachable", "not_reachable", "not_configured"
    latency_ms: Optional[float] = None
    detail: Optional[str] = None


async def probe_ollama(base_url: str) -> ProbeResult:
    """
    Probe Ollama by calling GET /api/tags.
    Returns the list of available models if reachable.
    """
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=PROBE_TIMEOUT) as client:
            response = await client.get(f"{base_url}/api/tags")
            latency = round((time.time() - start) * 1000, 2)

            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "?") for m in data.get("models", [])]
                return ProbeResult(
                    service="ollama",
                    status="reachable",
                    latency_ms=latency,
                    detail=f"models: {', '.join(models)}" if models else "no models pulled",
                )
            else:
                return ProbeResult(
                    service="ollama",
                    status="reachable",
                    latency_ms=latency,
                    detail=f"HTTP {response.status_code}",
                )
    except httpx.ConnectError:
        logger.debug("Ollama not reachable at %s", base_url)
        return ProbeResult(
            service="ollama",
            status="not_reachable",
            detail=f"Cannot connect to {base_url}",
        )
    except Exception as e:
        logger.debug("Ollama probe failed: %s", e)
        return ProbeResult(
            service="ollama",
            status="not_reachable",
            detail=str(e),
        )


async def probe_qdrant(host: str, port: int) -> ProbeResult:
    """
    Probe Qdrant by calling GET / on its REST API.
    """
    url = f"http://{host}:{port}"
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=PROBE_TIMEOUT) as client:
            response = await client.get(url)
            latency = round((time.time() - start) * 1000, 2)

            if response.status_code == 200:
                return ProbeResult(
                    service="qdrant",
                    status="reachable",
                    latency_ms=latency,
                    detail=f"REST API at {url}",
                )
            else:
                return ProbeResult(
                    service="qdrant",
                    status="reachable",
                    latency_ms=latency,
                    detail=f"HTTP {response.status_code}",
                )
    except httpx.ConnectError:
        logger.debug("Qdrant not reachable at %s", url)
        return ProbeResult(
            service="qdrant",
            status="not_reachable",
            detail=f"Cannot connect to {url}",
        )
    except Exception as e:
        logger.debug("Qdrant probe failed: %s", e)
        return ProbeResult(
            service="qdrant",
            status="not_reachable",
            detail=str(e),
        )


async def probe_all(ollama_url: str, qdrant_host: str, qdrant_port: int) -> dict:
    """
    Run all probes and return a summary dict.
    """
    ollama = await probe_ollama(ollama_url)
    qdrant = await probe_qdrant(qdrant_host, qdrant_port)

    return {
        "ollama": {
            "status": ollama.status,
            "latency_ms": ollama.latency_ms,
            "detail": ollama.detail,
        },
        "qdrant": {
            "status": qdrant.status,
            "latency_ms": qdrant.latency_ms,
            "detail": qdrant.detail,
        },
    }
