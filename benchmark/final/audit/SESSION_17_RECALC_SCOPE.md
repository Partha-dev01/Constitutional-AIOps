# Session 17 — Complete Recalculation Scope (D-1 Re-Label + D-6 BERT)

> Generated 2026-05-25 during audit triage. Companion to `SESSION_17_AUDIT_TRIAGE.md`. Enumerates every file, every test, every number that needs recomputation as a result of the **D-1 Option B (re-label all 33 OpsEval-remined cases as `qa_mcq`)** + **D-6 Option B (BERT-F1 recompute)** decisions.
>
> **All recalculation is LOCAL (no AWS re-run needed).** The 33 cases are model-output-stable (we have all saved predictions); we just change how they're counted.

---

## §1. Why this recalculation

The 33 `opseval_remine_*` cases (RCA_OPSEVAL_RM_001..033, 32 from Wired Network + 1 from Mobile Communication) are 100% MCQ-style knowledge-recall questions (CompTIA-style "A. X / B. Y / C. Z"), not diagnostic RCA scenarios.

They were over-included into the benchmark because the Stage 2 LLM judge — supposed to be Claude Haiku 4.5 via AWS Bedrock — silently fell back to local Qwen3-4B-Instruct after Bedrock model-access was payment-blocked (D-1 + D-3 root cause). The 4B fallback judge was too lenient and classified all 33 MCQs as DIAGNOSTIC.

Of the 33:
- **30 are already excluded** at evaluation time (`eval_method=None, correct=None`) — they were caught by a separate post-hoc filter
- **3 (RM_016, RM_022, RM_032) are still in the 142-evaluable RCA pool** — they got through because the model's freeform output happened to substring-match one of the MCQ option strings (all 3 are `correct=False` in our main run and ablation, but Llama+DeepSeek SOTA scored 2 of 3 as `correct=True`)

**Decision (locked 2026-05-25)**: re-label all 33 as `task_type: "qa_mcq"`. Re-compute Phase 5 stats locally (no AWS). Update SUMMARY/MANIFEST/METHODOLOGY/sandbox paper.

---

## §2. Result files needing `task_type` edit

| # | File | Records | What changes |
|---|---|---:|---|
| 1 | `benchmark/intermediate/datasets/benchmark_431_seed42.json` | 431 | 33 cases: `task_type: "rca"` → `"qa_mcq"` + add `excluded_reason: "MCQ knowledge format (post-hoc audit 2026-05-25); originally judged DIAGNOSTIC by Qwen3-4B-Instruct fallback judge"` |
| 2 | `benchmark/final/main_benchmark/results_sota_eval_431.json` | 431 | 3 cases (RM_016, 022, 032): same edit |
| 3 | `benchmark/final/main_benchmark/results.json` (rich eval) | 431 | 3 cases: same edit |
| 4 | `benchmark/final/ablation_v4/ablation_full/results_sota_eval_431.json` | 431 | 3 cases: same edit |
| 5 | `benchmark/final/ablation_v4/ablation_single_4b/results_sota_eval_431.json` | 431 | 3 cases |
| 6 | `benchmark/final/ablation_v4/ablation_single_14b/results_sota_eval_431.json` | 431 | 3 cases |
| 7 | `benchmark/final/ablation_v4/ablation_no_structured/results_sota_eval_431.json` | 431 | 3 cases |
| 8 | `benchmark/final/ablation_v4/ablation_no_system_prompt/results_sota_eval_431.json` | 431 | 3 cases |
| 9 | `benchmark/final/ablation_v4/ablation_with_graph/results_sota_eval_431.json` | 431 | 3 cases |
| 10 | `benchmark/final/ablation_v4/ablation_no_constitutional/results_sota_eval_431.json` | 431 | 3 cases |
| 11 | `benchmark/final/ablation_v4/ablation_with_orchestrator/results_sota_eval_431.json` | 431 | 3 cases |
| 12 | `benchmark/final/sota_baselines/llama_3_3_70b.jsonl` | 431 | **33 cases** (no `eval_method` field — all 33 are currently counted as RCA) |
| 13 | `benchmark/final/sota_baselines/deepseek_v3.jsonl` | 431 | **33 cases** |
| 14 | `benchmark/final/sota_baselines/drain.jsonl` | 202 | None (annotation-only, no remined cases) |
| 15 | `benchmark/final/phase46_no_prompt/llama_noprompt_clean.jsonl` | 431 | **33 cases** |
| 16 | `benchmark/final/phase46_no_prompt/deepseek_noprompt_v2.jsonl` | 431 | **33 cases** |

