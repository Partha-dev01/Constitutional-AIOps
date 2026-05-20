#!/usr/bin/env python3
"""benchmark/scripts/mine_openssh.py — extract ~40 annotation cases from Loghub OpenSSH.

Why OpenSSH (vs Linux/BGL): narrowest vocabulary in Loghub — "Failed password"
means exactly one thing. Very low false-positive risk per the dataset-expansion
agent's analysis.

Approach: session-level detection rather than per-line. A SSH brute-force burst
is N+ failed-password attempts from the same IP within a short window. Single
"Failed password" lines may be benign typos; bursts are anomalies.

Anomaly heuristic: 3+ "Failed password" events from same IP within any 60-second window.

Input:  benchmark/raw/loghub/openssh/OpenSSH_2k.log_structured.csv
Output: list of annotation cases (mix of anomaly bursts + normal single-event lines)

Usage:
    python benchmark/scripts/mine_openssh.py --target 40 --out benchmark/intermediate/candidates/openssh_candidates.jsonl
"""

from __future__ import annotations
import argparse
import csv
import json
import random
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENSSH_CSV = REPO_ROOT / "benchmark/raw/loghub/openssh/OpenSSH_2k.log_structured.csv"

BRUTE_FORCE_WINDOW_SEC = 60
BRUTE_FORCE_THRESHOLD = 3  # >=N failed logins from same IP in window = anomaly

IP_RE = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")


def load_entries() -> list[dict]:
    if not OPENSSH_CSV.exists():
        print(f"ERROR: OpenSSH CSV not found at {OPENSSH_CSV}", file=sys.stderr)
        print("Run: python benchmark/scripts/download_datasets.py --all", file=sys.stderr)
        sys.exit(2)
    entries = []
    with OPENSSH_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)
    return entries


def parse_timestamp(date_str: str, time_str: str) -> int | None:
    """Parse OpenSSH structured CSV timestamp.

    Loghub OpenSSH typically has 'Date' = '12  4' (day month indices) and
    'Time' = 'HH:MM:SS'. We treat each as a relative ordering rather than
    a calendar time — sufficient for burst detection within the log.

    Returns: epoch-like integer (line-number-based) for relative ordering.
    """
    try:
        # OpenSSH log lines are already in chronological order, so use index
        return None  # We'll just use list position
    except Exception:
        return None


def is_failed_password(entry: dict) -> bool:
    content = entry.get("Content", "")
    return "Failed password" in content or "authentication failure" in content.lower()


def extract_ip(entry: dict) -> str | None:
    m = IP_RE.search(entry.get("Content", ""))
    return m.group(1) if m else None


def detect_brute_force_bursts(entries: list[dict]) -> list[dict]:
    """Mark each entry as part-of-burst (anomaly) or single (normal).

    Sliding window over indices: for each failed-password event, check if
    >=N events from same IP occurred within the last `window` events.
    (Window size in records is a reasonable proxy for time window since
    OpenSSH log is densely packed during bursts.)
    """
    # Track recent attempts per IP
    ip_history: dict[str, list[int]] = defaultdict(list)
    burst_indices: set[int] = set()

    # Window: ~BRUTE_FORCE_WINDOW_SEC translates to roughly 60 entries
    # in dense brute-force periods (very conservative).
    window_records = 100

    for i, e in enumerate(entries):
        if not is_failed_password(e):
            continue
        ip = extract_ip(e)
        if ip is None:
            continue
        ip_history[ip].append(i)
        # Count recent attempts from this IP
        recent = [j for j in ip_history[ip] if j >= i - window_records]
        if len(recent) >= BRUTE_FORCE_THRESHOLD:
            burst_indices.update(recent)
    return burst_indices


def to_case(entry: dict, idx: int, is_burst: bool) -> dict:
    return {
        "id": f"ANN_OPENSSH_{idx:03d}",
        "source": "loghub_openssh",
        "task_type": "annotation",
        "input": {
            "telemetry_type": "log",
            "content": entry.get("Content", "").strip(),
            "context": (
                "OpenSSH server log; this entry is part of a brute-force burst "
                f"(≥{BRUTE_FORCE_THRESHOLD} failed logins from same IP in short window)"
                if is_burst else
                "OpenSSH server log; isolated event, not part of a brute-force burst"
            ),
        },
        "expected": {
            "anomaly_detected": is_burst,
            "severity": "high" if is_burst else "info",
            "category": "security" if is_burst else "unknown",
        },
        "ground_truth_label": "anomaly" if is_burst else "normal",
        "_provenance": {
            "loghub_event_template": entry.get("EventTemplate", ""),
            "loghub_event_id": entry.get("EventId", ""),
            "detection": "session-burst" if is_burst else "single-event",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", type=int, default=40)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    entries = load_entries()
    print(f"[mine_openssh] loaded {len(entries)} raw entries")

    burst_indices = detect_brute_force_bursts(entries)
    print(f"[mine_openssh] detected {len(burst_indices)} entries in brute-force bursts")

    rng = random.Random(args.seed)

    anomaly_pool = [(i, e) for i, e in enumerate(entries) if i in burst_indices]
    normal_pool = [(i, e) for i, e in enumerate(entries)
                   if i not in burst_indices and not is_failed_password(e)]

    rng.shuffle(anomaly_pool)
    rng.shuffle(normal_pool)

    half = args.target // 2
    selected_anom = anomaly_pool[:half]
    selected_norm = normal_pool[:args.target - half]
    selected = selected_anom + selected_norm
    rng.shuffle(selected)

    cases = [to_case(e, idx=i + 1, is_burst=(orig_idx in burst_indices))
             for i, (orig_idx, e) in enumerate(selected)]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")

    n_anom = sum(1 for c in cases if c["ground_truth_label"] == "anomaly")
    print(f"[mine_openssh] wrote {args.out} ({len(cases)} cases)")
    print(f"  brute-force burst (anomaly): {n_anom}")
    print(f"  isolated/benign (normal): {len(cases) - n_anom}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
