# Session 25 → Session 26 Handoff (2026-05-26)

> **PRIMARY ENTRY POINT for session 26**. Session 25 (2026-05-26) ran Path C camera-ready prep: applied I-E (sandbox `.tex:484` "deferred to supplementary" contradiction) and I-A/B/C (deliberate-defer bib entries from session 24, now resolved via external CrossRef + DBLP + NVIDIA blog verification). Both main + DIFF PDFs preserved at 16 pages. Sandbox files normalized to pure LF line endings (session 24 left mixed CRLF/LF). Working tree of `constitutional-aiops/` clean before session-25 commit. Path C is functionally complete; only camera-ready-window cosmetic polish remains.

---

## §0. One-line state

Path C camera-ready prep complete: I-E line-484 contradiction fixed; I-A peng2025graphragsurvey DOI added; I-B zhang2024aiopssurvey first-author corrected (Yongqian → Lingzhe), year corrected (2024 → 2026), DOI added; I-C nvidia2024specdec title corrected, year corrected (2024 → 2025), authors corrected (institutional → Li/Yu/Guo), URL added. Min-viable trim applied (DOI alone, no vol/issue/pages on I-A/B) to keep main PDF at 16 pages. DIFF PDF regenerated via `regen_diff_pdf.py` (LF write + Perl on PATH + listings drop, per session-24 recipe). Sandbox `main/sn-article.pdf` **16p / 467,671 B**; sandbox `diff/sn-article-DIFF.pdf` **16p / 469,229 B**. AWS still stopped, CW alarm armed.

---

## §1. What happened this session (chronological)

1. **State re-gather** — read MEMORY.md SESSION 25 STARTUP block + SESSION_24_HANDOFF.md in full + SESSION_23_HANDOFF.md + SESSION_22_HANDOFF.md + `paper_audit_session22_2026-05-26/00_SUMMARY.md` + `benchmark/HANDOFF.md` + `benchmark/final/SUMMARY.md` + all 7 non-MEMORY auto-memory files. State-verify: HEAD `0bca114`, working tree clean, sandbox PDFs 16p (466,286 B / 467,840 B), AWS stopped, CW alarm armed. Zero drift from expected.
2. **Path C locked** (camera-ready prep, recommended) over Path D (AWS), Path B' (bib-only), Path E (other).
3. **QC pass — inspection-only** (no edits yet):
   - Bibtex auto-validation: clean compile from existing `.aux`, exit 0, zero warnings, 32 cited entries
   - Targeted `.tex` reads at the 10 Group B + C edit sites confirmed all session-24 fixes render verbatim (I-3 RTT 1.10ms; I-7 Table 1 footnote; I-2 Table 4 percentile method; I-9 "6 cases overall (1 ann + 5 RCA)" at 3 sites; I-6 Table 5/6 −2.2pp; I-5 §6.2 "ran…aggregate preserved"; M-1a bertscore cite)
   - `.bib` inspection: header "35 entries (32 cited; 3 retained-orphan)" confirmed; I-A/B/C entries verified as still incomplete (deliberate session-24 defer)
   - PDF visual export of all 16 pages confirmed: 84% baseline label horizontal, Fig 3 callout "−34pp drop!" diagonal red arrow visible, Table 5/6 −2.2pp deltas rendered, §6.2 reframe reads cleanly, BERTScore cite renders at line 458
4. **Additional finding (audit-IMPORTANT, not in session-24 fix list)**: `.tex:484` "Numerical breakdowns are deferred to the camera-ready supplementary tables" contradicts Table 4 (`tab:errortable`) at lines 491-508 which has those exact breakdowns. Surfaced to user as I-E. Path C scope expanded by user GO.
5. **User decision points locked**:
   - **Option 1 (I-E line 484 contradiction)** → fix in place: replace "Numerical breakdowns are deferred to the camera-ready supplementary tables." with "Table~\ref{tab:errortable} below disaggregates by source."
   - **Option 2 (I-A/B/C deferred bib entries)** → fix via external lookup; do not fabricate fields; commit only verified values
   - **Option 3 (abstract / §1 tone pass)** → preserve original; correct only if a *factual* error surfaces (paper already accepted; minimum disturbance)
