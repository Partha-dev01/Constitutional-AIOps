# Archived originals — 2026-05-19

_Moved here: 2026-05-19 05:12 UTC_

These are the original result directories whose canonical paper-ready copies now
live in `benchmark/results_aws/FINAL/`. They were MOVED here (not deleted) to
keep `results_aws/` clean while preserving full provenance.

## Defense-in-depth

- This folder (file-level access to originals)
- `benchmark/results_aws/originals_backup_2026-05-19.zip` (zip backup with SHA-verified contents)
- `benchmark/results_aws/aiops_archive_2026-05-17.tar.gz` (earlier tarball)
- EBS snapshot `snap-01b191aedbf46b598` (cloud disaster recovery)

## Map (archived dir → canonical FINAL/ location)

| Archived dir | Canonical now lives at |
|---|---|
| `run_stackA_main431_newprompt/` | `FINAL/main_benchmark/` |
| `ablation_v4_newprompt/` | `FINAL/ablation_v4/` |
| `sota_llama_3_3_70b/` | `FINAL/sota_baselines/llama_3_3_70b.jsonl` |
| `sota_deepseek_v3/` | `FINAL/sota_baselines/deepseek_v3.jsonl` |
| `sota_drain/` | `FINAL/sota_baselines/drain.jsonl + drain_summary.json` |
| `phase46_noprompt/` | `FINAL/phase46_no_prompt/` |

## Restoring

If a downstream script or doc still expects the original path:

```bash
# Option 1: move back from this archive
mv benchmark/results_aws/_archive_originals_2026-05-19/<dirname> benchmark/results_aws/

# Option 2: extract from zip
unzip benchmark/results_aws/originals_backup_2026-05-19.zip -d benchmark/results_aws/
```

But the recommended fix is to update the script/doc to reference `FINAL/` instead.

## Constraint reminders (preserved from prior sessions)

- `run_stackA_main431/` (OLD-prompt v1 paper reference) was NOT archived — left in place
- `archive/` (smoke tests) was NOT archived — already an archive
- All `*_BAK*` files in archived dirs were preserved as-is (do NOT delete per provenance rule)
- `*_BROKEN` dirs on the AWS instance are NOT affected by this operation (they're on instance only)
