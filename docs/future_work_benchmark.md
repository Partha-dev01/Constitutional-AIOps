# Future Work: Benchmark v3.0 — LangGraph Integration + Expanded Datasets

> **Created**: 2026-03-01
> **Status**: Planned (not yet executed)
> **Purpose**: Reference document for next benchmark run

---

## Context

Current benchmark (v2.0) uses 150 test cases from 4 datasets (Loghub HDFS, Loghub BGL, OpsEval, LEMMA-RCA). Results: 90.7% overall (89% annotation, 94% RCA). Two reasons to re-run:

1. **LangGraph orchestrator (v0.10.0) is now mandatory in production but NOT used in benchmarks.** The `use_orchestrator` flag in `BenchmarkConfig` is a stub — defined but never checked. The v2.0 benchmark used direct agent calls, bypassing the production pipeline.

2. **Expand datasets and test cases** (150 → 250+) for stronger statistical significance.

### What the LangGraph Orchestrator Changes vs Direct Calls

| Aspect | Direct Benchmark (v2.0) | LangGraph Orchestrator (Production) |
|--------|------------------------|--------------------------------------|
| Prior context to RCA | None (unless ablation) | Mandatory: annotation feeds into RCA |
| `enable_thinking` | `False` | `True` (forced) |
| Constitutional validation | None | Yes (mandatory gate) |
| Pipeline | Single agent call | Annotate → Evaluate → Reason → Validate |
| Expected RCA impact | Baseline | +1-3% from layered context |

### "No System Prompt" Ablation: Confirmed Correct

Full code path trace confirms the implementation is correct:
- `runner.py` overrides `get_system_prompt()` → returns `""`
- `fast_annotator.py:217` → `model_router.fast_completion(system_prompt="")`
- `reasoning_agent.py:432` → `model_router.reasoning_completion(system_prompt="")`
- The -31.3% accuracy drop is a valid finding.

---

## Datasets

### Currently Downloaded
| Dataset | Type | Status |
|---------|------|--------|
| Loghub HDFS | Annotation (2k logs) | Downloaded |
| Loghub BGL | Annotation (2k logs) | Downloaded |
| OpsEval | RCA (8,920+ QA) | Downloaded |
| LEMMA-RCA | RCA (5.5GB cloud) | Downloaded |

### Available But NOT Downloaded
| Dataset | Type | Size |
|---------|------|------|
| Loghub Apache | Annotation (2k logs) | ~2MB |
| Loghub Linux | Annotation (2k logs) | ~2MB |
| Loghub OpenSSH | Annotation (2k logs) | ~2MB |
| LogEval | Annotation + RCA | ~50MB |
| AnoMod | RCA (microservice) | Large (Zenodo, unreliable) |

All parsers already exist in `prepare_datasets.py` and `download_datasets.py`.

---

## Implementation Steps

### Step 1: Implement LangGraph Orchestrator in Benchmark Runner

**File: `src/benchmark/runner.py`**

1a. Add orchestrator initialization to `BenchmarkRunner.__init__()`:
```python
from src.orchestration.graph import build_incident_graph
from src.validation import ConstitutionalValidator

self.validator = ConstitutionalValidator()
self.incident_graph = build_incident_graph(
    fast_annotator=self.fast_annotator,
    reasoning_agent=self.reasoning_agent,
    validator=self.validator,
)
```

1b. Wire `use_orchestrator` flag in `run_benchmark()` — currently defined but never checked.

1c. Add `_run_rca_test_orchestrated()` method routing through LangGraph pipeline.

1d. Make orchestrator the DEFAULT for main benchmark (`use_orchestrator=True`).

**File: `benchmark/scripts/run/run_ablation.py`**
- `full` (baseline) → now uses orchestrator
- Rename `with-orchestrator` to `without-orchestrator` (direct calls = old baseline)

### Step 2: Download Additional Datasets

```bash
cd "c:/Users/partha/Downloads/files AIOPS NEW/constitutional-aiops"
python benchmark/scripts/prep/download_datasets.py --all --skip-lemma
```

### Step 3: Prepare Expanded Benchmark Dataset

```bash
python benchmark/scripts/prep/prepare_datasets.py --target 250
```

Creates `benchmark/datasets/processed/benchmark_250_seed42.json`.

### Step 4: Create results_2 Directory

```bash
mkdir -p benchmark/results_2
```

Update `test_5plus5.py` and `run_ablation.py` to output to `benchmark/results_2/`.

### Step 5: SCP to Jarvis Labs

```bash
ssh -i .ssh/jarvis_labs_key -p 11214 root@sshq.jarvislabs.ai "curl -s http://localhost:6006/api/tags | head -5"

scp -i .ssh/jarvis_labs_key -P 11214 -r \
  benchmark/scripts/ benchmark/datasets/processed/ src/ requirements.txt \
  root@sshq.jarvislabs.ai:/root/constitutional-aiops/
```

### Step 6: Run Benchmark on Jarvis Labs

```bash
ssh -i .ssh/jarvis_labs_key -p 11214 root@sshq.jarvislabs.ai
cd /root/constitutional-aiops
pip install -r requirements.txt

# Main benchmark (250 tests, ~45-60 min)
python benchmark/scripts/run/test_5plus5.py --dataset benchmark/datasets/processed/benchmark_250_seed42.json

# Ablation study (250 tests × 7+ configs, ~3-5 hours)
python benchmark/scripts/run/run_ablation.py --dataset benchmark/datasets/processed/benchmark_250_seed42.json
```

### Step 7: Retrieve Results

```bash
scp -i .ssh/jarvis_labs_key -P 11214 -r \
  root@sshq.jarvislabs.ai:/root/constitutional-aiops/benchmark/results/ \
  benchmark/results_2/

python benchmark/scripts/eval/export_metrics.py
```

### Step 8: Update Paper Tables

Update `sn-article.tex` with new 250-test results, expanded per-source table, updated ablation.

---

## Key Files

| File | Role |
|------|------|
| `benchmark/scripts/prep/download_datasets.py` | Downloads raw data (supports --all) |
| `benchmark/scripts/prep/prepare_datasets.py` | Transforms to benchmark format (supports --target N) |
| `benchmark/scripts/run/test_5plus5.py` | Runs main benchmark |
| `benchmark/scripts/run/run_ablation.py` | Runs 7-config ablation |
| `benchmark/scripts/eval/export_metrics.py` | Generates LaTeX + MD tables |
| `src/benchmark/runner.py` | Core benchmark execution engine |
| `src/benchmark/evaluator.py` | Multi-metric evaluation |
| `src/orchestration/graph.py` | LangGraph StateGraph pipeline |

---

## Verification

1. Orchestrator integration works: RCA tests go through annotate → evaluate → reason → validate
2. New dataset has 250+ cases with 5+ annotation sources
3. Benchmark completes on Jarvis Labs
4. Results are plausible (annotation ~85-90%, RCA ~90-95%)
5. Ablation reproduces system prompt finding + shows orchestrator contribution
6. All tables exported + paper updated
