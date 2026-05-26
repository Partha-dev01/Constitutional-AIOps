"""Compute SOTA + Phase 4.6 accuracy numbers after the D-1 re-label."""
import json
from pathlib import Path


def load_jsonl(p):
    with open(p, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]


def stats(records):
    ann = [r for r in records if r.get('task_type') == 'annotation' and r.get('correct') is not None]
    rca = [r for r in records if r.get('task_type') == 'rca' and r.get('correct') is not None]
    ovl = ann + rca
    def acc(rs):
        if not rs: return (0, 0, float('nan'))
        c = sum(1 for r in rs if r.get('correct'))
        return (c, len(rs), 100.0 * c / len(rs))
    return {'ann': acc(ann), 'rca': acc(rca), 'overall': acc(ovl)}


def pretty(label, s):
    a, r, o = s['ann'], s['rca'], s['overall']
    print(f'  {label:<40} Ann {a[2]:>5.1f}% ({a[0]}/{a[1]})  '
          f'RCA {r[2]:>5.1f}% ({r[0]}/{r[1]})  Ovl {o[2]:>5.1f}% ({o[0]}/{o[1]})')


print('=' * 100)
print('SOTA baselines (Table 7) — POST D-1 re-label')
print('=' * 100)
for label, path in [
    ('Llama 3.3-70B', 'benchmark/final/sota_baselines/llama_3_3_70b.jsonl'),
    ('DeepSeek V3.2', 'benchmark/final/sota_baselines/deepseek_v3.jsonl'),
]:
    pretty(label, stats(load_jsonl(Path(path))))

# Drain has its own summary; load as JSONL
p_drain = Path('benchmark/final/sota_baselines/drain.jsonl')
drain_recs = load_jsonl(p_drain)
ann = [r for r in drain_recs if r.get('task_type') == 'annotation' and r.get('correct') is not None]
n_correct = sum(1 for r in ann if r.get('correct'))
print(f'  {"Drain (annotation only)":<40} Ann {100*n_correct/len(ann):.1f}% ({n_correct}/{len(ann)})  RCA N/A')

print()
print('=' * 100)
print('Phase 4.6 no-prompt (was Table 8) — POST D-1 re-label')
print('=' * 100)
for label, path in [
    ('Llama 3.3-70B no-prompt', 'benchmark/final/phase46_no_prompt/llama_noprompt_clean.jsonl'),
    ('DeepSeek V3.2 no-prompt', 'benchmark/final/phase46_no_prompt/deepseek_noprompt_v2.jsonl'),
]:
    pretty(label, stats(load_jsonl(Path(path))))

print()
print('=' * 100)
print('Main re-run + Ablation Full (Table 2 / Table 6) — confirm via JSON files too')
print('=' * 100)
for label, path in [
    ('Main re-run (Ours)', 'benchmark/final/main_benchmark/results_sota_eval_431.json'),
    ('Ablation Full Hybrid', 'benchmark/final/ablation_v4/ablation_full/results_sota_eval_431.json'),
]:
    with open(path, encoding='utf-8') as f:
        recs = json.load(f)
    pretty(label, stats(recs))
