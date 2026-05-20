#!/usr/bin/env python3
"""
Constitutional AIOps - Dataset Preparation (v2.0)

Converts downloaded datasets into standardized benchmark format.
NO synthetic data - only transforms real data into our format.

Sources:
  Annotation: Loghub (HDFS, BGL, Apache, Linux, OpenSSH), LogEval
  RCA: OpsEval, LEMMA-RCA, AnoMod, LogEval

Creates:
- annotation_test.json (annotation cases from all log sources)
- rca_test.json (RCA cases from all QA/fault sources)
- benchmark_{N}_seed42.json (combined curated benchmark)

Usage:
    python benchmark/scripts/prepare_datasets.py                    # Default ~200 cases
    python benchmark/scripts/prepare_datasets.py --target 500       # Expanded ~500 cases
    python benchmark/scripts/prepare_datasets.py --skip-lemma       # Skip LEMMA-RCA
"""

import os
import sys
import json
import csv
import random
import argparse
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Validation guards (added 2026-05-12, Phase 1.5 hardening)
#
# These prevent two known-historical bugs from recurring:
#  1. Missing `task_type` field → runner silently skips the case (17 orphaned
#     RCA cases bug, fix_benchmark_dataset.py was created to patch this).
#  2. RCA case missing both `logs` and `question` → runner.py:_run_rca_test
#     crashes with KeyError on incident["logs"] (64% crash rate bug).
#
# We assert at curation time, NOT at runtime, so the failure surfaces at
# dataset-build instead of mid-benchmark hour 2.
# ---------------------------------------------------------------------------

VALID_TASK_TYPES = {"annotation", "rca"}
VALID_SEVERITIES = {"info", "low", "warning", "medium", "high", "critical"}


def validate_cases(cases: list, context: str = "") -> None:
    """Validate a list of benchmark cases. Raises AssertionError on first failure.

    Args:
        cases: list of case dicts
        context: short label for error messages (e.g. 'annotation_test.json')
    """
    if not isinstance(cases, list):
        raise AssertionError(f"{context}: expected list of cases, got {type(cases)}")

    seen_ids: set[str] = set()
    for i, case in enumerate(cases):
        case_id = case.get("id", f"<idx={i}>")

        # Required: stable unique id
        if "id" not in case:
            raise AssertionError(
                f"{context}: case at index {i} missing required field 'id'"
            )
        if case_id in seen_ids:
            raise AssertionError(
                f"{context}: duplicate case id {case_id!r} "
                f"(would cause silent JSONL collisions on resume)"
            )
        seen_ids.add(case_id)

        # Required: task_type — runner filters on this; missing == silent skip
        tt = case.get("task_type")
        if tt is None:
            raise AssertionError(
                f"{context}: case {case_id} missing 'task_type' field "
                f"(would be silently skipped by runner.py — see 17-orphaned-cases bug)"
            )
        if tt not in VALID_TASK_TYPES:
            raise AssertionError(
                f"{context}: case {case_id} has invalid task_type={tt!r} "
                f"(must be one of {VALID_TASK_TYPES})"
            )

        # RCA cases need either logs or question — runner.py:_run_rca_test
        # accesses incident['logs'] or incident['question'] depending on source
        if tt == "rca":
            incident = case.get("incident") or case.get("input") or {}
            has_logs = bool(incident.get("logs"))
            has_question = bool(incident.get("question"))
            if not (has_logs or has_question):
                raise AssertionError(
                    f"{context}: RCA case {case_id} missing BOTH 'logs' and "
                    f"'question' fields in incident/input "
                    f"(would crash _run_rca_test with KeyError — see 64% crash bug)"
                )

        # Severity hygiene (if present)
        expected = case.get("expected") or {}
        sev = expected.get("severity") or case.get("severity")
        if sev is not None and str(sev).lower() not in VALID_SEVERITIES:
            # Warning, not error — model output not curator-controlled
            # but flag in case curator typo'd the gold label
            print(
                f"  WARN {context}: case {case_id} has severity={sev!r} "
                f"not in {VALID_SEVERITIES}",
                file=sys.stderr,
            )
from typing import Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

BENCHMARK_DIR = PROJECT_ROOT / "benchmark"
RAW_DIR = BENCHMARK_DIR / "raw"
PROCESSED_DIR = BENCHMARK_DIR / "intermediate" / "datasets"


# ============================================================
# Annotation Source Loaders
# ============================================================

# Common anomaly keywords for log classification
ANOMALY_KEYWORDS = [
    "ERROR", "EXCEPTION", "FAILED", "TIMEOUT", "REFUSED",
    "SHUTDOWN", "TERMINATED", "FATAL", "CRASH", "WARN",
    "IOException", "OutOfMemory", "SocketException",
    "CRITICAL", "PANIC", "DENIED", "INVALID", "ABORT",
]


