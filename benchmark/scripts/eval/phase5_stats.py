#!/usr/bin/env python3
"""Phase 5 statistics for paper Table 6 (Ablation, matched eval).

Reads each config's matched-eval JSON from final/, computes:
  - Accuracy + BCa 95% CI (10k resamples) per task type {ann, rca, overall}
  - McNemar paired p-value vs Full (per task type)
  - Cohen's h effect size vs Full (per task type)

Also runs the same stats on the main re-run (final/main_benchmark/) for
the standalone-system row.

Pairing semantics:
  Matched-eval JSONs all use the SAME 431 case_ids (218 ann + 213 rca,
  71 rca excluded → 142 evaluable). McNemar pairs per case_id between
  config X and Full.

Outputs:
  benchmark/final/ablation_v4/phase5_stats.json
  benchmark/final/ablation_v4/phase5_stats.md
  benchmark/final/main_benchmark/phase5_stats.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FINAL = REPO_ROOT / "benchmark" / "final"
ABL_ROOT = FINAL / "ablation_v4"
MAIN_DIR = FINAL / "main_benchmark"

# Add src/ to path so we can import the evaluator helpers
sys.path.insert(0, str(REPO_ROOT))
from src.benchmark.evaluator import (  # noqa: E402
    bootstrap_ci,
    cohens_h,
    mcnemar_test,
)


ABLATION_CONFIGS = [
    "full", "single_4b", "single_14b", "no_structured",
    "no_system_prompt", "with_graph", "no_constitutional", "with_orchestrator",
]

ABLATION_DESCRIPTIONS = {
    "full":              "Full Hybrid",
    "single_4b":         "Single-4B (both tasks)",
    "single_14b":        "Single-14B (both tasks)",
    "no_structured":     "No structured output",
    "no_system_prompt":  "No system prompt",
    "with_graph":        "With graph (RAG)",
    "no_constitutional": "No constitutional",
    "with_orchestrator": "With orchestrator",
}


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def collect_flags(records, task_type=None):
    """Return list of (case_id, correct_bool) for records matching task_type
    AND with correct != None (i.e. evaluable). task_type=None means both."""
    out = []
    for r in records:
        tt = r.get("task_type")
        if task_type is not None and tt != task_type:
            continue
        if tt not in ("annotation", "rca"):
            continue
        c = r.get("correct")
        if c is None:
            continue  # excluded (e.g. 71 RCA exclusions)
        cid = r.get("case_id") or r.get("test_id")
        if not cid:
            continue
        out.append((cid, bool(c)))
    return out


def pair_by_id(base_flags, var_flags):
    """Given two lists of (case_id, bool), return parallel lists of bools
    aligned by case_id. Drops any case_id not in both."""
    bd = dict(base_flags)
    vd = dict(var_flags)
    shared = sorted(set(bd) & set(vd))
    bl = [bd[k] for k in shared]
    vl = [vd[k] for k in shared]
    return bl, vl, shared


def compute_block(records, label):
    """Compute accuracy + BCa CI for ann, rca, overall."""
    block = {"label": label, "tasks": {}}
    for task in ("annotation", "rca"):
        flags = [c for _, c in collect_flags(records, task)]
        n = len(flags)
        ok = sum(flags)
        acc = ok / n if n else float("nan")
        low, high = bootstrap_ci(flags, n_resamples=10_000, ci=0.95,
                                  method="BCa", seed=42)
        block["tasks"][task] = {
            "n": n, "correct": ok, "accuracy": acc,
            "ci_low": low, "ci_high": high,
        }
    # Overall = ann + rca evaluable
    ann_pairs = collect_flags(records, "annotation")
    rca_pairs = collect_flags(records, "rca")
    ovl_flags = [c for _, c in ann_pairs + rca_pairs]
    n = len(ovl_flags)
    ok = sum(ovl_flags)
    acc = ok / n if n else float("nan")
    low, high = bootstrap_ci(ovl_flags, n_resamples=10_000, ci=0.95,
                              method="BCa", seed=42)
    block["tasks"]["overall"] = {
        "n": n, "correct": ok, "accuracy": acc,
        "ci_low": low, "ci_high": high,
    }
    return block


def compare_to_full(records, full_records):
    """For a non-full config, compute McNemar p + Cohen's h vs Full per task."""
    out = {}
    for task in ("annotation", "rca", None):
        task_key = task if task else "overall"
        base = collect_flags(full_records, task) if task else (
            collect_flags(full_records, "annotation")
            + collect_flags(full_records, "rca"))
        var = collect_flags(records, task) if task else (
            collect_flags(records, "annotation")
            + collect_flags(records, "rca"))
        bl, vl, shared = pair_by_id(base, var)
        if len(bl) == 0:
            out[task_key] = {"n_paired": 0, "p_value": float("nan"),
                              "cohens_h": float("nan"), "b": 0, "c": 0,
                              "delta_pp": 0.0}
            continue
        mc = mcnemar_test(bl, vl)
        out[task_key] = {
            "n_paired": mc["n"],
            "b_variant_lost": mc["b"],
            "c_variant_won": mc["c"],
            "p_value": mc["p_value"],
            "cohens_h": mc["cohens_h"],
            "baseline_acc": mc["baseline_acc"],
            "variant_acc": mc["variant_acc"],
            "delta_pp": 100.0 * (mc["variant_acc"] - mc["baseline_acc"]),
        }
    return out


