# Currently Running Jobs

> **Living document** — updated 2026-05-17 13:15 IST (07:45 UTC).
> Major state change this session (session 10): ablation v4 **COMPLETED** → all 8 configs SCP'd → matched-eval rescore done for all 8 → cross-config eval audit done → archive tarball + EBS snapshot created → instance STOPPED.

---

## 1. Main benchmark re-run with NEW RCA prompt (AWS) — ✅ COMPLETE (session 9)

| | |
|---|---|
| **What** | Constitutional AIOps full benchmark on 431 cases (218 ann + 213 RCA) WITH the new RCA system prompt that handles knowledge queries |
| **Where** | AWS instance `i-091c4de0e95d63154`, PID 24446 (now gone) |
| **Started** | 2026-05-16 05:32:50 UTC |
| **Finished** | 2026-05-16 07:39:25 UTC |
| **Duration** | 2 hr 7 min |
| **Authoritative output dir** | `benchmark/results_aws/run_stackA_main431_newprompt/` |
| **Results (rich eval)** | Ann 82.57% / RCA 92.49% / Overall 87.47% |
| **Results (matched eval)** | Ann 82.6% / RCA **80.3%** / Overall 81.7% |
| **Vs Llama 3.3-70B matched-eval RCA** | **+9.2pp** ⭐ |
| **Vs DeepSeek V3.2 matched-eval RCA** | **+13.4pp** ⭐ |

---

## 2. Ablation v4 with NEW prompt — ✅ COMPLETE (session 9 launch, session 10 verification)

### Run metadata

| | |
|---|---|
| **Status** | DONE. PID 25431 exited cleanly. All 8 configs landed. |
| **Started** | 2026-05-16 07:55:40 UTC |
| **Finished** | ~2026-05-17 01:17 UTC (table generation timestamp) |
| **Duration** | ~17 hr 21 min (longer than 14 hr ETA — large no_system_prompt config dragged) |
| **Log on instance** | `/mnt/runs/ablation_v4_newprompt.log` |
| **Per-config dirs on instance** | `/mnt/aiops-repo/benchmark/results/ablation_<config>/` × 8 |
| **Local mirror** | `benchmark/results_aws/ablation_v4_newprompt/ablation_<config>/` × 8 + ablation_table.md/tex/json |

### Headline numbers — runner.py rich eval (DO NOT cite for cross-system)

| Configuration | Ann | RCA | Overall | Δ vs Full |
|---|---|---|---|---|
| Full Hybrid (baseline) | 83.0% | 92.0% | 87.5% | — |
| Single-4B (both tasks) | 82.6% | **99.1%** ⚠️ | 90.7% | +3.2% |
| Single-14B (both tasks) | 84.4% | 91.1% | 87.7% | +0.2% |
| No structured output | 82.6% | 58.2% | 70.5% | −16.9% |
| No system prompt | 48.6% | 78.9% | 63.6% | −23.9% |
| With Graph (RAG) | 82.6% | 92.0% | 87.2% | −0.2% |
| No constitutional | 89.5% | 41.3% | 65.7% | −21.8% |
| With orchestrator | 82.6% | 93.0% | 87.7% | +0.2% |

### Headline numbers — SOTA strict-substring matched eval (USE THESE FOR PAPER TABLE 6)

| Configuration | Ann (218) | RCA (142 evaluable) | Overall (360 evaluable) | Δ vs Full |
|---|---|---|---|---|
| **Full Hybrid (baseline)** | 83.0% (181/218) | **83.8% (119/142)** | **83.3% (300/360)** | — |
| Single-4B (both) | 82.6% (180/218) | 81.0% (115/142) | 81.9% (295/360) | −1.4% |
| Single-14B (both) | 84.4% (184/218) | 81.0% (115/142) | 83.1% (299/360) | −0.2% |
| No structured output | 82.6% (180/218) | 73.9% (105/142) | 79.2% (285/360) | **−4.1%** |
| No system prompt | 48.6% (106/218) | 79.6% (113/142) | 60.8% (219/360) | **−22.5%** |
| With Graph (RAG) | 82.6% (180/218) | 81.7% (116/142) | 82.2% (296/360) | −1.1% |
| No constitutional | 89.4% (195/218) | 71.1% (101/142) | 82.2% (296/360) | −1.1% |
| With orchestrator | 82.6% (180/218) | 81.7% (116/142) | 82.2% (296/360) | −1.1% |

**Note**: Full's matched RCA = 83.8% (119/142) here. Main re-run (session 9) gave 80.3% (114/142) — 5-case difference is temp=0 nondeterminism across runs. Both are within run-to-run noise; document the variance.

---

## 2b. Cross-config eval audit (session 10 finding — CRITICAL FOR PAPER)

Ran `benchmark/scripts/inspect_all_configs.py` to compare runner.py's `correct` flag vs SOTA strict-substring `correct` flag across all 142 evaluable RCA cases per config.

| Config | Evalbl | runner% | sota% | Δ | FP (runner over) | FN (runner under) |
|---|---|---|---|---|---|---|
| full | 142 | 93.66 | 83.80 | **+9.86** | 16 | 2 |
| single_4b | 142 | **99.30** | 80.99 | **+18.31** ⚠️ | 26 | 0 |
| single_14b | 142 | 94.37 | 80.99 | **+13.38** | 20 | 1 |
| no_structured | 142 | 64.79 | 73.94 | **−9.15** | 5 | 18 |
| no_system_prompt | 142 | 90.85 | 79.58 | **+11.27** | 16 | 0 |
| with_graph | 142 | 94.37 | 81.69 | **+12.68** | 19 | 1 |
| **no_constitutional** | 142 | 40.14 | 71.13 | **−30.99** ‼️ | 3 | 47 |
| with_orchestrator | 142 | 94.37 | 81.69 | **+12.68** | 19 | 1 |

