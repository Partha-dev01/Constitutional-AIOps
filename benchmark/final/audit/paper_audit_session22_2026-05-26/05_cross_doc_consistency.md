# 05 — Cross-Doc Consistency Audit

**Auditor**: #5 of 5 (cross-doc consistency)
**Date**: 2026-05-26
**Independence**: Fresh audit, no reliance on prior session decisions.

## Scope

Verify the v2 sandbox paper (sn-article-template.v2.sandbox-session16/main/sn-article.tex) is corroborated by every supporting doc in `benchmark/final/` and by `benchmark/HANDOFF.md`. Findings filed by severity: CRITICAL (≥1 pp or wrong sign), IMPORTANT (0.1–1 pp / qualitative contradiction), MINOR (citation drift, missing cross-ref).

## Method

Files read in full or with targeted offsets:

- **Paper (target)**: `…\sandbox-session16\main\sn-article.tex` (lines 1–787)
- **Canonical results**: `benchmark/final/SUMMARY.md` (lines 1–335)
- **HANDOFF**: `benchmark/HANDOFF.md` (lines 1–503)
- **Methodology**: `benchmark/final/docs/METHODOLOGY.md` (lines 1–277)
- **Bug history**: `benchmark/final/docs/BUG_HISTORY.md` (lines 1–188)
- **Per-file SHA + provenance**: `benchmark/final/MANIFEST.md` (lines 1–88)
- **Per-file audit**: `benchmark/final/AUDIT_REPORT.md` (lines 1–194)
- **Phase 5 stats source-of-truth**: `benchmark/final/ablation_v4/phase5_stats.md` (lines 1–65)
- **Gate §15 latency source-of-truth**: `benchmark/final/infrastructure/gate15_comparison.md` (lines 1–24)
- **BERT-F1 source-of-truth**: `benchmark/final/_bert_f1_recompute_summary.json` (lines 1–100)
- **Current runs**: `benchmark/final/docs/CURRENT_RUNS.md` (lines 1–162)
- **Paper-tables provenance**: `benchmark/final/main_benchmark/paper_tables.md` (lines 1–49)

Cross-checks performed for each of the 14 specific claim families requested in the task brief, plus open-issue scan against AUDIT_REPORT.md + BUG_HISTORY.md.

---

## Findings

### CRITICAL (numeric or sign contradiction ≥1 pp, or paper-defining claim wrong)

#### CRIT-1. Abstract still reports v1 headline numbers (150-test, 90.7% acc)

- **Paper**: `sn-article.tex:123` — abstract states *"Validated on a 150-test benchmark from four established datasets, the system achieves 90.7% overall accuracy. A seven-configuration ablation study confirms…"*
- **Reality** per `SUMMARY.md:22` and `phase5_stats.md:59`: dataset is **431 cases** (six datasets), Overall **82.4%** (294/357 evaluable). Ablation is **8-configuration** (Table 5 + Table 6 in body), not 7.
- **Impact**: Reviewer reading abstract gets fundamentally wrong scale (~3× too small) and outdated headline accuracy. Inconsistent with paper body §4 Dataset Sources (line 406) and §5.2 Overall Results (line 455).
- **Cross-ref**: `HANDOFF.md:185-198` (Benchmark Datasets section) and `SUMMARY.md:22` both authoritatively use 431. Body line 425 says "Total (curated) 431 (218 Ann + 213 RCA)".

#### CRIT-2. Introduction repeats abstract's stale v1 numbers

- **Paper**: `sn-article.tex:137` — *"On a curated 150-test benchmark from four established datasets, the system achieves 90.7% overall accuracy; a seven-configuration ablation study (1,050 inferences) confirms system prompt engineering as the single most critical component (31.3 percentage point drop without it)."*
- **Reality**: 431-case benchmark from six sources, 82.4% overall, 8-config ablation. Per `phase5_stats.md:21-22`, the "No system prompt" overall drop is **−22.7pp** (61.3% vs 84.0% baseline), not "31.3 pp". 31.3 pp is the v1 paper's drop figure (still echoed in §5.6 line 600 below).
- **1,050 inferences** = 7×150 (v1 math); the v2 ablation footprint is "3,448 inferences" per paper line 540 itself — internal contradiction.
- **Impact**: Reviewer-facing first impression is wrong. Three independent numerical claims (sample size, accuracy, ablation drop) all stale.
- **Cross-ref**: `phase5_stats.md:23` (No sys prompt overall = 61.3%, Δ=−22.7pp).

