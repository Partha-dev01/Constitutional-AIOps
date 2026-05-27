"""Per-entry verification of 34 bib entries."""
import os, re, json

bib_path = r'c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\main\sn-bibliography.bib'
tex_path = r'c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\main\sn-article.tex'
ref_dir = r'c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\REFERENCE PAPERS'

bib_txt = open(bib_path, encoding='utf-8').read()
tex_txt = open(tex_path, encoding='utf-8').read()
pdf_files = [f for f in os.listdir(ref_dir) if f.lower().endswith('.pdf')]

entries = []
i = 0
while i < len(bib_txt):
    m = re.search(r'@(\w+)\s*\{\s*([^,\s]+)\s*,', bib_txt[i:])
    if not m: break
    typ, key = m.group(1), m.group(2)
    start = i + m.end()
    depth = 1
    j = start
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

# Entries where no PDF is expected (URL/blog/dataset-only)
pdf_optional = {'opentelemetry2024collector', 'datadog2024observability', 'grafana2024loki', 'nvidia2024specdec'}

results = []
for e in entries:
    key = e['key']
    f = e['fields']
    pattern = re.compile(r'\b' + re.escape(key) + r'\b')
    cite_count = len(pattern.findall(tex_txt))
    is_orphan_expected = key in retained_orphan
    cited_ok = (cite_count == 0) if is_orphan_expected else (cite_count >= 1)

    pdf_match = None
    for fn in pdf_files:
        if key.lower() in fn.lower():
            pdf_match = fn
            break
    if not pdf_match:
        # fallback search by title fragment (alphanum only)
        title_clean = re.sub(r'[^a-z0-9 ]', ' ', f.get('title', '').lower())
        words = [w for w in title_clean.split() if len(w) > 5]
        for fn in pdf_files:
            fn_low = fn.lower()
            for w in words[:3]:
                if w in fn_low:
                    pdf_match = fn
                    break
            if pdf_match:
                break

    pdf_required = key not in pdf_optional
    pdf_ok = pdf_match is not None or not pdf_required

    author = f.get('author', '')
    title = f.get('title', '')
    year = f.get('year', '')
    doi = f.get('doi', '')

    results.append({
        'key': key,
        'type': e['type'],
        'author': author,
        'title': title,
        'year': year,
        'doi': doi,
        'cite_count': cite_count,
        'cited_ok': cited_ok,
        'is_orphan_expected': is_orphan_expected,
        'pdf_match': pdf_match,
        'pdf_required': pdf_required,
        'pdf_ok': pdf_ok,
    })

print('=' * 100)
print(f'{"Key":<30s} {"Cit":>3s} OK PDF? {"DOI":<25s}')
print('=' * 100)
for r in results:
    pdf_status = 'YES' if r['pdf_match'] else ('N/A' if not r['pdf_required'] else 'NO')
    print(f'{r["key"]:<30s} {r["cite_count"]:>3d}  {"Y" if r["cited_ok"] else "N"}  {pdf_status:<4s} {r["doi"][:25]:<25s}')

out = r'c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\benchmark\final\audit\paper_audit_session27_2026-05-26\_per_entry_check.json'
with open(out, 'w', encoding='utf-8') as fh:
    json.dump(results, fh, indent=2, ensure_ascii=False)
print('\nSaved:', out)

issues = [r for r in results if not r['cited_ok'] or (r['pdf_required'] and not r['pdf_match'])]
print(f'\nIssues count: {len(issues)}')
for r in issues:
    print(f'  {r["key"]}: cited_ok={r["cited_ok"]} pdf_match={r["pdf_match"]}')
