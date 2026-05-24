# Session 13 → Session 14 Handoff (2026-05-20)

> ## ✅ RESOLVED in session 14 (2026-05-24) — Stage J complete.
>
> All §3 path-depth fixes, cross-script imports, docstrings, and external-doc invocations have been applied. Verification gate (§3.6) passed: matched-eval numbers (Ann 82.6 / RCA 80.3 / Overall 81.7 main; Full Hybrid 83.3 ablation) reproduce identically; inspect_all_configs Δ table matches (full +9.86, single_4b +18.31, no_constitutional −30.99); cross-imports work; manifest write-path verified.
>
> **This document is preserved as the forensic record of how the WIP was resumed.** Sub-folder layout (`prep/run/eval/ops/_dev`) is now the canonical structure.
>
> ---
>
> ## ⚠ ORIGINAL WARNING (session-13 close, now obsolete) — DO NOT RUN ANY MOVED SCRIPT BEFORE READING §3.
>
> Origin (`a20e3cb`) is clean and pushed. The 33 unstaged-renamed scripts in the working tree are **NOT yet runtime-safe** — they all use `Path(__file__).parent.parent.parent`-style path resolution that needs one extra level after the sub-folder move. Resume protocol below.

## 1. What session 13 successfully completed (pushed to origin)

| Commit | What |
|---|---|
| `d64965b` | Force-pushed after git filter-repo stripped all `Co-Authored-By: Claude` + `Generated with [Claude Code]` lines from 55 commits + 3 doc-mention commits. **0 Claude refs in entire history**. |
| `f504d6b` | Stage E+F+G+H — path hardcodes (24 scripts + 2 src files) + active docs (5) + scripts/strip_cc_trailers.py utility. Stage G verified all numbers reproduce. |
| `a20e3cb` | **Stage I — `benchmark/final/` sub-folder reorg** into `docs/` + `docs/_archived_session_history/` + `audit/`. 13 R100 moves, 2 critical script refs, 6 doc updates, scripts/README.md added (34-script index). Stage G verified. **THIS IS THE CURRENT ORIGIN HEAD**. |

All three pushed to `origin/main`. `.git` backup at `Backups/constitutional-aiops_git_backup_pre_filter_2026-05-20/`.

## 2. What session 13 attempted but did NOT complete (Stage J)

Sub-folder reorg of `benchmark/scripts/` into 5 sub-dirs:

```
benchmark/scripts/
├── __init__.py        ← unchanged (at root)
├── README.md          ← unchanged (at root, but tables inside STALE)
├── prep/              ← NEW; __init__.py created (untracked)
│   ├── clean_dataset.py            ← git mv from scripts/
│   ├── download_datasets.py
│   ├── fix_benchmark_dataset.py
│   ├── prepare_datasets.py
│   ├── remove_chinese.py
│   ├── mine_apache.py
│   ├── mine_openssh.py
│   ├── mine_opseval.py
│   └── vet_labels.py
├── run/               ← NEW; __init__.py created (untracked)
│   ├── run_benchmark.py
│   ├── run_ablation.py
│   ├── run_sota_baselines.py
│   ├── run_drain_baseline.py
│   ├── run_graph_experiments.py
│   └── test_5plus5.py
├── eval/              ← NEW; __init__.py created (untracked)
│   ├── evaluate_results.py
│   ├── rescore_ours_with_sota_eval.py
│   ├── inspect_all_configs.py
│   ├── inspect_single4b.py
│   ├── phase5_stats.py
│   ├── verify_authoritative_numbers.py
│   ├── compile_results.py
│   ├── compute_semantic_metrics.py
│   └── export_metrics.py
├── ops/               ← NEW; __init__.py created (untracked)
│   ├── archive_originals.py
│   ├── build_final_results.py
│   ├── master_backup_manifest.py
│   └── e2e_tests.py
└── _dev/              ← NEW; __init__.py created (untracked)
    ├── demo_test.py
    ├── smoke_knowledge_query.py
    ├── test_instruct.py
    ├── debug_connection.py
    └── create_nothink_model.py
```

