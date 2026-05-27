# Session 28 → Session 29 Handoff (2026-05-27)

> **PRIMARY ENTRY POINT for session 29**. Session 28 ran the second half of the multi-agent paper verification: Stage 1c (NEW per user request, PDF content re-verification) + Pair A (Stage 2 DIFF parity + Stage 3 audit history) + Pair B (Stage 4 paper claim cross-verification + Stage 5 benchmark topology). 5 themed commits landed locally (Gates 18-22); Gate 23 close-out + Gate 24 batched push pending USER GO. Stage 6 final synthesis + edit-phase deferred to session 29. Sandbox PDFs preserved at 16p / unchanged SHA-256. AWS untouched.

---

## §0. One-line state

5 of 6 verification stages COMPLETE this session (1c + 2 + 3 + 4 + 5). Camera-ready verdict: **GO on numerics + DIFF parity** (Stage 4 GO, Stage 2 YELLOW-acceptable); **FIX-NEEDED on bib metadata** (Stage 1c surfaced 16 NEW field-level errors across 10 entries on top of Stage 1b's 9 — total **24 bib field-level corrections across 14 entries** for edit-phase). 5 commits ahead of origin pending Gate 24 batched push (Gates 18-23). Stage 6 final synthesis is session 29's first action.

---

## §1. What happened this session (chronological)

1. **Session 28 start**: state-verify confirmed clean carry from session 27 close (HEAD `6aee747`, sandbox PDFs at known SHA-256, 32 PDFs in REFERENCE PAPERS/, AWS stopped).
2. **Stage 1c launched** (general-purpose, ~35 min): independent re-verification of all 29 downloaded PDFs against bib metadata via `pdftotext -l 3`. Per-PDF status: MATCH / PARTIAL / KNOWN_BIB_ERROR (confirms Stage 1b §9) / NEW_BIB_ERROR / UNREADABLE / TAMPER_DETECTED.
3. **Stage 1c findings**: 7 MATCH + 11 PARTIAL + 3 KNOWN_BIB_ERROR (confirms miller/wu/chen-automap) + 8 NEW_BIB_ERROR (NEW Stage 1c discoveries on top of Stage 1b's catalog). 24/24 newly-downloaded PDFs SHA-256 match manifest §4 exactly. 0 UNREADABLE. 0 TAMPER_DETECTED.
4. **Spot-checked 4 critical Stage 1c claims** via pdftotext on actual PDFs: chen2024rcagent (lead is Wang, not Chen ✓), shi2025aiopslabs (lead is Chen, not Shi ✓), askell2024collective (lead is Huang, not Askell ✓), bansal2021does (title says "Explanations" not "Confidence" ✓). All 4 confirmed.
5. **Gate 18 commit** (`b88590c`): Stage 1c report.
6. **Pair A launched** (2 parallel agents, single message): Stage 2 (DIFF parity v1↔sandbox↔DIFF, text + all-16-pages visual) + Stage 3 (audit history timeline + open items checklist).
7. **Stage 2 result** (~25 min): VERDICT YELLOW (acceptable for camera-ready). 0 false-negatives + 0 false-positives in strict sense. All 23 cumulative session-23..26 paper edits verified present in sandbox AND marked in DIFF. 32 PNGs (all 16 page-pairs) read successfully via pdftoppm at 150 dpi. 3 inherent latexdiff caveats documented (not bugs): bib edits invisible in body / deletions suppressed deliberately / TikZ rewrapped wholesale. No paper-body edits needed.
8. **Stage 3 result** (~35 min, 2 output files): ~700-line chronological timeline tracking ~60 decision IDs (D-1..17, Conflicts 1-5, M-1..7, I-2..E, Paths A..G, Tier1-3). 8 recalcs + 7 cross-session contradictions + 12 patterns aggregated. All session-22 audit findings (10 CRITICAL + 14 IMPORTANT + 7 MINOR) fully closed by session 25. Companion checklist: 20 CRITICAL + 5 IMPORTANT + 5 NICE-TO-HAVE + 4 DEFERRED items (with 4 stale flags for Items 14-17 that reflect pre-Gate-18 state — to be reconciled in Stage 6).
9. **Gates 19 + 20 commits** (`9110ec9` + `4225a91`): Stage 2 + Stage 3 reports. _artifacts/ 32-PNG dir intentionally NOT committed (reproducible via pdftoppm).
10. **Pair B launched** (2 parallel agents, single message): Stage 4 (paper claim ↔ benchmark cross-verification) + Stage 5 (benchmark topology analysis + ≥2 alternative topologies).
11. **Stage 4 result** (~25 min): VERDICT GO. 91/~94 cells GREEN within strict tolerance (≤0.05pp / ≤0.5s / ≤1e-3). 0 RED. 3 YELLOW — all already disclosed/defended in-paper (Y1 Fig 3 7-vs-8 bars; Y2 §6.2 P95 48.4 vs 48.57 within tolerance; Y3 BERT-F1 column scope per D-6 Option C). ZERO regressions vs session-22 baseline. All 6 CRITICAL + 6 IMPORTANT items resolved in sessions 23-26.
12. **Stage 5 result** (~30 min): Walked benchmark/ live: ~505 files vs INDEX.md baseline 422 (+83 net). 188 path-shaped refs across 39 .py files mapped. 7 pain points catalogued (10 underscore-prefix orphans, 3 raw mirror JSONLs, results.json vs results_sota_eval_431.json ambiguity, naming drift, hardcoded paths, INDEX_BUILD_REPORT.md misplaced, scripts/README stale 34→43). 3 topology options proposed: A minimal-disturbance (recommended; 10 moves + 10 cleanup, LOW risk, ~30 min), B task-oriented (~250+ moves, HIGH risk), C flat-then-deep (13 moves, MEDIUM risk). Recommended split: 3 phased commits.
13. **Gates 21 + 22 commits** (`bc9f5ab` + `f57f69e`): Stage 4 + Stage 5 reports.
14. **User pivot mid-session**: requested wrap-up and continue Stage 6 next session.
15. **Session 28 ended** at this handoff write. Pending Gate 23 = close-out commit (this handoff + benchmark/HANDOFF.md + MEMORY.md + session-29 starter prompt). Pending Gate 24 = batched push of Gates 18+19+20+21+22+23 (6 commits).

---

## §2. What changed on disk in session 28

### Committed (Gates 18-22; HEAD `f57f69e`)

| Commit | File | Notes |
|---|---|---|
| `b88590c` (Gate 18) | `paper_audit_session27_2026-05-26/03_pdf_content_verification.md` (423 lines) | Stage 1c — independent PDF content verification |
| `9110ec9` (Gate 19) | `paper_audit_session27_2026-05-26/04_diff_parity_report.md` (184 lines) | Stage 2 — DIFF parity v1↔sandbox↔DIFF + all-16-pages visual |
| `4225a91` (Gate 20) | `paper_audit_session27_2026-05-26/05_audit_history_timeline.md` (~700 lines) + `05_open_items_checklist.md` (~180 lines) | Stage 3 — audit history + open items |
| `bc9f5ab` (Gate 21) | `paper_audit_session27_2026-05-26/06_claim_cross_verification.md` (387 lines) | Stage 4 — paper claim ↔ benchmark cross-verification |
| `f57f69e` (Gate 22) | `paper_audit_session27_2026-05-26/07_benchmark_topology_analysis.md` (629 lines) | Stage 5 — topology + 3 proposed options |

### Pending in Gate 23 (close-out)

| File | Status | Notes |
|---|---|---|
| `SESSION_28_HANDOFF.md` | NEW | this file |
| `benchmark/HANDOFF.md` | MODIFIED | Last-updated bumped session 27 close → session 28 close |
| `MEMORY.md` (auto-memory) | MODIFIED | SESSION 28 STARTUP → SESSION 29 STARTUP block |
| `reference_session29_starter_prompt.md` (auto-memory) | NEW | paste-in starter for session 29 |

### NOT committed (intentional)

- `paper_audit_session27_2026-05-26/_artifacts/` (32 PNGs from Stage 2 visual export, ~10-15 MB) — reproducible via pdftoppm command documented in Stage 2 report §1; deletable after Stage 6 review.

### Sandbox paper artifacts — UNCHANGED (session 28 was read-only on paper)

| File | Size | SHA-256 |
|---|---|---|
| `main/sn-article.pdf` | 467,673 B / 16p | `be6c27abb2dcbdc23a0161c0926266bc18312db4c0a9660c289e1e06f78d9483` |
| `diff/sn-article-DIFF.pdf` | 469,231 B / 16p | `ed09349db0479ae7562e5e0709e5d21f50401e974ab8d7947de9e1d408c02d67` |

### AWS state at close (UNCHANGED from sessions 20-27)

Instance stopped, CW alarm armed, EIP retained, EBS preserved, snapshot held, ~$55/$120 spend. NO AWS work in session 28 — all read-only on benchmark/paper artifacts.

### Git state at close (pre-Gate-23)

- Local HEAD: `f57f69e` (post-Gate-22)
- Origin HEAD: `6aee747` (post-session-27 close-out push)
- Branch: `main`
- Working tree: 32-PNG `_artifacts/` dir untracked (intentional); soon-to-add Gate-23 close-out files
- Pending Gate 23: bundle all close-out file changes into one commit
- Pending Gate 24 push: Gates 18+19+20+21+22+23 (6 commits batched) to origin/main (separate USER GO)

---

## §3. Consolidated verification findings (Stage 1c + 2 + 3 + 4 + 5)

### §3.1 Stage 1c — PDF content verification

29 PDFs verified. Distribution:

| Status | Count | Bib keys |
|---|---:|---|
| MATCH (all 4 fields verified) | 7 | bai2022constitutional, bertscore2020, christakopoulou2024talker, edge2024graphrag, guo2017calibration, parasuraman2000model, zhang2020effect |
| PARTIAL (3 of 4 fields OK; missing non-critical) | 11 | alibaba2024qwen, cncf2024survey, lemma2024rca, lewis2020retrieval, peng2025graphragsurvey, reimers2019sentence, thakur2021beir, zhang2024aiopssurvey, zhu2023loghub, plus arigraph2024 + bansal2021does (also have NEW errors flagged separately) |
| KNOWN_BIB_ERROR (Stage 1b §9 confirmed) | 3 | chen2022automap, miller2025bootstrap, wu2020microrank |
| **NEW_BIB_ERROR (Stage 1c NEW findings)** | **8** | adaspec2025, askell2024collective, chen2024rcagent, li2024opseval, liu2025logeval, pei2025flowofaction, shi2025aiopslabs, xu2025openrca |
| UNREADABLE | 0 | — |
| TAMPER_DETECTED | 0 | — |

**24/24 newly-downloaded PDFs SHA-256 match Stage 1b manifest §4 exactly. 0 tampering detected.**

### §3.2 🔴 Cumulative bib metadata error catalog (24 field-level edits across 14 entries)

**Confirmed (Stage 1b §9, validated by Stage 1c):**

| bib_key | Field-level errors |
|---|---:|
| `miller2025bootstrap` | 4 (author + title + year + arXiv) |
| `wu2020microrank` | 1 (author — year already 2021 in bib per Stage 1c §3.24; Stage 1b §9 Q5 over-stated) |
| `chen2022automap` | 2 (author + year) |
| `notaro2021aiopssurvey` | 1 (journal field — DOI also unresolved; needs manual user fetch) |

**NEW (Stage 1c §5):**

| bib_key | Field-level errors | Severity |
|---|---:|---|
| `chen2024rcagent` | 1 author block (all 3 listed wrong; lead is Wang, not Chen — surname Chen absent from paper) | **CRITICAL** |
| `shi2025aiopslabs` | 3 (lead surname + 2nd author + title subtitle; lead is Chen, not Shi — reverses Stage 1a §7 Q5) | **CRITICAL** |
| `li2024opseval` | 2 (all 4 listed authors wrong + title subtitle; lead is Liu, not Li) | **CRITICAL** |
| `liu2025logeval` | 1 author block (all 3 listed wrong; lead is Cui, not Liu) | **CRITICAL** |
| `xu2025openrca` | 2 (lead first-name + 2nd/3rd authors wrong + title is paraphrase) | **CRITICAL** |
| `adaspec2025` | 1 (lead author Zhang Hao → Kaiyu Huang) | HIGH |
| `askell2024collective` | 1 (lead author Askell → Huang) | HIGH |
| `pei2025flowofaction` | 2 (lead first-name + 2nd/3rd authors + title subtitle) | HIGH |
| `bansal2021does` | 1 (title: "Confidence" → "Explanations") | HIGH |
| `arigraph2024` | 2 (2nd + 3rd authors) | MEDIUM |

**Total: 24 field-level corrections across 14 entries** for edit-phase. Recommended batching (per Stage 3 + Stage 1c):
- **Batch A**: 3 entries / 7-8 fields (miller, wu, chen-automap) — Stage 1b §9 confirmed
- **Batch B**: 5 entries / ~15 fields (chen-rcagent, shi-aiopslabs, li-opseval, liu-logeval, xu-openrca) — CRITICAL
- **Batch C**: 5 entries / ~10 fields (adaspec, askell, bansal, pei-flowofaction, arigraph) — HIGH/MEDIUM
- **Manual fetch**: notaro2021aiopssurvey (DOI unresolved + paywalled, not in sci-hub) — user institutional access

### §3.3 Stage 2 — DIFF parity verdict YELLOW (acceptable)

- 0 false-negatives + 0 false-positives in strict latexdiff sense
- All 23 cumulative session-23..26 paper edits verified present in sandbox AND marked in DIFF
- All 16 page-pairs visually verified (32 PNGs at 150 dpi)
- 3 inherent latexdiff caveats (not bugs): bib edits don't show body highlights (only in compiled References pp.15-16) / deletions suppressed via `\providecommand{\DIFdel}[1]{}` per regen recipe / TikZ figures rewrapped wholesale (Figure 4 entirely red-tinted)
- After bib-batch edits in edit-phase, regen DIFF and spot-check pp.15-16 only

### §3.4 Stage 3 — Audit history timeline + checklist

- ~60 decision IDs tracked across sessions 12-27
- All session-22 audit findings (10 CRITICAL + 14 IMPORTANT + 7 MINOR) fully closed by session 25 ✓
- 8 recalcs documented (D-1 re-label, D-6 BERT, Phase 4.5 PATH 4, Table 4 14B n=213 refit, CRIT-C2 flip, Group C M-5/M-6, Tier-1 peng year)
- 7 cross-session contradictions surfaced
- Open items checklist: 20 CRITICAL + 5 IMPORTANT + 5 NICE-TO-HAVE + 4 DEFERRED
- **Reconciliation note**: 4 checklist items (Items 14-17) flag stages already completed (Gate 16+17 landed at session 27 close; Stages 2+3 just landed this session). Stage 6 to clean up.

### §3.5 Stage 4 — Paper claim cross-verification verdict GO

- 91 of ~94 cells GREEN within strict tolerance
- 0 RED
- 3 YELLOW — all pre-disclosed or defended in-paper:
  - **Y1**: Figure 3 displays 7 of 8 ablation configs (With-orchestrator collapsed because identical-on-357/357 to With-graph). Caption claims "7 configurations"; abstract says "8-configuration ablation". Optional polish: add caption clause.
  - **Y2**: §6.2 P95 48.4s (linear-interp) vs Table 4 48.57s (index-floor) — 0.17s gap within disclosed 0.3s tolerance. Optional polish: align to 48.6s OR add cross-pointer.
  - **Y3**: BERT-F1 column in Table 2 only; §5.2 prose carries 0.81 ± 0.01 headline. Matches locked D-6 Option C decision. Optional: per-config BERT-F1 in Tables 5/6/7 if Stage 5 finds layout room.
- ZERO regressions vs session-22 baseline
- 16p invariant preserved through sessions 23-26 fixes

### §3.6 Stage 5 — Benchmark topology Option A recommended

- ~505 files live vs INDEX.md baseline 422 (+83 net)
- 188 path-shaped refs across 39 .py files; highest-density scripts (potential reorg breakers): `_idx_build.py` (22), `recompute_bert_f1.py` (18), `_apply_d1_result_sync.py` (15), `archive_originals.py` (16), `flip_qa_mcq_correct_to_null.py` (13)
- 6 root-orphan scripts have **0 importers** — safe to move into `_dev/`
- 3 raw/ mirror JSONLs (apache/openssh/opseval candidates) byte-identical to intermediate/candidates/ — violate "raw=untouched" rule; recommend archive
- **RECOMMENDED**: Option A minimal-disturbance, 3 phased commits:
  - Commit 1: 6 root underscore-orphans → `_dev/` + scripts/README regen (34→43)
  - Commit 2: 3 raw mirrors → `archive/raw_pre_reorg_mirrors/` + INDEX.md §1 tally update + 3 README annotations
  - Commit 3 (optional, requires USER GO for sealed-tree adjacency): `INDEX_BUILD_REPORT.md` → `final/audit/SESSION_16_INDEX_BUILD_REPORT.md`
- 7 OPEN QUESTIONS deferred to user / Stage 6

---

## §4. Authoritative state for session 29

### Paths (UNCHANGED from session 27 close)

| Item | Path |
|---|---|
| Active paper `.tex` | `…sandbox-session16\main\sn-article.tex` (55,201 B / 789 LF lines) |
| Active paper `.pdf` | `…sandbox-session16\main\sn-article.pdf` (**16 pages / 467,673 B**) |
| Active paper `.bib` | `…sandbox-session16\main\sn-bibliography.bib` (10,129 B / 272 LF lines / 35 entries; 32 cited; 3 retained-orphan; **24 metadata errors across 14 entries pending edit-phase**) |
| DIFF `.tex` | `…sandbox-session16\diff\sn-article-DIFF.tex` (68,263 B / 830 LF lines) |
| DIFF `.pdf` | `…sandbox-session16\diff\sn-article-DIFF.pdf` (**16 pages / 469,231 B**) |
| v1 paper (READ-ONLY) | `…Final Submission Paper (Accepted v.1)\…\sn-article.tex` |
| OLD `sn-article-template.v2/` | MOVED to `z.Dump Paper Archive/` — do NOT touch |
| Reference PDFs | `…PAPER\REFERENCE PAPERS\` (32 PDFs at top level / 71 MB) |
| Project handoff | `constitutional-aiops/benchmark/HANDOFF.md` (Last-updated session 28 close) |
| Session-27 audit dir | `constitutional-aiops/benchmark/final/audit/paper_audit_session27_2026-05-26/` (8 .md + 1 .csv + _artifacts/{32 PNGs untracked}) |

### Numbers (UNCHANGED — session 28 was read-only on benchmark data)

All headline values from session 26-27 close remain valid:
- Main Overall **82.4%** (294/357), BCa CI [78.2, 86.0]
- RCA **82.0%** (114/139), Ann **82.6%** (180/218)
- Llama ΔRCA **+10.8pp** / DeepSeek ΔRCA **+15.1pp**
- Stack B speedup **1.51×**, Phase 4.5a McNemar p=0.289 NS
- All Stage 4 cells verified against authoritative sources

### Git

- Local HEAD `f57f69e` (Gate 22); origin still `6aee747`
- 5 commits ahead of origin (Gates 18-22)
- Gate 23 commit (this close-out) pending USER GO
- Gate 24 push (Gates 18+19+20+21+22+23 batched) pending USER GO at session close

### AWS

Stopped, CW alarm enabled, EIP retained, EBS preserved, snapshot held, ~$55/$120 spend.

---

## §5. Hard rules carried forward (UNCHANGED — 18 rules + 4 process lessons + 2 session-27 lessons; no NEW session-28 lessons)

Session 28 was a read-only verification phase; no new process lessons emerged. The 18 hard rules + 4 process lessons from session 27 §5 carry through unchanged. Key rules:

1. NO Claude co-author trailer on any commit
2. NO push without explicit USER GO
3. Paper edits target sandbox `main/sn-article.tex` (or `main/sn-bibliography.bib`) ONLY
4. NEVER touch real `sn-article-template.v2/` (moved to `z.Dump Paper Archive/`)
5. v1 paper is READ-ONLY reference
6. AWS stays stopped unless user GO; do NOT release EIP `44.195.172.165`; do NOT delete snapshot
7. 3-point rubric mentions at sandbox lines 447 + 597 are INTENTIONAL DISCLOSURES
8. DO NOT recompute D-1 or BERT-F1 (done sessions 17-18)
9. DIFF PDF override uses `\textcolor{red!75!black}{#1}`; regen via `regen_diff_pdf.py`
10. PowerShell `:` parsing in filenames → use bash `mv`
11. PowerShell `>` redirect → UTF-16 LE BOM; use `[System.IO.File]::WriteAllText` with `UTF8Encoding $false` or Python with `newline="\n"`
12. Ollama 0.23.2 ignores `enable_thinking=False`
13. Master backup zip sacred
14. `annotation_test.json` + `rca_test.json` dirty in local — do NOT commit content changes
15. Sealed forensic docs untouchable: CV_PASS1/2, FULL_TRANSCRIPT_AUDIT, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, all SESSION_12-28_HANDOFF.md
16. Instance has NO git — always scp
17. Instance `src/` is OUTDATED — `find_similar_episodes_by_embedding` missing
18. DIFF regen recipe encoded in `regen_diff_pdf.py`

Process lessons (informational, carried unchanged from session 27):
- Min-viable bib rule (session 25)
- CrossRef API for ACM works (session 26)
- Cite-key as stable label (sessions 24/25/26)
- No submission "package" folders (session 26 post-close)
- Session 27 #1: Stage-1a URL guessing ~14% error rate; first-page-verify all downloaded PDFs (validated again this session by Stage 1c finding 16 NEW errors)
- Session 27 #2: Anna's Archive blocked in this env; sci-hub.ee → sci.bban.top CDN works as fallback

---

## §6. Mandatory reads for session 29

1. **`MEMORY.md`** (auto-loaded — read SESSION 29 STARTUP block in full)
2. **`benchmark/final/audit/SESSION_28_HANDOFF.md`** ⭐⭐⭐ (THIS FILE — primary entry, ~400 lines)
3. **`benchmark/final/audit/paper_audit_session27_2026-05-26/03_pdf_content_verification.md`** (Stage 1c — 423 lines; CRITICAL — has the 16 NEW bib metadata errors with full evidence)
4. **`benchmark/final/audit/paper_audit_session27_2026-05-26/05_open_items_checklist.md`** (Stage 3 actionable checklist — 20 CRITICAL items; reconcile Items 14-17 stale flags)
5. **`benchmark/final/audit/paper_audit_session27_2026-05-26/06_claim_cross_verification.md`** (Stage 4 — 91/94 GREEN, 3 YELLOW polish items)
6. **`benchmark/final/audit/paper_audit_session27_2026-05-26/07_benchmark_topology_analysis.md`** (Stage 5 — Option A recommended, 3 phased commits)
7. **`benchmark/final/audit/paper_audit_session27_2026-05-26/05_audit_history_timeline.md`** (Stage 3 timeline — reference only)
8. **`benchmark/final/audit/paper_audit_session27_2026-05-26/04_diff_parity_report.md`** (Stage 2 — YELLOW verdict; useful for edit-phase regen verification)
9. **`benchmark/final/audit/SESSION_27_HANDOFF.md`** (session 27 context — Stage 1a + 1b — primary entry until this handoff supersedes)
10. **`benchmark/HANDOFF.md`** (project handoff — Last-updated session 28 close)
11. **`benchmark/final/SUMMARY.md`** (canonical results — UNCHANGED)
12. **Stage 1a + 1b artifacts** (`01_references_inventory_report.md`, `01_xlsx_delta_proposal.csv`, `02_references_download_manifest.md`) — reference for bib edits
13. **All non-MEMORY auto-memory files** (auto-loaded)
14. **Sandbox `.tex` / `.bib`** ONLY when about to edit
15. **The plan file** at `C:\Users\partha\.claude\plans\misty-knitting-pine.md` (the v1 verification plan; sessions 27+28 executed Stages 1a→5; Stage 6 + edit-phase remain)

---

## §7. Verification plan — current status (UPDATED)

| Stage | Status | When |
|---|---|---|
| 1a — Reference inventory | ✅ COMPLETE (session 27) | — |
| 1b — Reference PDF download (3 sub-passes) | ✅ COMPLETE (session 27) | — |
| 1c — PDF content verification | ✅ COMPLETE (session 28, Gate 18) | — |
| 2 — DIFF parity (text + visual) | ✅ COMPLETE (session 28, Gate 19) | — |
| 3 — Audit history timeline + checklist | ✅ COMPLETE (session 28, Gate 20) | — |
| 4 — Paper claim cross-verification | ✅ COMPLETE (session 28, Gate 21) | — |
| 5 — Benchmark topology analysis | ✅ COMPLETE (session 28, Gate 22) | — |
| **6 — Final synthesis** | ⏳ PENDING — **session 29 first action** | Solo, ~15-20 min |
| **Edit-phase** | ⏳ PENDING — session 29 or 30 | Phased commits per Stage 6 synthesis |

### Session 29 first actions

1. Read `MEMORY.md` SESSION 29 STARTUP block (auto-loaded)
2. Read THIS handoff IN FULL
3. Read mandatory Stage 1c/3/4/5 reports per §6
4. Read session 27 handoff for earlier context
5. State-verify (single Bash call):
   - `git status --short` → 0 lines (clean — assuming Gate 24 push landed; otherwise might show _artifacts/ untracked)
   - `git log -1 --format='%h %s'` → expected post-Gate-24 HEAD (this commit's hash; TBD at Gate 23)
   - `git log origin/main -1 --format='%h'` → same (synced post-push)
   - Sandbox PDFs → 16p / unchanged SHA-256 (be6c27ab / ed09349d)
   - AWS → stopped; CW alarm → ActionsEnabled=True
   - REFERENCE PAPERS/ → 32 PDFs at top level / ~71 MB
6. **LAUNCH Stage 6 FIRST** (solo, ~15-20 min). Cross-validates all 5 prior reports (Stage 1c + 2 + 3 + 4 + 5) + integrated verdict + edit checklist + phased plan.
7. After Stage 6 review + commit → BEGIN EDIT-PHASE (24 bib field-level edits + chen2024autonomous decision + notaro manual + Stage 5 Option A topology moves + 3 optional Y polish items).
8. Each edit batch: edit → recompile main + DIFF → verify 16p → themed commit → spot-check pp.15-16 of DIFF for bib edits.
9. USER GO required before each agent launch, each commit, each push.

---

## §8. Carry-forward open items for session 29+

### CRITICAL for edit-phase (consolidated from Stage 1c + Stage 3 + Stage 4 + Stage 5)

**Bib metadata corrections** (24 field-level edits across 14 entries — see §3.2):
- [ ] **Batch A**: 3 Stage-1b confirmed (miller×4, wu×1, chen-automap×2)
- [ ] **Batch B**: 5 Stage-1c CRITICAL (chen-rcagent, shi-aiopslabs, li-opseval, liu-logeval, xu-openrca)
- [ ] **Batch C**: 5 Stage-1c HIGH/MEDIUM (adaspec, askell, bansal, pei-flowofaction, arigraph)

**Unresolved bib placeholders**:
- [ ] `notaro2021aiopssurvey` — journal field + real DOI unresolved; user institutional fetch needed
- [ ] `chen2024autonomous` — placeholder cite, no DOI/arXiv; decision required (find / substitute / remove)

**Stage 4 optional polish items**:
- [ ] Y1: Figure 3 caption clarify ("With-orchestrator omitted, identical to With-graph on 357/357")
- [ ] Y2: §6.2 P95 align to Table 4 (48.4 → 48.6 OR cross-pointer)
- [ ] Y3: BERT-F1 per-config columns in Tables 5/6/7 (if layout room after bib edits)

**Stage 5 topology moves (Option A — 3 phased commits)**:
- [ ] Commit topology-A1: 6 root underscore-orphans → `_dev/` + scripts/README regen (34→43)
- [ ] Commit topology-A2: 3 raw mirrors → `archive/raw_pre_reorg_mirrors/` + 3 README annotations + INDEX.md tally
- [ ] Commit topology-A3 (optional, sealed-tree adjacency): `INDEX_BUILD_REPORT.md` relocate

### IMPORTANT (deferred)

- 3 sci-hub-sourced PDFs (parasuraman / wu / chen-automap) — protocol drift decision: keep OR replace via institutional access
- xlsx update from Stage 1a `01_xlsx_delta_proposal.csv` (68-row draft with Status/Action/Notes columns)
- Tier-2 vol/issue/pages for peng + zhang (Path B'' Tier 2 — accept 17p overshoot risk)

### NICE-TO-HAVE

- Cite-key renames for surname-mismatch entries (chen2024rcagent → wang2024rcagent, etc.) — cosmetic per session-26 stable-label rule
- BERT-F1 re-run with MIN_TEXT_LEN=5 (D-6 known artifact)
- M-3/M-4 housekeeping (legacy excluded_rca_cases.json + stale summary.json)
- Abstract / §1 tone polish (preserve-as-accepted per locked decision)
- Path G submit (when COMSYS 2026 CFP opens)

### DEFERRED (out-of-scope for camera-ready)

- Path D AWS rerun (Stack B full 431, Phase 4.5c cold-start) — unless reviewer demands
- Brittlebench / C3AI bib additions
- CV 5th agent (superseded by multi-agent audits)

---

## §9. Pending Gate 23 (commit) + Gate 24 (push) for session 28

### Proposed Gate 23 commit (1 themed commit, requires USER GO)

**Commit** — `docs(audit-session28): close-out — SESSION_28 handoff + memory + session-29 starter`
- NEW: `benchmark/final/audit/SESSION_28_HANDOFF.md` (this file)
- MODIFIED: `benchmark/HANDOFF.md` — Last-updated bumped + audit dir state update
- MODIFIED (auto-memory): `MEMORY.md` — SESSION 28 STARTUP → SESSION 29 STARTUP block
- NEW (auto-memory): `reference_session29_starter_prompt.md` — paste-in starter

NO data files, NO scripts, NO sandbox edits.

### Pending Gate 24 push (batched, requires SEPARATE USER GO)

6 local commits ahead of origin/main:
- `b88590c` (Gate 18) — Stage 1c
- `9110ec9` (Gate 19) — Stage 2
- `4225a91` (Gate 20) — Stage 3
- `bc9f5ab` (Gate 21) — Stage 4
- `f57f69e` (Gate 22) — Stage 5
- `<Gate-23-hash>` (Gate 23) — close-out

Single batched push: `git push origin main`.

---

## §10. Useful commands for session 29

```bash
# State-verify
cd "c:/Users/partha/Downloads/files AIOPS NEW/constitutional-aiops"
git status --short
git log -1 --format='HEAD: %h %s'
git log origin/main -1 --format='ORIGIN: %h'

# Sandbox PDFs unchanged
SANDBOX="../PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2.sandbox-session16"
sha256sum "$SANDBOX/main/sn-article.pdf" "$SANDBOX/diff/sn-article-DIFF.pdf"

# Read Stage 1c bib error catalog before edit-phase
cat "benchmark/final/audit/paper_audit_session27_2026-05-26/03_pdf_content_verification.md"

# Read open items checklist
cat "benchmark/final/audit/paper_audit_session27_2026-05-26/05_open_items_checklist.md"

# Recompile main paper after .bib edits
PDFLATEX='/c/Users/partha/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe'
BIBTEX='/c/Users/partha/AppData/Local/Programs/MiKTeX/miktex/bin/x64/bibtex.exe'
cd "$SANDBOX/main"
"$PDFLATEX" sn-article.tex; "$BIBTEX" sn-article; "$PDFLATEX" sn-article.tex; "$PDFLATEX" sn-article.tex

# Regen DIFF (encoded recipe)
export PATH="/c/Program Files/Git/usr/bin:$PATH"
python "c:/Users/partha/Downloads/files AIOPS NEW/constitutional-aiops/benchmark/scripts/_dev/regen_diff_pdf.py"
cd "$SANDBOX/diff"
"$PDFLATEX" sn-article-DIFF.tex; "$BIBTEX" sn-article-DIFF; "$PDFLATEX" sn-article-DIFF.tex; "$PDFLATEX" sn-article-DIFF.tex

# CrossRef API for any DOI verification
curl -s 'https://api.crossref.org/works/<DOI>' | python -m json.tool
```

---

## §11. Session 28 budget summary

- Agent time: ~35 min (Stage 1c) + ~25 min (Stage 2) + ~35 min (Stage 3) + ~25 min (Stage 4) + ~30 min (Stage 5) = **~150 min**
- State verify + 4 spot-checks: ~10 min
- Review + 5 commits (Gates 18-22): ~25 min
- Documentation (this handoff + memory + starter): ~25 min (in progress)
- **Total wall-clock**: ~210 min / ~3h 30min

Budget projection for session 29 (Stage 6 + edit-phase Batch A + Batch B + Batch C + topology Option A + DIFF regens): ~4-5 hours total — likely splits into session 29 (Stage 6 + Batch A) and session 30 (Batch B + Batch C + topology + final 16p verify).

---

## §12. Gate ledger

| Gate | When | Status | Hash |
|---|---|---|---|
| 14 | Session 27 (Stage 1a commit) | ✅ DONE | `5bfbabe` |
| 15 | Session 27 (Stage 1b commit) | ✅ DONE | `e82f5cd` |
| 16 | Session 27 (close-out commit) | ✅ DONE | `6aee747` |
| 17 | Session 27 (push Gates 14+15+16) | ✅ DONE | — |
| 18 | Session 28 (Stage 1c commit) | ✅ DONE | `b88590c` |
| 19 | Session 28 (Stage 2 commit) | ✅ DONE | `9110ec9` |
| 20 | Session 28 (Stage 3 commit) | ✅ DONE | `4225a91` |
| 21 | Session 28 (Stage 4 commit) | ✅ DONE | `bc9f5ab` |
| 22 | Session 28 (Stage 5 commit) | ✅ DONE | `f57f69e` |
| 23 | Session 28 close-out commit | ⏳ PENDING — USER GO | TBD |
| 24 | Session 28 push (Gates 18-23 batched) | ⏳ PENDING — separate USER GO | — |
| 25+ | Session 29 (Stage 6 + edit-phase) | future | — |

---

*End of handoff. Session 28 close 2026-05-27. Next session = 29.*
