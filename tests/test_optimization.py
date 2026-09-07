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


def test_cpp_core_bridge_interface():
    from backend.cpp_bridge import cpp_core

    # Test classification
    task, model, conf, reason = cpp_core.classify("def fibonacci(n): return n")
    assert task == "coding"
    assert "coder" in model
    assert conf > 0.5

    # Test memory switch check
    allowed, evict = cpp_core.memory_prepare_switch("qwen3-14b", 5500)
    assert allowed is True
    cpp_core.record_model_loaded("qwen3-14b", 5500)

    # Switching to coder should trigger eviction of qwen3-14b
    allowed, evict = cpp_core.memory_prepare_switch("qwen2.5-coder-7b", 4500)
    assert allowed is True
    assert evict == "qwen3-14b"
    cpp_core.record_model_loaded("qwen2.5-coder-7b", 4500)

    # Test firewall check
    pol, rsn, compliant = cpp_core.firewall_evaluate("read_file")
    assert pol == "allowed"
    assert compliant is True

    blocked_pol, blocked_rsn, blocked_comp = cpp_core.firewall_evaluate("send_external")
    assert blocked_pol == "blocked"
    assert blocked_comp is False

    # Test token estimation
    tokens = cpp_core.estimate_tokens("Hello Sovereign AI world")
    assert tokens > 0


def test_bottleneck_diagnosis_classifier():
    from benchmarks.runner import diagnose_bottlenecks

    # Case 1: Scheduler / Concurrency Bottleneck
    diag1, rec1 = diagnose_bottlenecks(queue_wait_ms=120.0, ttft_ms=300.0, itl_p95_ms=30.0, tps=35.0, vram_used_mb=4000.0)
    assert "CASE 1" in diag1

    # Case 2: Prefill / Context Bottleneck
    diag2, rec2 = diagnose_bottlenecks(queue_wait_ms=10.0, ttft_ms=1600.0, itl_p95_ms=30.0, tps=35.0, vram_used_mb=4000.0)
    assert "CASE 2" in diag2

    # Case 3: Decode / Memory Bandwidth Bottleneck
    diag3, rec3 = diagnose_bottlenecks(queue_wait_ms=10.0, ttft_ms=400.0, itl_p95_ms=85.0, tps=12.0, vram_used_mb=4000.0)
    assert "CASE 3" in diag3

    # Optimal
    diag_opt, rec_opt = diagnose_bottlenecks(queue_wait_ms=10.0, ttft_ms=300.0, itl_p95_ms=32.0, tps=32.0, vram_used_mb=4000.0)
    assert "OPTIMAL" in diag_opt


def test_benchmark_runner_mock_suite(tmp_path):
    from pathlib import Path
    from benchmarks.runner import BenchmarkRunner

    runner = BenchmarkRunner(mock=True)
    short_chat_path = Path("benchmarks/short_chat.json")
    assert short_chat_path.exists()

    results = runner.run_suite(short_chat_path)
    assert len(results) == 3
    for r in results:
        assert r.tokens_generated > 0
        assert r.ttft_ms > 0
        assert r.itl_p50_ms > 0
        assert r.tokens_per_second > 0
        assert r.cpp_core_overhead_us > 0

    json_path, md_path = runner.generate_report(tmp_path)
    assert json_path.exists()
    assert md_path.exists()

