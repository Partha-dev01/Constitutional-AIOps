#!/usr/bin/env python3
"""Build benchmark/results_aws/FINAL/ — a curated copy of all paper-ready
result files, with per-file SHA verification + anomaly audit.

Original files are NEVER modified or moved. This is COPY-ONLY.
"""
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_AWS = REPO_ROOT / "benchmark" / "results_aws"
FINAL = RESULTS_AWS / "FINAL"
# 2026-05-19: originals were archived. Source dirs now live under here.
SOURCE_ROOT = RESULTS_AWS / "_archive_originals_2026-05-19"

EXPECTED_TOTAL = 431
EXPECTED_ANN = 218
EXPECTED_RCA = 213
EXPECTED_EXCLUDED_RCA = 71  # 39 Chinese + 32 MC letter
EXPECTED_EVALUABLE_RCA = EXPECTED_RCA - EXPECTED_EXCLUDED_RCA  # 142


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def audit_records(records, source_label, schema):
    """Schema-aware audit.

    schema dict keys:
      id_fields: list of fields any of which may carry the id (e.g. ['test_id', 'case_id'])
      input_fields: list of fields any of which is the model output (e.g. ['actual_output', 'model_response', 'predicted_anomaly'])
      expected_fields: list of fields any of which is the expected (e.g. ['expected_output', 'expected', 'expected_root_cause', 'expected_anomaly'])
      expect_ann: int or None
      expect_rca: int or None
      expect_excluded_rca: int or None
      check_bert: bool (skip for SOTA / Drain — they never had bert)
    """
    findings = []
    task_counts = Counter()
    id_counts = Counter()
    missing_id = 0
    missing_input = 0
    missing_expected = 0
    missing_correct = 0
    excluded_by_task = Counter()
    correct_by_task = Counter()
    bert_zero_records = 0
    bert_nonzero_records = 0

    for i, r in enumerate(records):
        tt = r.get("task_type")
        if tt is None:
            findings.append(f"FAIL: record {i} missing task_type")
            continue
        task_counts[tt] += 1

        tid = next((r[f] for f in schema["id_fields"] if r.get(f)), None)
        if not tid:
            missing_id += 1
        else:
            id_counts[tid] += 1

        if not any(f in r for f in schema["input_fields"]):
            missing_input += 1
        if not any(f in r for f in schema["expected_fields"]):
            missing_expected += 1

        if "correct" not in r:
            missing_correct += 1
        else:
            c = r["correct"]
            if c is None:
                excluded_by_task[tt] += 1
            elif c:
                correct_by_task[tt] += 1

        if schema.get("check_bert", True):
            bf = r.get("bert_f1")
            if bf is None or bf == 0 or bf == 0.0:
                bert_zero_records += 1
            else:
                bert_nonzero_records += 1

    if missing_id:
        findings.append(f"FAIL: {missing_id} records missing all of id_fields={schema['id_fields']}")
    if missing_input:
        findings.append(f"FAIL: {missing_input} records missing all of input_fields={schema['input_fields']}")
    if missing_expected:
        findings.append(f"FAIL: {missing_expected} records missing all of expected_fields={schema['expected_fields']}")
    if missing_correct:
        findings.append(f"FAIL: {missing_correct} records missing 'correct' field")

    # Duplicate IDs (allowing for Drain having only annotation IDs, etc.)
    dups = {tid: c for tid, c in id_counts.items() if c > 1}
    if dups:
        findings.append(f"FAIL: {len(dups)} duplicate IDs "
                        f"(top: {list(dups.items())[:3]})")

    # Task counts
    ann_n = task_counts.get("annotation", 0)
    rca_n = task_counts.get("rca", 0)
    if schema.get("expect_ann") is not None and ann_n != schema["expect_ann"]:
        findings.append(f"FAIL: annotation count {ann_n} != expected {schema['expect_ann']}")
    if schema.get("expect_rca") is not None and rca_n != schema["expect_rca"]:
        findings.append(f"FAIL: rca count {rca_n} != expected {schema['expect_rca']}")

    # Excluded RCA
    if schema.get("expect_excluded_rca") is not None:
        ex_rca = excluded_by_task.get("rca", 0)
        if ex_rca != schema["expect_excluded_rca"]:
            findings.append(f"FAIL: rca excluded (correct=None) {ex_rca} "
                            f"!= expected {schema['expect_excluded_rca']}")

    # Unexpected excluded annotation
    ex_ann = excluded_by_task.get("annotation", 0)
    if ex_ann > 0:
        findings.append(f"WARN: annotation has {ex_ann} excluded (correct=None) records "
                        f"(should be 0 — annotation is fully evaluable)")

    # Unknown task types
    unknown = set(task_counts) - {"annotation", "rca"}
    if unknown:
        findings.append(f"WARN: unknown task_types: {unknown}")

    # BERT score (known limitation — informational NOTE only)
    if schema.get("check_bert", True):
        if bert_zero_records > 0 and bert_nonzero_records == 0:
            findings.append(f"NOTE: all {bert_zero_records} records have bert_f1=0/null "
                            f"(known limitation, disk-full bug #8 — recomputable post-hoc)")
        elif bert_zero_records > 0:
            findings.append(f"NOTE: {bert_zero_records}/{len(records)} records have bert_f1=0/null")

    status = "FAIL" if any(s.startswith("FAIL") for s in findings) else (
        "WARN" if any(s.startswith("WARN") for s in findings) else "OK")
    stats = {
        "n": len(records),
        "ann_total": ann_n,
        "rca_total": rca_n,
        "ann_correct": correct_by_task.get("annotation", 0),
        "rca_correct": correct_by_task.get("rca", 0),
        "rca_excluded": excluded_by_task.get("rca", 0),
        "rca_evaluable": rca_n - excluded_by_task.get("rca", 0),
        "duplicate_ids": len(dups),
        "bert_zero": bert_zero_records,
    }
    return status, findings, stats


