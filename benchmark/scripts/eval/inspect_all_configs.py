#!/usr/bin/env python3
"""Inspect all 8 ablation configs for runner.py-vs-SOTA eval mismatches."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "benchmark/final/ablation_v4"
CONFIGS = [
    "full", "single_4b", "single_14b", "no_structured",
    "no_system_prompt", "with_graph", "no_constitutional", "with_orchestrator",
]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def by_id(records, task_type):
    out = {}
    for r in records:
        if r.get("task_type") != task_type:
            continue
        tid = r.get("test_id") or r.get("case_id")
        if tid:
            out[tid] = r
    return out


def summarize(cfg):
    raw = load(ROOT / f"ablation_{cfg}" / "results.json")
    sota = load(ROOT / f"ablation_{cfg}" / "results_sota_eval_431.json")
    raw_rca = by_id(raw, "rca")
    sota_rca = by_id(sota, "rca")

    # Restrict to evaluable: those where sota's correct is not None
    evaluable = [tid for tid, r in sota_rca.items() if r.get("correct") is not None]

    raw_correct = {tid for tid in evaluable if raw_rca[tid].get("correct")}
    sota_correct = {tid for tid in evaluable if sota_rca[tid].get("correct")}

    runner_says_yes_sota_says_no = raw_correct - sota_correct  # runner FALSE POSITIVES
    sota_says_yes_runner_says_no = sota_correct - raw_correct  # runner FALSE NEGATIVES
    agree_yes = raw_correct & sota_correct
    agree_no = set(evaluable) - raw_correct - sota_correct

    return {
        "cfg": cfg,
        "evaluable": len(evaluable),
        "runner_correct": len(raw_correct),
        "sota_correct": len(sota_correct),
        "runner_FP": len(runner_says_yes_sota_says_no),
        "runner_FN": len(sota_says_yes_runner_says_no),
        "agree_yes": len(agree_yes),
        "agree_no": len(agree_no),
        "runner_pct": 100.0 * len(raw_correct) / len(evaluable),
        "sota_pct": 100.0 * len(sota_correct) / len(evaluable),
        "fp_ids_sample": sorted(runner_says_yes_sota_says_no)[:5],
        "fn_ids_sample": sorted(sota_says_yes_runner_says_no)[:3],
        "raw_rca": raw_rca,
        "sota_rca": sota_rca,
    }


def main():
    rows = []
    samples = {}
    for cfg in CONFIGS:
        s = summarize(cfg)
        rows.append(s)
        samples[cfg] = s

    print(f"{'Config':<22} {'Evalbl':<7} {'runner_OK':<10} {'sota_OK':<8} {'FP':<5} {'FN':<5} {'runner%':<8} {'sota%':<7} {'Delta':<7}")
    print("-" * 100)
    for r in rows:
        delta = r["runner_pct"] - r["sota_pct"]
        print(f"{r['cfg']:<22} {r['evaluable']:<7} {r['runner_correct']:<10} {r['sota_correct']:<8} "
              f"{r['runner_FP']:<5} {r['runner_FN']:<5} {r['runner_pct']:<8.2f} {r['sota_pct']:<7.2f} {delta:+.2f}")

    print("\n\n=== Sample of runner.py FALSE POSITIVES (runner says correct, SOTA strict says wrong) ===")
    for r in rows:
        if r["runner_FP"] == 0:
            continue
        print(f"\n--- {r['cfg']} (FP count: {r['runner_FP']}) ---")
        for tid in r["fp_ids_sample"]:
            raw = r["raw_rca"][tid]
            exp = str(raw.get("expected_output"))[:120]
            act = str(raw.get("actual_output"))[:200]
            print(f"  {tid}  rule_score={raw.get('rule_score')}  term_overlap={raw.get('term_overlap')}  cosine={raw.get('cosine_similarity')}")
            print(f"    expected: {exp}")
            print(f"    actual:   {act}")

    print("\n\n=== Sample of runner.py FALSE NEGATIVES (SOTA says correct, runner says wrong) ===")
    for r in rows:
        if r["runner_FN"] == 0:
            continue
        print(f"\n--- {r['cfg']} (FN count: {r['runner_FN']}) ---")
        for tid in r["fn_ids_sample"]:
            raw = r["raw_rca"][tid]
            exp = str(raw.get("expected_output"))[:120]
            act = str(raw.get("actual_output"))[:200]
            print(f"  {tid}  rule_score={raw.get('rule_score')}  term_overlap={raw.get('term_overlap')}  cosine={raw.get('cosine_similarity')}")
            print(f"    expected: {exp}")
            print(f"    actual:   {act}")


if __name__ == "__main__":
    main()