def fmt_pct(x):  return f"{100*x:5.1f}" if x == x else "  nan"
def fmt_ci(lo, hi): return f"[{100*lo:5.1f}, {100*hi:5.1f}]" if lo == lo else "[ -- ]"
def fmt_p(p):
    if p != p: return "  nan"
    if p < 1e-15: return "<1e-15"
    if p < 1e-3:  return f"{p:.2e}"
    return f"{p:.3f}"
def fmt_h(h):
    if h != h: return "  nan"
    return f"{h:+.3f}"


def main():
    print("=" * 100)
    print("PHASE 5 STATISTICS — Paper Table 6 (Ablation, matched eval) + main re-run")
    print("=" * 100)

    # --- 1. Ablation: compute per-config blocks ---
    blocks = {}
    records_by_cfg = {}
    for cfg in ABLATION_CONFIGS:
        p = ABL_ROOT / f"ablation_{cfg}" / "results_sota_eval_431.json"
        if not p.exists():
            print(f"MISSING: {p}")
            sys.exit(1)
        recs = load_json(p)
        records_by_cfg[cfg] = recs
        blocks[cfg] = compute_block(recs, ABLATION_DESCRIPTIONS[cfg])

    full_recs = records_by_cfg["full"]

    # --- 2. Pairwise stats vs Full ---
    pairwise = {}
    for cfg in ABLATION_CONFIGS:
        if cfg == "full":
            continue
        pairwise[cfg] = compare_to_full(records_by_cfg[cfg], full_recs)

    # --- 3. Main re-run (standalone block, no pairwise) ---
    main_recs = load_json(MAIN_DIR / "results_sota_eval_431.json")
    main_block = compute_block(main_recs, "Main re-run (constitutional_aiops, new prompt)")

    # --- 4. Print to console ---
    print("\nABLATION — per config (matched eval)")
    print(f"  {'Config':<24} {'Task':<10} {'N':<5} {'Acc%':>6} {'95% BCa CI':<18} {'Δ vs Full':<10} {'McNemar p':<10} {'Cohen h':<8}")
    print("  " + "-" * 100)
    for cfg in ABLATION_CONFIGS:
        for task in ("annotation", "rca", "overall"):
            t = blocks[cfg]["tasks"][task]
            if cfg == "full":
                d, p_, h_ = "  —", "  —", "  —"
            else:
                pw = pairwise[cfg][task]
                d = f"{pw['delta_pp']:+5.1f}pp"
                p_ = fmt_p(pw["p_value"])
                h_ = fmt_h(pw["cohens_h"])
            print(f"  {cfg:<24} {task:<10} {t['n']:<5} {fmt_pct(t['accuracy']):>6} "
                  f"{fmt_ci(t['ci_low'], t['ci_high']):<18} {d:<10} {p_:<10} {h_:<8}")

    print("\nMAIN RE-RUN — standalone (matched eval)")
    print(f"  {'Task':<10} {'N':<5} {'Acc%':>6} {'95% BCa CI':<18}")
    print("  " + "-" * 50)
    for task in ("annotation", "rca", "overall"):
        t = main_block["tasks"][task]
        print(f"  {task:<10} {t['n']:<5} {fmt_pct(t['accuracy']):>6} "
              f"{fmt_ci(t['ci_low'], t['ci_high']):<18}")

    # --- 5. Write JSON ---
    out_json = {
        "schema_version": 1,
        "source": "FINAL/ablation_v4/ablation_*/results_sota_eval_431.json + FINAL/main_benchmark/results_sota_eval_431.json",
        "bootstrap": {"n_resamples": 10000, "ci": 0.95, "method": "BCa", "seed": 42},
        "mcnemar":   {"method": "exact binomial (two-sided)"},
        "configs": {cfg: {"block": blocks[cfg],
                          "vs_full": pairwise.get(cfg, None)}
                    for cfg in ABLATION_CONFIGS},
        "main_rerun": main_block,
    }
    (ABL_ROOT / "phase5_stats.json").write_text(
        json.dumps(out_json, indent=2), encoding="utf-8")
    (MAIN_DIR / "phase5_stats.json").write_text(
        json.dumps({"schema_version": 1,
                    "source": str((MAIN_DIR / "results_sota_eval_431.json").relative_to(REPO_ROOT)),
                    "bootstrap": out_json["bootstrap"],
                    "block": main_block},
                   indent=2), encoding="utf-8")
    print(f"\n[OK] Wrote {ABL_ROOT / 'phase5_stats.json'}")
    print(f"[OK] Wrote {MAIN_DIR / 'phase5_stats.json'}")

    # --- 6. Write paper-ready MD table ---
    lines = []
    lines.append("# Phase 5 — Ablation Table 6 (paper-ready, matched eval + stats)")
    lines.append("")
    lines.append(f"_Generated by `benchmark/scripts/eval/phase5_stats.py`. "
                 f"BCa bootstrap CIs (10k resamples, seed=42). "
                 f"McNemar exact binomial p-values, paired by case_id vs Full Hybrid baseline. "
                 f"Cohen's h is the arcsine effect size.")
    lines.append("")
    lines.append("## Full per-task table (Annotation, RCA, Overall)")
    lines.append("")
    lines.append("| Configuration | Task | N | Acc | 95% BCa CI | Δ vs Full | McNemar p | Cohen h |")
    lines.append("|---|---|---:|---:|---|---:|---:|---:|")
    for cfg in ABLATION_CONFIGS:
        label = ABLATION_DESCRIPTIONS[cfg]
        for task in ("annotation", "rca", "overall"):
            t = blocks[cfg]["tasks"][task]
            if cfg == "full":
                d_str, p_str, h_str = "—", "—", "—"
            else:
                pw = pairwise[cfg][task]
                d_str = f"{pw['delta_pp']:+.1f}pp"
                p_str = fmt_p(pw["p_value"]).strip()
                h_str = fmt_h(pw["cohens_h"]).strip()
            row_label = label if task == "annotation" else ""
            lines.append(f"| {row_label} | {task} | {t['n']} | {100*t['accuracy']:.1f}% "
                         f"({t['correct']}/{t['n']}) | [{100*t['ci_low']:.1f}, {100*t['ci_high']:.1f}] | "
                         f"{d_str} | {p_str} | {h_str} |")
    lines.append("")
    lines.append("## Compact Overall-only table (for paper Table 6 if space-constrained)")
    lines.append("")
    lines.append("| Configuration | Overall Acc | 95% BCa CI | Δ vs Full | McNemar p | Cohen h |")
    lines.append("|---|---:|---|---:|---:|---:|")
    for cfg in ABLATION_CONFIGS:
        t = blocks[cfg]["tasks"]["overall"]
        if cfg == "full":
            d_str, p_str, h_str = "—", "—", "—"
        else:
            pw = pairwise[cfg]["overall"]
            d_str = f"{pw['delta_pp']:+.1f}pp"
            p_str = fmt_p(pw["p_value"]).strip()
            h_str = fmt_h(pw["cohens_h"]).strip()
        lines.append(f"| {ABLATION_DESCRIPTIONS[cfg]} | {100*t['accuracy']:.1f}% "
                     f"({t['correct']}/{t['n']}) | [{100*t['ci_low']:.1f}, {100*t['ci_high']:.1f}] | "
                     f"{d_str} | {p_str} | {h_str} |")
    lines.append("")
    lines.append("## Cohen's h interpretation key")
    lines.append("- |h| < 0.2 → negligible effect")
    lines.append("- 0.2 ≤ |h| < 0.5 → small")
    lines.append("- 0.5 ≤ |h| < 0.8 → medium")
    lines.append("- |h| ≥ 0.8 → large")
    lines.append("")
    lines.append("## Main re-run (standalone system, matched eval)")
    lines.append("")
    lines.append("| Task | N | Acc | 95% BCa CI |")
    lines.append("|---|---:|---:|---|")
    for task in ("annotation", "rca", "overall"):
        t = main_block["tasks"][task]
        lines.append(f"| {task} | {t['n']} | {100*t['accuracy']:.1f}% "
                     f"({t['correct']}/{t['n']}) | "
                     f"[{100*t['ci_low']:.1f}, {100*t['ci_high']:.1f}] |")
    lines.append("")
    lines.append("## Notes")
    lines.append("- Ablation Full's matched RCA = 83.8% (119/142) here; main re-run's matched RCA = 80.3% (114/142) — 5-case temp=0 nondeterminism between runs. Both are within run-to-run noise; cite consistently and disclose the variance in a footnote.")
    lines.append("- 71 RCA cases excluded uniformly from all configs (39 Chinese + 32 MC bare-letter). See `../METHODOLOGY.md` §2.")
    lines.append("- All pairwise McNemar tests use the SAME 360-case evaluable set per config (218 ann + 142 rca).")

    md_path = ABL_ROOT / "phase5_stats.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] Wrote {md_path}")


if __name__ == "__main__":
    main()
