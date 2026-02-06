# Dataset Pipeline

> **Version**: 1.0
> **Last Updated**: 2026-02-06
> **Final Dataset**: `benchmark/datasets/processed/benchmark_150_seed42.json`

---

## Overview

The benchmark dataset is built from 3 public sources through a multi-stage pipeline:

```
Raw Sources (383 cases)
  ├── Loghub HDFS (100 annotation)
  ├── Loghub BGL (100 annotation)
  ├── OpsEval EN (100 RCA QA)
  └── LEMMA-RCA (83 RCA incidents)
       │
       ▼ prepare_datasets.py
annotation_test.json (200) + rca_test.json (183)
       │
       ▼ clean_dataset.py
annotation_clean.json (138) + rca_clean.json (180)
       │
       ▼ seed=42 sampling (prepare_datasets.py)
benchmark_150_seed42.json (100 ann + 50 rca)
       │
       ▼ remove_chinese.py
benchmark_150_seed42.json (all English, 150 cases)
       │
       ▼ runner.py + evaluator.py
results.json (per-test with 4 metrics)
```

---

## Stage 1: Raw Data Sources

### 1a. Loghub HDFS (Annotation)

- **Source**: [Loghub](https://github.com/logpai/loghub) - HDFS log dataset
- **Location**: `benchmark/datasets/raw/loghub/` (Parquet files)
- **Content**: Hadoop Distributed File System logs with labeled anomalies
- **Count**: 100 annotation test cases
- **Labels**: `anomaly_detected` (bool), `severity`, `category` (normal/error)
- **Script**: `download_datasets.py` fetches via HuggingFace datasets API

### 1b. Loghub BGL (Annotation)

- **Source**: [Loghub](https://github.com/logpai/loghub) - BlueGene/L supercomputer log dataset
- **Location**: `benchmark/datasets/raw/loghub/` (Parquet files)
- **Content**: BlueGene/L RAS (Reliability, Availability, Serviceability) logs
- **Count**: 100 annotation test cases
- **Labels**: Same schema as HDFS
- **Note**: BGL logs contain alarming keywords (e.g., "fatal", "machine check") in normal operations, causing 11 false positives in benchmark

### 1c. OpsEval (RCA)

- **Source**: [OpsEval](https://github.com/NetManAIOps/OpsEval-Datasets) benchmark
- **Location**: `benchmark/datasets/raw/opseval/data/en/`
- **Content**: Multiple-choice QA on operational knowledge (5G, Huawei Cloud, Network, etc.)
- **Count**: 100 English RCA test cases (dev + test splits)
- **Labels**: `expected_root_cause`, `acceptable_answers[]`, `choices[]`
- **Note**: Contains both English and Chinese subsets; only English used

### 1d. LEMMA-RCA (RCA)

- **Source**: [LEMMA-RCA](https://huggingface.co/datasets/lemma-rca/LEMMA-RCA) on HuggingFace
- **Location**: `benchmark/datasets/raw/lemma_rca/`
- **Content**: Real-world incident reports with root cause annotations
- **Count**: 83 RCA incident cases
- **Labels**: `expected_root_cause`, `acceptable_answers[]`, incident metadata
- **Script**: `download_datasets.py` fetches via HuggingFace `datasets` library

---

## Stage 2: Preparation (`prepare_datasets.py`)

**Script**: `benchmark/scripts/prepare_datasets.py`

Converts raw data into a standardized test case format:

### Annotation Test Case Schema
```json
{
  "id": "ANN_001",
  "task_type": "annotation",
  "source": "loghub_hdfs",
  "input": {
    "log_line": "...",
    "source": "hdfs",
    "timestamp": "..."
  },
  "expected": {
    "anomaly_detected": true,
    "severity": "high",
    "category": "error"
  }
}
```

### RCA Test Case Schema
```json
{
  "id": "RCA_001",
  "task_type": "rca",
  "source": "opseval",
  "incident": {
    "title": "...",
    "severity": "high",
    "logs": ["..."],
    "question": "...",
    "choices": ["A", "B", "C", "D"]
  },
  "expected_root_cause": "...",
  "acceptable_answers": ["...", "..."]
}
```

**Output**:
- `benchmark/datasets/processed/annotation_test.json` (200 cases)
- `benchmark/datasets/processed/rca_test.json` (183 cases)

---

## Stage 3: Cleaning (`clean_dataset.py`)

**Script**: `benchmark/scripts/clean_dataset.py`

Removes cases with quality issues:
- Missing required fields
- Empty log lines or descriptions
- Duplicate entries
- Malformed JSON in expected outputs

**Output**:
- `benchmark/datasets/processed/annotation_clean.json` (138 cases, 62 removed)
- `benchmark/datasets/processed/rca_clean.json` (180 cases, 3 removed)

---

## Stage 4: Sampling (seed=42)

**Script**: `benchmark/scripts/prepare_datasets.py` (sampling phase)

Selects the final 150 cases using `random.seed(42)` for reproducibility:
- 100 annotation cases sampled from 138 clean annotation cases
- 50 RCA cases sampled from 180 clean RCA cases

**Output**: `benchmark/datasets/processed/benchmark_150_seed42.json`

---

## Stage 5: Chinese Removal (`remove_chinese.py`)

**Script**: `benchmark/scripts/remove_chinese.py`

Some OpsEval cases contain Chinese text. This stage:
1. Identifies Chinese RCA cases via CJK Unicode detection (`\u4e00-\u9fff`)
2. Removes them from the benchmark
3. Replaces with English-only cases from the `rca_clean.json` pool (seed=42)
4. Ensures `task_type: "rca"` is set on all replacements

**Bug fixed (2026-02-06)**: Replacement cases were added without `task_type` field, causing 17 of 50 RCA cases to be silently skipped by the runner. Fixed in `fix_benchmark_dataset.py`.

**Output**: `benchmark/datasets/processed/benchmark_150_seed42.json` (updated in-place)
**Backup**: `benchmark/datasets/processed/benchmark_150_seed42_with_chinese.json`

---

## Stage 6: Benchmark Execution (`runner.py`)

**Module**: `src/benchmark/runner.py`

Runs each test case through the production agents:
- Annotation tests use `FastAnnotator` (Qwen3-4B-instruct)
- RCA tests use `ReasoningAgent` (Qwen3-14B)

Each test produces a `TestCaseResult` with:
- `correct` (bool) + `rule_score` (float 0-3)
- `inference_latency_ms`, `total_latency_ms`
- `actual_output`, `expected_output`

See [SCORING_METHODOLOGY.md](SCORING_METHODOLOGY.md) for the scoring rubric.

---

## Stage 7: Multi-Metric Evaluation (`evaluator.py`)

**Module**: `src/benchmark/evaluator.py`

Post-processing step that enriches each test result with:

| Metric | Model | Description |
|--------|-------|-------------|
| `rule_score` | N/A | Rule-based rubric (0-3 pts, from runner) |
| `bert_f1` | `microsoft/deberta-xlarge-mnli` | BERTScore F1 (token-level semantic similarity) |
| `cosine_similarity` | `all-MiniLM-L6-v2` | Sentence embedding cosine similarity |
| `term_overlap` | N/A | Normalized keyword overlap (stop-words removed) |

**Output**: `benchmark/results/{model_name}/results.json` (per-test with all 4 metrics)

---

## Final Dataset Statistics

| Stage | Annotation | RCA | Total |
|-------|-----------|-----|-------|
| Raw sources | 200 | 183 | 383 |
| After cleaning | 138 | 180 | 318 |
| Benchmark (seed=42) | 100 | 50 | 150 |
| After Chinese removal | 100 | 50 | 150 |

---

## Reproducibility

All random operations use `seed=42`:
- Dataset sampling in `prepare_datasets.py`
- Chinese replacement selection in `remove_chinese.py`
- Inference uses `temperature=0.0` + `seed=hash(prompt) % 2^32`

To reproduce the dataset from scratch:
```bash
python benchmark/scripts/download_datasets.py
python benchmark/scripts/prepare_datasets.py
python benchmark/scripts/clean_dataset.py
python benchmark/scripts/remove_chinese.py
```

To run the benchmark:
```bash
python benchmark/scripts/test_5plus5.py
# Or with subset: python benchmark/scripts/test_5plus5.py --ann=5 --rca=5
```

---

## Output Files

| File | Description |
|------|-------------|
| `benchmark/results/{model}/results.json` | Per-test results with all 4 metrics |
| `benchmark/results/{model}/summary.json` | Aggregate metrics |
| `benchmark/results/{model}/benchmark_result.json` | API-compatible summary |
| `benchmark/results/combined_results.json` | All models combined |
