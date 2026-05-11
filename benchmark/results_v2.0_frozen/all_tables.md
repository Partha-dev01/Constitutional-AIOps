# Constitutional AIOps - All Benchmark Tables

> Generated: 2026-02-10 14:11:30 UTC
> Model: constitutional_aiops
> Source: `benchmark/results/`

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


## Table 4: Ablation Study - Component Contributions

| Configuration | Ann Acc | RCA Acc | Overall | BERT-F1 | Cos Sim | Term Ov. | Avg Latency | Delta vs Full |
|--------------|---------|---------|---------|---------|---------|----------|-------------|---------------|
| Full System (Hybrid dual-agent baseline) | 89.0% | 98.0% | 92.0% | 0.459 | 0.308 | 0.433 | 5917ms | - |
| Single Agent - Qwen3-4B for both annotation and RCA | 89.0% | 94.0% | 90.7% | 0.457 | 0.309 | 0.401 | 6033ms | -1.3% |
| Single Agent - Qwen3-14B for both annotation and RCA | 89.0% | 88.0% | 88.7% | 0.458 | 0.306 | 0.427 | 5988ms | -3.3% |
| No Structured Output - raw text, no JSON metadata extraction | 89.0% | 96.0% | 91.3% | 0.457 | 0.302 | 0.383 | 6157ms | -0.7% |
| No System Prompt - empty system message, raw user query only | 45.0% | 92.0% | 60.7% | 0.389 | 0.288 | 0.780 | 11018ms | -31.3% |
| With Graph Context - historical episode context injected (RAG) | 89.0% | 90.0% | 89.3% | 0.454 | 0.288 | 0.335 | 6430ms | -2.7% |
| No Constitutional AI - skip validation (overhead measurement) | 89.0% | 96.0% | 91.3% | 0.457 | 0.307 | 0.420 | 6110ms | -0.7% |

> N=150 per configuration. Dataset: curated_150 (seed=42). Temperature=0.0.


---

*All values from actual benchmark runs. No fabricated or estimated data.*
