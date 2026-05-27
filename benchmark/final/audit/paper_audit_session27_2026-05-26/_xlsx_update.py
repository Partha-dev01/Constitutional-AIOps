"""xlsx update script for session 32."""
import openpyxl, os, json
from openpyxl.styles import Font

xlsx_path = r'c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\REFERENCE PAPERS\AIOps_References_Complete.xlsx'
wb = openpyxl.load_workbook(xlsx_path)
ws = wb['References']

change_log = []

# Phase 1: Add Status/Action/Notes cols
if ws.cell(1, 10).value is None:
    ws.cell(1, 10, 'Status')
    ws.cell(1, 11, 'Action')
    ws.cell(1, 12, 'Notes')
    for c in [10, 11, 12]:
        ws.cell(1, c).font = Font(bold=True)
    change_log.append(('header', '', 'Added cols Status/Action/Notes', 'OK'))

def find_row(key):
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 2).value == key:
            return r
    return None

csv_status_map = {
    'zhang2024aiopssurvey': 'cited',
    'wang2024scaling': 'xlsx-only-superseded',
    'roy2024exploring': 'xlsx-only-historical',
    'chen2024aiopslab': 'cited',
    'anthropic2024multiagent': 'xlsx-only-historical',
    'anokhin2024arigraph': 'cited',
    'hu2024memtree': 'xlsx-only-historical',
    'tulving1983episodic': 'xlsx-only-historical',
    'bai2022constitutional': 'cited',
    'askell2024collective': 'cited',
    'chen2024autonomous': 'dropped-from-bib',
    'li2024opseval': 'cited',
    'chen2024rcagent': 'cited',
    'microsoft2025triangle': 'xlsx-only-historical',
    'moya2025': 'xlsx-only-historical',
    'sabharwal2025mem0': 'xlsx-only-historical',
    'botvinick2024episodic': 'xlsx-only-historical',
    'park2025latent': 'xlsx-only-historical',
    'pan2023llmlingua': 'xlsx-only-historical',
    'huang2024recurrentcompression': 'xlsx-only-historical',
    'liu2024tokencompression': 'xlsx-only-historical',
    'infoworld2024dualagent': 'xlsx-only-historical',
    'jiang2024longllmlingua': 'xlsx-only-historical',
    'wang2024emllm': 'xlsx-only-historical',
    'ge2024visioncompression': 'xlsx-only-historical',
    'zhang2024llmcompression': 'xlsx-only-historical',
    'notaro2021aiopssurvey': 'cited',
    'patel2024practicalaiops': 'xlsx-only-historical',
    'rodriguez2023graphnns': 'xlsx-only-historical',
    'bernandez2024gnnet': 'xlsx-only-historical',
    'scarselli2008gnn': 'xlsx-only-historical',
    'shan2024llmalert': 'xlsx-only-historical',
    'grafana2024loki': 'cited',
    'grafana2024tempo': 'xlsx-only-historical',
    'grafana2024mimir': 'xlsx-only-historical',
    'opentelemetry2024': 'cited',
    'alibaba2024qwen': 'cited',
    'anthropic2024mcp': 'xlsx-only-historical',
    'observability2023evolution': 'xlsx-only-historical',
    'nguyen2024networksec': 'xlsx-only-historical',
    'wu2020microrank': 'cited',
    'chen2022automap': 'cited',
    'meta2024aiops': 'xlsx-only-historical',
    'google2024sre': 'xlsx-only-historical',
    'amazon2024mlops': 'xlsx-only-historical',
    'neo4j2024monitoring': 'xlsx-only-historical',
    'elasticsearch2024integration': 'xlsx-only-historical',
}

for r in range(2, ws.max_row + 1):
    key = ws.cell(r, 2).value
    if key in csv_status_map:
        ws.cell(r, 10, csv_status_map[key])

# askell2024collective -> huang2024collective
r = find_row('askell2024collective')
if r:
    old_key = ws.cell(r, 2).value
    old_auth = ws.cell(r, 3).value
    ws.cell(r, 2, 'huang2024collective')
    ws.cell(r, 3, 'Huang, Saffron and Siddarth, Divya and Lovitt, Liane and others')
    ws.cell(r, 10, 'cited')
    ws.cell(r, 12, 'Renamed in Gate 34 (session 31) - was: ' + old_key + '; reason: lead-author surname match (Saffron Huang is true lead per source). Batch C author corrected in session 30 Gate 30.')
    change_log.append((r, old_key, 'Key->huang2024collective; Authors updated; Status=cited', 'OK'))

