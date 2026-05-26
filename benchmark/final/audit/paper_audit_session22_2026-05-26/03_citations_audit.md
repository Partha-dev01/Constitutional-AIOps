# 03 — Citations + Bibliography Audit

## Scope

Verify citation-to-bibliography coverage in the v2 sandbox paper:
- `\cite{}` keys vs `@type{key,...}` entries in v2 .bib (broken refs would render as `[?]`)
- Orphan bib entries (declared but not cited)
- v1 vs v2 bib diff (added / removed / modified)
- Contextual correctness on a ~10-cite sample
- Bibliographic completeness for key new references
- Self-citation and citation-style consistency

Sources (READ-ONLY):
- v2 tex: `c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\main\sn-article.tex`
- v2 bib: `c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\main\sn-bibliography.bib`
- v1 tex: `c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\Final Submission Paper (Accepted v.1)\1ST SUBMISSION\sn-article-template\sn-article.tex`
- v1 bib: `c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\Final Submission Paper (Accepted v.1)\1ST SUBMISSION\sn-article-template\sn-bibliography.bib`

## Method

1. Extract all `\cite[a-z]*{...}` matches from v2 tex; split comma-separated keys; sort/unique.
   - regex: `\\cite[a-z]*\{[^}]+\}` then strip braces and tokenize on `,`
2. Extract all `^@type{key,` openers from v2 bib; sort/unique.
   - regex: `^@[a-zA-Z]+\{[^,]+,`
3. `comm` against the two sets: orphans (in bib only) vs missing (cited but not in bib).
4. Same extraction on v1 tex + v1 bib; `comm` v1 vs v2 for added/removed/modified.
5. Read each new entry to verify required BibTeX fields (author/title/venue/year).
6. Spot-check ~13 cite sites: read surrounding sentence, compare to bib title/year/venue.
7. Count cite-style variants (`\cite` vs `\citep` vs `\citet` vs `\citeauthor`).
8. Grep bib for author names matching the paper's author list (self-citation check).

---

## Findings

### CRITICAL (missing cite-to-bib, broken refs)

**NONE.** Every one of the 31 unique cite keys in v2 tex has a matching `@type{key,...}` entry in v2 bib. BibTeX will resolve all references; zero `[?]` placeholders will render in the PDF.

Verified by:
```
comm -13 <(bib-keys sorted) <(cite-keys sorted)   →   empty output
```

---

### IMPORTANT (contextual mismatch, missing bib fields)

**I-1. `peng2025graphragsurvey` missing volume / issue / pages / DOI.**
- Bib v2 `sn-bibliography.bib:273-278` — only `author`, `title`, `journal = "ACM Trans. Inf. Syst."`, `year = "2025"`.
- ACM TOIS articles require volume/issue/article-number for full citation. Reviewers may flag.
- Used at tex `sn-article.tex:739` (Limitations).
- **Fix**: add volume / issue / article-no / DOI when finalized.

**I-2. `zhang2024aiopssurvey` year mismatch with planned label.**
- Bib v2 `sn-bibliography.bib:18-23` says `year = "2024"`, journal = "ACM Computing Surveys".
- MEMORY.md and the "12 new entries expected" plan label it as "AIOps Survey 2025 (ACM CS)" — i.e. expected year 2025.
- This is the SAME entry that was in v1 (already 2024); not a new v2 entry. Either the bib year needs updating to match the published 2025 issue, or the "expected" label in the plan was off-by-one.
- Used at tex `sn-article.tex:135, 141, 160` (Intro + Related Work surveys).
- **Action**: verify the actual publication date on ACM Computing Surveys. If 2025, update bib `year`.

**I-3. `nvidia2024specdec` lacks URL/identifier.**
- Bib v2 `sn-bibliography.bib:250-255` — has `howpublished = "NVIDIA Developer Blog"` but no URL or post-date.
- A reviewer following the blog reference cannot locate it without a URL.
- Used at tex `sn-article.tex:514, 744`.
- **Fix**: add `\url{...}` to the actual blog post.

