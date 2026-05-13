# Constitutional AIOps - Paper Tables

> **Generated**: 2026-05-13 (Phase 4.2 final, BERTScore + cosine enriched)
> **Stack**: Stack A - Ollama Q4_K_M (qwen3:4b-instruct + qwen3:14b) on AWS g6.xlarge L4 24GB
> **Source**: benchmark/results_aws/run_stackA_main431/results_merged.json
> **Semantic metrics**: roberta-large BERTScore + all-MiniLM-L6-v2 cosine similarity

---

## Table 1: Comprehensive Benchmark Results

| Task | Agent | N | Accuracy | BERT-F1 | Cos Sim | Term Overlap | P50 (ms) | P95 (ms) |
|------|-------|---|----------|---------|---------|--------------|----------|----------|
| Annotation | qwen3:4b-instruct | 218 | 82.6% | 0.822 | 0.2041 | 0.2121 | 2,920 | 3,813 |
| RCA | qwen3:14b | 213 | 94.8% | 0.7726 | 0.3512 | 0.5259 | 30,336 | 65,595 |
| **Overall** | **Hybrid** | **431** | **88.6%** | **0.7975** | **0.2756** | **0.3314** | **4,089** | **54,343** |


## Table 2: Per-Source Breakdown

| Task | Source | N | Accuracy | BERT-F1 | Cos Sim |
|------|--------|---|----------|---------|--------|
| Annotation | Loghub Hdfs | 100 | 94.0% | 0.8292 | 0.2115 |
| Rca | Lemma-Rca Cloud | 80 | 100.0% | 0.7842 | 0.4469 |
| Rca | Opseval Wired Network | 79 | 88.6% | 0.7552 | 0.2666 |
| Annotation | Loghub Openssh | 40 | 50.0% | 0.8163 | 0.2163 |
| Annotation | Loghub Apache | 40 | 100.0% | 0.811 | 0.1365 |
| Annotation | Loghub Bgl | 38 | 68.4% | 0.8203 | 0.243 |
| Rca | Opseval-Remine Wired Network | 32 | 100.0% | 0.7923 | 0.3745 |
| Rca | Opseval Mobile Communication Network | 8 | 100.0% | 0.7796 | 0.3586 |
| Rca | Opseval Log Analysis | 7 | 100.0% | 0.7269 | 0.0704 |
| Rca | Opseval 5G Communication | 6 | 66.7% | 0.7825 | 0.252 |
| Rca | Opseval-Remine Mobile Communication Network | 1 | 100.0% | 0.7848 | 0.3399 |


## Table 3: Error Analysis

| Failure Mode | Count | Description |
|-------------|-------|-------------|
| ANNOTATION Incorrect (loghub_openssh) | 20 | ANN_OPENSSH_001, ANN_OPENSSH_027, ANN_OPENSSH_007, ANN_OPENSSH_010, ANN_OPENSSH_035 (+15 more) |
| ANNOTATION Incorrect (loghub_bgl) | 12 | ANN_122, ANN_118, ANN_142, ANN_129, ANN_135 (+7 more) |
| RCA Incorrect (opseval_Wired Network) | 9 | RCA_091, RCA_009, RCA_097, RCA_002, RCA_071 (+4 more) |
| ANNOTATION Incorrect (loghub_hdfs) | 6 | ANN_049, ANN_034, ANN_016, ANN_012, ANN_042 (+1 more) |
| RCA Incorrect (opseval_5G Communication) | 2 | RCA_067, RCA_018 |
| **Total Failures** | **49** | **49/431 = 11.4% error rate** |


---

*All values from actual benchmark runs. Semantic metrics computed on AWS L4 GPU (roberta-large BERTScore, all-MiniLM-L6-v2 cosine).*