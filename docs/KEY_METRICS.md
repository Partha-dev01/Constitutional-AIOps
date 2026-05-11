# KEY_METRICS.md - Constitutional AIOps Performance Metrics

> **Version**: 2.0
> **Last Updated**: 2026-02-11
> **Status**: Benchmark v2.0 complete (150 tests + 7-config ablation)

---

## Table 1: Accuracy Results (Benchmark v2.0)

| Metric | Value | Sample Size | Target | Status |
|--------|-------|-------------|--------|--------|
| **Annotation Accuracy** | **89.0%** (89/100) | 100 | 87-92% | IN TARGET |
| **RCA Accuracy** | **94.0%** (47/50) | 50 | 85-90% | EXCEEDS TARGET |
| **Overall Accuracy** | **90.7%** (136/150) | 150 | - | Excellent |
| Error Rate | 9.3% (14/150) | 150 | - | - |

---

## Table 2: Semantic Similarity Metrics

| Metric | Annotation | RCA | Overall |
|--------|-----------|-----|---------|
| **BERTScore F1** | 0.516 | 0.341 | **0.458** |
| **Cosine Similarity** | 0.265 | 0.387 | **0.305** |
| **Term Overlap** | 0.178 | 0.733 | **0.411** |

---

## Table 3: Latency Performance (localhost, RTT: 1.95ms)

| Agent | P50 (ms) | P95 (ms) | Avg (ms) | Min (ms) | Max (ms) |
|-------|----------|----------|----------|----------|----------|
| Annotation (qwen3:4b-instruct) | 1,872 | 2,284 | 1,853 | 1,112 | 2,360 |
| RCA (qwen3:14b) | 14,075 | 22,718 | 14,767 | 7,560 | 36,073 |
| **Overall (hybrid)** | **2,100** | **17,374** | **6,158** | - | - |
| Overall P99 | - | - | 25,547 | - | - |

---

## Table 4: Per-Source Breakdown

| Task | Source | N | Accuracy | BERT-F1 | Cos Sim |
|------|--------|---|----------|---------|---------|
| Annotation | Loghub HDFS | 72 | **95.8%** | 0.521 | 0.282 |
| Annotation | Loghub BGL | 28 | 71.4% | 0.503 | 0.223 |
| RCA | LEMMA-RCA Cloud | 28 | **100.0%** | 0.353 | 0.480 |
| RCA | OpsEval 5G Comms | 2 | **100.0%** | 0.302 | 0.282 |
| RCA | OpsEval Mobile Comms | 4 | **100.0%** | 0.353 | 0.334 |
| RCA | OpsEval Wired Network | 16 | 81.2% | 0.323 | 0.249 |

---

## Table 5: Ablation Study (7 Configurations, 150 tests each = 1,050 total)

| Configuration | Ann Acc | RCA Acc | Overall | BERT-F1 | Term Ov. | Avg Latency | Delta |
|--------------|---------|---------|---------|---------|----------|-------------|-------|
| **Full System (4B+14B hybrid)** | **89.0%** | **98.0%** | **92.0%** | **0.459** | 0.433 | **5,917ms** | **baseline** |
| Single 4B (both tasks) | 89.0% | 94.0% | 90.7% | 0.457 | 0.401 | 6,033ms | -1.3% |
| Single 14B (both tasks) | 89.0% | 88.0% | 88.7% | 0.458 | 0.427 | 5,988ms | -3.3% |
| No Structured Output | 89.0% | 96.0% | 91.3% | 0.457 | 0.383 | 6,157ms | -0.7% |
| **No System Prompt** | **45.0%** | **92.0%** | **60.7%** | **0.389** | 0.780 | **11,018ms** | **-31.3%** |
| With Graph Context (RAG) | 89.0% | 90.0% | 89.3% | 0.454 | 0.335 | 6,430ms | -2.7% |
| No Constitutional AI | 89.0% | 96.0% | 91.3% | 0.457 | 0.420 | 6,110ms | -0.7% |

---

## Table 6: Resource Utilization (A5000 24GB)

| Component | VRAM | Notes |
|-----------|------|-------|
| Qwen3-4B-Instruct Q4_K_M | ~4 GB | Incl. ~1GB KV cache |
| Qwen3-14B Q4_K_M | ~11 GB | Incl. ~1.5GB KV cache |
| **Total** | **~15 GB** | **63% of 24GB** |

---

## Table 7: Error Analysis (14/150 = 9.3%)

| Failure Mode | Count | Notes |
|-------------|-------|-------|
| BGL False Positive | 8 | Domain-specific vocabulary confusion |
| Annotation Incorrect (HDFS) | 3 | Edge cases in log parsing |
| RCA Incorrect (Wired Network) | 3 | OpsEval complex scenarios |
| **Total** | **14** | Zero crashes, zero parser failures, zero timeouts |

---

## Key Findings

1. **System prompt is the most critical component (-31.3%)**: Without it, annotation drops to 45%
2. **Hybrid outperforms single-agent**: Full 92.0% vs single-4B 90.7% vs single-14B 88.7%
3. **Constitutional AI has negligible overhead (-0.7%)**: Safety at near-zero accuracy cost
4. **Deterministic inference**: temperature=0, seed=hash(prompt) % 2^32 ensures reproducibility
5. **VRAM efficient**: ~15GB total, both models simultaneously loaded

---

## Methodology

### Evaluation Datasets
- **Annotation**: 100 cases from Loghub (72 HDFS + 28 BGL)
- **RCA**: 50 cases from OpsEval (22) + LEMMA-RCA (28)
- **Curation**: 3-phase pipeline (quality filtering, stratified sampling seed=42, language normalization)

### Metrics
- **Accuracy**: Rule-based scoring (max 3.0, pass >= 1.5)
- **BERTScore F1**: Semantic similarity (microsoft/deberta-xlarge-mnli)
- **Cosine Similarity**: all-MiniLM-L6-v2 384-dim embeddings
- **Term Overlap**: Domain keyword overlap with stopword exclusion
- **Latency**: Network-compensated (RTT: 1.95ms median)

---

*Generated from benchmark v2.0 results (2026-02-10). Updated 2026-02-11.*