#### CRIT-3. HANDOFF.md §7 ablation table contradicts SUMMARY.md / phase5_stats.md / paper

Multiple cells in `HANDOFF.md:215-223` ("Phase 4.3 Ablation 8 configs") disagree with the canonical Phase 5 numbers and with the paper's Table 6.

| Configuration | HANDOFF says | SUMMARY/phase5_stats.md/paper Table 6 say |
|---|---|---|
| Single-4B | Ann 82.6 / RCA 83.5 / Overall **82.9%** / Δ **−1.1pp** | Ann 82.6 / RCA 82.7 / Overall **82.6%** / Δ **−1.4pp** |
| Single-14B | Ann 84.4 / RCA 83.5 / Overall **83.5%** / Δ **−0.5pp** | Ann 84.4 / RCA 82.7 / Overall **83.8%** / Δ **−0.3pp** |
| With graph | Ann 82.6 / RCA 83.5 / Overall 82.9% / Δ −1.1pp p=0.289 | Ann 82.6 / RCA **83.5** / Overall 82.9% / Δ −1.1pp p=0.289 (RCA matches; rest OK) |
| **No constitutional** | Ann 89.4 / RCA **71.9%** / Overall **82.6%** / Δ **−1.4pp** | Ann 89.4 / RCA **72.7%** (101/139) / Overall **82.9%** / Δ **−1.1pp** |
| With orchestrator | Overall 82.9% / Δ −1.1pp | Overall 82.9% / Δ −1.1pp (matches) |
| **No system prompt** | Ann 48.6 / RCA 81.3 / Overall **60.8%** / Δ **−23.2pp**, p **<1e-15** | Ann 48.6 / RCA 81.3 / Overall **61.3%** / Δ **−22.7pp**, p **3.40e-11** |

Sources:
- HANDOFF §7: `benchmark/HANDOFF.md:214-225`
- Phase 5: `benchmark/final/ablation_v4/phase5_stats.md:12-32`
- Paper Tables 5+6: `sn-article.tex:548-595`
- SUMMARY headline: `SUMMARY.md:84-107`

**Impact**: Paper and SUMMARY agree; HANDOFF is the outlier. Since HANDOFF is the doc the next agent reads first (per its own §1 priority list), an agent acting on HANDOFF numbers would mis-cite the paper. Recommend HANDOFF §7 be re-synced to match `phase5_stats.md`.

#### CRIT-4. HANDOFF.md §7 SOTA Overall numbers disagree with paper Table 7 / SUMMARY

- `HANDOFF.md:232-233`: Llama Overall **83.3%**, DeepSeek Overall **81.1%**
- Paper Table 7 (`sn-article.tex:717-718`): Llama Overall **83.5%**, DeepSeek Overall **81.2%**
- `SUMMARY.md:30-31`: Llama **Ovl 83.5**, DeepSeek **Ovl 81.2** ✅ matches paper

HANDOFF's overall percentages are 0.2pp off. Annotation (91.3 / 90.4) and RCA (71.2 / 66.9) match. The −10.8pp / −15.1pp ΔRCA values match across all three docs. **Drift, not error in paper or SUMMARY.**

### IMPORTANT (qualitative contradictions or 0.1–1 pp drift)

#### IMP-1. Table 2 (`tab:overall`) Annotation accuracy 82.6% vs Phase 5 Full-Hybrid Annotation 83.0%

- Paper `tab:overall` row Annotation 82.6% (180/218) is the **main re-run** (Stack A, matched eval).
- Paper Table 5 (`tab:ablation_arch`) Full Hybrid Annotation **83.0%** (181/218).
- This is the disclosed 5-case temp-0 nondeterminism, footnoted on both tables (line 474 + line 597). **Internally consistent**, but the paper text in §5.2 line 455 says "**82.4% overall** (294/357)" pegged to main re-run — while Conclusion line 749 also says 82.4%. ✅ consistent.

  This is **not a bug** — it's just worth flagging that two different "Full Hybrid" numbers appear in the same paper (main re-run 82.4% vs Ablation Full 84.0%) and reviewers will need the footnotes to disambiguate.

