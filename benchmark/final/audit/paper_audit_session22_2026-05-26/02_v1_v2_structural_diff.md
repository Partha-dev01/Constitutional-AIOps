# 02 — v1 → v2 Structural Diff Audit

## Scope

Read-only structural diff between v1 (accepted Weak-Accept, 150 cases) and v2 sandbox (post-session-21 revision, 431 cases). Cross-checked: section-by-section claim preservation, silent removals, reframing honesty (prompt-fragility / graph-RAG / latency), table and figure numbering, RG1-RG5 framings, abstract↔body coherence. Source files:
- v1: `c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\Final Submission Paper (Accepted v.1)\1ST SUBMISSION\sn-article-template\sn-article.tex` (716 lines)
- v2: `c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\main\sn-article.tex` (787 lines)

## Method

Section TOC pulled via Grep on `^\\(section|subsection|subsubsection)\{` in both files; section pairs matched by title (not by number, which shifted because §5.5 Statistical Methodology and §5.7 SOTA were inserted in v2). For each matched section, Read'd the prose block and compared sentence-by-sentence. For tables/figures, captioned `^\\caption\{` count and label cross-reference. Key-number Grep over `150-test|90.7|31.3|45.0|94.0|22.7` (v1 anchors) and `431|82.4|84.0|34.4|48.6|48.4` (v2 anchors) to localise drift. No source files modified.

## Findings per section

### Abstract (pre-§1)

- **CRITICAL** — v2 abstract is byte-identical to v1 abstract; still claims "Validated on a 150-test benchmark from four established datasets, the system achieves 90.7\% overall accuracy. A seven-configuration ablation study confirms..." (v1 line 122 ↔ v2 line 123). v2 body now reports 431 cases / 82.4% overall / 8-configuration ablation (v2 lines 455, 469, 540). Abstract MUST be rewritten to: 431-case bench across six sources, 82.4% (BCa CI [78.2, 86.0]) under matched-substring eval, 8-configuration ablation, hybrid beats Llama-3.3-70B / DeepSeek-V3.2 on RCA by 10.8/15.1 pp. Reviewers WILL read abstract first and flag the inconsistency on page 1.

### Introduction (§1)

