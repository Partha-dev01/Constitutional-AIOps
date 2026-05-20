# Broken Ablation Runs — DO NOT USE

> **Location**: AWS instance `i-091c4de0e95d63154` at `/mnt/aiops-repo/benchmark/results/`. These directories are **NOT** copied to this local `results_aws/` directory.
> **Why this doc exists**: prevent accidental use of the broken numbers in any paper-table generation script.

---

## What's broken

| Path on instance | Bug source | Effect |
|------------------|------------|--------|
| `ablation_full_BROKEN/` | None (this one was valid for the routing axis) | BERTScore = 0 (disk-full bug #8); accuracy numbers were OK but already superseded by the v3 re-run |
| `ablation_single_4b_BROKEN/` | Bug #4 (model_router config caching) | Configured as 4B+4B but actually ran 4B+14B (same as full). Numbers are **not a real ablation**. |
| `ablation_single_14b_BROKEN/` | Bug #4 | Configured as 14B+14B but actually ran 4B+14B. Numbers are **not a real ablation**. |
| `ablation_no_structured_BROKEN/` | Bug #4 + Bug #6 | flag `no_structured` was never wired to runner; ran identical to full. |
| (no `_no_system_prompt_BROKEN` saved) | Bug #5 | Run was killed mid-way at RCA 139/198 during bug investigation. The 12 failed-confidence cases would have lowered the score; no saved summary. |
| (no `_with_graph_BROKEN`, `_no_constitutional_BROKEN`, `_with_orchestrator_BROKEN`) | — | Never started in the broken run (killed at config 5 of 8). |

Plus:
- `ablation_single_4b_SMOKE/` — 5-case verification of the bug #4 fix (not a real ablation)
- `ablation_single_14b_SMOKE/` — 5-case verification (not a real ablation)

---

## How to verify the smoking-gun

If you ever need to confirm Bug #4 happened, the test is:

```python
import json
full = json.load(open("/mnt/aiops-repo/benchmark/results/ablation_full_BROKEN/results.json"))
s14b = json.load(open("/mnt/aiops-repo/benchmark/results/ablation_single_14b_BROKEN/results.json"))
full_by_id = {r["test_id"]: r for r in full}
s14b_by_id = {r["test_id"]: r for r in s14b}

# For ALL 202 annotation cases, the actual_output should differ between 4B (full) and 14B (s14b).
# In the broken run, they were 100% IDENTICAL because both actually ran 4B for annotation.
ann_ids = [r["test_id"] for r in full if r["task_type"]=="annotation"]
identical = sum(1 for tid in ann_ids if full_by_id[tid]["actual_output"] == s14b_by_id[tid]["actual_output"])
print(f"Identical annotation outputs (broken run): {identical}/{len(ann_ids)}")  # 202/202 in the broken run

# After fix, the smoke-test verification confirmed differing outputs.
```

This is the test we used in session 8 to diagnose the issue. The local copy of those broken runs would let anyone reproduce the diagnosis.

---

## What to do with these on the instance

- **Keep them** for now: they're the evidence trail for bug #4.
- **Do not** SCP them to local `results_aws/` unless explicitly archiving the bug investigation.
- After the v3 ablation completes and is verified, these can be deleted from the instance to free disk space (~20 GB combined). Delete only after explicit confirmation from project lead.
