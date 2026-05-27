"""Phase A.2 verification: structural diff between git HEAD and current state for all 16 files."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

EXCLUDED_REASON = (
    'MCQ knowledge format (post-hoc audit 2026-05-25); '
    'originally judged DIAGNOSTIC by Qwen3-4B-Instruct fallback judge'
)
ID_FIELDS = ('case_id', 'test_id', 'id', 'test_case_id')


def get_id(rec, fields=ID_FIELDS):
    for f in fields:
        v = rec.get(f, '')
        if v:
            return str(v)
    return ''


def is_remined(cid):
    return str(cid).startswith('RCA_OPSEVAL_RM_')


def load_records(path: Path, raw: bytes) -> list:
    if path.suffix == '.jsonl':
        return [json.loads(l) for l in raw.decode('utf-8').splitlines() if l.strip()]
    return json.loads(raw)


def main():
    files = [
        'benchmark/final/main_benchmark/results_sota_eval_431.json',
        'benchmark/final/main_benchmark/results.json',
        'benchmark/final/ablation_v4/ablation_full/results_sota_eval_431.json',
        'benchmark/final/ablation_v4/ablation_single_4b/results_sota_eval_431.json',
        'benchmark/final/ablation_v4/ablation_single_14b/results_sota_eval_431.json',
        'benchmark/final/ablation_v4/ablation_no_structured/results_sota_eval_431.json',
        'benchmark/final/ablation_v4/ablation_no_system_prompt/results_sota_eval_431.json',
        'benchmark/final/ablation_v4/ablation_with_graph/results_sota_eval_431.json',
        'benchmark/final/ablation_v4/ablation_no_constitutional/results_sota_eval_431.json',
        'benchmark/final/ablation_v4/ablation_with_orchestrator/results_sota_eval_431.json',
        'benchmark/final/sota_baselines/llama_3_3_70b.jsonl',
        'benchmark/final/sota_baselines/deepseek_v3.jsonl',
        'benchmark/final/sota_baselines/drain.jsonl',
        'benchmark/final/phase46_no_prompt/llama_noprompt_clean.jsonl',
        'benchmark/final/phase46_no_prompt/deepseek_noprompt_v2.jsonl',
    ]

    total_fail = 0
    print(f'{"File":<70} {"orig":>4} {"now":>4} {"rl":>4} {"er":>4} {"unx":>4}  verdict')
    print('-' * 110)
    for rel in files:
        p = Path(rel)
        # Original from git
        r = subprocess.run(['git', 'show', f'HEAD:{rel}'], capture_output=True)
        if r.returncode != 0:
            print(f'  ERR git show: {rel}')
            total_fail += 1
            continue
        orig_raw = r.stdout
        cur_raw = p.read_bytes()
        try:
            orig_recs = load_records(p, orig_raw)
            cur_recs = load_records(p, cur_raw)
        except Exception as e:
            print(f'  ERR load: {rel}: {e}')
            total_fail += 1
            continue

        if len(orig_recs) != len(cur_recs):
            print(f'  LEN MISMATCH: orig={len(orig_recs)} cur={len(cur_recs)}: {rel}')
            total_fail += 1
            continue

        orig_remined = sum(1 for r in orig_recs if is_remined(get_id(r)))
        cur_remined = sum(1 for r in cur_recs if is_remined(get_id(r)))
        n_relabeled = 0
        n_reason = 0
        unexpected = []

        for o, n in zip(orig_recs, cur_recs):
            oid, nid = get_id(o), get_id(n)
            if oid != nid:
                unexpected.append(f'ID mismatch: {oid} -> {nid}')
                continue
            o_keys = set(o.keys())
            n_keys = set(n.keys())
            added = n_keys - o_keys
            removed = o_keys - n_keys
            tt_changed = o.get('task_type') != n.get('task_type')

            if not is_remined(oid):
                if added or removed or tt_changed:
                    unexpected.append(f'NON-remined modified: {oid} +{added} -{removed} tt:{o.get("task_type")}->{n.get("task_type")}')
                continue

            # Remined: expect task_type rca->qa_mcq, +excluded_reason field, nothing else
            if tt_changed:
                if o.get('task_type') == 'rca' and n.get('task_type') == 'qa_mcq':
                    n_relabeled += 1
                else:
                    unexpected.append(f'{oid}: bad tt change {o.get("task_type")}->{n.get("task_type")}')
            if added == {'excluded_reason'} and n.get('excluded_reason') == EXCLUDED_REASON:
                n_reason += 1
            elif added:
                unexpected.append(f'{oid}: unexpected added keys {added}')
            if removed:
                unexpected.append(f'{oid}: unexpected removed keys {removed}')
            for k in o_keys & n_keys:
                if k == 'task_type':
                    continue
                if o[k] != n[k]:
                    unexpected.append(f'{oid}.{k}: field value changed')

        if rel.endswith('drain.jsonl'):
            verdict = 'PASS' if (n_relabeled == 0 and n_reason == 0 and not unexpected) else 'FAIL'
        else:
            verdict = 'PASS' if (n_relabeled == 33 and n_reason == 33 and not unexpected) else 'FAIL'
        if verdict == 'FAIL':
            total_fail += 1
        print(f'  {Path(rel).name:<68s} {orig_remined:>4} {cur_remined:>4} {n_relabeled:>4} {n_reason:>4} {len(unexpected):>4}  {verdict}')
        for u in unexpected[:5]:
            print(f'    {u}')
    print('-' * 110)
    print(f'VERDICT: {"ALL PASS" if total_fail == 0 else f"{total_fail} FAILURES"}')
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == '__main__':
    main()
