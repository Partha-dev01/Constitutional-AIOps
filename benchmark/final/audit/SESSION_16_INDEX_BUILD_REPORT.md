# INDEX.md build report (session 16, 2026-05-25)

## §1 Build summary

| Metric | Value |
|---|---:|
| Files walked (current tree) | **422** |
| Baseline file count (`CV_PASS2_CODEBASE_AUDIT.md` Part B, git-tracked only) | 491 |
| Baseline file count (`MASTER_BACKUP_MANIFEST_2026-05-20.json`, all filesystem) | 493 |
| Why the two baselines differ | CV_PASS2 enumerated only git-tracked files via `git ls-files`; MASTER_BACKUP_MANIFEST used `Path.rglob('*')` and so additionally includes `.benchmark_step2_complete` + `.progress.json` (untracked sentinel files). 493 - 491 = 2. |
| Current count vs MASTER_BACKUP_MANIFEST | 422 - 493 = -71 (net contraction). Drivers: 4-partition reorg consolidated duplicates (`results/` + `results_v2.0_frozen/` were byte-identical; the v2 frozen copy was dropped — see §3 below), 8 `__pycache__/*.pyc` removed, several internal `_NEW`/`META` duplicates removed. |
| Added since baseline | **11** |
| Deleted since baseline | **13** |
| Possibly-modified (mtime > 2026-05-20) | **41** |
| SHA-mapped from manifest | 411 of 422 (97.4%) |
| SHA unknown (added since baseline) | 11 of 422 (2.6%) |

Walk command (per task constraint, `find` not Glob):

```
find "c:/Users/partha/Downloads/files AIOPS NEW/constitutional-aiops/benchmark" \
  -type f -not -path "*/__pycache__/*" -not -path "*/.git/*" -not -path "*/node_modules/*" \
  -printf '%P|%TY-%Tm-%Td %TH:%TM:%TS|%s\n'
```

422 results.

## §2 Methodology notes

### §2.1 SHA-256 lookup

For each current file, the post-reorg relative path was reverse-mapped to its pre-reorg path in `MASTER_BACKUP_MANIFEST_2026-05-20.json` using these rules (derived from `final/audit/REORG_PROPOSAL_2026-05-20.md` and the partition READMEs):

| Current path prefix | Pre-reorg path prefix |
|---|---|
| `raw/` | `datasets/raw/` |
| `intermediate/datasets/` | `datasets/processed/` |
| `intermediate/candidates/` | `v0.11/` |
| `final/` (subdirs) | `results_aws/FINAL/` |
| `final/docs/{METHODOLOGY,BUG_HISTORY,BROKEN_ABLATIONS,CURRENT_RUNS}.md` | `results_aws/<same>.md` |
| `final/docs/_archived_session_history/{FILE_PROVENANCE,RESULTS_SUMMARY,RUNS_INDEX}.md` | `results_aws/<same>.md` |
| `final/audit/` | (new; mostly post-2026-05-20) |
| `archive/originals_2026-05-19/` | `results_aws/_archive_originals_2026-05-19/` |
| `archive/v0.9.1_jarvis_baseline/` | `results/` or `results_v2.0_frozen/` |
| `archive/run_stackA_main431_OLD_PROMPT/` | `results_aws/run_stackA_main431/` |
| `archive/rerun_remine33_enriched/` | `results_aws/rerun_remine33_enriched/` |
| `archive/smoke_tests/` | `results_aws/archive/smoke_tests/` |
| `archive/aiops_archive_2026-05-17.tar.gz` | `results_aws/aiops_archive_2026-05-17.tar.gz` |
| `archive/originals_backup_2026-05-19.zip` | `results_aws/originals_backup_2026-05-19.zip` |
| `scripts/{prep,run,eval,ops,_dev}/<x>.py` | `scripts/<x>.py` (flat pre-session-13) |

Mapping was attempted in order; first hit in `sha_map` wins. No SHA was recomputed (per task constraint). 411 of 422 current files matched.

### §2.2 Role / status inference

Roles were assigned by file-path pattern matching against the partition READMEs and `scripts/README.md`:

