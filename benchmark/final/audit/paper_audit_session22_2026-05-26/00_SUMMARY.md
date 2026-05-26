# 00 — Master Summary (session-22 paper audit)

**Date**: 2026-05-26 session 22
**Scope**: Full reviewer-facing QC of the v2 sandbox paper against v1 paper + benchmark source-of-truth + supporting docs
**Auditors**: 5 parallel general-purpose subagents
**Reports**:
- `01_numbers_audit.md` — Tables 1-7 + Fig 3 + statistical claims vs source-of-truth result files
- `02_v1_v2_structural_diff.md` — section-by-section v1 vs v2 (preserved/dropped/reframed)
- `03_citations_audit.md` — `\cite{}` coverage + bib integrity + v1↔v2 bib diff
- `04_benchmark_integrity.md` — result-file self-consistency + MANIFEST SHA + dataset integrity
- `05_cross_doc_consistency.md` — paper vs SUMMARY/METHODOLOGY/BUG_HISTORY/AUDIT_REPORT/MANIFEST/HANDOFF

---

## Verdict

**The paper's body — Tables 2-7, Fig 3, §5.1-§5.7 — is internally consistent and well-corroborated.** All ablation numbers, SOTA numbers, statistical claims (CIs, McNemar, Cohen's h), figure values, citation keys, and dataset integrity check out. No data corruption. No bib breakage. The empirical case is solid.

**However, the front-matter (abstract + §1 + §2 + RG1-2) is STALE v1 text.** This is the single biggest reviewer-facing risk: reviewers reading paragraph one will see the old 150-case / 90.7% / 31.3pp numbers that contradict every table in the body.

A small set of supporting-doc issues (MANIFEST SHA staleness, HANDOFF.md numeric drift on 5 ablation rows + 2 SOTA cells) also need cleanup before any reviewer or external auditor compares paper to repo.

---

## CRITICAL findings (must fix before camera-ready submission)

| # | Where | Issue | Severity |
|---|---|---|---|
| **C-A1** | `sn-article.tex:123` (Abstract) | Still verbatim v1: "150-test benchmark from four established datasets, 90.7% overall accuracy". Reality: 431 cases / 6 datasets / 82.4% overall. | Top reviewer risk |
| **C-A2** | `sn-article.tex:137` (§1 Introduction, ¶2) | Still verbatim v1: "150-test / 90.7% / 7-config ablation / 31.3pp drop / 1,050 inferences". Reality: 431 / 82.4% / 8-config / 22.7pp / 3,448 inferences. Internally contradicts §5.6 (line 540) and Tables 5-6. |
| **C-A3** | `sn-article.tex:141, 143, 160` (§2 / RG1 / RG2) | "3.3pp dual-agent improvement" and "0.7% constitutional overhead" — neither is supported by current ablation. Single-14B vs Full is −0.3pp NS; No-Constitutional overall is −1.1pp NS (with asymmetric per-task collapse on RCA). |
| **C-B1** | `sn-article.tex` Table 4 14B Reasoning row + footnote | Row shows n=180 RCA-only percentiles (P50 30.72s, P95 59.38s, Avg 32.19s). Footnote claims n=431. If 14B is supposed to route the qa_mcq=33 cases too, recomputed values become P50 29.83s, P95 62.20s, Avg 32.50s. Either re-fit numbers OR fix the footnote. |
| **C-B2** | `sn-article.tex` Table 7 Drain row | Caption/prose says "same 431-case benchmark". Drain actually ran on `benchmark_400_seed42.json` (pre-D-1, 202 cases). Either re-run on 431 or disclose the 202-case subset. |
| **C-B3** | `sn-article.tex` §5.5 Stack B claim | "~1.5× vLLM speedup" was measured on a 30-case smoke (`benchmark/final/infrastructure/gate15_comparison.md`), NOT the full 431-case set. Disclose explicitly. |
| **C-C1** | `benchmark/final/MANIFEST.md` | SHA table is stale for all 14 files modified by D-6 BERT-F1 recompute (size deltas +7.8k…+9.7k bytes per file). Headline math unaffected; reproducibility documentation broken. Regenerate SHA table. |
| **C-C2** | `benchmark/final/ablation_v4/*/results_sota_eval_431.json` | 3 qa_mcq cases (`RCA_OPSEVAL_RM_016`, `_022`, `_032`) carry `correct=False/True` instead of `correct=null` across all 13 result files. Total excluded count is 71 actually-excluded vs 74 claimed. Headline math NOT affected (qa_mcq routed separately) but breaks the 74-case story. |
| **C-D1** | `benchmark/HANDOFF.md:215-223` (just-rewritten session 22) | §7 Phase 4.3 ablation cells contradict paper Tables 5+6 + SUMMARY + phase5_stats on **5 rows**: Single-4B, Single-14B, No-constitutional, No-system-prompt, with-graph. Drift introduced when HANDOFF was rewritten with approximate numbers instead of looking them up. |
| **C-D2** | `benchmark/HANDOFF.md:232-233` | SOTA Overall cells drift from paper Table 7: HANDOFF says Llama 83.3 / DeepSeek 81.1; paper + SUMMARY say 83.5 / 81.2. |

