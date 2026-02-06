#!/usr/bin/env python3
"""
Constitutional AIOps - Full Benchmark Test

Runs the curated 150-sample benchmark (100 annotation + 33 RCA) with
detailed debug output. Saves structured JSON results to benchmark/results/.

Uses qwen3:4b-instruct for annotation and qwen3:14b for RCA.

Usage: python benchmark/scripts/test_5plus5.py
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Force environment variables for Jarvis Labs
JARVIS_URL = "https://96c3f93672471.notebooks.jarvislabs.net"
os.environ["FAST_AGENT_URL"] = f"{JARVIS_URL}/v1"
os.environ["REASONING_AGENT_URL"] = f"{JARVIS_URL}/v1"
os.environ["FAST_AGENT_MODEL"] = "qwen3:4b-instruct"
os.environ["REASONING_AGENT_MODEL"] = "qwen3:14b"
os.environ["FAST_AGENT_TIMEOUT"] = "120"
os.environ["REASONING_AGENT_TIMEOUT"] = "180"

# Reload config after env vars set
import importlib
import src.config
importlib.reload(src.config)

from src.benchmark.runner import BenchmarkRunner, BenchmarkConfig, BenchmarkStatus


def save_results(result, ann_results, rca_results):
    """Save benchmark results to benchmark/results/ as structured JSON."""
    results_dir = PROJECT_ROOT / "benchmark" / "results" / result.model_name
    results_dir.mkdir(parents=True, exist_ok=True)

    # Per-test detailed results
    test_results_data = []
    for tr in result.test_results:
        test_results_data.append({
            "test_id": tr.test_id,
            "model": os.environ.get("FAST_AGENT_MODEL") if tr.task_type == "annotation"
                     else os.environ.get("REASONING_AGENT_MODEL"),
            "task_type": tr.task_type,
            "input_text": tr.expected_output[:500],
            "expected_output": tr.expected_output,
            "actual_output": tr.actual_output,
            "correct": tr.correct,
            "inference_latency_ms": round(tr.inference_latency_ms, 2),
            "total_latency_ms": round(tr.total_latency_ms, 2),
            "network_rtt_ms": round(result.network_rtt_ms, 2),
            "timestamp": tr.timestamp,
        })

    # Save per-test results
    results_file = results_dir / "results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(test_results_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[SAVED] Per-test results -> {results_file}")

    # Save summary
    ann_passed = sum(1 for r in ann_results if r.correct)
    rca_passed = sum(1 for r in rca_results if r.correct)
    ann_latencies = [tr.inference_latency_ms for tr in ann_results if tr.inference_latency_ms > 0]
    rca_latencies = [tr.inference_latency_ms for tr in rca_results if tr.inference_latency_ms > 0]

    summary = {
        "model_name": result.model_name,
        "model_type": "hybrid",
        "fast_model": os.environ.get("FAST_AGENT_MODEL", "qwen3:4b-instruct"),
        "reasoning_model": os.environ.get("REASONING_AGENT_MODEL", "qwen3:14b"),
        "vram_gb": 15,
        "annotation_accuracy": result.annotation_accuracy,
        "rca_accuracy": result.rca_accuracy,
        "overall_accuracy": round(result.passed_tests / max(result.total_tests, 1) * 100, 2),
        "annotation_tests": len(ann_results),
        "annotation_passed": ann_passed,
        "rca_tests": len(rca_results),
        "rca_passed": rca_passed,
        "total_tests": result.total_tests,
        "total_correct": result.passed_tests,
        "avg_inference_latency_ms": result.avg_latency_ms,
        "p50_latency_ms": result.p50_latency_ms,
        "p95_latency_ms": result.p95_latency_ms,
        "p99_latency_ms": result.p99_latency_ms,
        "network_rtt_ms": result.network_rtt_ms,
        "annotation_avg_latency_ms": round(sum(ann_latencies) / len(ann_latencies), 2) if ann_latencies else 0,
        "rca_avg_latency_ms": round(sum(rca_latencies) / len(rca_latencies), 2) if rca_latencies else 0,
        "dataset": "curated_150 (seed=42, English only)",
        "temperature": 0.0,
        "timestamp": result.completed_at or datetime.utcnow().isoformat(),
    }

    summary_file = results_dir / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"[SAVED] Summary -> {summary_file}")

    # Also save as benchmark_result.json (for API compatibility)
    benchmark_result_file = results_dir / "benchmark_result.json"
    with open(benchmark_result_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"[SAVED] API-compatible -> {benchmark_result_file}")

    # Update combined_results.json (append or replace entry for this model)
    combined_file = PROJECT_ROOT / "benchmark" / "results" / "combined_results.json"
    combined = []
    if combined_file.exists():
        try:
            with open(combined_file, "r", encoding="utf-8") as f:
                combined = json.load(f)
        except (json.JSONDecodeError, ValueError):
            combined = []

    # Remove old entry for same model if exists
    combined = [r for r in combined if r.get("model_name") != result.model_name]
    combined.append(summary)

    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, default=str)
    print(f"[SAVED] Combined results -> {combined_file}")


async def run_5plus5():
    """Run a 5+5 benchmark test with detailed debug output."""
    print("=" * 70)
    print("CONSTITUTIONAL AIOPS - 5+5 BENCHMARK TEST")
    print("=" * 70)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print(f"Fast Model:      {os.environ['FAST_AGENT_MODEL']}")
    print(f"Reasoning Model: {os.environ['REASONING_AGENT_MODEL']}")
    print(f"Endpoint:        {JARVIS_URL}")
    print(f"Dataset:         curated 150-sample (seed=42, English only)")
    print("=" * 70)

    config = BenchmarkConfig(
        model_name="constitutional_aiops",
        max_annotation_tests=5,
        max_rca_tests=5,
        temperature=0.0,
        timeout_seconds=300,
        calibrate_network=True,
        use_curated_150=True,
    )

    runner = BenchmarkRunner()

    def progress_callback(task_type: str, current: int, total: int):
        print(f"   [{task_type.upper()}] {current}/{total}")

    try:
        print("\n[STARTING] 5+5 benchmark...")
        result = await runner.run_benchmark(config, progress_callback)

        print("\n" + "=" * 70)
        print("RESULTS SUMMARY")
        print("=" * 70)
        print(f"Status:              {result.status.value}")
        print(f"Total Tests:         {result.total_tests}")
        print(f"Passed:              {result.passed_tests}")
        print(f"Annotation Accuracy: {result.annotation_accuracy:.2f}%")
        print(f"RCA Accuracy:        {result.rca_accuracy:.2f}%")
        print(f"Avg Latency:         {result.avg_latency_ms:.2f}ms")
        print(f"P50 Latency:         {result.p50_latency_ms:.2f}ms")
        print(f"P95 Latency:         {result.p95_latency_ms:.2f}ms")
        print(f"Network RTT:         {result.network_rtt_ms:.2f}ms")
        print("=" * 70)

        if result.status == BenchmarkStatus.COMPLETED:
            ann_results = [tr for tr in result.test_results if tr.task_type == "annotation"]
            rca_results = [tr for tr in result.test_results if tr.task_type == "rca"]
            ann_passed = sum(1 for r in ann_results if r.correct)
            rca_passed = sum(1 for r in rca_results if r.correct)

            print(f"\n--- ANNOTATION TESTS ({ann_passed}/{len(ann_results)} passed) ---")
            for tr in ann_results:
                status = "[PASS]" if tr.correct else "[FAIL]"
                print(f"\n   {status} {tr.test_id} ({tr.inference_latency_ms:.0f}ms)")
                print(f"         Expected: {tr.expected_output[:200]}")
                print(f"         Actual:   {tr.actual_output[:200]}")

            print(f"\n--- RCA TESTS ({rca_passed}/{len(rca_results)} passed) ---")
            for tr in rca_results:
                status = "[PASS]" if tr.correct else "[FAIL]"
                print(f"\n   {status} {tr.test_id} ({tr.inference_latency_ms:.0f}ms)")
                print(f"         Expected: {tr.expected_output[:200]}")
                print(f"         Actual:   {tr.actual_output[:200]}")

            total_pct = result.passed_tests / max(result.total_tests, 1) * 100
            print("\n" + "=" * 70)
            print("SCORE SUMMARY")
            print("=" * 70)
            print(f"Annotation: {ann_passed}/{len(ann_results)} = {result.annotation_accuracy:.1f}%")
            print(f"RCA:        {rca_passed}/{len(rca_results)} = {result.rca_accuracy:.1f}%")
            print(f"Overall:    {result.passed_tests}/{result.total_tests} = {total_pct:.1f}%")

            # Latency stats
            ann_latencies = [tr.inference_latency_ms for tr in ann_results if tr.inference_latency_ms > 0]
            rca_latencies = [tr.inference_latency_ms for tr in rca_results if tr.inference_latency_ms > 0]
            if ann_latencies:
                print(f"\nAnnotation Latency: avg={sum(ann_latencies)/len(ann_latencies):.0f}ms, min={min(ann_latencies):.0f}ms, max={max(ann_latencies):.0f}ms")
            if rca_latencies:
                print(f"RCA Latency:        avg={sum(rca_latencies)/len(rca_latencies):.0f}ms, min={min(rca_latencies):.0f}ms, max={max(rca_latencies):.0f}ms")

            print("=" * 70)

            # Save results to benchmark/results/ directory
            save_results(result, ann_results, rca_results)

            return 0
        else:
            print(f"\n[FAILED] Benchmark FAILED: {result.error}")
            return 1

    except Exception as e:
        print(f"\n[ERROR] Error running benchmark: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    return asyncio.run(run_5plus5())


if __name__ == "__main__":
    sys.exit(main())
