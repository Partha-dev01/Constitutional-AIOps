# Stage 5 — Benchmark Dir Analysis + Topology Proposal

**Generated**: 2026-05-27 (session 28)
**Agent**: Stage 5 (general-purpose, READ-ONLY)
**Status**: COMPLETE — full walk + dependency graph + 7 pain-point classes + 3 topology options + dry-run move plan delivered. archive/ untouched per user standing rule (sampled only the top-level catalog from INDEX.md §2.archive; did not deep-walk).

## §0. One-line state

**423 files / 5 partitions (raw + intermediate + final + scripts + archive) + 2 top-level dotfiles + 3 top-level .md files**;  **6 git-tracked orphan scripts at `scripts/` root** + **3 git-tracked orphan-style scripts in `_dev/` and `ops/`** (NEW since 2026-05-25 INDEX.md was built — sessions 17/21/24 added 9 new "underscore-prefix" one-offs that the old README's 34-script count does NOT reflect); **3 topology options proposed** (A minimal-disturbance, B task-oriented, C flat-then-deep); **RECOMMENDED: Option A** with the targeted enhancements in §6.

## §1. Current state inventory

### §1.1 Walked counts (live, 2026-05-27)

| Partition | INDEX.md (2026-05-25) | Live disk (this walk) | Delta | Source of delta |
|---|---:|---:|---:|---|
| `raw/` | 100 | 100 (sampled top 20 + counted full tree via INDEX) | 0 | gitignored mirror, no changes |
| `intermediate/` | 13 | 13 | 0 | stable |
| `final/` | 64 (excluding session-27 audit dir) | 137 (`find -type f`) | +73 | session-22 + session-27 audit subdir 5-agent reports + Stage-2 16+16 PDF artifacts (`_artifacts/diff_p-*.png`, `_artifacts/main_p-*.png` — 32 PNGs in session27/_artifacts/ alone), plus session 16-27 handoffs (12 new SESSION_*_HANDOFF.md) |
| `scripts/` | 40 (5 sub-folders + 34 .py + 1 README) | **49** (1 README + 1 root `__init__.py` + 6 root orphans + 5 sub-folders × ~8 each, of which 3 are sub-folder-orphans) | **+9** | sessions 17 + 21 + 22 + 24 added: `_apply_d1_result_sync.py`, `_compute_sota_post_relabel.py`, `_probe_format.py`, `_probe_format2.py`, `_verify_a2_apply.py`, `_verify_d1_relabel.py` (at root); `_session21_latency_e2e_no_qa.py`, `_session21_latency_pcts.py`, `flip_qa_mcq_correct_to_null.py`, `group_c_relabel_d1_rich_and_header.py`, `regen_diff_pdf.py` (in `_dev/`); `recompute_bert_f1.py` (in `eval/`); `_idx_build.py`, `_idx_render.py` (in `ops/`) |
| `archive/` | 203 | 203 (NOT deep-walked per user rule; trusted INDEX.md §2.archive) | 0 | preserved-as-is |
| **Top-level `benchmark/`** | 1 (INDEX.md) | **3 .md + 2 dotfiles** (`HANDOFF.md`, `INDEX.md`, `INDEX_BUILD_REPORT.md`, `.benchmark_step2_complete`, `.progress.json`) | +4 | INDEX_BUILD_REPORT.md is new (session 16 deliverable); HANDOFF.md MOVED from repo root in session 22 |
| **TOTAL** | 422 | **~505** | **+83** | most from `final/audit/paper_audit_session{22,27}_*/` + the 32-PNG artifact dir + 9 new scripts |

### §1.2 scripts/ subtree (LIVE, 2026-05-27)

```
benchmark/scripts/
├── README.md            (out-of-date: claims 34 scripts; live count 43 .py)
├── __init__.py
├── _apply_d1_result_sync.py        ★ ORPHAN (session 17/18 D-1 re-label)
├── _compute_sota_post_relabel.py   ★ ORPHAN (session 17/18 D-1 verifier)
├── _probe_format.py                ★ ORPHAN (session 17 one-off byte probe)
├── _probe_format2.py               ★ ORPHAN (session 17 one-off round-trip probe)
├── _verify_a2_apply.py             ★ ORPHAN (session 18 verification)
├── _verify_d1_relabel.py           ★ ORPHAN (session 17/18 verification)
├── _dev/
│   ├── __init__.py
│   ├── _session21_latency_e2e_no_qa.py    ★ session-21 prefix-orphan
│   ├── _session21_latency_pcts.py         ★ session-21 prefix-orphan
│   ├── create_nothink_model.py
│   ├── debug_connection.py
│   ├── demo_test.py
│   ├── flip_qa_mcq_correct_to_null.py     ★ NEW (session 22 CRIT-C2 fix; not in scripts/README)
│   ├── group_c_relabel_d1_rich_and_header.py  ★ NEW (session 24; not in scripts/README)
│   ├── regen_diff_pdf.py                  ★ NEW (session 21+; load-bearing; not in scripts/README)
│   ├── smoke_knowledge_query.py
│   ├── test_instruct.py
│   └── (README has 5; live = 10)
├── eval/
│   ├── __init__.py
│   ├── compile_results.py
│   ├── compute_semantic_metrics.py
│   ├── evaluate_results.py
│   ├── export_metrics.py
│   ├── inspect_all_configs.py
│   ├── inspect_single4b.py
│   ├── phase5_stats.py
│   ├── recompute_bert_f1.py              ★ NEW (session 18 D-6; not in scripts/README)
│   ├── rescore_ours_with_sota_eval.py
│   └── verify_authoritative_numbers.py
├── ops/
│   ├── __init__.py
│   ├── _idx_build.py                ★ ORPHAN (session 16 INDEX build helper; lives at root c:/Users/partha/Downloads/... per the build report — but file is actually in scripts/ops/)
│   ├── _idx_render.py               ★ ORPHAN (session 16 INDEX render helper)
│   ├── archive_originals.py
│   ├── build_final_results.py
│   ├── e2e_tests.py
│   └── master_backup_manifest.py
├── prep/
│   ├── __init__.py
│   ├── clean_dataset.py
│   ├── download_datasets.py
│   ├── fix_benchmark_dataset.py
│   ├── mine_apache.py
│   ├── mine_openssh.py
│   ├── mine_opseval.py
│   ├── prepare_datasets.py
│   ├── remove_chinese.py
│   └── vet_labels.py
└── run/
    ├── __init__.py
    ├── run_ablation.py
    ├── run_benchmark.py
    ├── run_drain_baseline.py
    ├── run_graph_experiments.py
    ├── run_sota_baselines.py
    └── test_5plus5.py
```

**Orphan count**: 6 at `scripts/` root + 2 in `_dev/` (`_session21_*`) + 2 in `ops/` (`_idx_*`) = **10 underscore-prefix orphans**. Plus 4 NEW-but-foldered scripts that the README simply doesn't list yet.

### §1.3 final/ subtree (LIVE, 2026-05-27)

```
benchmark/final/
├── AUDIT_REPORT.md, MANIFEST.md, README.md, SUMMARY.md
├── ablation_v4/        (8 ablation_*/ subdirs + matched_eval_table.md + phase5_stats.{json,md} + README)
├── audit/              (sealed forensic + 16 SESSION_*_HANDOFF.md + 2 paper_audit_session{22,27}*/ subdirs + 2 _sessionXX_*_intermediates/ subdirs)
│   ├── CV_PASS1_DISCREPANCIES.md ⚠ sealed
│   ├── CV_PASS2_CODEBASE_AUDIT.md ⚠ sealed
│   ├── FULL_TRANSCRIPT_AUDIT.md ⚠ sealed
│   ├── MASTER_BACKUP_MANIFEST_2026-05-20.json ⚠ sealed
│   ├── REORG_PROPOSAL_2026-05-20.md ⚠ sealed
│   ├── SESSION_12_HANDOFF.md … SESSION_27_HANDOFF.md ⚠ sealed (16 total)
│   ├── SESSION_16_AUDIT_LOST_CHECKLIST.md, SESSION_17_AUDIT_TRIAGE.md, SESSION_17_RECALC_SCOPE.md ⚠ sealed
│   ├── _session11_phase4_orphans/  (phase4_assist.txt + phase4_cmds.txt — historical orphan TXTs)
│   ├── _session12_reorg_intermediates/  (_index_added.txt + _index_deleted.txt — historical intermediates)
│   ├── paper_audit_session22_2026-05-26/  (6 .md files; 5-agent audit synthesis)
│   └── paper_audit_session27_2026-05-26/  (7 .md + 1 .csv + _artifacts/{32 PNGs})
├── docs/   (4 active .md + _archived_session_history/ 3 sealed .md)
├── infrastructure/     (gate15_comparison.md — sole file)
├── main_benchmark/     (7 files: paper_tables.{md,tex} + results.{json,sota_eval} + phase5_stats.json + summary.json + benchmark_result.json + README)
├── phase46_no_prompt/  (deepseek + llama .jsonl + README)
└── sota_baselines/     (deepseek_v3 + drain + drain_summary + llama_3_3_70b)
```

## §2. Dependency graph (path-shaped cross-references)

Methodology: `grep -c "benchmark/"` per .py file (39 .py in scripts/ tree). Files with the most outgoing edges (i.e., most fragile to a reorg) are at the top. Total path-shaped references captured: **188 occurrences across 39 files** (.py only). Full cap of top references at ~50 below; rest are similar-pattern in-line use of one of the canonical roots.

### §2.1 Outgoing-edge density (per Python script)

| Source file | benchmark/ refs | Target partitions | Risk if path-string breaks |
|---|---:|---|---|
| `scripts/ops/_idx_build.py` | 22 | `final/audit/`, `raw/`, `intermediate/`, `archive/`, `scripts/` (mapping rules) | MEDIUM — orphan, not in active eval gate; but is the regen helper |
| `scripts/eval/recompute_bert_f1.py` | 18 | `final/main_benchmark/`, `final/ablation_v4/`, `final/sota_baselines/`, `final/phase46_no_prompt/` | **HIGH** — touches all 14 paper-evidence result files; load-bearing |
| `scripts/_apply_d1_result_sync.py` | 15 | `final/main_benchmark/`, `final/ablation_v4/`, `intermediate/datasets/` | **HIGH** — orphan but touches 16 result files; canonical D-1 re-label applier |
| `scripts/ops/archive_originals.py` | 16 | `archive/originals_2026-05-19/`, `archive/originals_backup_2026-05-19.zip` | MEDIUM — historical, already-ran |
| `scripts/_verify_a2_apply.py` | 15 | `final/main_benchmark/`, `final/ablation_v4/` (and git HEAD for diff) | MEDIUM — verification orphan |
| `scripts/_dev/flip_qa_mcq_correct_to_null.py` | 13 | `final/main_benchmark/`, `final/ablation_v4/`, `final/phase46_no_prompt/`, `final/sota_baselines/` | **HIGH** — load-bearing; restores 74-excluded invariant across 13 files |
| `scripts/ops/build_final_results.py` | 12 | `archive/originals_2026-05-19/`, `final/`, `final/audit/MANIFEST.md` | MEDIUM — historical, may run again |
| `scripts/ops/_idx_render.py` | 12 | `final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json`, `final/audit/REORG_PROPOSAL_2026-05-20.md` | LOW — orphan render helper |
| `scripts/run/test_5plus5.py` | 9 | `intermediate/datasets/`, `final/main_benchmark/` | MEDIUM |
| `scripts/run/run_sota_baselines.py` | 9 | `intermediate/datasets/`, `final/sota_baselines/` | MEDIUM — paper-evidence runner |
| `scripts/eval/export_metrics.py` | 7 | `final/main_benchmark/`, `final/ablation_v4/` | MEDIUM |
| `scripts/run/run_graph_experiments.py` | 6 | `final/phase45_graph/` (output) | MEDIUM |
| `scripts/prep/vet_labels.py` | 6 | `intermediate/candidates/` | MEDIUM |
| `scripts/eval/rescore_ours_with_sota_eval.py` | 6 | `intermediate/datasets/excluded_rca_cases.json` | MEDIUM — paper-evidence producer |
| `scripts/eval/phase5_stats.py` | 6 | `final/ablation_v4/`, `final/main_benchmark/` | MEDIUM |
| `scripts/run/run_ablation.py` | 5 | `final/ablation_v4/` (write) | MEDIUM |
| `scripts/prep/mine_*` | 4-5 | `raw/loghub/`, `intermediate/candidates/` | MEDIUM |
| `scripts/prep/download_datasets.py` | 5 | `raw/` | MEDIUM |
| `scripts/run/run_drain_baseline.py` | 4 | `intermediate/datasets/`, `final/sota_baselines/` | MEDIUM |
| `scripts/run/run_benchmark.py` | 3 | `intermediate/datasets/`, `final/main_benchmark/` | MEDIUM |
| `scripts/prep/prepare_datasets.py` | 3 | `intermediate/datasets/`, `raw/` | MEDIUM |
| `scripts/eval/compute_semantic_metrics.py` | 3 | `archive/run_stackA_main431_OLD_PROMPT/` (docstring example), input/output args | LOW — args, no hardcoded read |
| `scripts/ops/master_backup_manifest.py` | 3 | `final/audit/MASTER_BACKUP_MANIFEST_*.json` (write) | LOW |
| `scripts/ops/e2e_tests.py` | 2 | (mostly imports) | LOW |
| `scripts/eval/inspect_all_configs.py` | 1 | `final/ablation_v4/` (via `parents[3] / "benchmark/final/ablation_v4"`) | LOW |
| `scripts/eval/verify_authoritative_numbers.py` | 1 | `final/` | LOW |
| `scripts/eval/compile_results.py` | 1 | docstring only | LOW |

### §2.2 Cross-script imports (high-criticality)

Per `scripts/README.md` §"Cross-script dependencies" (still accurate as of 2026-05-27 walk):

| Importer | Importee | Mechanism |
|---|---|---|
| `eval/rescore_ours_with_sota_eval.py` | `run/run_sota_baselines.py` | `importlib.util.spec_from_file_location` HARDCODED PATH — **moves break silently** |
| `ops/e2e_tests.py` | `run/run_benchmark.py` | `from benchmark.scripts.run.run_benchmark import BenchmarkRunner, MODELS, LatencyCompensatedClient` |
| `ops/e2e_tests.py` | `eval/export_metrics.py` | `from benchmark.scripts.eval.export_metrics import …` |
| `run/run_ablation.py` | `eval/export_metrics.py` | `from benchmark.scripts.eval.export_metrics import export_all` |
| (None) | `scripts/_apply_d1_result_sync.py`, `_compute_sota_post_relabel.py`, `_verify_*`, `_probe_format*`, `_session21_*`, `_idx_*`, `flip_qa_mcq_*`, `group_c_relabel_*`, `regen_diff_pdf.py`, `recompute_bert_f1.py` | **NO imports** — pure one-off scripts |

### §2.3 Incoming references to scripts/ (reverse-lookup; non-Python doc refs)

| Target script | Referenced from (file:context) |
|---|---|
| `scripts/ops/master_backup_manifest.py` | `INDEX.md:7`, `INDEX_BUILD_REPORT.md:7`, `final/audit/CV_PASS2_CODEBASE_AUDIT.md` (sealed) |
| `scripts/eval/verify_authoritative_numbers.py` | `scripts/README.md:109`, `final/SUMMARY.md` (around line 70), `REORG_PROPOSAL_2026-05-20.md:130` |
| `scripts/eval/inspect_all_configs.py` | `scripts/README.md:109`, `final/SUMMARY.md:70`, `REORG_PROPOSAL_2026-05-20.md:131` |
| `scripts/eval/phase5_stats.py` | `scripts/README.md:65` (own description) |
| `scripts/eval/export_metrics.py` | `scripts/README.md:68` (own description), `run/run_ablation.py:408` |
| `scripts/run/run_*` | `scripts/README.md` (own descriptions), various session handoff docs |
| `scripts/ops/build_final_results.py` | `scripts/README.md:74`, `final/SUMMARY.md:72` |
| `scripts/_dev/regen_diff_pdf.py` | `MEMORY.md` hard rule ("DIFF regen via `regen_diff_pdf.py`") + multiple session handoffs |
| `scripts/_dev/recompute_bert_f1.py` (note: actually in eval/) | `SUMMARY.md` D-6 narrative |

## §3. Pain points identified

### §3.1 Orphan scripts at scripts/ root (6 files; all git-tracked)

Underscore-prefix scripts that escaped the 5-subfolder convention. All are session-17/18 D-1 re-label one-offs that never got moved into `_dev/`. Each is fully self-contained (no imports from other scripts) with hardcoded absolute paths into `final/`.

| Path | Lines | Session | Purpose | Proposed home |
|---|---:|---|---|---|
| `scripts/_apply_d1_result_sync.py` | 139 | 17/18 | D-1 re-label applier (16 result files) | `scripts/_dev/` (one-off audit fix) |
| `scripts/_compute_sota_post_relabel.py` | 64 | 17/18 | D-1 verification stats | `scripts/_dev/` |
| `scripts/_probe_format.py` | 67 | 17 | Byte-level probe before re-apply | `scripts/_dev/` |
| `scripts/_probe_format2.py` | 60 | 17 | Round-trip probe (idempotency check) | `scripts/_dev/` |
| `scripts/_verify_a2_apply.py` | 133 | 18 | Structural diff vs git HEAD for D-1 | `scripts/_dev/` |
| `scripts/_verify_d1_relabel.py` | 67 | 17/18 | Re-label byte-diff verifier | `scripts/_dev/` |

**Aggregate**: 530 lines of orphan, 6 files, all `_dev/` candidates. Zero are referenced from scripts/README.md (still lists 34 scripts vs live 43).

### §3.2 final/intermediate/raw boundary fuzziness

The 5-partition rule (raw = third-party untouched; intermediate = processed JSON; final = paper-ready; archive = superseded; scripts = code) is mostly clean. Edge cases:

1. **`raw/apache_candidates.jsonl` + `raw/openssh_candidates.jsonl` + `raw/opseval_remine_s2.jsonl`** are byte-identical (or near-) to their `intermediate/candidates/` counterparts (`apache_candidates.jsonl`, `openssh_candidates.jsonl`, `opseval_remine.jsonl`). INDEX.md §2.raw line 31+48 explicitly labels these "raw mining output (gitignored mirror of intermediate/candidates/)". This **violates** the raw-is-third-party rule — the mining scripts (`prep/mine_*.py`) write into `intermediate/candidates/` per scripts/README §2 "Output write-paths". The `raw/` copies appear to be **stale, pre-reorg mirrors** that should be archived. SHA-12 comparison from INDEX confirms `raw/apache_candidates.jsonl 268999cfb202` matches `intermediate/candidates/apache_candidates.jsonl 268999cfb202` byte-for-byte. **Recommendation**: move the 3 mirror JSONLs to `archive/originals_2026-05-19/raw_pre_reorg/` (or similar) and add a README note. This is an automation gap, not a deletion candidate — preserves audit trail.
2. **`intermediate/datasets/annotation_clean.json` + `rca_clean.json`** are products of `prep/clean_dataset.py` (early-stage), while **`benchmark_400_seed42.json` + `benchmark_431_seed42.json` + `benchmark_150_seed42*.json` + `annotation_test.json` + `rca_test.json` + `excluded_rca_cases.json`** are later-stage outputs of `prepare_datasets.py` + manual exclusions. The `intermediate/datasets/` directory mixes 3 stages: cleaned (4 files), pre-final benchmark builds (3 files for n=150/400/431), and metadata (1 excluded_rca_cases.json). A future maintainer would not be able to tell from the directory alone which subset is the **canonical paper-evidence input**. **Minor**, no immediate move; could be solved by a one-line README annotation flagging `benchmark_431_seed42.json` as canonical.
3. **`final/main_benchmark/results.json` (rich-eval)** vs **`final/main_benchmark/results_sota_eval_431.json` (matched-eval, paper-canonical)**: both live in the same directory with similar names; only the SUMMARY.md / AUDIT_REPORT.md prose distinguishes "provenance only" from "paper-authoritative". The pattern repeats across all 8 `ablation_v4/ablation_*/` subdirs. Reviewer-confusing. **Minor**; partial mitigation in current setup is the AUDIT_REPORT annotation. Better: a `.canonical` symlink or `CANONICAL` marker file beside the `results_sota_eval_431.json`.
4. **`final/infrastructure/gate15_comparison.md`** is a 1-file folder. INDEX.md labels it "dual-stack gate evidence (§3)". One-file folders are smells; could plausibly live in `final/docs/` next to METHODOLOGY.md without losing semantics. **Minor**.

### §3.3 Duplicate / near-duplicate files

1. The 3 raw/intermediate candidates pairs (§3.2 item 1).
2. **`scripts/__init__.py`** (28 B) and **`scripts/{prep,run,eval,ops,_dev}/__init__.py`** (1 B each) — 6 package markers, intentional, not duplicates per se but worth listing.
3. **`final/MANIFEST.md` (8.7 KB)** vs **`final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json` (98.7 KB)** vs **`INDEX.md` (~25 KB)**: all 3 are "file inventory + SHA" documents but at different scopes. INDEX.md is the master, MANIFEST.md is the 47-file paper-evidence sub-set, MASTER_BACKUP_MANIFEST is the 493-file pre-reorg dump. Overlap is **intentional**; flagged here for completeness only.
4. **`final/AUDIT_REPORT.md` (10.4 KB)** is a per-file content audit of 23 files — single-purpose, no duplicate elsewhere.
5. **`scripts/eval/evaluate_results.py`** (historical, 8.9 KB) is fully superseded by the `rescore_ours_with_sota_eval.py` + `phase5_stats.py` pipeline per scripts/README §3 row 1. Could be moved to `scripts/_dev/` (preserves git history, removes confusion from active eval folder).
6. **`scripts/prep/fix_benchmark_dataset.py`** (historical, 2.3 KB) + **`prep/remove_chinese.py`** (historical, 4.9 KB) similarly are session-1-era one-offs. Live in `prep/` but flagged "historical" in README. Could be moved to `scripts/_dev/`.

### §3.4 Naming inconsistencies

| Pattern | Examples | Issue | Recommended |
|---|---|---|---|
| Underscore-prefix orphan | `_apply_d1_result_sync.py`, `_idx_build.py`, `_session21_latency_*.py` | Convention is ambiguous: at root = "orphan to triage" or "private helper to move to `_dev/`"? README doesn't define. | Adopt: underscore-prefix = "session-NN one-off, lives in `_dev/`". Anything load-bearing gets a real verb_noun.py name in prep/run/eval/ops. |
| `phase4*` vs `phase46_*` vs `phase45_*` | `final/phase46_no_prompt/`, `final/phase45_graph/` (referenced but not yet on disk — output dir), `audit/_session11_phase4_orphans/` | Inconsistent zero-padding: phase45 vs phase46 vs phase4. (Per the paper § numbering, these correspond to §4.5 / §4.6.) | Acceptable as-is since they map to paper section numbers; document the convention in `final/README.md`. |
| `_session11_phase4_orphans/` + `_session12_reorg_intermediates/` (under `final/audit/`) | These two underscored sub-folders contain intermediate text artifacts kept for forensic record. Convention overlaps with `final/docs/_archived_session_history/` and `paper_audit_session{22,27}_2026-05-26/`. | 3 different ways to encode "session-NN archive" under one dir. | Standardize on `paper_audit_session<NN>_<YYYY-MM-DD>/` for future audit outputs; leave the 2 sealed-forensic underscore-folders as-is. |
| Hyphen vs underscore in folder names | `_archived_session_history/` (under_score) vs no hyphen-case in benchmark/ tree | Consistent — snake_case for code + dirs, kebab-case nowhere. Per repo CLAUDE.md §"File Conventions" snake_case is correct for Python. | OK as-is. |
| Prefix-NN.md for audit reports | `paper_audit_session22_2026-05-26/00_SUMMARY.md` + `01_…` + `02_…` (numbered) vs `paper_audit_session27_2026-05-26/01_references_inventory_report.md` + `01_xlsx_delta_proposal.csv` + `02_…` + `03_…` + `04_…` + `05_audit_history_timeline.md` + `05_open_items_checklist.md` (some collide on `01_` and `05_`) | Session 22 used 00 to 05 (one per agent); session 27 mixes 01_ in two files (`01_references_inventory_report.md` + `01_xlsx_delta_proposal.csv`) and 05_ in two files. Not strictly broken but visually ambiguous. | Session 28 can stick to a single-stage-per-prefix convention going forward. |

### §3.5 Cross-partition path fragility (HIGH-RISK fragile paths)

Scripts that hardcode absolute or repo-relative `benchmark/...` strings rather than computing them relative to `__file__` location. If reorg moves the target, these break silently or with import error.

| Script | Fragile pattern | Severity |
|---|---|---|
| `scripts/_apply_d1_result_sync.py` (FILES list, lines 18-38) | 16 hardcoded `'benchmark/final/...'` tuples | **HIGH** — if any `final/` subdir moves, script breaks |
| `scripts/_dev/flip_qa_mcq_correct_to_null.py` | Similar hardcoded path list of 13 files | **HIGH** |
| `scripts/eval/recompute_bert_f1.py` (FILES list, lines 35-50) | 14 hardcoded `'benchmark/final/...'` tuples | **HIGH** |
| `scripts/eval/rescore_ours_with_sota_eval.py:74` | `REPO_ROOT / "benchmark/intermediate/datasets/excluded_rca_cases.json"` default — REPO_ROOT computed via `Path(__file__).resolve().parents[N]`, brittle if file moves between sub-folder depths | MEDIUM |
| `scripts/eval/inspect_all_configs.py:6` | `Path(__file__).resolve().parents[3] / "benchmark/final/ablation_v4"` — count `parents[3]` would break if script depth changes | **HIGH** (depth-coupled) |
| `scripts/_dev/_session21_latency_*.py` | Windows raw-string absolute paths (`r"c:\Users\partha\Downloads\..."`) | LOCK-IN: hard-coded to one operator's laptop. **HIGH** if anyone else runs them. |
| `scripts/ops/_idx_build.py:4` | Absolute path `c:/Users/partha/Downloads/files AIOPS NEW/...` | LOCK-IN to one laptop |
| `scripts/ops/_idx_render.py:5` | Absolute path `c:/Users/partha/Downloads/files AIOPS NEW/_index_render.txt` (note: this is OUTSIDE benchmark/) | LOCK-IN |

**Counter-pattern (well-behaved)**: `scripts/eval/inspect_all_configs.py` mostly uses `parents[3]` relative to its own location; `scripts/run/run_*` use argparse defaults so paths are explicit.

### §3.6 docs/ vs audit/ vs top-level md sprawl

Markdown files live in 5+ "doc-like" locations:

| Location | Files | Role |
|---|---:|---|
| `benchmark/` (top-level) | 3 (`HANDOFF.md`, `INDEX.md`, `INDEX_BUILD_REPORT.md`) | Navigation entry-points |
| `benchmark/final/` (top-level) | 4 (`AUDIT_REPORT.md`, `MANIFEST.md`, `README.md`, `SUMMARY.md`) | Paper-evidence summary |
| `benchmark/final/docs/` | 4 active (`BROKEN_ABLATIONS.md`, `BUG_HISTORY.md`, `CURRENT_RUNS.md`, `METHODOLOGY.md`) | Runbooks |
| `benchmark/final/docs/_archived_session_history/` | 3 sealed (`FILE_PROVENANCE.md`, `RESULTS_SUMMARY.md`, `RUNS_INDEX.md`) | Old session 9 history |
| `benchmark/final/audit/` | 16 sealed (CV_PASS1/2, FULL_TRANSCRIPT, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, all SESSION_NN_HANDOFF) + 3 historical (SESSION_16_AUDIT_LOST_CHECKLIST + SESSION_17_AUDIT_{TRIAGE,RECALC_SCOPE}) | Forensic + handoffs |
| `benchmark/final/audit/paper_audit_session{22,27}_*/` | 6 + 7 = 13 .md per-stage audit reports | Multi-agent audit outputs |
| `benchmark/raw/README.md`, `intermediate/README.md`, `scripts/README.md`, `archive/README.md`, plus per-subdir `README.md` files in `final/{ablation_v4,main_benchmark,phase46_no_prompt}/` | 9 READMEs | Partition + subdir narratives |

Observations:
- **`final/audit/` is loaded** (39 files, mix of sealed forensic + active session handoffs + multi-agent paper audit subdirs). Per user rule, do NOT propose splitting. But the implicit categorization (sealed vs active-handoff vs paper-audit-subdir) is not made explicit by file naming. The 3 `SESSION_17_*.md` siblings (HANDOFF + AUDIT_TRIAGE + RECALC_SCOPE) are an exception that proves the rule.
- **`final/docs/`** vs **`final/audit/`**: clear convention — docs/ = active runbook/methodology, audit/ = forensic + handoff. OK.
- **`benchmark/` top-level 3 .md**: `INDEX.md` (master file index) + `HANDOFF.md` (project-handoff) + `INDEX_BUILD_REPORT.md` (one-time build report for INDEX.md). The third is conceptually a session-16 audit artifact; arguably belongs at `final/audit/SESSION_16_INDEX_BUILD_REPORT.md`. **Minor mismatch**.

### §3.7 INDEX.md / SUMMARY.md / MANIFEST.md / HANDOFF.md overlap

| Doc | Purpose | Scope | Verdict |
|---|---|---|---|
| `benchmark/INDEX.md` | Master file index (422 files) with role/status/SHA/mtime/delta | EVERY file under benchmark/ | Single purpose — well-bounded ✅ |
| `benchmark/HANDOFF.md` | Agent-handoff: AWS state, paper edit target, hard rules, mandatory reads | Project narrative | Single purpose — overlaps only with MEMORY.md (intentional, MEMORY.md is auto-loaded) ✅ |
| `benchmark/INDEX_BUILD_REPORT.md` | Build-time report for INDEX.md | Session-16 one-off | **Could be moved** → `final/audit/SESSION_16_INDEX_BUILD_REPORT.md` (Minor §3.6 item) |
| `benchmark/final/SUMMARY.md` | Results landscape + Phase 5 narrative + ablation table | Paper-evidence numbers | Single purpose ✅ |
| `benchmark/final/MANIFEST.md` | 47-file FINAL build manifest with SHAs | Paper-evidence sub-set | Single purpose ✅ |
| `benchmark/final/AUDIT_REPORT.md` | Schema-aware content audit of 23 files | Paper-evidence sub-set | Single purpose ✅ |
| `benchmark/final/README.md` | partition entry-point | partition narrative | Single purpose ✅ |
| `benchmark/scripts/README.md` | 34-script breakdown by sub-folder | scripts/ tree | **Stale** (live = 43, README = 34) — fixable with a re-render, no move needed |

No deletion-grade overlap. `INDEX_BUILD_REPORT.md` is the lone misplaced file.

## §4. Proposed topology options

### Option A — Minimal-disturbance (preserve 5-partition, tighten edges)

**Rationale**: The current 5-partition layout (raw / intermediate / final / scripts / archive) is paper-defensibly clean, has been verified twice (sessions 12 and 16), and is recognized in MEMORY.md + HANDOFF.md + INDEX.md + all 16 session handoffs. Sessions 22 and 27 added multi-agent audit subdirs cleanly under `final/audit/paper_audit_session{NN}_*/`. The pain points are mostly **drift since 2026-05-20** (new scripts not foldered + 3 raw/ stale mirrors + 1 misplaced .md), not structural mis-design. Option A captures those low-cost fixes without disturbing any of the load-bearing path strings in 39 .py files.

**Target tree**:

```
benchmark/                                  (5 partitions + 2 top-level .md + 2 sentinels)
├── HANDOFF.md
├── INDEX.md
├── .benchmark_step2_complete               (sentinel; leave)
├── .progress.json                          (sentinel; leave)
├── raw/                                    (97 files; deep mirror UNCHANGED — gitignored)
│   ├── README.md
│   ├── loghub/                             ← UNCHANGED
│   ├── lemma_rca/                          ← UNCHANGED
│   └── opseval/                            ← UNCHANGED
│   (3 stale candidate JSONLs MOVED OUT to archive/raw_pre_reorg_mirrors/)
├── intermediate/                           (13 files UNCHANGED)
│   ├── README.md
│   ├── candidates/  (3 .jsonl)
│   └── datasets/    (9 .json)
├── final/                                  (137 files; UNCHANGED in this option; only tighten internal annotations)
│   ├── README.md, MANIFEST.md, SUMMARY.md, AUDIT_REPORT.md
│   ├── ablation_v4/, main_benchmark/, phase46_no_prompt/, sota_baselines/, infrastructure/
│   ├── docs/   (4 active + 3 sealed history)
│   └── audit/  (sealed + handoffs + paper_audit_session{22,27}/)
├── scripts/                                (49 files; folder all 6 root orphans into _dev/; new README count = 43)
│   ├── README.md                           ← REGEN (34→43, add new sections)
│   ├── __init__.py
│   ├── prep/   (9 .py + __init__.py)       UNCHANGED
│   ├── run/    (6 .py + __init__.py)       UNCHANGED
│   ├── eval/   (10 .py + __init__.py)      UNCHANGED (recompute_bert_f1.py belongs here ✓)
│   ├── ops/    (5 .py + __init__.py)       ← _idx_build.py + _idx_render.py STAY (they're ops/build helpers)
│   └── _dev/   (13 .py + __init__.py)      ← +6 root orphans moved IN
└── archive/                                (205+ files; +3 raw_pre_reorg_mirrors/, otherwise UNCHANGED per user rule)
```

**Concrete moves** (10 total):

1. `scripts/_apply_d1_result_sync.py` → `scripts/_dev/_apply_d1_result_sync.py`
2. `scripts/_compute_sota_post_relabel.py` → `scripts/_dev/_compute_sota_post_relabel.py`
3. `scripts/_probe_format.py` → `scripts/_dev/_probe_format.py`
4. `scripts/_probe_format2.py` → `scripts/_dev/_probe_format2.py`
5. `scripts/_verify_a2_apply.py` → `scripts/_dev/_verify_a2_apply.py`
6. `scripts/_verify_d1_relabel.py` → `scripts/_dev/_verify_d1_relabel.py`
7. `raw/apache_candidates.jsonl` → `archive/raw_pre_reorg_mirrors/apache_candidates.jsonl` (3-byte-identical mirror of intermediate/candidates/)
8. `raw/openssh_candidates.jsonl` → `archive/raw_pre_reorg_mirrors/openssh_candidates.jsonl`
9. `raw/opseval_remine_s2.jsonl` → `archive/raw_pre_reorg_mirrors/opseval_remine_s2.jsonl`
10. `INDEX_BUILD_REPORT.md` → `final/audit/SESSION_16_INDEX_BUILD_REPORT.md`

**Non-move actions**:
- Regen `scripts/README.md` to list all 43 .py + the 4 new scripts (`flip_qa_mcq_*`, `group_c_relabel_*`, `regen_diff_pdf.py`, `recompute_bert_f1.py`)
- Add one-line note to `final/main_benchmark/README.md` flagging `results_sota_eval_431.json` as canonical paper source (vs `results.json` rich-eval provenance)
- Add one-line note to `intermediate/README.md` flagging `benchmark_431_seed42.json` as canonical paper dataset
- Add `archive/raw_pre_reorg_mirrors/_NOTICE.md` explaining the 3 files are pre-2026-05-20 mirrors retained for forensic provenance
- Update `INDEX.md` §1 partition tally (raw 100→97, archive +4)

**Pros**:
- Tiny blast radius: 10 file moves + 4 doc edits + 1 regen.
- Zero changes to load-bearing scripts (the 6 orphans being moved have NO `from benchmark.scripts._foo import …` callers — verified §2.2).
- Preserves 5-partition rule that the paper, reviewers, MEMORY.md, and 16 session handoffs all reference.
- Sealed-forensic docs (CV_PASS1/2, FULL_TRANSCRIPT_AUDIT, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, SESSION_*_HANDOFF) untouched.
- archive/ untouched per user rule (only ADD a new subdir — no rearrangement).
- File-ref updates: ~3-5 places at most (`scripts/README.md` regen + 1 INDEX.md tally + 0 .py imports).

**Cons**:
- Doesn't fix the **deeper conceptual issue** that "final/main_benchmark/" and "final/ablation_v4/" each contain a rich-eval + matched-eval pair with only narrative annotation distinguishing them.
- Doesn't separate active scripts from sealed-forensic by lifecycle phase (which Option B does).
- The 6 underscore-prefix scripts move into `_dev/` but inherit the same already-loose convention (`_session21_*` already in `_dev/` with the same prefix).

**Migration cost estimate**: ~30 minutes (10 git mv + 4 small md edits + 1 INDEX.md tally regen + 1 scripts/README.md regen). Plus 1 verification re-run of `eval/verify_authoritative_numbers.py` + `eval/inspect_all_configs.py`. Total file-refs to update: **6** (1 scripts/README + 1 INDEX.md + 4 narrative .md edits). **Risk: LOW**.

### Option B — Task-oriented (lifecycle phase partition)

**Rationale**: Re-partition by **lifecycle phase** rather than artifact-type. Each phase owns its data + scripts + docs co-located. Makes the pipeline narrative obvious: phase folder = pipeline stage. Trade-off: heavy migration cost across 188 path-string references.

**Target tree**:

```
benchmark/
├── HANDOFF.md, INDEX.md, README.md
├── 01_mining/                       (~10 scripts + raw third-party + candidates JSONLs)
│   ├── raw_third_party/             ← raw/  (deep mirror of loghub + lemma_rca + opseval)
│   ├── candidates/                  ← intermediate/candidates/
│   ├── mine_apache.py               ← scripts/prep/mine_apache.py
│   ├── mine_openssh.py
│   ├── mine_opseval.py
│   ├── download_datasets.py
│   ├── README.md                    (mining-phase narrative)
│   └── (~5 historical mining helpers)
├── 02_curation/                     (~8 scripts + canonical JSON datasets + 3 historical fixers)
│   ├── datasets/                    ← intermediate/datasets/
│   ├── clean_dataset.py
│   ├── prepare_datasets.py
│   ├── vet_labels.py
│   ├── _apply_d1_result_sync.py     ← scripts/_apply_d1_result_sync.py (moved here, since it's a dataset-mutation script)
│   ├── _verify_d1_relabel.py        ← scripts/_verify_d1_relabel.py
│   ├── flip_qa_mcq_correct_to_null.py
│   ├── group_c_relabel_d1_rich_and_header.py
│   ├── remove_chinese.py            (historical)
│   ├── fix_benchmark_dataset.py     (historical)
│   └── README.md
├── 03_runs/                         (~8 scripts + their primary outputs)
│   ├── main/                        ← final/main_benchmark/
│   ├── ablation/                    ← final/ablation_v4/
│   ├── phase46_no_prompt/           ← final/phase46_no_prompt/
│   ├── sota_baselines/              ← final/sota_baselines/
│   ├── infrastructure/              ← final/infrastructure/
│   ├── run_benchmark.py
│   ├── run_ablation.py
│   ├── run_sota_baselines.py
│   ├── run_drain_baseline.py
│   ├── run_graph_experiments.py
│   ├── test_5plus5.py
│   ├── demo_test.py, debug_connection.py, smoke_knowledge_query.py, test_instruct.py, create_nothink_model.py (dev runners)
│   └── README.md
├── 04_evaluation/                   (~10 scripts + Phase 5 outputs)
│   ├── phase5/                      ← final/{main_benchmark,ablation_v4}/phase5_stats.{json,md}
│   ├── matched_eval_table.md, paper_tables.{md,tex}, ...
│   ├── compile_results.py, compute_semantic_metrics.py, evaluate_results.py
│   ├── export_metrics.py, inspect_all_configs.py, inspect_single4b.py
│   ├── phase5_stats.py, rescore_ours_with_sota_eval.py
│   ├── verify_authoritative_numbers.py, recompute_bert_f1.py
│   ├── _compute_sota_post_relabel.py, _verify_a2_apply.py, _probe_format.py, _probe_format2.py
│   ├── _session21_latency_*.py
│   ├── regen_diff_pdf.py
│   └── README.md
├── 05_paper_evidence/               (~50 files; the load-bearing canonical artifacts only)
│   ├── SUMMARY.md, MANIFEST.md, AUDIT_REPORT.md, README.md
│   ├── METHODOLOGY.md ← final/docs/METHODOLOGY.md
│   ├── BUG_HISTORY.md, BROKEN_ABLATIONS.md, CURRENT_RUNS.md
│   └── (the 14 result JSON/JSONL files referenced from the paper, copies or symlinks)
├── 06_audit_history/                ← final/audit/
│   ├── (16 sealed-forensic .md + .json)
│   ├── SESSION_NN_HANDOFF.md × 16
│   ├── paper_audit_session22_2026-05-26/
│   ├── paper_audit_session27_2026-05-26/
│   └── _session11/_session12/_archived_session_history/
├── 07_ops/                          (build/archive utilities + INDEX helpers)
│   ├── master_backup_manifest.py
│   ├── archive_originals.py, build_final_results.py, e2e_tests.py
│   ├── _idx_build.py, _idx_render.py
│   └── README.md
└── 08_archive/                      ← archive/  (UNCHANGED contents per user rule)
```

**Pros**:
- Pipeline narrative is **obvious** to a new reader: 01 → 02 → 03 → 04 → 05.
- Each phase folder is **self-contained** (scripts + data + docs co-located); a forensic dive into "the ablation runs" only needs to open `03_runs/ablation/` + `04_evaluation/`.
- Resolves §3.2 boundary issue (raw vs intermediate vs final) by making the boundary phase-based not artifact-type-based.
- Resolves §3.1 orphan issue trivially — each orphan goes into the phase it ran for.

**Cons**:
- **MASSIVE** path-string updates: ~188 path occurrences across 39 .py + many .md files would shift. Every `benchmark/final/main_benchmark/results.json` → `benchmark/05_paper_evidence/main/results.json` or `benchmark/03_runs/main/results.json` (ambiguous which is canonical, since they overlap).
- Breaks the "MANIFEST.md is the FINAL = paper-evidence subset" invariant — paper-evidence now lives in 05_, but the JSONs that ARE the evidence ALSO live in 03_runs/. Need to deduplicate-via-symlink or copy, both fragile on Windows (NTFS symlinks need admin).
- Breaks the **MEMORY.md hard-pointer rule** that lists `benchmark/final/` as the canonical paper artifact root. MEMORY.md, HANDOFF.md, and all 16 SESSION_*_HANDOFF.md docs reference `benchmark/final/...` — every one becomes stale.
- Breaks the **sealed-forensic rule** indirectly: REORG_PROPOSAL_2026-05-20.md describes a 4-partition tree that no longer exists; CV_PASS1/2 reference paths under `results_aws/FINAL/` already-mapped to `final/` and now would need a *second* mapping. Future audits can't replay session-12 forensics.
- Sealed-forensic CV_PASS2 has 491 file paths embedded in tables — does not get edited but becomes harder to interpret.
- **Cycle risk**: `03_runs/` outputs feed `04_evaluation/` scripts which write back to `03_runs/` (e.g., `recompute_bert_f1.py` overwrites `results.json` in place). Cross-phase write dependency makes the "self-contained phase folder" claim weaker than it sounds.

**Migration cost estimate**: ~2-3 sessions of work; ~150-180 .py + .md edits; high risk of subtle path-string breakage even after grep+sed. Verification: run **all** of `eval/verify_authoritative_numbers.py` + `eval/inspect_all_configs.py` + `e2e_tests.py` end-to-end. **Risk: HIGH**.

### Option C — Flat-then-deep (hybrid)

**Rationale**: Keep the 5-partition deep tree (since the deep tree's data is paper-evidence reachable from the .tex via predictable paths), but **promote** the most-referenced docs/scripts to a shallow top-level for discoverability. Compromise between A and B.

**Target tree**:

```
benchmark/
├── README.md                       ← regen with §-by-§ entry-point index
├── INDEX.md
├── HANDOFF.md
├── SUMMARY.md                      ← final/SUMMARY.md (PROMOTED for top-level visibility)
├── MANIFEST.md                     ← final/MANIFEST.md (PROMOTED)
├── METHODOLOGY.md                  ← final/docs/METHODOLOGY.md (PROMOTED)
├── raw/                            UNCHANGED (minus 3 stale mirrors → archive/)
├── intermediate/                   UNCHANGED
├── final/                          UNCHANGED (the 3 promoted .md are no longer here, but everything else is)
│   ├── README.md (kept for partition entry-point)
│   ├── AUDIT_REPORT.md
│   ├── ablation_v4/, main_benchmark/, phase46_no_prompt/, sota_baselines/, infrastructure/
│   ├── docs/  (3 remaining active + 3 sealed history)
│   └── audit/  UNCHANGED
├── scripts/                        Option A applied (6 root orphans → _dev/)
└── archive/                        UNCHANGED + raw_pre_reorg_mirrors/ subdir
```

**Pros**:
- The 3 most-referenced .md files (`SUMMARY.md`, `MANIFEST.md`, `METHODOLOGY.md`) are 1 directory shallower → faster discoverability for new reviewers / agents.
- Preserves the rest of Option A's tightening (orphan moves + raw mirror move + INDEX_BUILD_REPORT relocation).
- Better matches the "front door" pattern (top-level README + the most-important 3 .md files visible at a glance).

**Cons**:
- Breaks the 5-partition invariant ("everything paper-related lives in final/") — now 3 paper-related .md float at top-level.
- Breaks ~30 incoming references that point at `benchmark/final/SUMMARY.md`, `benchmark/final/MANIFEST.md`, `benchmark/final/docs/METHODOLOGY.md` (from MEMORY.md, HANDOFF.md, 16 SESSION_*_HANDOFF.md, scripts/README.md, multiple .py docstrings).
- Promotes 3 files but leaves `AUDIT_REPORT.md` (similar audience) and `README.md` (partition entry) under final/ — slightly inconsistent.

**Migration cost estimate**: ~1 hour; ~30-40 path-string updates across .md + .py docstrings. **Risk: MEDIUM**.

### Option comparison table

| Dimension | Option A (Minimal) | Option B (Task-oriented) | Option C (Flat-then-deep) |
|---|---|---|---|
| Files moved | 10 | ~250+ | 13 |
| Doc/file-ref updates needed | 6 | 150-180 | 30-40 |
| Sealed-forensic doc breakage | 0 | High (REORG_PROPOSAL, CV_PASS1/2 reference stale paths) | 0 |
| 5-partition invariant preserved | ✅ Yes | ❌ No (becomes 8-phase) | ⚠ Partial (3 .md floated) |
| `final/audit/` left alone | ✅ Yes | ✅ Yes (moves to `06_audit_history/`, contents same) | ✅ Yes |
| `archive/` left alone | ✅ Yes (+1 read-only subdir) | ✅ Yes (renamed) | ✅ Yes (+1 subdir) |
| Resolves orphan-scripts pain (§3.1) | ✅ Fully | ✅ Fully | ✅ Fully |
| Resolves boundary fuzziness (§3.2) | ⚠ Only the 3-mirror item | ✅ Fully (phase = boundary) | ⚠ Same as A |
| Resolves duplicate `results.json` confusion (§3.3 item 5) | ⚠ Annotation only | ✅ (rich vs matched land in different phase dirs) | ⚠ Annotation only |
| Resolves path fragility (§3.5) | ⚠ Leaves hardcoded path strings intact | ❌ Multiplies (deeper paths) | ⚠ Same as A |
| Mid-air collision with session-28 multi-agent audit | Low | High (Stages 2-6 reference `benchmark/final/...`) | Low |
| Long-term clarity | MEDIUM | HIGH | MEDIUM-HIGH |
| Risk score | **LOW** | **HIGH** | **MEDIUM** |
| Approx session-time cost | 30 min | 2-3 sessions | 1 hour |

## §5. Recommended option

**RECOMMENDED: Option A — Minimal-disturbance**.

Rationale, paragraph 1: The 5-partition layout (raw/intermediate/final/scripts/archive) has been **doubly-validated** — once in session 12 by REORG_PROPOSAL_2026-05-20.md (with explicit "Success criteria" that were met) and again in session 16 by INDEX.md (which mapped 411/422 files cleanly to the post-reorg structure). The pain points the user flagged ("scripts not fully foldered" + "final/intermediate/raw boundaries fuzzy") map to **drift** since 2026-05-20 (sessions 17-24 added 9 underscore-prefix one-offs without foldering them) and to **3 stale raw mirrors** that are forensic-byte-identical to intermediate copies. Both are surgically fixable without disturbing the 188 path-string occurrences across 39 .py files.

Rationale, paragraph 2: Option B (task-oriented) is conceptually cleaner but requires changing **every paper-evidence path string** in MEMORY.md (auto-loaded), HANDOFF.md, 16 SESSION_*_HANDOFF.md (12 of which are sealed-forensic), CV_PASS1/2 (sealed), REORG_PROPOSAL_2026-05-20.md (sealed), the live `.tex` if any paths are referenced (they are not currently, but the next reviewer cycle might add them), and 39 .py scripts. The forensic-trail damage alone (sealed docs become stale + the next CV pass has to map paths through TWO historical layouts) outweighs the discoverability benefit.

Rationale, paragraph 3: Option C (flat-then-deep) is a tempting compromise but breaks the "everything paper-related in final/" invariant for marginal benefit (3 fewer keystrokes per cd). It introduces a new front-door pattern with no precedent in the prior 27 sessions. The MEMORY.md hard-pointer block would need 3+ surgical edits, and the cost-benefit is poor.

Concretely, **Option A**'s scope (10 git mv + 4 small .md edits + 1 scripts/README.md regen) can be applied as ONE phased commit ("refactor(benchmark): orphan-script foldering + 3 raw-mirror archival + INDEX_BUILD_REPORT relocation") with a single verification re-run, and it cleanly addresses §3.1 + §3.2-item-1 + §3.6-item-on-INDEX_BUILD_REPORT. The remaining lower-severity items (§3.2 items 2-4, §3.3 items 5-6, §3.4 prefix conventions, §3.5 path fragility, §3.7 stale README count) are **annotation-only** fixes that can ride in the same commit or follow incrementally.

## §6. Dry-run move plan (Option A — recommended)

### §6.1 File-by-file move plan

| # | Current path | Target path | Reverse-link count | Risk | Notes |
|---|---|---|---:|---|---|
| 1 | `benchmark/scripts/_apply_d1_result_sync.py` | `benchmark/scripts/_dev/_apply_d1_result_sync.py` | 2 (SESSION_17_HANDOFF.md, SESSION_18_HANDOFF.md — both SEALED, do NOT edit) | **MEDIUM** | Sealed handoffs reference it but those docs are NOT updated post-edit. Script itself uses hardcoded `'benchmark/final/...'` (NOT relative paths), so it still runs from any cwd. NO imports from other scripts. |
| 2 | `benchmark/scripts/_compute_sota_post_relabel.py` | `benchmark/scripts/_dev/_compute_sota_post_relabel.py` | 1 (SESSION_17_HANDOFF.md sealed) | LOW | Self-contained one-off |
| 3 | `benchmark/scripts/_probe_format.py` | `benchmark/scripts/_dev/_probe_format.py` | 0 | LOW | Throwaway debugging probe |
| 4 | `benchmark/scripts/_probe_format2.py` | `benchmark/scripts/_dev/_probe_format2.py` | 0 | LOW | Throwaway |
| 5 | `benchmark/scripts/_verify_a2_apply.py` | `benchmark/scripts/_dev/_verify_a2_apply.py` | 1 (SESSION_18_HANDOFF.md sealed) | LOW | Sealed reference; verifier only, no production usage. |
| 6 | `benchmark/scripts/_verify_d1_relabel.py` | `benchmark/scripts/_dev/_verify_d1_relabel.py` | 1 (SESSION_18_HANDOFF.md sealed) | LOW | Sealed reference; verifier only. |
| 7 | `benchmark/raw/apache_candidates.jsonl` | `benchmark/archive/raw_pre_reorg_mirrors/apache_candidates.jsonl` | 3 (INDEX.md line 31, scripts/prep/mine_apache.py docstring example, MASTER_BACKUP_MANIFEST sealed json — leave) | **MEDIUM** | Byte-identical mirror per INDEX.md SHA-12 268999cfb202. Archive subdir is new + gitignored remains gitignored. INDEX.md needs §1 tally re-render. |
| 8 | `benchmark/raw/openssh_candidates.jsonl` | `benchmark/archive/raw_pre_reorg_mirrors/openssh_candidates.jsonl` | 3 (similar to #7) | **MEDIUM** | Byte-identical SHA-12 2794d6e92224. |
| 9 | `benchmark/raw/opseval_remine_s2.jsonl` | `benchmark/archive/raw_pre_reorg_mirrors/opseval_remine_s2.jsonl` | 3 (similar) | **MEDIUM** | Byte-identical SHA-12 b9396a58173d. |
| 10 | `benchmark/INDEX_BUILD_REPORT.md` | `benchmark/final/audit/SESSION_16_INDEX_BUILD_REPORT.md` | 2 (INDEX.md mentions implicitly in build provenance; SESSION_16 handoff sealed) | LOW | Standalone session-16 build report; logically a session handoff artifact. Sealed-forensic adjacency: lands in the sealed-forensic tree but as a NEW file, doesn't modify existing sealed docs. |

**No-move actions (10 cleanup items in same commit)**:

| # | Action | Risk | Notes |
|---|---|---|---|
| 11 | Regen `scripts/README.md` (34→43 script catalog; add new sections for `_dev/` foldered orphans + 3 new active scripts not yet documented: `flip_qa_mcq_correct_to_null.py`, `group_c_relabel_d1_rich_and_header.py`, `regen_diff_pdf.py`, `recompute_bert_f1.py`) | LOW | No moves, only doc regen. |
| 12 | Edit `INDEX.md` §1 partition tally (raw 100→97, archive 203→207 incl. new subdir, scripts 40→49 already true; total 422→similar) | LOW | One table cell update. |
| 13 | Add one-line note to `intermediate/README.md` flagging `benchmark_431_seed42.json` as canonical paper dataset (vs the 4 historical n=150/n=400 variants) | LOW | Annotation only. |
| 14 | Add one-line note to `final/main_benchmark/README.md` flagging `results_sota_eval_431.json` as paper-canonical (vs `results.json` rich-eval provenance) | LOW | Annotation only. |
| 15 | Create `archive/raw_pre_reorg_mirrors/_NOTICE.md` (3-line provenance note for the 3 mirror files) | LOW | New file. |
| 16 | Update `scripts/README.md` "Cross-script dependencies" table — confirm no broken imports after moves (verify: 6 scripts moved have ZERO importers per §2.2 grep) | LOW | Doc only. |
| 17 | Re-run `eval/verify_authoritative_numbers.py` (post-move sanity) | LOW | Verification gate; identical headline expected. |
| 18 | Re-run `eval/inspect_all_configs.py` (post-move sanity) | LOW | Verification gate. |
| 19 | Optionally regenerate INDEX.md from `ops/_idx_build.py` + `_idx_render.py` (after refresh of `MASTER_BACKUP_MANIFEST_2026-05-20.json` — though that filename is date-stamped; new manifest would be `MASTER_BACKUP_MANIFEST_2026-05-27.json`) | MEDIUM | Two manifests now; convention: keep both; only the latest is canonical. Or skip regen entirely for this commit and defer to next routine. |
| 20 | Update `MEMORY.md` `feedback_*` or `project_*` notes if they reference moved files (verify: 0 hits in current MEMORY.md or session-28 starter for the 6 underscore-prefix scripts) | LOW | Verify-and-skip likely. |

### §6.2 Risk summary

- **HIGH risk moves**: 0
- **MEDIUM risk moves**: 4 (items #1, #7, #8, #9) — all because reverse-references exist in sealed-forensic docs that we will NOT edit; the moved scripts/files still work post-move because they use absolute or self-relative paths.
- **LOW risk moves**: 6 + 10 cleanup actions
- **archive/ proximity**: Items 7-9 add a NEW subdir to `archive/` (not modifying existing contents). Per user rule, archive/ contents are preserved-as-is; ADDING is allowed (precedent: `archive/originals_2026-05-19/` was added in session 12).
- **Sealed-forensic proximity**: Item 10 ADDS a file at `final/audit/SESSION_16_INDEX_BUILD_REPORT.md` — this is the sealed-forensic tree, but the action is **add-only** (no modification of sealed CV_PASS1/2, FULL_TRANSCRIPT, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, or any SESSION_NN_HANDOFF). Naming follows the existing pattern (`SESSION_NN_*.md`). If user prefers, this can be skipped entirely and INDEX_BUILD_REPORT.md left at root.

### §6.3 Verification gates (post-commit)

1. `git mv` preserves history → run `git log --follow benchmark/scripts/_dev/_apply_d1_result_sync.py` and confirm session-17 origin commit appears.
2. `find benchmark/scripts -maxdepth 1 -type f -name "_*.py"` returns 0 (no more root underscore-orphans).
3. `find benchmark/raw -maxdepth 1 -type f -name "*.jsonl"` returns 0.
4. `find benchmark -maxdepth 1 -type f -name "INDEX_BUILD_REPORT.md"` returns 0 (if move applied).
5. `python benchmark/scripts/eval/verify_authoritative_numbers.py` exits 0 with same headline numbers (Ann 82.6 / RCA 82.0 / Overall 82.4).
6. `python benchmark/scripts/eval/inspect_all_configs.py` exits 0 with same cross-config audit.
7. SHA-12 spot-check: 5 random files from MASTER_BACKUP_MANIFEST_2026-05-20.json unchanged.

## §7. OPEN QUESTIONS / unresolved

1. **`INDEX_BUILD_REPORT.md` move (item #10)**: this lands in the sealed-forensic tree. Stage rule says sealed docs can be READ but NOT MOVED. ADDING a new file alongside them is undefined. **Recommend USER GO** for item #10 specifically; otherwise leave at root.
2. **`raw/lemma_rca/.cache/huggingface/*`** (2 files: `.gitignore` + `download/Log Data/20231207.zip.metadata`) per INDEX.md §5.2 recommendation are HuggingFace cache markers safe to leave. Not moved in Option A. **Confirm no-op is desired** (vs. moving to `archive/` as well).
3. **`raw/opseval/.DS_Store`** + **`raw/opseval/leaderboard/.DS_Store`** (macOS Finder metadata) — INDEX.md §5.2 leaves them for byte-identical upstream provenance. Not touched in Option A. **Confirm no-op desired**.
4. **Naming convention for orphan-prefix `_`**: should we standardize that "leading underscore" = "private/dev/forensic-only, not a stable API"? Currently used inconsistently across `scripts/_<orphan>.py`, `scripts/_dev/<file>.py`, `scripts/_dev/_session21_*`, `scripts/ops/_idx_*`, `final/audit/_session11_*` and `final/docs/_archived_session_history/`. Worth a 1-line "Conventions" entry in `scripts/README.md` / `final/README.md` — but proposing this is doc-only and orthogonal to topology. **Defer to user**.
5. **Whether to refresh `MASTER_BACKUP_MANIFEST_2026-05-27.json`** after Option A is applied (Stage G-equivalent verification). Pro: re-establishes a SHA baseline post-move. Con: introduces a 2nd manifest alongside the sealed `MASTER_BACKUP_MANIFEST_2026-05-20.json` — convention question. **Recommend deferring** until after Stage 6 synthesis decides whether to refresh.
6. **stale `scripts/eval/evaluate_results.py`** (historical superseded) and `scripts/prep/{fix_benchmark_dataset, remove_chinese}.py` (historical one-offs): should they be moved to `_dev/` like the underscore-prefix orphans? They're in the active prep/eval folders but flagged "historical" in README. **Option A leaves them in place** (the README's status legend distinguishes 🟢 / 🟡 / 🔵, which is sufficient annotation); but a stricter cleanup would move them. **Defer to Stage 6 synthesis**.
7. **`scripts/run/run_graph_experiments.py`** still references `final/phase45_graph/` as its output path, but **`final/phase45_graph/` does not currently exist on disk** (per the find walk in §1.1 — `final/` has main_benchmark, ablation_v4, phase46_no_prompt, sota_baselines, infrastructure, docs, audit; no phase45_graph). Per SUMMARY.md line 3, the session-19 attempt crashed and "Per-case JSONL files lost (0 bytes); 4.5c summary on disk is stale session-17 leftover (ignored)". The stale dir was apparently cleaned up. **Topology-orthogonal**, but worth flagging: a `final/phase45_graph/` subdirectory with a placeholder README + the salvaged `exp_4_5b_summary.json` would improve discoverability.

## §8. Recommendations for next session

### §8.1 Execution order (phased commits)

If user approves Option A, recommend splitting into **3 commits** for atomic reversibility:

**Commit 1 — `refactor(benchmark): folder 6 root underscore-orphan scripts into _dev/`**
- Items #1-6 (6 git mv)
- Item #11 (`scripts/README.md` regen with full 43-script catalog)
- Item #16 (cross-script dep table verify)
- Pre-commit grep: `find benchmark/scripts -maxdepth 1 -type f -name "_*.py"` returns empty
- Verification: `python benchmark/scripts/eval/verify_authoritative_numbers.py` + `python benchmark/scripts/eval/inspect_all_configs.py` both pass with identical numbers

**Commit 2 — `refactor(benchmark): archive 3 stale raw/ candidates mirrors`**
- Items #7-9 (3 git mv)
- Item #15 (`_NOTICE.md` in new archive subdir)
- Item #12 (INDEX.md §1 partition tally update)
- Items #13-14 (boundary clarifications in intermediate/README + main_benchmark/README)
- Pre-commit: confirm SHA-12 byte-identical to intermediate/candidates counterpart (`shasum -a 256` each pair)
- Post-commit verification: re-run prep/mine scripts on a smoke sample — confirm `intermediate/candidates/` still written (writes path unchanged)

**Commit 3 — `refactor(benchmark): relocate INDEX_BUILD_REPORT to session-16 audit subtree`** *(OPTIONAL — requires USER GO for sealed-forensic-adjacent action)*
- Item #10 only
- Update INDEX.md provenance reference (1-line edit)
- Skip if user prefers to leave at root

**(Optional) Commit 4 — `chore(benchmark): refresh MASTER_BACKUP_MANIFEST post-Option-A`**
- Run `python benchmark/scripts/ops/master_backup_manifest.py` → produces `final/audit/MASTER_BACKUP_MANIFEST_2026-05-27.json`
- New manifest co-exists with sealed 2026-05-20 manifest
- Optional INDEX.md re-render via `_idx_build.py` + `_idx_render.py`

### §8.2 Halt rules (per project standing rules)

- Halt for USER GO before each commit
- Halt for separate USER GO before any push
- Do NOT touch sealed-forensic docs (CV_PASS1/2, FULL_TRANSCRIPT_AUDIT, REORG_PROPOSAL_2026-05-20, MASTER_BACKUP_MANIFEST_2026-05-20, SESSION_*_HANDOFF.md from 12-27, the paper_audit_session{22,27}_*/ reports)
- archive/ contents UNTOUCHED; only ADD subdir `raw_pre_reorg_mirrors/` (precedent: session 12 added `originals_2026-05-19/`)
- 3-commit batch can be pushed as ONE batched push (Gate-style) after USER GO

### §8.3 Defer to Stage 6 (final synthesis)

The following can wait until Stage 6 cross-validation:

- The 4 §3.3 / §3.4 items 5-6 (historical scripts in active folders) — annotation may be enough
- The §3.5 path-fragility items (Windows raw-string paths in `_session21_*`, hardcoded absolute paths in `_idx_*`) — out of scope for topology, in scope for code-quality
- §3.7 (stale 34-script count in scripts/README) — fixed in Commit 1 above
- §7 OPEN QUESTIONS 1, 6, 7 — require user decisions

### §8.4 What this analysis explicitly does NOT do

- No file move or rename is performed by this agent (READ-ONLY mission)
- No edits to active paper `.tex` / `.bib` (out of scope)
- No touch on AWS, sealed-forensic docs, or `archive/` contents
- No proposal to split `final/audit/` (per task constraint)
- No proposal to delete any file (only MOVES + ANNOTATIONS)
- No proposal to drop `INDEX.md` regeneration (still useful)

---

**End of Stage 5 report**. Companion to Stage 4 (paper claim cross-verification, in same session-27 dir). Awaits Stage 6 final synthesis cross-validation in session 28.
