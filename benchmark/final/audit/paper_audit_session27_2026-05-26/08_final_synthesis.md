# Stage 6 — Final Synthesis
**Generated**: 2026-05-27 (session 29)
**Agent**: Stage 6 (general-purpose, READ-ONLY)
**Status**: COMPLETE

---

## §0. One-line state

**Verdict: DEFER — paper-numerics are GO (Stage 4: 91/94 GREEN, 0 RED, 3 pre-disclosed YELLOW), DIFF parity is YELLOW-acceptable (Stage 2), but bib metadata requires a 24-field correction across 14 entries (Stages 1b §9 + 1c §5) plus 2 placeholder/paywall decisions before camera-ready submission.** Total bib corrections: **24 fields across 14 entries** (8 confirmed Stage 1b + 16 NEW Stage 1c); Stage 5 topology: **10 file moves + 10 cleanup actions** recommended (Option A, LOW risk, 3 phased commits). Sandbox PDFs UNCHANGED at 16p / SHA-256 `be6c27ab…d9483` (main) + `ed09349d…02d67` (DIFF).

---

## §1. Inputs verified

| # | Report | Path | Lines | Status |
|---|---|---|---|---|
| 1 | Stage 1a — Reference Inventory | `…/paper_audit_session27_2026-05-26/01_references_inventory_report.md` | 177 | COMPLETE — READ |
| 2 | Stage 1a — xlsx delta CSV | `…/01_xlsx_delta_proposal.csv` | 68 rows × 12 cols | COMPLETE — READ |
| 3 | Stage 1b — PDF Download Manifest | `…/02_references_download_manifest.md` | 405 (+ §13 + §14) | COMPLETE — READ |
| 4 | Stage 1c — PDF Content Verification | `…/03_pdf_content_verification.md` | 423 | COMPLETE — READ |
| 5 | Stage 2 — DIFF Parity | `…/04_diff_parity_report.md` | 185 | COMPLETE — READ |
| 6 | Stage 3 — Audit History Timeline | `…/05_audit_history_timeline.md` | 899 (read 1-554 + 555-899) | COMPLETE — READ |
| 7 | Stage 3 — Open Items Checklist | `…/05_open_items_checklist.md` | 236 | COMPLETE — READ |
| 8 | Stage 4 — Paper Claim Cross-Verification | `…/06_claim_cross_verification.md` | 387 | COMPLETE — READ |
| 9 | Stage 5 — Topology Analysis | `…/07_benchmark_topology_analysis.md` | 630 (read 1-502 + 500-630) | COMPLETE — READ |
| 10 | Session 28 handoff | `…/SESSION_28_HANDOFF.md` | 436 | COMPLETE — READ |
| 11 | Sandbox `.tex` (cite-grep) | `…/sandbox-session16/main/sn-article.tex` | 789 | READ-ONLY spot-check at lines 135, 143, 160, 164, 168, 285, 383, 406, 422, 454, 707, 734, 736, 741, 768 |
| 12 | Sandbox `.bib` | `…/sandbox-session16/main/sn-bibliography.bib` | 272 (all 35 entries) | READ-ONLY full read for entry text |

No file or section listed as input could not be read. No halt-points were triggered during the cross-validation walk.

---

## §2. Cross-validation across stages

### 2.1 Stage 1a inventory ↔ Stage 1b download success — **CONSISTENT (with 1 noted reversal)**

Stage 1a §5 tagged 26 entries `DOWNLOAD_FROM_OFFICIAL` + 1 `DOWNLOAD_FROM_ANNAS` (parasuraman) + 1 `FLAG_AMBIGUITY` (chen2024autonomous) + 7 NONE (incl. 5 SKIP_EXISTS PDFs already on disk) + 4 vendor-URL-only.

Stage 1b §3 totals reconcile cleanly:
- **24 OK** (including: 21 via curl/arXiv/OpenReview/CNCF + 3 via sci-hub.ee/sci.bban.top fallback for `parasuraman2000model`, `wu2020microrank`, `chen2022automap`)
- **5 SKIP_EXISTS** (zhang2024aiopssurvey, shi2025aiopslabs, arigraph2024, bai2022constitutional, chen2024rcagent)
- **5 URL_ONLY** vendor pages (opentelemetry / datadog / grafana / nvidia / + cncf was downloaded)
- **1 FAILED_MANUAL** (`notaro2021aiopssurvey` — not in sci-hub DB across 5 mirrors × 3 DOI candidates)
- **1 NOT_ATTEMPTED** (`chen2024autonomous` — placeholder)

Stage 1a §7 Q5 recommended changing xlsx `chen2024aiopslab` cite-key to match bib `shi2025aiopslabs`. **Stage 1c §3.22 reverses this**: the PDF lead author is **Yinfang Chen** (Illinois), so the xlsx cite-key was closer to the truth all along; the bib's surname is what must be fixed (author field only; cite-key retained per session-26 stable-label rule). Reconciled in §3 below.

### 2.2 Stage 1b §9 bib errors ↔ Stage 1c confirmations — **CONSISTENT after self-correction**

Stage 1b §9 flagged 9 field-level errors across 4 entries (`miller2025bootstrap` ×4, `notaro2021aiopssurvey` ×1, `wu2020microrank` ×2, `chen2022automap` ×2).

Stage 1c §4 confirms 8 of these 9 fields via PDF content (the 1 not confirmable = notaro journal field, no PDF available). However, Stage 1c §3.24 **self-corrects** the Stage 1b §9 Q5 claim about `wu2020microrank` year: the bib already says `year = "2021"` (verified in `sn-bibliography.bib:76` — confirmed `year = "2021"`). Stage 1b §9 Q5 incorrectly stated the year needed a 2020→2021 fix; only the author field needs editing.

**Reconciled Stage 1b §9 count: 8 field-level errors across 4 entries** (not 9):
- `miller2025bootstrap`: 4 fields (author + title + year + arXiv number)
- `notaro2021aiopssurvey`: 1 field (journal — PDF-unverifiable; user manual fetch pending)
- `wu2020microrank`: **1 field** (author only — year already 2021)
- `chen2022automap`: 2 fields (author + year)

