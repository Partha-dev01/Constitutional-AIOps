# WHERE ARE THE NUMBERS — authoritative source map for the paper

> **Read this before comparing any benchmark value against the paper.**
> The benchmark was re-evaluated (matched-substring, "post-D-1"). Several
> **old** result files from the 2026-05-16 rubric run still sit on disk and
> will **not** match the paper. This document says which files are current.

---

## The one rule

| Filename pattern | Status | Evaluator | RCA denom | Total denom |
|---|---|---|---|---|
| **`results_sota_eval_431.json`** | ✅ **CURRENT** | matched-substring | 139 evaluable | 357 evaluable |
| **`phase5_stats.json` / `phase5_stats.md`** | ✅ **CURRENT** (aggregated, paper-ready) | matched-substring | 139 | 357 |
| `summary.json` | ❌ STALE (2026-05-16) | 3-point rubric | 213 | 431 |
| `results.json` (in ablation dirs) | ❌ STALE rich-eval | rule_score | 213 | 431 |
| `paper_tables.md` | ❌ STALE (2026-05-16 rubric) | rule_score | 213 | 431 |

The token **`sota_eval`** in a filename = the strict matched-substring
re-evaluation the paper reports. If a file does **not** have `sota_eval` in
its name (and isn't a `phase5_stats.*`), treat it as the old run.

> ⚠️ Exception: `main_benchmark/results.json` is the original run output and
> is the **correct source for the latency table** (it carries
> `inference_latency_ms`, already RTT-compensated). Its *accuracy* `correct`
> field, however, is superseded by `results_sota_eval_431.json`.

---

## Per-table location map

All paths are relative to `benchmark/final/`.

| Paper element | Authoritative file | How to read |
|---|---|---|
| **Table 2** — main (82.6 / 82.0 / 82.4 + BCa CIs) | `main_benchmark/phase5_stats.json` | aggregated; raw source ↓ |
| Table 2 raw per-case | `main_benchmark/results_sota_eval_431.json` | 431 records |
| **Per-source error table** (HDFS/BGL/OpenSSH/OpsEval/LEMMA) | `main_benchmark/results_sota_eval_431.json` | group by `source` |
| **Tables 5a + 5b** — 8-config ablation | `ablation_v4/phase5_stats.md` (+ `.json`) | paper-ready, matches line-for-line |
| Ablation raw per-config | `ablation_v4/<config>/results_sota_eval_431.json` | 8 config dirs |
| **Table 6** — SOTA (Llama / DeepSeek) | `sota_baselines/llama_3_3_70b.jsonl`, `sota_baselines/deepseek_v3.jsonl` | Ours column = main file above |
| **Table 4** — latency (P50/P95/Avg) | `main_benchmark/results.json` | `inference_latency_ms` |
| **BERT-F1** column (0.812 / 0.822 / 0.795) | `_bert_f1_recompute_summary.json` | RCA n=122 after MIN_TEXT_LEN=15 |

The 8 ablation config dirs: `ablation_full`, `ablation_single_4b`,
`ablation_single_14b`, `ablation_no_structured`, `ablation_no_system_prompt`,
`ablation_with_graph`, `ablation_no_constitutional`, `ablation_with_orchestrator`.

---

## 431 vs 357 — why both numbers are correct

- **431** = the full curated benchmark = **218 Annotation + 213 RCA-routed**
  (180 RCA-task + 33 `qa_mcq`). This is the *corpus size*. "431-case
  benchmark" in table captions refers to this.
- **357** = the **evaluable subset** under matched-substring scoring =
  **218 Annotation + 139 RCA**. These are the cases the accuracy
  denominators count.
- The **74-case gap** = **41 Chinese-language RCA + 33 OpsEval MCQ
  (`qa_mcq`)**, excluded uniformly across *every* system (ours + both SOTA
  baselines + all 8 ablations) for evaluator fairness. They remain in the
  files for reproducibility but score `correct: null`.
- `431 − 74 = 357`.  `218 + 139 = 357`.  (This is the "D-1" invariant.)

So a table headed "431-case benchmark" with columns summing to 357 is
**consistent, not contradictory**: 431 names the corpus, 357 is what's scored.

### ⚠️ Do NOT blanket-replace 431 with 357

431 and 357 measure **different things**. Several statements would become
**factually false** if 431 were changed to 357:

| Quantity | Correct denominator | Why |
|---|---|---|
| Dataset / corpus size, data release | **431** | the curated benchmark genuinely has 431 cases |
| Inferences run, latency table | **431** | all 431 cases were executed and timed |
| "zero crashes across the run" | **431** | all 431 ran without crashing |
| Graph populated (`N=431`) | **431** | the memory graph was built from all 431 incidents |
| **Accuracy** (Tables 2, 5a, 5b, 6) | **357** (218 Ann + 139 RCA) | matched-substring scoring excludes 74 RCA cases |
| **BERT-F1** semantic column | **340** (218 Ann + 122 RCA) | extra MIN\_TEXT\_LEN=15 pairing filter on RCA |

Rule of thumb: **431 = cases *run*; 357 = cases *scored for accuracy*; 340 =
text pairs *scored for BERTScore*.** The 74 excluded cases (41 Chinese-language
RCA + 33 `qa_mcq`) still ran and still produced outputs and latency — they are
removed from *accuracy denominators only*, uniformly across all systems.

### Is 357 uniform "for all tests"?

For **accuracy**: yes — main + all 8 ablation configs + Llama-3.3-70B +
DeepSeek-V3.2 were each scored on the identical 357-case evaluable set
(218 Ann + 139 RCA), verified from raw per-case files. For **latency** the
denominator is 431 (4B row n=218, 14B row n=213, E2E n=431); for **BERT-F1**
it is 340. Different metrics legitimately use different denominators, each
disclosed in its own table footnote.

---

## How to recompute any accuracy yourself

```python
import io, json
recs = json.load(io.open(PATH, encoding="utf-8"))   # UTF-8 is REQUIRED
                                                     # (files contain Chinese text;
                                                     # plain open() throws cp1252 error)

def acc(recs, task=None):
    sel = [r for r in recs
           if (task is None or r["task_type"] == task)
           and r["correct"] is not None]             # null = excluded
    correct = sum(1 for r in sel if r["correct"] is True)
    return correct, len(sel)

# evaluable = correct is not None
# annotation -> N=218 ; rca -> N=139 ; overall (ann+rca) -> N=357
```

SOTA baselines (`sota_baselines/*.jsonl`) are JSON-lines, same record schema;
read line by line with the same UTF-8 rule.

Latency (`main_benchmark/results.json`): convert `inference_latency_ms` to
seconds (÷1000); percentiles use the **index-floor** convention
`sorted[floor(q·n)]`. Rows: 4B = `task_type=='annotation'` (n=218);
14B = `task_type in ('rca','qa_mcq')` (n=213); E2E = all 431.

---

## Verification status (2026-05-29)

Every table in `sn-article-template.v3.sandbox/main/sn-article.tex` was
recomputed from the raw per-case files above — twice (main session +
two independent agents). **All values match exactly**, including the
run-to-run variance disclosure (main RCA 114/139 = 82.0% vs ablation Full
RCA 119/139 = 85.6%; documented as temperature-0 nondeterminism in the
Table 2 / Table 5b footnotes).