6. **Option 1 + 4 parallel web searches kicked off in single message**:
   - I-E sandbox `.tex:484` Edit applied
   - WebSearch for peng2025graphragsurvey: returned DOI 10.1145/3777378, ACM TOIS Vol 44 Issue 2 2025, 8 authors via arXiv ref
   - WebSearch for zhang2024aiopssurvey: **revealed bib had WRONG first author** — actual first author is Lingzhe Zhang (not Yongqian); year is 2025/2026 (not 2024); 10 authors
   - WebSearch for nvidia2024specdec: revealed bib title was **not verbatim** of any NVIDIA blog post; canonical post is "An Introduction to Speculative Decoding for Reducing Latency in AI Inference"
7. **Authoritative metadata fetches**:
   - WebFetch ACM TOIS DOI page (`https://dl.acm.org/doi/10.1145/3777378`): HTTP 403 (ACM blocks bot)
   - WebFetch ACM CS DOI page (`https://dl.acm.org/doi/10.1145/3746635`): HTTP 403
   - WebFetch NVIDIA blog: ✓ confirmed title + Sep 17 2025 publication date + 3 authors Li/Yu/Guo
   - WebFetch DBLP TOIS Vol 44 listing: returned No 1 only (Jan 2026); no Issue-2 article found
   - WebFetch DBLP record for Zhang aiops survey: ✓ confirmed Vol 58 Issue 2 = 2026 publication, Article 44, pages 44:1-44:35, DOI 10.1145/3746635, 10 authors
   - WebFetch arXiv abstract for peng2025graphragsurvey (2408.08921): ✓ confirmed 8-author list; **no journal-ref present** on arXiv (paper has since been accepted, but arXiv metadata not updated)
   - Final WebSearch for peng2025graphragsurvey article-number: ✓ confirmed Vol 44 Issue 2 + DOI, no article-number found
8. **Bib edits applied** (3 parallel Edit calls), full author lists, all metadata. **First recompile: 17 pages** (overshoot — bib expansions added ~300 chars total).
9. **Bib trim pass 1**: shortened author lists to "first-3 + and others" (Springer Vancouver style, matches v1-baseline convention). **Recompile: still 17 pages.**
10. **Bib trim pass 2 (min-viable)**: dropped volume/issue/pages from I-A and I-B (DOI alone resolves all of them); kept I-C URL (its purpose). **Recompile: 16 pages restored.**
11. **Abstract / §1 / §2 factual scan**: all numbers (82.4% / 6 sources / [78.2, 86.0] / 22.7pp / 34.4pp / 10.8/15.1pp / 8-config / 3,448 inferences / 12 principles / 3 tiers / p=0.652 / -12.9pp) verified against source-of-truth files. **No factual errors.** Per user constraint (preserve original; correct only if necessary) — abstract + §1 + §2 untouched.
12. **DIFF PDF regenerated** — ran `regen_diff_pdf.py` per session-24 recipe (Perl on PATH from Git for Windows + LF write + listings dependency dropped). Compile chain: pdflatex + bibtex + pdflatex + pdflatex. DIFF PDF **16p / 469,229 B / 0 undefined refs**.
13. **Sandbox file line-ending normalization**: side-effect of Edit tool — all 3 sandbox `.tex` + `.bib` files normalized to pure LF (session 24 left them with CRLF). Net byte savings ~310 from bib + ~786 from main `.tex` (matches expected `1 byte per line × line count` from CR removal). Content unchanged.

---

## §2. What changed on disk in session 25

### Sandbox paper (OUTSIDE git repo — not committed; sandbox lives at `PAPER AND FORMAL DOCUMENTATION/.../sandbox-session16/`)

