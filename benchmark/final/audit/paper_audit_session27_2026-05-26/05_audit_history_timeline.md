# Stage 3 — Audit History Timeline (Sessions 12-27)

**Generated**: 2026-05-27 (session 28)
**Agent**: Stage 3 (general-purpose, READ-ONLY)
**Status**: COMPLETE
**Companion**: `05_open_items_checklist.md` (actionable subset)

---

## §0. One-line state

**18 named decision IDs tracked** (D-1..D-17 + Conflicts 1..5 + Group A/B/C audit IDs C-A1..C-D2 + I-1..I-E + M-1..M-7 + Path A..G/B''/Tier1-3) / **~14 historical defers (most resolved)** / **~12 currently-open items for camera-ready edit-phase** (9 confirmed bib metadata errors from Stage 1b + 8 NEW bib errors from Stage 1c + chen2024autonomous placeholder + notaro DOI unresolved + 2 protocol-drift sci-hub PDFs) / **3 confirmed contradictions** (HANDOFF §6 vs §14 Phase 4.4/4.7 status [Conflict-1/2/3, resolved s23]; HANDOFF §7 ablation cells vs paper [CRIT-D1, resolved s23]; D-1 result-file claim "74 excluded" but only 71 actually null [CRIT-C2, resolved s23]).

**OPEN QUESTIONS** flagged: (a) whether the 3 sci-hub-sourced reference PDFs (parasuraman / wu / chen-automap) should be replaced via institutional access before camera-ready; (b) whether 8 Stage-1c-flagged NEW bib metadata errors require dataset-wide cross-checks (some affect cite renderings in the body); (c) whether session 27 Gate 16 + Gate 17 push actually landed (handoff says pending — see §2 sessions 27).

---

## §1. Inputs

Primary handoffs (16 files):
- `benchmark/final/audit/SESSION_12_HANDOFF.md` (170 lines)
- `benchmark/final/audit/SESSION_13_HANDOFF.md` (254 lines)
- `benchmark/final/audit/SESSION_14_HANDOFF.md` (273 lines)
- `benchmark/final/audit/SESSION_15_HANDOFF.md` (282 lines)
- `benchmark/final/audit/SESSION_16_AUDIT_LOST_CHECKLIST.md` (179 lines; note: no SESSION_16_HANDOFF.md exists — session 16 work captured in this checklist + session 17 handoff)
- `benchmark/final/audit/SESSION_17_HANDOFF.md` (284 lines)
- `benchmark/final/audit/SESSION_17_AUDIT_TRIAGE.md` (500 lines)
- `benchmark/final/audit/SESSION_17_RECALC_SCOPE.md` (235 lines)
- `benchmark/final/audit/SESSION_18_HANDOFF.md` (364 lines)
- `benchmark/final/audit/SESSION_19_HANDOFF.md` (449 lines)
- `benchmark/final/audit/SESSION_20_HANDOFF.md` (287 lines)
- `benchmark/final/audit/SESSION_21_HANDOFF.md` (226 lines)
- `benchmark/final/audit/SESSION_22_HANDOFF.md` (332 lines)
- `benchmark/final/audit/SESSION_23_HANDOFF.md` (255 lines)
- `benchmark/final/audit/SESSION_24_HANDOFF.md` (295 lines)
- `benchmark/final/audit/SESSION_25_HANDOFF.md` (341 lines)
- `benchmark/final/audit/SESSION_26_HANDOFF.md` (300 lines)
- `benchmark/final/audit/SESSION_27_HANDOFF.md` (408 lines)

Session-22 audit reports (5-agent parallel audit):
- `paper_audit_session22_2026-05-26/00_SUMMARY.md` (192 lines, master synthesis with 10 CRITICAL + 14 IMPORTANT + 7 MINOR)
- `paper_audit_session22_2026-05-26/01_numbers_audit.md` (206 lines, Tables 1-7 + Fig 3 verification)
- `paper_audit_session22_2026-05-26/02_v1_v2_structural_diff.md` (118 lines)
- `paper_audit_session22_2026-05-26/03_citations_audit.md` (291 lines)
- `paper_audit_session22_2026-05-26/04_benchmark_integrity.md` (427 lines, source-of-truth SHA + count verification)
- `paper_audit_session22_2026-05-26/05_cross_doc_consistency.md` (336 lines)

Session-27 audit artifacts (companion to this Stage 3):
- `paper_audit_session27_2026-05-26/01_references_inventory_report.md` (Stage 1a)
- `paper_audit_session27_2026-05-26/01_xlsx_delta_proposal.csv` (Stage 1a CSV)
- `paper_audit_session27_2026-05-26/02_references_download_manifest.md` (Stage 1b, 405 lines, includes 9-error bib metadata findings)
- `paper_audit_session27_2026-05-26/03_pdf_content_verification.md` (Stage 1c, +8 NEW bib metadata errors)

Forensic / cross-validation (sealed, READ-ONLY):
- `CV_PASS1_DISCREPANCIES.md` (303 lines)
- `CV_PASS2_CODEBASE_AUDIT.md` (715 lines)
- `FULL_TRANSCRIPT_AUDIT.md` (1507 lines)
- `REORG_PROPOSAL_2026-05-20.md` (174 lines)
- `MASTER_BACKUP_MANIFEST_2026-05-20.json`
- `benchmark/final/docs/BUG_HISTORY.md` (188 lines)

---

## §2. Chronological decision log

### Session 12 (2026-05-20) — Cross-validation passes + reorg Stages A-D

**Source**: `SESSION_12_HANDOFF.md` §2

- **CV Pass 1** (suggest-only subagent): audit doc ↔ JSONL. Outputs `CV_PASS1_DISCREPANCIES.md`. 1 CRITICAL (JSONL grew to 17455 lines; audit covers 15282), 1 MEDIUM (L11774 timestamp drift), 3 LOW, 2 UNVERIFIABLE. Status: ACTIVE (sealed forensic record).
- **CV Pass 2** (suggest-only subagent): audit doc ↔ codebase + per-file metadata. Outputs `CV_PASS2_CODEBASE_AUDIT.md` Part B = 491 files indexed. 31 Tier 1-3 items VERIFIED, 0 CRITICAL/HIGH. Status: ACTIVE (sealed).
- **Batch A**: applied 3 audit-doc fixes (D1 JSONL-growth footnote, D10 L11774 disambig, D19 Phase 2 schema-list). Audit doc reaches 1507 lines.
- **Batch B**: 4 path updates to `HANDOFF.md`.
- **Memory paths**: updated for new `PAPER AND FORMAL DOCUMENTATION/PAPER/` paper tree.
- **Master backup** created: `Backups/benchmark_master_backup_2026-05-20.zip` (14.27 MB, SHA `7b01aef0…`, 494 entries). Pre-zip manifest: `MASTER_BACKUP_MANIFEST_2026-05-20.json` (493 files + per-file SHA-256). Crosslink: [[Conflict-5]] (sacred-forever policy locked s17).
- **Reorg Stages A–D DONE** (8 commits, NOT yet pushed):
  - `647e07c` Pre-A — .gitignore / .gitattributes
  - `67f7307` Stage A — `benchmark/datasets/raw/` → `benchmark/raw/`
  - `bb36900` Stage A-finalization — 55 orphan deletions
  - `a62d600` Stage B — `git mv` 12 R100 files: processed → intermediate/datasets, v0.11 → intermediate/candidates
  - `f2f0c09` Stage C — `results_aws/FINAL/` → `final/` + 7 nav docs; dropped 2 byte-identical dedups
  - `185b9b5` Stage D — historical → `archive/`; removed `v2.0_frozen` + gate15 duplicate
  - `0e47671` Stage D-fix — smoke_tests path correction
- **Stages E/F/G/H** REMAINING (pending session 13). Defer reason: high-risk (Phase 5 stats depends on correct paths).

### Session 13 (2026-05-20) — Stages E/F/G/H + Stage I + Stage J partial

**Source**: `SESSION_13_HANDOFF.md`

- **`d64965b`** — Force-pushed after `git filter-repo` stripped Claude trailers from 55 commits + 3 doc mentions. **0 Claude refs in entire history**. Crosslink: [[hard-rule-1]] (no Claude trailer) enforced going forward.
- **`f504d6b`** — Stage E+F+G+H — path hardcodes (24 scripts + 2 src files) + active docs (5) + `strip_cc_trailers.py`. Stage G verified all numbers reproduce.
- **`a20e3cb`** — Stage I: `benchmark/final/` sub-folder reorg into `docs/` + `docs/_archived_session_history/` + `audit/`. 13 R100 moves, 2 critical script refs, 6 doc updates, `scripts/README.md` added.
- **Stage J attempted but FAILED**: 33 `git mv` operations of `benchmark/scripts/` into 5 sub-dirs (prep/run/eval/ops/_dev), but 11 of 12 path-depth Edit calls FAILED because git-mv invalidated Read-tool cache. Working tree left at 33 R + 5 ?? state, runtime-unsafe. Status: DEFERRED to session 14.

### Session 14 (2026-05-24) — Stage J complete + paper revision pivot

**Source**: `SESSION_14_HANDOFF.md` §2

- **Stage J resumed** via bulk-edit (user chose this over abandon-and-restart):
  - 27 path-depth fixes (Groups A-E) with rollback after substring-collision bug
  - 4 cross-script imports fixed
  - 61 docstring updates across 26 scripts
  - 58 external-doc invocations across 12 Tier-1 files
  - Verification 5/5 PASSED: numbers reproduce identically (Ann 82.6/RCA 80.3/Overall 81.7 main, Full Hybrid 83.3 ablation)
  - Committed as `a5e9005`, pushed to origin/main
- **Pivot to paper revision** with HARD 16-page cap on `sn-article-template.v2/sn-article.tex`.
- **Plan-subagent compression analysis** (preserved verbatim in SESSION_14 §3): 17 compression options C1-C17. Verdict: 16p achievable with comfortable margin (~12.75p projected).
- **User-locked decisions (session 14)**:
  - Baseline: rebuild Phase 5 content fresh on the 716-line v1 .tex (newer source DELETED, irrecoverable)
  - Phase 4.5: **KEEP** Table 9 + Fig 3 shells with `[TBD]`. Will run ($3, 3h). Crosslink: [[D-12]] (4.5 trigger), [[D-16]] (later blocker).
  - Phase 4.6: **DROP** Table 8 entirely. Skip running ($10, 12h). Crosslink: [[C-1]] (dropped).
  - Table 5: Convert to **prose sentence form**.
  - KEEP Appendix A, KEEP Table 6 per-task, KEEP Table 4.
  - Section heading depth: **FROZEN** (paper accepted at v1 structure).
  - TBDs allowed for Phase 4.5 cells.

