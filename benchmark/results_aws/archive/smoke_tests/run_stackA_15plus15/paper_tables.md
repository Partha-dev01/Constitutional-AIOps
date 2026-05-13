# Constitutional AIOps - Paper Tables

> Generated: 2026-05-13 06:54:09 UTC
> Model: constitutional_aiops
> Source: `benchmark/results/constitutional_aiops/results.json`

## Table 1: Comprehensive Benchmark Results

| Task | Agent | N | Accuracy | BERT-F1 | Cos Sim | Term Overlap | P50 (ms) | P95 (ms) |
|------|-------|---|----------|---------|---------|--------------|----------|----------|
| Annotation | qwen3:4b-instruct | 15 | 100.0% | 0.000 | 0.000 | 0.161 | 3466 | 9345 |
| RCA | qwen3:14b | 15 | 86.7% | 0.000 | 0.000 | 0.765 | 32719 | 84526 |
| **Overall** | **Hybrid** | **30** | **93.3%** | **0.000** | **0.000** | **0.477** | **23206** | **65961** |


## Table 2: Per-Source Breakdown

| Task | Source | N | Accuracy | BERT-F1 | Cos Sim |
|------|--------|---|----------|---------|--------|
| Annotation | Loghub Bgl | 3 | 100.0% | 0.000 | 0.000 |
| Annotation | Loghub Hdfs | 12 | 100.0% | 0.000 | 0.000 |
| Rca | Lemma Rca Cloud | 7 | 100.0% | 0.000 | 0.000 |
| Rca | Opseval 5G Communication | 1 | 100.0% | 0.000 | 0.000 |
| Rca | Opseval Mobile Communication Network | 2 | 100.0% | 0.000 | 0.000 |
| Rca | Opseval Wired Network | 5 | 60.0% | 0.000 | 0.000 |


## Table 3: Error Analysis

| Failure Mode | Count | Description |
|-------------|-------|-------------|
| RCA Incorrect (opseval_Wired Network) | 2 | RCA_060, RCA_002 |
| **Total Failures** | **2** | **2/30 = 6.7% error rate** |


---

*All values from actual benchmark runs. No fabricated or estimated data.*
