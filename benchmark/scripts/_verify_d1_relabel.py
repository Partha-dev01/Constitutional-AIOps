"""Verify D-1 re-label: structural diff between git HEAD and current dataset."""
import json
import subprocess

r = subprocess.run(
    ['git', 'show', 'HEAD:benchmark/intermediate/datasets/benchmark_431_seed42.json'],
    capture_output=True,
)
orig = r.stdout
print(f'Original (git HEAD) bytes: {len(orig):,}')

with open('benchmark/intermediate/datasets/benchmark_431_seed42.json', 'rb') as f:
    cur = f.read()
print(f'Current bytes: {len(cur):,}')
print(f'Size delta: {len(cur) - len(orig):+,}')

nesc_orig = orig.decode('utf-8', errors='replace').count(chr(92) + 'u')
nesc_cur = cur.decode('utf-8').count(chr(92) + 'u')
print(f'\\u escapes in original: {nesc_orig:,}')
print(f'\\u escapes in current:  {nesc_cur:,}')

non_ascii_cur = sum(1 for b in cur if b > 127)
non_ascii_orig = sum(1 for b in orig if b > 127)
print(f'Non-ASCII bytes in original: {non_ascii_orig:,}')
print(f'Non-ASCII bytes in current:  {non_ascii_cur:,}')

orig_data = json.loads(orig)
cur_data = json.loads(cur)
assert len(orig_data['test_cases']) == len(cur_data['test_cases']) == 431, 'Case-count mismatch!'

mismatches = []
relabel_count = 0
extra_field_count = 0
for o, n in zip(orig_data['test_cases'], cur_data['test_cases']):
    if o['id'] != n['id']:
        mismatches.append(f'ID mismatch at index')
        continue
    o_keys = set(o.keys())
    n_keys = set(n.keys())
    if o_keys != n_keys:
        added = n_keys - o_keys
        removed = o_keys - n_keys
        if added == {'excluded_reason'} and not removed:
            extra_field_count += 1
        else:
            mismatches.append(f'KEY MISMATCH {o["id"]}: +{added} -{removed}')
    if o.get('task_type') != n.get('task_type'):
        if (o.get('task_type') == 'rca'
                and n.get('task_type') == 'qa_mcq'
                and str(n['id']).startswith('RCA_OPSEVAL_RM_')):
            relabel_count += 1
        else:
            mismatches.append(f'UNEXPECTED tt change {o["id"]}: {o.get("task_type")} -> {n.get("task_type")}')
    for k in o_keys & n_keys:
        if k == 'task_type':
            continue
        if o[k] != n[k]:
            mismatches.append(f'FIELD MISMATCH {o["id"]}.{k}')

print(f'\nRe-labeled (rca->qa_mcq) count: {relabel_count}  (expected 33)')
print(f'Added excluded_reason count:    {extra_field_count}  (expected 33)')
print(f'Unexpected mismatches:          {len(mismatches)}  (expected 0)')
for m in mismatches[:20]:
    print(f'  {m}')

ok = (relabel_count == 33 and extra_field_count == 33 and not mismatches)
print(f'\nVERDICT: {"PASS" if ok else "FAIL"}')