**What's done**: 33 `git mv` operations (visible as R100 in git status). 5 `__init__.py` files (visible as `??` untracked).

**What FAILED to apply**: 11 of 12 Edit-tool calls for path-depth fixes failed because git mv invalidated the Read-tool's "have you read this file" cache on the moved paths. The Edit tool's safety check requires reading the file at its current path before editing, which I had not done post-move.

**What this means for runtime**: every moved script that uses `Path(__file__).parent.parent.parent` (was repo, now benchmark) or `Path(__file__).resolve().parents[2]` (was repo, now benchmark) will compute the wrong repo root. **Do not invoke any moved script until §3 fixes are applied.**

## 3. Resume protocol for session 14 (the Stage J completion)

### 3.0 PRECONDITION — choose one of:
- **(a) Continue from current WIP**: working tree has 33 R + 5 ?? changes. Apply §3.1–§3.6 fixes, verify, commit.
- **(b) Abandon WIP, start clean**: `git restore --staged --worktree benchmark/scripts/ && rm -rf benchmark/scripts/{prep,run,eval,ops,_dev}` returns the working tree to match `a20e3cb`. Then re-apply Stage J using a better strategy (see §3.7 alternative-strategy note).

### 3.1 Edits required to make the moved scripts runtime-safe

For each file below, change the path-depth expression on the listed line. **READ each file first** (Read tool) before Edit, per the Edit tool's contract.

**Group A — `.parent.parent.parent` → `.parent.parent.parent.parent`** (11 files):

| File | Line | Variable |
|---|---|---|
| `benchmark/scripts/eval/evaluate_results.py` | 25 | `PROJECT_ROOT` |
| `benchmark/scripts/eval/export_metrics.py` | 27 | `PROJECT_ROOT` |
| `benchmark/scripts/ops/e2e_tests.py` | 28 | `PROJECT_ROOT` |
| `benchmark/scripts/prep/download_datasets.py` | 36 | `PROJECT_ROOT` |
| `benchmark/scripts/prep/prepare_datasets.py` | 116 | `PROJECT_ROOT` |
| `benchmark/scripts/run/run_ablation.py` | 35 | `PROJECT_ROOT` |
| `benchmark/scripts/run/run_benchmark.py` | 35 | `PROJECT_ROOT` |
| `benchmark/scripts/run/test_5plus5.py` | 27 | `PROJECT_ROOT` |
| `benchmark/scripts/_dev/debug_connection.py` | 22 | `PROJECT_ROOT` |
| `benchmark/scripts/_dev/demo_test.py` | 20 | `PROJECT_ROOT` |
| `benchmark/scripts/_dev/test_instruct.py` | 20 | `PROJECT_ROOT` |

**Group B — `parents[2]` → `parents[3]`** (10 files):

| File | Line | Variable |
|---|---|---|
| `benchmark/scripts/eval/phase5_stats.py` | 27 | `REPO_ROOT` |
| `benchmark/scripts/eval/rescore_ours_with_sota_eval.py` | 27 | `REPO_ROOT` |
| `benchmark/scripts/eval/inspect_all_configs.py` | 6 | `ROOT` (`parents[2] / "benchmark/final/ablation_v4"`) |
| `benchmark/scripts/ops/archive_originals.py` | 35 | `REPO_ROOT` |
| `benchmark/scripts/ops/build_final_results.py` | 22 | `REPO_ROOT` |
| `benchmark/scripts/prep/mine_apache.py` | 32 | `REPO_ROOT` |
| `benchmark/scripts/prep/mine_openssh.py` | 32 | `REPO_ROOT` |
| `benchmark/scripts/prep/mine_opseval.py` | 37 | `REPO_ROOT` |
| `benchmark/scripts/run/run_drain_baseline.py` | 33 | `REPO_ROOT` |
| `benchmark/scripts/run/run_graph_experiments.py` | 38 | `ROOT` |
| `benchmark/scripts/run/run_sota_baselines.py` | 38 | `REPO_ROOT` |

