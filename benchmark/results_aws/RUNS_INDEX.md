# Benchmark Results — AWS Runs Index

_Last updated: 2026-05-16 (Session 8 end)_

> ### ⚠ 2026-05-19 ARCHIVE NOTICE
> Active result dirs (`run_stackA_main431_newprompt/`, `ablation_v4_newprompt/`, `sota_*`, `phase46_noprompt/`) were moved into `_archive_originals_2026-05-19/` on 2026-05-19. Canonical paper-ready copies are now in `FINAL/` (see `FINAL/README.md` and `FINAL/SUMMARY.md`). Ablation v4 is COMPLETE — for the canonical matched-eval Table 6 use `FINAL/ablation_v4/matched_eval_table.md`. Path tables below reflect the old layout; update mentally by substituting `FINAL/<dest>/` for paper use or `_archive_originals_2026-05-19/<dirname>/` for provenance.

> **Read first when scanning this directory.** For deeper detail see:
> - `FILE_PROVENANCE.md` — per-file authoritative status
> - `BUG_HISTORY.md` — 8 bugs found and fixed
> - `METHODOLOGY.md` — eval rules, 71-case exclusion, temperature choice
> - `CURRENT_RUNS.md` — what's running right now
> - `BROKEN_ABLATIONS.md` — invalidated runs on AWS instance (DO NOT use)
> - `phase46_noprompt/README.md` — per-file map of that subdirectory

---

## Active results (source of truth for paper) — SESSION 9 END

> **AUTHORITATIVE SWITCH (2026-05-16)**: The `run_stackA_main431_newprompt/` directory is now the authoritative source for paper Tables 2/3/4. The previous `run_stackA_main431/` directory contains v1-paper-state (OLD prompt) results — preserved for diff/provenance only, do NOT cite from it.

| Directory / file | Phase | Cases | Numbers | Paper table |
|------------------|-------|-------|---------|-------------|
| `run_stackA_main431_newprompt/results.json` | **4.2 Main benchmark (NEW prompt)** | 431 | **87.5%** overall, Ann 82.6%, RCA **92.5%** | Tables 2/3/4 ⭐ |
| `run_stackA_main431_newprompt/results_sota_eval_431.json` | **4.2 + matched-eval rescore** | 431 | Ann 82.6%, **RCA 80.3% matched** (+9.2pp vs Llama, +13.4pp vs DeepSeek) | Table 7 "Ours" row ⭐ |
| `run_stackA_main431/results_merged.json` | 4.2 v1 reference (OLD prompt) | 431 | Ann 82.6%, RCA 94.8%, Overall 88.6% (rich eval) — DO NOT CITE | Diff/provenance only |
| `run_stackA_main431/results_merged_enriched.json` | 4.2 + semantic metrics | 431 | Same + BERTScore + cosine per-case | Tables 2/3/4 |
| `run_stackA_main431/paper_tables.md/.tex` | 4.2 LaTeX | — | Pre-formatted tables | Direct paper source |
| `sota_llama_3_3_70b/results.jsonl` (400-case, t=0.05) | **4.7 SOTA Llama prompted** | 400 | Ann 91.6% (185/202), RCA 71.7% (91/127), Overall 83.9% | Table 7 — superseded by 431 extension when complete |
| `sota_deepseek_v3/results.jsonl` (400-case, t=0.05) | **4.7 SOTA DeepSeek prompted** | 400 | Ann 90.6% (183/202), RCA 67.7% (86/127), Overall 81.8% | Table 7 — superseded by 431 extension when complete |
| `phase46_noprompt/llama_noprompt_clean.jsonl` (400-case, t=0.05) | **4.6 SOTA Llama no-prompt** | 400 | Ann 69.8% (141/202), RCA 74.0% (94/127), Overall 71.4% | Table 8 — superseded by 431 extension when complete |
| `phase46_noprompt/deepseek_noprompt_v2.jsonl` (400-case, t=0.05) | **4.6 SOTA DeepSeek no-prompt** | 400 | Ann 88.6% (179/202), RCA 74.0% (94/127), Overall 83.0% | Table 8 — superseded by 431 extension when complete |
| `sota_drain/results.jsonl` + summary.json | **4.7 SOTA — Drain log parser** | 202 (ann only) | Ann 50.5%, RCA N/A | Table 7 Drain row |
| `archive/gate15_comparison.md` | Stack A vs Stack B gate | 30 | Acc Δ pass, Speedup 1.51× | §3 dual-stack methodology |

