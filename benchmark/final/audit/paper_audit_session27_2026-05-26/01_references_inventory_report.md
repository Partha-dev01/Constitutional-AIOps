# Stage 1a — Reference Inventory Report

**Generated**: 2026-05-26 (session 27)
**Agent**: Stage 1a (general-purpose, read-only on source files)
**Status**: COMPLETE — pending user review

## §0. One-line state

Bib has 35 entries (32 cited, 3 retained-orphan); xlsx has 47 rows of which 14 map to current bib and 33 are historical/superseded; 8 PDFs on disk + 2 out-of-scope files in Extra/.

## §1. Counts

- Bib entries: **35** (expected 35)
- Cited keys via cite-grep: **32** unique (expected 32)
- Retained-orphan keys: **3** (`adaspec2025`, `edge2024graphrag`, `zhang2020effect`)
- xlsx rows: **47** (expected 47)
- xlsx rows mapped to bib (direct or via manual_map): **14**
- xlsx-only rows (not in bib): **33**
- PDFs on disk (top level): **8**
- PDFs on disk (Extra/): **2** (both out-of-scope; 1 is a JFIF image, 1 is unrelated AI ethics paper)

- Cited keys present in bib: **32**

## §2. Per-bib-key inventory (35 entries)

| # | Bib key | Cite status | xlsx row | PDF on disk | Primary URL | Alt URL | Action |
|---|---|---|---|---|---|---|---|
| 1 | `opentelemetry2024collector` | cited | row 36 (key=`opentelemetry2024`) | — | https://opentelemetry.io/ | https://github.com/open-telemetry/opentelemetry-collector | NONE |
| 2 | `datadog2024observability` | cited | — | — | https://www.datadoghq.com/state-of-observability/ | — | DOWNLOAD_FROM_OFFICIAL |
| 3 | `zhang2024aiopssurvey` | cited | row 1 (key=`zhang2024aiopssurvey`) | A Survey of AIOps in the Era of Large Language Models - 2507.12472v1.pdf | https://doi.org/10.1145/3746635 | https://arxiv.org/abs/2507.12472 | NONE |
| 4 | `notaro2021aiopssurvey` | cited | row 27 (key=`notaro2021aiopssurvey`) | — | https://arxiv.org/abs/2010.10772 | https://doi.org/10.1007/s10922-021-09601-z | DOWNLOAD_FROM_OFFICIAL |
| 5 | `chen2024autonomous` | cited | row 11 (key=`chen2024autonomous`) | — | https://dl.acm.org/journal/taos | https://api.crossref.org/works/?query=Towards+Autonomous+IT+Operations+Trust+Safety+Verification | FLAG_AMBIGUITY |
| 6 | `alibaba2024qwen` | cited | row 37 (key=`alibaba2024qwen`) | — | https://arxiv.org/abs/2505.09388 | https://qwenlm.github.io/blog/qwen3/ | DOWNLOAD_FROM_OFFICIAL |
| 7 | `guo2017calibration` | cited | — | — | https://arxiv.org/abs/1706.04599 | https://proceedings.mlr.press/v70/guo17a.html | DOWNLOAD_FROM_OFFICIAL |
| 8 | `bansal2021does` | cited | — | — | https://dl.acm.org/doi/10.1145/3411764.3445717 | https://arxiv.org/abs/2103.13243 | DOWNLOAD_FROM_OFFICIAL |
| 9 | `chen2024rcagent` | cited | row 13 (key=`chen2024rcagent`) | RCAgent Cloud Root Cause Analysis by Autonomous Agents - 2310.16340v3.pdf | https://dl.acm.org/doi/10.1145/3627673.3679718 | https://arxiv.org/abs/2310.16340 | NONE |
| 10 | `wu2020microrank` | cited | row 41 (key=`wu2020microrank`) | — | https://dl.acm.org/doi/10.1145/3442381.3449905 | https://hal.science/hal-03155265 | DOWNLOAD_FROM_OFFICIAL |
| 11 | `chen2022automap` | cited | row 42 (key=`chen2022automap`) | — | https://dl.acm.org/doi/10.1145/3366423.3380111 | https://api.crossref.org/works/10.1145/3366423.3380111 | DOWNLOAD_FROM_OFFICIAL |
| 12 | `arigraph2024` | cited | row 6 (key=`anokhin2024arigraph`) | AriGraph - Learning Knowledge Graph World Models with Episodic Memory for LLM Agents - 2407.04363v3.pdf | https://arxiv.org/abs/2407.04363 | https://www.ijcai.org/proceedings/2025/ | NONE |
| 13 | `bai2022constitutional` | cited | row 9 (key=`bai2022constitutional`) | Constitutional AI Harmlessness from AI Feedback - 2212.08073v1.pdf | https://arxiv.org/abs/2212.08073 | https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback | NONE |
| 14 | `askell2024collective` | cited | row 10 (key=`askell2024collective`) | — | https://dl.acm.org/doi/10.1145/3630106.3658979 | https://arxiv.org/abs/2406.07814 | DOWNLOAD_FROM_OFFICIAL |
| 15 | `grafana2024loki` | cited | row 33 (key=`grafana2024loki`) | — | https://grafana.com/docs/loki/latest/ | https://github.com/grafana/loki | NONE |
| 16 | `cncf2024survey` | cited | — | — | https://www.cncf.io/reports/cncf-annual-survey-2024/ | https://www.cncf.io/reports/ | DOWNLOAD_FROM_OFFICIAL |
| 17 | `reimers2019sentence` | cited | — | — | https://arxiv.org/abs/1908.10084 | https://aclanthology.org/D19-1410/ | DOWNLOAD_FROM_OFFICIAL |
| 18 | `lewis2020retrieval` | cited | — | — | https://arxiv.org/abs/2005.11401 | https://papers.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html | DOWNLOAD_FROM_OFFICIAL |
| 19 | `thakur2021beir` | cited | — | — | https://arxiv.org/abs/2104.08663 | https://openreview.net/forum?id=wCu6T5xFjeJ | DOWNLOAD_FROM_OFFICIAL |
| 20 | `parasuraman2000model` | cited | — | — | https://doi.org/10.1109/3468.844354 | https://ieeexplore.ieee.org/document/844354 | DOWNLOAD_FROM_ANNAS |
| 21 | `zhang2020effect` | orphan-retained | — | — | https://dl.acm.org/doi/10.1145/3351095.3372852 | https://arxiv.org/abs/2001.02114 | DOWNLOAD_FROM_OFFICIAL |
| 22 | `zhu2023loghub` | cited | — | — | https://arxiv.org/abs/2008.06448 | https://github.com/logpai/loghub | DOWNLOAD_FROM_OFFICIAL |
| 23 | `li2024opseval` | cited | row 12 (key=`li2024opseval`) | — | https://arxiv.org/abs/2310.07637 | https://dl.acm.org/doi/10.1145/3663529.3663849 | DOWNLOAD_FROM_OFFICIAL |
| 24 | `lemma2024rca` | cited | — | — | https://huggingface.co/datasets/LEMMA-RCA | https://arxiv.org/abs/2406.05375 | DOWNLOAD_FROM_OFFICIAL |
| 25 | `bertscore2020` | cited | — | — | https://arxiv.org/abs/1904.09675 | https://openreview.net/forum?id=SkeHuCVFDr | DOWNLOAD_FROM_OFFICIAL |
| 26 | `christakopoulou2024talker` | cited | — | — | https://arxiv.org/abs/2410.08328 | https://research.google/pubs/talker-reasoner-a-dual-process-framework-for-conversational-agents/ | DOWNLOAD_FROM_OFFICIAL |
| 27 | `shi2025aiopslabs` | cited | row 4 (key=`chen2024aiopslab`) | AIOPSLAB A HOLISTIC FRAMEWORK TO EVALUATE AI AGENTS FOR - 2501.06706v1.pdf | https://arxiv.org/abs/2501.06706 | https://proceedings.mlsys.org/paper_files/paper/2025/ | NONE |
| 28 | `xu2025openrca` | cited | — | — | https://openreview.net/forum?id=M4qNIzQYpd | https://github.com/microsoft/OpenRCA | DOWNLOAD_FROM_OFFICIAL |
| 29 | `pei2025flowofaction` | cited | — | — | https://dl.acm.org/doi/10.1145/3696410.3714932 | https://arxiv.org/abs/2502.08820 | DOWNLOAD_FROM_OFFICIAL |
| 30 | `liu2025logeval` | cited | — | — | https://doi.org/10.1007/s10664-025-10600-0 | https://arxiv.org/abs/2407.01896 | DOWNLOAD_FROM_OFFICIAL |
| 31 | `miller2025bootstrap` | cited | — | — | https://arxiv.org/abs/2503.01747 | — | DOWNLOAD_FROM_OFFICIAL |
| 32 | `nvidia2024specdec` | cited | — | — | https://developer.nvidia.com/blog/an-introduction-to-speculative-decoding-for-reducing-latency-in-ai-inference/ | — | DOWNLOAD_FROM_OFFICIAL |
| 33 | `adaspec2025` | orphan-retained | — | — | https://arxiv.org/abs/2503.05096 | — | DOWNLOAD_FROM_OFFICIAL |
| 34 | `edge2024graphrag` | orphan-retained | — | — | https://arxiv.org/abs/2404.16130 | https://github.com/microsoft/graphrag | DOWNLOAD_FROM_OFFICIAL |
| 35 | `peng2025graphragsurvey` | cited | — | — | https://doi.org/10.1145/3777378 | https://arxiv.org/abs/2408.08921 | DOWNLOAD_FROM_OFFICIAL |