#### IMP-2. Latency Table 4 reports Stack A only; Stack B / 1.51× claim lives only in HANDOFF + SUMMARY (and a vague paper sentence)

- Paper Table 4 (`tab:latency`, `sn-article.tex:522-535`): only Stack A numbers (End-to-End P50 4.15 / P95 48.57 / Avg 17.62 / P99 81.16).
- Paper §5.5 text (line 514): *"Preliminary vLLM+FP8 gate tests show ~1.5× speedup"* — vague, no source table.
- `gate15_comparison.md:14-17` reports Stack A overall P95 **65.96s** / Stack B P95 **43.71s** (1.51×). But this 65.96s figure is from a **30-case smoke**, not the 431-case main run.
- The full 431-case main run yields the P95 48.4s (≈ paper's 48.57s) figure quoted in §6.2 Limitations (line 739) and in `SUMMARY.md:24`.
- **Issue**: Paper does not table Stack B numbers, even though HANDOFF §7 frames the 1.51× as a reviewer-defense argument. The "preliminary" hedge in line 514 is *technically* honest because Stack B only ran a 30-case smoke. **Risk**: a careful reviewer will ask "where is the Stack B table?" and may not be satisfied that one sentence in §5.5 + one in §6.3 Future Work (line 744) covers it.

#### IMP-3. Paper §4.5 graph sub-experiment phrasing labels it "planned"; supporting docs say "completed (PATH 4)"

- Paper `sn-article.tex:739`: *"a **planned** homogeneous-LEMMA 5-fold sub-experiment saturated at the model's accuracy ceiling at this difficulty (no-graph = with-graph = 100%, n=80, populated graph N=431)"*
- `SUMMARY.md:175-186`: Phase 4.5b **ran to completion** session 19/20. Past tense ("ran"), n=80, no-graph=with-graph=100%. Numbers match paper exactly.
- `BUG_HISTORY.md:175-183` (D-17 footnote): Confirms 4.5b actually ran to completion in memory; per-case JSONL was lost to D-17 bug but aggregate summary is valid.
- **Issue**: "**planned**" is the wrong tense — the experiment was actually executed. The numerical result (100% / 100% saturation, n=80, populated N=431) is correctly cited. Cosmetic but reviewer-visible — they will check provenance.

#### IMP-4. `bert_f1` per-task n disclosure: paper says n=218 ann / n=122 rca; this is correct per source but does not match Table 2 RCA denominator (139)

- Paper Table 2 footnote (`sn-article.tex:474`): *"BERT-F1 (roberta-large, post-D-1, n=218 Ann / n=122 RCA after MIN_TEXT_LEN=15 filter)"*
- `_bert_f1_recompute_summary.json:10-19`: confirms `n_pairs=370`, `annotation n=218 mean=0.822`, `rca n=122 mean=0.7954`.
- `SUMMARY.md:142-145` documents the MIN_TEXT_LEN=15 filter caveat: BERT-F1 RCA evaluable set is **122**, not 139.
- **OK as disclosed**, but a reader comparing the 122 vs 139 evaluable for accuracy may be momentarily confused. Footnote does say "after MIN_TEXT_LEN=15 filter" so it's defensible.

#### IMP-5. Paper Table 1 (`tab:datasets`) line 425 says "431 (218 Ann + 213 RCA)" but body text and Table 4 footnote say "218 ann + 180 rca + 33 qa_mcq"

- Paper Table 1: 431 = **218 Ann + 213 RCA** (line 425)
- Paper §4.1.1 line 433: *"yielding 139 evaluable RCA cases"* of 213 RCA total
- Paper Table 4 footnote line 534: *"n=431 (218 annotation + 180 RCA + 33 qa_mcq)"*
- `HANDOFF.md:192-194` (post-D-1 composition): **218 ann + 180 rca + 33 qa_mcq**
- `METHODOLOGY.md:11`: *"218 annotation + 213 RCA = 431 total task_type ∈ {annotation, rca} cases. After the 2026-05-26 D-1 re-label, 33 OpsEval-remined cases carry task_type=qa_mcq"*

The paper inconsistently uses two compositions: the pre-D-1 "213 RCA" framing (Table 1) and the post-D-1 "180 rca + 33 qa_mcq" framing (Table 4 footnote). Both are technically reconcilable (213 = 180 + 33), but the inconsistency is visible to a careful reviewer. METHODOLOGY.md splits the difference. **Recommend** harmonizing Table 1's "213 RCA" cell to "**213 RCA** (180 RCA + 33 qa_mcq post-D-1)" or similar.

#### IMP-6. Paper line 540 says "8-configuration ablation (3,448 inferences)" — internally consistent but ablation tables and Fig 3 show only 7 non-baseline configs

- 8 configs × 431 inferences/config = 3,448 ✓ math correct.
- Tables 5 + 6 show 6 configs (Full + 5 ablations) and Fig 3 shows 7 configs (Full + 6 ablations) — with-orchestrator (Table 5) + with-graph and no-constitutional (Table 6) make 8 total including Full. ✓ Reconcilable, but the visual asymmetry across Tables 5/6/Fig 3 is annoying. No reviewer-fatal issue, just presentation.

### MINOR (citation drift / terminology / cross-ref)

#### MIN-1. Paper says "six datasets" body / Table 1, but abstract says "four established datasets"

- `sn-article.tex:123` abstract — **four**
- `sn-article.tex:406` Methodology — *"431-case benchmark from **six** established sources"*
- `sn-article.tex:749` Conclusion — *"431-case benchmark across **six** datasets"*

Same root cause as CRIT-1; abstract is stale.

#### MIN-2. Paper uses "1.7M tokens/hour" telemetry rate; SUMMARY/HANDOFF don't anchor this number

- `sn-article.tex:135` + line 437: 1.7M tokens/hour.
- Not contradicted by any supporting doc; just no provenance pointer to validate the figure for reviewers.

#### MIN-3. Paper §5.6 line 600 still uses "31.3pp prompt-fragility headline" framing

*"the 31.3pp 'prompt-fragility' headline conflates a small-model task-specification cost (4B annotation collapses −34.4pp without scaffolding) with a robust reasoning-stage behavior (14B RCA holds within 4.3pp)."*

This is the **v1 paper's** 31.3pp figure being reframed/critiqued. Phrasing is defensible but the same number appears as a fresh claim in line 137 (CRIT-2). Recommend either explicitly tagging "v1's 31.3pp headline" both places, or removing the v1 number from §1 (where it reads as a current claim).

#### MIN-4. CURRENT_RUNS.md is mostly session-10 (pre-D-1) — outdated denominators (142 / 360)

- `CURRENT_RUNS.md:54-65` shows Ablation matched eval with "RCA (142 evaluable) … Overall (360 evaluable)" — pre-D-1.
- Not a paper inconsistency per se, but a doc reader could be misled. The doc carries `_Last updated: 2026-05-17 13:15_` header (line 3) — pre-D-1 timestamp is honest, but the doc was not refreshed after D-1.

#### MIN-5. `paper_tables.md` is the **v1-style** output (RCA 92.5%, Overall 87.5%) — not used by paper but lives in `main_benchmark/`

- `paper_tables.md:9-13`: Overall **87.5%**, RCA **92.5%** — these are the v1 / rich-eval numbers, NOT the matched-eval numbers cited by paper.
- This file's existence next to `results.json` could mislead a future reader. SUMMARY.md §1 footnote (line 21) does flag "rich-eval; not paper-canonical".

#### MIN-6. Paper does not cite `phase5_stats.md` or `SUMMARY.md` provenance anywhere

The paper's matched-eval numbers (including BCa CIs, McNemar p, Cohen's h) all flow from `ablation_v4/phase5_stats.md` and `main_benchmark/phase5_stats.json`. The paper acknowledges Phase 5 stats methodology (§5.1.1) but never cites the artifact path. Acceptable for a journal paper, but reviewer-defense docs should preserve the linkage.

