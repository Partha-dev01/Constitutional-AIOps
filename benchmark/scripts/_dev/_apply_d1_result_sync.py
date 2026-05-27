"""Phase A.2: Sync task_type rca->qa_mcq for 33 OpsEval-remined cases across result files.

Preserves original JSON formatting (indent=2 for JSON, line-per-record for JSONL).
Idempotent. Adds excluded_reason field to match dataset.
"""
from __future__ import annotations

import json
from pathlib import Path

EXCLUDED_REASON = (
    'MCQ knowledge format (post-hoc audit 2026-05-25); '
    'originally judged DIAGNOSTIC by Qwen3-4B-Instruct fallback judge'
)

# (path, format) — format ∈ {"json_list", "jsonl"}
FILES = [
    # 10 main + ablation JSON files (top-level list; each needs 33 records updated)
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
    # 5 SOTA + phase46 JSONL files (line-per-record; each needs 33 records updated)
    ('benchmark/final/sota_baselines/llama_3_3_70b.jsonl', 'jsonl'),
    ('benchmark/final/sota_baselines/deepseek_v3.jsonl', 'jsonl'),
    ('benchmark/final/sota_baselines/drain.jsonl', 'jsonl'),  # expected 0 edits
    ('benchmark/final/phase46_no_prompt/llama_noprompt_clean.jsonl', 'jsonl'),
    ('benchmark/final/phase46_no_prompt/deepseek_noprompt_v2.jsonl', 'jsonl'),
]

ROOT = Path('.')


ID_FIELD_CANDIDATES = ('case_id', 'test_id', 'id', 'test_case_id')


def get_id(rec: dict, id_field: str) -> str:
    return str(rec.get(id_field, ''))


def is_remined(case_id: str) -> bool:
    return str(case_id).startswith('RCA_OPSEVAL_RM_')


def detect_id_field(records: list) -> str:
    if not records:
        return 'case_id'
    keys = records[0].keys()
    for k in ID_FIELD_CANDIDATES:
        if k in keys:
            return k
    raise ValueError(f'No known ID field in record keys: {list(keys)}')


def detect_ensure_ascii(raw: bytes) -> bool:
    """True if the file contains ONLY ASCII bytes (so ensure_ascii=True preserves)."""
    return all(b < 128 for b in raw)


def detect_trailing_newline(raw: bytes) -> bool:
    return raw.endswith(b'\n')


def update_record(rec: dict, id_field: str) -> int:
    cid = get_id(rec, id_field)
    if not is_remined(cid):
        return 0
    changed = False
    if rec.get('task_type') != 'qa_mcq':
        rec['task_type'] = 'qa_mcq'
        changed = True
    if rec.get('excluded_reason') != EXCLUDED_REASON:
        rec['excluded_reason'] = EXCLUDED_REASON
        changed = True
    return 1 if changed else 0


def process_json_list(path: Path) -> tuple[int, int, int]:
    raw_before = path.read_bytes()
    records = json.loads(raw_before)
    assert isinstance(records, list), f'{path}: expected list at top level'
    id_field = detect_id_field(records)
    ensure_ascii = detect_ensure_ascii(raw_before)
    trailing_nl = detect_trailing_newline(raw_before)
    n_remined = sum(1 for r in records if is_remined(get_id(r, id_field)))
    n_changed = sum(update_record(r, id_field) for r in records)
    new_text = json.dumps(records, indent=2, ensure_ascii=ensure_ascii)
    raw_after = new_text.encode('utf-8')
    if trailing_nl:
        raw_after += b'\n'
    path.write_bytes(raw_after)
    return n_remined, n_changed, len(raw_after) - len(raw_before)


def process_jsonl(path: Path) -> tuple[int, int, int]:
    raw_before = path.read_bytes()
    lines = raw_before.decode('utf-8').splitlines(keepends=False)
    records = [json.loads(l) for l in lines if l.strip()]
    id_field = detect_id_field(records)
    ensure_ascii = detect_ensure_ascii(raw_before)
    trailing_nl = detect_trailing_newline(raw_before)
    n_remined = sum(1 for r in records if is_remined(get_id(r, id_field)))
    n_changed = sum(update_record(r, id_field) for r in records)
    new_lines = [json.dumps(r, ensure_ascii=ensure_ascii) for r in records]
    new_text = '\n'.join(new_lines)
    raw_after = new_text.encode('utf-8')
    if trailing_nl:
        raw_after += b'\n'
    path.write_bytes(raw_after)
    return n_remined, n_changed, len(raw_after) - len(raw_before)


def main():
    total_changed = 0
    print(f'{"File":<70} {"remined":>8} {"changed":>8} {"dbytes":>10}')
    print('-' * 100)
    for rel, fmt in FILES:
        p = ROOT / rel
        assert p.exists(), f'Missing: {p}'
        if fmt == 'json_list':
            nr, nc, delta = process_json_list(p)
        elif fmt == 'jsonl':
            nr, nc, delta = process_jsonl(p)
        else:
            raise ValueError(f'unknown fmt: {fmt}')
        total_changed += nc
        print(f'{rel:<70} {nr:>8} {nc:>8} {delta:>+10,}')
    print('-' * 100)
    print(f'{"TOTAL":<70} {"":>8} {total_changed:>8}')


if __name__ == '__main__':
    main()
