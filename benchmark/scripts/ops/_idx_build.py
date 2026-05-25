import json, os, sys

# Load master backup manifest (pre-reorg)
m = json.load(open('c:/Users/partha/Downloads/files AIOPS NEW/constitutional-aiops/benchmark/final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json'))
sha_map = {f['path']: f['sha256'][:12] for f in m['files']}
size_map = {f['path']: f['size'] for f in m['files']}

# Walk current tree
walk_path = 'c:/Users/partha/Downloads/files AIOPS NEW/_index_walk.txt'
current = []
with open(walk_path) as fh:
    for line in fh:
        line = line.rstrip('\n')
        if not line:
            continue
        parts = line.split('|')
        rel = parts[0].replace('\\', '/')
        mtime = parts[1]
        size = int(parts[2])
        current.append((rel, mtime, size))

print('CURRENT_COUNT:', len(current))

def find_sha(cr):
    direct = 'benchmark/' + cr
    if direct in sha_map:
        return sha_map[direct], 'manifest-direct'
    candidates = []
    if cr.startswith('raw/'):
        candidates.append('benchmark/datasets/raw/' + cr[4:])
    if cr.startswith('intermediate/datasets/'):
        candidates.append('benchmark/datasets/processed/' + cr[len('intermediate/datasets/'):])
    if cr.startswith('intermediate/candidates/'):
        candidates.append('benchmark/v0.11/' + cr[len('intermediate/candidates/'):])
    if cr.startswith('final/docs/_archived_session_history/'):
        fname = cr[len('final/docs/_archived_session_history/'):]
        candidates.append('benchmark/results_aws/FINAL/' + fname)
        # Top-level docs at results_aws/ that got archived
        candidates.append('benchmark/results_aws/' + fname)
    elif cr.startswith('final/docs/'):
        fname = cr[len('final/docs/'):]
        candidates.append('benchmark/results_aws/' + fname)
        candidates.append('benchmark/results_aws/FINAL/' + fname)
    elif cr.startswith('final/audit/'):
        fname = cr[len('final/audit/'):]
        candidates.append('benchmark/results_aws/FINAL/audit/' + fname)
        candidates.append('benchmark/results_aws/FINAL/' + fname)
    elif cr.startswith('final/'):
        candidates.append('benchmark/results_aws/FINAL/' + cr[6:])
    if cr.startswith('archive/originals_2026-05-19/'):
        candidates.append('benchmark/results_aws/_archive_originals_2026-05-19/' + cr[len('archive/originals_2026-05-19/'):])
    if cr.startswith('archive/v0.9.1_jarvis_baseline/'):
        candidates.append('benchmark/results/' + cr[len('archive/v0.9.1_jarvis_baseline/'):])
        candidates.append('benchmark/results_v2.0_frozen/' + cr[len('archive/v0.9.1_jarvis_baseline/'):])
    for prefix in ['aiops_archive_2026-05-17.tar.gz', 'originals_backup_2026-05-19.zip']:
        if cr == 'archive/' + prefix:
            candidates.append('benchmark/results_aws/' + prefix)
    if cr.startswith('archive/run_stackA_main431_OLD_PROMPT/'):
        candidates.append('benchmark/results_aws/run_stackA_main431/' + cr[len('archive/run_stackA_main431_OLD_PROMPT/'):])
    if cr.startswith('archive/rerun_remine33_enriched/'):
        candidates.append('benchmark/results_aws/rerun_remine33_enriched/' + cr[len('archive/rerun_remine33_enriched/'):])
    if cr.startswith('archive/smoke_tests/'):
        candidates.append('benchmark/results_aws/archive/smoke_tests/' + cr[len('archive/smoke_tests/'):])
    if cr.startswith('scripts/'):
        parts = cr.split('/')
        if len(parts) >= 3 and parts[1] in ('prep', 'run', 'eval', 'ops', '_dev'):
            candidates.append('benchmark/scripts/' + parts[-1])
    for c in candidates:
        if c in sha_map:
            return sha_map[c], 'manifest-mapped'
    return None, 'unknown'

matched = 0
unknown = 0
for_render = []
for rel, mtime, size in current:
    sha, source = find_sha(rel)
    for_render.append((rel, mtime, size, sha or '[unknown]', source))
    if sha:
        matched += 1
    else:
        unknown += 1

print('MATCHED:', matched, 'UNKNOWN:', unknown)

unknowns_list = [(r, sz) for r, mt, sz, sha, src in for_render if src == 'unknown']
print('UNKNOWN SAMPLES:')
for r, sz in unknowns_list[:50]:
    print(' ', r, sz)
