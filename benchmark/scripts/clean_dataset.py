#!/usr/bin/env python3
"""
Dataset Cleanup and Sampling Script for Constitutional AIOps Benchmark

This script:
1. Removes 62 bogus annotation entries (cryptic BGL logs)
2. Removes 3 mislabeled RCA entries
3. Creates clean dataset files
4. Samples 150 cases with seed=42 for reproducibility

Usage:
    python benchmark/scripts/clean_dataset.py
"""

import json
import random
from pathlib import Path
from datetime import datetime

# IDs to REMOVE from annotation dataset (62 cryptic BGL entries)
REMOVE_ANNOTATION_IDS = {
    "ANN_101", "ANN_102", "ANN_103", "ANN_104", "ANN_106", "ANN_108", "ANN_109", "ANN_110", "ANN_111", "ANN_112",
    "ANN_113", "ANN_115", "ANN_116", "ANN_117", "ANN_120", "ANN_124", "ANN_125", "ANN_126", "ANN_127", "ANN_128",
    "ANN_131", "ANN_132", "ANN_133", "ANN_134", "ANN_136", "ANN_137", "ANN_138", "ANN_139", "ANN_140", "ANN_143",
    "ANN_144", "ANN_145", "ANN_147", "ANN_148", "ANN_150", "ANN_152", "ANN_157", "ANN_158", "ANN_159", "ANN_160",
    "ANN_161", "ANN_162", "ANN_163", "ANN_165", "ANN_172", "ANN_175", "ANN_178", "ANN_180", "ANN_181", "ANN_183",
    "ANN_185", "ANN_186", "ANN_187", "ANN_188", "ANN_190", "ANN_191", "ANN_193", "ANN_195", "ANN_196", "ANN_197",
    "ANN_199", "ANN_200"
}

# IDs to REMOVE from RCA dataset (3 mislabeled entries)
REMOVE_RCA_IDS = {
    "RCA_118",  # session-db_config_error: Normal Redis startup logs
    "RCA_165",  # productcatalogservice_config_error: Normal service startup
    "RCA_182"   # grafana_dependency_failure: Normal initialization logs
}

# Random seed for reproducible sampling
RANDOM_SEED = 42

# Sample sizes
ANNOTATION_SAMPLE_SIZE = 100
RCA_SAMPLE_SIZE = 50


