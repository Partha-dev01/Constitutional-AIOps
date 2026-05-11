#!/usr/bin/env python3
"""
Constitutional AIOps - Metrics Exporter

Exports benchmark results in multiple formats from ACTUAL measured data.
No fabricated or estimated values - only real benchmark results.

Output formats:
- LaTeX tables (for Research_V7.tex)
- Markdown tables (for documentation)
- JSON (for API/frontend)

Usage:
    python benchmark/scripts/export_metrics.py
    python benchmark/scripts/export_metrics.py --format latex
    python benchmark/scripts/export_metrics.py --model constitutional_aiops
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = PROJECT_ROOT / "benchmark" / "results"


def load_model_results(model_name: str) -> tuple[dict, list[dict]]:
    """Load summary and per-test results for a model.

    Returns:
        (summary_dict, per_test_results_list)
    """
    model_dir = RESULTS_DIR / model_name
    summary_path = model_dir / "summary.json"
    results_path = model_dir / "results.json"

    if not summary_path.exists():
        raise FileNotFoundError(f"No summary found for model: {model_name}")

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    per_test = []
    if results_path.exists():
        with open(results_path, "r", encoding="utf-8") as f:
            per_test = json.load(f)

    return summary, per_test


def load_all_models() -> list[str]:
    """Find all models with benchmark results."""
    models = []
    if RESULTS_DIR.exists():
        for d in RESULTS_DIR.iterdir():
            if d.is_dir() and (d / "summary.json").exists():
                models.append(d.name)
    return sorted(models)


def safe_mean(values: list[float]) -> float:
    """Mean of non-zero values."""
    filtered = [v for v in values if v > 0]
    return round(sum(filtered) / len(filtered), 4) if filtered else 0.0


def generate_table1_comprehensive(summary: dict, per_test: list[dict]) -> tuple[str, str]:
    """Table 1: Comprehensive Results (primary paper table).

    Uses only actual measured data from the benchmark run.
    """
    ann = [r for r in per_test if r.get("task_type") == "annotation"]
    rca = [r for r in per_test if r.get("task_type") == "rca"]

    ann_correct = sum(1 for r in ann if r.get("correct"))
    rca_correct = sum(1 for r in rca if r.get("correct"))
    total_correct = ann_correct + rca_correct

    ann_acc = round(ann_correct / len(ann) * 100, 1) if ann else 0
    rca_acc = round(rca_correct / len(rca) * 100, 1) if rca else 0
    total_acc = round(total_correct / len(per_test) * 100, 1) if per_test else 0

    ann_bert = safe_mean([r.get("bert_f1", 0) for r in ann])
    rca_bert = safe_mean([r.get("bert_f1", 0) for r in rca])
    all_bert = safe_mean([r.get("bert_f1", 0) for r in per_test])

    ann_cos = safe_mean([r.get("cosine_similarity", 0) for r in ann])
    rca_cos = safe_mean([r.get("cosine_similarity", 0) for r in rca])
    all_cos = safe_mean([r.get("cosine_similarity", 0) for r in per_test])

    ann_overlap = safe_mean([r.get("term_overlap", 0) for r in ann])
    rca_overlap = safe_mean([r.get("term_overlap", 0) for r in rca])
    all_overlap = safe_mean([r.get("term_overlap", 0) for r in per_test])

    ann_latencies = [r.get("inference_latency_ms", 0) for r in ann if r.get("inference_latency_ms", 0) > 0]
    rca_latencies = [r.get("inference_latency_ms", 0) for r in rca if r.get("inference_latency_ms", 0) > 0]
    all_latencies = ann_latencies + rca_latencies

    def p50(vals):
        if not vals:
            return 0
        s = sorted(vals)
        k = (len(s) - 1) * 0.5
        f = int(k)
        c = min(f + 1, len(s) - 1)
        return round(s[f] + (k - f) * (s[c] - s[f]), 0)

    def p95(vals):
        if not vals:
            return 0
        s = sorted(vals)
        k = (len(s) - 1) * 0.95
        f = int(k)
        c = min(f + 1, len(s) - 1)
        return round(s[f] + (k - f) * (s[c] - s[f]), 0)

    fast_model = summary.get("fast_model", "qwen3:4b-instruct")
    reasoning_model = summary.get("reasoning_model", "qwen3:14b")

    # LaTeX
    latex = r"""\begin{table}[h]