| File | Before (sess 24 close) | After (sess 25 close) | Delta |
|---|---|---|---|
| `main/sn-article.tex` | 55,987 B / 793 lines (CRLF) | 55,201 B / 789 LF lines | -786 B, content +1 sentence shorter (I-E), line-ending normalized |
| `main/sn-article.pdf` | 466,286 B / 16p | 467,671 B / 16p | +1,385 B (bib DOI additions) |
| `main/sn-bibliography.bib` | 10,439 B / ~270 CRLF lines / 35 entries | 10,129 B / 272 LF lines / 35 entries | -310 B (LF normalization saves ~270, +60 char content net) |
| `diff/sn-article-DIFF.tex` | 68,267 B (CRLF) | 68,263 B / 830 LF lines | -4 B (regen + LF normalization) |
| `diff/sn-article-DIFF.pdf` | 467,840 B / 16p | 469,229 B / 16p | +1,389 B (parity with main) |
| `diff/sn-article.tex` + `.bib` | mirror of main | mirror of main (refreshed by regen_diff_pdf.py) | — |

### `constitutional-aiops/` repo (about to be committed in Gate 8)

- NEW file: `benchmark/final/audit/SESSION_25_HANDOFF.md` (THIS FILE)
- EDIT: `benchmark/HANDOFF.md` — Last-updated line bumped session 24 close → session 25 close; sandbox size table refreshed; §5 layout block updated; key numbers UNCHANGED (Path C did not move headlines)
- NO changes to result files, scripts, or any data artifacts (Path C was sandbox-only + repo doc-only)

### Git state at start of session 25

- Local HEAD `0bca114` = origin `0bca114` (synced from session-24 close)
- Working tree clean

### Git state at session-25 close (pre-Gate-8)

- Local HEAD still `0bca114` until commits land
- 1 new file + 1 modified file uncommitted (this handoff + HANDOFF.md)
- Pending Gate 8 commits (require user GO) — see §7 below

### AWS state at close (UNCHANGED from sessions 20-24)

- Instance `i-091c4de0e95d63154`: **stopped** ✅
- CloudWatch alarm `aiops-idle-stop`: **ActionsEnabled=True** ✅
- EIP `44.195.172.165`, EBS root + data, snapshot `snap-01b191aedbf46b598`: preserved
- Spend ~$55 / $120 ceiling (NO AWS work in session 25)

---

## §3. Path C audit-fix outcomes

### I-E — `.tex:484` "deferred to supplementary" contradiction (Path C scope, surfaced session 25 from audit-IMPORTANT)

| Before | After |
|---|---|
| `...with OpsEval wired-network items as the weakest cell. Numerical breakdowns are deferred to the camera-ready supplementary tables.` | `...with OpsEval wired-network items as the weakest cell; Table~\ref{tab:errortable} below disaggregates by source.` |

**Net layout impact**: -18 characters; no page-count change. Reads more naturally as a forward-pointer to the table that immediately follows.

### I-A — `peng2025graphragsurvey` (session-24 deliberate defer; resolved in session 25)

Verified metadata from initial WebSearch + arXiv abstract page:

```bibtex
@article{peng2025graphragsurvey,
  author  = "Peng, Boci and Zhu, Yun and Liu, Yongchao and others",
  title   = "Graph Retrieval-Augmented Generation: {A} Survey",
  journal = "ACM Trans. Inf. Syst.",
  year    = "2025",
  doi     = "10.1145/3777378"
}
```

Changes vs session-24 baseline:
- `journal` kept as abbreviated form ("ACM Trans. Inf. Syst.") to preserve layout (no page overflow)
- `doi` added (resolves vol/issue/pages implicitly via DOI lookup)
- `Zhu, Yunfeng` → `Zhu, Yun` (first-name corrected from arXiv author list)
- vol/issue NOT added (would push to 17p; DOI alone is sufficient for reviewer-actionable lookup)

