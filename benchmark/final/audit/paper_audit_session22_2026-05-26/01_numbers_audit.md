# 01 — Numbers Audit (Tables 1-7 + Fig 3 + statistical claims)

> Audit date: 2026-05-26 (Session 22)
> Auditor: #1/5 — read-only numeric verification only
> Sandbox under audit: `PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2.sandbox-session16/main/sn-article.tex` (787 lines)

## Scope

Every numeric value in Tables 1–7, Figure 3, the abstract, and statistical-claim sentences of the v2 sandbox paper was traced to a single source-of-truth file under `benchmark/final/` and verified for accuracy, CI consistency, denominator consistency, p-value / Cohen's-h consistency, and exclusion-count consistency. No source files were modified. All findings cite v2 `.tex` line numbers AND the source path.

## Method

- Read full sandbox `.tex` (787 lines) end-to-end.
- Grepped for: `\begin{table}`, `\caption{`, `\d+\.\d+\\%`, `\d+/\d+`, `n=\d+`, McNemar/BCa/Cohen markers — to enumerate every numeric table cell and statistical claim.
- For each finding, read the source-of-truth file directly: `main_benchmark/{summary.json,phase5_stats.json,results.json,results_sota_eval_431.json,paper_tables.md,README.md}`, `ablation_v4/{phase5_stats.json,matched_eval_table.md}`, `sota_baselines/{drain_summary.json, drain.jsonl, llama_3_3_70b.jsonl, deepseek_v3.jsonl}`, `_bert_f1_recompute_summary.json`, `infrastructure/gate15_comparison.md`, `SUMMARY.md`.
- Recomputed denominators, accuracies, and percentiles via inline Python (utf-8 decode) against the raw `.json/.jsonl` rather than trusting any cached summary, e.g. n_eval=357=218+139 split per `task_type`+`eval_method!='excluded'`.
- Cross-verified Table 7 SOTA rows by recomputing Ann/RCA/Overall accuracy directly from `llama_3_3_70b.jsonl` and `deepseek_v3.jsonl`.

## Findings

### CRITICAL (paper says X, source says Y; gap ≥ 1pp or unjustified)

**C-1 — Abstract still cites V1 numbers (NOT V2)**
- v2 `.tex` line 123 (abstract): "Validated on a 150-test benchmark from four established datasets, the system achieves 90.7% overall accuracy. A seven-configuration ablation study confirms system prompt engineering as the single most critical component."
- Source-of-truth: `main_benchmark/summary.json` + `phase5_stats.json` + `ablation_v4/phase5_stats.json` + `SUMMARY.md` §1: 431-case benchmark from **six** sources, 82.4% overall (matched-substring) / 87.5% (rich-eval); **8-config** ablation (not 7).
- Discrepancy: 150 → 431 cases; 90.7% → 82.4%; four → six datasets; seven → eight ablation configs.
- Severity: **CRITICAL**. Abstract is the most-read paragraph and disagrees with every Table 1–7 number in the same document.

**C-2 — Introduction §1 ¶2 repeats stale V1 numbers**
- v2 `.tex` line 137: "On a curated 150-test benchmark from four established datasets, the system achieves 90.7% overall accuracy; a seven-configuration ablation study (1,050 inferences) confirms system prompt engineering as the single most critical component (31.3 percentage point drop without it)."
- Source-of-truth: SUMMARY.md, paper Table 5/6/7. Body section §5.2 line 455 + Table 2 line 469 say 82.4% (294/357), 431-case bench, 6 sources. §5.6 line 540 says "8-configuration ablation (3,448 inferences)". Conclusion line 749 says "8-configuration ablation". No source supports 150-test / 90.7% / 7-config / 1050 inferences / -31.3pp.
- Severity: **CRITICAL** — directly contradicts Tables 1, 2, 5, 6, 7 and the conclusion.

