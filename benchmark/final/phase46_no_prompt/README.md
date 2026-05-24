# `phase46_noprompt/` — Cross-model no-prompt replication (Table 8)

> **Purpose**: Runs Llama-3.3-70B and DeepSeek-V3.2 on the same 400-case benchmark with the **system prompt stripped** to test cross-model prompt sensitivity. Compares against Table 7 (prompted) to compute the per-model annotation/RCA drop.
> **See also**: `../FILE_PROVENANCE.md`, `../METHODOLOGY.md`, `../BUG_HISTORY.md`.

---

## Which file should I read?

**For the paper Table 8**: use the two files **without** any suffix:
- `llama_noprompt_clean.jsonl` ← Llama no-prompt
- `deepseek_noprompt_v2.jsonl` ← DeepSeek no-prompt

Both produced by the fixed `run_sota_baselines.py` (post all 8 bugs fixed).

All other files in this directory are kept for **provenance** — they document earlier iterations during bug discovery. None should be cited as primary results.

---

## File-by-file

| File | What | Status |
|------|------|--------|
| `llama_noprompt_clean.jsonl` | Single fresh run, fixed script | ✅ Authoritative (Table 8 Llama row) |
| `deepseek_noprompt_v2.jsonl` | Inline-excluded handling, fixed script | ✅ Authoritative (Table 8 DeepSeek row) |
| `llama_clean_t005.log` | Live log of the t=0.05 re-run | Diagnostic |
| `deepseek_v2_t005.log` | Live log of the t=0.05 re-run | Diagnostic |
| — | — | — |
| `llama_noprompt_clean_t0_BAK.jsonl` | Previous t=0 deterministic run of the fixed-script Llama | Provenance (preserves the deterministic numbers) |
| `deepseek_noprompt_v2_t0_BAK.jsonl` | Previous t=0 deterministic run of v2 DeepSeek | Provenance |
| `llama_v2.log` | Log of the contaminated `llama_noprompt_v2.jsonl` (3 overlapping runs) | Diagnostic |
| `llama_clean.log` | Log of the t=0 clean Llama run | Diagnostic |
| `deepseek_v2.log` | Log of the t=0 v2 DeepSeek run | Diagnostic |
| — | — | — |
| `llama_noprompt_v2.jsonl` | **CONTAMINATED** — 641 records from 3 overlapping runs (first partial 150 + resume + fresh full). Has duplicate case_ids. | ❌ Use only with last-wins dedup. |
| `llama_noprompt_bak.jsonl` | First failed Llama run (0% annotation — no NL fallback was implemented at the time) | ❌ Broken |
| `llama_noprompt_final_bak.jsonl` | Session-6 partial: 202 ann + 107 RCA | ❌ Partial, pre-fix |
| `llama_noprompt_rescored_bak.jsonl` | Intermediate rescoring attempt | ❌ Artifact |
| `deepseek_noprompt.jsonl` | Pre-fix DeepSeek run (excluded 71 not marked inline) | ❌ Use only after post-hoc filter |

---

## Authoritative numbers (t=0 — preserved in `*_t0_BAK.jsonl` for reference)

These numbers come from the post-fix scripts at t=0 deterministic sampling. The session-8 re-runs at t=0.05 may differ slightly.

| Model | Annotation | RCA (127 evaluable) | Overall (329) |
|-------|------------|---------------------|---------------|
| Llama 3.3-70B (no-prompt) | 140/202 = 69.3% | 95/127 = 74.8% | 235/329 = 71.4% |
| DeepSeek V3.2 (no-prompt) | 176/202 = 87.1% | 95/127 = 74.8% | 271/329 = 82.4% |

**The Llama-DeepSeek 95/127 RCA tie** is a real coincidence (verified case-by-case: 91 cases both correct, 28 both wrong, 4+4 cancelling disagreement). The t=0.05 re-run aims to break this for paper-presentation clarity.

---

## How the no-prompt eval works

When `--no-prompt` is set, `run_sota_baselines.py`:
1. Passes an **empty system prompt** to Bedrock (`system=""`).
2. For annotation, the model usually responds in natural-language prose (no JSON) because the JSON-format instruction was in the stripped system prompt.
3. The eval (`_eval_annotation`) attempts JSON parse first; on failure, falls back to **NL keyword detection** (regex pattern for "anomaly", "error", "failure" vs "normal", "routine", "benign").
4. For RCA, the eval uses the standard substring match (model still tends to mention the root cause in its prose even without the prompt).

DeepSeek tends to output structured JSON even without the prompt (smaller annotation drop ~−4 pp). Llama defaults to NL prose (larger annotation drop ~−23 pp). This asymmetry supports the paper's "the small annotation model is the prompt-sensitive component" framing.

---

## How to reproduce

```bash
cd "<repo-root>"

# Llama no-prompt
python benchmark/scripts/run/run_sota_baselines.py \
    --model llama-3.3-70b \
    --no-prompt --temperature 0.05 \
    --dataset benchmark/datasets/processed/benchmark_400_seed42.json \
    --out benchmark/results_aws/phase46_noprompt/llama_noprompt_clean.jsonl

# DeepSeek no-prompt
python benchmark/scripts/run/run_sota_baselines.py \
    --model deepseek-v3 \
    --no-prompt --temperature 0.05 \
    --dataset benchmark/datasets/processed/benchmark_400_seed42.json \
    --out benchmark/results_aws/phase46_noprompt/deepseek_noprompt_v2.jsonl
```

Both use the fixed script with inline-excluded handling and float-coerced confidence parsing. Re-runs at the same temperature should produce similar (not identical) results.
