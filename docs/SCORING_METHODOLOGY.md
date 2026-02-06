# Scoring Methodology

> **Version**: 1.0
> **Last Updated**: 2026-02-06
> **Source**: `src/benchmark/runner.py` lines 529-677
> **Status**: Documents current rule-based scoring + planned multi-metric evaluation

---

## Overview

Constitutional AIOps uses a **multi-metric evaluation pipeline** to assess model performance on two task types:

1. **Annotation** (log anomaly detection + classification) — scored by the Fast Agent (Qwen3-4B-instruct)
2. **Root Cause Analysis (RCA)** — scored by the Reasoning Agent (Qwen3-14B)

Each test case produces:
- **Rule-based score** (0-3 points, pass/fail threshold at 1.5)
- **BERTScore F1** (semantic similarity via `microsoft/deberta-xlarge-mnli`)
- **Cosine similarity** (sentence embedding via `all-MiniLM-L6-v2`, 384-dim)
- **Term overlap** (normalized lexical overlap with stop-word removal)

---

## 1. Annotation Scoring Rubric

**Source**: `runner.py:_check_annotation_correct_comprehensive()` (lines 529-607)

The annotation rubric evaluates whether the Fast Agent correctly detects and classifies log anomalies. Maximum score is **3.0 points** with a **pass threshold of 1.5**.

### Primary Metrics (3.0 points)

| Component | Points | Criteria |
|-----------|--------|----------|
| **Anomaly Detection** | 1.0 | Boolean match: `actual.anomaly_detected == expected.anomaly_detected` |
| **Severity Classification** | 1.0 (full) / 0.5 (partial) | Exact match = 1.0; Adjacent severity = 0.5 |
| **Category Classification** | 1.0 (full) / 0.5 (partial) | Exact match = 1.0; Substring match = 0.5 |

### Bonus & Penalty

| Component | Points | Criteria |
|-----------|--------|----------|
| **Triplet Extraction** | +0.25 | At least 1 valid triplet with `subject`, `relation`, `object` fields |
| **Invalid Confidence** | -0.25 | Confidence score outside [0, 1] range or non-numeric |

### Severity Adjacency (Partial Credit)

The `_severity_close()` method (lines 669-677) grants 0.5 partial credit when the predicted severity is exactly one level away from the expected severity on the ordered scale:

```
info → low → warning → medium → high → critical
```

For example:
- Expected `high`, actual `critical` → **0.5 points** (adjacent)
- Expected `high`, actual `medium` → **0.5 points** (adjacent)
- Expected `high`, actual `low` → **0.0 points** (2+ levels away)

### Category Vocabulary Bridging

The scoring bridges two different vocabularies:

| Source | Categories |
|--------|-----------|
| **FastAnnotator output** | `error`, `performance`, `security`, `resource`, `unknown`, `info`, `normal` |
| **Dataset labels** | `normal`, `error` |

**Bridging logic** (lines 567-581):
- If expected = `normal` AND model detected no anomaly → any of `{unknown, performance, resource, security, info, normal}` maps to `normal`
- If expected = `error` AND model detected an anomaly → any of `{performance, security, resource, error}` maps to `error`

This prevents penalizing the model for using a more specific category (e.g., `security`) when the dataset only labels it as `error`.

### Pass Criteria

```
score >= 1.5 / 3.0 → PASS
```

A test case passes if the model gets at least the anomaly detection correct (1.0) plus either severity or category partially correct (0.5+). This means a model that detects the right anomaly but misclassifies both severity and category by more than one level will fail.

---

## 2. RCA Scoring Rubric

**Source**: `runner.py:_check_rca_correct_comprehensive()` (lines 609-667)

The RCA rubric evaluates whether the Reasoning Agent correctly identifies root causes and produces actionable analysis. Maximum score is **3.0 points** with a **pass threshold of 1.5**.

### Scoring Components

| Component | Points | Criteria |
|-----------|--------|----------|
| **Root Cause Identification** | 1.5 (full) / 1.0 (partial) | Full: any `acceptable_answer` substring found in output; Partial: `expected_root_cause` substring match |
| **Causal Chain Validity** | 0.5 | List with >= 2 entries |
| **Impact Assessment** | 0.5 | Dict with both `services` and `severity` keys |
| **Confidence Score** | 0.25 | Numeric value in [0, 1] range |
| **Remediation Steps** | 0.25 | List with >= 1 entry containing `action` key |

### Root Cause Matching (lines 631-636)

Two-tier substring matching:

1. **Full match (1.5 pts)**: Any string from `acceptable_answers[]` appears as a substring in the model's `root_cause` output (case-insensitive)
2. **Partial match (1.0 pt)**: The `expected_root_cause` string appears as a substring in the output (case-insensitive)
3. **No match (0.0 pts)**: Neither condition met

The `acceptable_answers` field in the dataset provides multiple valid phrasings. For example, a disk failure test case might accept:
```json
"acceptable_answers": ["disk failure", "disk error", "storage failure", "I/O error"]
```

### Structured Output Validation

Components 2-5 validate the **structure** of the model's JSON output, not its content. This ensures the model produces outputs compatible with the Constitutional AIOps pipeline:

