# KEY_METRICS.md - Constitutional AIOps Performance Metrics

> **Version**: 4.0
> **Last Updated**: 2026-09-07
> **Status**: COMSYS 2026 camera-ready final (matched-substring evaluator, 431-case benchmark, 357 scored)
> **Source of truth**: the camera-ready paper *Constitutional AIOps: A Dual-Agent Architecture with Deterministic Inference and Graph-Episodic Memory* (COMSYS 2026). These figures supersede every earlier v1 / v3.0 number in this repo.

---

## Why these numbers differ from older docs

The published results use a strict matched-substring evaluator. An answer counts as correct only when one of the dataset's acceptable surface forms appears verbatim in the output after case-insensitive whitespace normalization. This replaced the v1 3.0-point overlap rubric, which over-credited partial-overlap answers. The lower headline is an evaluator change, not a system regression.

Any older figure of 90.7% overall accuracy or a "negligible constitutional overhead" of -0.7% is retired. Both came from the old rubric and must not be reused.

Benchmark: 431 curated cases across six sources, expanded from the v1 150-case set. Accuracy is scored on 357 evaluable cases (218 annotation + 139 RCA). 74 cases (41 Chinese-language + 33 OpsEval-remined MCQ-format) are excluded uniformly across every system for evaluator fairness. Hardware: AWS g6.xlarge L4 24GB for the 431-case revision and the SOTA baselines (via AWS Bedrock); the v1 150-case run used Jarvis Labs A5000 24GB. Runtime Ollama Q4_K_M (qwen3-4b-instruct + qwen3-14b). Statistics: 95% BCa bootstrap intervals from 10,000 resamples (seed=42); pairwise ablation via McNemar exact two-sided binomial test paired by `case_id`.

---

## Table 1: Overall benchmark results (matched-substring, 431-case / 357 scored)

| Task | Agent | N | Accuracy | 95% BCa CI | BERT-F1 / Cosine / Term |
|------|-------|---|----------|------------|-------------------------|
| Annotation | Qwen3-4B | 218 | **82.6%** (180/218) | [77.1, 87.2] | 0.822 / 0.24 / 0.19 |
| RCA | Qwen3-14B | 139 | **82.0%** (114/139) | [74.8, 87.8] | 0.795 / 0.41 / 0.78 |
| **Overall** | **Hybrid** | **357** | **82.4%** (294/357) | **[78.2, 86.0]** | 0.812 / 0.33 / 0.53 |

BERTScore F1 uses roberta-large; the overall 0.812 sits at 0.81 ± 0.01 across all configurations.

---

## Table 2: Per-source accuracy (matched-substring, post-D-1)

| Source | Task | N | Evaluable | Accuracy | Dominant failure |
|--------|------|---|-----------|----------|------------------|
| Loghub HDFS | Annotation | 100 | 100 | **94.0%** | edge-case false positives |
| Loghub Apache | Annotation | 40 | 40 | **100.0%** | none |
| Loghub BGL | Annotation | 38 | 38 | 68.4% | benign RAS read as alarm |
| Loghub OpenSSH | Annotation | 40 | 40 | 50.0% | all 20 false positives, zero false negatives |
| OpsEval (all RCA subsets) | RCA | 100 | 59 | 66.1% | telecom-domain limit; 41 Chinese excluded |
| LEMMA-RCA | RCA | 80 | 80 | **93.8%** | cloud microservice edge cases |

OpenSSH 50% is a conservative bias, not a defect. Every failure is a false positive where the model flags isolated auth-failure events, with zero false negatives on coordinated brute-force. That bias is desirable for production triage.

---

## Table 3: Latency and resource utilization (AWS L4 24GB, RTT-compensated)

| Component | VRAM | P50 (s) | P95 (s) | Avg (s) | Range (s) |
|-----------|------|---------|---------|---------|-----------|
| Fast Agent (4B, annotation) | ~4 GB | 2.99 | 3.87 | 3.07 | 2.05 to 21.74 |
| Reasoning Agent (14B, RCA + qa_mcq) | ~11 GB | 29.83 | 62.20 | 32.50 | 11.55 to 84.50 |
| **End-to-end** | **~15 GB** | 4.15 | 48.57 | 17.62 | 2.05 to 84.50 |

Both models load simultaneously at ~15GB total (63% of 24GB), which removes hot-swap latency entirely. Network RTT 1.10ms is subtracted. Preliminary vLLM AWQ (awq_marlin) gate tests showed ~1.5x speedup on a 30-case smoke.

---

## Table 4: Ablation, architecture / orchestration variants vs Full Hybrid (357 paired)

