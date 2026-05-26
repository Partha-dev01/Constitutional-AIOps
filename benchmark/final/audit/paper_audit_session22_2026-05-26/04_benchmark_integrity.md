# 04 — Benchmark Integrity Audit

_Auditor #4 of 5 — Session 22 paper revision QC._
_Run: 2026-05-26 (Windows / Python 3.12)._
_Mode: READ-ONLY across all source files; SHA-256 + count-based verification only._

## Scope

Verify the source-of-truth result files in `benchmark/final/` are self-consistent,
match MANIFEST.md SHA claims, and contain no orphan/stale references. Cross-check the
dataset, the 9 matched-eval result files (1 main + 8 ablation), the 3 SOTA baselines,
the 2 Phase 4.6 no-prompt files, the Phase 5 stats, and the Phase 4.5 forensic
artifacts.

## Method

| Step | What was done |
|---|---|
| 1 | Walked `benchmark/final/` and `benchmark/intermediate/datasets/` trees (59 + 9 files indexed). |
| 2 | Loaded `benchmark_431_seed42.json` and counted task-type composition, required fields, source mix, orphan task types, qa_mcq markers. |
| 3 | Loaded `excluded_rca_cases.json` (legacy path; alternative path `benchmark/datasets/processed/...` does not exist). |
| 4 | Counted `correct = True/False/None` per task-type for all 9 matched-eval files (`results_sota_eval_431.json`). |
| 5 | Recomputed accuracy from counting and compared to `phase5_stats.json`, `phase5_stats.md`, `matched_eval_table.md`, and SUMMARY.md. |
| 6 | Computed SHA-256 + size for 14 representative files via `hashlib.sha256` against MANIFEST.md "Post-D-1 state" table. |
| 7 | Parsed SOTA Llama/DeepSeek/Drain and Phase 4.6 no-prompt JSONLs; counted records, accuracies, duplicates, bert_f1 presence, NaN. |
| 8 | Verified phase45_graph forensic artifacts: `exp_4_5b_summary.json`, `_failed_run_log.txt`, 0-byte per-case JSONLs, stale `exp_4_5c_summary.json`. |
| 9 | Spot-checked 5 OpsEval-remined IDs (`RCA_OPSEVAL_RM_{014,020,023,006,025}`) for D-1 routing across dataset + main + ablation_full. |
| 10 | Cross-checked work files (`_*.json`, `_*.log`) and archive directories against SUMMARY.md / MANIFEST.md references. |

---

## Findings

### CRITICAL

#### C1 — MANIFEST.md "Post-D-1 state" SHA + size table is stale (does not include D-6 BERT-F1 recompute)

All 14 SOTA-eval and JSONL files modified by the D-6 BERT-F1 recompute (session 18,
2026-05-26) have a current SHA-256 that does NOT match the MANIFEST.md
"Post-D-1 state" table (lines 64-85 of `benchmark/final/MANIFEST.md`).

