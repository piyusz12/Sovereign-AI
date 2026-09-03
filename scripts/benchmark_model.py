"""
Sovereign AI Workbench — Model Benchmarking

Measure VRAM, RAM, tokens/sec, and latency for each model.
Results saved to tests/benchmarks/ as both JSON and markdown.

Phase 4: Uses OllamaClient, adds VRAM measurement via ps, multi-run averaging,
and markdown report generation.

Usage:
    python scripts/benchmark_model.py                   # benchmark all models
    python scripts/benchmark_model.py --model qwen3:14b  # benchmark one model
    python scripts/benchmark_model.py --runs 5           # 5 runs per model
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.router.ollama_client import ollama_client


BENCHMARK_DIR = Path("tests/benchmarks")
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

MODELS = [
    {"name": "qwen3:14b", "category": "reasoning"},
    {"name": "qwen2.5-coder:7b", "category": "coding"},
]

TEST_PROMPTS = {
    "reasoning": "Explain the difference between a gate valve and a globe valve in a P&ID.",
    "coding": "Write a Python function that reads a CSV file and calculates the average of a numeric column.",
}


async def get_vram_usage(model_name: str) -> dict:
    """Get VRAM usage for a specific model from Ollama ps."""
    running = await ollama_client.ps()
    for m in running:
        if m.name == model_name or m.name.startswith(model_name.split(":")[0]):
            return {
                "vram_mb": m.vram_used_mb,
                "size_vram_bytes": m.size_vram,
                "size_ram_bytes": m.size_ram,
            }
    return {"vram_mb": 0, "size_vram_bytes": 0, "size_ram_bytes": 0}


async def benchmark_single_run(model_name: str, category: str, run_index: int) -> dict:
    """Execute a single benchmark run for a model."""
    prompt = TEST_PROMPTS.get(category, TEST_PROMPTS["reasoning"])

    try:
        result = await ollama_client.generate(
            model=model_name,
            prompt=prompt,
            max_tokens=256,
            temperature=0.7,
        )

        # Get VRAM usage after inference
        vram = await get_vram_usage(model_name)

        return {
            "run": run_index,
            "success": True,
            "tokens_per_sec": result.tokens_per_sec,
            "eval_count": result.eval_count,
            "eval_duration_ns": result.eval_duration_ns,
            "prompt_eval_duration_ns": result.prompt_eval_duration_ns,
            "total_duration_ns": result.total_duration_ns,
            "first_token_ms": round(result.prompt_eval_duration_ns / 1e6, 2) if result.prompt_eval_duration_ns else 0,
            "total_time_s": round(result.total_duration_ns / 1e9, 2) if result.total_duration_ns else 0,
            "vram_mb": vram["vram_mb"],
        }
    except Exception as e:
        return {
            "run": run_index,
            "success": False,
            "error": str(e),
        }


async def benchmark_model(model_name: str, category: str, num_runs: int = 3) -> dict:
    """Benchmark a model with multiple runs. Discards the first run (warmup)."""
    print(f"\n{'='*60}")
    print(f"  Benchmarking: {model_name} ({category})")
    print(f"  Runs: {num_runs} (first is warmup)")
    print(f"{'='*60}")

    # Check if model is available
    exists = await ollama_client.model_exists(model_name)
    if not exists:
        print(f"  SKIP: Model not pulled. Run: ollama pull {model_name}")
        return {
            "model": model_name,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "status": "skipped",
            "reason": "Model not pulled",
        }

    runs = []
    for i in range(num_runs):
        label = "warmup" if i == 0 else f"run {i}"
        print(f"  [{label}] ", end="", flush=True)

        result = await benchmark_single_run(model_name, category, i)
        runs.append(result)

        if result["success"]:
            print(
                f"{result['tokens_per_sec']:.1f} tok/s, "
                f"first token: {result['first_token_ms']:.0f}ms, "
                f"VRAM: {result['vram_mb']}MB"
            )
        else:
            print(f"FAILED: {result.get('error', 'unknown')}")

    # Calculate averages (excluding warmup run 0)
    scored_runs = [r for r in runs[1:] if r.get("success")]
    if scored_runs:
        avg = {
            "tokens_per_sec": round(sum(r["tokens_per_sec"] for r in scored_runs) / len(scored_runs), 2),
            "first_token_ms": round(sum(r["first_token_ms"] for r in scored_runs) / len(scored_runs), 2),
            "total_time_s": round(sum(r["total_time_s"] for r in scored_runs) / len(scored_runs), 2),
            "vram_mb": scored_runs[-1]["vram_mb"],  # Use latest VRAM reading
        }
        print(f"\n  Average: {avg['tokens_per_sec']} tok/s, "
              f"first token: {avg['first_token_ms']}ms, "
              f"VRAM: {avg['vram_mb']}MB")
    else:
        avg = {}
        print("\n  No successful scored runs")

    return {
        "model": model_name,
        "category": category,
        "timestamp": datetime.now().isoformat(),
        "prompt": TEST_PROMPTS.get(category, ""),
        "num_runs": num_runs,
        "runs": runs,
        "averages": avg,
        "status": "completed" if scored_runs else "failed",
    }


def generate_markdown_report(results: list[dict], output_path: Path) -> None:
    """Generate a human-readable markdown benchmark report."""
    lines = [
        "# Sovereign AI Workbench — Model Benchmarks",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Hardware:** RTX 4060 Laptop 8GB VRAM + Ryzen 7 7840HS + 16GB RAM",
        "",
        "## Summary",
        "",
        "| Model | Category | Tok/s | First Token (ms) | VRAM (MB) | Status |",
        "|-------|----------|-------|-------------------|-----------|--------|",
    ]

    for r in results:
        avg = r.get("averages", {})
        if avg:
            lines.append(
                f"| {r['model']} | {r['category']} | "
                f"{avg.get('tokens_per_sec', '-')} | "
                f"{avg.get('first_token_ms', '-')} | "
                f"{avg.get('vram_mb', '-')} | "
                f"{r['status']} |"
            )
        else:
            lines.append(
                f"| {r['model']} | {r['category']} | - | - | - | {r['status']} |"
            )

    lines.extend([
        "",
        "## Detailed Runs",
        "",
    ])

    for r in results:
        lines.append(f"### {r['model']} ({r['category']})")
        lines.append("")
        if r.get("runs"):
            lines.append("| Run | Tok/s | First Token (ms) | Total (s) | VRAM (MB) |")
            lines.append("|-----|-------|-------------------|-----------|-----------|")
            for run in r["runs"]:
                if run.get("success"):
                    label = "warmup" if run["run"] == 0 else str(run["run"])
                    lines.append(
                        f"| {label} | {run['tokens_per_sec']:.1f} | "
                        f"{run['first_token_ms']:.0f} | "
                        f"{run['total_time_s']:.1f} | "
                        f"{run['vram_mb']} |"
                    )
                else:
                    lines.append(f"| {run['run']} | FAILED | - | - | - |")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


async def main():
    parser = argparse.ArgumentParser(description="Benchmark Sovereign AI models")
    parser.add_argument("--model", type=str, help="Benchmark a specific model (e.g. qwen3:14b)")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs per model (default: 3)")
    args = parser.parse_args()

    print("Sovereign AI Workbench — Model Benchmarks")
    print("=" * 60)

    # Check Ollama
    is_running = await ollama_client.is_running()
    if not is_running:
        print("ERROR: Ollama is not running. Start with 'ollama serve'.")
        sys.exit(1)

    # Select models to benchmark
    if args.model:
        models_to_test = [
            m for m in MODELS if m["name"] == args.model
        ]
        if not models_to_test:
            # Allow benchmarking any model, not just registered ones
            models_to_test = [{"name": args.model, "category": "reasoning"}]
    else:
        models_to_test = MODELS

    # Run benchmarks
    all_results = []
    for model in models_to_test:
        result = await benchmark_model(model["name"], model["category"], num_runs=args.runs)
        all_results.append(result)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = BENCHMARK_DIR / f"benchmark_{timestamp}.json"
    json_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"\nJSON saved to: {json_path}")

    md_path = BENCHMARK_DIR / f"benchmark_{timestamp}.md"
    generate_markdown_report(all_results, md_path)
    print(f"Markdown saved to: {md_path}")


if __name__ == "__main__":
    asyncio.run(main())
