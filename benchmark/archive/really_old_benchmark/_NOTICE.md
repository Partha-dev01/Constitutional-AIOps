# `really_old_benchmark/` — provenance notice

**Archived:** 2026-05-27 (session 35)
**Origin:** repo root, untracked folder named `really old benchmark/`
**Era:** **2026-02-06** (all 25 files timestamped that day)
**Status:** historical — pre-D-1, pre-current-paper, pre-431-case-benchmark

## What this is

An early-development benchmark + ablation scratch folder that lived at the constitutional-aiops repo root, untracked, since February 2026. The user moved it here in session 35 so it lives alongside other superseded artifacts under `benchmark/archive/` (e.g., `v0.9.1_jarvis_baseline/`, `run_stackA_main431_OLD_PROMPT/`).

## What's inside

- `ablation.log` (4.5 KB) — log output from an early ablation run
- `benchmark_full.log` (48.5 KB) — log output from an early end-to-end benchmark run
- `results/` (23 files) — JSON / Markdown / TeX outputs from a tiny **N=10** benchmark (5 annotation cases + 5 RCA cases), Overall accuracy 70.0%, with 4 ablation variants

  Notable: `results/paper_tables.md` reports `qwen3:4b-instruct` + `qwen3:14b` (Ollama Q4_K_M Stack A naming), Annotation 60.0% on N=5, RCA 80.0% on N=5, Overall 70.0% — **clearly distinct from the current paper's 431-case 82.4% headline**.

## Why archived rather than deleted

- The data is small (340 KB) and posed no storage cost.
- It documents the evolution of the benchmark methodology — useful as forensic context if anyone later wants to trace why the paper's evaluation looks the way it does.
- Matches the convention used by `run_stackA_main431_OLD_PROMPT/` (an earlier stack-A run that was kept for the same reason).

## Hard rules carried forward

- **READ-ONLY** from session 35 onward. Do not modify any file under this dir.
- Not part of any active pipeline (`benchmark/final/**`, `benchmark/intermediate/**`, `benchmark/scripts/**`). No script reads from here.
- Not referenced by the paper (`sn-article.tex`) or the active SUMMARY/MANIFEST docs.

## INDEX.md tally update

Net effect on `benchmark/INDEX.md` §1:

- `archive/` 207 → 233 (+26: 25 source files + 1 `_NOTICE.md`)
- `archive/` size 21.38 MB → 21.71 MB
- Repo-root untracked folder count: 1 → 0 (this folder was the only one)
- Total `benchmark/` file count: +26 (these files entered git tracking for the first time)
