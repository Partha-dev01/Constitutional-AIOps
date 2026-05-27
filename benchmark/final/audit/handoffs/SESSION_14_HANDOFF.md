# Session 14 → Session 15 Handoff (2026-05-24)

> ## ⚠ SESSION 15 STARTUP — READ EVERY FILE BELOW IN FULL, NO SHORTCUTS, NO MEMORY-SUMMARY RELIANCE
>
> This handoff is structured so a fresh agent can resume **exactly where session 14 left off** without re-deriving context. The user has been explicit: **do not skip any reads, do not rely on memory summaries, re-read primary artifacts.** See `feedback_no_shortcuts_read_sources.md` for the standing rule.

## 0. Where session 14 stopped — one paragraph

Stage J (scripts/ sub-folder reorg) was completed and pushed as `a5e9005` to origin/main. The user then pivoted to paper revision: target is **HARD 16-page cap** for `sn-article-template.v2/sn-article.tex` (the v1 paper is sealed, edit v2 only). A Plan-subagent analyzed and reported the 16-page fit is achievable with margin. The user locked in all decisions for the rebuild. **The .tex on disk (716 lines) is stale v1; the PDF on disk (17 pages) was built from a NEWER source that was subsequently DELETED.** Decision: rebuild Phase 5 content fresh on the 716-line .tex. Session 14 stopped immediately after reading the .tex contents fully and before any edits. **No paper edits applied yet.**

## 1. Mandatory reads (read EVERY file, in order, no skipping)