def load_json(filepath: Path) -> dict:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: dict, filepath: Path):
    """Save JSON file with proper formatting."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {filepath}")


def clean_annotation_dataset(input_path: Path, output_path: Path) -> list:
    """
    Clean annotation dataset by removing bogus entries.

    Returns list of clean test cases.
    """
    data = load_json(input_path)

    original_count = len(data["test_cases"])

    # Filter out bogus entries
    clean_cases = [
        case for case in data["test_cases"]
        if case["id"] not in REMOVE_ANNOTATION_IDS
    ]

    removed_count = original_count - len(clean_cases)

    # Create clean dataset
    clean_data = {
        "version": "2.0-clean",
        "created": datetime.now().isoformat(),
        "source": data["source"],
        "description": f"Cleaned annotation dataset - removed {removed_count} bogus BGL entries",
        "original_total": original_count,
        "removed_ids": list(REMOVE_ANNOTATION_IDS),
        "total_cases": len(clean_cases),
        "distribution": {
            "hdfs": sum(1 for c in clean_cases if c["source"] == "loghub_hdfs"),
            "bgl": sum(1 for c in clean_cases if c["source"] == "loghub_bgl"),
            "normal": sum(1 for c in clean_cases if c["ground_truth_label"] == "normal"),
            "anomaly": sum(1 for c in clean_cases if c["ground_truth_label"] != "normal")
        },
        "test_cases": clean_cases
    }

    save_json(clean_data, output_path)

    print(f"Annotation: {original_count} -> {len(clean_cases)} (removed {removed_count})")
    print(f"  HDFS: {clean_data['distribution']['hdfs']}")
    print(f"  BGL: {clean_data['distribution']['bgl']}")
    print(f"  Normal: {clean_data['distribution']['normal']}")
    print(f"  Anomaly: {clean_data['distribution']['anomaly']}")

    return clean_cases


def clean_rca_dataset(input_path: Path, output_path: Path) -> list:
    """
    Clean RCA dataset by removing mislabeled entries.

    Returns list of clean test cases.
    """
    data = load_json(input_path)

    original_count = len(data["test_cases"])

    # Filter out mislabeled entries
    clean_cases = [
        case for case in data["test_cases"]
        if case["id"] not in REMOVE_RCA_IDS
    ]

    removed_count = original_count - len(clean_cases)

    # Count sources
    opseval_count = sum(1 for c in clean_cases if "opseval" in c["source"].lower())
    lemma_count = sum(1 for c in clean_cases if "lemma" in c["source"].lower())

    # Create clean dataset
    clean_data = {
        "version": "2.0-clean",
        "created": datetime.now().isoformat(),
        "source": data["source"],
        "description": f"Cleaned RCA dataset - removed {removed_count} mislabeled entries",
        "original_total": original_count,
        "removed_ids": list(REMOVE_RCA_IDS),
        "removal_reasons": {
            "RCA_118": "Normal Redis startup logs labeled as config_error",
            "RCA_165": "Normal service startup labeled as config_error",
            "RCA_182": "Normal initialization logs labeled as dependency_failure"
        },
        "total_cases": len(clean_cases),
        "distribution": {
            "opseval": opseval_count,
            "lemma_rca": lemma_count
        },
        "test_cases": clean_cases
    }

    save_json(clean_data, output_path)

    print(f"RCA: {original_count} -> {len(clean_cases)} (removed {removed_count})")
    print(f"  OpsEval: {opseval_count}")
    print(f"  LEMMA-RCA: {lemma_count}")

    return clean_cases


def create_sampled_dataset(
    annotation_cases: list,
    rca_cases: list,
    output_path: Path,
    seed: int = RANDOM_SEED
):
    """
    Create a sampled dataset with seed for reproducibility.

    Sample: 100 annotation + 50 RCA = 150 total
    """
    random.seed(seed)

    # Sample from each dataset
    ann_sample = random.sample(annotation_cases, min(ANNOTATION_SAMPLE_SIZE, len(annotation_cases)))
    rca_sample = random.sample(rca_cases, min(RCA_SAMPLE_SIZE, len(rca_cases)))

    # Combine samples
    combined = []

    # Add annotation samples with task_type marker
    for case in ann_sample:
        combined.append({
            **case,
            "task_type": "annotation"
        })

    # Add RCA samples with task_type marker
    for case in rca_sample:
        combined.append({
            **case,
            "task_type": "rca"
        })

    # Create sampled dataset
    sampled_data = {
        "version": "2.0-sampled",
        "created": datetime.now().isoformat(),
        "description": f"Sampled benchmark dataset (seed={seed})",
        "seed": seed,
        "sampling": {
            "annotation_pool": len(annotation_cases),
            "annotation_sampled": len(ann_sample),
            "rca_pool": len(rca_cases),
            "rca_sampled": len(rca_sample)
        },
        "total_cases": len(combined),
        "test_cases": combined
    }

    save_json(sampled_data, output_path)

    print(f"\nSampled dataset created with seed={seed}:")
    print(f"  Annotation: {len(ann_sample)} from {len(annotation_cases)}")
    print(f"  RCA: {len(rca_sample)} from {len(rca_cases)}")
    print(f"  Total: {len(combined)}")

    # Print sample IDs for verification
    print(f"\nSampled annotation IDs (first 10): {[c['id'] for c in ann_sample[:10]]}")
    print(f"Sampled RCA IDs (first 10): {[c['id'] for c in rca_sample[:10]]}")


def main():
    """Main entry point."""
    # Paths
    base_dir = Path(__file__).parent.parent
    processed_dir = base_dir / "datasets" / "processed"

    annotation_input = processed_dir / "annotation_test.json"
    rca_input = processed_dir / "rca_test.json"

    annotation_clean = processed_dir / "annotation_clean.json"
    rca_clean = processed_dir / "rca_clean.json"
    sampled_output = processed_dir / "benchmark_150_seed42.json"

    print("=" * 60)
    print("Constitutional AIOps - Dataset Cleanup & Sampling")
    print("=" * 60)
    print()

    # Step 1: Clean annotation dataset
    print("Step 1: Cleaning annotation dataset...")
    print(f"  Removing {len(REMOVE_ANNOTATION_IDS)} bogus BGL entries")
    annotation_cases = clean_annotation_dataset(annotation_input, annotation_clean)
    print()

    # Step 2: Clean RCA dataset
    print("Step 2: Cleaning RCA dataset...")
    print(f"  Removing {len(REMOVE_RCA_IDS)} mislabeled entries")
    rca_cases = clean_rca_dataset(rca_input, rca_clean)
    print()

    # Step 3: Create sampled dataset
    print("Step 3: Creating sampled dataset...")
    create_sampled_dataset(annotation_cases, rca_cases, sampled_output)
    print()

    # Summary
    print("=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"Annotation: 200 -> {len(annotation_cases)} (removed 62)")
    print(f"RCA: 183 -> {len(rca_cases)} (removed 3)")
    print(f"Total clean: {len(annotation_cases) + len(rca_cases)}")
    print(f"Sampled: 150 (100 ann + 50 rca) with seed=42")
    print()
    print("Output files:")
    print(f"  - {annotation_clean}")
    print(f"  - {rca_clean}")
    print(f"  - {sampled_output}")


if __name__ == "__main__":
    main()
