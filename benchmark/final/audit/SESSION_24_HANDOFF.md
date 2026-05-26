# Session 24 → Session 25 Handoff (2026-05-26)

> **PRIMARY ENTRY POINT for session 25**. Session 24 (2026-05-26, ~3h elapsed) applied the full **Group B** (10 should-fix items: 7 reviewer-surface + 3 deliberate-defer + 1 deliberate-skip) and **Group C** (5 polish items) fix sets from the session-22 paper audit. Both PDFs preserved at 16 pages. DIFF PDF regenerated from scratch with root-cause fixes (CRLF + listings v1.11b incompatibility). 4 themed Gate 6 commits applied and pushed `affad56..dd51724 main -> main`. AWS untouched. Remaining work: Path C camera-ready prep, Path D AWS re-runs, or deliberate-defer bib items.

---

## §0. One-line state

Group B + Group C audit fixes applied; sandbox `main/sn-article.pdf` **16p / 466,286 B**; sandbox `diff/sn-article-DIFF.pdf` **16p / 467,840 B**; 4 themed commits landed and pushed (`affad56..dd51724 main -> main`); 8 ablation rich-eval results.json files relabeled (264 task_type flips: rca→qa_mcq for 33 OpsEval-remined cases); benchmark_431_seed42.json header refreshed; SUMMARY.md M-6 rich-eval RCA/Overall corrected post-D-1; bertscore2020 cited at §5.2; karpukhin2020dense dropped from bib; stale phase45_graph/exp_4_5c_summary.json renamed `_STALE_session17.json`; MANIFEST.md SHA refreshed for the changed dataset entry. AWS still stopped, CW alarm armed.

---

## §1. What happened this session (chronological)

1. **State re-gather** — read MEMORY.md SESSION 24 STARTUP block, SESSION_23_HANDOFF.md in full, SESSION_22_HANDOFF.md (audit context), 00_SUMMARY.md (Group B/C pending). State-verify: HEAD `affad56`, working tree clean, sandbox PDFs at session-23 sizes (463,353 / 464,912 B), AWS stopped, CW alarm armed.
2. **Path A locked** (Group B fixes, recommended) over Path B (Group C), Path C (camera-ready prep), Path D (AWS).
3. **4 decision points locked** for Group B (after dialogue):
   - **I-8** (BERT-F1 in Tables 5/6/7) → Option C: leave as-is (already in Table 2 + §5.2 prose covers Table 7 baselines)
   - **I-4** (alibaba2024qwen bib) → update title to "Qwen Technical Report (Qwen3 Series)" + year 2025 (keep cite key `alibaba2024qwen`)
   - **I-A/B/C** (peng2025graphragsurvey / zhang2024 / nvidia2024 bib fields) → defer to camera-ready (no fake-field invention; needs external lookup)
   - **Plan** → 2 batches: Batch 1 low-risk mechanical, Batch 2 prose
4. **Batch 1 applied** (8 edits): I-6 Table 5/6 −2.1→−2.2pp (2 cells); I-9 5→6 cases at 3 sites; I-3 RTT 1.95→1.10ms; I-D bib header "26 references"→"36 entries (31 cited; 5 retained-orphan)"; I-4 alibaba bib title/year. Recompile: main PDF 16p / 463,475 B. ✓
5. **Batch 2 applied** (3 edits): I-5 §6.2 "planned"→"ran to completion and saturated (aggregate preserved; per-case logs lost to post-run serialization bug)"; I-7 Table 1 new footnote (213 = 180 rca + 33 qa_mcq, 74 excluded, 139 evaluable); I-2 Table 4 footnote append "Percentiles use index-floor convention …; linear-interpolation values differ by <0.3s". Recompile: main PDF **16p / 465,732 B / +2,379 B** vs session-23 close. ✓
6. **DIFF regen** — wrote `benchmark/scripts/_dev/regen_diff_pdf.py` (idempotent regen wrapper). First run crashed: latexdiff-fast.exe needs Perl on PATH. Found `C:\Program Files\Git\usr\bin\perl.exe` (Git for Windows ships perl); set PATH. Second crash: Python's `re.subn` choked on `\R` in template; switched to lambda replacement. Third crash: latexdiff inserted stray ` %DIF > ` markers outside the preamble extension block; added strip logic for preamble-area markers. Fourth crash: listings package v1.11b parser error inside `\lstdefinelanguage{json}{...}` block ("Paragraph ended before `\lst@DefDriver@@` was complete"). **Root cause**: Python's `Path.write_text()` wrote CRLF on Windows; v1's `\lstdefinelanguage{json}` is sensitive to CRLF inside its braces under listings v1.11b. **Fix**: passed `newline="\n"` to all `write_text()` calls + simplified OVERRIDE to drop the listings dependency entirely (DIFverbatim unused in this paper's body). Recompile: DIFF PDF **16p / 467,281 B**. ✓
7. **Path B locked** for next half-session (Group C polish, 5 items).
8. **3 Group C decision points locked**:
   - **M-1a** (bertscore2020 used uncited at §5.2/Table 2 footnote) → add `~\cite{bertscore2020}` at first BERTScore mention
   - **M-1b** (karpukhin2020dense orphan since v1) → drop from bib
   - **Plan** → all 5 items + MANIFEST refresh as one cohesive Gate 6 batch