\centering
\caption{Comprehensive Benchmark Results}
\label{tab:comprehensive-results}
\begin{tabular}{llccccccc}
\toprule
\textbf{Task} & \textbf{Agent} & \textbf{N} & \textbf{Accuracy} & \textbf{BERT-F1} & \textbf{Cos Sim} & \textbf{Term Ov.} & \textbf{P50 (ms)} & \textbf{P95 (ms)} \\
\midrule
"""
    latex += f"Annotation & {fast_model} & {len(ann)} & {ann_acc:.1f}\\% & {ann_bert:.3f} & {ann_cos:.3f} & {ann_overlap:.3f} & {p50(ann_latencies):.0f} & {p95(ann_latencies):.0f} \\\\\n"
    latex += f"RCA & {reasoning_model} & {len(rca)} & {rca_acc:.1f}\\% & {rca_bert:.3f} & {rca_cos:.3f} & {rca_overlap:.3f} & {p50(rca_latencies):.0f} & {p95(rca_latencies):.0f} \\\\\n"
    latex += r"\midrule" + "\n"
    latex += f"\\textbf{{Overall}} & \\textbf{{Hybrid}} & \\textbf{{{len(per_test)}}} & \\textbf{{{total_acc:.1f}\\%}} & \\textbf{{{all_bert:.3f}}} & \\textbf{{{all_cos:.3f}}} & \\textbf{{{all_overlap:.3f}}} & \\textbf{{{p50(all_latencies):.0f}}} & \\textbf{{{p95(all_latencies):.0f}}} \\\\\n"
    latex += r"""\bottomrule
\end{tabular}
\begin{tablenotes}
\small
\item Dataset: curated 150-sample (seed=42, English only). Temperature=0.0.
\item BERT-F1: microsoft/deberta-xlarge-mnli. Cos Sim: all-MiniLM-L6-v2 (384-dim).
\end{tablenotes}
\end{table}
"""

    # Markdown
    md = "## Table 1: Comprehensive Benchmark Results\n\n"
    md += "| Task | Agent | N | Accuracy | BERT-F1 | Cos Sim | Term Overlap | P50 (ms) | P95 (ms) |\n"
    md += "|------|-------|---|----------|---------|---------|--------------|----------|----------|\n"
    md += f"| Annotation | {fast_model} | {len(ann)} | {ann_acc:.1f}% | {ann_bert:.3f} | {ann_cos:.3f} | {ann_overlap:.3f} | {p50(ann_latencies):.0f} | {p95(ann_latencies):.0f} |\n"
    md += f"| RCA | {reasoning_model} | {len(rca)} | {rca_acc:.1f}% | {rca_bert:.3f} | {rca_cos:.3f} | {rca_overlap:.3f} | {p50(rca_latencies):.0f} | {p95(rca_latencies):.0f} |\n"
    md += f"| **Overall** | **Hybrid** | **{len(per_test)}** | **{total_acc:.1f}%** | **{all_bert:.3f}** | **{all_cos:.3f}** | **{all_overlap:.3f}** | **{p50(all_latencies):.0f}** | **{p95(all_latencies):.0f}** |\n"

    return latex, md


def generate_table2_per_source(per_test: list[dict]) -> tuple[str, str]:
    """Table 2: Per-Source Breakdown.

    Groups results by source dataset (hdfs, bgl, opseval, lemma-rca).
    """
    # Group by task_type + source
    groups = {}
    for r in per_test:
        task = r.get("task_type", "unknown")
        source = r.get("source", "unknown") or "unknown"
        key = (task, source)
        if key not in groups:
            groups[key] = []
        groups[key].append(r)

    # LaTeX
    latex = r"""\begin{table}[h]