**Path A methodological decision (2026-05-16)**: Both differences between SOTA (N=400, run_sota_baselines.py eval) and main benchmark (N=431, runner.py eval) are being eliminated by (a) re-running SOTA on the 431-case dataset via append-resume (extends each 400-record output by 31 new cases) and (b) re-scoring our system's `actual_output` strings through `run_sota_baselines.py`'s `_eval_annotation` / `_eval_rca` to produce an eval-matched "Ours" row at N=431. Numbers above will be superseded — see `CURRENT_RUNS.md` and `METHODOLOGY.md` §6.

## In progress (session 8/9 re-runs)

| Output path | Phase | ETA |
|-------------|-------|-----|
| `/mnt/runs/ablation_v3.log` (on instance) | **4.3 Ablation — 8 configs with all flags wired** | ~6-7 hrs remaining (config 5 of 8 at RCA 50/198) |
| `sota_llama_3_3_70b/results.jsonl` (extending 400 → 431) | **4.7 Path A: Llama prompted +31 cases** | ~10-25 min |
| `sota_deepseek_v3/results.jsonl` (extending 400 → 431) | **4.7 Path A: DeepSeek prompted +31 cases** | ~10-25 min |
| `phase46_noprompt/llama_noprompt_clean.jsonl` (extending 400 → 431) | **4.6 Path A: Llama no-prompt +31** | Pending (after Pair 1) |
| `phase46_noprompt/deepseek_noprompt_v2.jsonl` (extending 400 → 431) | **4.6 Path A: DeepSeek no-prompt +31** | Pending (after Pair 1) |
| `run_stackA_main431/results_sota_eval_431.json` | **4.7 Path A: re-score our outputs with SOTA eval** | ~1 min (after all 4 above done) |

## Preserved BAK files (for provenance)

| File | What it preserves |
|------|-------------------|
| `sota_llama_3_3_70b/results_t0_BAK.jsonl` | Llama prompted at t=0 — pre temperature flag |
| `sota_deepseek_v3/results_t0_BAK.jsonl` | DeepSeek prompted at t=0 — has 103 duplicate RCA records |
| `phase46_noprompt/llama_noprompt_clean_t0_BAK.jsonl` | Llama no-prompt at t=0 (fresh, fixed script) |
| `phase46_noprompt/deepseek_noprompt_v2_t0_BAK.jsonl` | DeepSeek no-prompt at t=0 v2 (inline-excluded, fixed) |
| `phase46_noprompt/deepseek_noprompt.jsonl` | Older DeepSeek no-prompt BEFORE excluded-inline fix (session 6) |
| `phase46_noprompt/llama_noprompt_v2.jsonl` | Contaminated 641-record v2 (3 overlapping runs) |
| `phase46_noprompt/llama_noprompt_{bak,final_bak,rescored_bak}.jsonl` | Earlier Llama attempts (broken or partial) |

Do NOT use any `_BAK` or `_bak` file as a primary result without explicit reason. They exist so reviewers can verify iteration history.

## Pending (after current runs)