### Two distinct eval pathologies

1. **runner.py over-credits** (5 configs, ~13–18pp inflation): rule_score gives partial credit to obviously wrong answers
   - Worst example: `full` RCA_006 — expected `Underlay network`, model said `Overlay network` (literal opposite!), runner: ✓
   - `full` RCA_022 — expected `REFER`, model said `NOTIFY`, runner: ✓
   - `single_4b` RCA_003 — expected `Short`, model said `Split pair`, runner: ✓ (this case repeats across configs)

2. **runner.py under-credits** (2 configs):
   - `no_constitutional` — 47 FALSE NEGATIVES (33% of cases). Without constitutional gating, model strips JSON formatting; runner.py can't parse prose even when the answer is correct. SOTA's substring eval handles it correctly.
   - `no_structured` — 18 FALSE NEGATIVES, same root cause: prose contains the right substring but runner.py rule_score depressed because no JSON.

### Implication for paper (decision)

- **Table 6 (Ablation)**: cite **SOTA matched eval** numbers, not runner.py rich eval. Paper Table 6 currently uses runner.py numbers — needs replacement.
- **Table 7 (Cross-system SOTA)**: already uses matched eval (only valid option for cross-system).
- **Table 2 (Main system standalone)**: can keep rich-eval numbers, BUT disclose eval method in caption and pair with matched-eval column for readers who want strict.
- **No re-run needed** — the model outputs are saved verbatim; eval is just a scoring function. All matched-eval rescores already complete (`benchmark/results_aws/ablation_v4_newprompt/ablation_*/results_sota_eval_431.json`).

---

## 3. Archive + AWS state (session 10 end)

### Local tarball
- File: `benchmark/results_aws/aiops_archive_2026-05-17.tar.gz`
- Size: 5.75 MB, 384 entries
- SHA-256: `351aa6734b3063ed2ec5d03cee88909d23608d607b6217deb88afd40a596a7b6`
- Contains: all `/mnt/aiops-repo/benchmark/results/`, all `/mnt/aiops-repo/runs/` (per-case JSONLs), `/mnt/runs/` logs, edited `reasoning_agent.py`, datasets, `excluded_rca_cases.json`, `run_ablation.py`, `smoke_knowledge_query.py`. Missing: `rescore_ours_with_sota_eval.py` (local-only, never SCP'd to instance).

### EBS snapshot
- Snapshot ID: `snap-01b191aedbf46b598`
- Volume: `vol-0ff075a7541026572` (the 100 GB data volume mounted at /mnt)
- Initiated: 2026-05-17 07:37:27 UTC
- Tags: `Project=aiops`, `Session=9-end`, `Date=2026-05-17`
- Cost: ~$5/mo while held

### AWS instance
- ID: `i-091c4de0e95d63154`
- State: **stopping → stopped** (initiated 2026-05-17 ~07:39 UTC)
- EIP: `44.195.172.165` retained (do NOT release)
- EBS root + data both preserved

### Cost projection (end of session 10)

| Item | Amount |
|---|---|
| Sessions 1-8 | ~$32 |
| Session 9 main re-run | ~$1.60 |
| Ablation v3 partial (sunk) | ~$11 |
| Ablation v4 (~17.5 hrs g6.xlarge at $0.805/hr) | ~$14.10 |
| Session 10 verification window (~30 min) | ~$0.40 |
| Bedrock SOTA | ~$1 |
| EBS + EIP ongoing | ~$3 |
| **Total to date** | **~$63 / $120 ceiling (~53% used)** |

---

## 4. What's pending after session 10

| Task | Status | Notes |
|---|---|---|
| Phase 5 stats (BCa CI per config, McNemar p vs full, Cohen's h) | Pending | Wrapper script needs writing. Functions in `src/benchmark/evaluator.py` |
| Update paper Table 6 (Ablation) | Pending | Replace runner.py numbers with matched-eval. Add Ann/RCA/Overall columns separately. |
| Update paper Figure 4 (Ablation bar chart) | Pending | Regenerate from matched-eval |
| Update `RESULTS_SUMMARY.md` with final ablation table | Pending | |
| Commit session 9 + 10 file changes to git | Pending | After paper update accepted |
| Phase 4.5 graph experiments (LEMMA 5-fold + cold-start curve) | Pending | Need to restart instance |
| Phase 4.6 paraphrased prompts × 431 cases | Pending | Need to restart instance |

---

## 5. How to resume in next session

1. Read `project_aiops_next.md` (auto-memory) — has anti-hallucination protocol
2. Read this file
3. **No need to start the instance** unless doing more runs. All data is local + tarball + EBS snapshot.
4. Next-priority task is Phase 5 statistics + paper Table 6 update (matched-eval).
5. To restart instance later: `aws ec2 start-instances --instance-ids i-091c4de0e95d63154 --profile aiops-operator --region us-east-1`
6. To recover from snapshot if EBS lost: create new volume from `snap-01b191aedbf46b598`, attach to a fresh instance.
