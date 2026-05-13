#!/usr/bin/env python3
"""scripts/compare_stacks.py — side-by-side comparison of two benchmark runs.

For the dual-stack smoke (Phase 4.0e): Stack A (Ollama Q4_K_M) vs Stack B (vLLM FP8/AWQ).
Reads two run directories' results.jsonl and emits markdown delta + go/no-go gate decision.

Gate criteria (per REVIEWER_RESPONSE.md §15):
  1. Accuracy delta < 2pp between stacks → proceed
  2. P95 speedup (A.latency / B.latency) ≥ 1.5× → C5 reframe holds

Usage:
    python scripts/compare_stacks.py --a runs/<stack_A_dir> --b runs/<stack_B_dir>
    python scripts/compare_stacks.py --a A.jsonl --b B.jsonl  # direct file mode
"""

from __future__ import annotations
import argparse
import json
import statistics
from pathlib import Path
from typing import Iterable


def _load(path: Path) -> list[dict]:
    if path.is_dir():
        for name in ("results.jsonl", "results.json"):
            candidate = path / name
            if candidate.exists():
                path = candidate
                break
        else:
            raise SystemExit(f"results not found in {path} (tried results.jsonl, results.json)")
    if not path.exists():
        raise SystemExit(f"results not found: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _p95(lats: list[float]) -> float:
    """Numpy-style linear interpolation P95 — matches test_5plus5.py benchmark output."""
    if not lats:
        return 0.0
    s = sorted(lats)
    n = len(s)
    if n == 1:
        return s[0]
    pos = 0.95 * (n - 1)
    low, high = int(pos), min(int(pos) + 1, n - 1)
    return s[low] + (pos - low) * (s[high] - s[low])


def _stats(results: list[dict]) -> dict:
    by_task: dict[str, list[dict]] = {"annotation": [], "rca": []}
    for r in results:
        t = r.get("task_type", "?")
        if t in by_task:
            by_task[t].append(r)
    out: dict = {"total": len(results), "by_task": {}}
    for task, rows in by_task.items():
        if not rows:
            continue
        correct = sum(1 for r in rows if r.get("correct"))
        lats = [r.get("inference_latency_ms", 0) or 0 for r in rows]
        out["by_task"][task] = {
            "n": len(rows),
            "correct": correct,
            "accuracy": correct / len(rows),
            "lat_avg_ms": statistics.mean(lats),
            "lat_p95_ms": _p95(lats),
            "lat_max_ms": max(lats, default=0),
        }
    # Overall
    correct = sum(1 for r in results if r.get("correct"))
    lats = [r.get("inference_latency_ms", 0) or 0 for r in results]
    out["overall"] = {
        "accuracy": correct / max(1, len(results)),
        "lat_avg_ms": statistics.mean(lats) if lats else 0,
        "lat_p95_ms": _p95(lats),
    }
    return out


def _fmt_ms(ms: float) -> str:
    return f"{ms/1000:.2f}s" if ms >= 1000 else f"{ms:.0f}ms"


def render(stack_a: dict, stack_b: dict, a_name: str, b_name: str) -> str:
    L: list[str] = []
    L.append(f"# Stack comparison — {a_name} vs {b_name}\n")
    L.append("## Per-task accuracy + latency\n")
    L.append("| Task | Stack | N | Correct | Accuracy | Lat avg | Lat P95 | Lat max |")
    L.append("|------|-------|---|---------|----------|---------|---------|---------|")
    for task in ("annotation", "rca"):
        for label, stats in (("A", stack_a), ("B", stack_b)):
            ts = stats["by_task"].get(task)
            if not ts:
                continue
            L.append(
                f"| {task} | {label} | {ts['n']} | {ts['correct']} | {ts['accuracy']*100:.1f}% | "
                f"{_fmt_ms(ts['lat_avg_ms'])} | {_fmt_ms(ts['lat_p95_ms'])} | {_fmt_ms(ts['lat_max_ms'])} |"
            )

    L.append("\n## Overall\n")
    L.append("| Stack | Accuracy | Lat avg | Lat P95 |")
    L.append("|-------|----------|---------|---------|")
    for label, stats in (("A " + a_name, stack_a), ("B " + b_name, stack_b)):
        ov = stats["overall"]
        L.append(f"| {label} | {ov['accuracy']*100:.1f}% | {_fmt_ms(ov['lat_avg_ms'])} | {_fmt_ms(ov['lat_p95_ms'])} |")

    # Gate decisions
    L.append("\n## Gate decisions (per REVIEWER_RESPONSE.md §15)\n")
    acc_a = stack_a["overall"]["accuracy"]
    acc_b = stack_b["overall"]["accuracy"]
    acc_delta_pp = abs(acc_a - acc_b) * 100
    p95_a = stack_a["overall"]["lat_p95_ms"]
    p95_b = stack_b["overall"]["lat_p95_ms"]
    speedup = p95_a / p95_b if p95_b > 0 else float("inf")

    gate1 = "✅ PASS" if acc_delta_pp < 2.0 else "❌ FAIL"
    L.append(f"- **Gate 1 — Accuracy delta < 2pp**: |{acc_a*100:.1f}% − {acc_b*100:.1f}%| = {acc_delta_pp:.2f}pp → {gate1}")

    gate2 = "✅ PASS" if speedup >= 1.5 else "❌ FAIL"
    L.append(f"- **Gate 2 — P95 speedup ≥ 1.5×**: {_fmt_ms(p95_a)} / {_fmt_ms(p95_b)} = {speedup:.2f}× → {gate2}")

    if gate1 == "✅ PASS" and gate2 == "✅ PASS":
        L.append("\n**Decision**: ✅ Proceed with full Phase 4 on both stacks.")
    elif gate1 == "❌ FAIL":
        L.append("\n**Decision**: ❌ Investigate accuracy delta before full runs. Likely a setup bug.")
    else:
        L.append("\n**Decision**: ⚠️ C5 latency reframe is weakened. Revisit before committing.")

    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--a", required=True, type=Path, help="Stack A run dir or results.jsonl")
    ap.add_argument("--b", required=True, type=Path, help="Stack B run dir or results.jsonl")
    ap.add_argument("--a-name", default="Stack A (Ollama Q4_K_M)")
    ap.add_argument("--b-name", default="Stack B (vLLM FP8/AWQ)")
    ap.add_argument("--out", type=Path, help="Output markdown path (default: stdout)")
    args = ap.parse_args()

    a = _stats(_load(args.a))
    b = _stats(_load(args.b))
    md = render(a, b, args.a_name, args.b_name)

    if args.out:
        args.out.write_text(md, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
