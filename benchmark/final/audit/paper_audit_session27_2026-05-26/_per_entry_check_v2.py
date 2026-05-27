"""Per-entry verification v2 with explicit PDF mapping."""
import os, re, json

bib_path = r'c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\main\sn-bibliography.bib'
tex_path = r'c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\main\sn-article.tex'
ref_dir = r'c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\REFERENCE PAPERS'

bib_txt = open(bib_path, encoding='utf-8').read()
tex_txt = open(tex_path, encoding='utf-8').read()
pdf_files = sorted([f for f in os.listdir(ref_dir) if f.lower().endswith('.pdf')])

# parse bib
entries = []
i = 0
while i < len(bib_txt):
    m = re.search(r'@(\w+)\s*\{\s*([^,\s]+)\s*,', bib_txt[i:])
    if not m: break
    typ, key = m.group(1), m.group(2)
    start = i + m.end()
    depth = 1; j = start
    while j < len(bib_txt) and depth > 0:
        if bib_txt[j] == '{': depth += 1
        elif bib_txt[j] == '}': depth -= 1
        j += 1
    body = bib_txt[start:j-1]
    fields = {}
    fpat = re.compile(r'(\w+)\s*=\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|"[^"]*")', re.DOTALL)
    for fm in fpat.finditer(body):
        fname = fm.group(1).lower()
        fval = fm.group(2)[1:-1] if fm.group(2)[0] in '{"' else fm.group(2)
        fields[fname] = fval.strip()
    entries.append({'type': typ, 'key': key, 'fields': fields})
    i = j

retained_orphan = {'adaspec2025', 'edge2024graphrag', 'zhang2020effect'}
pdf_optional = {'opentelemetry2024collector', 'datadog2024observability', 'grafana2024loki', 'nvidia2024specdec', 'cncf2024survey', 'lemma2024rca'}

# Explicit PDF mappings for entries where filename doesn't begin with citekey
EXPLICIT_PDF = {
    'zhang2024aiopssurvey': 'A Survey of AIOps in the Era of Large Language Models - 2507.12472v1.pdf',
    'chen2025aiopslabs': 'AIOPSLAB A HOLISTIC FRAMEWORK TO EVALUATE AI AGENTS FOR - 2501.06706v1.pdf',
    'arigraph2024': 'AriGraph - Learning Knowledge Graph World Models with Episodic Memory for LLM Agents - 2407.04363v3.pdf',
    'bai2022constitutional': 'Constitutional AI Harmlessness from AI Feedback - 2212.08073v1.pdf',
    'wang2024rcagent': 'RCAgent Cloud Root Cause Analysis by Autonomous Agents - 2310.16340v3.pdf',
    # Renamed disk files still on disk under old name:
    'huang2024collective': 'askell2024collective - Collective Constitutional AI - Aligning a Language Model with Public Input - 2406.07814.pdf',
    'liu2024opseval': 'li2024opseval - OpsEval - A Comprehensive IT Operations Benchmark Suite for Large Language Models - 2310.07637.pdf',
    'cui2025logeval': 'liu2025logeval - LogEval - A Comprehensive Benchmark Suite for Large Language Models In Log Analysis - 2407.01896.pdf',
}

def find_pdf(key, title):
    if key in EXPLICIT_PDF:
        fn = EXPLICIT_PDF[key]
        return fn if fn in pdf_files else None
    # exact prefix match (citekey - )
    for fn in pdf_files:
        if fn.lower().startswith(key.lower() + ' '):
            return fn
    # contained key
    for fn in pdf_files:
        if key.lower() in fn.lower():
            return fn
    return None

results = []
for e in entries:
    key = e['key']
    f = e['fields']
    pattern = re.compile(r'\b' + re.escape(key) + r'\b')
    cite_count = len(pattern.findall(tex_txt))
    is_orphan_expected = key in retained_orphan
    cited_ok = (cite_count == 0) if is_orphan_expected else (cite_count >= 1)
    pdf_match = find_pdf(key, f.get('title', ''))
    pdf_required = key not in pdf_optional
    pdf_ok = pdf_match is not None or not pdf_required

    results.append({
        'key': key,
        'type': e['type'],
        'author': f.get('author', ''),
        'title': f.get('title', ''),
        'year': f.get('year', ''),
        'doi': f.get('doi', ''),
        'cite_count': cite_count,
        'cited_ok': cited_ok,
        'is_orphan_expected': is_orphan_expected,
        'pdf_match': pdf_match,
        'pdf_required': pdf_required,
        'pdf_ok': pdf_ok,
    })

print(f'{"Key":<30s} {"Cit":>3s} OK PDF Filename')
print('=' * 130)
for r in results:
    pdf_status = 'YES' if r['pdf_match'] else ('N/A' if not r['pdf_required'] else 'NO ')
    fn = r['pdf_match'] or ''
    print(f'{r["key"]:<30s} {r["cite_count"]:>3d}  {"Y" if r["cited_ok"] else "N"}  {pdf_status} {fn[:80]}')

out = r'c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\benchmark\final\audit\paper_audit_session27_2026-05-26\_per_entry_check_v2.json'
with open(out, 'w', encoding='utf-8') as fh:
    json.dump(results, fh, indent=2, ensure_ascii=False)
print('\nSaved:', out)

issues = [r for r in results if not r['cited_ok'] or (r['pdf_required'] and not r['pdf_match'])]
print(f'\nIssues count: {len(issues)}')
for r in issues:
    print(f'  {r["key"]}: cited_ok={r["cited_ok"]} pdf_match={r["pdf_match"]} pdf_required={r["pdf_required"]}')

# Find PDFs not assigned to any bib key (audit completeness)
assigned_pdfs = set(r['pdf_match'] for r in results if r['pdf_match'])
unassigned = [p for p in pdf_files if p not in assigned_pdfs]
print(f'\nUnassigned PDFs on disk: {len(unassigned)}')
for p in unassigned:
    print(f'  {p}')