## §3. xlsx-only rows (in xlsx, not in current bib)

| xlsx row | Key | Title | Year | Type | Status | Rationale |
|---|---|---|---|---|---|---|
| 2 | `wang2024scaling` | Scaling Observability: Managing High-Cardinality Metrics in  | 2024 | Conference | xlsx-only-superseded | Cloud-scale observability paper; superseded by datadog2024observability + cncf2024survey now in bib |
| 3 | `roy2024exploring` | Exploring LLM-based Agents for Root Cause Analysis | 2024 | Conference | xlsx-only-historical | arXiv 2403.04123 — LLM agents for RCA; replaced by chen2024rcagent in bib |
| 5 | `anthropic2024multiagent` | The Prompt Engineering Guide to Multi-Agent Architectures | 2024 | Technical Report | xlsx-only-historical | Internal prompt-engineering guide; dropped from bib as non-essential |
| 7 | `hu2024memtree` | MemTree: Semantic Memory Management with Tree-Structured Mem | 2024 | Preprint | xlsx-only-historical | MemTree (2410.14052) — early memory-architecture candidate; superseded by arigraph2024 + christakopoulou2024talker |
| 8 | `tulving1983episodic` | Elements of Episodic Memory | 1983 | Book | xlsx-only-historical | Foundational episodic memory book; dropped — narrative-only reference, not cited in v2 paper |
| 14 | `microsoft2025triangle` | Triangle: Multi-LLM-Agent Framework for Azure Cloud Operatio | 2025 | Technical Report | xlsx-only-historical | Triangle Azure CloudOps — dropped from bib (alternative framework, not benchmarked) |
| 15 | `moya2025` | MOYA: Multi-Agent Framework for CloudOps Compliance and Secu | 2025 | Preprint | xlsx-only-historical | MOYA CloudOps compliance — dropped from bib (orthogonal compliance angle) |
| 16 | `sabharwal2025mem0` | Mem0: Adaptive Memory Layer for Personalized AI | 2025 | Preprint | xlsx-only-historical | Mem0 adaptive memory — dropped from bib (personalization-focused, not AIOps RCA) |
| 17 | `botvinick2024episodic` | Elements of Episodic Memory: Insights from Artificial Agents | 2024 | Journal | xlsx-only-historical | Botvinick episodic-memory commentary — dropped from bib (narrative-only) |
| 18 | `park2025latent` | Latent Learning: Episodic Memory Complements Parametric Lear | 2025 | Preprint | xlsx-only-historical | Latent learning — dropped from bib (cognitive-science framing, not cited) |
| 19 | `pan2023llmlingua` | LLMLingua: Compressing Prompts for Accelerated Inference of  | 2023 | Conference | xlsx-only-historical | LLMLingua prompt compression — dropped from bib (compression not in scope after v2 refactor) |
| 20 | `huang2024recurrentcompression` | Recurrent Context Compression: Efficiently Expanding the Con | 2024 | Preprint | xlsx-only-historical | Recurrent context compression — dropped from bib (compression out of scope) |
| 21 | `liu2024tokencompression` | Efficient Token Compression Strategies for Large Language Mo | 2024 | Conference | xlsx-only-historical | Token compression strategies — dropped from bib (compression out of scope) |
| 22 | `infoworld2024dualagent` | Building Effective Dual-Agent LLM Systems for Enterprise App | 2024 | Technical Report | xlsx-only-historical | InfoWorld blog dual-agent piece — dropped from bib (industry blog, not load-bearing) |
| 23 | `jiang2024longllmlingua` | LongLLMLingua: Accelerating and Enhancing LLMs in Long Conte | 2024 | Preprint | xlsx-only-historical | LongLLMLingua — dropped from bib (compression out of scope) |
| 24 | `wang2024emllm` | EM-LLM: Surprise-based Episodic Memory for Efficient Large L | 2024 | Preprint | xlsx-only-historical | EM-LLM surprise-based episodic memory — dropped (replaced by arigraph2024 episodic-memory cite) |
| 25 | `ge2024visioncompression` | Vision-centric Token Compression in Large Language Model | 2025 | Preprint | xlsx-only-historical | Vision-centric token compression — dropped (compression+vision out of scope) |
| 26 | `zhang2024llmcompression` | More Effective LLM Compressed Tokens with Uniformly Spread P | 2024 | Preprint | xlsx-only-historical | LLM compressed tokens — dropped (compression out of scope) |
| 28 | `patel2024practicalaiops` | Practical AIOps: Implementation Challenges and Success Facto | 2024 | Conference | xlsx-only-historical | Practical AIOps challenges — dropped (industry framing, superseded by zhang2024aiopssurvey) |
| 29 | `rodriguez2023graphnns` | Graph Neural Networks for Distributed System Monitoring and  | 2023 | Conference | xlsx-only-historical | GNN system monitoring — dropped (GNN angle not used in v2 architecture) |
| 30 | `bernandez2024gnnet` | Graph Neural Networking Challenges: Applications, Challenges | 2024 | Workshop | xlsx-only-historical | GNN networking workshop — dropped (GNN out of scope) |
| 31 | `scarselli2008gnn` | The Graph Neural Network Model | 2009 | Journal | xlsx-only-historical | Original GNN paper — dropped with GNN angle |
| 32 | `shan2024llmalert` | Leveraging Large Language Models for Efficient Alert Aggrega | 2024 | Journal | xlsx-only-historical | LLM alert aggregation — dropped (alerting not in v2 scope) |
| 34 | `grafana2024tempo` | Tempo Documentation - v2.8 | 2024 | Documentation | xlsx-only-historical | Tempo docs — dropped (only Loki retained for log-store discussion) |
| 35 | `grafana2024mimir` | Mimir Documentation - v2.16 | 2024 | Documentation | xlsx-only-historical | Mimir docs — dropped (only Loki retained for log-store discussion) |
| 38 | `anthropic2024mcp` | Model Context Protocol Specification | 2024 | Specification | xlsx-only-historical | MCP spec — dropped (protocol used but not cited as defining work) |
| 39 | `observability2023evolution` | The Evolution of Observability: From Monitoring to AI-Driven | 2023 | Journal | xlsx-only-historical | Generic observability evolution piece — dropped (no specific data load-bearing) |
| 40 | `nguyen2024networksec` | Network Security AIOps for Online Stream Data Monitoring | 2024 | Journal | xlsx-only-historical | Network-security AIOps — dropped (security angle out of scope) |
| 43 | `meta2024aiops` | AI-Powered Incident Management at Meta Scale | 2024 | Blog | xlsx-only-historical | Meta AIOps blog — dropped (industry framing, not load-bearing) |
| 44 | `google2024sre` | Advances in Google SRE: AI-Driven Automation for Reliability | 2024 | Technical Report | xlsx-only-historical | Google SRE AI report — dropped (industry framing, not load-bearing) |
| 45 | `amazon2024mlops` | Machine Learning for Operational Excellence at Amazon Scale | 2024 | Conference | xlsx-only-historical | Amazon MLOps — dropped (vendor-specific, not load-bearing) |
| 46 | `neo4j2024monitoring` | Graph-Based Infrastructure Monitoring at Scale | 2024 | Whitepaper | xlsx-only-historical | Neo4j monitoring whitepaper — dropped (vendor whitepaper, not load-bearing) |
| 47 | `elasticsearch2024integration` | Elasticsearch + Graph Analytics for Root Cause Analysis | 2024 | Documentation | xlsx-only-historical | Elasticsearch+Graph integration — dropped (vendor doc, not load-bearing) |