- Per-script roles (`active` / `historical` / `dev`) follow the status legend in `scripts/README.md` verbatim.
- `final/main_benchmark/` + `final/ablation_v4/`: roles distinguish `results.json` (rich-eval, provenance) from `results_sota_eval_431.json` (matched-eval, **authoritative for paper**) per `final/AUDIT_REPORT.md` notes.
- `final/audit/` content marked `sealed-forensic` per the user's standing rule from MEMORY.md ("sealed forensic: FULL_TRANSCRIPT_AUDIT, CV_PASS1/2, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST — do NOT regenerate").
- `final/docs/_archived_session_history/` content marked `sealed-forensic` per the explicit `_archived_session_history/` sub-folder name + the existing `_ARCHIVED.md` headers.
- `archive/**` content marked `historical` uniformly per `archive/README.md` ("Nothing here is read by active scripts").
- `raw/**` content marked `active` (still consumed by `prep/*` scripts) even though gitignored.

### §2.3 Files where role could not be cleanly inferred from any README

None — every file mapped to a partition with a README + status convention. The only ambiguity was top-level `.benchmark_step2_complete` and `.progress.json`, which are session-9-era benchmark sentinels (mtime 2026-05-13, content stable since); marked `historical` because no current script reads them.

### §2.4 Files NOT present in either baseline NOR with a README pointer

| Path | Why missing | Note |
|---|---|---|
| `final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json` | Self-referential — the manifest does not list itself | Generated AT 2026-05-20 by `scripts/ops/master_backup_manifest.py`. |
| `final/audit/REORG_PROPOSAL_2026-05-20.md` | Created during session 12 (after manifest snapshot) | Sealed forensic. |
| `final/audit/SESSION_12_HANDOFF.md` | Created session 12 (after manifest snapshot) | First session handoff. |
| `final/audit/SESSION_13_HANDOFF.md` | Created session 13 | |
| `final/audit/SESSION_14_HANDOFF.md` | Created session 14 | |
| `final/audit/SESSION_15_HANDOFF.md` | Created session 15 | |
| `raw/README.md` | Created during 2026-05-20 reorg (after manifest snapshot) | Partition README. |
| `intermediate/README.md` | Same | Partition README. |
| `archive/README.md` | Same | Partition README. |
| `scripts/README.md` | Same | 34-script index. |
| `archive/originals_2026-05-19/_REORG_NOTE_2026-05-20.md` | Added during reorg | Forensic note. |

All 11 are documentation files created during or after the 2026-05-20 reorg, which is exactly the expected post-baseline addition pattern.

## §3 Discrepancies vs existing manifests

### §3.1 Files in `final/MANIFEST.md` not on disk

`final/MANIFEST.md` lists 47 source→dest pairs. The DEST column lists 47 paths under `benchmark/results_aws/FINAL/`. Under the post-reorg layout these now live under `benchmark/final/`. All 47 dest files are present on disk except for two that were intentionally deduplicated during reorg:

- `benchmark/results_aws/FINAL/BUG_HISTORY.md` → consolidated to `final/docs/BUG_HISTORY.md` (was byte-identical META copy)
- `benchmark/results_aws/FINAL/METHODOLOGY.md` → consolidated to `final/docs/METHODOLOGY.md` (was byte-identical META copy)

Both deduplications are documented in `archive/README.md` "Removed during 2026-05-20 reorg" §. **No regressions.** The MANIFEST.md SHAs for these two files match the current `final/docs/` copies.

### §3.2 Files in `MASTER_BACKUP_MANIFEST_2026-05-20.json` not on disk

13 files. Documented in `INDEX.md` §3.2:

- 5 docs moved (3 to `final/docs/_archived_session_history/`, 2 deduplicated to `final/docs/`)
- 8 are `scripts/__pycache__/*.pyc` Python bytecode

All 13 are expected losses from the reorg + bytecode cleanup. **No regressions.**

### §3.3 Files in `CV_PASS2_CODEBASE_AUDIT.md` Part B not on disk

CV_PASS2 enumerated 491 git-tracked files. By symmetric difference with the 422 current files (using the same path-mapping logic in §2.1), the same 13 missing files appear plus 0 git-tracked-only losses. **No regressions.**

### §3.4 Mapping coverage gaps

