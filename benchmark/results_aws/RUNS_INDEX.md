# Benchmark Results — AWS Runs Index

## Active Results (source of truth for paper)

| Dir | What | Cases | Accuracy | Use for |
|-----|------|-------|----------|---------|
| `run_stackA_main431/results_merged.json` | **Phase 4.2 main benchmark** | 431 | **88.6%** | Tables 2/3/4/6 |
| `rerun_remine33_enriched/results.json` | Remine 33 re-run | 33 | 100% | Merged into above |

> **Note on BERTScore/Cosine = 0.0**: `sentence-transformers` and `bert-score` not installed on AWS instance. Accuracy numbers are correct; semantic similarity metrics need local post-processing with `pip install sentence-transformers bert-score`.

> **Note on combined_results.md in run_stackA_main431/**: Shows pre-merge numbers (81.0% / 169/213 RCA). Use `results_merged.json` for all paper numbers.

## Pending (to be created)

| Dir | What | Cases | Status |
|-----|------|-------|--------|
| `sota_llama_3_3_70b/` | Phase 4.7 Llama 3.3 70B | 400 | Run from laptop via Bedrock ~30 min |
| `sota_deepseek_r1/` | Phase 4.7 DeepSeek R1 | 400 | Run from laptop via Bedrock ~80 min |
| `run_ablation_all/` | Phase 4.3 ablation (7 configs) | 400×7 | Run on instance overnight ~15 hrs |
| `run_phase45_graph/` | Phase 4.5 graph experiments | varies | Blocked on Phase 4.4 Neo4j population |

## Archive (`archive/`)

All intermediate verification runs. Not paper numbers.

| Location | What |
|----------|------|
| `archive/gate15_comparison.md` | Stack A vs B: A=93.3%/65.96s P95, B=100%/43.71s P95. Gate 2 PASS 1.51× |
| `archive/smoke_tests/` | All 5+5 and 15+15 smoke runs for both stacks |