# chen2024autonomous (preserve audit trail, mark dropped)
r = find_row('chen2024autonomous')
if r:
    ws.cell(r, 10, 'dropped-from-bib')
    ws.cell(r, 12, 'Phase 4 L3 substitution session 31 Gate 33; bib entry dropped; cite{} reassigned to bai2022constitutional. Placeholder entry; v1 had it but no real paper matches the cited claim. User-provided arXiv 2411.14155 verified to be Leahy et al. on robotics (unrelated).')
    change_log.append((r, 'chen2024autonomous', 'Status=dropped-from-bib + Notes added', 'OK'))

# li2024opseval -> liu2024opseval
r = find_row('li2024opseval')
if r:
    old_key = ws.cell(r, 2).value
    ws.cell(r, 2, 'liu2024opseval')
    ws.cell(r, 3, 'Liu, Yuhe and Pei, Changhua and Sun, Yongqian and others')
    ws.cell(r, 4, "OpsEval: A Comprehensive Benchmark Suite for Evaluating Large Language Models' Capability in IT Operations Domain")
    ws.cell(r, 10, 'cited')
    ws.cell(r, 12, 'Renamed in Gate 34 (session 31) - was: ' + old_key + '; reason: lead-author surname match (Yuhe Liu is true lead). Batch B authors+title subtitle corrected in session 30 Gate 29.')
    change_log.append((r, old_key, 'Key->liu2024opseval; Authors+Title updated; Status=cited', 'OK'))

# chen2024rcagent -> wang2024rcagent
r = find_row('chen2024rcagent')
if r:
    old_key = ws.cell(r, 2).value
    ws.cell(r, 2, 'wang2024rcagent')
    ws.cell(r, 3, 'Wang, Zefan and Liu, Zichuan and Zhang, Yingying')
    ws.cell(r, 10, 'cited')
    ws.cell(r, 12, 'Renamed in Gate 34 (session 31) - was: ' + old_key + '; reason: lead-author surname match (Zefan Wang is true lead). Batch B 3-author block corrected in session 30 Gate 29.')
    change_log.append((r, old_key, 'Key->wang2024rcagent; Authors updated; Status=cited', 'OK'))

# notaro2021aiopssurvey - venue + DOI primary
r = find_row('notaro2021aiopssurvey')
if r:
    old_venue = ws.cell(r, 5).value
    old_prim = ws.cell(r, 7).value
    old_alt = ws.cell(r, 8).value
    ws.cell(r, 3, 'Notaro, Paolo and Cardoso, Jorge and Gerndt, Michael')
    ws.cell(r, 5, 'ACM Trans. TIST 12(6)')
    new_prim = 'https://doi.org/10.1145/3483424'
    new_alt = old_prim if old_prim else old_alt
    ws.cell(r, 7, new_prim)
    ws.cell(r, 8, new_alt)
    ws.cell(r, 10, 'cited')
    ws.cell(r, 12, 'Phase 4 (session 31 Gate 33) - institutional fetch resolved. Venue corrected: "' + str(old_venue) + '" -> "ACM Trans. TIST 12(6)". DOI 10.1145/3483424 set as primary; arXiv moved to alt. Vol/number dropped per min-viable rule.')
    change_log.append((r, 'notaro2021aiopssurvey', 'Venue+Primary updated; Status=cited', 'OK'))

# wu2020microrank - Batch A author update
r = find_row('wu2020microrank')
if r:
    ws.cell(r, 3, 'Yu, Guangba and Chen, Pengfei and Chen, Hongyang and Guan, Zijie and others')
    ws.cell(r, 10, 'cited')
    ws.cell(r, 12, 'Batch A (session 30 Gate 28) author correction; year was already 2021.')
    change_log.append((r, 'wu2020microrank', 'Authors updated; Status=cited', 'OK'))

# chen2022automap - Batch A author+year
r = find_row('chen2022automap')
if r:
    old_year = ws.cell(r, 6).value
    ws.cell(r, 3, 'Ma, Meng and Wang, Ping and Xu, Jingmin and Wang, Yuan and Chen, Pengfei and Zhang, Zonghua')
    ws.cell(r, 5, 'WWW 2020')
    ws.cell(r, 6, 2020)
    ws.cell(r, 10, 'cited')
    ws.cell(r, 12, 'Batch A (session 30 Gate 28) author+year+venue correction: year ' + str(old_year) + ' -> 2020.')
    change_log.append((r, 'chen2022automap', 'Authors + Year + Venue updated; Status=cited', 'OK'))