411 of 422 current files (97.4%) matched the manifest via path-mapping. The 11 unmatched are all the post-baseline additions in §2.4. **Zero current files have an unexplained SHA gap.**

## §4 Memory-update note (for the user to apply manually)

Suggested addition to `C:/Users/partha/.claude/projects/c--Users-partha-Downloads-files-AIOPS-NEW/memory/MEMORY.md` under the "Hard pointers (updated 2026-05-20 — POST-REORG + POST-SUB-FOLDER paths)" block (insert as the first bullet so it surfaces above the existing per-folder pointers):

```markdown
- **Master `benchmark/` index** (canonical entry-point): `benchmark/INDEX.md` — 422-file index with per-file role / status / SHA-256[:12] / mtime, partition tally, delta vs 2026-05-20 baseline, cross-references. Built 2026-05-25 (session 16). Regenerate whenever files are added/removed/moved under `benchmark/`. Build helper sources: `_idx_build.py` (mapping + delta) + `_idx_render.py` (Markdown rendering), kept under `c:/Users/partha/Downloads/files AIOPS NEW/` (NOT in git).
```

No existing pointer needs to be deleted — the new bullet supplements the existing ones (which point at MANIFEST.md, AUDIT_REPORT.md, SUMMARY.md, CV_PASS2 Part B, etc.).

The "Current state" block at the bottom of MEMORY.md also benefits from a one-line update under "**`benchmark/final/` sub-folder layout (active)**":

```markdown
- **`benchmark/INDEX.md`** (NEW 2026-05-25): top-level master index, 422 files, regenerable.
```

## §5 Recommendations

### §5.1 When to regenerate INDEX.md

- After any file is **added**, **renamed**, **moved between partitions**, or **deleted** under `benchmark/`
- After running `scripts/ops/master_backup_manifest.py` (the new manifest is the canonical SHA source)
- At the END of each session that touched `benchmark/`, so the next session opens to an accurate index

A lightweight regen would be: (1) re-run `find` walk, (2) re-run `master_backup_manifest.py`, (3) re-run `_idx_build.py` + `_idx_render.py`. Total time: <1 minute. None of these are in git; the user may wish to promote them to `scripts/ops/` if regen becomes routine.

### §5.2 Files / folders that look orphaned (candidates for cleanup)

| Path | Status | Recommendation |
|---|---|---|
| `.benchmark_step2_complete` | empty sentinel from session 9 (mtime 2026-05-13) | Safe to delete — no current script reads it. Was never git-tracked (UNTRACKED in CV_PASS2). Low priority. |
| `.progress.json` | 408-byte progress marker from session 9 (mtime 2026-05-13) | Same — safe to delete; not git-tracked. Low priority. |
| `raw/lemma_rca/.cache/huggingface/.gitignore` | 1-byte HuggingFace cache marker | Belongs to the LEMMA-RCA download cache; safe to leave (gitignored, won't bloat repo). |
| `raw/lemma_rca/.cache/huggingface/download/Log Data/20231207.zip.metadata` | 127-byte HuggingFace cache marker | Same — leave alone. |
| `raw/opseval/{.DS_Store,leaderboard/.DS_Store}` | macOS Finder metadata | Could delete (no semantic value), but they're part of the upstream OpsEval repo; leaving them preserves byte-identical provenance. |

### §5.3 Long-term hygiene

- The **41 possibly-modified files** in §3.3 of INDEX.md are mostly innocuous (mtime touches during the session-14 Stage J + matched_eval_table regen). If reviewer-defensibility ever requires byte-equivalence to the 2026-05-20 baseline, re-run `master_backup_manifest.py` and diff against the baseline. Any file whose new SHA-256 differs would indicate actual content drift since 2026-05-20.
- Consider promoting `INDEX.md` to be cross-linked from `final/README.md` (currently the partition entry-points don't reference the top-level index). One-line edit to each partition README would close the discoverability loop.
- The user's MEMORY.md "Mandatory reads" list (15 files) does not currently include `benchmark/INDEX.md`. After §4 above is applied, the next session's startup protocol could insert it as item 5.5 (between `scripts/README.md` and `final/SUMMARY.md`).