9. **Group C applied** (6 edits): M-1a cite added at sandbox `.tex:455`; M-1b karpukhin block removed (bib `-1` entry); bib header "36 entries (31 cited; 5 retained-orphan)" → "35 entries (32 cited; 3 retained-orphan)"; M-6 SUMMARY.md:21 rich-eval RCA 92.5%→91.1%, Overall 87.5%→86.4% (post-D-1 denominator 180/398); M-7 rename `phase45_graph/exp_4_5c_summary.json` → `exp_4_5c_summary_STALE_session17.json`; auditor-4 I2 + M4 via `benchmark/scripts/_dev/group_c_relabel_d1_rich_and_header.py` (264 task_type flips across 8 ablation rich-eval files + dataset header `rca_cases: 213→180, qa_mcq_cases: 33`).
10. **Recompile both** — main PDF **16p / 466,286 B**; DIFF PDF **16p / 467,840 B**. ✓
11. **MANIFEST.md SHA refresh** — only 1 Group-C-changed entry tracked (`benchmark_431_seed42.json`): size 351,400 → 388,351 B, SHA `d1a8f79f…` → `8202330996…`. Header timestamp bumped session 23 → session 24. New Group-C provenance bullet added. (Rich-eval `ablation_*/results.json` are NOT in the Post-D-1 SHA section — that section tracks only matched-eval `results_sota_eval_431.json`; no refresh needed for them.)
12. **Gate 6 — 4 themed commits applied** in order, each with HEREDOC body, NO Claude trailer, NO `--no-verify`:
    - `dfcc471` data(audit-Group-C): D-1 rich-eval re-label (8 files) + dataset header + archive stale 4.5c summary (10 files, +9571 −265)
    - `881ad20` docs(audit-Group-C): SUMMARY.md M-6 rich-eval RCA 92.5→91.1, Overall 87.5→86.4 (1 file, +1 −1)
    - `c533765` tools(_dev): DIFF regen wrapper + Group-C relabel helper (2 files, +205, new)
    - `dd51724` docs(MANIFEST): refresh SHA for benchmark_431_seed42.json (auditor-4 M4) (1 file, +3 −2)
13. **Gate 7 — pushed to origin/main**: `affad56..dd51724 main -> main`. Local = origin = `dd51724` synced.

---

## §2. What changed on disk in session 24

### Committed + pushed (`affad56..dd51724`, 4 commits)

| Commit | Files |
|---|---|
| `dfcc471` | 8 `ablation_v4/ablation_*/results.json` + 1 dataset header + rename (delete + add) |
| `881ad20` | `benchmark/final/SUMMARY.md` |
| `c533765` | 2 new dev scripts in `benchmark/scripts/_dev/` |
| `dd51724` | `benchmark/final/MANIFEST.md` |

### Sandbox paper (OUTSIDE git repo — `PAPER AND FORMAL DOCUMENTATION/...`)

- `sandbox-session16/main/sn-article.tex`: 55,987 B (was 54,591) / 793 lines (was 786) — Group B + Group C `.tex` edits
- `sandbox-session16/main/sn-article.pdf`: **16 pages / 466,286 B** (was 463,353)
- `sandbox-session16/main/sn-bibliography.bib`: 10,439 B (was 10,634) — karpukhin removed, header refreshed, alibaba title/year updated
- `sandbox-session16/diff/sn-article.tex`: refreshed copy of main
- `sandbox-session16/diff/sn-bibliography.bib`: refreshed copy of main bib
- `sandbox-session16/diff/sn-article-DIFF.tex`: 68,267 B (regenerated; simpler red-text override, no listings dep)
- `sandbox-session16/diff/sn-article-DIFF.pdf`: **16 pages / 467,840 B**

