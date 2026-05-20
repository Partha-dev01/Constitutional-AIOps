#!/usr/bin/env python3
"""Verify the matched-eval numbers in CURRENT_RUNS.md / project_aiops_next.md
by recomputing counts directly from the source JSON files.

Sanity check — no assumptions, recompute from raw fields.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "final"


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def tally(records, task_type):
    """Count {correct, evaluable, total} for a task_type, where
    'evaluable' means correct flag is not None (i.e. not excluded)."""
    total = 0
    evaluable = 0
    correct = 0
    for r in records:
        if r.get("task_type") != task_type:
            continue
        total += 1
        c = r.get("correct")
        if c is None:
            continue  # excluded case
        evaluable += 1
        if c:
            correct += 1
    return correct, evaluable, total


def pct(num, den):
    return 100.0 * num / den if den else 0.0


def main():
    print("=" * 90)
    print("AUTHORITATIVE NUMBERS — VERIFICATION (computed from source JSONs)")
    print("=" * 90)

    # 1. Main re-run, both eval methods
    print("\n## 1. MAIN RE-RUN — FINAL/main_benchmark/")
    print("-" * 90)
    for tag, fname in [
        ("rich eval (runner.py)", "results.json"),
        ("matched eval (SOTA)", "results_sota_eval_431.json"),
    ]:
        p = ROOT / "main_benchmark" / fname
        if not p.exists():
            print(f"  MISSING: {p}")
            continue
        d = load(p)
        a_ok, a_ev, a_tot = tally(d, "annotation")
        r_ok, r_ev, r_tot = tally(d, "rca")
        ov_ok = a_ok + r_ok
        ov_ev = a_ev + r_ev
        print(f"  [{tag}]")
        print(f"    Annotation: {a_ok}/{a_ev} = {pct(a_ok, a_ev):.1f}% (total {a_tot})")
        print(f"    RCA       : {r_ok}/{r_ev} = {pct(r_ok, r_ev):.1f}% (total {r_tot})")
        print(f"    Overall   : {ov_ok}/{ov_ev} = {pct(ov_ok, ov_ev):.1f}% (total {a_tot+r_tot})")

    # 2. All 8 ablation configs under matched eval
    print("\n## 2. ABLATION — FINAL/ablation_v4/ablation_*/results_sota_eval_431.json")
    print("-" * 90)
    print(f"  {'Config':<22} {'Ann(ev)':<14} {'Ann%':<7} {'RCA(ev)':<14} {'RCA%':<7} {'Ovl(ev)':<14} {'Ovl%':<7}")
    print(f"  {'-'*22} {'-'*14} {'-'*7} {'-'*14} {'-'*7} {'-'*14} {'-'*7}")
    configs = ["full", "single_4b", "single_14b", "no_structured",
               "no_system_prompt", "with_graph", "no_constitutional", "with_orchestrator"]
    matched_data = {}
    for cfg in configs:
        p = ROOT / "ablation_v4" / f"ablation_{cfg}" / "results_sota_eval_431.json"
        if not p.exists():
            print(f"  MISSING: {p}")
            continue
        d = load(p)
        a_ok, a_ev, _ = tally(d, "annotation")
        r_ok, r_ev, _ = tally(d, "rca")
        ov_ok = a_ok + r_ok
        ov_ev = a_ev + r_ev
        matched_data[cfg] = (a_ok, a_ev, r_ok, r_ev, ov_ok, ov_ev)
        print(f"  {cfg:<22} {f'{a_ok}/{a_ev}':<14} {pct(a_ok,a_ev):<7.1f} "
              f"{f'{r_ok}/{r_ev}':<14} {pct(r_ok,r_ev):<7.1f} "
              f"{f'{ov_ok}/{ov_ev}':<14} {pct(ov_ok,ov_ev):<7.1f}")

    # 3. Cross-check: deltas vs full
    print("\n## 3. ABLATION — Δ overall vs Full (matched eval)")
    print("-" * 90)
    if "full" in matched_data:
        full_ovl_pct = pct(matched_data["full"][4], matched_data["full"][5])
        for cfg in configs:
            if cfg not in matched_data:
                continue
            ov_pct = pct(matched_data[cfg][4], matched_data[cfg][5])
            delta = ov_pct - full_ovl_pct
            print(f"  {cfg:<22} {ov_pct:6.1f}%  Δ = {delta:+.1f}pp")

    # 4. SOTA baselines for cross-check
    print("\n## 4. SOTA baselines (jsonl, matched eval)")
    print("-" * 90)
    for tag, fname in [
        ("Llama 3.3-70B", "llama_3_3_70b.jsonl"),
        ("DeepSeek V3.2", "deepseek_v3.jsonl"),
    ]:
        p = ROOT / "sota_baselines" / fname
        if not p.exists():
            print(f"  {tag}: MISSING {p}")
            continue
        records = []
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        a_ok, a_ev, _ = tally(records, "annotation")
        r_ok, r_ev, _ = tally(records, "rca")
        ov_ok = a_ok + r_ok
        ov_ev = a_ev + r_ev
        print(f"  {tag:<20}: Ann {a_ok}/{a_ev} = {pct(a_ok, a_ev):.1f}%, "
              f"RCA {r_ok}/{r_ev} = {pct(r_ok, r_ev):.1f}%, "
              f"Overall {ov_ok}/{ov_ev} = {pct(ov_ok, ov_ev):.1f}%   (n={len(records)})")


if __name__ == "__main__":
    main()
