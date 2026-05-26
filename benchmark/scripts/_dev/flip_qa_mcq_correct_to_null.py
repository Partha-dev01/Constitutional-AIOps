"""Restore the 74-excluded invariant.

After the D-1 re-label (session 17/18) reclassified 33 OpsEval-remined cases as
task_type=qa_mcq, the substring re-scorer left 3 of them with correct=True/False
instead of correct=null. Audit 2026-05-26 (session 22 paper QC, finding CRIT-C2)
identified IDs RCA_OPSEVAL_RM_016/022/032 across 13 result files.

This script flips those 3 cases to correct=null in all 13 files. Headline math is
unaffected (qa_mcq routes outside the RCA denominator); the change only restores
the 74-excluded count reported in METHODOLOGY/SUMMARY/paper.

Atomic write: temp file in same dir, fsync, rename.
"""
import json
import os
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TARGET_IDS = {"RCA_OPSEVAL_RM_016", "RCA_OPSEVAL_RM_022", "RCA_OPSEVAL_RM_032"}

FILES_JSON = [
    "benchmark/final/main_benchmark/results_sota_eval_431.json",
    "benchmark/final/ablation_v4/ablation_full/results_sota_eval_431.json",
    "benchmark/final/ablation_v4/ablation_single_4b/results_sota_eval_431.json",
    "benchmark/final/ablation_v4/ablation_single_14b/results_sota_eval_431.json",
    "benchmark/final/ablation_v4/ablation_no_structured/results_sota_eval_431.json",
    "benchmark/final/ablation_v4/ablation_no_system_prompt/results_sota_eval_431.json",
    "benchmark/final/ablation_v4/ablation_with_graph/results_sota_eval_431.json",
    "benchmark/final/ablation_v4/ablation_no_constitutional/results_sota_eval_431.json",
    "benchmark/final/ablation_v4/ablation_with_orchestrator/results_sota_eval_431.json",
]
FILES_JSONL = [
    "benchmark/final/sota_baselines/llama_3_3_70b.jsonl",
    "benchmark/final/sota_baselines/deepseek_v3.jsonl",
    "benchmark/final/phase46_no_prompt/llama_noprompt_clean.jsonl",
    "benchmark/final/phase46_no_prompt/deepseek_noprompt_v2.jsonl",
]


def atomic_write(path: Path, payload: str) -> None:
    """Write payload to path atomically: tempfile in same dir, fsync, rename."""
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


def flip_json_array(path: Path) -> int:
    records = json.loads(path.read_text(encoding="utf-8"))
    flipped = 0
    for rec in records:
        if rec.get("case_id") in TARGET_IDS and rec.get("correct") is not None:
            rec["correct"] = None
            flipped += 1
    atomic_write(path, json.dumps(records, indent=2, ensure_ascii=False))
    return flipped


def flip_jsonl(path: Path) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    flipped = 0
    out = []
    for line in lines:
        if not line.strip():
            out.append(line)
            continue
        rec = json.loads(line)
        if rec.get("case_id") in TARGET_IDS and rec.get("correct") is not None:
            rec["correct"] = None
            flipped += 1
        out.append(json.dumps(rec, ensure_ascii=False))
    atomic_write(path, "\n".join(out) + "\n")
    return flipped


def main() -> None:
    total = 0
    for rel in FILES_JSON:
        n = flip_json_array(REPO / rel)
        print(f"  {rel}: flipped={n}")
        total += n
    for rel in FILES_JSONL:
        n = flip_jsonl(REPO / rel)
        print(f"  {rel}: flipped={n}")
        total += n
    print(f"\ntotal flipped: {total} (expected: 39 = 3 IDs * 13 files)")


if __name__ == "__main__":
    main()
