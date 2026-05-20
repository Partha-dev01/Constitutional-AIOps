# benchmark/scripts/ — Index

Flat directory of 34 Python scripts grouped by purpose below. All scripts are runnable from the repo root via `python benchmark/scripts/<name>.py [args]`.

Path conventions assumed (post 2026-05-20 reorg):

| Logical role | Path |
|---|---|
| Raw third-party datasets (gitignored) | `benchmark/raw/` |
| Processed canonical JSON datasets | `benchmark/intermediate/datasets/` |
| Mining-stage candidate JSONLs | `benchmark/intermediate/candidates/` |
| Paper-ready results, manifests, methodology | `benchmark/final/` (+ subdirs `docs/`, `audit/`, `main_benchmark/`, `ablation_v4/`, `sota_baselines/`, `phase46_no_prompt/`, `infrastructure/`) |
| Historical / superseded artifacts | `benchmark/archive/` |

Status legend:
- 🟢 **active** — used in current paper-evidence workflows
- 🟡 **historical** — already executed once, kept for forensic record
- 🔵 **dev** — smoke / debug / one-off

---

## 1. Dataset prep + mining (9 scripts)

| Script | Status | Purpose |
|---|---|---|
| [`download_datasets.py`](download_datasets.py) | 🟢 active | Download Loghub (Apache, OpenSSH, BGL, HDFS), OpsEval, LogEval, LEMMA-RCA into `benchmark/raw/`. Idempotent; skips already-present files. |
| [`clean_dataset.py`](clean_dataset.py) | 🟢 active | Strip dirty rows from `annotation_test.json` + `rca_test.json` → produces `annotation_clean.json` + `rca_clean.json` at `benchmark/intermediate/datasets/`. |
| [`prepare_datasets.py`](prepare_datasets.py) | 🟢 active | Build canonical benchmark JSONs from `benchmark/raw/` + cleaned sources → `benchmark_400_seed42.json`, `benchmark_431_seed42.json` in `benchmark/intermediate/datasets/`. |
| [`fix_benchmark_dataset.py`](fix_benchmark_dataset.py) | 🟡 historical | One-off fixer for the legacy `benchmark_150_seed42.json` (v1-era). |
| [`remove_chinese.py`](remove_chinese.py) | 🟡 historical | Detect + flag 39 Chinese-language RCA cases for the exclusion list. Output used to seed `excluded_rca_cases.json`. |
| [`mine_apache.py`](mine_apache.py) | 🟢 active | Template-cluster Loghub Apache 2k log into ~40 annotation candidates. Reads `benchmark/raw/loghub/apache/`, writes `benchmark/intermediate/candidates/apache_candidates.jsonl`. |
| [`mine_openssh.py`](mine_openssh.py) | 🟢 active | Brute-force-burst detection on Loghub OpenSSH 2k → ~40 annotation candidates at `benchmark/intermediate/candidates/openssh_candidates.jsonl`. |
| [`mine_opseval.py`](mine_opseval.py) | 🟢 active | Re-mine OpsEval EN for diagnostic-style RCA cases via regex pre-filter + optional LLM judge stage. Reads `benchmark/raw/opseval/data/en/`, writes `benchmark/intermediate/candidates/opseval_remine.jsonl`. |
| [`vet_labels.py`](vet_labels.py) | 🟢 active | Two-LLM-judge label vetting pipeline for mined candidates. Splits into Tier 0 (auto-accept) / Tier 1 (human review) / Tier 2 (audit). |

## 2. Benchmark runners (6 scripts)

| Script | Status | Purpose |
|---|---|---|
| [`run_benchmark.py`](run_benchmark.py) | 🟢 active | Main 431-case benchmark runner for our system (Stack A Ollama or Stack B vLLM). Reads from `benchmark/intermediate/datasets/`, writes results into `benchmark/final/main_benchmark/` (or transient run dir). |
| [`run_ablation.py`](run_ablation.py) | 🟢 active | 8-config ablation study runner: full / single_4b / single_14b / no_structured / no_system_prompt / with_graph / no_constitutional / with_orchestrator. Outputs into `benchmark/final/ablation_v4/ablation_<config>/`. |
| [`run_sota_baselines.py`](run_sota_baselines.py) | 🟢 active | SOTA-baseline runner for Llama 3.3-70B + DeepSeek V3.2 via AWS Bedrock. Default dataset `benchmark/intermediate/datasets/benchmark_400_seed42.json`. |
| [`run_drain_baseline.py`](run_drain_baseline.py) | 🟢 active | Drain log-parser baseline (LogPAI drain3) — annotation only, no RCA. Traditional non-LLM SOTA comparator for Table 7. |
| [`run_graph_experiments.py`](run_graph_experiments.py) | 🟢 active | Phase 4.5 experiments — LEMMA-RCA 5-fold homogeneous-domain split + cold-start curve at N=0,20,40,60. Default output `benchmark/final/phase45_graph/`. Requires AWS instance running. |
| [`test_5plus5.py`](test_5plus5.py) | 🟢 active | Curated smoke runner (5+5 or arbitrary `--ann N --rca M`). Used as the dual-stack gate during session 4. |

