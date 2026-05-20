# benchmark/ — Full Reorganization Proposal

_Generated: 2026-05-20 (session 12, after CV passes 1+2 + master backup)_
_Target structure: 4-partition paper-defensible tree (raw / intermediate / final / archive)_
_Master backup taken first: `<repo>/../Backups/benchmark_master_backup_2026-05-20.zip` (14.27 MB, SHA `7b01aef090…`, integrity verified). Pre-backup manifest at `FINAL/MASTER_BACKUP_MANIFEST_2026-05-20.json`._
_Per-file metadata source: `FINAL/CV_PASS2_CODEBASE_AUDIT.md` Part B (491 files indexed)._

> **Safety contract**: every move uses `git mv` to preserve history for tracked files. Untracked files moved with plain `mv`. Each stage is a separate git commit so any stage can be reverted independently. Scripts that hardcode paths are updated in Stage E AFTER moves, with verification re-runs in Stage G.

---

## Target tree

```
benchmark/
├── raw/                            # Third-party datasets, NEVER modified
│   ├── loghub/                     ← datasets/raw/loghub/
│   ├── lemma_rca/                  ← datasets/raw/lemma_rca/
│   ├── opseval/                    ← datasets/raw/opseval/
│   ├── apache_candidates.jsonl     ← datasets/raw/apache_candidates.jsonl
│   ├── openssh_candidates.jsonl    ← datasets/raw/openssh_candidates.jsonl
│   └── opseval_remine_s2.jsonl     ← datasets/raw/opseval_remine_s2.jsonl
├── intermediate/                   # Processed datasets + mining outputs
│   ├── datasets/                   ← datasets/processed/  (all 9 JSONs)
│   └── candidates/                 ← v0.11/  (apache + openssh + opseval_remine)
├── final/                          # Paper-ready (canonical AWS results)
│   ├── main_benchmark/             ← results_aws/FINAL/main_benchmark/
│   ├── ablation_v4/                ← results_aws/FINAL/ablation_v4/
│   ├── sota_baselines/             ← results_aws/FINAL/sota_baselines/
│   ├── phase46_no_prompt/          ← results_aws/FINAL/phase46_no_prompt/
│   ├── infrastructure/             ← results_aws/FINAL/infrastructure/
│   ├── (all SUMMARY/MANIFEST/AUDIT/CV/audit-doc files stay here)
│   ├── METHODOLOGY.md              ← results_aws/METHODOLOGY.md
│   ├── BUG_HISTORY.md              ← results_aws/BUG_HISTORY.md
│   ├── CURRENT_RUNS.md             ← results_aws/CURRENT_RUNS.md
│   ├── RESULTS_SUMMARY.md          ← results_aws/RESULTS_SUMMARY.md
│   ├── RUNS_INDEX.md               ← results_aws/RUNS_INDEX.md
│   ├── FILE_PROVENANCE.md          ← results_aws/FILE_PROVENANCE.md
│   └── BROKEN_ABLATIONS.md         ← results_aws/BROKEN_ABLATIONS.md
├── archive/                        # Historical / superseded
│   ├── results_local/              ← results/  (Jarvis-era v0.9.1 runs)
│   ├── results_v2.0_frozen/        ← results_v2.0_frozen/  (frozen baseline)
│   ├── originals_2026-05-19/       ← results_aws/_archive_originals_2026-05-19/
│   ├── smoke_tests/                ← results_aws/archive/smoke_tests/
│   ├── gate15_comparison.md        ← results_aws/archive/gate15_comparison.md
│   ├── run_stackA_main431_OLD_PROMPT/  ← results_aws/run_stackA_main431/
│   ├── rerun_remine33_enriched/    ← results_aws/rerun_remine33_enriched/
│   ├── originals_backup_2026-05-19.zip  ← results_aws/originals_backup_2026-05-19.zip
│   └── aiops_archive_2026-05-17.tar.gz  ← results_aws/aiops_archive_2026-05-17.tar.gz
├── scripts/                        # UNCHANGED (active mining/eval/run scripts)
├── data/                           # already empty per Phase 2 audit (manifest.json was rm'd)
├── .benchmark_step2_complete       # untracked runtime marker — leave
└── .progress.json                  # untracked runtime marker — leave
```

