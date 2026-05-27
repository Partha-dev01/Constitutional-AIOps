# benchmark/scripts/ — Index

47 Python scripts organized into 5 sub-folders by purpose. All scripts are runnable from the repo root via `python benchmark/scripts/<subdir>/<name>.py [args]`.

```
benchmark/scripts/
├── prep/      — dataset prep + mining (9 scripts)
├── run/       — benchmark runners (6 scripts)
├── eval/      — eval / scoring / stats (10 scripts)
├── ops/       — build / archive / e2e utilities (6 scripts)
└── _dev/      — smoke / debug / one-off + foldered session-NN orphans (16 scripts)
```

Path conventions assumed (post 2026-05-20 reorg, with session-32 cleanup):

| Logical role | Path |
|---|---|
| Raw third-party datasets (gitignored) | `benchmark/raw/` |
| Processed canonical JSON datasets | `benchmark/intermediate/datasets/` (canonical paper input = `benchmark_431_seed42.json`) |
| Mining-stage candidate JSONLs | `benchmark/intermediate/candidates/` |
| Paper-ready results, manifests, methodology | `benchmark/final/` (+ subdirs `docs/`, `audit/`, `main_benchmark/`, `ablation_v4/`, `sota_baselines/`, `phase46_no_prompt/`, `infrastructure/`) |
| Historical / superseded artifacts | `benchmark/archive/` |

Status legend:
- 🟢 **active** — used in current paper-evidence workflows
- 🟡 **historical** — already executed once, kept for forensic record
- 🔵 **dev** — smoke / debug / one-off
- ★ **orphan** — session-NN one-off helper now foldered in `_dev/` (post-session-32 convention)

---

## 1. `prep/` — Dataset prep + mining (9 scripts)

| Script | Status | Purpose |
|---|---|---|
| [`prep/download_datasets.py`](prep/download_datasets.py) | 🟢 active | Download Loghub (Apache, OpenSSH, BGL, HDFS), OpsEval, LogEval, LEMMA-RCA into `benchmark/raw/`. Idempotent; skips already-present files. |
| [`prep/clean_dataset.py`](prep/clean_dataset.py) | 🟢 active | Strip dirty rows from `annotation_test.json` + `rca_test.json` → produces `annotation_clean.json` + `rca_clean.json` at `benchmark/intermediate/datasets/`. |
| [`prep/prepare_datasets.py`](prep/prepare_datasets.py) | 🟢 active | Build canonical benchmark JSONs from `benchmark/raw/` + cleaned sources → `benchmark_400_seed42.json`, `benchmark_431_seed42.json` in `benchmark/intermediate/datasets/`. |
| [`prep/fix_benchmark_dataset.py`](prep/fix_benchmark_dataset.py) | 🟡 historical | One-off fixer for the legacy `benchmark_150_seed42.json` (v1-era). |
| [`prep/remove_chinese.py`](prep/remove_chinese.py) | 🟡 historical | Detect + flag 39 Chinese-language RCA cases for the exclusion list. Output used to seed `excluded_rca_cases.json`. |
| [`prep/mine_apache.py`](prep/mine_apache.py) | 🟢 active | Template-cluster Loghub Apache 2k log into ~40 annotation candidates. Reads `benchmark/raw/loghub/apache/`, writes `benchmark/intermediate/candidates/apache_candidates.jsonl`. |
| [`prep/mine_openssh.py`](prep/mine_openssh.py) | 🟢 active | Brute-force-burst detection on Loghub OpenSSH 2k → ~40 annotation candidates at `benchmark/intermediate/candidates/openssh_candidates.jsonl`. |
| [`prep/mine_opseval.py`](prep/mine_opseval.py) | 🟢 active | Re-mine OpsEval EN for diagnostic-style RCA cases via regex pre-filter + optional LLM judge stage. Reads `benchmark/raw/opseval/data/en/`, writes `benchmark/intermediate/candidates/opseval_remine.jsonl`. |
| [`prep/vet_labels.py`](prep/vet_labels.py) | 🟢 active | Two-LLM-judge label vetting pipeline for mined candidates. Splits into Tier 0 (auto-accept) / Tier 1 (human review) / Tier 2 (audit). |

## 2. `run/` — Benchmark runners (6 scripts)

