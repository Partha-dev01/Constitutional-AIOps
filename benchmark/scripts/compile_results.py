#!/usr/bin/env python3
"""
compile_results.py - Generate a Markdown + LaTeX summary table of all benchmark results.

Usage:
    python benchmark/scripts/compile_results.py [--out docs/RESULTS_SUMMARY.md]
"""

import argparse
import json
import os
from datetime import datetime

BASE = os.path.join(os.path.dirname(__file__), "..", "archive", "originals_2026-05-19")


def load_deduped(path):
    """Load JSONL, deduplicate by case_id (keeps first occurrence)."""
    seen = {}
    if not os.path.exists(path):
        return seen
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            cid = r.get("case_id") or r.get("id") or ""
            if cid and cid not in seen:
                seen[cid] = r
    return seen


def accuracy(records, task_type):
    ok = total = 0
    for r in records.values():
        if r.get("task_type") == task_type:
            total += 1
            ok += bool(r.get("correct"))
    return ok, total


def latency_stats(records):
    lats = [r["latency_ms"] for r in records.values() if r.get("latency_ms")]
    if not lats:
        return None, None
    lats.sort()
    return sum(lats) / len(lats), lats[int(len(lats) * 0.95)]


SYSTEMS = [
    {
        "label": "Constitutional AIOps (Ours)",
        "path": None,  # hardcoded from Phase 4.2 run
        "ann": (180, 218),
        "rca": (202, 213),
        "latency_avg": None,
        "latency_p95": None,
        "notes": "Stack A, Ollama Q4_K_M, 431 cases, L4 24GB",
    },
    {
        "label": "Llama 3.3-70B (Bedrock)",
        "path": os.path.join(BASE, "sota_llama_3_3_70b", "results.jsonl"),
        "ann": None,
        "rca": None,
        "latency_avg": None,
        "latency_p95": None,
        "notes": "SOTA baseline, 400 cases",
    },
    {
        "label": "DeepSeek V3.2 (Bedrock)",
        "path": os.path.join(BASE, "sota_deepseek_v3", "results.jsonl"),
        "ann": None,
        "rca": None,
        "latency_avg": None,
        "latency_p95": None,
        "notes": "SOTA baseline, 400 cases",
    },
]


def build_row(sys):
    if sys["path"] is not None:
        records = load_deduped(sys["path"])
        ann_ok, ann_total = accuracy(records, "annotation")
        rca_ok, rca_total = accuracy(records, "rca")
        avg, p95 = latency_stats(records)
    else:
        ann_ok, ann_total = sys["ann"]
        rca_ok, rca_total = sys["rca"]
        avg = sys["latency_avg"]
        p95 = sys["latency_p95"]

    total = ann_total + rca_total
    overall_ok = ann_ok + rca_ok

    ann_pct = 100 * ann_ok / ann_total if ann_total else 0
    rca_pct = 100 * rca_ok / rca_total if rca_total else 0
    ov_pct = 100 * overall_ok / total if total else 0

    return {
        "label": sys["label"],
        "ann": f"{ann_ok}/{ann_total} ({ann_pct:.1f}%)",
        "ann_pct": ann_pct,
        "rca": f"{rca_ok}/{rca_total} ({rca_pct:.1f}%)",
        "rca_pct": rca_pct,
        "overall": f"{overall_ok}/{total} ({ov_pct:.1f}%)",
        "ov_pct": ov_pct,
        "lat": f"avg {avg:.0f}ms / P95 {p95:.0f}ms" if avg else "—",
        "notes": sys["notes"],
    }


def generate_md(rows):
    lines = [
        f"# Benchmark Results Summary",
        f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
        "## Table 7 — SOTA Baseline Comparison",
        "",
        "| System | Annotation | RCA | Overall | Latency | Notes |",
        "|--------|-----------|-----|---------|---------|-------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['label']} | {r['ann']} | {r['rca']} | {r['overall']} | {r['lat']} | {r['notes']} |"
        )

    # RCA gap analysis
    our_rca = rows[0]["rca_pct"]
    lines += [
        "",
        "## RCA Gap vs SOTA",
        "",
    ]
    for r in rows[1:]:
        gap = our_rca - r["rca_pct"]
        lines.append(f"- **{r['label']}**: Our RCA {our_rca:.1f}% vs {r['rca_pct']:.1f}% = **+{gap:.1f}pp**")

    lines += [
        "",
        "## LaTeX Snippet (Table 7)",
        "",
        "```latex",
        r"\begin{table}[t]",
        r"\caption{SOTA Baseline Comparison (400 cases, same system prompt)}\label{tab:sota}",
        r"\begin{tabular}{lccccc}",
        r"\toprule",
        r"System & Ann. & RCA & Overall & $\Delta$ RCA \\",
        r"\midrule",
    ]
    our_rca_pct = rows[0]["rca_pct"]
    for i, r in enumerate(rows):
        delta = ""
        if i > 0:
            d = our_rca_pct - r["rca_pct"]
            delta = f" & $+{d:.1f}$pp"
        else:
            delta = " & —"
        lines.append(
            f"{r['label']} & {r['ann_pct']:.1f}\\% & {r['rca_pct']:.1f}\\% & {r['ov_pct']:.1f}\\%{delta} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "```",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="docs/RESULTS_SUMMARY.md")
    args = parser.parse_args()

    rows = [build_row(s) for s in SYSTEMS]

    md = generate_md(rows)

    out_path = os.path.join(
        os.path.dirname(__file__), "..", "..", args.out
    )
    out_path = os.path.normpath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(md)
    print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