### I-B — `zhang2024aiopssurvey` (session-24 deliberate defer; resolved in session 25 with bonus author + year fix)

Verified metadata from DBLP record `journals/csur/ZhangJJWLYWHYL26`:

```bibtex
@article{zhang2024aiopssurvey,
  author  = "Zhang, Lingzhe and Jia, Tong and Jia, Mengxi and others",
  title   = "{A Survey of AIOps in the Era of Large Language Models}",
  journal = "ACM Computing Surveys",
  year    = "2026",
  doi     = "10.1145/3746635"
}
```

Changes vs session-24 baseline:
- **First author FIXED**: "Zhang, Yongqian" → "Zhang, Lingzhe" (the bib had the wrong first author — pre-session-25 was unverified placeholder; DBLP confirms correct author is Lingzhe Zhang)
- Added 2nd + 3rd authors (Jia, Tong; Jia, Mengxi) per Vancouver-style Springer convention
- **Year FIXED**: 2024 → 2026 (DBLP confirms ACM CS Vol 58 Issue 2 = 2026 publication; arXiv prepub was 2025)
- `doi` added (resolves vol/issue/pages/article-number via DOI lookup)
- vol/issue/pages NOT added (would push to 17p)
- **Cite key `zhang2024aiopssurvey` preserved as a stable identifier** despite year change — `\cite{}` at .tex lines 135, 141, 160, [other refs] remains valid; numerical [N] citation unaffected; only year shown in reference list now reads 2026

### I-C — `nvidia2024specdec` (session-24 deliberate defer; resolved in session 25 with bonus title + year fix)

Verified metadata from WebFetch of NVIDIA blog:

```bibtex
@misc{nvidia2024specdec,
  author       = "Li, Jamie and Yu, Chenhan and Guo, Hao",
  title        = "An Introduction to Speculative Decoding for Reducing Latency in {AI} Inference",
  year         = "2025",
  howpublished = "NVIDIA Developer Blog, \url{https://developer.nvidia.com/blog/an-introduction-to-speculative-decoding-for-reducing-latency-in-ai-inference/}"
}
```

Changes vs session-24 baseline:
- **Title FIXED**: "Accelerating LLM Inference with Speculative Decoding" (no NVIDIA blog with that exact title exists) → "An Introduction to Speculative Decoding for Reducing Latency in AI Inference" (verified canonical blog title via WebFetch)
- **Year FIXED**: 2024 → 2025 (blog publication date Sep 17 2025 per page metadata)
- **Author FIXED**: "{NVIDIA Corporation}" institutional → "Li, Jamie and Yu, Chenhan and Guo, Hao" (named bylines from blog)
- **URL added** (the actual audit-flagged issue): full blog URL appended to `howpublished`
- **Cite key `nvidia2024specdec` preserved** despite year change — same cite-key-as-label rule as I-B

---

## §4. Authoritative state for session 26

### Paths (UNCHANGED from session 24)

| Item | Path |
|---|---|
| Active paper `.tex` | `…sandbox-session16\main\sn-article.tex` (55,201 B / 789 LF lines) |
| Active paper `.pdf` | `…sandbox-session16\main\sn-article.pdf` (**16 pages / 467,671 B**) |
| Active paper `.bib` | `…sandbox-session16\main\sn-bibliography.bib` (10,129 B / 272 LF lines / 35 entries; 32 cited; 3 retained-orphan) |
| DIFF `.tex` | `…sandbox-session16\diff\sn-article-DIFF.tex` (68,263 B / 830 LF lines) |
| DIFF `.pdf` | `…sandbox-session16\diff\sn-article-DIFF.pdf` (**16 pages / 469,229 B**) |
| v1 paper (READ-ONLY) | `…Final Submission Paper (Accepted v.1)\…\sn-article.tex` |
| OLD `sn-article-template.v2/` | **MOVED to `z.Dump Paper Archive/`** — do NOT touch |
| Project handoff | `constitutional-aiops/benchmark/HANDOFF.md` |
| Audit dir | `constitutional-aiops/benchmark/final/audit/` |