| Script | Status | Purpose |
|---|---|---|
| [`run/run_benchmark.py`](run/run_benchmark.py) | 🟢 active | Main 431-case benchmark runner for our system (Stack A Ollama or Stack B vLLM). Reads from `benchmark/intermediate/datasets/`, writes results into `benchmark/final/main_benchmark/` (or transient run dir). |
| [`run/run_ablation.py`](run/run_ablation.py) | 🟢 active | 8-config ablation study runner: full / single_4b / single_14b / no_structured / no_system_prompt / with_graph / no_constitutional / with_orchestrator. Outputs into `benchmark/final/ablation_v4/ablation_<config>/`. |
| [`run/run_sota_baselines.py`](run/run_sota_baselines.py) | 🟢 active | SOTA-baseline runner for Llama 3.3-70B + DeepSeek V3.2 via AWS Bedrock. Default dataset `benchmark/intermediate/datasets/benchmark_400_seed42.json`. |
| [`run/run_drain_baseline.py`](run/run_drain_baseline.py) | 🟢 active | Drain log-parser baseline (LogPAI drain3) — annotation only, no RCA. Traditional non-LLM SOTA comparator for Table 6. |
| [`run/run_graph_experiments.py`](run/run_graph_experiments.py) | 🟢 active | Phase 4.5 experiments — LEMMA-RCA 5-fold homogeneous-domain split + cold-start curve at N=0,20,40,60. Default output `benchmark/final/phase45_graph/`. Requires AWS instance running. |
| [`run/test_5plus5.py`](run/test_5plus5.py) | 🟢 active | Curated smoke runner (5+5 or arbitrary `--ann N --rca M`). Used as the dual-stack gate during session 4. |

## 3. `eval/` — Eval / scoring / stats (10 scripts)

| Script | Status | Purpose |
|---|---|---|
| [`eval/evaluate_results.py`](eval/evaluate_results.py) | 🟡 historical | v1-era multi-metric evaluator (exact match + BERTScore + partial match). Superseded by matched-eval + Phase 5 stats pipeline. |
| [`eval/rescore_ours_with_sota_eval.py`](eval/rescore_ours_with_sota_eval.py) | 🟢 active | Re-scores our system's outputs through SOTA's strict-substring eval. Reads `_eval_annotation` + `_eval_rca` from `run/run_sota_baselines.py`. Source of the `results_sota_eval_431.json` files in `benchmark/final/`. |
| [`eval/inspect_all_configs.py`](eval/inspect_all_configs.py) | 🟢 active | Cross-config audit: runner.py rich-eval vs SOTA strict-substring. Surfaces the two eval pathologies (over-credit + under-credit). Reads `benchmark/final/ablation_v4/`. |
| [`eval/inspect_single4b.py`](eval/inspect_single4b.py) | 🟡 historical | One-off diagnostic for the 99.1% single_4b RCA anomaly that flagged the rule_score over-credit bug. |
| [`eval/phase5_stats.py`](eval/phase5_stats.py) | 🟢 active | Computes BCa 95% CI + McNemar paired p + Cohen's h vs Full for every ablation config + main re-run. Writes `phase5_stats.{json,md}` into `benchmark/final/ablation_v4/` + `benchmark/final/main_benchmark/`. |
| [`eval/verify_authoritative_numbers.py`](eval/verify_authoritative_numbers.py) | 🟢 active | Independent recompute of all headline numbers directly from source JSONs. Sanity check — no assumptions. Reads `benchmark/final/`. Used as Stage G + Stage J verification gate. |
| [`eval/compile_results.py`](eval/compile_results.py) | 🟢 active | Generates Markdown + LaTeX SOTA summary table from per-system JSONLs. Reads `benchmark/archive/originals_2026-05-19/` (the original SCP locations). Used to produce paper Table 6 (SOTA comparison). |
| [`eval/compute_semantic_metrics.py`](eval/compute_semantic_metrics.py) | 🟢 active | Post-processor that adds BERTScore + cosine similarity columns to a results JSON. Only used on `results_merged.json`-format files. |
| [`eval/export_metrics.py`](eval/export_metrics.py) | 🟢 active | Exports benchmark numbers in LaTeX / Markdown / JSON formats for paper tables. ONLY uses measured data — no fabrication. |
| [`eval/recompute_bert_f1.py`](eval/recompute_bert_f1.py) | 🟢 active | Independent BERT-F1 recompute (D-6 audit) across all 14 paper-evidence result files. Uses `roberta-large` on matched cases; writes `_bert_f1_recompute_summary.json`. Added session 18. |