| # | File | Purpose | Lines / Size |
|---|---|---|---|
| 1 | `C:\Users\partha\.claude\projects\c--Users-partha-Downloads-files-AIOPS-NEW\memory\MEMORY.md` | auto-loaded; SESSION 15 STARTUP block + paper revision pointers | ~150 lines |
| 2 | **THIS FILE**: `benchmark/final/audit/SESSION_14_HANDOFF.md` | what happened in session 14 + resume protocol | — |
| 3 | `C:\Users\partha\.claude\projects\c--Users-partha-Downloads-files-AIOPS-NEW\memory\project_aiops_next.md` | historical resume protocol (path retrofit map at top after session 14 update) | ~410 lines |
| 4 | `benchmark/final/audit/SESSION_13_HANDOFF.md` | Stage J forensic record (has RESOLVED header now) | 257 lines |
| 5 | `benchmark/final/audit/SESSION_12_HANDOFF.md` | session 12 close-out | 170 lines |
| 6 | `benchmark/scripts/README.md` | 34-script index by sub-folder + cross-deps + output-paths (post-Stage-J) | ~130 lines |
| 7 | `benchmark/final/SUMMARY.md` | canonical results landscape + Phase 5 stats §3 (Table 6 source) + §4 (headline findings for §6.1 reframes) | 273 lines |
| 8 | `benchmark/final/ablation_v4/phase5_stats.md` | paper-ready ablation table (BCa CI + McNemar p + Cohen's h) — has BOTH per-task variant AND compact overall-only variant | ~80 lines |
| 9 | `benchmark/final/MANIFEST.md` + `AUDIT_REPORT.md` | per-file SHA + audit (sanity check FINAL/ integrity) | — |
| 10 | `C:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2\sn-article.tex` | **the target file** (716 lines, identical to v1) | 716 lines |
| 11 | `C:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2\sn-bibliography.bib` | bib file — verify ref count (subagent claimed 34 from PDF refs, but v2 .bib may still be 26 since v2 is byte-identical copy of v1) | check |
| 12 | `C:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2\sn-article.pdf` | reference PDF (17 pages with Phase 5 content from DELETED newer source) — use as VISUAL REFERENCE ONLY for what §5.7/5.9/Table 7/9/Fig 3 should look like | 17 pages |
| 13 | `C:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\Final Submission Paper (Accepted v.1)\1ST SUBMISSION\sn-article-template\sn-article.tex` | v1 reference — **DO NOT EDIT**, read-only for reasoning | 716 lines (identical to v2) |
| 14 | `benchmark/final/audit/FULL_TRANSCRIPT_AUDIT.md` (1507 lines) | sealed forensic audit | sealed |
| 15 | `benchmark/final/audit/CV_PASS1_DISCREPANCIES.md` + `CV_PASS2_CODEBASE_AUDIT.md` | sealed forensic | sealed |
| 16 | `benchmark/final/audit/REORG_PROPOSAL_2026-05-20.md` | original reorg plan | sealed |
| 17 | `benchmark/final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json` | pre-zip 493-file SHA manifest (do NOT regenerate — provenance link to 2026-05-20 zip) | sealed |
| 18 | All non-MEMORY memory files: `project_aiops_state.md`, `project_dualstack_decision.md`, `project_thinking_mode_audit_logging.md`, `project_vram_tuning_l4.md`, `user_profile.md`, `feedback_git_filter_repo_lessons.md`, `feedback_no_shortcuts_read_sources.md` | hard rules + historical state + lessons | each ~30-50 lines |

## 2. Session 14 timeline (factual record)

1. Session began with SESSION_13_HANDOFF.md broken-state warning; user asked to regather context properly twice ("DO NOT BE DESPARATE")
2. User chose **Resume Stage J via bulk-edit**
3. Stage J fixes applied in batches:
   - 27 path-depth fixes (Groups A-E) — initial bulk fixer over-applied due to substring-collision bug (`parent.parent` substring of `parent.parent.parent`); wrote a rollback script; final state correct
   - 4 cross-script imports (rescore→run/run_sota via importlib, e2e_tests→run/run_benchmark ×3 + eval/export_metrics, run_ablation→eval/export_metrics)
   - 61 docstring updates across 26 scripts via dry-run-first then --apply
   - HANDOFF.md 6 invocations
   - benchmark/final/docs/{BUG_HISTORY,METHODOLOGY,CURRENT_RUNS}.md (7 mentions)
   - 58 external-doc invocations across 12 Tier-1 files
   - scripts/README.md full rewrite for sub-folder layout
4. Verification gate (5/5 passed):
   - verify_authoritative_numbers: Ann 82.6/RCA 80.3/Overall 81.7 main, Full Hybrid 83.3 ablation — IDENTICAL TO PRE-STAGE-J
   - inspect_all_configs Δ table: full +9.86, single_4b +18.31, no_constitutional −30.99 — IDENTICAL
   - run_ablation + e2e_tests imports OK
   - master_backup_manifest write-path OK (script's idempotent re-write was REVERTED to preserve 2026-05-20 provenance to the zip)
5. SESSION_13_HANDOFF.md got RESOLVED header at top; MEMORY.md updated to SESSION 15 STARTUP block (now superseded by SESSION 16 block in this session — see §4 below); project_aiops_next.md got SUPERSEDED banner
6. 4 throwaway helper scripts deleted from `scripts/`
7. **COMMITTED** as `a5e9005`, NO Claude trailer, working tree clean
8. **PUSHED** to origin/main with user GO
9. User asked Phase 4.5/4.6 cost+time estimates → I gave: 4.5 = $3+3h, 4.6 = $10+12h
10. User asked which were worth running → I gave pros/cons (4.5 = strong empirical evidence add, 4.6 = marginal since per-task split already defuses prompt concern)
11. User pivoted to paper revision (16-page hard cap)
12. Spawned Plan subagent for compression analysis
13. Subagent found PDF/.tex mismatch and produced compression plan (see §3 below)
14. User locked decisions (see §4 below) and noted **"newer tex was deleted unfortunately, rebuild fresh properly"**
15. I started reading v2 .tex (716 lines, full read)
16. User interrupted to ask for compaction prep → **this handoff doc**

## 3. Plan-subagent's compression analysis (CRITICAL — preserve verbatim conclusions)

### 3.1 Current state (factual baseline)
- **Current PDF**: **17 pages** (A4) — built from a NEWER source than the .tex on disk (that source has been DELETED). Contains Phase 5 content with TBD placeholders (Tables 7/8/9, §5.1.1, §5.7-5.9, Fig 3, 34 refs).
- **Current .tex**: 716 lines, identical to v1 (byte-equal). DOES NOT contain Phase 5 content. ~13 pages if compiled standalone.
- **bib**: subagent counted 34 refs in PDF but v2 .bib may still be 26 from v1 — must verify at startup of session 15.

### 3.2 Section/Page Map (from compiled PDF — for visual reference)
| § | Title | PDF page(s) | Approx footprint |
|---|---|---|---|
| Title/Abstract | — | 1 | 1.0 |
| §1 Introduction | | 2-3 (top) | ~1.5 |
| §2 Related Work | | 3 (bot)-4 (top) | ~0.7 |
| §3 Methodology + Fig 1 + Fig 2 | | 4-6 | ~3.0 |
| §4 Experimentation + Table 1 | | 7 | ~1.0 |
| §5 Results (5.1, 5.1.1, 5.2) + Tables 2-3 | | 8-9 top | ~1.4 |
| §5.4 Error + Table 4 | | 9-10 top | ~0.4 |
| §5.5 Latency + Table 5 | | 10 | ~0.5 |
| §5.6 Ablation + Table 6 | | 10-11 top | ~0.7 |
| §5.7 SOTA + Table 7 | | 11 | ~0.6 |
| §5.8 Prompt Robustness + Table 8 | | 11-12 top | ~0.7 |
| §5.9 Graph Memory + Fig 3 + Table 9 | | 12 | ~0.8 |
| §6 Discussion | | 12 bot-13 | ~1.2 |
| §7 Conclusion + Declarations | | 13 bot | ~0.4 |
| Refs (34) | | 14-17 | ~3.5 |

### 3.3 Compression opportunities (ranked by saving)
| ID | Compression | Location | Saving | Risk |
|---|---|---|---|---|
| **MUST-DO** | | | | |
| C15 | Don't re-add Fig 4 ablation bar chart (Table 6 conveys same info) | tex L560-657 (currently in v1; subagent says NOT in PDF — verify) | **0.6** | very low |
| C5 | §4.2 prose: cut duplication with §3.3 dual-agent + §1 abstract | tex L431-439 | **0.5** | medium |
| C10 | Truncate bib author lists to 3 + "et al.", drop URLs from preprints | sn-bibliography.bib | **0.4** | low |
| C1 | Fig 2 graph schema: scale 0.58→0.45, drop redundant in-figure legend | tex L295-377 | **0.4** | low |
| C7 | §1: collapse RG1-3 + Contribution-1-3 double-restatement | tex L138-152 | **0.25** | low |
| C2 | Fig 1 architecture: scale 0.80→0.65, drop layer-labels column | tex L173-266 | **0.2** | low |
| MUST-DO subtotal | | | **~2.35** | |
| **PLUS (user-locked)** | | | | |
| Table 5 → prose | Convert Table 5 entirely to sentence form in §5.5 | tex L515-532 | **~0.4** | low |
| Drop Table 8 entirely (Phase 4.6 skip) | Don't add to fresh build | — | **+0.4 saved vs adding** | none |
| **GRAND TOTAL savings (user picks)** | | | **~3.15** | |
| **OPTIONAL** (NOT chosen by user) | | | | |
| C9 | Drop Appendix A "Formal Determinism Analysis" stub | tex L704-710 | 0.2 | low |
| C12 | Table 6 compact-overall variant (8 rows) instead of per-task (22 rows) | — | 0.3 | medium |
| C13 | Table 4 Failure Mode → inline prose in §5.3 | tex L492-511 | 0.2 | low |
| C3 | Caption tightening across all figures/tables | various | 0.15 | very low |
| C4 | §4.1 + §4.1.1 inline content merge (keep both headings) | tex L403-429 | 0.1 | low |
| C6 | §3.3 tighten VRAM details | tex L274-280 | 0.15 | low |
| C8 | §2 Related Work prose tighten | tex L155-167 | 0.2 | low |
| C14 | §6.2 + §6.3 prose tighten (keep headings) | tex L667-673 | 0.2 | low |
| C16 | Inline equations 2 & 3 | tex L289-292, L386-397 | 0.1 | very low |
| C17 | Abstract tighten | tex L122 | 0.05 | very low |

### 3.4 16-page feasibility math (Plan-subagent's verdict)
- Starting from v1 .tex (~13 pages compiled), adding Phase 5 content (no Table 8, no Stack B latency rows since Table 5 → prose):
  - §5.1.1 Statistical Methodology subsection: ~0.3 page
  - Updated Table 6 with CI+p+h columns (per-task = 22 rows): ~0.5 page net (replaces existing ~0.3 → 0.5)
  - §5.7 SOTA Baselines + Table 7: ~0.6 page
  - §5.9 Graph Memory + Table 9 (TBD shell) + Fig 3 (TBD shell): ~0.8 page
  - §6.1 paragraph reframes (graph defused, prompt task-specific, constitutional asymmetric, novelty 2-sentence): ~0.3 page
  - ~12 new bib entries: ~0.4 page
  - **Total new content add**: ~2.9 pages
- Minus must-do + user-picked compressions: **~3.15 pages**
- **Net**: 13 + 2.9 − 3.15 = **~12.75 pages** ✓ comfortably under 16

**Verdict: 16 pages is YES achievable with comfortable margin.**

## 4. User-locked decisions (session 14)

1. **Baseline**: Rebuild Phase 5 content fresh on the 716-line .tex (newer source DELETED, irrecoverable)
2. **Phase 4.5** (graph LEMMA + cold-start): **KEEP** Table 9 + Fig 3 shells with `[TBD]` placeholders. Commit to running it (~$3, ~3h). Table 9 is a 3-row table (4.5a heterogeneous + 4.5b homogeneous 5-fold + 4.5c cold-start). Fig 3 is the cold-start curve at N=0,20,40,60.
3. **Phase 4.6** (paraphrase): **DROP Table 8 entirely**. Skip running (~$10, ~12h). Rely on per-task split (Ann -34.4pp p=1.2e-10 vs RCA -4.2pp p=0.18 NS) already in Phase 5 stats. The 5-paraphrase robustness band is not worth the cost/time when the per-task disaggregation already defuses the prompt concern.
4. **Table 5**: Convert to **prose sentence form** in §5.5 (more aggressive than just dropping Stack B rows). User said: "table 5 can be sentence form, keep the rest intact".
5. **Optional cuts**: **KEEP** Appendix A, **KEEP** Table 6 per-task variant (preserves constitutional-asymmetric story), **KEEP** Table 4 intact.
6. **Section heading depth**: **FROZEN** — paper accepted at v1 with current structure. Do NOT delete any \section, \subsection, or \subsubsection. Content merges OK (keep both headings).
7. **TBDs allowed**: Phase 4.5 numbers can be `[TBD]` placeholders until run.

## 5. The work — exact next-session execution plan

### 5.1 Pre-work verification (≤5 min)
- Confirm v2 .tex is still 716 lines, byte-identical to v1
- Count refs in v2 sn-bibliography.bib — verify if 26 (v1 baseline) or 34 (already has new refs)
- Confirm v2 .pdf still 17 pages (use `pdfinfo` at `/c/Users/partha/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdfinfo`)

### 5.2 Content additions to make on top of v1 .tex (in section order)
Each item below describes WHAT to add and gives the source-of-truth file:

| Step | Where | What | Source-of-truth |
|---|---|---|---|
| A | §1 (L138-152) | Collapse RG1-3 + Contributions 1-3 into single combined block (per C7) | own writing; preserves \textbf{RG1}/\textbf{RG2}/\textbf{RG3} bold labels |
| B | §3.3 (L274-280) | Tighten VRAM details if C6 selected (OPTIONAL) | own |
| C | §4.2 (L431-439) | Cut duplication with §3.3 + §1 abstract — keep only Phase 1-5 RCA enumeration; drop 5-stage JSON parsing detail (per C5) | own; mitigate by moving cut detail to supplementary if needed |
| D | §5 results — update all percentages | Replace 90.7% / 89.0% / 94.0% headline with **matched-eval main numbers**: Ann 82.6% / RCA 80.3% / Overall 81.7% (BCa CI [77.5, 85.6]) | `benchmark/final/SUMMARY.md` §3.3, `phase5_stats.md` |
| E | NEW §5.1.1 Statistical Methodology subsection (~0.3 page) | BCa bootstrap (10k resamples, seed=42, scipy), McNemar exact two-sided binomial paired by case_id, Cohen's h arcsine effect size. Cite Miller et al. arXiv:2503.01747 (CLT/bootstrap) | `benchmark/final/SUMMARY.md` §3 + Phase 5 plan §6.2 |
| F | UPDATE Table 6 (currently tex L538-558) | Replace with matched-eval + new columns (BCa CI + McNemar p + Cohen's h). Use **per-task variant (22 rows)** per user decision. Source: `phase5_stats.md` §3.1 (full per-task table) | `benchmark/final/ablation_v4/phase5_stats.md` §3.1 |
| G | Table 5 (L515-532) → PROSE form | Delete table; write 2-3 sentences in §5.5 covering: avg 17.6s end-to-end (P50 4.1s, P95 48.4s), Ann ~1-2s, RCA avg ~14.8s P95 ~22.7s, A5000 24GB simultaneous load ~15GB total | `benchmark/final/SUMMARY.md` (Latency from Table 5 row) |
| H | NEW §5.7 SOTA Baselines subsection + Table 7 (~0.6 page) | Constitutional AIOps vs Llama 3.3-70B vs DeepSeek V3.2 vs Drain. Numbers: ours Ann 82.6 / RCA 80.3 / Overall 81.7, Llama Ann 91.3 / RCA 71.1 / Overall 83.3, DeepSeek Ann 90.4 / RCA 66.9 / Overall 81.1, Drain Ann 50.5% (202 cases, RCA N/A). **ΔRCA vs Llama = +9.2pp, vs DeepSeek = +13.4pp**. Cite Shi 2025 AIOpsLab + Xu 2025 OpenRCA + Pei 2025 Flow-of-Action | `benchmark/final/SUMMARY.md` §1 Table 7 rows |
| I | DROP Fig 4 ablation chart (L560-657) | Don't re-add — Table 6 carries same info more precisely (per C15) | — |
| J | NEW §5.9 Graph Memory Sub-experiment + Table 9 + Fig 3 (~0.8 page) | 3-row table: 4.5a heterogeneous steady-state (use existing with-graph row: 296/360 = 82.2%), 4.5b homogeneous LEMMA 5-fold = **[TBD]**, 4.5c cold-start at N=0,20,40,60 = **[TBD]**. Fig 3 = cold-start curve (TBD). Caption notes 4.5b/c pending Phase 4.5 run | `benchmark/final/SUMMARY.md` §4.1 graph defense |
| K | §6.1 paragraph reframes (~0.3 page) | (1) **Graph defused**: cite Peng 2025 TOIS + Edge GraphRAG; "Under matched eval, Δ=−1.1pp, p=0.289, h=−0.029 — statistically indistinguishable from noise. Table 9 + Fig 3 isolate the architectural contribution from cross-domain retrieval-space sparsity." (2) **Prompt task-specific**: cite Brittlebench/NAACL-SRW 2025 + Flow-of-Action (WWW 2025); "The 22.5pp drop reflects task-specification loss in the small annotation model (Ann −34.4pp, p=1.2e-10) rather than reasoning-model fragility (RCA −4.2pp, p=0.18 NS)." (3) **Constitutional asymmetric**: "Overall p=0.652 NS but constitutional gating specifically protects RCA correctness (−12.7pp, p=5.3e-04) while imposing a modest annotation cost (+6.4pp without gating, p=0.001)." (4) **Novelty 2-sentence**: explicit architectural contrast with Flow-of-Action (WWW 2025, SOP-based) and AIOpsLab (MLSys 2025, single-agent) — same domain, different architecture, hybrid beats frontier monoliths on RCA per Table 7 | `benchmark/final/SUMMARY.md` §4 |
| L | §6.2 Limitations + §6.3 Future Work | Update graph wording for Phase 5 framing; mention Phase 4.5 sub-experiment shows architectural fairness; remove now-superseded "−2.7% simulated context" language | own |
| M | Bibliography additions (~12 new refs, ~0.4 page) | Add to sn-bibliography.bib: Shi et al. AIOpsLab (MLSys 2025), Xu et al. OpenRCA (ICLR 2025), Pei et al. Flow-of-Action (WWW 2025), Liu et al. LogEval (Springer EMSE 2025), Lin et al. AIOps Survey (ACM CS 2025), Miller et al. CLT/bootstrap (arXiv:2503.01747), Brittlebench/PromptRobust (NAACL-SRW 2025), NVIDIA spec decoding blog, AdaSpec (arXiv:2503.05096), Edge et al. GraphRAG (arXiv:2404.16130), Peng et al. Graph RAG Survey (ACM TOIS 2025), C3AI (WWW 2025 — replaces speculative askell2024 placeholder). **Apply C10 truncation (3 authors + et al., drop URLs from preprints) when adding**. Verify if any are already in v2 .bib | Plan §6.4 in `C:\Users\partha\.claude\plans\misty-knitting-pine.md` |
| N | Acknowledgements / Data availability | Update: Jarvis Labs → AWS L4 24GB g6.xlarge for benchmark; data sources list now 6 (add Apache + OpenSSH per Phase 2 data expansion in plan) | own |
| O | §7 Conclusion | Update 90.7% / 150-test → 81.7% / 431-case headline. Update "1,050 inferences" → matched ablation total. Preserve hybrid-architecture / constitutional / determinism three-contribution structure | `SUMMARY.md` |

### 5.3 Verification gate (after each major batch of edits)
```bash
cd "C:/Users/partha/Downloads/files AIOPS NEW/PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2"
# Compile (MiKTeX pdflatex)
pdflatex -interaction=nonstopmode sn-article.tex
# Read page count
"/c/Users/partha/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdfinfo" sn-article.pdf | grep "^Pages"
# Target: <= 16 (with 0.5-1 page safety margin preferred)
```
Compile twice if refs added (1st pass updates .aux, 2nd pass resolves \cite{}).

### 5.4 Compile-check rhythm
After steps A-G: check page count (should be ~15)
After steps H-K: check again (should be ~15.5-16, may need optional compressions)
After steps L-O: final check (target ≤16)
If over: apply optional compressions C3, C4, C6, C8, C14, C16, C17 in that order.

### 5.5 What to do if 16 doesn't land
1. Apply C9 (drop Appendix A) — frees 0.2 page
2. Apply C12 (Table 6 compact-overall) — frees 0.3 page (loses constitutional-asymmetric story; **ask user before doing this**)
3. Apply C13 (Table 4 → prose) — frees 0.2 page
4. Drop §5.7 SOTA table caption verbose part
5. Last resort: drop §5.9 Phase 4.5 Table 9 + Fig 3 entirely (cancels commitment to run 4.5)

## 6. Hard constraints (carry forward)

1. **No Claude co-author trailer** on any commit (verify before commit)
2. **No push without user GO** — local commits OK, push requires explicit confirmation
3. **Sealed forensic + historical docs untouched**: benchmark/final/audit/*, benchmark/final/docs/_archived_session_history/*, benchmark/archive/*, docs/CHANGELOG.md, docs/JARVIS_LABS_DEPLOYMENT.md, docs/ISSUES.md
4. **Paper v1 sealed** — read-only at `PAPER AND FORMAL DOCUMENTATION/PAPER/Final Submission Paper (Accepted v.1)/1ST SUBMISSION/sn-article-template/sn-article.tex`. Edit v2 only.
5. **MASTER_BACKUP_MANIFEST_2026-05-20.json**: do NOT re-run master_backup_manifest.py since that would overwrite the 493-file manifest documenting the 2026-05-20 zip (provenance link). The 425-file count from current tree is for verification only, not committed.
6. **AWS instance STOPPED** (`i-091c4de0e95d63154`). EIP `44.195.172.165` retained. EBS snapshot `snap-01b191aedbf46b598` held. Do NOT restart unless user authorizes (Phase 4.5 will need a restart).
7. **Master backup zip sacred**: `Backups/benchmark_master_backup_2026-05-20.zip` — do NOT delete
8. **Stage J helper scripts deleted**: do NOT recreate stage_j_bulk_fixer.py, stage_j_rollback_overapply.py, stage_j_fix_docstrings.py, stage_j_fix_external_docs.py. They were one-shot throwaways.
9. **Edit-before-Read rule**: For any moved file (Stage J renames), Read FIRST before Edit — git mv invalidates the Edit tool's read-cache.
10. **Heading depth FROZEN**: paper accepted at v1 structure. Do NOT delete \section, \subsection, \subsubsection. Content merges OK.
11. **Phase 4.5 commitment**: user wants this run (~$3, ~3h). After paper rebuild done, AWS restart + run + fill TBDs. NOT before paper structure is laid down with shells.
12. **Phase 4.6 dropped permanently** for this revision. Don't add Table 8.
13. **Excluded RCA cases**: 71 cases (39 Chinese + 32 MC bare-letter) excluded uniformly across all systems for fairness. Listed in `benchmark/intermediate/datasets/excluded_rca_cases.json`. Methodology in `benchmark/final/docs/METHODOLOGY.md` §2.

## 7. Conversation transcript pointers (read directly from JSONL if reconstructing context)

**Transcript file**: `C:\Users\partha\.claude\projects\c--Users-partha-Downloads-files-AIOPS-NEW\f63e3e73-b5a5-476e-9373-0ee35d7c1476.jsonl` (~24,635 lines, ~94 MB at session 14 close)

Use Python to read specific ranges (don't load whole file):
```python
import json
with open("<transcript>", "r", encoding="utf-8", errors="replace") as f:
    for i, line in enumerate(f):
        if 24000 <= i <= 24600:  # adjust to needed range
            rec = json.loads(line)
            # extract message text from rec['message']['content']
```

**Key session-14 turns** (approximate line ranges; rebuild with Python script above if exact):
- L24114+ — User: prior summary block (from earlier compaction)
- L24129+ — User: "regather context properly and check the last few messages, DO NOT BE DESPARATE"
- L24149 — User: "PLEASE PROPERLY REGATHER ALL NECESSARY CONTEXT FIRST THEN ASK THIS QUESTION NOT BEFORE THAT"
- Stage J resume decision answer: "Resume Stage J via bulk-edit"
- Mid-session: "do manual checks later"
- Mid-session: user opens v1 paper, asks "btw do a proper estimate we need to fit the paper at hard limit 16 pages"
- "use subagents for reading and rsuggestions properly , (AGENTS CANNOT EDIT)"
- Decision answers: rebuild fresh / keep Phase 4.5 shells / drop Table 8 / Table 5 → sentence form / keep rest intact
- "The newser tex was deleted by my unfortunatelyy rebuild fresh properly"
- Final pre-compact: "can we compact safely now and continue next session? DO NOT LOOSE ANY CONTEXT AT ALL"
- "also make sure all memory and other files are read properly and not skipped and also the current proper to dos is properly populated and we continue exactly where we left off"

## 8. Files modified in session 14 BUT NOT in the Stage J commit (uncommitted at handoff)

| File | What changed |
|---|---|
| `C:\Users\partha\.claude\projects\...\memory\MEMORY.md` | SESSION 14 → SESSION 15 STARTUP block (this session 14 itself; will be SESSION 16 after compact) |
| `C:\Users\partha\.claude\projects\...\memory\project_aiops_next.md` | SUPERSEDED banner added at top |
| `benchmark/final/audit/SESSION_13_HANDOFF.md` | RESOLVED header at top (part of Stage J commit, already pushed) |
| **`benchmark/final/audit/SESSION_14_HANDOFF.md`** | **NEW (this file)** |

If you want a clean git history, commit this handoff doc as `chore(session-14): safety commit of paper-revision handoff pre-compact` (no Claude trailer).

## 9. Pending tracks (post-compact priority order)

| # | Track | AWS? | Blocks paper publish? |
|---|---|---|---|
| 1 | **Paper v2 rebuild** (steps A-O in §5.2) | No | Yes |
| 2 | Paper v2 compile-check + iterate to ≤16 pages | No | Yes |
| 3 | Paper v2 cumulative commit (no Claude trailer) | No | No |
| 4 | Paper v2 push to origin (with user GO) | No | No |
| 5 | Phase 4.5 LEMMA 5-fold + cold-start → fills Table 9 + Fig 3 TBDs | YES (~$3, ~3h) | No (TBDs acceptable for first submission) |
| 6 | After 4.5 results: edit Table 9 + Fig 3 in v2 .tex, recompile, re-push | No (after 4.5) | No |
| 7 | (Skipped) Phase 4.6 — DROPPED per user decision | — | — |
| 8 | Final submission readiness pass | No | Yes |

## 10. First actions in session 15 (in order — DO NOT improvise)

1. Read `MEMORY.md` (auto-loaded)
2. Read THIS FILE (`benchmark/final/audit/SESSION_14_HANDOFF.md`) in full
3. Read all 18 mandatory files in §1 — do NOT skip, do NOT rely on memory summaries
4. Run `git status` + `git log --oneline -5` — verify Stage J at `a5e9005` is origin HEAD; verify any session-14 safety commit if present
5. Run `wc -l` on v2 .tex (expect 716) and `pdfinfo` on v2 .pdf (expect 17 pages)
6. Run `wc -l` and `grep -c "^@" sn-bibliography.bib` to count v2 bib entries
7. Report status to user: "Session 15 ready. Stage J at `a5e9005` pushed. Paper v2 baseline confirmed: .tex={N} lines, .pdf={M} pages, .bib={K} entries. Decisions from session 14: rebuild fresh, Phase 4.5 shells with TBD, Phase 4.6 dropped, Table 5 → prose. Ready to start edits at step A (§5.2 of handoff). GO?"
8. WAIT for user GO before any edit
9. Once GO, work through §5.2 steps A-O in order, compile-checking per §5.3 rhythm
10. If at any point user pushes back or interrupts, STOP and ask before proceeding

End of handoff.
