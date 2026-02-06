# Session State - Multi-Metric Benchmark v0.9.1

> **Last Updated**: 2026-02-06
> **Session**: Session 4 - Fresh Full Benchmark + Full Ablation + Auto-Export Pipeline
> **Purpose**: Track progress for context compaction recovery
> **Plan File**: `C:\Users\partha\.claude\plans\greedy-sauteeing-balloon.md`

---

## Current Task

ALL COMPLETE. Fresh full 150-test benchmark and 4-config full ablation study (150 tests each) run on Jarvis Labs with all 4 metrics populated. Auto-export pipeline generates all output files on completion.

---

## Jarvis Labs Status: ACTIVE
- Endpoint: `https://96c3f93672471.notebooks.jarvislabs.net`
- Ollama port: `6006` (OLLAMA_HOST=0.0.0.0:6006)
- Models path: `/home/.ollama/models/` (NOT /home/ollama-models)
- Models loaded: `qwen3:4b-instruct`, `qwen3:14b`
- ML deps installed: `sentence-transformers`, `bert-score`, `transformers<5.0`, `tokenizers<0.22`
- SSH: `ssh -i .ssh/jarvis_labs_key -p 11114 root@sshn.jarvislabs.ai`

---

## Session 4 Progress

### What Was Done
- [x] **Modified `export_metrics.py`** - Added `export_all()` function, `generate_ablation_table_from_json()`, `generate_combined_results_md()`, `generate_results_index()`
- [x] **Modified `test_5plus5.py`** - Auto-calls `export_all()` after `save_results()`
- [x] **Modified `run_ablation.py`** - Auto-calls `export_all()` after ablation table generation
- [x] **Cleared old results on Jarvis Labs** - Removed stale `benchmark/results/` from previous runs
- [x] **Re-uploaded code to Jarvis Labs** - Created tarball excluding raw datasets, SCP'd to Jarvis
- [x] **Ran 5+5 verification test** - 10/10 passed, auto-export working
- [x] **Ran full 150-test benchmark** - 89/100 ann, 45/50 RCA, 134/150 = 89.3%
- [x] **Ran full 4-config ablation study** - 100+50 per config, all 4 configs complete
- [x] **Copied results back to local machine** - SCP'd `benchmark/results/` from Jarvis
- [x] **Updated documentation** - SESSION_STATE, CHANGELOG, JARVIS_LABS_DEPLOYMENT, BENCHMARK, FINDINGS

---

## Full Benchmark Results (150 tests, Jarvis Labs localhost, FRESH RUN)

| Metric | Annotation | RCA | Overall |
|--------|-----------|-----|---------|
| **Accuracy** | 89/100 = **89.0%** | 45/50 = **90.0%** | 134/150 = **89.3%** |
| **BERTScore F1** | 0.516 | 0.337 | **0.456** |
| **Cosine Similarity** | 0.266 | 0.358 | **0.297** |
| **Term Overlap** | 0.178 | 0.649 | **0.364** |
| **P50 Latency** | 2082ms | 17096ms | 3124ms |
| **P95 Latency** | 4115ms | 29403ms | 23941ms |
| **Network RTT** | - | - | **2.0ms** (localhost) |

### Per-Source Breakdown
| Source | N | Accuracy | BERTScore |
|--------|---|----------|-----------|
| Loghub HDFS | 72 | 95.8% | 0.521 |
| Loghub BGL | 28 | 71.4% | 0.503 |
| LEMMA RCA Cloud | 28 | 100.0% | 0.349 |
| OpsEval Wired Network | 16 | 75.0% | 0.318 |
| OpsEval Mobile Comms | 4 | 100.0% | 0.352 |
| OpsEval 5G Comms | 2 | 50.0% | 0.294 |

### Error Analysis (16/150 = 10.7% failure rate)
| Failure Mode | Count | IDs |
|-------------|-------|-----|
| BGL False Positive | 8 | ANN_118, ANN_142, ANN_141, ANN_135, ANN_119 +3 more |
| RCA Incorrect (Wired Network) | 4 | RCA_002, RCA_040, RCA_039, RCA_046 |
| Annotation Incorrect (HDFS) | 3 | ANN_049, ANN_034, ANN_012 |
| RCA Incorrect (5G) | 1 | RCA_067 |

### Full Ablation Study Results (100+50 per config, 4 configs)
| Configuration | Ann Acc | RCA Acc | Overall | BERT-F1 | Cos Sim | Term Ov. | Avg Latency |
|--------------|---------|---------|---------|---------|---------|----------|-------------|
| Full System (4B + 14B) | 89.0% | 88.0% | 88.7% | 0.458 | 0.302 | 0.371 | 7208ms |
| Single 4B | 89.0% | 94.0% | 90.7% | 0.458 | 0.303 | 0.389 | 7250ms |
| Single 14B | 89.0% | 92.0% | 90.0% | 0.457 | 0.302 | 0.392 | 7582ms |
| No Structured | 89.0% | 92.0% | 90.0% | 0.458 | 0.303 | 0.385 | 7467ms |

