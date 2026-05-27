# Constitutional AIOps — Agent Handoff Document

**Last updated**: 2026-05-27 (session 29 close — multi-agent paper verification phase **ALL 6 STAGES COMPLETE**: Stage 6 (Final Synthesis) landed in session 29 with VERDICT **DEFER**. Synthesis cross-validated all 5 prior reports + reconciled the cumulative **24 bib field-level corrections across 14 entries** + produced 7-phase edit plan + flagged 17p-overshoot risk on title-rewrite fields C4/C6/C9/C12/C14 in Batches B+C. Main session manually sanity-checked Stage 6's load-bearing claims against ground-truth `.bib` + `.tex` — all 13 bib line-ranges EXACT, cite-grep verifications PASS at sandbox `.tex` lines 135 + 143 + 160 + 168 + 383 + 406 + 422 + 736 + 768, wu year-already-2021 reconciliation CONFIRMED at `sn-bibliography.bib:76`, chen2024autonomous + notaro2021aiopssurvey placeholder/paywall status CONFIRMED. 1 themed commit landed (`30ba5ca` Gate 25 Stage 6 report). Gate 26 close-out + Gate 27 batched push (Gates 25-26) pending. **Edit-phase Batch A → B → C → manual fetches → topology Option A → optional polish sequenced for session 30** (first action: Batch A miller+wu+chen-automap, 3 entries / 7 fields). Sandbox PDFs preserved at 16p / unchanged SHA-256. AWS untouched.)
**For**: Next AI agent (Claude Code, Codex, etc.) to resume this work
**Working directory**: `c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\`
**Document location** (moved session 22): `constitutional-aiops/benchmark/HANDOFF.md` (was at repo root)

---

## 1. READ THESE FIRST (in order)

| Priority | File | Why |
|----------|------|-----|
| 1 | **THIS FILE** | Current state, what to do |
| 2 | `MEMORY.md` SESSION 23 STARTUP block | Live state snapshot, path discipline (auto-loaded) |
| 3 | `benchmark/final/audit/SESSION_22_HANDOFF.md` | Session 22 close + 5-agent paper audit synthesis (10 CRITICAL + 14 IMPORTANT + 7 MINOR findings) |
| 4 | `benchmark/final/audit/paper_audit_session22_2026-05-26/00_SUMMARY.md` | Master audit synthesis — file:line citations for every finding |
| 5 | `benchmark/final/audit/SESSION_21_HANDOFF.md` | Session 21 → 22 handoff (DIFF resume + sandbox polish) |
| 6 | `benchmark/final/audit/SESSION_20_HANDOFF.md` §6.1 | Gate 1 commit grouping reference |
| 7 | `benchmark/final/SUMMARY.md` | Canonical results landscape |
| 8 | `benchmark/final/docs/METHODOLOGY.md` | Eval methodology + 3-point rubric disclosure |

Memory dir (all files auto-loaded via MEMORY.md):
`C:\Users\partha\.claude\projects\c--Users-partha-Downloads-files-AIOPS-NEW\memory\`

---

## 2. Project Overview

**What this is**: Constitutional AIOps — autonomous IT operations system for B.Tech final year paper submitted to COMSYS 2026. Weak Accept verdict from 3 reviewers. This is the revision work to address reviewer concerns.

**Paper active edit target** (post-session-22 folder reorg):
- `c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\main\sn-article.tex`

**DIFF artifact** (v1 → current sandbox, red-text highlights):
- `...\sandbox-session16\diff\sn-article-DIFF.tex` + `.pdf` (16p, plain `\textcolor{red!75!black}` override, refs resolved)

**Paper v1 (reference only, READ-ONLY)**:
- `c:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\Final Submission Paper (Accepted v.1)\1ST SUBMISSION\sn-article-template\sn-article.tex`

**Old `sn-article-template.v2/` path**: MOVED by user (session 22 housekeeping) to `z.Dump Paper Archive\` — do NOT read or edit.

**Reviewer concerns and status**:
- R1/R2: Dataset too small (150) → expanded to 431 (post-D-1 re-label) ✅
- R2: No strong SOTA baselines → Llama 3.3 70B + DeepSeek V3.2 + Drain added ✅
- R1/R3: Graph memory −2.7% → re-tested with populated 431-episode graph: Δ=−1.1pp p=0.289 NS (within noise); LEMMA-CV ceiling outcome ✅
- R1/R3: P95 22.7s latency → Stack B vLLM measured at 43.71s (1.51× Stack A 65.96s speedup) ✅
- R2/R3: Writing refinement → Decisions 1/3/4 applied + Tables 1-7 rewritten + Fig 3 polished (sessions 18-21) ✅

**Team**: [redacted], [redacted], [redacted], [redacted]
**Institution**: [redacted]
**Advisor**: [redacted]

---

## 3. AWS Infrastructure State

| Resource | Value |
|----------|-------|
| Instance ID | `i-091c4de0e95d63154` |
| State | **STOPPED** (2026-05-26 05:19:47 GMT, end of Phase 4.5 wrap) |
| Type | g6.xlarge (NVIDIA L4 24GB, $0.8048/hr on-demand) |
| EIP | `44.195.172.165` (do NOT release) |
| EBS root | `vol-01714af69faebb973` (80 GB gp3, in-use) |
| EBS data | `vol-0ff075a7541026572` (100 GB gp3, mounted `/mnt`, in-use) |
| Snapshot | `snap-01b191aedbf46b598` (held, do NOT delete) |
| CloudWatch | `aiops-idle-stop` alarm, `ActionsEnabled=True` (CPU<5% × 30 min → auto-stop) |
| AWS Budget | $5/day cap → auto-stop at 100% |
| Region | `us-east-1` |
| Profile | `aiops-operator` |
| Cumulative spend | ~$55 / $120 ceiling (~46%) |
| Passive carry | ~$5/mo while stopped (EBS + EIP idle + snapshot) |

### Start instance (NOT needed unless reviewer demands new run)

```bash
aws ec2 start-instances --profile aiops-operator --region us-east-1 --instance-ids i-091c4de0e95d63154
aws ec2 wait instance-running --profile aiops-operator --region us-east-1 --instance-ids i-091c4de0e95d63154
# Add current laptop IP to SG (rotates per session):
LAPTOP_IP=$(curl -s checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --profile aiops-operator --region us-east-1 \
  --group-name aiops-vllm-sg --protocol tcp --port 22 --cidr ${LAPTOP_IP}/32
ssh -i ~/.ssh/aiops-key.pem ubuntu@44.195.172.165
```

### Stack A (Ollama Q4_K_M) — accuracy source of truth
```bash
curl http://localhost:11434/api/tags   # qwen3:4b-instruct + qwen3:14b should be listed
sudo systemctl start ollama            # if not auto-started
```

### Stack B (vLLM AWQ) — latency source of truth (Table 5)
```bash
# Stack A and Stack B share the same L4 GPU — run ONLY ONE at a time
sudo systemctl stop ollama
cd /mnt/aiops-repo
docker compose -f aws/docker-compose.vllm.yml up -d
curl http://localhost:8000/health     # 4B AWQ
curl http://localhost:8001/health     # 14B AWQ
```

### Stop instance (preserves EBS — DO NOT terminate)
```bash
aws ec2 stop-instances --profile aiops-operator --region us-east-1 --instance-ids i-091c4de0e95d63154
```

---

## 4. Git State

**Repository**: `c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\`
**Remote**: `https://github.com/Partha-dev01/Aiops_Final.git`
**Branch**: main
**Local HEAD**: `57035cf` — `fix(benchmark/scripts/run): D-13 patch — Phase 4.5 script API fixes`
**Origin HEAD**: `a5e9005` — 2 commits behind by design (Gate 1 + Gate 3 pending USER GO)
**Tags**: `paper-v1-submitted`, `bench-v2.0-frozen`

### Uncommitted local changes
**45 modified files in working tree** (session 17-22 cumulative — see §10 below for inventory).

**Gate 1**: 7 themed local commits drafted per `benchmark/final/audit/SESSION_20_HANDOFF.md` §6.1, awaiting USER GO. NO commits as of session 22 close.
**Gate 2 (rsync sandbox → real)**: **PERMANENTLY DROPPED** per user decision 2026-05-26. Sandbox IS the final draft location.
**Gate 3 (push origin/main)**: requires SEPARATE USER GO after Gate 1 lands.

### Recent commits (newest first)

```
57035cf  fix(benchmark/scripts/run): D-13 patch — Phase 4.5 script API fixes      [LOCAL HEAD]
ee8f125  (intermediate session-16 commit)                                          [LOCAL]
a5e9005  refactor(benchmark/scripts): Stage J — sub-folder into prep/run/eval/ops/_dev  [ORIGIN HEAD]
31d9bdc  feat: ablation v4 matched-eval + Phase 5 stats + FINAL/ + archive originals
98181c0  feat(sota): complete Llama 3.3 70B SOTA baseline (400/400)
6fc2011  feat(sota): Llama 3.3 70B partial SOTA results (374/400, resume-safe)
522245b  fix(aws): add scp fallback for sync_results.sh on Windows
06262e8  feat(phase45): add graph memory sub-experiment runner
ba282fa  feat(sota): add DeepSeek V3.2 model support to SOTA baseline runner
842c1e0  docs(results): regenerate all three result markdown files with correct numbers
```

**Important**: Instance has NO git. Always `scp` files directly, NEVER `git pull` on instance.

---

## 5. Sandbox Folder Layout (post-session-22 housekeeping)

After session 22 reorganization, the sandbox contains exactly 2 subfolders, each mirroring v1's flat layout:

```
sn-article-template.v2.sandbox-session16/
├── main/
│   ├── bst/  empty.eps  fig.eps
│   ├── sn-article.tex                (55,201 B, 789 LF lines — post-session-25 Path C audit fixes)
│   ├── sn-article.pdf                (467,673 B, 16 pages — post-session-26 peng year 2025→2026; SHA-256 be6c27ab...d9483)
│   ├── sn-bibliography.bib           (10,129 B, 272 LF lines; 35 entries; 32 cited; 3 retained-orphan — post-session-26 peng year=2026)
│   ├── sn-jnl.cls  sn-mathphys-num.bst
└── diff/
    ├── bst/  empty.eps  fig.eps
    ├── sn-article.tex                (55,201 B — read-only copy = diff target, mirrors main)
    ├── sn-article-DIFF.tex           (68,263 B, 830 LF lines — latexdiff-fast INVISIBLE + --no-del + simplified red-text override, listings dep dropped)
    ├── sn-article-DIFF.pdf           (469,231 B, 16 pages, 0 undefined refs, plain red highlights — post-session-26 regen; SHA-256 ed09349d...02d67)
    ├── sn-bibliography.bib  sn-jnl.cls  sn-mathphys-num.bst

(note: a `_camera_ready_2026-05-26/` package was built at session-26 close
 then deleted post-close as redundant — main/sn-article.pdf IS the submission
 file; SHA-256 above is authoritative provenance. See SESSION_26_HANDOFF.md §11.)
```

**Recompile main**:
```powershell
$pdflatex = 'C:\Users\partha\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe'
$bibtex   = 'C:\Users\partha\AppData\Local\Programs\MiKTeX\miktex\bin\x64\bibtex.exe'
Set-Location "...sandbox-session16\main"
& $pdflatex sn-article.tex; & $bibtex sn-article; & $pdflatex sn-article.tex; & $pdflatex sn-article.tex
```

**Recompile DIFF**: same chain with `sn-article-DIFF` substituted, run from `diff/` directory.

**Regenerate DIFF from scratch** (compare v1 → current sandbox):
```powershell
$latexdiff = 'C:\Users\partha\AppData\Local\Programs\MiKTeX\miktex\bin\x64\latexdiff-fast.exe'
$v1Tex = "C:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\Final Submission Paper (Accepted v.1)\1ST SUBMISSION\sn-article-template\sn-article.tex"
Set-Location "...sandbox-session16\diff"
& $latexdiff --type=INVISIBLE --graphics-markup=none --no-del `
  --exclude-textcmd="emph,textbf,textit,texttt" `
  $v1Tex sn-article.tex > sn-article-DIFF-RAW.tex
# Then manually apply red text override at the \DIFadd line — see §13 gotcha #7
```

---

## 6. Benchmark Datasets

| File | Location | Cases | Purpose | Status |
|------|----------|-------|---------|--------|
| `benchmark_431_seed42.json` | `benchmark/intermediate/datasets/` | 431 | Main + ablation + SOTA | ✅ Frozen (post-D-1 re-label) |

**Post-D-1 dataset composition** (after re-labeling 33 OpsEval-remined `rca` → `qa_mcq`):
- 218 annotation cases
- 180 RCA cases
- 33 qa_mcq cases (routed through 14B for RCA-style scoring)

**Excluded RCA**: 74 cases (41 Chinese-language + 33 OpsEval-remined MCQ). List in `benchmark/intermediate/datasets/excluded_rca_cases.json`.

---

## 7. Current Benchmark Results (authoritative, post-D-1 + BERT-F1 recompute)

### Phase 4.2 Main Re-run (Stack A, matched eval)

| Metric | Value | BERTScore F1 |
|--------|-------|-------------|
| **Overall** | **82.4% (294/357)** | **0.8124** |
| Annotation | 82.6% (180/218) | 0.822 |
| RCA | 82.0% (114/139) | 0.795 |

Source: `benchmark/final/main_benchmark/results.json` + `phase5_stats.json`.

### Phase 4.3 Ablation (8 configs, matched eval — post-D-1)

| Configuration | Ann (218) | RCA (139) | Overall (357) | Δ Overall | McNemar p (overall) |
|---|---|---|---|---|---|
| **Full Hybrid** | **83.0%** | **85.6%** | **84.0%** | — | — |
| Single-4B | 82.6% | 82.7% | 82.6% | −1.4pp | 0.302 |
| Single-14B | 84.4% | 82.7% | 83.8% | −0.3pp | 1.000 |
| No structured output | 82.6% | 75.5% | 79.8% | −4.2pp | 0.086 |
| **No system prompt** | **48.6%** | 81.3% | 61.3% | **−22.7pp** | **3.40e-11** |
| With Graph | 82.6% | 83.5% | 82.9% | −1.1pp | **0.289 (NS)** |
| No constitutional | 89.4% | 72.7% | 82.9% | −1.1pp | 0.652 |
| With orchestrator | 82.6% | 83.5% | 82.9% | −1.1pp | 0.289 |

Source: `benchmark/final/ablation_v4/ablation_*/results_sota_eval_431.json` + `phase5_stats.md`. (Cells re-synced 2026-05-26 session 23 — prior version had 5-row drift on Single-4B, Single-14B, No-system-prompt, No-constitutional, and Full Hybrid Ann.)

### Phase 4.7 SOTA Baselines (Bedrock)

| System | Ann | RCA | Overall | Source file |
|---|---|---|---|---|
| **Ours (Full Hybrid)** | 82.6% (180/218) | **82.0% (114/139)** | 82.4% (294/357) | `main_benchmark/results.json` |
| Llama 3.3-70B | 91.3% | 71.2% (99/139) | 83.5% | `sota_baselines/llama_3_3_70b.jsonl` |
| DeepSeek V3.2 | 90.4% | 66.9% (93/139) | 81.2% | `sota_baselines/deepseek_v3.jsonl` |

**ΔRCA Ours vs Llama: +10.8pp.** **ΔRCA Ours vs DeepSeek: +15.1pp.**

Headline novelty: 14B+4B hybrid with constitutional gating beats 70B Llama (+10.8pp) and DeepSeek V3.2 (+15.1pp) on RCA. Drain (LogPAI) included as non-LLM baseline.

### Gate §15 Smoke Comparison (Stack A vs B, 30 cases each)

| Stack | Accuracy | Avg lat | P95 |
|-------|----------|---------|-----|
| Stack A (Ollama Q4_K_M) | 93.3% | 22.43s | **65.96s** |
| Stack B (vLLM AWQ awq_marlin) | 100.0% | 17.38s | **43.71s** |

Gate 2 P95 speedup = 1.51× → reframes R1/R3 latency concern as serving-stack artifact (Ollama Q4_K_M → vLLM AWQ).

### Phase 4.5 Graph Sub-experiment — PATH 4 outcome (locked session 20)

- **4.5a heterogeneous steady-state**: Δ=−1.1pp (within noise, McNemar p=0.289)
- **4.5b homogeneous LEMMA 5-fold**: **CEILING** — no-graph = with-graph = 100% on all 5 folds (cases too easy after model + constitutional gating)
- **4.5c cold-start curve**: NEVER RAN — D-17 dataclass JSON serialization bug crashed the post-processing step

**Paper disclosure** (sandbox §6.2 Limitations + §6.3 Future Work): graph memory's architectural value rests on heterogeneous-distribution result; homogeneous-easy regime saturated; cold-start curve left for future work.

Source: `benchmark/final/phase45_graph/` (4 scp'd files + `_failed_run_log.txt`).

---

## 8. Next Actions (Priority Order)

### Action 1 — Gate 1: 7 themed local commits (LAPTOP, requires USER GO)

Per `benchmark/final/audit/SESSION_20_HANDOFF.md` §6.1 (commit #6 updated for session-21+22 polish):

1. `data(D-1): re-label 33 OpsEval-remined cases as qa_mcq + sync 16 result files + Phase 5 recompute`
2. `docs: update SUMMARY/METHODOLOGY/MANIFEST/BUG_HISTORY/AUDIT_REPORT for post-D-1 + D-2/D-3/D-5/Conflict-5 disclosures`
3. `fix(benchmark/scripts): D-7 test_5plus5 ref + D-14 path fallback + D-16 dataclass attr + D-17 dataclass file-write`
4. `eval(D-6): BERT-F1 recompute via roberta-large on CUDA + recompute_bert_f1.py + SUMMARY.md §3.5 + BUG_HISTORY.md D-6 -> RESOLVED`
5. `data(4.5): Phase 4.5 LEMMA-CV results (PATH 4 ceiling outcome) + D-17 forensic log + BUG_HISTORY.md D-17 + SUMMARY.md §3.6 + §6 AWS refresh`
6. `paper(sandbox-session16): Decisions 1/3/4 + Fig 3 v1 dims + Fig 3 source move + Fig 3 callout fixes + 84% baseline horizontal + interpretive sentence + placeins/FloatBarrier + 3 bib drops + Table 4 v1 layout + tab:graphsub dropped + folder reorg main+diff + DIFF PDF generation`
7. `docs(audit): SESSION_19/20/21_HANDOFF close-outs + HANDOFF.md relocation to benchmark/ + root file housekeeping (sort into _session11_phase4_orphans/, _session12_reorg_intermediates/, _dev/)`

**Rules**:
- NO Claude trailer (NEVER `Co-Authored-By: Claude ...`)
- HEREDOC for multi-line commit messages
- Apply one at a time; halt for confirmation between batches if user prefers

### Action 2 — Gate 3: Push origin/main (LAPTOP, requires SEPARATE USER GO)

After all 7 commits land locally, HALT and ASK. Then:
```bash
git push origin main
```

### Action 3 — Optional Phase 4.5c cold-start re-run (INSTANCE, only if reviewer demands)

- Pre-flight: scp updated `src/memory/neo4j_client.py` to instance (instance is missing `find_similar_episodes_by_embedding`)
- Pre-flight: D-16 + D-17 dataclass patches already on laptop; scp `benchmark/scripts/run/run_graph_experiments.py` to instance
- Start instance, run on 20 held-out LEMMA cases at N=0/20/40/60 episodes
- Cost: ~$5, ~5h wallclock
- Output: Fig 5 cold-start curve for NEW Table 9 row

### Action 4 — Optional Stack B full 431-case latency re-run (INSTANCE)

Currently Stack B latency numbers are from 15+15 smoke. Full 431 run would tighten Table 5 numbers but isn't strictly needed for review defense.

---

## 9. Sandbox Paper Changes Applied (sessions 16-22 cumulative)

### Tables refreshed
- **Table 1** (Datasets): updated source breakdown post-D-1
- **Table 2** (Overall Results): post-D-1 numbers + BCa CIs + BERT-F1 column
- **Table 3** (Per-Source): post-D-1 + Apache + OpenSSH rows
- **Table 4** (Latency): **v1 component×metrics layout** (Decision 1, session 21) — n=431 (218+180+33), RTT-compensated, 0 `---` cells
- **Table 5** (Ablation 6a): architecture/orchestration variants
- **Table 6** (Ablation 6b): component ablations + interpretive footnote
- **Table 7** (SOTA): Llama 3.3-70B + DeepSeek V3.2 + Drain, separate Ann/RCA/Overall

### Figures
- **Fig 3** (Ablation bar chart): v1 dims (`height=8.5cm`, `bar=6pt`), `xmin=30`, `xtick={30,50,70,90}`. Callout `−34pp drop!` at `(axis cs:101, 1.4) anchor=east` with `\scriptsize\bfseries`, diagonal red arrow to `(axis cs:49, 1.05)`. 84% baseline label horizontal `\scriptsize` gray upper-right (via `\coordinate (chartUR) at (rel axis cs:1,1)` defined INSIDE axis then referenced OUTSIDE).

### Sections rewritten
- §3.5 Evaluation Methodology (matched-substring eval; 3-point rubric kept as INTENTIONAL DISCLOSURE, lines 447 + 597)
- §4 Dataset Curation (post-D-1 counts: 218 ann + 180 rca + 33 qa_mcq)
- §5.5 Performance + Resource (latency paragraph reframe)
- §5.6 Ablation (interpretive sentence after Table 6 — task-specific prompt sensitivity framing)
- §5.7 SOTA (3 baselines)
- §5.8 **DROPPED** (Decision 4) — content absorbed into §6.2 Limitations + §6.3 Future Work
- §6.1 Research Gap Validation (4 concerns defused)
- §6.2 Limitations (absorbed §5.8 graph sub-experiment + matched-eval disclosure)
- §6.3 Future Work (trimmed parenthetical)

### Bibliography
- **31 cited entries** (was 34 pre-session-21; dropped `adaspec2025`, `edge2024graphrag`, `zhang2020effect` from cite groups to keep 16p)
- 12 new entries added per plan §6.4 (AIOpsLab, OpenRCA, Flow-of-Action, LogEval, AIOps Survey 2025, Miller et al. CLT, etc.)

---

## 10. Critical Files Modified (current uncommitted state — 45 files in working tree)

### Code patches
- `benchmark/scripts/run/run_graph_experiments.py` — D-13 + D-14 + D-16 + D-17 (4 patches across sessions 16/17/20)

### BERT-F1 recompute (session 18, D-6)
- `benchmark/scripts/eval/recompute_bert_f1.py` (new)
- 14 result files with `bert_f1` populated in place
- `benchmark/final/_bert_f1_recompute_summary.json`, `_bert_recompute.log`

### Phase 4.5 forensic (session 20)
- `benchmark/final/phase45_graph/exp_4_5b_summary.json` (757 B valid)
- `benchmark/final/phase45_graph/exp_4_5b_*.jsonl` (0 B — D-17 loss)
- `benchmark/final/phase45_graph/exp_4_5c_summary.json` (stale session-17)
- `benchmark/final/phase45_graph/_failed_run_log.txt` (full crash trace + per-fold progress)

### Docs (sessions 17-21)
- `benchmark/final/SUMMARY.md` (post-D-1 + §3.5 BERT + §3.6 Phase 4.5 + §6 AWS refresh)
- `benchmark/final/docs/BUG_HISTORY.md` (#1-9 + D-6 + D-17 + footnotes)
- `benchmark/final/docs/METHODOLOGY.md` (post-D-1 disclosures)
- `benchmark/final/MANIFEST.md`, `AUDIT_REPORT.md` (refreshed)

### Sandbox paper (sessions 17, 18, 21, 22)
- `PAPER AND FORMAL DOCUMENTATION/.../sandbox-session16/main/sn-article.tex` + `.pdf` (16p)
- `.../sandbox-session16/diff/sn-article-DIFF.tex` + `.pdf` (16p, NEW session 22)

### Session handoffs (4 new audit docs)
- `benchmark/final/audit/SESSION_19_HANDOFF.md`
- `benchmark/final/audit/SESSION_20_HANDOFF.md`
- `benchmark/final/audit/SESSION_21_HANDOFF.md`
- `benchmark/HANDOFF.md` ← THIS FILE (moved from `constitutional-aiops/HANDOFF.md` session 22)

### Sorted-from-root files (session 22 housekeeping)
- `benchmark/final/audit/_session11_phase4_orphans/phase4_assist.txt` + `phase4_cmds.txt` (mangled-name temp orphans from session 11 transcript audit Phase 4)
- `benchmark/final/audit/_session12_reorg_intermediates/_index_*.txt` (5 files — session 12 directory walks + change lists, info captured in `MASTER_BACKUP_MANIFEST_2026-05-20.json`)
- `benchmark/scripts/_dev/_session21_latency_pcts.py` + `_session21_latency_e2e_no_qa.py` (Table 4 P50/P95/P99 computation helpers, results landed in sandbox Table 4)

---

## 11. Key Decisions Made (Do Not Re-Litigate)

### Dual-Stack Architecture (locked 2026-05-12)
Stack A (Ollama, port 11434) = accuracy source of truth for Tables 2/3/4/6/8/9.
Stack B (vLLM, ports 8000/8001) = latency source of truth for Table 5.
Same hardware (L4 24 GB), sequential GPU usage.

### Graph Memory FIXED + Re-tested (sessions 14, 20)
v1 paper had fake hardcoded context (`_build_sample_graph_context()` with invented incidents). Real Neo4j retrieval (`find_similar_episodes_by_embedding`) shipped session 14. Phase 4.5 results show graph value rests on heterogeneous distributions, not homogeneous-easy (which saturates at ceiling).

### D-1 OpsEval-remined re-label (locked session 17)
33 cases re-labeled `rca` → `qa_mcq`. Numbers shifted up ~1.5-1.8pp on RCA (favorable). NO AWS re-run needed. Local re-compute done session 17.

### 3-point rubric mentions (intentional disclosures, locked session 17)
2 mentions remain in sandbox at line 447 (§5.1 Evaluation Methodology) + line 597 (Table 6 footnote). Documents the v1→v2 methodology change for reviewer transparency. **Do NOT remove without explicit user ask.**

### Gate 2 Rsync PERMANENTLY DROPPED (locked 2026-05-26 session 20)
sandbox-session16 IS the final draft location. Do NOT rsync to old `sn-article-template.v2/` (now moved to `z.Dump Paper Archive\` by user housekeeping).

### Sandbox folder layout (locked 2026-05-26 session 22)
Sandbox now contains `main/` + `diff/` subfolders, each mirroring v1's flat layout. Active edit target: `main/sn-article.tex`.

### Budget
Ceiling $120 (raised from $75 on 2026-05-12 to fund dual-stack). Spent ~$55 (~46%). Frozen at ~$5/mo passive while stopped.

---

## 12. Memory Files

All memory at: `C:\Users\partha\.claude\projects\c--Users-partha-Downloads-files-AIOPS-NEW\memory\`

| File | Content |
|------|---------|
| `MEMORY.md` | Index + SESSION 23 STARTUP block (auto-loaded each session) |
| `project_paper_sandbox_active.md` | Active paper path discipline (post-session-22 reorg) |
| `project_aiops_next.md` | Pre-revision baseline (mostly superseded) |
| `project_aiops_state.md` | Historical project state (pre-revision Session 7) |
| `project_dualstack_decision.md` | Why dual-stack, budget ceiling |
| `project_thinking_mode_audit_logging.md` | Ollama thinking mode + reasoning capture policy |
| `project_vram_tuning_l4.md` | 5 VRAM tuning attempts, final 4B AWQ + 14B FP8 config |
| `feedback_git_filter_repo_lessons.md` | filter-repo deletes working tree — caution |
| `feedback_no_shortcuts_read_sources.md` | Always re-read primary artifacts |
| `user_profile.md` | [redacted] profile |

---

## 13. Known Issues and Gotchas

1. **Instance has NO git** — always `scp` files directly, NEVER `git pull` on instance.
2. **Instance `src/` is OUTDATED** — `Neo4jClient.find_similar_episodes_by_embedding` exists on laptop but NOT on instance (instance last updated session 9-10). Any 4.5b/4.5c re-run requires scp `src/memory/` first.
3. **D-16 / D-17 dataclass bugs** in `run_graph_experiments.py`: D-16 (attribute access on dataclass instance) patched session 17. D-17 (JSON serialization of dataclass) patched session 20. Both patched on laptop; instance script needs scp before any re-launch.
4. **Stack A and Stack B share same GPU** — never run simultaneously; stop Ollama before starting vLLM.
5. **OpenSSH 50% accuracy** is NOT a bug — all 20 failures are FPs on isolated auth events; 0 false negatives on real brute-force. Discussed in sandbox §5.3 caveat per Decision 2 (session 17).
6. **`enable_thinking=False` is ignored by Ollama 0.23.2** — thinking happens anyway. Reasoning lands in `message.reasoning`, JSON in `message.content`. v1 paper numbers were produced this way; current behavior matches v1 exactly. See `project_thinking_mode_audit_logging.md`.
7. **DIFF PDF override** — `\hl{}` from soul breaks on `\cite{}` inside additions; `\textbf{}` widens text and pushes DIFF to 17 pages (loses parity with main). Use `\textcolor{red!75!black}{#1}` for `\DIFadd` override (session 22 finding). Override block lives at `diff/sn-article-DIFF.tex` around line 102-108.
8. **AWS Budget Action triggers**: $5/day cap auto-stops instance at 100%. Be mindful when starting instance after long pauses; verify SG ingress for current laptop IP first.
9. **PowerShell `>` redirect produces UTF-16 LE w/ BOM** — pdflatex can't read it. When writing `.tex` files from PowerShell, use `[System.IO.File]::WriteAllText` with `New-Object System.Text.UTF8Encoding $false`.
10. **PowerShell `:` parsing in filenames** — paths containing colons (e.g., mangled temp-redirect names) require bash `mv`, not PowerShell `Move-Item` (the colon is interpreted as drive separator even when quoted).

---

## 14. Phase Completion Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Safety net, tagging, backups | ✅ Complete |
| 1 | Code hardening (JSONL resume, CIs, golden tests) | ✅ Complete |
| 2 | Dataset expansion to 431 + D-1 re-label | ✅ Complete (post-D-1) |
| 3 | AWS infrastructure (g6.xlarge, Ollama + vLLM) | ✅ Complete |
| 4.0 | Smoke gate + dual-stack verification | ✅ Complete (Gate 1+2 PASS) |
| 4.1 | LangGraph orchestrator wired | ✅ Complete |
| 4.2 | Main benchmark 431 cases (Stack A, matched eval) | ✅ Complete (Overall 82.4%, RCA 82.0%, Ann 82.6%) |
| 4.3 | 8-config ablation 431 cases | ✅ Complete (`benchmark/final/ablation_v4/`) |
| 4.4 | Populate Neo4j with real episodes | ✅ Complete (431 episodes) |
| 4.5 | Graph sub-experiments | ✅ Complete (PATH 4 — heterogeneous Δ=−1.1pp NS; LEMMA-CV ceiling; 4.5c left for future work) |
| 4.6 | No-prompt cross-model (Llama, DeepSeek) | ✅ Complete (`benchmark/final/phase46_no_prompt/`) |
| 4.7 | SOTA baselines (Bedrock) | ✅ Complete (Llama 3.3-70B + DeepSeek V3.2 + Drain) |
| 5 | Statistical analysis (BCa CIs, McNemar, Cohen's h) | ✅ Complete (post-D-1 recompute) |
| 6 | Paper update (Tables 1-7, paragraphs, refs, Fig 3) | ✅ Complete (sessions 18-21 — sandbox `main/`) + DIFF PDF (session 22) |
| 7 | Final commit + release | ⏳ Gate 1 (7 themed commits) + Gate 3 (push) PENDING USER GO |

---

## 15. Useful One-Liners

```powershell
# Check instance state:
aws ec2 describe-instances --profile aiops-operator --region us-east-1 `
  --instance-ids i-091c4de0e95d63154 `
  --query 'Reservations[0].Instances[0].State.Name' --output text

# Sandbox PDF info:
& 'C:\Users\partha\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdfinfo.exe' `
  "C:\Users\partha\Downloads\files AIOPS NEW\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\main\sn-article.pdf"

# Quick accuracy check on results.json:
python3 -c "
import json
with open('benchmark/final/main_benchmark/results.json') as f:
    results = json.load(f)
total = len(results)
correct = sum(1 for r in results if r.get('correct'))
print(f'{correct}/{total} = {correct/total*100:.1f}%')
"

# Sync results from instance (if instance is running):
bash aws/sync_results.sh

# Stop instance (preserves EBS — DO NOT terminate):
aws ec2 stop-instances --profile aiops-operator --region us-east-1 --instance-ids i-091c4de0e95d63154
```

---

## 16. Session History Quick Reference

| Session | Date | Outcome |
|---------|------|---------|
| 1-10 | 2026-05-11 → 17 | Phase 0-3, Phase 4.2 main, Phase 4.7 SOTA, ablation v3-v4 |
| 11 | 2026-05-19 | Eval pathology audit, matched-eval rescoring, FINAL/ build |
| 12 | 2026-05-20 | Reorg Stages A-D (filesystem cleanup), backup zip, CV passes |
| 13-15 | 2026-05-20 → 24 | Reorg Stages E-J (path retrofits + scripts subfolder), paper sandbox creation |
| 16 | 2026-05-25 | Paper sandbox-session16 created (top-half revert, §6.1 reframe, bib hygiene) |
| 17 | 2026-05-25 | Deep audit-triage; D-1 through D-17 locked; Phase 4.5 launch attempts (3 crashes) |
| 18 | 2026-05-26 | D-1 dataset re-label + Phase 5 recompute + D-6 BERT-F1 recompute + sandbox §5.x edits |
| 19 | 2026-05-26 | Phase 4.5 launch on AWS (instance up, tmux launch, hibernation handoff) |
| 20 | 2026-05-26 | Phase 4.5 PATH 4 outcome + D-17 patch + Phase B sandbox edits begin |
| 21 | 2026-05-26 | 5 session-20 Decisions applied + Fig 3 polish (subagent ×2) + 84% baseline horizontal |
| 22 | 2026-05-26 | DIFF PDF complete (red text, 16p, refs resolved) + sandbox reorg main/diff + root file housekeeping + HANDOFF.md relocation/rewrite |

---

*Last updated: 2026-05-26 session 22 close. Document moved from `constitutional-aiops/HANDOFF.md` to `constitutional-aiops/benchmark/HANDOFF.md` in session 22 housekeeping. Next session = 23.*
