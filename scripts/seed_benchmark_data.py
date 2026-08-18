#!/usr/bin/env python3
"""Seed the Benchmark page with a small, synthetic public sample.

Why this exists
---------------
The Benchmark page (Datasets / Results / Compare tabs) needs data present under
``data/benchmark/`` to render. The open-source build does **not** ship the
paper's private research corpus. Instead this script writes a tiny, fully
**synthetic** starter dataset -- safe to publish, obviously not real telemetry --
so the page works out of the box and self-hosters can swap in their own data
("bring your own dataset").

What it writes (idempotent, deterministic -- stdlib only, no dependencies):
  * data/benchmark/intermediate/datasets/annotation_test.json
  * data/benchmark/intermediate/datasets/rca_test.json
  * data/benchmark/intermediate/datasets/benchmark_150_seed42.json
        (the curated file name the runner loads by default; here a small
        synthetic annotation+RCA mix, each case tagged with ``task_type``)

What it does NOT touch:
  * data/benchmark/results/  -- the published aggregate result summaries that
    ship with the app are left exactly as committed.

Bring your own dataset
----------------------
Replace the JSON files above with your own cases in the same shape (see the
records below for the schema) and both the Benchmark page and the benchmark
runner will pick them up. The original corpus-backed seeder that produced the
paper's datasets is kept privately, outside this public repository.
"""

from __future__ import annotations

import json
from pathlib import Path

# scripts/seed_benchmark_data.py -> repo root is one level up.
REPO_ROOT = Path(__file__).resolve().parents[1]
DATASETS = REPO_ROOT / "data" / "benchmark" / "intermediate" / "datasets"

_CREATED = "2026-01-01T00:00:00Z"
_SAMPLE_NOTE = "SYNTHETIC SAMPLE -- invented data, not real telemetry. Replace with your own dataset."


# --- Synthetic annotation cases (log anomaly classification) ----------------
# Fully invented example telemetry. Shape matches what the /benchmark API and
# the runner's annotation path expect.
ANNOTATION_CASES = [
    {
        "id": "ANN_SAMPLE_001",
        "source": "synthetic_sample",
        "input": {
            "telemetry_type": "log",
            "content": "2026-01-01 00:00:01 ERROR web-frontend: connection to payments-api timed out after 30000ms",
            "context": "Synthetic sample log from an example web service",
        },
        "expected": {
            "anomaly_detected": True,
            "severity": "critical",
            "category": "error",
            "classification": "alert",
        },
        "ground_truth_label": "alert",
        "alert_category": "APPSEV",
    },
    {
        "id": "ANN_SAMPLE_002",
        "source": "synthetic_sample",
        "input": {
            "telemetry_type": "log",
            "content": "2026-01-01 00:05:12 WARN example-db: disk usage on /var/lib/data reached 87% capacity",
            "context": "Synthetic sample log from an example database node",
        },
        "expected": {
            "anomaly_detected": True,
            "severity": "warning",
            "category": "resource",
            "classification": "warn",
        },
        "ground_truth_label": "warn",
        "alert_category": "RESOURCE",
    },
    {
        "id": "ANN_SAMPLE_003",
        "source": "synthetic_sample",
        "input": {
            "telemetry_type": "log",
            "content": "2026-01-01 00:07:44 INFO health-checker: liveness probe for orders-service returned 200 OK",
            "context": "Synthetic sample log from an example health check",
        },
        "expected": {
            "anomaly_detected": False,
            "severity": "info",
            "category": "normal",
            "classification": "normal",
        },
        "ground_truth_label": "normal",
        "alert_category": "NORMAL",
    },
]