### 2.3 Stage 1c NEW bib errors ↔ Stage 4 citation-using prose — **ORTHOGONAL (no numerical impact)**

Cite-grep against `sn-article.tex` for the 10 Stage 1c-flagged keys returns the following call sites (only authoritative call sites are inside `\cite{...}`):

| Key | Lines cited in body | Function in body |
|---|---|---|
| `chen2024rcagent` | 160 | §2.1 Related Work — qualitative "RCAgent demonstrates LLM-based RCA but relies on a single model architecture" |
| `shi2025aiopslabs` | 406, 736 | §4.1 prose ("address reviewer concerns") + §6.1 Architectural-contrast novelty |
| `li2024opseval` | 422, 768 | Table 1 row + Declarations: Data availability |
| `liu2025logeval` | 406 | §4.1 prose ("address reviewer concerns") |
| `xu2025openrca` | 736 | §6.1 Architectural-contrast novelty |
| `adaspec2025` | (not cited — retained-orphan per bib comment line 2) | — |
| `askell2024collective` | 168, 383 | §2.3 ("Constitutional AI frameworks") + §3.5 ("Following Bai et al.") |
| `pei2025flowofaction` | 736 | §6.1 Architectural-contrast novelty |
| `bansal2021does` | 143 | §1 RG2 cite |
| `arigraph2024` | 164, 285 | §2.2 + §3.4 graph-episodic memory rationale |
| `chen2024autonomous` | 135 | §1 "absent safety mechanisms" cite — **load-bearing on §1 narrative**; will RED if entry stays placeholder |
| `notaro2021aiopssurvey` | 135, 160 | §1 "53% implementation failure rate" + §2.1 Related Work co-cite — **load-bearing on §1 statistic** |

None of these affect any *numerical* claim verified in Stage 4 (all 91 GREEN cells trace to `benchmark/final/`, not to external references). However, two cite sites — `chen2024autonomous` at line 135 and `notaro2021aiopssurvey` at lines 135 + 160 — depend on the entries being **real references**; both are flagged in §4 below as CRITICAL decision items.

### 2.4 Stage 2 DIFF discrepancies ↔ Stage 4 paper-claim YELLOWs — **ORTHOGONAL**

Stage 2 verdict YELLOW (acceptable) flagged 3 inherent latexdiff caveats: (a) bib edits don't show body highlights; (b) deletions suppressed by `\providecommand{\DIFdel}[1]{}` per regen recipe; (c) TikZ figures rewrapped wholesale.

Stage 4 verdict GO flagged 3 YELLOW cells: Y1 Fig 3 7-vs-8 bars; Y2 §6.2 P95 48.4 vs 48.57; Y3 BERT-F1 column scope per D-6 Option C.

**No overlap**. Stage 2 caveats are about how latexdiff renders changes; Stage 4 YELLOWs are about substantive but already-disclosed methodological choices in the live paper. Both sets of findings are independent and both lean GO/acceptable.

### 2.5 Stage 3 open items ↔ Stage 4 RED/YELLOW + Stage 1c NEW errors — **STALE FLAGS RECONCILED (see §4)**

Stage 3 checklist contains 4 stale flags (Items 14-17) reflecting pre-Gate-18 state. Post-session-28-close reality:

| Stale flag | Stage 3 state | Actual state | Resolution |
|---|---|---|---|
| Item 14 (Gate 16) | PENDING USER GO | CLOSED — committed `6aee747` at session 27 close | reclassify CLOSED |
| Item 15 (Gate 17 push) | PENDING SEPARATE USER GO | CLOSED — push landed end of session 27 | reclassify CLOSED |
| Item 16 (Stage 2 DIFF parity) | PENDING (Pair A) | CLOSED — `9110ec9` Gate 19 | reclassify CLOSED |
| Item 17 (Stage 3 timeline) | IN PROGRESS | CLOSED — `4225a91` Gate 20 (this report being synthesized) | reclassify CLOSED |
| Item 18 (Pair B Stages 4+5) | PENDING | CLOSED — `bc9f5ab` + `f57f69e` Gates 21+22 | reclassify CLOSED |
| Item 19 (Stage 6 synthesis) | PENDING | IN PROGRESS (this report) | reclassify IN PROGRESS |
| Item 20 (Edit-phase) | PENDING | PENDING — sequenced session 29+ | unchanged |

Stage 4 found 0 RED; the 3 YELLOWs are all OPTIONAL polish (not blocking). Stage 1c surfaced 16 NEW field-level bib errors (10 distinct entries); the genuinely-open items reconcile to §4 below.

### 2.6 Stage 5 topology proposal ↔ Stage 4 source-of-truth paths — **CONSISTENT (no breakage)**

Stage 4 §1 reads 14 authoritative source files under `benchmark/final/`:
1. `final/SUMMARY.md`
2. `final/main_benchmark/results_sota_eval_431.json`
3. `final/main_benchmark/results.json`
4. `final/main_benchmark/phase5_stats.json`
5. `final/main_benchmark/summary.json`
6. `final/_bert_f1_recompute_summary.json`
7. `final/ablation_v4/phase5_stats.json`
8. `final/sota_baselines/llama_3_3_70b.jsonl`
9. `final/sota_baselines/deepseek_v3.jsonl`
10. `final/sota_baselines/drain_summary.json`
11. `final/phase45_graph/exp_4_5b_summary.json`
12. `final/phase46_no_prompt/llama_noprompt_clean.jsonl`
13. `final/phase46_no_prompt/deepseek_noprompt_v2.jsonl`
14. `final/infrastructure/gate15_comparison.md`
15. `final/audit/paper_audit_session22_2026-05-26/01_numbers_audit.md` (regression baseline)

