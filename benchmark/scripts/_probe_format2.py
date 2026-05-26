"""Probe results.json format for A.2 re-apply."""
import json
from pathlib import Path

NL = b'\n'

p = Path('benchmark/final/main_benchmark/results.json')
raw = p.read_bytes()
print(f'results.json: size={len(raw):,}')
d = json.loads(raw)
# Round-trip
for indent in (2, 4):
    rt = json.dumps(d, indent=indent, ensure_ascii=True).encode('utf-8')
    print(f'  round-trip indent={indent}: {len(rt):,} (delta {len(rt)-len(raw):+,})')
    rtnl = rt + NL
    print(f'  round-trip indent={indent} + trailing NL: {len(rtnl):,} (delta {len(rtnl)-len(raw):+,})')

# Find first byte diff for indent=2
rt2 = json.dumps(d, indent=2, ensure_ascii=True).encode('utf-8')
for i in range(min(len(raw), len(rt2))):
    if raw[i] != rt2[i]:
        print(f'\n  first diff (indent=2) at byte {i}:')
        print(f'    orig: {raw[max(0,i-50):i+50]!r}')
        print(f'    new:  {rt2[max(0,i-50):i+50]!r}')
        break

# Check tail
print(f'\n  orig last 100 bytes: {raw[-100:]!r}')
print(f'  new  last 100 bytes: {rt2[-100:]!r}')

# Probe all .json result files to check if any use different indent
print('\n=== All JSON result file format checks ===')
JSON_FILES = [
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
]
for rel in JSON_FILES:
    p = Path(rel)
    raw = p.read_bytes()
    d = json.loads(raw)
    rt2 = json.dumps(d, indent=2, ensure_ascii=True).encode('utf-8')
    rt4 = json.dumps(d, indent=4, ensure_ascii=True).encode('utf-8')
    # ID field detection
    if isinstance(d, list) and d:
        keys = list(d[0].keys())
        id_field = next((k for k in ('case_id', 'test_id', 'id', 'test_case_id') if k in keys), None)
        n_remined = sum(1 for r in d if str(r.get(id_field, '')).startswith('RCA_OPSEVAL_RM_')) if id_field else 0
    else:
        id_field, n_remined = None, 0
    delta2 = len(rt2) - len(raw)
    delta4 = len(rt4) - len(raw)
    print(f'  {Path(rel).name:48s}  size={len(raw):>8,}  d2={delta2:>+6}  d4={delta4:>+7}  id_field={id_field}  remined={n_remined}')