print('TOTAL UNKNOWNS:', len(unknowns_list))

with open('c:/Users/partha/Downloads/files AIOPS NEW/_index_render.txt', 'w') as fh:
    for row in for_render:
        fh.write('|'.join(str(x) for x in row) + '\n')

current_rels = {r for r, _, _, _, _ in for_render}

def manifest_to_current_candidates(mpath):
    rest = mpath[len('benchmark/'):] if mpath.startswith('benchmark/') else mpath
    cands = []
    if rest.startswith('datasets/raw/'):
        cands.append('raw/' + rest[len('datasets/raw/'):])
    if rest.startswith('datasets/processed/'):
        cands.append('intermediate/datasets/' + rest[len('datasets/processed/'):])
    if rest.startswith('v0.11/'):
        cands.append('intermediate/candidates/' + rest[len('v0.11/'):])
    if rest.startswith('results_aws/FINAL/'):
        cands.append('final/' + rest[len('results_aws/FINAL/'):])
        cands.append('final/docs/_archived_session_history/' + rest[len('results_aws/FINAL/'):])
        cands.append('final/audit/' + rest[len('results_aws/FINAL/'):])
    if rest.startswith('results_aws/_archive_originals_2026-05-19/'):
        cands.append('archive/originals_2026-05-19/' + rest[len('results_aws/_archive_originals_2026-05-19/'):])
    if rest.startswith('results_aws/run_stackA_main431/'):
        cands.append('archive/run_stackA_main431_OLD_PROMPT/' + rest[len('results_aws/run_stackA_main431/'):])
    if rest.startswith('results_aws/rerun_remine33_enriched/'):
        cands.append('archive/rerun_remine33_enriched/' + rest[len('results_aws/rerun_remine33_enriched/'):])
    if rest.startswith('results_aws/archive/smoke_tests/'):
        cands.append('archive/smoke_tests/' + rest[len('results_aws/archive/smoke_tests/'):])
    elif rest.startswith('results_aws/archive/'):
        # gate15_comparison.md and other archive/ items
        cands.append('final/infrastructure/' + rest[len('results_aws/archive/'):])
    for f in ['aiops_archive_2026-05-17.tar.gz', 'originals_backup_2026-05-19.zip']:
        if rest == 'results_aws/' + f:
            cands.append('archive/' + f)
    if rest.startswith('results_aws/') and '/' not in rest[len('results_aws/'):]:
        cands.append('final/docs/' + rest[len('results_aws/'):])
    if rest.startswith('results/'):
        cands.append('archive/v0.9.1_jarvis_baseline/' + rest[len('results/'):])
    if rest.startswith('results_v2.0_frozen/'):
        cands.append('archive/v0.9.1_jarvis_baseline/' + rest[len('results_v2.0_frozen/'):])
    if rest.startswith('scripts/') and '/' not in rest[len('scripts/'):]:
        fname = rest[len('scripts/'):]
        for sub in ['prep', 'run', 'eval', 'ops', '_dev']:
            cands.append('scripts/' + sub + '/' + fname)
        cands.append('scripts/' + fname)
    if '/' not in rest:
        cands.append(rest)
    return cands

deleted = []
for mpath in sha_map:
    cands = manifest_to_current_candidates(mpath)
    if not any(c in current_rels for c in cands):
        if mpath[len('benchmark/'):] in current_rels:
            continue
        deleted.append((mpath, sha_map[mpath], size_map[mpath]))

print('DELETED-SINCE-BASELINE:', len(deleted))
with open('c:/Users/partha/Downloads/files AIOPS NEW/_index_deleted.txt', 'w') as fh:
    for mp, sha, sz in deleted:
        fh.write(mp + '|' + sha + '|' + str(sz) + '\n')

added = [(r, sz) for r, mt, sz, sha, src in for_render if src == 'unknown']
print('ADDED-SINCE-BASELINE (unknown=true):', len(added))
with open('c:/Users/partha/Downloads/files AIOPS NEW/_index_added.txt', 'w') as fh:
    for r, sz in added:
        fh.write(r + '|' + str(sz) + '\n')

modified = []
for rel, mtime, size, sha, src in for_render:
    if sha and sha != '[unknown]':
        date_part = mtime.split(' ')[0] if ' ' in mtime else mtime
        if date_part > '2026-05-20':
            modified.append((rel, sha, mtime))
print('POSSIBLY-MODIFIED:', len(modified))
with open('c:/Users/partha/Downloads/files AIOPS NEW/_index_modified.txt', 'w') as fh:
    for r, sha, mt in modified:
        fh.write(r + '|' + sha + '|' + mt + '\n')