---

## Auto-Export Pipeline (NEW in Session 4)

Both `test_5plus5.py` and `run_ablation.py` now auto-call `export_all()` from `export_metrics.py` after completing their runs. This generates:

| File | Description |
|------|-------------|
| `all_tables.md` / `.tex` | Combined Tables 1-4 (comprehensive, per-source, error, ablation) |
| `paper_tables.md` / `.tex` | Tables 1-3 for research paper |
| `combined_results.md` | Rendered combined_results.json as markdown |
| `results_index.md` | Index of all result files with descriptions |
| `ablation_table.md` / `.tex` | Table 4 ablation comparison |

---

## Key Bug Fixes (All Sessions)

### Session 4: Auto-Export + Format Normalization
- **Format normalization**: `_normalize_for_comparison()` in evaluator.py converts JSON metadata to natural language before BERTScore/cosine comparison
- **Auto-export pipeline**: `export_all()` generates all output files automatically
- **Tarball deployment**: Proper code transfer workflow to Jarvis Labs

### Session 3: Ablation Runner + ML Dependencies
- **Ablation "Unknown Model" Bug**: MODELS dict is module-level; must reload `src.benchmark.runner` after `src.config`
- **Jarvis Labs Localhost Detection**: Port 6006, path `/home/.ollama/models`
- **BERTScore Tokenizer Overflow**: Pin `transformers>=4.40,<5.0` and `tokenizers>=0.19,<0.22`

### Session 2: Benchmark Scoring
- 7 scoring bugs fixed (category vocab, triplet key, severity order, KeyError, parser, threshold, Chinese)
- Dataset cleaned: 17 Chinese cases removed, English replacements added
- Qwen3 thinking mode: switched to `qwen3:4b-instruct` (11.2x speedup)

---

## Files Created/Modified (Session 4)

| File | Action | Description |
|------|--------|-------------|
| `benchmark/scripts/export_metrics.py` | MODIFIED | Added `export_all()`, ablation table from JSON, combined results MD, results index |
| `benchmark/scripts/test_5plus5.py` | MODIFIED | Auto-calls `export_all()` after save_results() |
| `benchmark/scripts/run_ablation.py` | MODIFIED | Auto-calls `export_all()` after ablation table generation |
| `benchmark/results/all_tables.md` | GENERATED | Combined Tables 1-4 |
| `benchmark/results/paper_tables.md` | GENERATED | Paper-ready Tables 1-3 |
| `benchmark/results/ablation_results.json` | GENERATED | Full 4-config ablation data |
| `benchmark/results/combined_results.json` | GENERATED | Full 150-test benchmark summary |
| `benchmark/results/FINDINGS.md` | CREATED | Overall Performance analysis |
| `docs/SESSION_STATE.md` | UPDATED | This file - Session 4 results |
| `docs/CHANGELOG.md` | UPDATED | v0.9.0 + v0.9.1 entries |
| `docs/JARVIS_LABS_DEPLOYMENT.md` | UPDATED | Data transfer commands section |
| `docs/BENCHMARK.md` | UPDATED | Latest results + ablation + auto-export |

---

## Next Steps

1. **Update Research_V6.tex**: Insert real metrics into paper tables (Tables 1-4)
2. **Update KEY_METRICS.md**: Reflect final measured values
3. **Git commit**: Stage all changes as v0.9.1

---

## Previous Sessions Summary

### Session 3 (Benchmark v0.9.0 - Ablation + Jarvis Labs)
- Fixed ablation runner module reload bug
- Fixed localhost detection (port 6006, /home/.ollama/models)
- Installed ML deps on Jarvis Labs (BERTScore, sentence-transformers)
- Ran full 150-test benchmark: 88.0% overall (old run, before re-run)
- Ran 5+5 ablation study (small sample size)

### Session 2 (Benchmark v0.8.0-v0.8.1)
- 7 scoring bugs fixed in runner.py
- Qwen3 thinking mode diagnosed (THINK-001 to THINK-009)
- Switched to qwen3:4b-instruct (2.5s avg vs 19s with thinking)
- Full 133-test benchmark run: 89% ann, 87.9% RCA

### Session 1 (Graph Schema v0.6.0)
- Graph schema redesign for "hairball" fix
- SIMILAR_TO_THRESHOLD=0.75, MAX_EDGES_PER_NODE=5
- Frontend physics: charge=-800, center=0.2
