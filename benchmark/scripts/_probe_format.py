"""Probe exact byte-level format of result files for A.2 re-apply."""
import json
from pathlib import Path

NL = b'\n'

# Probe 1: results.json structure
p = Path('benchmark/final/main_benchmark/results.json')
raw = p.read_bytes()
nl_count = raw.count(NL)
print(f'results.json: size={len(raw):,} bytes, newlines={nl_count}')
d = json.loads(raw)
print(f'  type: {type(d).__name__}')
if isinstance(d, dict):
    print(f'  keys: {list(d.keys())}')
    for key in ('test_results', 'results', 'test_cases'):
        if key in d:
            tr = d[key]
            print(f'  {key} len: {len(tr)}')
            if tr and isinstance(tr, list):
                print(f'  first record keys: {list(tr[0].keys())[:10]}')
                remined = [r for r in tr if str(r.get("case_id", r.get("id",""))).startswith("RCA_OPSEVAL_RM_")]
                print(f'  remined in {key}: {len(remined)}')
elif isinstance(d, list):
    print(f'  list len: {len(d)}')

# Probe 2: results_sota_eval_431.json byte-level round-trip
p2 = Path('benchmark/final/main_benchmark/results_sota_eval_431.json')
raw2 = p2.read_bytes()
print(f'\nresults_sota_eval_431.json: size={len(raw2):,} bytes')
d2 = json.loads(raw2)
roundtrip = json.dumps(d2, indent=2, ensure_ascii=True).encode('utf-8')
print(f'  round-trip indent=2 ensure_ascii=True: {len(roundtrip):,} bytes (delta {len(roundtrip)-len(raw2):+,})')
roundtrip_nl = roundtrip + NL
print(f'  ...+trailing NL: {len(roundtrip_nl):,} bytes (delta {len(roundtrip_nl)-len(raw2):+,})')

# Find first byte of difference
limit = min(len(raw2), len(roundtrip))
for i in range(limit):
    if raw2[i] != roundtrip[i]:
        ctx_orig = raw2[max(0,i-40):i+40]
        ctx_new = roundtrip[max(0,i-40):i+40]
        print(f'  first byte diff at offset {i}:')
        print(f'    orig: {ctx_orig!r}')
        print(f'    new:  {ctx_new!r}')
        break
else:
    print(f'  no diff in first {limit} bytes')

print(f'  orig last 80 bytes: {raw2[-80:]!r}')
print(f'  new  last 80 bytes: {roundtrip[-80:]!r}')

# Probe 3: drain.jsonl
p3 = Path('benchmark/final/sota_baselines/drain.jsonl')
raw3 = p3.read_bytes()
print(f'\ndrain.jsonl: size={len(raw3):,} bytes, ends with NL: {raw3.endswith(NL)}')
print(f'  last 40 bytes: {raw3[-40:]!r}')

# Round-trip jsonl
lines3 = raw3.decode('utf-8').splitlines(keepends=False)
records3 = [json.loads(l) for l in lines3 if l.strip()]
rebuilt = ('\n'.join(json.dumps(r, ensure_ascii=True) for r in records3) + '\n').encode('utf-8')
print(f'  round-trip size: {len(rebuilt):,} (delta {len(rebuilt)-len(raw3):+,})')

# Also try without trailing newline
rebuilt2 = '\n'.join(json.dumps(r, ensure_ascii=True) for r in records3).encode('utf-8')
print(f'  round-trip size (no trailing NL): {len(rebuilt2):,} (delta {len(rebuilt2)-len(raw3):+,})')
