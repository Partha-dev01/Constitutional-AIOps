import os, sys

# Read for_render
rows = []
with open('c:/Users/partha/Downloads/files AIOPS NEW/_index_render.txt') as fh:
    for line in fh:
        line = line.rstrip('\n')
        if not line:
            continue
        parts = line.split('|')
        # rel | mtime | size | sha | source
        rows.append({
            'path': parts[0],
            'mtime': parts[1],
            'size': int(parts[2]),
            'sha': parts[3],
            'source': parts[4],
        })

# Read added/deleted/modified
added = []
with open('c:/Users/partha/Downloads/files AIOPS NEW/_index_added.txt') as fh:
    for line in fh:
        line = line.rstrip('\n')
        if not line: continue
        p, sz = line.split('|')
        added.append((p, int(sz)))

deleted = []
with open('c:/Users/partha/Downloads/files AIOPS NEW/_index_deleted.txt') as fh:
    for line in fh:
        line = line.rstrip('\n')
        if not line: continue
        parts = line.split('|')
        deleted.append((parts[0], parts[1], int(parts[2])))

modified = []
with open('c:/Users/partha/Downloads/files AIOPS NEW/_index_modified.txt') as fh:
    for line in fh:
        line = line.rstrip('\n')
        if not line: continue
        parts = line.split('|')
        modified.append((parts[0], parts[1], parts[2]))

# Partition classification
def partition(path):
    if path.startswith('raw/'): return 'raw'
    if path.startswith('intermediate/'): return 'intermediate'
    if path.startswith('final/'): return 'final'
    if path.startswith('archive/'): return 'archive'
    if path.startswith('scripts/'): return 'scripts'
    return 'other'

# Tally per partition
from collections import defaultdict
part_count = defaultdict(int)
part_size = defaultdict(int)
for r in rows:
    p = partition(r['path'])
    part_count[p] += 1
    part_size[p] += r['size']

print('=== PARTITION TALLY ===')
total_count = 0; total_size = 0
for p in ['raw', 'intermediate', 'final', 'archive', 'scripts', 'other']:
    print(f'{p}: {part_count[p]} files, {part_size[p]:,} bytes ({part_size[p]/1024/1024:.2f} MB)')
    total_count += part_count[p]
    total_size += part_size[p]
print(f'TOTAL: {total_count} files, {total_size:,} bytes ({total_size/1024/1024:.2f} MB)')