**C-3 — RG2 / Related-Work 0.7% overhead claim mismatches ablation Δ**
- v2 `.tex` line 143 (RG2) AND line 168 (Related Work §2.3): "imposing only 0.7\% accuracy overhead" for the constitutional layer.
- Source-of-truth: `ablation_v4/phase5_stats.json` `no_constitutional.vs_full.overall.delta_pp = -1.1204…`. Removing constitutional changes overall accuracy by 1.12pp (Full 84.0 → 82.9). Paper Table 6 line 592 itself reports "$-$1.1pp" for the no-constitutional overall row.
- Discrepancy: stated 0.7% vs measured ~1.1pp. 0.4pp delta.
- Severity: **CRITICAL** — 0.7% is a stale V1 figure; the V2 paper's own Table 6 directly contradicts it.

**C-4 — Related Work §2.1 "3.3 percentage points improvement" claim**
- v2 `.tex` line 160: "Our dual-agent approach separates fast annotation from deep reasoning, with ablation results showing 3.3 percentage points improvement over single-model alternatives."
- Source-of-truth: `ablation_v4/phase5_stats.json`. Full vs Single-4B overall Δ=+1.4pp; Full vs Single-14B overall Δ=+0.3pp. Per-task: Full RCA 85.6% vs Single-4B RCA 82.7% / Single-14B RCA 82.7% → max Δ=+2.9pp. No metric yields 3.3pp.
- Severity: **CRITICAL** (≥0.4pp wrong; no source produces 3.3).

**C-5 — Table 4 (Latency) 14B row label/footnote internally inconsistent on N**
- v2 `.tex` line 527 ("14B Reasoning (RCA)") + line 534 footnote ("n=431 (218 annotation + 180 RCA + 33 qa_mcq routed through 14B per Sec. 3.5)").
- Source-of-truth: `main_benchmark/results.json` per-record `inference_latency_ms` + `task_type`:
  - rca-only (n=180): P50=30.72 / P95=59.38 / Avg=32.19 / min=11.55 / max=84.50 — matches paper.
  - rca+qa_mcq combined (n=213, what footnote describes): P50=29.83 / P95=62.20 / Avg=32.50 / max=84.50 — does NOT match paper row.
- Discrepancy: The displayed numbers are RCA-only (n=180), but the footnote claims n=431 inferences include qa_mcq through 14B. Either the label is wrong (should be "14B RCA-only"), or the footnote is wrong (should specify n=180 for the 14B row), or the cell values should be the combined n=213 figures.
- Severity: **CRITICAL** for table/footnote internal consistency. Numeric magnitude shift is small (Avg 32.19→32.50, P50 30.72→29.83) but the methodological statement is misleading.

**C-6 — Table 7 vs §5.7 prose: "Same 431-case benchmark" claim for Drain**
- v2 `.tex` line 704: "We compare against three external baselines on the same 431-case benchmark and matched-substring evaluator". Table 7 row 719: "Drain (LogPAI) 50.5% (102/202) N/A N/A".
- Source-of-truth: `drain_summary.json.dataset = "benchmark_400_seed42.json"`; `drain.jsonl` has 202 records (35 BGL + 93 HDFS + 37 SSH + 37 Apache) — a SUBSET, not "the same 431-case benchmark". The 218→202 (16 excluded) part is consistent with the footnote line 724 ("16 no-template cases excluded") but the dataset name itself indicates Drain ran on the V1 400-case split, not the V2 431-case curated benchmark.
- Severity: **CRITICAL** for methodological claim — Drain's denominator is from a different dataset version.

### IMPORTANT (questionable; 0.1–1pp gap, missing CI, or label wrong)