#### MIN-7. AUDIT_REPORT.md is pre-D-1 snapshot (2026-05-19); explicit header note covers this

- `AUDIT_REPORT.md:5` notes the post-D-1 update: "Current SHAs are in MANIFEST.md 'Post-D-1 state' section; current record counts are: 218 annotation + 180 rca + 33 qa_mcq = 431 total"
- Pre-D-1 stats (e.g. `rca_excluded: 71`, `rca_evaluable: 142`) still appear in per-file findings — accurately marked as the original 2026-05-19 snapshot.
- ✅ Not contradicting paper; explicit forensic preservation.

---

## Per-doc summary

### v2 paper vs SUMMARY.md

| Claim | Paper | SUMMARY.md | Status |
|---|---|---|---|
| Overall acc (main re-run) | 82.4% (294/357) line 455 | 82.4% (294/357) §3.3 | ✅ |
| Ann acc | 82.6% (180/218) line 467 | 82.6% (180/218) §3.3 | ✅ |
| RCA acc | 82.0% (114/139) line 468 | 82.0% (114/139) §3.3 | ✅ |
| BCa CI Overall | [78.2, 86.0] line 469 | [78.2, 86.0] §3.3 | ✅ |
| BERT-F1 main | 0.812 line 455 | 0.8124 §3.5 | ✅ (paper rounds) |
| Ablation Full overall | 84.0% (300/357) line 554 | 84.0% (300/357) §3.1 | ✅ |
| All 7 ablation configs | Tables 5 + 6 | §3.1 | ✅ all cells match |
| Excluded RCA count | 74 (41 Ch + 33 MCQ) line 433/447 | 74 §5 / §1 | ✅ |
| McNemar p (no sys prompt) | 3.4e−11 line 586 | 3.40e-11 §3.1 | ✅ |
| Cohen h (no sys prompt) | −0.52 line 586 | −0.520 §3.1 | ✅ |
| Llama RCA | 71.2% line 717 | 71.2 §1 | ✅ |
| DeepSeek RCA | 66.9% line 718 | 66.9 §1 | ✅ |
| Phase 4.5 LEMMA-CV ceiling | 100/100 n=80 N=431 line 739 | 100/100 n=80 N=431 §3.6 | ✅ |
| Latency P95 (Q4_K_M) | 48.57s Table 4 / 48.4s §6.2 | 48.4s §1 | ✅ |