| Phase | Cases | Blocked on |
|-------|-------|-----------|
| **Phase 5 statistics** (BCa bootstrap CIs, McNemar, Cohen's h) | All saved results | All re-runs complete |
| **Tables 2/3/4/6/7/8 regeneration** with final numbers + CIs | — | Phase 5 |
| **`RESULTS_SUMMARY.md` regeneration** | — | All 5 in-progress jobs complete |
| Phase 4.5 graph experiments (LEMMA 5-fold + cold-start curve) | 80 + 20 | Ablation complete |
| Phase 4.6 Part A (5 paraphrased prompts × 400 cases) | 2000 inferences | Ablation complete |

---

## Gate comparison (Stack A accuracy vs Stack B latency)

Established session 4-5, unchanged:

| Stack | N | Accuracy | P95 Latency | Speedup |
|-------|---|----------|-------------|---------|
| Stack A (Ollama Q4_K_M) | 15+15 | 93.3% | 65.96 s | 1× |
| Stack B (vLLM AWQ marlin) | 15+15 | 100.0% | 43.71 s | **1.51×** |

- Gate 1 (Δ accuracy < 2 pp): **conditional pass** (Stack A's 2 fails were OpsEval knowledge-Qs later excluded — same effective accuracy).
- Gate 2 (P95 speedup ≥ 1.5×): **pass** (65.96/43.71 = 1.51×).

---

## Key data warnings

1. **OpenSSH annotation 50%** is NOT a bug. All 20 failures are false positives (single auth events flagged as anomaly), zero false negatives on real brute force. Disclosed in paper Table 4.
2. **71 RCA cases excluded** from accuracy denominators across ALL systems for fairness. List in `benchmark/datasets/processed/excluded_rca_cases.json`. 39 Chinese-language expected + 32 bare-letter MC. See `METHODOLOGY.md` §2.
3. **`run_stackA_main431/summary.json` vs `results_merged.json`** discrepancy is intentional: `summary.json` shows pre-remine-fix numbers (RCA 79.3%), `results_merged.json` shows post-fix (RCA 94.8%). **Paper uses `results_merged.json`.** See `FILE_PROVENANCE.md`.
4. **DeepSeek t=0 prompted SOTA has 103 duplicate RCA records** in `*_t0_BAK.jsonl` from overlapping resume runs. After last-wins dedup + 71-case exclusion: ann=90.6%, rca=67.7%, overall=81.8%. The t=0.05 re-run gives a clean file without this artifact.
5. **All 4 `ablation_*_BROKEN/` directories on the AWS instance** are NOT in this local directory and should NEVER be SCP'd as results. They suffer from the model_router config-caching bug (#4) and effectively ran identical to full. See `BROKEN_ABLATIONS.md`.
6. **`bert_f1: 0.0` in older ablation summaries** was due to AWS root disk being full when the BERTScore model tried to download. Disk has now been resized 40→80 GB. Recomputable post-hoc on saved `actual_output` strings if needed.
7. **Sampling temperature**: main benchmark and ablation use 0.0 (deterministic). SOTA prompted/no-prompt RE-RUNS use 0.05 to avoid the deterministic Llama==DeepSeek 95/127 RCA tie. Reproducible re-runs at the same temperature should produce similar but not identical results.

---

## How to regenerate `RESULTS_SUMMARY.md`

Once all in-progress jobs complete:
```bash
cd "<repo root>"
python benchmark/scripts/compile_results.py \
    --out benchmark/results_aws/RESULTS_SUMMARY.md
```

This script reads `run_stackA_main431/results_merged.json` for the main results, the SOTA `*.jsonl` files for Table 7, and the no-prompt files for Table 8. See `METHODOLOGY.md` for the exact aggregation rules.

---

## Bug history

See `BUG_HISTORY.md`. Summary of session 7-8 fixes:
1. `run_sota_baselines.py`: `--rca 0` argparse bug
2. `run_sota_baselines.py`: 71-case inline exclusion
3. `run_sota_baselines.py`: summary denominator
4. `src/agents/model_router.py`: stale config reference (CRITICAL — broke all ablation routing)
5. `src/agents/fast_annotator.py`: confidence type coercion
6. `src/benchmark/runner.py`: missing `no_structured` and `skip_constitutional` ablation flags
7. `run_sota_baselines.py`: temperature now CLI-configurable
8. AWS root EBS expanded 40 → 80 GB
