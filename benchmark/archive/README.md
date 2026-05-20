# benchmark/archive/

Historical / superseded artifacts. Nothing here is read by active scripts. Preserved for evidence trail + reproducibility.

## Contents

| Path | What | Why preserved |
|---|---|---|
| `v0.9.1_jarvis_baseline/` | February 2026 Jarvis Labs A5000 runs (pre-AWS, pre-v1-paper-submission). 74 files in `2026-02-06_v0.9.1/`. | v1 paper baseline reference. (Also see the byte-identical Phase-0 safety copy that was REMOVED on 2026-05-20: `results_v2.0_frozen/` was redundant once we adopted defense-in-depth.) |
| `originals_2026-05-19/` | Snapshot of the original session-10/11 result dirs before they were curated into `benchmark/final/`. Includes per-dir `_ARCHIVED_NOTICE.md` files. | Provenance for the canonical `final/` build (see `final/MANIFEST.md` for source → dest map). |
| `run_stackA_main431_OLD_PROMPT/` | First main run with the OLD RCA prompt (pre-2026-05-16T05:27 prompt fix). v1 paper headline numbers came from here. | Diff anchor for the new-vs-old prompt comparison; not for paper-defense use. |
| `rerun_remine33_enriched/` | Partial re-run of 33 OpsEval re-mine cases after the L5614 enrichment fix. | Bug-fix evidence; numbers superseded by main re-run + ablation v4. |
| `smoke_tests/` | All 5+5 / 15+15 dual-stack smoke runs from sessions 2–4 (Stack A Ollama + Stack B vLLM AWQ). | Dual-stack gate evidence; cited from `final/infrastructure/gate15_comparison.md`. |
| `originals_backup_2026-05-19.zip` | Defense-in-depth zip of all originals at the time of the session-11 archive operation. 69 entries, SHA-verified at build time. | Single-file recoverable form of `originals_2026-05-19/`. |
| `aiops_archive_2026-05-17.tar.gz` | Defense-in-depth tarball built on the AWS instance at session-10 close (~5.75 MB, 384 entries). SHA `351aa6734b3063ed2ec5d03cee88909d23608d607b6217deb88afd40a596a7b6`. | Instance-side checkpoint before instance was stopped on 2026-05-17. |

## Defense-in-depth backup layers (still valid)

1. `benchmark/archive/originals_2026-05-19/` — file-level snapshot
2. `benchmark/archive/originals_backup_2026-05-19.zip` — zip
3. `benchmark/archive/aiops_archive_2026-05-17.tar.gz` — instance-side tarball
4. AWS EBS snapshot `snap-01b191aedbf46b598` — cloud disaster recovery
5. **(new, 2026-05-20)** `<repo>/../Backups/benchmark_master_backup_2026-05-20.zip` — pre-reorg snapshot of entire `benchmark/` tree (14.27 MB, SHA `7b01aef090…`)

## Removed during 2026-05-20 reorg

- `benchmark/results_v2.0_frozen/` — byte-identical Phase-0 safety copy of `benchmark/results/`. Removed (deduplicated) since `archive/v0.9.1_jarvis_baseline/` now preserves the same content under a clearer name + multiple backup layers above still cover it.
- `benchmark/results_aws/archive/gate15_comparison.md` — byte-identical to `benchmark/final/infrastructure/gate15_comparison.md` (SHA `83706a84e4e8…`); removed, canonical version retained in final/.
- 2× internal BUG_HISTORY.md.NEW + METHODOLOGY.md.NEW (META copies in FINAL/, byte-identical to canonical originals).

## Provenance

Reorganized 2026-05-20 (session 12) from the legacy `benchmark/results/`, `benchmark/results_v2.0_frozen/`, and `benchmark/results_aws/` (non-FINAL) trees. See `benchmark/final/audit/REORG_PROPOSAL_2026-05-20.md`.