**Verdict**: paper vs SUMMARY is essentially fully aligned. The single drift is "BERT-F1 0.812 vs 0.8124" — a deliberate rounding, not an error.

### v2 paper vs MANIFEST.md

MANIFEST is a SHA + file-path provenance doc, not a numeric claims doc. Cross-check:
- 16 result files covered (`results.json`, `results_sota_eval_431.json`, ablation_*, SOTA, phase46 no-prompt).
- Post-D-1 section (lines 60–87) provides current canonical SHA-256s.
- Paper does not cite MANIFEST directly; not flagged.

**Verdict**: ✅ no contradictions found.

### v2 paper vs AUDIT_REPORT.md

- AUDIT_REPORT.md is the **2026-05-19** content audit (pre-D-1). Header note (line 5) explicitly documents the post-D-1 state.
- Per-file findings show 23 OK / 0 WARN / 0 FAIL on the 2026-05-19 snapshot.
- Bert-F1 zeros disclosed inline; D-6 footnote in BUG_HISTORY.md and SUMMARY.md §3.5 cover the post-D-6 recompute.

**Verdict**: ✅ no open flags contradict paper claims. Pre-D-1 numbers in AUDIT_REPORT are clearly marked as forensic / superseded.

### v2 paper vs METHODOLOGY.md

