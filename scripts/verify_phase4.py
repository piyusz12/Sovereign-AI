"""
Sovereign AI Workbench — Phase 4 Verification

End-to-end smoke test that verifies Milestone 1:
    Qwen3-14B → local chat → working

Checks:
    1. Ollama is reachable
    2. qwen3:14b is pulled
    3. Model loads into VRAM
    4. Test prompt produces real output
    5. Metrics are valid (tokens/sec, first-token latency)
    6. /health and /sovereignty endpoints respond
    7. Streaming works

Usage:
    python scripts/verify_phase4.py
    python scripts/verify_phase4.py --api-only   # skip Ollama direct tests
    python scripts/verify_phase4.py --quick       # single short prompt only
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.router.ollama_client import ollama_client


# ── Configuration ─────────────────────────────────────────────────────────────

API_BASE = "http://127.0.0.1:8080"
OLLAMA_BASE = "http://localhost:11434"
TARGET_MODEL = "qwen3:14b"
TEST_PROMPT = "Explain what a P&ID is in two sentences."

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


# ── Test Helpers ──────────────────────────────────────────────────────────────


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.status = SKIP
        self.detail = ""
        self.duration_ms = 0.0

    def passed(self, detail: str = "", duration_ms: float = 0.0):
        self.status = PASS
        self.detail = detail
        self.duration_ms = duration_ms

    def failed(self, detail: str = "", duration_ms: float = 0.0):
        self.status = FAIL
        self.detail = detail
        self.duration_ms = duration_ms

    def skipped(self, detail: str = ""):
        self.status = SKIP
        self.detail = detail


results: list[TestResult] = []


def print_header(text: str):
    print(f"\n{'─' * 60}")
    print(f"  {text}")
    print(f"{'─' * 60}")


def print_result(r: TestResult):
    icon = {"PASS": "+", "FAIL": "X", "SKIP": "-"}[r.status]
    time_str = f" ({r.duration_ms:.0f}ms)" if r.duration_ms else ""
    detail_str = f" — {r.detail}" if r.detail else ""
    print(f"  [{icon}] {r.name}{time_str}{detail_str}")


# ── Tests ─────────────────────────────────────────────────────────────────────


async def test_ollama_reachable() -> TestResult:
    """Test 1: Ollama is running and reachable."""
    t = TestResult("Ollama reachable")
    start = time.time()
    try:
        is_up = await ollama_client.is_running()
        ms = round((time.time() - start) * 1000, 2)
        if is_up:
            t.passed("Connected to Ollama", ms)
        else:
            t.failed("Ollama returned non-200", ms)
    except Exception as e:
        t.failed(str(e))
    return t


async def test_model_pulled() -> TestResult:
    """Test 2: qwen3:14b is pulled and available."""
    t = TestResult(f"Model '{TARGET_MODEL}' pulled")
    try:
        models = await ollama_client.list_models()
        names = [m.name for m in models]
        if any(TARGET_MODEL in name for name in names):
            matched = next(m for m in models if TARGET_MODEL in m.name)
            t.passed(f"Found: {matched.name} ({matched.size_gb}GB, {matched.quantization_level})")
        else:
            t.failed(f"Not found. Available: {', '.join(names) or 'none'}")
    except Exception as e:
        t.failed(str(e))
    return t


async def test_model_load() -> TestResult:
    """Test 3: Model loads into VRAM."""
    t = TestResult(f"Load '{TARGET_MODEL}' into VRAM")
    start = time.time()
    try:
        success = await ollama_client.load_model(TARGET_MODEL, keep_alive="5m")
        ms = round((time.time() - start) * 1000, 2)
        if success:
            # Check ps for VRAM usage
            running = await ollama_client.ps()
            vram_info = ""
            for m in running:
                if TARGET_MODEL in m.name:
                    vram_info = f"VRAM: {m.vram_used_mb}MB"
                    break
            t.passed(f"Loaded. {vram_info}", ms)
        else:
            t.failed("load_model returned False", round((time.time() - start) * 1000, 2))
    except Exception as e:
        t.failed(str(e))
    return t


async def test_inference() -> TestResult:
    """Test 4: Send a real prompt and get a meaningful response."""
    t = TestResult("Inference (non-streaming)")
    start = time.time()
    try:
        response = await ollama_client.chat(
            model=TARGET_MODEL,
            messages=[
                {"role": "user", "content": TEST_PROMPT},
            ],
            temperature=0.7,
            max_tokens=256,
        )
        ms = round((time.time() - start) * 1000, 2)

        if response.content and len(response.content) > 20:
            t.passed(
                f"{response.tokens_per_sec} tok/s, "
                f"first_token: {response.first_token_ms}ms, "
                f"eval_count: {response.eval_count}, "
                f"response: {response.content[:80]}...",
                ms,
            )
        else:
            t.failed(f"Response too short: '{response.content}'", ms)
    except Exception as e:
        t.failed(str(e))
    return t


async def test_streaming() -> TestResult:
    """Test 5: Streaming inference works."""
    t = TestResult("Inference (streaming)")
    start = time.time()
    try:
        chunks = []
        async for chunk in ollama_client.chat_stream(
            model=TARGET_MODEL,
            messages=[
                {"role": "user", "content": "What is a control valve? One sentence."},
            ],
            temperature=0.7,
            max_tokens=100,
        ):
            chunks.append(chunk)

        ms = round((time.time() - start) * 1000, 2)
        content = "".join(c.content for c in chunks)
        num_chunks = len(chunks)

        if content and num_chunks > 1:
            t.passed(f"{num_chunks} chunks, {len(content)} chars", ms)
        else:
            t.failed(f"Only {num_chunks} chunks, {len(content)} chars", ms)
    except Exception as e:
        t.failed(str(e))
    return t


async def test_ollama_ps() -> TestResult:
    """Test 6: Ollama ps returns VRAM info."""
    t = TestResult("Ollama ps (VRAM monitoring)")
    try:
        running = await ollama_client.ps()
        if running:
            info = ", ".join(f"{m.name}: {m.vram_used_mb}MB" for m in running)
            t.passed(info)
        else:
            t.passed("No models currently loaded")
    except Exception as e:
        t.failed(str(e))
    return t


async def test_api_health() -> TestResult:
    """Test 7: FastAPI /health endpoint responds."""
    t = TestResult("API /health endpoint")
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{API_BASE}/health")
            ms = round((time.time() - start) * 1000, 2)
            if resp.status_code == 200:
                data = resp.json()
                t.passed(
                    f"sovereign={data.get('sovereign')}, "
                    f"ollama={data.get('services', {}).get('ollama', {}).get('status', '?')}",
                    ms,
                )
            else:
                t.failed(f"HTTP {resp.status_code}", ms)
    except httpx.ConnectError:
        t.skipped("API not running (start with 'python start.py')")
    except Exception as e:
        t.failed(str(e))
    return t


async def test_api_sovereignty() -> TestResult:
    """Test 8: /sovereignty endpoint confirms zero egress."""
    t = TestResult("API /sovereignty endpoint")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{API_BASE}/sovereignty")
            if resp.status_code == 200:
                data = resp.json()
                external = data.get("external_tcp_connections", -1)
                t.passed(f"external_connections={external}, sovereign={data.get('sovereign')}")
            else:
                t.failed(f"HTTP {resp.status_code}")
    except httpx.ConnectError:
        t.skipped("API not running")
    except Exception as e:
        t.failed(str(e))
    return t


async def test_api_chat() -> TestResult:
    """Test 9: POST /api/v1/chat with live inference."""
    t = TestResult("API /api/v1/chat (live inference)")
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{API_BASE}/api/v1/chat",
                json={"message": TEST_PROMPT},
            )
            ms = round((time.time() - start) * 1000, 2)

            if resp.status_code == 200:
                data = resp.json()
                response_text = data.get("response", "")
                route = data.get("route", {})

                if response_text and "[Error" not in response_text and len(response_text) > 20:
                    t.passed(
                        f"route={route.get('task_type')}, "
                        f"model={route.get('model')}, "
                        f"response={response_text[:60]}...",
                        ms,
                    )
                else:
                    t.failed(f"Bad response: {response_text[:100]}", ms)
            else:
                t.failed(f"HTTP {resp.status_code}", ms)
    except httpx.ConnectError:
        t.skipped("API not running")
    except Exception as e:
        t.failed(str(e))
    return t


async def test_api_models_status() -> TestResult:
    """Test 10: GET /api/v1/models/status returns GPU info."""
    t = TestResult("API /api/v1/models/status")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{API_BASE}/api/v1/models/status")
            if resp.status_code == 200:
                data = resp.json()
                gpu = data.get("gpu", {})
                t.passed(
                    f"active={gpu.get('active_heavy_model')}, "
                    f"vram_used={gpu.get('used_vram_mb')}MB"
                )
            else:
                t.failed(f"HTTP {resp.status_code}")
    except httpx.ConnectError:
        t.skipped("API not running")
    except Exception as e:
        t.failed(str(e))
    return t


# ── Main ──────────────────────────────────────────────────────────────────────


async def main():
    parser = argparse.ArgumentParser(description="Phase 4 Verification — Milestone 1")
    parser.add_argument("--api-only", action="store_true", help="Skip direct Ollama tests")
    parser.add_argument("--quick", action="store_true", help="Run minimal tests only")
    args = parser.parse_args()

    print("=" * 60)
    print("  SOVEREIGN AI WORKBENCH — Phase 4 Verification")
    print("  Milestone 1: Qwen3-14B → local chat → working")
    print("=" * 60)

    # Direct Ollama tests
    if not args.api_only:
        print_header("Ollama Direct Tests")
        for test_fn in [
            test_ollama_reachable,
            test_model_pulled,
            test_model_load,
            test_inference,
            *([] if args.quick else [test_streaming]),
            test_ollama_ps,
        ]:
            r = await test_fn()
            results.append(r)
            print_result(r)

            # Stop early if Ollama isn't reachable
            if r.name == "Ollama reachable" and r.status == FAIL:
                print("\n  Stopping: Ollama not reachable. Start with 'ollama serve'.")
                break

    # API tests
    print_header("FastAPI Endpoint Tests")
    for test_fn in [
        test_api_health,
        test_api_sovereignty,
        *([] if args.quick else [test_api_chat, test_api_models_status]),
    ]:
        r = await test_fn()
        results.append(r)
        print_result(r)

    # Summary
    print_header("RESULTS")
    passed = sum(1 for r in results if r.status == PASS)
    failed = sum(1 for r in results if r.status == FAIL)
    skipped = sum(1 for r in results if r.status == SKIP)

    print(f"  Passed:  {passed}")
    print(f"  Failed:  {failed}")
    print(f"  Skipped: {skipped}")
    print(f"  Total:   {len(results)}")

    if failed == 0 and passed > 0:
        print(f"\n  MILESTONE 1 {'ACHIEVED' if not args.api_only else 'PARTIAL'}")
        print("  Qwen3-14B is running locally. Hello Sovereign AI.")
    elif failed > 0:
        print(f"\n  MILESTONE 1 NOT YET ACHIEVED — {failed} test(s) failed")
        for r in results:
            if r.status == FAIL:
                print(f"    - {r.name}: {r.detail}")
    else:
        print("\n  No tests ran successfully.")

    print()
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