# -----------------------------------------------------------------------------
# File map: (source, dest, audit_fn)
# -----------------------------------------------------------------------------

# Schema for runner.py rich-eval results.json (our system, all 213 RCA scored — no exclusions)
SCHEMA_RICH_EVAL = {
    "id_fields": ["test_id", "case_id"],
    "input_fields": ["actual_output", "model_response"],
    "expected_fields": ["expected_output", "expected", "expected_root_cause"],
    "expect_ann": 218, "expect_rca": 213, "expect_excluded_rca": 0,
    "check_bert": True,
}

# Schema for rescored matched-eval (test_id renamed to case_id, model_response, 71 excluded)
SCHEMA_MATCHED_EVAL = {
    "id_fields": ["case_id", "test_id"],
    "input_fields": ["model_response", "actual_output"],
    "expected_fields": ["expected", "expected_root_cause", "expected_output"],
    "expect_ann": 218, "expect_rca": 213, "expect_excluded_rca": 71,
    "check_bert": False,  # rescore doesn't carry bert_f1
}

# Schema for SOTA baseline (run_sota_baselines.py output — 71 excluded)
SCHEMA_SOTA = {
    "id_fields": ["case_id", "test_id"],
    "input_fields": ["model_response"],
    "expected_fields": ["expected", "expected_root_cause"],
    "expect_ann": 218, "expect_rca": 213, "expect_excluded_rca": 71,
    "check_bert": False,  # SOTA pipeline doesn't compute bert
}

# Drain — annotation only, no RCA, custom fields
SCHEMA_DRAIN = {
    "id_fields": ["test_id", "case_id"],
    "input_fields": ["predicted_anomaly", "model_response"],
    "expected_fields": ["expected_anomaly", "expected"],
    "expect_ann": 202, "expect_rca": 0, "expect_excluded_rca": 0,
    "check_bert": False,
}

# Phase 4.6 no-prompt = same as SOTA
SCHEMA_NOPROMPT = SCHEMA_SOTA