# --- Synthetic RCA cases (root-cause analysis) ------------------------------
RCA_CASES = [
    {
        "id": "RCA_SAMPLE_001",
        "source": "synthetic_sample",
        "incident": {
            "title": "Checkout latency spike on the example storefront",
            "severity": "high",
            "fault_type": "latency_degradation",
            "logs": [
                "web-frontend: p99 checkout latency 8200ms (baseline 240ms)",
                "payments-api: connection pool exhausted, 0 idle connections",
                "payments-api: rejected 143 requests with pool timeout",
            ],
            "metrics": {"p99_latency_ms": 8200, "pool_wait_ms": 7600},
            "system_id": "example_storefront",
        },
        "expected_root_cause": "payments_api_connection_pool_exhaustion",
        "expected_category": "application",
        "acceptable_answers": [
            "connection pool exhaustion",
            "payments-api connection pool exhausted",
            "pool_exhaustion",
        ],
    },
    {
        "id": "RCA_SAMPLE_002",
        "source": "synthetic_sample",
        "incident": {
            "title": "Cache tier unavailable for the example catalog service",
            "severity": "critical",
            "fault_type": "service_unavailable",
            "logs": [
                "catalog-service: redis GET failed: connection refused",
                "example-cache: OOM, evicting keys under maxmemory policy",
                "example-cache: process restarted by supervisor",
            ],
            "metrics": {"cache_memory_pct": 100, "evicted_keys": 51230},
            "system_id": "example_cache",
        },
        "expected_root_cause": "cache_out_of_memory_restart",
        "expected_category": "infrastructure",
        "acceptable_answers": [
            "cache out of memory",
            "redis oom",
            "memory eviction",
        ],
    },
    {
        "id": "RCA_SAMPLE_003",
        "source": "synthetic_sample",
        "incident": {
            "title": "Elevated 5xx rate on the example API gateway",
            "severity": "high",
            "fault_type": "error_rate_increase",
            "logs": [
                "api-gateway: 5xx rate 18% (baseline 0.2%)",
                "auth-service: NullPointerException after deploy v2.3.1",
                "deploy-bot: rolled out auth-service v2.3.1 3 minutes before spike",
            ],
            "metrics": {"error_rate_pct": 18.0, "minutes_since_deploy": 3},
            "system_id": "example_gateway",
        },
        "expected_root_cause": "auth_service_bad_deploy_regression",
        "expected_category": "application",
        "acceptable_answers": [
            "bad deploy",
            "auth-service deploy regression",
            "regression from v2.3.1",
        ],
    },
]


def _annotation_doc() -> dict:
    return {
        "version": "synthetic-1",
        "created": _CREATED,
        "source": "Synthetic sample (bring your own dataset)",
        "description": _SAMPLE_NOTE,
        "total_cases": len(ANNOTATION_CASES),
        "distribution": {"anomaly": 2, "normal": 1},
        "test_cases": ANNOTATION_CASES,
    }


def _rca_doc() -> dict:
    return {
        "version": "synthetic-1",
        "created": _CREATED,
        "source": "Synthetic sample (bring your own dataset)",
        "description": _SAMPLE_NOTE,
        "total_cases": len(RCA_CASES),
        "distribution": {"application": 2, "infrastructure": 1},
        "categories": {"application": 2, "infrastructure": 1},
        "test_cases": RCA_CASES,
    }


def _curated_doc() -> dict:
    """The default curated file the runner loads (``benchmark_150_seed42.json``).

    In the OSS build this is a small synthetic annotation+RCA mix, each case
    tagged with ``task_type`` so the runner can split them.
    """
    cases = []
    for c in ANNOTATION_CASES:
        cases.append({**c, "task_type": "annotation"})
    for c in RCA_CASES:
        cases.append({**c, "task_type": "rca"})
    return {
        "version": "synthetic-1",
        "created": _CREATED,
        "description": _SAMPLE_NOTE,
        "seed": 42,
        "sampling": "synthetic",
        "total_cases": len(cases),
        "test_cases": cases,
    }


def _write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")


def main() -> None:
    print(f"[seed] destination : {DATASETS}")
    _write(DATASETS / "annotation_test.json", _annotation_doc())
    _write(DATASETS / "rca_test.json", _rca_doc())
    _write(DATASETS / "benchmark_150_seed42.json", _curated_doc())
    print("[seed] wrote synthetic sample datasets:")
    print("        - intermediate/datasets/annotation_test.json")
    print("        - intermediate/datasets/rca_test.json")
    print("        - intermediate/datasets/benchmark_150_seed42.json")
    print("[seed] results/ left untouched (published aggregate summaries ship as committed).")
    print("[seed] done. Replace these files with your own dataset to benchmark real data.")


if __name__ == "__main__":
    main()
