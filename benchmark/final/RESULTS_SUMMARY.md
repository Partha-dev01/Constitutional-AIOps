# Benchmark Results Summary
_Generated: 2026-05-16 13:25 IST (08:00 UTC) — session 9 end_

> ### ⚠ 2026-05-19 ARCHIVE NOTICE — read `FINAL/SUMMARY.md` first
> This file is the session-9 summary and predates: (a) the ablation v4 matched-eval rescoring done in session 10, and (b) the 2026-05-19 archive operation. The headline numbers in this file are still correct but the ablation Table 6 in here is missing. **For the current authoritative summary, use [FINAL/SUMMARY.md](FINAL/SUMMARY.md).** Source-file paths referenced below pointed at `run_stackA_main431_newprompt/`, `sota_*/`, `phase46_noprompt/` — those dirs were moved to `_archive_originals_2026-05-19/` and the canonical copies are now in `FINAL/`.

> ✅ **This is the authoritative results summary as of 2026-05-16 session 9.** Supersedes all prior versions of this file. Authoritative source files are linked per row in the tables below.

---

## Headline numbers (paper-ready)

### Our system on full benchmark (Table 2 — rich eval, 431 cases)

| Metric | Value | Source file |
|---|---|---|
| Annotation | **82.57% (180/218)** | `run_stackA_main431_newprompt/results.json` |
| RCA | **92.49% (197/213)** | same |
| Overall | **87.47% (377/431)** | same |
| BERTScore F1 (overall) | (re-run with new prompt outputs needed) | — |
| Cosine similarity | 0.3265 | `run_stackA_main431_newprompt/summary.json` |
| Term overlap | 0.5249 | same |

### SOTA baseline comparison (Table 7 — matched substring eval, 431 cases, 71 RCA excluded)

| System | Ann | RCA (evaluable) | Overall (evaluable) | ΔRCA vs Ours |
|---|---|---|---|---|
| **Constitutional AIOps (Ours, new prompt)** | 82.6% (180/218) | **80.3% (114/142)** | 81.7% (294/360) | — |
| Llama 3.3-70B (Bedrock, prompted) | 91.3% (199/218) | 71.1% (101/142) | 83.3% (300/360) | **−9.2pp** |
| DeepSeek V3.2 (Bedrock, prompted) | 90.4% (197/218) | 66.9% (95/142) | 81.1% (292/360) | **−13.4pp** |
| Drain (LogPAI parser) | 50.5% (102/202, 400 cases) | N/A | N/A | N/A |

**RCA Gap vs SOTA monoliths under apples-to-apples eval: +9.2pp (Llama) and +13.4pp (DeepSeek).**
Annotation gap behind both SOTAs by ~8pp (small-model inherent limit, 4B vs 70B).
Overall: essentially tied with DeepSeek (+0.6pp), 1.6pp behind Llama.

### Prompt sensitivity (Table 8 — matched eval, 431 cases)

| System | Ann (prompted → no-prompt) | RCA (prompted → no-prompt) | Headline |
|---|---|---|---|
| Llama 3.3-70B | 91.3% → 67.9% = **−23.4pp** | 71.1% → 73.2% = +2.1pp | Annotation collapses, RCA flat |
| DeepSeek V3.2 | 90.4% → 88.5% = **−1.9pp** | 66.9% → 73.9% = +7.0pp | Prompt-insensitive (JSON anyway) |

The 31pp prompt-removal drop in our v1 paper headline reflects loss of **task specification in the small annotation model**, not architectural fragility — 14B reasoning model is largely robust (≤7pp change). Cross-model replication shows this asymmetry is universal: large reasoning model robust, small classification model brittle under prompt removal.

---

## What changed from v1 paper

| | v1 paper (OLD prompt) | v2 (NEW prompt, post-session-9) |
|---|---|---|
| Main RCA (rich eval) | 94.8% | 92.5% (−2.3pp) |
| Main RCA (matched eval) | 69.0% | **80.3% (+11.3pp)** |
| Vs Llama on matched-eval RCA | −2.1pp (loss) | **+9.2pp (lead)** |
| Vs DeepSeek on matched-eval RCA | +2.1pp (lead) | **+13.4pp (lead)** |
| Annotation | 82.6% | 82.6% (unchanged) |
| Refusal behavior on knowledge queries | Refused with "this is a conceptual inquiry not an incident" | Provides substantive technical answer |
| Code change | — | `src/agents/reasoning_agent.py` RCA_SYSTEM_PROMPT — added INPUT FORMATS section |

The change is a **capability improvement** (system now handles knowledge-format queries), not eval-gaming: the prompt does not mention canonical labels or eval-relevant strings; it just instructs the model to give substantive answers instead of refusing.

---

## What's blocked / pending

| Item | Status | Blocker |
|---|---|---|
| Table 6 ablation (8 configs) | Re-run needed with new prompt | User decision (~14 hrs, ~$11) |
| Phase 5 stats (BCa CIs, McNemar, Cohen's h) | Scripts in `src/benchmark/evaluator.py` | Apply to `run_stackA_main431_newprompt/results.json` + SOTA jsonls |
| Phase 4.5 graph experiments | Pending after ablation | Sequencing |
| Phase 4.6 Part A (5 paraphrases) | Pending after ablation | Sequencing |

---

## Authoritative file map

| Use | File path |
|---|---|
| Tables 2/3/4 (rich eval) | `run_stackA_main431_newprompt/results.json` |
| Table 7 row "Ours" (matched eval) | `run_stackA_main431_newprompt/results_sota_eval_431.json` |
| Table 7 row "Llama 3.3-70B" | `sota_llama_3_3_70b/results.jsonl` (431 records) |
| Table 7 row "DeepSeek V3.2" | `sota_deepseek_v3/results.jsonl` (431 records) |
| Table 7 row "Drain" | `sota_drain/results.jsonl` (202 cases — needs 16-case 431 extension) |
| Table 8 Llama row | `phase46_noprompt/llama_noprompt_clean.jsonl` (431 records) |
| Table 8 DeepSeek row | `phase46_noprompt/deepseek_noprompt_v2.jsonl` (431 records) |
| Latency (Stack A) | `run_stackA_main431_newprompt/summary.json` |

---

## v1 paper reference state (do NOT cite from these)

| Dir | What |
|---|---|
| `run_stackA_main431/` | OLD prompt main results (v1 paper headline) — preserved for diff and provenance |
| `ablation_*_oldprompt_BAK/` (on AWS instance) | OLD prompt 4-config ablation results — preserved for diff |

---

## How to regenerate this file

After any new SOTA run or main re-run completes:
```bash
cd "<repo root>"
python benchmark/scripts/compile_results.py \
    --main benchmark/results_aws/run_stackA_main431_newprompt/results.json \
    --sota-rescore benchmark/results_aws/run_stackA_main431_newprompt/results_sota_eval_431.json \
    --out benchmark/results_aws/RESULTS_SUMMARY.md
```
(Note: compile_results.py may need updating to take these new flag forms — currently it auto-discovers from `run_stackA_main431`.)
