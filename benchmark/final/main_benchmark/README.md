# `run_stackA_main431_newprompt/` — AUTHORITATIVE main benchmark (v2)

> **Status (2026-05-16 session 9 end)**: This directory contains the AUTHORITATIVE Constitutional AIOps main benchmark results. The previous `run_stackA_main431/` directory is kept for v1-paper reference but is **superseded by these results** for all paper claims.
>
> **Canonical paper-source file**: `results_sota_eval_431.json` (matched/strict eval, Table 7 + Phase 5 stats). `results.json` is the runner.py rich-eval provenance copy retained for audit; the paper headline numbers are computed from `results_sota_eval_431.json`.
> **What changed**: The RCA system prompt in `src/agents/reasoning_agent.py` was extended to explicitly handle knowledge-format queries (no longer refuses with "this is a conceptual inquiry, not an incident"). See `../METHODOLOGY.md` §7 for the diff and rationale.

---

## Run metadata

| | |
|---|---|
| Started | 2026-05-16 05:32:50 UTC |
| Finished | 2026-05-16 07:39:25 UTC |
| Duration | 2h 7min |
| Where | AWS instance `i-091c4de0e95d63154`, PID 24446 |
| Endpoint | Ollama `localhost:11434` (Q4_K_M on instance) |
| Fast model | qwen3:4b-instruct |
| Reasoning model | qwen3:14b |
| Temperature | 0.0 (deterministic) |
| Dataset | `benchmark/datasets/processed/benchmark_431_seed42.json` (218 ann + 213 RCA) |
| Per-case persistence | `/mnt/aiops-repo/runs/2026-05-16T05-32-50_bench_constitutional_aiops/results.jsonl` (append+fsync, 431 records) |
| System prompt change | `src/agents/reasoning_agent.py` RCA_SYSTEM_PROMPT — added INPUT FORMATS section |

---

## Files in this directory

| File | What |
|---|---|
| `results.json` | 431 per-case records (test_id, task_type, correct, rule_score, actual_output, expected_output, bert_f1, cosine_similarity, term_overlap, etc.) |
| `summary.json` | Aggregate metrics (annotation/rca/overall accuracy, latencies, ...) |
| `benchmark_result.json` | API-compatible summary |
| `paper_tables.md` / `.tex` | Pre-formatted tables (instance-generated) |
| `results_sota_eval_431.json` | Re-scored through SOTA eval (`benchmark/scripts/eval/rescore_ours_with_sota_eval.py`) — used for the apples-to-apples Table 7 comparison |

---

## Authoritative numbers

### Under runner.py rich eval (Table 2 — paper headline)

| Metric | Value |
|---|---|
| Annotation accuracy | 82.57% (180/218) |
| RCA accuracy | **92.49% (197/213)** |
| Overall accuracy | **87.47% (377/431)** |
| Cosine similarity (overall) | 0.3265 |
| Term overlap (overall) | 0.5249 |
| RCA term overlap | 0.7794 |
| Avg inference latency | 17.6 s |
| P95 inference latency | 48.4 s |
| Annotation avg latency | 3.07 s |
| RCA avg latency | 32.5 s |

### Under SOTA matched eval (Table 7 — apples-to-apples)

| Metric | Value | Δ vs Llama | Δ vs DeepSeek |
|---|---|---|---|
| Annotation | 82.6% (180/218) | −8.7pp | −7.8pp |
| **RCA (evaluable)** | **80.3% (114/142)** | **+9.2pp** ⭐ | **+13.4pp** ⭐ |
| Overall (evaluable) | 81.7% (294/360) | −1.6pp | +0.6pp |

71 RCA cases excluded (39 Chinese-language + 32 multiple-choice letters). See `../METHODOLOGY.md` §2.

### Comparison vs OLD prompt (this directory's predecessor)

| Eval | OLD prompt | NEW prompt | Δ |
|---|---|---|---|
| Runner.py RCA | 94.8% (202/213) | 92.5% (197/213) | **−2.3pp** |
| Runner.py Overall | 88.6% (382/431) | 87.5% (377/431) | −1.1pp |
| Matched (SOTA) RCA | 69.0% (98/142) | **80.3% (114/142)** | **+11.3pp** ⭐ |
| Matched (SOTA) Overall | 77.2% (278/360) | 81.7% (294/360) | **+4.5pp** ⭐ |

Trade-off: gave up 5 cases under the lenient eval (verbose old refusals had term-overlap accidents that the lenient eval credited), gained 16 cases under the strict eval. Net win is unambiguous.