max_existing = ws.max_row
print('After in-place updates, max_row =', max_existing, 'max_col =', ws.max_column)

# Collect current keys
existing_keys = set()
for r in range(2, ws.max_row + 1):
    k = ws.cell(r, 2).value
    if k:
        existing_keys.add(k)

# New rows for bib entries not in xlsx + leahy
new_rows = [
    ('datadog2024observability', '{Datadog}', 'State of Observability 2024', 'Datadog Technical Report', 2024,
     'https://www.datadoghq.com/state-of-observability/', '', 'Misc', 'cited', '',
     'NEW (from Stage 1a CSV row 48). Bib entry datadog2024observability.'),
    ('guo2017calibration', 'Guo, Chuan and Pleiss, Geoff and Sun, Yu and Weinberger, Kilian Q.',
     'On Calibration of Modern Neural Networks',
     'Proceedings of the 34th International Conference on Machine Learning (ICML)', 2017,
     'https://arxiv.org/abs/1706.04599', 'https://proceedings.mlr.press/v70/guo17a.html', 'Conference', 'cited', '',
     'NEW (from Stage 1a CSV row 49).'),
    ('bansal2021does', 'Bansal, Gagan and Wu, Tongshuang and Zhou, Joyce and others',
     'Does the Whole Exceed its Parts? The Effect of AI Explanations on Complementary Team Performance',
     'Proc. CHI', 2021,
     'https://dl.acm.org/doi/10.1145/3411764.3445717', 'https://arxiv.org/abs/2103.13243', 'Conference', 'cited', '',
     'NEW (from Stage 1a CSV row 50). Batch C (session 30 Gate 30) title 1-word correction: Confidence -> Explanations.'),
    ('cncf2024survey', '{Cloud Native Computing Foundation}', 'CNCF Annual Survey 2024',
     'CNCF Technical Report', 2024,
     'https://www.cncf.io/reports/cncf-annual-survey-2024/', 'https://www.cncf.io/reports/', 'Misc', 'cited', '',
     'NEW (from Stage 1a CSV row 51).'),
    ('reimers2019sentence', 'Reimers, Nils and Gurevych, Iryna',
     'Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks',
     'Proc. EMNLP-IJCNLP', 2019,
     'https://arxiv.org/abs/1908.10084', 'https://aclanthology.org/D19-1410/', 'Conference', 'cited', '',
     'NEW (from Stage 1a CSV row 52).'),
    ('lewis2020retrieval', 'Lewis, Patrick and Perez, Ethan and Piktus, Aleksandra and others',
     'Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks',
     'Advances in Neural Information Processing Systems (NeurIPS)', 2020,
     'https://arxiv.org/abs/2005.11401',
     'https://papers.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html', 'Conference', 'cited', '',
     'NEW (from Stage 1a CSV row 53).'),
    ('thakur2021beir', 'Thakur, Nandan and Reimers, Nils and Rueckle, Andreas and others',
     'BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models',
     'Proc. NeurIPS', 2021,
     'https://arxiv.org/abs/2104.08663', 'https://openreview.net/forum?id=wCu6T5xFjeJ', 'Conference', 'cited', '',
     'NEW (from Stage 1a CSV row 54).'),
    ('parasuraman2000model', 'Parasuraman, Raja and Sheridan, Thomas B. and Wickens, Christopher D.',
     'A Model for Types and Levels of Human Interaction with Automation',
     'IEEE Transactions on Systems, Man, and Cybernetics---Part A: Systems and Humans', 2000,
     'https://doi.org/10.1109/3468.844354', 'https://ieeexplore.ieee.org/document/844354', 'Journal', 'cited', '',
     'NEW (from Stage 1a CSV row 55).'),
    ('zhang2020effect', 'Zhang, Yunfeng and Liao, Q. Vera and Bellamy, Rachel K. E.',
     'Effect of Confidence and Explanation on Accuracy and Trust Calibration in AI-Assisted Decision Making',
     'Proceedings of the 2020 Conference on Fairness, Accountability, and Transparency (FAT*)', 2020,
     'https://dl.acm.org/doi/10.1145/3351095.3372852', 'https://arxiv.org/abs/2001.02114', 'Conference',
     'orphan-retained', '', 'NEW (from Stage 1a CSV row 56). Retained uncited per session-26 stable-label rule.'),
    ('zhu2023loghub', 'Zhu, Jieming and He, Shilin and Liu, Jinyang and others',
     'Loghub: A Large Collection of System Log Datasets towards Automated Log Analytics',
     'arXiv:2008.06448', 2023,
     'https://arxiv.org/abs/2008.06448', 'https://github.com/logpai/loghub', 'Journal', 'cited', '',
     'NEW (from Stage 1a CSV row 57).'),
    ('lemma2024rca', '{LEMMA-RCA}',
     'A Large Multi-modal Multi-domain Dataset for Root Cause Analysis',
     'HuggingFace Dataset', 2024,
     'https://huggingface.co/datasets/LEMMA-RCA', 'https://arxiv.org/abs/2406.05375', 'Misc', 'cited', '',
     'NEW (from Stage 1a CSV row 58).'),
    ('bertscore2020', 'Zhang, Tianyi and Kishore, Varsha and Wu, Felix and Weinberger, Kilian Q. and Artzi, Yoav',
     'BERTScore: Evaluating Text Generation with BERT',
     'Proceedings of the International Conference on Learning Representations (ICLR)', 2020,
     'https://arxiv.org/abs/1904.09675', 'https://openreview.net/forum?id=SkeHuCVFDr', 'Conference', 'cited', '',
     'NEW (from Stage 1a CSV row 59).'),
    ('christakopoulou2024talker', 'Christakopoulou, Konstantina and others',
     'Talker-Reasoner: A Dual-Process Framework for Conversational Agents', '', 2024,
     'https://arxiv.org/abs/2410.08328',
     'https://research.google/pubs/talker-reasoner-a-dual-process-framework-for-conversational-agents/', 'Misc',
     'cited', '', 'NEW (from Stage 1a CSV row 60).'),
    ('xu2025openrca', 'Xu, Junjielong and Zhang, Qinan and Zhong, Zhiqing and He, Shilin and others',
     'OpenRCA: Can Large Language Models Locate the Root Cause of Software Failures?',
     'Proceedings of the International Conference on Learning Representations (ICLR)', 2025,
     'https://openreview.net/forum?id=M4qNIzQYpd', 'https://github.com/microsoft/OpenRCA', 'Conference', 'cited', '',
     'NEW (from Stage 1a CSV row 61). Batch B (session 30 Gate 29) author lead corrected to Junjielong Xu + title rewritten. Key not renamed (lead-author surname Xu already matches).'),
    ('pei2025flowofaction', 'Pei, Changhua and Wang, Zexin and Liu, Fengrui and others',
     'Flow-of-Action: SOP Enhanced LLM-Based Multi-Agent System for Root Cause Analysis',
     'Proceedings of The ACM Web Conference (WWW)', 2025,
     'https://dl.acm.org/doi/10.1145/3696410.3714932', 'https://arxiv.org/abs/2502.08820', 'Conference', 'cited', '',
     'NEW (from Stage 1a CSV row 62). Batch C (session 30 Gate 30) authors+subtitle corrected. Key not renamed (lead-author surname Pei already matches).'),
    ('cui2025logeval', 'Cui, Tianyu and Ma, Shiyu and Chen, Ziang and others',
     'LogEval: A Comprehensive Benchmark Suite for Large Language Models in Log Analysis',
     'Empirical Software Engineering', 2025,
     'https://doi.org/10.1007/s10664-025-10600-0', 'https://arxiv.org/abs/2407.01896', 'Journal', 'cited', '',
     'NEW (from Stage 1a CSV row 63 - was liu2025logeval). Renamed in Gate 34 (session 31): liu2025logeval -> cui2025logeval (lead-author surname match). Batch B (session 30 Gate 29) author lead corrected to Tianyu Cui.'),
    ('miller2025bootstrap', 'Miller, Evan',
     'Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations',
     'arXiv (techreport)', 2024,
     'https://arxiv.org/abs/2411.00640', '', 'Technical Report', 'cited', '',
     'NEW (from Stage 1a CSV row 64). Batch A (session 30 Gate 28) corrections: author Miller Joshua -> Miller Evan; title Bootstrap CI -> Adding Error Bars; year 2025 -> 2024; arXiv 2503.01747 -> 2411.00640.'),
    ('nvidia2024specdec', 'Li, Jamie and Yu, Chenhan and Guo, Hao',
     'An Introduction to Speculative Decoding for Reducing Latency in AI Inference',
     'NVIDIA Developer Blog', 2025,
     'https://developer.nvidia.com/blog/an-introduction-to-speculative-decoding-for-reducing-latency-in-ai-inference/',
     '', 'Misc', 'cited', '', 'NEW (from Stage 1a CSV row 65).'),
    ('adaspec2025', 'Huang, Kaiyu and Wu, Hao and Shi, Zhubo and Zou, Han and Yu, Minchen and Shi, Qingjiang',
     'AdaSpec: Adaptive Speculative Decoding for Efficient Large Language Model Serving',
     'arXiv (techreport)', 2025,
     'https://arxiv.org/abs/2503.05096', '', 'Technical Report', 'orphan-retained', '',
     'NEW (from Stage 1a CSV row 66). Retained uncited per session-26 stable-label rule. Batch C (session 30 Gate 30) author block corrected (project-name label retained, NOT renamed to surname-based).'),
    ('edge2024graphrag', 'Edge, Darren and Trinh, Ha and Cheng, Newman and others',
     'From Local to Global: A GraphRAG Approach to Query-Focused Summarization',
     'arXiv (techreport)', 2024,
     'https://arxiv.org/abs/2404.16130', 'https://github.com/microsoft/graphrag', 'Technical Report',
     'orphan-retained', '', 'NEW (from Stage 1a CSV row 67). Retained uncited per session-26 stable-label rule.'),
    ('peng2025graphragsurvey', 'Peng, Boci and Zhu, Yun and Liu, Yongchao and others',
     'Graph Retrieval-Augmented Generation: A Survey',
     'ACM Trans. Inf. Syst.', 2026,
     'https://doi.org/10.1145/3777378', 'https://arxiv.org/abs/2408.08921', 'Journal', 'cited', '',
     'NEW (from Stage 1a CSV row 68).'),
    ('leahy2024grandchallenges', 'Leahy, Alexander and Brettschneider, Christopher J. and Wagner, Manfred and others',
     'Grand Challenges in the Verification of Autonomous Systems',
     'IEEE RAS Technical Committee', 2024,
     'https://arxiv.org/abs/2411.14155', '', 'Technical Report', 'downloaded-not-in-bib', '',
     'User-provided arXiv 2411.14155 in session 31 as candidate for chen2024autonomous substitution; verified to be Leahy et al. Grand Challenges in the Verification of Autonomous Systems (IEEE RAS Technical Committee, robotics-domain); retained on disk as unused reference.'),
]

