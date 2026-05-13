# Constitutional AIOps - All Benchmark Tables

> Generated: 2026-05-13 09:09:39 UTC
> Model: constitutional_aiops
> Source: `benchmark/results/`

## Table 1: Comprehensive Benchmark Results

| Task | Agent | N | Accuracy | BERT-F1 | Cos Sim | Term Overlap | P50 (ms) | P95 (ms) |
|------|-------|---|----------|---------|---------|--------------|----------|----------|
| Annotation | qwen3:4b-instruct | 218 | 82.6% | 0.000 | 0.000 | 0.188 | 2943 | 3814 |
| RCA | qwen3:14b | 213 | 79.3% | 0.000 | 0.000 | 0.709 | 30408 | 60624 |
| **Overall** | **Hybrid** | **431** | **81.0%** | **0.000** | **0.000** | **0.446** | **3671** | **48053** |


## Table 2: Per-Source Breakdown

| Task | Source | N | Accuracy | BERT-F1 | Cos Sim |
|------|--------|---|----------|---------|--------|
| Annotation | Loghub Apache | 40 | 100.0% | 0.000 | 0.000 |
| Annotation | Loghub Bgl | 38 | 68.4% | 0.000 | 0.000 |
| Annotation | Loghub Hdfs | 100 | 94.0% | 0.000 | 0.000 |
| Annotation | Loghub Openssh | 40 | 50.0% | 0.000 | 0.000 |
| Rca | Lemma Rca Cloud | 80 | 100.0% | 0.000 | 0.000 |
| Rca | Opseval 5G Communication | 6 | 66.7% | 0.000 | 0.000 |
| Rca | Opseval Log Analysis | 7 | 100.0% | 0.000 | 0.000 |
| Rca | Opseval Mobile Communication Network | 8 | 100.0% | 0.000 | 0.000 |
| Rca | Opseval Wired Network | 79 | 88.6% | 0.000 | 0.000 |
| Rca | Unknown | 33 | 0.0% | 0.000 | 0.000 |


## Table 3: Error Analysis

| Failure Mode | Count | Description |
|-------------|-------|-------------|
| Server/Network Error | 33 | RCA_OPSEVAL_RM_025, RCA_OPSEVAL_RM_006, RCA_OPSEVAL_RM_023, RCA_OPSEVAL_RM_020, RCA_OPSEVAL_RM_014 (+28 more) |
| ANNOTATION Incorrect (loghub_openssh) | 20 | ANN_OPENSSH_001, ANN_OPENSSH_027, ANN_OPENSSH_007, ANN_OPENSSH_010, ANN_OPENSSH_035 (+15 more) |
| BGL False Positive | 12 | ANN_122, ANN_118, ANN_142, ANN_129, ANN_135 (+7 more) |
| RCA Incorrect (opseval_Wired Network) | 9 | RCA_091, RCA_009, RCA_097, RCA_002, RCA_071 (+4 more) |
| ANNOTATION Incorrect (loghub_hdfs) | 6 | ANN_049, ANN_034, ANN_016, ANN_012, ANN_042 (+1 more) |
| RCA Incorrect (opseval_5G Communication) | 2 | RCA_067, RCA_018 |
| **Total Failures** | **82** | **82/431 = 19.0% error rate** |


---

*All values from actual benchmark runs. No fabricated or estimated data.*
