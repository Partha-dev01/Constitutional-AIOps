# Benchmark Runs Index — Constitutional AIOps v3.0

All runs stored in `/mnt/runs/<run-name>/`. Each dir contains:
- `manifest.json` — metadata, accuracy, latency
- `benchmark.log` — full stdout
- `results.json` — per-case results
- `summary.json` — aggregated metrics
- `paper_tables.tex/md` — drop-in LaTeX/markdown for paper

## Runs

### run_stackA_5plus5_oninstance (2026-05-12)
- **Stack A** | Ollama 0.23.2 | Q4_K_M
- 10/10 = 100% | ann avg 3.3s | RCA avg 31s
- ✅ Jarvis-parity baseline confirmed on AWS L4

### run_stackB_5plus5_v1_bad (2026-05-13) — INVALID
- **Stack B** | vLLM 0.9.2 | awq_marlin
- 9/10 = 90% | ann avg 30s (thinking mode bug) | RCA avg 27s
- ❌ Do NOT use — thinking mode ON for annotation (bug)

### run_stackB_5plus5_v2 (2026-05-13) ← CURRENT BASELINE
- **Stack B** | vLLM 0.9.2 | awq_marlin + thinking fix
- 10/10 = 100% | ann avg 3.4s | RCA avg 26.4s | P95 32s
- ✅ Gate 1 (accuracy delta): PASS (0pp vs Stack A)
- ⏳ Gate 2 (P95 speedup ≥1.5×): pending 15+15 confirmation

### run_stackB_15plus15 (2026-05-13) — IN PROGRESS
- **Stack B** | vLLM 0.9.2 | awq_marlin + thinking fix
- 30 cases (15 ann + 15 RCA) for gate §15 P95 comparison

---

## Next planned runs
- `run_stackA_15plus15` — Stack A 15+15 for P95 baseline (gate §15)
- `run_stackB_full_150` — Stack B full 150-case benchmark (Table 5 latency)
- `run_stackA_full_500` — Stack A full 500-case main benchmark (Tables 2-4,6)

### run_stackB_15plus15 (2026-05-13) ← GATE §15 CANDIDATE
- **Stack B** | vLLM 0.9.2 | awq_marlin + thinking fix (enable_thinking=false for 4B)
- 30/30 = 100% | ann avg 3.3s (min 2.5s, max 4.2s) | RCA avg 31.4s | P95 43.7s
- ✅ Gate 1 (accuracy delta <2pp): PASS — both 100%
- ⏳ Gate 2 (P95 speedup ≥1.5×): PENDING Stack A 15+15 for P95 baseline
- Note: RCA max 76.6s outlier (one case); typical RCA range 20-35s