Stage 5 Option A's 10 file moves (§6.1 of Stage 5):
- Moves #1-6: 6 root underscore-prefix orphan scripts under `scripts/` → `scripts/_dev/`
- Moves #7-9: 3 raw mirror JSONLs under `raw/` → `archive/raw_pre_reorg_mirrors/`
- Move #10: top-level `INDEX_BUILD_REPORT.md` → `final/audit/SESSION_16_INDEX_BUILD_REPORT.md`

**Cross-check**: none of the 10 move targets is in Stage 4's 15-file source-of-truth list. Option A is **safe** with respect to paper-claim cross-verification reproducibility.

### 2.7 Stage 5 topology proposal ↔ Stage 3 sealed-forensic untouchability — **CONSISTENT (ADD-only)**

Stage 5 Option A move #10 (`INDEX_BUILD_REPORT.md` → `final/audit/SESSION_16_INDEX_BUILD_REPORT.md`) is sealed-tree adjacent. The action is **ADD-only** (lands a new file inside `final/audit/`); it does NOT modify any sealed-forensic doc (CV_PASS1, CV_PASS2, FULL_TRANSCRIPT_AUDIT, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, or any SESSION_12-28_HANDOFF.md). Stage 5 §7 OPEN QUESTION 1 correctly flags this for **separate USER GO**; recommend treating Move #10 as OPTIONAL commit A3 (deferrable if user prefers minimal sealed-tree adjacency).

---

## §3. Reconciled cumulative bib error catalog

**Reconciled total: 24 field-level corrections across 14 entries** (8 confirmed Stage 1b + 16 NEW Stage 1c). Math: Stage 1b §9 = 9 stated → 1 collapsed (wu year self-corrected by Stage 1c) → **8** + Stage 1c §5 = 16 NEW → cumulative **24**. The session-28 handoff §3.2 "24 field-level corrections across 14 entries" headline is correct after this reconciliation.

| # | bib_key | Field | Current (wrong) | Correct | Source | Severity | Batch |
|---|---|---|---|---|---|---|---|
| **B1** | `miller2025bootstrap` | author | `Miller, Joshua and Ruder, Sebastian and others` | `Miller, Evan` (sole author, Anthropic) | Stage 1b §9 Q1 + Stage 1c §3.17 | CRITICAL | **A** |
| **B2** | `miller2025bootstrap` | title | `Bootstrap Confidence Intervals for Evaluation Metrics in Natural Language Processing` | `Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations` | Stage 1b §9 Q1 + Stage 1c §3.17 | CRITICAL | **A** |
| **B3** | `miller2025bootstrap` | year | `2025` | `2024` | Stage 1b §9 Q1 + Stage 1c §3.17 | CRITICAL | **A** |
| **B4** | `miller2025bootstrap` | number | `arXiv:2503.01747` | `arXiv:2411.00640` | Stage 1b §9 Q1 + Stage 1c §3.17 | CRITICAL | **A** |
| **B5** | `wu2020microrank` | author | `Wu, Li and Tordsson, Johan and Elmroth, Erik and Kao, Odej` | `Yu, Guangba and Chen, Pengfei and Chen, Hongyang and Guan, Zijie and others` (Sun Yat-Sen Univ + Tencent) | Stage 1b §9 Q5 + Stage 1c §3.24 | CRITICAL | **A** |
| **B6** | `chen2022automap` | author | `Chen, Pengfei and Liu, Yu and Wu, Li` | `Ma, Meng and Wang, Ping and Xu, Jingmin and Wang, Yuan and Chen, Pengfei and Zhang, Zonghua` | Stage 1b §9 Q6 + Stage 1c §3.7 | CRITICAL | **A** |
| **B7** | `chen2022automap` | year | `2022` | `2020` (WWW 2020) | Stage 1b §9 Q6 + Stage 1c §3.7 | CRITICAL | **A** |
| **B8** | `notaro2021aiopssurvey` | journal + doi | `ACM Transactions on Networking and Service Management` (journal name does NOT exist) | likely **IEEE Transactions on Network and Service Management (TNSM)** — real DOI still **unverified** (3 candidates tested; sci-hub returned explicit not-in-DB) | Stage 1b §9 Q2 + Stage 1b §14 retry-2 | CRITICAL | **Manual fetch** (separate) |
| **C1** | `chen2024rcagent` | author | `Chen, Zefan and Liu, Yuren and Zhou, Jingwei and others` | `Wang, Zefan and Liu, Zichuan and Zhang, Yingying` (Tsinghua / Nanjing / Alibaba) — lead surname is **Wang**, not Chen | Stage 1c §3.8 / §5 N6 | **CRITICAL** | **B** |
| **C2** | `shi2025aiopslabs` | author (lead) | `Shi, Yinfang` | `Chen, Yinfang` (Illinois) — surname is **Chen**, not Shi | Stage 1c §3.22 / §5 N12 | **CRITICAL** | **B** |
| **C3** | `shi2025aiopslabs` | author (2nd) | `Bhatt, Nikhil` | `Shetty, Manish` (Berkeley) | Stage 1c §3.22 / §5 N13 | HIGH | **B** |
| **C4** | `shi2025aiopslabs` | title subtitle | `A Holistic Platform to Evaluate AI Agents for Enabling AIOps` | `A Holistic Framework to Evaluate AI Agents for Enabling Autonomous Clouds` | Stage 1c §3.22 / §5 N14 | MEDIUM | **B** |
| **C5** | `li2024opseval` | author | `Li, Liang and Zhang, Yichen and Chen, Jingwei and Wang, Hao` | `Liu, Yuhe and Pei, Changhua and Sun, Yongqian and Zhang, Shenglin and Wang, Kun and others` — lead is **Liu**, not Li | Stage 1c §3.15 / §5 N7 | **CRITICAL** | **B** |
| **C6** | `li2024opseval` | title subtitle | `Capabilities for AIOps` | `Capability in IT Operations Domain` | Stage 1c §3.15 / §5 N8 | LOW | **B** |
| **C7** | `liu2025logeval` | author | `Liu, Lingyue and Zhu, Jieming and He, Shilin and others` | `Cui, Tianyu and Ma, Shiyu and Chen, Ziang and Xiao, Tong and Tao, Shimin and Liu, Yilun and Zhang, Shenglin` — lead is **Cui**, not Liu | Stage 1c §3.16 / §5 N9 | **CRITICAL** | **B** |
| **C8** | `xu2025openrca` | author | `Xu, Yihan and Zhao, Peiliang and Wang, Mingyi and others` | `Xu, Junjielong and Zhang, Qinan and Zhong, Zhiqing and He, Shilin and others` (CUHK Shenzhen + Microsoft) — lead first-name is **Junjielong**, not Yihan | Stage 1c §3.25 / §5 N15 | **CRITICAL** | **B** |
| **C9** | `xu2025openrca` | title | `An Open Benchmark for Root Cause Analysis of Microservice Systems` | `Can Large Language Models Locate the Root Cause of Software Failures?` (actual ICLR 2025 title) | Stage 1c §3.25 / §5 N16 | HIGH | **B** |
| **C10** | `adaspec2025` | author | `Zhang, Hao and others` | `Huang, Kaiyu and Wu, Hao and Shi, Zhubo and Zou, Han and Yu, Minchen and Shi, Qingjiang` (Tongji) — lead is **Huang**, not Zhang | Stage 1c §3.1 / §5 N1 | HIGH | **C** |
| **C11** | `askell2024collective` | author | `Askell, Amanda and others` | `Huang, Saffron and Siddarth, Divya and Lovitt, Liane and others` (Collective Intelligence Project) — lead is **Huang**, not Askell | Stage 1c §3.4 / §5 N4 | HIGH | **C** |
| **C12** | `bansal2021does` | title (1-word) | `…The Effect of AI Confidence on Complementary Team Performance` | `…The Effect of AI **Explanations** on Complementary Team Performance` (CHI 2021 official title) | Stage 1c §3.5 / §5 N5 | HIGH | **C** |
| **C13** | `pei2025flowofaction` | author | `Pei, Yuwei and Yang, Cheng and Li, Jiaying and others` | `Pei, Changhua and Wang, Zexin and Liu, Fengrui and Li, Zeyan and Liu, Yang and others` (CAS/CNIC + ByteDance) — lead first-name is **Changhua**, not Yuwei | Stage 1c §3.19 / §5 N10 | HIGH | **C** |
| **C14** | `pei2025flowofaction` | title subtitle | `SOP-Enhanced LLM Agents for Automated IT Operations` | `SOP Enhanced LLM-Based Multi-Agent System for Root Cause Analysis` | Stage 1c §3.19 / §5 N11 | HIGH | **C** |
| **C15** | `arigraph2024` | author (2nd) | `Gavrilov, Nikita` | `Semenov, Nikita` (first-name matches; surname wrong) | Stage 1c §3.3 / §5 N2 | MEDIUM | **C** |
| **C16** | `arigraph2024` | author (3rd) | `Sychev, Artem` | `Sorokin, Artyom` (different person) | Stage 1c §3.3 / §5 N3 | MEDIUM | **C** |