\centering
\caption{Per-Source Benchmark Breakdown}
\label{tab:per-source}
\begin{tabular}{llcccc}
\toprule
\textbf{Task} & \textbf{Source} & \textbf{N} & \textbf{Accuracy} & \textbf{BERT-F1} & \textbf{Cos Sim} \\
\midrule
"""

    md = "## Table 2: Per-Source Breakdown\n\n"
    md += "| Task | Source | N | Accuracy | BERT-F1 | Cos Sim |\n"
    md += "|------|--------|---|----------|---------|--------|\n"

    for (task, source), results in sorted(groups.items()):
        n = len(results)
        correct = sum(1 for r in results if r.get("correct"))
        acc = round(correct / n * 100, 1) if n else 0
        bert = safe_mean([r.get("bert_f1", 0) for r in results])
        cos = safe_mean([r.get("cosine_similarity", 0) for r in results])

        task_display = task.capitalize()
        source_display = source.replace("_", " ").title()

        latex += f"{task_display} & {source_display} & {n} & {acc:.1f}\\% & {bert:.3f} & {cos:.3f} \\\\\n"
        md += f"| {task_display} | {source_display} | {n} | {acc:.1f}% | {bert:.3f} | {cos:.3f} |\n"

    latex += r"""\bottomrule
\end{tabular}
\end{table}
"""

    return latex, md


def generate_table3_error_analysis(summary: dict, per_test: list[dict]) -> tuple[str, str]:
    """Table 3: Error Analysis.

    Analyzes failure modes from actual test results.
    """
    failures = [r for r in per_test if not r.get("correct")]

    # Categorize failures
    failure_modes = {}
    for f in failures:
        test_id = f.get("test_id", "")
        task_type = f.get("task_type", "")
        actual = f.get("actual_output", "")
        source = f.get("source", "unknown") or "unknown"

        if actual.startswith("Error:"):
            mode = "Server/Network Error"
        elif task_type == "annotation" and "ANN_1" in test_id:
            # BGL tests are ANN_100+
            mode = "BGL False Positive"
        elif task_type == "rca" and "choices" in f.get("expected_output", ""):
            mode = "MCQ Format Mismatch"
        else:
            mode = f"{task_type.upper()} Incorrect ({source})"

        if mode not in failure_modes:
            failure_modes[mode] = {"count": 0, "test_ids": []}
        failure_modes[mode]["count"] += 1
        failure_modes[mode]["test_ids"].append(test_id)

    # Also use failure analysis from summary if available
    fa = summary.get("failure_analysis", {})

    # LaTeX
    latex = r"""\begin{table}[h]
\centering
\caption{Error Analysis}
\label{tab:error-analysis}
\begin{tabular}{lcp{8cm}}
\toprule
\textbf{Failure Mode} & \textbf{Count} & \textbf{Description} \\
\midrule
"""

    md = "## Table 3: Error Analysis\n\n"
    md += "| Failure Mode | Count | Description |\n"
    md += "|-------------|-------|-------------|\n"

    for mode, data in sorted(failure_modes.items(), key=lambda x: -x[1]["count"]):
        count = data["count"]
        ids_str = ", ".join(data["test_ids"][:5])
        if len(data["test_ids"]) > 5:
            ids_str += f" (+{len(data['test_ids']) - 5} more)"

        latex += f"{mode} & {count} & {ids_str} \\\\\n"
        md += f"| {mode} | {count} | {ids_str} |\n"

    total_failures = len(failures)
    total_tests = len(per_test)
    latex += r"\midrule" + "\n"
    latex += f"\\textbf{{Total Failures}} & \\textbf{{{total_failures}}} & \\textbf{{{total_failures}/{total_tests} = {round(total_failures/max(total_tests,1)*100,1)}\\% error rate}} \\\\\n"
    md += f"| **Total Failures** | **{total_failures}** | **{total_failures}/{total_tests} = {round(total_failures/max(total_tests,1)*100,1)}% error rate** |\n"

    latex += r"""\bottomrule
