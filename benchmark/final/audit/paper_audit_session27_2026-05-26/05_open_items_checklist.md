# Stage 3 — Open Items Checklist (Currently Pending for Edit-Phase)

**Generated**: 2026-05-27 (session 28)
**Source**: Stage 3 audit history timeline (`05_audit_history_timeline.md`)
**Companion**: Stage 1b `02_references_download_manifest.md` §9 + §13 + §14; Stage 1c `03_pdf_content_verification.md` §3

This checklist is the actionable-deliverable from the Stage 3 audit. Each item references its origin session AND its current status. Companion Stage 6 (planned session 28) will synthesize this with Stages 2/4/5 outputs to produce the phased edit plan.

---

## CRITICAL (must close before camera-ready submission)

### Bib metadata corrections (Edit-phase batch 1)

- [ ] **Item-1: `miller2025bootstrap` — 4-field bib correction** (Stage 1b §9 Q1; Stage 1c confirmed KBE)
  - Author: `Miller, Joshua and Ruder, Sebastian and others` → `Miller, Evan` (Anthropic, sole author)
  - Title: `Bootstrap Confidence Intervals for Evaluation Metrics in NLP` → `Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations`
  - Year: `2025` → `2024`
  - arXiv: `2503.01747` → `2411.00640`
  - Cite key preserved (rule: cite-key as stable label)
  - **PDF on disk correct**: `miller2025bootstrap - Adding Error Bars to Evals - 2411.00640.pdf` (s27 retry-2)
  - Origin: Session 27 Stage 1b verification

- [ ] **Item-2: `wu2020microrank` — 2-field bib correction** (Stage 1b §9 Q5; Stage 1c confirmed KBE)
  - Author: `Wu, Li and Tordsson, Johan and Elmroth, Erik and Kao, Odej` → lead author **Guangba Yu** (Sun Yat-Sen Univ) + Pengfei Chen (corresponding); author list completely wrong
  - Year: `2020` → `2021` (WWW 2021)
  - Cite key preserved
  - **PDF on disk correct**: `wu2020microrank - MicroRank ... acm-www2021-microrank.pdf` (s27 retry-2 via sci-hub)
  - Origin: Session 27 Stage 1b retry-2

- [ ] **Item-3: `chen2022automap` — 2-field bib correction** (Stage 1b §9 Q6; Stage 1c confirmed KBE)
  - Author: `Chen, Pengfei and Liu, Yu and Wu, Li` → lead authors **Meng Ma + Ping Wang** (PKU); Pengfei Chen is 5th author
  - Year: `2022` → `2020` (WWW 2020)
  - Cite key preserved
  - **PDF on disk correct**: `chen2022automap - AutoMAP ... acm-www2020-automap.pdf` (s27 retry-2 via sci-hub)
  - Origin: Session 27 Stage 1b retry-2

### Bib metadata corrections (Edit-phase batch 2 — NEW Stage 1c findings)

- [ ] **Item-4: `adaspec2025` — NEW author + minor title drift** (Stage 1c §3.1 NBE)
  - Author: `Zhang, Hao and others` → lead author **Kaiyu Huang** (Tongji); Hao Wu is 2nd author
  - Title subtitle drift acceptable (same paper)
  - Year/venue OK
  - **PDF on disk correct**

- [ ] **Item-5: `askell2024collective` — NEW author correction** (Stage 1c §3 NBE)
  - Author: `Askell, Amanda and others` → lead authors **Saffron Huang + Divya Siddarth + Liane Lovitt**; Askell is co-author not first
  - Other fields OK

- [ ] **Item-6: `chen2024rcagent` — NEW author correction** (Stage 1c §3 NBE)
  - Author: `Chen, Zefan and Liu, Yuren and Zhou, Jingwei` → actual authors **Zefan Wang** (Tsinghua) + Zichuan Liu (NJU) + Yingying Zhang (Alibaba)
  - **Surname Chen does NOT appear on the paper at all** — cite-key may need rename too (decision)
  - Title/year/venue OK

