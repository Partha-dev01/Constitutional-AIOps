# Session 31 → Session 32 Handoff (2026-05-27)

> **PRIMARY ENTRY POINT for session 32**. Session 31 closed the paper-editing portion of the COMSYS 2026 camera-ready revision. **All required + chosen optional paper edits applied + 16p preserved**. Phase 4 (notaro institutional fetch metadata + chen2024autonomous L3 substitution) + Phase 6 OPTIONAL (Y1 Fig 3 caption + Y2 §6.2 P95) bundled in Gate 33 `4df8ca2`. 5 cite-key renames (Stage 6 OI-N1) landed in Gate 34 `de1c440`. Gate 32 batched push (Gates 28-31 from session 30) landed `580eecd..801225a` early this session. Gate 35 close-out + verification-agent + xlsx-update + Phase 5 topology + Phase 7 push deferred to session 32 per user direction. AWS untouched.

---

## §0. One-line state

**Paper editing COMPLETE for camera-ready** — 16p invariant preserved on both main and DIFF; bib has 34 entries (31 cited + 3 retained-orphan); chen2024autonomous placeholder fully replaced by bai2022constitutional citation; notaro fixed with correct ACM TIST journal + DOI 10.1145/3483424; 5 cite-keys renamed to lead-author-surname-matched form; Y1 + Y2 Stage 4 polish applied. Gates 33 + 34 landed locally; Gate 32 (deferred session-30 push) already landed; Gate 35 close-out + Gate 36 batched push pending USER GO. Verification agent + xlsx update + Phase 5 topology deferred to session 32.

---

## §1. What happened this session (chronological)

1. **Session 31 start**: read all 15 mandatory files per session-31 starter (MEMORY SESSION 31 STARTUP, SESSION_30 handoff, Stage 6 final synthesis playbook, Stage 1b manifest, Stage 5 topology, Stage 4 cross-verification, Stage 2 DIFF parity, SESSION_29/28/27 handoffs, benchmark/HANDOFF, final/SUMMARY, plan file, 3 starred auto-memory files). No file or section skipped.
2. **State-verify** (single Bash call): clean carry from session-30 close. HEAD `801225a` (Gate 31), origin `580eecd` (Gate 32 push deferred), 0 4 ahead. Working tree only `_artifacts/` untracked (intentional). Sandbox `main/sn-article.pdf` = 467,786 B / SHA-256 `62c8386e…7973` ✓. `diff/sn-article-DIFF.pdf` = 469,344 B / `9640abbd…342c` ✓. REFERENCE PAPERS/ = 32 PDFs / 71 MB ✓. Bib 10,347 B / 272 lines ✓.
3. **Sanity-check session-30 work**: grep'd live bib for 13 batch-A/B/C entries — all corrections verified on disk (Miller Evan line 236, Yu Guangba line 73, Ma Meng line 80, Wang Zefan line 66, Chen Yinfang line 206, Liu Yuhe line 174, Cui Tianyu line 227, Xu Junjielong line 213, Huang Kaiyu line 251, Huang Saffron line 102, Effect of AI Explanations line 59, Pei Changhua line 220, Semenov+Sorokin line 87). NO hallucinations in session-30 close.
4. **Gate 32 batched push** (per session-30 close carry-forward, user GO): `git push origin main` landed `580eecd..801225a` — pushed Gates 28+29+30+31 (4 commits batched).
5. **User provided Phase 4 inputs**:
   - chen2024autonomous: `https://arxiv.org/html/2411.14155v1` with label "Chen, D., Williams, M.: Towards Autonomous IT Operations: Trust, Safety, and Verification Challenges. ACM Transactions on Autonomous Systems (2024)"
   - notaro2021aiopssurvey: `https://dl.acm.org/doi/10.1145/3483424` with label "ACM Transactions on Networking and Service Management 20(3) (2021)"
6. **Verified both PDFs on disk** (`2411.14155v1.pdf` + `3483424.pdf` already in REFERENCE PAPERS/) via pdftotext first-page:
   - `3483424.pdf` = correct Notaro AIOps survey ✓ (Paolo Notaro + Jorge Cardoso + Michael Gerndt; ACM Trans Intell Syst Technol Vol 12 No 6 Article 81; 45 pages)
   - `2411.14155v1.pdf` = Leahy et al. "Grand Challenges in the Verification of Autonomous Systems" — NOT Chen+Williams as user expected ⚠
7. **CrossRef API verification** (DOI 10.1145/3483424): confirmed journal is **ACM Transactions on Intelligent Systems and Technology** (NOT "Networking and Service Management" as bib + user-note both claimed). Volume 12, Issue 6. The bib's "20(3)" was wrong on both vol and issue.
8. **Flagged 2 issues to user**:
   - chen URL/citation mismatch: arXiv 2411.14155 doesn't match the Chen+Williams citation; it's Leahy et al. (robotics-domain autonomous-systems verification roadmap, IEEE RAS Technical Committee)
   - notaro journal name discrepancy: DOI maps to ACM TIST, not TNSM
