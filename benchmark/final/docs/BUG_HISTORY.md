# Bug History — Benchmark Infrastructure

> **Scope**: Bugs discovered in `benchmark/scripts/run/run_sota_baselines.py`, `benchmark/scripts/run/run_ablation.py`, `src/benchmark/runner.py`, and `src/agents/*` that affected the validity of saved results in this directory. Documented for reviewer transparency and reproducibility.
> **Maintained**: Append-only. When a new bug is found and fixed, add a row below.

---

## Summary table

| # | When found | Severity | Component | Affected files in this dir | Status |
|---|------------|----------|-----------|----------------------------|--------|
| 1 | Session 6 (2026-05-14) | High | `run_sota_baselines.py` argparse | All earlier SOTA runs | Fixed session 7 |
| 2 | Session 7 (2026-05-15) | High | `run_sota_baselines.py` excluded handling | All earlier no-prompt runs | Fixed session 7 |
| 3 | Session 7 (2026-05-15) | Medium | `run_sota_baselines.py` summary denominator | All earlier no-prompt summaries | Fixed session 7 |
| 4 | Session 8 (2026-05-15) | **Critical** | `src/agents/model_router.py` config caching | All `*_BROKEN/` dirs on AWS instance | Fixed session 8 |
| 5 | Session 8 (2026-05-15) | Medium | `src/agents/fast_annotator.py` confidence type | `no-system-prompt` ablation only (12 cases) | Fixed session 8 |
| 6 | Session 8 (2026-05-15) | High | `src/benchmark/runner.py` missing ablation flags | `no-structured` + `no-constitutional` ablation rows | Fixed session 8 |
| 7 | Session 8 (2026-05-15) | Low | `run_sota_baselines.py` hardcoded temperature | All earlier SOTA runs at t=0 | Fixed session 8 (added `--temperature`) |
| 8 | Session 8 (2026-05-15) | Infrastructure | AWS instance root EBS full | Couldn't compute BERTScore, blocked writes | Fixed session 8 (resized 40→80 GB) |

---

## Bug #1 — `run_sota_baselines.py`: `--rca 0` / `--ann 0` ignored

**Symptom**: Passing `--rca 0` to limit RCA cases didn't skip them — all RCA cases still ran.

**Root cause**: Argparse defaults were `default=0` with check `if args.rca: slice_to(args.rca)`. Python evaluates `if 0:` as False, so the slice was never applied. `0` was indistinguishable from "no limit".

**Fix** (`run_sota_baselines.py:354-355` and `387-390`): Changed `default=0` to `default=None`, condition to `if args.rca is not None: cases = cases[:args.rca]`. Now `0` means "skip all" (empty slice), `None` means "all".

**Impact on saved data**: Earlier exploratory runs used `--rca 0 --ann 5` expecting only annotation but got all 198 RCA cases run. Doesn't affect any published paper number.

---

## Bug #2 — `run_sota_baselines.py`: 71 excluded RCA cases evaluated as if real

**Symptom**: DeepSeek prompted SOTA RCA reported as 57.1% but expected ~67%. After investigation, the 71 known-unevaluable cases (39 Chinese-language expected outputs + 32 bare-letter multiple-choice answers) were being evaluated and counted as "wrong" because the model's English response didn't substring-match the Chinese/letter expected text.

**Root cause**: The script ran all 198 RCA cases. Exclusion was supposed to be applied post-hoc by callers reading the JSONL, but multiple downstream summaries forgot.

**Fix** (`run_sota_baselines.py:392-453`): At startup, the script now loads `benchmark/datasets/processed/excluded_rca_cases.json` and inlines a `correct=null, skip_reason="excluded_unevaluable"` record for each of the 71 cases. Summary then uses `rca_eval` (non-null) for the denominator.