**Totals by batch**:
- **Batch A** (Stage 1b confirmed): **7 fields across 3 entries** (miller×4, wu×1, chen-automap×2)
- **Batch B** (Stage 1c CRITICAL): **9 fields across 5 entries** (chen-rcagent×1, shi-aiopslabs×3, li-opseval×2, liu-logeval×1, xu-openrca×2)
- **Batch C** (Stage 1c HIGH/MEDIUM): **7 fields across 5 entries** (adaspec×1, askell×1, bansal×1, pei-foa×2, arigraph×2)
- **Manual fetch**: notaro2021aiopssurvey (1 field — journal + DOI; user institutional access required)

**Reconciled cumulative count: 24 field-level corrections across 14 entries.** (Batch A 7 + Batch B 9 + Batch C 7 + Manual 1 = 24; entries 3 + 5 + 5 + 1 = 14.)

**Note on cite-key stability** (session-26 lesson, carried forward): all cite-keys retained as stable labels even when surname or year now misleads (chen2024rcagent, li2024opseval, liu2025logeval, shi2025aiopslabs, xu2025openrca). Author field is what gets corrected. Rename only if reviewer flags.

---

## §4. Open items checklist (RECONCILED post-session-28-close)

### CRITICAL — blocking camera-ready

| ID | Item | Status | Batch / Action |
|---|---|---|---|
| OI-1 | Batch A bib edits (3 entries, 7 fields) — miller2025bootstrap + wu2020microrank + chen2022automap | OPEN | Phase 1 of §6 plan |
| OI-2 | Batch B bib edits (5 entries, 9 fields) — chen2024rcagent + shi2025aiopslabs + li2024opseval + liu2025logeval + xu2025openrca | OPEN | Phase 2 of §6 plan |
| OI-3 | Batch C bib edits (5 entries, 7 fields) — adaspec2025 + askell2024collective + bansal2021does + pei2025flowofaction + arigraph2024 | OPEN | Phase 3 of §6 plan |
| OI-4 | `notaro2021aiopssurvey` — journal field + real DOI unresolved; sci-hub not-in-DB across 5 mirrors × 3 candidate DOIs; user must fetch via institutional access. **Affects §1 line 135 "53% failure rate" cite + §2.1 line 160 co-cite — load-bearing on §1 narrative.** | OPEN | Phase 4 (manual fetch) |
| OI-5 | `chen2024autonomous` — placeholder cite; bib has no DOI / arXiv. **Affects §1 line 135 "absent safety mechanisms" cite — load-bearing on §1 narrative.** DECISION REQUIRED: (a) find real reference, (b) substitute, (c) remove `\cite{}` from `.tex` (would require 1-line rewrite of §1 sentence). | OPEN | Phase 4 (decision) |

### IMPORTANT — close before submission (not strictly blocking)