## §4. PDFs on disk

| Filename | Matched bib key | Confidence | Notes |
|---|---|---|---|
| `A Survey of AIOps in the Era of Large Language Models - 2507.12472v1.pdf` | `zhang2024aiopssurvey` | HIGH | arXiv 2507.12472 = preprint of ACM TOIS survey |
| `AIOPSLAB A HOLISTIC FRAMEWORK TO EVALUATE AI AGENTS FOR - 2501.06706v1.pdf` | `shi2025aiopslabs` | HIGH | arXiv 2501.06706 = AIOpsLab MLSys 2025 |
| `AriGraph - Learning Knowledge Graph World Models with Episodic Memory for LLM Agents - 2407.04363v3.pdf` | `arigraph2024` | HIGH | arXiv 2407.04363 explicitly cited in bib note field |
| `Constitutional AI Harmlessness from AI Feedback - 2212.08073v1.pdf` | `bai2022constitutional` | HIGH | arXiv 2212.08073 = Constitutional AI |
| `Exploring LLM-based Agents for Root Cause Analysis - 2403.04123v1.pdf` | — | NO_MATCH | Not in current bib; xlsx-only candidate (row 3 roy2024exploring) |
| `FROM ISOLATED CONVERSATIONS TO HIERARCHICAL SCHEMAS DYNAMIC TREE MEMORY REPRESENTATION FOR LLMS- 2410.14052v3.pdf` | — | NO_MATCH | arXiv 2410.14052 = MemTree; xlsx row 7 hu2024memtree; not in current bib |
| `High Cardinality at Scale Rethinking Observability for Cloud- - EMA7260-Otel-RR-Apica.pdf` | — | NO_MATCH | Apica/EMA whitepaper; xlsx row 2 wang2024scaling; not in current bib |
| `RCAgent Cloud Root Cause Analysis by Autonomous Agents - 2310.16340v3.pdf` | `chen2024rcagent` | HIGH | arXiv 2310.16340 = RCAgent CIKM 2024 |
| `Extra/Enchanted Determinism Power without Responsibility in Artificial Intelligence, 277-Article Text-1175-1-10-20200108.pdf` | — | NOT_IN_SCOPE | Outside AIOps topic — not in bib or xlsx |
| `Extra/1768055357955.jfif` | — | NOT_IN_SCOPE | Image file (JFIF) — not a PDF reference |

