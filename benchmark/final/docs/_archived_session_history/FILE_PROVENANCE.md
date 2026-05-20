# File Provenance — `benchmark/results_aws/`

> **Purpose**: For every file in this directory, state: (a) what it contains, (b) whether to use it for the paper, (c) why it exists. Useful when scanning the directory you can tell at a glance which file is the "real" one.
> **Last reviewed**: 2026-05-16 (session 8 end). Files referenced as "currently re-running" will become final once those tasks complete.

> ### ⚠ 2026-05-19 ARCHIVE NOTICE
> The 6 active result dirs described in this doc — `run_stackA_main431_newprompt/`, `ablation_v4_newprompt/`, `sota_llama_3_3_70b/`, `sota_deepseek_v3/`, `sota_drain/`, `phase46_noprompt/` — were MOVED into `_archive_originals_2026-05-19/` on 2026-05-19. Canonical paper-ready copies now live in `FINAL/`. See `FINAL/README.md` for the new layout and `_archive_originals_2026-05-19/_ARCHIVED.md` for the source→archive map. A SHA-verified zip backup sits at `originals_backup_2026-05-19.zip`. The path tables below describe the **historical layout** prior to the move; replace `<dirname>/` with either `FINAL/<canonical-name>/` (for paper use) or `_archive_originals_2026-05-19/<dirname>/` (for provenance) when looking files up.

---

## Top-level

| File | What | Use for paper? |
|------|------|----------------|
| `RUNS_INDEX.md` | Master index of all runs and their status | ✅ Always read first |
| `RESULTS_SUMMARY.md` | Pre-formatted Table 7 LaTeX (auto-generated) | ⚠️ Outdated as of session 8; regenerate after SOTA re-runs complete |
| `BUG_HISTORY.md` | All 8 bugs found in scripts and their fixes | ✅ Cite as supplementary methodology |
| `METHODOLOGY.md` | Eval rules, exclusion list rationale, temperature choice | ✅ Cite in paper §3 methodology |
| `FILE_PROVENANCE.md` | This file — per-file authoritative-status map | ✅ Reference for reviewers |
| `CURRENT_RUNS.md` | Which background jobs are running right now | ⚠️ Living document; delete or empty after all jobs complete |

---

## `run_stackA_main431/` — Phase 4.2 main benchmark (Tables 2/3/4)

| File | What | Use for paper? |
|------|------|----------------|
| `results.json` | Raw per-case results, 431 cases, BEFORE 33-case remine relabel | ❌ Pre-merge |
| `results_merged.json` | Same 431 cases AFTER applying remine label fix from `rerun_remine33_enriched/` | ✅ **AUTHORITATIVE for Tables 2/3/4** |
| `results_merged_enriched.json` | Same as above + BERTScore + cosine similarity columns | ✅ **AUTHORITATIVE for semantic metrics** |
| `summary.json` | Aggregate stats computed from `results.json` (pre-merge) | ❌ Pre-merge — shows RCA 79.3% which is BEFORE the remine fix. Kept for provenance only. |
| `benchmark_result.json` | Identical to `summary.json` (legacy duplicate) | ❌ Same as summary.json |
| `paper_tables.md` / `paper_tables.tex` | Pre-formatted Tables 2/3/4 from `results_merged.json` | ✅ Direct LaTeX source for paper |
| `all_tables.md` / `all_tables.tex` | Same content, different bundling | ✅ Alternative format |
| `combined_results.md` | Multi-table summary including main + drain | ✅ Quick overview |
| `manifest.json` | Dataset hash + git SHA at run time | ✅ Reproducibility manifest |
| `run.log` / `benchmark.log` | Raw stdout/stderr from the benchmark run | 🗄️ Reference only |

**Key numbers (post-merge, paper-authoritative)**:
- Overall: 382/431 = **88.6%**
- Annotation: 180/218 = **82.6%**
- RCA: 202/213 = **94.8%**
- BERTScore F1: **0.7975** | Cosine: 0.2756

---

## `rerun_remine33_enriched/` — OpsEval-remine label fix

| File | What | Use for paper? |
|------|------|----------------|
| `results.json` | Re-run of 33 OpsEval-remine cases that were originally labeled wrong | ✅ Merged into `run_stackA_main431/results_merged.json` |

**Reason this exists**: Original Phase 4.2 run scored OpsEval-remine cases at 0% because of label-format mismatch (expected_root_cause field was named differently). After fixing the label extraction, all 33 cases passed. The fix was merged into the main results rather than rerunning everything.

---

## `sota_drain/` — Drain log parser baseline (Table 7 row)

| File | What | Use for paper? |
|------|------|----------------|
| `results.jsonl` | 202 annotation results from Drain template parser (no RCA capability) | ✅ Table 7 Drain row |
| `summary.json` | `{"annotation_accuracy": 0.505, "rca_accuracy": null, ...}` | ✅ Reference for paper |