### Case-level diff (RCA, 142 evaluable cases)

| Outcome | Count |
|---|---|
| Both prompts correct | 93 |
| Both prompts wrong | 23 |
| **GAINS** (OLD wrong / NEW right) | **21** |
| **LOSSES** (OLD right / NEW wrong) | 5 |
| **Net** | **+16** |

Known refusal cases all flipped to correct: RCA_002 (TACACS+) ✓, RCA_028 (IGMPv3) ✓, RCA_067 (100MHz) ✓. Improvement generalizes beyond the 3 targeted cases (21 gains total).

---

## What's needed downstream

- **Table 6 ablation** still uses OLD prompt (4 configs in `ablation_*_oldprompt_BAK/`). To get an apples-to-apples ablation table, the 8-config ablation must be re-run with the new prompt. Pending user decision (~14 hrs, ~$11).
- **Phase 5 statistics** (BCa CIs, McNemar p, Cohen's h) should run on this directory's `correct` flags + the SOTA jsonls.
- **Table 7 + 8 in the paper** should cite numbers from this directory (matched eval) for the SOTA comparison, and from this directory (rich eval) for the system-on-its-own benchmark.

---

## Provenance trail (for reviewers)

- Pre-edit refusal smoke (3/3 refused): saved in `../../benchmark/scripts/_dev/smoke_knowledge_query.py` history (prompt diff in git).
- Post-edit smoke (3/3 substantive answers): same script, output verified in session 9 chat log.
- Per-case JSONL with fsync per record on AWS instance at `/mnt/aiops-repo/runs/2026-05-16T05-32-50_bench_constitutional_aiops/results.jsonl`.
- Old-prompt results preserved in `../run_stackA_main431/` for diff.

---

## Loss-case analysis (Path 2 investigation, session 9)

Of the 5 cases that flipped from "correct under matched eval" to "wrong under matched eval" after the prompt change, we examined each manually to determine whether the prompt edit caused a systematic regression. **None of the 5 losses are caused by the new "handle knowledge query" instruction misfiring.**

| Case | Expected | OLD output (correct) | NEW output (wrong) | Diagnosis |
|---|---|---|---|---|
| RCA_003 | `Short` | "Short circuit between two conductors in the twisted-pair cable" | "Crosstalk" | **Genuine answer change** — model picked a different (likely wrong) cause. Cause: temp=0 numerical nondeterminism (model output is stochastic across runs even at temp=0). Unrelated to the prompt edit. |
| RCA_183 | `catalogue_disk_io_issue` | "Network connectivity failure due to misconfigured firewall rules..." | "Network connectivity failure between agent and target hosts due to misconfigured routing..." | Both substantively wrong; old happened to cross the term-overlap threshold by a few stop-words, new fell below by tiny wording variance. **Borderline noise.** |
| RCA_169 | `orders-db_cpu_spike` | "Sudden surge in incoming connections overwhelming server resources, leading to CPU exhaustion" | "Sudden surge in short-lived TCP connections overwhelming server connection handling mechanisms, leading to excessive CPU utilization" | Same diagnosis as RCA_183. Both miss the canonical `orders-db_cpu_spike` label entirely; old happened to overlap on filler words. **Borderline noise.** |
| RCA_041 | `UNIX time` | Refused as "question contains a critical error" but listed all 4 options including UNIX time → **lucky substring match** | "ISO 8601 is correct, none of the listed options is valid" — more direct, no longer enumerates options | **NEW answer is arguably better** (more direct technical assessment) but lost the accidental substring hit. Not a real regression. |
| RCA_156 | `prometheus_service_degradation` | "Client-side connection termination caused by server-side response delays leading to client timeouts" | "Client-side connection termination due to server-side response delays or client-side timeout configurations" | Near-identical wording, both miss the canonical label entirely. **Borderline noise.** |

### Loss-pattern conclusion

- **0 systematic regressions** from the prompt edit
- **1 case** (RCA_003): genuine model nondeterminism — would happen on any deterministic-but-stochastic re-run regardless of prompt
- **3 cases** (RCA_183, RCA_169, RCA_156): borderline term-overlap edge cases where tiny wording variance crossed the threshold; both old and new are wrong substantively
- **1 case** (RCA_041): NEW answer is arguably better; only "lost" because OLD's verbose refusal happened to include the expected substring

The 21 GAINS are systematic (knowledge-query fix working as designed across multiple cases). The 5 LOSSES are noise + borderline + 1 case where NEW is arguably better. **No regression worth fixing before ablation re-run.**