## §5. Action summary by tag

- **DOWNLOAD_FROM_OFFICIAL**: 26 bib entries
  - `datadog2024observability`
  - `notaro2021aiopssurvey`
  - `alibaba2024qwen`
  - `guo2017calibration`
  - `bansal2021does`
  - `wu2020microrank`
  - `chen2022automap`
  - `askell2024collective`
  - `cncf2024survey`
  - `reimers2019sentence`
  - `lewis2020retrieval`
  - `thakur2021beir`
  - `zhang2020effect`
  - `zhu2023loghub`
  - `li2024opseval`
  - `lemma2024rca`
  - `bertscore2020`
  - `christakopoulou2024talker`
  - `xu2025openrca`
  - `pei2025flowofaction`
  - `liu2025logeval`
  - `miller2025bootstrap`
  - `nvidia2024specdec`
  - `adaspec2025`
  - `edge2024graphrag`
  - `peng2025graphragsurvey`
- **NONE**: 7 bib entries
  - `opentelemetry2024collector`
  - `zhang2024aiopssurvey`
  - `chen2024rcagent`
  - `arigraph2024`
  - `bai2022constitutional`
  - `grafana2024loki`
  - `shi2025aiopslabs`
- **FLAG_AMBIGUITY**: 1 bib entries
  - `chen2024autonomous`
