#!/usr/bin/env python3
"""
Constitutional AIOps - Full Benchmark Test

Runs a curated benchmark with detailed debug output.
Saves structured JSON results to benchmark/results/.

Uses qwen3:4b-instruct for annotation and qwen3:14b for RCA.

Usage:
    python benchmark/scripts/run/test_5plus5.py                       # Default curated_150
    python benchmark/scripts/run/test_5plus5.py --dataset benchmark/intermediate/datasets/benchmark_431_seed42.json
    python benchmark/scripts/run/test_5plus5.py --dataset latest      # Auto-detect latest
    python benchmark/scripts/run/test_5plus5.py --ann=5 --rca=5       # Quick smoke (equals form)
    python benchmark/scripts/run/test_5plus5.py --ann 5 --rca 5       # Quick smoke (space form)
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Detect if running on Jarvis Labs (localhost) or remotely
# Jarvis Labs Ollama template binds to port 6006, models in /home/.ollama/
# Phase 4.0d (2026-05-12): also support Stack B (vLLM separate ports) via
# explicit FAST_AGENT_URL/REASONING_AGENT_URL env vars set by caller.
if os.path.exists("/home/.ollama/models"):
    JARVIS_URL = "http://localhost:6006"
    print("[INFO] Running on Jarvis Labs - using localhost:6006 Ollama")
elif os.environ.get("FAST_AGENT_URL") and os.environ.get("REASONING_AGENT_URL"):
    # Caller pre-set both URLs (e.g., Stack B vLLM 8000/8001) — honor them.
    print(f"[INFO] Using pre-set FAST_AGENT_URL={os.environ['FAST_AGENT_URL']}")
    print(f"[INFO] Using pre-set REASONING_AGENT_URL={os.environ['REASONING_AGENT_URL']}")
    JARVIS_URL = None  # skip the override below
else:
    JARVIS_URL = os.environ.get(
        "JARVIS_OLLAMA_URL",
        "https://96c3f93672471.notebooks.jarvislabs.net",
    )
if JARVIS_URL is not None:
    os.environ["FAST_AGENT_URL"] = f"{JARVIS_URL}/v1"
    os.environ["REASONING_AGENT_URL"] = f"{JARVIS_URL}/v1"
os.environ.setdefault("FAST_AGENT_MODEL", "qwen3:4b-instruct")
os.environ.setdefault("REASONING_AGENT_MODEL", "qwen3:14b")
os.environ.setdefault("FAST_AGENT_TIMEOUT", "120")
os.environ.setdefault("REASONING_AGENT_TIMEOUT", "180")

# Reload config after env vars set
import importlib
import src.config
importlib.reload(src.config)

from src.benchmark.runner import BenchmarkRunner, BenchmarkConfig, BenchmarkStatus
from src.benchmark.evaluator import BenchmarkEvaluator


def save_results(result, ann_results, rca_results, dataset_label="curated_150 (seed=42, English only)"):
    """Save benchmark results to benchmark/results/ as structured JSON.

    Runs multi-metric evaluation (BERTScore, cosine similarity, term overlap)
    as post-processing before saving.
    """
    results_dir = PROJECT_ROOT / "benchmark" / "results" / result.model_name
    results_dir.mkdir(parents=True, exist_ok=True)

    # Per-test detailed results (with rule_score and source from runner)
    test_results_data = []
    for tr in result.test_results:
        test_results_data.append({
            "test_id": tr.test_id,
            "model": os.environ.get("FAST_AGENT_MODEL") if tr.task_type == "annotation"
                     else os.environ.get("REASONING_AGENT_MODEL"),
            "task_type": tr.task_type,
            "source": tr.source,
            "input_text": tr.expected_output[:500],
            "expected_output": tr.expected_output,
            "actual_output": tr.actual_output,
            "correct": tr.correct,
            "rule_score": tr.rule_score,
            "rule_max_score": tr.rule_max_score,
            "bert_f1": 0.0,
            "cosine_similarity": 0.0,
            "term_overlap": 0.0,
            "inference_latency_ms": round(tr.inference_latency_ms, 2),
            "total_latency_ms": round(tr.total_latency_ms, 2),
            "network_rtt_ms": round(result.network_rtt_ms, 2),
            "timestamp": tr.timestamp,
        })

    # Run multi-metric evaluation (BERTScore + cosine + term overlap)
    print("\n[EVAL] Running multi-metric evaluation (post-processing)...")
    try:
        evaluator = BenchmarkEvaluator(use_bertscore=True, use_embeddings=True)
        test_results_data = evaluator.compute_all_metrics(test_results_data)
        print("[EVAL] Multi-metric evaluation complete")
    except Exception as e:
        print(f"[EVAL] Warning: Multi-metric evaluation failed: {e}")
        print("[EVAL] Saving with rule-based scores only")

    # Save per-test results
    results_file = results_dir / "results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(test_results_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[SAVED] Per-test results -> {results_file}")

    # Compute aggregate semantic metrics
    ann_data = [r for r in test_results_data if r.get("task_type") == "annotation"]
    rca_data = [r for r in test_results_data if r.get("task_type") == "rca"]

    def safe_mean(values):
        filtered = [v for v in values if v > 0]
        return round(sum(filtered) / len(filtered), 4) if filtered else 0.0

    ann_bert_f1 = safe_mean([r.get("bert_f1", 0) for r in ann_data])
    rca_bert_f1 = safe_mean([r.get("bert_f1", 0) for r in rca_data])
    ann_cosine = safe_mean([r.get("cosine_similarity", 0) for r in ann_data])
    rca_cosine = safe_mean([r.get("cosine_similarity", 0) for r in rca_data])
    ann_overlap = safe_mean([r.get("term_overlap", 0) for r in ann_data])
    rca_overlap = safe_mean([r.get("term_overlap", 0) for r in rca_data])
    all_bert_f1 = safe_mean([r.get("bert_f1", 0) for r in test_results_data])
    all_cosine = safe_mean([r.get("cosine_similarity", 0) for r in test_results_data])
    all_overlap = safe_mean([r.get("term_overlap", 0) for r in test_results_data])

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
        "annotation_min_latency_ms": round(min(ann_latencies), 2) if ann_latencies else 0,
        "annotation_max_latency_ms": round(max(ann_latencies), 2) if ann_latencies else 0,
        "rca_avg_latency_ms": round(sum(rca_latencies) / len(rca_latencies), 2) if rca_latencies else 0,
        "rca_min_latency_ms": round(min(rca_latencies), 2) if rca_latencies else 0,
        "rca_max_latency_ms": round(max(rca_latencies), 2) if rca_latencies else 0,
        "bert_f1": all_bert_f1,
        "annotation_bert_f1": ann_bert_f1,
        "rca_bert_f1": rca_bert_f1,
        "cosine_similarity": all_cosine,
        "annotation_cosine_sim": ann_cosine,
        "rca_cosine_sim": rca_cosine,
        "term_overlap": all_overlap,
        "annotation_term_overlap": ann_overlap,
        "rca_term_overlap": rca_overlap,
        "dataset": dataset_label,
        "temperature": 0.0,
        "determinism": "temperature=0.0 + seed=hash(prompt) % 2^32",
        "endpoint": JARVIS_URL,
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
    """Run the full benchmark (or a subset via CLI args) with detailed debug output."""
    # Parse CLI args — argparse handles both --ann=5 and --ann 5 forms
    parser = argparse.ArgumentParser(description="Constitutional AIOps Benchmark Test")
    parser.add_argument("--ann", type=int,
                        default=int(os.environ.get("MAX_ANNOTATION_TESTS", "100")),
                        help="Max annotation test cases to run")
    parser.add_argument("--rca", type=int,
                        default=int(os.environ.get("MAX_RCA_TESTS", "50")),
                        help="Max RCA test cases to run")
    parser.add_argument("--dataset", type=str, default="",
                        help="Dataset file path or 'latest'")
    args = parser.parse_args()
    max_ann = args.ann
    max_rca = args.rca
    dataset_file = args.dataset

    # Resolve dataset
    if dataset_file == "latest":
        dataset_file = "benchmark_latest"
        dataset_label = "latest available benchmark"
    elif dataset_file:
        dataset_label = dataset_file
    else:
        dataset_label = "curated_150 (seed=42, English only)"

    print("=" * 70)
    print("CONSTITUTIONAL AIOPS - BENCHMARK TEST")
    print("=" * 70)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print(f"Fast Model:      {os.environ['FAST_AGENT_MODEL']}")
    print(f"Reasoning Model: {os.environ['REASONING_AGENT_MODEL']}")
    print(f"Endpoint:        {JARVIS_URL}")
    print(f"Dataset:         {dataset_label}")
    print(f"Test counts:     {max_ann} annotation + {max_rca} RCA")
    print("=" * 70)

    config = BenchmarkConfig(
        model_name="constitutional_aiops",
        max_annotation_tests=max_ann,
        max_rca_tests=max_rca,
        temperature=0.0,
        timeout_seconds=300,
        calibrate_network=True,
        use_curated_150=not bool(dataset_file),
        curated_dataset=dataset_file,
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
            save_results(result, ann_results, rca_results, dataset_label=dataset_label)

            # Auto-generate all output tables (all_tables.md, paper_tables, index, etc.)
            try:
                from benchmark.scripts.export_metrics import export_all
                export_all("constitutional_aiops")
            except Exception as e:
                print(f"[EXPORT] Warning: Auto-export failed: {e}")
                print("[EXPORT] Run manually: python benchmark/scripts/eval/export_metrics.py")

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