---

## IMPORTANT findings (should fix; will not break review but visible)

| # | Where | Issue |
|---|---|---|
| **I-1** | `sn-article.tex` §5.5 + Table 4 caption | Stack B labeled "vLLM+FP8" but production config is `vLLM AWQ awq_marlin`. Wrong quantization scheme name throughout. |
| **I-2** | `sn-article.tex` Table 4 P95/P99 cells | Use index-floor percentile method; `phase5_stats.json` uses linear-interp. ~0.2s gap. Pick one and be consistent. |
| **I-3** | `sn-article.tex` §5.1 footnote | Claims "1.95 ms RTT" but Table 4 footnote on same page says "1.10 ms". Reconcile to a single measured value. |
| **I-4** | `sn-article.tex` `\bibitem` for `alibaba2024qwen` | Bib title `Qwen2.5: A Family of Large Language Models`; tex line 277 says `Qwen3 family`. Either bib entry or paper claim is wrong (likely bib entry — actual model used is Qwen3). |
| **I-5** | `sn-article.tex` §6.2 Limitations | Calls Phase 4.5 LEMMA-CV sub-experiment "planned" but it actually ran (just lost per-case JSONL to D-17 bug). Reframe to "ran but per-case logs lost; aggregate summary preserved." |
| **I-6** | `sn-article.tex` Table 4 with-graph / with-orchestrator RCA delta | Paper shows −2.1pp; recompute from `ablation_v4/phase5_stats.json` is −2.2pp. Rounding direction. |
| **I-7** | `sn-article.tex` Table 1 vs Table 4 footnote | Table 1 splits 431 = 218 Ann + 213 RCA. Table 4 footnote splits 431 = 218 Ann + 180 RCA + 33 qa_mcq. Both are correct under different framings (213 = 180 rca + 33 qa_mcq pre-D-1 routing) but reconcile for reader clarity. |
| **I-8** | `sn-article.tex` BERT-F1 column | Only present in Table 2. Missing from Tables 5, 6, 7. Per D-6 decision the recompute was meant to cover all paper tables — confirm if Tables 5-7 omission is intentional. |
| **I-9** | `sn-article.tex` run-to-run footnote | Says "5 cases of nondeterminism." Actual is 6 (1 ann + 5 rca) between main re-run RCA 82.0% and ablation Full RCA 85.6%. |
| **I-A** | `sn-bibliography.bib` `peng2025graphragsurvey` | Missing volume, issue, pages, DOI. Reviewer may flag incomplete ref. |
| **I-B** | `sn-bibliography.bib` `zhang2024aiopssurvey` | Year is `2024` in bib; ACM CS publication date should be checked — likely `2025`. |
| **I-C** | `sn-bibliography.bib` `nvidia2024specdec` | Blog citation lacks URL. Not locatable as cited. |
| **I-D** | `sn-bibliography.bib` header comment | Says "26 references" — actual count is 36. Cosmetic but visible. |

---

## MINOR findings (nice-to-have polish, low review risk)

| # | Where | Issue |
|---|---|---|
| **M-1** | `sn-bibliography.bib` | 5 orphan (uncited) entries: 3 intentional (`adaspec2025`, `edge2024graphrag`, `zhang2020effect` per session-21 drop) + 2 unflagged (`bertscore2020` — BERTScore used uncited in tex:455/474; `karpukhin2020dense` — orphan since v1). |
| **M-2** | `sn-bibliography.bib` | 2 of 12 expected new entries missing: Brittlebench/PromptRobust (NAACL-SRW 2025), C3AI (WWW 2025). May be intentional but worth noting. |
| **M-3** | `benchmark/intermediate/datasets/excluded_rca_cases.json` | Pre-D-1 file describing the older 400-case benchmark. METHODOLOGY acknowledges it's legacy. |
| **M-4** | `benchmark/final/main_benchmark/summary.json` | Byte-identical to `benchmark_result.json`; contains pre-D-1 rich-eval numbers (rca_tests:213, rca_passed:197, 92.49%). Latency numbers within are current. |
| **M-5** | `benchmark/final/ablation_v4/*/results.json` (rich-eval) | D-1 re-label NOT applied to rich-eval files — only to matched-eval `results_sota_eval_431.json`. Doesn't affect paper because matched-eval is canonical, but inconsistent across the dir. |
| **M-6** | `benchmark/final/SUMMARY.md:21` | Quotes "RCA 92.5%" for rich-eval; actual is 164/180=91.1% post-D-1. |
| **M-7** | `benchmark/final/phase45_graph/exp_4_5c_summary.json` | Stale session-17 file, documented stale in `_failed_run_log.txt` but still on disk. Could be deleted or moved to archive. |

