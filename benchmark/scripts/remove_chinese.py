#!/usr/bin/env python3
"""
Remove Chinese OpsEval test cases from benchmark_150_seed42.json
and replace with English cases from rca_clean.json pool.

Maintains 150 total cases (100 annotation + 50 RCA, all English).
Uses seed=42 for reproducible replacement selection.
"""

import json
import re
import random
from pathlib import Path
from datetime import datetime

DATASET_DIR = Path(__file__).parent.parent / "datasets" / "processed"


def has_chinese(text: str) -> bool:
    """Check if text contains Chinese characters (CJK Unified Ideographs)."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def main():
    # Load benchmark_150
    bench_path = DATASET_DIR / "benchmark_150_seed42.json"
    with open(bench_path, "r", encoding="utf-8") as f:
        bench_data = json.load(f)

    # Load rca_clean for replacement pool
    rca_path = DATASET_DIR / "rca_clean.json"
    with open(rca_path, "r", encoding="utf-8") as f:
        rca_data = json.load(f)

    all_tests = bench_data["test_cases"]
    annotation_tests = [t for t in all_tests if t.get("task_type") == "annotation"]
    rca_tests = [t for t in all_tests if t.get("task_type") == "rca"]

    print(f"Original: {len(annotation_tests)} annotation + {len(rca_tests)} RCA = {len(all_tests)} total")

    # Find Chinese RCA cases
    chinese_ids = []
    english_rca = []
    for t in rca_tests:
        title = t.get("incident", {}).get("title", "")
        question = t.get("incident", {}).get("question", "")
        expected = t.get("expected_root_cause", "")
        # Check title, question, AND expected_root_cause for Chinese
        if has_chinese(title) or has_chinese(question) or has_chinese(expected):
            chinese_ids.append(t["id"])
        else:
            english_rca.append(t)

    print(f"Chinese RCA cases found: {len(chinese_ids)}")
    print(f"Chinese IDs: {chinese_ids}")
    print(f"English RCA remaining: {len(english_rca)}")

    # Get IDs already in benchmark
    existing_ids = {t["id"] for t in all_tests}

    # Find replacement candidates from rca_clean (English only, not already in benchmark)
    replacement_pool = []
    for t in rca_data["test_cases"]:
        if t["id"] in existing_ids:
            continue  # Already in benchmark
        title = t.get("incident", {}).get("title", "")
        question = t.get("incident", {}).get("question", "")
        expected = t.get("expected_root_cause", "")
        if has_chinese(title) or has_chinese(question) or has_chinese(expected):
            continue  # Skip Chinese
        replacement_pool.append(t)

    print(f"Replacement pool (English, unused): {len(replacement_pool)} cases")

    # Select replacements with seed=42
    needed = len(chinese_ids)
    random.seed(42)
    replacements = random.sample(replacement_pool, min(needed, len(replacement_pool)))
    print(f"Selected {len(replacements)} replacements")

    # Build new test case list
    new_rca = english_rca + replacements
    new_tests = annotation_tests + new_rca

    print(f"\nNew dataset: {len(annotation_tests)} annotation + {len(new_rca)} RCA = {len(new_tests)} total")

    # Update metadata
    bench_data["test_cases"] = new_tests
    bench_data["total_cases"] = len(new_tests)
    bench_data["description"] = "Sampled benchmark dataset (seed=42) - Chinese cases removed"
    bench_data["chinese_removed"] = {
        "count": len(chinese_ids),
        "ids": chinese_ids,
        "replacements_added": len(replacements),
        "replacement_ids": [r["id"] for r in replacements],
    }
    bench_data["sampling"]["rca_chinese_removed"] = len(chinese_ids)
    bench_data["modified"] = datetime.utcnow().isoformat()

    # Backup original
    backup_path = DATASET_DIR / "benchmark_150_seed42_with_chinese.json"
    with open(bench_path, "r", encoding="utf-8") as f:
        original = f.read()
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(original)
    print(f"\nBackup saved to: {backup_path.name}")

    # Write updated dataset
    with open(bench_path, "w", encoding="utf-8") as f:
        json.dump(bench_data, f, indent=2, ensure_ascii=False)
    print(f"Updated dataset saved to: {bench_path.name}")

    # Verify no Chinese remains
    with open(bench_path, "r", encoding="utf-8") as f:
        content = f.read()
    remaining_chinese = len(re.findall(r'[\u4e00-\u9fff]', content))
    print(f"\nVerification: {remaining_chinese} Chinese characters remaining in dataset")
    if remaining_chinese == 0:
        print("[OK] Dataset is now fully English!")
    else:
        print("[WARNING] Some Chinese characters still remain - check manually")


if __name__ == "__main__":
    main()
