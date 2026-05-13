#!/usr/bin/env python3
"""
Phase 4.4 — Populate Neo4j with real benchmark episodes.

Reads benchmark_431_seed42.json (or any benchmark file) and inserts each
test case as a real Episode node in Neo4j with a 384-dim sentence-transformer
embedding.  Idempotent: uses MERGE, safe to re-run.

Usage (from repo root on the AWS instance):
    python3 scripts/populate_neo4j.py
    python3 scripts/populate_neo4j.py --dataset benchmark/datasets/processed/benchmark_431_seed42.json
    python3 scripts/populate_neo4j.py --dataset benchmark/datasets/processed/benchmark_400_seed42.json \
        --exclude-ids RCA_001 RCA_002   # hold-out for 4.5b LEMMA fold

Output summary:
    Episodes inserted / skipped / failed + final graph stats.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

# Make sure project root is on sys.path when run directly
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.memory.episode_store import Episode, EpisodeStore
from src.memory.neo4j_client import Neo4jClient, NEO4J_AVAILABLE


# ── helpers ────────────────────────────────────────────────────────────────

def _derive_category(source: str, task_type: str) -> str:
    if task_type == "rca":
        if "lemma" in source:
            return "cloud_microservices"
        if "opseval" in source:
            return "network_rca"
        return "rca"
    # annotation
    if "openssh" in source:
        return "security"
    if "apache" in source:
        return "web_access"
    if "bgl" in source:
        return "hpc_compute"
    if "hdfs" in source:
        return "distributed_storage"
    return "log_anomaly"


def _derive_services(case: dict) -> list[str]:
    """Extract affected service names from a benchmark case."""
    source = case.get("source", "")

    # LEMMA-RCA: system_id like "cloud_computing_orders-db"
    incident = case.get("incident", {})
    system_id = incident.get("system_id", "")
    if system_id:
        # strip "cloud_computing_" prefix, use remainder as service name
        svc = system_id.replace("cloud_computing_", "").replace("_", "-")
        return [svc] if svc else ["unknown-service"]

    # Loghub sources — map to well-known service names
    if "hdfs" in source:
        return ["hdfs-datanode", "hdfs-namenode"]
    if "bgl" in source:
        return ["hpc-node"]
    if "apache" in source:
        return ["apache-httpd"]
    if "openssh" in source:
        return ["sshd"]
    if "opseval" in source:
        return ["network-device"]

    return ["unknown-service"]


def _case_to_episode(case: dict, exclude_ids: set[str]) -> Optional[Episode]:
    """Convert a benchmark test case dict to an Episode object."""
    case_id = case.get("id", str(uuid4()))
    if case_id in exclude_ids:
        return None

    task_type = case.get("task_type", "annotation")
    source = case.get("source", "unknown")
    episode_id = f"ep-{case_id.lower().replace('_', '-')}"

    if task_type == "rca":
        incident = case.get("incident", {})
        title = incident.get("title") or f"RCA incident {case_id}"
        logs = incident.get("logs", [])
        description = " ".join(str(l) for l in logs[:8]).strip()
        root_cause = case.get("expected_root_cause", "")
        severity = incident.get("severity", "high")
        category = _derive_category(source, task_type)
        affected = _derive_services(case)

    else:  # annotation
        inp = case.get("input", {})
        content = inp.get("content", "")
        ctx = inp.get("context", "")
        title = f"[{source}] telemetry anomaly — {case_id}"
        description = f"{content} {ctx}".strip()[:600]
        expected = case.get("expected", {})
        root_cause = (
            "anomaly_detected"
            if expected.get("anomaly_detected") is True
            else "normal_operation"
        )
        severity = expected.get("severity", "medium")
        if not isinstance(severity, str):
            severity = "medium"
        category = _derive_category(source, task_type)
        affected = _derive_services(case)

    # Outcome: all benchmark episodes are "ground truth verified" resolved
    outcome = "resolved"

    return Episode(
        episode_id=episode_id,
        incident_id=case_id,
        title=title,
        description=description,
        severity=severity,
        category=category,
        detected_at=datetime.utcnow(),
        analyzed_at=datetime.utcnow(),
        resolved_at=datetime.utcnow(),
        root_cause=root_cause,
        confidence=0.95,  # ground truth labels are authoritative
        affected_services=affected,
        outcome=outcome,
        tags=[source, task_type],
        resolution_notes=f"Ground-truth benchmark case from {source}",
    )


# ── main ───────────────────────────────────────────────────────────────────

async def run(dataset_path: Path, exclude_ids: set[str], dry_run: bool) -> None:
    if not NEO4J_AVAILABLE:
        print("[ERROR] neo4j Python driver not installed.")
        print("        pip install neo4j sentence-transformers torch")
        sys.exit(1)

    # Load benchmark
    print(f"[populate] Loading {dataset_path} ...")
    with dataset_path.open() as f:
        data = json.load(f)

    cases_key = "test_cases" if "test_cases" in data else "cases"
    cases = data.get(cases_key, [])
    print(f"[populate] {len(cases)} total cases in dataset")

    if exclude_ids:
        print(f"[populate] Excluding {len(exclude_ids)} IDs (held-out for 4.5b fold)")

    # Build episode objects
    episodes: list[Episode] = []
    for case in cases:
        ep = _case_to_episode(case, exclude_ids)
        if ep is not None:
            episodes.append(ep)

    print(f"[populate] {len(episodes)} episodes to insert")

    if dry_run:
        print("[populate] DRY RUN — not writing to Neo4j")
        for ep in episodes[:3]:
            print(f"  {ep.episode_id}  title={ep.title[:60]}  root_cause={ep.root_cause[:40]}")
        return

    # Connect to Neo4j
    client = Neo4jClient()
    connected = await client.connect()
    if not connected:
        print("[ERROR] Could not connect to Neo4j at bolt://localhost:7687")
        print("        Check NEO4J_URI / NEO4J_PASSWORD env vars or run docker-compose.")
        sys.exit(1)

    store = EpisodeStore(neo4j_client=client)

    inserted = skipped = failed = 0
    t0 = datetime.utcnow()

    for i, ep in enumerate(episodes):
        try:
            await store.store_episode(ep)
            inserted += 1
            if (i + 1) % 20 == 0 or (i + 1) == len(episodes):
                elapsed = (datetime.utcnow() - t0).total_seconds()
                print(f"  [{i+1}/{len(episodes)}] inserted={inserted} skipped={skipped} "
                      f"failed={failed}  ({elapsed:.0f}s elapsed)")
        except Exception as exc:
            failed += 1
            if failed <= 5:
                print(f"  [WARN] {ep.episode_id}: {exc}")

    print()
    print("=" * 60)
    print(f"  Inserted : {inserted}")
    print(f"  Skipped  : {skipped}")
    print(f"  Failed   : {failed}")
    print(f"  Elapsed  : {(datetime.utcnow() - t0).total_seconds():.1f}s")

    # Final graph stats
    try:
        stats = await client.get_graph_stats()
        print()
        print(f"  Neo4j graph now: {stats.get('nodes', {})} nodes")
        print(f"                   {stats.get('edges', {})} edges")
    except Exception:
        pass

    print("=" * 60)
    await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate Neo4j with benchmark episodes (Phase 4.4)")
    parser.add_argument(
        "--dataset",
        default=str(ROOT / "benchmark" / "datasets" / "processed" / "benchmark_431_seed42.json"),
        help="Path to benchmark JSON file",
    )
    parser.add_argument(
        "--exclude-ids",
        nargs="*",
        default=[],
        metavar="ID",
        help="Case IDs to exclude (for held-out fold in 4.5b)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and preview episodes without writing to Neo4j",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"[ERROR] Dataset not found: {dataset_path}")
        sys.exit(1)

    asyncio.run(run(dataset_path, set(args.exclude_ids), args.dry_run))


if __name__ == "__main__":
    main()