After reorg: `benchmark/datasets/`, `benchmark/v0.11/`, `benchmark/results/`, `benchmark/results_v2.0_frozen/`, `benchmark/results_aws/` will be empty and removed.

---

## Stage plan (each is a separate git commit)

### Stage A — `raw/` (lowest risk)
- `mkdir benchmark/raw`
- `git mv` 3 subdirs (loghub, lemma_rca, opseval) + 3 jsonl files from `benchmark/datasets/raw/` into `benchmark/raw/`
- Commit: `refactor(benchmark): Stage A — move raw third-party datasets to benchmark/raw/`

### Stage B — `intermediate/`
- `mkdir benchmark/intermediate/{datasets,candidates}`
- `git mv` 9 JSONs from `datasets/processed/` → `intermediate/datasets/`
- `git mv` 3 candidates JSONLs from `v0.11/` → `intermediate/candidates/`
- `rmdir benchmark/datasets/ benchmark/v0.11/` (now empty)
- Commit: `refactor(benchmark): Stage B — move processed datasets + candidates to benchmark/intermediate/`

### Stage C — `final/`
- `git mv benchmark/results_aws/FINAL benchmark/final` (whole subtree, preserves all the CV docs + master backup manifest + all subdirs)
- `git mv` 7 nav docs from `results_aws/` → `final/`
- Commit: `refactor(benchmark): Stage C — move FINAL/ + nav docs to benchmark/final/`

### Stage D — `archive/`
- `mkdir benchmark/archive`
- `git mv benchmark/results benchmark/archive/results_local`
- `git mv benchmark/results_v2.0_frozen benchmark/archive/results_v2.0_frozen`
- `git mv benchmark/results_aws/_archive_originals_2026-05-19 benchmark/archive/originals_2026-05-19`
- `git mv benchmark/results_aws/archive/smoke_tests benchmark/archive/smoke_tests`
- `git mv benchmark/results_aws/archive/gate15_comparison.md benchmark/archive/`
- `rmdir benchmark/results_aws/archive`
- `git mv benchmark/results_aws/run_stackA_main431 benchmark/archive/run_stackA_main431_OLD_PROMPT`
- `git mv benchmark/results_aws/rerun_remine33_enriched benchmark/archive/`
- `git mv benchmark/results_aws/originals_backup_2026-05-19.zip benchmark/archive/`
- `git mv benchmark/results_aws/aiops_archive_2026-05-17.tar.gz benchmark/archive/`
- `rmdir benchmark/results_aws` (now empty)
- Commit: `refactor(benchmark): Stage D — move historical/superseded artifacts to benchmark/archive/`

### Stage E — update path hardcodes in scripts + src
Files needing path updates (from grep):
- `benchmark/scripts/master_backup_manifest.py`
- `benchmark/scripts/phase5_stats.py`
- `benchmark/scripts/build_final_results.py`
- `benchmark/scripts/inspect_all_configs.py`
- `benchmark/scripts/archive_originals.py` (historical, may be skipped — already ran)
- `benchmark/scripts/rescore_ours_with_sota_eval.py`
- `benchmark/scripts/run_sota_baselines.py`
- `benchmark/scripts/run_drain_baseline.py`
- `benchmark/scripts/run_graph_experiments.py`
- `benchmark/scripts/compute_semantic_metrics.py`
- `benchmark/scripts/mine_opseval.py`
- `benchmark/scripts/mine_openssh.py`
- `benchmark/scripts/mine_apache.py`
- `benchmark/scripts/vet_labels.py`
- `src/benchmark/runner.py`

Path mapping (in order of replacement):
- `benchmark/results_aws/FINAL/` → `benchmark/final/`
- `benchmark/datasets/processed/` → `benchmark/intermediate/datasets/`
- `benchmark/datasets/raw/` → `benchmark/raw/`
- `benchmark/v0.11/` → `benchmark/intermediate/candidates/`
- `benchmark/results_aws/` (residual, e.g. `_archive_originals_2026-05-19`) → `benchmark/archive/originals_2026-05-19/`
- `benchmark/data/` → no replacement (empty dir, was deleted at L5222 of transcript)