9. **User clarification**: initially "rather lets drop the chen paper?" then "no wait we cant drop that paper we have given that in first submission which was accepted" — chen2024autonomous citation must be retained (v1 already had it) but its bib entry must point to a real paper. User asked me to assess Leahy as substitute given its autonomous-systems framing.
10. **Leahy assessment** (read full intro): "Grand Challenges in Verification of Autonomous Systems" by IEEE RAS Technical Committee — talks about verification, safety, autonomous systems generally, but DOMAIN MISMATCH (robotics/vehicles, not AIOps; explicitly says AI verification is "orthogonal" to their scope). Defensible-but-imperfect substitute. Presented 3 options: L1 keep cite-key+sub Leahy / L2 rename cite-key+sub Leahy / L3 sub bai2022constitutional+drop chen entry.
11. **User decided**: Phase 4 chen2024autonomous → **L3** (substitute with bai2022constitutional already cited adjacent at §2.3 line 168 + §3.5 line 383; drop chen2024autonomous bib entry). Also: do Y1 + Y2; explain Y3 + deferred items.
12. **Renamed both PDFs** to project convention:
    - `3483424.pdf` → `notaro2021aiopssurvey - A Survey of AIOps Methods for Failure Management - acm-tist-3483424.pdf`
    - `2411.14155v1.pdf` → `leahy2024grandchallenges - Grand Challenges in the Verification of Autonomous Systems - 2411.14155.pdf` (kept as unused reference, NOT in bib)
13. **Applied 5 edits** (Phase 4 + Phase 6 polish):
    - notaro: 3-author + ACM TIST journal correction + DOI added + min-viable (drop vol/num per session-25 rule)
    - chen L3: bib entry deleted + bib header tweaked (35→34, 32→31) + sandbox `.tex:135` `\cite{chen2024autonomous}` → `\cite{bai2022constitutional}`
    - Y1: Fig 3 caption added clause (initial 135-char attempt with table cross-refs)
    - Y2: §6.2 line 741 P95 "48.4\,s" → "48.6\,s" (initial attempt also added parenthetical "(index-floor convention per Table~\ref{tab:latency} footnote)")
14. **Recompile #1 (notaro full + chen L3 + Y1 + Y2 full)**: **17p OVERSHOOT** — Stage 6 §7 risk materialized.
15. **Bisection**:
    - First trim: notaro min-viable (drop vol/number) — still 17p (chen drop only -200 chars; Y1+Y2 added more than that)
    - Second trim: Y2 parenthetical removed (just number swap) — still 17p
    - Third trim: Y1 reverted entirely — **16p RESTORED** → confirmed Y1 caption growth was the dominant cause
    - Fourth try: Y1 trimmed to shortest viable clause "; With-orchestrator omitted, equals With-graph" (~38 chars vs original 135) — **16p HELD**
16. **DIFF regen + recompile** post-final-edits — 16p preserved on both.
17. **Spot-checks (pdftotext)**: §1 line 135 `[5] = Bai`; §6.2 P95 = 48.6 s; Fig 3 caption Y1 clause present; Refs [4] Notaro 3-author + ACM TIST + DOI; Refs [5] Bai unchanged; chen2024autonomous absent from References. ALL PASS.
18. **Gate 33 commit** (`4df8ca2`): `paper(sandbox-session16): Phase 4 + Phase 6 — notaro/chen bib resolution + Y1 caption + Y2 P95 polish`. `--allow-empty` per session-26 `99f03fe` out-of-tree pattern. Full HEREDOC body documenting all 5 edits + 16p verification + new SHA-256s + reasoning + carry-forward.
19. **User decisions on 5 deferred items**:
    - #1 sci-hub PDFs: SKIP
    - #2 xlsx update: USE AGENT NOW (combined task)
    - #3 cite-key renames: DO IT
    - #4 BERT-F1 MIN_TEXT_LEN=5 rerun: SKIP
    - #5 Path G submit: user handles, not assistant's concern
    - Phase 5 topology: deferred to session 32
20. **Cite-key rename analysis**: Identified 5 actual renames (not 8 as initially counted) — `xu2025openrca` + `pei2025flowofaction` surnames already match corrected lead-author; `adaspec2025` is project-name label not surname-based. Renames:
    - `chen2024rcagent` → `wang2024rcagent` (lead Wang Zefan)
    - `shi2025aiopslabs` → `chen2025aiopslabs` (lead Yinfang Chen)
    - `li2024opseval` → `liu2024opseval` (lead Yuhe Liu)
    - `liu2025logeval` → `cui2025logeval` (lead Tianyu Cui)
    - `askell2024collective` → `huang2024collective` (lead Saffron Huang)
21. **Applied 10 Edit calls** (5 cite-keys × 2 files; replace_all=true on bare cite-key strings — safe because cite-keys are unique-spelled identifiers). All confirmed via grep: all 5 OLD keys absent from both `.tex` + `.bib`; all 5 NEW keys present.
22. **Recompile + regen DIFF + recompile DIFF**: both 16p preserved. 0 undefined refs. References list spot-check confirms all 5 entries render correctly with new keys ([9] Wang, [13] Huang, [20] Cui, [21] Chen, [23] Liu).
23. **Gate 34 commit** (`de1c440`): `paper(sandbox-session16): Gate 34 — 5 cite-key renames to lead-author surname-matched keys`. Full HEREDOC body with rename map + sites-modified + verification + reasoning + note on session-26 stable-label rule reversal for these 5 entries.
24. **User direction at this point**: launch combined verification + xlsx-update agent.
25. **Agent prep interrupted by user**: "is paper work done fully? need to compact safely now and continue next session also remember to give me the next session prompt".
26. **Session 31 ended** at this handoff write. Pending Gate 35 = close-out commit (this handoff + benchmark/HANDOFF + MEMORY.md + session-32 starter). Pending Gate 36 = batched push of Gates 33+34+35 to origin/main (separate USER GO).

---

## §2. What changed on disk in session 31

### Pushed (Gate 32 from session 30; landed early session 31)