- [ ] **Item-7: `li2024opseval` — NEW author + minor title drift** (Stage 1c §3 NBE)
  - Author: `Li, Liang and Zhang, Yichen and Chen, Jingwei and Wang, Hao` → lead author **Yuhe Liu** (Tsinghua); no "Li, Liang" on paper
  - Title slight drift: `Capabilities for AIOps` → `Capability in IT Operations Domain`
  - **Surname Li does NOT appear on the paper** — cite-key may need rename (decision)
  - Year/venue OK

- [ ] **Item-8: `liu2025logeval` — NEW author + year correction** (Stage 1c §3 NBE)
  - Author: `Liu, Lingyue and Zhu, Jieming and He, Shilin` → lead author **Tianyu Cui** (Nankai); Yilun Liu IS on paper as 6th author but "Liu, Lingyue" does not appear
  - Year: bib 2025 vs arXiv 2024 — likely EmSE publication 2025 (acceptable preprint→journal gap)

- [ ] **Item-9: `pei2025flowofaction` — NEW author first-name + subtitle correction** (Stage 1c §3 NBE)
  - Author: `Pei, Yuwei and Yang, Cheng and Li, Jiaying` → lead author **Changhua Pei** (CAS), not Yuwei Pei
  - Title subtitle: `SOP-Enhanced LLM Agents for Automated IT Operations` → `SOP Enhanced LLM-Based Multi-Agent System for Root Cause Analysis`

- [ ] **Item-10: `shi2025aiopslabs` — NEW author correction (cite-key implication)** (Stage 1c §3 NBE)
  - Author: `Shi, Yinfang and Bhatt, Nikhil and Ma, Minghua` → lead author **Yinfang Chen** (Illinois), not Yinfang Shi; Manish Shetty is 2nd not Bhatt; Minghua Ma is 4th
  - Title: `Holistic Platform...for Enabling AIOps` → `Holistic Framework...for Enabling Autonomous Clouds`
  - **Surname Shi mismatches — cite-key may need rename to `chen2025aiopslabs`** (decision)

- [ ] **Item-11: `xu2025openrca` — NEW author first-name + title correction** (Stage 1c §3 NBE)
  - Author: `Xu, Yihan and Zhao, Peiliang and Wang, Mingyi` → lead author **Junjielong Xu** (CUHK Shenzhen), not Yihan Xu; 2nd author Qinan Zhang
  - Title: `An Open Benchmark for Root Cause Analysis of Microservice Systems` → `Can Large Language Models Locate the Root Cause of Software Failures?`

### Unresolved bib placeholders

- [ ] **Item-12: `notaro2021aiopssurvey` — journal field + DOI unresolved** (Stage 1b §9 Q2)
  - Current journal field: `ACM Transactions on Networking and Service Management` (journal does NOT exist)
  - Likely real: `IEEE Transactions on Network and Service Management` (TNSM) — needs user manual verification of real DOI; sci-hub doesn't have this paper across 5 mirrors
  - **DECISION REQUIRED**: user manual institutional fetch + DOI verification + journal field correction
  - Origin: Session 27 Stage 1b retry-2

- [ ] **Item-13: `chen2024autonomous` — placeholder cite, no DOI/arXiv** (Stage 1b §13)
  - Bib has placeholder metadata only
  - **DECISION REQUIRED**: (a) find real reference, (b) substitute with verified work, or (c) remove `\cite{}` from `.tex`

### Pending commits + push (session 27 carry-forward)

- [ ] **Item-14: Gate 16 — session 27 close-out commit** (PENDING USER GO)
  - Files: `02_references_download_manifest.md` (+§14), `SESSION_27_HANDOFF.md` (new), `benchmark/HANDOFF.md` (update), `MEMORY.md` (auto-memory), `reference_session28_starter_prompt.md` (new auto-memory)
  - Suggested commit message: `docs(audit-session27): close-out — Stage 1b retry-2 + handoff + memory + session-28 starter`

- [ ] **Item-15: Gate 17 — batched push (Gates 14 + 15 + 16)** (PENDING SEPARATE USER GO at session close)
  - 3 local commits ahead of origin: `5bfbabe` + `e82f5cd` + `<Gate-16-hash>`
  - Single command: `git push origin main`

### Session 28 verification stages remaining