| ID | Item | Status | Notes |
|---|---|---|---|
| OI-6 | Gate 16 (session-27 close-out commit `6aee747`) | CLOSED at session 27 close | Stale Stage 3 flag reconciled |
| OI-7 | Gate 17 (push of Gates 14+15+16) | CLOSED at session 27 close | Stale Stage 3 flag reconciled |
| OI-8 | Gate 19 — Stage 2 DIFF parity commit (`9110ec9`) | CLOSED session 28 | Stale Stage 3 flag reconciled |
| OI-9 | Gate 20 — Stage 3 audit commit (`4225a91`) | CLOSED session 28 | Stale Stage 3 flag reconciled |
| OI-10 | Gate 21 — Stage 4 commit (`bc9f5ab`) | CLOSED session 28 | Stale Stage 3 flag reconciled |
| OI-11 | Gate 22 — Stage 5 commit (`f57f69e`) | CLOSED session 28 | Stale Stage 3 flag reconciled |
| OI-12 | Gates 23 + 24 (session-28 close-out commit + batched push of Gates 18-23) | CLOSED at session 28 close per session-28 handoff §12 | Stale Stage 3 flag reconciled |
| OI-13 | 3 sci-hub-sourced PDFs (parasuraman / wu / chen-automap) — protocol drift decision | OPEN | DECISION: keep (substantively-equivalent) OR replace via institutional access. All 3 passed 5-point verification (authentic publisher PDFs, not scraped HTML); SHAs in Stage 1b §4 + retry-2. |
| OI-14 | xlsx update from Stage 1a draft CSV (`01_xlsx_delta_proposal.csv`) — 68 rows × 12 cols | OPEN | Apply after all bib edits land; reflect Stage 1c surname-correction reversals (e.g., xlsx `chen2024aiopslab` actually closer to truth than bib `shi2025aiopslabs`). |
| OI-15 | Topology Option A commit A1 (6 root orphans → `_dev/` + scripts/README regen 34→43) | OPEN | Phase 5 of §6 plan |
| OI-16 | Topology Option A commit A2 (3 raw mirrors → `archive/raw_pre_reorg_mirrors/` + INDEX.md tally + 3 README annotations) | OPEN | Phase 5 of §6 plan |
| OI-17 | Topology Option A commit A3 OPTIONAL (`INDEX_BUILD_REPORT.md` relocate) | OPEN | Phase 5 of §6 plan — requires separate USER GO (sealed-tree adjacency) |
| OI-18 | Stage 4 Y1 — Figure 3 caption clarify ("With-orchestrator omitted because identical to With-graph on 357/357") | OPEN | Phase 6 of §6 plan (OPTIONAL polish) |
| OI-19 | Stage 4 Y2 — §6.2 P95 align to Table 4 (48.4 → 48.6 OR cross-pointer) | OPEN | Phase 6 of §6 plan (OPTIONAL polish) |
| OI-20 | Stage 4 Y3 — BERT-F1 per-config in Tables 5/6/7 (only if layout room after bib edits) | OPEN | Phase 6 of §6 plan (OPTIONAL polish) |

### NICE-TO-HAVE — reviewer-flag-only

| ID | Item | Status |
|---|---|---|
| OI-N1 | Cite-key renames for surname-mismatch entries (chen2024rcagent → wang…, li2024opseval → liu…, shi2025aiopslabs → chen…, etc.) | DEFER — cosmetic per session-26 rule |
| OI-N2 | Path B'' Tier 2 — peng + zhang vol/issue/pages (30-50% chance of 17p overshoot) | DEFER — DOI alone is sufficient |
| OI-N3 | BERT-F1 re-run with MIN_TEXT_LEN=5 (D-6 known artifact: ablation_no_system_prompt Ann n=1, ablation_with_graph Ann n=0) | DEFER |
| OI-N4 | M-3 pre-D-1 `excluded_rca_cases.json` legacy file housekeeping | DEFER |
| OI-N5 | M-4 stale `main_benchmark/summary.json` housekeeping | DEFER |
| OI-N6 | Abstract / §1 tone polish | DEFER — locked "preserve as-accepted" sessions 25+ |
| OI-N7 | Path G submit (`main/sn-article.pdf` directly) | DEFER — pending COMSYS 2026 CFP open |

### DEFERRED — out-of-scope unless reviewer demands

| ID | Item | Status |
|---|---|---|
| OI-D1 | Path D — Stack B full 431-case latency re-run (~$5, ~3h) | DEFER |
| OI-D2 | Path D — Phase 4.5c cold-start curve (~$5, ~5h) | DEFER |
| OI-D3 | Brittlebench / C3AI bib additions (audit M-2) | DEFER — judged intentional drops per page budget |
| OI-D4 | CV 5th agent (D-10) | DEFER — superseded by multi-agent audits |

**NEW DISCOVERY (Stage 6)**: none. All findings traceable to Stages 1a-5.

---

## §5. Camera-ready verdict

**Verdict: DEFER** (defensible but needs polish before submitting).

**Defense**: On the *numerical* front, the paper is camera-ready. Stage 4 verified 91 of ~94 cells GREEN within strict tolerance (≤0.05pp / ≤0.5s / ≤1e-3), with 0 RED and 3 YELLOWs that are all pre-disclosed methodological choices (Y1 collapsed-bar Figure 3, Y2 percentile-method spread within disclosed 0.3s tolerance, Y3 BERT-F1 column omitted per locked D-6 Option C). Stage 2 verified all 23 cumulative session-23..26 paper edits are present in sandbox AND marked in DIFF with zero false-positives and zero false-negatives in the strict latexdiff sense; the 3 latexdiff caveats are inherent (bib edits invisible / deletions suppressed / TikZ rewrapped wholesale) and acceptable for a reviewer-shared DIFF if a 1-sentence cover-note discloses them. The 16-page invariant has held through all of sessions 23-26's fixes. However, the *bibliography* requires 24 field-level corrections across 14 entries (Stage 1b confirmed 8 + Stage 1c NEW 16) before the paper can be submitted with integrity, and two cite sites on page 1 (`chen2024autonomous` line 135 + `notaro2021aiopssurvey` line 135/160) depend on placeholder/paywalled entries that need user decision and manual fetch. None of these blocks the numerical claims, but submitting with a placeholder cite for the "53% failure rate" statistic or an entry whose lead author surname is wrong (e.g., Chen → Wang for RCAgent) is a defensible reviewer complaint. Hence: DEFER until §6 Phases 1-4 land; Phases 5-7 are OPTIONAL polish that can ride the same release window.