**I-1 — Latency footnote (line 514) says "vLLM+FP8" but Stack B is AWQ**
- v2 `.tex` line 514: "Preliminary vLLM+FP8 gate tests show ~1.5× speedup".
- Source-of-truth: `infrastructure/gate15_comparison.md` row 1: "Stack B (vLLM AWQ awq_marlin)". Quantization is **AWQ awq_marlin**, not FP8. The 1.51× P95 speedup (65.96s / 43.71s) is verified ✓ but the quantization label is wrong.
- Severity: IMPORTANT (terminology / reproducibility).
- (Future Work §6.3 line 744 ALSO says "vLLM with FP8 plus speculative decoding" — same mislabel; future-work framing makes this less acute but still inconsistent with §5.5.)

**I-2 — Latency Table 4 vs summary.json P95 (end-to-end)**
- v2 `.tex` Table 4 line 529: End-to-End P95 = 48.57.
- Source-of-truth: `main_benchmark/summary.json.p95_latency_ms = 48368.23` → 48.37s (linear interpolation). The 48.57 matches index-floor convention `s[int(0.95*431)]`. Both methods are defensible; the inconsistency is that the paper reports floor-index P95 but the summary.json (also a paper artifact) reports linear-interp P95.
- Severity: IMPORTANT (≤0.2pp). Disclose percentile method in §5.5 or footnote.

**I-3 — Latency Table 4 footnote: P99 = 81.16s vs summary.json**
- v2 `.tex` line 534 footnote: "End-to-end P99 81.16s".
- Source-of-truth: `summary.json.p99_latency_ms = 80544.31` → 80.54s (linear). Index-floor `s[int(0.99*431)]` = 81.16s. Same methodological inconsistency as I-2.
- Severity: IMPORTANT.

**I-4 — Table 6 With-graph delta sign / magnitude vs phase5_stats.md**
- v2 `.tex` line 588 (`tab:ablation_comp` with-graph RCA): "$-$2.1pp" delta.
- Source-of-truth: `ablation_v4/phase5_stats.json.with_graph.vs_full.rca.delta_pp = -2.1582…` (rounds to -2.2pp). `ablation_v4/phase5_stats.md` also says "-2.2pp". Paper Table 5 line 563 (with orchestrator) uses "-2.1pp" similarly; orchestrator delta_pp is also -2.1583… (≈ -2.2pp).
- Severity: IMPORTANT — rounds-the-wrong-way (truncation, not nearest-even). Two rows affected (Table 5 line 563 + Table 6 line 588).

**I-5 — Statistical methodology §5.1 line 451: "differ by at most 5 cases"**
- v2 `.tex` line 451: "Independent runs of Full Hybrid at T=0 on identical hardware differ by at most 5 cases".
- Source-of-truth: main re-run RCA = 114/139 (82.0%); ablation Full RCA = 119/139 (85.6%). Cell-level diff = 5 cases on RCA, but the union of Ann + RCA differences is bigger: main Ann = 180/218; ablation Full Ann = 181/218 (1-case diff). Total cell-level diff = 6 cases (1 ann + 5 rca), with 5-case net delta on overall (300-294=6 actually; not 5).
- Recomputed: 300−294 = 6 cases overall. Footnote on Table 2 line 474 says "5-case difference" but actually 6 cases differ on overall.
- Severity: IMPORTANT (off-by-one on a methodological claim).

**I-6 — Table 5 / Table 6 are missing BERT-F1 column despite D-6 recompute**
- v2 `.tex` Tables 5 and 6 have no BERT-F1 column, even though `_bert_f1_recompute_summary.json` provides per-config BERT-F1 (full=0.8126, single-4b=0.8176, single-14b=0.8083, no-structured=0.8377, no-system-prompt=0.8102, with-graph=0.8116, no-constitutional=0.8238, with-orchestrator=0.8113).
- Table 2 line 469 DOES include the BERT-F1 trio. Table 7 also omits BERT-F1, but §5.2 prose (line 455) gives "Ours 0.812, Llama 0.827, DeepSeek 0.826" — which matches source. So BERT-F1 is partially integrated.
- Severity: IMPORTANT — verify whether this is by design (per D-6 Option C "1-sentence fallback") or an oversight.