### Session 15 (2026-05-24) — Paper rebuild A-O applied

**Source**: `SESSION_15_HANDOFF.md` §3

All 16 A-O steps from session-14 §5.2 applied:

- Step A: §1 RG/Contribution merge (C7) — DONE
- Step B: §3.3 VRAM tighten — SKIPPED (optional). Crosslink: [[C-3]] (dropped).
- Step C: §4.2 cut duplication — DONE
- Step D: §5 headline numbers — DONE (Ann 82.6 / RCA 80.3 / Overall 81.7 / BCa CI [77.5, 85.6])
- Step E: NEW §5.1.1 Statistical Methodology — DONE
- Step F: UPDATE Table 6 — **SPLIT INTO 6a + 6b per user request** ("absolute mess"); per-task BCa CI + McNemar p + Cohen's h
- Step G: Table 5 → PROSE in §5.5 — DONE
- Step H: NEW §5.7 SOTA + Table 7 — DONE (Llama 91.3/71.1/83.3, DeepSeek 90.4/66.9/81.1, Drain 50.5%)
- Step I: DROP Fig 4 ablation chart (C15) — DONE
- Step J: NEW §5.8 Graph Memory + Table 9 — DONE (3-row, 4.5a 82.2% + 4.5b [TBD] + 4.5c [TBD])
- Step K: §6.1 paragraph reframes — DONE BUT **OVER-TECHNICAL** (user complaint 1B)
- Step L: §6.2/§6.3 Limitations + Future Work — DONE
- Step M: bib citations from .tex — PARTIAL (11 new entries cited; v1 usage audit deferred). Crosslink: [[D-1 bib audit]].
- Step N: Acknowledgements (Jarvis→AWS) — DONE
- Step O: §7 Conclusion update — DONE
- Beyond plan: Table 1 dataset update (4→6 sources, N=150→431), DROP §5.3 Per-Source Table 3 (Page comp), C1+C2 figure compressions

**Page count history this session**: baseline 17 (PDF only) → after A-G = 16 → after H-O = 19 → after split+drops = 17 (over by 1).

**Three user complaints surfaced at session close**:
- **Complaint 1A (PRIORITY 0)**: edited top half (pages 1-6) but user wanted top half preserved, edits to start at page 7
- **Complaint 1B (PRIORITY 1)**: §6.1 RG reframes too technical (p-values everywhere) — wants discussion-prose
- **Complaint 1C (PRIORITY 2)**: "PDF flipped" — unclear meaning

### Session 16 (2026-05-25) — Lost-checklist audit + Phase 4.5 launch + D-13 patch

**Source**: `SESSION_16_AUDIT_LOST_CHECKLIST.md` + `SESSION_17_HANDOFF.md` §3.1 + `BUG_HISTORY.md`

(No standalone SESSION_16_HANDOFF.md; work captured in audit checklist and session 17 close-out.)

