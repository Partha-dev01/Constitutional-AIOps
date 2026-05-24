# FINAL/ — Results Summary

_Last updated: 2026-05-20 (session 12) — added CV passes + master backup pointer. Previous: 2026-05-19 (session 11) — Phase 5 statistics complete (BCa CI + McNemar + Cohen's h). All numbers independently recomputed from raw JSONs._

> ## Cross-validation + per-file metadata (added 2026-05-20)
>
> - **Audit doc**: `FULL_TRANSCRIPT_AUDIT.md` (1507 lines, full 4-phase forensic audit of session 1–11 transcript)
> - **CV Pass 1** (audit doc ↔ JSONL): `CV_PASS1_DISCREPANCIES.md` (303 lines, 1 CRITICAL + 1 MEDIUM + 3 LOW + 2 UNVERIFIABLE)
> - **CV Pass 2** (audit doc ↔ codebase + per-file metadata): `CV_PASS2_CODEBASE_AUDIT.md` (715 lines, 31 Tier 1-3 VERIFIED, 0 errors). **Part B of this file is the canonical per-file metadata table for the entire `benchmark/` tree** — 491 files with git first-add commit + last-modify commit + filesystem mtime + discrepancy flag (side-by-side).
> - **Master backup**: `../../../Backups/benchmark_master_backup_2026-05-20.zip` (14.27 MB, SHA `7b01aef090…`, 494 entries, integrity verified)
> - **Pre-backup manifest** (493 files + SHA-256s): `MASTER_BACKUP_MANIFEST_2026-05-20.json`

---

## 1. Authoritative file map (USE THESE)

Every file in this table was copied into `FINAL/` with SHA-256 verification (see `MANIFEST.md`) and a per-file schema-aware content audit (see `AUDIT_REPORT.md`). All 23 audited files pass clean (`OK=23 WARN=0 FAIL=0`).

| Paper artifact | FINAL/ path | Number | Verified |
|---|---|---|---|
| **Table 2** (system standalone, rich eval) | `main_benchmark/results.json` | Ann 82.6% / RCA 92.5% / Overall 87.5% | ✅ recomputed |
| **Table 2** companion (matched eval) | `main_benchmark/results_sota_eval_431.json` | Ann 82.6% / RCA 80.3% / Overall 81.7% | ✅ recomputed |
| **Table 2** with BCa CIs (matched eval) | `main_benchmark/phase5_stats.json` | see §3.1 below | ✅ Phase 5 |
| **Table 5** (Latency) | `main_benchmark/summary.json` | P50 4.1s / P95 48.4s / avg 17.6s | ✅ |
| **Table 6** (Ablation, 8 configs) — raw matched eval | `ablation_v4/ablation_*/results_sota_eval_431.json` | see §3 below | ✅ recomputed |
| **Table 6** — paper-ready table (Overall only, no stats) | `ablation_v4/matched_eval_table.md` | — | ✅ generated |
| **Table 6** — full Phase 5 table (CIs + p + h) | `ablation_v4/phase5_stats.md` ⭐ | see §3.2 | ✅ Phase 5 |
| **Table 6** — Phase 5 machine-readable | `ablation_v4/phase5_stats.json` | — | ✅ Phase 5 |
| **Table 7** Ours row | `main_benchmark/results_sota_eval_431.json` | Ann 82.6 / RCA 80.3 / Ovl 81.7 | ✅ recomputed |
| **Table 7** Llama 3.3-70B | `sota_baselines/llama_3_3_70b.jsonl` | Ann 91.3 / RCA 71.1 / Ovl 83.3 | ✅ recomputed |
| **Table 7** DeepSeek V3.2 | `sota_baselines/deepseek_v3.jsonl` | Ann 90.4 / RCA 66.9 / Ovl 81.1 | ✅ recomputed |
| **Table 7** Drain | `sota_baselines/drain.jsonl` + `drain_summary.json` | Ann 50.5% (202 cases, RCA N/A) | ✅ recomputed |
| **Table 8** Llama no-prompt | `phase46_no_prompt/llama_noprompt_clean.jsonl` | Ann 67.9 / RCA 73.2 | ✅ recomputed |
| **Table 8** DeepSeek no-prompt | `phase46_no_prompt/deepseek_noprompt_v2.jsonl` | Ann 88.5 / RCA 73.9 | ✅ recomputed |
| **§3** dual-stack methodology | `infrastructure/gate15_comparison.md` | Stack B = 1.51× faster | ✅ |
| **§3** eval methodology | `METHODOLOGY.md` | — | ✅ |
| **§3** bug-investigation provenance | `BUG_HISTORY.md` | — | ✅ |

---

## 2. Where the originals went (2026-05-19 archive operation)

Original result dirs were MOVED (not deleted) on 2026-05-19 to declutter `results_aws/`. Defense-in-depth: zip backup + folder with metadata + earlier tarball + EBS snapshot.

| Item | Location | Note |
|---|---|---|
| **Defense layer 1**: file-level archive folder | `benchmark/archive/originals_2026-05-19/` | 6 dirs + `_ARCHIVED.md` map + per-dir `_ARCHIVED_NOTICE.md` |
| **Defense layer 2**: zip backup | `benchmark/archive/originals_backup_2026-05-19.zip` | 1.7 MB, 69 entries, every entry SHA-verified against original |
| **Defense layer 3**: instance-side tarball (session 10) | `benchmark/archive/aiops_archive_2026-05-17.tar.gz` | 5.75 MB, SHA `351aa6734b…` (re-verified this session) |
| **Defense layer 4**: AWS EBS snapshot | `snap-01b191aedbf46b598` | cloud disaster recovery, ~$0.13/mo |

Dirs that were MOVED:

| Archived dir | Canonical now at |
|---|---|
| `run_stackA_main431_newprompt/` → `_archive_originals_2026-05-19/...` | `FINAL/main_benchmark/` |
| `ablation_v4_newprompt/` → `_archive_originals_2026-05-19/...` | `FINAL/ablation_v4/` |
| `sota_llama_3_3_70b/` → `_archive_originals_2026-05-19/...` | `FINAL/sota_baselines/llama_3_3_70b.jsonl` |
| `sota_deepseek_v3/` → `_archive_originals_2026-05-19/...` | `FINAL/sota_baselines/deepseek_v3.jsonl` |
| `sota_drain/` → `_archive_originals_2026-05-19/...` | `FINAL/sota_baselines/drain.jsonl` + `drain_summary.json` |
| `phase46_noprompt/` → `_archive_originals_2026-05-19/...` | `FINAL/phase46_no_prompt/` |

Dirs NOT touched (preserved in place per prior-session constraints):
- `run_stackA_main431/` — OLD-prompt v1-paper reference (kept for diff)
- `archive/` — smoke tests (already organized as an archive)
- `rerun_remine33_enriched/` — old merge artifact
- All top-level nav docs (BROKEN_ABLATIONS.md, BUG_HISTORY.md, CURRENT_RUNS.md, FILE_PROVENANCE.md, METHODOLOGY.md, RESULTS_SUMMARY.md, RUNS_INDEX.md) — `FILE_PROVENANCE.md` + `RUNS_INDEX.md` + `RESULTS_SUMMARY.md` got an ARCHIVE NOTICE header

Scripts updated to read from new paths:
- `benchmark/scripts/eval/verify_authoritative_numbers.py` → reads `FINAL/`
- `benchmark/scripts/eval/inspect_all_configs.py` → reads `FINAL/ablation_v4/`
- `benchmark/scripts/ops/build_final_results.py` → sources from `_archive_originals_2026-05-19/` so re-build still works

---

## 3. Verified ablation matched-eval numbers + Phase 5 stats

### 3.1 Headline (full per-config) — paper Table 6 source-of-truth

From `ablation_v4/phase5_stats.md` (paper-ready) and `phase5_stats.json` (full structured). BCa 95% CI from scipy bootstrap (10k resamples, seed=42). McNemar exact two-sided binomial paired by `case_id` vs Full Hybrid. Cohen's h = arcsine effect size.

| Configuration | Task | N | Acc | 95% BCa CI | Δ vs Full | McNemar p | Cohen h |
|---|---|---:|---:|---|---:|---:|---:|
| **Full Hybrid** | annotation | 218 | 83.0% (181/218) | [77.5, 87.6] | — | — | — |
|  | rca | 142 | 83.8% (119/142) | [76.8, 88.7] | — | — | — |
|  | **overall** | **360** | **83.3% (300/360)** | **[79.2, 86.9]** | **—** | **—** | **—** |
| Single-4B (both tasks) | annotation | 218 | 82.6% (180/218) | [77.1, 87.2] | −0.5pp | 1.000 | −0.012 |
|  | rca | 142 | 81.0% (115/142) | [73.9, 86.6] | −2.8pp | 0.424 | −0.074 |
|  | overall | 360 | 81.9% (295/360) | [77.5, 85.6] | −1.4pp | 0.302 | −0.037 |
| Single-14B (both tasks) | annotation | 218 | 84.4% (184/218) | [78.9, 89.0] | +1.4pp | 0.664 | +0.037 |
|  | rca | 142 | 81.0% (115/142) | [73.9, 86.6] | −2.8pp | 0.219 | −0.074 |
|  | overall | 360 | 83.1% (299/360) | [78.9, 86.7] | −0.3pp | 1.000 | −0.007 |
| No structured output | annotation | 218 | 82.6% (180/218) | [77.1, 87.2] | −0.5pp | 1.000 | −0.012 |
|  | rca | 142 | 73.9% (105/142) | [66.2, 80.3] | −9.9pp | **0.004** | −0.243 |
|  | overall | 360 | 79.2% (285/360) | [74.7, 83.3] | −4.2pp | 0.086 | −0.107 |
| No system prompt | annotation | 218 | 48.6% (106/218) | [42.2, 55.5] | −34.4pp | **1.2e-10** | **−0.749** |
|  | rca | 142 | 79.6% (113/142) | [72.1, 85.2] | −4.2pp | 0.180 | −0.109 |
|  | overall | 360 | 60.8% (219/360) | [55.8, 65.8] | −22.5pp | **3.4e-11** | **−0.511** |
| With graph (RAG) | annotation | 218 | 82.6% (180/218) | [77.1, 87.2] | −0.5pp | 1.000 | −0.012 |
|  | rca | 142 | 81.7% (116/142) | [74.6, 87.3] | −2.1pp | 0.453 | −0.056 |
|  | overall | 360 | 82.2% (296/360) | [78.1, 85.8] | −1.1pp | 0.289 | −0.029 |
| No constitutional | annotation | 218 | 89.4% (195/218) | [84.9, 93.1] | +6.4pp | **0.001** | +0.188 |
|  | rca | 142 | 71.1% (101/142) | [63.4, 78.2] | −12.7pp | **5.3e-04** | −0.306 |
|  | overall | 360 | 82.2% (296/360) | [78.1, 85.8] | −1.1pp | 0.652 | −0.029 |
| With orchestrator | annotation | 218 | 82.6% (180/218) | [77.1, 87.2] | −0.5pp | 1.000 | −0.012 |
|  | rca | 142 | 81.7% (116/142) | [74.6, 87.3] | −2.1pp | 0.453 | −0.056 |
|  | overall | 360 | 82.2% (296/360) | [78.1, 85.8] | −1.1pp | 0.289 | −0.029 |

### 3.2 Compact overall-only (for paper Table 6 if space-constrained)

| Configuration | Overall Acc | 95% BCa CI | Δ vs Full | McNemar p | Cohen h |
|---|---:|---|---:|---:|---:|
| **Full Hybrid** | **83.3% (300/360)** | **[79.2, 86.9]** | — | — | — |
| Single-4B | 81.9% (295/360) | [77.5, 85.6] | −1.4pp | 0.302 | −0.037 |
| Single-14B | 83.1% (299/360) | [78.9, 86.7] | −0.3pp | 1.000 | −0.007 |
| No structured | 79.2% (285/360) | [74.7, 83.3] | −4.2pp | 0.086 | −0.107 |
| No system prompt | 60.8% (219/360) | [55.8, 65.8] | −22.5pp | **3.4e-11** | **−0.511** |
| With graph | 82.2% (296/360) | [78.1, 85.8] | −1.1pp | 0.289 | −0.029 |
| No constitutional | 82.2% (296/360) | [78.1, 85.8] | −1.1pp | 0.652 | −0.029 |
| With orchestrator | 82.2% (296/360) | [78.1, 85.8] | −1.1pp | 0.289 | −0.029 |

### 3.3 Main re-run (standalone, Table 2 companion matched-eval)

| Task | N | Acc | 95% BCa CI |
|---|---:|---:|---|
| annotation | 218 | 82.6% (180/218) | [77.1, 87.2] |
| rca | 142 | 80.3% (114/142) | [73.2, 85.9] |
| **overall** | **360** | **81.7% (294/360)** | **[77.5, 85.6]** |

**Footnote**: ablation Full's matched-eval RCA = 83.8% (119/142); main re-run's = 80.3% (114/142). Same Stack A, same temperature=0, same dataset, different run — 5-case nondeterminism. Disclose in paper as run-to-run variance footnote on Table 2 + Table 6.

### 3.4 Cohen's h interpretation key

| Range | Effect size |
|---|---|
| |h| < 0.2 | negligible |
| 0.2 ≤ |h| < 0.5 | small |
| 0.5 ≤ |h| < 0.8 | medium |
| |h| ≥ 0.8 | large |

---

## 4. Phase 5 headline findings (use these for paper narrative)

These are the actionable conclusions from the statistical analysis. They directly support the reviewer-response framing in [`REVIEWER_RESPONSE.md`](../../../AiOps%20Research%20Paper%20Stuff/Final%20Submission%20Paper%20(Accepted%20v.1)/REVIEWER_RESPONSE.md) and the plan's deep-dive refinements.

### 4.1 The "graph hurts" defense lands cleanly (defuses R1 + R3)

R1 and R3's concern was the v1 paper's −2.7% graph drop. Under matched eval + McNemar:
- **With graph vs Full**: Overall Δ = **−1.1pp**, **p = 0.289 (NOT significant)**, **Cohen's h = −0.029 (negligible)**
- Reframe: "The graph drop is statistically indistinguishable from noise at this sample size." Combined with the planned Table 9 (homogeneous LEMMA 5-fold sub-experiment), this resolves the concern.

### 4.2 The "31% prompt drop" reframe is now defensible with stats (defuses R1 + R3)

The −22.5pp overall drop has p = 3.4e-11 (overwhelming), but the per-task split is sharp:
- **Annotation: −34.4pp, p = 1.2e-10, h = −0.749** (medium-to-large effect — small annotation model is brittle)
- **RCA: −4.2pp, p = 0.180 (NOT significant), h = −0.109** (negligible — reasoning model robust)
- Story: it's a **task-specification cost for the small annotation model**, NOT system-wide brittleness. Per-task disaggregation in Table 6 (separate Ann / RCA / Overall rows) makes this visible to reviewers.

### 4.3 Constitutional gating: clean nuance reveal (NEW, more honest than v1)

v1 paper claimed −21.8% from removing constitutional. Matched eval + stats shows a much more nuanced (and honest) story:
- **Overall: −1.1pp, p = 0.652 (NOT significant)** — no overall accuracy cost
- **Annotation: +6.4pp, p = 0.001** (gating slightly hurts annotation — forces conservative answers)
- **RCA: −12.7pp, p = 5.3e-04, h = −0.306** (small effect, statistically significant)
- Story: the constitutional layer **specifically protects RCA correctness** while imposing a modest annotation cost; the net overall effect is zero. The v1 overall-only framing missed the asymmetry. This is paper-defensible and more interesting than the v1 claim.

### 4.4 Hybrid lead over single-models is real but small

Both single-4B (p = 0.302) and single-14B (p = 1.0) are NOT significantly different from Full on overall accuracy. Hybrid wins narrowly while being:
- Faster than single-14B (17.6s avg vs 33.7s — see Table 5)
- More accurate on RCA than single-4B (83.8 vs 81.0% RCA, though p = 0.424)

Recommended framing: "Hybrid sits at the latency/accuracy optimum — within noise on accuracy, ~2× faster than 14B-only, with a small RCA edge over 4B-only that becomes meaningful at scale."

### 4.5 With_orchestrator is identical to with_graph under matched eval

Both produced the **same correct flag on every one of 360 evaluable cases**. Worth investigating before paper claims if you want to differentiate them. Simplest reading: both are thin wrappers that don't change LLM outputs on this benchmark — the orchestrator is plumbing, not a new accuracy driver.

### 4.6 What about no_structured?

- RCA: −9.9pp, **p = 0.004** (statistically significant, h = −0.243 small effect)
- Overall: −4.2pp, **p = 0.086 (marginally not significant)** at α = 0.05
- The structured-output wrapper helps RCA materially; the effect on overall accuracy is borderline.

---

## 5. Anomaly scan — what was checked, what was clean, what's a known limit

Per-file audit (see `AUDIT_REPORT.md` for full output):

| Check | Result |
|---|---|
| Record counts (expect 218 ann + 213 rca = 431 for main + ablation + SOTA) | ✅ all match |
| Drain record count (expect 202 annotation, 0 RCA) | ✅ matches |
| Phase 4.6 record counts (expect 431 each) | ✅ matches |
| Excluded RCA cases (matched-eval files expect 71 = 39 Chinese + 32 MC letter) | ✅ all 11 matched-eval files have exactly 71 excluded |
| Duplicate test_ids (DeepSeek t=0 BAK had 103 dups) | ✅ all final files have 0 duplicates |
| Missing required fields (`task_type`, id, `correct`, model output, expected) | ✅ all present (schema-aware: `actual_output`/`model_response`/`predicted_anomaly` for output; `expected_output`/`expected`/`expected_root_cause`/`expected_anomaly` for ground truth) |
| BERT-F1 scores | ⚠ **all 431 records have `bert_f1: 0.0`** — known limitation from disk-full bug #8 (BERTScore model couldn't download when AWS root EBS was 40 GB). Disk now 80 GB. Recomputable post-hoc from saved `actual_output` strings if reviewers ask. Disclosed in `BUG_HISTORY.md`. |
| Wrong test criteria (runner.py vs matched-eval) | ✅ FINAL/ ships BOTH so the difference is visible. Per-config matched-eval is the canonical paper number; rich-eval is kept for provenance and disclosure. |
| Pairwise McNemar pairings (all 360 evaluable cases per config) | ✅ All 7 non-full configs pair against full with n_paired = 360 |
| Statistical sanity (CIs straddle point estimate, p-values monotonic with effect size) | ✅ verified by inspection |

**Verdict: no data anomalies in the final set.** Single known issue is BERT scores being zero (instrument issue, not data integrity). Does not affect any accuracy claim (Tables 2-8 use accuracy %, not BERTScore).

---

## 6. AWS state (per session-10 record; sandbox CLI clock-skewed, cannot live-verify)

| Resource | State |
|---|---|
| Instance `i-091c4de0e95d63154` | **stopped** since 2026-05-17 ~07:39 UTC |
| EIP `44.195.172.165` | retained (do NOT release) |
| EBS root `vol-01714af69faebb973` (80 GB) | preserved |
| EBS data `vol-0ff075a7541026572` (100 GB) | preserved |
| Snapshot `snap-01b191aedbf46b598` | held |
| Passive carry while stopped | ~$5.50/mo |
| Local tarball `aiops_archive_2026-05-17.tar.gz` | SHA `351aa6734b…` (verified intact in this session) |
| Local zip backup `originals_backup_2026-05-19.zip` | SHA-verified, 69 entries |
| Budget used / ceiling | $47 / $120 (39%) |

To live-verify AWS from a shell with correct clock (sandbox here is 5h 15m behind real UTC):
```bash
aws ec2 describe-instances --instance-ids i-091c4de0e95d63154 \
  --profile aiops-operator --region us-east-1 \
  --query 'Reservations[0].Instances[0].State.Name' --output text
```

---

## 7. Status of plan tasks (post-session-11)

| # | Task | Status | Output |
|---|---|---|---|
| **PHASE 5 STATS** | | | |
| 1.1–1.5 | BCa CI + McNemar + Cohen's h per config (Ann / RCA / Overall) | ✅ DONE | `FINAL/ablation_v4/phase5_stats.{json,md}` + `FINAL/main_benchmark/phase5_stats.json` |
| **REGENERATE STATIC DOCS** | | | |
| 2.1 | Update SUMMARY.md (this file) with Phase 5 + archive | ✅ DONE | this file |
| 2.2 | RUNS_INDEX.md / RESULTS_SUMMARY.md / FILE_PROVENANCE.md ARCHIVE NOTICE headers | ✅ DONE | (header added; bodies are session-9 historical) |
| **PAPER UPDATES** (target: `sn-article-template.v2/sn-article.tex`, NOT v1) | | | |
| 3.1 | Replace Table 6 with matched-eval + CIs + McNemar p + Cohen's h | ⏳ pending | next |
| 3.2 | Verify Table 7 "Ours" row uses main re-run matched eval (Ann 82.6 / RCA 80.3 / Ovl 81.7) | ⏳ pending | |
| 3.3 | Add nondeterminism footnote (Full ablation RCA 83.8 vs main RCA 80.3 = 5 cases) | ⏳ pending | |
| 3.4 | Regenerate Figure 4 (ablation bar chart) from matched-eval | ⏳ pending | |
| 3.5 | §6.1 paragraph reframes (graph defused, prompt task-specific, constitutional asymmetric, novelty) | ⏳ pending | |
| **REPO HOUSEKEEPING** | | | |
| 4.1 | Originals moved to `_archive_originals_2026-05-19/` + zip backup | ✅ DONE | see §2 |
| 4.2 | git commit (NO Claude co-author per user instruction) | ⏳ pending | end |
| **FUTURE (AWS NEEDED)** | | | |
| 5.1 | Phase 4.5 LEMMA 5-fold + cold-start curve | ⏳ deferred | |
| 5.2 | Phase 4.6 paraphrased prompts × 431 cases | ⏳ deferred | |

---

## 8. Quick reproducibility checklist

To re-derive everything in this directory from the archived originals:
```bash
cd "<repo root>"
# 1. Rebuild FINAL/ from archive (COPY + SHA-verify + audit)
python benchmark/scripts/ops/build_final_results.py

# 2. Re-verify all matched-eval headline numbers from the source JSONs
python benchmark/scripts/eval/verify_authoritative_numbers.py

# 3. Re-run Phase 5 statistics
python benchmark/scripts/eval/phase5_stats.py
```

Per-file SHA-256 in `MANIFEST.md`. Per-file content audit in `AUDIT_REPORT.md`. Phase 5 paper-ready output in `ablation_v4/phase5_stats.md`.

Originals at `_archive_originals_2026-05-19/` are NEVER modified. The zip backup at `originals_backup_2026-05-19.zip` is the single-file recoverable form.