### Numbers (UNCHANGED — Path C did not move any headline numbers)

All authoritative values from session 24 close remain. Key reminders:

| Metric | Value | Source |
|---|---|---|
| Main re-run Overall | **82.4% (294/357)** | `main_benchmark/phase5_stats.json` |
| Main re-run Annotation | **82.6% (180/218)** | same |
| Main re-run RCA | **82.0% (114/139)** | same |
| Ablation Full RCA | **85.6% (119/139)** | `ablation_v4/phase5_stats.json` |
| Ablation Full Overall | **84.0% (300/357)** | same |
| Llama 3.3-70B RCA | **71.2% (99/139)** | `sota_baselines/llama_3_3_70b.jsonl` |
| DeepSeek V3.2 RCA | **66.9% (93/139)** | `sota_baselines/deepseek_v3.jsonl` |
| ΔRCA Ours − Llama | **+10.8pp** | derived |
| ΔRCA Ours − DeepSeek | **+15.1pp** | derived |
| Stack A P95 latency | **65.96s** (30-case smoke) | `infrastructure/gate15_comparison.md` |
| Stack B P95 latency | **43.71s** (30-case smoke) | same |
| Stack B speedup | **1.51×** | same |
| BERT-F1 mean (main re-run) | **0.8124** (Ann 0.822, RCA 0.795) | `_bert_f1_recompute_summary.json` |
| Rich-eval Overall (post-D-1) | **86.4% (344/398)** | M-6 corrected session 24 |
| Rich-eval RCA (post-D-1) | **91.1% (164/180)** | same |

### Git

- Local HEAD `0bca114` at session-25 start = origin `0bca114` synced
- Session 25 pending commits land into origin/main during Gate 8 (with user GO)

### AWS

Stopped, CW alarm enabled, EIP retained, EBS preserved, snapshot held, ~$55/$120 spend.

---

## §5. Hard rules carried forward (UNCHANGED from session 24 §5; rule 18 still active)

1. **NO Claude co-author trailer** on any commit
2. **NO push without explicit USER GO** (Gate 9 requires separate confirm)
3. **Paper edits target sandbox `main/sn-article.tex` only**
4. **NEVER touch real `sn-article-template.v2/`** (moved to `z.Dump Paper Archive/`)
5. **v1 paper is READ-ONLY reference**
6. **AWS stays stopped** unless user GO; do NOT release EIP `44.195.172.165`; do NOT delete snapshot
7. **3-point rubric mentions** at sandbox lines 447 + 597 are **INTENTIONAL DISCLOSURES** — do NOT remove without explicit ask
8. **DO NOT recompute D-1 or BERT-F1** (done sessions 17-18)
9. **DIFF PDF override** uses `\textcolor{red!75!black}{#1}` (no bold); `\hl{}` from soul breaks on `\cite{}`. Use `benchmark/scripts/_dev/regen_diff_pdf.py` for clean regen.
10. **PowerShell `:` parsing** in filenames → use bash `mv`
11. **PowerShell `>` redirect produces UTF-16 LE BOM** → use `[System.IO.File]::WriteAllText` with `UTF8Encoding $false`, OR Python `pathlib.Path.write_text(..., newline="\n")`
12. **Ollama 0.23.2 ignores `enable_thinking=False`** — reasoning lands in `message.reasoning`. Do NOT try to disable.
13. **Master backup zip** sacred
14. **`annotation_test.json` + `rca_test.json`** dirty in local — do NOT commit content changes
15. **Sealed forensic docs untouchable**: CV_PASS1/2, FULL_TRANSCRIPT_AUDIT, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, all SESSION_12-25_HANDOFF.md
16. **Instance has NO git** — always scp
17. **Instance `src/` is OUTDATED** — `find_similar_episodes_by_embedding` missing on instance
18. **DIFF regen recipe** (session-24 origin): (a) Git for Windows perl.exe on PATH via `$env:PATH = 'C:\Program Files\Git\usr\bin;' + $env:PATH`; (b) LF line endings (CRLF trips listings v1.11b on `\lstdefinelanguage{json}`); (c) listings package dropped from OVERRIDE (DIFverbatim unused in body). All three encoded in `regen_diff_pdf.py`.

