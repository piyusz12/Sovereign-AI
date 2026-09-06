"""Focused checks for the local 8 GB inference optimization layer."""

from __future__ import annotations

import asyncio

import pytest

from backend.optimization.context import ContextBudgeter
from backend.optimization.scheduler import GPUScheduler
from backend.router.model_registry import DEFAULT_MODELS, ModelProvider
from backend.settings import settings


def test_prompt_builder_keeps_static_prefix_stable_and_current_request_last():
    budgeter = ContextBudgeter(max_total_tokens=120, output_reserve_tokens=20)
    history = [{"role": "user", "content": "old turn " * 20}]

    first = budgeter.build_messages(
        system_prompt="Stable policy and tool schema.",
        user_request="First request",
        history=history,
        retrieved_documents=["ranked evidence " * 20],
    )
    second = budgeter.build_messages(
        system_prompt="Stable policy and tool schema.",
        user_request="Second request",
        history=history,
        retrieved_documents=["ranked evidence " * 20],
    )

    assert first.prefix_key == second.prefix_key
    assert first.messages[0]["content"] == "Stable policy and tool schema."
    assert first.messages[-1] == {"role": "user", "content": "First request"}
    assert second.messages[-1] == {"role": "user", "content": "Second request"}
    assert first.budget.used_tokens <= first.budget.max_input_tokens


def test_prompt_builder_trims_an_oversized_static_prefix():
    budgeter = ContextBudgeter(max_total_tokens=60, output_reserve_tokens=20)
    build = budgeter.build_messages(
        system_prompt="x" * 1000,
        user_request="current request",
    )

    assert build.budget.used_tokens <= build.budget.max_input_tokens
    assert build.messages[-1]["content"] == "current request"


@pytest.mark.asyncio
async def test_gpu_scheduler_serializes_jobs():
    scheduler = GPUScheduler()
    active = 0
    peak_active = 0
    completed: list[str] = []

    async def job(name: str):
        nonlocal active, peak_active
        active += 1
        peak_active = max(peak_active, active)
        await asyncio.sleep(0.01)
        completed.append(name)
        active -= 1
        return name

    results = await asyncio.gather(
        scheduler.schedule("background", priority=3, coro=job("background")),
        scheduler.schedule("interactive", priority=1, coro=job("interactive")),
    )

    assert sorted(results) == ["background", "interactive"]
    assert sorted(completed) == ["background", "interactive"]
    assert peak_active == 1
    assert scheduler.queue_depth == 0


def test_default_heavy_models_are_direct_ollama_qwen_profiles():
    for category in ("reasoning", "coding", "vision"):
        model = DEFAULT_MODELS[category]
        assert model.provider is ModelProvider.OLLAMA
        assert model.is_heavy is True
    assert DEFAULT_MODELS["reasoning"].model_id == settings.ollama_reasoning_model
    assert DEFAULT_MODELS["coding"].model_id == settings.ollama_coding_model