**Total file edits**: 16 files. Some files only need 3 records edited, others need 33.

---

## §3. Headline numbers that shift (Tables 2 / 6a / 6b / 7)

### §3.1 Table 2 — Main Re-Run (Overall)

| Metric | Before | After re-label | Δ |
|---|---|---|---:|
| Annotation | 82.6% (180/218) | 82.6% (180/218) | — (annotation unaffected) |
| **RCA** | 80.3% (114/142) | **82.0% (114/139)** | **+1.7pp** |
| **Overall** | 81.7% (294/360) | **82.4% (294/357)** | **+0.7pp** |

### §3.2 Table 6a + 6b — Ablation (RCA column shifts every config)

Each config's RCA % goes up because denominator shrinks 142→139 while numerator (correct count) stays the same (all 3 affected cases were `correct=False` in every Constitutional AIOps config).

| Config | RCA Before | RCA After | Δ |
|---|---|---|---:|
| Full Hybrid | 83.8% (119/142) | **85.6% (119/139)** | +1.81pp |
| Single-4B | 81.0% (115/142) | **82.7% (115/139)** | +1.75pp |
| Single-14B | 81.0% (115/142) | **82.7% (115/139)** | +1.75pp |
| No structured output | 73.9% (105/142) | **75.5% (105/139)** | +1.60pp |
| No system prompt | 79.6% (113/142) | **81.3% (113/139)** | +1.72pp |
| With graph (RAG) | 81.7% (116/142) | **83.5% (116/139)** | +1.76pp |
| No constitutional | 71.1% (101/142) | **72.7% (101/139)** | +1.54pp |
| With orchestrator | 81.7% (116/142) | **83.5% (116/139)** | +1.76pp |

**Annotation columns unaffected** (no remined cases are annotation task_type).

**Overall accuracy shifts** by ~+0.6-0.7pp per config (denominator 360→357, numerator unchanged).

### §3.3 Table 7 — SOTA Baselines

For SOTA baselines, the 3 cases (RM_016, RM_022, RM_032) had `correct=True/True/False` for Llama and DeepSeek (different from Constitutional AIOps, which got all 3 wrong). Removing them changes both numerator and denominator:

| System | RCA Before | RCA After (estimated) | Notes |
|---|---|---|---|
| Constitutional AIOps (ours) | 80.3% (114/142) | **82.0% (114/139)** | +1.7pp (3 cases all wrong, removed clean) |
| Llama 3.3-70B | 71.1% (101/142) | **~71.2% (99/139)** | 3 cases removed: 2 were correct, 1 wrong → -2 numerator, -3 denominator |
| DeepSeek V3.2 | 66.9% (95/142) | **~66.9% (93/139)** | Similar: 2 correct + 1 wrong removed |

**ΔRCA values shift FAVORABLY for our system**:
- vs Llama: was +9.2pp → becomes **~+10.8pp**
- vs DeepSeek: was +13.4pp → becomes **~+15.1pp**

→ The "hybrid wins RCA against frontier monoliths" story strengthens.

### §3.4 Table 7 — Annotation row (unchanged)

| System | Ann Before | Ann After |
|---|---|---|
| Constitutional AIOps | 82.6% (180/218) | 82.6% (180/218) |
| Llama 3.3-70B | 91.3% (199/218) | 91.3% (199/218) |
| DeepSeek V3.2 | 90.4% (197/218) | 90.4% (197/218) |
| Drain | 50.5% (102/202) | 50.5% (102/202) |

### §3.5 BCa CIs, McNemar p-values, Cohen's h

Re-running `phase5_stats.py` against the modified result files will produce:
- New BCa 95% CIs (BCa shrinks slightly with N=139 vs 142, but still bootstrap with 10k resamples + seed=42)
- New McNemar paired p-values (paired by case_id — the same 3 cases removed from both arms of each comparison; magnitudes shift but qualitative findings stay the same)
- New Cohen's h effect sizes (same direction, slightly different magnitudes)

**Headline qualitative findings stay**:
- Graph (RAG): Δ still ~−1pp on Overall, p still NS (defused)
- No system prompt: Ann −34pp p=tiny stays; RCA −4pp p=NS stays (task-asymmetric)
- No constitutional: RCA −12pp p<0.001 stays; Ann +6pp p<0.01 stays (asymmetric)
- Single-4B / single-14B: still indistinguishable from Full Hybrid on Overall
- All directional conclusions in `phase5_stats.md §4` stand

---

## §4. Files to regenerate

