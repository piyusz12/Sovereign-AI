"""
Sovereign AI Workbench — Provider Factory

Creates and caches provider instances by name. The router and registry
use this factory to get the correct provider without knowing concrete classes.

Usage:
    from backend.router.providers.factory import get_provider

    provider = get_provider("ollama", "http://localhost:11434")
    response = await provider.chat("qwen3:14b", messages=[...])
"""

from __future__ import annotations

import logging
from typing import Optional

from backend.router.providers.base import BaseProvider
from backend.router.providers.ollama_provider import OllamaProvider
from backend.router.providers.vllm_provider import VLLMProvider
from backend.router.providers.litellm_provider import LiteLLMProvider

logger = logging.getLogger("sovereign.providers.factory")


# ── Provider Cache ────────────────────────────────────────────────────────────

_providers: dict[str, BaseProvider] = {}


def get_provider(
    provider_name: str,
    base_url: Optional[str] = None,
) -> BaseProvider:
    """
    Get or create a provider instance by name.

    Args:
        provider_name: "ollama", "vllm", etc.
        base_url: Override the default base URL

    Returns:
        A BaseProvider instance

    Raises:
        ValueError: If provider_name is not recognized
    """
    cache_key = f"{provider_name}:{base_url or 'default'}"

    if cache_key not in _providers:
        _providers[cache_key] = _create_provider(provider_name, base_url)
        logger.info("Created %s provider at %s", provider_name, base_url or "default")

    return _providers[cache_key]


def _create_provider(provider_name: str, base_url: Optional[str] = None) -> BaseProvider:
    """Instantiate a provider by name."""
    defaults = {
        "ollama": ("http://localhost:11434", OllamaProvider),
        "vllm": ("http://localhost:8000", VLLMProvider),
        "litellm": ("http://localhost:4000", LiteLLMProvider),
    }

    if provider_name not in defaults:
        raise ValueError(
            f"Unknown provider '{provider_name}'. "
            f"Available: {', '.join(defaults.keys())}"
        )

    default_url, cls = defaults[provider_name]
    return cls(base_url=base_url or default_url)


def list_providers() -> list[str]:
    """Return names of all available providers."""
    return ["ollama", "vllm", "litellm"]