- **Causal chain**: Must be a list with at least 2 steps (cause → effect)
- **Impact**: Must include affected `services` and `severity` classification
- **Remediation**: Must include at least 1 step with an `action` field

### Pass Criteria

```
score >= 1.5 / 3.0 → PASS
```

A test case passes if the model at minimum identifies the root cause correctly (1.5 or 1.0 points). A correct root cause identification alone is sufficient to pass.

---

## 3. Semantic Metrics (Post-Processing)

These metrics are computed after the benchmark run completes, using the collected `(expected, actual)` pairs.

### 3a. BERTScore F1

**Model**: `microsoft/deberta-xlarge-mnli`
**Source**: `src/benchmark/evaluator.py`

BERTScore computes token-level similarity between expected and actual outputs using contextual embeddings. We report the F1 score (harmonic mean of precision and recall).

- **Range**: [0.0, 1.0]
- **Interpretation**: > 0.85 indicates strong semantic similarity
- **Why DeBERTa**: Better calibration on technical/domain-specific text than RoBERTa

### 3b. Cosine Similarity

**Model**: `all-MiniLM-L6-v2` (384-dimensional sentence embeddings)
**Source**: `src/memory/embedding_service.py`

Sentence-level cosine similarity between the expected and actual output embeddings.

- **Range**: [-1.0, 1.0] (typically [0.0, 1.0] for similar domain text)
- **Interpretation**: > 0.70 indicates good semantic alignment
- **Why MiniLM**: Already loaded for the graph-episodic memory system (no additional VRAM cost)

### 3c. Term Overlap

Normalized lexical overlap between expected and actual outputs after tokenization and stop-word removal.

```
term_overlap = |tokens(expected) ∩ tokens(actual)| / |tokens(expected)|
```

- **Range**: [0.0, 1.0]
- **Interpretation**: Captures keyword coverage independent of phrasing
- **Normalization**: Divided by expected token count (recall-oriented)

---

## 4. Aggregate Metrics

### Per-Task Aggregation

| Metric | Formula |
|--------|---------|
| **Accuracy** | `passed_tests / total_tests * 100` |
| **Mean BERTScore F1** | `mean(bert_f1 for all tests in task)` |
| **Mean Cosine Similarity** | `mean(cosine_sim for all tests in task)` |
| **Mean Term Overlap** | `mean(term_overlap for all tests in task)` |

### Latency Metrics

| Metric | Description |
|--------|-------------|
| **avg_inference_latency_ms** | Mean model inference time (excludes network RTT) |
| **p50_latency_ms** | Median inference latency |
| **p95_latency_ms** | 95th percentile inference latency |
| **network_rtt_ms** | Round-trip time to Jarvis Labs endpoint (calibrated at start) |

### Determinism

All benchmark runs use:
- **Temperature**: 0.0
- **Seed**: `hash(prompt) % 2^32`

This ensures reproducible results across runs on the same hardware and model versions.

---

## 5. Dataset Composition

| Task | Source | Clean Pool | Benchmark (seed=42) |
|------|--------|-----------|-------------------|
| Annotation | Loghub HDFS + BGL | 138 cases | 100 cases |
| RCA | OpsEval + LEMMA-RCA | 180 cases | 50 cases |
| **Total** | | **318 cases** | **150 cases** |

See [DATASET_PIPELINE.md](DATASET_PIPELINE.md) for the full data processing flow.

---

## 6. Known Limitations

### Rule-Based Scoring Limitations

1. **Substring matching is brittle**: A model outputting "not a disk failure" would match `acceptable_answer: "disk failure"` — false positive risk
2. **No semantic understanding**: Rule-based scoring cannot recognize paraphrases (e.g., "memory leak" vs "heap exhaustion")
3. **Binary pass/fail loses granularity**: A score of 1.4 (fail) and 0.0 (fail) are treated identically
4. **Vocabulary bridging is heuristic**: The annotation category mapping assumes anomaly detection correctness as a proxy for category correctness

### Why Multi-Metric Evaluation

The semantic metrics (BERTScore, cosine similarity, term overlap) address these limitations:

| Limitation | Addressed By |
|-----------|-------------|
| Substring false positives | BERTScore (contextual similarity) |
| Paraphrase blindness | Cosine similarity (sentence-level meaning) |
| Binary loss of granularity | All 3 metrics provide continuous scores |
| Domain-specific vocabulary | Term overlap (keyword coverage) |

By reporting all 4 metrics, we provide a comprehensive view of model performance that is both reproducible (rule-based) and semantically meaningful (BERTScore + cosine + overlap).

---

## 7. Scoring Code Reference

| Method | File | Lines | Purpose |
|--------|------|-------|---------|
| `_check_annotation_correct_comprehensive()` | `runner.py` | 529-607 | Annotation 3-point rubric |
| `_check_rca_correct_comprehensive()` | `runner.py` | 609-667 | RCA 3-point rubric |
| `_severity_close()` | `runner.py` | 669-677 | Adjacent severity partial credit |
| `_calculate_bertscore()` | `evaluator.py` | 257-294 | BERTScore F1 computation |
| `compute_all_metrics()` | `evaluator.py` | (planned) | Batch multi-metric evaluation |
| `cosine_similarity()` | `embedding_service.py` | 214+ | Sentence embedding cosine similarity |
