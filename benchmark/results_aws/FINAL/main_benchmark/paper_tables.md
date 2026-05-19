# Constitutional AIOps - Paper Tables

> Generated: 2026-05-16 07:39:58 UTC
> Model: constitutional_aiops
> Source: `benchmark/results/constitutional_aiops/results.json`

## Table 1: Comprehensive Benchmark Results

| Task | Agent | N | Accuracy | BERT-F1 | Cos Sim | Term Overlap | P50 (ms) | P95 (ms) |
|------|-------|---|----------|---------|---------|--------------|----------|----------|
| Annotation | qwen3:4b-instruct | 218 | 82.6% | 0.000 | 0.243 | 0.188 | 2978 | 3865 |
| RCA | qwen3:14b | 213 | 92.5% | 0.000 | 0.413 | 0.779 | 29827 | 60509 |
| **Overall** | **Hybrid** | **431** | **87.5%** | **0.000** | **0.327** | **0.525** | **4147** | **48368** |


## Table 2: Per-Source Breakdown

| Task | Source | N | Accuracy | BERT-F1 | Cos Sim |
|------|--------|---|----------|---------|--------|
| Annotation | Loghub Apache | 40 | 100.0% | 0.000 | 0.181 |
| Annotation | Loghub Bgl | 38 | 68.4% | 0.000 | 0.228 |
| Annotation | Loghub Hdfs | 100 | 94.0% | 0.000 | 0.276 |
| Annotation | Loghub Openssh | 40 | 50.0% | 0.000 | 0.237 |
| Rca | Lemma Rca Cloud | 80 | 100.0% | 0.000 | 0.423 |
| Rca | Opseval 5G Communication | 6 | 83.3% | 0.000 | 0.343 |
| Rca | Opseval Log Analysis | 7 | 71.4% | 0.000 | 0.210 |
| Rca | Opseval Mobile Communication Network | 8 | 100.0% | 0.000 | 0.422 |
| Rca | Opseval Wired Network | 79 | 83.5% | 0.000 | 0.404 |
| Rca | Opseval Remine Mobile Communication Network | 1 | 100.0% | 0.000 | 0.245 |
| Rca | Opseval Remine Wired Network | 32 | 100.0% | 0.000 | 0.461 |


## Table 3: Error Analysis

| Failure Mode | Count | Description |
|-------------|-------|-------------|
| ANNOTATION Incorrect (loghub_openssh) | 20 | ANN_OPENSSH_001, ANN_OPENSSH_027, ANN_OPENSSH_007, ANN_OPENSSH_010, ANN_OPENSSH_035 (+15 more) |
| RCA Incorrect (opseval_Wired Network) | 13 | RCA_012, RCA_054, RCA_035, RCA_021, RCA_071 (+8 more) |
| BGL False Positive | 12 | ANN_122, ANN_118, ANN_142, ANN_129, ANN_135 (+7 more) |
| ANNOTATION Incorrect (loghub_hdfs) | 6 | ANN_049, ANN_034, ANN_016, ANN_012, ANN_042 (+1 more) |
| RCA Incorrect (opseval_Log Analysis) | 2 | RCA_011, RCA_062 |
| RCA Incorrect (opseval_5G Communication) | 1 | RCA_025 |
| **Total Failures** | **54** | **54/431 = 12.5% error rate** |


---

*All values from actual benchmark runs. No fabricated or estimated data.*