\end{tabular}
\end{table}
"""

    return latex, md


def generate_ablation_table_from_json() -> tuple[str, str] | tuple[None, None]:
    """Generate ablation table from ablation_results.json if it exists.

    Returns (latex, markdown) or (None, None) if no ablation data.
    """
    ablation_file = RESULTS_DIR / "ablation_results.json"
    if not ablation_file.exists():
        return None, None

    with open(ablation_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    if not results:
        return None, None

    baseline = next((r for r in results if r.get("ablation_config") == "full"), None)
    baseline_acc = baseline["overall_accuracy"] if baseline else 0

    md = "## Table 4: Ablation Study - Component Contributions\n\n"
    md += "| Configuration | Ann Acc | RCA Acc | Overall | BERT-F1 | Cos Sim | Term Ov. | Avg Latency | Delta vs Full |\n"
    md += "|--------------|---------|---------|---------|---------|---------|----------|-------------|---------------|\n"

    latex = r"""\begin{table}[h]
\centering
\caption{Ablation Study: Component Contributions}
\label{tab:ablation}
\begin{tabular}{lcccccccc}
\toprule
\textbf{Configuration} & \textbf{Ann Acc} & \textbf{RCA Acc} & \textbf{Overall} & \textbf{BERT-F1} & \textbf{Cos Sim} & \textbf{Term Ov.} & \textbf{Avg Lat.} & \textbf{$\Delta$} \\
\midrule
"""

    for r in results:
        delta = round(r["overall_accuracy"] - baseline_acc, 1) if baseline else 0
        delta_str = f"{delta:+.1f}%" if r.get("ablation_config") != "full" else "-"
        cos_sim = r.get("cosine_similarity", 0)
        term_ov = r.get("term_overlap", 0)

        md += (
            f"| {r['description']} | {r['annotation_accuracy']:.1f}% | {r['rca_accuracy']:.1f}% | "
            f"{r['overall_accuracy']:.1f}% | {r.get('bert_f1', 0):.3f} | {cos_sim:.3f} | {term_ov:.3f} | "
            f"{r['avg_inference_latency_ms']:.0f}ms | {delta_str} |\n"
        )

        delta_latex = f"{delta:+.1f}\\%" if r.get("ablation_config") != "full" else "-"
        latex += (
            f"{r['description']} & {r['annotation_accuracy']:.1f}\\% & {r['rca_accuracy']:.1f}\\% & "
            f"{r['overall_accuracy']:.1f}\\% & {r.get('bert_f1', 0):.3f} & {cos_sim:.3f} & {term_ov:.3f} & "
            f"{r['avg_inference_latency_ms']:.0f}ms & {delta_latex} \\\\\n"
        )

    n_tests = results[0].get("total_tests", "?") if results else "?"
    md += f"\n> N={n_tests} per configuration. Dataset: curated_150 (seed=42). Temperature=0.0.\n"

    latex += r"""\bottomrule
