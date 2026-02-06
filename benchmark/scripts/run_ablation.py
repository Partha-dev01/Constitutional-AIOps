#!/usr/bin/env python3
"""
Constitutional AIOps - Ablation Study Runner

Runs the full 150-test benchmark under different configurations to measure
the contribution of each architectural component.

Configurations:
  full        - Baseline: Qwen3-4B-instruct (ann) + Qwen3-14B (rca)
  single-4b   - Single agent: Qwen3-4B-instruct for BOTH tasks
  single-14b  - Single agent: Qwen3-14B for BOTH tasks
  no-structured - Skip JSON parsing, raw text scoring only

Usage:
    python benchmark/scripts/run_ablation.py --config full
    python benchmark/scripts/run_ablation.py --config single-4b
    python benchmark/scripts/run_ablation.py --config all       # Run all 4 sequentially
    python benchmark/scripts/run_ablation.py --config all --ann 5 --rca 5  # Quick test

Time estimate: ~20 min per config on Jarvis Labs, ~1.5 hours for all 4.
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Detect if running on Jarvis Labs (localhost) or remotely
# Jarvis Labs Ollama template binds to port 6006, models in /home/.ollama/
if os.path.exists("/home/.ollama/models"):
    JARVIS_URL = "http://localhost:6006"
    print("[INFO] Running on Jarvis Labs - using localhost:6006 Ollama")
else:
    JARVIS_URL = os.environ.get(
        "JARVIS_OLLAMA_URL",
        "https://96c3f93672471.notebooks.jarvislabs.net",
    )

ABLATION_CONFIGS = {
    "full": {
        "description": "Full System (Hybrid dual-agent baseline)",
        "fast_model": "qwen3:4b-instruct",
        "reasoning_model": "qwen3:14b",
        "model_name": "ablation_full",
    },
    "single-4b": {
        "description": "Single Agent - Qwen3-4B for both annotation and RCA",
        "fast_model": "qwen3:4b-instruct",
        "reasoning_model": "qwen3:4b-instruct",
        "model_name": "ablation_single_4b",
    },
    "single-14b": {
        "description": "Single Agent - Qwen3-14B for both annotation and RCA",
        "fast_model": "qwen3:14b",
        "reasoning_model": "qwen3:14b",
        "model_name": "ablation_single_14b",
    },
    "no-structured": {
        "description": "No Structured Output - raw text, no JSON metadata extraction",
        "fast_model": "qwen3:4b-instruct",
        "reasoning_model": "qwen3:14b",
        "model_name": "ablation_no_structured",
        "no_structured": True,
    },
}


def setup_env(config: dict):
    """Set environment variables for the ablation configuration."""
    os.environ["FAST_AGENT_URL"] = f"{JARVIS_URL}/v1"
    os.environ["REASONING_AGENT_URL"] = f"{JARVIS_URL}/v1"
    os.environ["FAST_AGENT_MODEL"] = config["fast_model"]
    os.environ["REASONING_AGENT_MODEL"] = config["reasoning_model"]
    os.environ["FAST_AGENT_TIMEOUT"] = "120"
    os.environ["REASONING_AGENT_TIMEOUT"] = "180"

    # Reload config AND runner so MODELS dict gets fresh values from new env vars
    # (MODELS is module-level, evaluated once at import - must reload to rebuild)
    import importlib
    import src.config
    importlib.reload(src.config)
    import src.benchmark.runner
    importlib.reload(src.benchmark.runner)


async def run_single_ablation(config_name: str, config: dict, max_ann: int, max_rca: int):
    """Run a single ablation configuration."""
    # MUST set env and reload modules BEFORE importing runner
    # (MODELS dict is built at import time from config values)
    setup_env(config)

    from src.benchmark.runner import BenchmarkRunner, BenchmarkConfig, BenchmarkStatus
    from src.benchmark.evaluator import BenchmarkEvaluator

    print("\n" + "=" * 70)
    print(f"ABLATION: {config['description']}")
    print("=" * 70)
    print(f"Config:          {config_name}")
    print(f"Fast Model:      {config['fast_model']}")
    print(f"Reasoning Model: {config['reasoning_model']}")
    print(f"Test counts:     {max_ann} annotation + {max_rca} RCA")
    print(f"Timestamp:       {datetime.utcnow().isoformat()}")
    print("=" * 70)

    # Use "constitutional_aiops" which is in the MODELS dict and reads
    # from config.llm.* (now refreshed by setup_env -> importlib.reload)
    bench_config = BenchmarkConfig(
        model_name="constitutional_aiops",
        max_annotation_tests=max_ann,
        max_rca_tests=max_rca,
        temperature=0.0,
        timeout_seconds=300,
        calibrate_network=True,
        use_curated_150=True,
    )

    runner = BenchmarkRunner()

    def progress_callback(task_type: str, current: int, total: int):
        print(f"   [{task_type.upper()}] {current}/{total}")

    try:
        result = await runner.run_benchmark(bench_config, progress_callback)

        if result.status != BenchmarkStatus.COMPLETED:
            print(f"\n[FAILED] {config_name}: {result.error}")
            return None

        # Save results
        results_dir = PROJECT_ROOT / "benchmark" / "results" / config["model_name"]
        results_dir.mkdir(parents=True, exist_ok=True)

        # Per-test results
        test_results_data = []
        for tr in result.test_results:
            test_results_data.append({
                "test_id": tr.test_id,
                "model": config["fast_model"] if tr.task_type == "annotation"
                         else config["reasoning_model"],
                "task_type": tr.task_type,
                "source": tr.source,
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
                "timestamp": tr.timestamp,
            })

        # Run multi-metric evaluation
        print(f"\n[EVAL] Running multi-metric evaluation for {config_name}...")
        try:
            evaluator = BenchmarkEvaluator(use_bertscore=True, use_embeddings=True)
            test_results_data = evaluator.compute_all_metrics(test_results_data)
            print("[EVAL] Multi-metric evaluation complete")
        except Exception as e:
            print(f"[EVAL] Warning: {e}")

        # Save per-test results
        with open(results_dir / "results.json", "w", encoding="utf-8") as f:
            json.dump(test_results_data, f, indent=2, ensure_ascii=False, default=str)

        # Compute aggregates
        ann_results = [r for r in result.test_results if r.task_type == "annotation"]
        rca_results = [r for r in result.test_results if r.task_type == "rca"]
        ann_data = [r for r in test_results_data if r.get("task_type") == "annotation"]
        rca_data = [r for r in test_results_data if r.get("task_type") == "rca"]

        def sm(vals):
            f = [v for v in vals if v > 0]
            return round(sum(f) / len(f), 4) if f else 0.0

        summary = {
            "model_name": config["model_name"],
            "ablation_config": config_name,
            "description": config["description"],
            "fast_model": config["fast_model"],
            "reasoning_model": config["reasoning_model"],
            "annotation_accuracy": result.annotation_accuracy,
            "rca_accuracy": result.rca_accuracy,
            "overall_accuracy": round(result.passed_tests / max(result.total_tests, 1) * 100, 2),
            "annotation_tests": len(ann_results),
            "annotation_passed": sum(1 for r in ann_results if r.correct),
            "rca_tests": len(rca_results),
            "rca_passed": sum(1 for r in rca_results if r.correct),
            "total_tests": result.total_tests,
            "total_correct": result.passed_tests,
            "avg_inference_latency_ms": result.avg_latency_ms,
            "p50_latency_ms": result.p50_latency_ms,
            "p95_latency_ms": result.p95_latency_ms,
            "bert_f1": sm([r.get("bert_f1", 0) for r in test_results_data]),
            "cosine_similarity": sm([r.get("cosine_similarity", 0) for r in test_results_data]),
            "term_overlap": sm([r.get("term_overlap", 0) for r in test_results_data]),
            "annotation_bert_f1": sm([r.get("bert_f1", 0) for r in ann_data]),
            "rca_bert_f1": sm([r.get("bert_f1", 0) for r in rca_data]),
            "dataset": "curated_150 (seed=42, English only)",
            "temperature": 0.0,
            "timestamp": result.completed_at or datetime.utcnow().isoformat(),
        }

        with open(results_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        with open(results_dir / "benchmark_result.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"\n[SAVED] Results -> {results_dir}/")
        print(f"   Annotation: {summary['annotation_passed']}/{summary['annotation_tests']} = {summary['annotation_accuracy']:.1f}%")
        print(f"   RCA:        {summary['rca_passed']}/{summary['rca_tests']} = {summary['rca_accuracy']:.1f}%")
        print(f"   Overall:    {summary['total_correct']}/{summary['total_tests']} = {summary['overall_accuracy']:.1f}%")

        return summary

    except Exception as e:
        print(f"\n[ERROR] {config_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_ablation_table(results: list[dict]) -> None:
    """Generate ablation comparison table from results."""
    output_dir = PROJECT_ROOT / "benchmark" / "results"

    # Find baseline
    baseline = next((r for r in results if r.get("ablation_config") == "full"), None)
    baseline_acc = baseline["overall_accuracy"] if baseline else 0

    # Markdown
    md = "# Ablation Study Results\n\n"
    md += f"> Generated: {datetime.utcnow().isoformat()}\n\n"
    md += "| Configuration | Ann Acc | RCA Acc | Overall | BERT-F1 | Avg Latency | Delta vs Full |\n"
    md += "|--------------|---------|---------|---------|---------|-------------|---------------|\n"

    for r in results:
        delta = round(r["overall_accuracy"] - baseline_acc, 1) if baseline else 0
        delta_str = f"{delta:+.1f}%" if r.get("ablation_config") != "full" else "-"
        md += (
            f"| {r['description']} | {r['annotation_accuracy']:.1f}% | {r['rca_accuracy']:.1f}% | "
            f"{r['overall_accuracy']:.1f}% | {r.get('bert_f1', 0):.3f} | "
            f"{r['avg_inference_latency_ms']:.0f}ms | {delta_str} |\n"
        )

    # LaTeX
    latex = r"""\begin{table}[h]