### §4.1 Stats files (script-generated)

| File | Regenerator | What changes |
|---|---|---|
| `benchmark/final/main_benchmark/phase5_stats.json` | `benchmark/scripts/eval/phase5_stats.py` | Main BCa CI for RCA + Overall |
| `benchmark/final/ablation_v4/phase5_stats.md` | `benchmark/scripts/eval/phase5_stats.py` | Paper-ready table (full per-task + compact overall) |
| `benchmark/final/ablation_v4/phase5_stats.json` | `benchmark/scripts/eval/phase5_stats.py` | Machine-readable Phase 5 |
| `benchmark/final/ablation_v4/matched_eval_table.md` | `benchmark/scripts/eval/inspect_all_configs.py` (or build helper) | Overall-only compact table |

### §4.2 Documentation files (hand-edit)

| File | What changes |
|---|---|
| `benchmark/final/SUMMARY.md` | §1 file map shows new Ann/RCA/Overall; §3.1 paper Table 6 source updated; §3.3 main re-run table updated; §4 narrative findings refreshed; §1 footnote about D-1 re-label; §6 cost-source note (D-5); §3 BERT recompute note (D-6) |
| `benchmark/final/MANIFEST.md` | SHA-256 for every modified file (16 files); add new SHAs for phase5_stats.* and recalc-supporting scripts |
| `benchmark/final/docs/METHODOLOGY.md` | §2 exclusion section: correct breakdown (was 39 Chinese + 32 MC; actual is **41 Chinese + 30 MCQ-pre-relabel = 71** → post-relabel becomes **41 Chinese + 33 MCQ = 74 excluded, leaving 213-74 = 139 evaluable**); add D-1 disclosure paragraph (judge fallback + post-hoc re-label) |
| `benchmark/final/docs/BUG_HISTORY.md` | Add D-4 L5307 footnote (fake-graph-context commit invalidated archived smoke results) |
| `benchmark/final/AUDIT_REPORT.md` | Re-run `audit_results.py` to verify new record counts (218 ann + 213 rca = 431 split into 33 qa_mcq + 180 rca total → 218 ann + 180 rca = 398 task_type rca/ann + 33 qa_mcq) |

### §4.3 Sandbox paper files (sandbox path = `sn-article-template.v2.sandbox-session16/`)

| File | What changes |
|---|---|
| `sn-article.tex` Table 2 (Overall) | New Ann/RCA/Overall numbers + add **B-4 variance footnote** ("5-case temp=0 nondeterminism between runs") |
| `sn-article.tex` Table 6a (architecture variants) | New RCA column + CIs + p + h for full/single-4B/single-14B |
| `sn-article.tex` Table 6b (component ablations) | Same for no-structured / no-prompt / with-graph / no-constitutional / with-orchestrator |
| `sn-article.tex` Table 7 (SOTA Baselines) | New Ours/Llama/DeepSeek numbers + ΔRCA values |
| `sn-article.tex` §5.1.1 Statistical Methodology | Update BCa CI / McNemar / Cohen's h numbers throughout (any inline number citations) |
| `sn-article.tex` §5.2 Main Results prose | Update headline number (was 81.7%, becomes 82.4%); update CI |
| `sn-article.tex` §5.7 SOTA Baselines prose | Update ΔRCA citations + add **D-3 launch-date 1-sentence** ("DeepSeek V3.2 and Llama 3.3-70B are used as closed-source and open-weight frontier baselines from the 2024-2025 release window.") |
| `sn-article.tex` §5.3 Per-Source OR §6.2 Limitations | Add **D-2 OpenSSH 1-sentence caveat** ("On OpenSSH, all 20 errors are false positives over-flagging single failed-login events; zero false negatives on the 20 brute-force attacks; conservative bias may be desirable in production triage.") |
| `sn-article.tex` §6.2 Limitations | Add **Conflict-4 calibration sentence** ("The confidence weight coefficients (α=0.4, β=0.35, γ=0.25) were chosen heuristically; empirical calibration on a held-out tuning set is left for future work.") |
| `sn-article.tex` §4 Experimentation | Add **D-1 1-sentence caveat** ("71 RCA candidates were excluded at evaluation time (41 Chinese-language plus 30 MCQ-format cases mis-classified during curation), yielding 139 evaluable RCA cases.") |
| `sn-article.tex` §7 Conclusion | Update headline numbers if any cited (was 81.7%, becomes 82.4%) |
| Recompile | `pdflatex` ×2 + verify ≤ 16 pages |

---