### NEW dev scripts (committed)

- `benchmark/scripts/_dev/regen_diff_pdf.py` (DIFF regen wrapper; idempotent; encodes the CRLF-vs-listings-v1.11b lesson)
- `benchmark/scripts/_dev/group_c_relabel_d1_rich_and_header.py` (auditor-4 I2 + M4 in one pass)

### Git state at close

- Local HEAD: `dd51724` = origin `dd51724` (synced)
- Branch: `main`
- Working tree: **clean** (apart from SESSION_24_HANDOFF.md untracked once this file lands; will be committed as session-24 close marker if user GO)
- 4 commits added in session 24
- NO Claude trailer in any commit (verified via grep)

### AWS state at close (UNCHANGED from session 22-23)

- Instance `i-091c4de0e95d63154`: **stopped** ✅
- CloudWatch alarm `aiops-idle-stop`: **ActionsEnabled=True** ✅
- EIP `44.195.172.165`, EBS root + data, snapshot `snap-01b191aedbf46b598`: preserved
- Spend ~$55 / $120 ceiling (NO AWS work in session 24)

---

## §3. Group B + C audit-fix outcomes

### Group B (12 audit IDs, 8 cohesive tasks)

| # | Audit ID | Where | Fix applied |
|---|---|---|---|
| 1 | I-6 (Table 5) | sandbox `.tex:563` | `−2.1pp` → `−2.2pp` (with-orchestrator RCA delta) |
| 2 | I-6 (Table 6) | sandbox `.tex:588` | `−2.1pp` → `−2.2pp` (with-graph RCA delta) |
| 3 | I-9 (§5.1 prose) | sandbox `.tex:451` | "5 cases" → "6 cases overall (1 ann + 5 RCA)" |
| 4 | I-9 (Table 2 fn) | sandbox `.tex:474` | "5-case difference" → "6-case overall difference (1 ann + 5 RCA)" |
| 5 | I-9 (Table 6 fn) | sandbox `.tex:597` | "5 cases" → "5 RCA cases (overall delta 6 incl. 1 ann)" |
| 6 | I-3 (RTT) | sandbox `.tex:447` | "calibration RTT 1.95\,ms" → "1.10\,ms" (matches summary.json + Table 4 footnote) |
| 7 | I-D (bib header) | bib line 2 | "26 references…" → "36 entries (31 cited; 5 retained-orphan)" *(later refined to 35/32/3 in Group C)* |
| 8 | I-4 (Qwen bib) | bib `alibaba2024qwen` | title → "Qwen Technical Report (Qwen3 Series)"; year 2024 → 2025 |
| 9 | I-5 (§6.2) | sandbox `.tex:738` | "planned" → "ran to completion and saturated… (aggregate preserved, per-case logs lost to post-run serialization bug)" |
| 10 | I-7 (Table 1) | sandbox `.tex:427` | NEW footnote: 213 = 180 rca + 33 qa_mcq; 74 excluded; 139 evaluable |
| 11 | I-2 (percentile) | sandbox `.tex:534` (Table 4 fn) | Append: "Percentiles use index-floor; linear-interp differs by <0.3s" |
| — | **I-8** | Tables 5/6/7 | **Deliberate skip** (locked Option C) — BERT-F1 already in Table 2 + §5.2 prose covers Table 7 |
| — | **I-A/B/C** | bib peng/zhang/nvidia | **Deliberate defer** — needs external lookup; revisit at camera-ready |

### Group C (5 polish items)

| # | Audit ID | Where | Fix applied |
|---|---|---|---|
| 1 | M-1a | sandbox `.tex:455` | Add `~\cite{bertscore2020}` after first BERTScore mention |
| 2 | M-1b | bib `karpukhin2020dense` | Entry removed (orphan since v1, never cited in v2) |
| — | (derived) | bib line 2 header | "36 entries (31 cited; 5 retained-orphan)" → "35 entries (32 cited; 3 retained-orphan)" (post-M-1) |
| 3 | M-6 | `SUMMARY.md:21` | rich-eval RCA 92.5% → 91.1%, Overall 87.5% → 86.4% (post-D-1; Ann unchanged at 82.6%) |
| 4 | M-7 | `phase45_graph/` | `exp_4_5c_summary.json` → `exp_4_5c_summary_STALE_session17.json` (session-17 leftover, D-17 crash never produced data) |
| 5 | auditor-4 I2 | 8 `ablation_v4/ablation_*/results.json` | 264 task_type flips (33 OpsEval-remined IDs × 8 files): `rca` → `qa_mcq` (matched-eval canonical-D-1 propagated to rich-eval) |
| 6 | auditor-4 M4 | `benchmark_431_seed42.json` | header: `rca_cases: 213` → `180`, added `qa_mcq_cases: 33` |
| — | (derived) | `MANIFEST.md` | benchmark_431 SHA refresh: `d1a8f79f…` → `8202330996…`, size 351,400 → 388,351; new Group-C provenance bullet |