## 4. `ops/` — Build / archive / e2e utilities (6 scripts)

| Script | Status | Purpose |
|---|---|---|
| [`ops/build_final_results.py`](ops/build_final_results.py) | 🟡 historical | Built the original `FINAL/` mirror with SHA verification + per-file audit. Now reads from `benchmark/archive/originals_2026-05-19/` post-reorg. |
| [`ops/archive_originals.py`](ops/archive_originals.py) | 🟡 historical | Zip-and-archive script. Executed once on 2026-05-19; outputs now at `benchmark/archive/originals_2026-05-19/` and `benchmark/archive/originals_backup_2026-05-19.zip`. |
| [`ops/master_backup_manifest.py`](ops/master_backup_manifest.py) | 🟢 active | Generates pre-zip SHA-256 manifest of every file under `benchmark/`. Output: `benchmark/final/audit/MASTER_BACKUP_MANIFEST_<date>.json`. |
| [`ops/e2e_tests.py`](ops/e2e_tests.py) | 🟢 active | End-to-end smoke wrapper that imports `BenchmarkRunner` + `LatencyCompensatedClient` + `export_metrics` and exercises them as a single pipeline check. |
| [`ops/_idx_build.py`](ops/_idx_build.py) | ★ 🔵 orphan-build-helper | Session-16 INDEX.md build helper. Reads `MASTER_BACKUP_MANIFEST_2026-05-20.json` + walks tree; emits mapping rules. Hardcoded absolute paths; one-laptop lock-in. |
| [`ops/_idx_render.py`](ops/_idx_render.py) | ★ 🔵 orphan-build-helper | Companion to `_idx_build.py`; renders the partition-tally table. Hardcoded absolute paths. |

## 5. `_dev/` — Smoke / debug / dev + session-NN orphans (16 scripts) — 🔵 / ★

### 5.1 Smoke / debug / dev runners (5 scripts)

| Script | Status | Purpose |
|---|---|---|
| [`_dev/demo_test.py`](_dev/demo_test.py) | 🔵 dev | 30-sample (15+15) demo runner with verbose debug output. Pre-cursor to `run/test_5plus5.py`. |
| [`_dev/smoke_knowledge_query.py`](_dev/smoke_knowledge_query.py) | 🔵 dev | 3-case smoke verifying the post-fix `RCA_SYSTEM_PROMPT` no longer refuses knowledge queries. Used as the post-prompt-fix sanity check on 2026-05-16. |
| [`_dev/test_instruct.py`](_dev/test_instruct.py) | 🔵 dev | Single-sample verification of `qwen3:4b-instruct` connectivity + content-vs-reasoning field check + determinism (run-twice). |
| [`_dev/debug_connection.py`](_dev/debug_connection.py) | 🔵 dev | Layer-by-layer pipeline debugger: raw httpx → ModelRouter → FastAnnotator → ReasoningAgent. Includes Qwen3 thinking-mode behavior probe. |
| [`_dev/create_nothink_model.py`](_dev/create_nothink_model.py) | 🟡 historical | Jarvis-Labs-era utility that created a custom `qwen3-4b-nothink` Ollama model by stripping `<think>` from the template. Obsolete on AWS (use `enable_thinking=False` in `chat_template_kwargs` instead — but Ollama 0.23.2 ignores that flag; see [`project_thinking_mode_audit_logging.md`](../../../.claude/projects/c--Users-partha-Downloads-files-AIOPS-NEW/memory/project_thinking_mode_audit_logging.md)). |

### 5.2 Session-NN orphan helpers (11 scripts)

All foldered here via Phase 5 Topology Option A (session 32). Each is a self-contained one-off with no cross-script imports. Convention: underscore-prefix → `_dev/`.