- **DOWNLOAD_FROM_ANNAS**: 1 bib entries
  - `parasuraman2000model`

## §6. URL discovery sources used

- **arXiv abs/pdf** (open access; primary for all preprint entries): zhang2024aiopssurvey (2507.12472), shi2025aiopslabs (2501.06706), arigraph2024 (2407.04363), bai2022constitutional (2212.08073), chen2024rcagent (2310.16340), notaro2021aiopssurvey (2010.10772), guo2017calibration (1706.04599), bansal2021does (2103.13243), reimers2019sentence (1908.10084), lewis2020retrieval (2005.11401), thakur2021beir (2104.08663), zhu2023loghub (2008.06448), li2024opseval (2310.07637), lemma2024rca (2406.05375), bertscore2020 (1904.09675), christakopoulou2024talker (2410.08328), pei2025flowofaction (2502.08820), liu2025logeval (2407.01896), miller2025bootstrap (2503.01747), adaspec2025 (2503.05096), edge2024graphrag (2404.16130), peng2025graphragsurvey (2408.08921), alibaba2024qwen (2505.09388 — Qwen3 tech report), askell2024collective (2406.07814).
- **DOI / publisher pages**: zhang2024aiopssurvey (10.1145/3746635 ACM CSUR), peng2025graphragsurvey (10.1145/3777378 ACM TOIS), liu2025logeval (10.1007/s10664-025-10600-0 EmSE), chen2024rcagent (10.1145/3627673.3679718 CIKM), wu2020microrank (10.1145/3442381.3449905 WWW), chen2022automap (10.1145/3366423.3380111 WWW), askell2024collective (10.1145/3630106.3658979 FAccT), bansal2021does (10.1145/3411764.3445717 CHI), zhang2020effect (10.1145/3351095.3372852 FAccT), parasuraman2000model (10.1109/3468.844354 IEEE), pei2025flowofaction (10.1145/3696410.3714932 WWW).
- **Vendor/blog URLs** (misc entries with no DOI): opentelemetry2024collector, datadog2024observability, grafana2024loki, cncf2024survey, lemma2024rca (HuggingFace), nvidia2024specdec (NVIDIA Developer Blog).
- **OpenReview** (ICLR): xu2025openrca, bertscore2020 alt, thakur2021beir alt.
- **CrossRef REST API** noted as ACM-DOI workaround per session-26 lesson (`https://api.crossref.org/works/<DOI>`).

