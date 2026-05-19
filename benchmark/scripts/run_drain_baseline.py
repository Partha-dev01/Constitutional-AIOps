#!/usr/bin/env python3
"""benchmark/scripts/run_drain_baseline.py — Phase 4.7 Drain log-parser baseline.

Drain (LogPAI drain3) is a traditional template-based log parser with NO RCA capability.
For annotation tasks: uses Drain template frequency as anomaly signal.
For RCA tasks: skipped (outputs N/A).

Anomaly detection heuristic:
  - Parse all log lines from a case into templates via Drain TemplateMiner.
  - A case is anomalous if ANY log line matches a "rare" template (cluster size < threshold)
    OR contains explicit error/failure keywords that the template preserves.
  - Compared against expected anomaly_detected field.

Usage:
    python benchmark/scripts/run_drain_baseline.py \\
        --dataset benchmark/datasets/processed/benchmark_400_seed42.json \\
        --out benchmark/results_aws/sota_drain/results.jsonl

Paper reference: Table 7, "Drain" row (annotation only; RCA = N/A).
Cite: zhu2023loghub
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

try:
    from drain3 import TemplateMiner
    from drain3.template_miner_config import TemplateMinerConfig
except ImportError:
    print("ERROR: drain3 not installed. Run: pip install drain3", file=sys.stderr)
    sys.exit(1)

# Keywords that Drain templates preserve even in rare clusters (strong anomaly signal)
_ERROR_KEYWORDS = re.compile(
    r'\b(error|fail(?:ed|ure)?|exception|critical|fatal|panic|crash|'
    r'refused|denied|invalid|unauthorized|abort|corrupt|timeout|'
    r'not found|no such|broken|unavailable)\b',
    re.IGNORECASE,
)

# Drain cluster size below which a template is considered "rare" (anomaly signal)
_RARE_THRESHOLD = 3


def _extract_log_lines(case: dict) -> list[str]:
    """Pull raw log line strings from a benchmark case regardless of format."""
    lines: list[str] = []
    incident = case.get("incident", {})
    logs = incident.get("logs", [])
    if isinstance(logs, list):
        for entry in logs:
            if isinstance(entry, str):
                lines.append(entry)
            elif isinstance(entry, dict):
                # Common fields: message, log_message, content, raw
                for field in ("message", "log_message", "content", "raw", "text"):
                    if field in entry:
                        lines.append(str(entry[field]))
                        break
    # Annotation cases may use input.log_entry or similar
    inp = case.get("input", {})
    for field in ("log_entry", "log_text", "message", "content"):
        if field in inp:
            lines.append(str(inp[field]))
    return [ln for ln in lines if ln.strip()]


def _drain_predict_anomaly(log_lines: list[str]) -> bool:
    """Return True if Drain's template analysis signals an anomaly."""
    if not log_lines:
        return False

    cfg = TemplateMinerConfig()
    # Tighter similarity threshold so keyword-bearing lines form their own clusters
    cfg.drain_sim_th = 0.4
    cfg.drain_depth = 4
    miner = TemplateMiner(config=cfg)

    clusters_seen: list = []
    for line in log_lines:
        result = miner.add_log_message(line.strip())
        if result:
            clusters_seen.append(result)

    # Heuristic 1: any template contains explicit error keyword → anomaly
    for cluster in miner.drain.id_to_cluster.values():
        template = " ".join(cluster.log_template_tokens)
        if _ERROR_KEYWORDS.search(template):
            return True

    # Heuristic 2: any rare cluster (few supporting log lines) → likely anomaly
    for cluster in miner.drain.id_to_cluster.values():
        if cluster.size < _RARE_THRESHOLD:
            template = " ".join(cluster.log_template_tokens)
            # Only flag rare templates that look structural (not all-wildcard)
            non_wildcard = [t for t in cluster.log_template_tokens if t != "<*>"]
            if len(non_wildcard) >= 2:
                return True

    return False


def _evaluate_case(case: dict) -> dict:
    task_type = case.get("task_type", "annotation")

    if task_type == "rca":
        # Drain has no RCA capability
        return {
            "test_id": case.get("id", case.get("test_id", "unknown")),
            "task_type": "rca",
            "source": case.get("source", "unknown"),
            "model": "drain3",
            "correct": None,   # N/A
            "predicted": "N/A",
            "expected": case.get("expected_root_cause", ""),
            "drain_rca": False,  # not capable
        }

    # Annotation case
    log_lines = _extract_log_lines(case)
    predicted_anomaly = _drain_predict_anomaly(log_lines)

    expected = case.get("expected", {})
    expected_anomaly = expected.get("anomaly_detected", None)
    if expected_anomaly is None:
        # Try alternative field names
        expected_anomaly = expected.get("is_anomaly", expected.get("anomalous", None))

    correct = None
    if expected_anomaly is not None:
        correct = bool(predicted_anomaly) == bool(expected_anomaly)

    return {
        "test_id": case.get("id", case.get("test_id", "unknown")),
        "task_type": "annotation",
        "source": case.get("source", "unknown"),
        "model": "drain3",
        "correct": correct,
        "predicted_anomaly": predicted_anomaly,
        "expected_anomaly": expected_anomaly,
        "log_lines_parsed": len(log_lines),
    }


def main():
    parser = argparse.ArgumentParser(description="Run Drain log-parser baseline")
    parser.add_argument("--dataset", required=True, help="Path to benchmark JSON")
    parser.add_argument("--out", required=True, help="Output JSONL path")
    parser.add_argument("--task", choices=["annotation", "rca", "all"], default="annotation",
                        help="Task filter (default: annotation only)")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(dataset_path, encoding="utf-8") as f:
        data = json.load(f)
    cases = data if isinstance(data, list) else data.get("test_cases", [])

    if args.task != "all":
        cases = [c for c in cases if c.get("task_type") == args.task]

    print(f"Drain baseline: {len(cases)} cases from {dataset_path.name}")

    completed_ids: set[str] = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    completed_ids.add(rec["test_id"])
                except Exception:
                    pass
        print(f"Resuming: {len(completed_ids)} already done")

    ann_total = ann_correct = 0
    with open(out_path, "a", encoding="utf-8") as out_f:
        for i, case in enumerate(cases):
            case_id = case.get("id", case.get("test_id", f"case_{i}"))
            if case_id in completed_ids:
                continue

            result = _evaluate_case(case)
            out_f.write(json.dumps(result) + "\n")
            out_f.flush()

            if result["task_type"] == "annotation" and result["correct"] is not None:
                ann_total += 1
                if result["correct"]:
                    ann_correct += 1

            if (i + 1) % 50 == 0:
                acc = ann_correct / ann_total * 100 if ann_total else 0
                print(f"  [{i+1}/{len(cases)}] Ann accuracy so far: {acc:.1f}% ({ann_correct}/{ann_total})")

    acc = ann_correct / ann_total * 100 if ann_total else 0
    print(f"\nDrain baseline complete.")
    print(f"Annotation: {ann_correct}/{ann_total} = {acc:.1f}%")
    print(f"RCA: N/A (Drain has no RCA capability)")
    print(f"Results: {out_path}")

    # Write summary
    summary = {
        "model": "drain3",
        "dataset": str(dataset_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "annotation_accuracy": round(acc / 100, 4),
        "annotation_correct": ann_correct,
        "annotation_total": ann_total,
        "rca_accuracy": None,
        "note": "Drain is a template-based log parser. No RCA capability.",
    }
    summary_path = out_path.parent / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
