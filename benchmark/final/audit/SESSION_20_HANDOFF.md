# Session 20 → Session 21 Handoff (2026-05-26)

> ## ⚠ STATUS AT WRITING — PHASE B IN PROGRESS
>
> Session 20 wakes from hibernation, finishes the AWS Phase 4.5 wrap (PATH 4 locked), documents the new D-17 bug, and proceeds with Phase B sandbox paper edits. This file is the close-out. Session 21 (if needed) starts at §6 below.

---

## §0. One-line state

Phase C ✅ wrapped (AWS Phase 4.5 outcome: PATH 4). D-17 patched + documented. Phase B sandbox paper edits **in progress** (this session is doing them). Phase D commits + rsync + push remain — gated on user GO.

---

## §1. What happened this session (chronological)

1. **State re-gather** — read MEMORY.md, SESSION_19_HANDOFF.md in full, SUMMARY.md, paper_sandbox_active memory file
2. **State verify** — git HEAD `57035cf`, 42 modified files (matches expectation); AWS instance `running` (still on from session 19 launch); CloudWatch alarm `ActionsEnabled=False, StateValue=ALARM` (the ALARM state was the first signal Phase 4.5 had completed — CPU < 5% for 30 min)
3. **SSH re-authorize** — laptop public IP rotated `49.37.33.243 → 49.37.33.71`; added the new CIDR to `sg-09680d8eb448fb704`
4. **AWS validation** (per SESSION_19_HANDOFF §4.0 10-step block) — `.FAIL` marker present, tmux gone, python gone, log tail shows all 5 folds completed with `no-graph=100.0% with-graph=100.0%` then `TypeError: Object of type TestCaseResult is not JSON serializable` at `run_graph_experiments.py:172`
5. **Decision rule** — 4.5b |Δ|=0pp (fails ≥2pp), 4.5c never ran (cannot satisfy ≥3pp) → **PATH 4 locked**
6. **scp Phase 4.5 results** to `benchmark/final/phase45_graph/`: `exp_4_5b_summary.json` (757B valid), per-case JSONLs (0B — lost), `exp_4_5c_summary.json` (489B stale session-17)
7. **STOP instance** — `aws ec2 stop-instances` → `running → stopping`, then `aws ec2 wait instance-stopped` blocked until `stopped` at 05:19:47 GMT
8. **RE-ENABLE CloudWatch alarm** — `ActionsEnabled=True`, action `arn:aws:automate:us-east-1:ec2:stop` confirmed
9. **User confirmed Option A** — drop both tests, document AWS parts, proceed with Phase B
10. **D-17 patch** — `run_graph_experiments.py:31` added `import dataclasses`; lines 172/174 wrapped with `json.dumps(dataclasses.asdict(r), default=str)`
11. **Forensic log written** — `benchmark/final/phase45_graph/_failed_run_log.txt` (captures full crash traceback + per-fold progress + AWS final state)
12. **BUG_HISTORY.md** — added summary-table row #9 + new D-17 footnote (sister of D-16, attribute-access vs file-write halves of same dataclass type)
13. **SUMMARY.md** — header line 3 prepended session-20 Phase 4.5 outcome; NEW §3.6 Phase 4.5 outcome (decision rule + table of outcomes + paper integration plan); §6 AWS state refreshed (live-verified, includes CW alarm + cost delta)
14. **Phase B (in progress)** — sandbox `.tex` edits per SESSION_19_HANDOFF §5

---

## §2. What changed on disk in session 20

### Modified (uncommitted, working tree)
- `benchmark/scripts/run/run_graph_experiments.py` — D-17 patch (`import dataclasses` + 2 call-site wraps)
- `benchmark/final/docs/BUG_HISTORY.md` — summary-table row #9 + D-17 footnote
- `benchmark/final/SUMMARY.md` — header session-20 prepend + NEW §3.6 + §6 refresh
- `PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2.sandbox-session16/sn-article.tex` (in progress, Phase B) — Tables 2/6a/6b/7 + 4 new sentences + tab:graphsub PATH 4 + BERT-F1 column + footnotes