| Claim | Paper | METHODOLOGY.md | Status |
|---|---|---|---|
| Exclusion = 74 (41 Ch + 33 MCQ) | line 433 / 447 / 474 | §2 line 19 + 22 | ✅ |
| Matched-substring evaluator | §5.1 line 447 | §3 + §4 + §6 | ✅ |
| Composition 218 + 180 + 33 | Table 4 footnote + §4.1.1 | §1 line 11 + §6 line 111 | ✅ |
| 3-point rubric mention (v1 disclosure) | line 447 + line 597 | §3 (under "Standard with system prompt") | partial — METHODOLOGY documents the v2 substring eval, but the v1→v2 rubric transition rationale is housed in SUMMARY.md / BUG_HISTORY.md, not METHODOLOGY |
| Latency methodology (RTT-compensated) | line 447 + Table 4 footnote | §7 line 127-131 | ✅ |
| Stack A vs Stack B split | line 514 | §7 + `gate15_comparison.md` | ✅ |
| Substring eval weaknesses | not in paper | §4 known weaknesses | one-way — paper does not warn about substring eval's "ISM"/"6 dB" false-positive bias (METHODOLOGY §4 does) |

**Verdict**: ✅ no contradictions. METHODOLOGY contains some self-protective caveats (eval weaknesses) that paper omits — acceptable per Phase B framing, but reviewer-facing.

### v2 paper vs BUG_HISTORY.md

| Claim | Paper | BUG_HISTORY.md | Status |
|---|---|---|---|
| Phase 4.5 LEMMA-CV ceiling (no-graph=with-graph=100%, n=80) | line 739 | D-17 footnote line 177-181 | ✅ |
| D-17 dataclass serialization patch | not mentioned (forensic) | D-17 line 175-183 | RESOLVED ✓ |
| D-1 OpsEval 33 reclassify | mentioned in §4.1.1 + §5.1 + Table 2 footnote (lines 433/447/474) | D-1 footnote line 171-173 | RESOLVED ✓ |
| D-6 BERT-F1 recompute | "BERT-F1 0.812" line 455 | D-6 footnote line 185-187 | RESOLVED ✓ |
| OpenSSH 50% all FP | line 486/501 | "What was NOT a bug" line 160 | ✅ |
| BGL false positives dominant failure | line 486 | not directly in bug history (Phase 5 finding) | ✅ |

**Verdict**: ✅ all bug-resolved markers cover paper claims. No open / unresolved D-items affect paper validity.

### v2 paper vs HANDOFF.md

This is where most discrepancies live (see CRIT-3 + CRIT-4 + IMP-2 above).

| Claim | Paper | HANDOFF | Status |
|---|---|---|---|
| Dataset = 431 | ✓ | §6 line 188 | ✅ |
| Overall acc 82.4% | ✓ | §7 line 208 + §14 line 441 | ✅ |
| Ann 82.6 | ✓ | §7 line 209 | ✅ |
| RCA 82.0 (114/139) | ✓ | §7 line 210 | ✅ |
| BERT-F1 0.8124 | 0.812 (rounded) | §7 line 208 | ✅ |
| Ablation Full Overall 84.0% (matched eval) | line 554 | §7 line 216 | **conflict** — HANDOFF says "84.0%" but lists Single-4B at 82.9% / -1.1pp instead of 82.6% / -1.4pp (CRIT-3) |
| Single-4B / Single-14B / No-constitutional cells | match SUMMARY/phase5_stats.md | §7 lines 217-218, 222 | **conflict** (CRIT-3) |
| No-system-prompt Overall 61.3% Δ−22.7pp p=3.4e-11 | ✓ | §7 line 220: 60.8% Δ−23.2pp p<1e-15 | **conflict** (CRIT-3) |
| Llama Overall 83.5 / DeepSeek Overall 81.2 | ✓ | §7 lines 232-233: 83.3 / 81.1 | **conflict** (CRIT-4) |
| Stack A P95 / Stack B P95 / 1.51× | paper §5.5 vague; §6.2 cites 48.4s Q4 only | §7 lines 240-246 | HANDOFF cites gate15 30-case smoke; paper Table 4 cites 431-case run; both valid but not the same N |
| Phase 4.5 PATH 4 outcome | line 739 (calls it "planned") | §7 line 248-256 (calls it "PATH 4 outcome") | **terminology** (IMP-3) |
| §14 Phase Completion status | line 442 (Phase 4.2 complete, Overall 82.4%) | §14 line 441 | ✅ |
| 12 constitutional principles / 3 tiers | line 123 / 383 | §11 (Key Decisions) | ✅ |
| Dual-stack arch (Stack A = accuracy / Stack B = latency) | implicit in §5.5 + §6.2 | §11 line 372-374 | ✅ |
| 4B + 14B model selection | line 277 + 279 | §11 line 374-378 | ✅ |

