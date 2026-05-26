# Stage 1b — Reference PDF Download Manifest

**Generated**: 2026-05-26 → 2026-05-27 (session 27, Stage 1b agent; continuation pass + retry-2 sci-hub pass 2026-05-27)
**Agent**: Stage 1b (general-purpose; curl-first + playwright fallback)
**Status**: PARTIAL — 24/27 downloads complete (+2 from retry-2 sci-hub pass: `wu2020microrank` + `chen2022automap`) + 2 entries still FAILED_MANUAL_NEEDED (`notaro2021aiopssurvey` not in sci-hub DB; `chen2024autonomous` placeholder per Stage 1a FLAG_AMBIGUITY). Vendor pages (4) URL-only. `miller2025bootstrap` correctly resolved to arXiv 2411.00640 (Evan Miller).

## §0. One-line state

24 PDFs newly downloaded and verified (arXiv + OpenReview + CNCF + sci-hub fallback for parasuraman/microrank/automap). 1 conference-paper entry (`notaro2021aiopssurvey`) tried across 3 DOI candidates × 5 sci-hub mirrors but is genuinely not in sci-hub's collection (all mirrors returned "article is not available" / no-iframe / DDoS-Guard); user must manually obtain via institutional ACM access. 1 entry intentionally skipped (FLAG_AMBIGUITY: `chen2024autonomous`). Vendor pages (`opentelemetry2024collector`, `datadog2024observability`, `grafana2024loki`, `nvidia2024specdec`) recorded as URL-only per Stage 1a §5. **Stage 1b continuation pass 1 (2026-05-27)** fixed `miller2025bootstrap` → arXiv 2411.00640 (Evan Miller). **Stage 1b retry-2 sci-hub pass (2026-05-27)** added `wu2020microrank` (DOI 10.1145/3442381.3449905) and `chen2022automap` (DOI 10.1145/3366423.3380111) via sci-hub.ee → sci.bban.top. NEW critical finding: `wu2020microrank` bib metadata is wrong — actual paper's lead author is **Guangba Yu** (Sun Yat-Sen Univ), not Wu, but title matches bib exactly; bib's `author=` field must be corrected in Stage 1c.

## §1. Environment

- Playwright: 1.60.0 (installed; not used in this session — all successes were curl-only)
- Chromium: 148.0.7778.96 (v1223)
- Python: 3.12.6
- curl: 8.9.0 (x86_64-w64-mingw32) Schannel
- MiKTeX pdfinfo + pdftotext available at `C:/Users/partha/AppData/Local/Programs/MiKTeX/miktex/bin/x64/`
- Smoke test status: PASS (pre-flight by main session)

## §2. Stage 1a → Stage 1b corrections applied

**Stage 1a's arXiv IDs were partially wrong** — three of the 22 arxiv-tagged entries pointed at unrelated papers:

| bib_key | Stage 1a arXiv ID | Actual paper at that ID | Correct arXiv ID (Stage 1b) |
|---|---|---|---|
| `notaro2021aiopssurvey` | 2010.10772 | *Semantics-Guided Representation Learning* (CV) | NO arXiv preprint exists |
| `bansal2021does` | 2103.13243 | *The Third Way to Interacting p-form Theories* (hep-th) | **2006.14779** ✓ |
| `wu2020microrank` | 2106.05798 | *Indecomposable Objects in Khovanov-Sazdanovic's...* (math.RT) | NO arXiv preprint exists |
| `chen2022automap` | (stage 1a left blank) | n/a | NO arXiv preprint exists |
| `pei2025flowofaction` | 2502.08820 | *CoALM: A Unified Conversational Agentic Language Model* | **2502.08224** ✓ |
| `miller2025bootstrap` | 2503.01747 | *Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints* by Bowyer/Aitchison/Ivanova | **2411.00640** ✓ — *Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations* by **Evan Miller** (Anthropic), Nov 2024. Retracted Stage 1b's first "correction" to 2412.18860 (Liang Wang — unrelated context-length paper). |

**Action**: Stage 1c (xlsx update) should propagate the correct arXiv IDs for `bansal2021does`, `pei2025flowofaction`, `miller2025bootstrap`. For `miller2025bootstrap`, the bib's `author = "Miller, Joshua and Ruder, Sebastian and others"` is also incorrect — actual sole author is **Evan Miller** (Anthropic). Bib's title "Bootstrap Confidence Intervals for Evaluation Metrics in Natural Language Processing" is a paraphrase; actual paper title is "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations". Bib's year `2025` should be `2024` per arXiv:2411.00640 (1 Nov 2024). Recommend keeping cite-key `miller2025bootstrap` as stable label per session-26 lesson (year-in-key need not match year-in-entry), but update `author`, `title`, `year`, `number` fields. The Bowyer paper at arXiv 2503.01747 is a *different* position paper that *cites* Miller (2024); the bib's intended citation is Miller, not Bowyer.

**Stage 1b first-pass mistake explained**: original Stage 1a recorded arXiv ID 2503.01747 for the entry. First-pass Stage 1b inspected 2503.01747, saw the title mentioned bootstrap/CLT but did not match the bib's paraphrased "Bootstrap Confidence Intervals" title, and **incorrectly substituted** 2412.18860 (Liang Wang "Bootstrap Your Own Context Length") solely on title-substring overlap. Continuation pass 2026-05-27 re-examined: Bowyer's paper text reveals Miller is a *cited* author (E. Miller 2024, arXiv 2411.00640) — that Miller paper IS the intended bib citation (matches surname + topic of bootstrap/CIs for LLM evals). 2411.00640 is now on disk; 2412.18860 was deleted; the spurious 2503.01747 was also briefly downloaded for inspection then deleted.

**Stage 1a's DOI for Notaro was also wrong**: `10.1007/s10922-021-09601-z` resolves to *GlobeSnap (SDN statistics)* by Rathee — NOT the AIOps survey. Correct DOI per CrossRef: **`10.1145/3483424`** (ACM Trans. Intelligent Systems and Technology, 2021).

## §3. Download summary table (27 entries from Stage 1a + 1 ambiguous)