next_idx = max_existing
appended = 0
for tup in new_rows:
    key = tup[0]
    if key in existing_keys:
        change_log.append(('SKIP', key, 'Already in xlsx (renamed previously); not appending', 'SKIPPED'))
        continue
    next_idx += 1
    new_num = next_idx - 1
    ws.cell(next_idx, 1, new_num)
    for c in range(2, 13):
        ws.cell(next_idx, c, tup[c-2])
    appended += 1
    change_log.append((next_idx, key, 'APPENDED new row #' + str(new_num) + ', status=' + tup[8], 'OK'))

print('Rows appended:', appended)
print('Final max_row =', ws.max_row)

wb.save(xlsx_path)
print('Saved:', xlsx_path)

wb2 = openpyxl.load_workbook(xlsx_path)
ws2 = wb2['References']
print('Re-loaded:', ws2.max_row, 'rows x', ws2.max_column, 'cols')

bak = xlsx_path.replace('.xlsx', '.bak_2026-05-27.xlsx')
print('Backup size:', os.path.getsize(bak))
print('Live size:  ', os.path.getsize(xlsx_path))
print('Delta:      +' + str(os.path.getsize(xlsx_path) - os.path.getsize(bak)) + ' bytes')

print()
print('=== CHANGE LOG ===')
for entry in change_log:
    print(' ', entry)

log_path = r'c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\benchmark\final\audit\paper_audit_session27_2026-05-26\_xlsx_change_log.json'
with open(log_path, 'w', encoding='utf-8') as f:
    json.dump([list(e) for e in change_log], f, indent=2, ensure_ascii=False)
print('\nChange log saved:', log_path)