| Script | Status | Session | Purpose |
|---|---|---|---|
| [`_dev/_apply_d1_result_sync.py`](_dev/_apply_d1_result_sync.py) | ★ historical | 17/18 | D-1 re-label applier — propagates the corrected 74-case exclusion across 16 result files in `benchmark/final/`. |
| [`_dev/_compute_sota_post_relabel.py`](_dev/_compute_sota_post_relabel.py) | ★ historical | 17/18 | D-1 verification stats — recomputes SOTA accuracy post-re-label. |
| [`_dev/_probe_format.py`](_dev/_probe_format.py) | ★ historical | 17 | Byte-level probe of result file format before D-1 re-apply. |
| [`_dev/_probe_format2.py`](_dev/_probe_format2.py) | ★ historical | 17 | Round-trip probe (idempotency check) for D-1 re-apply. |
| [`_dev/_verify_a2_apply.py`](_dev/_verify_a2_apply.py) | ★ historical | 18 | Structural diff vs git HEAD for D-1 re-applied files. |
| [`_dev/_verify_d1_relabel.py`](_dev/_verify_d1_relabel.py) | ★ historical | 17/18 | Byte-diff verifier for the D-1 re-label sweep. |
| [`_dev/_session21_latency_e2e_no_qa.py`](_dev/_session21_latency_e2e_no_qa.py) | ★ historical | 21 | End-to-end latency stat re-derivation excluding QA cases. Hardcoded Windows path; one-laptop lock-in. |
| [`_dev/_session21_latency_pcts.py`](_dev/_session21_latency_pcts.py) | ★ historical | 21 | Latency percentile computation for Table 4. Hardcoded Windows path. |
| [`_dev/flip_qa_mcq_correct_to_null.py`](_dev/flip_qa_mcq_correct_to_null.py) | 🟢 active | 22 | CRIT-C2 fix: restores 74-excluded-case invariant by nulling `correct` field on 33 OpsEval MCQ + 41 Chinese RCA cases across 13 result files. |
| [`_dev/group_c_relabel_d1_rich_and_header.py`](_dev/group_c_relabel_d1_rich_and_header.py) | 🟢 active | 24 | Group C D-1 audit fix: re-labels rich-eval + benchmark header `n=` value consistency. |
| [`_dev/regen_diff_pdf.py`](_dev/regen_diff_pdf.py) | 🟢 active | 21+ | Regenerates the `diff/sn-article-DIFF.tex` via latexdiff against v1 paper, applies the encoded recipe (LF write, `\providecommand{\DIFdel}[1]{}` suppression, listings dep drop, Perl on PATH). Load-bearing for every paper DIFF regen since session 21. |

## 6. Package markers

| File | Purpose |
|---|---|
| `__init__.py` (root) | Makes `benchmark.scripts` an importable Python package. |
| `prep/__init__.py`, `run/__init__.py`, `eval/__init__.py`, `ops/__init__.py`, `_dev/__init__.py` | Make each sub-folder importable (e.g. `from benchmark.scripts.run.run_benchmark import BenchmarkRunner`). |

---

## Cross-script dependencies

Important runtime imports — if any of these scripts move, the import paths must be updated:

| Importer | Importee | Mechanism |
|---|---|---|
| `eval/rescore_ours_with_sota_eval.py` | `run/run_sota_baselines.py` | `importlib.util.spec_from_file_location` (hardcoded path) |
| `ops/e2e_tests.py` | `run/run_benchmark.py` | `from benchmark.scripts.run.run_benchmark import BenchmarkRunner, MODELS, LatencyCompensatedClient` |
| `ops/e2e_tests.py` | `eval/export_metrics.py` | `from benchmark.scripts.eval.export_metrics import ...` |
| `run/run_ablation.py` | `eval/export_metrics.py` | `from benchmark.scripts.eval.export_metrics import export_all` |

If you ever move any script between sub-folders, update both the imports and the `importlib` hardcoded path simultaneously, then re-run [`eval/verify_authoritative_numbers.py`](eval/verify_authoritative_numbers.py) + [`eval/inspect_all_configs.py`](eval/inspect_all_configs.py) to confirm nothing broke.

Note: the 11 `_dev/_session*` + `_dev/_*` foldered orphans listed in §5.2 have **zero importers** — all are self-contained one-offs with hardcoded paths. Safe to move within `_dev/` without import-path edits.

## Output write-paths (where each script writes)

