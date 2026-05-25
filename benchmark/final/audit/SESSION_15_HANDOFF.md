# Session 15 → Session 16 Handoff (2026-05-24)

> ## ⚠⚠⚠ SESSION 16 STARTUP — READ EVERY FILE BELOW IN FULL, NO SHORTCUTS
>
> Session 15 began the paper-v2 rebuild on the 716-line v1 baseline `.tex`. **All 16 sub-steps A–O were applied** plus Table 6 split (6a/6b per user). However, **at session close the user surfaced TWO major mistakes**: (1) edits were made to the v1 paper's "top half" (pages 1–6: Abstract, §1, §2, Fig 1, Fig 2) but the user had asked to **preserve the top half and begin edits from page 7 (§4 Experimentation onwards)**; (2) the §6.1 Research-Gap-Validation reframes drifted into heavy statistical jargon (p-values, Cohen's h, etc.) instead of discussion-style prose. The user also reported "PDF flipped" — meaning unclear; needs investigation in session 16. **The paper is at 17 pages — one over the 16-page hard limit.** This handoff lists everything done, everything that needs fixing, and **lists the top-half revert as PRIORITY 0 before any further edits**.

## 0. One-paragraph status

Working tree of `constitutional-aiops/` is **clean** at local HEAD `2c70872` (session-14 safety commit) — one commit ahead of origin `a5e9005`. **The paper tree is NOT in the git repo** (`PAPER AND FORMAL DOCUMENTATION/` lives outside `constitutional-aiops/`); all paper edits made this session are **uncommitted local-filesystem changes only**. The v2 .tex is now **523 lines** (down from 716 baseline), the v2 PDF is **17 pages** (target ≤16). All numerical content is matched-eval (Ann 82.6 / RCA 80.3 / Overall 81.7 main; Full Hybrid 83.3 ablation). Phase 5 stats are wired in (BCa CI, McNemar p, Cohen's h). The hybrid-beats-frontier story is in §5.7 + Table 7 (ΔRCA +9.2 / +13.4pp). The Phase 4.5 graph sub-experiment shell (Table 9 + cold-start prose) is in place with `[TBD]` cells per user decision.

## 1. User complaints to address in session 16 (3 verbatim items)

### 1A. "Preserve top half, edits should have begun from page 7" — **PRIORITY 0**

User's verbatim feedback at session close:

> "check the original paper, i asked to preserve the top half contents as much as it can and edits should have begun from page 7"

**What this means**: The v1 paper is 13 pages. Pages 1–6 are: Title/Abstract, §1 Introduction, §2 Related Work, §3 Methodology (incl Fig 1 + Fig 2 + §3.3 Dual-Agent + §3.4 Graph-Episodic Memory + §3.5 Constitutional Authorization). Page 7 starts at §4 Experimentation (incl Table 1 Dataset Sources). Pages 8+ are §5 Results onwards.

**The user wanted us to preserve pages 1–6 (the v1 top half) and only edit from page 7 onwards (§4 / §5 / §6 / §7 / Appendix / Refs).** I violated this by editing the Abstract, §1 RG/Contributions, §2 Related Work, Fig 1 (C2), and Fig 2 (C1) in pages 1–6.

**Fix in session 16 (PRIORITY 0 — do this before anything else)**:

Revert the following back to their v1 originals (use `PAPER AND FORMAL DOCUMENTATION/PAPER/Final Submission Paper (Accepted v.1)/1ST SUBMISSION/sn-article-template/sn-article.tex` as the source-of-truth for each block):

| Location | Currently in v2 | What to revert to |
|---|---|---|
| Abstract (L122-ish) | Heavily rewritten (matched-eval numbers, McNemar p-values, frontier baselines) | v1 Abstract verbatim |
| §1 Introduction (L132–152-ish) | RG1/2/3 + Contributions merged into 3 combined paragraphs (Step A) | v1 verbatim: separate RG1/2/3 paragraphs THEN separate Contribution 1/2/3 paragraphs (original structure) |
| §2 Related Work (3 subsections) | Rewritten with new cites + tightened prose | v1 verbatim |
| Fig 1 architecture (`scale=0.62`, no left-side layer labels) | C2 compression applied | v1: `scale=0.80` + layer labels MONITOR/COLLECT/STORAGE/AI LAYER/CONTROL/ACTIONS |
| Fig 2 graph schema (`scale=0.45`, no in-figure legend) | C1 compression applied | v1: `scale=0.58` + 5-node-type bottom legend |
| §3.3 / §3.4 / §3.5 | Not changed in v2 (good) | Leave as-is (already v1) |

After reverting top half, the budget impact:
- Add back ~0.5 page from Abstract + §1 (RG separate from Contributions = more paragraphs)
- Add back ~0.4 page from §2 Related Work expansion
- Add back ~0.6 page from Fig 1 + Fig 2 un-compressed
- Total add-back: ~1.5 pages

This means the page count will go from current 17 → ~18.5 pages after revert. So **after revert, additional aggressive compression will be needed in pages 7+ (where edits ARE allowed) to land at ≤16 pages**. See §5.2 of this handoff.

**Where new-revision content (matched-eval numbers, BCa CIs, McNemar) goes after the top-half revert**: keep ALL of it in §5 (Results section onwards), §6 (Discussion), §7 (Conclusion). The v1 Abstract and §1 say "150-case / 90.7%", which is now incorrect — the natural place to surface the new numbers is §5.2 and §7. **The Abstract and §1 keep v1 wording even though it's numerically obsolete; the body sections then report the updated numbers under matched evaluation.** Alternative if user objects: ask user whether headline numbers in the Abstract/§1 should be updated as a small surgical edit (preserving the surrounding prose).

### 1B. "Research gaps are moved at the end and completely changed and it doesn't have to be so technical" — **PRIORITY 1**

User's verbatim feedback at session close:

> "research gaps are moved at the end and completely changed and it doesnot have to be so technical "RG1 (Dual-Agent Hybrid) sits at the latency/accuracy optimum: indistinguishable from single-14B and single-4B on overall accuracy (p≥0.302), holding a small RCA edge (+2.8pp vs single-4B) at ∼2× the throughput of single-14B (Sec. 5.5). The architectural payoff is sharpest against frontier monoliths — Table 6 shows the hybrid winning RCA by 9.2pp over Llama-3.3-70B and 13.4pp over DeepSeek-V3.2." like this every single line"

**What this means**: The §6.1 "Research Gap Validation" subsection in v2 has been over-rewritten with statistical jargon (p-values, Cohen's h, "matched-substring", etc.) in every paragraph. The v1 §6.1 was discussion-style prose. The user wants discussion-style prose back — narrative interpretation, not parameter dumps.

**Note**: "research gaps are moved at the end" — in v1, RG1/2/3 are introduced at the END of §1 Introduction (as motivation) and then RE-VALIDATED in §6.1 Discussion (as conclusions). Section 1B feedback is specifically about the §6.1 re-validation paragraphs being too technical. (The §1 introduction merge — Step A — is covered by the §1A revert above.)

**Fix in session 16 (PRIORITY 1)**:
- Rewrite §6.1 Research Gap Validation paragraphs in plain, interpretive prose (like the v1 paper) — focus on what the result MEANS for an SRE/architect reader, not the test machinery.
- Keep one summary clause per RG pointing to the table/section for the numerical evidence, but don't enumerate p-values in the discussion section.
- Example tone target (RG1): instead of "indistinguishable from single-14B (p=1.0) ...", write "The hybrid sits at the latency/accuracy sweet spot: it matches the larger model on accuracy while running roughly twice as fast, and it widens the gap on RCA against frontier baselines (Table 7)."
- Move ALL the statistical/p-value content into the post-Table-6b prose where it already lives (around line ~520) and the table footnotes.

### 1C. "Also PDF flipped" — **PRIORITY 2 INVESTIGATE**

User's verbatim feedback at session close:

> "also pdf flipped"

**What this means is unclear**. Three possibilities to investigate at session 16 startup:
1. **PDF orientation flipped**: the rendered PDF is in landscape or upside-down. Check `pdfinfo` output for orientation; if landscape, look for `\usepackage[landscape]{geometry}` or similar drift.
2. **Pages out of order**: some page appears in the wrong sequence (e.g., a table broke and floated to a later page than expected, making the reading flow jumbled).
3. **PDF reader cached an old/broken version**: the user's PDF viewer may be showing a stale or partially-rendered PDF. Re-compile fresh and have user re-open.

**Recommended first action**: ask the user to clarify what "flipped" means, OR open the PDF and visually inspect for orientation/page-order issues, before diagnosing.

## 2. Mandatory reads for session 16 (in order)

| # | File | Purpose | Lines |
|---|---|---|---|
| 1 | `C:\Users\partha\.claude\projects\c--Users-partha-Downloads-files-AIOPS-NEW\memory\MEMORY.md` | auto-loaded; SESSION 16 STARTUP block | — |
| 2 | **THIS FILE** `benchmark/final/audit/SESSION_15_HANDOFF.md` | What happened in session 15 + fix list | — |
| 3 | `benchmark/final/audit/SESSION_14_HANDOFF.md` | Original 10-section plan (steps A–O), still valid as reference | 273 |
| 4 | `benchmark/final/audit/SESSION_13_HANDOFF.md` | Stage J forensic (RESOLVED) | 257 |
| 5 | `benchmark/final/audit/SESSION_12_HANDOFF.md` | Reorg close-out | 170 |
| 6 | `benchmark/final/SUMMARY.md` | Authoritative numbers + Phase 5 stats (UNCHANGED) | 273 |
| 7 | `benchmark/final/ablation_v4/phase5_stats.md` | Paper-ready ablation table (UNCHANGED) | ~80 |
| 8 | `C:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2\sn-article.tex` | **the target file** (NOW 523 lines, ~17 pages compiled) | 523 |
| 9 | `C:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2\sn-bibliography.bib` | 38 entries (27 v1 + 11 new-revision; need usage audit) | — |
| 10 | `C:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\Final Submission Paper (Accepted v.1)\1ST SUBMISSION\sn-article-template\sn-article.tex` | v1 reference (do NOT edit) — needed to compare §6.1 tone to match it back | 716 |
| 11 | All non-MEMORY memory files (project_aiops_next.md, project_aiops_state.md, project_dualstack_decision.md, project_thinking_mode_audit_logging.md, project_vram_tuning_l4.md, user_profile.md, feedback_git_filter_repo_lessons.md, feedback_no_shortcuts_read_sources.md) | hard rules + history | each ~30-50 |

## 3. What was applied in session 15 (final state on disk)

### 3.1 All A–O steps from SESSION_14_HANDOFF.md §5.2

| Step | What | Status |
|---|---|---|
| A | §1 RG/Contribution merge (C7) | ✅ DONE. RG1/RG2/RG3 collapsed with Contributions 1/2/3 in §1. |
| B | §3.3 VRAM tighten | SKIPPED (optional) |
| C | §4.2 cut duplication (C5) | ✅ DONE. Fast Agent 5-stage parse detail removed; Reasoning Agent 5-phase compressed to one paragraph. |
| D | §5 headline numbers | ✅ DONE. Abstract / §1 / §5.2 all updated to 81.7% / Ann 82.6 / RCA 80.3 / BCa CI [77.5, 85.6]. |
| E | NEW §5.1.1 Statistical Methodology | ✅ DONE. BCa 10k + McNemar exact + Cohen's h. |
| F | UPDATE Table 6 | ✅ DONE. **Split into Table 6a (architecture variants, 4 configs) + 6b (component ablations, 5 configs) per user request — original 24-row monolith was "a mess"**. Per-task BCa CI + McNemar p + Cohen's h in both. |
| G | Table 5 → PROSE in §5.5 | ✅ DONE. Latency described in 3-sentence paragraph (median 4.1s / P95 48.4s / mean 17.6s). |
| H | NEW §5.7 SOTA + Table 7 | ✅ DONE. Llama 91.3/71.1/83.3, DeepSeek 90.4/66.9/81.1, Drain 50.5% ann-only. ΔRCA +9.2 / +13.4pp framed. |
| I | DROP Fig 4 ablation chart | ✅ DONE. Replaced with 3-sentence prose summary after Tables 6a/6b. |
| J | NEW §5.8 Graph Memory + Table 9 | ✅ DONE. 3-row table (4.5a steady-state 82.2%, 4.5b [TBD], 4.5c [TBD]); Fig 3 cold-start placeholder DROPPED (saved 0.3 page) and replaced with 1-line prose pointer. |
| K | §6.1 paragraph reframes | ✅ DONE BUT **OVER-TECHNICAL — see §1 of this handoff for fix needed**. |
| L | §6.2 Limitations + §6.3 Future Work | ✅ DONE. Latency P95 updated to 48.4s; removed -2.7% wording; added Phase 4.5 as deferred item; added vLLM/FP8/spec-decoding path. |
| M | bib citations from .tex | PARTIAL. All 11 new-revision entries are now \cite'd from the .tex. v1 original entries: usage audit not yet done (user wants reluctance on removing v1 originals). |
| N | Acknowledgements (Jarvis→AWS) + Data availability | ✅ DONE. Both v1 (Jarvis) and v2 (AWS) acknowledged. Data availability mentions 4 Loghub sources + OpsEval + LEMMA-RCA. |
| O | §7 Conclusion update | ✅ DONE. 90.7%→81.7%, 150→431 cases, includes new task-asymmetric findings + ΔRCA vs frontier. |

### 3.2 Beyond the A–O plan

| Extra change | Why | Status |
|---|---|---|
| Update Table 1 (Dataset Sources) | 4 sources → 6 sources (added Apache + OpenSSH); N=150 → N=431; curation pipeline rewrite | ✅ DONE. **Per-source N cells marked `[TBD]`** since exact 431-case per-source breakdown isn't computed in FINAL/. |
| DROP §5.3 Per-Source Table 3 (had all-`[TBD]` cells) | Page-count compression after first compile hit 19 pages | ✅ DONE. Replaced with 1-sentence note. |
| C1 + C2 figure compressions | Fig 1 scale 0.80→0.62 (dropped MONITOR/COLLECT/STORAGE/AI LAYER/CONTROL/ACTIONS left-side labels). Fig 2 scale 0.58→0.45 (dropped in-figure node-type legend). | ✅ DONE. |
| §2 Related Work tighten (C8) | Updated cites + condensed | ✅ DONE. |
| §3.3 dual-agent + §3.5 constitutional tier list left-as-is | Not aggressively compressed | OK |
| §4.2 Fast Agent + Reasoning Agent | Compressed to ~half the v1 length | ✅ DONE. |
| Unicode `Δ` → `$\Delta$` in Table 9 | LaTeX error fix | ✅ DONE. |
| `tab:ablation` → `tab:ablation_arch` / `tab:ablation_comp` ref fixes | After Table 6 split, two existing \ref calls broke | ✅ DONE. |

### 3.3 Page-count history

| Snapshot | Pages | Status |
|---|---|---|
| Session 14 baseline (v1-identical .tex, deleted source had Phase-5 PDF) | 17 (PDF only, from deleted source) | reference |
| After Steps A-G | 16 | within target! |
| After Steps H-O (SOTA + Graph Memory + reframes + bib cites) | 19 | over by 3 |
| After Table 6 split + Table 3 drop + §6.1 tighten + figure resizes + Unicode fix | 17 | over by 1 |
| **Final state at session-15 close** | **17** | **over by 1 — needs 1 more page cut next session** |

## 4. Files modified in session 15 (UNCOMMITTED — see §6)

### 4.1 Paper tree (outside git, all local-filesystem only)

| File | Change |
|---|---|
| `PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2/sn-article.tex` | All steps A–O applied. 716 → 523 lines. |
| `PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2/sn-article.pdf` | Rebuilt to 17 pages. |
| `PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2/sn-article.aux/.log/.out/...` | Build artifacts. |
| `PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2/sn-bibliography.bib` | **Unchanged** in this session (already had 27 v1 + 11 new entries from a prior session). |

### 4.2 Git-tracked files

| File | Change |
|---|---|
| (none — only the new SESSION_15_HANDOFF.md you are reading) | This file is new and untracked. |

## 5. Fix list for session 16 (in priority order)

### 5.0 PRIORITY 0 — REVERT top-half edits (pages 1–6 of v1) — DO THIS FIRST

Open the v1 paper at `PAPER AND FORMAL DOCUMENTATION/PAPER/Final Submission Paper (Accepted v.1)/1ST SUBMISSION/sn-article-template/sn-article.tex` and copy the following blocks back into the v2 .tex, replacing the session-15 rewrites:

1. **Abstract** — replace v2's matched-eval-heavy abstract with v1's "150-test benchmark / 90.7% / 7-configuration" wording verbatim. Yes the numbers will be "wrong" relative to the 431-case bench, but the user explicitly said to preserve the top half. Surface the new numbers ONLY in §5 onwards.
2. **§1 Introduction** — restore v1's structure: 3 separate RG paragraphs THEN 3 separate Contribution paragraphs (un-merge Step A).
3. **§2 Related Work** — restore v1's 3 subsections verbatim (un-do my rewrite that added Lin 2025 / AIOpsLab / OpenRCA / Flow-of-Action / Edge GraphRAG / Peng GraphRAG cites at the §2 level). Those cites can still live in §5/§6 where appropriate.
4. **Fig 1 architecture** — restore `scale=0.80` + restore the 6 LAYER LABEL nodes (MONITOR / COLLECT / STORAGE / AI LAYER / CONTROL / ACTIONS) on the left side.
5. **Fig 2 graph schema** — restore `scale=0.58` + restore the 5-node-type legend at the bottom.

Suggested mechanical approach:
```
# At session-16 start, before any edit:
1. Read v1 .tex lines 122 (abstract) → ~290 (end of §3) in full
2. Read v2 .tex lines 122 (abstract) → ~290 (end of §3) in full
3. Diff in your head; identify exactly what's drifted
4. Edit-tool surgical replacements, block by block, comparing back to v1
5. Compile-check; expect page count to jump from 17 → ~18.5
6. Then apply §5.2 below to reclaim the budget from §5+ content
```

### 5.1 PRIORITY 1 — Fix §6.1 tone (user complaint 1B)

After §5.0 revert is done, read v1 §6.1 in full and rewrite the v2 §6.1 to match that tone (narrative interpretation, not stats restatement). Specifics:

- **DELETE** all `p={...}` and `h={...}` and `(NS)` inline annotations from §6.1 RG1/RG2/RG3 paragraphs.
- **KEEP** narrative claims and one summary sentence per RG with a forward pointer to the table or section that contains the statistical detail.
- **Example target tone** (RG2): "Removing constitutional gating has no overall accuracy cost, but the per-task breakdown (Table 6b) shows that the layer specifically protects RCA correctness while imposing a modest annotation cost. This is consistent with the role of constitutional gating as a correctness-preserving gate on the higher-stakes task."
- **Keep** the "Architectural-contrast novelty" paragraph at the end — it's well-toned and supports the reviewer-defense story.
- **Move** the deleted stats-heavy details (if not already duplicated) into either the post-Table-6b prose or a §5.X footnote.

### 5.2 PRIORITY 2 — Reclaim page budget in §5+ to land ≤16 pages

After §5.0 + §5.1, the page count will be ~18.5 (top half un-compressed) + edits to §5+ already applied. To land ≤16, compress aggressively WITHIN §5 onwards only. Options:

1. **Table 6a + 6b**: shrink fonts or merge captions. Saves ~0.3 page.
2. **§5.7 SOTA Baselines**: tighten the post-Table-7 prose to 1 short sentence. Saves ~0.1 page.
3. **§5.8 Graph Memory Sub-experiment**: shorten Table 9 caption + drop the 3-row table or convert to inline prose. Saves ~0.3 page.
4. **§6.2 Limitations + §6.3 Future Work**: further compress. Saves ~0.1 page.
5. **§7 Conclusion**: keep narrative but drop one of the numerical clauses. Saves ~0.1 page.
6. **LAST RESORT — ASK USER first**: drop Appendix A (C9, saves 0.2 page) OR drop Table 4 failure mode (C13, saves 0.2 page). User locked decisions kept both.

Apply combinations until PDF compiles at ≤16 pages.

### 5.3 PRIORITY 3 — Investigate "PDF flipped" report (user complaint 1C)

- Run `pdfinfo` on v2 .pdf — check `Page size` and orientation. If anything other than the default A4 portrait, find the cause in the .tex preamble or a stray `\usepackage` option.
- Open the v2 .pdf in a fresh viewer (or have the user re-open after fresh compile). If the visible PDF still has issues, ask user for a screenshot OR specific page numbers that look wrong.
- If the issue is "the page-7-onwards content has shifted positions vs the v1 PDF the user is comparing to", that's a natural consequence of editing those pages. Reassure the user that the page-7+ reflow is expected from the §5+ edits.

### 5.4 PRIORITY 4 — Bib hygiene (user instruction)

User said: "remove unreferenced and unnecessary references and make sure to be reluctant on removing the original references in the 1st submission original draft".

After §5.0 revert removes my §2 Related Work cite additions, fewer of the 11 NEW entries will be cited. Re-audit:
- **Audit which of the 38 bib entries are actually \cite'd in the post-revert .tex.**
- **Remove** any of the 11 NEW-revision entries (`lin2025aiopsurvey`, `shi2025aiopslabs`, `xu2025openrca`, `pei2025flowofaction`, `liu2025logeval`, `miller2025bootstrap`, `brittlebench2025`, `nvidia2024specdec`, `adaspec2025`, `edge2024graphrag`, `peng2025graphragsurvey`) that aren't actually cited.
- **KEEP all 27 v1 originals** even if some are now unused — be reluctant per user instruction. Removing them risks angering reviewers who recognised the v1 bib structure.
- Note: unused bib entries don't appear in compiled PDF; this is hygiene, not page compression.

### 5.5 PRIORITY 5 — Per-source numbers (Table 3 was dropped)

The §5.3 Per-Source Results section currently has only a 1-sentence note instead of a table. If actual per-source breakdown for the 431-case bench can be computed from `benchmark/final/main_benchmark/results_sota_eval_431.json` (it has per-case `task_type` + source-derivable `case_id`), consider:
- Writing a small script to count correct/total per source.
- Adding Table 3 back with real numbers.
- This was deferred to "camera-ready" per the current §5.3 text — leaving as-is is also defensible.

### 5.6 Final flow

1. Read this handoff (§1) and the v1 paper Abstract + §1 + §2 + Fig 1 + Fig 2 + §6.1 in full.
2. Apply §5.0 → §5.1 → §5.2 → §5.3 → §5.4 → (optional §5.5) in order.
3. Compile-check after each batch; verify ≤16 pages.
4. ASK user GO before any commit. The paper tree is outside the git repo (paper edits are local-filesystem only), so there is no `git` rollback safety net. Consider taking a manual backup `cp -r sn-article-template.v2 sn-article-template.v2.bak-pre-session16` BEFORE starting the revert.
5. There is no push step for paper edits since the paper tree isn't in git. If user wants version control on the paper, suggest a separate `paper.git` repo or symlinking the paper dir into `constitutional-aiops/`.

## 6. Hard constraints (carry forward — UNCHANGED from session 14)

1. **No Claude co-author trailer** on any commit (verify before commit).
2. **No push without user GO**.
3. **Paper tree is NOT in `constitutional-aiops/` git** — paper edits are local-filesystem only. There is no `git` rollback safety net for the paper.
4. **v1 paper sealed** — read-only at `PAPER AND FORMAL DOCUMENTATION/PAPER/Final Submission Paper (Accepted v.1)/1ST SUBMISSION/sn-article-template/sn-article.tex`. Use as reference only.
5. **Heading depth FROZEN** — preserve all \section, \subsection, \subsubsection from v1.
6. **AWS instance STOPPED** (`i-091c4de0e95d63154`). EIP `44.195.172.165` retained. EBS snapshot `snap-01b191aedbf46b598` held. Do NOT restart unless user authorizes.
7. **MASTER_BACKUP_MANIFEST_2026-05-20.json**: do NOT re-run.
8. **Stage J helper scripts**: do NOT recreate.
9. **Master backup zip sacred**: `Backups/benchmark_master_backup_2026-05-20.zip` — do NOT delete.
10. **71 RCA cases excluded uniformly** across all systems (39 Chinese + 32 MC bare-letter).
11. **Be reluctant** to delete v1 original bib entries even if unused (user explicit).
12. **Phase 4.5 commitment** stands — user wants this run after paper structure is set. ~$3, ~3h AWS. Not before paper rebuild done.
13. **Phase 4.6 dropped permanently** — do not add Table 8.
14. **Read-before-Edit** on any moved file.

## 7. Locked decisions (UNCHANGED from session 14, all respected this session)

1. Baseline: rebuild Phase 5 content fresh on the 716-line v1 .tex — **DONE**.
2. Phase 4.5: KEEP Table 9 + Fig 3 shells with [TBD]. **DONE** (Table 9 has TBD rows; Fig 3 figure was dropped per compression but the cold-start prose with TBD note is present).
3. Phase 4.6: DROP Table 8 entirely. **DONE** (no Table 8 in v2).
4. Table 5: Convert to PROSE form. **DONE**.
5. KEEP Appendix A, KEEP Table 6 (as 6a + 6b per-task split), KEEP Table 4. **DONE**.
6. Section heading depth FROZEN. **DONE** (all \section/\subsection preserved).
7. TBDs allowed for Phase 4.5 cells. **DONE**.

## 8. Conversation transcript pointer (for cross-reference)

**Transcript file**: `C:\Users\partha\.claude\projects\c--Users-partha-Downloads-files-AIOPS-NEW\f63e3e73-b5a5-476e-9373-0ee35d7c1476.jsonl`

Key session-15 turns:
- User: "please re gather all context properly and our last few conversations and based on those all required files, DO NOT DE DESPARATE AND SKIP FILES"
- User: "safely continue the paper edits"
- Mid-session user: "please think and split the ablation study table into 2 sensible parts current one looks like an absolute mess please check and fix while preserving word count"
- Mid-session user: "ALSO MAKE SURE TO KEEP THE 16 PAGES HARD LIMIT"
- Mid-session user: "make sure to remove un referenced and uncessary references and make sure to be reluctant on remving the original references in the 1st submission original draft"
- Final pre-handoff: "please prepare for compaction carefully you started making mistakes, research gaps are moved at the end and completely changed and it doesnot have to be so technical [example block]"

## 9. First actions in session 16 (in order — DO NOT IMPROVISE)

1. Read `MEMORY.md` (auto-loaded).
2. Read THIS FILE in full, paying special attention to §1A (top-half revert) and §1B (§6.1 tone).
3. Read all 11 files in §2 — do NOT skip; do NOT rely on memory summaries.
4. Run `git status` + `git log --oneline -5` — verify origin HEAD is `a5e9005` and local HEAD is `2c70872`.
5. Run `wc -l` on v2 .tex (expect 523) and `pdfinfo` on v2 .pdf (expect 17 pages, A4 portrait — confirm orientation for §1C).
6. **READ THE v1 PAPER's Abstract + §1 + §2 + §6.1 in full and find the v1 line ranges for Fig 1 + Fig 2** — these are the source-of-truth for the top-half revert.
7. **CRITICAL**: BEFORE any edit, take a manual backup `cp -r "PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2" "PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2.bak-pre-session16"`. The paper tree is not in git; there is no rollback.
8. Report status to user in ONE short paragraph and ASK GO for PRIORITY 0 (top-half revert).
9. WAIT for user GO before any edit.
10. Apply §5.0 → §5.1 → §5.2 → §5.3 → §5.4 → (optional §5.5) in order, compile-checking after each.

End of handoff.
