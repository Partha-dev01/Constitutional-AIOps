# Stack comparison — Stack A (Ollama Q4_K_M) vs Stack B (vLLM AWQ awq_marlin)

## Per-task accuracy + latency

| Task | Stack | N | Correct | Accuracy | Lat avg | Lat P95 | Lat max |
|------|-------|---|---------|----------|---------|---------|---------|
| annotation | A | 15 | 15 | 100.0% | 4.61s | 9.34s | 22.42s |
| annotation | B | 15 | 15 | 100.0% | 3.32s | 4.07s | 4.16s |
| rca | A | 15 | 13 | 86.7% | 40.26s | 84.53s | 92.73s |
| rca | B | 15 | 15 | 100.0% | 31.45s | 58.65s | 76.65s |

## Overall

| Stack | Accuracy | Lat avg | Lat P95 |
|-------|----------|---------|---------|
| A Stack A (Ollama Q4_K_M) | 93.3% | 22.43s | 65.96s |
| B Stack B (vLLM AWQ awq_marlin) | 100.0% | 17.38s | 43.71s |

## Gate decisions (per REVIEWER_RESPONSE.md §15)

- **Gate 1 — Accuracy delta < 2pp**: |93.3% − 100.0%| = 6.67pp → ❌ FAIL
- **Gate 2 — P95 speedup ≥ 1.5×**: 65.96s / 43.71s = 1.51× → ✅ PASS

**Decision**: ❌ Investigate accuracy delta before full runs. Likely a setup bug.