| File | Current size | MANIFEST size | Δ | Current SHA-256 (prefix) | MANIFEST SHA-256 (prefix) |
|---|---:|---:|---:|---|---|
| `benchmark/final/main_benchmark/results_sota_eval_431.json` | 329,301 | 319,622 | +9,679 | `f5fa8b577ca97710…` | `af0aebf65b9be6ce…` |
| `benchmark/final/main_benchmark/results.json` | 435,677 | 434,618 | +1,059 | `9ae84c215cf3c5d2…` | `4cb598a516ae6c9a…` |
| `benchmark/final/ablation_v4/ablation_full/results_sota_eval_431.json` | 328,482 | 318,793 | +9,689 | `fc9fad40f9c30e34…` | `71f86fb80a5ab74d…` |
| `benchmark/final/ablation_v4/ablation_single_4b/results_sota_eval_431.json` | 310,589 | 300,901 | +9,688 | (mismatch) | `bd7797a8db8ac009…` |
| `benchmark/final/ablation_v4/ablation_single_14b/results_sota_eval_431.json` | 319,368 | 309,694 | +9,674 | (mismatch) | `b436a9b3b372f250…` |
| `benchmark/final/ablation_v4/ablation_no_structured/results_sota_eval_431.json` | 215,809 | 206,745 | +9,064 | (mismatch) | `fe7d6317b3d64a1b…` |
| `benchmark/final/ablation_v4/ablation_no_system_prompt/results_sota_eval_431.json` | 272,624 | 263,555 | +9,069 | (mismatch) | `3b82a10af95d4415…` |
| `benchmark/final/ablation_v4/ablation_with_graph/results_sota_eval_431.json` | 326,724 | 317,040 | +9,684 | (mismatch) | `5eb5cb42cf52e8f7…` |
| `benchmark/final/ablation_v4/ablation_no_constitutional/results_sota_eval_431.json` | 274,265 | 264,592 | +9,673 | `c73908fd9e56d09a…` | `2ffc74e70381dfa8…` |
| `benchmark/final/ablation_v4/ablation_with_orchestrator/results_sota_eval_431.json` | 326,896 | 317,206 | +9,690 | (mismatch) | `eec18fa38401874a…` |
| `benchmark/final/sota_baselines/llama_3_3_70b.jsonl` | 208,020 | 200,226 | +7,794 | `5a41b9c505a23ea3…` | `751d9daac02b161e…` |
| `benchmark/final/sota_baselines/deepseek_v3.jsonl` | 193,986 | 186,189 | +7,797 | `e216a0fbbe8482f8…` | `1efa5c93b23bf9fe…` |
| `benchmark/final/phase46_no_prompt/llama_noprompt_clean.jsonl` | 334,942 | 327,113 | +7,829 | `1c65bb656b3bdcbd…` | `b001b7ea826d7b23…` |
| `benchmark/final/phase46_no_prompt/deepseek_noprompt_v2.jsonl` | 340,116 | 332,287 | +7,829 | `110d93213bf65b17…` | `898a5752ed4778e2…` |

**Root cause (verified)**: All deltas are consistent with the BERT-F1 inline write
(~22 bytes/record × ~430 records ≈ 9,680 for JSON; ~18 bytes/record × ~430 ≈ 7,800 for
JSONL). `benchmark/final/_bert_f1_recompute_summary.json` confirms exactly these 14
files have `written: true`. Drain.jsonl (skipped by D-6, boolean output) has
0-byte delta and a matching SHA — confirming the diagnosis.

**Effect on paper math**: ZERO. All accuracy counts recompute correctly from the
current files (see OK section). However, the MANIFEST.md table is INTERNALLY
inconsistent with the on-disk state and cannot be relied on by reviewers for
reproducibility checks.

**Fix**: re-run `benchmark/scripts/ops/build_final_results.py` (or hand-update the
table) to record post-D-6 SHAs. The MANIFEST.md header acknowledges this layout
(line 60: "session-11 / 2026-05-19 snapshot, pre-reorg paths"), but the supposed
"Post-D-1 state" block (line 62+) claims to be authoritative for the current state
and is not.

#### C2 — 3 qa_mcq cases are scored (not excluded) across all 13 result files

The D-1 re-label (session 17/18) reclassified 33 OpsEval-remined cases from
`task_type=rca` to `task_type=qa_mcq` with an `excluded_reason` field. The
methodology (per `docs/METHODOLOGY.md` §2) is that they should be excluded from
scoring (`correct=None`), giving 74 excluded RCA cases total (41 Chinese + 33 MCQ).

In every matched-eval and SOTA result file, only **30 of the 33** qa_mcq cases have
`correct=None` (excluded). The remaining 3 IDs are still being scored:

| Case ID | task_type (correct) | Our matched-eval | Llama | DeepSeek | Llama no-prompt | DeepSeek no-prompt |
|---|---|---|---|---|---|---|
| `RCA_OPSEVAL_RM_016` | qa_mcq | False | True | True | True | True |
| `RCA_OPSEVAL_RM_022` | qa_mcq | False | True | True | True | True |
| `RCA_OPSEVAL_RM_032` | qa_mcq | False | False | False | False | False |

`eval_method` on the 3 cases in the matched-eval files is
`rescored_with_sota_eval_substring` — i.e., the post-D-1 re-scoring pass still
ran the substring matcher on them.

The same pattern is consistent across ALL 9 matched-eval files (main + 8 ablations):
`task_types={annotation: 218, rca: 180, qa_mcq: 33}`, `total None=71`,
qa_mcq breakdown `True=0, False=3, None=30`.