**I-4. Stale bib header comment.**
- Bib v2 `sn-bibliography.bib:2` says `%% 26 references matching citation keys in sn-article.tex`.
- Actual: 36 entries total, 31 cited. Misleading to reader.
- **Fix**: update to `%% 36 entries (31 cited; 5 retained-orphan)`.

**Contextual sample — all 13 spot-checked cites are correct in context:**

| Tex line | Cite | Surrounding context | Bib title (match?) |
|---|---|---|---|
| 135 | opentelemetry2024collector, datadog2024observability | "~1.7M tokens per hour of combined telemetry" | OpenTelemetry Collector + Datadog State of Observability ✓ |
| 135 | notaro2021aiopssurvey | "53% implementation failure rate" | Survey of AIOps Methods for Failure Management ✓ |
| 160 | chen2024rcagent | "RCAgent demonstrates LLM-based RCA" | RCAgent: Cloud RCA by Autonomous Agents ✓ |
| 164 | arigraph2024 | "AriGraph...dual-memory architecture" | AriGraph: Knowledge Graph World Models w/ Episodic Memory ✓ |
| 168, 383 | bai2022constitutional, askell2024collective | "Constitutional AI frameworks", "Following Bai et al." | Constitutional AI + Collective Constitutional AI ✓ |
| 285 | reimers2019sentence | "384-dim embeddings via all-MiniLM-L6-v2" | Sentence-BERT (Reimers & Gurevych EMNLP-IJCNLP) ✓ |
| 293 | lewis2020retrieval | "RAG literature favoring dense retrieval" | RAG for Knowledge-Intensive NLP Tasks (NeurIPS) ✓ |
| 293 | thakur2021beir | "semantic search benchmarks" | BEIR: Zero-shot IR benchmark ✓ |
| 406 | liu2025logeval, shi2025aiopslabs | "expanded from v1...sample size and source diversity" | LogEval + AIOpsLab (both motivate larger curated benchmarks) ✓ |
| 451 | miller2025bootstrap | "BCa bootstrap intervals from 10,000 resamples...recent NLP-evaluation guidance on bootstrap usage" | Bootstrap CIs for Eval Metrics in NLP (arXiv:2503.01747) ✓ |
| 514, 744 | nvidia2024specdec | "speculative decoding" | Accelerating LLM Inference with Speculative Decoding ✓ |
| 704 | shi2025aiopslabs, xu2025openrca | "matched-substring evaluator" | AIOpsLab + OpenRCA (both established this eval style) ✓ |
| 734 | shi2025aiopslabs, xu2025openrca, pei2025flowofaction | "single-agent LLM systems on AIOps...distinct hybrid niche" | AIOpsLab + OpenRCA + Flow-of-Action ✓ |
| 739 | peng2025graphragsurvey | "Graph-RAG...retrieval-space sparsity...memory-architecture work" | Graph RAG: A Survey (ACM TOIS) ✓ |

All contextual placements verified appropriate. No factual mis-citations detected.

---

### MINOR (orphan bib entries, style inconsistencies)

**M-1. Five orphan bib entries (declared, never cited).**

MEMORY.md predicted 3 orphans; actual is 5:

| Key | Bib line | Status |
|---|---|---|
| `adaspec2025` | sn-bibliography.bib:257 | Expected orphan (session-21 cite-group drop). |
| `edge2024graphrag` | sn-bibliography.bib:265 | Expected orphan (session-21 cite-group drop). |
| `zhang2020effect` | sn-bibliography.bib:157 | Expected orphan (session-21 cite-group drop). |
| `bertscore2020` | sn-bibliography.bib:194 | **Not flagged in MEMORY.** Was cited in v1; uncited in v2. BERTScore is still discussed in v2 text (tex:455, 474 — "BERT-F1", "Mean BERTScore F1") but without a `\cite{}`. |
| `karpukhin2020dense` | sn-bibliography.bib:165 | **Already orphan in v1.** Carried forward. Topic (Dense Passage Retrieval) is adjacent to the cited `reimers2019sentence` + `thakur2021beir`. |