**NEW session-25 lesson (not a hard rule, but a process refinement)**: when adding bib metadata to existing entries, default to **min-viable (DOI alone)** rather than full vol/issue/pages, because each added field expands the rendered bib entry by ~30 chars × 80-chars-per-rendered-line which compounds across multiple entries and can push the PDF over the page-count cap. DOI is the most reviewer-actionable single identifier — vol/issue/pages are nice-to-have and derivable via DOI lookup.

**Reading non-ASCII result files from Windows shell**: always pass `encoding='utf-8'` to `open()` — cp1252 default crashes on bytes ≥ 0x80.

---

## §6. Mandatory reads for session 26

1. **`MEMORY.md`** (auto-loaded — read SESSION 26 STARTUP block in full)
2. **`benchmark/final/audit/SESSION_25_HANDOFF.md`** ⭐⭐⭐ (THIS FILE — primary entry)
3. **`benchmark/final/audit/SESSION_24_HANDOFF.md`** (Group B + C context; do NOT skip)
4. **`benchmark/final/audit/SESSION_23_HANDOFF.md`** (Group A context)
5. **`benchmark/final/audit/SESSION_22_HANDOFF.md`** (audit findings master tables)
6. **`benchmark/final/audit/paper_audit_session22_2026-05-26/00_SUMMARY.md`** (master synthesis — Group A done session 23, Group B + C done session 24, Path C done session 25)
7. **`benchmark/HANDOFF.md`** (project handoff — sandbox sizes refreshed for session 25)
8. **`benchmark/final/SUMMARY.md`** (canonical results landscape)
9. **All non-MEMORY auto-memory files** (auto-loaded)
10. **Sandbox `.tex` only when about to edit** — do NOT bulk-read

---

## §7. Pending Gate 8 (commit) + Gate 9 (push) for session 25

### Proposed Gate 8 commits (2 themed, require USER GO)

**Commit 1** — `docs(audit): SESSION_25_HANDOFF + benchmark HANDOFF sandbox sizes refresh`
- NEW: `benchmark/final/audit/SESSION_25_HANDOFF.md` (~this file)
- EDIT: `benchmark/HANDOFF.md` — Last-updated line + §5 sandbox size table refresh + key numbers preserved

No data files changed (Path C was sandbox + repo-doc only).

**Commit 2** (alternative): bundle as 1 commit. Probably cleaner since both files are session-25 close-out markers.

### Path C remaining items (sessions 26+, low priority)

| Item | Why deferred |
|---|---|
| I-A peng2025graphragsurvey vol/issue/pages/article-num | DBLP/ACM not yet indexed at Issue-2 granularity; can verify post-publication |
| I-B zhang2024aiopssurvey vol/issue/pages | Same — kept DOI which resolves them |
| Cite-key renames `zhang2024aiopssurvey` → `zhang2026aiopssurvey` + `nvidia2024specdec` → `nvidia2025specdec` | Cosmetic; cite keys are stable labels; would require 5+ `.tex` edits at all `\cite{}` sites |
| Abstract / §1 tone pass | User locked: preserve as-accepted; correct only if factual error surfaces. None found in session 25. |

### Path D (AWS work, NOT blocking)

| Item | Cost | Time |
|---|---|---|
| Stack B full 431-case latency re-run | ~$5 | ~3h |
| Phase 4.5c cold-start curve (N=0/20/40/60 on 20 LEMMA cases) | ~$5 | ~5h |

