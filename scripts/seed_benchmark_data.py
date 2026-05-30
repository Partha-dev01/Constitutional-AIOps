#!/usr/bin/env python3
"""Seed app-facing benchmark data from the read-only research corpus.

Why this exists
---------------
The Benchmark page (Datasets / Results / Compare tabs) renders empty in the
deployed container because:

  * The curated datasets live (git-tracked) under ``benchmark/intermediate/
    datasets/`` but the production image only ships ``src/`` + ``configs/`` --
    ``benchmark/`` is never COPYed in, so the API finds no datasets.
  * The headline + ablation run *results* live under ``benchmark/final/`` in a
    research-paper schema (``avg_inference_latency_ms``, ``total_correct`` ...),
    NOT the schema the web API / React frontend read. And ``benchmark/results/``
    (the dir the API scans) is git-ignored and absent.

This script reads the corpus **READ-ONLY** and writes a small, app-shaped
mirror into ``data/benchmark/`` (which the API now prefers via ``_data_root()``
and which the Dockerfile now COPYs). It NEVER modifies anything under
``benchmark/`` -- that corpus is the paper's evidence and is strictly off limits.

Design notes
------------
* Standard library only -- no new dependencies.
* Idempotent -- re-running overwrites the generated mirror deterministically.
* Datasets are copied **verbatim** (byte-for-byte) so previews/distributions
  match the corpus exactly.
* Result files are **key-mapped** from the corpus ``summary.json`` schema into
  the shape ``src/api/routes/benchmark.py`` + ``frontend/.../Benchmark.tsx``
  read: ``avg_latency_ms``, ``passed_tests``, ``total_tests``,
  ``annotation_accuracy``, ``rca_accuracy``, ``bert_f1``, ``p95_latency_ms``,
  ``status: "completed"`` ... (plus the original corpus fields, retained for
  provenance, never read by the app).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

# scripts/seed_benchmark_data.py -> repo root is one level up.
REPO_ROOT = Path(__file__).resolve().parents[1]

# READ-ONLY source corpus (never written to).
CORPUS = REPO_ROOT / "benchmark"
CORPUS_DATASETS = CORPUS / "intermediate" / "datasets"
CORPUS_MAIN = CORPUS / "final" / "main_benchmark"
CORPUS_ABLATION = CORPUS / "final" / "ablation_v4"

# Destination app-facing mirror (the only thing this script writes).
DATA_ROOT = REPO_ROOT / "data" / "benchmark"
DATA_DATASETS = DATA_ROOT / "intermediate" / "datasets"
DATA_RESULTS = DATA_ROOT / "results"

# Datasets copied verbatim when present (the API reads annotation_test.json /
# rca_test.json; the runner also falls back to *_clean.json + benchmark_150).
DATASET_FILES = [
    "annotation_test.json",
    "rca_test.json",
    "annotation_clean.json",
    "rca_clean.json",
    "benchmark_150_seed42.json",
]

# Result runs to surface in the app. "main" is the headline run; the rest are a
# representative spread of v4 ablations so the Compare tab is meaningful. Each
# tuple is (corpus summary.json path, destination model dir name).
RESULT_RUNS = [
    (CORPUS_MAIN / "summary.json", "constitutional_aiops"),
    (CORPUS_ABLATION / "ablation_full" / "summary.json", "ablation_full"),
    (CORPUS_ABLATION / "ablation_single_4b" / "summary.json", "ablation_single_4b"),
    (CORPUS_ABLATION / "ablation_single_14b" / "summary.json", "ablation_single_14b"),
    (CORPUS_ABLATION / "ablation_no_constitutional" / "summary.json", "ablation_no_constitutional"),
]


def _to_app_result(corpus: dict, model_dir: str) -> dict:
    """Key-map a corpus summary.json into the app's benchmark_result.json shape.

    The app/frontend read: model_name, annotation_accuracy, rca_accuracy,
    bert_f1, avg_latency_ms, p50/p95/p99_latency_ms, total_tests, passed_tests,
    status. We map corpus field names onto those and keep the originals for
    provenance.
    """
    total_tests = corpus.get("total_tests", 0)
    passed_tests = corpus.get("total_correct", 0)
    avg_latency_ms = corpus.get("avg_inference_latency_ms", 0.0)

    return {
        # --- fields the API + frontend read ---
        "model_name": corpus.get("model_name", model_dir),
        "status": "completed",
        "annotation_accuracy": corpus.get("annotation_accuracy", 0.0),
        "rca_accuracy": corpus.get("rca_accuracy", 0.0),
        "overall_accuracy": corpus.get("overall_accuracy", 0.0),
        "bert_f1": corpus.get("bert_f1", 0.0),
        "avg_latency_ms": avg_latency_ms,
        "p50_latency_ms": corpus.get("p50_latency_ms", 0.0),
        "p95_latency_ms": corpus.get("p95_latency_ms", 0.0),
        "p99_latency_ms": corpus.get("p99_latency_ms", 0.0),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        # --- helpful context, also surfaced verbatim ---
        "model_type": corpus.get("model_type", ""),
        "fast_model": corpus.get("fast_model", ""),
        "reasoning_model": corpus.get("reasoning_model", ""),
        "annotation_tests": corpus.get("annotation_tests", 0),
        "annotation_passed": corpus.get("annotation_passed", 0),
        "rca_tests": corpus.get("rca_tests", 0),
        "rca_passed": corpus.get("rca_passed", 0),
        "dataset": corpus.get("dataset", ""),
        "temperature": corpus.get("temperature", 0.0),
        "started_at": corpus.get("timestamp", ""),
        "completed_at": corpus.get("timestamp", ""),
        # Provenance: this result was seeded from the corpus, not freshly run.
        "source": "seeded_from_corpus",
        "test_results": [],
    }


def seed_datasets() -> list[str]:
    """Copy curated datasets verbatim into data/benchmark/. Returns names written."""
    DATA_DATASETS.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name in DATASET_FILES:
        src = CORPUS_DATASETS / name
        if not src.exists():
            continue
        # Validate it parses before copying (fail loudly on a corrupt corpus).
        with src.open("r", encoding="utf-8") as f:
            json.load(f)
        shutil.copyfile(src, DATA_DATASETS / name)  # verbatim bytes
        written.append(name)
    return written


def seed_results() -> list[str]:
    """Key-map corpus run summaries into app-shaped result files. Returns dirs written."""
    DATA_RESULTS.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for src, model_dir in RESULT_RUNS:
        if not src.exists():
            continue
        with src.open("r", encoding="utf-8") as f:
            corpus = json.load(f)
        app_result = _to_app_result(corpus, model_dir)
        out_dir = DATA_RESULTS / model_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "benchmark_result.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(app_result, f, indent=2)
            f.write("\n")
        written.append(model_dir)
    return written


def main() -> None:
    print(f"[seed] corpus (read-only) : {CORPUS}")
    print(f"[seed] destination        : {DATA_ROOT}")

    if not CORPUS.exists():
        raise SystemExit(f"[seed] ERROR: corpus not found at {CORPUS}")

    datasets = seed_datasets()
    results = seed_results()

    print(f"[seed] wrote {len(datasets)} dataset(s) -> {DATA_DATASETS}")
    for name in datasets:
        print(f"        - intermediate/datasets/{name}")
    print(f"[seed] wrote {len(results)} result run(s) -> {DATA_RESULTS}")
    for model_dir in results:
        print(f"        - results/{model_dir}/benchmark_result.json")

    if not datasets:
        print("[seed] WARNING: no datasets seeded (corpus datasets missing?)")
    if not results:
        print("[seed] WARNING: no results seeded (corpus summaries missing?)")
    print("[seed] done.")


if __name__ == "__main__":
    main()