- **Fix recommendations**:
  - `bertscore2020`: re-add a `\cite{bertscore2020}` next to the first BERTScore mention (tex:455 `Mean BERTScore F1`) OR drop the entry. Pre-existing science-claim convention favors adding the cite — the BERTScore metric is non-trivially attributed and reviewers may flag uncited use.
  - `karpukhin2020dense`: drop the entry; it has been orphan since v1 with no in-text justification.
  - `adaspec2025`, `edge2024graphrag`, `zhang2020effect`: leaving orphan is intentional per session-21 decision; either drop entirely or keep silent.

**M-2. Citation-style consistency.**
- `\cite{}`: 29 occurrences.
- `\citep`, `\citet`, `\citeauthor`: 0 occurrences each.
- All-uniform `\cite{}` style. No mixed-style rendering risk. ✓

**M-3. Self-citation check.**
- Bib grepped for `[redacted]`, `[redacted]`, `[redacted]`, `[redacted]`, `De,`, `[redacted]`, `[redacted]`.
- Zero matches. No self-citations to author names or affiliation. ✓
- Note: This is unusual for an iterative work — the v1 paper itself is **not** cited as a prior submission in v2. Reviewers MAY ask why the authors do not self-cite their own v1; the v2 paper instead refers to "v1" in prose (e.g., tex:160 "v1 paper's 3.0-point rubric", tex:447 etc.) without a citation. This is acceptable since v1 may not be officially indexable, but consider adding a self-cite if v1 has a DOI.

**M-4. Author lists trimmed via "and others" in v2.**
Several v2 entries replace full author lists from v1 with `"X, Y and others"`. Not a render bug, but reduces searchability:
- `bansal2021does`: v1 had 8 authors → v2 line 57 truncated to `"Bansal, Gagan and Wu, Tongshuang and Zhou, Joyce and others"`.
- `chen2024rcagent`: v1 had 9 authors → v2 line 65 truncated to 3 + others.
- `thakur2021beir`: v1 had 5 authors → v2 line 139 truncated to 3 + others.
- `zhu2023loghub`: v1 had 7 authors → v2 line 174 truncated to 3 + others.
- `christakopoulou2024talker`: v1 note said "Google DeepMind, arXiv:2410.08328" → v2 line 205 just "arXiv:2410.08328".
- `karpukhin2020dense`: v1 had 8 authors → v2 line 166 truncated to 3 + others.
- `arigraph2024`: v1 had 4 authors → v2 line 86 truncated to 3 + others; venue trimmed `Proc. IJCAI` vs full name.
- `reimers2019sentence`, `lewis2020retrieval` unchanged.
- **Recommendation**: For camera-ready, restore full author lists from v1 (no page budget reason to abbreviate the bib).

---

## v1 vs v2 bibliography diff

### Added in v2 (9 keys present in v2 bib, absent from v1 bib)

| Key | v2 bib line | Brief title / venue | Cited in v2? |
|---|---|---|---|
| `shi2025aiopslabs` | 212 | AIOpsLab — MLSys 2025 | YES (tex:406, 704, 734) |
| `xu2025openrca` | 219 | OpenRCA — ICLR 2025 | YES (tex:704, 734) |
| `pei2025flowofaction` | 226 | Flow-of-Action — WWW 2025 | YES (tex:734) |
| `liu2025logeval` | 233 | LogEval — Springer EMSE 2025 | YES (tex:406) |
| `miller2025bootstrap` | 242 | Bootstrap CIs for NLP Eval — arXiv:2503.01747 | YES (tex:451) |
| `nvidia2024specdec` | 250 | Speculative Decoding — NVIDIA blog | YES (tex:514, 744) |
| `adaspec2025` | 257 | AdaSpec — arXiv:2503.05096 | **NO (orphan)** |
| `edge2024graphrag` | 265 | GraphRAG — arXiv:2404.16130 | **NO (orphan)** |
| `peng2025graphragsurvey` | 273 | Graph RAG Survey — ACM TOIS 2025 | YES (tex:739) |

### Comparison against MEMORY's "12 expected new entries"