**Status**: COMPLETE and stable since 2026-05-15. Not affected by any of the bugs in `BUG_HISTORY.md` (Drain doesn't use the LLM router or system prompts).

**Key number**: Annotation 102/202 = **50.5%**. RCA: N/A (Drain is a log template parser, not a reasoning system).

---

## `sota_llama_3_3_70b/` — Llama 3.3-70B PROMPTED SOTA (Table 7)

| File | What | Use for paper? |
|------|------|----------------|
| `results.jsonl` | **CURRENTLY RE-RUNNING** at temperature=0.05 (session 8) | ⏳ Will be authoritative |
| `results_t0_BAK.jsonl` | Previous temperature=0 run | 🗄️ Kept for provenance |
| `run_t005.log` | Live log of the re-run | 🗄️ Diagnostic |

**Why re-running**: The t=0 run pre-dated several bug fixes (#1 #2 #3 #7). Re-run uses fixed script + non-zero temperature so re-runs don't return identical deterministic outputs.

---

## `sota_deepseek_v3/` — DeepSeek V3.2 PROMPTED SOTA (Table 7)

| File | What | Use for paper? |
|------|------|----------------|
| `results.jsonl` | **CURRENTLY RE-RUNNING** at temperature=0.05 (session 8) | ⏳ Will be authoritative |
| `results_t0_BAK.jsonl` | Previous t=0 run with **103 duplicate RCA records** from overlapping resume runs | ❌ Use only after post-hoc dedup. After dedup + 71-case exclusion: ann=90.6%, rca=67.7%, overall=81.8% |
| `run_t005.log` | Live log of the re-run | 🗄️ Diagnostic |

---

## `phase46_noprompt/` — No-prompt cross-model replication (Table 8)

This directory has the most file clutter because of multiple iterations during bug investigation. Per-file:

| File | Size | Status | Use for paper? |
|------|------|--------|----------------|
| `llama_noprompt_clean.jsonl` | 0 B currently | **RE-RUNNING t=0.05** | ⏳ Will be authoritative |
| `llama_noprompt_clean_t0_BAK.jsonl` | 296 KB | Previous fresh single-run at t=0 | 🗄️ Provenance |
| `llama_noprompt_v2.jsonl` | 462 KB | **CONTAMINATED** — duplicates from 3 overlapping runs (1st partial 150, resume, fresh full) | ❌ Use only with last-wins dedup |
| `llama_noprompt_bak.jsonl` | 118 KB | First failed run (0% annotation, no NL fallback) | ❌ Pre-fix, broken |
| `llama_noprompt_final_bak.jsonl` | 386 KB | 202 ann + partial RCA from session 6 | ❌ Pre-fix, partial |
| `llama_noprompt_rescored_bak.jsonl` | 109 KB | Intermediate rescoring artifact | ❌ Pre-fix |
| `llama_v2.log` | 25 KB | Log of contaminated v2 run | 🗄️ Diagnostic |
| `llama_clean.log` | 23 KB | Log of t=0 clean run | 🗄️ Diagnostic |
| `llama_clean_t005.log` | 0 B currently | Live log of t=0.05 re-run | 🗄️ Diagnostic |
| `deepseek_noprompt_v2.jsonl` | 0 B currently | **RE-RUNNING t=0.05** | ⏳ Will be authoritative |
| `deepseek_noprompt_v2_t0_BAK.jsonl` | 302 KB | Previous v2 (inline excluded) at t=0 | 🗄️ Provenance — ann=87.1%, rca=74.8% (clean) |
| `deepseek_noprompt.jsonl` | 384 KB | Older pre-fix DeepSeek (excluded 71 not handled inline) | ❌ Pre-fix; use only with post-hoc filter |
| `deepseek_v2.log` | 23 KB | Log of v2 t=0 run | 🗄️ Diagnostic |
| `deepseek_v2_t005.log` | 0 B currently | Live log of t=0.05 re-run | 🗄️ Diagnostic |

**Per-file selection rule**: Read `*_clean.jsonl` (no suffix BAK) for paper. The BAK files exist solely for reviewer provenance ("here's what the deterministic run produced") and shouldn't be cited as primary results.

---

## `archive/` — Smoke tests and gate comparisons

| Path | What | Use for paper? |
|------|------|----------------|
| `gate15_comparison.md` | Stack A vs Stack B 15+15 smoke gate comparison | ✅ Supporting evidence for paper §3 (dual-stack methodology) |
| `smoke_tests/run_stackA_15plus15/` | Stack A gate smoke results | 🗄️ Reference |
| `smoke_tests/run_stackA_5plus5_oninstance/` | Stack A on-instance smoke (~14.2 ms RTT) | 🗄️ Reference for "run from instance" methodology |
| `smoke_tests/run_stackB_15plus15/` | Stack B gate smoke | 🗄️ Reference |
| `smoke_tests/run_stackB_5plus5_v2/` | Stack B AWQ-marlin smoke (final working config) | 🗄️ Reference |
| `smoke_tests/run_stackB_5plus5_v1_bad/` | Failed FP8 attempt (VRAM overflow) | ❌ Negative-result archive |
| `smoke_tests/sota_smoke_*/` | Initial 3-case Bedrock connectivity checks | 🗄️ Reference |
| `smoke_tests/*.log` | Captured stdout from gates | 🗄️ Diagnostic |

---

## On AWS instance (NOT in this directory)

These exist on the AWS instance at `/mnt/aiops-repo/benchmark/results/` and should NOT be copied locally because they're invalid:

| Path on instance | Why broken | Status |
|------------------|------------|--------|
| `ablation_full_BROKEN/` | First valid (pre-bug-discovery), kept for reference | Mostly OK but bert_f1=0 from disk full |
| `ablation_single_4b_BROKEN/` | Bug #4 (model_router caching): actually ran 4B+14B not 4B+4B | ❌ DO NOT USE |
| `ablation_single_14b_BROKEN/` | Bug #4: actually ran 4B+14B not 14B+14B | ❌ DO NOT USE |
| `ablation_no_structured_BROKEN/` | Bug #4 + Bug #6: ran identical to full | ❌ DO NOT USE |
| `ablation_single_4b_SMOKE/` | 5-case smoke verification of bug fix | 🗄️ Verification artifact |
| `ablation_single_14b_SMOKE/` | 5-case smoke verification | 🗄️ Verification artifact |

All renamed with `_BROKEN` or `_SMOKE` suffix to avoid accidental use. The real fixed-ablation results will live at the same paths without suffixes once the in-progress run finishes.