---

## §6. Phased edit plan for session 29+

Each phase = at least one atomic, themed commit. USER GO required before each commit. USER GO required separately before each push.

### Phase 1 — Batch A bib edits (Stage 1b confirmed; 3 entries / 7 fields)

**Pre-conditions**: clean tree post-Gate-24 push; sandbox PDFs at known SHA-256s; Perl on PATH (for DIFF regen).

**Files changed**:
- `…/sandbox-session16/main/sn-bibliography.bib` (3 entry blocks edited)
- After recompile: `…/main/sn-article.pdf` + `…/diff/sn-article-DIFF.pdf` regenerated

**Process**:
1. Edit `miller2025bootstrap` block (sandbox bib lines 235-241): replace 4 fields (B1-B4) — note that `@techreport` becomes either `@techreport` (preserve) or `@misc` (per arXiv convention). Min-viable: keep `@techreport` with `institution = "Anthropic"` swap from "arXiv".
2. Edit `wu2020microrank` block (lines 72-77): replace `author=` (B5) only; year already 2021.
3. Edit `chen2022automap` block (lines 79-84): replace `author=` (B6) + `year=` "2022"→"2020" (B7).
4. Recompile `main/sn-article.tex` via `pdflatex; bibtex; pdflatex; pdflatex`.
5. Verify `pdfinfo` shows **Pages: 16** (16p invariant).
6. Regen DIFF via `regen_diff_pdf.py` (per session-24 recipe encoded in script).
7. Spot-check DIFF pp.15-16 (bib renders): all 3 entries should show updated metadata.
8. Themed commit: `fix(paper-bib-batch-A): apply Stage 1b verified author/year corrections to miller/wu/chen-automap`.

**Verification gates**:
- `pdfinfo main/sn-article.pdf` → **Pages: 16** (not 17)
- `pdfinfo diff/sn-article-DIFF.pdf` → **Pages: 16**
- SHA-256 of main PDF changes (expected — content drifted)
- Visual spot-check pp.15-16 confirms 3 entries updated

**Rollback**: if 17p overshoot, trim min-viable per session-25 rule (drop DOI / volume / institution to fit). If still 17p, defer offending entry to Batch B/C and reorder.

**Estimated runtime**: 20-30 min including 2 pdflatex passes + DIFF regen + spot-check.

### Phase 2 — Batch B bib edits (Stage 1c CRITICAL; 5 entries / 9 fields)

**Pre-conditions**: Phase 1 GREEN; clean working tree.

**Files changed**: `…/main/sn-bibliography.bib` (5 entry blocks edited) + recompiled PDFs.

**Process**:
1. Edit `chen2024rcagent` (bib lines 65-70): replace `author=` (C1). Cite-key retained as stable label per session-26 rule. **Sanity-check**: confirm the surname-Chen-misleading cite-key change is documented in commit message.
2. Edit `shi2025aiopslabs` (lines 205-210): replace `author=` (C2 lead surname Shi→Chen) + `author=` 2nd author (C3 Bhatt→Shetty) + `title` subtitle (C4 "Platform→Framework" + "AIOps→Autonomous Clouds"). **Reversal note**: this reverses Stage 1a §7 Q5 direction.
3. Edit `li2024opseval` (lines 173-178): replace `author=` (C5 lead Li→Liu) + `title` subtitle (C6).
4. Edit `liu2025logeval` (lines 226-233): replace `author=` (C7 lead Liu→Cui).
5. Edit `xu2025openrca` (lines 212-217): replace `author=` (C8 lead first-name Yihan→Junjielong) + `title` (C9 replace whole title).
6. Recompile main + DIFF; verify 16p; spot-check pp.15-16.
7. Themed commit: `fix(paper-bib-batch-B): apply Stage 1c CRITICAL lead-author/title corrections to 5 entries (cite-keys retained as stable labels)`.

**Verification gates**: same as Phase 1.

**Rollback**: same as Phase 1 (min-viable trim). Note title-rewrites (C4, C6, C9) add ~30-60 chars each entry; risk of 17p overshoot is HIGHER than Phase 1.

**Estimated runtime**: 30-40 min.

### Phase 3 — Batch C bib edits (Stage 1c HIGH/MEDIUM; 5 entries / 7 fields)

**Pre-conditions**: Phase 2 GREEN.

**Files changed**: `…/main/sn-bibliography.bib` (5 entry blocks) + recompiled PDFs.

**Process**:
1. Edit `adaspec2025` (bib lines 250-256): replace `author=` (C10).
2. Edit `askell2024collective` (lines 101-106): replace `author=` (C11). Note: cite-key `askell…` retained as stable label even though Askell is no longer the lead author.
3. Edit `bansal2021does` (lines 57-63): replace `title` (C12 1-word change: Confidence → Explanations).
4. Edit `pei2025flowofaction` (lines 219-224): replace `author=` (C13) + `title` subtitle (C14).
5. Edit `arigraph2024` (lines 86-92): replace `author=` 2nd + 3rd authors (C15 + C16).
6. Recompile + verify 16p + spot-check pp.15-16.
7. Themed commit: `fix(paper-bib-batch-C): apply Stage 1c HIGH/MEDIUM author/title corrections to 5 entries`.

**Estimated runtime**: 25-35 min.

### Phase 4 — Manual fetches + decisions (2 items; user-driven)

**Pre-conditions**: Phases 1-3 GREEN; user has time to do institutional library fetches.

**Files potentially changed**: `…/main/sn-bibliography.bib` (1-2 entry blocks) + possibly `…/main/sn-article.tex` (if removing chen2024autonomous cite).