| Expected | Status |
|---|---|
| AIOpsLab (MLSys 2025) | ✓ shi2025aiopslabs |
| OpenRCA (ICLR 2025) | ✓ xu2025openrca |
| Flow-of-Action (WWW 2025) | ✓ pei2025flowofaction |
| LogEval (Springer EMSE 2025) | ✓ liu2025logeval |
| AIOps Survey 2025 (ACM CS) | ⚠ `zhang2024aiopssurvey` exists from v1 — year 2024 not 2025 (see I-2) |
| Miller et al. CLT/bootstrap (arXiv:2503.01747) | ✓ miller2025bootstrap |
| Brittlebench/PromptRobust (NAACL-SRW 2025) | **MISSING** — no matching entry |
| NVIDIA spec-decoding blog | ✓ nvidia2024specdec |
| AdaSpec (arXiv:2503.05096) | ✓ adaspec2025 (orphan, intentional) |
| Edge et al. GraphRAG (arXiv:2404.16130) | ✓ edge2024graphrag (orphan, intentional) |
| Peng et al. Graph RAG Survey (ACM TOIS 2025) | ✓ peng2025graphragsurvey |
| C3AI (WWW 2025) | **MISSING** — no matching entry |

**Missing 2 of 12**: Brittlebench/PromptRobust and C3AI. If these were planned as cites and dropped, that may be intentional (page budget). If they were supposed to land in §5.x or Related Work, they're absent. Review against SESSION_12+ plan documents to confirm intentional drop vs accidental omission.

### Removed from v1 (entries that were in v1 bib but now absent from v2 bib)

NONE. All 27 v1 bib entries are preserved in v2 (the v2 bib is a strict superset of v1 bib + 9 new entries = 36 total).

### Removed cites from v1 (keys cited in v1 tex but not in v2 tex)

| Key | v1 status | v2 status |
|---|---|---|
| `bertscore2020` | cited | uncited (M-1: BERTScore still used in v2 text without `\cite`) |
| `zhang2020effect` | cited | uncited (session-21 intentional drop) |

### Modified entries (bib field changes between v1 and v2)

The v2 bib generally TRIMMED v1 entries (author lists shortened, venue names abbreviated). No factual error introduced; see M-4 for the full list. No `title` or `year` changes detected for any carried-over key.

**Anomaly worth noting**: `alibaba2024qwen` title says **`{Qwen2.5: A Family of Large Language Models}`** (bib line 43) but the paper text consistently refers to **Qwen3** family (tex:277 `two models from the Qwen3 family`). The tex calls the family Qwen3 but cites a Qwen2.5 technical report. This bib title:text mismatch warrants verification — either the bib should be updated to a Qwen3 report or the text should match the cited Qwen2.5 report. This is a **POTENTIAL IMPORTANT** discrepancy I'm escalating; see I-5 below.

**I-5 (newly identified). `alibaba2024qwen` title says "Qwen2.5" but paper text uses "Qwen3" family.**
- Bib `sn-bibliography.bib:43`: `title = "{Qwen2.5: A Family of Large Language Models}"`
- Tex `sn-article.tex:277`: `two models from the Qwen3 family~\cite{alibaba2024qwen}`
- Also tex:135 cites `alibaba2024qwen` for "LLM output non-determinism from temperature-based sampling" — generic enough to apply to either version.
- **Action**: update bib title to the actual Qwen3 tech report (the team published a separate Qwen3 release in mid-2025), or update tex to say "Qwen2.5 family" if the deployed models are actually 2.5. Verify which model family is actually deployed in the benchmark.

---

## Cited entries count vs expected (31)

**Actual cited unique keys: 31** (matches expected exactly).

Full list (alphabetical):