**Group C — `parents[1]` → `parents[2]`** (1 file):

| File | Line | Variable |
|---|---|---|
| `benchmark/scripts/eval/verify_authoritative_numbers.py` | 10 | `ROOT = parents[1] / "final"` |

**Group D — `parent.parent` → `parent.parent.parent`** (3 files):

| File | Line | Variable |
|---|---|---|
| `benchmark/scripts/prep/clean_dataset.py` | 223 | `base_dir = Path(__file__).parent.parent` |
| `benchmark/scripts/prep/fix_benchmark_dataset.py` | 15 | `DATASET_DIR = parent.parent / "intermediate" / "datasets"` |
| `benchmark/scripts/prep/remove_chinese.py` | 16 | `DATASET_DIR = parent.parent / "intermediate" / "datasets"` |

**Group E — special** (2 files):

| File | Lines | Change |
|---|---|---|
| `benchmark/scripts/eval/compile_results.py` | 14, 186 | L14: `"..", "archive"` → `"..", "..", "archive"`; L186: `"..", ".."` → `"..", "..", ".."` |
| `benchmark/scripts/_dev/smoke_knowledge_query.py` | 22 | Add one more `os.path.dirname()` wrap (currently 3 levels, needs 4) |

### 3.2 Cross-script imports to fix (4 files)

| File | Current import | Fixed import |
|---|---|---|
| `benchmark/scripts/eval/rescore_ours_with_sota_eval.py` (~L36) | `REPO_ROOT / "benchmark" / "scripts" / "run_sota_baselines.py"` | `REPO_ROOT / "benchmark" / "scripts" / "run" / "run_sota_baselines.py"` |
| `benchmark/scripts/ops/e2e_tests.py` (3 lines) | `from benchmark.scripts.run_benchmark import …` | `from benchmark.scripts.run.run_benchmark import …` |
| `benchmark/scripts/ops/e2e_tests.py` | `from benchmark.scripts.export_metrics import …` | `from benchmark.scripts.eval.export_metrics import …` |
| `benchmark/scripts/run/run_ablation.py` (~L404) | `from benchmark.scripts.export_metrics import export_all` | `from benchmark.scripts.eval.export_metrics import export_all` |

### 3.3 Docstring `Usage:` examples in every moved script (~30 lines)

Each script has `python benchmark/scripts/<name>.py …` in its docstring. Update each to `python benchmark/scripts/<subdir>/<name>.py …`. Quick grep to find them all:
```bash
grep -rn 'python benchmark/scripts/' benchmark/scripts/
```

### 3.4 External doc invocations

| File | Approx hits |
|---|---|
| `HANDOFF.md` | several `python benchmark/scripts/...` invocations |
| `benchmark/scripts/README.md` | every link in the tables points at flat `<script>.py` — update to `<subdir>/<script>.py` |
| `benchmark/final/audit/SESSION_12_HANDOFF.md` | small handful |
| `benchmark/final/docs/METHODOLOGY.md` | possibly some |
| `benchmark/final/docs/CURRENT_RUNS.md` | possibly some |
| `docs/CHANGELOG.md` | one historical entry (leave as historical) |

### 3.5 Memory files
- `MEMORY.md` — no script-path references in the current SESSION 13 STARTUP block (only doc paths)
- `project_aiops_next.md` — check for any `benchmark/scripts/X.py` invocations

### 3.6 Verification (gate before commit)

