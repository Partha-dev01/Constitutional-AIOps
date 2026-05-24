#!/usr/bin/env python3
"""benchmark/scripts/eval/rescore_ours_with_sota_eval.py — Path A Step 2.

Re-scores our system's per-case outputs in `results_merged.json` through the
SOTA evaluation pipeline (`_eval_annotation` and `_eval_rca` from
`run_sota_baselines.py`). Produces an eval-matched record set so the Table 7
"Ours" row uses the same scoring function as the Llama/DeepSeek rows.

NO new inference is performed. Reads existing `actual_output` and
`expected_output` strings, recomputes `correct`/`rule_score` only.

Why this exists: see `benchmark/final/docs/METHODOLOGY.md` §6.

Usage:
    python benchmark/scripts/eval/rescore_ours_with_sota_eval.py \
        --in  benchmark/archive/run_stackA_main431_OLD_PROMPT/results_merged.json \
        --out benchmark/archive/run_stackA_main431_OLD_PROMPT/results_sota_eval_431.json
"""

from __future__ import annotations
import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))


def _load_sota_eval_functions():
    """Import _eval_annotation and _eval_rca from run_sota_baselines.py without
    triggering its argparse main()."""
    spec = importlib.util.spec_from_file_location(
        "run_sota_baselines",
        str(REPO_ROOT / "benchmark" / "scripts" / "run" / "run_sota_baselines.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._eval_annotation, mod._eval_rca


def _parse_expected_annotation(expected_field):
    """results_merged.json stores expected_output as a JSON string. Parse it.
    Returns a dict with anomaly_detected / severity / category if present."""
    if isinstance(expected_field, dict):
        return expected_field
    if isinstance(expected_field, str):
        try:
            return json.loads(expected_field)
        except json.JSONDecodeError:
            return {}
    return {}


def _build_rca_case(rec):
    """SOTA's _eval_rca expects a case dict with expected_root_cause and
    optional acceptable_answers. Reconstruct from our record."""
    expected_text = rec.get("expected_output", "") or ""
    return {
        "expected_root_cause": expected_text,
        "acceptable_answers": rec.get("acceptable_answers", []),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="in_path", type=Path, required=True,
                    help="Source file (results_merged.json from main run)")
    ap.add_argument("--out", type=Path, required=True,
                    help="Output JSON file with re-scored records")
    ap.add_argument("--excluded",
                    type=Path,
                    default=REPO_ROOT / "benchmark/intermediate/datasets/excluded_rca_cases.json",
                    help="Path to excluded RCA case IDs (for inline correct=null marking)")
    args = ap.parse_args()

    eval_ann, eval_rca = _load_sota_eval_functions()

    src = json.loads(args.in_path.read_text(encoding="utf-8"))
    if isinstance(src, dict):
        src = src.get("results", src.get("test_results", src))
    if not isinstance(src, list):
        print(f"[rescore] ERROR: source must be a list of records or dict with results[]", file=sys.stderr)
        return 1

    excluded_ids: set[str] = set()
    if args.excluded.exists():
        ex = json.loads(args.excluded.read_text(encoding="utf-8"))
        excluded_ids = {item["id"] for item in ex.get("excluded_ids", [])}
    print(f"[rescore] Source: {args.in_path} ({len(src)} records)")
    print(f"[rescore] Excluded RCA: {len(excluded_ids)} IDs (will be marked correct=null)")

    out: list[dict] = []
    ann_in = ann_out = rca_eval_in = rca_eval_out = rca_excl = 0

    for rec in src:
        task_type = rec.get("task_type")
        case_id = rec.get("test_id") or rec.get("case_id")
        actual = rec.get("actual_output", "") or ""
        expected = rec.get("expected_output", "")

        new_rec = {
            "case_id": case_id,
            "task_type": task_type,
            "source": rec.get("source", ""),
            "model_response": actual[:500],
        }

        if task_type == "annotation":
            # Annotation: PRESERVE the original `correct` flag from runner.py.
            # Rationale: our annotation pipeline (FastAnnotator) produces a
            # structured `metadata` dict (anomaly_detected, severity, category)
            # which is evaluated directly via `_check_annotation_correct_comprehensive`.
            # The structured fields are NOT persisted to disk — only the NL summary
            # in `actual_output` survives. So we cannot retroactively run SOTA's
            # JSON-parse eval on our outputs.
            #
            # The original flag IS a stringent structured-field match — logically
            # equivalent to SOTA's JSON-parse-then-field-match. The only difference
            # is the parse step is unnecessary because the data was already a dict
            # in memory. Both evals check: anomaly_detected match + severity match.
            # See METHODOLOGY.md §6 for the disclosed asymmetry.
            ann_in += 1
            preserved = bool(rec.get("correct"))
            expected_dict = _parse_expected_annotation(expected)
            new_rec["correct"] = preserved
            new_rec["rule_score"] = float(rec.get("rule_score", 0.0))
            new_rec["expected"] = expected_dict
            new_rec["eval_method"] = "preserved_from_runner_structured_field_match"
            if preserved:
                ann_out += 1
        elif task_type == "rca":
            if case_id in excluded_ids:
                new_rec["correct"] = None
                new_rec["rule_score"] = None
                new_rec["skip_reason"] = "excluded_unevaluable"
                new_rec["expected_root_cause"] = expected
                rca_excl += 1
            else:
                # RCA: re-evaluate using SOTA's _eval_rca (substring match).
                # Our system's RCA response is full free-text reasoning, fully
                # compatible with SOTA's substring evaluator. This is the
                # meaningful eval-matching step.
                rca_eval_in += 1
                case_for_eval = _build_rca_case(rec)
                correct, score = eval_rca(actual, case_for_eval)
                new_rec["correct"] = bool(correct)
                new_rec["rule_score"] = round(float(score), 2)
                new_rec["expected_root_cause"] = expected
                new_rec["eval_method"] = "rescored_with_sota_eval_substring"
                if correct:
                    rca_eval_out += 1
        else:
            new_rec["correct"] = None
            new_rec["rule_score"] = None
            new_rec["unknown_task_type"] = True

        out.append(new_rec)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")

    ann_acc = (ann_out / ann_in * 100) if ann_in else 0.0
    rca_acc = (rca_eval_out / rca_eval_in * 100) if rca_eval_in else 0.0
    all_eval_in = ann_in + rca_eval_in
    all_eval_out = ann_out + rca_eval_out
    overall = (all_eval_out / all_eval_in * 100) if all_eval_in else 0.0

    print()
    print("=" * 60)
    print("  Ours (re-scored with SOTA eval)")
    print("=" * 60)
    print(f"  Annotation: {ann_out}/{ann_in} = {ann_acc:.1f}%")
    print(f"  RCA:        {rca_eval_out}/{rca_eval_in} evaluable = {rca_acc:.1f}% ({rca_excl} excluded)")
    print(f"  Overall:    {all_eval_out}/{all_eval_in} evaluable = {overall:.1f}%")
    print("=" * 60)
    print(f"[rescore] Wrote {len(out)} records -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
