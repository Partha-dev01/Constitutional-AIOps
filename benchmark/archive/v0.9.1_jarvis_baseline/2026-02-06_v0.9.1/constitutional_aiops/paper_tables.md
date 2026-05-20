# Constitutional AIOps - Paper Tables

> Generated: 2026-02-06 14:53:49 UTC
> Model: constitutional_aiops
> Source: `benchmark/results/constitutional_aiops/results.json`

## Table 1: Comprehensive Benchmark Results

| Task | Agent | N | Accuracy | BERT-F1 | Cos Sim | Term Overlap | P50 (ms) | P95 (ms) |
|------|-------|---|----------|---------|---------|--------------|----------|----------|
| Annotation | qwen3:4b-instruct | 100 | 89.0% | 0.516 | 0.266 | 0.178 | 2082 | 4115 |
| RCA | qwen3:14b | 50 | 90.0% | 0.337 | 0.358 | 0.649 | 17096 | 29403 |
| **Overall** | **Hybrid** | **150** | **89.3%** | **0.456** | **0.297** | **0.364** | **3124** | **23941** |


## Table 2: Per-Source Breakdown

| Task | Source | N | Accuracy | BERT-F1 | Cos Sim |
|------|--------|---|----------|---------|--------|
| Annotation | Loghub Bgl | 28 | 71.4% | 0.503 | 0.223 |
| Annotation | Loghub Hdfs | 72 | 95.8% | 0.521 | 0.283 |
| Rca | Lemma Rca Cloud | 28 | 100.0% | 0.349 | 0.463 |
| Rca | Opseval 5G Communication | 2 | 50.0% | 0.294 | 0.221 |
| Rca | Opseval Mobile Communication Network | 4 | 100.0% | 0.352 | 0.243 |
| Rca | Opseval Wired Network | 16 | 75.0% | 0.318 | 0.222 |


## Table 3: Error Analysis

| Failure Mode | Count | Description |
|-------------|-------|-------------|
| BGL False Positive | 8 | ANN_118, ANN_142, ANN_141, ANN_135, ANN_119 (+3 more) |
| RCA Incorrect (opseval_Wired Network) | 4 | RCA_002, RCA_040, RCA_039, RCA_046 |
| ANNOTATION Incorrect (loghub_hdfs) | 3 | ANN_049, ANN_034, ANN_012 |
| RCA Incorrect (opseval_5G Communication) | 1 | RCA_067 |
| **Total Failures** | **16** | **16/150 = 10.7% error rate** |


---

*All values from actual benchmark runs. No fabricated or estimated data.*