**Verdict**: HANDOFF.md §7 ablation cells + SOTA Overall cells are stale / drifted. **HANDOFF is the doc that disagrees with itself** — its own §14 (Phase Completion) matches paper, but §7 (Current Benchmark Results) has out-of-date cells. Paper and SUMMARY agree; HANDOFF §7 should be re-synced from `phase5_stats.md`.

---

## OK (verified consistent claims)

1. ✅ **Headline overall accuracy** 82.4% (294/357) — paper line 455, SUMMARY §3.3, HANDOFF §7 line 208, phase5_stats.md line 59, Conclusion line 749.
2. ✅ **Ann 82.6% (180/218)** + **RCA 82.0% (114/139)** — paper Table 2, SUMMARY §3.3, HANDOFF §7.
3. ✅ **Excluded RCA = 74** (41 Chinese + 33 OpsEval MCQ post-D-1) — paper §4.1.1 + §5.1 + Table 2 footnote, METHODOLOGY §2, SUMMARY §5, HANDOFF §6.
4. ✅ **BERT-F1 0.812 main re-run** — paper §5.2 line 455, SUMMARY §3.5, `_bert_f1_recompute_summary.json` n_pairs=370 / mean 0.8124, BUG_HISTORY D-6 RESOLVED.
5. ✅ **Phase 5 ablation cells (all 7 non-Full configs)** Ann/RCA/Overall — paper Tables 5+6 = SUMMARY §3.1 = phase5_stats.md = ALL match.
6. ✅ **McNemar p (no system prompt) = 3.4e−11** — paper line 586, SUMMARY §3.1, phase5_stats.md line 23.
7. ✅ **McNemar p (with graph) = 0.289 NS** — paper Tables 5+6, SUMMARY §3.1, phase5_stats.md, paper §5.6 (line 540) all match.
8. ✅ **Cohen h (no sys prompt overall) = −0.52** — paper line 586, SUMMARY §3.1.
9. ✅ **No-constitutional asymmetry**: Ann +6.4pp p=0.001 / RCA −12.9pp p=5.3e−4 — paper line 590-591, SUMMARY §4.3, phase5_stats.md.
10. ✅ **Llama 3.3-70B / DeepSeek V3.2 RCA + ΔRCA** — paper Table 7 (71.2 / 66.9 / Δ−10.8 / Δ−15.1), SUMMARY §1, HANDOFF §7 lines 232-235 (Δ matches; only Overall % drifts).
11. ✅ **Drain (LogPAI)** 50.5% (102/202) annotation-only — paper Table 7 line 719, SUMMARY §1 line 32.
12. ✅ **Phase 4.5 ceiling outcome** (no-graph=with-graph=100%, n=80, populated N=431) — paper line 739, SUMMARY §3.6, HANDOFF §7, BUG_HISTORY D-17.
13. ✅ **Latency Table 4 cells** (Stack A end-to-end P50 4.15 / P95 48.57 / Avg 17.62 / 14B P50 30.72 / 14B P95 59.38 etc.) — paper Table 4 vs SUMMARY §1 row "P50 4.1s / P95 48.4s / avg 17.6s" (paper has more decimal precision; figures consistent).
14. ✅ **Architecture (4B + 14B simultaneous, ~15GB / 63% of 24GB)** — paper §3.3 line 277-281, HANDOFF §11, CLAUDE.md.
15. ✅ **3-point rubric INTENTIONAL DISCLOSURE** — paper line 447 (§5.1) + line 597 (Table 6 footnote), 2 mentions. METHODOLOGY documents the eval-method change.
16. ✅ **All 14 PRT brief points** numerically reconciled to source-of-truth `phase5_stats.md` + `SUMMARY.md` (some with HANDOFF drift noted).

---

## Skipped