- **Lost-Checklist Audit** (Task 1 read-only subagent): produced 32-item inventory of D-1..D-13 silently-lost items. 13 in Category D (SILENTLY LOST) + 8 ACTIVE + 7 DEFERRED + 4 DROPPED. Conflicts 1-5 surfaced.
- **D-1 (OpsEval-remine secret judge)** [[introduced]]: 33 cases judged by local Qwen3-4B-Instruct instead of Bedrock Haiku (Bedrock payment-blocked). Crosslink: [[D-3 Bedrock pivot]].
- **D-2 (OpenSSH 50% never validated)** [[introduced]]
- **D-3 (Bedrock pivot Anthropic→DeepSeek+Llama undocumented)** [[introduced]]
- **D-4 (L5307 fake-graph-context invalidated archived smoke results)** [[introduced]]
- **D-5 (AWS Budgets never created; $47/$120 is CE-derived)** [[introduced]]
- **D-6 (BERT-F1 zeros; bug #8, recomputable post-hoc)** [[introduced]]. Crosslink to `BUG_HISTORY.md` #8.
- **D-7 (test_5plus5.py references deleted benchmark_499_seed42.json)** [[introduced]]. Crosslink to `FULL_TRANSCRIPT_AUDIT.md:399`.
- **D-8 (HANDOFF.md still telling next session to delete 499)** [[introduced]]
- **D-9 (HANDOFF.md §6 vs §14 self-contradictions Phase 4.4 / 4.7)** [[introduced]]. Crosslink: [[Conflict-1]], [[Conflict-2]], [[Conflict-3]].
- **D-10 (CV 5th agent never run)** [[introduced]]
- **D-11 (Flow-of-Action architectural-contrast paragraph)** [[introduced]]
- **D-12 (AWS Phase 4.5 GO/NO-GO trigger never defined)** [[introduced]]
- **D-13 (NEW THIS SESSION)** [[introduced]]: `run_graph_experiments.py exp_4_5c` called nonexistent `Neo4jClient.run_query`. Discovered when this session attempted Phase 4.5. Patched in place. Crosslink to `BUG_HISTORY.md` #9 (sister bug D-17 later).
- **Phase 4.5 attempted** on restarted AWS instance — CRASHED. Documented bug D-13a/b/c/d.
- **Conflict-1 / -2 (HANDOFF.md self-contradictions)** [[introduced]]: §6 says Phase 4.4 + 4.7 COMPLETE, §14 says NOT STARTED. Reality COMPLETE.
- **Conflict-3 (stale benchmark_499 delete instruction)** [[introduced]]: file was already deleted.
- **Conflict-4 (confidence weights α/β/γ never empirically calibrated)** [[introduced]]
- **Conflict-5 (master backup zip — affirm keep-indefinitely)** [[introduced]]

**Two MAJOR mistakes from session 15 surfaced for session 16 fix**:
- PRIORITY 0: revert top-half edits to v1
- PRIORITY 1: rewrite §6.1 in plain discussion-prose

### Session 17 (2026-05-25) — Deep audit triage + 4 Phase 4.5 bugs

**Source**: `SESSION_17_HANDOFF.md` + `SESSION_17_AUDIT_TRIAGE.md` + `SESSION_17_RECALC_SCOPE.md`

**Status at session close**: NO file edits applied beyond 3 new audit docs. Execution deferred to session 18.

**LOCKED DECISIONS** (Tier 1/2/3) — DO NOT re-ask:

**TIER 1 — paper defense**:
- **[[D-1]]** locked Option B (re-label all 33 OpsEval-remined as `task_type: qa_mcq` + recompute Phase 5 locally; no AWS rerun). Estimated numbers shift: RCA 80.3→82.0%, Overall 81.7→82.4%. Crosslink: [[D-1 spot-check finding]] — wrinkle: 3 of 33 (RM_016/022/032) ARE in 142-evaluable pool; split between safe-30 vs consistent-33 → user chose consistent-33.
- **[[D-2]]** locked Option A: 1-sentence paper caveat (§5.3 or §6.2) — OpenSSH 50% validated this session (all 20 errors are FPs, zero FNs).
- **[[D-3]]** locked Option B: add 1 sentence to §5.7 with launch-date framing.
- **[[D-6]]** locked Option B: BERT-F1 recompute (~3h laptop) + add column to Tables 2/3, fallback Option C if PDF > 16p.
- **[[D-11]]** RESOLVED this session: Flow-of-Action paragraph EXISTS at line 617 of sandbox sn-article.tex (preserved through s15/s16 rewrites).
- **[[B-4]]** locked: 1-sentence variance footnote to Tables 2 + 6 ("5-case temp=0 nondeterminism between runs"). Note: revised to 6 cases (1 ann + 5 rca) in session 24.
- **[[Conflict-4]]** locked: 1-sentence calibration limitation in §6.2.

**TIER 2 — repo hygiene**: D-4, D-5, D-7, D-8, D-9, D-12, D-14 (NEW), D-15 (NEW). All ACT NOW carefully.

**TIER 3**:
- **[[D-10]]** locked: mark superseded by CV1+CV2 + session 16 audit work ("no need for this i guess anymore").
- **[[Conflict-5]]** locked: master backup zip = keep FOREVER ("it should remain forever").

**TIER 4 — D-13 + D-16**: skip pytest smoke; D-16 NEW dataclass bug discovered.

**NEW items discovered session 17**:
- **D-14**: script default `--dataset` path doesn't exist on instance (pre-reorg layout). Patched.
- **D-15**: temp file written as plain list, runner expected dict. Patched.
- **D-16 (NEW)**: `r.get("correct")` on `TestCaseResult` dataclass (lines 132, 133, 221, 222). Blocker. **Pending patch for session 18**.
- **Instance src/ OUTDATED**: `Neo4jClient.find_similar_episodes_by_embedding` exists on laptop (line 747) but NOT on instance. Causes silent warning loop in with-graph mode → results would be meaningless. **Blocker for Phase 4.5 4.5b/4.5c**.

**Phase 4.5 attempts session 17**: 3 launches, 3 crashes (D-13/14/15/16 + instance src outdated). Instance auto-stopped via CloudWatch idle-stop alarm at 10:51 UTC. Partial 16-case results preserved on EBS at `/mnt/aiops-repo/runs/2026-05-25T10-18-31_*/results.jsonl`.

**Phase 4.5 PATH options for next session** (locked in SESSION_17 §3.4):
- PATH 1: patch D-16 + SCP src/ + re-launch (~$5, ~5h)
- PATH 2: re-clone instance from main + same (~$5, ~6h, cleanest)
- PATH 3: defer 4.5 entirely, ship paper with [TBD] cells
- PATH 4: drop 4.5b/4.5c rows from sandbox Table 6

### Session 18 (2026-05-26) — Phase A executed + D-6 BERT background

**Source**: `SESSION_18_HANDOFF.md` §2-3

**Phase A DONE** (~3h):
- A.1 [[D-1]] dataset re-label (33 cases): `task_type: rca→qa_mcq` + `excluded_reason` field. New SHA `d1a8f79f...`.
- A.2 [[D-1]] result-file sync: updated 33 cases task_type across 16 files.
- A.3 [[D-1]] Phase 5 stats recompute via `phase5_stats.py`.
- A.4 doc edits: SUMMARY.md / METHODOLOGY.md / MANIFEST.md / BUG_HISTORY.md / AUDIT_REPORT.md per locked items.
- A.5 Tier 2 mechanicals: [[D-7]] [[D-8]] [[D-9]] [[D-12]] [[D-14]] [[D-15]] applied.
- A.6 [[D-6]] BERT recompute kicked off in background.

**D-6 BERT-F1 background result** (~9 min completion): 14 files processed via roberta-large on CUDA. Mean F1 = 0.8124 (Ann 0.822, RCA 0.795). **KNOWN ARTIFACT**: `ablation_no_system_prompt` n=1 and `ablation_with_graph` n=0 because their JSON outputs filtered by MIN_TEXT_LEN=15. Crosslink: [[I-8]] (BERT-F1 in tables 5/6/7 decision).

**Phase B (sandbox paper edits)** NOT yet applied — only investigation reads done.

**Phase C (AWS Phase 4.5)** NOT yet launched.

**Phase D (commits + rsync + push)** deferred to end of all phases.

**USER DIRECTIVE for session 19**: "start session 19 with Phase C FIRST. Wait for AWS Phase 4.5 to FINISH before doing Phase B paper edits."

### Session 19 (2026-05-26) — Phase C launched (AWS Phase 4.5)

**Source**: `SESSION_19_HANDOFF.md`

- User chose **PATH 2 then PATH 1** for Phase C.
- Re-cloned instance from origin/main + scp'd patched src/. Smoke-tested + smoked PASSED.
- **AWS Phase 4.5 launched** at 20:48:02 UTC in tmux `phase45` on instance `i-091c4de0e95d63154`. ETA ~2h 10min.
- CloudWatch `aiops-idle-stop` alarm DISABLED before launch (to survive slow Neo4j writes). Re-enable in session 20.
- Fold 1 results at session-19 close: **no-graph=100% / with-graph=100%** (ceiling effect at 16/16 each leg).
- User hibernated laptop with Phase 4.5 still running.
- **D-6 BERT context saved** to SUMMARY.md §3.5 + BUG_HISTORY.md D-6 → RESOLVED.

### Session 20 (2026-05-26) — Phase C wrapped (PATH 4 locked) + D-17 + Phase B

**Source**: `SESSION_20_HANDOFF.md`

- AWS validation block (10 checks) executed. Result: **`.FAIL` marker present** + tmux gone + python gone + log shows all 5 folds completed with `no-graph=with-graph=100%` then crash with `TypeError: Object of type TestCaseResult is not JSON serializable` at `run_graph_experiments.py:172`. **NEW BUG: D-17**.
- **Decision rule applied**: 4.5b |Δ|=0pp (fails ≥2pp), 4.5c never ran. **PATH 4 locked**.
- **[[D-17]]** patched: `import dataclasses` + wrap JSON-write calls with `json.dumps(dataclasses.asdict(r), default=str)`. Crosslink: [[D-16]] sister bug (attribute-access vs file-write halves of same dataclass type). Documented in `BUG_HISTORY.md` row #9.
- **Phase 4.5 partial-result handling**: `exp_4_5b_summary.json` (757B valid) + per-case JSONLs (0B — D-17 loss) + stale `exp_4_5c_summary.json` (session-17 leftover, do NOT cite). Forensic log written.
- **Instance stopped** + CloudWatch alarm re-enabled.
- **5 FINAL LOCKED DECISIONS** for session 21 (Phase B execution):
  - Decision 1: Table 4 → Option A (v1 component×metrics layout, after Option D recompute n=213)
  - Decision 2: Latency Stack B → Option A (keep Stack A only, no table change)
  - Decision 3: Figure 3 → Option A+D (restore v1 dims + xmin=30)
  - Decision 4: Drop §5.8 Graph Sub-experiment subsection → Option B
  - Decision 5: §6.1 Research Gap → Option C (keep as-is unless Decisions 1+3+4 push to 17p)
- **Phase B partially applied** session 20 (Table 2/6a/6b/7 + new sentences for D-1/D-2/D-3 + Table 6 graphsub PATH 4 + BERT-F1 Option C 1-sentence after Option B failed at 17p).

### Session 21 (2026-05-26) — Decision 1/3/4 + 7 polish + DIFF PDF started

**Source**: `SESSION_21_HANDOFF.md`

- Decisions 1, 3, 4 from session 20 applied to sandbox.
- 5 additional user polish fixes (Fig 3 overlap callout + 84% baseline label + interpretive paragraph after Table 6 + `\usepackage{placeins}` + `\FloatBarrier` before §5.7 + 3 bib drops `adaspec2025` `edge2024graphrag` `zhang2020effect`).
- Final sandbox PDF: 16 pages / 460,355 bytes / ~782 lines.
- **Intentional 3-point rubric disclosures** confirmed at lines 447 + 597. DO NOT REMOVE.
- **DIFF PDF generation STARTED but INCOMPLETE**:
  - latexdiff failed (Algorithm::Diff missing in MiKTeX) → latexdiff-fast WORKS
  - Multiple type attempts failed: UNDERLINE breaks tables, CFONT breaks emph, BOLD not allowed in section args
  - Working combo: `--type=INVISIBLE --graphics-markup=none --no-del --exclude-textcmd="emph,textbf,textit,texttt"`
  - About to apply yellow `\hl{}` override when user INTERRUPTED
  - **References NOT resolved** in current DIFF PDF (bibtex not run yet)
- No commits made session 21 (Gate 1 pending).

### Session 22 (2026-05-26) — DIFF PDF complete + sandbox reorg + Gate 1 push + 5-agent audit

**Source**: `SESSION_22_HANDOFF.md` + `paper_audit_session22_2026-05-26/`

- **DIFF PDF resume**: yellow `\hl{}` failed on `\cite{}` → switched to `\textcolor{red!75!black}` (no bold to avoid 17p regression). Final DIFF PDF: 16 pages / 461,798 bytes / 0 undefined refs. Crosslink: [[hard-rule-9]] DIFF override.
- **Sandbox reorganization** (user choice Option 2): sandbox split into `main/` + `diff/` subfolders mirroring v1 flat layout. **Mid-stream objective change**.
- **9 loose root files** sorted under `_session11_phase4_orphans/`, `_session12_reorg_intermediates/`, `benchmark/scripts/_dev/`.
- **HANDOFF.md MOVED** to `benchmark/HANDOFF.md` and rewritten (470 lines, was dated 2026-05-13).
- **Mid-stream objective change**: real `sn-article-template.v2/` MOVED to `z.Dump Paper Archive/` by user → sandbox-session16 IS the canonical edit target. **Rsync to real path PERMANENTLY DROPPED** (Gate 2).
- **Gate 1 — 6 themed commits applied + pushed**: `9bc5107` (D-1 data) + `3e29c14` (docs) + `916220b` (scripts fix) + `5843f99` (D-6 eval) + `a9dcb53` (4.5 data + D-17 forensic) + `77f49f9` (audit/HANDOFF docs).
- **Gate 3 push**: `a5e9005..77f49f9 main -> main` synced.
- **5-agent parallel paper audit** launched. Findings consolidated in `00_SUMMARY.md`:

**10 CRITICAL findings** [[introduced]] (must fix pre-camera-ready):
- **[[C-A1]]** Abstract still cites v1 numbers (150-test / 90.7% / four datasets)
- **[[C-A2]]** §1 Intro ¶2 repeats stale v1 numbers (1,050 inferences / 31.3pp drop)
- **[[C-A3]]** §2/RG1/RG2 "3.3pp dual-agent" and "0.7% constitutional overhead" unsupported
- **[[C-B1]]** Table 4 14B row shows n=180 RCA-only but footnote claims n=431
- **[[C-B2]]** Table 7 Drain row caption claims 431-case but Drain ran on 202-case subset
- **[[C-B3]]** §5.5 "vLLM+FP8 1.5×" was 30-case smoke, not 431-case
- **[[C-C1]]** MANIFEST.md SHA table stale for all 14 D-6 BERT-F1 recompute files
- **[[C-C2]]** 3 qa_mcq cases (RM_016/022/032) have `correct=True/False` instead of null; 71 actually-excluded vs 74 claimed
- **[[C-D1]]** HANDOFF.md §7 ablation cells drift on 5 rows (Single-4B, Single-14B, No-constitutional, No-system-prompt, with-graph)
- **[[C-D2]]** HANDOFF.md §7 SOTA Overall cells drift (Llama 83.3 / DeepSeek 81.1 vs paper+SUMMARY 83.5 / 81.2)

**14 IMPORTANT findings** [[introduced]]:
- **[[I-1]]** Stack B "vLLM+FP8" should be "vLLM AWQ awq_marlin"
- **[[I-2]]** P95/P99 percentile method inconsistency (index-floor vs linear-interp, 0.2s gap)
- **[[I-3]]** §5.1 RTT 1.95ms vs Table 4 footnote 1.10ms
- **[[I-4]]** `alibaba2024qwen` bib title says Qwen2.5 but paper uses Qwen3
- **[[I-5]]** §6.2 calls Phase 4.5 "planned" but it ran
- **[[I-6]]** with-graph / with-orchestrator RCA delta rounds to −2.2pp (paper says −2.1pp)
- **[[I-7]]** Table 1 splits 431 as 218+213; Table 4 footnote as 218+180+33
- **[[I-8]]** BERT-F1 only in Table 2; missing from Tables 5/6/7
- **[[I-9]]** Run-to-run footnote "5 cases" — actual 6 (1 ann + 5 rca)
- **[[I-A]]** `peng2025graphragsurvey` bib missing volume/issue/pages/DOI
- **[[I-B]]** `zhang2024aiopssurvey` year=2024 (likely 2025/2026)
- **[[I-C]]** `nvidia2024specdec` lacks URL
- **[[I-D]]** Bib comment "26 references" (actual 36)
- **[[I-E]]** Per-source numerical breakdowns at `:481` says "deferred to supplementary" but next table contains them

**7 MINOR findings** [[introduced]]:
- **[[M-1]]** 5 orphan bib entries (3 intentional drops + bertscore2020 + karpukhin2020dense)
- **[[M-2]]** 2 of 12 expected new bib entries missing (Brittlebench, C3AI)
- **[[M-3]]** Pre-D-1 `excluded_rca_cases.json` still on disk
- **[[M-4]]** Stale `main_benchmark/summary.json` byte-identical to `benchmark_result.json`
- **[[M-5]]** D-1 rich-eval not applied to 8 ablation `results.json` files (matched-eval canonical)
- **[[M-6]]** SUMMARY.md:21 rich-eval RCA 92.5% (actual 91.1% post-D-1)
- **[[M-7]]** Stale `phase45_graph/exp_4_5c_summary.json` (session-17 leftover)

### Session 23 (2026-05-26) — Group A applied (10 CRITICAL fixes)

**Source**: `SESSION_23_HANDOFF.md`

Path A locked (Group A fixes). 3 decision points locked:
- **Table 4 14B row** → refit to n=213 (P50 29.83 / P95 62.20 / Avg 32.50)
- **Table 7 Drain row** → DROP row entirely + non-LLM baseline note in §5.7 prose
- **71-vs-74 exclusion** → Option A: flip 3 qa_mcq `correct=True/False`→`null` in 13 result files

Group A outcomes (all 10 CRITICAL + 1 bonus applied):
- **[[C-A1]]** Abstract rewritten (431 / 82.4% / BCa CI [78.2,86.0] / 8-config / 3,448 inf / −22.7pp / −34.4pp / SOTA-beat 10.8/15.1pp)
- **[[C-A2]]** §1 Intro ¶2 rewritten with v3.0 numbers
- **[[C-A3]]** RG2 / Contribution-1 / §2.1 / §2.3 rewritten — "0.7% overhead" removed; "3.3pp" replaced with empirically-supported framing
- **[[C-B1]]** Table 4 14B row refit + footnote disclosure (n=218 / n=213 / n=431)
- **[[C-B2]]** Drain row dropped + §5.7 supplementary disclosure
- **[[I-1]] = audit-CRIT-B3 + C-B3** "vLLM+FP8" → "vLLM AWQ" at 3 sites
- **[[C-C1]]** MANIFEST.md all 20 Post-D-1 SHAs + sizes refreshed
- **[[C-D1, C-D2]]** HANDOFF.md §7 fixed (5 ablation rows + 2 SOTA Overall + Full-Hybrid Ann typo + sandbox sizes + priority list)
- **[[C-C2]]** Flip script `flip_qa_mcq_correct_to_null.py` run on 13 files (39 cells flipped). null_count: 71→74 in every file.

Gate 4 — 4 themed commits + Gate 5 push: `77f49f9..68b5a58 main -> main`. Sandbox: 16p / 463,353 B.

### Session 24 (2026-05-26) — Group B (10) + Group C (5)

**Source**: `SESSION_24_HANDOFF.md`

Path A locked (Group B fixes). 4 decision points:
- **[[I-8]]** → Option C: leave as-is (BERT-F1 only in Table 2 + §5.2 prose covers Table 7)
- **[[I-4]]** → update title to "Qwen Technical Report (Qwen3 Series)" + year 2025 (keep cite key)
- **[[I-A/B/C]]** → **DEFER to camera-ready** (no fake fields; needs external lookup)
- Plan: 2 batches

Group B applied (10 items: 7 reviewer-surface + 3 deliberate-defer + 1 deliberate-skip):
- **[[I-6]]** −2.1pp → −2.2pp (Tables 5 + 6)
- **[[I-9]]** 5→6 cases at 3 sites
- **[[I-3]]** RTT 1.95→1.10ms
- **[[I-D]]** bib header "26 references" → "36 entries (31 cited; 5 retained-orphan)"
- **[[I-4]]** alibaba bib title + year
- **[[I-5]]** §6.2 "planned" → "ran to completion and saturated (aggregate preserved; per-case logs lost to post-run serialization bug)"
- **[[I-7]]** Table 1 new footnote (213 = 180+33, 74 excluded, 139 evaluable)
- **[[I-2]]** Table 4 footnote append "Percentiles use index-floor convention"

Group C applied (5+1 items + MANIFEST refresh):
- **[[M-1a]]** bertscore cite added at line 455
- **[[M-1b]]** karpukhin2020dense bib block removed (3 → "35 entries / 32 cited / 3 retained-orphan")
- **[[M-6]]** SUMMARY.md:21 rich-eval RCA 92.5→91.1%, Overall 87.5→86.4%
- **[[M-7]]** rename `exp_4_5c_summary.json` → `exp_4_5c_summary_STALE_session17.json`
- **[[Auditor-4 I2]]** D-1 re-label to 8 rich-eval `ablation_*/results.json` (264 task_type flips)
- **[[Auditor-4 M4]]** `benchmark_431_seed42.json` header `rca_cases: 213→180` + add `qa_mcq_cases: 33`
- MANIFEST SHA refresh for the changed dataset entry

**DIFF regen ROOT-CAUSE DEBUG**: CRLF + listings v1.11b incompatibility → LF write + drop listings dep. Encoded in `regen_diff_pdf.py`. Crosslink: [[hard-rule-18]] (DIFF regen recipe).

Gate 6 — 4 themed commits + push: `affad56..dd51724 main -> main`. Sandbox: 16p / 466,286 B.

### Session 25 (2026-05-26) — Path C camera-ready prep (I-E + I-A/B/C resolved)

**Source**: `SESSION_25_HANDOFF.md`

Path C locked. 3 user decisions:
- **I-E** (sandbox `.tex:484` "deferred to supplementary" contradiction) → fix in place
- **I-A/B/C** (deferred bib entries) → fix via external lookup
- Abstract/§1 tone pass → preserve original; correct only if factual error surfaces (none found)

Outcomes:
- **[[I-E]]**: replace "Numerical breakdowns are deferred to the camera-ready supplementary tables." with "Table~\ref{tab:errortable} below disaggregates by source."
- **[[I-A]]** `peng2025graphragsurvey`: WebSearch + arXiv. Added DOI 10.1145/3777378; "Zhu, Yunfeng" → "Zhu, Yun"; vol/issue NOT added (min-viable). **Process lesson born**: min-viable bib rule (DOI alone preferred over vol/issue/pages).
- **[[I-B]]** `zhang2024aiopssurvey`: WebSearch + DBLP. **BIB HAD WRONG FIRST AUTHOR** — "Zhang, Yongqian" → "Zhang, Lingzhe". Year 2024 → 2026. DOI added. **Cite key preserved as stable label** (zhang2024 stays despite 2026 entry). Crosslink: [[Process lesson #3 cite-key as stable label]].
- **[[I-C]]** `nvidia2024specdec`: WebFetch NVIDIA blog. **TITLE WAS WRONG** — "Accelerating LLM Inference with Speculative Decoding" → "An Introduction to Speculative Decoding for Reducing Latency in AI Inference". Year 2024 → 2025. Authors institutional → Li/Yu/Guo. URL added.
- Min-viable trim applied (DOI alone, no vol/issue/pages on I-A/B) to preserve 16p.
- DIFF regen via `regen_diff_pdf.py` (Perl on PATH + LF write + listings drop).

Pushed: `0bca114..618c4cc main -> main`. Sandbox: 16p / 467,671 B.

### Session 26 (2026-05-26) — Path B'' Tier 1 (peng year) + Path F (post-close cleanup)

**Source**: `SESSION_26_HANDOFF.md`

- CrossRef API lookups for peng (10.1145/3777378) and zhang (10.1145/3746635) DOIs. **Bonus finding**: peng bib year 2025 → 2026 per CrossRef (same arXiv-vs-journal year split as zhang).
- **Tier 1 applied**: peng `year="2025"→"2026"` (single Edit, +1 char).
- Tier 2 (vol/issue/pages) and Tier 3 (cite-key renames) DEFERRED (still pending).
- **Camera-ready submission package built** at `_camera_ready_2026-05-26/` (5 files, 1.09 MB).
- **POST-CLOSE CLEANUP**: user observed package PDFs are pure duplicates of live main/diff PDFs → package DELETED. Live PDFs SHA-256s preserved in handoff for provenance. **Process lesson born**: no submission "package" folders; submit `main/sn-article.pdf` directly.
- 2 commits + push: `0bca114..fc375b8 main -> main`. Sandbox: 16p / 467,673 B / SHA-256 `be6c27ab…d9483`.

### Session 27 (2026-05-26 → 2026-05-27) — Multi-agent verification Stages 1a + 1b

**Source**: `SESSION_27_HANDOFF.md`

User pivot: multi-agent verification pass before camera-ready. **Mid-stream objective change**: instead of Path G submit, ran first 2 of 8-stage plan.

**Stage 1a** (general-purpose agent): reference inventory mapping 35 bib × 47 xlsx × 8 on-disk PDFs. Output: `01_references_inventory_report.md` (177 lines) + `01_xlsx_delta_proposal.csv` (68 rows × 12 cols, NEW Status/Action/Notes columns).

**Stage 1b** (general-purpose agent + 2 retry passes): PDF download for 27 entries via playwright (1.60.0 installed + Chromium v1223 downloaded 294 MB).

Results:
- 21 OK via curl from arXiv/OpenReview/CNCF
- 3 via sci-hub.ee → sci.bban.top CDN fallback (Anna's Archive DNS/DPI-blocked across all 4 domains in this env)
- 1 paywalled FAILED_MANUAL (`notaro2021aiopssurvey` — genuinely not in sci-hub across 5 mirrors)
- 1 NOT_ATTEMPTED (`chen2024autonomous` — bib placeholder, no DOI/arXiv)

**24 new PDFs landed in REFERENCE PAPERS/** (13.7 MB → 71 MB, 32 PDFs at top level).

**🔴 9 bib metadata errors flagged across 4 entries** [[introduced]]:
- **[[S1b-miller×4]]** `miller2025bootstrap`: author Joshua Miller+Ruder → Evan Miller (Anthropic); title paraphrase → "Adding Error Bars to Evals"; year 2025 → 2024; arXiv 2503.01747 → 2411.00640
- **[[S1b-notaro×1]]** `notaro2021aiopssurvey`: journal "ACM Transactions on Networking and Service Management" (doesn't exist) → likely IEEE TNSM (real DOI unconfirmed)
- **[[S1b-wu×2]]** `wu2020microrank`: author list completely wrong (real lead = Guangba Yu, NOT Wu/Tordsson/Elmroth/Kao); year 2020 → 2021 (WWW 2021)
- **[[S1b-chen-automap×2]]** `chen2022automap`: author list partially wrong (real leads = Meng Ma + Ping Wang PKU; Chen is 5th author); year 2022 → 2020 (WWW 2020)

**Stage-1a-style URL guessing error rate**: ~3/22 (14%) of agent-discovered URLs pointed at wrong papers. **Process lesson #6 born**: first-page-verify a downloaded PDF before trusting bib metadata. Title-substring matching alone too weak.

**NEW Stage 1c added to plan** (per user request mid-session): independent PDF content verification agent for session 28 start.

**Gates landed locally**: 14 (Stage 1a `5bfbabe`) + 15 (Stage 1b initial `e82f5cd`).
**Gate 16** (close-out commit) **PENDING USER GO**.
**Gate 17** (batched push of 14+15+16) **PENDING SEPARATE USER GO at session close**.

### Stage 1c (session 28 start, 2026-05-27) — Independent PDF content verification

**Source**: `paper_audit_session27_2026-05-26/03_pdf_content_verification.md`

29 PDFs verified via `pdftotext -l 3 + SHA-256 + bib field cross-check`:
- 7 MATCH
- 11 PARTIAL (preprint year vs venue year, venue not on first-3-pages, minor title drift)
- 3 KNOWN_BIB_ERROR (confirmed Stage 1b's 9-field-across-3-entries findings)
- **8 NEW_BIB_ERROR** [[introduced]] across 8 entries:
  - **[[S1c-adaspec]]** `adaspec2025`: lead author Kaiyu Huang (Tongji), not Zhang Hao
  - **[[S1c-askell]]** `askell2024collective`: lead authors Saffron Huang + Divya Siddarth + Liane Lovitt; Askell is co-author not first
  - **[[S1c-chen-rcagent]]** `chen2024rcagent`: lead author Zefan **Wang** (Tsinghua), not Zefan Chen — surname Chen does not appear on paper at all
  - **[[S1c-li-opseval]]** `li2024opseval`: lead author Yuhe **Liu** (Tsinghua), not Li Liang
  - **[[S1c-liu-logeval]]** `liu2025logeval`: lead author Tianyu **Cui** (Nankai); Yilun Liu is 6th author
  - **[[S1c-pei-foa]]** `pei2025flowofaction`: lead author Changhua Pei (CAS), not Yuwei Pei
  - **[[S1c-shi-aiopslabs]]** `shi2025aiopslabs`: lead author Yinfang **Chen** (Illinois), not Yinfang Shi
  - **[[S1c-xu-openrca]]** `xu2025openrca`: lead author Junjielong Xu (CUHK Shenzhen), not Yihan Xu; title differs
- **Other**: `arigraph2024` 2nd/3rd author drift (separately flagged)
- **Other**: `bansal2021does` title drift "AI Confidence" → "AI Explanations"

**0 UNREADABLE. 0 TAMPER_DETECTED.** All 24 newly-downloaded PDFs have intact SHA-256.

---

## §3. Decision lifecycle index

| Decision ID | Locked in | Last touched | Current status | Crosslinks |
|---|---|---|---|---|
| **D-1** OpsEval-remine qa_mcq re-label | Session 17 (Option b consistent-33) | Session 22-23 (CRIT-C2 flipped 3 to null) | ACTIVE — Phase 5 stats use 357 evaluable | [[D-3]], [[D-6]], [[CRIT-C2]] |
| **D-2** OpenSSH 50% caveat | Session 17 (Option A) | Session 20 (in Phase B sandbox §6.2) | RESOLVED — sentence in §6.2 | — |
| **D-3** Bedrock pivot launch-date framing | Session 17 (Option B) | Session 20 (in Phase B sandbox §5.7) | RESOLVED — sentence in §5.7 | [[D-1]] (same Bedrock root cause) |
| **D-4** L5307 fake-graph BUG_HISTORY footnote | Session 17 | Session 18 (BUG_HISTORY footnote added) | RESOLVED | — |
| **D-5** AWS Budgets cost-source footnote | Session 17 | Session 18 (SUMMARY.md §6) | RESOLVED | — |
| **D-6** BERT-F1 recompute | Session 17 (Option B → fallback C) | Session 24 (Option C 1-sentence kept; Tables 5/6/7 column dropped per [[I-8]]) | RESOLVED (recompute done s18; in Table 2 + §5.2) | [[BUG #8]], [[I-8]] |
| **D-7** test_5plus5.py 499→431 fix | Session 17 | Session 18 | RESOLVED | [[D-8]], [[Conflict-3]] |
| **D-8** HANDOFF.md strike stale 499 delete | Session 17 | Session 18 | RESOLVED | [[Conflict-3]] |
| **D-9** HANDOFF.md §6↔§14 reconcile | Session 17 | Session 18 (initial) + Session 23 (CRIT-D1/D2 deeper drift fix) | RESOLVED (post s23 commit `61ca91f`) | [[Conflict-1]], [[Conflict-2]] |
| **D-10** CV 5th agent | Session 17 (mark superseded) | Session 17 | RESOLVED (superseded by CV1+CV2 + s16 audit) | — |
| **D-11** Flow-of-Action paragraph | Session 17 (RESOLVED — exists at line 617) | Session 17 | RESOLVED | — |
| **D-12** AWS Phase 4.5 GO/NO-GO trigger | Session 17 (mark moot) | Session 18 | RESOLVED — Phase 4.5 launched in s19 | [[D-13/14/15/16/17]] |
| **D-13** `exp_4_5c` `Neo4jClient.run_query` AttrErr | Session 16 (discovered + patched) | Session 16 commit `57035cf` | RESOLVED | [[BUG_HISTORY-D-13]] |
| **D-14** Script default `--dataset` path nonexistent on instance | Session 17 (discovered) | Session 18 (fallback added) | RESOLVED | — |
| **D-15** Temp file list-vs-dict format | Session 17 (discovered + patched) | Session 18 (committed) | RESOLVED | — |
| **D-16** `r.get("correct")` on dataclass | Session 17 (discovered) | Session 18 (patched 6 instances) | RESOLVED | [[D-17]] sister bug |
| **D-17** `json.dumps(TestCaseResult)` not serializable | Session 19 (discovered post-Phase-4.5-crash) | Session 20 (patched + forensic log) | RESOLVED — instance copy still buggy (rule 22) | [[D-16]] sister, [[BUG_HISTORY #9]] |
| **Conflict-1** HANDOFF Phase 4.4 status | Session 16 | Session 23 | RESOLVED (CRIT-D1 fix) | [[D-9]] |
| **Conflict-2** HANDOFF Phase 4.7 status | Session 16 | Session 23 | RESOLVED (CRIT-D1 fix) | [[D-9]] |
| **Conflict-3** benchmark_499 delete stale instruction | Session 16 | Session 18 | RESOLVED | [[D-8]] |
| **Conflict-4** Confidence weights α/β/γ never calibrated | Session 16 | Session 20 (sentence in §6.2) | RESOLVED | — |
| **Conflict-5** Master backup zip keep-indefinitely | Session 16 | Session 17 (locked "remain forever") | RESOLVED | — |
| **B-4** Variance footnote (5→6 cases) | Session 17 (initial 5) → Session 24 (corrected to 6) | Session 24 ([[I-9]]) | RESOLVED | [[I-9]] |
| **C-A1** Abstract v1 numbers stale | Session 22 (audit) | Session 23 (rewritten) | RESOLVED | [[C-A2]], [[C-A3]] |
| **C-A2** §1 Intro v1 numbers stale | Session 22 | Session 23 | RESOLVED | [[C-A1]] |
| **C-A3** §2/RG1/RG2 unsupported claims | Session 22 | Session 23 | RESOLVED | [[C-A1]], [[C-A2]] |
| **C-B1** Table 4 14B row inconsistency | Session 22 | Session 23 (refit n=213) | RESOLVED | — |
| **C-B2** Drain 431 claim wrong | Session 22 | Session 23 (Drain row dropped) | RESOLVED | — |
| **C-B3** Stack B 30-case smoke disclosure | Session 22 | Session 23 (disclosed inline) | RESOLVED | [[I-1]] |
| **C-C1** MANIFEST SHA stale (14 BERT-F1 files) | Session 22 | Session 23 (refreshed) | RESOLVED | [[D-6]] |
| **C-C2** 3 qa_mcq cases correct≠null | Session 22 | Session 23 (39 cells flipped) | RESOLVED | [[D-1]] |
| **C-D1** HANDOFF §7 ablation drift | Session 22 | Session 23 | RESOLVED | [[D-9]] |
| **C-D2** HANDOFF §7 SOTA Overall drift | Session 22 | Session 23 | RESOLVED | [[D-9]] |
| **I-1** Stack B "vLLM+FP8" → "vLLM AWQ" | Session 22 | Session 23 | RESOLVED | [[C-B3]] |
| **I-2** P95/P99 percentile method | Session 22 | Session 24 (Table 4 footnote disclosure) | RESOLVED | — |
| **I-3** RTT 1.95 vs 1.10 ms | Session 22 | Session 24 (1.10ms canonical) | RESOLVED | — |
| **I-4** alibaba Qwen2.5 vs Qwen3 | Session 22 | Session 24 (title + year corrected) | RESOLVED | — |
| **I-5** §6.2 "planned" → "ran" | Session 22 | Session 24 | RESOLVED | [[D-17]] |
| **I-6** Table 5/6 −2.1 → −2.2pp | Session 22 | Session 24 | RESOLVED | — |
| **I-7** Table 1 vs Table 4 footnote 213 vs 180+33 | Session 22 | Session 24 (Table 1 footnote) | RESOLVED | — |
| **I-8** BERT-F1 in Tables 5/6/7 | Session 22 | Session 24 (Option C: leave as-is, only in Table 2) | RESOLVED (deliberate skip) | [[D-6]] |
| **I-9** 5 vs 6 cases run-to-run | Session 22 | Session 24 (3 sites updated) | RESOLVED | [[B-4]] |
| **I-A** peng vol/issue/pages | Session 22 (defer) | Session 25 (DOI only added) + Session 26 (year 2025→2026) | PARTIAL — vol/issue/pages still deferred | [[Tier 2]] |
| **I-B** zhang year/author | Session 22 (defer) | Session 25 (year 2024→2026, author Yongqian→Lingzhe, DOI added) | RESOLVED (cite-key retained as stable label) | [[Process lesson #3]] |
| **I-C** nvidia URL | Session 22 (defer) | Session 25 (title + year + authors + URL fixed) | RESOLVED | — |
| **I-D** bib header "26 references" | Session 22 | Session 24 ("36 entries" → s24 → "35 entries" after M-1b) | RESOLVED | [[M-1]] |
| **I-E** §484 deferred-to-supplementary contradiction | Session 22 (surfaced as audit-IMPORTANT) | Session 25 (Path C, in-place fix) | RESOLVED | — |
| **M-1a** bertscore2020 orphan → cite | Session 22 | Session 24 | RESOLVED | [[M-1]] |
| **M-1b** karpukhin2020dense drop | Session 22 | Session 24 | RESOLVED | [[M-1]] |
| **M-2** Brittlebench + C3AI missing | Session 22 | Session 24 (judged intentional drops per page budget) | RESOLVED (deliberate) | — |
| **M-3** Pre-D-1 excluded_rca_cases.json on disk | Session 22 | (not closed) — described as legacy in METHODOLOGY | DEFERRED | — |
| **M-4** Stale main_benchmark/summary.json | Session 22 | (not closed) | DEFERRED | — |
| **M-5** D-1 rich-eval | Session 22 | Session 24 (auditor-4 I2 applied) | RESOLVED | — |
| **M-6** SUMMARY.md:21 RCA 92.5%→91.1% | Session 22 | Session 24 | RESOLVED | — |
| **M-7** Stale exp_4_5c_summary.json | Session 22 | Session 24 (renamed _STALE_session17) | RESOLVED | [[D-17]] |
| **Path A** Group A | Session 22 | Session 23 | RESOLVED | — |
| **Path B** Group C | Session 22 (alt name) | Session 24 | RESOLVED | — |
| **Path B'' Tier 1** peng year | Session 26 | Session 26 | RESOLVED | [[I-A]] |
| **Path B'' Tier 2** vol/issue/pages | Session 24/26 | Pending (Tier 2 risk 17p overshoot) | DEFERRED (low priority) | [[I-A]] |
| **Path B'' Tier 3** cite-key renames | Session 24 | Pending (cosmetic) | DEFERRED (only-if-reviewer-flags) | — |
| **Path C** Camera-ready prep | Session 24 | Session 25 (I-E + I-A/B/C) | RESOLVED | — |
| **Path D** AWS rerun (Stack B / 4.5c) | Session 22 onward | Pending | DEFERRED (not blocking; only-on-reviewer-demand) | — |
| **Path E** Other | Session 22+ | (no action) | N/A | — |
| **Path F** Camera-ready submission package | Session 26 | Session 26 (built then deleted post-close) | RESOLVED — submit `main/sn-article.pdf` directly | — |
| **Path G** Submit | Session 26 | Pending COMSYS 2026 CFP | DEFERRED (CFP-gated) | — |
| **Stage 1a** Reference inventory | Session 27 | Session 27 | RESOLVED | — |
| **Stage 1b** PDF download | Session 27 | Session 27 (3 sub-passes) | RESOLVED (with 9 bib errors flagged) | [[S1b-miller×4]], [[S1b-notaro×1]], [[S1b-wu×2]], [[S1b-chen-automap×2]] |
| **Stage 1c** PDF content verification | Session 28 (planned) | Session 28 | RESOLVED — 8 NEW bib errors flagged | [[Stage 1b]] |

---

## §4. Recalcs / numerical revisions

### Recalc #1 — D-1 OpsEval-remine re-label (session 18)

**Trigger**: D-1 spot-check (session 17) found 33 cases are MCQ-style knowledge questions, not diagnostic RCA.

**Files mutated** (16): `benchmark_431_seed42.json` + 9 matched-eval result files (main + 8 ablation) + 2 SOTA baselines (llama_3_3_70b.jsonl, deepseek_v3.jsonl; drain.jsonl no-op) + 2 phase46_no_prompt JSONLs.

**Source-of-truth files regenerated**: `main_benchmark/phase5_stats.{json,md}`, `ablation_v4/phase5_stats.{json,md}`, `matched_eval_table.md`.

**Numerical impact** (per `SESSION_17_RECALC_SCOPE.md` §3 + verified s18):

| Metric | Before | After | Δ |
|---|---|---|---|
| Main Annotation | 82.6% (180/218) | 82.6% (180/218) | — |
| **Main RCA** | 80.3% (114/142) | **82.0% (114/139)** | **+1.7pp** |
| **Main Overall** | 81.7% (294/360) | **82.4% (294/357)** | **+0.7pp** |
| **Ablation Full RCA** | 83.8% (119/142) | **85.6% (119/139)** | +1.81pp |
| Ablation Full Overall | derived | **84.0% (300/357)** | — |
| Llama 3.3-70B RCA | 71.1% (101/142) | **71.2% (99/139)** | (3 cases removed: 2 correct, 1 wrong) |
| DeepSeek V3.2 RCA | 66.9% (95/142) | **66.9% (93/139)** | — |
| **ΔRCA Ours − Llama** | +9.2pp | **+10.8pp** | +1.6pp (FAVORABLE to ours) |
| **ΔRCA Ours − DeepSeek** | +13.4pp | **+15.1pp** | +1.7pp (FAVORABLE to ours) |

**Headline qualitative findings unchanged** (graph defused, prompt task-asymmetric, constitutional asymmetric — see `phase5_stats.md §4`).

### Recalc #2 — D-6 BERT-F1 recompute (session 18, background ~9min)

**Trigger**: Bug #8 (session 8, AWS root EBS 40 GB → BERTScore couldn't download).

**Files mutated** (14): same set as Recalc #1 minus drain.jsonl (boolean output, skipped). `bert_f1` field populated in place per record.

**Headline**: Mean F1 = 0.8124 (Ann 0.822, RCA 0.795). Stored in `_bert_f1_recompute_summary.json`.

**KNOWN ARTIFACT** (carried forward): `ablation_no_system_prompt` Ann n=1 (1 pair passed MIN_TEXT_LEN=15 filter; JSON-only outputs); `ablation_with_graph` Ann n=0 (same reason). RCA counts unaffected. Crosslink: [[Open item]] for re-run with MIN_TEXT_LEN=5 if reviewer asks.

### Recalc #3 — Phase 4.5 LEMMA-CV (session 19, AWS ~2h 10min)

**Trigger**: Locked since session 14 ($3, 3h). Required for Table 9 / `tab:graphsub` 4.5b + 4.5c cells.

**Result**: PATH 4 outcome. **Ceiling effect: no-graph = with-graph = 100%** across all 5 folds (n=80). 4.5c never ran due to D-17 JSON-serialization crash.

**Files**: `exp_4_5b_summary.json` (757B valid), per-case JSONLs (0B — D-17 loss), `_failed_run_log.txt` (forensic).

**Numerical impact on paper**: §5.8 Graph Sub-experiment subsection DROPPED (Decision 4). Content absorbed into §6.2 Limitations + §6.3 Future Work. Headline numbers unchanged (graph-RAG value rests on heterogeneous-distribution Δ=−1.1pp p=0.289 NS from ablation_with_graph).

### Recalc #4 — Table 4 14B row refit n=213 (session 23)

**Trigger**: Audit CRIT-B1 (Table 4 14B shows n=180 RCA-only but footnote claimed n=431).

**Recomputed from**: `main_benchmark/results.json` per-record `inference_latency_ms` (RTT 1.10ms subtracted) for `task_type in {rca, qa_mcq}`.

| Cell | Old (n=180 RCA-only) | New (n=213 rca+qa_mcq) | Source verified |
|---|---|---|---|
| P50 | 30.72 | **29.83** | ✓ |
| P95 | 59.38 | **62.20** | ✓ |
| Avg | 32.19 | **32.50** | ✓ |
| Range max | 84.50 | **84.50** | ✓ |
| Range min | 11.55 | **11.55** | ✓ |

Footnote rewritten to disclose 4B n=218, 14B n=213, E2E n=431 separately.

### Recalc #5 — CRIT-C2 flip 3 cases (session 23)

**Trigger**: Audit CRIT-C2 (3 qa_mcq cases RM_016/022/032 carry `correct=True/False` instead of null; null_count was 71 not 74).

**Script**: `benchmark/scripts/_dev/flip_qa_mcq_correct_to_null.py` (atomic write + fsync).

**Files mutated** (13): 9 matched-eval + 2 SOTA + 2 no-prompt. Flipped 39 cells (3 IDs × 13 files).

**Headline impact**: Zero (headline Ann/RCA counts match SUMMARY.md exactly). Only methodological invariant restored (null_count 71→74 in every file).

### Recalc #6 — Group C auditor-4 I2 (session 24)

**Trigger**: Auditor-4 finding M-5 (D-1 re-label not applied to 8 rich-eval `results.json`).

**Script**: `benchmark/scripts/_dev/group_c_relabel_d1_rich_and_header.py`.

**Mutation**: 264 task_type flips (33 OpsEval-remined IDs × 8 ablation rich-eval files). Plus `benchmark_431_seed42.json` header `rca_cases: 213→180, qa_mcq_cases: 33`.

**Impact on paper**: zero (matched-eval canonical; rich-eval not cited in paper body).

### Recalc #7 — Group C M-6 SUMMARY.md rich-eval correction (session 24)

**Trigger**: Audit M-6 (SUMMARY.md:21 said rich-eval RCA 92.5%, actual 91.1%).

**Mutation**: SUMMARY.md:21 rich-eval RCA 92.5%→91.1%, Overall 87.5%→86.4% (post-D-1 denominator 180/398).

### Recalc #8 — Path B'' Tier 1 peng year (session 26)

**Trigger**: CrossRef API lookup bonus finding (peng `year="2025"` in bib but CrossRef says ACM TOIS publication is 2026).

**Mutation**: `sn-bibliography.bib` peng entry `year` 2025 → 2026. Both PDFs +2 B (digit re-render). Page count unchanged.

---

## §5. Errors caught and slipped

### §5.1 Errors caught in same session (bug-history numbered + D-series)

| Bug ID | Session caught | What | How |
|---|---|---|---|
| #1 | Session 6 | argparse `--rca 0` ignored | `if 0:` → False; changed default to None |
| #2 | Session 7 | 71 excluded RCA evaluated as wrong | Script now inlines null records for excluded |
| #3 | Session 7 | Summary denominator wrong (198 not 127) | Use `len(rca_eval)` denominator |
| #4 | Session 8 | **CRITICAL** model_router config caching → identical accuracy across ablation configs | Replace bound config name with dynamic module attribute |
| #5 | Session 8 | fast_annotator confidence type | (BUG_HISTORY #5) |
| #6 | Session 8 | runner.py missing ablation flags | (BUG_HISTORY #6) |
| #7 | Session 8 | hardcoded temperature | Added `--temperature` flag |
| #8 | Session 8 | AWS EBS full → BERTScore zeros | Resized 40→80 GB; D-6 recompute deferred to s18 |
| D-13 | Session 16 | `Neo4jClient.run_query` doesn't exist | Patched 3 calls + try/finally |
| D-14 | Session 17 | `--dataset` default path wrong on instance | Added backward-compat fallback |
| D-15 | Session 17 | temp file list vs dict | Wrap with `{"test_cases": cases}` |
| D-17 / Bug #9 | Session 19 | `json.dumps(TestCaseResult)` → TypeError | Patched in session 20 via `dataclasses.asdict + default=str` |

### §5.2 Errors slipped (caught in later session)

| Error | Slipped from | Caught in | Description |
|---|---|---|---|
| D-1 OpsEval-judge silent fallback | Sessions 1-11 (Bedrock pivot era) | Session 16 + s17 spot-check | 33 MCQ-style cases over-included as DIAGNOSTIC by Qwen3-4B-Instruct fallback judge |
| D-2 OpenSSH 50% claim | Sessions 1-11 | Session 16 (validated session 17) | All 20 errors are FPs / zero FNs — never validated against ground truth |
| D-3 Bedrock pivot Anthropic→DeepSeek+Llama | Sessions 1-11 | Session 16 | Substitution forced by payment block, undocumented in METHODOLOGY |
| D-4 L5307 fake-graph-context invalidation | Pre-session 12 | Session 16 | Replaced fake mock data; all pre-existing with-graph smoke archived results silently invalidated |
| D-5 AWS Budgets never created | Pre-session 12 | Session 16 | $47/$120 figure is CE-derived; no Budgets resource with auto-stop |
| D-6 BERT-F1 zeros | Session 8 (bug #8) | Session 16 (audit) → session 17 (locked) → session 18 (recompute) | All 431 records bert_f1=0.0 due to disk-full bug |
| D-7 test_5plus5.py 499 ref | Sessions 1-11 | Session 16 + transcript audit s12 (FULL_TRANSCRIPT_AUDIT:399) | Hardcoded reference to deleted dataset |
| D-9 HANDOFF.md §6↔§14 self-contradictions | Pre-session 12 | Session 16 | §6 says Phase 4.4+4.7 COMPLETE; §14 says NOT STARTED |
| D-13 `exp_4_5c` `Neo4jClient.run_query` | Session 14 (committed in Stage J without ever being executed) | Session 16 (first Phase 4.5 launch attempt) | Stub-script never-run bug class |
| D-16 dataclass `r.get` | Sessions 14-16 | Session 17 (3rd Phase 4.5 launch crash) | Same script Stage-J reorg surfaced this only at runtime |
| D-17 dataclass JSON-serialize | Session 14-18 | Session 19 (post-Phase-4.5-fold-1 crash) | Sister bug to D-16 (attr-access vs file-write halves of same dataclass) |
| All 10 CRITICAL audit findings | Sessions 14-21 paper rebuild | Session 22 (5-agent audit) | Body Tables 2-7 correct but Abstract/§1/§2 still v1 numbers; HANDOFF.md drift |
| C-C2 71-vs-74 disparity | Session 17/18 D-1 application | Session 22 | 3 of 33 qa_mcq cases had `correct=True/False` instead of null |
| 9 bib metadata errors (4 entries) | Sessions 11-21 (paper rebuild bib additions) | Session 27 (Stage 1b PDF verification) | miller/notaro/wu/chen-automap had wrong author/title/year/venue |
| 8 NEW bib metadata errors (8 entries) | Sessions 11-21 | Session 28 Stage 1c | adaspec/askell/chen-rcagent/li-opseval/liu-logeval/pei-foa/shi-aiopslabs/xu-openrca had wrong first-author or title |
| zhang2024aiopssurvey first author wrong | Sessions 14-22 (when added) | Session 25 (WebSearch + DBLP) | Bib had "Zhang, Yongqian" — actual is Lingzhe Zhang |
| nvidia2024specdec wrong title | Sessions 14-22 | Session 25 (WebFetch NVIDIA blog) | Title was not verbatim of any NVIDIA blog post |
| peng year arXiv vs journal | Sessions 14-25 | Session 26 (CrossRef API) | bib had 2025 (arXiv); journal published 2026 |

---

## §6. Contradictions across sessions

### Contradiction 1: HANDOFF.md §6 vs §14 (Phase 4.4 + 4.7 status)
- **Source**: `HANDOFF.md:236` says `"Phase 4.4 ✅ COMPLETE"`, `HANDOFF.md:530` says `"❌ NOT STARTED"`. Same pattern for Phase 4.7.
- **Surfaced**: Session 16 (Conflict-1 / Conflict-2 in lost checklist).
- **Resolved**: Session 23 commit `61ca91f` (HANDOFF §7 fix as part of CRIT-D1).
- **Reversal-without-rationale**: NO. Was internal stale text; §14 was simply not updated when Phase 4.4 + 4.7 actually completed (pre-session 12).

### Contradiction 2: HANDOFF.md §7 ablation drift vs paper / SUMMARY (5 cells)
- **Source**: Session 22 audit CRIT-D1. HANDOFF.md §7 (just-rewritten session 22) had 5 ablation rows + 2 SOTA Overall cells drift on Single-4B (82.9% vs 82.6%), Single-14B (83.5 vs 83.8), No-constitutional (82.6 vs 82.9), No-system-prompt (60.8 vs 61.3), with-graph (RCA 83.5pp ok rest off), Llama Overall (83.3 vs 83.5), DeepSeek Overall (81.1 vs 81.2). Plus Full-Hybrid Ann typo (84.4→83.0 discovered s23).
- **Root cause**: When HANDOFF.md was rewritten session 22 (post-reorg), numbers were typed by approximation rather than copy-paste from `phase5_stats.md`.
- **Resolved**: Session 23 commit `61ca91f`.

### Contradiction 3: D-1 "74 excluded" vs only 71 actually null in result files (CRIT-C2)
- **Source**: Audit CRIT-C2. Paper claimed 74 excluded but 30 of 33 qa_mcq had `correct=null`; 3 (RM_016/022/032) had True/False (got through because freeform output substring-matched MCQ option).
- **Surfaced**: Session 22 audit.
- **Resolved**: Session 23 commit `7998393` (flip script).

### Contradiction 4: with-graph delta rounding (Tables 5+6 vs phase5_stats)
- **Source**: Paper Tables 5/6 say `−2.1pp`, phase5_stats says `−2.1582…` (rounds to −2.2pp). 0.1pp inconsistency.
- **Surfaced**: Session 22 audit I-6.
- **Resolved**: Session 24 (Tables 5 + 6 changed to −2.2pp at 2 sites).

### Contradiction 5: §484 "deferred to camera-ready supplementary" vs Table 4 right below it
- **Source**: Sandbox `.tex:484` said "Numerical breakdowns are deferred to the camera-ready supplementary tables" but Table 4 (`tab:errortable`) at lines 491-508 had those exact breakdowns.
- **Surfaced**: Session 25 inspection-only pass (audit-IMPORTANT).
- **Resolved**: Session 25 (changed to "Table~\ref{tab:errortable} below disaggregates by source.").

### Contradiction 6: Variance footnote "5 cases" vs actual 6 cases (1 ann + 5 rca)
- **Source**: Ablation Full RCA 119/139 = 85.6% (-1pp from main RCA 114/139 = 82.0%; not "5 cases" of difference). Discrepancy = 5 RCA + 1 ann.
- **Surfaced**: Session 22 audit I-9.
- **Resolved**: Session 24 (3 sites updated to "6 cases (1 ann + 5 RCA)").

### Contradiction 7: SUMMARY.md:21 rich-eval RCA 92.5% vs actual 91.1%
- **Source**: SUMMARY.md was not updated with post-D-1 rich-eval denominators.
- **Surfaced**: Session 22 audit M-6.
- **Resolved**: Session 24 (`881ad20` commit).

### Same item-ID disambiguation

The id-naming has been consistent. One area of mild overlap:
- **`I-A/B/C/D/E`** (session 22) refer to bib-and-prose items (I-A peng, I-B zhang, I-C nvidia, I-D bib header, I-E §484 contradiction). These are NOT to be confused with **`Auditor-4 I2`** which is a separate finding in session-22's audit report #4 about rich-eval files.
- **`B-4`** = variance footnote (locked s17). Distinct from session-22's grouping label **Group B** (8 should-fix items).

---

## §7. Open items (carried into session 28+)

Cross-referenced with §3 lifecycle index + Stage 1b §13 + Stage 1c §3.

### CRITICAL — must close before camera-ready submission (camera-ready already drafted; these are pre-submit polish)

1. **9 Stage-1b bib metadata errors** (4 entries) — `miller2025bootstrap` (4 fields), `notaro2021aiopssurvey` (1 field), `wu2020microrank` (2 fields), `chen2022automap` (2 fields). Apply as one themed bib commit in edit-phase. Cite keys stay as stable labels.
2. **8 Stage-1c NEW bib metadata errors** (8 entries) — `adaspec2025`, `askell2024collective`, `chen2024rcagent`, `li2024opseval`, `liu2025logeval`, `pei2025flowofaction`, `shi2025aiopslabs`, `xu2025openrca`. Some affect cite renderings in paper body. Apply as second themed bib commit.
3. **chen2024autonomous placeholder cite** — bib has no DOI/arXiv. **DECISION REQUIRED**: (a) find real reference, (b) substitute, (c) remove `\cite{}` from `.tex`.
4. **notaro2021aiopssurvey paywalled** — sci-hub doesn't have it; real DOI unconfirmed. **DECISION REQUIRED**: institutional access fetch + DOI verification + journal field correction.
5. **Gate 16 + Gate 17 (session 27 close-out)** — PENDING per session 27 handoff. This handoff (this file) + manifest §14 retry-2 + benchmark/HANDOFF.md update + MEMORY.md + reference_session28_starter_prompt.md need to be committed (Gate 16) + pushed (Gate 17). User GO required for each.

### IMPORTANT — should close but not blocking

6. **3 sci-hub-sourced PDFs** (`parasuraman2000model`, `wu2020microrank`, `chen2022automap`) — protocol drift from plan-authorized Anna's Archive. **DECISION REQUIRED**: keep (substantively-equivalent shadow lib) or replace via institutional access.
7. **Path B'' Tier 2: peng + zhang vol/issue/pages** — DEFERRED s24/s26 (DOI alone sufficient; 30-50% chance of 17p overshoot if added). Revisit only if reviewer flags.
8. **Stages 2-6 of the multi-agent verification plan** — Pair A (Stages 2 + 3) + Pair B (Stages 4 + 5) + Stage 6 sequenced for session 28 per session 27 handoff. Stage 2 = DIFF parity (this Stage 3 = audit history timeline = self-reflexive); Stage 4 = paper-claim ↔ benchmark cross-verification; Stage 5 = benchmark-dir analysis + ≥2 alternative topologies; Stage 6 = final synthesis.
9. **Cite-key renames** (Path B'' Tier 3): `zhang2024→zhang2026`, `nvidia2024→nvidia2025`, `peng2025→peng2026`. Cosmetic; reviewer-flag-only justified.
10. **xlsx update** — Stage 1a draft CSV `01_xlsx_delta_proposal.csv` not yet applied to the live xlsx. Coordinated pass after all stages close.

### DEFERRED — out of scope unless reviewer demands

- **Path D — Stack B full 431-case latency re-run** (~$5, ~3h) — only if reviewer asks
- **Path D — Phase 4.5c cold-start curve** (~$5, ~5h; D-17 patched on laptop; instance needs scp `src/memory/` first)
- **Path G — Submit camera-ready** — pending COMSYS 2026 CFP open. Submission file IS `main/sn-article.pdf` (16p, 467,673 B, SHA-256 `be6c27ab…d9483`).
- **BERT-F1 recompute with MIN_TEXT_LEN=5** — to fill the `ablation_no_system_prompt` Ann n=1 + `ablation_with_graph` Ann n=0 cells (D-6 known artifact carry-forward).
- **M-3 pre-D-1 `excluded_rca_cases.json`** — legacy file on disk; described as legacy in METHODOLOGY; could delete or archive.
- **M-4 stale `main_benchmark/summary.json`** — byte-identical to `benchmark_result.json` with pre-D-1 rich-eval numbers; not cited in paper; could delete.
- **Abstract / §1 tone polish** — user locked sessions 25+ "preserve as-accepted; correct only if factual error surfaces". None found across sessions 25-27.

---

## §8. SCP / path / file incidents

### SCP-1: Instance src/ outdated (sessions 16-19)
- `Neo4jClient.find_similar_episodes_by_embedding` exists on laptop (line 747 of `src/memory/neo4j_client.py`) but NOT on instance (last updated session 9-10).
- **Impact**: Phase 4.5 with-graph mode silently fails with `'Neo4jClient' object has no attribute 'find_similar_episodes_by_embedding'` warning loop → with-graph results identical to without-graph (no context injected).
- **Resolution**: Session 19 chose PATH 2 (re-clone instance from origin/main) + scp src/. Smoke-tested clean.
- **Carry-forward rule**: Instance has NO git — always scp. Instance `src/` is OUTDATED unless explicitly re-cloned.

### SCP-2: D-14 dataset path discrepancy (session 17)
- Script default `--dataset` was `benchmark/intermediate/datasets/benchmark_431_seed42.json` (post-Stage-B reorg path on laptop). Instance had pre-reorg `benchmark/datasets/processed/`.
- **Resolution**: Backward-compat fallback added in `load_lemma_cases()`.

### SCP-3: D-17 patch local-only (session 20)
- `run_graph_experiments.py` updated on laptop; instance copy at `/mnt/aiops-repo/...` still buggy.
- **Rule 22 (s20)**: Re-SCP only if re-running Phase 4.5.

### Path-1: Stage J path-depth fixes (sessions 13-14)
- 33 `git mv` operations of `benchmark/scripts/` into 5 sub-dirs broke 27 path-depth `Path(__file__).parent.parent.parent`-style expressions.
- Session 13: 11 Edit calls FAILED because git-mv invalidated Read-tool cache.
- Session 14: bulk-edit strategy worked; rollback after substring-collision bug (`parent.parent` substring of `parent.parent.parent`); 5/5 verification PASSED.

### Path-2: Real paper moved to z.Dump (session 22)
- User moved `sn-article-template.v2/` to `z.Dump Paper Archive/` mid-session 22.
- **Rule 4** locked: NEVER touch real `sn-article-template.v2/` (gone). Sandbox `main/sn-article.tex` IS the canonical edit target.

### File-1: PowerShell `:` parsing in filenames (session 22)
- `_session11_phase4_*.txt` files (mangled C:Users... names from Windows backslash stripping) couldn't be moved via PowerShell Move-Item.
- **Workaround**: bash `mv` (rule 10).

### File-2: PowerShell `>` UTF-16 BOM (session 22)
- Default `>` redirect produces UTF-16 LE with BOM, breaks LaTeX compilation when feeding `.tex` content.
- **Workaround**: `[System.IO.File]::WriteAllText` with `New-Object System.Text.UTF8Encoding $false` OR Python `pathlib.Path.write_text(..., newline="\n")` (rule 11).

### File-3: CRLF + listings v1.11b incompatibility (session 24)
- DIFF regen via `regen_diff_pdf.py` crashed with "Paragraph ended before `\lst@DefDriver@@` was complete" inside `\lstdefinelanguage{json}` because Python's `Path.write_text()` wrote CRLF on Windows.
- **Fix encoded in script**: pass `newline="\n"` to all `write_text()` calls + drop listings dep entirely (DIFverbatim unused in body).
- Combined with: (a) Git for Windows perl.exe on PATH; (b) LF write; (c) listings drop. All three encoded in `regen_diff_pdf.py` (rule 18).

### File-4: latexdiff vs soul `\hl{}` breaks on `\cite{}` (sessions 21-22)
- Session 21 attempt to use `\sethlcolor{yellow}\hl{#1}` override for DIFF additions failed with `! Argument of \@citex has an extra }` at line 449 because soul's `\hl{}` breaks on `\cite{}` inside additions.
- **Workaround**: `\textcolor{red!75!black}{#1}` override (no bold; bold widens text → 17p regression).

### File-5: Sandbox folder reorg (session 22)
- Sandbox-session16 split into `main/` + `diff/` subfolders per user request (Option 2 of 3).
- All path references updated. Real `sn-article-template.v2/` moved to `z.Dump`.

### File-6: Reference PDFs (sessions 27)
- 24 new PDFs landed in `REFERENCE PAPERS/` (13.7 MB → 71 MB).
- 3 of 24 from sci-hub (Anna's blocked in this env).
- 9 bib metadata errors discovered during first-page-verify pass.

### File-7: Anna's Archive DNS/DPI block (session 27)
- `annas-archive.{org,se,li,gs}` all blocked. Sci-hub.ee → sci.bban.top CDN works as fallback. Disclosed in manifest as protocol drift.

---

## §9. Patterns / lessons learned

### Pattern 1: V1 paper text preserved while body updated (sessions 14-22)
- Sessions 14-21 focused edits on §5 Results + §6 Discussion + §7 Conclusion (where reviewer concerns landed).
- Abstract + §1 + §2 + RG1-2 left as v1 text until session 22 audit caught it.
- **Lesson**: front-matter is the most-read paragraph; never leave it stale.

### Pattern 2: Stub scripts committed without ever running (D-13/D-16/D-17 class)
- `run_graph_experiments.py` was added in Stage J (session 14) and committed without execution.
- 4 separate runtime bugs (D-13/14/15/16) surfaced when Phase 4.5 launch first attempted.
- D-17 surfaced AFTER Phase 4.5 ran (post-loop JSON-serialize crash).
- **Lesson**: write a smoke test for any script that has long-running outer loops + file I/O outside its main loop.

### Pattern 3: latexdiff misrenders (sessions 21-22)
- 4 different `--type` settings tried before INVISIBLE + `\textcolor` override worked.
- soul's `\hl{}` breaks on `\cite{}`. BOLD widens text. CFONT breaks emph. UNDERLINE breaks tables.
- **Lesson encoded in `regen_diff_pdf.py`**: use INVISIBLE + custom `\providecommand{\DIFadd}[1]{{\protect\color{red!75!black}#1}}` + LF write + listings drop + Perl on PATH.

### Pattern 4: PowerShell encoding gotchas (sessions 14, 22, 24)
- UTF-16 LE BOM on `>` redirect.
- `:` parsing in filenames requires bash mv.
- CRLF default breaks `lstdefinelanguage{json}` in listings v1.11b.
- **Lesson**: always pass `encoding='utf-8'` to Python `open()` + `newline="\n"` to `write_text()`. Reading non-ASCII result files from Windows shell crashes on cp1252 default.

### Pattern 5: Min-viable bib rule (session 25)
- Each added bib field expands rendered entry by ~30 chars × 80-cols, which compounds across multiple entries and can push the PDF over 16p.
- DOI alone is most reviewer-actionable single identifier — vol/issue/pages derivable via DOI lookup.
- **Lesson**: default to min-viable when adding bib metadata.

### Pattern 6: Cite-key as stable label (sessions 24-26)
- `zhang2024aiopssurvey` cite key retained despite year 2026 in entry.
- `nvidia2024specdec` cite key retained despite year 2025 in entry.
- `peng2025graphragsurvey` cite key retained despite year 2026.
- **Lesson**: cite keys are stable identifiers across `\cite{}` sites; renames require updates at all sites; year discrepancy is acceptable when key tracks the preprint era while entry tracks the journal era. Rename only if reviewer flags.

### Pattern 7: CrossRef REST API workaround (session 26)
- dl.acm.org WebFetch returns HTTP 403 (ACM blocks bots).
- `https://api.crossref.org/works/<DOI>` works directly via curl — no auth needed for public lookups, returns structured JSON.
- CrossRef is authoritative for publication year (arXiv preprint year may differ).

### Pattern 8: No submission "package" folders (session 26)
- Camera-ready submission package built s26 contained pure duplicates of live main/diff PDFs.
- Submit `main/sn-article.pdf` directly. SHA-256 provenance preserved in handoff doc.
- **Lesson**: avoid redundant artifact copies; document SHA-256 in audit doc instead.

### Pattern 9: First-page-verify downloaded PDFs (session 27)
- Stage 1a URL-guessing had ~14% error rate; title-substring matching alone too weak (e.g., "Bootstrap" matched 3 unrelated papers).
- Stage 1b's 5-point verification missed some errors caught by user spot-check.
- Stage 1c independent agent surfaced 8 NEW bib metadata errors beyond Stage 1b's 9.
- **Lesson**: ALWAYS first-page-verify a downloaded PDF before trusting bib metadata. Multiple-agent independent verification adds defense-in-depth.

### Pattern 10: Anna's Archive blocked, sci-hub.ee works (session 27)
- 4 Anna's domains all DNS/DPI-blocked in this env.
- sci-hub.ee → sci.bban.top CDN works as substantively-equivalent shadow lib.
- **Disclose in manifest** as protocol drift.

### Pattern 11: Sister-bug architecture (D-13/D-14/D-15/D-16/D-17 cluster)
- D-13: `Neo4jClient.run_query` doesn't exist (s16).
- D-14: `--dataset` default path wrong on instance (s17).
- D-15: temp file list vs dict (s17).
- D-16: `r.get("correct")` on dataclass (s17 discovered, s18 patched).
- D-17: `json.dumps(TestCaseResult)` not serializable (s19 discovered, s20 patched) — sister to D-16 (attr-access vs file-write halves).
- **Lesson**: when one bug is found in a script, audit the script for adjacent same-class issues.

### Pattern 12: Audit-driven fix cycle (sessions 22-25)
- Session 22: 5-agent parallel audit → 10 CRITICAL + 14 IMPORTANT + 7 MINOR findings.
- Session 23: Group A (10 CRITICAL) closed.
- Session 24: Group B (10 should-fix) + Group C (5 polish) closed.
- Session 25: Path C camera-ready prep + I-E + I-A/B/C deferred items closed.
- Session 26: Path B'' Tier 1 (peng year fix) closed via CrossRef bonus finding.
- Session 27: multi-agent verification pass restarted (Stages 1a/1b/1c — found NEW errors).
- **Lesson**: defense-in-depth multi-agent audits surface drift that single-agent passes miss.

---

*End of timeline. Cross-link companion: `05_open_items_checklist.md`.*