## 3. Eval / scoring / stats (9 scripts)

| Script | Status | Purpose |
|---|---|---|
| [`evaluate_results.py`](evaluate_results.py) | 🟡 historical | v1-era multi-metric evaluator (exact match + BERTScore + partial match). Superseded by matched-eval + Phase 5 stats pipeline. |
| [`rescore_ours_with_sota_eval.py`](rescore_ours_with_sota_eval.py) | 🟢 active | Re-scores our system's outputs through SOTA's strict-substring eval. Reads `_eval_annotation` + `_eval_rca` from `run_sota_baselines.py`. Source of the `results_sota_eval_431.json` files in `benchmark/final/`. |
| [`inspect_all_configs.py`](inspect_all_configs.py) | 🟢 active | Cross-config audit: runner.py rich-eval vs SOTA strict-substring. Surfaces the two eval pathologies (over-credit + under-credit). Reads `benchmark/final/ablation_v4/`. |
| [`inspect_single4b.py`](inspect_single4b.py) | 🟡 historical | One-off diagnostic for the 99.1% single_4b RCA anomaly that flagged the rule_score over-credit bug. |
| [`phase5_stats.py`](phase5_stats.py) | 🟢 active | Computes BCa 95% CI + McNemar paired p + Cohen's h vs Full for every ablation config + main re-run. Writes `phase5_stats.{json,md}` into `benchmark/final/ablation_v4/` + `benchmark/final/main_benchmark/`. |
| [`verify_authoritative_numbers.py`](verify_authoritative_numbers.py) | 🟢 active | Independent recompute of all headline numbers directly from source JSONs. Sanity check — no assumptions. Reads `benchmark/final/`. Used as Stage G verification. |
| [`compile_results.py`](compile_results.py) | 🟢 active | Generates Markdown + LaTeX SOTA summary table from per-system JSONLs. Reads `benchmark/archive/originals_2026-05-19/` (the original SCP locations). Used to produce paper Table 7. |
| [`compute_semantic_metrics.py`](compute_semantic_metrics.py) | 🟢 active | Post-processor that adds BERTScore + cosine similarity columns to a results JSON. Only used on `results_merged.json`-format files. |
| [`export_metrics.py`](export_metrics.py) | 🟢 active | Exports benchmark numbers in LaTeX / Markdown / JSON formats for paper tables. ONLY uses measured data — no fabrication. |

## 4. Build / archive utilities (4 scripts)

| Script | Status | Purpose |
|---|---|---|
| [`build_final_results.py`](build_final_results.py) | 🟡 historical | Built the original `FINAL/` mirror with SHA verification + per-file audit. Now reads from `benchmark/archive/originals_2026-05-19/` post-reorg. |
| [`archive_originals.py`](archive_originals.py) | 🟡 historical | Zip-and-archive script. Executed once on 2026-05-19; outputs now at `benchmark/archive/originals_2026-05-19/` and `benchmark/archive/originals_backup_2026-05-19.zip`. |
| [`master_backup_manifest.py`](master_backup_manifest.py) | 🟢 active | Generates pre-zip SHA-256 manifest of every file under `benchmark/`. Output: `benchmark/final/audit/MASTER_BACKUP_MANIFEST_<date>.json`. |
| [`e2e_tests.py`](e2e_tests.py) | 🟢 active | End-to-end smoke wrapper that imports `BenchmarkRunner` + `LatencyCompensatedClient` + `export_metrics` and exercises them as a single pipeline check. |

## 5. Smoke / debug / dev (5 scripts) — 🔵