| Commit | Type | Notes |
|---|---|---|
| `9307cb3` (Gate 28) | `--allow-empty` paper(sandbox-session16) | Batch A bib edits (carried from session 30) |
| `9cfa888` (Gate 29) | `--allow-empty` paper(sandbox-session16) | Batch B bib edits (carried from session 30) |
| `f69c3c5` (Gate 30) | `--allow-empty` paper(sandbox-session16) | Batch C bib edits (carried from session 30) |
| `801225a` (Gate 31) | docs(audit-session30) | session-30 close-out (carried from session 30) |
| **Gate 32 push** | — | `git push origin main` — `580eecd..801225a` |

### Committed this session (Gates 33-34; HEAD `de1c440`)

| Commit | Type | Notes |
|---|---|---|
| `4df8ca2` (Gate 33) | `--allow-empty` paper(sandbox-session16) | Phase 4 (notaro/chen L3) + Phase 6 polish (Y1+Y2) |
| `de1c440` (Gate 34) | `--allow-empty` paper(sandbox-session16) | 5 cite-key renames (Stage 6 OI-N1) |

### Pending in Gate 35 (close-out, this commit)

| File | Status | Notes |
|---|---|---|
| `SESSION_31_HANDOFF.md` | NEW | this file |
| `benchmark/HANDOFF.md` | MODIFIED | Last-updated bumped session 30 close → session 31 close |
| `MEMORY.md` (auto-memory) | MODIFIED | SESSION 31 STARTUP → SESSION 32 STARTUP block + archive entry |
| `reference_session32_starter_prompt.md` (auto-memory) | NEW | paste-in starter for session 32 |

### NOT committed (intentional)

- `paper_audit_session27_2026-05-26/_artifacts/` (32 PNGs from Stage 2 visual export, ~10-15 MB) — reproducible via pdftoppm command in Stage 2 report §1; carry-forward across sessions; do not commit.

### Sandbox paper artifacts — CHANGED this session (NEW SHA-256 baseline)

| File | Pre-session-31 SHA-256 | Post-session-31 SHA-256 | Size delta |
|---|---|---|---|
| `main/sn-article.pdf` | `62c8386e5a0d6c2e24bb65a70f99301b6dc2e12ca0401c8e3287da3df08e7973` | **`5e2f3635ccfd9b235a29f227144616a6085321086cd9771a695a9c7799225313`** | 467,786 → 467,886 (+100 B) |
| `diff/sn-article-DIFF.pdf` | `9640abbd2cd306eac9b410bf8722c1c0471cda278cca23ac23fcbaebe6cd342c` | **`d6733a53de142f9d75f0bd6bd3befc20d0dbf6fc0e98340ad9563628765b02c3`** | 469,344 → 469,490 (+146 B) |
| `main/sn-bibliography.bib` | 10,347 B / 272 LF lines | **10,124 B / 264 LF lines** | -223 B / -8 lines (chen drop dominated) |
| `diff/sn-article-DIFF.tex` | 68,249 B / 830 LF lines | 68,514 B (refreshed) | +265 B (latexdiff markup for Gate 33 + 34 changes) |

**Both PDFs preserved at 16 pages.** Cumulative session-31 paper-artifact delta: +100 B on main, +146 B on DIFF, -223 B on bib (net SHRINK due to chen entry drop).

### REFERENCE PAPERS/ disk state — CHANGED this session

| State | Pre-session-31 | Post-session-31 |
|---|---|---|
| PDF count | 32 | **34** |
| Total size | ~71 MB | ~71 MB (+~700 KB for 2 new) |
| New PDFs | — | `notaro2021aiopssurvey - … - acm-tist-3483424.pdf`; `leahy2024grandchallenges - … - 2411.14155.pdf` (unused ref) |
| xlsx | NOT updated | NOT updated (pending session-32 agent) |

### AWS state at close (UNCHANGED from sessions 20-30)

Instance stopped, CW alarm armed (ActionsEnabled=True, StateValue=INSUFFICIENT_DATA — normal for long-stopped instance), EIP retained, EBS preserved, snapshot held, ~$55/$120 spend. NO AWS work in session 31 — all read-only on benchmark + write on sandbox + write on REFERENCE PAPERS/.

### Git state at close (pre-Gate-35)

- Local HEAD: `de1c440` (post-Gate-34)
- Origin HEAD: `801225a` (post-Gate-32 push)
- Branch: `main`
- Working tree: 32-PNG `_artifacts/` dir untracked (intentional); soon-to-add Gate-35 close-out files
- Pending Gate 35: bundle all close-out file changes into one commit
- Pending Gate 36 push: Gates 33+34+35 (3 commits batched) to origin/main (separate USER GO)

---

## §3. Edit-phase verdict update (Stage 6 §6 phased plan — paper-side COMPLETE)

### §3.1 Cumulative bib catalog (24 of 24 fields / 14 of 14 entries DONE)

| Batch | Entries | Fields | Status | Gate |
|---|---:|---:|---|---|
| A (Stage 1b confirmed) | 3 | 7 | ✅ DONE session 30 | Gate 28 `9307cb3` |
| B (Stage 1c CRITICAL) | 5 | 9 | ✅ DONE session 30 | Gate 29 `9cfa888` |
| C (Stage 1c HIGH/MED) | 5 | 7 | ✅ DONE session 30 | Gate 30 `f69c3c5` |
| **Phase 4 manual+decisions** | **2** | **2** | ✅ **DONE session 31** | **Gate 33 `4df8ca2`** |
| **TOTAL** | **15** | **25** | **24/24 FIELD CORRECTIONS APPLIED** | + 1 chen-substitution decision |