**Process**:
1. **notaro2021aiopssurvey**: user fetches via institutional ACM/IEEE access; report back the real DOI and journal. Then edit bib entry's `journal` + `doi` fields (and `volume`/`number` if user wants — but min-viable rule says DOI alone is sufficient).
2. **chen2024autonomous**: user decision among:
   - (a) find a real reference for "absent safety mechanisms preventing autonomous remediation adoption" → replace bib entry + cite stays
   - (b) substitute with one of bai2022constitutional / askell2024collective which are already cited adjacent → remove the placeholder bib entry + edit §1 line 135 to drop the `chen2024autonomous` cite
   - (c) remove entirely: edit §1 line 135 to drop the cite + remove bib entry (4-line block)
3. Recompile main + DIFF; verify 16p.
4. Themed commit per item: `fix(paper-bib-notaro): apply user-confirmed DOI + journal correction` and `fix(paper-cite-chen2024autonomous): <substitute|remove>`.

**Verification gates**: 16p preserved; if chen2024autonomous removed, verify §1 prose still reads cleanly (the sentence at line 135 has 4 cites: opentelemetry / datadog (separate cite); zhang2024aiopssurvey; notaro2021aiopssurvey; **chen2024autonomous**; alibaba2024qwen — drop the 4th cite cleanly).

**Estimated runtime**: depends on user availability for institutional fetch; bib edit + recompile ~15 min once data is in hand.

### Phase 5 — Topology Option A (3 phased sub-commits per Stage 5 §8.1)

**Pre-conditions**: Phases 1-3 GREEN (Phase 4 can land in parallel since topology is orthogonal to paper).

**Files changed** (Option A summary; see Stage 5 §6.1):

**Commit A1** — folder 6 root underscore-orphans into `_dev/`:
- 6 `git mv` operations under `benchmark/scripts/`
- Regen `scripts/README.md` (34→43 script catalog)
- Pre-commit: `find benchmark/scripts -maxdepth 1 -type f -name "_*.py"` returns 0

**Commit A2** — archive 3 raw mirrors:
- 3 `git mv` from `benchmark/raw/` → `benchmark/archive/raw_pre_reorg_mirrors/`
- Add `_NOTICE.md` in new archive subdir
- Update `INDEX.md` §1 partition tally
- Add 1-line note to `intermediate/README.md` (canonical dataset = `benchmark_431_seed42.json`)
- Add 1-line note to `final/main_benchmark/README.md` (canonical = `results_sota_eval_431.json`)

**Commit A3 (OPTIONAL — separate USER GO required, sealed-tree adjacent)**:
- `git mv benchmark/INDEX_BUILD_REPORT.md benchmark/final/audit/SESSION_16_INDEX_BUILD_REPORT.md`

**Process** per Stage 5 §6.3:
1. Run topology-changing git mv operations.
2. Edit docs as specified.
3. Re-run `python benchmark/scripts/eval/verify_authoritative_numbers.py` — should exit 0 with same headline numbers (Ann 82.6 / RCA 82.0 / Overall 82.4).
4. Re-run `python benchmark/scripts/eval/inspect_all_configs.py` — should exit 0 with same cross-config audit.
5. Themed commits per sub-commit.

**Verification gates**: numerical re-verify passes; sandbox PDFs UNCHANGED (topology moves do NOT touch paper).

**Rollback**: each commit is atomic and reversible via `git revert`.

**Estimated runtime**: ~45-60 min total for A1+A2 (A3 ~10 min additional if user approves).

### Phase 6 — OPTIONAL Stage 4 YELLOW polish

**Pre-conditions**: Phases 1-3 GREEN; user wants extra polish.

**Files changed**: `…/main/sn-article.tex` only.

**Process** (any subset; all OPTIONAL):
- **Y1**: edit Figure 3 caption (sandbox line ~698) to add clause: "With-orchestrator omitted; identical to With-graph on all 357/357 cells (see Tables~\ref{tab:ablation_arch}+\ref{tab:ablation_comp})." This pre-empts a reviewer count-mismatch question against the abstract's "8-configuration" claim.
- **Y2**: edit §6.2 line 741 — change "P95 48.4\,s" → "P95 48.6\,s" (index-floor convention rounded to 1dp, consistent with Table 4 footnote). OR add parenthetical "(linear-interp; Table~\ref{tab:latency} index-floor 48.57\,s)".
- **Y3**: ONLY if Stage 5 finds layout room — add BERT-F1 column to Tables 5/6/7 from `_bert_f1_recompute_summary.json` (Full=0.8126 / Single-4B=0.8176 / Single-14B=0.8083 / No-structured=0.8377 / No-sys-prompt=0.8102 / With-graph=0.8116 / No-constitutional=0.8238 / With-orchestrator=0.8113; Llama=0.8269 / DeepSeek=0.8264). HIGH risk of 17p overshoot.

Recompile + verify 16p + themed commit per item.

**Estimated runtime**: 10-20 min per Y item.

### Phase 7 — Final batched push

**Pre-conditions**: All commits land locally; user gives separate push GO.

**Process**: `git push origin main` — single batched push of Phase 1-6 commits.

**Estimated runtime**: <5 min.

---