**Effect on paper math**: ZERO on the headline numbers. The 3 cases carry
`task_type=qa_mcq` and are NOT counted in the rca denominator (still 139).
The annotation denominator (218) is also unaffected.

**However**, the SUMMARY.md / METHODOLOGY claim "**74 RCA cases excluded** from
all systems" is numerically inconsistent with the 71 cases with `correct=None`
present in every file. The matched_eval_table.md (line 18) repeats the 74 claim:
"**74 RCA cases excluded** from all systems (41 Chinese-language + 33 OpsEval-remined
MCQ knowledge format)".

**Fix**: either (a) flip `correct: False → None` for the 3 cases in all 13 files
(restores the 74-excluded invariant cleanly), or (b) reword SUMMARY/METHODOLOGY/
matched_eval_table.md to read "30 qa_mcq cases have `correct=None`; 3 qa_mcq cases
have a stale rescored substring flag that does NOT enter accuracy denominators",
or (c) accept the small inconsistency and document it as a known limitation.

#### C3 — `excluded_rca_cases.json` is stale (pre-D-1) and contradicts current state

`benchmark/intermediate/datasets/excluded_rca_cases.json` (9,889 bytes, mtime 2026-05-15)
describes the OLDER 400-case benchmark schema:

```
total_rca_cases: 198         # vs current 180+33=213 (or 180 if you only count task_type==rca)
total_ann_cases: 202         # vs current 218
excluded_count:  71          # = 39 Chinese + 32 multiple_choice_letter
evaluable_rca:   127         # vs current 139
description: "RCA cases excluded from SOTA comparison eval (benchmark_400_seed42)"
```