# Role/status inference rules
def role(path):
    # File-level overrides first
    name = os.path.basename(path)
    # READMEs
    if name == 'README.md':
        return ('partition/folder README', 'active')
    # Scripts
    if path.startswith('scripts/'):
        if name == '__init__.py': return ('package marker', 'active')
        if path.startswith('scripts/prep/'): return ('dataset prep / mining script', 'active' if name not in ('fix_benchmark_dataset.py', 'remove_chinese.py') else 'historical')
        if path.startswith('scripts/run/'): return ('benchmark runner script', 'active')
        if path.startswith('scripts/eval/'): return ('eval / scoring / stats script', 'active' if name not in ('evaluate_results.py', 'inspect_single4b.py') else 'historical')
        if path.startswith('scripts/ops/'): return ('build / archive / e2e utility', 'active' if name in ('master_backup_manifest.py', 'e2e_tests.py') else 'historical')
        if path.startswith('scripts/_dev/'): return ('smoke / debug / dev script', 'dev' if name != 'create_nothink_model.py' else 'historical')
        if name == '__init__.py': return ('package marker', 'active')
        return ('script', 'unknown')
    # final/
    if path.startswith('final/'):
        if path.startswith('final/main_benchmark/'):
            if name.endswith('.json') or name.endswith('.jsonl'):
                if 'phase5' in name: return ('Phase 5 stats (main re-run)', 'active')
                if 'results_sota_eval_431' in name: return ('Table 2 matched-eval source', 'active')
                if name == 'results.json': return ('Table 2 rich-eval source', 'active')
                if name == 'summary.json' or name == 'benchmark_result.json': return ('runner.py aggregate (provenance)', 'active')
            if name.endswith('.md'): return ('README / paper-table doc', 'active')
            if name.endswith('.tex'): return ('paper-table LaTeX', 'active')
            return ('main_benchmark artifact', 'active')
        if path.startswith('final/ablation_v4/'):
            if 'phase5' in name: return ('Phase 5 ablation stats', 'active')
            if 'matched_eval_table' in name: return ('Table 6 matched-eval canonical', 'active')
            if 'results_sota_eval_431' in name: return ('ablation matched-eval (Table 6 raw)', 'active')
            if name == 'results.json': return ('ablation rich-eval (provenance only — see AUDIT_REPORT)', 'active')
            if name == 'summary.json': return ('ablation aggregate (provenance)', 'active')
            return ('ablation_v4 artifact', 'active')
        if path.startswith('final/sota_baselines/'):
            return ('SOTA baseline JSONL (Table 7)', 'active')
        if path.startswith('final/phase46_no_prompt/'):
            return ('no-prompt baseline JSONL (Table 8)', 'active')
        if path.startswith('final/infrastructure/'):
            return ('dual-stack gate evidence (§3)', 'active')
        if path.startswith('final/audit/'):
            if 'MASTER_BACKUP_MANIFEST' in name: return ('pre-zip SHA-256 manifest (493 files, 2026-05-20)', 'sealed-forensic')
            if 'CV_PASS' in name: return ('cross-validation pass (sealed forensic)', 'sealed-forensic')
            if 'FULL_TRANSCRIPT_AUDIT' in name: return ('sessions 1–11 transcript forensic audit', 'sealed-forensic')
            if 'REORG_PROPOSAL' in name: return ('2026-05-20 4-partition reorg plan', 'sealed-forensic')
            if 'SESSION_' in name and 'HANDOFF' in name: return ('session handoff doc', 'sealed-forensic')
            return ('audit artifact', 'sealed-forensic')
        if path.startswith('final/docs/_archived_session_history/'):
            return ('session 9 historical doc (sealed)', 'sealed-forensic')
        if path.startswith('final/docs/'):
            return ('active runbook / methodology doc', 'active')
        if name == 'SUMMARY.md': return ('results landscape + Phase 5 narrative', 'active')
        if name == 'MANIFEST.md': return ('47-file FINAL build manifest + SHAs', 'active')
        if name == 'AUDIT_REPORT.md': return ('per-file content audit (23 files)', 'active')
        if name == 'README.md': return ('final/ entry-point README', 'active')
        return ('final/ artifact', 'active')
    # intermediate/
    if path.startswith('intermediate/datasets/'):
        return ('canonical benchmark dataset', 'active')
    if path.startswith('intermediate/candidates/'):
        return ('mining-stage candidate JSONL', 'active')
    # raw/
    if path.startswith('raw/loghub/'):
        return ('Loghub raw dataset (gitignored)', 'active')
    if path.startswith('raw/opseval/'):
        return ('OpsEval raw dataset (gitignored)', 'active')
    if path.startswith('raw/lemma_rca/'):
        return ('LEMMA-RCA cache marker (gitignored)', 'active')
    if path.startswith('raw/') and name.endswith('candidates.jsonl'):
        return ('raw mining output (gitignored mirror of intermediate/candidates/)', 'active')
    if path == 'raw/opseval_remine_s2.jsonl':
        return ('OpsEval re-mining stage-2 output (gitignored)', 'active')
    # archive/
    if path.startswith('archive/originals_2026-05-19/'):
        if name.startswith('_ARCHIVED_NOTICE') or name == '_ARCHIVED.md' or name == '_REORG_NOTE_2026-05-20.md':
            return ('archive notice / reorg note', 'historical')
        return ('originals snapshot (sessions 10–11, pre-FINAL build)', 'historical')
    if path.startswith('archive/v0.9.1_jarvis_baseline/'):
        return ('Jarvis Labs A5000 v1 baseline (Feb 2026)', 'historical')
    if path.startswith('archive/run_stackA_main431_OLD_PROMPT/'):
        return ('main run with OLD RCA prompt (pre-fix; v1-paper anchor)', 'historical')
    if path.startswith('archive/rerun_remine33_enriched/'):
        return ('partial re-run after L5614 enrichment fix', 'historical')
    if path.startswith('archive/smoke_tests/'):
        return ('5+5 / 15+15 dual-stack smoke runs (sessions 2–4)', 'historical')
    if path == 'archive/aiops_archive_2026-05-17.tar.gz':
        return ('instance-side session-10 tarball backup', 'historical')
    if path == 'archive/originals_backup_2026-05-19.zip':
        return ('defense-in-depth zip of originals_2026-05-19/', 'historical')
    # top-level
    if path == '.benchmark_step2_complete':
        return ('benchmark step-2 sentinel', 'historical')
    if path == '.progress.json':
        return ('benchmark progress marker', 'historical')
    if name == '__init__.py':
        return ('package marker', 'active')
    return ('unknown', 'unknown')