- The paper's TikZ figures (Fig 1 architecture, Fig 2 graph schema, Fig 3 ablation chart) were inspected for numerical labels only — Fig 3's per-bar numbers (48.6, 84.4, 82.6, 82.6, 82.6, 89.4, 83.0 / 81.3, 82.7, 83.5, 82.7, 75.5, 72.7, 85.6) at `sn-article.tex:658-682` were spot-checked against `phase5_stats.md` and **all 14 cells match exactly**.
- Bibliography entries not audited (not in scope).
- Frontend / src code not audited (not in scope).
- Memory files / sealed forensic docs not read per task constraints.
- BCa CI cells of Tables 5+6 spot-checked (3 of 21 rows verified against phase5_stats.md); no drift found; full row-by-row not performed due to length cap.

---

## Recommendations

**Blocking before camera-ready submission**:

1. **Fix CRIT-1 + CRIT-2 (abstract + intro)**: replace "150-test benchmark from four established datasets, 90.7% overall accuracy, seven-configuration ablation, 31.3 percentage point drop, 1,050 inferences" with the v2 numbers: 431-case from six datasets, 82.4% overall, 8-configuration ablation (3,448 inferences), and either drop the "31.3pp" framing or scope it explicitly as "the v1 headline …". This is the single biggest reviewer-facing risk.

**High-priority (HANDOFF-only, doesn't affect paper but agents reading HANDOFF will mis-cite)**:

2. **Fix CRIT-3**: re-sync `HANDOFF.md` §7 "Phase 4.3 Ablation" table from `benchmark/final/ablation_v4/phase5_stats.md`. Specifically:
   - Single-4B Overall **82.6%** / Δ **−1.4pp** (not 82.9% / −1.1pp)
   - Single-14B Overall **83.8%** / Δ **−0.3pp** (not 83.5% / −0.5pp)
   - No-constitutional RCA **72.7%** / Overall **82.9%** / Δ **−1.1pp** (not 71.9% / 82.6% / −1.4pp)
   - No-system-prompt Overall **61.3%** / Δ **−22.7pp** / p **3.40e−11** (not 60.8% / −23.2pp / <1e-15)

3. **Fix CRIT-4**: HANDOFF §7 SOTA overall cells: Llama **83.5** (not 83.3), DeepSeek **81.2** (not 81.1).

**Medium-priority polish**:

4. **IMP-3**: Change "**planned** homogeneous-LEMMA 5-fold" (paper line 739) to "**conducted**" or "**run**". The experiment finished; only the per-case JSONL was lost (D-17). Aggregate result is real.

5. **IMP-5**: Table 1 line 425 "213 RCA" cell would benefit from a footnote tagging "(180 RCA + 33 qa_mcq after D-1 re-label)".

6. **IMP-2**: If Stack B vLLM smoke is going to remain only a 30-case smoke, consider either (a) suppress the "1.5× speedup" sentence in §5.5 line 514 to a Future Work mention, or (b) commit to a full 431-case Stack B run before submission. Currently the asymmetry between "we benchmarked 431 on Stack A" + "we smoke-tested 30 on Stack B" then claim "1.5× speedup" is reviewer-vulnerable.

**Cosmetic**:

7. **MIN-3**: Disambiguate "31.3pp" mentions — either tag both as v1-headline-being-critiqued or remove the §1 occurrence.

8. **MIN-4**: `CURRENT_RUNS.md` could carry an "obsoleted by D-1 re-label; see SUMMARY.md §3" header to prevent future confusion.

9. **MIN-5**: `main_benchmark/paper_tables.md` could carry an ARCHIVE NOTICE header similar to `_archived_session_history/` docs — it's v1-style rich-eval and risks misleading a reader.

**No action needed** (already correct):
- All ablation Table 5 + Table 6 cells in the paper.
- All Table 7 SOTA cells in the paper.
- All Phase 4.5 disclosures.
- All exclusion-count disclosures (74).
- BERT-F1 disclosure pattern.
- 3-point rubric INTENTIONAL DISCLOSURES (2 mentions per locked decision).

---

*End of cross-doc consistency audit. 487 lines. No source files modified.*