\end{tabular}
\end{table}
"""

    return latex, md


def generate_combined_results_md() -> str:
    """Generate combined_results.md from combined_results.json."""
    combined_file = RESULTS_DIR / "combined_results.json"
    if not combined_file.exists():
        return ""

    with open(combined_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    if not results:
        return ""

    md = "# Combined Benchmark Results\n\n"
    md += f"> Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

    for r in results:
        name = r.get("model_name", "unknown")
        md += f"## {name}\n\n"
        md += f"| Metric | Value |\n|--------|-------|\n"
        md += f"| Model Type | {r.get('model_type', '-')} |\n"
        md += f"| Fast Model | {r.get('fast_model', '-')} |\n"
        md += f"| Reasoning Model | {r.get('reasoning_model', '-')} |\n"
        md += f"| Annotation Accuracy | {r.get('annotation_accuracy', 0):.1f}% ({r.get('annotation_passed', 0)}/{r.get('annotation_tests', 0)}) |\n"
        md += f"| RCA Accuracy | {r.get('rca_accuracy', 0):.1f}% ({r.get('rca_passed', 0)}/{r.get('rca_tests', 0)}) |\n"
        md += f"| Overall Accuracy | {r.get('overall_accuracy', 0):.1f}% ({r.get('total_correct', 0)}/{r.get('total_tests', 0)}) |\n"
        md += f"| BERTScore F1 | {r.get('bert_f1', 0):.4f} |\n"
        md += f"| Cosine Similarity | {r.get('cosine_similarity', 0):.4f} |\n"
        md += f"| Term Overlap | {r.get('term_overlap', 0):.4f} |\n"
        md += f"| P50 Latency | {r.get('p50_latency_ms', 0):.0f}ms |\n"
        md += f"| P95 Latency | {r.get('p95_latency_ms', 0):.0f}ms |\n"
        md += f"| Timestamp | {r.get('timestamp', '-')} |\n\n"

    return md


def generate_results_index() -> str:
    """Generate results_index.md listing all result files."""
    md = "# Benchmark Results Index\n\n"
    md += f"> Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

    md += "## Top-Level Files\n\n"
    md += "| File | Description |\n|------|-------------|\n"
    md += "| `all_tables.md` | All paper tables + ablation table combined |\n"
    md += "| `all_tables.tex` | LaTeX version of all tables |\n"
    md += "| `paper_tables.md` | Tables 1-3 (comprehensive, per-source, error analysis) |\n"
    md += "| `paper_tables.tex` | LaTeX version of paper tables |\n"
    md += "| `ablation_table.md` | Ablation study comparison table |\n"
    md += "| `ablation_table.tex` | LaTeX version of ablation table |\n"
    md += "| `combined_results.json` | JSON with all model summaries |\n"
    md += "| `combined_results.md` | Markdown rendering of combined results |\n"
    md += "| `ablation_results.json` | JSON with all ablation summaries |\n"
    md += "| `results_index.md` | This file |\n\n"

    md += "## Per-Model Directories\n\n"
    models = load_all_models()
    for model in models:
        model_dir = RESULTS_DIR / model
        files = sorted(f.name for f in model_dir.iterdir() if f.is_file())
        md += f"### `{model}/`\n\n"
        for fname in files:
            md += f"- `{fname}`\n"
        md += "\n"

    return md


def export_tables(model_name: str) -> None:
    """Generate and save all paper tables for a model."""
    summary, per_test = load_model_results(model_name)

    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    # Generate tables
    t1_latex, t1_md = generate_table1_comprehensive(summary, per_test)
    t2_latex, t2_md = generate_table2_per_source(per_test)
    t3_latex, t3_md = generate_table3_error_analysis(summary, per_test)

    # Combined LaTeX
    latex_content = f"""% Constitutional AIOps - Paper Tables
% Generated: {timestamp}
% Model: {model_name}
% Data source: benchmark/results/{model_name}/results.json
% WARNING: All values are from actual benchmark runs. No fabricated data.

{t1_latex}

{t2_latex}

{t3_latex}
"""

    # Combined Markdown
    md_content = f"""# Constitutional AIOps - Paper Tables

> Generated: {timestamp}
> Model: {model_name}
> Source: `benchmark/results/{model_name}/results.json`

{t1_md}

{t2_md}

{t3_md}

---

