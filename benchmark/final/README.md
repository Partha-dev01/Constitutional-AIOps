# FINAL/ — paper-ready result files

_Built: 2026-05-19 04:58 UTC_  
_Builder script: `benchmark/scripts/ops/build_final_results.py`_

## Quick map (which file backs which paper artifact)

| Paper artifact | File |
|---|---|
| Table 2 (system standalone, rich eval) | `main_benchmark/results.json` |
| Table 2 companion (matched eval) | `main_benchmark/results_sota_eval_431.json` |
| Table 5 (Latency) | `main_benchmark/summary.json` |
| Table 6 (Ablation) | `ablation_v4/matched_eval_table.md` (canonical) + `ablation_v4/ablation_*/results_sota_eval_431.json` (raw) |
| Table 7 Ours row | `main_benchmark/results_sota_eval_431.json` |
| Table 7 Llama 3.3-70B | `sota_baselines/llama_3_3_70b.jsonl` |
| Table 7 DeepSeek V3.2 | `sota_baselines/deepseek_v3.jsonl` |
| Table 7 Drain | `sota_baselines/drain.jsonl` + `drain_summary.json` |
| Table 8 Llama no-prompt | `phase46_no_prompt/llama_noprompt_clean.jsonl` |
| Table 8 DeepSeek no-prompt | `phase46_no_prompt/deepseek_noprompt_v2.jsonl` |
| §3 dual-stack methodology | `infrastructure/gate15_comparison.md` |
| §3 eval methodology | `METHODOLOGY.md` |
| §3.3 bug-investigation provenance | `BUG_HISTORY.md` |

## Integrity & audit

- `MANIFEST.md` — every file with source path + SHA-256
- `AUDIT_REPORT.md` — per-file content audit (record counts, missing fields,
  duplicate IDs, BERT-zero scan, etc.)

## Source paths preserved

Every file in this directory was COPIED (not moved) from its original location.
After the 2026-05-20 reorg the sources live under `benchmark/archive/originals_2026-05-19/`.
See `MANIFEST.md` for the source→dest mapping.

## What is NOT in this directory (and why)

- `ablation_v4_newprompt/ablation_table.md` / `.tex` / `ablation_results.json` —
  these contain runner.py **rich-eval** ablation numbers (e.g. single_4b RCA = 99.1%)
  which are broken: rule_score gives partial credit to literal-opposite answers.
  See `AUDIT_REPORT.md`.
- `benchmark/archive/run_stackA_main431_OLD_PROMPT/` (OLD prompt v1-paper reference) — kept for diff/provenance only.
- `benchmark/archive/v0.9.1_jarvis_baseline/` — Jarvis-era v1.0 / v0.9.1 frozen state.
- `phase46_noprompt/*_BAK*` and `*.log` — earlier iteration artifacts, kept for
  provenance but not paper-ready (see `phase46_no_prompt/README.md` selection rule).
