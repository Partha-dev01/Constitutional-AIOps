#!/usr/bin/env python3
"""
One-time fix: Add task_type="rca" to orphaned RCA cases in benchmark_150_seed42.json.

Bug: remove_chinese.py added replacement RCA cases from rca_clean.json without
setting the task_type field. The runner filters by task_type, so 17 RCA cases
were silently skipped (100 ann + 33 rca + 17 orphaned = 150).

This script patches the existing dataset in place.
"""

import json
from pathlib import Path

DATASET_DIR = Path(__file__).parent.parent / "datasets" / "processed"


def main():
    bench_path = DATASET_DIR / "benchmark_150_seed42.json"
    with open(bench_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    test_cases = data["test_cases"]

    # Count before fix
    ann_count = sum(1 for t in test_cases if t.get("task_type") == "annotation")
    rca_count = sum(1 for t in test_cases if t.get("task_type") == "rca")
    missing = sum(1 for t in test_cases if "task_type" not in t)

    print(f"Before fix: {ann_count} annotation + {rca_count} rca + {missing} missing = {len(test_cases)} total")

    if missing == 0:
        print("[OK] No orphaned cases found. Dataset is already clean.")
        return

    # Fix: any case with id starting with "RCA_" but missing task_type
    fixed_ids = []
    for t in test_cases:
        if "task_type" not in t and t.get("id", "").startswith("RCA_"):
            t["task_type"] = "rca"
            fixed_ids.append(t["id"])

    # Verify after fix
    ann_after = sum(1 for t in test_cases if t.get("task_type") == "annotation")
    rca_after = sum(1 for t in test_cases if t.get("task_type") == "rca")
    still_missing = sum(1 for t in test_cases if "task_type" not in t)

    print(f"Fixed {len(fixed_ids)} cases: {fixed_ids}")
    print(f"After fix: {ann_after} annotation + {rca_after} rca + {still_missing} missing = {len(test_cases)} total")

    if ann_after == 100 and rca_after == 50 and still_missing == 0:
        print("[OK] Dataset now has 100 annotation + 50 RCA = 150 total")
    else:
        print(f"[WARNING] Unexpected counts - check manually")

    # Save
    with open(bench_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] {bench_path}")


if __name__ == "__main__":
    main()