# Add role/status to rows
for r in rows:
    r['role'], r['status'] = role(r['path'])

# Now write INDEX.md
def fmt_size(b):
    if b >= 1e6: return f'{b/1e6:.2f} MB'
    if b >= 1e3: return f'{b/1e3:.1f} KB'
    return f'{b} B'

OUT = ['# benchmark/ - Master Index',
       '',
       '_Generated: 2026-05-25 (session 16). Baseline: `CV_PASS2_CODEBASE_AUDIT.md` Part B (491 files, 2026-05-20) + `MASTER_BACKUP_MANIFEST_2026-05-20.json` (493 files)._',
       '',
       '> **Update protocol**: whenever a file is added/removed/moved under `benchmark/`, this index MUST be regenerated. Also bump the `MEMORY.md` "Hard pointers" block if a canonical artifact location changes.',
       '',
       '> **SHA-256 source**: SHAs in this index are short (first 12 hex chars) and cite `MASTER_BACKUP_MANIFEST_2026-05-20.json` via mapped post-reorg paths. Files added since 2026-05-20 (or for which no mapping exists in the manifest) are marked `[unknown - not in 2026-05-20 manifest]`. To recompute, run `python benchmark/scripts/ops/master_backup_manifest.py` (writes a new JSON manifest with full 64-char hashes).',
       '',
       '## §1 Partition overview',
       '',
       '| Partition | Role | File count | Total size | Key entry-points |',
       '|---|---|---:|---:|---|',
       f'| `raw/` | Third-party + mining outputs (gitignored mirrors) | {part_count["raw"]} | {fmt_size(part_size["raw"])} | `raw/README.md`, `loghub/`, `opseval/`, `lemma_rca/` |',
       f'| `intermediate/` | Processed datasets + candidates (tracked) | {part_count["intermediate"]} | {fmt_size(part_size["intermediate"])} | `intermediate/README.md`, `datasets/benchmark_431_seed42.json` |',
       f'| `final/` | Paper-ready results + audit + docs | {part_count["final"]} | {fmt_size(part_size["final"])} | `final/SUMMARY.md`, `final/MANIFEST.md`, `final/AUDIT_REPORT.md`, `final/audit/`, `final/docs/` |',
       f'| `archive/` | Historical / superseded artifacts | {part_count["archive"]} | {fmt_size(part_size["archive"])} | `archive/README.md`, `originals_2026-05-19/`, `v0.9.1_jarvis_baseline/` |',
       f'| `scripts/` | 34 Python scripts in 5 sub-folders + README | {part_count["scripts"]} | {fmt_size(part_size["scripts"])} | `scripts/README.md`, `prep/`, `run/`, `eval/`, `ops/`, `_dev/` |',
       f'| **TOTAL** | | **{total_count}** | **{fmt_size(total_size)}** | |',
       '',
       'Walk methodology: `find benchmark -type f` (excluding `__pycache__`, `.git`, `node_modules`). Files in `raw/` are gitignored but present on disk; counted here.',
       '',
       '## §2 Per-file index',
       '',
       'Grouped by partition. Within each partition rows are sorted alphabetically by path. Status legend: `active` = paper-evidence pipeline reads it; `historical` = forensic / superseded; `dev` = smoke / debug; `sealed-forensic` = do-not-modify session-12 forensic; `unknown` = role could not be inferred.',
       '',
]

