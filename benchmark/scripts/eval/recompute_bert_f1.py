"""D-6 (session 18): Recompute BERTScore F1 across the 16 FINAL/ result files.

Reads each result file, extracts (predicted, expected) text pairs per record using
schema auto-detection, computes BERTScore F1 with roberta-large on GPU (CPU fallback),
and writes back updating ONLY the `bert_f1` field. Original record schema, field
order, and (for json_list files) indent style are preserved.

Idempotent: re-running on already-populated bert_f1 fields will recompute the same
values (deterministic given fixed model + inputs).

Usage:
    python benchmark/scripts/eval/recompute_bert_f1.py                  # all files
    python benchmark/scripts/eval/recompute_bert_f1.py --file <path>    # one file
    python benchmark/scripts/eval/recompute_bert_f1.py --dry-run        # no write

Outputs:
    * Updates `bert_f1` field in 16 files
    * Writes summary to benchmark/final/_bert_f1_recompute_summary.json
"""
from __future__ import annotations
import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
BERTSCORE_MODEL = "roberta-large"

# (path, format) — format ∈ {"json_list", "jsonl"}
FILES = [
    ('benchmark/final/main_benchmark/results_sota_eval_431.json', 'json_list'),
    ('benchmark/final/main_benchmark/results.json', 'json_list'),
    ('benchmark/final/ablation_v4/ablation_full/results_sota_eval_431.json', 'json_list'),
    ('benchmark/final/ablation_v4/ablation_single_4b/results_sota_eval_431.json', 'json_list'),
    ('benchmark/final/ablation_v4/ablation_single_14b/results_sota_eval_431.json', 'json_list'),
    ('benchmark/final/ablation_v4/ablation_no_structured/results_sota_eval_431.json', 'json_list'),
    ('benchmark/final/ablation_v4/ablation_no_system_prompt/results_sota_eval_431.json', 'json_list'),
    ('benchmark/final/ablation_v4/ablation_with_graph/results_sota_eval_431.json', 'json_list'),
    ('benchmark/final/ablation_v4/ablation_no_constitutional/results_sota_eval_431.json', 'json_list'),
    ('benchmark/final/ablation_v4/ablation_with_orchestrator/results_sota_eval_431.json', 'json_list'),
    ('benchmark/final/sota_baselines/llama_3_3_70b.jsonl', 'jsonl'),
    ('benchmark/final/sota_baselines/deepseek_v3.jsonl', 'jsonl'),
    # drain.jsonl SKIPPED — outputs are boolean `predicted_anomaly`, not free text;
    # BERTScore on "True"/"False" string pairs is not a meaningful semantic comparison.
    ('benchmark/final/phase46_no_prompt/llama_noprompt_clean.jsonl', 'jsonl'),
    ('benchmark/final/phase46_no_prompt/deepseek_noprompt_v2.jsonl', 'jsonl'),
]

MIN_TEXT_LEN = 15  # skip BERT compute on trivially short pairs (binary outputs, single tokens)


def detect_text_fields(rec: dict) -> tuple[str | None, str | None]:
    """Return (predicted_field, expected_field) names that exist in this record."""
    pred_candidates = ('actual_output', 'model_response', 'predicted_anomaly', 'response')
    exp_candidates = ('expected_output', 'expected', 'expected_root_cause', 'expected_anomaly')
    pred_f = next((k for k in pred_candidates if k in rec and rec.get(k)), None)
    exp_f = next((k for k in exp_candidates if k in rec and rec.get(k) is not None), None)
    return pred_f, exp_f


def normalize_expected(value, task_type: str) -> str:
    """Flatten annotation JSON-string/dict expected to a text representation;
    leave RCA expected_root_cause / other strings as-is."""
    if value is None:
        return ''
    if isinstance(value, dict):
        if task_type == 'annotation':
            parts = []
            if value.get('anomaly_detected'):
                parts.append('anomaly detected')
            if 'severity' in value:
                parts.append(f"severity {value['severity']}")
            if 'category' in value:
                parts.append(f"category {value['category']}")
            return ' '.join(parts) if parts else json.dumps(value)
        return json.dumps(value)
    text = str(value).strip()
    if task_type == 'annotation' and text.startswith('{'):
        try:
            obj = json.loads(text)
            return normalize_expected(obj, task_type)
        except (json.JSONDecodeError, ValueError):
            pass
    return text


def normalize_predicted(value) -> str:
    if value is None:
        return ''
    return str(value).strip()


def detect_id_field(records: list) -> str:
    for k in ('case_id', 'test_id', 'id'):
        if records and k in records[0]:
            return k
    return 'case_id'