The 71 excluded IDs in this file map to the older 400-case dataset; the current
exclusion mechanism is `task_type=qa_mcq` carried inline on the dataset records
themselves (METHODOLOGY.md §2 acknowledges this: "the MCQ exclusion is now declared
via `task_type=qa_mcq` on the cases themselves rather than via an external list").

**Effect**: any downstream tool that still reads `excluded_rca_cases.json` will
get the wrong evaluable set. Per the audit-context spec ("legacy path") the file
should either be (a) updated to the current 74-exclusion state with the proper IDs,
(b) deleted, or (c) renamed `excluded_rca_cases_LEGACY_2026-05-15.json` with a
"DO NOT USE" header.

---

### IMPORTANT

#### I1 — `main_benchmark/summary.json` and `main_benchmark/benchmark_result.json` are identical byte-for-byte and pre-D-1

Both files (1,234 bytes each, both SHA `b56253786917…` per MANIFEST line 16+20)
contain identical pre-D-1 rich-eval numbers:

```
rca_tests: 213,  rca_passed: 197,  rca_accuracy: 92.49,
overall_accuracy: 87.47,
bert_f1: 0.0, annotation_bert_f1: 0.0, rca_bert_f1: 0.0,
timestamp: 2026-05-16T07:39:25
```

SUMMARY.md line 24 cites THIS file for "Table 5 (Latency) P50 4.1s / P95 48.4s /
avg 17.6s". The latency numbers match (4147ms / 48368ms / 17615ms). But the
accuracy numbers in the same file are STALE rich-eval (197/213 = 92.49% RCA),
pre-dating the D-1 re-label (which would have given 197/180 or 164/180 depending
on rescoring). The `bert_f1: 0.0` row is the pre-D-6 placeholder.

**Effect**: any reader who opens `summary.json` to verify latency will see
contradictory accuracy numbers from the SUMMARY.md headline (92.49% vs 92.5%
vs current rich-eval 91.1% from counting `results.json` directly).

**Fix**: regenerate `summary.json` (and the duplicate `benchmark_result.json`) from
the current `results.json`, or split it into `latency_summary.json` (latency only)
+ point Table 5 at that.

#### I2 — Asymmetric D-1 application: `main_benchmark/results.json` has D-1 re-label but `ablation_v4/*/results.json` do NOT

Verified by counting `task_type`:

| File | task_types |
|---|---|
| `main_benchmark/results.json` (rich-eval) | `{annotation: 218, rca: 180, qa_mcq: 33}` ✓ post-D-1 |
| `main_benchmark/results_sota_eval_431.json` | `{annotation: 218, rca: 180, qa_mcq: 33}` ✓ post-D-1 |
| `ablation_v4/ablation_*/results.json` (rich-eval, all 8) | `{annotation: 218, rca: 213}` ✗ pre-D-1 |
| `ablation_v4/ablation_*/results_sota_eval_431.json` (all 8) | `{annotation: 218, rca: 180, qa_mcq: 33}` ✓ post-D-1 |

The ablation rich-eval files still carry the 33 OpsEval-remined cases as
`task_type=rca`. Per `ablation_v4/README.md` and `AUDIT_REPORT.md`, the rich-eval
files are "kept for provenance" and "**do NOT cite rich-eval ablation numbers for
paper Table 6**". So this does NOT affect paper math.

But the asymmetry — main rich-eval was re-labeled but ablation rich-eval was not —
suggests the D-1 patch ran partial coverage. Either intentionally (because main is
shown in Table 2 alongside matched-eval, while ablation rich-eval is purely archival)
or by oversight. Worth a 1-line clarification in METHODOLOGY.md if intentional.

#### I3 — SUMMARY.md cites "92.5% rich-eval RCA" but actual count is 91.1%

SUMMARY.md line 21:
> **Table 2** (system standalone, rich eval) | `main_benchmark/results.json` | Ann 82.6% / RCA **92.5%** / Overall 87.5%

Counting the current `main_benchmark/results.json` directly:
- annotation: 180/218 = 82.6% ✓
- rca: 164/180 = **91.1%** (post-D-1) — NOT 92.5%
- 92.5% would be 197/213 (the pre-D-1 numerator+denominator, which is also what
  `summary.json` / `benchmark_result.json` report)

The pre-D-1 rich-eval count was 197/213 = 92.49%. After D-1, 33 cases moved to
qa_mcq; 33 cases that were `correct=True` under rich-eval (197 total) lost ~33
numerator credits → effectively 164/180. The SUMMARY headline still quotes the
pre-D-1 92.5% number.

**Effect**: SUMMARY.md is internally inconsistent with the file it cites. The
rich-eval RCA % is also clearly flagged as "not paper-canonical" (SUMMARY footnote),
so paper Table 2 is unaffected — but the cited number is stale.

#### I4 — `summary.json` / `benchmark_result.json` have `rca_tests: 213` but file actually has 180 rca

This is essentially the same root cause as I3 but creates a separate
inconsistency for any auto-extraction tool. The latency P50/P95/P99 + avg fields
in this file ARE post-current and match SUMMARY.md exactly.

---

### MINOR

#### M1 — `phase45_graph/exp_4_5c_summary.json` retained on disk despite being known-stale

`_failed_run_log.txt` (line 18) explicitly labels it stale (all-zero, mtime
session-17 leftover). It is NOT referenced by SUMMARY.md (good) or MANIFEST.md
(good). Per PATH 4 decision it should ideally be deleted or renamed
`exp_4_5c_summary_STALE.json` to prevent accidental re-use. Current SHA was not
checked because the file is documented as DO-NOT-USE.

#### M2 — `phase45_graph/exp_4_5b_no_graph.jsonl` and `exp_4_5b_with_graph.jsonl` are 0 bytes (expected per D-17)

Confirmed: both files = 0 bytes (D-17 dataclass crash before file write).
`_failed_run_log.txt` explicitly documents this as expected. The aggregate
`exp_4_5b_summary.json` (757 bytes) is the authoritative source for Phase 4.5b
per SUMMARY.md §3.6. **No action**: this is correctly handled.

#### M3 — Work files `_bert_f1_recompute_summary.json` + `_bert_recompute.log` not listed in MANIFEST.md

The summary JSON IS referenced in SUMMARY.md §3.5 (line 143: "Full per-record
output: `_bert_f1_recompute_summary.json`"). The 33KB log file is NOT referenced
anywhere but is a reproducibility artifact. Neither is in MANIFEST.md.

**Recommendation**: add a new section to MANIFEST.md for post-D-6 generated
artifacts (`_bert_f1_recompute_summary.json`, `_bert_recompute.log`), and any
post-D-1 / post-D-6 SHA refresh.

#### M4 — Dataset header field `rca_cases: 213` no longer matches `task_type==rca` count of 180

`benchmark_431_seed42.json` top-level header retains the pre-D-1 dataset
metadata:
- `total_cases: 431` ✓
- `annotation_cases: 218` ✓
- `rca_cases: 213` ✗ — current count is 180 (rca) + 33 (qa_mcq)
- `source_mix` sums to 431 ✓

This was likely left in place because the dataset creation pipeline ran before
D-1 and the header was not regenerated when task_types were patched in-line.
Functionally harmless (no script depends on this header field per the methodology),
but a reviewer auto-parsing the header will see 218+213=431 and miss the 33
qa_mcq subset.

#### M5 — AUDIT_REPORT.md is the 2026-05-19 build snapshot and uses pre-reorg paths

AUDIT_REPORT.md line 3-5 acknowledges this: "Built: 2026-05-19 04:58 UTC" with a
post-D-1 note added at the top. The per-file blocks still cite pre-reorg paths
(`benchmark\results_aws\FINAL\...`) and pre-D-1 stats (e.g. `rca_total: 213,
rca_correct: 197, rca_excluded: 71`). The added note acknowledges that
"post-D-1 is 218 ann + 180 rca + 33 qa_mcq = 431 total, with 74 RCA cases excluded
(41 Chinese + 33 MCQ-relabeled, evaluable RCA = 139)" — but the per-file stats
table was not regenerated.

**Effect**: reviewers reading AUDIT_REPORT.md per-file blocks see contradictory
numbers vs SUMMARY.md.

**Fix**: re-run `build_final_results.py` audit pass + regenerate per-file findings.

#### M6 — Drain.jsonl: 202 records (annotation only), not 431

This is documented behavior (Drain is OpenSSH log parser, no RCA capability) per
SUMMARY.md line 32. Verified: 202 annotation records, 0 rca, 0 qa_mcq. Headline
50.5% (102/202) matches.

#### M7 — `exp_4_5c_summary.json` is referenced by neither SUMMARY.md nor MANIFEST.md

Correctly excluded since the file is stale leftover (verified content shows all
zeros, mtime session-17). The `_failed_run_log.txt` correctly documents this.
No action needed but recommend deleting or renaming with `_STALE` suffix.

---

## OK (clean verifications)

### Dataset integrity (benchmark_431_seed42.json, SHA `d1a8f79fa65fc61b…` verified ✓)
- Total `test_cases`: **431** ✓
- `task_type` counts: **{annotation: 218, rca: 180, qa_mcq: 33}** ✓ post-D-1
- All 431 records have `id`, `task_type`, `source` fields populated (0 missing)
- 0 orphan task_type values (only annotation/rca/qa_mcq present)
- All 218 annotation cases have `expected` field
- All 180 rca cases have `expected_root_cause`/`expected`/`expected_output` field
- All 33 qa_mcq cases have `expected_root_cause` + `acceptable_answers` + `excluded_reason`
- All 33 qa_mcq cases have `excluded_reason: "MCQ knowledge format (post-hoc audit 2026-05-25)..."`
- `source_mix` sums to 431
- SHA-256 matches the MANIFEST "Post-D-1 state" entry exactly ✓

### Per-file accuracy counts vs SUMMARY.md (all matched-eval files)
Independently counted from `results_sota_eval_431.json` and compared to
SUMMARY.md §3.1 and matched_eval_table.md:

| Config | Ann | RCA | Overall | SUMMARY claim | Match |
|---|---|---|---|---|---|
| Main re-run | 180/218 (82.6%) | 114/139 (82.0%) | 294/357 (82.4%) | 82.6 / 82.0 / 82.4 | ✓ |
| ablation_full | 181/218 (83.0%) | 119/139 (85.6%) | 300/357 (84.0%) | 83.0 / 85.6 / 84.0 | ✓ |
| ablation_single_4b | 180/218 (82.6%) | 115/139 (82.7%) | 295/357 (82.6%) | 82.6 / 82.7 / 82.6 | ✓ |
| ablation_single_14b | 184/218 (84.4%) | 115/139 (82.7%) | 299/357 (83.8%) | 84.4 / 82.7 / 83.8 | ✓ |
| ablation_no_structured | 180/218 (82.6%) | 105/139 (75.5%) | 285/357 (79.8%) | 82.6 / 75.5 / 79.8 | ✓ |
| ablation_no_system_prompt | 106/218 (48.6%) | 113/139 (81.3%) | 219/357 (61.3%) | 48.6 / 81.3 / 61.3 | ✓ |
| ablation_with_graph | 180/218 (82.6%) | 116/139 (83.5%) | 296/357 (82.9%) | 82.6 / 83.5 / 82.9 | ✓ |
| ablation_no_constitutional | 195/218 (89.4%) | 101/139 (72.7%) | 296/357 (82.9%) | 89.4 / 72.7 / 82.9 | ✓ |
| ablation_with_orchestrator | 180/218 (82.6%) | 116/139 (83.5%) | 296/357 (82.9%) | 82.6 / 83.5 / 82.9 | ✓ |

### Phase 5 stats file consistency
- `main_benchmark/phase5_stats.json` (894 bytes, SHA `196c9b89fad9d859…`) ✓ matches MANIFEST
- `ablation_v4/phase5_stats.json` (14,769 bytes, SHA `cc2566b05fd903bf…`) ✓ matches MANIFEST
- `ablation_v4/phase5_stats.md` (4,316 bytes, SHA `8a1bcb44ab8cf45c…`) ✓ matches MANIFEST
- All 8 ablation configs in `phase5_stats.json` show `n_ann=218, n_rca=139, n_overall=357` ✓
- correct counts in stats match counted-correct in result files (verified all 8)

### SOTA baseline integrity
- llama_3_3_70b.jsonl: 431 records, 0 duplicates, 0 NaN, ann=199/218=91.3%, rca=99/139=71.2%, overall=298/357=83.5% ✓ matches SUMMARY (91.3 / 71.2 / 83.5)
- deepseek_v3.jsonl: 431 records, 0 duplicates, 0 NaN, ann=197/218=90.4%, rca=93/139=66.9%, overall=290/357=81.2% ✓ matches SUMMARY (90.4 / 66.9 / 81.2)
- drain.jsonl: 202 records (annotation-only), 0 duplicates, 0 NaN, 102/202=50.5% ✓ matches SUMMARY

### Phase 4.6 no-prompt
- llama_noprompt_clean.jsonl: 431 records, ann=148/218=67.9%, rca=102/139=73.4% ✓ matches SUMMARY (67.9 / 73.4)
- deepseek_noprompt_v2.jsonl: 431 records, ann=193/218=88.5%, rca=103/139=74.1% ✓ matches SUMMARY (88.5 / 74.1)

### BERT-F1 field presence (D-6)
- All 14 files identified in `_bert_f1_recompute_summary.json` have `bert_f1` field populated (non-null) on every record (431/431 or 202/202)
- 0 NaN values found in any numeric field across all 14 files
- Drain.jsonl correctly skipped (boolean output)

### Phase 4.5 forensic artifacts
- `exp_4_5b_summary.json` (757 bytes): schema valid, n_folds=5, fold_size=16, all 5 folds returned (no_graph=100.0, with_graph=100.0), aggregate Δ=0.0pp ✓ matches SUMMARY §3.6
- `_failed_run_log.txt`: clearly documents D-17 dataclass JSON-serialize crash at `run_graph_experiments.py:172`; correctly flags `exp_4_5c_summary.json` as stale leftover; correctly notes 0-byte JSONLs are expected
- `exp_4_5b_no_graph.jsonl` and `exp_4_5b_with_graph.jsonl` both 0 bytes ✓ (expected per D-17 crash)
- AWS state in failed-run log matches SUMMARY §6 (instance stopped, alarm re-enabled, EIP retained)

### D-1 spot-check (5 sample IDs)
All 5 sampled OpsEval-remined IDs (`RM_014, RM_020, RM_023, RM_006, RM_025`) consistently:
- Carry `task_type=qa_mcq` in dataset ✓
- Carry `excluded_reason: "MCQ knowledge format (post-hoc audit 2026-05-25)..."` ✓
- Have `task_type=qa_mcq, correct=None, eval_method=None` in main_benchmark/results_sota_eval_431.json ✓
- Have identical routing in ablation_full/results_sota_eval_431.json ✓

### Duplicate ID check
- 0 duplicate `case_id` / `test_id` in all 9 matched-eval files + 4 JSONLs + drain.jsonl
- 0 duplicate IDs in the dataset

### Cross-file consistency: 9 matched-eval files all carry exactly 71 cases with `correct=None`
- Breakdown identical across all 9: 41 rca (Chinese) + 30 qa_mcq = 71 None
- The other 3 qa_mcq cases (RM_016/022/032) are scored as False/True — see C2
- Same 71-None pattern in 4 SOTA/no-prompt JSONLs

---

## Skipped

- File-content audit of every record in every result file (limited spot-checks performed instead)
- Re-derivation of BCa CIs and McNemar p-values from raw `correct` arrays (Phase 5 stats trusted at JSON-level only; arithmetic checked, statistics not re-bootstrapped)
- `_bert_recompute.log` (33KB) content — not opened
- `benchmark/archive/originals_*` zip contents — out of scope (audit context says "may be referenced elsewhere"; verified non-referenced from SUMMARY/MANIFEST only)
- Underlying source `paper_tables.md` / `paper_tables.tex` content audit (only counted existence + SHA)
- Cross-file consistency of `bert_f1` values vs `_bert_f1_recompute_summary.json` per-file averages (only verified field presence + non-null + no NaN)

---

## Recommendations

Ordered by impact:

1. **Refresh MANIFEST.md (CRITICAL)**: re-run `benchmark/scripts/ops/build_final_results.py`
   (or update the "Post-D-1 state" table by hand) so all 14 SHAs reflect the
   current on-disk state (i.e., post-D-6 BERT-F1). The header at line 60-63
   should be reworded to "Post-D-1 + post-D-6 state".

2. **Reconcile 71-vs-74 exclusion count (CRITICAL)**: pick ONE of (a) flip the 3
   qa_mcq cases (RM_016/022/032) from `correct=False` → `correct=None` in all
   13 result files to enforce the 74-excluded invariant, or (b) reword
   SUMMARY.md §3 + matched_eval_table.md + METHODOLOGY.md §2 to be precise:
   "71 cases carry `correct=None`; 33 qa_mcq cases are excluded from RCA scoring
   via `task_type` routing". Option (a) is cleaner for downstream tooling.

3. **Update or retire `excluded_rca_cases.json` (CRITICAL)**: it currently
   contradicts current state by claiming 71 exclusions on a 400-case benchmark.
   Either regenerate or rename `excluded_rca_cases_LEGACY_400ds.json` with
   a "DO NOT USE" header.

4. **Regenerate `summary.json` + `benchmark_result.json` (IMPORTANT)**: split
   them into a latency-only file (cited by SUMMARY.md §1 Table 5) and remove the
   stale accuracy numbers. Or regenerate from current `results.json`.

5. **Fix SUMMARY.md rich-eval RCA % (IMPORTANT)**: line 21 should say "91.1%"
   not "92.5%" (post-D-1 rich-eval count is 164/180, not 197/213). The line is
   flagged "not paper-canonical" so impact is low but the cited number is wrong.

6. **Decide on rich-eval D-1 asymmetry (IMPORTANT)**: either apply D-1 to the
   8 ablation `results.json` files (mirror what was done to main) for
   consistency, or add a 1-line note to METHODOLOGY.md explaining the intentional
   asymmetry.

7. **Refresh AUDIT_REPORT.md (MINOR)**: it's a 2026-05-19 build snapshot with
   pre-D-1 per-file stats; the top note acknowledges this but per-file blocks
   read inconsistently with current SUMMARY.

8. **Update dataset header `rca_cases: 213` → `rca_cases: 180, qa_mcq_cases: 33` (MINOR)**:
   keeps the header consistent with the inline `task_type` field.

9. **Rename or delete `phase45_graph/exp_4_5c_summary.json` (MINOR)**: rename to
   `exp_4_5c_summary_STALE_session17.json` or move it under
   `audit/_session17_phase45_attempt/` to prevent accidental future use.

10. **Add work files to MANIFEST.md (MINOR)**: `_bert_f1_recompute_summary.json`,
    `_bert_recompute.log` are session-18 provenance artifacts cited from
    SUMMARY.md §3.5 but absent from MANIFEST.

None of these recommendations require re-running the benchmark or AWS compute.
All paper headline numbers (Tables 2/5/6/7) verify clean against the current
on-disk state.