# Build sections per partition
for p in ['raw', 'intermediate', 'final', 'archive', 'scripts', 'other']:
    sub = [r for r in rows if partition(r['path']) == p]
    if not sub: continue
    sub.sort(key=lambda r: r['path'])
    OUT.append(f'### §2.{p} — `{p}/` ({len(sub)} files, {fmt_size(sum(r["size"] for r in sub))})')
    OUT.append('')
    OUT.append('| Path | Role | Status | Size | Last-modified | SHA-256[:12] |')
    OUT.append('|---|---|---|---:|---|---|')
    for r in sub:
        sha = r['sha'] if r['sha'] != '[unknown]' else '`[unknown - not in 2026-05-20 manifest]`'
        if r['sha'] != '[unknown]':
            sha = '`' + sha + '`'
        mtime_short = r['mtime'].split('.')[0]  # drop subseconds
        OUT.append(f'| `{r["path"]}` | {r["role"]} | {r["status"]} | {fmt_size(r["size"])} | {mtime_short} | {sha} |')
    OUT.append('')

# Delta sections
OUT.append('## §3 Delta vs 2026-05-20 baseline')
OUT.append('')
OUT.append('Baseline = `MASTER_BACKUP_MANIFEST_2026-05-20.json` (493 entries, full filesystem) + `CV_PASS2_CODEBASE_AUDIT.md` Part B (491 git-tracked entries). The 2-file gap between the two baselines reflects 2 files that were on disk but not git-tracked at 2026-05-20 (`.benchmark_step2_complete` and `.progress.json`).')
OUT.append('')
OUT.append('### §3.1 Added since baseline (file in current tree, not in baseline)')
OUT.append('')
OUT.append('| Path | Size | Role / guess |')
OUT.append('|---|---:|---|')
for path, sz in sorted(added):
    r_info = next((rr for rr in rows if rr['path'] == path), None)
    role_s = r_info['role'] if r_info else 'unknown'
    OUT.append(f'| `{path}` | {fmt_size(sz)} | {role_s} |')
OUT.append('')
OUT.append(f'**Total added: {len(added)} files.** All are documentation / metadata: 5 partition READMEs created during the 2026-05-20 reorg, 4 session handoffs (SESSION_12-15), the reorg proposal, the reorg note in originals/, and the MASTER_BACKUP_MANIFEST itself (which was generated AT 2026-05-20 and so appears in its own contents only as a post-baseline artifact).')
OUT.append('')
OUT.append('### §3.2 Deleted since baseline (in baseline, not in current tree)')
OUT.append('')
OUT.append('| Path (baseline) | Last-known SHA-256[:12] | Size | Reason / replacement |')
OUT.append('|---|---|---:|---|')
delete_reasons = {
    'benchmark/results_aws/FILE_PROVENANCE.md': 'moved → `final/docs/_archived_session_history/FILE_PROVENANCE.md`',
    'benchmark/results_aws/RESULTS_SUMMARY.md': 'moved → `final/docs/_archived_session_history/RESULTS_SUMMARY.md`',
    'benchmark/results_aws/RUNS_INDEX.md': 'moved → `final/docs/_archived_session_history/RUNS_INDEX.md`',
    'benchmark/results_aws/FINAL/BUG_HISTORY.md': 'deduplicated; canonical at `final/docs/BUG_HISTORY.md`',
    'benchmark/results_aws/FINAL/METHODOLOGY.md': 'deduplicated; canonical at `final/docs/METHODOLOGY.md`',
}
for path, sha, sz in deleted:
    reason = delete_reasons.get(path, 'build artifact (Python `__pycache__/*.pyc`) — not needed in source tree')
    OUT.append(f'| `{path}` | `{sha}` | {fmt_size(sz)} | {reason} |')