Commit: `refactor(benchmark): Stage E — update path hardcodes after benchmark/ reorg`

### Stage F — update docs + memory
- `HANDOFF.md` — replace any remaining `benchmark/results_aws/` refs
- `MEMORY.md` + memory files — replace path refs
- `FINAL/SUMMARY.md`, `FINAL/MANIFEST.md`, `FINAL/AUDIT_REPORT.md`, `FINAL/METHODOLOGY.md`, `FINAL/BUG_HISTORY.md`, etc. — replace internal links
- Audit doc + CV reports — **leave alone** (historical accuracy at audit-generation time)
- Commit: `docs(benchmark): Stage F — update path refs in handoff/memory/FINAL docs post-reorg`

### Stage G — verify
- Re-run `benchmark/scripts/verify_authoritative_numbers.py` → expect same headline numbers (Ann 82.6 / RCA 80.3 / Overall 81.7)
- Re-run `benchmark/scripts/inspect_all_configs.py` → expect same 142-RCA cross-config audit table
- Spot-check 10 file SHA-256s from MASTER_BACKUP_MANIFEST_2026-05-20.json against post-reorg disk state
- No new commit (just verification)

### Stage H — final session-12 commit
- Bundles any remaining session-12 artifacts (audit doc edits, HANDOFF.md path updates, CV docs, this proposal, master backup manifest, master_backup_manifest.py script)
- Commit: `feat(session-12): CV audit + master backup + benchmark/ reorg`
- NO Claude co-author per memory
- Confirm with user before push

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Script path-hardcode missed in Stage E breaks Phase 5 stats recomputation | Medium | Stage G verification catches it; Stage E uses grep before/after to confirm zero remaining refs |
| `annotation_test.json` + `rca_test.json` dirty files get committed accidentally | Low | Confirm `.gitignore` or per-file `git rm --cached` if currently in index. These are in `datasets/processed/` (Stage B) — verify they're untracked before mv |
| `_archive_originals_2026-05-19/` `_ARCHIVED_NOTICE.md` files contain hardcoded back-pointers to old paths | Low | Those notices reference relative paths within the archive — likely unaffected; spot-check during Stage D |
| Phase 5 stats `phase5_stats.py` reads from `FINAL/ablation_v4/` — must update after move | High (high-impact) | Stage E pinpoints this file specifically; verify Stage G re-run |
| The 1.59 GB `files AIOPS NEW (backup incase).rar` in `Backups/` is from 2026-05-11 (pre-AWS) — may be stale | Low | Not touched by reorg; informational |
| Git history opacity if mv batches are too large per commit | Low | Stage A/B/C/D are separate commits with clear scope |

---

## What's NOT in scope

- AWS infrastructure (instance still stopped — no AWS calls)
- Code refactoring beyond path updates (no behavior changes)
- Paper edits (separate task, after reorg)
- New benchmark runs (separate task, requires AWS)
- Master backup is already taken — not re-created during reorg

---

## Success criteria

1. `benchmark/` has exactly 4 partition top-level dirs (raw/, intermediate/, final/, archive/) plus `scripts/`, `data/`, and the 2 runtime dotfiles
2. `benchmark/datasets/`, `benchmark/v0.11/`, `benchmark/results/`, `benchmark/results_v2.0_frozen/`, `benchmark/results_aws/` no longer exist
3. `verify_authoritative_numbers.py` re-runs cleanly with identical headline numbers
4. `inspect_all_configs.py` re-runs cleanly with identical cross-config table
5. Zero grep matches in `benchmark/scripts/` + `src/benchmark/` for the OLD paths (`benchmark/datasets/processed`, `benchmark/v0.11`, `benchmark/results_aws/FINAL`, `benchmark/results_aws/_archive_originals_2026-05-19`)
6. All 493 manifest files still SHA-256-verifiable (content untouched, only paths changed)
7. Final commit pushed cleanly with NO Claude co-author