(Phase 4 contributed: notaro min-viable fix [1 entry / multi-field] + chen2024autonomous L3 substitution [drop entry + reassign cite to bai] — combined as 1 commit Gate 33 with Y1+Y2 polish.)

### §3.2 Cite-key renames (Stage 6 OI-N1 — session-26 stable-label rule reversed for 5 entries)

| Old | New | Reason | Gate |
|---|---|---|---|
| `chen2024rcagent` | `wang2024rcagent` | Lead Wang Zefan | 34 `de1c440` |
| `shi2025aiopslabs` | `chen2025aiopslabs` | Lead Yinfang Chen | 34 `de1c440` |
| `li2024opseval` | `liu2024opseval` | Lead Yuhe Liu | 34 `de1c440` |
| `liu2025logeval` | `cui2025logeval` | Lead Tianyu Cui | 34 `de1c440` |
| `askell2024collective` | `huang2024collective` | Lead Saffron Huang | 34 `de1c440` |

Keys NOT renamed (intentional):
- `xu2025openrca` — Lead Xu (Junjielong), surname matches
- `pei2025flowofaction` — Lead Pei (Changhua), surname matches
- `adaspec2025` — Project-name label (AdaSpec), not surname-based

### §3.3 Stage 4 OPTIONAL polish (Y1+Y2 applied; Y3 skipped per user)

| Item | Status | Action | Note |
|---|---|---|---|
| Y1 (Fig 3 caption) | ✅ APPLIED (trimmed) | Added "; With-orchestrator omitted, equals With-graph" (38 chars) | Original 135-char clause with table cross-refs caused 17p; trimmed to fit |
| Y2 (§6.2 P95) | ✅ APPLIED (number-only) | "P95 48.4\,s" → "P95 48.6\,s" | Original parenthetical "(index-floor convention per Table~\ref{tab:latency} footnote)" caused 17p; trimmed to bare swap |
| Y3 (BERT-F1 per-config) | ⏭ SKIPPED | Locked D-6 Option C retained (1-sentence §5.2 prose "Mean BERTScore F1 was 0.81 ± 0.01") | HIGH 17p risk; per-config columns would require additional bib trimming; reader impact zero given current §5.2 summary |

### §3.4 16p invariant — held through all Gate 33 + 34 edits

| Checkpoint | main pages / size | DIFF pages / size |
|---|---|---|
| Session-30 close (pre-31) | 16p / 467,786 B | 16p / 469,344 B |
| Post-Gate-33 (Phase 4 + Y1 trimmed + Y2 number-only) | 16p / 467,885 B (+99 B) | 16p / 469,436 B (+92 B) |
| Post-Gate-34 (cite-key renames) | 16p / 467,886 B (+1 B) | 16p / 469,490 B (+54 B) |
| **Cumulative session-31** | **16p HELD (+100 B)** | **16p HELD (+146 B)** |

Bisection cost (3 failed 17p compiles before final fit): documented in Gate 33 commit message + this handoff §1 step 15. Min-viable rule (session 25) applied to notaro; shortest-viable rule applied to Y1 (38 chars vs 135) and Y2 (bare swap vs parenthetical). Stage 6 §7 risk MATERIALIZED but was mitigated via the encoded "verify 16p after EACH commit" rule + min-viable trims.

---

## §4. Authoritative state for session 32

### Paths (NEW SHA-256 baselines post-session-31)