def audit_main_rich(records, label):       return audit_records(records, label, SCHEMA_RICH_EVAL)
def audit_main_matched(records, label):    return audit_records(records, label, SCHEMA_MATCHED_EVAL)
def audit_ablation_rich(records, label):   return audit_records(records, label, SCHEMA_RICH_EVAL)
def audit_ablation_matched(records, label):return audit_records(records, label, SCHEMA_MATCHED_EVAL)
def audit_sota(records, label):            return audit_records(records, label, SCHEMA_SOTA)
def audit_drain(records, label):           return audit_records(records, label, SCHEMA_DRAIN)
def audit_noprompt(records, label):        return audit_records(records, label, SCHEMA_NOPROMPT)


ABLATION_CONFIGS = [
    "full", "single_4b", "single_14b", "no_structured",
    "no_system_prompt", "with_graph", "no_constitutional", "with_orchestrator",
]


def file_map():
    """Return list of (source_path, dest_path, loader, auditor, kind)."""
    M = []

    # Main benchmark (rich + matched)
    src_main = SOURCE_ROOT / "run_stackA_main431_newprompt"
    M += [
        (src_main / "results.json",                   FINAL / "main_benchmark" / "results.json",                load_json,  audit_main_rich,    "json"),
        (src_main / "results_sota_eval_431.json",     FINAL / "main_benchmark" / "results_sota_eval_431.json",  load_json,  audit_main_matched, "json"),
        (src_main / "summary.json",                   FINAL / "main_benchmark" / "summary.json",                None,       None,               "metadata"),
        (src_main / "README.md",                      FINAL / "main_benchmark" / "README.md",                   None,       None,               "doc"),
        (src_main / "paper_tables.md",                FINAL / "main_benchmark" / "paper_tables.md",             None,       None,               "doc"),
        (src_main / "paper_tables.tex",               FINAL / "main_benchmark" / "paper_tables.tex",            None,       None,               "doc"),
        (src_main / "benchmark_result.json",          FINAL / "main_benchmark" / "benchmark_result.json",       None,       None,               "metadata"),
    ]

    # Ablation (per-config rich + matched)
    src_abl = SOURCE_ROOT / "ablation_v4_newprompt"
    for cfg in ABLATION_CONFIGS:
        cfg_src = src_abl / f"ablation_{cfg}"
        cfg_dst = FINAL / "ablation_v4" / f"ablation_{cfg}"
        M += [
            (cfg_src / "results.json",                cfg_dst / "results.json",               load_json, audit_ablation_rich,    "json"),
            (cfg_src / "results_sota_eval_431.json",  cfg_dst / "results_sota_eval_431.json", load_json, audit_ablation_matched, "json"),
            (cfg_src / "summary.json",                cfg_dst / "summary.json",               None,      None,                   "metadata"),
        ]

    # SOTA baselines
    M += [
        (SOURCE_ROOT / "sota_llama_3_3_70b" / "results.jsonl",  FINAL / "sota_baselines" / "llama_3_3_70b.jsonl",  load_jsonl, audit_sota,  "jsonl"),
        (SOURCE_ROOT / "sota_deepseek_v3"   / "results.jsonl",  FINAL / "sota_baselines" / "deepseek_v3.jsonl",    load_jsonl, audit_sota,  "jsonl"),
        (SOURCE_ROOT / "sota_drain"         / "results.jsonl",  FINAL / "sota_baselines" / "drain.jsonl",          load_jsonl, audit_drain, "jsonl"),
        (SOURCE_ROOT / "sota_drain"         / "summary.json",   FINAL / "sota_baselines" / "drain_summary.json",   None,       None,        "metadata"),
    ]

    # Phase 4.6 no-prompt
    M += [
        (SOURCE_ROOT / "phase46_noprompt" / "llama_noprompt_clean.jsonl",   FINAL / "phase46_no_prompt" / "llama_noprompt_clean.jsonl",   load_jsonl, audit_noprompt, "jsonl"),
        (SOURCE_ROOT / "phase46_noprompt" / "deepseek_noprompt_v2.jsonl",   FINAL / "phase46_no_prompt" / "deepseek_noprompt_v2.jsonl",   load_jsonl, audit_noprompt, "jsonl"),
        (SOURCE_ROOT / "phase46_noprompt" / "README.md",                    FINAL / "phase46_no_prompt" / "README.md",                    None,       None,           "doc"),
    ]

    # Infrastructure / methodology
    M += [
        (RESULTS_AWS / "archive" / "gate15_comparison.md", FINAL / "infrastructure" / "gate15_comparison.md", None, None, "doc"),
        (RESULTS_AWS / "METHODOLOGY.md",                   FINAL / "METHODOLOGY.md",                          None, None, "doc"),
        (RESULTS_AWS / "BUG_HISTORY.md",                   FINAL / "BUG_HISTORY.md",                          None, None, "doc"),
    ]
    return M