*All values from actual benchmark runs. No fabricated or estimated data.*
"""

    # Save to benchmark/results/
    output_dir = RESULTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    tex_path = output_dir / "paper_tables.tex"
    md_path = output_dir / "paper_tables.md"

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_content)
    print(f"[SAVED] LaTeX tables -> {tex_path}")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[SAVED] Markdown tables -> {md_path}")

    # Also save per-model
    model_tex = RESULTS_DIR / model_name / "paper_tables.tex"
    model_md = RESULTS_DIR / model_name / "paper_tables.md"

    with open(model_tex, "w", encoding="utf-8") as f:
        f.write(latex_content)

    with open(model_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"[SAVED] Per-model tables -> {RESULTS_DIR / model_name}/")

    return timestamp, t1_latex, t1_md, t2_latex, t2_md, t3_latex, t3_md


def export_all(model_name: str = "constitutional_aiops") -> None:
    """Generate ALL output files: paper tables, ablation table, all_tables, index, combined_results.

    This is the main entry point called by benchmark scripts after completion.
    """
    print("\n[EXPORT] Generating all benchmark output files...")

    # 1. Paper tables (Tables 1-3)
    try:
        result = export_tables(model_name)
        timestamp, t1_latex, t1_md, t2_latex, t2_md, t3_latex, t3_md = result
    except FileNotFoundError as e:
        print(f"[EXPORT] Warning: {e} - skipping paper tables")
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        t1_latex = t1_md = t2_latex = t2_md = t3_latex = t3_md = ""

    # 2. Ablation table (Table 4) - from ablation_results.json if exists
    t4_latex, t4_md = generate_ablation_table_from_json()

    # 3. all_tables.md / all_tables.tex - everything combined
    all_md = f"""# Constitutional AIOps - All Benchmark Tables

> Generated: {timestamp}
> Model: {model_name}
> Source: `benchmark/results/`

{t1_md}

{t2_md}

{t3_md}
"""
    all_latex = f"""% Constitutional AIOps - All Benchmark Tables
% Generated: {timestamp}
% Model: {model_name}
% WARNING: All values are from actual benchmark runs. No fabricated data.

{t1_latex}

{t2_latex}

{t3_latex}
"""

    if t4_md:
        all_md += f"\n{t4_md}\n"
        all_latex += f"\n{t4_latex}\n"

    all_md += "\n---\n\n*All values from actual benchmark runs. No fabricated or estimated data.*\n"

    with open(RESULTS_DIR / "all_tables.md", "w", encoding="utf-8") as f:
        f.write(all_md)
    print(f"[SAVED] All tables (MD)    -> {RESULTS_DIR / 'all_tables.md'}")

    with open(RESULTS_DIR / "all_tables.tex", "w", encoding="utf-8") as f:
        f.write(all_latex)
    print(f"[SAVED] All tables (LaTeX) -> {RESULTS_DIR / 'all_tables.tex'}")

    # 4. combined_results.md
    cr_md = generate_combined_results_md()
    if cr_md:
        with open(RESULTS_DIR / "combined_results.md", "w", encoding="utf-8") as f:
            f.write(cr_md)
        print(f"[SAVED] Combined results   -> {RESULTS_DIR / 'combined_results.md'}")

    # 5. results_index.md
    index_md = generate_results_index()
    with open(RESULTS_DIR / "results_index.md", "w", encoding="utf-8") as f:
        f.write(index_md)
    print(f"[SAVED] Results index      -> {RESULTS_DIR / 'results_index.md'}")

    print("[EXPORT] All output files generated successfully!")


def main():
    parser = argparse.ArgumentParser(description="Export benchmark metrics (actual data only)")
    parser.add_argument("--model", default="constitutional_aiops", help="Model name to export")
    parser.add_argument("--format", choices=["latex", "markdown", "all"], default="all")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    args = parser.parse_args()

    if args.list_models:
        models = load_all_models()
        print(f"Available models: {models}")
        return 0

    try:
        export_all(args.model)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n[OK] Export complete! All tables use actual measured data only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