| Item | Path |
|---|---|
| Active paper `.tex` | `…sandbox-session16\main\sn-article.tex` (~55,200 B / 789 LF lines — content of 5 cite-keys renamed and chen cite swapped; total bytes ≈ unchanged from session 30) |
| Active paper `.pdf` | `…sandbox-session16\main\sn-article.pdf` (**16 pages / 467,886 B**, NEW SHA-256 `5e2f3635ccfd9b235a29f227144616a6085321086cd9771a695a9c7799225313`) |
| Active paper `.bib` | `…sandbox-session16\main\sn-bibliography.bib` (**10,124 B** / 264 LF lines / 34 entries; 31 cited; 3 retained-orphan; **ALL 24 field-level corrections APPLIED**; **5 cite-key renames APPLIED**) |
| DIFF `.tex` | `…sandbox-session16\diff\sn-article-DIFF.tex` (68,514 B / refreshed via regen_diff_pdf.py post-renames) |
| DIFF `.pdf` | `…sandbox-session16\diff\sn-article-DIFF.pdf` (**16 pages / 469,490 B**, NEW SHA-256 `d6733a53de142f9d75f0bd6bd3befc20d0dbf6fc0e98340ad9563628765b02c3`) |
| v1 paper (READ-ONLY) | `…Final Submission Paper (Accepted v.1)\…\sn-article.tex` |
| OLD `sn-article-template.v2/` | MOVED to `z.Dump Paper Archive/` — do NOT touch |
| Reference PDFs | `…PAPER\REFERENCE PAPERS\` (**34 PDFs** at top level / ~71 MB; +2 vs session 30: notaro + leahy) |
| xlsx | `…PAPER\REFERENCE PAPERS\AIOps_References_Complete.xlsx` (47 rows × 9 cols — **NOT UPDATED**; pending session-32 agent) |
| Project handoff | `constitutional-aiops/benchmark/HANDOFF.md` (Last-updated session 31 close) |
| Session-27 audit dir | `constitutional-aiops/benchmark/final/audit/paper_audit_session27_2026-05-26/` (9 .md + 1 .csv + `_artifacts/` 32-PNG untracked; report `09_xlsx_update_and_final_verification.md` will be created by session-32 agent) |

### Numbers (UNCHANGED — session 31 was paper-side write-only on sandbox; benchmark data untouched)

All headline values preserved: Main Overall **82.4%** (294/357), Ann **82.6%** (180/218), RCA **82.0%** (114/139), BCa CI [78.2, 86.0], Llama ΔRCA **+10.8pp**, DeepSeek ΔRCA **+15.1pp**, Stack B speedup **1.51×**, Phase 4.5a McNemar p=0.289 NS. Stack B = vLLM AWQ awq_marlin, NOT FP8. All Stage 4 cells verified GREEN against authoritative sources.

### Git

- Local HEAD `de1c440` (Gate 34); origin `801225a` (post-Gate-32 push)
- 2 commits ahead of origin (Gates 33+34)
- Gate 35 commit (this close-out) pending USER GO
- Gate 36 push (Gates 33+34+35 batched) pending USER GO at session close

### AWS

Stopped, CW alarm enabled, EIP retained, EBS preserved, snapshot held, ~$55/$120 spend.

---

## §5. Hard rules carried forward (UNCHANGED — 18 rules + 6 process lessons + NEW session-31 lesson)

The 18 hard rules + 6 process lessons from session 30 §5 carry through unchanged. Key rules unchanged:

1. NO Claude co-author trailer on any commit
2. NO push without explicit USER GO (each push = separate confirm)
3. Paper edits target sandbox `main/sn-article.tex` (or `main/sn-bibliography.bib`) ONLY
4. NEVER touch real `sn-article-template.v2/` (moved to `z.Dump Paper Archive/`)
5. v1 paper is READ-ONLY reference
6. AWS stays stopped unless user GO; do NOT release EIP `44.195.172.165`; do NOT delete snapshot `snap-01b191aedbf46b598`
7. 3-point rubric mentions at sandbox lines 447 + 597 are INTENTIONAL DISCLOSURES
8. DO NOT recompute D-1 or BERT-F1 (done sessions 17-18)
9. DIFF PDF override uses `\textcolor{red!75!black}{#1}`; regen via `regen_diff_pdf.py`
10. PowerShell `:` parsing in filenames → use bash `mv`
11. PowerShell `>` redirect → UTF-16 LE BOM; use `[System.IO.File]::WriteAllText` with `UTF8Encoding $false` or Python with `newline="\n"`
12. Ollama 0.23.2 ignores `enable_thinking=False`
13. Master backup zip sacred
14. `annotation_test.json` + `rca_test.json` dirty in local — do NOT commit content changes
15. Sealed forensic docs untouchable: CV_PASS1/2, FULL_TRANSCRIPT_AUDIT, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, all SESSION_12-31_HANDOFF.md
16. Instance has NO git — always scp
17. Instance `src/` is OUTDATED — `find_similar_episodes_by_embedding` missing
18. DIFF regen recipe encoded in `regen_diff_pdf.py`

Process lessons (informational, carried from sessions 25-27 + session-30 addition):
- Min-viable bib rule (session 25): DOI alone preferred over vol/issue/pages
- CrossRef API for ACM works (session 26): hit `https://api.crossref.org/works/<DOI>` directly via curl
- Cite-key as stable label (sessions 24/25/26): default rule; reversed deliberately in session 31 Gate 34 for 5 entries per user judgment
- No submission "package" folders (session 26 post-close)
- Session 27 #1: first-page-verify all downloaded PDFs (validated again by Stage 1c finding 16 NEW errors)
- Session 27 #2: Anna's Archive blocked in env; sci-hub.ee → sci.bban.top CDN works as fallback
- Session 30 #1: `--allow-empty` themed `paper(sandbox-session16):…` commits for out-of-tree paper edits (matches session-26 `99f03fe` pattern)

**NEW session-31 lesson (informational, not a hard rule)**: When the user provides a URL+citation pair that they assume map to each other, **verify first via pdftotext / CrossRef before trusting**. Two specific anti-patterns surfaced this session: (a) `arXiv 2411.14155` was labeled as "Chen+Williams: Towards Autonomous IT Operations…" but the actual PDF is Leahy et al. "Grand Challenges in the Verification of Autonomous Systems" (different paper); (b) `DOI 10.1145/3483424` was labeled as "ACM Transactions on Networking and Service Management 20(3)" but CrossRef confirms it's "ACM Transactions on Intelligent Systems and Technology 12(6)". Same trap as Stage 1a's ~14% URL-guessing error rate (session-27 #1 lesson) but on the receiving end. Always validate before applying bib metadata.

---

## §6. Mandatory reads for session 32

1. **`MEMORY.md`** (auto-loaded — read SESSION 32 STARTUP block in full)
2. **`benchmark/final/audit/SESSION_31_HANDOFF.md`** ⭐⭐⭐ (THIS FILE — primary entry)
3. **`benchmark/final/audit/SESSION_30_HANDOFF.md`** (predecessor — Batches A+B+C bib edits context)
4. **`benchmark/final/audit/paper_audit_session27_2026-05-26/08_final_synthesis.md`** ⭐⭐⭐ (Stage 6 — 439 lines; operational playbook; needed for Phase 5 + 6 + 7 details)
5. **`benchmark/final/audit/paper_audit_session27_2026-05-26/07_benchmark_topology_analysis.md`** (Stage 5 — Option A 3 phased commits; A1 = 6 underscore-orphans → `scripts/_dev/`; A2 = 3 raw mirrors → `archive/raw_pre_reorg_mirrors/`; A3 OPTIONAL = `INDEX_BUILD_REPORT.md` relocate)
6. **`benchmark/final/audit/paper_audit_session27_2026-05-26/01_xlsx_delta_proposal.csv`** (Stage 1a draft CSV — 68 rows × 12 cols; for the verification-agent xlsx update task)
7. **`benchmark/final/audit/paper_audit_session27_2026-05-26/02_references_download_manifest.md`** (Stage 1b — for verification agent's PDF SHA-256 cross-check)
8. **`benchmark/final/audit/paper_audit_session27_2026-05-26/03_pdf_content_verification.md`** (Stage 1c — for verification agent's content cross-check)
9. **`benchmark/final/audit/paper_audit_session27_2026-05-26/06_claim_cross_verification.md`** (Stage 4 — for any final numerics cross-check)
10. **`benchmark/final/audit/paper_audit_session27_2026-05-26/04_diff_parity_report.md`** (Stage 2 — for DIFF parity verification reference)
11. **`benchmark/final/audit/SESSION_29_HANDOFF.md`** + **`SESSION_28_HANDOFF.md`** + **`SESSION_27_HANDOFF.md`** (predecessor context)
12. **`benchmark/HANDOFF.md`** (project handoff — Last-updated session 31 close)
13. **`benchmark/final/SUMMARY.md`** (canonical results — UNCHANGED)
14. **All non-MEMORY auto-memory files** (auto-loaded)
15. **Sandbox `.tex` / `.bib`** ONLY when about to edit (probably no edits in session 32; everything is verification + topology + close-out + push)
16. **The plan file** at `C:\Users\partha\.claude\plans\misty-knitting-pine.md` (v1 verification plan; ALL Stages 1a→6 + edit-phase Phases 1-4+6 complete; Phase 5 + agent verification + Phase 7 remain)

---

## §7. Verification plan — final status

| Stage / Phase | Status | When |
|---|---|---|
| Stages 1a / 1b / 1c / 2 / 3 / 4 / 5 / 6 | ✅ COMPLETE (sessions 27-29) | — |
| Edit-phase Phase 1 (Batch A bib) | ✅ COMPLETE (Gate 28 `9307cb3`) | session 30 |
| Edit-phase Phase 2 (Batch B bib) | ✅ COMPLETE (Gate 29 `9cfa888`) | session 30 |
| Edit-phase Phase 3 (Batch C bib) | ✅ COMPLETE (Gate 30 `f69c3c5`) | session 30 |
| **Edit-phase Phase 4 (notaro + chen2024autonomous L3)** | **✅ COMPLETE (Gate 33 `4df8ca2`)** | **session 31** |
| **Edit-phase Phase 6 (Y1 + Y2 polish; Y3 skipped)** | **✅ COMPLETE (bundled in Gate 33)** | **session 31** |
| **Cite-key renames (OI-N1)** | **✅ COMPLETE (Gate 34 `de1c440`)** | **session 31** |
| **Edit-phase Phase 5 (Topology Option A)** | ⏳ **PENDING — session 32** | A1+A2 LOW risk; A3 OPTIONAL sealed-tree adjacent |
| **Final verification agent** (xlsx + sanity-check) | ⏳ **PENDING — session 32 first action** | per session-31 user direction "use agent now"; deferred at user request |
| **Edit-phase Phase 7 (final batched push)** | ⏳ **PENDING — session 32** | separate USER GO; bundles all session-31+32 gates |

### Session 32 first actions

1. Read `MEMORY.md` SESSION 32 STARTUP block (auto-loaded)
2. Read THIS handoff IN FULL
3. Read Stage 6 `08_final_synthesis.md` IN FULL (operational playbook reference)
4. Read Stage 5 `07_benchmark_topology_analysis.md` IN FULL (topology move plan)
5. State-verify (single Bash call):
   - `git status --short` → 0 lines (clean) OR `_artifacts/` untracked
   - `git log -1 --format='%h %s'` → expect post-Gate-35 HEAD (this close-out commit, hash TBD)
   - `git log origin/main -1 --format='%h'` → expect `801225a` (Gate 32 push HEAD) OR same as local if Gate 36 pushed
   - `git rev-list --left-right --count origin/main...HEAD` → expect 0 0 OR 0 3 (Gates 33-35 if push deferred)
   - Sandbox `main/sn-article.pdf` → expect **16p, 467,886 B**, SHA-256 `5e2f3635…225313` (NEW post-session-31; NOT session-30 `62c8386e…7973`)
   - Sandbox `diff/sn-article-DIFF.pdf` → expect **16p, 469,490 B**, SHA-256 `d6733a53…02c3` (NEW post-session-31)
   - REFERENCE PAPERS/ → expect **34 PDFs** (was 32 at session-30 close + 2 new), ~71 MB
   - AWS `i-091c4de0e95d63154` → expect `stopped`
   - CloudWatch alarm → expect ActionsEnabled=True
6. **FIRST ACTION**: Launch combined verification + xlsx-update agent (per session-31 deferred direction). Agent inputs: full reads of Stages 1a-6 reports + session 30-31 handoffs + current bib + .tex. Agent tasks: (a) update `REFERENCE PAPERS/AIOps_References_Complete.xlsx` per Stage 1a draft CSV + reflect all session 30-31 changes (13 batch entries + chen drop + notaro fix + 5 cite-key renames + leahy PDF addition); (b) final sanity-check: walk every cite-key, every bib entry, verify against PDF or CrossRef DOI metadata, 16p invariant, Y1+Y2 in place, chen2024autonomous absent. Output: `paper_audit_session27_2026-05-26/09_xlsx_update_and_final_verification.md`. **USER GO REQUIRED before launch.**
7. **AFTER agent report**: address any findings (Gate 36a if fix-needed); if all GREEN, proceed.
8. **Phase 5 Topology Option A** (3 phased sub-commits, USER GO per gate):
   - A1 (Gate 37): 6 root underscore-orphan scripts → `scripts/_dev/` + scripts/README regen (34→43)
   - A2 (Gate 38): 3 raw mirror JSONLs → `archive/raw_pre_reorg_mirrors/` + INDEX.md §1 tally + 3 README annotations + `_NOTICE.md` in new subdir
   - A3 OPTIONAL (Gate 39, sealed-tree adjacent — separate USER GO): `INDEX_BUILD_REPORT.md` → `final/audit/SESSION_16_INDEX_BUILD_REPORT.md`
   - Verification gates per sub-commit: `python benchmark/scripts/eval/verify_authoritative_numbers.py` exits 0; `python benchmark/scripts/eval/inspect_all_configs.py` exits 0; sandbox PDFs UNCHANGED (topology moves do NOT touch paper).
9. **Session-32 close-out** (Gate 40 min): SESSION_32_HANDOFF.md + benchmark/HANDOFF.md Last-updated + MEMORY.md rotation + reference_session33_starter_prompt.md
10. **Phase 7 Final batched push** (separate USER GO): bundles all session-31 (Gates 33+34+35) + session-32 (Gates 36+ through 40) commits.
11. **All halt points carry forward**: USER GO before each agent launch, each commit (Gate 36+), each push (separate GO), any sandbox edit beyond planned phases, any AWS start, any submission action, Topology-A3 (sealed-tree adjacent), replacing any sci-hub-sourced PDF.

---

## §8. Carry-forward open items for session 32+

### CRITICAL for edit-phase completion

- ⏳ **OI-21 (NEW): Final verification agent** — combined task: xlsx update + sanity-check sweep across all session-30+31 work. Session-32 first action.
- ⏳ **OI-15: Topology A1 commit** (6 root orphans → `_dev/` + scripts/README regen 34→43) — Stage 6 Phase 5
- ⏳ **OI-16: Topology A2 commit** (3 raw mirrors → `archive/raw_pre_reorg_mirrors/` + INDEX.md tally) — Stage 6 Phase 5
- ⏳ **OI-17: Topology A3 OPTIONAL commit** (sealed-tree adjacent — separate USER GO) — Stage 6 Phase 5

### CLOSED in session 31

- ✅ **OI-4: notaro2021aiopssurvey** (Phase 4 manual fix) — Gate 33 `4df8ca2`
- ✅ **OI-5: chen2024autonomous** (Phase 4 L3 substitute) — Gate 33 `4df8ca2`
- ✅ **OI-18: Y1 Fig 3 caption clarify** (trimmed to 38-char clause) — Gate 33 `4df8ca2`
- ✅ **OI-19: Y2 §6.2 P95 align** (number-only swap) — Gate 33 `4df8ca2`
- ✅ **OI-N1: Cite-key renames for surname-mismatch entries** — Gate 34 `de1c440` (5 of 8 actually renamed; xu/pei/adaspec kept per surname-already-matches or project-name-label rule)

### SKIPPED in session 31 per user direction

- ⏭ **OI-13: 3 sci-hub-sourced PDFs (parasuraman/wu/chen-automap)** — keep as-is; institutional-access replacement is busywork with zero reader impact
- ⏭ **OI-20: Y3 BERT-F1 per-config in Tables 5/6/7** — HIGH 17p risk; locked D-6 Option C (1-sentence §5.2 prose summary) retained
- ⏭ **OI-N3: BERT-F1 re-run with MIN_TEXT_LEN=5** — only matters if Y3 done; SKIPPED with Y3
- ⏭ **Path G submit** — user-handled when COMSYS 2026 CFP opens

### IMPORTANT / NICE-TO-HAVE / DEFERRED

- ⏳ **OI-14: xlsx update** — bundled into OI-21 agent task
- ⏳ **OI-N2: Tier-2 vol/issue/pages for peng + zhang** (Path B'' Tier 2) — DEFER unless reviewer demands; 30-50% 17p overshoot risk
- ⏳ **OI-N4/N5: housekeeping** (legacy excluded_rca_cases.json, stale main_benchmark/summary.json) — DEFER
- ⏳ **OI-N6: Abstract / §1 tone polish** — DEFER (preserve-as-accepted lock from session 25+)
- ⏳ **OI-D1: Path D — Stack B full 431-case latency re-run** — DEFER unless reviewer demands
- ⏳ **OI-D2: Path D — Phase 4.5c cold-start curve** — DEFER unless reviewer demands
- ⏳ **OI-D3: Brittlebench/C3AI bib additions** — DEFER (judged intentional drops per page budget)
- ⏳ **OI-D4: CV 5th agent** — DEFER (superseded by multi-agent audits)

---

## §9. Pending Gate 35 (commit) + Gate 36 (push) for session 31

### Proposed Gate 35 commit (1 themed commit, requires USER GO)

**Commit** — `docs(audit-session31): close-out — SESSION_31 handoff + HANDOFF refresh + memory rotation + session-32 starter`
- NEW: `benchmark/final/audit/SESSION_31_HANDOFF.md` (this file)
- MODIFIED: `benchmark/HANDOFF.md` — Last-updated bumped session 30 close → session 31 close
- MODIFIED (auto-memory): `MEMORY.md` — SESSION 31 STARTUP → SESSION 32 STARTUP block; cascade prior session-30 archive from full-verbatim to one-line pointer; add Original SESSION 31 STARTUP archive (full verbatim)
- NEW (auto-memory): `reference_session32_starter_prompt.md` — paste-in starter for session 32

NO data files, NO scripts, NO sandbox edits, NO new audit reports.

### Pending Gate 36 push (batched, requires SEPARATE USER GO)

3 local commits ahead of origin/main after Gate 35:
- `4df8ca2` (Gate 33) — Phase 4 + Y1 + Y2
- `de1c440` (Gate 34) — cite-key renames
- `<Gate-35-hash>` (Gate 35) — close-out

Single batched push: `git push origin main`.

---

## §10. Useful commands for session 32

```bash
# State-verify
cd "c:/Users/partha/Downloads/files AIOPS NEW/constitutional-aiops"
git status --short
git log -1 --format='HEAD: %h %s'
git log origin/main -1 --format='ORIGIN: %h'
git rev-list --left-right --count origin/main...HEAD

# Sandbox PDFs at new post-session-31 baseline
SANDBOX="../PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2.sandbox-session16"
sha256sum "$SANDBOX/main/sn-article.pdf" "$SANDBOX/diff/sn-article-DIFF.pdf"
# Expected: 5e2f3635... main; d6733a53... DIFF (both 16p)

# REFERENCE PAPERS count
ls "../PAPER AND FORMAL DOCUMENTATION/PAPER/REFERENCE PAPERS/"*.pdf | wc -l
# Expected: 34

# Topology Phase 5 verification gates (Gate 37 + 38 pre-commit)
python benchmark/scripts/eval/verify_authoritative_numbers.py
python benchmark/scripts/eval/inspect_all_configs.py

# xlsx update (agent task, openpyxl)
python -c "from openpyxl import load_workbook; wb = load_workbook('...AIOps_References_Complete.xlsx'); ..."

# CrossRef API for DOI verification (used this session for notaro)
curl -s 'https://api.crossref.org/works/<DOI>' | python -m json.tool

# Recompile main paper (if any further edits in session 32 — likely none)
PDFLATEX='/c/Users/partha/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe'
BIBTEX='/c/Users/partha/AppData/Local/Programs/MiKTeX/miktex/bin/x64/bibtex.exe'
cd "$SANDBOX/main"
"$PDFLATEX" sn-article.tex; "$BIBTEX" sn-article; "$PDFLATEX" sn-article.tex; "$PDFLATEX" sn-article.tex

# DIFF regen + recompile
export PATH="/c/Program Files/Git/usr/bin:$PATH"
python "c:/Users/partha/Downloads/files AIOPS NEW/constitutional-aiops/benchmark/scripts/_dev/regen_diff_pdf.py"
cd "$SANDBOX/diff"
"$PDFLATEX" sn-article-DIFF.tex; "$BIBTEX" sn-article-DIFF; "$PDFLATEX" sn-article-DIFF.tex; "$PDFLATEX" sn-article-DIFF.tex
```

---

## §11. Session 31 budget summary

- Mandatory reads (15 files): ~30 min
- State verify + session-30 sanity check: ~10 min
- Gate 32 push: ~1 min
- Phase 4 + Y1 + Y2 work (3 bisection passes for 17p): ~45 min (incl. PDF first-page-verify, CrossRef checks, Leahy assessment, 3 trim passes)
- Gate 33 commit: ~3 min
- Cite-key renames + verification + Gate 34: ~15 min
- Documentation (this handoff + memory + starter): ~25 min (in progress)
- **Total wall-clock**: ~130 min / ~2h 10min

Session 31 was scoped to: edit-phase Phase 4 + Phase 6 polish + cite-key renames + close-out. Budget projection for session 32 (verification agent + Phase 5 topology Option A 3 sub-commits + close-out + Phase 7 push): ~2-3 hours total.

---

## §12. Gate ledger

| Gate | When | Status | Hash |
|---|---|---|---|
| 14-17 | Session 27 | ✅ DONE | — |
| 18-24 | Session 28 | ✅ DONE | — |
| 25-27 | Session 29 | ✅ DONE | — |
| 28 | Session 30 (Batch A) | ✅ DONE | `9307cb3` |
| 29 | Session 30 (Batch B) | ✅ DONE | `9cfa888` |
| 30 | Session 30 (Batch C) | ✅ DONE | `f69c3c5` |
| 31 | Session 30 close-out | ✅ DONE | `801225a` |
| **32** | **Session 31 (push Gates 28-31 batched)** | **✅ DONE** | **`580eecd..801225a`** |
| **33** | **Session 31 (Phase 4 + Y1 + Y2)** | **✅ DONE** | **`4df8ca2`** |
| **34** | **Session 31 (5 cite-key renames)** | **✅ DONE** | **`de1c440`** |
| 35 | Session 31 close-out commit | ⏳ PENDING — USER GO | TBD |
| 36 | Session 31 push (Gates 33+34+35 batched) | ⏳ PENDING — separate USER GO | — |
| 37+ | Session 32 (verification agent + Phase 5 topology + close-out + Phase 7 push) | future | — |

---

*End of handoff. Session 31 close 2026-05-27. Next session = 32.*
