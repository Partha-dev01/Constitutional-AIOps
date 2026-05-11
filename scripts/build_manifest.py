#!/usr/bin/env python3
"""scripts/build_manifest.py — produce a tamper-evident manifest for the benchmark.

Records:
  * SHA-256 of every input source file (raw datasets) — pinned by content
  * SHA-256 of the curation script(s) that produced the outputs — pinned by code
  * SHA-256 of every output file (curated benchmark JSONs) — pinned by content
  * Generator metadata (git SHA, flags, timestamp)

Why this exists: the v2.0 run silently shipped 62 bogus BGL entries and 17
orphaned RCA cases for weeks before anyone noticed. A manifest + verifier
would have caught both at the moment of curation by detecting label drift
or script changes.

This is the lightweight alternative to DVC for a single-team research repo.
For full DVC parity you'd add a pipeline DAG; we don't need it.

Usage:
    python scripts/build_manifest.py [--out benchmark/data/manifest.json]

If --out is omitted, prints the manifest JSON to stdout.

Non-destructive: only reads files and writes the manifest.
"""

from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Files that constitute the benchmark.
# We treat the curated outputs as authoritative; raw sources are recorded
# only by SHA so we can detect any future drift in the underlying data.
SOURCES: list[dict] = [
    # Raw Loghub samples currently used (HDFS ships as .log, BGL as _structured.csv)
    {
        "path": "benchmark/datasets/raw/loghub/hdfs/HDFS_2k.log",
        "origin": "https://github.com/logpai/loghub",
        "kind": "raw",
    },
    {
        "path": "benchmark/datasets/raw/loghub/bgl/BGL_2k.log_structured.csv",
        "origin": "https://github.com/logpai/loghub",
        "kind": "raw",
    },
    # OpsEval English splits we mine from
    {
        "path": "benchmark/datasets/raw/opseval/data/en/test/Wired Network.json",
        "origin": "https://github.com/netmanaiops/opseval-datasets",
        "kind": "raw",
    },
    {
        "path": "benchmark/datasets/raw/opseval/data/en/test/5G Communication.json",
        "origin": "https://github.com/netmanaiops/opseval-datasets",
        "kind": "raw",
    },
    {
        "path": "benchmark/datasets/raw/opseval/data/en/test/Mobile Communication Network.json",
        "origin": "https://github.com/netmanaiops/opseval-datasets",
        "kind": "raw",
    },
]

# Scripts whose contents materially affect the curated outputs.
# If any of these change, the manifest hash for outputs may also need to change.
GENERATOR_SCRIPTS: list[str] = [
    "benchmark/scripts/clean_dataset.py",
    "benchmark/scripts/prepare_datasets.py",
    "benchmark/scripts/remove_chinese.py",
    "benchmark/scripts/fix_benchmark_dataset.py",
]

# Curated outputs that should be deterministic given the sources + scripts.
OUTPUTS_GLOB: list[str] = [
    "benchmark/datasets/processed/annotation_clean.json",
    "benchmark/datasets/processed/rca_clean.json",
    "benchmark/datasets/processed/benchmark_150_seed42.json",
    # benchmark_500_seed42.json will be added by Phase 2.8 when it exists
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(rel_path: str, kind: str, origin: str | None = None) -> dict | None:
    p = REPO_ROOT / rel_path
    if not p.exists():
        return None
    rec = {
        "path": rel_path,
        "sha256": sha256_file(p),
        "size_bytes": p.stat().st_size,
        "kind": kind,
    }
    if origin:
        rec["origin"] = origin
    # For curated benchmark JSONs, include case count for quick sanity check
    if rel_path.endswith(".json") and "processed" in rel_path:
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "test_cases" in data:
                rec["case_count"] = len(data["test_cases"])
            elif isinstance(data, list):
                rec["case_count"] = len(data)
        except Exception:
            pass
    return rec


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT, stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


def build_manifest() -> dict:
    sources = []
    for spec in SOURCES:
        rec = file_record(spec["path"], "source", spec.get("origin"))
        if rec is not None:
            sources.append(rec)
        else:
            sources.append({"path": spec["path"], "missing": True, "kind": "source"})

    scripts = []
    for sp in GENERATOR_SCRIPTS:
        rec = file_record(sp, "script")
        if rec is not None:
            scripts.append(rec)

    outputs = []
    for op in OUTPUTS_GLOB:
        rec = file_record(op, "output")
        if rec is not None:
            outputs.append(rec)

    return {
        "schema_version": 1,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": {
            "git_sha": git_sha(),
            "script": "scripts/build_manifest.py",
        },
        "sources": sources,
        "scripts": scripts,
        "outputs": outputs,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=None,
                    help="Output path. If omitted, prints to stdout.")
    args = ap.parse_args()

    manifest = build_manifest()
    text = json.dumps(manifest, indent=2)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"[manifest] wrote {args.out} ({len(text):,} bytes)")
        # Friendly summary
        print(f"  sources: {sum(1 for s in manifest['sources'] if 'sha256' in s)}/{len(manifest['sources'])} present")
        print(f"  scripts: {len(manifest['scripts'])}")
        print(f"  outputs: {len(manifest['outputs'])}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