## §7. Risks + mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **17p overshoot from bib edits** (Phase 1-3) — title rewrites in Batch B (C4 C6 C9) + Batch C (C12 C14) each add 30-60 chars to References; cumulatively can push to 17p | MEDIUM (precedent: Path B'' Tier 2 deferred sessions 24/26 at 30-50% overshoot risk) | HIGH (breaks 16p invariant; reorder needed) | Min-viable rule per session-25 lesson (DOI alone, no vol/issue/pages on new entries); rollback offending edits; reorder Batches; consider deferring largest title rewrites to last commit; verify 16p after EACH commit not just at end |
| **Cite-key renames cosmetic mismatch** (5 keys now have surname or first-name mismatch: chen2024rcagent → Wang, shi2025aiopslabs → Chen, li2024opseval → Liu, liu2025logeval → Cui, xu2025openrca → Junjielong Xu) | HIGH (purely cosmetic) | LOW (cite-key stable-label rule established sessions 24-26; no reviewer impact expected) | Defer rename to NICE-TO-HAVE OI-N1; only act if reviewer flags |
| **Sci-hub-sourced PDFs as protocol drift** (parasuraman / wu / chen-automap) | Already in repo | LOW | Documented in Stage 1b §13/§14 as protocol drift; PDFs passed 5-point verification (authentic publisher PDFs, not scraped); replace via institutional access only if user prefers cleaner provenance |
| **chen2024autonomous decision delay blocks §1 cite resolution** | MEDIUM | MEDIUM (line 135 keeps a placeholder cite until decided) | Place Phase 4 decisions early in session 29; substitute with bai2022constitutional / askell2024collective if user prefers fast close |
| **notaro DOI still unverified across 5 sci-hub mirrors × 3 candidates** | HIGH | MEDIUM (line 135 "53% failure rate" stat still cites placeholder journal name) | User institutional ACM/IEEE access fetch; verify TNSM 18(4) 2021 candidate (most likely DOI 10.1109/TNSM.2021.3107504) |
| **Stage 5 Option A risks** | LOW for A1+A2 (10 git mv; 0 importers per Stage 5 §2.2); MEDIUM for A3 (sealed-tree adjacent) | LOW | A3 split as separate OPTIONAL commit with separate USER GO; verify numerical re-runs post-each-A-commit |
| **DIFF regen requires Perl on PATH + LF write + listings drop** (encoded in `regen_diff_pdf.py` per session-24 recipe) | LOW (script encodes lesson) | MEDIUM (breaks DIFF if missed) | Use the existing script; do NOT call latexdiff directly |
| **Stage 3 stale flags Items 14-17 already CLOSED before session 29 starts** | LOW (reconciled in §4 above) | LOW | Use §4 reconciled table going forward; do NOT use Stage 3 Item-14 onwards from `05_open_items_checklist.md` |
| **Reference paper instance src/ outdated** (instance still has buggy D-17 + missing `find_similar_episodes_by_embedding`) | Carried-forward rule | LOW (no AWS work in session 29) | Rule 17: instance `src/` outdated; always scp if re-running Phase 4.5 |

**No genuine contradictions between prior reports** were surfaced during the cross-validation walk. The one possible contradiction (Stage 1b §9 Q5 said wu year 2020→2021 fix; Stage 1c §3.24 said year already 2021) is a self-correction within Stage 1c, not an unresolved contradiction. Reconciled in §3 (Batch A wu entry has only 1 field correction, not 2).

---

## §8. Recommendations summary

Ordered by priority. Each is actionable and traceable to a §6 phase.

1. **HIGHEST**: Apply Batch A bib edits (§6 Phase 1). 3 entries / 7 fields confirmed by both Stage 1b §9 and Stage 1c §4. Low-risk; precedent for the bib-edit recompile + DIFF regen workflow established sessions 23-26. **USER GO required.**

2. **HIGH**: Apply Batch B bib edits (§6 Phase 2) — 5 entries / 9 fields. These include 5 CRITICAL lead-author surname corrections (chen2024rcagent: Wang; shi2025aiopslabs: Chen; li2024opseval: Liu; liu2025logeval: Cui; xu2025openrca: Junjielong Xu first-name). Cite-keys retained as stable labels per session-26 lesson. **USER GO required.**

3. **HIGH**: Apply Batch C bib edits (§6 Phase 3) — 5 entries / 7 fields. HIGH/MEDIUM severity (adaspec / askell / bansal title-1-word / pei-foa / arigraph 2nd+3rd authors). **USER GO required.**

4. **HIGH (user-driven)**: Resolve §6 Phase 4 manual fetches/decisions — notaro institutional fetch + chen2024autonomous (find / substitute / remove). Both load-bearing on §1 line 135 prose. **USER decision required before edit.**

5. **MEDIUM**: Apply Stage 5 Option A topology (§6 Phase 5 commits A1+A2) — 9 moves + 4 doc edits + 1 README regen. Verifies numerical re-runs pass (`verify_authoritative_numbers.py` + `inspect_all_configs.py`). Defer commit A3 (sealed-tree adjacent) for separate USER GO. **USER GO required per commit.**

6. **OPTIONAL**: Stage 4 YELLOW polish (§6 Phase 6 Y1+Y2; defer Y3 unless layout room confirmed). 1-line caption clarification on Figure 3 + percentile alignment on §6.2 are low-risk and reviewer-friendly. **USER decision (low priority).**

7. **REVIEWER-FLAG-ONLY (defer)**: OI-N1 cite-key renames; OI-N2 vol/issue/pages; OI-N3 BERT-F1 MIN_TEXT_LEN=5 re-run; OI-N4/N5 housekeeping; OI-N6 tone polish; OI-N7 Path G submit. None blocks camera-ready; act only if reviewers flag.

8. **CARRY-FORWARD**: After §6 Phases 1-4 land + verify 16p, the paper is ready for COMSYS 2026 camera-ready submission (Path G when CFP opens). Submission file IS `main/sn-article.pdf` directly (no package folder per session-26 lesson). Hold separate USER GO for Phase 7 batched push.

9. **HARD-RULES carry-forward** (18 rules + 6 process lessons per session-28 handoff §5): no Claude trailer; no push without GO; sandbox `main/` only; never touch real `sn-article-template.v2/`; 3-point rubric mentions at lines 447 + 597 are INTENTIONAL DISCLOSURES; min-viable bib rule; cite-key as stable label; DIFF regen via `regen_diff_pdf.py` only; verify 16p after each commit.

10. **DOCUMENTATION HYGIENE**: At session-29 close (Gate 25+), update MEMORY.md SESSION 29 STARTUP block to reflect §4 reconciliations (mark Items 14-17 + 18 as CLOSED with commit hashes from sessions 27-28); record Phase 1-7 outcomes; carry forward this synthesis report as a primary reference for any follow-up session.

---

*End of Stage 6 Final Synthesis. Cross-link companions: 5 prior stage reports in same dir + SESSION_28_HANDOFF.md. Ready for review.*