| # | bib_key | Action tag | Status | Source used | Size | Pages | SHA-256 (16) |
|---|---|---|---|---|---|---|---|
| 1 | `opentelemetry2024collector` | NONE (URL-only) | URL_ONLY | https://opentelemetry.io/ | — | — | — |
| 2 | `datadog2024observability` | OFFICIAL (vendor) | URL_ONLY | https://www.datadoghq.com/state-of-observability/ | — | — | — |
| 3 | `zhang2024aiopssurvey` | NONE | SKIP_EXISTS | (already on disk) | 1108667 | — | — |
| 4 | `notaro2021aiopssurvey` | OFFICIAL | **FAILED_MANUAL** | arxiv (wrong ID) → Springer (403) → sci-hub.ee/se/st/ru/ren × 3 DOI candidates all returned "article not in sci-hub" / DDoS-Guard / no-iframe (retry-2 2026-05-27) | — | — | — |
| 5 | `chen2024autonomous` | FLAG_AMBIGUITY | **NOT_ATTEMPTED** | (no source per Stage 1a) | — | — | — |
| 6 | `alibaba2024qwen` | OFFICIAL | OK | arxiv 2505.09388 | 779424 | 35 | 84a5e2b1fa04bb77 |
| 7 | `guo2017calibration` | OFFICIAL | OK | arxiv 1706.04599 | 1349691 | 14 | cb654a65acb785ed |
| 8 | `bansal2021does` | OFFICIAL | OK | arxiv 2006.14779 (Stage 1b correction) | 3420209 | 16 | 9a00f4566bf0b4a8 |
| 9 | `chen2024rcagent` | NONE | SKIP_EXISTS | (already on disk) | 980598 | — | — |
| 10 | `wu2020microrank` | OFFICIAL | OK | sci-hub.ee → sci.bban.top (DOI 10.1145/3442381.3449905, retry-2 2026-05-27; verified by title-match — bib's `author=Wu, Li...` is WRONG, actual lead author Guangba Yu) | 1561388 | 12 | 37fc6fe5adcb5287 |
| 11 | `chen2022automap` | OFFICIAL | OK | sci-hub.ee → sci.bban.top (DOI 10.1145/3366423.3380111, retry-2 2026-05-27) | 17193728 | 13 | a257b6d168e64113 |
| 12 | `arigraph2024` | NONE | SKIP_EXISTS | (already on disk) | 5036614 | — | — |
| 13 | `bai2022constitutional` | NONE | SKIP_EXISTS | (already on disk) | 2088111 | — | — |
| 14 | `askell2024collective` | OFFICIAL | OK | arxiv 2406.07814 | 2767196 | 23 | bf59c3f9a5c569b7 |
| 15 | `grafana2024loki` | NONE (URL-only) | URL_ONLY | https://grafana.com/docs/loki/latest/ | — | — | — |
| 16 | `cncf2024survey` | OFFICIAL | OK | cncf.io/wp-content PDF | 3662017 | 39 | 2c9f3fbcddcd8c41 |
| 17 | `reimers2019sentence` | OFFICIAL | OK | arxiv 1908.10084 | 548961 | 11 | 92366d22fc052135 |
| 18 | `lewis2020retrieval` | OFFICIAL | OK | arxiv 2005.11401 | 885323 | 19 | 23e3249e9a1e7541 |
| 19 | `thakur2021beir` | OFFICIAL | OK | arxiv 2104.08663 | 2094824 | 24 | 1925755aeb627123 |
| 20 | `parasuraman2000model` | ANNAS | OK | sci-hub.ee → sci.bban.top (Anna's mirrors blocked at network layer) | 160136 | 12 | 96225ab69b539352 |
| 21 | `zhang2020effect` | OFFICIAL (orphan-retained) | OK | arxiv 2001.02114 | 671555 | 11 | 1a66373b8d916bcb |
| 22 | `zhu2023loghub` | OFFICIAL | OK | arxiv 2008.06448 | 677222 | 12 | a0d116b2f43e7eb4 |
| 23 | `li2024opseval` | OFFICIAL | OK | arxiv 2310.07637 | 1628110 | 11 | 8ad512b1e4e02c65 |
| 24 | `lemma2024rca` | OFFICIAL | OK | arxiv 2406.05375 | 2499452 | 17 | 14845c9c72ed1a83 |
| 25 | `bertscore2020` | OFFICIAL | OK | arxiv 1904.09675 | 2197308 | 43 | 9796d7a74e978bcc |
| 26 | `christakopoulou2024talker` | OFFICIAL | OK | arxiv 2410.08328 | 1097030 | 11 | 14973ffd504ed842 |
| 27 | `shi2025aiopslabs` | NONE | SKIP_EXISTS | (already on disk) | 809427 | — | — |
| 28 | `xu2025openrca` | OFFICIAL | OK | openreview M4qNIzQYpd | 1110745 | 29 | 3cd926feb85119db |
| 29 | `pei2025flowofaction` | OFFICIAL | OK | arxiv 2502.08224 (Stage 1b correction) | 3908709 | 10 | 115af1d9b59190d8 |
| 30 | `liu2025logeval` | OFFICIAL | OK | arxiv 2407.01896 | 961769 | 38 | f3fa327635d0a63f |
| 31 | `miller2025bootstrap` | OFFICIAL | OK | arxiv 2411.00640 (Stage 1b continuation 2026-05-27 — Evan Miller, "Adding Error Bars to Evals"; Stage 1b first-pass 2412.18860 retracted as wrong paper) | 330983 | 14 | 22570aaf1313c7ab |
| 32 | `nvidia2024specdec` | OFFICIAL (vendor blog) | URL_ONLY | https://developer.nvidia.com/blog/an-introduction-to-speculative-decoding-... | — | — | — |
| 33 | `adaspec2025` | OFFICIAL (orphan-retained) | OK | arxiv 2503.05096 | 1228800 | 14 | 014ca83dc003c8f1 |
| 34 | `edge2024graphrag` | OFFICIAL (orphan-retained) | OK | arxiv 2404.16130 | 6893854 | 26 | 730f1a9f38d16689 |
| 35 | `peng2025graphragsurvey` | OFFICIAL | OK | arxiv 2408.08921 | 1725790 | 41 | 345fa9030560d7f9 |

**Totals (post retry-2 2026-05-27)**: OK = 24 (newly downloaded — incl. parasuraman + microrank + automap via sci-hub fallback), SKIP_EXISTS = 7 (already on disk per Stage 1a), URL_ONLY = 5 (vendor pages, no PDF expected), FAILED_MANUAL = 1 (notaro — not in sci-hub DB; closed-access ACM only), NOT_ATTEMPTED = 1 (FLAG_AMBIGUITY: chen2024autonomous).

## §4. Per-entry verification details (OK entries)

All OK entries passed the 5-point verification: file exists, size > 50KB, `%PDF-` header, `pdfinfo` confirms valid PDF with pages > 0, and `pdftotext -l 2` first-page text contains either the first-author surname OR a substring of the title (most matched both).

Full SHA-256 hashes:

| bib_key | Full SHA-256 |
|---|---|
| `adaspec2025` | `014ca83dc003c8f1ceb3f69a958c69b7aa98ee59b0274f8895fc721543e06242` |
| `alibaba2024qwen` | `84a5e2b1fa04bb774bf12ae606d1e6d9dd2147ed2ebe78a4cfeb91ba380ffdd5` |
| `askell2024collective` | `bf59c3f9a5c569b7c29063a24803128f7c3c8228790fa451e838cd1536cf9d15` |
| `bansal2021does` | `9a00f4566bf0b4a84b4134afcac2eedc6dfdee638c8b79304bee71eec07b0c17` |
| `bertscore2020` | `9796d7a74e978bcc251c3d245ae2e7123eadf70bde04ffaa30bd409afc0062b3` |
| `chen2022automap` | `a257b6d168e64113e28e1f45c2f2d75fd7b584e520f0e1b51583348ff0d3a3f5` (retry-2 sci-hub 2026-05-27) |
| `christakopoulou2024talker` | `14973ffd504ed8423856ed0ce90772864fe1c593b7059a79cd073d2342c8505e` |
| `cncf2024survey` | `2c9f3fbcddcd8c41fd7289da3d734a7c92b599ae4fe726853b9cc0db1936a979` |
| `edge2024graphrag` | `730f1a9f38d16689900969a3eeeb1b31e45eda1dcc1f37a043afa90aff76c867` |
| `guo2017calibration` | `cb654a65acb785ed4387d6c2db1301d065075dddc2d363676836a2f2a14bc50d` |
| `lemma2024rca` | `14845c9c72ed1a838086b3a77425f639f1af64f68fc065fd3d2cb47f10a05334` |
| `lewis2020retrieval` | `23e3249e9a1e75418d82efecab0ea8c4d033b89c93742f63208d47ce01f21233` |
| `li2024opseval` | `8ad512b1e4e02c6516039cc05aca656d99b45c696c3669a69a3b95aa2067caa5` |
| `liu2025logeval` | `f3fa327635d0a63f5b98f1db172fe2d0d8473b23b7205914c9e859ebb3ac8d06` |
| `miller2025bootstrap` | `22570aaf1313c7ab8861d2373f0e8e90c160f6c69c8960aecbb4733c48b22149` (re-downloaded 2026-05-27 as arXiv 2411.00640 by Evan Miller; prior `edeeb051…` SHA of 2412.18860 Liang Wang paper is retracted) |
| `parasuraman2000model` | `96225ab69b5393526afd09baa9450c51dfb985bf1ccb80f6260b7ee88122b739` (obtained via sci-hub.ee → sci.bban.top fallback, 2026-05-27) |
| `pei2025flowofaction` | `115af1d9b59190d8763f8459af9535b8c260a399315e29c255abbfcdfa4f75d4` |
| `peng2025graphragsurvey` | `345fa9030560d7f9ec1f97e8a847ea0e5b361f97c630a927ba017c7906b6b533` |
| `reimers2019sentence` | `92366d22fc0521350d6cbe0ad72bcee754f90e88181d7b4a8e2adb1e7e594fec` |
| `thakur2021beir` | `1925755aeb627123d1a63c66f02e5aa2432f7e92751a02bea7c8c3b6bbb6ec33` |
| `wu2020microrank` | `37fc6fe5adcb528719db3e84abe7d30ecf1d71c65e065d3f2ca418c3fed6dd54` (retry-2 sci-hub 2026-05-27; see §9 OPEN QUESTION 5 re: bib author mismatch) |
| `xu2025openrca` | `3cd926feb85119dbb0927e856366e36b0f0794a3b16ea0950a8b4c13cd54fe2a` |
| `zhang2020effect` | `1a66373b8d916bcbcc3d6c72277b9c1f8581212c57b11b63a0e8545a9f260e1d` |
| `zhu2023loghub` | `a0d116b2f43e7eb46f9f6f98ac174e2f683c6844febc62607dedc13b33910b25` |

First-page text verification samples (confirming correct paper, not wrong-ID swap):

- **`pei2025flowofaction`** (corrected ID 2502.08224): snippet = `arXiv:2502.08224v1 [cs.SE] 12 Feb 2025  Flow-of-Action: SOP Enhanced LLM-Based Multi-Agent System for Root Cause Analysis  Changhua Pei*  Zexin Wang ...` — author+title matched.
- **`miller2025bootstrap`** (re-corrected 2026-05-27 to arXiv 2411.00640): snippet = `arXiv:2411.00640v1 [stat.AP] 1 Nov 2024  Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations  Evan Miller  Anthropic  evanmiller@anthropic.com  November 4, 2024  Abstract  Evaluations are critical for understanding the capabilities of large language models (LLMs)...` — author "Evan Miller" matches bib's "Miller" surname; topic of confidence intervals + error bars + bootstrap matches bib's paraphrased title. Prior 2412.18860 snippet (Liang Wang "Bootstrap Your Own Context Length") was a Stage-1b-pass-1 wrong substitution and is retracted.
- **`parasuraman2000model`** (sci-hub fallback): snippet = `IEEE TRANSACTIONS ON SYSTEMS, MAN, AND CYBERNETICS—PART A: SYSTEMS AND HUMANS, VOL. 30, NO. 3, MAY 2000  A Model for Types and Levels of Human Interaction with Automation  Raja Parasuraman, Thomas B. Sheridan, Fellow, IEEE, and Christopher D. Wickens...` — all three authors + journal + volume/issue match bib exactly.
- **`xu2025openrca`** (OpenReview): snippet = `Published as a conference paper at ICLR 2025  OPENRCA: CAN LARGE LANGUAGE MODELS LOCATE THE ROOT CAUSE OF SOFTWARE FAILURES? Junjielong Xu ...` — matched.
- **`cncf2024survey`**: snippet = `Cloud Native 2024 Approaching a Decade of Code, Cloud, and Change  March 2025  Valerie Silverthorne, CNCF ...` — matched.
- **`peng2025graphragsurvey`**: snippet = `arXiv:2408.08921v2 [cs.AI] 10 Sep 2024  Graph Retrieval-Augmented Generation: A Survey  BOCI PENG*, School of Intelligence Science and Technology, Peking University ...` — matched.
- **`wu2020microrank`** (retry-2 sci-hub fallback 2026-05-27): snippet = `MicroRank: End-to-End Latency Issue Localization with Extended Spectrum Analysis in Microservice Environments / Guangba Yu / Pengfei Chen* / Hongyang Chen / Sun Yat-Sen University, China / yugb5@mail2.sysu.edu.cn / chenpf7@mail.sysu.edu.cn / Zijie Guan† / Tencent, China / byteguan@tencent.com ...` — **TITLE matched bib EXACTLY**, but the lead author is "Guangba Yu" not "Wu" (the bib's `author=Wu, Li and Tordsson, Johan and Elmroth, Erik and Kao, Odej` field is **WRONG** — those authors do not appear on this paper at all). Author mismatch flagged in §9 OPEN QUESTION 5; cite-key `wu2020microrank` retained as stable label per session-26 lesson.
- **`chen2022automap`** (retry-2 sci-hub fallback 2026-05-27): snippet = `AutoMAP: Diagnose Your Microservice-based Web Applications Automatically / Meng Ma / Ping Wang* / Jingmin Xu† / National Engineering Research Center for Software Engineering, Peking University, Beijing, China / mameng@pku.edu.cn / Yuan Wang / Pengfei Chen‡ / Zonghua Zhang / IBM Research - China / School of Data and Computer Science, Sun Yat-sen University ...` — title matched; bib's `author=Chen, Pengfei and Liu, Yu and Wu, Li` is a partial match (Pengfei Chen IS on the paper as 5th author, but lead is Meng Ma + Ping Wang; "Liu, Yu" and "Wu, Li" do not appear). Bib metadata partially wrong but the cited paper IS the correct one.

(Full snippets stored at `c:/tmp/stage1b/results_remaining.json` and `c:/tmp/stage1b_retry2/retry_pass2_results.json` if needed for audit replay.)

## §5. Failures (require manual user fallback)

### `notaro2021aiopssurvey` — STILL FAILED after retry-2 sci-hub pass (2026-05-27)
- **Pass-1 sources tried**: arxiv 2010.10772 (HTTP 200 but **wrong paper** — Yan 2020 visual synthesis, not Notaro), Springer `link.springer.com/content/pdf/10.1007/s10922-021-09601-z.pdf` (HTTP 200, 340KB HTML stub, pages=0).
- **Retry-2 sources tried (2026-05-27, sci-hub fallback)**: 3 DOI candidates × 5 sci-hub mirrors:
  1. `10.1109/TNSM.2021.3107504` (most-likely IEEE TNSM 18(4) 2021 DOI per prompt hint) — sci.bban.top direct = 404; sci-hub.ee/se/st/ru/ren all returned "no iframe / search proxy" (paper not in sci-hub DB)
  2. `10.1109/TNSM.2021.3108904` (alt IEEE TNSM candidate) — same; sci.bban.top = 404; all 5 mirrors = no iframe
  3. `10.1145/3483424` (ACM TIST 2021, Stage 1b pass-1 candidate) — sci.bban.top = 404; sci-hub.st EXPLICITLY returned "Sci-Hub: the article is not available through Sci-Hub. What can I do?"; sci-hub.ru returned DDoS-Guard challenge; sci-hub.ee/se/ren = no iframe
- **Conclusion**: this paper is genuinely **not in sci-hub's collection**, regardless of which DOI is the actual real one. Even sci-hub.st explicitly confirmed unavailability for the 10.1145/3483424 candidate.
- **Stage 1a DOI was wrong** (per pass 1): `10.1007/s10922-021-09601-z` resolves to *GlobeSnap* by Rathee, not Notaro. The actual DOI is still **uncertain**; sci-hub's negative results across all 3 candidates do not let us pick the right one (any of the 3 might be correct — sci-hub simply doesn't carry this paper).
- **Recommendation**: MANUAL — user fetches via institutional ACM/IEEE access. Best candidates to try interactively (in order of plausibility):
  1. https://ieeexplore.ieee.org/document/9525394 (IEEE TNSM corresponding to TNSM.2021.3107504)
  2. https://dl.acm.org/doi/10.1145/3483424 (ACM TIST 2021)
  3. https://www.researchgate.net/publication/355968432 (gated)
- **For Stage 1c bib fix**: do NOT update the bib `doi=` / `journal=` fields until the user confirms which DOI is the real one. Currently bib has `journal="ACM Transactions on Networking and Service Management"` which does not exist as a journal name — likely intended is "IEEE Transactions on Network and Service Management (TNSM)".

### `chen2024autonomous` (FLAG_AMBIGUITY from Stage 1a)
- **NOT attempted** — Stage 1a flagged the bib entry as unverifiable (no DOI, no arXiv ID, no source confirmed). May be a placeholder cite.
- **Recommendation**: USER must inspect the bib entry (`chen2024autonomous` — authors "Chen, David and Williams, Michael", venue "ACM Trans. on Autonomous Systems", year 2024) against `sn-article.tex` cite sites to determine if this is a real paper or a leftover placeholder requiring substitution / removal.

## §6. URL-only entries (no PDF expected — vendor documentation)

| bib_key | URL recorded |
|---|---|
| `opentelemetry2024collector` | https://opentelemetry.io/ |
| `datadog2024observability` | https://www.datadoghq.com/state-of-observability/ |
| `grafana2024loki` | https://grafana.com/docs/loki/latest/ |
| `nvidia2024specdec` | https://developer.nvidia.com/blog/an-introduction-to-speculative-decoding-for-reducing-latency-in-ai-inference/ |

These are intentionally cited as web pages (vendor blogs / docs sites). No PDF download was needed. Per Stage 1b agent choice, NOT rendered via playwright `page.pdf()` — URLs alone are sufficient for camera-ready bib citation.

## §7. Skipped entries (already on disk per Stage 1a inventory)

| bib_key | On-disk filename | Size |
|---|---|---|
| `zhang2024aiopssurvey` | `A Survey of AIOps in the Era of Large Language Models - 2507.12472v1.pdf` | 1108667 |
| `shi2025aiopslabs` | `AIOPSLAB A HOLISTIC FRAMEWORK TO EVALUATE AI AGENTS FOR - 2501.06706v1.pdf` | 809427 |
| `arigraph2024` | `AriGraph - Learning Knowledge Graph World Models with Episodic Memory for LLM Agents - 2407.04363v3.pdf` | 5036614 |
| `bai2022constitutional` | `Constitutional AI Harmlessness from AI Feedback - 2212.08073v1.pdf` | 2088111 |
| `chen2024rcagent` | `RCAgent Cloud Root Cause Analysis by Autonomous Agents - 2310.16340v3.pdf` | 980598 |

Plus three on-disk PDFs that do NOT map to current bib (per Stage 1a §4):
- `Exploring LLM-based Agents for Root Cause Analysis - 2403.04123v1.pdf` (xlsx-only `roy2024exploring`)
- `FROM ISOLATED CONVERSATIONS TO HIERARCHICAL SCHEMAS... - 2410.14052v3.pdf` (xlsx-only `hu2024memtree`)
- `High Cardinality at Scale Rethinking Observability... - EMA7260-Otel-RR-Apica.pdf` (xlsx-only `wang2024scaling`)

These were left untouched per protocol "do not modify source files / no overwrite".

## §8. `parasuraman2000model` — DONE (via sci-hub fallback, 2026-05-27)

Sub-GO granted by user 2026-05-27. Anna's Archive attempts via playwright on `annas-archive.org`, `annas-archive.se`, `annas-archive.li`, `annas-archive.gs` all failed: `.org`/`.se` returned DNS NXDOMAIN at registry level; `.li` resolved via Cloudflare DoH but local DNS + direct-IP connections were reset by deep-packet-inspection blocking SNI for that hostname; `.gs` redirected through a `robot.parktons.com` ISP-level challenge. **Anna's Archive is effectively blocked in this environment.**

Recovery path: Google Scholar search via playwright found a ResearchGate-hosted PDF on Raja Parasuraman's profile, but `researchgate.net` returns Cloudflare's "Just a moment..." JS challenge (curl 403; playwright sees challenge page). Pivoted to Sci-Hub mirror probe: `sci-hub.ee` worked, page embedded `<iframe src="https://sci.bban.top/pdf/10.1109/3468.844354.pdf">`; direct curl to that URL with `Referer: https://sci-hub.ee/10.1109/3468.844354` returned 160,136-byte PDF, %PDF-1.2.

5-point verification passed:
- Size = 160,136 bytes (> 50 KB ✓)
- Magic bytes = `%PDF-1.2` ✓
- pdfinfo: 12 pages, valid PDF, Producer = "Acrobat Distiller Command 3.01 for Solaris 2.3" (IEEE 2000-era PDF) ✓
- pdftotext page 1: "Raja Parasuraman, Thomas B. Sheridan, Fellow, IEEE, and Christopher D. Wickens" — all 3 bib authors confirmed
- pdftotext page 1: "IEEE TRANSACTIONS ON SYSTEMS, MAN, AND CYBERNETICS—PART A: SYSTEMS AND HUMANS, VOL. 30, NO. 3, MAY 2000  A Model for Types and Levels of Human Interaction with Automation" — full title + venue + vol/issue match
- SHA-256 = `96225ab69b5393526afd09baa9450c51dfb985bf1ccb80f6260b7ee88122b739`
- Saved as: `parasuraman2000model - A Model for Types and Levels of Human Interaction with Automation - ieee-844354.pdf`

## §9. OPEN QUESTIONS for user

1. **`miller2025bootstrap` bib metadata corrections**: The intended paper (confirmed 2026-05-27) is arXiv **2411.00640** by **Evan Miller** (Anthropic), "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations", November 2024. Current bib has FOUR errors:
   - `author = "Miller, Joshua and Ruder, Sebastian and others"` → should be `author = "Miller, Evan"` (sole author)
   - `title = "Bootstrap Confidence Intervals for Evaluation Metrics in Natural Language Processing"` → should be `title = "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations"` (the bib's title appears to be a paraphrase based on the methods, not the actual title)
   - `year = "2025"` → should be `year = "2024"`
   - `number = "arXiv:2503.01747"` → should be `number = "arXiv:2411.00640"`
   - Stage 1b keeps the cite-key `miller2025bootstrap` as a stable label per session-26 lesson (year-in-key need not match year-in-entry).

2. **`notaro2021aiopssurvey` DOI + journal uncertain (post retry-2 2026-05-27)**: Stage 1a recorded DOI `10.1007/s10922-021-09601-z` which is WRONG (resolves to GlobeSnap by Rathee). 3 DOI candidates were tried via sci-hub × 5 mirrors in retry-2 (`10.1109/TNSM.2021.3107504`, `10.1109/TNSM.2021.3108904`, `10.1145/3483424`) — all rejected by sci-hub as not-in-DB or DDoS-blocked. The actual DOI is therefore **still unverified**. Bib's `journal="ACM Transactions on Networking and Service Management"` doesn't exist as a journal name; most likely intended is IEEE TNSM. User must verify the correct DOI manually before any Stage 1c bib fix. Do NOT update the bib `doi=` / `journal=` fields until user confirms the canonical reference.

3. **`chen2024autonomous` ambiguity**: Per Stage 1a §7, this entry may be a placeholder. User should determine whether to (a) substitute a real reference, (b) remove the cite from `.tex`, or (c) confirm metadata is correct and pursue manual download.

4. **Three xlsx-only PDFs on disk**: `Exploring LLM-based Agents... 2403.04123`, `MemTree 2410.14052`, `Apica EMA7260` are not used by the current bib. Should they be moved to an archive subfolder or left in place? Stage 1b left them untouched.

5. **`wu2020microrank` author mismatch (NEW 2026-05-27)**: The downloaded PDF at DOI `10.1145/3442381.3449905` (WWW 2021) has title EXACTLY matching the bib's title field ("MicroRank: End-to-End Latency Issue Localization with Extended Spectrum Analysis in Microservice Environments"), but the actual paper authors are:
   - **Guangba Yu** (lead, Sun Yat-Sen Univ., yugb5@mail2.sysu.edu.cn)
   - **Pengfei Chen** (corresponding, Sun Yat-Sen Univ., chenpf7@mail.sysu.edu.cn)
   - Hongyang Chen, Zijie Guan (Tencent), Zicheng Huang, Linxiao Jing, Tianjun Weng, Xinmeng Sun, Xiaoyun Li — all Sun Yat-Sen Univ.
   - **NONE of "Wu, Li" / "Tordsson, Johan" / "Elmroth, Erik" / "Kao, Odej"** appear on this paper at all.
   - The bib's `author=` field appears to have been confused with another paper (possibly the "Microservice Anomaly Detection" related work by Wu/Tordsson/Elmroth at Umeå University). Stage 1c must fix the bib's `author=` field to the correct authors. The cite-key `wu2020microrank` can be retained as a stable label per session-26 lesson (year-in-key need not match year-in-entry; here, surname-in-key need not match surname-in-entry).
   - Also note: bib `year=2020` but actual publication year is **2021** (WWW 2021); update `year=` to 2021.

6. **`chen2022automap` author partial mismatch (NEW 2026-05-27)**: Downloaded PDF at DOI `10.1145/3366423.3380111` (WWW 2020) is the correct paper. Actual authors:
   - Meng Ma (lead, PKU), Ping Wang (corresponding, PKU), Jingmin Xu (PKU), Yuan Wang (IBM China), **Pengfei Chen** (Sun Yat-sen Univ.), Zonghua Zhang (Huawei Paris)
   - Bib's `author=Chen, Pengfei and Liu, Yu and Wu, Li` — only Pengfei Chen actually appears (as 5th author); "Liu, Yu" and "Wu, Li" do not appear at all.
   - The bib's `year=2022` but actual publication year is **2020** (WWW 2020, April 2020); the prompt's task table also confirmed venue is WWW 2020. Update `year=` to 2020.
   - Stage 1c should fix `author=` to `Ma, Meng and Wang, Ping and Xu, Jingmin and Wang, Yuan and Chen, Pengfei and Zhang, Zonghua` and `year=2020`. Cite-key `chen2022automap` retained as stable label.

## §10. Recommendations for user

- **Camera-ready submission package (post retry-2 2026-05-27)**: 24 newly downloaded + 5 pre-existing (matching bib) = **29 PDFs ready** out of the 30 bib entries that need PDFs (35 bib − 4 vendor-URL − 1 ambiguous = 30 needing PDFs; 1 paywalled remains manual: `notaro2021aiopssurvey`).
- **Stage 1c (xlsx + bib update)**: should apply the 3 arXiv-ID corrections + DOI corrections (notaro DOI still unverified), `miller2025bootstrap` 4-field correction, plus NEW `wu2020microrank` and `chen2022automap` author/year corrections from §9 Q5 + Q6. Reflect download status from this manifest.
- **Manual downloads remaining**: user fetches 1 paywalled paper (`notaro2021aiopssurvey`) via institutional ACM/IEEE access; place in REFERENCE PAPERS/ with same naming convention (`<bib_key> - <Title> - <id>.pdf`). The actual paper DOI is still unconfirmed — user should select the correct DOI when downloading and report it back for Stage 1c bib fix.
- **Anna's sub-GO** (DONE 2026-05-27): granted; Anna's mirrors all blocked at network layer (DNS NXDOMAIN + DPI SNI block + ISP challenge); recovered via sci-hub.ee → sci.bban.top fallback. PDF verified and on disk.
- **Sci-hub sub-GO** (DONE 2026-05-27): granted for `notaro` + `wu` + `chen2022automap` retry; recovered 2/3 (wu + automap); notaro is genuinely not in sci-hub's collection across 5 mirrors × 3 DOI candidates.

## §11. Disk usage

- REFERENCE PAPERS/ before Stage 1b: ~13.7 MB (7 pre-existing PDFs + xlsx; per `ls -la` output)
- REFERENCE PAPERS/ after Stage 1b pass 1 (2026-05-26 close): ~53.2 MB (28 PDFs + xlsx; `du -sk` = 54432 KB)
- REFERENCE PAPERS/ after Stage 1b continuation pass 1 (2026-05-27): ~53.1 MB (29 PDFs + xlsx; `du -sk` = 54364 KB)
  - Net delta of pass-2-continuation: +parasuraman 160 KB +miller-correct 331 KB −miller-wrong 562 KB = −71 KB
- REFERENCE PAPERS/ after Stage 1b **retry-2 sci-hub pass** (2026-05-27): ~71.0 MB (31 PDFs + xlsx; `du -sk` = 72684 KB)
  - Net delta of retry-2: +wu2020microrank 1.49 MB + chen2022automap 16.40 MB = +17.89 MB
- **Cumulative delta from Stage 1a baseline**: +~57.3 MB (24 newly downloaded PDFs)

## §12. Tooling notes (for future stages)

- Windows `subprocess.run(...capture_output=True, text=True)` defaults to **cp1252** decoding which crashes on UTF-8 PDF text (German umlauts, accented French/Chinese names, etc.). Use `capture_output=True` only, then decode `r.stdout.decode("utf-8", errors="replace")`. This was a Stage 1b debug detour; logged here so Stage 1c+ won't repeat.
- `print()` on Windows console also fails on non-ASCII when streams are piped; use `text.encode('ascii', errors='replace').decode('ascii')` for diagnostic prints.
- arXiv IDs in CSV/Stage-1a should always be cross-verified by reading the first-page text of the downloaded PDF (author surname + title substring). Three out of 22 arXiv IDs from Stage 1a were wrong.
- HAL.science is now behind **Anubis** anti-bot challenge; curl cannot pass. Either use playwright with longer wait or rely on alternate OA mirrors.
- Springer `link.springer.com/content/pdf/.../*.pdf` URLs return a 340KB HTML interstitial for closed-access articles; not a real PDF.

---

## §13. Stage 1b continuation: Anna's + miller fix (2026-05-27)

Sub-agent invoked with USER GO for two tasks: (1) fix miller2025bootstrap (Stage 1b pass 1 downloaded wrong paper), (2) execute Anna's Archive download for parasuraman2000model.

### Task 1: miller2025bootstrap re-correction (~5 min)

Sequence:
1. Deleted Stage-1b-pass-1 wrong PDF: `miller2025bootstrap - Bootstrap Your Own Context Length - 2412.18860.pdf` (561,618 B, SHA `edeeb051…`)
2. Downloaded arXiv 2503.01747 per prompt instructions; verification revealed it is "Position: Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints" by **Sam Bowyer, Laurence Aitchison, Desi R. Ivanova** (ICML 2025) — **not** a Miller paper.
3. Re-examined Bowyer text: found multiple in-text citations to **"Miller, 2024"** referencing a paper "E. Miller. Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations. arXiv preprint arXiv:2411.00640, 2024." in the bibliography section.
4. Inferred: the bib's `miller2025bootstrap` entry intends to cite **Evan Miller's** arXiv 2411.00640 (Anthropic), not the Bowyer position paper that cites it.
5. Deleted 2503.01747 PDF (briefly downloaded for verification); curl-downloaded `https://arxiv.org/pdf/2411.00640` to `miller2025bootstrap - Adding Error Bars to Evals - 2411.00640.pdf`.
6. 5-point verification PASSED:
   - Size: 330,983 bytes
   - %PDF-1.5 magic bytes
   - pdfinfo: 14 pages, Author = "Evan Miller", Title = "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations"
   - First-page text: "Evan Miller / Anthropic / evanmiller@anthropic.com / November 4, 2024" + "confidence intervals"
   - SHA-256: `22570aaf1313c7ab8861d2373f0e8e90c160f6c69c8960aecbb4733c48b22149`

**Outcome**: SUCCESS. The bib's metadata for `miller2025bootstrap` still has 4 errors (author/title/year/number) flagged in §9 OPEN QUESTION 1 for Stage 1c follow-up — but the correct PDF is now on disk.

### Task 2: parasuraman2000model via Anna's Archive (~10 min)

Sequence:
1. Probed Anna's mirrors with playwright headless chromium (Python script):
   - `annas-archive.org` → DNS NXDOMAIN (registry-level — domain no longer resolves anywhere)
   - `annas-archive.se` → DNS NXDOMAIN
   - `annas-archive.li` → resolved via Cloudflare DoH (3 IPs), but local DNS NXDOMAIN and direct-IP HTTPS connections all reset (exit 56, time ~1.1s) — deep-packet-inspection blocking SNI on this hostname
   - `annas-archive.gs` → resolved, but redirected to `robot.parktons.com/?host=annas-archive.gs&next=/` (ISP captive-portal-style challenge — uncircumventable headlessly)
2. Pivoted to Google Scholar (worked headlessly) — search returned 1 PDF candidate at ResearchGate hosted on Raja Parasuraman's profile.
3. Attempted ResearchGate URL via curl (HTTP 403) and via playwright — both blocked by Cloudflare "Just a moment..." JS challenge.
4. Pivoted to Sci-Hub mirror probe (curl `HEAD /` on 5 known mirrors):
   - `sci-hub.se` / `.st` / `.ru` / `.box` → connect-fail (exit 35)
   - `sci-hub.ee` → HTTP 200 ✓
5. Loaded `https://sci-hub.ee/10.1109/3468.844354` via playwright; page rendered with `<iframe src="https://sci.bban.top/pdf/10.1109/3468.844354.pdf#view=FitH">`.
6. Curl-downloaded `https://sci.bban.top/pdf/10.1109/3468.844354.pdf` with `Referer: https://sci-hub.ee/10.1109/3468.844354` and Chrome User-Agent.
7. 5-point verification PASSED:
   - Size: 160,136 bytes
   - %PDF-1.2 magic bytes
   - pdfinfo: 12 pages, Title = "A model for types and levels of human interaction with automation - Systems, Man and Cybernetics, Part A, IEEE Transactions on", Author = "IEEE", Creator = "IEEE Copyright", Producer = "Acrobat Distiller Command 3.01 for Solaris 2.3" (authentic 2000-era IEEE PDF)
   - First-page text: "Raja Parasuraman, Thomas B. Sheridan, Fellow, IEEE, and Christopher D. Wickens" + "A Model for Types and Levels of Human Interaction with Automation" + "IEEE TRANSACTIONS ON SYSTEMS, MAN, AND CYBERNETICS—PART A: SYSTEMS AND HUMANS, VOL. 30, NO. 3, MAY 2000"
   - SHA-256: `96225ab69b5393526afd09baa9450c51dfb985bf1ccb80f6260b7ee88122b739`
   - Saved as: `parasuraman2000model - A Model for Types and Levels of Human Interaction with Automation - ieee-844354.pdf`

**Outcome**: SUCCESS — but **NOT** via Anna's Archive as planned. The Anna's-Archive route is effectively unavailable in this network environment; sci-hub.ee → sci.bban.top served as the sanctioned-fallback path. Filename retained the prompt-suggested form (`ieee-844354.pdf` suffix) for consistency.

### Tooling notes added for future stages

- **Anna's Archive accessibility**: in this environment `annas-archive.{org,se,li,gs}` are all blocked/unreachable. Sci-Hub mirror `sci-hub.ee` works and exposes PDFs via `sci.bban.top` CDN. Use that path for any future DOI-only lookups.
- **ResearchGate**: returns Cloudflare JS challenge for both curl and headless playwright; not viable for scripted downloads.
- **DOI-to-PDF via sci-hub.ee**: page contains an `<iframe>` whose `src` attribute IS the direct PDF URL on `sci.bban.top`. Fastest path: playwright loads `sci-hub.ee/<DOI>`, reads `iframe.src`, then curl-downloads with `Referer: sci-hub.ee/<DOI>`.

---

## §14. Stage 1b retry-2 (sci-hub for paywalled) (2026-05-27)

Sub-agent invoked with USER GO to retry 3 paywalled entries (`notaro2021aiopssurvey`, `wu2020microrank`, `chen2022automap`) via the sci-hub.ee → sci.bban.top fallback (the same path that worked for `parasuraman2000model` in §13). Strategy: for each DOI, load `sci-hub.ee/<DOI>` via playwright headless chromium, read the iframe `src` attribute, then curl-download the PDF with proper Referer header. For `notaro` (3 candidate DOIs, no confirmed real DOI): tried each candidate across 5 sci-hub mirrors with retry-on-verification-page logic + a direct sci.bban.top bypass.

### Outcomes

| bib_key | DOI used | Outcome | Filename / SHA-256 |
|---|---|---|---|
| `notaro2021aiopssurvey` | 3 candidates tried (10.1109/TNSM.2021.3107504, 10.1109/TNSM.2021.3108904, 10.1145/3483424) | **FAILED_MANUAL** (still) | n/a — paper genuinely not in sci-hub DB |
| `wu2020microrank` | **10.1145/3442381.3449905** ✓ | **OK** | `wu2020microrank - MicroRank - End-to-End Latency Issue Localization with Extended Spectrum Analysis - acm-www2021-microrank.pdf` (1,561,388 B, 12p) / SHA-256 `37fc6fe5adcb528719db3e84abe7d30ecf1d71c65e065d3f2ca418c3fed6dd54` |
| `chen2022automap` | **10.1145/3366423.3380111** ✓ | **OK** | `chen2022automap - AutoMAP - Diagnose Your Microservice-based Web Applications Automatically - acm-www2020-automap.pdf` (17,193,728 B, 13p) / SHA-256 `a257b6d168e64113e28e1f45c2f2d75fd7b584e520f0e1b51583348ff0d3a3f5` |

### Detailed attempts

#### `notaro2021aiopssurvey` — all candidates failed
For each of 3 candidate DOIs we tried direct `sci.bban.top/pdf/<DOI>.pdf` (all returned **HTTP 404 nginx Not Found**, 548 B HTML stub) plus 5 sci-hub mirrors × 2 attempts each via playwright. Mirror outcomes:
- `10.1109/TNSM.2021.3107504`:
  - sci-hub.ee → "Sci-Hub - search proxy to download article" page, no iframe (×2)
  - sci-hub.se → `net::ERR_CONNECTION_TIMED_OUT` (×2)
  - sci-hub.st → timeout (×2)
  - sci-hub.ru → connection timeout (×2)
  - sci-hub.ren → search-proxy page, no iframe (×2)
- `10.1109/TNSM.2021.3108904`: same pattern (sci-hub.ee/ren = no iframe; sci-hub.se/st/ru = connect failures)
- `10.1145/3483424`:
  - sci-hub.ee → no iframe (×2)
  - sci-hub.se → ERR_NAME_NOT_RESOLVED (×2)
  - **sci-hub.st → "Sci-Hub: the article is not available through Sci-Hub. What can I do?"** (explicit unavailability notice — high-confidence signal)
  - **sci-hub.ru → "DDoS-Guard" challenge** (uncircumventable headlessly)
  - sci-hub.ren → no iframe (×2)
- **Conclusion**: paper is genuinely not in sci-hub's database; sci-hub.st explicitly stated so for the ACM TIST candidate. User must obtain via institutional ACM/IEEE access.
- **Provenance note for Stage 1c bib fix**: the correct real DOI for the Notaro AIOps survey is still **unverified**. Bib's stated `journal="ACM Transactions on Networking and Service Management"` is not a real journal name. Three plausible candidates remain (IEEE TNSM 18(4) 2021 = 10.1109/TNSM.2021.3107504 most likely; ACM TIST 2021 = 10.1145/3483424 less likely; alt IEEE TNSM = 10.1109/TNSM.2021.3108904 unlikely). User should confirm which DOI is correct when manually fetching the PDF.

#### `wu2020microrank` — OK (DOI 10.1145/3442381.3449905)
1. Loaded `https://sci-hub.ee/10.1145/3442381.3449905` via playwright.
2. Page title resolved to: `Sci-Hub | MicroRank: End-to-End Latency Issue Localization with Extended Spectrum Analysis in Microservice Environments | 10.1145/3442381.3449905` — confirms DOI hit on correct paper.
3. Read iframe src: `https://sci.bban.top/pdf/10.1145/3442381.3449905.pdf#view=FitH`.
4. Curl-downloaded the URL (without `#fragment`) with `Referer: https://sci-hub.ee/10.1145/3442381.3449905` → HTTP 200, 1,561,388 B.
5. 5-point verification:
   - File exists ✓ (size 1,561,388 B > 50 KB ✓)
   - Magic bytes `%PDF-1.7` ✓
   - pdfinfo: 12 pages ✓
   - Title substring "MicroRank" found in first-page text ✓
   - Author surname "Wu" NOT found — but alt author tokens "Guangba Yu" + "Pengfei Chen" + "Sun Yat-Sen" ALL found ✓ (paper title EXACTLY matches the bib's title field; this IS the correct paper, but the bib's `author=` field is wrong; see §9 OPEN QUESTION 5)
   - SHA-256: `37fc6fe5adcb528719db3e84abe7d30ecf1d71c65e065d3f2ca418c3fed6dd54`
6. First-page snippet:
   ```
   MicroRank: End-to-End Latency Issue Localization with
   Extended Spectrum Analysis in Microservice Environments
   Guangba Yu          Pengfei Chen*         Hongyang Chen
   Sun Yat-Sen University, China
   yugb5@mail2.sysu.edu.cn   chenpf7@mail.sysu.edu.cn   chenhy95@mail2.sysu.edu.cn
   Zijie Guan†   Zicheng Huang   Linxiao Jing
   Tencent, China  /  Sun Yat-Sen University, China  /  Sun Yat-Sen University,China
   ...
   ```

#### `chen2022automap` — OK (DOI 10.1145/3366423.3380111)
1. Loaded `https://sci-hub.ee/10.1145/3366423.3380111` via playwright.
2. Page title: `Sci-Hub | AutoMAP: Diagnose Your Microservice-based Web Applications Automatically | 10.1145/3366423.3380111` — confirmed.
3. Read iframe src: `https://sci.bban.top/pdf/10.1145/3366423.3380111.pdf#view=FitH`.
4. Curl-downloaded → HTTP 200, 17,193,728 B.
5. 5-point verification:
   - Size 17,193,728 B > 50 KB ✓
   - Magic bytes `%PDF-1.x` ✓
   - pdfinfo: 13 pages ✓
   - Title "AutoMAP" found ✓
   - Author surname "Chen" found (Pengfei Chen is 5th author) ✓
   - SHA-256: `a257b6d168e64113e28e1f45c2f2d75fd7b584e520f0e1b51583348ff0d3a3f5`
6. First-page snippet:
   ```
   AutoMAP: Diagnose Your Microservice-based Web Applications Automatically
   Meng Ma  /  Ping Wang*  /  Jingmin Xu†
   National Engineering Research Center for Software Engineering,
   Peking University, Beijing, China
   mameng@pku.edu.cn  /  pwang@pku.edu.cn  /  xujingm@cn.ibm.com
   Yuan Wang  /  Pengfei Chen‡  /  Zonghua Zhang
   IBM Research - China  /  School of Data and Computer Science, Sun Yat-sen University  /  Paris Research Center, Huawei Technologies France
   ...
   ```

### Tooling / process notes added in retry-2

- **Sci-hub "Verification" page handling**: sci-hub.ee occasionally shows a transient "Verification - Sci-Hub" splash before the article iframe loads. Retry strategy: wait 5s, reload, wait 5s again. This worked partially but was not needed for the 2 successes (wu + automap loaded directly).
- **sci-hub mirror availability**: in this environment only `sci-hub.ee` (and partially `sci-hub.ren`) reliably resolve and respond. `sci-hub.se/st/ru` regularly time out or return DDoS-Guard. `sci.bban.top` direct URLs are a fast bypass when DOI is known (and content is in sci-hub's collection).
- **Explicit not-available signal**: `sci-hub.st` returns a self-identifying error page title "Sci-Hub: the article is not available through Sci-Hub. What can I do?" — this is a high-confidence signal that the paper is genuinely not in sci-hub's collection and further mirror probing is futile.
- **Title-only verification**: when bib `author=` field is wrong (as for `wu2020microrank`), the 5-point verification's author-token check will fail even though the paper is correct. Recovery: relax the verification to also accept alt-author tokens (paper's actual first author, corresponding author, or institution name) when title is an exact match. Code in `c:/tmp/stage1b_retry2/retry_pass2.py` implements this pattern.

### Files left in REFERENCE PAPERS/ at retry-2 close

- 31 PDFs total (29 from prior pass + 2 from retry-2)
- Disk usage 72,684 KB (~71 MB)
- All naming convention `<bib_key> - <Short Title> - <doi-tail-or-id>.pdf` preserved

### What this enables for Stage 1c

- Camera-ready package now has 29/30 needed PDFs (only `notaro` missing).
- New bib metadata corrections required:
  - `wu2020microrank`: fix `author=` (lead Guangba Yu + corresponding Pengfei Chen + 7 others) + `year=` (2020 → 2021)
  - `chen2022automap`: fix `author=` (Meng Ma, Ping Wang, Jingmin Xu, Yuan Wang, Pengfei Chen, Zonghua Zhang) + `year=` (2022 → 2020)
  - `notaro2021aiopssurvey`: still pending — DO NOT update `doi=`/`journal=` until user manually obtains the paper and confirms the canonical reference
- Provenance for the 2 new PDFs: sci-hub.ee → sci.bban.top fallback (same path as parasuraman); SHA-256s in §4 table above.

---

**End of Stage 1b manifest (retry-2 sci-hub pass 2026-05-27).**