### NEW files (untracked)
- `benchmark/final/phase45_graph/exp_4_5b_summary.json` (scp'd, 757B)
- `benchmark/final/phase45_graph/exp_4_5b_no_graph.jsonl` (scp'd, 0B — D-17 loss)
- `benchmark/final/phase45_graph/exp_4_5b_with_graph.jsonl` (scp'd, 0B — D-17 loss)
- `benchmark/final/phase45_graph/exp_4_5c_summary.json` (scp'd, 489B — stale session-17, DO NOT USE)
- `benchmark/final/phase45_graph/_failed_run_log.txt` (forensic record of crash)
- `benchmark/final/audit/SESSION_20_HANDOFF.md` (THIS FILE)

### Carried over from session 18-19 (still uncommitted)
- 29 files from session 18 (D-1 dataset re-label + 16 result files + 4 stats + 5 docs + 3 scripts + 2 audit + SESSION_18_HANDOFF.md)
- 14 result files with `bert_f1` field populated (BERT recompute session 18)
- 2 docs from session 19: `SUMMARY.md` (D-6 footer/§3.5/§5), `BUG_HISTORY.md` (D-6 footnote)
- 1 NEW from session 19: `audit/SESSION_19_HANDOFF.md`

### Git state (UNCHANGED, no new commits this session yet)
- Local HEAD: `57035cf` (D-13 patch from session 16)
- Origin: `a5e9005` (still 2 commits behind: `ee8f125` + `57035cf`)
- Pending commit groups for Phase D — see §6 below

### AWS final state
- Instance `i-091c4de0e95d63154`: **stopped** at 2026-05-26 05:19:47 GMT ✅
- CloudWatch alarm `aiops-idle-stop`: **ActionsEnabled=True** ✅
- EIP `44.195.172.165` + EBS root + data: preserved
- Snapshot `snap-01b191aedbf46b598`: held
- Phase 4.5 EBS preserves full logs (`/mnt/runs/phase45_*` + `/mnt/aiops-repo/benchmark/final/phase45_graph/`) — retrievable on next instance start
- Cumulative spend ~$55 / $120 ceiling

---

## §3. Phase 4.5 OUTCOME — full decision trace (lookup-ready)

**Inputs to decision rule** (locked pre-hibernation per SESSION_19_HANDOFF §4.4):
- 4.5b aggregate Δ: `0.0pp` (5 folds × no-graph=100% with-graph=100%, ceiling effect)
- 4.5c monotone lift N=0→60: **N/A — never ran** (crash in 4.5b post-processing)

**Both threshold clauses fail** → PATH 4 fires.

**Locked outcome**:
- Drop the two `[TBD]` rows for 4.5b and 4.5c from sandbox `tab:graphsub`
- Keep only the §4.5a heterogeneous steady-state row (already real data from `tab:ablation_comp` with-graph row: Δ=−1.1pp, p=0.289 NS)
- Replace with the disclosure sentence in §4.5 prose (pre-drafted in SESSION_19_HANDOFF §5.1; refined below for honesty about 4.5c never running):

> *"The homogeneous-LEMMA 5-fold sub-experiment saturated at the model's accuracy ceiling on this difficulty (no-graph = with-graph = 100% across all 5 folds, n=80, populated graph N=431); the cold-start curve sub-experiment is left for future work. Graph memory's architectural value in this paper therefore rests on the heterogeneous-distribution result (§4.5a, Δ=−1.1pp, p=0.289 NS) rather than on homogeneous-easy regimes."*

**Why the ceiling is real (not a retrieval bug)**:
- Neo4j held 431 populated episodes throughout (confirmed via `MATCH (e:Episode) RETURN count(e)`)
- with-graph also achieved 100% on every fold (if graph context wasn't injecting, with-graph would diverge from no-graph)
- Per-fold trace shows consistent 16/16 = 100% in both arms, not e.g. 15/16 vs 16/16

**Why 4.5b might saturate**:
- LEMMA-RCA cloud-microservices cases have narrow-vocabulary expected outputs ("DB primary failover", "Pod OOMKilled", "Gateway timeout") which the 14B model with constitutional gating handles well
- The homogeneity that was supposed to demonstrate retrieval value also made the cases individually easy
- Reframing in §4.5: graph memory shows up under heterogeneous distributions where retrieval narrows the search; under homogeneous-easy, the model doesn't need retrieval to begin with

---

## §4. Hard constraints (carry forward — UNCHANGED + session-20 additions)

(Numbered to extend SESSION_19_HANDOFF §7)

1-20. (UNCHANGED — see SESSION_19_HANDOFF §7)

21. **Phase 4.5 PATH 4 is locked** — do not re-run 4.5b (ceiling is property of data + model, not the bug); 4.5c re-run is hypothetically possible (~$1, ~40 min) but the paper text does not depend on it
22. **D-17 patch is local-only** — `run_graph_experiments.py` updated on laptop; instance copy at `/mnt/aiops-repo/...` is still buggy. Re-SCP only if re-running Phase 4.5
23. **4.5c stale JSON on disk** (`exp_4_5c_summary.json`, all-zero, mtime 2026-05-25 10:06 UTC) — DO NOT cite, DO NOT delete (keep as forensic provenance of session-17 attempt; the `_failed_run_log.txt` documents its provenance)
24. **D-17 forensic log** at `benchmark/final/phase45_graph/_failed_run_log.txt` — committed as part of Phase D commit 5; do not delete

---

## §5. Phase B sandbox edit list — DONE THIS SESSION (status updated 2026-05-26 close)

| # | Edit | Status |
|---|---|---|
| 5.1 | Table 2 (`tab:overall`) + line 455 prose + line 632 prose | ✅ DONE |
| 5.2 | Table 6a (`tab:ablation_arch`) post-D-1 | ✅ DONE |
| 5.3 | Table 6b (`tab:ablation_comp`) post-D-1 | ✅ DONE |
| 5.4 | Table 7 (`tab:sota`) + caption + footnote (D-3 launch-window integrated) | ✅ DONE |
| 5.5 | Table 6 (`tab:graphsub`) PATH 4: dropped → became §5.8 (1 paragraph) | ✅ DONE |
| 5.6 | 4 new sentences: D-1 / D-2 / D-3 / Conflict-4 + line 649 backmatter 71→74 | ✅ DONE |
| 5.7 | BERT-F1 column — Option B tried (17p), reverted to **Option C** (1-sentence in §5.3) | ✅ DONE |
| 5.8 | Phase B-2 subagent pass: Table 1 N fill + shrink, §5.3 para-table, Table 2 Semantic col, NEW Table 3 errortable, NEW Table 4 latency, §5.6 para-table-table, §5.7 trim, §6.1 30% compress, NEW Fig 3 ablation bar chart | ✅ DONE |
| 5.9 | Final sandbox PDF = **16 pages / 461,918 bytes / 785 lines, clean compile** | ✅ DONE |

All edits in `sn-article-template.v2.sandbox-session16/sn-article.tex`. **Sandbox-session16 IS the final draft location** (rsync to real `sn-article-template.v2/` permanently dropped per user, 2026-05-26).

---

## §5.locked — 5 FINAL LOCKED DECISIONS for session 21 (user-confirmed 2026-05-26)

Apply in this exact order. After each, recompile (2× pdflatex pass) and verify ≤16 pages. If any pushes to 17p, apply per-decision fallback.

Authoritative table/figure render order (verified end of session 20):
- Table 1 = `tab:datasets` (line 409)
- Table 2 = `tab:overall` (line 458)
- Table 3 = `tab:errortable` (line 489)
- **Table 4 = `tab:latency` (line 515-533) — DECISION 1 TARGET**
- Table 5 = `tab:ablation_arch` (line 638; caption says "Ablation 6a" — naming legacy)
- Table 6 = `tab:ablation_comp` (line 665; caption says "Ablation 6b")
- Table 7 = `tab:sota` (line 701)
- Figure 1 (line 173) — Architecture
- Figure 2 = `fig:graph_memory` (line 295) — Graph schema
- **Figure 3 = `fig:ablation_chart` (line 540-634) — DECISION 3 TARGET**

### Decision 1 — Table 4 (`tab:latency`) → Option A (v1 component×metrics layout, after Option D recompute)

**Step 1**: Compute per-task percentiles. Bucket `benchmark/final/main_benchmark/results.json` by `task_type` ∈ {annotation, rca} and compute P50, P95, P99 of `latency_ms` for each bucket.

```python
import json, statistics
from pathlib import Path
d = json.loads(Path('benchmark/final/main_benchmark/results.json').read_text(encoding='utf-8'))
recs = d if isinstance(d, list) else d.get('test_results', d.get('results', []))
ann = [r['latency_ms'] for r in recs if (r.get('task_type') or r.get('test_case',{}).get('task_type'))=='annotation' and r.get('latency_ms') is not None]
rca = [r['latency_ms'] for r in recs if (r.get('task_type') or r.get('test_case',{}).get('task_type'))=='rca' and r.get('latency_ms') is not None]
def pcts(xs): xs = sorted(xs); n=len(xs); return {'P50': xs[n//2], 'P95': xs[int(n*0.95)], 'P99': xs[int(n*0.99)], 'avg': statistics.mean(xs), 'min': xs[0], 'max': xs[-1]}
print('annotation:', pcts(ann)); print('rca:', pcts(rca))
```

**Step 2**: Replace sandbox lines 515-533 with v1 component×metrics layout. Reference v1 paper at `c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\Final Submission Paper (Accepted v.1)\1ST SUBMISSION\sn-article-template\sn-article.tex` lines 515-532 for the exact v1 structure.

Target table:
```
\begin{tabular}{lccccc}
\textbf{Component} & \textbf{VRAM} & \textbf{P50 (s)} & \textbf{P95 (s)} & \textbf{Avg (s)} & \textbf{Range (s)} \\
\midrule
4B Fast (annotation)   & ~4 GB  & <P50_ann>  & <P95_ann>  & 3.07 & 2.05--21.7 \\
14B Reasoning (RCA)    & ~11 GB & <P50_rca>  & <P95_rca>  & 32.5 & 11.5--84.5 \\
\midrule
\textbf{End-to-End}    & ~15 GB & 4.1        & 48.4       & 17.6 & ---        \\
\botrule
\end{tabular}
\smallskip
\footnotesize{Both models loaded simultaneously (63\% of 24 GB). Network RTT 1.10 ms subtracted. End-to-end P99 80.5 s. Run on AWS L4 24GB host.}
```

**Goal**: zero `---` cells except possibly the End-to-End Range cell (acceptable).

### Decision 2 — Latency Stack B → Option A (keep Stack A only)

No table change. §5.5 prose at line 513 already states "Preliminary vLLM+FP8 gate tests show $\sim$1.5$\times$ speedup" — leave intact.

### Decision 3 — Figure 3 (`fig:ablation_chart`) → Option A+D (restore v1 dims + xmin=30)

At sandbox lines 540-634, apply these exact edits:
- Line 546: `height=5.4cm` → `height=8.5cm`
- Line 548: `bar width=4pt` → `bar width=6pt`
- Line 552: `xmin=40` → `xmin=30`
- Line 554: `xtick={40,60,80,100}` → `xtick={30,50,70,90}`
- Line 588 highlight rect: `\fill[red!10, opacity=0.5] (axis cs:40,0.55) rectangle (axis cs:101,1.45);` → change `axis cs:40` to `axis cs:30` to extend the highlight to the new xmin

**Compile gate**: if PDF ≤16p, success. If 17p → revert dims to compromise `height=7cm bar width=5pt` (Option B+D). If still 17p → apply Decision 5 (compress §6.1).

### Decision 4 — Drop §5.8 Graph Sub-experiment subsection → Option B

**Step 1**: Delete sandbox lines 720-723 entirely:
```
\subsection{Graph-Episodic Memory Sub-experiment}
\label{sec:graph_subexp}

The Sec.~\ref{sec:ablation} with-graph row (Table~\ref{tab:ablation_comp}: $\Delta{=}-1.1$pp, $p{=}0.289$ NS) is computed under \emph{heterogeneous} retrieval, conflating cold-start and cross-domain sparsity. A homogeneous-LEMMA 5-fold sub-experiment saturated at the accuracy ceiling (no-graph $=$ with-graph $=$ 100\%, $n{=}80$, populated graph $N{=}431$); a cold-start curve is deferred (Sec.~\ref{sec:future})~\cite{peng2025graphragsurvey,edge2024graphrag}. Graph-memory value in this paper thus rests on heterogeneous-distribution evidence, not homogeneous-easy regimes.
```

**Step 2**: Fix the now-dangling `\ref{sec:graph_subexp}` references.

- At line 737 (§6.2 Limitations), REPLACE:
```
Graph-RAG's architectural value rests on heterogeneous-distribution evidence (Sec.~\ref{sec:graph_subexp}); the homogeneous-LEMMA sub-experiment saturated at the ceiling.
```
WITH (absorbs the dropped §5.8 content into Limitations):
```
Graph-RAG's architectural value (Table~\ref{tab:ablation_comp} with-graph row: $\Delta{=}-1.1$pp, $p{=}0.289$ NS) is computed under heterogeneous retrieval; a planned homogeneous-LEMMA 5-fold sub-experiment saturated at the model's accuracy ceiling at this difficulty (no-graph $=$ with-graph $=$ 100\%, $n{=}80$, populated graph $N{=}431$)~\cite{peng2025graphragsurvey,edge2024graphrag}, leaving cross-domain retrieval-space sparsity as the more informative regime for future memory-architecture work.
```

- At line 742 (§6.3 Future Work), REPLACE the parenthetical `(Sec.~\ref{sec:graph_subexp})`:
```
Three near-term directions extend this submission: (1)~\textbf{Cold-start curve and harder homogeneous-domain memory benchmarks} --- LEMMA-RCA 5-fold saturated at the accuracy ceiling (Sec.~\ref{sec:graph_subexp}); a cold-start curve at $N\in\{0,20,40,60\}$ and harder-distribution sub-experiments remain to be run;
```
WITH (just drop the parenthetical; rest of paragraph stays):
```
Three near-term directions extend this submission: (1)~\textbf{Cold-start curve and harder homogeneous-domain memory benchmarks} --- the LEMMA-RCA 5-fold sub-experiment saturated at the model's accuracy ceiling at the current difficulty; a cold-start curve at $N\in\{0,20,40,60\}$ and harder-distribution sub-experiments remain to be run;
```

### Decision 5 — §6.1 Research Gap Validation → Option C (keep as-is)

Only apply further compression IF after Decisions 1+3+4 the PDF is at 17p. Target if forced: drop the 2-sentence "Architectural-contrast novelty" paragraph at line 732 (move into §6.2 Limitations or §7 Conclusion as a single inline sentence).

---

---

## §6. Phase D plan (session 21)

### §6.1 Gate 1 — 7 themed local commits (USER-APPROVED in principle session 20; verify each before pushing)

NO Claude trailer (`Co-Authored-By: Claude ...`). NO emoji in commit messages. Use HEREDOC for multi-line bodies. Apply AFTER Decisions 1+3+4 land and sandbox PDF re-verified ≤16p.

1. `data(D-1): re-label 33 OpsEval-remined cases as qa_mcq + sync 16 result files + Phase 5 recompute`
   - Files: `benchmark/intermediate/datasets/benchmark_431_seed42.json`, 16 result files under `benchmark/final/main_benchmark/*` and `benchmark/final/ablation_v4/ablation_*/*` and `benchmark/final/sota_baselines/*` and `benchmark/final/phase46_no_prompt/*`, `benchmark/final/ablation_v4/phase5_stats.{json,md}`, `benchmark/final/ablation_v4/matched_eval_table.md`, `benchmark/final/main_benchmark/phase5_stats.json`
2. `docs: update SUMMARY/METHODOLOGY/MANIFEST/BUG_HISTORY/AUDIT_REPORT for post-D-1 + D-2/D-3/D-5/Conflict-5 disclosures`
   - Files: `benchmark/final/SUMMARY.md` (header, §3.x), `benchmark/final/docs/METHODOLOGY.md`, `benchmark/final/MANIFEST.md`, `benchmark/final/AUDIT_REPORT.md`
3. `fix(benchmark/scripts): D-7 test_5plus5 ref + D-14 path fallback + D-16 dataclass attr + D-17 dataclass file-write`
   - Files: `benchmark/scripts/run/run_graph_experiments.py` (D-14 + D-16 + D-17), `benchmark/scripts/run/test_5plus5.py` (D-7 if any), helper scripts at `benchmark/scripts/_*.py`
4. `eval(D-6): BERT-F1 recompute via roberta-large on CUDA + recompute_bert_f1.py + SUMMARY.md §3.5 + BUG_HISTORY.md D-6 -> RESOLVED`
   - Files: `benchmark/scripts/eval/recompute_bert_f1.py`, `benchmark/final/_bert_f1_recompute_summary.json`, `benchmark/final/_bert_recompute.log`, 14 result files with `bert_f1` populated in place, `benchmark/final/docs/BUG_HISTORY.md` D-6 footnote, `benchmark/final/SUMMARY.md` §3.5
5. `data(4.5): Phase 4.5 LEMMA-CV results (PATH 4 ceiling outcome) + D-17 forensic log + BUG_HISTORY.md D-17 + SUMMARY.md §3.6 + §6 AWS refresh`
   - Files: `benchmark/final/phase45_graph/exp_4_5b_summary.json`, `exp_4_5b_no_graph.jsonl`, `exp_4_5b_with_graph.jsonl`, `exp_4_5c_summary.json`, `_failed_run_log.txt`; `benchmark/final/docs/BUG_HISTORY.md` (#9 + D-17 footnote); `benchmark/final/SUMMARY.md` (header + §3.6 + §6)
6. `paper(sandbox-session16): Tables 1-7 post-D-1 + tab:graphsub dropped + Fig 3 v1-dims + 4 new sentences + BERT-F1 Option C + Decision 1/3/4 final`
   - Files: ONLY sandbox `.tex` + `.bib` + `.pdf` + `.log/.aux/.out` under `sn-article-template.v2.sandbox-session16/`. **Do NOT touch real `sn-article-template.v2/`.**
   - Note: paper tree is OUTSIDE constitutional-aiops/ git → this commit covers the sandbox dir if it's been added; if outside git entirely, this commit is skipped and the sandbox is just preserved on disk
7. `docs(audit): SESSION_19_HANDOFF + SESSION_20_HANDOFF close-outs`
   - Files: `benchmark/final/audit/SESSION_19_HANDOFF.md`, `benchmark/final/audit/SESSION_20_HANDOFF.md`

### §6.2 Gate 2 — Rsync sandbox → real: **PERMANENTLY DROPPED**

User-locked decision 2026-05-26: sandbox-session16 IS the final draft location. Do NOT rsync, robocopy, or otherwise copy contents to `sn-article-template.v2/`. The real path stays untouched as v1.5 reference. Update `project_paper_sandbox_active.md` memory file to reflect this if not already done.

### §6.3 Gate 3 — Push to origin: REQUIRES EXPLICIT USER GO

Do NOT execute `git push origin main` without separate confirmation in-conversation. After Gate 1 commits land locally, halt and ASK.

```powershell
# Only after USER GO:
git push origin main
```

---

## §7. Open follow-ups for future sessions (low priority)

- If reviewer asks for 4.5c data: re-run standalone on AWS (~40 min, ~$1) after applying D-17 patch to instance
- BERT-F1 recompute with `MIN_TEXT_LEN=5` (to fill the `ablation_no_structured` Ann n=1 and `ablation_no_system_prompt` Ann n=0 cells) — out of scope unless reviewer asks
- Potential Phase 5 stats recompute with `phase5_stats.py` extended to include McNemar on the 4.5b 80-case subset (would all be 1.0 p-values given ceiling — likely not worth it)

---

## §8. First-action quickref for session 21 (if needed)

```
SESSION 21 STARTUP (if needed)
1. Read MEMORY.md + this handoff (5 min)
2. State verify: git, sandbox PDF, AWS state (should be stopped) (3 min)
3. Resume Phase B (if in-progress) OR begin Phase D commits per §6 (5-30 min)
4. Halt at rsync + push for USER GO
```

End of handoff. Phase B in progress; this file will be updated again at end of session 20 with final PDF page count + commit list status.