## §7. OPEN QUESTIONS / ambiguities

1. **`chen2024autonomous` (FLAG_AMBIGUITY)** — Bib lists "Chen, David and Williams, Michael" / "ACM Trans. on Autonomous Systems" / 2024 with no DOI or arXiv ID. I could NOT locate this paper via title search in the time-box. Two possibilities: (a) the bib metadata is correct but the paper is recent/un-indexed and needs manual verification by the user; (b) the entry is a placeholder/speculative cite that was never replaced. Recommend user check the cite location in `sn-article.tex` and confirm the actual reference. Cited at line(s) found via cite-grep.
2. **`alibaba2024qwen` arXiv ID** — Qwen3 tech report (year 2025 in bib) most likely corresponds to arXiv 2505.09388 ("Qwen3 Technical Report"), but the bib's `note="Technical Report, Alibaba Cloud"` does not pin a specific arXiv ID. User should confirm 2505.09388 vs. blog-only release before download.
3. **Three PDFs on disk that do NOT map to current bib** — `Exploring LLM-based Agents for Root Cause Analysis` (2403.04123), `MemTree` (2410.14052), `High Cardinality at Scale` (Apica whitepaper). These map to xlsx-only-historical rows (`roy2024exploring`, `hu2024memtree`, `wang2024scaling` respectively) that were dropped from the bib in earlier sessions. User should confirm these PDFs are safe to LEAVE on disk (no action) or relocate to an archive subfolder. They are not needed for the camera-ready paper.
4. **`chen2024rcagent` PDF title mismatch** — On-disk PDF is titled `RCAgent Cloud Root Cause Analysis by Autonomous Agents - 2310.16340v3.pdf` (matches arXiv 2310.16340 v3). Bib title is `RCAgent: Cloud Root Cause Analysis by Autonomous Agents with Tool-Augmented Large Language Models` and venue is `Proc. CIKM`. The arXiv title has the same prefix but the bib title is the published CIKM version — consistent, but if user wants the CIKM camera-ready PDF specifically (not the v3 arXiv), would need DOWNLOAD_FROM_OFFICIAL via DOI 10.1145/3627673.3679718. Currently tagged NONE because the arXiv PDF is on disk and substantively equivalent.
5. **xlsx row 4 `chen2024aiopslab`** is the same paper as bib key `shi2025aiopslabs` (AIOpsLab MLSys 2025) but uses a different first-author cite-key. The bib's `shi2025aiopslabs` matches the arXiv 2501.06706 author order (Shi first). Recommend updating xlsx Key column to `shi2025aiopslabs` to align — minor cosmetic delta proposed in CSV.

## §8. Pointer to draft CSV

See `01_xlsx_delta_proposal.csv` (same dir). Contains all 47 existing xlsx rows + proposed status/action/notes columns. No row deletions are proposed; the 3 retained-orphans are preserved. Bib keys not currently in xlsx are appended as new proposed rows at the bottom.