---

## OK — verified clean (the strong base)

The audit confirmed the following are RIGHT and need no fix:

### Numbers (auditor #1)
- **All Table 5 ablation cells** match `ablation_v4/phase5_stats.json` exactly (8 configs × Ann/RCA/Overall + CIs + McNemar p + Cohen's h)
- **All Table 6 ablation cells** match exactly
- **All Figure 3 bar values** match Tables 5+6
- **Table 7 SOTA** values recompute from raw `.jsonl` to exact match (Llama 91.3/71.2/83.5; DeepSeek 90.4/66.9/81.2)
- **Table 2 main re-run** all 8 cells match `main_benchmark/phase5_stats.json`
- **Table 3 per-source breakdown** verified per-cell from `results_sota_eval_431.json`
- **Statistical methodology** (n_resamples=10000, seed=42, BCa, McNemar, 357 paired) exact match
- **74-case exclusion** = 41 Chinese + 33 OpsEval-MCQ verified consistent in paper + METHODOLOGY (though see C-C2 for the actual 71 vs claimed 74 disparity)

### Structure (auditor #2)
- **§5.8 Graph-Episodic Memory Sub-experiment cleanly removed** per Decision 4; content absorbed into §6.2 + §6.3
- **Table 4 v1 component×metrics layout** restored per Decision 1, no `---` cells
- **Fig 3 dimensions** match v1 spec per Decision 3 (height=8.5cm, bar=6pt, xmin=30)
- **Prompt-fragility reframe** is honest disaggregation (4B annotation −34.4pp vs 14B RCA −4.3pp)
- **Graph-RAG reframe** honestly converts v1's −2.7% to NS (p=0.289)
- **Latency reframe** attributes P95 to serving-stack and proposes vLLM path
- **Architectural-contrast paragraph** at line 734 cites Flow-of-Action + AIOpsLab + OpenRCA
- **§5.7 SOTA Table 7** has Ann/RCA/Overall split as required
- **Intentional 3-point rubric disclosures** at lines 447 + 597 present and contextually appropriate

### Citations (auditor #3)
- **All 31 cited keys resolve to bib entries** — no `[?]` will render in PDF
- **0 critical citation breakage**
- **Citation style** uniformly `\cite{}` — no mixed styles
- **0 self-citations** flagged
- **Contextual sample of 13 cites checked** — all topically correct
- **Cite count: 31** matches the session-21 close exactly

### Benchmark integrity (auditor #4)
- **Dataset SHA `d1a8f79f…` matches MANIFEST**
- **431 records: 218 ann + 180 rca + 33 qa_mcq** verified by counting
- **0 missing required fields**, **0 orphan task_types**, **0 duplicate IDs**
- All 33 qa_mcq cases carry `excluded_reason`
- **All 9 matched-eval headline percentages** match SUMMARY.md §3.1 exactly
- **Phase 5 stats files** match counted-correct from result files
- **All 14 D-6 BERT-F1 files**: `bert_f1` field populated 431/431 (or 202/202), 0 NaN
- **D-1 re-label spot-check** on 5 sample IDs: all consistent across dataset + main + ablation_full
- **4.5b summary schema** valid
- **SOTA + no-prompt baselines** match SUMMARY

### Cross-doc consistency (auditor #5)
- **Paper vs SUMMARY.md** numerically aligned on 14 claim families
- **AUDIT_REPORT.md** shows 23 OK / 0 WARN / 0 FAIL pre-D-1 snapshot with proper post-D-1 header note
- **BUG_HISTORY.md** shows D-1, D-6, D-17 (paper-relevant) marked RESOLVED
- **METHODOLOGY.md** corroborates 74-exclusion methodology
- **MANIFEST.md** covers all in-scope files (modulo C-C1 SHA staleness)

---

## Cross-cutting themes

1. **The paper revision did NOT update the abstract / intro / RG1-2 narratives.** Every table from Table 2 onward reflects v3.0 reality, but the first 2 pages of the paper still read as v1. Pattern: sessions 16-21 focused on §5 (Results) and §6 (Discussion) since those are where reviewer concerns landed; §1-2 were unchanged.

2. **Drift between paper and HANDOFF.md** is recent (session 22). When HANDOFF.md was rewritten today, several ablation cells and SOTA Overall percentages were typed by approximation rather than copy-paste from `phase5_stats.md`. Easy fix: regenerate HANDOFF §7 ablation table from `phase5_stats.md` and §7 SOTA table from `sota_baselines/llama_3_3_70b.jsonl` + `deepseek_v3.jsonl`.

3. **MANIFEST SHA + 71-vs-74 exclusion miscount** stem from the same root cause: D-6 BERT-F1 recompute (session 18) wrote bert_f1 in place but did not update MANIFEST, and D-1 re-label (session 17) marked 30 of 33 qa_mcq cases as `correct=null` but left 3 with True/False. Both are documentation/metadata, not data corruption.

4. **Drain "same 431-case" claim** is the only finding where a real re-run is needed (or the claim must be downgraded to "202 annotation cases, subset of the 431 benchmark"). Cheap to fix in prose; expensive to re-run.

5. **`vLLM+FP8` mis-label** is consistent across paper. It should be `vLLM AWQ` (awq_marlin kernel). Mechanical find-and-replace fix.

---

## Recommended fix order

Group A — **must fix before camera-ready submission**:

1. Rewrite abstract (`sn-article.tex:121-128`) with v3.0 numbers (431 / 82.4% / 6 datasets / 8-config ablation / 3 SOTA baselines).
2. Rewrite §1 Introduction ¶2 (line 137 area) with current numbers (431 / 82.4% / 8-config / 22.7pp / 3,448 inferences).
3. Update §2 Related Work / RG1 / RG2 (lines 141, 143, 160) to remove "3.3pp dual-agent" and "0.7% constitutional overhead" — replace with empirically-supported framing.
4. Decide on Table 4 14B row: re-fit to n=213 (180 + 33 qa_mcq) OR fix footnote to admit n=180 (RCA-only).
5. Decide on Drain row: re-run on 431 OR change caption to disclose 202-case annotation subset.
6. Fix Stack B mislabel: "vLLM+FP8" → "vLLM AWQ" everywhere in paper + Table 4 caption.
7. Regenerate `MANIFEST.md` SHA table by running `sha256sum` on the 14 D-6 affected files.
8. Fix `HANDOFF.md` §7 ablation cells + SOTA Overall cells (copy from `phase5_stats.md` + `sota_baselines/*.jsonl`).
9. Reconcile the 71-vs-74 exclusion: either flip the 3 qa_mcq `correct` fields to null, OR update METHODOLOGY/paper to say 71 excluded + 3 qa_mcq scored separately.

Group B — **should fix but not blocking**:

10. Reconcile "1.95 ms" vs "1.10 ms" RTT (§5.1 vs Table 4 footnote).
11. Fix `alibaba2024qwen` bib entry: Qwen2.5 → Qwen3 (or whichever is the actual model used).
12. §6.2 reframe Phase 4.5 from "planned" to "ran with per-case loss".
13. §5.5 disclose Stack B 30-case smoke (not 431).
14. Round Table 4 deltas consistently (with-graph / with-orchestrator −2.1 vs −2.2).
15. Table 1 ↔ Table 4 footnote 213-vs-180 reconciliation.
16. Decide if BERT-F1 should appear in Tables 5, 6, 7 (currently only Table 2).
17. Fix bib year on `zhang2024aiopssurvey`, add URL to `nvidia2024specdec`, fill in `peng2025graphragsurvey` fields, fix bib comment "26 references" → "36 references".

Group C — **cleanup polish**:

18. Mark `bertscore2020` cited or remove from bib (BERTScore is used uncited at tex:455/474).
19. Decide on `karpukhin2020dense` orphan from v1 (preserve or drop).
20. Update SUMMARY.md:21 RCA 92.5% → 91.1% (rich-eval count).
21. Delete or archive stale `exp_4_5c_summary.json` (session-17 leftover).
22. Apply D-1 re-label to the 8 rich-eval `results.json` files too (currently only matched-eval has it).

---

## Sources used (all read-only)

- v1 paper: `c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\Final Submission Paper (Accepted v.1)\1ST SUBMISSION\sn-article-template\sn-article.tex`
- v2 sandbox paper: `c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\main\sn-article.tex`
- v1/v2 bib files at the same parent paths
- `c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\benchmark\final\**`
- `c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\benchmark\HANDOFF.md`
- `c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\benchmark\intermediate\datasets\benchmark_431_seed42.json`

No source files were modified by any auditor. All findings are deterministically reproducible by re-reading these sources with the cited line numbers and recomputing via the result file JSONs.

---

*End of master summary. See individual auditor reports for detailed file:line evidence and per-finding analysis.*