After §3.1–§3.5:
```bash
cd "<repo>"
python benchmark/scripts/eval/verify_authoritative_numbers.py
# Expect identical output to pre-Stage-J: Ann 82.6/RCA 80.3/Overall 81.7 main; all 8 ablation configs

python benchmark/scripts/eval/inspect_all_configs.py
# Expect identical Δ table: full +9.86, single_4b +18.31, no_constitutional -30.99, etc.

# Verify import chain (run_ablation → eval/export_metrics) works
python -c "from benchmark.scripts.run.run_ablation import *" 2>&1 | head -5
python -c "from benchmark.scripts.ops.e2e_tests import *" 2>&1 | head -5

# Verify master_backup_manifest writes to the right place
python benchmark/scripts/ops/master_backup_manifest.py
# Expect: writes to benchmark/final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json (idempotent)
```

If any of these fail, do NOT commit. Diagnose the missed path.

### 3.7 Alternative strategy (if §3.1 edit-by-edit feels too brittle)

The path-depth fix is mechanical and repetitive. Two faster approaches:

**(a) sed / PowerShell bulk-edit** — single command pattern per group:
```bash
# Group A (Bash, run from repo root)
sed -i 's|Path(__file__)\.parent\.parent\.parent$|Path(__file__).parent.parent.parent.parent|' \
  benchmark/scripts/eval/evaluate_results.py \
  benchmark/scripts/eval/export_metrics.py \
  benchmark/scripts/ops/e2e_tests.py \
  benchmark/scripts/prep/download_datasets.py \
  benchmark/scripts/prep/prepare_datasets.py \
  benchmark/scripts/run/run_ablation.py \
  benchmark/scripts/run/run_benchmark.py \
  benchmark/scripts/run/test_5plus5.py \
  benchmark/scripts/_dev/debug_connection.py \
  benchmark/scripts/_dev/demo_test.py \
  benchmark/scripts/_dev/test_instruct.py
```

**(b) Throw-away Python script** that reads + edits each file. Less risky than sed (uses str-replace not regex). One-shot, then delete the script.

Either approach avoids the Read-before-Edit cache failure that bit session 13.

## 4. Pending work after Stage J completes

- **Stage K** (if user wants): re-run scripts/README.md generation with new sub-folder paths (or manual update)
- **Paper v2 edits** (no AWS): Table 6 + Figure 4 + §6.1 paragraph reframes using `benchmark/final/ablation_v4/phase5_stats.md`
- **Phase 4.5 LEMMA 5-fold + cold-start curve** (needs AWS restart): produces Table 9 + Figure 5
- **Phase 4.6 paraphrased prompts × 431** (needs AWS restart): produces Table 8

## 5. Hard constraints (carry forward)

1. **No Claude co-author** on any commit (verified 0 in history at a20e3cb).
2. **No push without user GO**.
3. **Master backup zip** + `.git` pre-filter backup — DO NOT delete.
4. **AWS instance STOPPED** (`i-091c4de0e95d63154`); do NOT restart unless authorized.
5. **Sealed audit docs** (FULL_TRANSCRIPT_AUDIT, CV_PASS1, CV_PASS2, sealed archive notices) — content untouched.
6. **For every Edit on a moved file**: Read FIRST. The Edit tool's safety check requires it.

## 6. Recent git commits

```
a20e3cb refactor(benchmark/final): sub-folder into docs/ + audit/ + add scripts/README.md
f504d6b refactor(benchmark): Stage E+F — update path hardcodes + docs for 4-partition tree
d64965b chore(session-12): safety commit of CV audit + master backup + handoff artifacts pre-compact   (rewritten by filter-repo to strip Claude trailers)
... (8 reorg commits Pre-A through Stage D-fix, all from session 12, all rewritten by filter-repo)
```

## 7. First actions in session 14 (in order)

1. Read `MEMORY.md` (auto-loaded) — points here
2. Read this file in full
3. Run `git status` — expect 33 R + 5 ?? if WIP preserved, OR clean tree if user abandoned WIP
4. ASK the user: "Resume Stage J path-depth fixes from the WIP, or abandon WIP and restart clean?"
5. If resume: follow §3.1–§3.6 (preferably via §3.7 bulk-edit alternative)
6. If abandon: see §3.0 reset command + start over with §3.7 strategy applied from the get-go

End of handoff.