def detect_ensure_ascii(raw: bytes) -> bool:
    return all(b < 128 for b in raw)


def detect_trailing_newline(raw: bytes) -> bool:
    return raw.endswith(b'\n')


def load_records(path: Path, fmt: str) -> tuple[list, bytes]:
    raw = path.read_bytes()
    if fmt == 'jsonl':
        records = [json.loads(l) for l in raw.decode('utf-8').splitlines() if l.strip()]
    else:
        records = json.loads(raw)
    return records, raw


def write_records(path: Path, records: list, fmt: str, raw_before: bytes):
    ensure_ascii = detect_ensure_ascii(raw_before)
    trailing_nl = detect_trailing_newline(raw_before)
    if fmt == 'jsonl':
        text = '\n'.join(json.dumps(r, ensure_ascii=ensure_ascii) for r in records)
    else:
        text = json.dumps(records, indent=2, ensure_ascii=ensure_ascii)
    data = text.encode('utf-8')
    if trailing_nl:
        data += b'\n'
    path.write_bytes(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--file', help='Process a single file (relative to repo root)')
    ap.add_argument('--dry-run', action='store_true', help='Do not write')
    ap.add_argument('--bert-model', default=BERTSCORE_MODEL)
    ap.add_argument('--batch-size', type=int, default=16)
    args = ap.parse_args()

    files = [(args.file, 'jsonl' if args.file.endswith('.jsonl') else 'json_list')] if args.file else FILES

    from bert_score import score as bert_score_fn
    import torch
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f'BERTScore device={device}, model={args.bert_model}, batch_size={args.batch_size}')

    summary = {'model': args.bert_model, 'device': device, 'files': []}
    for rel, fmt in files:
        p = ROOT / rel
        if not p.exists():
            logger.warning(f'SKIP missing: {p}')
            continue
        records, raw = load_records(p, fmt)
        id_field = detect_id_field(records)

        # Extract (pred, exp) pairs + indices for write-back
        pairs = []  # list of (idx, pred_text, exp_text)
        for idx, rec in enumerate(records):
            pred_f, exp_f = detect_text_fields(rec)
            if not pred_f or not exp_f:
                continue
            task = rec.get('task_type', '')
            pred = normalize_predicted(rec.get(pred_f))
            exp = normalize_expected(rec.get(exp_f), task)
            if not pred.strip() or not exp.strip():
                continue
            if len(pred) < MIN_TEXT_LEN or len(exp) < MIN_TEXT_LEN:
                continue
            pairs.append((idx, pred, exp))

        n_records = len(records)
        n_pairs = len(pairs)
        logger.info(f'{rel}: {n_records} records, {n_pairs} BERT pairs')
        if n_pairs == 0:
            summary['files'].append({'path': rel, 'n_records': n_records, 'n_pairs': 0,
                                     'mean_bert_f1': 0.0, 'written': False})
            continue

        cands = [p[1] for p in pairs]
        refs = [p[2] for p in pairs]
        _P, _R, F1 = bert_score_fn(cands, refs, model_type=args.bert_model,
                                    lang='en', verbose=False,
                                    device=device, batch_size=args.batch_size)
        scores = [round(float(f), 4) for f in F1.tolist()]
        # Initialise everyone to 0.0 (preserves convention for empty-text records)
        for rec in records:
            rec['bert_f1'] = 0.0
        # Write computed scores back
        for (idx, _, _), s in zip(pairs, scores):
            records[idx]['bert_f1'] = s

        mean_f1 = round(sum(scores) / len(scores), 4)
        # Per-task means too (useful for paper)
        per_task = {}
        for task in ('annotation', 'rca'):
            tscores = [records[i]['bert_f1'] for (i, _, _) in pairs
                       if records[i].get('task_type') == task]
            per_task[task] = {'n': len(tscores),
                              'mean_bert_f1': round(sum(tscores) / len(tscores), 4) if tscores else 0.0}
        logger.info(f'  mean F1={mean_f1}, per-task={per_task}')

        if not args.dry_run:
            write_records(p, records, fmt, raw)
            written = True
        else:
            written = False
        summary['files'].append({'path': rel, 'n_records': n_records, 'n_pairs': n_pairs,
                                  'mean_bert_f1': mean_f1, 'per_task': per_task,
                                  'written': written})

    out = ROOT / 'benchmark' / 'final' / '_bert_f1_recompute_summary.json'
    out.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    logger.info(f'Wrote summary: {out}')


if __name__ == '__main__':
    main()
