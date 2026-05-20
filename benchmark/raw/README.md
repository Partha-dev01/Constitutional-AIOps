# benchmark/raw/

Third-party raw datasets, never modified after download. Files in this directory are gitignored (see `.gitignore`); they live on disk but are not committed.

| Subdir / file | Source | Purpose |
|---|---|---|
| `loghub/` | <https://github.com/logpai/loghub> | HDFS_2k, BGL_2k, Apache_2k, OpenSSH_2k, Linux_2k — structured-CSV log datasets |
| `lemma_rca/` | <https://github.com/microsoft/LemmaRCA> | LEMMA-RCA microservices RCA dataset (~5.5 GB; large files kept outside the repo proper) |
| `opseval/` | <https://github.com/luo-junyu/OpsEval> | OpsEval Wired Network EN/ZH multiple-choice diagnostic Qs |
| `apache_candidates.jsonl` | mining output | Apache mining script output (40 candidates, fed Apache annotation cases in benchmark_431) |
| `openssh_candidates.jsonl` | mining output | OpenSSH mining script output (40 candidates) |
| `opseval_remine_s2.jsonl` | mining output | OpsEval re-mining stage-2 output (33 candidates judged by Qwen3-4B-Instruct — see Phase 2 transcript audit + METHODOLOGY.md) |

## Regenerate

```bash
python benchmark/scripts/download_datasets.py        # core datasets only
python benchmark/scripts/download_datasets.py --all  # ALL including LEMMA-RCA
```

## Provenance

Moved here 2026-05-20 from the legacy path `benchmark/datasets/raw/` as part of the 4-partition reorg (raw / intermediate / final / archive). See `benchmark/final/audit/REORG_PROPOSAL_2026-05-20.md` for the full plan and `benchmark/final/audit/CV_PASS2_CODEBASE_AUDIT.md` Part B for per-file metadata.