## §5. D-6 BERT-F1 Recompute (separate ~3h local job)

After D-1 work above, the BERT-F1 recompute runs against the now-correctly-labeled result files.

### §5.1 Setup

```bash
pip install bert-score
# First run downloads bert-base-uncased (~440 MB), cached to ~/.cache/huggingface
```

### §5.2 Recompute script (`benchmark/scripts/eval/recompute_bert_f1.py`)

For each of ~3000 records across all result files:
- Read `actual_output` / `model_response` and `expected` strings
- Compute BERTScore F1 (uses bert-base-uncased by default; deterministic)
- Update the record's `bert_f1` field in place

### §5.3 Files updated

All 16 result files (§2 above) plus aggregate summaries in:
- `benchmark/final/SUMMARY.md` — add BERT-F1 averages per config
- `benchmark/final/ablation_v4/phase5_stats.md` — add BERT-F1 column to Tables 3.1 + 3.2

### §5.4 Paper update (D-6 Option B preferred)

- Add BERT-F1 column to sandbox Tables 2 + 3
- Decision gate: if PDF > 16 pages after adding column → fall back to **Option C** (1 sentence in §5 mentioning average instead of column)

### §5.5 Estimated runtime

- ~3 hours on laptop CPU (or ~30 min on GPU if Torch/CUDA available)
- Can run in background while doing other tasks
- Output: per-record `bert_f1` field populated for the first time since the 2026-05-13 disk-full bug #8

---

## §6. Execution sequence (next session)

Sequenced for safety — verify after each phase before proceeding:

| Phase | Step | Files touched | Verification |
|---|---|---|---|
| A | Re-label dataset.json (33 cases) | 1 | grep `qa_mcq` returns 33 lines; SHA changes |
| B | Update result files (3 cases × 10 + 33 cases × 5 = 195 record edits across 16 files) | 16 | Spot-check 2-3 files manually |
| C | Re-run `phase5_stats.py` locally | regenerates stats/*.{md,json} | New numbers match §3 estimates above (±0.1pp) |
| D | Update SUMMARY.md / METHODOLOGY.md / MANIFEST.md / BUG_HISTORY.md / AUDIT_REPORT.md | 5 doc files | Manual read-through |
| E | Update sandbox paper Tables 2/6a/6b/7 + add sentences for D-1/D-2/D-3/Conflict-4 + B-4 variance footnote | sandbox sn-article.tex | Recompile → verify ≤16p |
| F | Tier 2 mechanicals: D-7 (test_5plus5 fix), D-8 (strike stale HANDOFF instruction), D-9 (reconcile §6↔§14), D-12 (mark moot), D-14 (script fallback), D-15 (commit) | 5 files + 1 commit | Quick visual diff |
| G | BERT recompute in background (~3h) | 16 result files + SUMMARY + phase5_stats + sandbox tables | Wait for finish + verify averages reasonable |
| H | Final commits (3-4 themed, no Claude trailer) | git | Verify HEAD matches plan |

---

## §7. After this session 17 prep work

State at compact:
- Phase 4.5 launch attempt **CRASHED** (root cause TBD — to be diagnosed next session)
- AWS instance was idle-stopped at ~10:51 UTC (~50 min after launch); restarted briefly to retrieve state; stopped again
- Phase 4.5 results.jsonl had only ~4-5 cases logged in the brief run before crash
- Phase 4.5 needs to be re-launched cleanly next session
- BUT: the D-1 / D-2 / D-3 / D-6 / Tier 2 work above does NOT depend on Phase 4.5 — can all be done locally first
- Phase 4.5 fills the 4 TBD cells in sandbox `tab:graphsub` (Table 6 = `tab:graphsub` per LaTeX label resolution). Without Phase 4.5, those 4 cells stay [TBD]; the paper compiles fine with them.

---

## §8. Cost / time budget

| Item | Cost | Time |
|---|---|---|
| D-1 dataset re-label + Phase 5 recompute + doc updates | $0 | ~60 min |
| Tier 2 mechanicals (D-7/D-8/D-9/D-12/D-14/D-15) | $0 | ~45 min |
| Sandbox paper edits + recompile | $0 | ~30 min |
| D-6 BERT recompute (background) | $0 | ~3h laptop |
| Phase 4.5 re-launch (if attempted) — requires AWS restart + disable idle-stop alarm OR much higher CPU threshold | ~$3-5 | ~5h AWS |
| Total (full plan including Phase 4.5) | ~$3-5 | ~5-6h foreground + 3h BERT background |

End of recalc-scope doc.