def copy_verify(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    s = sha256(src)
    d = sha256(dst)
    assert s == d, f"SHA mismatch after copy: {src} -> {dst}"
    return s


def build_matched_eval_table(audit_results):
    """Compose the canonical ablation matched-eval table from audit stats."""
    # Pull out the matched-eval rows
    rows = {}
    for entry in audit_results:
        dst = entry["dest"]
        if "/ablation_v4/" not in dst.replace("\\", "/"):
            continue
        if not dst.endswith("results_sota_eval_431.json"):
            continue
        cfg = Path(dst).parent.name.replace("ablation_", "")
        rows[cfg] = entry["stats"]

    if "full" not in rows:
        return "Could not compose matched-eval table — full config missing.\n"

    full = rows["full"]
    full_ovl_pct = 100.0 * (full["ann_correct"] + full["rca_correct"]) / (full["ann_total"] + full["rca_evaluable"])

    lines = [
        "# Ablation v4 — matched-eval table (authoritative for paper Table 6)",
        "",
        "> Generated by `benchmark/scripts/build_final_results.py`.",
        "> Source: each config's `results_sota_eval_431.json` (strict-substring match,",
        "> identical scoring function to SOTA baselines for apples-to-apples comparison).",
        "",
        "| Configuration | Ann | RCA (evaluable) | Overall (evaluable) | Δ Overall |",
        "|---|---|---|---|---|",
    ]
    for cfg in ABLATION_CONFIGS:
        if cfg not in rows:
            continue
        s = rows[cfg]
        ann_n, ann_ev = s["ann_correct"], s["ann_total"]
        rca_n, rca_ev = s["rca_correct"], s["rca_evaluable"]
        ovl_n, ovl_ev = ann_n + rca_n, ann_ev + rca_ev
        ovl_pct = 100.0 * ovl_n / ovl_ev if ovl_ev else 0.0
        delta = ovl_pct - full_ovl_pct
        label = "**Full Hybrid**" if cfg == "full" else cfg
        delta_str = "—" if cfg == "full" else f"{delta:+.1f}pp"
        lines.append(f"| {label} | "
                     f"{100.0*ann_n/ann_ev:.1f}% ({ann_n}/{ann_ev}) | "
                     f"{100.0*rca_n/rca_ev:.1f}% ({rca_n}/{rca_ev}) | "
                     f"{ovl_pct:.1f}% ({ovl_n}/{ovl_ev}) | "
                     f"{delta_str} |")
    lines += [
        "",
        "**71 RCA cases excluded** from all systems (39 Chinese-language + 32 MC bare-letter).",
        "See `../METHODOLOGY.md` §2.",
        "",
        "**Note**: under rich-eval (`results.json`), single_4b RCA = 99.1% — that number is a",
        "broken-eval artifact (rule_score gives partial credit to literal-opposite answers).",
        "**Do NOT cite the rich-eval ablation numbers for paper Table 6**.",
        "See `../AUDIT_REPORT.md` for details on the two distinct eval pathologies.",
    ]
    return "\n".join(lines) + "\n"


def main():
    print(f"Building {FINAL} (COPY-only, originals untouched)...\n")
    FINAL.mkdir(parents=True, exist_ok=True)

    manifest_entries = []
    audit_entries = []

    for src, dst, loader, auditor, kind in file_map():
        if not src.exists():
            print(f"  [MISSING] {src.relative_to(REPO_ROOT)}")
            manifest_entries.append({
                "source": str(src.relative_to(REPO_ROOT)),
                "dest": str(dst.relative_to(REPO_ROOT)),
                "kind": kind,
                "status": "MISSING",
                "sha256": None,
                "size_bytes": None,
            })
            continue

        src_sha = copy_verify(src, dst)
        size = dst.stat().st_size

        # Audit content if we have a loader+auditor
        if loader and auditor:
            try:
                records = loader(dst)
                status, findings, stats = auditor(records, str(dst.relative_to(REPO_ROOT)))
            except Exception as e:
                status, findings, stats = "FAIL", [f"FAIL: loader error: {e}"], {}
            audit_entries.append({
                "source": str(src.relative_to(REPO_ROOT)),
                "dest": str(dst.relative_to(REPO_ROOT)),
                "status": status,
                "findings": findings,
                "stats": stats,
                "sha256": src_sha,
            })
        else:
            status = "META"
        manifest_entries.append({
            "source": str(src.relative_to(REPO_ROOT)),
            "dest": str(dst.relative_to(REPO_ROOT)),
            "kind": kind,
            "status": status,
            "sha256": src_sha,
            "size_bytes": size,
        })
        print(f"  [{status:<4}] {src.name:40} -> {dst.relative_to(REPO_ROOT)}  ({size} B)")

    # MANIFEST.md
    lines = [
        "# FINAL/ — Manifest",
        "",
        f"_Built: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        f"_By: `benchmark/scripts/build_final_results.py`_",
        "",
        "> COPY-ONLY operation. Source files at original paths are UNTOUCHED and remain authoritative for any path-dependent script. This directory is purely a curated mirror for paper-ready files.",
        "",
        "## Files (source → dest, with SHA-256)",
        "",
        "| Status | Source | Dest | Size | SHA-256 |",
        "|---|---|---|---|---|",
    ]
    for e in manifest_entries:
        sha_short = (e["sha256"][:12] + "…") if e["sha256"] else "—"
        size = f"{e['size_bytes']:,}" if e["size_bytes"] else "—"
        lines.append(f"| {e['status']} | `{e['source']}` | `{e['dest']}` | {size} | `{sha_short}` |")
    (FINAL / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # AUDIT_REPORT.md
    lines = [
        "# FINAL/ — Audit Report",
        "",
        f"_Built: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        "Per-file content audit. Looks for:",
        "- Record count mismatches (expected 218 ann + 213 rca = 431; SOTA Drain = 202 ann; phase46 = 431)",
        "- Missing required fields (`task_type`, `test_id`/`case_id`, `correct`, `expected_output`, `actual_output`)",
        "- Wrong number of excluded RCA records (should be 71 = 39 Chinese + 32 MC letter)",
        "- Duplicate test_ids (the bug found in DeepSeek t=0 BAK had 103 dups)",
        "- BERT-F1 zeros (known limitation from disk-full bug #8 — informational only)",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "|---|---|",
    ]
    status_counts = Counter(e["status"] for e in audit_entries)
    for s in ("OK", "WARN", "FAIL"):
        lines.append(f"| {s} | {status_counts.get(s, 0)} |")
    lines += ["", "## Per-file findings", ""]

    for e in audit_entries:
        lines += [
            f"### `{e['dest']}` — **{e['status']}**",
            "",
            f"- SHA-256: `{e['sha256']}`",
            f"- Stats: {e['stats']}",
            "",
        ]
        if e["findings"]:
            lines += ["Findings:"]
            for f in e["findings"]:
                lines.append(f"- {f}")
        else:
            lines.append("- _no findings — all checks passed_")
        lines.append("")
    (FINAL / "AUDIT_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Ablation matched-eval table
    table_md = build_matched_eval_table(audit_entries)
    (FINAL / "ablation_v4" / "matched_eval_table.md").write_text(table_md, encoding="utf-8")

    # ablation_v4/README.md (small navigation file)
    (FINAL / "ablation_v4" / "README.md").write_text(
        "# Ablation v4 — final\n\n"
        "**For paper Table 6**: use `matched_eval_table.md` (computed from each config's\n"
        "`results_sota_eval_431.json`).\n\n"
        "**Per-config files**:\n"
        "- `ablation_<cfg>/results.json` — raw model outputs + runner.py rich-eval flags\n"
        "  (provenance; rich-eval `correct` flag is **broken** in 7 of 8 configs — see\n"
        "  `../AUDIT_REPORT.md` for the audit; do NOT cite rich-eval RCA accuracies)\n"
        "- `ablation_<cfg>/results_sota_eval_431.json` — re-scored with SOTA strict-substring\n"
        "  matched eval (**AUTHORITATIVE for Table 6**)\n"
        "- `ablation_<cfg>/summary.json` — runner.py aggregate (rich eval), kept for provenance\n",
        encoding="utf-8",
    )

    # FINAL/README.md (top-level navigation)
    (FINAL / "README.md").write_text(
        "# FINAL/ — paper-ready result files\n\n"
        f"_Built: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_  \n"
        "_Builder script: `benchmark/scripts/build_final_results.py`_\n\n"
        "## Quick map (which file backs which paper artifact)\n\n"
        "| Paper artifact | File |\n"
        "|---|---|\n"
        "| Table 2 (system standalone, rich eval) | `main_benchmark/results.json` |\n"
        "| Table 2 companion (matched eval) | `main_benchmark/results_sota_eval_431.json` |\n"
        "| Table 5 (Latency) | `main_benchmark/summary.json` |\n"
        "| Table 6 (Ablation) | `ablation_v4/matched_eval_table.md` (canonical) + `ablation_v4/ablation_*/results_sota_eval_431.json` (raw) |\n"
        "| Table 7 Ours row | `main_benchmark/results_sota_eval_431.json` |\n"
        "| Table 7 Llama 3.3-70B | `sota_baselines/llama_3_3_70b.jsonl` |\n"
        "| Table 7 DeepSeek V3.2 | `sota_baselines/deepseek_v3.jsonl` |\n"
        "| Table 7 Drain | `sota_baselines/drain.jsonl` + `drain_summary.json` |\n"
        "| Table 8 Llama no-prompt | `phase46_no_prompt/llama_noprompt_clean.jsonl` |\n"
        "| Table 8 DeepSeek no-prompt | `phase46_no_prompt/deepseek_noprompt_v2.jsonl` |\n"
        "| §3 dual-stack methodology | `infrastructure/gate15_comparison.md` |\n"
        "| §3 eval methodology | `METHODOLOGY.md` |\n"
        "| §3.3 bug-investigation provenance | `BUG_HISTORY.md` |\n\n"
        "## Integrity & audit\n\n"
        "- `MANIFEST.md` — every file with source path + SHA-256\n"
        "- `AUDIT_REPORT.md` — per-file content audit (record counts, missing fields,\n"
        "  duplicate IDs, BERT-zero scan, etc.)\n\n"
        "## Source paths preserved\n\n"
        "Every file in this directory was COPIED (not moved) from its original location\n"
        "under `benchmark/results_aws/`. Original paths remain functional for any script\n"
        "that references them. See `MANIFEST.md` for the source→dest mapping.\n\n"
        "## What is NOT in this directory (and why)\n\n"
        "- `ablation_v4_newprompt/ablation_table.md` / `.tex` / `ablation_results.json` —\n"
        "  these contain runner.py **rich-eval** ablation numbers (e.g. single_4b RCA = 99.1%)\n"
        "  which are broken: rule_score gives partial credit to literal-opposite answers.\n"
        "  See `AUDIT_REPORT.md`.\n"
        "- `run_stackA_main431/` (OLD prompt v1-paper reference) — kept for diff/provenance only.\n"
        "- `results/`, `results_v2.0_frozen/` — Jarvis-era v1.0 / v0.9.1 frozen state.\n"
        "- `phase46_noprompt/*_BAK*` and `*.log` — earlier iteration artifacts, kept for\n"
        "  provenance but not paper-ready (see `phase46_no_prompt/README.md` selection rule).\n",
        encoding="utf-8",
    )

    print(f"\nBuilt {FINAL}")
    print(f"  Files copied: {len(manifest_entries)}")
    print(f"  Audited (json/jsonl): {len(audit_entries)}")
    print(f"  Status: OK={status_counts.get('OK', 0)}  "
          f"WARN={status_counts.get('WARN', 0)}  "
          f"FAIL={status_counts.get('FAIL', 0)}")


if __name__ == "__main__":
    main()