- **CRITICAL** — v2 §1 paragraph-2 still says "On a curated 150-test benchmark from four established datasets, the system achieves 90.7\% overall accuracy; a seven-configuration ablation study (1,050 inferences) confirms system prompt engineering as the single most critical component (31.3 percentage point drop without it)." v1 line 136 ↔ v2 line 137 — VERBATIM. Numbers and claim style are stale. Should read "431-case benchmark from six sources", "82.4%", "8-configuration ablation (3,448 inferences)", and reframe "31.3pp drop" as "34.4pp drop in 4B annotation only" per the new disaggregation at v2 line 600.
- **CRITICAL** — RG1 paragraph (v1 140 ↔ v2 141) still says "3.3 percentage points improvement over single-model alternatives" — that number derives from v1 ablation (Full Hybrid 92.0% vs Single-14B 88.7%). v2 ablation (Table 5, v2 lines 552-565) shows Single-14B overall 83.8% vs Full Hybrid 84.0% — i.e. $-$0.3pp NS (`p=1.000, h=-0.01`). The "3.3 pp" claim is no longer empirically supported.
- **CRITICAL** — RG2 paragraph (v1 142 ↔ v2 143) still says "imposing only 0.7\% accuracy overhead". v2 No-Constitutional row (line 590-592) shows overall $-$1.1pp (`p=0.652`), and PER TASK: annotation $+$6.4pp (`p=0.001`) but RCA $-$12.9pp (`p=5.3e-4`). The "0.7\%" headline is from v1 Table 6; v2 evidence is different and the framing should match the new ablation finding.
- **MINOR** — RG3 paragraph (v1 144 ↔ v2 145) is preserved and still defensible (the determinism claim isn't number-dependent). OK.
- **MINOR** — Three contributions (v1 146-152 ↔ v2 147-153) preserved verbatim. The 7-configuration claim under Contribution 1 should be updated to 8-configuration.

### Related Work (§2)

- **OK** — v1 §2 (lines 155-167) and v2 §2 (lines 156-168) are byte-identical across all three subsections (LLM-Based AIOps Systems / Graph-Based Approaches and Memory Systems / Safety and Determinism). v2 line 160 still says "ablation results showing 3.3 percentage points improvement" — same stale number as RG1 in Intro. **CRITICAL** carried over: should be updated to the v2 ablation effect (Single-14B vs Full Hybrid: $\Delta=-0.3$pp NS).
- **IMPORTANT** — v2 does NOT add a Related Work paragraph for the three new baselines (Llama-3.3-70B, DeepSeek-V3.2, Drain) or for AIOpsLab / OpenRCA / Flow-of-Action despite citing them in §5.7 and §6.1. R2's "no strong SOTA baselines" critique would be better addressed by 2–3 sentences in §2.1 LLM-Based AIOps Systems that pre-position these systems, rather than first-introducing them in Discussion.

### Methodology (§3)

- **OK** — §3.1 System Architecture diagram + caption (v1 174-266 ↔ v2 175-267): unchanged, per locked decision.
- **OK** — §3.2 Telemetry Collection (v1 270-272 ↔ v2 271-273): unchanged.
- **OK** — §3.3 Dual-Agent AI Processing (v1 274-280 ↔ v2 275-281): unchanged.
- **OK** — §3.4 Graph-Episodic Memory math (v1 282-293 ↔ v2 283-294) and the Fig 2 graph-memory schema diagram: unchanged.
- **MINOR** — §3.5 Constitutional AI Authorization (v1 380-397 ↔ v2 381-397): minor copy-edit (Tier 3 lost a partial-list phrase "continuous improvement", but all four Tier-3 principles P3.1–P3.4 still listed). Substantively equivalent.
- **CRITICAL** — There is NO §3.5 (or equivalent) "Evaluation Methodology" in §3. The matched-eval method is described in §5.1 (v2 line 447) only. v1 had the rubric described in §5.1 (line 447) too, so the absence is structurally consistent — but the audit-mandated "INTENTIONAL DISCLOSURE at lines ~447 + ~597" specified in the audit brief for §3.5 actually live in §5.1 + Table 6b footnote. Those disclosures exist (v2 line 447 "This replaces the v1 paper's 3.0-point rubric (retained for forensic parity in supplementary material), which we found to over-credit partial-overlap answers"; v2 line 597 "The matched-substring evaluator replaces the v1 rubric, which cross-config audit shows over-credited partial-overlap answers by $-$31 to $+$18pp per configuration."). Both intentional — confirm to readers that the eval changed v1→v2.

### Dataset Curation (§4 Experimentation)

- **OK** — §4 intro (v1 401 ↔ v2 402): trivial copy-edit. Substantively equivalent.
- **OK** — §4.1 Dataset Sources expanded honestly: v2 line 406 explicitly says "expanded from the v1 150-case curation to address reviewer concerns about sample size and source diversity". Table 1 (v2 lines 408-428) now lists 6 sources vs v1's 4; total 431 (218 Ann + 213 RCA). Reviewer R1/R2 expansion concern addressed.
- **OK** — §4.1.1 Curation Pipeline (v1 426-429 ↔ v2 430-433): v1's "three-phase" became v2's "four-phase pipeline" (source expansion, quality filtering, two-LLM label vetting, stratified seeding). Tier-0 / Tier-1 vetting with Llama-3.3-70B + DeepSeek-V3.2 as judges is a new, defensible methodology addition. The 74-case exclusion (41 Ch + 33 OpsEval-remined `qa_mcq`) is disclosed.
- **MINOR** — v2 line 425 "Total (curated) … **431** (218 Ann + 213 RCA)" plus elsewhere "139 evaluable RCA cases of 213" (v2 line 447). Reader has to do mental arithmetic 213−74=139; an explicit footnote on Table 1 would help.
- **OK** — §4.2 Data Processing Pipeline (v1 431-440 ↔ v2 435-441): condensed but content-preserving. All five RCA pipeline phases still enumerated. The composite confidence formula and authorization thresholds are unchanged.

### Results (§5)

- **CRITICAL** — §5.1 Evaluation Methodology (v1 445-447 ↔ v2 445-447): **honest re-framing**. v1's "Each test is scored on a 3.0-point rubric with pass threshold $\geq$1.5" is REPLACED by v2's "Each outcome is binarised by a strict matched-substring evaluator". v2 explicitly discloses the change: "This replaces the v1 paper's 3.0-point rubric (retained for forensic parity in supplementary material), which we found to over-credit partial-overlap answers". This is correct intentional-disclosure handling.
- **OK (NEW)** — §5.1.1 Statistical Methodology (v2 lines 449-451) is genuinely new and addresses R2/R3 statistical-rigor concerns: BCa bootstrap CIs, McNemar exact test, Cohen's $h$. Defensible.
- **IMPORTANT** — §5.2 Overall Benchmark Results (v1 449-467 ↔ v2 453-475): numbers updated (90.7 → 82.4%; 89% Ann → 82.6%; 94% RCA → 82.0%). v2 line 455 explains the headline drop honestly as "Lower headline numbers vs v1 reflect the stricter matched-substring evaluator, not a system regression" with BERT-F1 0.81 as supporting semantic-adequacy evidence. Honest reframing.
- **OK** — §5.3 Per-Source Results (v1 469-490 ↔ v2 478-509): v1's standalone Per-Source Accuracy Breakdown table (v1 471-488) was merged into v2's combined Per-source / failure-mode Table 3 (v2 488-509). Numerical breakdown content is preserved (HDFS, BGL, OpenSSH, OpsEval, LEMMA all listed).
- **IMPORTANT** — v2 line 481 says "Numerical breakdowns are deferred to the camera-ready supplementary tables." but the very next paragraph displays Table 3 which IS the per-source numerical breakdown (HDFS 94%, BGL 68.4%, OpenSSH 50%, OpsEval 66.1%, LEMMA 93.8%). The "deferred" prose contradicts the inline table — likely a leftover from an earlier draft state where the table was absent.
- **OK** — §5.3 / §5.4 Error Analysis (v1 492-511 ↔ v2 483-509): v1 had a 3-row Failure Mode Analysis table (BGL FP / HDFS / OpsEval Wired). v2 consolidates this with the per-source table. v2 line 486 adds new disclosure: "On OpenSSH (50\%), all 20 errors are false positives with zero false negatives on brute-force --- a conservative bias desirable for production triage." This addresses the new OpenSSH source's surprising number with honest framing.
- **IMPORTANT** — §5.5 Performance and Resource Utilization (v1 513-532 ↔ v2 511-535): latency numbers updated honestly (v1 P95 22.7s on A5000 ↔ v2 P95 48.6s on AWS L4). v2 line 514 reframes R3's latency concern as a serving-stack artifact: "Preliminary vLLM+FP8 gate tests show $\sim$1.5$\times$ speedup; with speculative decoding, a sub-5\,s P95 path is credible". This is the audit-requested honest reframing.
- **IMPORTANT** — v2 Table 4 (latency, v2 518-535) uses v1's component×metrics layout (per Decision 1) instead of the metric×task layout that earlier drafts had. Confirmed in v2: rows are 4B Fast / 14B Reasoning / End-to-End; columns are VRAM / P50 / P95 / Avg / Range. NO `---` cells. Footnote discloses $n=431$ + 33 `qa_mcq` routed through 14B. Layout is v1-compatible.
- **CRITICAL** — Table 4 caption (v2 line 518) says "431 inferences, RTT-compensated" but the footnote (v2 line 534) says "$n{=}431$ (218 annotation + 180 RCA + 33 \texttt{qa\_mcq}…)". 218+180+33=431. However, the End-to-End row averages 17.62s and the Avg of 14B is 32.19s while Avg of 4B is 3.07s — these are component-level distributions, not request-level. A request goes through 4B annotation then optionally 14B RCA. The 218 annotation cases get 4B only (~3s), the 213 RCA cases get 4B+14B (~3+32=35s). The "End-to-End" P50 4.15s suggests it's dominated by annotation-only paths. Footnote should clarify that End-to-End is over the 431-request mix, not over a uniformly composed dual-call latency. Reviewer R3 may flag.
- **OK** — §5.6 Ablation Study (v1 534-558 / Table 6 + Fig 3 ↔ v2 537-697): expanded from a single Table 6 in v1 to TWO tables (5 arch/orchestration + 6 component ablations) in v2 plus Figure 3. v2 also adds the orchestrator row (v2 line 562) which v1 promised in future work (v1 line 673) — promise fulfilled.
- **CRITICAL (HONEST REFRAMING)** — Prompt-fragility reframe at v2 line 600: "the 31.3pp ``prompt-fragility'' headline conflates a small-model task-specification cost (4B annotation collapses $-$34.4pp without scaffolding) with a robust reasoning-stage behavior (14B RCA holds within 4.3pp)." Exactly the audit-mandated honest disaggregation. Fig 3 (v2 lines 602-697) visualises both bars per config. v1's "$-$44pp drop!" callout (v1 line 645) becomes v2's "$-$34pp drop!" (v2 line 685) — consistent with the post-D-1 number 48.6% from 83.0% baseline.
- **CRITICAL (HONEST REFRAMING)** — Graph-RAG reframe at v2 line 540: "(iii) graph-RAG is statistically indistinguishable from Full Hybrid ($p{=}0.289$, $|h|{=}0.03$), defusing v1's $-$2.7\% concern." v1's $-$2.7% concern (v1 line 551, line 659, line 665, line 669, line 673) is replaced by the populated-graph result $\Delta=-1.1$pp NS. Reviewer R1/R3 graph concern addressed honestly.
- **OK (NEW)** — §5.7 Comparison Against SOTA Baselines (v2 lines 701-725): the entire NEW section addressing R2's SOTA-baselines critique. Three baselines (Llama-3.3-70B, DeepSeek-V3.2, Drain), separate Ann/RCA/Overall columns (NOT just overall — audit spec satisfied), and $\Delta$RCA column showing $-$10.8 / $-$15.1 pp deltas. Drain annotation-only with 16 no-template exclusions disclosed. Caveat about "Frontier monoliths win annotation … but lose RCA" is the substantive comparative claim.
- **OK (DROPPED ON PURPOSE per Decision 4)** — §5.8 Graph-Episodic Memory Sub-experiment is NOT present in v2. Verified by exhaustive section grep — last §5.x is §5.7 SOTA, then §6 Discussion at line 727. Decision 4 correctly applied. Cross-checked: no `tab:graphsub` label, no `fig:graphsub` label, no remaining `\subsection{Graph-Episodic` heading.

### Discussion (§6)

- **OK (HONEST RG VALIDATION REWRITE)** — §6.1 Research Gap Validation (v1 663-665 ↔ v2 729-734): completely rewritten. v1's "Hybrid 92.0% outperforms single-model alternatives" + "0.7% accuracy overhead" + "$-$2.7% simulated episodes" are all replaced by v2's three honest reframings: (i) "hybrid holds a small RCA edge over single-model alternatives" + frontier-monolith win, (ii) "no overall accuracy cost but specifically protects RCA correctness", (iii) "the v1 ``$-$2.7\% graph concern'' is statistically indistinguishable from zero under matched evaluation, and the v1 ``prompt fragility'' headline decomposes into a small-model task-specification cost".
- **OK (NEW ARCHITECTURAL-CONTRAST PARAGRAPH)** — v2 line 734 contains the 2-sentence architectural-contrast paragraph contrasting Constitutional AIOps with Flow-of-Action (`pei2025flowofaction`), AIOpsLab (`shi2025aiopslabs`), and OpenRCA (`xu2025openrca`). Audit spec satisfied (the brief asks for Flow-of-Action + AIOpsLab; OpenRCA is bonus). All three citations are new in v2 vs v1.
- **OK (LIMITATIONS — HONEST ABSORPTION OF DROPPED §5.8)** — §6.2 Limitations (v1 667-669 ↔ v2 736-739): v1's "Graph memory faces a cold-start problem" sentence (v1 669) is absorbed and EXPANDED into v2's clause: "Graph-RAG's architectural value … is computed under heterogeneous retrieval; a planned homogeneous-LEMMA 5-fold sub-experiment saturated at the model's accuracy ceiling at this difficulty (no-graph = with-graph = 100\%, n=80, populated graph N=431), leaving cross-domain retrieval-space sparsity as the more informative regime for future memory-architecture work." This is the dropped-§5.8 content honestly absorbed (cites `peng2025graphragsurvey`). Also the 22.7s P95 limitation updated to 48.4s on Q4_K_M/Ollama.
- **IMPORTANT** — v1 line 669 cited `zhang2020effect` in Limitations. Per MEMORY.md session-21 changes, this citation was dropped from v2 ("3 v2-only bib drops to keep 16p"). Confirmed: `zhang2020effect` is NOT in v2 main `.tex`. The replacement v2 citation list `guo2017calibration,bansal2021does,parasuraman2000model` is grammatically intact. OK as a deliberate citation drop.
- **OK (FUTURE WORK REWRITE)** — §6.3 Future Work (v1 671-673 ↔ v2 741-744): rewritten as numbered list: (1) cold-start curve + harder homogeneous-domain memory benchmarks; (2) serving-stack latency (vLLM + FP8 + spec decoding cites `nvidia2024specdec`); (3) multi-modal telemetry. Audit-mandated cold-start curve + spec-decoding mentions present. The v1 "validating graph memory with genuine production incident histories (the $-$2.7\% simulated-context drop suggests real episodes would improve accuracy)" sentence is correctly REPLACED with the cold-start framing — the v1 "$-$2.7\%" suggestion is no longer applicable because v2 ablation shows graph-RAG is NS.
- **MINOR** — v1's promise to "benchmarking the LangGraph orchestration pipeline against direct agent calls" (v1 673) is FULFILLED in v2 as the "With orchestrator" row in Table 5 (v2 562). Fulfilled v1-promise; no longer needs to be in Future Work. Correctly absent from v2 §6.3.

### Conclusion (§7)

- **OK (HONEST NUMBER UPDATE)** — v1 678 ↔ v2 749: numbers updated correctly. "150-test … 90.7\%" → "431-case benchmark across six datasets, the system achieves 82.4\% overall accuracy (BCa CI [78.2, 86.0])". 7-config → 8-config. New claim added: "The hybrid beats both Llama-3.3-70B and DeepSeek-V3.2 on RCA by 11--15pp." Honest summary.
- **MINOR** — Conclusion still says "constitutional gating specifically protects RCA correctness at zero overall cost" — consistent with v2 ablation Table 6 (overall $\Delta=-1.1$pp NS), good.

### Appendix A — Formal Determinism Analysis

- **OK** — v1 706-708 ↔ v2 777-779: minor copy-edit only. Theorem 1 and Theorem 2 preserved. Bounded-determinism claim unchanged.

### Acknowledgements + Declarations

- **OK** — v2 line 759 updates Acks honestly to credit BOTH Jarvis Labs (v1 bench) and AWS (v2 revision + Bedrock baselines).
- **OK** — Data availability (v2 766) adds "The 431-case curated split with the uniformly-excluded 74-case RCA list is released alongside the code" — addresses reproducibility.

## OK (preserved or properly updated)

1. Section structure: v1 7 sections (Intro, Related Work, Methodology, Experimentation, Results, Discussion, Conclusion) preserved; v2 adds §5.1.1 Statistical Methodology and §5.7 SOTA. No silent removals.
2. §5.8 Graph-Episodic Memory Sub-experiment correctly REMOVED (Decision 4); content absorbed into §6.2 Limitations + §6.3 Future Work.
3. Tables: v1 had 6 tables; v2 has 7 (NEW Table 7 = SOTA baselines). v1 Per-Source + Failure Mode tables merged into v2 Table 3 (no information loss).
4. Figures: 3 in v1, 3 in v2 (architecture, graph-memory schema, ablation chart). Fig 3 dimensions restored to v1 spec per Decision 3 (height=8.5cm, bar=6pt, xmin=30, xtick={30,50,70,90}).
5. Decision 1 (Table 4 v1 component×metrics layout) verified — no `---` cells.
6. Prompt-fragility reframe (§5.6 line 540 + line 600) is honest disaggregation, not whitewash.
7. Graph-RAG reframe (§5.6 + §6.1 + §6.2) honestly converts v1's $-$2.7% concern to NS under matched eval; cold-start framing moved to §6.3.
8. Latency reframe (§5.5 line 514 + §6.2 line 739 + §6.3) honestly attributes P95 to serving-stack (Q4_K_M/Ollama) and proposes vLLM+FP8+spec decoding path.
9. Intentional-disclosure mentions of v1 3-point rubric at v2 §5.1 line 447 + Table 6b footnote line 597 are present and audit-mandated.
10. SOTA Table 7 has the audit-spec Ann/RCA/Overall split (not overall-only).
11. Architectural-contrast paragraph (§6.1 line 734) cites Flow-of-Action + AIOpsLab + OpenRCA.

## Skipped / Could not verify

- BibTeX/citation closure: did NOT diff `sn-bibliography.bib` between v1 and v2; relied on MEMORY.md statement that 3 entries (`adaspec2025`, `edge2024graphrag`, `zhang2020effect`) were dropped from cite groups in session 21. Spot-checked `zhang2020effect` absence in v2 main — confirmed.
- Compiled PDF: did NOT open the actual `sn-article.pdf` for v1 or v2 — analysis is `.tex`-only. Page-count, float placement, and visual-overlap verification (Fig 3 callout, 84% baseline label) deferred to auditor #4 or visual QC.
- DIFF PDF (`...sandbox-session16/diff/sn-article-DIFF.pdf`): not opened. The DIFF source `sn-article-DIFF.tex` exists per directory listing but yellow-highlight override + bibtex pass are incomplete per session-21 handoff. Cannot use DIFF as an oracle.
- Per-source rubric→matched-eval re-scoring: I cannot independently verify the 5-case temperature-0 variance footnote (v2 line 474) without re-running the benchmark.

## Recommendations

1. **(BLOCKER, abstract+intro)** Rewrite v2 abstract (line 123) and v2 §1 paragraph-2 (line 137) to use 431-case / 82.4% / 8-configuration / 3,448-inference numbers, and either drop the "3.3 pp single-model" claim from RG1 (line 141) or replace it with the v2 ablation finding (Single-14B vs Full Hybrid: $\Delta=-0.3$pp NS, plus the frontier-monolith RCA win 10.8/15.1 pp from Table 7). RG2 "0.7\% overhead" claim (line 143) similarly needs updating to "overall-neutral $p=0.652$ but specifically protects RCA $\Delta=-12.9$pp $p=5.3e-4$" or a one-line summary thereof.
2. **(BLOCKER, §2 Related Work)** Update v2 line 160 "3.3 percentage points improvement" to match v2 ablation. Optionally add 2–3 sentences in §2.1 or new §2.4 pre-positioning Llama-3.3-70B, DeepSeek-V3.2, Drain, AIOpsLab, OpenRCA, and Flow-of-Action — currently they are first-introduced in §5.7 and §6.1, which R2 may flag as "no related-work treatment of SOTA baselines."
3. **(IMPORTANT, §5.3)** v2 line 481 "Numerical breakdowns are deferred to the camera-ready supplementary tables" CONTRADICTS Table 3 that follows it (which contains the very breakdown). Delete the deferral sentence or rephrase to "Table~\ref{tab:errortable} disaggregates the per-source distribution …".
4. **(IMPORTANT, §5.5)** v2 Table 4 footnote should clarify that End-to-End latency distribution is over the 431-request mix (annotation-only requests skew P50 low, RCA-bearing requests dominate P95). The current footnote "$n=431$ (218 annotation + 180 RCA + 33 qa_mcq)" is ambiguous about whether the P50 4.15s is dual-call or single-call.
5. **(MINOR, §4.1 Table 1)** Add explicit footnote to Table 1 noting that 213 RCA cases contain 74 uniformly-excluded cases, leaving 139 evaluable — to spare the reader the mental arithmetic.
6. **(MINOR, §1 RG1)** Contribution 1 (v2 line 149) still says "seven-configuration ablation study" — update to eight (matches v2 §5.6 introduction at line 540 "8-configuration ablation").
7. **(VERIFY)** Run a final visual check on the compiled v2 PDF for the Fig 3 callout and 84% baseline label, and confirm that all `\cite{}` references resolve against the trimmed bib (31 entries).
