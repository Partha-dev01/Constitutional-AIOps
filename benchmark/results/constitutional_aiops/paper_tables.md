# Constitutional AIOps - Paper Tables

> Generated: 2026-02-10 14:11:30 UTC
> Model: constitutional_aiops
> Source: `benchmark/results/constitutional_aiops/results.json`

## Table 1: Comprehensive Benchmark Results

| Task | Agent | N | Accuracy | BERT-F1 | Cos Sim | Term Overlap | P50 (ms) | P95 (ms) |
|------|-------|---|----------|---------|---------|--------------|----------|----------|
| Annotation | qwen3:4b-instruct | 100 | 89.0% | 0.516 | 0.265 | 0.178 | 1872 | 2284 |
| RCA | qwen3:14b | 50 | 94.0% | 0.341 | 0.387 | 0.733 | 14075 | 22718 |
| **Overall** | **Hybrid** | **150** | **90.7%** | **0.458** | **0.305** | **0.411** | **2100** | **17374** |


## Table 2: Per-Source Breakdown

| Task | Source | N | Accuracy | BERT-F1 | Cos Sim |
|------|--------|---|----------|---------|--------|
| Annotation | Loghub Bgl | 28 | 71.4% | 0.503 | 0.223 |
| Annotation | Loghub Hdfs | 72 | 95.8% | 0.521 | 0.282 |
| Rca | Lemma Rca Cloud | 28 | 100.0% | 0.353 | 0.480 |
| Rca | Opseval 5G Communication | 2 | 100.0% | 0.302 | 0.282 |
| Rca | Opseval Mobile Communication Network | 4 | 100.0% | 0.353 | 0.334 |
| Rca | Opseval Wired Network | 16 | 81.2% | 0.323 | 0.249 |


## Table 3: Error Analysis

| Failure Mode | Count | Description |
|-------------|-------|-------------|
| BGL False Positive | 8 | ANN_118, ANN_142, ANN_141, ANN_135, ANN_119 (+3 more) |
| ANNOTATION Incorrect (loghub_hdfs) | 3 | ANN_049, ANN_034, ANN_012 |
| RCA Incorrect (opseval_Wired Network) | 3 | RCA_060, RCA_040, RCA_039 |
| **Total Failures** | **14** | **14/150 = 9.3% error rate** |


---

*All values from actual benchmark runs. No fabricated or estimated data.*