---

## §4. Authoritative state for session 25

### Paths (UNCHANGED from session 23)

| Item | Path |
|---|---|
| Active paper `.tex` | `…sandbox-session16\main\sn-article.tex` (55,987 B / 793 lines) |
| Active paper `.pdf` | `…sandbox-session16\main\sn-article.pdf` (**16 pages / 466,286 B**) |
| DIFF `.tex` | `…sandbox-session16\diff\sn-article-DIFF.tex` (68,267 B) |
| DIFF `.pdf` | `…sandbox-session16\diff\sn-article-DIFF.pdf` (**16 pages / 467,840 B**) |
| v1 paper (READ-ONLY) | `…Final Submission Paper (Accepted v.1)\…\sn-article.tex` |
| OLD `sn-article-template.v2/` | **MOVED to `z.Dump Paper Archive/`** — do NOT touch |
| Project handoff | `constitutional-aiops/benchmark/HANDOFF.md` |
| Audit dir | `constitutional-aiops/benchmark/final/audit/` |

### Numbers (UNCHANGED — Group B + C are reviewer-surface and bookkeeping only, no headline movement)

All headline values from session-23 close remain. Key reminders:

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
| Rich-eval Overall (post-D-1) | **86.4% (344/398)** | `main_benchmark/results.json`, M-6 corrected this session |
| Rich-eval RCA (post-D-1) | **91.1% (164/180)** | same |

### Git

- Local HEAD `dd51724` = origin `dd51724` synced
- 4 commits added in session 24

### AWS

Stopped, CW alarm enabled, EIP retained, EBS preserved, snapshot held, ~$55/$120 spend.

---

## §5. Hard rules carried forward (UNCHANGED from session 23 §5; bumped #18 for session-24 lesson)

1. **NO Claude co-author trailer** on any commit
2. **NO push without explicit USER GO** (Gate push requires separate confirm)
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
15. **Sealed forensic docs untouchable**: CV_PASS1/2, FULL_TRANSCRIPT_AUDIT, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, all SESSION_12-24_HANDOFF.md
16. **Instance has NO git** — always scp
17. **Instance `src/` is OUTDATED** — `find_similar_episodes_by_embedding` missing on instance
18. **NEW session 24**: DIFF regen requires (a) Git for Windows perl.exe on PATH (set `$env:PATH = 'C:\Program Files\Git\usr\bin;' + $env:PATH`); (b) LF line endings (CRLF trips listings v1.11b on `\lstdefinelanguage{json}`); (c) listings package dropped from OVERRIDE (DIFverbatim unused in body). All three encoded in `regen_diff_pdf.py`.

**Reading non-ASCII result files from Windows shell**: always pass `encoding='utf-8'` to `open()` — cp1252 default crashes on bytes ≥ 0x80 (LEMMA-RCA + OpsEval contain non-ASCII chars).

---

## §6. Mandatory reads for session 25

1. **`MEMORY.md`** (auto-loaded — read SESSION 25 STARTUP block in full)
2. **`benchmark/final/audit/SESSION_24_HANDOFF.md`** ⭐⭐⭐ (THIS FILE — primary entry)
3. **`benchmark/final/audit/SESSION_23_HANDOFF.md`** (Group A context; Group B was its pending list)
4. **`benchmark/final/audit/SESSION_22_HANDOFF.md`** (5-agent audit findings; do NOT skip — the IMPORTANT/MINOR lists are the source for any remaining work)
5. **`benchmark/final/audit/paper_audit_session22_2026-05-26/00_SUMMARY.md`** (master synthesis — Group A complete in session 23, Group B + C complete in session 24)
6. **Individual auditor reports as needed** (only when working a specific deferred item)
7. **`benchmark/HANDOFF.md`** (project handoff)
8. **`benchmark/final/SUMMARY.md`** (canonical results landscape)
9. **All non-MEMORY auto-memory files** (auto-loaded)
10. **Sandbox `.tex` only when about to edit** — do NOT bulk-read