| Script | Writes to |
|---|---|
| `prep/download_datasets.py` | `benchmark/raw/` |
| `prep/prepare_datasets.py` | `benchmark/intermediate/datasets/` |
| `prep/clean_dataset.py` | `benchmark/intermediate/datasets/{annotation_clean,rca_clean}.json` |
| `prep/mine_apache.py` | `benchmark/intermediate/candidates/apache_candidates.jsonl` |
| `prep/mine_openssh.py` | `benchmark/intermediate/candidates/openssh_candidates.jsonl` |
| `prep/mine_opseval.py` | `benchmark/intermediate/candidates/opseval_remine.jsonl` |
| `prep/vet_labels.py` | `benchmark/intermediate/candidates/vetted/` |
| `run/run_benchmark.py` | transient run dir + `benchmark/final/main_benchmark/` (when promoted) |
| `run/run_ablation.py` | `benchmark/final/ablation_v4/ablation_<config>/` |
| `run/run_sota_baselines.py` | `benchmark/final/sota_baselines/*.jsonl` |
| `run/run_drain_baseline.py` | `benchmark/final/sota_baselines/drain.jsonl` |
| `run/run_graph_experiments.py` | `benchmark/final/phase45_graph/` |
| `eval/phase5_stats.py` | `benchmark/final/ablation_v4/phase5_stats.{json,md}` + `benchmark/final/main_benchmark/phase5_stats.json` |
| `eval/rescore_ours_with_sota_eval.py` | `<input>_sota_eval_431.json` next to source |
| `eval/compile_results.py` | stdout (or `--out <path>`) |
| `eval/export_metrics.py` | stdout (LaTeX/Markdown/JSON) |
| `eval/recompute_bert_f1.py` | `benchmark/final/_bert_f1_recompute_summary.json` |
| `ops/master_backup_manifest.py` | `benchmark/final/audit/MASTER_BACKUP_MANIFEST_<date>.json` |
| `_dev/flip_qa_mcq_correct_to_null.py` | in-place on 13 result files in `benchmark/final/*/` |
| `_dev/group_c_relabel_d1_rich_and_header.py` | in-place on 16 result files in `benchmark/final/*/` |
| `_dev/regen_diff_pdf.py` | sandbox `diff/sn-article-DIFF.tex` (outside repo) |

## Provenance

This index was created 2026-05-20 in session 13 as the cap of the 4-partition reorg. Session 14 (2026-05-24) sub-foldered the directory itself into `prep/run/eval/ops/_dev` and updated this index. Session 32 (2026-05-27) executed Phase 5 Topology Option A sub-commit A1: foldered 6 root underscore-prefix orphans (`_apply_d1_result_sync`, `_compute_sota_post_relabel`, `_probe_format`, `_probe_format2`, `_verify_a2_apply`, `_verify_d1_relabel`) into `_dev/`; documented the 5 unlisted active scripts (`eval/recompute_bert_f1.py`, `_dev/flip_qa_mcq_correct_to_null.py`, `_dev/group_c_relabel_d1_rich_and_header.py`, `_dev/regen_diff_pdf.py`, plus `ops/_idx_*` orphan-build-helpers) and 2 session-21 underscore-orphans already in `_dev/`. Catalog now lists all 47 .py scripts (was 34); each move preserved git history (R100 renames).

See also:
- [`benchmark/final/audit/REORG_PROPOSAL_2026-05-20.md`](../final/audit/REORG_PROPOSAL_2026-05-20.md) — original 4-partition reorg plan
- [`benchmark/final/audit/handoffs/SESSION_12_HANDOFF.md`](../final/audit/handoffs/SESSION_12_HANDOFF.md) — session-12 close-out
- [`benchmark/final/audit/handoffs/SESSION_13_HANDOFF.md`](../final/audit/handoffs/SESSION_13_HANDOFF.md) — Stage J broken-state + resume protocol (RESOLVED in session 14)
- [`benchmark/final/audit/paper_audit_session27_2026-05-26/07_benchmark_topology_analysis.md`](../final/audit/paper_audit_session27_2026-05-26/07_benchmark_topology_analysis.md) — Stage 5 topology analysis + Option A move plan executed in session 32
- [`benchmark/final/docs/METHODOLOGY.md`](../final/docs/METHODOLOGY.md) — evaluation methodology authoritative ref