- [ ] **Item-16: Stage 2 — DIFF parity v1 ↔ sandbox ↔ DIFF** (text + visual 16-page export)
  - Sequenced as Pair A with this Stage 3 (running parallel session 28)
  - Output: `04_diff_parity_audit.md` (Stage 2's slot)

- [ ] **Item-17: Stage 3 — Audit History Timeline** (THIS DELIVERABLE — IN PROGRESS)
  - Output: `05_audit_history_timeline.md` + this checklist

- [ ] **Item-18: Pair B — Stages 4 + 5 parallel** (session 28)
  - Stage 4 = Paper claim ↔ benchmark cross-verification (per-cell GREEN/YELLOW/RED): `06_*.md`
  - Stage 5 = Benchmark dir analysis + ≥2 alternative topologies (no moves — report only): `07_*.md`

- [ ] **Item-19: Stage 6 — Final synthesis** (session 28 solo, after Pair B)
  - Cross-validates all 5 prior reports + edit-list synthesis with CRITICAL/IMPORTANT/NICE-TO-HAVE priority + phased edit plan
  - Output: `08_synthesis.md` (Stage 6's slot)

- [ ] **Item-20: Edit-phase** (post-Stage-6)
  - Apply the 9 Stage-1b bib metadata fixes + 8 Stage-1c bib fixes + chen2024autonomous decision + notaro manual fetch + any Stage 4 RED claims + Stage 5 topology moves
  - Phased commits with main + DIFF recompile after each batch
  - Verify 16p preserved throughout

---

## IMPORTANT (should close)

- [ ] **Item-A: 3 sci-hub-sourced PDFs — protocol drift decision** (Stage 1b)
  - Files: `parasuraman2000model` (IEEE 2000), `wu2020microrank` (ACM WWW 2021), `chen2022automap` (ACM WWW 2020)
  - All 3 passed 5-point verification (authentic publisher PDFs, not scraped HTML)
  - **DECISION REQUIRED**: keep (substantively-equivalent shadow lib disclosed in manifest) OR replace via institutional access
  - Origin: Session 27 Stage 1b

- [ ] **Item-B: arigraph2024 2nd/3rd author drift** (Stage 1c separately flagged)
  - Bib: `Anokhin, Petr and Gavrilov, Nikita and Sychev, Anton` → actual: Anokhin matches but 2nd+3rd are Semenov/Sorokin
  - Edit if user wants full author-list accuracy

- [ ] **Item-C: bansal2021does title drift** (Stage 1c)
  - Bib: `AI Confidence on Complementary Team Performance` → PDF: `AI Explanations on Complementary Team Performance`
  - Likely same paper with reformulated title; edit if user wants verbatim

- [ ] **Item-D: xlsx update — Stage 1a draft CSV** (`01_xlsx_delta_proposal.csv`)
  - 68 rows × 12 cols with new Status/Action/Notes columns
  - Not yet applied to the live xlsx
  - Coordinated pass after all session-28 stages close

- [ ] **Item-E: Path B'' Tier 2 — peng + zhang vol/issue/pages** (Audit I-A; deferred s24/s26)
  - DOI alone is sufficient (current state) but vol/issue/pages would add article-level granularity
  - 30-50% chance of 17p overshoot per session-25 precedent if added
  - Revisit only if reviewer flags

---

## NICE-TO-HAVE

- [ ] **Item-N1: Cite-key renames** (Path B'' Tier 3; audit M-2 adjacent)
  - `zhang2024aiopssurvey` → `zhang2026aiopssurvey` (year now 2026)
  - `nvidia2024specdec` → `nvidia2025specdec` (year now 2025)
  - `peng2025graphragsurvey` → `peng2026graphragsurvey` (year now 2026)
  - Plus potential `chen2024rcagent` → `wang2024rcagent` (Stage 1c surname change)
  - Plus potential `li2024opseval` → `liu2024opseval` (Stage 1c surname change)
  - Plus potential `shi2025aiopslabs` → `chen2025aiopslabs` (Stage 1c surname change)
  - 9+ `.tex` `\cite{}` site edits + bib renames; cosmetic; reviewer-flag-only justified

- [ ] **Item-N2: BERT-F1 re-run with MIN_TEXT_LEN=5** (D-6 known artifact carry-forward)
  - To fill the `ablation_no_system_prompt` Ann n=1 + `ablation_with_graph` Ann n=0 cells
  - Out of scope unless reviewer asks
  - Origin: Session 18 D-6 background recompute

- [ ] **Item-N3: M-3 / M-4 housekeeping** (Audit MINOR)
  - M-3: pre-D-1 `excluded_rca_cases.json` legacy file on disk — described as legacy in METHODOLOGY; could delete or archive
  - M-4: stale `main_benchmark/summary.json` byte-identical to `benchmark_result.json` with pre-D-1 rich-eval numbers; not cited in paper; could delete

- [ ] **Item-N4: Abstract / §1 tone polish**
  - User locked sessions 25+: preserve as-accepted; correct only if factual error surfaces
  - None found across sessions 25-27 + Stage 1c verification

- [ ] **Item-N5: Path G — Submit camera-ready**
  - Pending COMSYS 2026 CFP open
  - Submission file IS `main/sn-article.pdf` directly (16p, 467,673 B, SHA-256 `be6c27ab…d9483`)
  - If LaTeX source bundle requested at upload time, zip `main/` on the spot

---

## DEFERRED (out of scope for camera-ready; track but don't close)

- [ ] **Item-Def-1: Path D — Stack B full 431-case latency re-run** (~$5, ~3h)
  - Only if reviewer demands full-bench latency (current paper discloses 30-case smoke)
  - Origin: Session 22 audit CRIT-B3 (mitigated via disclosure)

- [ ] **Item-Def-2: Path D — Phase 4.5c cold-start curve** (~$5, ~5h)
  - Only if reviewer demands cold-start data
  - D-17 patched on laptop; instance needs scp `src/memory/neo4j_client.py` first
  - Origin: Session 19 PATH 4 lock

- [ ] **Item-Def-3: Brittlebench + C3AI bib additions** (Audit M-2)
  - 2 of 12 expected new bib entries missing
  - Judged intentional drops per page budget (session 24)
  - Add only if reviewer flags

- [ ] **Item-Def-4: CV 5th agent** (D-10)
  - Marked superseded by CV1+CV2 + session 16 audit work (locked s17 "no need for this i guess anymore")
  - Multi-agent session-22 + session-27/28 audits supersede further

---

## Origin-session quick-reference

| Item range | Origin session | Status notes |
|---|---|---|
| Items 1-3 | Session 27 Stage 1b §9 | KNOWN_BIB_ERROR confirmed by Stage 1c |
| Items 4-11 | Session 28 Stage 1c §3 | NEW_BIB_ERROR (8 entries beyond Stage 1b's 4) |
| Item 12 | Session 27 Stage 1b retry-2 | notaro real DOI unconfirmed |
| Item 13 | Session 27 Stage 1b §13 | chen2024autonomous placeholder |
| Items 14-15 | Session 27 close (pending USER GO) | Gate 16 + Gate 17 |
| Items 16-19 | Session 28 verification plan | Stages 2/3/4/5/6 sequencing per `misty-knitting-pine.md` |
| Item 20 | Post-Stage-6 (session 28+ edit-phase) | Phased commits |
| Items A-E | Sessions 22/24/25/27 mix | Important but not blocking |
| Items N1-N5 | Sessions 24-27 deferrals | Reviewer-flag-only |
| Items Def-1-4 | Sessions 17-22 deferrals | Out-of-scope unless demanded |

---

## CRITICAL totals at a glance

- **9 Stage-1b bib metadata corrections** across 4 entries (Items 1-3 + Item 12)
- **8 Stage-1c NEW bib metadata corrections** across 8 entries (Items 4-11)
- **1 placeholder cite** decision required (Item 13)
- **2 commits + 1 push** pending USER GO (Items 14-15)
- **5 verification stages** remaining in session 28 (Items 16-19)
- **1 edit-phase** post-synthesis (Item 20)

**Total CRITICAL items**: 20

---

*End of checklist. Cross-link companion: `05_audit_history_timeline.md`.*