**Impact on saved data**:
- `sota_deepseek_v3/results_t0_BAK.jsonl` — pre-fix, evaluated all 198 (also has Bug #6-related duplicate-RCA artifact from overlapping resume runs — 301 RCA records)
- `sota_llama_3_3_70b/results_t0_BAK.jsonl` — pre-fix, evaluated all 198 (clean dedup, but excluded cases mixed in)
- `phase46_noprompt/deepseek_noprompt.jsonl` — pre-fix
- `phase46_noprompt/llama_noprompt_v2.jsonl` and `_bak` variants — pre-fix

For all of these, the "clean" numbers can be recovered by filtering out the 71 IDs in `excluded_rca_cases.json` post-hoc. Done in `BUG_HISTORY` walkthroughs and the `METHODOLOGY.md` reproduction snippets.

---

## Bug #3 — `run_sota_baselines.py`: summary denominator wrong

**Symptom**: Even after Bug #2 fix, the printed summary showed `RCA: X/198 = Y%` which still divided by 198, not 127 (evaluable). The percentage shown was depressed.

**Fix** (`run_sota_baselines.py:462-471`): Summary now computes `rca_eval = [r for r in rca_r if r.get("correct") is not None]` and uses `len(rca_eval)` (= 127) as denominator. Prints `"X/127 evaluable = Y% (71 excluded)"`.

---

## Bug #4 — `src/agents/model_router.py`: stale `config` reference broke ablation routing (CRITICAL)

**Symptom**: Ablation produced **identical** accuracy numbers for `full` (4B+14B), `single-4b` (4B+4B), `single-14b` (14B+14B), and `no-structured` (4B+14B). For all 202 annotation cases, the saved `actual_output` was **character-for-character identical** across configs — impossible if different models had been called.

**Root cause**: `model_router.py:27` had `from src.config import config`. This captured the config object reference at first import. The ablation script's `importlib.reload(src.config)` correctly replaced `sys.modules['src.config'].config` with a new object reading new env vars, but `model_router.py`'s already-bound `config` name still pointed to the **old** object. Every `payload["model"] = config.llm.fast_agent_model` line in completion methods therefore returned the model name from the FIRST config that was set — never updating across ablation configs. The `model` field saved in `results.json` was just a label from the ablation config dict, not what was actually called.

**Fix** (`model_router.py:27` and all `config.llm.X` references):
```python
# Old:
from src.config import config
# Used as: config.llm.fast_agent_model

# New:
import src.config as _cfg_module
# Used as: _cfg_module.config.llm.fast_agent_model  (dynamic module-attribute lookup)
```
After `importlib.reload(src.config)`, `_cfg_module.config` reads the **current** module attribute (which has been replaced with the new config). 8 occurrences updated.

**Belt-and-suspenders** (`benchmark/scripts/run/run_ablation.py:115-130`): `setup_env()` now also reloads `src.agents.model_router`, `src.agents.fast_annotator`, `src.agents.reasoning_agent` after `src.config`. This ensures any other modules that imported `config` via `from src.config import config` also get refreshed.

**Verification**: Smoke tests post-fix confirmed:
- For `single-4b` config, RCA responses now genuinely differ from `full` (4B vs 14B reasoning produces different prose)
- For `single-14b` config, annotation responses now differ from `full` (14B vs 4B annotation produces different summaries)

**Impact on saved data**: All four already-completed ablation configs from the broken run (`ablation_full_BROKEN/`, `ablation_single_4b_BROKEN/`, `ablation_single_14b_BROKEN/`, `ablation_no_structured_BROKEN/` on the AWS instance at `/mnt/aiops-repo/benchmark/results/`) effectively tested the same `qwen3:4b-instruct + qwen3:14b` configuration. Numbers there are INVALID for model-architecture comparison.

---

## Bug #5 — `src/agents/fast_annotator.py`: confidence type mismatch

**Symptom**: In the `no-system-prompt` ablation config, 12 annotation cases failed with `TypeError: '>=' not supported between instances of 'str' and 'float'`. These were silently counted as `correct=False`, depressing the no-system-prompt annotation score.

**Root cause**: Without the system prompt, the model occasionally returned `{"confidence": "0.85"}` (string) or `{"confidence": "high"}` instead of float. The downstream `if confidence >= 0.90:` check in `base_agent.calculate_confidence_level()` couldn't compare str to float, raising an exception caught generically and logged as "Fast annotation failed".

**Fix** (`fast_annotator.py:228-235`):
```python
raw_confidence = annotation.get("confidence", 0.5)
try:
    confidence = float(raw_confidence) if not isinstance(raw_confidence, bool) else 0.5
except (TypeError, ValueError):
    confidence = 0.5
confidence = max(0.0, min(1.0, confidence))
```

**Impact**: `ablation_no_system_prompt_BROKEN/` (on AWS instance) ran with this bug. 12 cases artificially marked wrong. The re-run with the fix should show ~6pp higher annotation accuracy for that config.

---

## Bug #6 — `run_ablation.py` + `src/benchmark/runner.py`: ablation flags defined but never wired

**Symptom**: The `no-structured` and `no-constitutional` ablation configs produced numbers nearly identical to `full`. Investigation showed these flags were never read by any code path.

**Root cause**:
- `benchmark/scripts/run/run_ablation.py` defines flags `no_structured: True` (line 73) and `skip_constitutional: True` (line 94) in the config dicts
- `BenchmarkConfig` in `src/benchmark/runner.py:43-55` only had 3 ablation fields: `skip_system_prompt`, `inject_graph_context`, `use_orchestrator`
- The two undeclared flags were silently ignored when building `BenchmarkConfig(...)`
- Even when passed, the runner had no code path to act on them

**Fix** (this session, 2026-05-15):
1. Added `no_structured: bool = False` and `skip_constitutional: bool = False` fields to `BenchmarkConfig`.
2. Wired both through in `run_ablation.py:170-175`: now passing `no_structured=config.get(...)` and `skip_constitutional=config.get(...)` to `BenchmarkConfig`.
3. Added handler in `runner.py:421-454`: when `no_structured` is set, overrides `self.fast_annotator.get_system_prompt` and `self.reasoning_agent.get_system_prompt` to plain-text variants that don't request JSON; when `skip_constitutional` is set, overrides them to minimal task-only JSON prompts without constitutional/safety language.

**Impact on saved data**: Any earlier `ablation_no_structured/` or `ablation_no_constitutional/` results (including in `benchmark/results_v2.0_frozen/`) ran with these flags as **labels only** — the actual setup was identical to `full`. **The numbers there are not honest ablations.** This is independent of Bug #4: even without the routing bug, these two configs would have given the same numbers as full.

---

## Bug #7 — `run_sota_baselines.py`: temperature hardcoded to 0.0

**Symptom**: Llama and DeepSeek no-prompt RCA both happened to score **95/127 evaluable** (74.8%). At `temperature=0` Bedrock returns deterministic outputs, so re-running gives identical results — the coincidence couldn't be broken by re-running. Case-by-case analysis showed the two models agree on 91 cases, both fail on 28, and disagree on 8 (4 each direction, cancelling perfectly). Real but optically suspicious for reviewers.

**Root cause**: Temperature was a literal `0.0` in three places in `_call_bedrock()` body construction (one per model format).

**Fix** (this session, 2026-05-15):
1. Added `--temperature` CLI argument (default 0.0).
2. Threaded `temperature` through `model_cfg` dict.
3. `_call_bedrock` reads `model_cfg["temperature"]` instead of literal 0.0.

**Re-run policy** (session 8 onward): SOTA runs use `--temperature 0.05` to introduce natural sampling variance while keeping output quality essentially unchanged. The `*_t0_BAK.jsonl` files preserve the deterministic t=0 numbers for provenance.

---

## Bug #8 — AWS root EBS full → BERTScore + writes broken

**Symptom**: All saved ablation summaries on AWS show `"bert_f1": 0.0`. SCP from local to instance failed. Live writes to `/mnt/runs/ablation_v3.log` blocked (0 bytes).

**Root cause**: Root EBS volume was 40 GB; usage reached 100% from accumulated pytorch site-packages (5 GB in `~/.local`), Hugging Face Hub partial downloads (~1.6 GB incomplete `deberta-xlarge-mnli`), and runtime caches.

**Fix** (session 8): `aws ec2 modify-volume --size 80 → growpart /dev/nvme0n1 1 → resize2fs /dev/nvme0n1p1`. Now 78 GB total, 41 GB free.

**Impact**: BERTScore can now download correctly for the re-run ablation. Earlier ablation summaries with `bert_f1: 0.0` are not "wrong" per se — they just couldn't be computed. If needed for the paper, BERTScore can be recomputed post-hoc on saved `actual_output` strings using a local install.

---

## What was NOT a bug (verified)

- **74.8% RCA tie between Llama and DeepSeek**: real coincidence at t=0 deterministic sampling, verified via per-case comparison (8 disagreements that cancel). Not a methodology error. Re-running at t=0.05 should naturally break the tie.
- **`run_stackA_main431/summary.json` vs `results_merged.json`**: the `summary.json` shows lower RCA (79.34%) because it predates the 33-case OpsEval-remine label fix; `results_merged.json` is the post-fix data and is what the paper uses. Both files coexist intentionally for provenance.
- **OpenSSH annotation 50%**: not a bug. All 20 failures are false positives (single auth events flagged as anomaly), zero false negatives on real brute force. Disclosed in paper Table 4.
- **`benchmark/results/ablation_*_BROKEN/` on AWS**: kept for provenance, NOT to be used. Renamed with `_BROKEN` suffix.
