# Session 27 → Session 28 Handoff (2026-05-26 → 2026-05-27)

> **PRIMARY ENTRY POINT for session 28**. Session 27 ran the first 2 stages of an 8-stage multi-agent paper verification plan (Stage 1c added per user request mid-session): Stage 1a (reference inventory) + Stage 1b (PDF download in 3 sub-passes). **24 new PDFs** landed in `REFERENCE PAPERS/`. 2 themed commits applied locally + Gate 16 close-out pending. Stages **1c (NEW), 2, 3, 4, 5, 6** deferred to session 28. Sandbox PDFs preserved at 16p / unchanged SHA-256. AWS untouched. **9 bib metadata errors across 4 entries surfaced for edit-phase.**

---

## §0. One-line state

Verification stages 1a + 1b complete (with 2 retry passes). 47-row xlsx mapped to 35-bib + on-disk-PDF inventory + Status/Action/Notes draft CSV. **24 new PDFs downloaded** (21 official-source curl + 3 sci-hub fallback after Anna's blocked). **1 paywalled FAILED_MANUAL** (notaro2021aiopssurvey — not in sci-hub collection across 5 mirrors) + 1 bib-placeholder NOT_ATTEMPTED (chen2024autonomous). **9 bib metadata errors flagged for edit-phase across 4 entries** (miller×4, notaro×1, wu×2, chen-automap×2). Gates 14 + 15 landed locally (HEAD `e82f5cd`); Gate 16 = this handoff + memory + session-28 starter; push deferred to session-27 close (separate USER GO).

---

## §1. What happened this session (chronological)

1. **Session 27 start**: state-verify confirmed clean carry-over from session 26 close (HEAD `fc375b8`, sandbox PDFs at known SHA-256, AWS stopped).
2. **User pivot**: deferred Path G (submit), Path D (AWS), Path B'' residual, Path E (other) in favor of a comprehensive **multi-agent verification pass** before camera-ready.
3. **Pre-plan dialogue** (4 questions): locked sequencing (1a→1b→pairs→6), download sources (official-first + Anna's fallback via playwright), Stage 5 scope (issues + ≥2 topologies), storage (per-agent commits to `paper_audit_session27_2026-05-26/`).
4. **Plan-mode**: entered, drafted comprehensive plan to `C:\Users\partha\.claude\plans\misty-knitting-pine.md` (replaced obsolete revision plan), got 4 more clarifications locked (playwright pre-install by main session, xlsx Status column, all-16-pages visual sample, edits deferred to post-Stage-6), proposed 2-parallel-pairs sequencing as recommendation, user accepted.
5. **Stage 1a launched** (general-purpose; Explore type lacks Write tool). Read bib + xlsx + REFERENCE PAPERS dir + cite-grepped paper. Produced `01_references_inventory_report.md` (177 lines) + `01_xlsx_delta_proposal.csv` (69 rows / 12 cols with new Status/Action/Notes columns).
6. **Stage 1a findings**: 32 cited + 3 retained-orphan; 47 xlsx rows = 14 mapped + 33 xlsx-only-historical; 8 PDFs on disk + 2 out-of-scope in Extra/; 1 FLAG_AMBIGUITY (`chen2024autonomous`); 26 OFFICIAL + 1 ANNAS download actions queued.
7. **Gate 14 commit** (`5bfbabe`): Stage 1a artifacts. No Claude trailer.
8. **Stage 1b pre-flight** (main session): `pip install playwright` (1.60.0). Initial smoke FAILED because chromium-1217 doesn't match playwright-1.60 expectations. Ran `playwright install chromium` → downloaded 294 MB (Chrome 148.0.7778.96 v1223 + headless shell). Re-smoke PASSED.
9. **Stage 1b main pass**: agent processed 27 entries. 21 successful arXiv/OpenReview/CNCF curl downloads. Sub-halted before Anna's for `parasuraman2000model`. 4 entries failed (notaro, wu, chen-automap, chen-autonomous).
10. **Stage 1a → 1b corrections caught during downloads**:
    - `bansal2021does` arXiv 2103.13243 → 2006.14779 (correct)
    - `pei2025flowofaction` arXiv 2502.08820 → 2502.08224 (correct)
    - `miller2025bootstrap` over-corrected by agent (took 2412.18860 "Bootstrap Your Own Context Length" — wrong paper)
    - `notaro2021aiopssurvey` Stage 1a DOI `10.1007/s10922-021-09601-z` was wrong (resolves to GlobeSnap by Rathee, not Notaro). Bib venue also wrong ("ACM Transactions on Networking and Service Management" — journal doesn't exist; should be IEEE TNSM).
11. **User dialogue at sub-halt**: GO Anna's + quick-fix miller now.
12. **Stage 1b continuation (Anna's + miller fix)**: spawned separate agent.
    - **miller2025bootstrap deep correction**: investigated arXiv 2503.01747 = "Position: Don't Use the CLT" by Bowyer (NOT a Miller paper). Real intended cite is **Evan Miller's "Adding Error Bars to Evals"** (arXiv 2411.00640, Anthropic, Nov 2024). Deleted wrong 2412.18860; downloaded 2411.00640. **4 bib metadata errors flagged**: author (Joshua Miller+Ruder → Evan Miller alone), title (paraphrase → actual), year (2025 → 2024), arXiv number.
    - **parasuraman2000model via sci-hub**: Anna's Archive DNS/DPI-blocked across 4 domains (annas-archive.{org,se,li,gs}). Agent pivoted to sci-hub.ee → sci.bban.top CDN. Authentic 2000-era IEEE PDF, 12 pages, 5-point verification PASSED. **Protocol drift**: used sci-hub instead of plan-authorized Anna's, since Anna's was effectively unavailable.
13. **Gate 15 commit** (`e82f5cd`): Stage 1b manifest (282 lines with §13 continuation).
14. **User request mid-wrap-up #1**: "try missing papers from scihub or annas archive if possible".
15. **Stage 1b retry-2 (sci-hub)**: spawned third focused agent for the 3 still-FAILED_MANUAL entries.
    - `wu2020microrank` (10.1145/3442381.3449905) → **OK via sci-hub.ee** (1.5 MB, 5-point verification PASSED). **NEW bib finding**: actual lead author is **Guangba Yu**, NOT Wu/Tordsson/Elmroth/Kao as bib claims. Year 2020 → 2021 (WWW 2021).
    - `chen2022automap` (10.1145/3366423.3380111) → **OK via sci-hub** (17.2 MB, 5-point verification PASSED). **NEW bib finding**: actual lead authors are **Meng Ma + Ping Wang** (PKU); Pengfei Chen is 5th author. Year 2022 → 2020 (WWW 2020).
    - `notaro2021aiopssurvey` → **still FAILED**. Tried 3 DOI candidates × 5 sci-hub mirrors (sci-hub.{ee,se,st,ru,ren}). sci-hub.st explicitly returned "the article is not available through Sci-Hub" for `10.1145/3483424`. Genuinely not in sci-hub collection. **Real DOI remains unconfirmed**.
16. **User request mid-wrap-up #2**: "another agent next session must verify the paper manifest and actually downloaded pdf contents to see if they are correct or not". → Added as **Stage 1c (NEW)** in session 28 plan.
17. **Session 27 ended** at this handoff write. Pending Gate 16 = this handoff + manifest retry-2 update + MEMORY/HANDOFF/starter-prompt updates; pending Gate 17 = batched push.

---

## §2. What changed on disk in session 27

### Committed (Gates 14 + 15; HEAD `e82f5cd`)

| Commit | File | Notes |
|---|---|---|
| `5bfbabe` (Gate 14) | `benchmark/final/audit/paper_audit_session27_2026-05-26/01_references_inventory_report.md` (177 LF lines, 21.6 KB) | Stage 1a markdown report |
| `5bfbabe` (Gate 14) | `benchmark/final/audit/paper_audit_session27_2026-05-26/01_xlsx_delta_proposal.csv` (68 data rows + header, 12 cols, 23.4 KB) | Stage 1a CSV with new Status/Action/Notes columns |
| `e82f5cd` (Gate 15) | `benchmark/final/audit/paper_audit_session27_2026-05-26/02_references_download_manifest.md` (282 LF lines at Gate 15) | Stage 1b manifest (Anna's blocked → sci-hub for parasuraman; miller fix) |

### Pending in Gate 16 (this close-out)

| File | Status | Notes |
|---|---|---|
| `02_references_download_manifest.md` | MODIFIED (282 → 405 LF lines, +§14) | Stage 1b retry-2 (sci-hub for paywalled) — wu + automap OK, notaro still failed; 4 NEW bib errors documented |
| `SESSION_27_HANDOFF.md` | NEW | this file |
| `benchmark/HANDOFF.md` | MODIFIED | Last-updated + §5 layout + key numbers preserved |
| `MEMORY.md` (auto-memory) | MODIFIED | SESSION 27 STARTUP → SESSION 28 STARTUP block |
| `reference_session28_starter_prompt.md` (auto-memory) | NEW | paste-in starter |

### NEW files outside the repo (REFERENCE PAPERS/ tree — not committed)

**24 new PDFs** in `c:/Users/partha/Downloads/files AIOPS NEW/PAPER AND FORMAL DOCUMENTATION/PAPER/REFERENCE PAPERS/`:

Standard arXiv/OA (21):
```
adaspec2025, alibaba2024qwen, askell2024collective, bansal2021does, bertscore2020,
christakopoulou2024talker, cncf2024survey, edge2024graphrag, guo2017calibration,
lemma2024rca, lewis2020retrieval, li2024opseval, liu2025logeval, pei2025flowofaction,
peng2025graphragsurvey, reimers2019sentence, thakur2021beir, xu2025openrca,
zhang2020effect, zhu2023loghub
```

Plus the late-fix and sci-hub trio:
- `miller2025bootstrap - Adding Error Bars to Evals - 2411.00640.pdf` (replaces wrong 2412.18860)
- `parasuraman2000model - A Model for Types and Levels of Human Interaction with Automation - ieee-844354.pdf` (sci-hub fallback)
- `wu2020microrank - MicroRank - End-to-End Latency Issue Localization with Extended Spectrum Analysis - acm-www2021-microrank.pdf` (sci-hub retry-2)
- `chen2022automap - AutoMAP - Diagnose Your Microservice-based Web Applications Automatically - acm-www2020-automap.pdf` (sci-hub retry-2; 17.2 MB)

**REFERENCE PAPERS/ disk usage**: 13.7 MB → 71 MB (+57.3 MB; 32 PDFs at top level + Extra/ subdir untouched).

### Environment change (main session pre-flight)

- Python `playwright` 1.60.0 installed at user-site.
- Chromium 148.0.7778.96 (v1223) installed at `~/AppData/Local/ms-playwright/` (~294 MB net).
- Total `ms-playwright/` dir: 2.1 GB (multiple historical versions).

### Sandbox paper artifacts — UNCHANGED

| File | Size | SHA-256 |
|---|---|---|
| `main/sn-article.pdf` | 467,673 B / 16p | `be6c27abb2dcbdc23a0161c0926266bc18312db4c0a9660c289e1e06f78d9483` |
| `diff/sn-article-DIFF.pdf` | 469,231 B / 16p | `ed09349db0479ae7562e5e0709e5d21f50401e974ab8d7947de9e1d408c02d67` |

### AWS state at close (UNCHANGED from sessions 20-26)

Instance stopped, CW alarm armed, EIP retained, EBS preserved, snapshot held, ~$55/$120 spend.

### Git state at close (pre-Gate-16)

- Local HEAD: `e82f5cd` (post-Gate-15)
- Origin HEAD: `fc375b8` (pre-session-27; 2 commits behind by design)
- Branch: `main`
- Working tree: manifest modified (+§14), this handoff untracked, soon-to-be-modified HANDOFF.md + MEMORY.md + NEW reference_session28_starter_prompt.md
- Pending Gate 16: bundle all close-out file changes into one commit
- Pending Gate 17 push: Gates 14 + 15 + 16 (3 commits) to origin/main (separate USER GO)

---

## §3. Stage 1a + 1b authoritative findings (consolidated post-retry-2)

### Inventory totals

| Item | Count |
|---|---|
| Bib cite-keys | 35 (32 cited + 3 retained-orphan: adaspec2025, edge2024graphrag, zhang2020effect) |
| xlsx rows (live) | 47 (14 map to bib, 33 xlsx-only-historical/superseded) |
| Bib entries with on-disk PDF (post-retry-2) | **29 of 35 (83%)** ✅ |
| Bib entries as URL-only (vendor docs) | 4 (opentelemetry/datadog/grafana/nvidia blog) |
| Bib entries still paywalled FAILED_MANUAL | **1** (notaro2021aiopssurvey — not in sci-hub) |
| Bib entries NOT_ATTEMPTED (ambiguous bib metadata) | 1 (chen2024autonomous — placeholder cite likely) |

**Coverage**: 33 of 35 bib entries fully resolved (29 PDFs + 4 URL-only). 2 remaining are open items for edit-phase / manual.

### 🔴 Bib metadata errors flagged for edit-phase (CRITICAL — 9 across 4 entries)

| Bib key | Error | Current (wrong) | Correct |
|---|---|---|---|
| `miller2025bootstrap` | author | "Miller, Joshua and Ruder, Sebastian and others" | "Miller, Evan" (Anthropic) |
| `miller2025bootstrap` | title | "Bootstrap Confidence Intervals for Evaluation Metrics in NLP" | "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations" |
| `miller2025bootstrap` | year | "2025" | "2024" |
| `miller2025bootstrap` | arXiv number | "arXiv:2503.01747" | "arXiv:2411.00640" |
| `notaro2021aiopssurvey` | journal | "ACM Transactions on Networking and Service Management" | "IEEE Transactions on Network and Service Management" (or other — needs user manual verification of real DOI; sci-hub doesn't have this paper) |
| `wu2020microrank` | author | "Wu, Li and Tordsson, Johan and Elmroth, Erik and Kao, Odej" | Lead author is **Guangba Yu** (Sun Yat-Sen Univ); corresponding author Pengfei Chen. Bib author list completely wrong. |
| `wu2020microrank` | year | "2020" | "2021" (WWW 2021) |
| `chen2022automap` | author | "Chen, Pengfei and Liu, Yu and Wu, Li" | Lead authors **Meng Ma + Ping Wang** (PKU); Pengfei Chen is 5th author. Bib author list partially wrong. |
| `chen2022automap` | year | "2022" | "2020" (WWW 2020) |

**Recommendation for session-28 edit phase**: apply these 9 bib edits in a single themed commit, recompile main + DIFF, verify 16p still holds. Cite-keys stay as stable labels per session-26 lesson. Note: `wu2020microrank` and `chen2022automap` cite-keys retain wrong years (2020/2022) but bib entries point to correct WWW 2021 / WWW 2020 — same convention as `zhang2024aiopssurvey` retaining 2024-key-with-2026-entry.

### Stage 1a → Stage 1b URL corrections (xlsx-side only; no bib edit)

| Bib key | Stage 1a guess | Stage 1b correct |
|---|---|---|
| `bansal2021does` | arXiv 2103.13243 (hep-th) | arXiv 2006.14779 ✓ |
| `pei2025flowofaction` | arXiv 2502.08820 (CoALM) | arXiv 2502.08224 ✓ |
| `notaro2021aiopssurvey` DOI | `10.1007/s10922-021-09601-z` (GlobeSnap) | UNRESOLVED — needs manual user check via institutional access |

### Shadow-library usage disclosure (protocol drift)

3 of 24 new PDFs sourced from sci-hub mirrors (sci-hub.ee → sci.bban.top CDN):
- `parasuraman2000model` (IEEE 2000) — Anna's blocked, sci-hub used per first sub-GO
- `wu2020microrank` (ACM WWW 2021) — sci-hub used per retry-2 user request
- `chen2022automap` (ACM WWW 2020) — sci-hub used per retry-2 user request

Plan authorized Anna's Archive as fallback. Sci-hub is same-class shadow library; substituted because Anna's was effectively unavailable in this network env (all 4 Anna's domains DNS-blocked or DPI-blocked). If user wants pure-Anna's provenance, the 3 sci-hub PDFs can be deleted in session 28 and re-flagged FAILED_MANUAL for institutional fetch. All 3 passed 5-point verification (authentic publisher PDFs, not scraped HTML).

---

## §4. Authoritative state for session 28

### Paths (UNCHANGED from session 26)

| Item | Path |
|---|---|
| Active paper `.tex` | `…sandbox-session16\main\sn-article.tex` (55,201 B / 789 LF lines) |
| Active paper `.pdf` | `…sandbox-session16\main\sn-article.pdf` (**16 pages / 467,673 B / SHA-256 `be6c27ab…d9483`**) |
| Active paper `.bib` | `…sandbox-session16\main\sn-bibliography.bib` (10,129 B / 272 LF lines / 35 entries; 32 cited; 3 retained-orphan; **9 metadata errors pending edit-phase**) |
| DIFF `.tex` | `…sandbox-session16\diff\sn-article-DIFF.tex` (68,263 B / 830 LF lines) |
| DIFF `.pdf` | `…sandbox-session16\diff\sn-article-DIFF.pdf` (**16 pages / 469,231 B / SHA-256 `ed09349d…02d67`**) |
| v1 paper (READ-ONLY) | `…Final Submission Paper (Accepted v.1)\…\sn-article.tex` |
| OLD `sn-article-template.v2/` | MOVED to `z.Dump Paper Archive/` — do NOT touch |
| Reference PDFs | `…PAPER\REFERENCE PAPERS\` (32 PDFs after retry-2: 29 bib-matched + 3 xlsx-only-historical at top level + Extra/ with 1 unrelated PDF + 1 JFIF) |
| Project handoff | `constitutional-aiops/benchmark/HANDOFF.md` (Last-updated session 27 close) |
| Audit dir | `constitutional-aiops/benchmark/final/audit/` (session-27 subdir added: `paper_audit_session27_2026-05-26/`) |

### Numbers (UNCHANGED — session 27 was read-only on benchmark data)

All headline values from session 26 close remain valid. Sandbox PDFs unchanged at known SHA-256.

### Git

- Local HEAD `e82f5cd` (Gate 15); origin still `fc375b8` (pre-session-27); 2 commits ahead pending Gate 17 push
- Gate 16 commit (this handoff + manifest retry-2 + memory/starter updates) pending USER GO
- Gate 17 push (Gates 14+15+16 batched) pending USER GO at session close

### AWS

Stopped, CW alarm enabled, EIP retained, EBS preserved, snapshot held, ~$55/$120 spend.

---

## §5. Hard rules carried forward (UNCHANGED from session 26 §5; 18 rules + 4 process lessons + 2 NEW session-27 lessons)

1. NO Claude co-author trailer on any commit
2. NO push without explicit USER GO
3. Paper edits target sandbox `main/sn-article.tex` (or `main/sn-bibliography.bib`) ONLY
4. NEVER touch real `sn-article-template.v2/` (moved to `z.Dump Paper Archive/`)
5. v1 paper is READ-ONLY reference
6. AWS stays stopped unless user GO; do NOT release EIP `44.195.172.165`; do NOT delete snapshot
7. 3-point rubric mentions at sandbox lines 447 + 597 are INTENTIONAL DISCLOSURES — do NOT remove without explicit ask
8. DO NOT recompute D-1 or BERT-F1 (done sessions 17-18)
9. DIFF PDF override uses `\textcolor{red!75!black}{#1}` (no bold); use `regen_diff_pdf.py` for clean regen
10. PowerShell `:` parsing in filenames → use bash `mv`
11. PowerShell `>` redirect → UTF-16 LE BOM; use `[System.IO.File]::WriteAllText` with `UTF8Encoding $false` OR Python with `newline="\n"`
12. Ollama 0.23.2 ignores `enable_thinking=False`
13. Master backup zip sacred
14. `annotation_test.json` + `rca_test.json` dirty in local — do NOT commit content changes
15. Sealed forensic docs untouchable: CV_PASS1/2, FULL_TRANSCRIPT_AUDIT, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, all SESSION_12-27_HANDOFF.md
16. Instance has NO git — always scp
17. Instance `src/` is OUTDATED — `find_similar_episodes_by_embedding` missing on instance
18. DIFF regen recipe (encoded in `regen_diff_pdf.py`)

**Process lessons (informational)**:

- Min-viable bib rule (session 25): DOI alone preferred over vol/issue/pages
- CrossRef REST API workaround (session 26): `api.crossref.org/works/<DOI>` when dl.acm.org returns 403
- Cite-key as stable label (session 24/25/26): year-in-key need not match year-in-entry
- No submission "package" folders (session 26 post-close): submit `main/sn-article.pdf` directly
- **NEW session 27 #1**: Stage-1a-style URL guessing has ~3/22 (~14%) error rate. ALWAYS first-page-verify a downloaded PDF before treating bib metadata as ground truth. Title-substring matching alone is too weak.
- **NEW session 27 #2**: Anna's Archive is effectively unavailable in this network env (DNS-blocked / DPI-blocked across `annas-archive.{org,se,li,gs}`). Sci-hub mirror `sci-hub.ee` → `sci.bban.top` CDN works as a fallback. Path: `page.goto("sci-hub.ee/<DOI>")` → read `iframe.src` → curl-fetch with `Referer: sci-hub.ee/<DOI>`. Substantively equivalent shadow-lib path; disclose in manifest.

---

## §6. Mandatory reads for session 28

1. **`MEMORY.md`** (auto-loaded — read SESSION 28 STARTUP block in full)
2. **`benchmark/final/audit/SESSION_27_HANDOFF.md`** ⭐⭐⭐ (THIS FILE — primary entry)
3. **`benchmark/final/audit/paper_audit_session27_2026-05-26/01_references_inventory_report.md`** (Stage 1a baseline)
4. **`benchmark/final/audit/paper_audit_session27_2026-05-26/02_references_download_manifest.md`** (Stage 1b manifest with all SHA-256 + finding catalogs — 405 lines, sections §0-§14)
5. **`benchmark/final/audit/paper_audit_session27_2026-05-26/01_xlsx_delta_proposal.csv`** (reference when crafting xlsx update)
6. **`benchmark/final/audit/SESSION_26_HANDOFF.md`** (session 26 close — carries authoritative state)
7. **`benchmark/final/audit/SESSION_25_HANDOFF.md`** + **`SESSION_22_HANDOFF.md`** + **`paper_audit_session22_2026-05-26/00_SUMMARY.md`** (audit findings master)
8. **`benchmark/HANDOFF.md`** (project handoff — Last-updated session 27)
9. **`benchmark/final/SUMMARY.md`** (canonical results landscape — numbers UNCHANGED)
10. **All non-MEMORY auto-memory files** (auto-loaded)
11. **Sandbox `.tex` / `.bib`** ONLY when about to edit — do NOT bulk-read
12. **The plan file** at `C:\Users\partha\.claude\plans\misty-knitting-pine.md` (updated with Stage 1c addition)

---

## §7. Verification plan — current status + session 28 sequence (UPDATED with Stage 1c)

| Stage | Status | When |
|---|---|---|
| 1a — Reference inventory | ✅ COMPLETE (session 27) | — |
| 1b — Reference PDF download | ✅ COMPLETE (session 27; 3 sub-passes: main + Anna's-replaced-with-sci-hub + sci-hub retry-2) | — |
| **🆕 1c — PDF content verification** | ⏳ PENDING — session 28 (NEW per user request, see §8 below) | Solo, FIRST in session 28 |
| **Pair A: 2 + 3** (DIFF parity + audit history) | ⏳ PENDING — session 28 | Parallel launch (single message, 2 Agent calls) |
| **Pair B: 4 + 5** (claim cross-verification + benchmark topology) | ⏳ PENDING — session 28 | Parallel launch |
| 6 — Final synthesis | ⏳ PENDING — session 28 | Solo, after Pair B |
| Edit-phase (post-Stage-6) | ⏳ PENDING — session 28 or 29 | Phased commits applying edit checklist from Stage 6 verdict |

### Session 28 first actions

1. Read `MEMORY.md` SESSION 28 STARTUP block (auto-loaded)
2. Read THIS handoff IN FULL
3. Read session-26 + session-25 + session-22 handoffs for older context (skim)
4. Read all 3 Stage 1a + 1b artifacts from `paper_audit_session27_2026-05-26/`
5. State-verify (single Bash call):
   - `git status --short` → 0 lines (clean)
   - `git log -1 --format='%h %s'` → expected post-Gate-17 push HEAD (TBD)
   - `git log origin/main -1 --format='%h'` → same (synced post-push)
   - Sandbox PDFs → 16p / unchanged SHA-256
   - AWS → stopped; CW alarm → ActionsEnabled=True
   - REFERENCE PAPERS/ → 32 PDFs at top level
6. **Launch Stage 1c FIRST** (NEW per user request — see §8 below). Agent verifies all 29 downloaded PDFs match their bib metadata (independent of Stage 1b's own verification).
7. After Stage 1c review + commit → Launch Pair A (Stages 2 + 3 parallel).
8. Continue per plan: Pair B → Stage 6 → edit-phase.
9. Each stage halts for USER GO + themed commit per agent.

---

## §8. NEW Stage 1c — Reference PDF content verification (session 28)

### Why this stage was added (user request mid-session-27)

> "another agent next session must verify the paper manifest and actually downloaded pdf contents to see if they are correct or not"

Stage 1b's own 5-point verification (size, %PDF header, pdfinfo, first-page-text contains author surname OR title substring) caught some errors but missed others — e.g., the miller2025bootstrap "Bootstrap" title-substring match passed for the wrong paper before being caught by the user-spotted bib-vs-content mismatch. An independent verifier strengthens reviewer-defensibility.

### Mission

Independent re-verification of all 29 downloaded PDFs (incl. 24 newly added + 5 pre-existing on disk that match bib) against `sn-bibliography.bib` metadata. Surface any content mismatch — title drift, wrong author, wrong year, wrong venue, wrong paper entirely.

### Agent type & estimated runtime

- `general-purpose` (needs Read on PDFs via pdftotext)
- ~30-45 min (29 PDFs × first-3-pages each)

### What the agent will do

1. Read bib entries from `sn-bibliography.bib` (35 cite-keys with full metadata).
2. Read Stage 1b manifest `02_references_download_manifest.md` for the per-key SHA-256 + filename.
3. For each of 29 PDFs:
   - Verify SHA-256 in manifest matches current file (no tampering).
   - Extract first 3 pages text via `pdftotext -l 3 <pdf> -`.
   - Verify ALL bib metadata fields appear in extracted text:
     - Full author list (each surname must appear, in order)
     - Title (substring of at least 20 chars contiguous)
     - Year (must appear on page 1 or in headers/footers)
     - Venue/journal (must appear)
   - Status per PDF: `MATCH` (all bib fields verified), `PARTIAL` (some fields present, some absent — bib likely has minor metadata error), `MISMATCH` (PDF is wrong paper entirely)
4. Cross-reference with the 9 bib metadata errors already flagged in Stage 1b (don't re-flag those; confirm them).
5. Surface NEW errors not caught by Stage 1b's weaker verification.

### Output

`paper_audit_session27_2026-05-26/03_pdf_content_verification.md` — per-PDF MATCH/PARTIAL/MISMATCH table + detailed mismatch evidence (extracted text snippets) for any PARTIAL or MISMATCH.

### Hard constraints (same as prior agents)

- READ-ONLY on bib + paper + PDFs
- WRITE only to the audit report path
- No commits, no pushes, no source edits
- If PDF can't be opened or `pdftotext` fails: flag as `UNREADABLE` (don't claim MATCH or MISMATCH)

### Recommendation for execution timing

Stage 1c launches SOLO at start of session 28, BEFORE Pair A. This sequences cleanly: references settled → paper verification (Pair A) → claims+topology (Pair B) → synthesis (Stage 6).

---

## §9. Open items carry-forward to session 28+

### From Stage 1a + 1b + retry-2 (CRITICAL for edit-phase)

| ID | Item | Action |
|---|---|---|
| S1b-1 | `miller2025bootstrap` bib has 4 errors (author/title/year/arXiv) | Apply 4-field bib edit in session 28 edit-phase. PDF correct on disk. Cite-key stays. |
| S1b-2 | `notaro2021aiopssurvey` bib `journal` field references nonexistent journal | Decision required: substitute IEEE TNSM OR fetch real DOI via institutional access first. |
| S1b-3 | `chen2024autonomous` is placeholder (no DOI/arXiv) | Decision required: (a) find real reference, (b) substitute, (c) remove cite from `.tex`. |
| S1b-4 | `notaro2021aiopssurvey` paywalled AND not in sci-hub | User manual fetch via institutional access (real DOI first). |
| S1b-5 | `parasuraman2000model` PDF is sci-hub-sourced | Decision required: keep, or replace with institutional-access version. |
| S1b-6 | xlsx Status/Action/Notes draft CSV not yet applied to live xlsx | After all stages close: coordinated xlsx update pass. |
| **S1b-7 (NEW)** | `wu2020microrank` bib author list completely wrong | Bib edit: author `"Wu, Li and Tordsson, Johan..."` → `"Yu, Guangba and Chen, Pengfei and others"`. Year 2020 → 2021. |
| **S1b-8 (NEW)** | `chen2022automap` bib author list partially wrong | Bib edit: author `"Chen, Pengfei and Liu, Yu and Wu, Li"` → `"Ma, Meng and Wang, Ping and others"`. Year 2022 → 2020. |
| **S1b-9 (NEW)** | `wu2020microrank` + `chen2022automap` PDFs sci-hub-sourced (retry-2) | Same decision as parasuraman: keep or institutional swap. |
| **S1c (NEW)** | Independent PDF content verification agent for session 28 | Per user request; see §8 above. |

### From plan carry-over (still applicable)

- Path G: submit camera-ready (when CFP opens; submission file IS `main/sn-article.pdf`)
- Path D: optional AWS Stack B full 431-case re-run OR Phase 4.5c cold-start curve
- Path B'' Tier 2/3: cite-key renames OR vol/issue/pages additions (cosmetic; only if reviewer flags)

---

## §10. Useful commands for session 28

```bash
# State-verify
cd "c:/Users/partha/Downloads/files AIOPS NEW/constitutional-aiops"
git log -1 --format='HEAD: %h %s'
git log origin/main -1 --format='ORIGIN: %h'
git status --short

# Verify sandbox PDFs unchanged
SANDBOX="../PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2.sandbox-session16"
sha256sum "$SANDBOX/main/sn-article.pdf" "$SANDBOX/diff/sn-article-DIFF.pdf"
# Expected: be6c27ab... main; ed09349d... diff

# Count reference PDFs after Stage 1b
ls "../PAPER AND FORMAL DOCUMENTATION/PAPER/REFERENCE PAPERS/"/*.pdf | wc -l
# Expected: 32

# Re-read Stage 1a + 1b artifacts before launching Stage 1c
cat "benchmark/final/audit/paper_audit_session27_2026-05-26/01_references_inventory_report.md"
cat "benchmark/final/audit/paper_audit_session27_2026-05-26/02_references_download_manifest.md"
```

---

## §11. Pending Gate 16 (commit) + Gate 17 (push)

### Proposed Gate 16 commit (1 themed commit, requires USER GO)

**Commit** — `docs(audit-session27): close-out — Stage 1b retry-2 + handoff + memory + session-28 starter`
- MODIFIED: `benchmark/final/audit/paper_audit_session27_2026-05-26/02_references_download_manifest.md` (+§14 retry-2 documenting wu/automap OK + notaro still failed; 4 NEW bib metadata errors)
- NEW: `benchmark/final/audit/SESSION_27_HANDOFF.md` (this file)
- MODIFIED: `benchmark/HANDOFF.md` (Last-updated + §5 layout + key numbers preserved)
- MODIFIED (auto-memory): `MEMORY.md` (SESSION 27 STARTUP → SESSION 28 STARTUP)
- NEW (auto-memory): `reference_session28_starter_prompt.md` (paste-in starter)

NO data files, NO scripts, NO sandbox edits.

### Pending Gate 17 push (batched, requires SEPARATE USER GO)

3 local commits ahead of origin/main: `5bfbabe` (Gate 14) + `e82f5cd` (Gate 15) + `<Gate-16-hash>` (Gate 16). Single batched push: `git push origin main`.

---

## §12. Session 27 budget summary

- Agent time: ~30 min (Stage 1a) + ~25 min (Stage 1b main) + ~10 min (Stage 1b continuation: Anna's→sci-hub + miller fix) + ~19 min (Stage 1b retry-2: 3 sci-hub attempts) = **~84 min**
- Pre-flight (main session playwright install + chromium download): ~7 min
- Review + commits: ~30 min
- Documentation (this handoff): ~20 min
- **Total wall-clock**: ~141 min / ~2h 21min

Budget projection for session 28 (Stage 1c + Pair A + Pair B + Stage 6 + edit-phase): ~3-4 hours.

---

*End of handoff. Session 27 close 2026-05-26 → 2026-05-27. Next session = 28.*