---

## §7. Items pending for session 25

### Path C — Camera-ready prep (no audit IDs; visual + scope work)

| Item | Description |
|---|---|
| Visual QC | Page-by-page check of `sn-article.pdf` (Fig 3 callout, 84% baseline label, Table 1 new footnote, Table 4 RTT/percentile footnote, Table 6 −2.2pp, §6.2 reframe, §5.2 cite render) |
| Bib auto-validation | Run `bibtex sn-article` clean (verify no warnings about missing fields after Group B edits) |
| Abstract / §1 tone pass | Light Grammarly-style edit if camera-ready feedback wants it |
| Journal-extension scope | Decide which Group B-deferred items (I-A/B/C bib fields) to fix vs leave for journal version |

### Path D — AWS work (NOT blocking for camera-ready)

| Item | Cost | Time | Pre-req |
|---|---|---|---|
| Stack B full 431-case latency re-run | ~$5 | ~3h | start instance; sequential GPU (stop Ollama first) |
| Phase 4.5c cold-start curve (N=0/20/40/60 on 20 LEMMA cases) | ~$5 | ~5h | scp updated `src/memory/neo4j_client.py` to instance first (missing `find_similar_episodes_by_embedding`) + D-16/D-17 patches already on laptop |

### Deliberate defers from Group B (Path C scope)

| Audit ID | Item | Why deferred |
|---|---|---|
| I-A | `peng2025graphragsurvey` missing volume/issue/pages/DOI | Needs external CrossRef/dblp lookup at camera-ready |
| I-B | `zhang2024aiopssurvey` year 2024 vs likely 2025 | Needs ACM CS publication date verification |
| I-C | `nvidia2024specdec` lacks URL | Needs verified blog post URL |

---

## §8. Session 25 first actions (in order)

1. **Read MEMORY.md** (auto-loaded — verify SESSION 25 STARTUP block)
2. **Read THIS file IN FULL** (`SESSION_24_HANDOFF.md`)
3. **Reference SESSION_23_HANDOFF.md + SESSION_22_HANDOFF.md + 00_SUMMARY.md** as needed for context on remaining items
4. **State-verify** (single PowerShell call, expected values):
   - `git status --short | wc -l` → 1 (just `SESSION_24_HANDOFF.md` if not yet committed)
   - `git log -1 --format='%h %s'` → `dd51724 docs(MANIFEST): refresh SHA for benchmark_431_seed42.json (auditor-4 M4)`
   - `git log origin/main -1 --format='%h'` → `dd51724` (synced)
   - Sandbox `main/sn-article.pdf` → **16p / 466,286 B**
   - Sandbox `diff/sn-article-DIFF.pdf` → **16p / 467,840 B**
   - AWS `i-091c4de0e95d63154` → `stopped`
   - CW alarm → `ActionsEnabled=True`
5. **ASK USER**: pick a path —
   - **Path C — Camera-ready prep** (visual QC, bib validation, scope decisions, tone pass)
   - **Path D — AWS work** (Stack B full 431 or 4.5c cold-start; not blocking)
   - **Path B' — Deliberate-defer bib items** (I-A/B/C with external verification)
   - **Path E — Other** (user specifies)
6. **Halt for USER GO** before any sandbox `.tex` edit, any repo commit, any AWS work
7. **Hard rules carried**: NO Claude trailer, NO push without GO, sandbox `main/` only, NEVER touch real `sn-article-template.v2/`, AWS stays stopped, do NOT remove 3-point rubric disclosures, DIFF regen uses the encoded script with Perl on PATH + LF write.

---

## §9. Useful commands for session 25

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

# Verify post-D-1 invariants
python -c "import json; recs=json.load(open('benchmark/final/main_benchmark/results_sota_eval_431.json', encoding='utf-8')); print('null_count:', sum(1 for r in recs if r.get('correct') is None))"  # expect 74
```

---

## §10. Open follow-ups for sessions 26+ (low priority)

- If reviewer demands 4.5c cold-start curve: re-launch on instance (~$5, ~5h) — patches on laptop, instance needs scp `src/memory/` first
- If reviewer demands full 431-case latency for Stack B: ~$5, ~3h
- Deliberate-defer bib items (I-A/B/C) — needs external lookup
- Optional: Brittlebench/PromptRobust + C3AI bib additions (audit M-2; likely intentional drops per page budget)

---

*End of handoff. Session 24 close 2026-05-26. Next session = 25.*
