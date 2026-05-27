# Session 22 → Session 23 Handoff (2026-05-26)

> **PRIMARY ENTRY POINT for session 23**. Session 22 (2026-05-26, ~5h elapsed) completed DIFF PDF, reorganized sandbox folder, sorted loose root files, moved + rewrote HANDOFF.md, applied 6 themed Gate 1 commits + Gate 3 push, and ran a 5-agent parallel paper audit producing 10 CRITICAL + 14 IMPORTANT + 7 MINOR findings. Session ends with audit synthesis ready for action.

---

## §0. One-line state

DIFF PDF complete (16p, red text override). Sandbox reorganized into `main/` + `diff/` subfolders. 9 loose root files sorted under `benchmark/final/audit/_session11_phase4_orphans/`, `_session12_reorg_intermediates/`, and `benchmark/scripts/_dev/`. HANDOFF.md relocated to `benchmark/HANDOFF.md` and rewritten. 6 Gate 1 commits (#6 skipped) landed and pushed to origin/main (`a5e9005..77f49f9`). 5-agent paper audit complete with master summary identifying **10 CRITICAL paper-defining fixes** for session 23.

---

## §1. What happened this session (chronological)

1. **State re-gather** — read MEMORY.md, SESSION_21_HANDOFF.md, 3 memory files. State-verify: sandbox PDF 16p, DIFF artifacts present but unfinished, git HEAD `57035cf` w/ 45 modified files, AWS stopped, CW alarm armed.
2. **Path A chosen** (Finish DIFF PDF) over Path B (Skip to Gate 1).
3. **DIFF PDF resume** — yellow `\hl{}` override already in `.tex` from session 21; first pdflatex FAILED at line 449 (`! Argument of \@citex has an extra }`) because soul's `\hl{}` breaks on `\cite{}` inside additions. Switched to fallback `\providecommand{\DIFadd}[1]{{\protect\color{yellow!50!orange}\textbf{#1}}}`. Pass 1 clean. Bibtex pass clean (0 undefined refs). 3 passes total → PDF 16 pages (was 17 with bold).
4. **User flagged 17p regression** — bold widened text. Re-edited override to plain `\textcolor{red!75!black}{#1}` (no bold). Recompile + bibtex + 2 more passes → final PDF **16 pages, 461,798 bytes, 0 undefined refs**.
5. **Visual verify** — exported pages 2, 10, 11, 13, 16 via pdftoppm. Red highlights visible on all v1→sandbox additions including Table 4 rewrite, Table 5+6 contents, §5.7 SOTA, §6.1 Research Gap Validation, bibliography refs.
6. **User asked for sandbox housekeeping** — clean folder like v1 reference structure.
7. **Question asked** (3 options, user chose Option 2): two subfolders `main/` + `diff/` each mirroring v1's flat layout.
8. **Sandbox reorganization**:
   - Created `main/` and `diff/` subfolders
   - Copied shared support files (bst/, .cls, .bst, .bib, .eps figures) to both
   - Moved `sn-article.tex` + `sn-article.pdf` to `main/`
   - Copied `sn-article.tex` to `diff/` as read-only diff target ref
   - Moved `sn-article-DIFF.tex` + `sn-article-DIFF.pdf` to `diff/`
   - Deleted all transient junk: 2 PNG export dirs, 6 .log files, 2 stray PNGs, 13 .aux/.bbl/.blg/.out files
   - Result: sandbox root contains ONLY `main/` + `diff/`
9. **Memory updated**: `project_paper_sandbox_active.md` + MEMORY.md SESSION 22 STARTUP block reflect new path `...sandbox-session16\main\sn-article.tex`.
10. **User asked**: sort 9 loose .txt/.py at AIOPS root + move HANDOFF.md.
11. **Loose-file investigation** — peeked at each file to determine origin:
    - 2 mangled-name `C:Users...phase4_*.txt` = session 11 transcript audit Phase 4 temp-redirect failures (Windows backslash stripped, content duplicated in `FULL_TRANSCRIPT_AUDIT.md`)
    - 5 `_index_*.txt` = session 12 directory walks + change lists (work captured in `MASTER_BACKUP_MANIFEST_2026-05-20.json`)
    - 2 `_session21_latency_*.py` = session 21 Table 4 P50/P95/P99 computation helpers (numbers landed in paper)
12. **File sort executed** — bash `mv` for the colon-named files (PowerShell `:` parser issue forced bash). Final: root has only `ssh.txt` + 3 dirs.
13. **HANDOFF.md moved** → `constitutional-aiops/benchmark/HANDOFF.md`.
14. **HANDOFF.md fully rewritten** — was dated 2026-05-13 (session-4 era). New version: 470 lines, current paper path, AWS budget ~$55/$120, HEAD `57035cf` + 7 pending commits noted, Phase 4.5 PATH 4 outcome, Phase 6 sandbox `main/` + DIFF, all hard rules, 16-row session history, recompile recipes for both subfolders, 10 known gotchas including session-22 finds (`\hl{}` breaks on `\cite{}`, PowerShell `:` parsing, UTF-16 BOM redirect).
15. **User said "GO Gate" — safe commit**. Status survey: 50 files in working tree (45 modified + housekeeping).
16. **Gate 1 — 6 themed commits applied** (commit #6 paper-sandbox SKIPPED because paper tree is at `PAPER AND FORMAL DOCUMENTATION/` which is OUTSIDE the constitutional-aiops/ git repo):
    - `9bc5107` data(D-1): re-label 33 OpsEval-remined + sync 16 result files + Phase 5 recompute (20 files)
    - `3e29c14` docs: refresh SUMMARY/METHODOLOGY/MANIFEST/BUG_HISTORY/AUDIT_REPORT + session-16 checklist (6 files)
    - `916220b` fix(scripts): D-7 + D-14 + D-16 + D-17 + 6 D-1 helper scripts (8 files)
    - `5843f99` eval(D-6): BERT-F1 recompute via roberta-large + summary artifact (2 files)
    - `a9dcb53` data(4.5): Phase 4.5 LEMMA-CV PATH 4 + D-17 forensic log (5 files)
    - `77f49f9` docs(audit): SESSION_17/18/19/20/21 handoffs + HANDOFF.md relocation + root housekeeping (18 files)
    - All used HEREDOC for multi-line bodies, NO `Co-Authored-By: Claude` trailer, no emoji, no `--no-verify`, no force push
17. **User said "GO Gate 3 safely"**. Pre-push verify (branch main, HEAD 77f49f9, clean tree, no Claude trailer) → `git push origin main` → `a5e9005..77f49f9  main -> main` clean. Post-push verify: local = origin synced.
18. **User asked for multi-agent paper audit**. Launched 5 parallel general-purpose subagents in single message:
    - **Auditor #1 — Numbers**: Tables 1-7 + Fig 3 + statistical claims vs source-of-truth result files
    - **Auditor #2 — v1↔v2 structural diff**: section-by-section preservation/dropping/reframing
    - **Auditor #3 — Citations + bib**: `\cite{}` coverage + bib integrity + v1↔v2 bib diff
    - **Auditor #4 — Benchmark integrity**: result file self-consistency + MANIFEST SHA + dataset
    - **Auditor #5 — Cross-doc consistency**: paper vs SUMMARY/METHODOLOGY/BUG_HISTORY/AUDIT_REPORT/MANIFEST/HANDOFF
19. **5 agents completed in ~7-14 min each** (parallel). All 5 reports written to `benchmark/final/audit/paper_audit_session22_2026-05-26/`.
20. **Master synthesis written** to `00_SUMMARY.md` (same dir) — 10 CRITICAL + 14 IMPORTANT + 7 MINOR findings with file:line citations and Group A/B/C fix order.

---

## §2. What changed on disk in session 22

### Committed and pushed to origin/main (50 files across 6 commits)
See `git log a5e9005..77f49f9` for full diff. Key:
- `benchmark/HANDOFF.md` NEW (relocated + rewritten)
- `HANDOFF.md` DELETED at repo root
- 6 SESSION_*.md audit handoffs NEW (sessions 17-21)
- 2 new sub-dirs at `benchmark/final/audit/_session11_phase4_orphans/` + `_session12_reorg_intermediates/`
- 8 D-1 + D-bugfix script changes
- 2 _dev scripts NEW
- 14 D-6 BERT-F1 result files (bert_f1 field populated)
- 16 D-1 result files synced (task_type relabel)
- Phase 4.5 forensic dump (5 files)
- 5 SUMMARY/METHODOLOGY/MANIFEST/BUG_HISTORY/AUDIT_REPORT updates

### NEW files (untracked — session 22 audit, NOT committed)
- `benchmark/final/audit/paper_audit_session22_2026-05-26/00_SUMMARY.md` (master)
- `benchmark/final/audit/paper_audit_session22_2026-05-26/01_numbers_audit.md`
- `benchmark/final/audit/paper_audit_session22_2026-05-26/02_v1_v2_structural_diff.md`
- `benchmark/final/audit/paper_audit_session22_2026-05-26/03_citations_audit.md`
- `benchmark/final/audit/paper_audit_session22_2026-05-26/04_benchmark_integrity.md`
- `benchmark/final/audit/paper_audit_session22_2026-05-26/05_cross_doc_consistency.md`
- `benchmark/final/audit/SESSION_22_HANDOFF.md` (THIS FILE)

### Modified sandbox paper (OUTSIDE git repo — `PAPER AND FORMAL DOCUMENTATION/`)
- `...sandbox-session16/main/sn-article.tex` + `.pdf` (16p)
- `...sandbox-session16/diff/sn-article-DIFF.tex` + `.pdf` (16p, red-text highlights)
- Old folder structure dissolved (was sandbox-session16/ flat); now sandbox-session16/main/ + sandbox-session16/diff/
- Old `sn-article-template.v2/` moved by user to `z.Dump Paper Archive/` (do NOT touch)

### Git state at close
- Local HEAD: `77f49f9` (synced with origin/main)
- Origin HEAD: `77f49f9`
- Branch: `main`
- Working tree: clean (no uncommitted changes to constitutional-aiops/ repo)
- Untracked: only `benchmark/final/audit/paper_audit_session22_2026-05-26/` + `SESSION_22_HANDOFF.md` (this file)

### AWS state at close (UNCHANGED from session 20-21)
- Instance `i-091c4de0e95d63154`: **stopped** ✅
- CloudWatch alarm `aiops-idle-stop`: **ActionsEnabled=True** ✅
- EIP `44.195.172.165`, EBS root + data, snapshot `snap-01b191aedbf46b598`: preserved
- Spend ~$55 / $120 ceiling
- NO AWS work in session 22

---

## §3. Audit findings (full summary)

**Verdict**: paper body (Tables 2-7, Fig 3, §5.1-§5.7) is internally consistent and well-corroborated. Front matter (abstract + §1 + §2 + RG1-2) is STALE v1 text. Top reviewer risk.

### CRITICAL — must fix pre-camera-ready (10 items)

| # | Where | What's wrong |
|---|---|---|
| C-A1 | Abstract `sn-article.tex:123` | Verbatim v1: "150-test / 90.7% / four datasets". Reality: 431 / 6 datasets / 82.4%. |
| C-A2 | §1 Intro `:137` | Verbatim v1: "150-test / 90.7% / 7-config / 31.3pp / 1,050 inferences". Reality: 431 / 82.4% / 8-config / 22.7pp / 3,448 inferences. |
| C-A3 | §2/RG1/RG2 `:141,143,160` | Unsupported: "3.3pp dual-agent improvement" (max +2.9pp RCA); "0.7% constitutional overhead" (current −1.1pp NS asymmetric). |
| C-B1 | Table 4 14B row | Shows n=180 RCA-only percentiles; footnote claims n=431. Refit to n=213 or fix footnote. |
| C-B2 | Table 7 Drain row | Caption says "same 431-case"; Drain ran on `benchmark_400_seed42.json` (V1, 202 cases only). |
| C-B3 | §5.5 Stack B claim | "~1.5× vLLM speedup" measured on 30-case smoke (`gate15_comparison.md`), NOT 431. |
| C-C1 | `MANIFEST.md` | SHA table stale for all 14 D-6 BERT-F1 recompute files. Regenerate. |
| C-C2 | `ablation_v4/*/results_sota_eval_431.json` | 3 qa_mcq cases (`RCA_OPSEVAL_RM_016/022/032`) carry `correct=True/False` instead of null. Paper claims 74 excluded; actual 71. Math OK; story off-by-3. |
| C-D1 | `HANDOFF.md:215-223` (just-rewritten) | §7 ablation cells drift from paper on 5 rows: Single-4B, Single-14B, No-constitutional, No-system-prompt, with-graph. |
| C-D2 | `HANDOFF.md:232-233` | SOTA Overall cells drift: HANDOFF Llama 83.3 / DeepSeek 81.1; paper + SUMMARY 83.5 / 81.2. |

### IMPORTANT — should fix (14 items)
- I-1: Stack B "vLLM+FP8" should be "vLLM AWQ (awq_marlin)" everywhere
- I-2: P95/P99 percentile method (index-floor in paper vs linear-interp in summary.json, 0.2s gap)
- I-3: §5.1 "1.95 ms RTT" vs Table 4 footnote "1.10 ms"
- I-4: `alibaba2024qwen` bib says Qwen2.5 but paper says Qwen3 family
- I-5: §6.2 calls Phase 4.5 "planned" but it ran (per-case JSONL lost to D-17)
- I-6: with-graph / with-orchestrator RCA delta rounds to −2.2pp (paper says −2.1pp)
- I-7: Table 1 splits 431 as "218 Ann + 213 RCA"; Table 4 footnote as "218 + 180 + 33 qa_mcq"
- I-8: BERT-F1 only in Table 2, missing from Tables 5/6/7
- I-9: Run-to-run footnote says "5 cases" (actual 6 = 1 ann + 5 rca)
- I-A: `peng2025graphragsurvey` bib missing volume/issue/pages/DOI
- I-B: `zhang2024aiopssurvey` year=2024 (likely 2025)
- I-C: `nvidia2024specdec` lacks URL
- I-D: Bib comment "26 references" (actual 36)
- I-E (= 5.5 of orig): per-source numerical breakdowns at `:481` say "deferred to supplementary" but next table contains them

### MINOR — polish (7 items)
- M-1: 5 orphan bib entries (3 intentional drops + `bertscore2020` + `karpukhin2020dense`)
- M-2: 2 of 12 expected new bib entries missing (Brittlebench, C3AI)
- M-3: pre-D-1 `excluded_rca_cases.json` still on disk
- M-4: stale `main_benchmark/summary.json` byte-identical to `benchmark_result.json` w/ rich-eval pre-D-1 numbers
- M-5: D-1 rich-eval files in 8 ablation_* not relabeled (matched-eval is canonical so OK)
- M-6: SUMMARY.md:21 rich-eval RCA 92.5% → actual 91.1% post-D-1
- M-7: stale `phase45_graph/exp_4_5c_summary.json` (session-17 leftover, documented stale)

### OK — verified clean (the strong base)
All Table 5+6 cells match `phase5_stats.json` exactly • all Fig 3 bars match Tables 5+6 • Table 7 SOTA recompute from raw `.jsonl` matches • Table 2 main re-run all 8 cells match • Table 3 per-source verified per-cell • statistical methodology (n_resamples=10000, seed=42, BCa, McNemar, 357 paired) matches • 74-case exclusion methodology consistent • §5.8 cleanly removed (Decision 4) • Table 4 v1 component×metrics layout (Decision 1) • Fig 3 v1 dims (Decision 3) • prompt-fragility reframe honest (4B −34.4pp vs 14B −4.3pp) • graph reframe honest (p=0.289 NS) • architectural-contrast paragraph cites Flow-of-Action + AIOpsLab + OpenRCA • intentional 3-point rubric disclosures at lines 447 + 597 present • all 31 cited keys resolve (no `[?]`) • citation style uniform • 13-cite contextual sample all topically correct • dataset SHA matches MANIFEST • 431 records valid (218+180+33) • 0 NaN • 0 duplicate IDs • all 33 qa_mcq have `excluded_reason` • all 9 matched-eval headline percentages match SUMMARY §3.1 exactly • Phase 5 stats files match counted-correct • all 14 D-6 BERT-F1 files populated 431/431 • D-1 spot-check 5 sample IDs consistent • 4.5b summary schema valid • SOTA + no-prompt baselines match SUMMARY • AUDIT_REPORT shows 23 OK / 0 WARN / 0 FAIL with post-D-1 header note • BUG_HISTORY shows D-1/D-6/D-17 RESOLVED

### Recommended fix order
- **Group A — 9 items, must fix pre-submit**: rewrite abstract + §1 + §2 with v3.0 numbers, fix Table 4 14B row, decide Drain row, mechanical "vLLM+FP8" → "vLLM AWQ", regenerate MANIFEST SHA, fix HANDOFF §7, reconcile 71-vs-74 exclusion
- **Group B — 8 items, should fix**: RTT reconciliation, Qwen bib fix, §6.2 reframe "planned" → "ran with per-case loss", §5.5 disclose 30-case smoke, Table 4 rounding, Table 1↔4 footnote, BERT-F1 in Tables 5/6/7 decision, 4 bib fixes
- **Group C — 5 items, polish**: orphan bib decisions, SUMMARY.md 91.1% correction, archive stale 4.5c file, D-1 rich-eval sync

See `paper_audit_session22_2026-05-26/00_SUMMARY.md` §Recommended-fix-order for full detail with file:line citations.

---

## §4. Authoritative state for session 23

### Paths (UPDATED session 22, do NOT use old paths)
| Item | Path |
|---|---|
| Active paper `.tex` | `c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\main\sn-article.tex` |
| Active paper `.pdf` | `...sandbox-session16\main\sn-article.pdf` (460,355 B, 16 pages) |
| DIFF `.tex` | `...sandbox-session16\diff\sn-article-DIFF.tex` (68,844 B) |
| DIFF `.pdf` | `...sandbox-session16\diff\sn-article-DIFF.pdf` (461,798 B, 16 pages) |
| v1 paper (READ-ONLY ref) | `...Final Submission Paper (Accepted v.1)\1ST SUBMISSION\sn-article-template\sn-article.tex` |
| OLD `sn-article-template.v2/` | **MOVED to `z.Dump Paper Archive/` by user — do NOT touch** |
| Project handoff | `c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\benchmark\HANDOFF.md` (was at repo root pre-session-22) |
| Audit dir | `c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\benchmark\final\audit\` |
| Session 22 audit reports | `...\benchmark\final\audit\paper_audit_session22_2026-05-26\` (6 files: 00_SUMMARY + 5 auditor reports) |

### Numbers (post-D-1, authoritative)
| Metric | Value | Source |
|---|---|---|
| Total cases | 431 | `benchmark_431_seed42.json` |
| Composition | 218 ann + 180 rca + 33 qa_mcq | D-1 re-label (session 17) |
| Excluded RCA | 74 (41 Chinese + 33 OpsEval-MCQ) | METHODOLOGY.md §2 |
| Evaluable | 357 (218 ann + 139 rca) | phase5_stats.json |
| Main re-run Overall | 82.4% (294/357) | `main_benchmark/phase5_stats.json` |
| Main re-run Annotation | 82.6% (180/218) | same |
| Main re-run RCA | 82.0% (114/139) | same |
| BERT-F1 mean | 0.8124 (Ann 0.822, RCA 0.795) | `_bert_f1_recompute_summary.json` |
| Ablation Full RCA | 85.6% (119/139) | `ablation_v4/phase5_stats.json` |
| Ablation Full Overall | 84.0% (300/357) | same |
| Llama 3.3-70B RCA | 71.2% (99/139) | `sota_baselines/llama_3_3_70b.jsonl` |
| DeepSeek V3.2 RCA | 66.9% (93/139) | `sota_baselines/deepseek_v3.jsonl` |
| ΔRCA Ours − Llama | +10.8pp | derived |
| ΔRCA Ours − DeepSeek | +15.1pp | derived |
| Stack A latency P95 | 65.96s | Gate §15 smoke (30 cases) |
| Stack B latency P95 | 43.71s | Gate §15 smoke (30 cases) |
| Stack B speedup | 1.51× | Gate §15 smoke |
| Phase 4.5a heterogeneous | Δ=−1.1pp, p=0.289 NS | Within ablation `with_graph` |
| Phase 4.5b LEMMA-CV | 100% no-graph = 100% with-graph (CEILING) | `phase45_graph/exp_4_5b_summary.json` |
| Phase 4.5c cold-start | NEVER RAN (D-17 crash) | `phase45_graph/_failed_run_log.txt` |

**Stack B is `vLLM AWQ awq_marlin`, NOT `vLLM+FP8`** — paper currently mislabels this throughout (CRITICAL I-1 fix).

### Git
- Local HEAD `77f49f9` = origin `77f49f9` (synced)
- Branch `main`
- Working tree clean (only session 22 audit untracked)
- Recent commit run: 6 themed commits in session 22 (`9bc5107`, `3e29c14`, `916220b`, `5843f99`, `a9dcb53`, `77f49f9`)
- NO Claude trailer in any commit verified

### AWS (unchanged from session 20 close)
Instance stopped, CW alarm enabled, EIP retained, EBS preserved, snapshot held, ~$55/$120 spend.

---

## §5. Hard rules carried forward (DO NOT VIOLATE without explicit GO)

1. **NO Claude co-author trailer** on any commit (NEVER `Co-Authored-By: Claude ...`)
2. **NO push to origin without explicit USER GO** (Gate 3 requires separate confirmation)
3. **Paper edits target sandbox `sn-article-template.v2.sandbox-session16/main/sn-article.tex` only**
4. **NEVER touch real `sn-article-template.v2/`** — Gate 2 PERMANENTLY DROPPED; moved to `z.Dump Paper Archive/`
5. **v1 paper at `Final Submission Paper (Accepted v.1)/.../sn-article.tex` is READ-ONLY**
6. **AWS instance stays STOPPED** unless user GO; do NOT release EIP `44.195.172.165`; do NOT delete snapshot `snap-01b191aedbf46b598`
7. **3-point rubric mentions** at sandbox lines 447 (§5.1) + 597 (Table 6 footnote) are **INTENTIONAL DISCLOSURES** — do NOT remove without explicit ask (audit auditor #2 + #5 confirmed these are NOT bugs)
8. **DO NOT recompute D-1 dataset or BERT-F1** (done sessions 17-18)
9. **DIFF PDF override** uses `\textcolor{red!75!black}{#1}` (no bold) for `\DIFadd` — bold widens text +1 page; `\hl{}` from soul breaks on `\cite{}`. Override block at `diff/sn-article-DIFF.tex:102-108`.
10. **PowerShell `:` parsing** in filenames requires bash `mv` (not Move-Item) even when path is quoted
11. **PowerShell `>` redirect** produces UTF-16 LE BOM — use `[System.IO.File]::WriteAllText` with `New-Object System.Text.UTF8Encoding $false` when writing `.tex` files
12. **`enable_thinking=False` is ignored by Ollama 0.23.2** — thinking happens anyway; reasoning lands in `message.reasoning`. v1 paper produced this way. Do NOT try to disable thinking.
13. **Master backup zip** `Backups/benchmark_master_backup_2026-05-20.zip` is sacred — do NOT delete
14. **`annotation_test.json` + `rca_test.json`** dirty in local — do NOT commit content changes
15. **Sealed forensic docs untouchable**: `CV_PASS1/2`, `FULL_TRANSCRIPT_AUDIT.md`, `REORG_PROPOSAL_2026-05-20.md`, `MASTER_BACKUP_MANIFEST_2026-05-20.json`, all `SESSION_12-22_HANDOFF.md`
16. **Instance has NO git** — always `scp` files; NEVER `git pull` on instance
17. **Instance `src/` is OUTDATED** — `Neo4jClient.find_similar_episodes_by_embedding` is on laptop but NOT on instance. Any 4.5b/4.5c re-run requires scp `src/memory/` first.

---

## §6. Mandatory reads for session 23 (in order, no skipping)

The user emphasized: "FILES MUST NOT BE SKIPPED, MAKE SURE ALL MEMORY IS READ".

1. **`MEMORY.md`** (auto-loaded — read SESSION 23 STARTUP block in full)
2. **`benchmark/final/audit/SESSION_22_HANDOFF.md`** ⭐⭐⭐ (THIS FILE — primary entry doc)
3. **`benchmark/final/audit/paper_audit_session22_2026-05-26/00_SUMMARY.md`** ⭐⭐⭐ (master audit synthesis — the 10 CRITICAL + 14 IMPORTANT + 7 MINOR findings)
4. **`benchmark/final/audit/paper_audit_session22_2026-05-26/01_numbers_audit.md`** — for Group A fixes (Tables, statistical claims)
5. **`benchmark/final/audit/paper_audit_session22_2026-05-26/02_v1_v2_structural_diff.md`** — for abstract/§1/§2 rewrites (CRIT-A1, A2, A3)
6. **`benchmark/final/audit/paper_audit_session22_2026-05-26/03_citations_audit.md`** — for bib fixes (Group B I-4, I-A through I-D)
7. **`benchmark/final/audit/paper_audit_session22_2026-05-26/04_benchmark_integrity.md`** — for MANIFEST SHA + 71-vs-74 reconciliation (CRIT-C1, C2)
8. **`benchmark/final/audit/paper_audit_session22_2026-05-26/05_cross_doc_consistency.md`** — for HANDOFF.md drift fix (CRIT-D1, D2)
9. **`benchmark/HANDOFF.md`** — session-22-rewritten project handoff (note: §7 has known drift to be fixed per CRIT-D1, D2)
10. **`benchmark/final/SUMMARY.md`** — canonical results landscape (use as source of truth when fixing HANDOFF.md)
11. **All non-MEMORY auto-memory files** (auto-loaded from `C:\Users\partha\.claude\projects\c--Users-partha-Downloads-files-AIOPS-NEW\memory\`):
    - `project_paper_sandbox_active.md` ⭐ (path discipline)
    - `user_profile.md`
    - `feedback_no_shortcuts_read_sources.md` ⭐ (working principle)
    - `feedback_git_filter_repo_lessons.md`
    - `project_dualstack_decision.md`
    - `project_thinking_mode_audit_logging.md`
    - `project_vram_tuning_l4.md`
    - `project_aiops_next.md` (historical)
    - `project_aiops_state.md` (historical)
12. **Sandbox `.tex` only when about to edit** — do NOT bulk-read unless making fixes
13. **Sealed forensic docs**: do NOT modify (CV_PASS1/2, FULL_TRANSCRIPT_AUDIT, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, SESSION_12-22 handoffs)

---

## §7. Session 23 first actions (in order, no improvisation)

1. **Read MEMORY.md** (auto-loaded — verify SESSION 23 STARTUP block)
2. **Read THIS file IN FULL** (`SESSION_22_HANDOFF.md`)
3. **Read `paper_audit_session22_2026-05-26/00_SUMMARY.md` IN FULL** (master audit synthesis)
4. **State-verify** (single PowerShell call, report results in one paragraph):
   - `git status --short | wc -l` → expect 7 untracked (6 audit reports + this handoff)
   - `git log -1 --format='%h %s'` → expect `77f49f9 docs(audit): ...`
   - `git log origin/main -1 --format='%h'` → expect `77f49f9` (synced)
   - Sandbox `main/sn-article.pdf` → expect 16 pages, ~460,355 bytes
   - Sandbox `diff/sn-article-DIFF.pdf` → expect 16 pages, ~461,798 bytes
   - AWS `i-091c4de0e95d63154` → expect `stopped`
   - CloudWatch `aiops-idle-stop` → expect ActionsEnabled=True
5. **ASK USER**: 3 viable paths for session 23 — choose one:
   - **Path A — Group A fixes (must-fix-before-camera-ready)**: rewrite abstract + §1 + §2 with v3.0 numbers, fix Table 4 14B row, decide Drain row, "vLLM+FP8" → "vLLM AWQ", regenerate MANIFEST SHA, fix HANDOFF §7, reconcile 71-vs-74 exclusion (~9 items, mix of sandbox `.tex` edits + repo doc fixes)
   - **Path B — Audit triage only**: walk through 00_SUMMARY.md per-finding with user to lock decisions (like session-17 triage); produce a SESSION_23_TRIAGE.md with locked decisions before any edits
   - **Path C — Other**: user specifies (e.g., Stack B full 431 re-run on AWS, Phase 4.5c cold-start re-run, etc.)
6. **Halt for USER GO** before any sandbox `.tex` edit, any repo commit, any AWS work
7. **If Path A or after Path B triage**: apply fixes carefully:
   - Sandbox `.tex` edits → recompile + verify 16 pages + visual spot-check via pdftoppm
   - Repo doc fixes (MANIFEST, HANDOFF, result files) → commit per-theme, NO Claude trailer
8. **If Stack B re-run needed**: see SESSION_22_HANDOFF.md §4 AWS section for instance start procedure (laptop IP rotates, must re-add SG ingress)

---

## §8. Useful commands for session 23

```powershell
# Verify state at start
Set-Location 'c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops'
git log -1 --format='HEAD: %h %s'
git status --short

# Recompile sandbox main paper
$pdflatex = 'C:\Users\partha\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe'
$bibtex   = 'C:\Users\partha\AppData\Local\Programs\MiKTeX\miktex\bin\x64\bibtex.exe'
Set-Location "c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\main"
& $pdflatex sn-article.tex; & $bibtex sn-article; & $pdflatex sn-article.tex; & $pdflatex sn-article.tex

# Re-generate DIFF after sandbox .tex edits (uses red-text override at line 102-108)
Set-Location "c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\diff"
$latexdiff = 'C:\Users\partha\AppData\Local\Programs\MiKTeX\miktex\bin\x64\latexdiff-fast.exe'
$v1Tex = "c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\Final Submission Paper (Accepted v.1)\1ST SUBMISSION\sn-article-template\sn-article.tex"
# (To re-generate from scratch, latexdiff-fast → .tex, then manually patch \DIFadd override per session-22 §13 gotcha)
& $pdflatex sn-article-DIFF.tex; & $bibtex sn-article-DIFF; & $pdflatex sn-article-DIFF.tex; & $pdflatex sn-article-DIFF.tex

# Regenerate MANIFEST.md SHA table (for CRIT-C1 fix)
Set-Location 'c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops'
# Use Get-FileHash -Algorithm SHA256 per file listed in MANIFEST.md and replace the SHA column

# Check instance state (no AWS work expected — just verify still stopped)
aws ec2 describe-instances --profile aiops-operator --region us-east-1 `
  --instance-ids i-091c4de0e95d63154 `
  --query 'Reservations[0].Instances[0].State.Name' --output text
```

---

## §9. Open follow-ups for future sessions (low priority)

- If reviewer demands 4.5c cold-start curve: re-launch on instance (~$5, ~5h) — see `paper_audit_session22_2026-05-26/00_SUMMARY.md` for D-17 patch status
- If reviewer demands full 431-case latency: re-run Stack B (~$5, ~3h)
- Group C polish items if time permits before submission

---

*End of handoff. Session 22 close 2026-05-26. Next session = 23.*