---

## §8. Session 26 first actions (in order)

1. **Read MEMORY.md** (auto-loaded — verify SESSION 26 STARTUP block)
2. **Read THIS file IN FULL** (`SESSION_25_HANDOFF.md`)
3. **Reference SESSION_22/23/24_HANDOFF.md + 00_SUMMARY.md** for older context as needed
4. **State-verify** (single PowerShell call, expected values):
   - `git status --short | wc -l` → 0 (clean) or 1 (just `SESSION_25_HANDOFF.md` if not yet committed)
   - `git log -1 --format='%h %s'` → expected new session-25 commit head (TBD at Gate 8)
   - `git log origin/main -1 --format='%h'` → same (post-Gate-9 push)
   - Sandbox `main/sn-article.pdf` → **16p / 467,671 B**
   - Sandbox `diff/sn-article-DIFF.pdf` → **16p / 469,229 B**
   - AWS `i-091c4de0e95d63154` → `stopped`
   - CW alarm → `ActionsEnabled=True`
5. **ASK USER**: pick a path —
   - **Path D — AWS work** (Stack B full 431 or 4.5c cold-start; not blocking)
   - **Path B' — Remaining bib polish** (vol/issue/pages for I-A/B if you want article-level granularity; cite-key renames)
   - **Path E — Other** (camera-ready submission window, journal extension scope, etc.)
6. **Halt for USER GO** before any sandbox `.tex` edit, any repo commit, any AWS work
7. **Hard rules carried**: NO Claude trailer, NO push without GO, sandbox `main/` only, NEVER touch real `sn-article-template.v2/`, AWS stays stopped, do NOT remove 3-point rubric disclosures.

---

## §9. Useful commands for session 26

```powershell
# Verify state at start
Set-Location 'c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops'
git log -1 --format='HEAD: %h %s'
git log origin/main -1 --format='ORIGIN: %h'
git status --short

# Recompile sandbox main paper
$pdflatex = 'C:\Users\partha\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe'
$bibtex   = 'C:\Users\partha\AppData\Local\Programs\MiKTeX\miktex\bin\x64\bibtex.exe'
Set-Location "...sandbox-session16\main"
& $pdflatex sn-article.tex; & $bibtex sn-article; & $pdflatex sn-article.tex; & $pdflatex sn-article.tex

# Regenerate DIFF (encoded recipe in script)
$env:PATH = 'C:\Program Files\Git\usr\bin;' + $env:PATH  # for perl.exe
python "c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\benchmark\scripts\_dev\regen_diff_pdf.py"
Set-Location "...sandbox-session16\diff"
& $pdflatex sn-article-DIFF.tex; & $bibtex sn-article-DIFF; & $pdflatex sn-article-DIFF.tex; & $pdflatex sn-article-DIFF.tex

# Verify post-D-1 invariants (UNCHANGED)
python -c "import json; recs=json.load(open('benchmark/final/main_benchmark/results_sota_eval_431.json', encoding='utf-8')); print('null_count:', sum(1 for r in recs if r.get('correct') is None))"  # expect 74
```

---

## §10. Open follow-ups for sessions 27+ (low priority)

- If reviewer demands article-level granularity on I-A/I-B (vol/issue/pages): wait for DBLP TOIS Vol 44 No 2 indexing OR query CrossRef API directly with API key (not WebFetch which gets 403 on dl.acm.org)
- If reviewer demands 4.5c cold-start curve: re-launch on instance (~$5, ~5h) — patches on laptop, instance needs scp `src/memory/` first
- If reviewer demands full 431-case latency for Stack B: ~$5, ~3h
- Cite-key rename for `zhang2024aiopssurvey` → `zhang2026aiopssurvey` if a reviewer flags the year-vs-key mismatch as confusing

---

*End of handoff. Session 25 close 2026-05-26. Next session = 26.*