def load_bgl_structured() -> list[dict]:
    """Load REAL BGL logs from structured CSV with labels."""
    bgl_dir = RAW_DIR / "loghub" / "bgl"
    logs = []

    structured_path = bgl_dir / "BGL_2k.log_structured.csv"
    if not structured_path.exists():
        print("   WARNING: BGL_2k.log_structured.csv not found!")
        return []

    print(f"   Loading {structured_path.name}...")
    with open(structured_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row.get("Label", "-")
            content = row.get("Content", "")
            level = row.get("Level", "INFO")
            component = row.get("Component", "")
            node = row.get("Node", "")
            event_template = row.get("EventTemplate", "")

            # Label "-" = normal, anything else = anomaly
            is_anomaly = label != "-"

            if content:
                logs.append({
                    "content": content,
                    "full_log": f"{label} {row.get('Timestamp', '')} {row.get('Date', '')} {node} {content}",
                    "label": "anomaly" if is_anomaly else "normal",
                    "source": "loghub_bgl",
                    "level": level,
                    "component": component,
                    "alert_category": label if is_anomaly else None,
                    "event_template": event_template,
                })

    print(f"   Loaded {len(logs)} BGL log entries")
    return logs


def load_hdfs_logs() -> list[dict]:
    """Load REAL HDFS logs from raw log file."""
    hdfs_dir = RAW_DIR / "loghub" / "hdfs"
    logs = []

    raw_path = hdfs_dir / "HDFS_2k.log"
    if not raw_path.exists():
        print("   WARNING: HDFS_2k.log not found!")
        return []

    print(f"   Loading {raw_path.name}...")

    with open(raw_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            line_upper = line.upper()
            is_anomaly = any(kw.upper() in line_upper for kw in ANOMALY_KEYWORDS)

            if "ERROR" in line_upper:
                level = "ERROR"
            elif "WARN" in line_upper:
                level = "WARN"
            elif "FATAL" in line_upper:
                level = "FATAL"
            else:
                level = "INFO"

            logs.append({
                "content": line,
                "label": "anomaly" if is_anomaly else "normal",
                "source": "loghub_hdfs",
                "level": level,
            })

    print(f"   Loaded {len(logs)} HDFS log entries")
    return logs


def load_loghub_generic(dataset_key: str, dataset_name: str, context: str) -> list[dict]:
    """Generic loader for Loghub 2k log datasets (Apache, Linux, OpenSSH, etc.).

    Tries structured CSV first (has Label column), falls back to raw log + keyword detection.

    Args:
        dataset_key: Directory name under loghub/ (e.g., "apache")
        dataset_name: Display name and filename prefix (e.g., "Apache")
        context: Context description for annotation cases

    Returns:
        List of log entries with content, label, source, level fields.
    """
    dataset_dir = RAW_DIR / "loghub" / dataset_key
    logs = []

    # Try structured CSV first (has Label column for some datasets)
    structured_path = dataset_dir / f"{dataset_name}_2k.log_structured.csv"
    if structured_path.exists():
        print(f"   Loading {structured_path.name} (structured)...")
        try:
            with open(structured_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                fields = reader.fieldnames or []

                has_label = "Label" in fields
                content_field = "Content" if "Content" in fields else None

                for row in reader:
                    content = row.get(content_field, "") if content_field else ""
                    if not content:
                        # Try other common content fields
                        for cf in ["Content", "Message", "Log", "content", "message"]:
                            if cf in row and row[cf]:
                                content = row[cf]
                                break
                    if not content:
                        continue

                    # Determine label
                    if has_label:
                        label_val = row.get("Label", "-")
                        is_anomaly = label_val != "-" and label_val.strip() != ""
                    else:
                        # Fall back to keyword detection
                        content_upper = content.upper()
                        is_anomaly = any(kw.upper() in content_upper for kw in ANOMALY_KEYWORDS)

                    level = row.get("Level", "")
                    if not level:
                        content_upper = content.upper()
                        if "ERROR" in content_upper:
                            level = "ERROR"
                        elif "WARN" in content_upper:
                            level = "WARN"
                        elif "FATAL" in content_upper or "CRITICAL" in content_upper:
                            level = "FATAL"
                        else:
                            level = "INFO"

                    logs.append({
                        "content": content,
                        "label": "anomaly" if is_anomaly else "normal",
                        "source": f"loghub_{dataset_key}",
                        "level": level,
                        "context": context,
                    })

            print(f"   Loaded {len(logs)} {dataset_name} entries from structured CSV")
            return logs
        except Exception as e:
            print(f"   Warning: structured CSV parse failed: {e}")
            logs = []

    # Fall back to raw log file with keyword detection
    raw_path = dataset_dir / f"{dataset_name}_2k.log"
    if not raw_path.exists():
        print(f"   WARNING: {dataset_name}_2k.log not found!")
        return []

    print(f"   Loading {raw_path.name} (raw, keyword detection)...")
    with open(raw_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            line_upper = line.upper()
            is_anomaly = any(kw.upper() in line_upper for kw in ANOMALY_KEYWORDS)

            if "ERROR" in line_upper:
                level = "ERROR"
            elif "WARN" in line_upper:
                level = "WARN"
            elif "FATAL" in line_upper or "CRITICAL" in line_upper:
                level = "FATAL"
            else:
                level = "INFO"

            logs.append({
                "content": line,
                "label": "anomaly" if is_anomaly else "normal",
                "source": f"loghub_{dataset_key}",
                "level": level,
                "context": context,
            })

    print(f"   Loaded {len(logs)} {dataset_name} entries from raw log")
    return logs


def load_logeval_anomaly() -> list[dict]:
    """Load LogEval anomaly detection data.

    The LogEval repo structure varies; we search for anomaly detection data
    in common directory patterns and parse JSON/JSONL/CSV formats.

    Returns:
        List of log entries with content, label, source fields.
    """
    logeval_dir = RAW_DIR / "logeval"
    logs = []

    if not logeval_dir.exists():
        print("   WARNING: LogEval directory not found!")
        return []

    print("   Scanning LogEval for anomaly detection data...")

    # Search for anomaly detection data in various possible paths
    search_paths = [
        logeval_dir / "data" / "anomaly_detection",
        logeval_dir / "data" / "anomaly",
        logeval_dir / "anomaly_detection",
        logeval_dir / "benchmark" / "anomaly_detection",
        logeval_dir / "datasets" / "anomaly_detection",
    ]

    data_dir = None
    for sp in search_paths:
        if sp.exists():
            data_dir = sp
            print(f"   Found anomaly data at: {sp.relative_to(logeval_dir)}")
            break

    if data_dir is None:
        # Broader search: find any JSON/JSONL files that might contain anomaly data
        print("   Standard paths not found, searching broadly...")
        all_json = list(logeval_dir.rglob("*.json")) + list(logeval_dir.rglob("*.jsonl"))
        anomaly_files = [f for f in all_json if "anomal" in f.name.lower() or "anomal" in str(f.parent).lower()]

        if anomaly_files:
            print(f"   Found {len(anomaly_files)} potential anomaly files")
            for af in anomaly_files[:5]:
                loaded = _try_load_logeval_file(af, "logeval_anomaly")
                logs.extend(loaded)
        else:
            # Try loading ANY data files and check for anomaly labels
            print("   No anomaly-specific files found. Trying all data files...")
            for json_file in list(logeval_dir.rglob("*.json"))[:20]:
                loaded = _try_load_logeval_file(json_file, "logeval_anomaly")
                if loaded:
                    logs.extend(loaded)
                    if len(logs) >= 500:
                        break
    else:
        # Load from the found directory
        for data_file in sorted(data_dir.rglob("*")):
            if data_file.suffix in (".json", ".jsonl", ".csv"):
                loaded = _try_load_logeval_file(data_file, "logeval_anomaly")
                logs.extend(loaded)

    print(f"   Loaded {len(logs)} LogEval anomaly entries")
    return logs


def _try_load_logeval_file(filepath: Path, source: str) -> list[dict]:
    """Try to load a LogEval data file in various formats."""
    entries = []
    try:
        if filepath.suffix == ".jsonl":
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    entry = _parse_logeval_entry(item, source)
                    if entry:
                        entries.append(entry)

        elif filepath.suffix == ".json":
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    entry = _parse_logeval_entry(item, source)
                    if entry:
                        entries.append(entry)
            elif isinstance(data, dict):
                # Might have a "data" or "samples" key
                for key in ["data", "samples", "test", "logs", "entries"]:
                    if key in data and isinstance(data[key], list):
                        for item in data[key]:
                            entry = _parse_logeval_entry(item, source)
                            if entry:
                                entries.append(entry)
                        break

        elif filepath.suffix == ".csv":
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Try to find content and label fields
                    content = ""
                    for cf in ["log", "content", "message", "text", "input", "Log", "Content"]:
                        if cf in row and row[cf]:
                            content = row[cf]
                            break
                    if not content:
                        continue

                    label_val = ""
                    for lf in ["label", "Label", "anomaly", "is_anomaly", "class"]:
                        if lf in row and row[lf]:
                            label_val = row[lf]
                            break

                    is_anomaly = label_val.lower() in ("anomaly", "1", "true", "yes", "abnormal")
                    entries.append({
                        "content": content,
                        "label": "anomaly" if is_anomaly else "normal",
                        "source": source,
                        "level": "ERROR" if is_anomaly else "INFO",
                    })

    except Exception:
        pass  # Skip files that can't be parsed

    return entries


def _parse_logeval_entry(item: Any, source: str) -> Optional[dict]:
    """Parse a single LogEval entry from various possible formats."""
    if not isinstance(item, dict):
        return None

    # Try to find content
    content = ""
    for cf in ["log", "content", "message", "text", "input", "Log", "Content", "question"]:
        if cf in item and item[cf]:
            content = str(item[cf])
            break

    if not content or len(content) < 10:
        return None

    # Try to find label
    label_val = ""
    for lf in ["label", "Label", "anomaly", "is_anomaly", "class", "output", "answer"]:
        if lf in item:
            label_val = str(item[lf])
            break

    # Detect anomaly from label
    label_lower = label_val.lower()
    is_anomaly = any(kw in label_lower for kw in ["anomal", "abnormal", "error", "fault", "1", "true", "yes"])

    # Skip if we can't determine the label confidently
    if not label_val:
        return None

    level = "ERROR" if is_anomaly else "INFO"
    content_upper = content.upper()
    if "WARN" in content_upper:
        level = "WARN"
    elif "FATAL" in content_upper:
        level = "FATAL"

    return {
        "content": content[:2000],  # Truncate very long entries
        "label": "anomaly" if is_anomaly else "normal",
        "source": source,
        "level": level,
    }


def load_logeval_diagnosis() -> list[dict]:
    """Load LogEval fault diagnosis data for RCA test cases.

    Returns:
        List of diagnosis cases with question, answer, source fields.
    """
    logeval_dir = RAW_DIR / "logeval"
    cases = []

    if not logeval_dir.exists():
        return []

    print("   Scanning LogEval for fault diagnosis data...")

    # Search for fault diagnosis data
    search_paths = [
        logeval_dir / "data" / "fault_diagnosis",
        logeval_dir / "data" / "diagnosis",
        logeval_dir / "fault_diagnosis",
        logeval_dir / "benchmark" / "fault_diagnosis",
    ]

    data_dir = None
    for sp in search_paths:
        if sp.exists():
            data_dir = sp
            print(f"   Found diagnosis data at: {sp.relative_to(logeval_dir)}")
            break

    if data_dir is None:
        # Broader search
        all_files = list(logeval_dir.rglob("*.json")) + list(logeval_dir.rglob("*.jsonl"))
        diag_files = [f for f in all_files if "diagnos" in f.name.lower() or "fault" in f.name.lower()]

        if diag_files:
            print(f"   Found {len(diag_files)} potential diagnosis files")
            for df in diag_files[:5]:
                loaded = _try_load_logeval_diagnosis_file(df)
                cases.extend(loaded)
        else:
            print("   No fault diagnosis data found in LogEval")
    else:
        for data_file in sorted(data_dir.rglob("*")):
            if data_file.suffix in (".json", ".jsonl", ".csv"):
                loaded = _try_load_logeval_diagnosis_file(data_file)
                cases.extend(loaded)

    print(f"   Loaded {len(cases)} LogEval diagnosis cases")
    return cases


def _try_load_logeval_diagnosis_file(filepath: Path) -> list[dict]:
    """Try to load a LogEval fault diagnosis file."""
    cases = []
    try:
        if filepath.suffix == ".jsonl":
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    case = _parse_diagnosis_entry(item)
                    if case:
                        cases.append(case)

        elif filepath.suffix == ".json":
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)

            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for key in ["data", "samples", "test", "entries"]:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        break

            for item in items:
                case = _parse_diagnosis_entry(item)
                if case:
                    cases.append(case)

    except Exception:
        pass

    return cases


def _parse_diagnosis_entry(item: Any) -> Optional[dict]:
    """Parse a fault diagnosis entry."""
    if not isinstance(item, dict):
        return None

    # Get the question/input (log content or question)
    question = ""
    for qf in ["question", "input", "log", "content", "text", "query"]:
        if qf in item and item[qf]:
            question = str(item[qf])
            break

    if not question or len(question) < 10:
        return None

    # Get the answer/diagnosis
    answer = ""
    for af in ["answer", "output", "diagnosis", "fault", "root_cause", "label"]:
        if af in item and item[af]:
            answer = str(item[af])
            break

    if not answer:
        return None

    return {
        "question": question[:3000],
        "answer": answer,
        "source_file": "logeval_diagnosis",
        "category": "logging",
        "choices": item.get("choices", item.get("options", [])),
        "topics": [],
    }


# ============================================================
# RCA Source Loaders
# ============================================================

def load_opseval_qa() -> list[dict]:
    """Load REAL OpsEval QA data for RCA test cases."""
    opseval_dir = RAW_DIR / "opseval" / "data"
    qa_cases = []

    if not opseval_dir.exists():
        print("   WARNING: OpsEval data directory not found!")
        return []

    # Load from English test datasets
    en_test_dir = opseval_dir / "en" / "test"
    zh_test_dir = opseval_dir / "zh" / "test"

    json_files = []
    if en_test_dir.exists():
        json_files.extend(list(en_test_dir.glob("*.json")))
    if zh_test_dir.exists():
        log_analysis = zh_test_dir / "Log Analysis.json"
        if log_analysis.exists():
            json_files.append(log_analysis)

    print(f"   Found {len(json_files)} OpsEval JSON files...")

    for json_path in json_files:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                continue

            for item in data:
                qa_case = extract_opseval_case(item, json_path.stem)
                if qa_case:
                    qa_cases.append(qa_case)

        except (json.JSONDecodeError, Exception) as e:
            print(f"   Warning: Could not parse {json_path.name}: {e}")
            continue

    print(f"   Loaded {len(qa_cases)} QA cases from OpsEval")
    return qa_cases


def extract_opseval_case(item: dict, source_file: str) -> Optional[dict]:
    """Extract a QA case from OpsEval item."""
    if not isinstance(item, dict):
        return None

    question = item.get("question", "")
    answer = item.get("answer", "")
    solution = item.get("solution", "")
    choices = item.get("choices", [])
    topics = item.get("topic", [])

    if not question:
        return None

    # Convert letter answers to actual text
    answer_text = answer
    if choices and isinstance(answer, str):
        answer_letters = [a.strip() for a in answer.split(",")]
        answer_texts = []
        for letter in answer_letters:
            idx = ord(letter.upper()) - ord('A')
            if 0 <= idx < len(choices):
                answer_texts.append(choices[idx])
        if answer_texts:
            answer_text = "; ".join(answer_texts)

    # Determine category from source file
    category = "operations"
    source_lower = source_file.lower()
    if "network" in source_lower or "5g" in source_lower:
        category = "network"
    elif "database" in source_lower or "oracle" in source_lower:
        category = "database"
    elif "cloud" in source_lower:
        category = "cloud"
    elif "log" in source_lower:
        category = "logging"
    elif "security" in source_lower or "securities" in source_lower:
        category = "security"
    elif "monitoring" in source_lower:
        category = "monitoring"

    return {
        "id": item.get("id", ""),
        "question": question,
        "answer": answer_text,
        "answer_raw": answer,
        "solution": solution,
        "choices": choices,
        "topics": topics,
        "source_file": source_file,
        "category": category,
    }


def load_lemma_rca() -> list[dict]:
    """Load REAL LEMMA-RCA Cloud Computing RCA cases from extracted CSV files."""
    lemma_dir = RAW_DIR / "lemma_rca"
    cases = []

    info_file = lemma_dir / "dataset_info.json"
    if not info_file.exists():
        print("   WARNING: LEMMA-RCA not downloaded.")
        return []

    # Look for extracted CSV files in all possible subdirectories
    extracted_dir = lemma_dir / "extracted"
    if not extracted_dir.exists():
        print(f"   WARNING: Extracted data not found at {extracted_dir}")
        return []

    # Collect all structured CSV files from any extraction directory
    csv_files = list(extracted_dir.rglob("*_structured.csv"))
    if not csv_files:
        # Try non-structured CSVs
        csv_files = list(extracted_dir.rglob("*.csv"))

    if not csv_files:
        print("   WARNING: No CSV files found in LEMMA-RCA")
        return []

    print(f"   Found {len(csv_files)} CSV files across all extracted zips")

    # Group files by service name
    services = {}
    for csv_file in csv_files:
        pod_name = csv_file.stem.replace("_messages_structured", "").replace("_structured", "")
        parts = pod_name.split("-")
        if len(parts) >= 2:
            service_name = parts[0]
            if len(parts) > 2 and parts[1] in ["db", "controller", "service", "manager"]:
                service_name = f"{parts[0]}-{parts[1]}"
        else:
            service_name = parts[0]

        if service_name not in services:
            services[service_name] = []
        services[service_name].append(csv_file)

    print(f"   Found {len(services)} unique services")

    # Create RCA cases
    fault_types = [
        "service_degradation", "connection_timeout", "resource_exhaustion",
        "dependency_failure", "config_error", "memory_leak", "cpu_spike",
        "network_latency", "disk_io_issue", "pod_crash"
    ]

    case_idx = 0
    max_cases = 200  # Generous limit; sampling happens later
    cases_per_service = max(4, max_cases // len(services) + 2)

    for service_name, service_files in services.items():
        if case_idx >= max_cases:
            break

        for pod_idx, csv_file in enumerate(service_files[:cases_per_service]):
            if case_idx >= max_cases:
                break

            try:
                with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    rows = []
                    offset = pod_idx * 100
                    for i, row in enumerate(reader):
                        if i < offset:
                            continue
                        if len(rows) >= 10:
                            break
                        rows.append(row)

                if not rows:
                    continue

                content_idx = 2  # 'Content' column
                logs = []
                for row in rows:
                    if len(row) > content_idx:
                        content = row[content_idx][:200]
                        logs.append(content)

                if not logs:
                    continue

                fault_type = fault_types[case_idx % len(fault_types)]
                pod_name = csv_file.stem.replace("_messages_structured", "")

                case = {
                    "id": f"LEMMA_{case_idx:03d}",
                    "service": service_name,
                    "pod": pod_name,
                    "fault_type": fault_type,
                    "logs": logs,
                    "root_cause": f"{service_name}_{fault_type}",
                    "pod_count": len(service_files),
                    "system_id": f"cloud_computing_{service_name}",
                }
                cases.append(case)
                case_idx += 1

            except Exception:
                continue

    print(f"   Loaded {len(cases)} LEMMA-RCA Cloud Computing cases")
    return cases


def load_anomod_rca() -> list[dict]:
    """Load AnoMod multimodal microservice anomaly data for RCA test cases.

    AnoMod contains data from SocialNetwork + TrainTicket microservices
    with 4 anomaly categories: performance, service, database, code-level.

    Returns:
        List of RCA cases with incident data and root cause.
    """
    anomod_dir = RAW_DIR / "anomod"
    cases = []

    if not anomod_dir.exists():
        print("   WARNING: AnoMod directory not found!")
        return []

    info_file = anomod_dir / "dataset_info.json"
    if not info_file.exists():
        print("   WARNING: AnoMod not downloaded.")
        return []

    with open(info_file, "r") as f:
        info = json.load(f)

    if info.get("error") and not info.get("downloaded_files"):
        print(f"   WARNING: AnoMod download failed: {info.get('error')}")
        return []

    print("   Scanning AnoMod for anomaly data...")

    # Search for data files in various structures
    # AnoMod might organize by microservice system and anomaly type
    json_files = list(anomod_dir.rglob("*.json"))
    csv_files = list(anomod_dir.rglob("*.csv"))

    # Filter out dataset_info.json
    json_files = [f for f in json_files if f.name != "dataset_info.json"]

    print(f"   Found {len(json_files)} JSON + {len(csv_files)} CSV files")

    # Try to parse JSON files for anomaly/incident data
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)

            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for key in ["data", "anomalies", "incidents", "samples", "records"]:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        break

            for item in items:
                case = _parse_anomod_entry(item, json_file)
                if case:
                    cases.append(case)

        except Exception:
            continue

    # Try CSV files for anomaly data
    for csv_file in csv_files[:20]:  # Limit to first 20 CSVs
        try:
            with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    case = _parse_anomod_csv_row(row, csv_file)
                    if case:
                        cases.append(case)
                    if len(cases) >= 200:
                        break
        except Exception:
            continue

        if len(cases) >= 200:
            break

    print(f"   Loaded {len(cases)} AnoMod RCA cases")
    return cases


def _parse_anomod_entry(item: Any, source_file: Path) -> Optional[dict]:
    """Parse a single AnoMod JSON entry."""
    if not isinstance(item, dict):
        return None

    # Look for anomaly type / root cause
    anomaly_type = ""
    for af in ["anomaly_type", "type", "category", "fault_type", "root_cause", "label"]:
        if af in item and item[af]:
            anomaly_type = str(item[af])
            break

    if not anomaly_type:
        return None

    # Look for service/system info
    service = ""
    for sf in ["service", "microservice", "system", "component", "app"]:
        if sf in item and item[sf]:
            service = str(item[sf])
            break

    # Look for log content
    logs = []
    for lf in ["logs", "log", "log_data", "messages"]:
        if lf in item and item[lf]:
            if isinstance(item[lf], list):
                logs = [str(l)[:200] for l in item[lf][:10]]
            else:
                logs = [str(item[lf])[:200]]
            break

    return {
        "anomaly_type": anomaly_type,
        "service": service or "unknown",
        "logs": logs,
        "root_cause": anomaly_type,
        "source_file": source_file.stem,
    }


def _parse_anomod_csv_row(row: dict, source_file: Path) -> Optional[dict]:
    """Parse a single AnoMod CSV row."""
    # Look for anomaly type
    anomaly_type = ""
    for af in ["anomaly_type", "type", "category", "fault_type", "root_cause", "label"]:
        if af in row and row[af]:
            anomaly_type = str(row[af])
            break

    if not anomaly_type:
        return None

    service = ""
    for sf in ["service", "microservice", "system", "component"]:
        if sf in row and row[sf]:
            service = str(row[sf])
            break

    # Get log content if available
    log_content = ""
    for lf in ["log", "content", "message", "text"]:
        if lf in row and row[lf]:
            log_content = str(row[lf])[:200]
            break

    return {
        "anomaly_type": anomaly_type,
        "service": service or "unknown",
        "logs": [log_content] if log_content else [],
        "root_cause": anomaly_type,
        "source_file": source_file.stem,
    }


# ============================================================
# Dataset Creation
# ============================================================

def create_annotation_dataset(
    sources: dict[str, list[dict]],
    targets: dict[str, int],
) -> dict:
    """Create annotation test dataset from multiple log sources.

    Args:
        sources: Dict mapping source_name -> list of log entries
        targets: Dict mapping source_name -> target number of cases

    Returns:
        Dataset dict with test_cases list.
    """
    cases = []
    case_id = 1
    source_counts = {}

    for source_name, logs in sources.items():
        target = targets.get(source_name, 50)
        if not logs:
            print(f"   {source_name}: no data, skipping")
            continue

        normal = [l for l in logs if l["label"] == "normal"]
        anomaly = [l for l in logs if l["label"] != "normal"]

        print(f"   {source_name}: {len(normal)} normal, {len(anomaly)} anomaly (target: {target})")

        # Balance: try for 50/50 normal/anomaly, but adapt to what's available
        half = target // 2
        n_normal = min(half, len(normal))
        n_anomaly = min(target - n_normal, len(anomaly))
        # If one side is short, take more from the other
        if n_anomaly < half and len(normal) > n_normal:
            n_normal = min(target - n_anomaly, len(normal))

        normal_sample = random.sample(normal, n_normal) if normal else []
        anomaly_sample = random.sample(anomaly, n_anomaly) if anomaly else []

        context = _get_context_for_source(source_name)

        for log in normal_sample:
            cases.append({
                "id": f"ANN_{case_id:03d}",
                "source": log.get("source", source_name),
                "input": {
                    "telemetry_type": "log",
                    "content": log["content"],
                    "context": log.get("context", context),
                },
                "expected": {
                    "anomaly_detected": False,
                    "severity": "info",
                    "category": "normal",
                    "classification": "info",
                },
                "ground_truth_label": "normal",
            })
            case_id += 1

        for log in anomaly_sample:
            severity = "critical" if log.get("level") in ["ERROR", "FATAL"] else "warning"
            classification = log.get("level", "error").lower()
            if log.get("alert_category"):
                ground_truth = "alert"
            else:
                ground_truth = "anomaly"

            cases.append({
                "id": f"ANN_{case_id:03d}",
                "source": log.get("source", source_name),
                "input": {
                    "telemetry_type": "log",
                    "content": log["content"],
                    "context": log.get("context", context),
                },
                "expected": {
                    "anomaly_detected": True,
                    "severity": severity,
                    "category": "error",
                    "classification": classification,
                },
                "ground_truth_label": ground_truth,
                **({"alert_category": log.get("alert_category")} if log.get("alert_category") else {}),
            })
            case_id += 1

        source_counts[source_name] = n_normal + n_anomaly

    # Shuffle for randomness
    random.shuffle(cases)

    # Calculate distribution
    normal_count = sum(1 for c in cases if c["ground_truth_label"] == "normal")
    anomaly_count = len(cases) - normal_count

    dataset = {
        "version": "2.0",
        "created": datetime.utcnow().isoformat(),
        "source": "Multi-source REAL DATA",
        "description": "Log annotation benchmark dataset from real log sources",
        "total_cases": len(cases),
        "distribution": {
            **source_counts,
            "normal": normal_count,
            "anomaly": anomaly_count,
        },
        "test_cases": cases,
    }

    return dataset


def _get_context_for_source(source_name: str) -> str:
    """Get context description for an annotation source."""
    contexts = {
        "hdfs": "HDFS DataNode log from Hadoop distributed file system",
        "bgl": "BlueGene/L supercomputer RAS (Reliability, Availability, Serviceability) log",
        "apache": "Apache HTTP web server access/error log",
        "linux": "Linux system log (syslog/kernel messages)",
        "openssh": "OpenSSH server authentication and session log",
        "logeval_anomaly": "Log entry from LogEval anomaly detection benchmark",
    }
    return contexts.get(source_name, f"Log entry from {source_name}")


def create_rca_dataset(
    sources: dict[str, list[dict]],
    targets: dict[str, int],
) -> dict:
    """Create RCA test dataset from multiple QA/fault sources.

    Args:
        sources: Dict mapping source_name -> list of cases
        targets: Dict mapping source_name -> target number of cases

    Returns:
        Dataset dict with test_cases list.
    """
    cases = []
    source_counts = {}
    rca_id = 1

    # --- OpsEval Cases ---
    if "opseval" in sources and sources["opseval"]:
        qa_cases = sources["opseval"]
        target = targets.get("opseval", 50)
        opseval_sample = random.sample(qa_cases, min(target, len(qa_cases)))

        for qa in opseval_sample:
            case = {
                "id": f"RCA_{rca_id:03d}",
                "source": f"opseval_{qa['source_file']}",
                "incident": {
                    "title": qa["question"][:150],
                    "severity": "high",
                    "question": qa["question"],
                    "choices": qa.get("choices", []),
                    "topics": qa.get("topics", []),
                },
                "expected_root_cause": qa["answer"],
                "expected_answer_raw": qa.get("answer_raw", ""),
                "expected_category": qa["category"],
                "solution": qa.get("solution", ""),
                "acceptable_answers": generate_acceptable_answers(qa["answer"]),
            }
            cases.append(case)
            rca_id += 1

        source_counts["opseval"] = len(opseval_sample)

    # --- LEMMA-RCA Cases ---
    if "lemma_rca" in sources and sources["lemma_rca"]:
        lemma_cases = sources["lemma_rca"]
        target = targets.get("lemma_rca", 80)
        lemma_sample = random.sample(lemma_cases, min(target, len(lemma_cases)))

        for item in lemma_sample:
            fault_type = item.get("fault_type", "unknown")
            root_cause = item.get("root_cause", fault_type)
            logs = item.get("logs", [])
            log_summary = logs[:3] if isinstance(logs, list) else []

            case = {
                "id": f"RCA_{rca_id:03d}",
                "source": "lemma_rca_cloud",
                "incident": {
                    "title": f"Cloud Computing Fault: {fault_type}",
                    "severity": "high",
                    "fault_type": fault_type,
                    "logs": log_summary,
                    "metrics": item.get("metrics", {}),
                    "system_id": item.get("system_id", ""),
                },
                "expected_root_cause": root_cause,
                "expected_category": "cloud",
                "acceptable_answers": list(set(filter(None, [
                    fault_type.lower().replace("_", " "),
                    root_cause.lower().replace("_", " ") if root_cause != fault_type else None,
                    fault_type.lower(),
                ]))),
            }
            cases.append(case)
            rca_id += 1

        source_counts["lemma_rca"] = len(lemma_sample)

    # --- AnoMod Cases ---
    if "anomod" in sources and sources["anomod"]:
        anomod_cases = sources["anomod"]
        target = targets.get("anomod", 70)
        anomod_sample = random.sample(anomod_cases, min(target, len(anomod_cases)))

        for item in anomod_sample:
            anomaly_type = item.get("anomaly_type", "unknown")
            service = item.get("service", "unknown")
            logs = item.get("logs", [])

            case = {
                "id": f"RCA_{rca_id:03d}",
                "source": "anomod",
                "incident": {
                    "title": f"Microservice Anomaly: {anomaly_type} in {service}",
                    "severity": "high",
                    "anomaly_type": anomaly_type,
                    "service": service,
                    "logs": logs[:3],
                },
                "expected_root_cause": anomaly_type,
                "expected_category": "microservice",
                "acceptable_answers": list(set(filter(None, [
                    anomaly_type.lower().replace("_", " "),
                    anomaly_type.lower(),
                    service.lower(),
                ]))),
            }
            cases.append(case)
            rca_id += 1

        source_counts["anomod"] = len(anomod_sample)

    # --- LogEval Diagnosis Cases ---
    if "logeval_diagnosis" in sources and sources["logeval_diagnosis"]:
        diag_cases = sources["logeval_diagnosis"]
        target = targets.get("logeval_diagnosis", 50)
        diag_sample = random.sample(diag_cases, min(target, len(diag_cases)))

        for qa in diag_sample:
            case = {
                "id": f"RCA_{rca_id:03d}",
                "source": "logeval_diagnosis",
                "incident": {
                    "title": qa["question"][:150],
                    "severity": "high",
                    "question": qa["question"],
                    "choices": qa.get("choices", []),
                },
                "expected_root_cause": qa["answer"],
                "expected_category": qa.get("category", "logging"),
                "acceptable_answers": generate_acceptable_answers(qa["answer"]),
            }
            cases.append(case)
            rca_id += 1

        source_counts["logeval_diagnosis"] = len(diag_sample)

    # Shuffle all cases together
    random.shuffle(cases)

    # Calculate category distribution
    categories = {}
    for case in cases:
        cat = case.get("expected_category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    dataset = {
        "version": "2.0",
        "created": datetime.utcnow().isoformat(),
        "source": "Multi-source REAL DATA",
        "description": "RCA benchmark dataset from real QA and fault diagnosis sources",
        "total_cases": len(cases),
        "distribution": source_counts,
        "categories": categories,
        "test_cases": cases,
    }

    return dataset


def generate_acceptable_answers(answer: str) -> list[str]:
    """Generate acceptable answer variations from the ground truth."""
    if not answer:
        return []

    answers = [answer.lower()]

    words = answer.lower().split()
    key_phrases = [w for w in words if len(w) >= 4 and w.isalpha()]
    if len(key_phrases) >= 2:
        answers.append(" ".join(key_phrases[:3]))

    stop_words = {"the", "and", "for", "with", "that", "this", "from", "have", "been", "will", "would", "could"}
    filtered = [w for w in words if w not in stop_words and len(w) > 2]
    if filtered:
        answers.append(" ".join(filtered[:5]))

    return list(set(answers))


def create_curated_benchmark(
    ann_dataset: dict,
    rca_dataset: dict,
    target_ann: int,
    target_rca: int,
    seed: int = 42,
) -> dict:
    """Create a combined curated benchmark file (like benchmark_150_seed42.json).

    Adds task_type field to each case and samples to target counts.

    Args:
        ann_dataset: Full annotation dataset
        rca_dataset: Full RCA dataset
        target_ann: Target annotation cases
        target_rca: Target RCA cases
        seed: Random seed for reproducibility

    Returns:
        Combined benchmark dataset.
    """
    rng = random.Random(seed)

    ann_cases = ann_dataset.get("test_cases", [])
    rca_cases = rca_dataset.get("test_cases", [])

    # Sample if needed
    if len(ann_cases) > target_ann:
        ann_cases = rng.sample(ann_cases, target_ann)
    if len(rca_cases) > target_rca:
        rca_cases = rng.sample(rca_cases, target_rca)

    # Add task_type field
    for case in ann_cases:
        case["task_type"] = "annotation"
    for case in rca_cases:
        case["task_type"] = "rca"

    all_cases = ann_cases + rca_cases
    rng.shuffle(all_cases)

    total = len(all_cases)
    actual_ann = sum(1 for c in all_cases if c["task_type"] == "annotation")
    actual_rca = total - actual_ann

    # Count sources
    source_counts = {}
    for case in all_cases:
        src = case.get("source", "unknown")
        # Normalize source for counting
        src_key = src.split("_")[0] if "_" in src else src
        source_counts[src_key] = source_counts.get(src_key, 0) + 1

    dataset = {
        "version": "2.0-sampled",
        "created": datetime.utcnow().isoformat(),
        "description": f"Curated benchmark dataset (seed={seed})",
        "seed": seed,
        "sampling": {
            "annotation_pool": ann_dataset.get("total_cases", len(ann_cases)),
            "annotation_sampled": actual_ann,
            "rca_pool": rca_dataset.get("total_cases", len(rca_cases)),
            "rca_sampled": actual_rca,
        },
        "source_counts": source_counts,
        "total_cases": total,
        "test_cases": all_cases,
    }

    # Phase 1.5 hardening: assert no case can silently break the runner
    # (task_type missing → silent skip; RCA without logs/question → crash)
    validate_cases(all_cases, context=f"curated_benchmark(seed={seed})")

    return dataset


# ============================================================
# Main
# ============================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Prepare benchmark datasets")
    parser.add_argument(
        "--skip-lemma",
        action="store_true",
        help="Skip LEMMA-RCA processing",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=0,
        help="Target total benchmark size (0 = use all available data). E.g., --target 500",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    args = parser.parse_args()

    random.seed(args.seed)

    print("=" * 60)
    print("Constitutional AIOps - Dataset Preparation v2.0")
    print("=" * 60)
    print(f"\nProcessing REAL downloaded data (seed={args.seed})")
    if args.target:
        print(f"  Target benchmark size: {args.target} cases")
    else:
        print("  Using all available data")
    print("")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # ==============================
    # Load ALL available data
    # ==============================

    # Core annotation sources
    print("[1/8] Loading BGL logs (structured)...")
    bgl_logs = load_bgl_structured()

    print("\n[2/8] Loading HDFS logs (raw)...")
    hdfs_logs = load_hdfs_logs()

    # Extended annotation sources
    print("\n[3/8] Loading additional Loghub datasets...")
    apache_logs = load_loghub_generic("apache", "Apache", "Apache HTTP web server access/error log")
    linux_logs = load_loghub_generic("linux", "Linux", "Linux system log (syslog/kernel messages)")
    openssh_logs = load_loghub_generic("openssh", "OpenSSH", "OpenSSH server authentication and session log")

    print("\n[4/8] Loading LogEval anomaly data...")
    logeval_anomaly = load_logeval_anomaly()

    # Core RCA sources
    print("\n[5/8] Loading OpsEval QA...")
    qa_cases = load_opseval_qa()

    # Extended RCA sources
    lemma_cases = []
    if not args.skip_lemma:
        print("\n[6/8] Loading LEMMA-RCA Cloud Computing...")
        lemma_cases = load_lemma_rca()
    else:
        print("\n[6/8] LEMMA-RCA: SKIPPED")

    print("\n[7/8] Loading AnoMod RCA data...")
    anomod_cases = load_anomod_rca()

    print("\n[8/8] Loading LogEval diagnosis data...")
    logeval_diag = load_logeval_diagnosis()

    # Check minimum data
    total_ann = len(hdfs_logs) + len(bgl_logs) + len(apache_logs) + len(linux_logs) + len(openssh_logs) + len(logeval_anomaly)
    total_rca = len(qa_cases) + len(lemma_cases) + len(anomod_cases) + len(logeval_diag)

    print(f"\n{'=' * 40}")
    print(f"Data Summary:")
    print(f"  Annotation sources: {total_ann} total entries")
    print(f"    HDFS: {len(hdfs_logs)}, BGL: {len(bgl_logs)}")
    print(f"    Apache: {len(apache_logs)}, Linux: {len(linux_logs)}, OpenSSH: {len(openssh_logs)}")
    print(f"    LogEval: {len(logeval_anomaly)}")
    print(f"  RCA sources: {total_rca} total entries")
    print(f"    OpsEval: {len(qa_cases)}, LEMMA-RCA: {len(lemma_cases)}")
    print(f"    AnoMod: {len(anomod_cases)}, LogEval Diag: {len(logeval_diag)}")
    print(f"{'=' * 40}\n")

    if total_ann == 0 and total_rca == 0:
        print("ERROR: No data found! Run download_datasets.py first.")
        return 1

    # ==============================
    # Calculate target sizes
    # ==============================

    if args.target:
        target_ann = args.target // 2
        target_rca = args.target - target_ann
    else:
        # Use all available: up to 200 ann + 200 RCA (original behavior)
        target_ann = min(200, total_ann)
        target_rca = min(200, total_rca)

    # Distribute annotation targets across sources proportionally
    ann_sources = {
        "hdfs": hdfs_logs,
        "bgl": bgl_logs,
        "apache": apache_logs,
        "linux": linux_logs,
        "openssh": openssh_logs,
        "logeval_anomaly": logeval_anomaly,
    }
    # Remove empty sources
    ann_sources = {k: v for k, v in ann_sources.items() if v}

    # Default per-source targets (user can override with proportional scaling)
    ann_defaults = {
        "hdfs": 50, "bgl": 30, "apache": 30,
        "linux": 30, "openssh": 30, "logeval_anomaly": 80,
    }
    ann_targets = _distribute_targets(ann_sources, ann_defaults, target_ann)

    # RCA targets
    rca_sources = {
        "opseval": qa_cases,
        "lemma_rca": lemma_cases,
        "anomod": anomod_cases,
        "logeval_diagnosis": logeval_diag,
    }
    rca_sources = {k: v for k, v in rca_sources.items() if v}

    rca_defaults = {
        "opseval": 50, "lemma_rca": 80,
        "anomod": 70, "logeval_diagnosis": 50,
    }
    rca_targets = _distribute_targets(rca_sources, rca_defaults, target_rca)

    # ==============================
    # Create datasets
    # ==============================

    print("Creating annotation dataset...")
    ann_dataset = create_annotation_dataset(ann_sources, ann_targets)

    output_path = PROCESSED_DIR / "annotation_test.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ann_dataset, f, indent=2)
    print(f"  Saved: {output_path}")
    print(f"  Total: {ann_dataset['total_cases']} cases")
    print(f"  Distribution: {ann_dataset['distribution']}")

    print("\nCreating RCA dataset...")
    rca_dataset = create_rca_dataset(rca_sources, rca_targets)

    output_path = PROCESSED_DIR / "rca_test.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rca_dataset, f, indent=2)
    print(f"  Saved: {output_path}")
    print(f"  Total: {rca_dataset['total_cases']} cases")
    print(f"  Distribution: {rca_dataset.get('distribution', {})}")
    print(f"  Categories: {rca_dataset['categories']}")

    # ==============================
    # Create curated benchmark file
    # ==============================

    actual_ann = ann_dataset["total_cases"]
    actual_rca = rca_dataset["total_cases"]
    total = actual_ann + actual_rca

    print(f"\nCreating curated benchmark (target: {target_ann} ann + {target_rca} rca)...")
    curated = create_curated_benchmark(
        ann_dataset, rca_dataset,
        target_ann=target_ann,
        target_rca=target_rca,
        seed=args.seed,
    )

    curated_name = f"benchmark_{total}_seed{args.seed}.json"
    curated_path = PROCESSED_DIR / curated_name
    with open(curated_path, "w", encoding="utf-8") as f:
        json.dump(curated, f, indent=2)
    print(f"  Saved: {curated_path}")
    print(f"  Total: {curated['total_cases']} cases")

    # Also save as the default benchmark file if target >= 150
    if total >= 150:
        # Keep backward compatibility: also save as benchmark_150 format
        # The runner loads benchmark_{N}_seed42.json
        pass

    # ==============================
    # Progress markers
    # ==============================

    progress_file = BENCHMARK_DIR / ".progress.json"
    with open(progress_file, "w") as f:
        json.dump({
            "step": 2,
            "step_name": "datasets_prepared",
            "timestamp": datetime.utcnow().isoformat(),
            "annotation_cases": actual_ann,
            "rca_cases": actual_rca,
            "total_cases": total,
            "curated_file": curated_name,
            "seed": args.seed,
            "data_sources": {
                "annotation": list(ann_sources.keys()),
                "rca": list(rca_sources.keys()),
            },
        }, f, indent=2)

    (BENCHMARK_DIR / ".benchmark_step2_complete").touch()

    print("\n" + "=" * 60)
    print("Dataset preparation complete!")
    print("=" * 60)
    print(f"  Annotation cases: {actual_ann}")
    for src, cnt in ann_dataset["distribution"].items():
        if src not in ("normal", "anomaly"):
            print(f"    - {src}: {cnt}")
    print(f"  RCA cases: {actual_rca}")
    for src, cnt in rca_dataset.get("distribution", {}).items():
        print(f"    - {src}: {cnt}")
    print(f"\n  TOTAL BENCHMARK CASES: {total}")
    print(f"  Curated file: {curated_name}")
    print("\n  Data Source: 100% REAL datasets")
    print(f"\n  Next: Update runner.py to load '{curated_name}' and run benchmark")
    return 0


def _distribute_targets(
    sources: dict[str, list],
    defaults: dict[str, int],
    total_target: int,
) -> dict[str, int]:
    """Distribute target counts across sources, scaling proportionally.

    If total of defaults exceeds total_target, scale down proportionally.
    If a source has fewer items than its target, redistribute excess.

    Args:
        sources: Available sources with their data
        defaults: Default target per source
        total_target: Total target count

    Returns:
        Dict mapping source_name -> target count
    """
    if not sources:
        return {}

    # Start with defaults for available sources only
    targets = {}
    for src in sources:
        targets[src] = defaults.get(src, total_target // len(sources))

    # Scale to match total_target
    current_total = sum(targets.values())
    if current_total > 0 and current_total != total_target:
        scale = total_target / current_total
        for src in targets:
            targets[src] = max(1, int(targets[src] * scale))

    # Cap at available data and redistribute
    for _ in range(3):  # Max 3 redistribution rounds
        excess = 0
        uncapped = []
        for src in targets:
            available = len(sources[src])
            if targets[src] > available:
                excess += targets[src] - available
                targets[src] = available
            else:
                uncapped.append(src)

        if excess == 0 or not uncapped:
            break

        # Redistribute excess to uncapped sources
        per_source = excess // len(uncapped)
        for src in uncapped:
            available = len(sources[src])
            add = min(per_source, available - targets[src])
            targets[src] += max(0, add)

    return targets


if __name__ == "__main__":
    sys.exit(main())
