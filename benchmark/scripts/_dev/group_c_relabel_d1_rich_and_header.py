"""Group C audit fixes (session 24):

1. **auditor-4 I2**: Apply D-1 re-label (33 OpsEval-remined cases: task_type rca -> qa_mcq)
   to the 8 ablation rich-eval `results.json` files. Matched-eval was relabeled in
   session 17/18; rich-eval was not. Doesn't affect paper headlines (matched-eval is
   canonical), but eliminates cross-file inconsistency for the audit.

2. **auditor-4 M4**: Update `benchmark_431_seed42.json` header fields:
   - rca_cases: 213 -> 180
   - add qa_mcq_cases: 33

Atomic writes: temp file in same dir, fsync, rename.

The 33 qa_mcq case IDs are derived from `main_benchmark/results_sota_eval_431.json`
(matched-eval, post-D-1) where task_type == 'qa_mcq'. Match against rich-eval via
`test_id` field (rich-eval uses test_id, matched-eval uses case_id; same values).
"""
import json
import os
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

MATCHED_EVAL = REPO / "benchmark" / "final" / "main_benchmark" / "results_sota_eval_431.json"
ABLATION_RICH = [
    REPO / "benchmark" / "final" / "ablation_v4" / d / "results.json"
    for d in [
        "ablation_full",
        "ablation_single_4b",
        "ablation_single_14b",
        "ablation_no_structured",
        "ablation_no_system_prompt",
        "ablation_with_graph",
        "ablation_no_constitutional",
        "ablation_with_orchestrator",
    ]
]
DATASET_HEADER = REPO / "benchmark" / "intermediate" / "datasets" / "benchmark_431_seed42.json"


def atomic_write(path: Path, payload: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def load_qa_mcq_ids() -> set:
    with MATCHED_EVAL.open(encoding="utf-8") as f:
        records = json.load(f)
    return {r["case_id"] for r in records if r.get("task_type") == "qa_mcq"}


def relabel_rich_eval(qa_ids: set, path: Path) -> int:
    with path.open(encoding="utf-8") as f:
        records = json.load(f)
    n_flipped = 0
    for r in records:
        if r.get("test_id") in qa_ids and r.get("task_type") == "rca":
            r["task_type"] = "qa_mcq"
            n_flipped += 1
    atomic_write(path, json.dumps(records, indent=2, ensure_ascii=False))
    return n_flipped


def update_dataset_header(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    before = {"rca_cases": data.get("rca_cases"), "qa_mcq_cases": data.get("qa_mcq_cases")}
    data["rca_cases"] = 180
    data["qa_mcq_cases"] = 33
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False))
    after = {"rca_cases": data.get("rca_cases"), "qa_mcq_cases": data.get("qa_mcq_cases")}
    return {"before": before, "after": after}


def main() -> None:
    qa_ids = load_qa_mcq_ids()
    print(f"qa_mcq IDs (from matched-eval): {len(qa_ids)} (expected 33)")
    total = 0
    for p in ABLATION_RICH:
        n = relabel_rich_eval(qa_ids, p)
        rel = p.relative_to(REPO).as_posix()
        print(f"  {rel}: flipped {n}")
        total += n
    print(f"total rich-eval rca->qa_mcq flips: {total} (expected: 33 * 8 = 264)")

    print()
    print("dataset header update:")
    res = update_dataset_header(DATASET_HEADER)
    print(f"  before: {res['before']}")
    print(f"  after:  {res['after']}")


if __name__ == "__main__":
    main()