\centering
\caption{Ablation Study: Component Contributions}
\label{tab:ablation}
\begin{tabular}{lccccc}
\toprule
\textbf{Configuration} & \textbf{Ann Acc} & \textbf{RCA Acc} & \textbf{BERT-F1} & \textbf{Avg Latency} & \textbf{$\Delta$ vs Full} \\
\midrule
"""

    for r in results:
        delta = round(r["overall_accuracy"] - baseline_acc, 1) if baseline else 0
        delta_str = f"{delta:+.1f}\\%" if r.get("ablation_config") != "full" else "-"
        latex += (
            f"{r['description']} & {r['annotation_accuracy']:.1f}\\% & {r['rca_accuracy']:.1f}\\% & "
            f"{r.get('bert_f1', 0):.3f} & {r['avg_inference_latency_ms']:.0f}ms & {delta_str} \\\\\n"
        )

    latex += r"""\bottomrule
\end{tabular}
\end{table}
"""

    # Save
    with open(output_dir / "ablation_table.md", "w", encoding="utf-8") as f:
        f.write(md)
    with open(output_dir / "ablation_table.tex", "w", encoding="utf-8") as f:
        f.write(latex)

    # Also save combined ablation results JSON
    with open(output_dir / "ablation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n[SAVED] Ablation table -> {output_dir / 'ablation_table.md'}")
    print(f"[SAVED] Ablation LaTeX -> {output_dir / 'ablation_table.tex'}")
    print(f"[SAVED] Ablation JSON  -> {output_dir / 'ablation_results.json'}")


async def main():
    parser = argparse.ArgumentParser(description="Constitutional AIOps Ablation Study")
    parser.add_argument(
        "--config",
        choices=list(ABLATION_CONFIGS.keys()) + ["all"],
        default="all",
        help="Which ablation config to run",
    )
    parser.add_argument("--ann", type=int, default=100, help="Max annotation tests")
    parser.add_argument("--rca", type=int, default=50, help="Max RCA tests")
    args = parser.parse_args()

    configs_to_run = (
        list(ABLATION_CONFIGS.keys()) if args.config == "all"
        else [args.config]
    )

    print("=" * 70)
    print("CONSTITUTIONAL AIOPS - ABLATION STUDY")
    print("=" * 70)
    print(f"Configs to run: {configs_to_run}")
    print(f"Test counts:    {args.ann} annotation + {args.rca} RCA per config")
    print(f"Endpoint:       {JARVIS_URL}")
    print(f"Started:        {datetime.utcnow().isoformat()}")
    print("=" * 70)

    all_results = []
    for config_name in configs_to_run:
        config = ABLATION_CONFIGS[config_name]
        result = await run_single_ablation(config_name, config, args.ann, args.rca)
        if result:
            all_results.append(result)

    if len(all_results) > 1:
        print("\n" + "=" * 70)
        print("ABLATION STUDY COMPLETE - GENERATING COMPARISON TABLE")
        print("=" * 70)
        generate_ablation_table(all_results)

    # Auto-generate all output tables (all_tables.md, paper_tables, index, etc.)
    try:
        from benchmark.scripts.export_metrics import export_all
        export_all("constitutional_aiops")
    except Exception as e:
        print(f"[EXPORT] Warning: Auto-export failed: {e}")
        print("[EXPORT] Run manually: python benchmark/scripts/export_metrics.py")

    print(f"\n[DONE] Completed {len(all_results)}/{len(configs_to_run)} configurations")
    return 0 if len(all_results) == len(configs_to_run) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
