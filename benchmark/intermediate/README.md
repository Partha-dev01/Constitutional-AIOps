# benchmark/intermediate/

Processed datasets + mining-output candidates that sit between `benchmark/raw/` (third-party) and `benchmark/final/` (paper-ready). These files ARE tracked in git (small, diffable, paper-relevant).

> **Canonical paper dataset**: `datasets/benchmark_431_seed42.json` (218 annotation + 213 RCA = 431 cases; seed 42). All other JSONs in `datasets/` are historical builds, intermediates, or metadata. See the table below for full provenance.

## Layout

| Subdir | Contents | Source |
|---|---|---|
| `datasets/` | Clean canonical benchmark JSONs that feed the runner | Built from `benchmark/raw/` via `benchmark/scripts/prep/prepare_datasets.py` + `clean_dataset.py` + manual curation |
| `candidates/` | Mining-stage candidate JSONLs (Apache 40, OpenSSH 40, OpsEval remine 33) | Output of `benchmark/scripts/mine_*.py` before vetting + integration into `benchmark_431_seed42.json` |

## datasets/ — canonical inputs to the runner

| File | Use | Notes |
|---|---|---|
| `annotation_clean.json` | Annotation eval cases | 138 cases |
| `rca_clean.json` | RCA eval cases | 180 cases |
| `benchmark_150_seed42.json` | v1 paper-era 150-case benchmark | Historical |
| `benchmark_150_seed42_with_chinese.json` | v1 + 39 Chinese RCA cases | Historical (Chinese cases later excluded — see `excluded_rca_cases.json`) |
| `benchmark_400_seed42.json` | Phase 4.7 SOTA-baseline benchmark | 400 cases, stratified |
| `benchmark_431_seed42.json` | **Canonical paper benchmark (paper v2)** | 218 ann + 213 RCA |
| `excluded_rca_cases.json` | 71 RCA cases excluded from matched eval | 39 Chinese + 32 MC bare-letter |
| `annotation_test.json` | Dirty local test JSON | Per memory: **do NOT commit content changes**; move was OK |
| `rca_test.json` | Dirty local test JSON | Per memory: **do NOT commit content changes**; move was OK |

## candidates/ — mining-stage outputs

| File | Notes |
|---|---|
| `apache_candidates.jsonl` | Apache log mining output (40 candidates, judged Qwen3-4B-Instruct) |
| `openssh_candidates.jsonl` | OpenSSH mining output (40 candidates) |
| `opseval_remine.jsonl` | OpsEval re-mining stage-2 output (33 candidates) — same as `benchmark/raw/opseval_remine_s2.jsonl`; the v0.11 path is the version that landed in `benchmark_431_seed42.json` |

## Provenance

Moved here 2026-05-20 from the legacy paths:
- `benchmark/datasets/processed/` → `benchmark/intermediate/datasets/` (9 files, all tracked, R100 rename)
- `benchmark/v0.11/` → `benchmark/intermediate/candidates/` (3 files, R100 rename)

See `benchmark/final/audit/REORG_PROPOSAL_2026-05-20.md` for the full plan and `benchmark/final/audit/CV_PASS2_CODEBASE_AUDIT.md` Part B for per-file metadata.