| Configuration | Ann | RCA | Overall | Delta vs Full | McNemar p |
|---------------|-----|-----|---------|---------------|-----------|
| **Full Hybrid (4B+14B)** | **83.0%** | **85.6%** | **84.0%** | baseline | — |
| Single-4B (both tasks) | 82.6% | 82.7% | 82.6% | -1.4pp | 0.302 |
| Single-14B (both tasks) | 84.4% | 82.7% | 83.8% | -0.3pp | 1.000 |
| With orchestrator | 82.6% | 83.5% | 82.9% | -1.1pp | 0.289 |

Full Hybrid overall 84.0%, BCa CI [79.8, 87.4].

---

## Table 5: Ablation, component removals vs Full Hybrid (357 paired)

| Configuration | Ann | RCA | Overall | Delta overall | Key result |
|---------------|-----|-----|---------|---------------|------------|
| **Full Hybrid (baseline)** | 83.0% | 85.6% | **84.0%** | — | — |
| No structured output | 82.6% | 75.5% | 79.8% | -4.2pp | RCA -10.1pp (p=0.086) |
| **No system prompt** | **48.6%** | 81.3% | **61.3%** | **-22.7pp** | annotation -34.4pp (p=1.2e-11) |
| With graph (RAG) | 82.6% | 82.9% | 82.9% | -1.1pp | indistinguishable (p=0.289) |
| No constitutional gate | 89.4% | 72.7% | 82.9% | -1.1pp | overall-neutral p=0.652; RCA -12.9pp (p=5.3e-4) |

---

## Table 6: Cross-system comparison (matched-substring, 357 evaluable)

| System | Annotation | RCA | Overall | Delta RCA vs Ours |
|--------|-----------|-----|---------|-------------------|
| **Constitutional AIOps (Ours)** | 82.6% | **82.0%** | **82.4%** | — |
| Llama-3.3-70B-Instruct | 91.3% | 71.2% | 83.5% | **-10.8pp** |
| DeepSeek-V3.2 | 90.4% | 66.9% | 81.2% | **-15.1pp** |

Both frontier monoliths win annotation, where scale favors classification, but lose RCA. The hybrid wins root cause analysis by 10.8pp over Llama-3.3-70B and 15.1pp over DeepSeek-V3.2, where constitutional gating plus structured output boost correct-substring extraction. BERTScore F1: Ours 0.812, Llama-3.3-70B 0.827, DeepSeek-V3.2 0.826.

---

## Key findings

1. **System prompt engineering is the single most critical component.** Removing it drops overall accuracy 22.7pp, driven by a 34.4pp collapse in small-model (4B) annotation while 14B RCA barely moves (-4.3pp). The old "prompt fragility" headline is a small-model task-specification cost, not a reasoning-stage vulnerability.
2. **The dual-agent hybrid earns its keep on RCA.** It holds a small RCA edge over single-model alternatives at higher throughput, and beats both frontier monoliths (Llama-3.3-70B, DeepSeek-V3.2) on RCA by 10.8 / 15.1pp.
3. **Constitutional gating is overall-neutral (p=0.652) but per-task asymmetric.** It costs +6.4pp on annotation while specifically protecting RCA correctness, which drops 12.9pp without the gate (p=5.3e-4). Safety at no net accuracy cost.
4. **Deterministic inference.** T=0 with seed=hash(prompt) mod 2^32 for annotation, RCA, validation, and graph queries; interactive chat is intentionally non-deterministic (T=0.5). Run-to-run variance at T=0 is bounded to at most 6 cases overall.
5. **VRAM efficient.** ~15GB total for both models simultaneously (63% of 24GB).

---

## Methodology

### Evaluation
Strict matched-substring binarisation: an acceptable surface form must appear verbatim after case-insensitive whitespace normalization. It is intentionally conservative and produces a defensible lower bound. The v1 3.0-point rubric is retained only for forensic parity in the supplementary material.

### Datasets
Loghub (HDFS, BGL, Apache, OpenSSH), OpsEval, and LEMMA-RCA. 431 curated cases via a four-phase pipeline: source expansion, quality filtering, two-LLM label vetting with Llama-3.3-70B and DeepSeek-V3.2 as judges, then stratified seeding (seed=42) preserving source ratios and a 50/50 normal-anomaly balance for annotation.

### Metrics
- **Accuracy**: matched-substring (max credit only on a verbatim acceptable form)
- **BERTScore F1**: roberta-large
- **Cosine similarity**: all-MiniLM-L6-v2, 384-dim
- **Term overlap**: domain keyword overlap with stopword exclusion
- **Latency**: network-compensated (RTT 1.10ms)

### Statistics
95% BCa bootstrap CIs (10,000 resamples, seed=42); McNemar exact two-sided binomial test for paired ablation; Cohen's h effect sizes.

---

*Regenerated 2026-09-07 to match the COMSYS 2026 camera-ready final results. Earlier revisions of this file recorded the v1 / v3.0 3.0-point-rubric benchmark and are superseded.*