OUT.append('')
OUT.append(f'**Total deleted: {len(deleted)} files.** Breakdown: 5 documentation files were moved/deduplicated under the 4-partition reorg (locations preserved or content unchanged), and 8 are Python bytecode files (`__pycache__/*.pyc`) that should not be in the source tree.')
OUT.append('')
OUT.append('### §3.3 Possibly modified (same path-mapping, mtime newer than 2026-05-20)')
OUT.append('')
OUT.append('`mtime > 2026-05-20` means the file has been touched on disk since the manifest was generated. This does NOT prove content change — `touch` updates mtime without changing content. To detect actual content drift, re-run `python benchmark/scripts/ops/master_backup_manifest.py` and diff the new SHA-256 against the baseline. Files below either had content changes during sessions 13–15, or were re-touched by a build/move operation.')
OUT.append('')
OUT.append('| Path | Baseline SHA-256[:12] | Current mtime |')
OUT.append('|---|---|---|')
for path, sha, mt in sorted(modified):
    OUT.append(f'| `{path}` | `{sha}` | {mt.split(".")[0]} |')
OUT.append('')
OUT.append(f'**Total possibly-modified: {len(modified)} files.** Most are in `final/` (docs + ablation_v4/main_benchmark READMEs touched during the session-14 Stage J reflow + matched_eval_table regen) or `scripts/` (sub-folder moves on 2026-05-20 + session-14 source-of-truth re-touches).')
OUT.append('')

OUT.append('## §4 Cross-references')
OUT.append('')
OUT.append('- For per-file SHA-256 of paper-evidence files in `final/` (47 files at FINAL build time): see [`final/MANIFEST.md`](final/MANIFEST.md)')
OUT.append('- For per-file content audit of `final/` (record counts, missing fields, BERT-zero scan): see [`final/AUDIT_REPORT.md`](final/AUDIT_REPORT.md)')
OUT.append('- For 34-script breakdown by sub-folder (`prep/run/eval/ops/_dev`): see [`scripts/README.md`](scripts/README.md)')
OUT.append('- For canonical results landscape + Phase 5 statistics: see [`final/SUMMARY.md`](final/SUMMARY.md)')
OUT.append('- For forensic per-file metadata as of 2026-05-20 (491 git-tracked files with first-add/last-modify commits + flags): see [`final/audit/CV_PASS2_CODEBASE_AUDIT.md`](final/audit/CV_PASS2_CODEBASE_AUDIT.md) Part B')
OUT.append('- For pre-zip SHA-256 manifest of every file at 2026-05-20 (493 files): see [`final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json`](final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json)')
OUT.append('- For the 4-partition reorg plan + rationale: see [`final/audit/REORG_PROPOSAL_2026-05-20.md`](final/audit/REORG_PROPOSAL_2026-05-20.md)')
OUT.append('- For session-by-session handoff docs: see [`final/audit/SESSION_12_HANDOFF.md`](final/audit/SESSION_12_HANDOFF.md), [`13`](final/audit/SESSION_13_HANDOFF.md), [`14`](final/audit/SESSION_14_HANDOFF.md), [`15`](final/audit/SESSION_15_HANDOFF.md)')
OUT.append('- For runbook / methodology / bug history: see [`final/docs/METHODOLOGY.md`](final/docs/METHODOLOGY.md), [`BUG_HISTORY.md`](final/docs/BUG_HISTORY.md), [`BROKEN_ABLATIONS.md`](final/docs/BROKEN_ABLATIONS.md), [`CURRENT_RUNS.md`](final/docs/CURRENT_RUNS.md)')
OUT.append('')

OUT.append('## §5 Memory-update suggestion')
OUT.append('')
OUT.append('Suggested addition to `C:/Users/partha/.claude/projects/c--Users-partha-Downloads-files-AIOPS-NEW/memory/MEMORY.md` under "Hard pointers (updated 2026-05-20 - POST-REORG + POST-SUB-FOLDER paths)":')
OUT.append('')
OUT.append('```markdown')
OUT.append('- **Master `benchmark/` index** (canonical entry-point as of 2026-05-25): `benchmark/INDEX.md` - 422-file index with per-file role/status/SHA/mtime, partition tally, delta-vs-2026-05-20-baseline. Regenerate whenever files are added/removed/moved under `benchmark/`.')
OUT.append('```')
OUT.append('')

# Write INDEX.md
out_path = 'c:/Users/partha/Downloads/files AIOPS NEW/constitutional-aiops/benchmark/INDEX.md'
with open(out_path, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT))
print('WROTE:', out_path, 'lines:', len(OUT))