| Script | Status | Purpose |
|---|---|---|
| [`demo_test.py`](demo_test.py) | 🔵 dev | 30-sample (15+15) demo runner with verbose debug output. Pre-cursor to `test_5plus5.py`. |
| [`smoke_knowledge_query.py`](smoke_knowledge_query.py) | 🔵 dev | 3-case smoke verifying the post-fix `RCA_SYSTEM_PROMPT` no longer refuses knowledge queries. Used as the post-prompt-fix sanity check on 2026-05-16. |
| [`test_instruct.py`](test_instruct.py) | 🔵 dev | Single-sample verification of `qwen3:4b-instruct` connectivity + content-vs-reasoning field check + determinism (run-twice). |
| [`debug_connection.py`](debug_connection.py) | 🔵 dev | Layer-by-layer pipeline debugger: raw httpx → ModelRouter → FastAnnotator → ReasoningAgent. Includes Qwen3 thinking-mode behavior probe. |
| [`create_nothink_model.py`](create_nothink_model.py) | 🟡 historical | Jarvis-Labs-era utility that created a custom `qwen3-4b-nothink` Ollama model by stripping `<think>` from the template. Obsolete on AWS (use `enable_thinking=False` in `chat_template_kwargs` instead — but Ollama 0.23.2 ignores that flag; see [`project_thinking_mode_audit_logging.md`](../../../.claude/projects/c--Users-partha-Downloads-files-AIOPS-NEW/memory/project_thinking_mode_audit_logging.md)). |

## 6. Package marker (1 file)

| File | Purpose |
|---|---|
| `__init__.py` | Makes `benchmark.scripts` an importable Python package (used by `e2e_tests.py` imports). |

---

## Cross-script dependencies

Important runtime imports — if any of these scripts move, the import paths must be updated:

| Importer | Importee | Mechanism |
|---|---|---|
| `rescore_ours_with_sota_eval.py` | `run_sota_baselines.py` | `importlib.util.spec_from_file_location` (hardcoded path) |
| `e2e_tests.py` | `run_benchmark.py` | `from benchmark.scripts.run_benchmark import BenchmarkRunner, MODELS, LatencyCompensatedClient` |
| `e2e_tests.py` | `export_metrics.py` | `from benchmark.scripts.export_metrics import ...` |
| `run_ablation.py` | `export_metrics.py` | `from benchmark.scripts.export_metrics import export_all` |

If you ever sub-folder this directory, update both the imports and the `importlib` hardcoded path simultaneously, then re-run [`verify_authoritative_numbers.py`](verify_authoritative_numbers.py) + [`inspect_all_configs.py`](inspect_all_configs.py) to confirm nothing broke.

## Output write-paths (where each script writes)

| Script | Writes to |
|---|---|
| `download_datasets.py` | `benchmark/raw/` |
| `prepare_datasets.py` | `benchmark/intermediate/datasets/` |
| `clean_dataset.py` | `benchmark/intermediate/datasets/{annotation_clean,rca_clean}.json` |
| `mine_apache.py` | `benchmark/intermediate/candidates/apache_candidates.jsonl` |
| `mine_openssh.py` | `benchmark/intermediate/candidates/openssh_candidates.jsonl` |
| `mine_opseval.py` | `benchmark/intermediate/candidates/opseval_remine.jsonl` |
| `vet_labels.py` | `benchmark/intermediate/candidates/vetted/` |
| `run_benchmark.py` | transient run dir + `benchmark/final/main_benchmark/` (when promoted) |
| `run_ablation.py` | `benchmark/final/ablation_v4/ablation_<config>/` |
| `run_sota_baselines.py` | `benchmark/final/sota_baselines/*.jsonl` |
| `run_drain_baseline.py` | `benchmark/final/sota_baselines/drain.jsonl` |
| `run_graph_experiments.py` | `benchmark/final/phase45_graph/` |
| `phase5_stats.py` | `benchmark/final/ablation_v4/phase5_stats.{json,md}` + `benchmark/final/main_benchmark/phase5_stats.json` |
| `rescore_ours_with_sota_eval.py` | `<input>_sota_eval_431.json` next to source |
| `master_backup_manifest.py` | `benchmark/final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json` |
| `compile_results.py` | stdout (or `--out <path>`) |
| `export_metrics.py` | stdout (LaTeX/Markdown/JSON) |

## Provenance

This index was created 2026-05-20 in session 13 as part of the sub-folder reorg of `benchmark/final/`. The directory itself remains flat (no sub-folders) — sub-foldering scripts/ adds invocation cost across docs/CI without proportional benefit. This README replaces that organizational need.

See also:
- [`benchmark/final/audit/REORG_PROPOSAL_2026-05-20.md`](../final/audit/REORG_PROPOSAL_2026-05-20.md) — original 4-partition reorg plan
- [`benchmark/final/audit/SESSION_12_HANDOFF.md`](../final/audit/SESSION_12_HANDOFF.md) — session-12 close-out
- [`benchmark/final/docs/METHODOLOGY.md`](../final/docs/METHODOLOGY.md) — evaluation methodology authoritative ref
