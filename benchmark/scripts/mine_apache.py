#!/usr/bin/env python3
"""benchmark/scripts/mine_apache.py — extract ~40 annotation cases from Loghub Apache.

Why Apache (vs Linux/Thunderbird): Apache error log uses unambiguous English
("File does not exist", "client denied by server config", "AH..." codes),
making it a LOW-RISK addition that doesn't repeat the BGL false-positive trap.

Input:  benchmark/datasets/raw/loghub/apache/Apache_2k.log_structured.csv
Output: list of vetted annotation cases ready for benchmark_500 assembly

Approach:
  1. Load 2k structured Apache entries (already template-parsed by Loghub team)
  2. Cluster by EventTemplate (~20 unique templates expected)
  3. Sample representatives: half ERROR-level (anomaly), half NOTICE-level (normal)
  4. Emit candidates with task_type='annotation' + the schema runner.py expects

Per Phase 1.5 hardening, every output case has task_type and proper input shape.

Usage:
    python benchmark/scripts/mine_apache.py --target 40 --out benchmark/v0.11/apache_candidates.jsonl
"""

from __future__ import annotations
import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APACHE_CSV = REPO_ROOT / "benchmark/datasets/raw/loghub/apache/Apache_2k.log_structured.csv"


def load_apache_entries() -> list[dict]:
    """Load all 2k entries from the Loghub-structured Apache CSV."""
    if not APACHE_CSV.exists():
        print(f"ERROR: Apache CSV not found at {APACHE_CSV}", file=sys.stderr)
        print("Run: python benchmark/scripts/download_datasets.py --all", file=sys.stderr)
        sys.exit(2)
    entries = []
    with APACHE_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)
    return entries


def is_anomaly(entry: dict) -> bool:
    """Apache anomaly heuristic: severity ERROR or specific failure templates.

    Apache log levels in Loghub set: notice / error / warn (very few warn).
    Anomaly = error level. NOT all warnings (some are routine).
    """
    level = (entry.get("Level") or "").lower()
    content = (entry.get("Content") or "").lower()
    # Genuine anomaly indicators
    error_signals = [
        "error", "denied", "does not exist", "internal dummy",
        "alert", "emerg", "crit",
    ]
    if level == "error":
        return True
    if any(sig in content for sig in error_signals):
        # Soft-include: explicit error vocabulary even if level=notice
        return True
    return False


def select_balanced(entries: list[dict], target: int, seed: int = 42) -> list[dict]:
    """Stratified selection: balance anomaly/normal AND across templates.

    Picks at most 2 representatives per (template, label) bucket so we get
    template diversity rather than 40 copies of the same error.
    """
    rng = random.Random(seed)
    buckets: dict[tuple[str, bool], list[dict]] = defaultdict(list)
    for e in entries:
        key = (e.get("EventTemplate") or "<no-template>", is_anomaly(e))
        buckets[key].append(e)

    # Sample at most 2 per (template, label)
    pool: list[dict] = []
    for key, group in buckets.items():
        rng.shuffle(group)
        pool.extend(group[:2])

    # Now balance the pool 50/50 anomaly vs normal as much as possible
    anom = [e for e in pool if is_anomaly(e)]
    norm = [e for e in pool if not is_anomaly(e)]
    rng.shuffle(anom)
    rng.shuffle(norm)

    half = target // 2
    selected = anom[:half] + norm[:target - half]
    if len(selected) < target:
        # Top up from whichever pool has more, then from full entries
        rest = [e for e in entries if e not in selected]
        rng.shuffle(rest)
        selected.extend(rest[: target - len(selected)])
    return selected[:target]


def to_case(entry: dict, idx: int) -> dict:
    """Convert a Loghub-structured row to a runner-compatible annotation case."""
    anomaly = is_anomaly(entry)
    return {
        "id": f"ANN_APACHE_{idx:03d}",
        "source": "loghub_apache",
        "task_type": "annotation",
        "input": {
            "telemetry_type": "log",
            "content": entry.get("Content", "").strip(),
            "context": f"Apache HTTP server log entry (level={entry.get('Level','')})",
        },
        "expected": {
            "anomaly_detected": anomaly,
            "severity": "high" if anomaly else "info",
            "category": "error" if anomaly else "unknown",
        },
        "ground_truth_label": "anomaly" if anomaly else "normal",
        # Provenance for label vetting
        "_provenance": {
            "loghub_event_template": entry.get("EventTemplate", ""),
            "loghub_event_id": entry.get("EventId", ""),
            "loghub_level": entry.get("Level", ""),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", type=int, default=40, help="Target case count")
    ap.add_argument("--out", type=Path, required=True, help="Output JSONL path")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    entries = load_apache_entries()
    print(f"[mine_apache] loaded {len(entries)} raw entries")

    selected = select_balanced(entries, args.target, seed=args.seed)
    cases = [to_case(e, i + 1) for i, e in enumerate(selected)]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")

    n_anom = sum(1 for c in cases if c["ground_truth_label"] == "anomaly")
    print(f"[mine_apache] wrote {args.out} ({len(cases)} cases)")
    print(f"  anomaly: {n_anom}, normal: {len(cases) - n_anom}")
    print(f"  unique templates: {len({c['_provenance']['loghub_event_template'] for c in cases})}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
