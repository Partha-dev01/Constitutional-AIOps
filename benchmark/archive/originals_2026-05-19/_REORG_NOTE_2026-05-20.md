# Reorg note — 2026-05-20

The per-dir `_ARCHIVED_NOTICE.md` files inside this folder reference paths from
the pre-reorg tree (e.g., `benchmark/results_aws/FINAL/main_benchmark/`). Those
paths no longer exist as of 2026-05-20.

**Current canonical paths (post-reorg)**:

| Pre-reorg path used in notices | Post-reorg path |
|---|---|
| `benchmark/results_aws/FINAL/` | `benchmark/final/` |
| `benchmark/results_aws/FINAL/main_benchmark/` | `benchmark/final/main_benchmark/` |
| `benchmark/results_aws/FINAL/ablation_v4/` | `benchmark/final/ablation_v4/` |
| `benchmark/results_aws/FINAL/sota_baselines/` | `benchmark/final/sota_baselines/` |
| `benchmark/results_aws/FINAL/phase46_no_prompt/` | `benchmark/final/phase46_no_prompt/` |
| `benchmark/results_aws/originals_backup_2026-05-19.zip` | `benchmark/archive/originals_backup_2026-05-19.zip` |
| `benchmark/results_aws/aiops_archive_2026-05-17.tar.gz` | `benchmark/archive/aiops_archive_2026-05-17.tar.gz` |

The notices' content is otherwise historically accurate at the time they were
written (2026-05-19) and is preserved verbatim for forensic continuity. Do not
edit the notices to retrofit new paths — use this single mapping table instead.

See also: `benchmark/final/audit/REORG_PROPOSAL_2026-05-20.md`, `benchmark/archive/README.md`.