```
alibaba2024qwen
arigraph2024
askell2024collective
bai2022constitutional
bansal2021does
chen2022automap
chen2024autonomous
chen2024rcagent
christakopoulou2024talker
cncf2024survey
datadog2024observability
grafana2024loki
guo2017calibration
lemma2024rca
lewis2020retrieval
li2024opseval
liu2025logeval
miller2025bootstrap
notaro2021aiopssurvey
nvidia2024specdec
opentelemetry2024collector
parasuraman2000model
pei2025flowofaction
peng2025graphragsurvey
reimers2019sentence
shi2025aiopslabs
thakur2021beir
wu2020microrank
xu2025openrca
zhang2024aiopssurvey
zhu2023loghub
```

**Bib total entries: 36** (31 cited + 5 orphan = `adaspec2025`, `bertscore2020`, `edge2024graphrag`, `karpukhin2020dense`, `zhang2020effect`).

---

## OK

- **Zero broken references**: every cited key resolves to a bib entry.
- **Citation style is uniform** (`\cite{}` only; no `\citep`/`\citet`/`\citeauthor`).
- **No self-citations** to the paper's authors or affiliation.
- **All 13 sampled contextual placements** verified correct (cite is topically aligned with surrounding sentence).
- **v1→v2 bib diff is clean and additive**: no v1 entries removed; 9 new entries added (matching planned revision scope ±2).
- **Required BibTeX fields** (author/title/venue/year) present for all new entries.
- **Multi-key cite groups** (e.g. `\cite{a,b,c}`) parse cleanly with no trailing comma / whitespace issues.

---

## Skipped

- **Page numbers / DOI verification against external sources** (e.g., did MLSys 2025 actually publish AIOpsLab at the page range stated?) — out of scope; needs external lookup (CrossRef, dblp).
- **Author-list canonicalization** (full first-name vs initial, Asian-name surname order) — purely cosmetic, no impact on render.
- **`.bbl` file** verification — not generated yet; will be confirmed at next pdflatex/bibtex compile.
- **Latex compile log** for warning-level cite issues — relied on session-21 handoff's "clean compile" claim instead of re-running.
- **Citations in supplementary materials** (if any) — out of audit scope.
- **Cross-reference (`\ref{}`) audit** — separate auditor scope.

---

## Recommendations

**Pre-submission must-fix (IMPORTANT-level)**:

1. **I-5**: Reconcile `alibaba2024qwen` Qwen2.5 vs Qwen3 mismatch. Either update the bib title to the Qwen3 tech report or change the tex "Qwen3 family" wording.
2. **I-3**: Add `\url{}` to `nvidia2024specdec` so the NVIDIA blog post is locatable.
3. **I-2**: Verify `zhang2024aiopssurvey` actual publication year (ACM CS sometimes assigns publication dates spanning a year boundary).
4. **M-1 (bertscore2020)**: Either re-cite BERTScore (BERTScore is used as a non-trivial metric and reviewers may flag uncited use at tex:455, 474) or drop the bib entry.
5. **I-1**: Add volume/issue/article-number to `peng2025graphragsurvey` once ACM TOIS finalizes.

**Nice-to-have (MINOR-level)**:

6. **M-1 (karpukhin2020dense)**: Drop or cite — orphan since v1.
7. **M-1 (adaspec2025, edge2024graphrag, zhang2020effect)**: Confirm intentional retention as orphans; otherwise drop.
8. **M-4**: Restore full author lists from v1 for the 7 entries that were trimmed in v2 (no page budget justifies this, and reviewers value complete author attribution).
9. **I-4**: Update the bib header comment `26 references` → `36 entries (31 cited)`.
10. **MEMORY-12-list missing entries**: Confirm Brittlebench/PromptRobust and C3AI were intentionally dropped from the v2 reference list (the v2 paper does not appear to discuss prompt-robustness benchmarks or C3AI directly, so absence may be deliberate).

**No-action / observe**:

- Citation style is clean, all-`\cite{}` — keep as is.
- Self-citation: no current mention of v1; if v1 has a DOI/arXiv ID, consider adding `~\cite{v1self}` at first "v1 paper" mention (tex:160, 447). Otherwise the current prose-reference is fine.

---

*Audit complete. Total: 0 CRITICAL, 5 IMPORTANT, 4 MINOR finding clusters. Citations are sound for compile; the bib has ~5 polish items before camera-ready.*
