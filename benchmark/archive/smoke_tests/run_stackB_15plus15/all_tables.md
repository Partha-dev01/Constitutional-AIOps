# Constitutional AIOps - All Benchmark Tables

> Generated: 2026-05-13 06:33:38 UTC
> Model: constitutional_aiops
> Source: `benchmark/results/`

## Table 1: Comprehensive Benchmark Results

| Task | Agent | N | Accuracy | BERT-F1 | Cos Sim | Term Overlap | P50 (ms) | P95 (ms) |
|------|-------|---|----------|---------|---------|--------------|----------|----------|
| Annotation | qwen3-4b | 15 | 100.0% | 0.000 | 0.000 | 0.000 | 3160 | 4071 |
| RCA | qwen3-14b | 15 | 100.0% | 0.000 | 0.000 | 0.875 | 27897 | 58654 |
| **Overall** | **Hybrid** | **30** | **100.0%** | **0.000** | **0.000** | **0.875** | **12075** | **43712** |


## Table 2: Per-Source Breakdown

| Task | Source | N | Accuracy | BERT-F1 | Cos Sim |
|------|--------|---|----------|---------|--------|
| Annotation | Loghub Bgl | 3 | 100.0% | 0.000 | 0.000 |
| Annotation | Loghub Hdfs | 12 | 100.0% | 0.000 | 0.000 |
| Rca | Lemma Rca Cloud | 7 | 100.0% | 0.000 | 0.000 |
| Rca | Opseval 5G Communication | 1 | 100.0% | 0.000 | 0.000 |
| Rca | Opseval Mobile Communication Network | 2 | 100.0% | 0.000 | 0.000 |
| Rca | Opseval Wired Network | 5 | 100.0% | 0.000 | 0.000 |


## Table 3: Error Analysis

| Failure Mode | Count | Description |
|-------------|-------|-------------|
| **Total Failures** | **0** | **0/30 = 0.0% error rate** |


---

*All values from actual benchmark runs. No fabricated or estimated data.*