### MINOR (cosmetic, ≤0.1pp, or methodological consistency)

**M-1 — Conclusion (line 749) abstract-style claim consistency**
- v2 `.tex` line 749: "Validated on a 431-case benchmark across six datasets, the system achieves 82.4% overall accuracy (BCa CI [78.2, 86.0])".
- Source: `phase5_stats.json` CI = [0.7815, 0.8599] → [78.2, 86.0] ✓. Number = 82.4% ✓. Consistent with body.
- Severity: NONE — flagged only to confirm conclusion is internally consistent; abstract/intro are the violators (see C-1/C-2).

**M-2 — Table 3 LEMMA-RCA 93.8%**
- v2 `.tex` line 503: "LEMMA-RCA RCA 80 80 93.8%".
- Source: 75/80 = 93.75% → rounds to 93.8% ✓. (paper_tables.md old version said 100.0% — that's pre-D-1 rich-eval; paper correctly uses matched-eval value.)
- Severity: NONE / verified clean.

**M-3 — Table 4 Stack-A label**
- v2 `.tex` Table 4 caption (line 518): "Inference latency and resource utilization on AWS L4 24 GB (431 inferences, RTT-compensated)". No explicit "Stack A Ollama Q4_K_M" label in the table; only mentioned implicitly via §5.5 prose. Audit-scope instruction expected component×metrics layout, which IS present (rows are 4B/14B/E2E; cols are VRAM/P50/P95/Avg/Range).
- Severity: NONE — Decision 1 (component×metrics) verified.

**M-4 — Table 7 footnote "scale-favoring classification"**
- v2 `.tex` line 724 footnote: "Frontier monoliths win annotation (scale-favoring classification) but lose RCA". Source confirms: Llama Ann 91.3% vs Ours 82.6% (Δ=+8.7pp for Llama); DeepSeek Ann 90.4% vs Ours 82.6% (Δ=+7.8pp); but Ours RCA 82.0 vs Llama 71.2 / DeepSeek 66.9. Directional claim verified.
- Severity: NONE.

## OK (verified clean against source-of-truth)

### Table 1 — Datasets
- Loghub HDFS 100 ✓; Loghub BGL 38 ✓; Loghub Apache 40 ✓; Loghub OpenSSH 40 ✓; OpsEval 133 ✓ (= 100 rca + 33 qa_mcq); LEMMA-RCA 80 ✓; Total 431 = 218 Ann + 213 RCA ✓.

### Table 2 — Overall Benchmark Results (matched-eval)
- Ann 82.6% (180/218) ✓ — `phase5_stats.json` `main_rerun.annotation`.
- Ann BCa CI [77.1, 87.2] ✓ — source [0.7706, 0.8716].
- RCA 82.0% (114/139) ✓ — source `main_rerun.rca`.
- RCA BCa CI [74.8, 87.8] ✓ — source [0.7482, 0.8777].
- Overall 82.4% (294/357) ✓ — source `main_rerun.overall`.
- Overall BCa CI [78.2, 86.0] ✓ — source [0.7815, 0.8599].
- BERT-F1 0.822 / 0.795 / 0.812 ✓ — `_bert_f1_recompute_summary.json` row #1 (main_benchmark): 0.822 ann / 0.7954 rca / 0.8124 mean.
- Cosine/Term values (0.24/0.19; 0.41/0.78; 0.33/0.53) ✓ — `summary.json` annotation_cosine_sim=0.2431, rca_cosine_sim=0.4134, cosine_similarity=0.3265, annotation_term_overlap=0.1877, rca_term_overlap=0.7794, term_overlap=0.5249.

### Table 3 — Per-source breakdown (post-D-1)
- HDFS 100/100/94.0% ✓; Apache 40/40/100.0% ✓; BGL 38/38/68.4% ✓; OpenSSH 40/40/50.0% (all 20 FP) ✓ (recomputed: 20 errors all false positives — verified from results.json error pattern).
- OpsEval (RCA-subs aggregate) 100/59/66.1% ✓ (recomputed: 100=6+7+8+79 RCA-task, 59 evaluable=6+2+8+43, correct=39=5+0+6+28, 39/59=66.10%).
- LEMMA-RCA 80/80/93.8% ✓ (75/80 = 93.75%).
- Footnote: Wired 28/43 ✓, Mobile 6/8 ✓, 5G 5/6 ✓, Log-Analysis 0/2 ✓. 33 qa_mcq + 41 Ch = 74 excluded ✓.

### Table 4 — Latency (Stack A Ollama Q4_K_M)
- 4B: P50=2.99 / P95=3.87 / Avg=3.07 / Range 2.05–21.74 — recomputed from `results.json` per-record (n=218): P50=2.99 ✓ (linear=2.978), P95=3.87 ✓ (floor-idx=3.8654), Avg=3.07 ✓, min=2.05 ✓, max=21.74 ✓.
- 14B (RCA-only, n=180): P50=30.72 ✓, P95=59.38 ✓ (floor-idx), Avg=32.19 ✓, min=11.55 ✓, max=84.50 ✓. (Footnote conflict — see C-5.)
- E2E (n=431): P50=4.15 ✓ (linear=4.147), max=84.50 ✓, Avg=17.62 ✓. P95=48.57 (floor) vs summary.json=48.37 (linear) — see I-2. P99=81.16 (floor) vs summary.json=80.54 (linear) — see I-3.
- VRAM ~4 / ~11 / ~15 GB — claimed but not numerically verified (no per-config VRAM measurement in source-of-truth; consistent with CLAUDE.md `~4GB / ~11GB / ~15GB`).
- 63% of 24 GB = 15/24 = 62.5% (rounds to 63%) ✓.
- Network RTT 1.10 ms ✓ — `summary.json.network_rtt_ms = 1.1041865` rounds to 1.10. (§5.1 line 447 says "1.95 ms" — see flag note in M-5 below.)

### Table 5 — Architecture / orchestration ablation (matched-eval, 357 cases)
- Full Hybrid 83.0/85.6/84.0 with CIs [77.5,87.6]/[79.1,90.6]/[79.8,87.4] ✓ — `ablation_v4/phase5_stats.json.full.tasks.*` 0.8302/0.8561/0.8403; CIs [0.7752,0.8761]/[0.7914,0.9065]/[0.7983,0.8739].
- Single-4B ann 82.6 / rca 82.7 / overall 82.6, deltas -0.5/-2.9/-1.4, McN p 1.000/0.424/0.302, h -0.01/-0.08/-0.04 ✓ — all four cells match source.
- Single-14B ann 84.4 / rca 82.7 / overall 83.8, deltas +1.4/-2.9/-0.3, p 0.664/0.219/1.000, h +0.04/-0.08/-0.01 ✓.
- With orchestrator: ann/rca/overall 82.6/83.5/82.9, deltas -0.5/**-2.1**/-1.1, p 1.000/0.453/0.289, h -0.01/-0.06/-0.03 — see I-4 (rca delta should be -2.2 not -2.1).

### Table 6 — Component ablations
- Full Hybrid baseline overall 84.0 [79.8, 87.4] ✓.
- No structured ann 82.6 / rca 75.5 / overall 79.8 with deltas -0.5/-10.1/-4.2 ✓; p 1.000/**0.004**/0.086 ✓; h -0.01/-0.26/-0.11 ✓.
- No sys. prompt ann **48.6** / rca 81.3 / overall **61.3** with deltas **-34.4**/-4.3/**-22.7**; p **1.2e-10**/0.180/**3.4e-11** ✓; h **-0.75**/-0.12/**-0.52** ✓ — all match `no_system_prompt.vs_full`.
- With graph (RAG) ann 82.6 / rca 83.5 / overall 82.9; deltas -0.5/**-2.1**/-1.1 — see I-4; p 1.000/0.453/0.289 ✓; h -0.01/-0.06/-0.03 ✓.
- No constitutional ann **89.4** / rca **72.7** / overall 82.9; deltas **+6.4**/**-12.9**/-1.1; p **0.001**/**5.3e-4**/0.652 ✓; h **+0.19**/**-0.32**/-0.03 ✓.

### Figure 3 — Ablation bar chart
- All 14 bar values match Table 5+6 numbers EXACTLY (4B annotation): No Sys Prompt 48.6 ✓; Single 14B 84.4 ✓; With Graph 82.6 ✓; Single 4B 82.6 ✓; No Structured 82.6 ✓; No Constitutional 89.4 ✓; Full Hybrid 83.0 ✓. RCA: 81.3 / 82.7 / 83.5 / 82.7 / 75.5 / 72.7 / 85.6 ✓.
- Callout "$-$34pp drop!" — matches -34.4pp from no-system-prompt ann delta. (Rounded down to 34 for display.)
- 84% baseline ✓ — Full Hybrid overall.
- Caption: "Full Hybrid achieves 83% annotation and 86% RCA" — 83.0 and 85.6 round to 83/86 ✓.

### Table 7 — SOTA comparison
- Ours: Ann 82.6 / RCA 82.0 / Overall 82.4 ✓.
- Llama-3.3-70B: Ann 91.3 / RCA 71.2 / Overall 83.5 — recomputed from `llama_3_3_70b.jsonl`: ann 199/218=91.28%→91.3 ✓; rca 99/139=71.22%→71.2 ✓; overall 298/357=83.47%→83.5 ✓. ΔRCA = Ours 82.0 − Llama 71.2 = +10.8 ✓ (paper says Llama "-10.8pp" relative).
- DeepSeek-V3.2: Ann 90.4 / RCA 66.9 / Overall 81.2 — recomputed: ann 197/218=90.37%→90.4 ✓; rca 93/139=66.91%→66.9 ✓; overall 290/357=81.23%→81.2 ✓. ΔRCA = +15.1 ✓.
- Drain: 50.5% (102/202) ✓ — `drain_summary.json` 0.505, 102/202. (Caveat — see C-6 on denominator.)

### Statistical methodology §5.1 (line 449–451)
- 95% BCa, n_resamples=10000, seed=42, SciPy bootstrap ✓ — `phase5_stats.json.bootstrap` matches exactly: `{n_resamples: 10000, ci: 0.95, method: "BCa", seed: 42}`.
- McNemar exact two-sided binomial ✓.
- Cohen's h formula ✓.
- 357 paired cases per configuration ✓ — every `vs_full.overall.n_paired = 357` in phase5_stats.json.

### Exclusion counts
- Paper §3.5 line 433 + §5.1 line 447 + Table 2 footnote + Table 3 footnote: 74 = 41 Chinese + 33 OpsEval-remined MCQ ✓ — confirmed by SUMMARY.md and per-source recompute (33 qa_mcq + 41 Chinese excluded by eval_method='excluded').

### Run-to-run variance disclosure
- Table 2 footnote line 474 + Table 6 footnote line 597: "5-case difference" / 82.0% vs 85.6% on identical 139 RCA cases — see I-5 (actually 5 RCA + 1 Ann = 6 overall delta cases).

### BERT-F1 §5.2 prose
- v2 `.tex` line 455: "Ours 0.812, Llama 3.3-70B 0.827, DeepSeek V3.2 0.826" — source `_bert_f1_recompute_summary.json`: Ours 0.8124, Llama 0.8269, DeepSeek 0.8264. All match to 3 dp ✓.

## Skipped / Could not verify

**S-1 — VRAM figures in Table 4 (~4 / ~11 / ~15 GB)**: no per-run VRAM measurement file in source-of-truth tree; consistent with CLAUDE.md hardware spec and Q4_K_M model sizes but not numerically traceable to a benchmark artifact.

**S-2 — §5.1 line 447 "calibration RTT 1.95 ms"**: paper text says 1.95 ms; Table 4 footnote (line 534) says 1.10 ms; `summary.json.network_rtt_ms = 1.10`. Either the 1.95 figure is from a different calibration run (not in this directory) or stale. **Could not verify 1.95** — likely an inconsistency, but conservatively flag rather than count as CRITICAL since no source contradicts 1.95 (it's just unsupported).

**S-3 — §1 "1.7M tokens/hour" telemetry rate**: cited to opentelemetry2024collector / datadog2024observability; not a benchmark number; outside numbers-audit scope.

**S-4 — Drain BERT-F1**: explicitly excluded in source (boolean output, BERTScore not meaningful). Paper Table 7 row also lists Drain as N/A for RCA. Consistent.

**S-5 — §6.2 "P95 48.4 s on Q4_K_M / Ollama" (line 739)**: matches summary.json linear-interp P95 (48.37→48.4). But Table 4 itself says 48.57 (floor-idx). Internal inconsistency, but the §6.2 figure aligns with summary.json. Flag noted in I-2.

## Recommendations (what needs updating; no specific text rewrites)

1. **Abstract (line 123)** — update to 431-case / 6 sources / 82.4% / 8-config to match the rest of the paper. (C-1)
2. **Introduction §1 ¶2 (line 137)** — same replacements as #1; also replace the "-31.3pp" headline with -22.7pp overall or -34.4pp (ann-specific). (C-2)
3. **RG2 + Related Work 0.7% (lines 143, 168)** — replace 0.7% with 1.1pp (consistent with Table 6 no-constitutional row). (C-3)
4. **Related Work §2.1 "3.3 percentage points" (line 160)** — replace with a figure that traces to Table 5 (e.g., +2.9pp on RCA against single-model, or +1.4pp overall vs Single-4B). (C-4)
5. **Table 4 row label + footnote (lines 527, 534)** — disambiguate whether 14B row is RCA-only (n=180) or all 14B work (n=213). Either change the label to "14B Reasoning (RCA, n=180)" and rewrite the footnote, OR recompute the row with n=213 to match the footnote claim. (C-5)
6. **§5.7 prose (line 704)** — qualify Drain's "same 431-case benchmark" claim: Drain runs on 202 annotation cases from a different curation (`benchmark_400_seed42.json`), not the 431-case V2 benchmark. (C-6)
7. **§5.5 + §6.3 (lines 514, 744)** — fix "vLLM+FP8" → "vLLM AWQ awq_marlin" (matches `gate15_comparison.md`). (I-1)
8. **Table 4 latency percentile method consistency** — pick ONE method (floor-index or linear-interpolation) and apply uniformly; disclose in caption or §5.1 footnote. Affects P95/P99 reporting in Table 4 + §6.2. (I-2, I-3)
9. **Table 5 line 563 + Table 6 line 588 (-2.1 → -2.2)** — round-to-nearest, not truncate. (I-4)
10. **§5.1 line 451 + Table 2 footnote line 474** — "5 cases" should be either "5 RCA cases" or "6 cases overall" to match the actual delta. (I-5)
11. **Verify D-6 BERT-F1 column decision** — Table 5/6/7 currently omit BERT-F1 (only Table 2 + §5.2 prose carry it). Confirm this matches the chosen D-6 sub-decision (Option B full integration vs Option C 1-sentence fallback). (I-6)
12. **§5.1 line 447 "1.95 ms" RTT** — reconcile with Table 4 footnote "1.10 ms" and `summary.json.network_rtt_ms=1.10`. (S-2)
