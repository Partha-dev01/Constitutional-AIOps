# Constitutional AIOps - Paper Tables

> Generated: 2026-02-06 11:00:50 UTC
> Model: constitutional_aiops
> Source: `benchmark/results/constitutional_aiops/results.json`

## Table 1: Comprehensive Benchmark Results

| Task | Agent | N | Accuracy | BERT-F1 | Cos Sim | Term Overlap | P50 (ms) | P95 (ms) |
|------|-------|---|----------|---------|---------|--------------|----------|----------|
| Annotation | qwen3:4b-instruct | 5 | 60.0% | 0.000 | 0.000 | 0.000 | 15171 | 24041 |
| RCA | qwen3:14b | 5 | 80.0% | 0.000 | 0.000 | 0.000 | 8367 | 58983 |
| **Overall** | **Hybrid** | **10** | **70.0%** | **0.000** | **0.000** | **0.000** | **14237** | **48319** |


## Table 2: Per-Source Breakdown

| Task | Source | N | Accuracy | BERT-F1 | Cos Sim |
|------|--------|---|----------|---------|--------|
| Annotation | Unknown | 5 | 60.0% | 0.000 | 0.000 |
| Rca | Unknown | 5 | 80.0% | 0.000 | 0.000 |


## Table 3: Error Analysis

| Failure Mode | Count | Description |
|-------------|-------|-------------|
| BGL False Positive | 2 | ANN_101, ANN_143 |
| RCA Incorrect (unknown) | 1 | RCA_111 |
| **Total Failures** | **3** | **3/10 = 30.0% error rate** |


---

*All values from actual benchmark runs. No fabricated or estimated data.*
