# Session 18 → Session 19 Handoff (2026-05-26)

> ## ⚠⚠⚠ SESSION 19 STARTUP — READ EVERY MANDATORY FILE BELOW IN FULL, NO SHORTCUTS
>
> Session 18 (2026-05-26, ~3h elapsed): completed **all of Phase A** (D-1 dataset re-label + 16 result-file sync + Phase 5 stats recompute + 5 doc files + 6 Tier 2 mechanicals patched), kicked off **D-6 BERT-F1 recompute in background** (running at compact time), and **STARTED but did NOT apply** Phase B (sandbox paper edits — only investigation/reading was done). Phase C (AWS Phase 4.5) **not yet launched**. Phase D **deferred**.
>
> **NEW USER DIRECTIVE for session 19 (2026-05-26)**:
> 1. **Start session 19 with Phase C FIRST** — kick off AWS Phase 4.5 launch (the long-running ~5h experiment).
> 2. **Wait for AWS Phase 4.5 to FINISH before doing Phase B paper edits** — because sandbox Table 6 (`tab:graphsub`) has [TBD] cells (rows 4.5b + 4.5c) that need real Phase 4.5 numbers. User explicitly said: *"need to run the aws test too and let it finish before phase C edits"*.
> 3. Phase B sandbox paper edits (Tables 2/6a/6b/7 + new sentences for D-1/D-2/D-3/Conflict-4/B-4 + variance footnotes + Table 6 TBD fills + BERT-F1 integration) all happen AFTER Phase C completes.
>
> **PRIMARY ENTRY POINTS** (read in this order):
> 1. This file (`SESSION_18_HANDOFF.md`) — START HERE
> 2. `SESSION_17_HANDOFF.md` — still valid for Phase C path options + locked decisions
> 3. `SESSION_17_AUDIT_TRIAGE.md` — locked decisions per audit item
> 4. `SESSION_17_RECALC_SCOPE.md` — exact file-by-file recalc plan with before/after numbers
>
> ---

## §0. One-paragraph state summary

Phase A is **DONE**. 29 files modified in the working tree (1 dataset + 16 result files + 4 stats files + 5 doc files + 3 scripts + 2 audit docs + 1 HANDOFF.md). D-6 BERT-F1 recompute is **running in background** at compact time (task id `bq32h5vqv`, 5/14 files done at log offset 99, total ETA ~9 min remaining from compact). Phase B (sandbox paper edits) is **NOT yet applied** — only investigation reads of the sandbox tex were done. Phase C (AWS Phase 4.5) is **the first action for session 19** per new user directive. Phase D (commits + rsync + push) is deferred to end. Sandbox paper UNCHANGED (16p, ModDate 2026-05-25 11:05). Real paper UNCHANGED (17p, ModDate 2026-05-24 21:24). AWS instance `i-091c4de0e95d63154` is **stopped**.

---

## §1. Mandatory reads for session 19 (in order, no skipping)

| # | File | Purpose | Why critical |
|---|---|---|---|
| 1 | `C:\Users\partha\.claude\projects\c--Users-partha-Downloads-files-AIOPS-NEW\memory\MEMORY.md` | auto-loaded; SESSION 19 STARTUP block | session-19 entry point |
| 2 | **`benchmark/final/audit/SESSION_18_HANDOFF.md`** (THIS FILE) | what happened in session 18 + Phase C-first execution plan | mandatory primary |
| 3 | **`benchmark/final/audit/SESSION_17_HANDOFF.md`** ⭐ | Phase C path-forward options (§3 PATH 1/2/3/4) + Phase 4.5 status | needed for Phase C decision |
| 4 | **`benchmark/final/audit/SESSION_17_AUDIT_TRIAGE.md`** | per-item locked decisions with USER DECISION lines | needed for Phase B sentence content |
| 5 | **`benchmark/final/audit/SESSION_17_RECALC_SCOPE.md`** | file-by-file recalc plan, before/after numbers (Phase A reference) | most of these now reflected in current state |
| 6 | `benchmark/final/audit/SESSION_16_AUDIT_LOST_CHECKLIST.md` | origin of D-items (some now resolved this session) | reference |
| 7 | `benchmark/final/SUMMARY.md` | **POST-D-1 numbers** — main re-run Ann 82.6 / RCA 82.0 / Overall 82.4 | source-of-truth for Phase B Table 2 numbers |
| 8 | `benchmark/final/ablation_v4/phase5_stats.md` | **POST-D-1 ablation table** — Full Hybrid RCA 85.6% etc | source-of-truth for Phase B Tables 6a/6b numbers |
| 9 | `benchmark/final/ablation_v4/matched_eval_table.md` | compact overall-only ablation (manually refreshed) | reference |
| 10 | `benchmark/final/docs/METHODOLOGY.md` | post-D-1 dataset/exclusions/composition (74 excluded, 139 evaluable) | reference for paper §3/§4 |
| 11 | `benchmark/final/docs/BUG_HISTORY.md` | new D-1/D-4/D-6 footnotes section | reference |
| 12 | `benchmark/final/MANIFEST.md` | "Post-D-1 state" appended section with new SHA-256s | reference |
| 13 | `benchmark/final/AUDIT_REPORT.md` | Post-D-1 note at top with current counts | reference |
| 14 | `benchmark/final/_bert_f1_recompute_summary.json` | **NEW** — BERT-F1 averages per file after background run completes | needed for Phase B BERT-F1 integration |
| 15 | Sandbox paper `.tex`: `PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2.sandbox-session16/sn-article.tex` (670 lines, 16-page PDF) | edit target for Phase B | primary Phase B target |
| 16 | Sandbox paper `.bib`: same dir, 278 lines, 36 entries | bib reference | reference |
| 17 | v1 reference (sealed): `Final Submission Paper (Accepted v.1)/.../sn-article.tex` | DO NOT modify | sealed |
| 18 | `benchmark/scripts/run/run_graph_experiments.py` | **PATCHED** session 18 (D-14 fallback + D-16 dataclass × 6 instances) | ready to run Phase 4.5 |
| 19 | `src/memory/neo4j_client.py` line 747 (`find_similar_episodes_by_embedding`) | **MUST SCP to instance** before Phase 4.5 launch | Phase C blocker |
| 20 | `src/benchmark/runner.py` line 848 (calls `find_similar_episodes_by_embedding`) | **MUST SCP to instance** before Phase 4.5 launch | Phase C blocker |
| 21 | All non-MEMORY memory files (project_aiops_state/next, project_dualstack_decision, project_thinking_mode_audit_logging, project_vram_tuning_l4, project_paper_sandbox_active, user_profile, feedback_*) | hard rules + history | reference |
| 22 | Sealed forensic (FULL_TRANSCRIPT_AUDIT, CV_PASS1/2, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, prior SESSION_12/13/14/15/16 handoffs) | do NOT modify | sealed |

---

## §2. What changed on disk in session 18

### Modified (committed-tracked, NOT yet committed)
- `benchmark/intermediate/datasets/benchmark_431_seed42.json` — 33 cases task_type `rca`→`qa_mcq` + `excluded_reason` field. SHA `d1a8f79f...`.
- 16 result files (all 33 OpsEval-remined records per file → `task_type: qa_mcq` + `excluded_reason`):
  - `benchmark/final/main_benchmark/results.json`
  - `benchmark/final/main_benchmark/results_sota_eval_431.json`
  - 8 `benchmark/final/ablation_v4/ablation_*/results_sota_eval_431.json`
  - `benchmark/final/sota_baselines/llama_3_3_70b.jsonl`
  - `benchmark/final/sota_baselines/deepseek_v3.jsonl`
  - `benchmark/final/sota_baselines/drain.jsonl` (no-op — 0 remined records)
  - `benchmark/final/phase46_no_prompt/llama_noprompt_clean.jsonl`
  - `benchmark/final/phase46_no_prompt/deepseek_noprompt_v2.jsonl`
- 4 stats outputs (auto-regenerated):
  - `benchmark/final/main_benchmark/phase5_stats.json`
  - `benchmark/final/ablation_v4/phase5_stats.json`
  - `benchmark/final/ablation_v4/phase5_stats.md`
  - `benchmark/final/ablation_v4/matched_eval_table.md` (hand-refreshed)
- 5 doc files updated (D-1/D-2/D-4/D-5/D-6/Conflict-5 disclosures + post-D-1 numbers):
  - `benchmark/final/SUMMARY.md`
  - `benchmark/final/MANIFEST.md` (appended "Post-D-1 state" section)
  - `benchmark/final/AUDIT_REPORT.md` (Post-D-1 note at top)
  - `benchmark/final/docs/METHODOLOGY.md` (§1 dataset, §2 exclusion + D-1 paragraph, §6 composition, §7 prompt-revision impact)
  - `benchmark/final/docs/BUG_HISTORY.md` (D-1/D-4/D-6 footnotes section + OpenSSH "validated" note)
- 1 audit doc updated: `benchmark/final/audit/SESSION_16_AUDIT_LOST_CHECKLIST.md` — D-12 marked MOOT
- 1 HANDOFF.md updated: `HANDOFF.md` lines 465 + 583 (D-8 strike) + §14 table reconcile (D-9 + Conflict-1/2/3)
- 3 scripts modified:
  - `benchmark/scripts/eval/phase5_stats.py` — lines 307-309 hardcoded text updated for new exclusion counts
  - `benchmark/scripts/run/run_graph_experiments.py` — D-14 backward-compat path fallback + D-16 dataclass attribute fix (6 instances `r.get("correct")` → `r.correct`)
  - `benchmark/scripts/run/test_5plus5.py` — D-7 docstring dataset reference

### Untracked (in working tree, NOT staged for commit)
- 3 NEW audit docs at `benchmark/final/audit/`:
  - `SESSION_17_AUDIT_TRIAGE.md` (~500 lines — created session 17)
  - `SESSION_17_HANDOFF.md` (~284 lines — created session 17)
  - `SESSION_17_RECALC_SCOPE.md` (~250 lines — created session 17)
  - **`SESSION_18_HANDOFF.md`** (THIS FILE) — created session 18
- 1 BERT recompute summary: `benchmark/final/_bert_f1_recompute_summary.json` — populated by background run
- 1 BERT recompute log: `benchmark/final/_bert_recompute.log` — `tee`'d output of background run
- 1 NEW eval script: `benchmark/scripts/eval/recompute_bert_f1.py` — D-6 implementation
- 6 helper scripts (session-18 internal use, can stay or be deleted):
  - `benchmark/scripts/_apply_d1_result_sync.py`
  - `benchmark/scripts/_verify_a2_apply.py`
  - `benchmark/scripts/_verify_d1_relabel.py`
  - `benchmark/scripts/_probe_format.py`
  - `benchmark/scripts/_probe_format2.py`
  - `benchmark/scripts/_compute_sota_post_relabel.py`

### Git state (UNCHANGED commits)
- Local HEAD: `57035cf` (D-13 patch from session 16)
- Origin: `a5e9005` (2 commits behind — `57035cf` + `ee8f125` not pushed)
- No new commits made this session (per "no commits without GO" rule)

### Paper state (UNCHANGED)
- Sandbox: `sn-article-template.v2.sandbox-session16/sn-article.pdf` — 16 pages, ModDate 2026-05-25 11:05:57
- Real: `sn-article-template.v2/sn-article.pdf` — 17 pages, ModDate 2026-05-24 21:24:32

### AWS state (UNCHANGED)
- Instance `i-091c4de0e95d63154`: stopped
- EIP `44.195.172.165`: retained
- EBS snapshot `snap-01b191aedbf46b598`: held
- Budget: ~$48/$120 (~40%)
- Phase 4.5 partial-results from session 17 still on EBS: `/mnt/aiops-repo/runs/2026-05-25T10-18-31_bench_constitutional_aiops/results.jsonl` (16 records)

---

## §3. D-6 BERT-F1 background run — ✅ COMPLETED before compact

**Task ID**: `bq32h5vqv` (background process — completed with exit 0 at ~2026-05-26 01:55 IST)
**Log file**: `C:\Users\partha\AppData\Local\Temp\claude\c--Users-partha-Downloads-files-AIOPS-NEW\f63e3e73-b5a5-476e-9373-0ee35d7c1476\tasks\bq32h5vqv.output`
**Tee'd output**: `benchmark/final/_bert_recompute.log` (local persistent log)
**Summary output**: `benchmark/final/_bert_f1_recompute_summary.json` (14 files processed, all written)

### Final BERT-F1 numbers (model: roberta-large on CUDA)

| File | mean F1 | Ann F1 (n) | RCA F1 (n) | Written |
|---|---:|---|---|---|
| main_benchmark/results_sota_eval_431.json | 0.8124 | 0.8220 (218) | 0.7954 (122) | ✅ |
| main_benchmark/results.json (rich) | 0.8124 | 0.8220 (218) | 0.7954 (122) | ✅ |
| ablation_full | 0.8126 | 0.8222 (218) | 0.7951 (122) | ✅ |
| ablation_single_4b | 0.8126 | 0.8222 (218) | 0.7951 (122) | ✅ |
| ablation_single_14b | 0.8176 | 0.8220 (218) | 0.8074 (122) | ✅ |
| ablation_no_structured | 0.8083 | 0.8160 (217) | 0.7936 (122) | ✅ |
| ablation_no_system_prompt | 0.8377 | 0.7936 (**1** — short outputs filtered) | 0.8260 (122) | ✅ |
| ablation_with_graph | 0.8102 | 0.0000 (**0** — short outputs filtered) | 0.8047 (122) | ✅ |
| ablation_no_constitutional | 0.8116 | 0.8220 (218) | 0.7941 (122) | ✅ |
| ablation_with_orchestrator | 0.8238 | 0.8257 (218) | 0.8149 (122) | ✅ |
| sota_baselines/llama_3_3_70b.jsonl | 0.8269 | 0.8236 (218) | 0.8321 (102) | ✅ |
| sota_baselines/deepseek_v3.jsonl | 0.8264 | 0.8241 (218) | 0.8301 (102) | ✅ |
| phase46_no_prompt/llama_noprompt_clean.jsonl | 0.7891 | 0.7780 (218) | 0.8111 (102) | ✅ |
| phase46_no_prompt/deepseek_noprompt_v2.jsonl | 0.7849 | 0.7727 (218) | 0.8093 (102) | ✅ |

**KNOWN ARTIFACT for session 19**: `ablation_no_system_prompt` and `ablation_with_graph` show very low annotation-pair counts (1 and 0 respectively) because their `actual_output`/`model_response` fields contain JSON-only outputs that the script's `MIN_TEXT_LEN=15` filter rejected after normalization. The RCA numbers are unaffected. For Phase B paper integration:
- Headline figure: use Main re-run + Full ablation mean F1 = **0.8124–0.8126** (Ann 0.822, RCA 0.795)
- For ablation table: report only the configs with full Ann coverage (full, single_4b, single_14b, no_structured, no_constitutional, with_orchestrator) — OR re-run with `MIN_TEXT_LEN=5` to capture more pairs (decide in session 19 based on page-budget gate)
- For SOTA table: Llama 0.8269, DeepSeek 0.8264 (both with full 218 Ann + 102 RCA coverage — these will fit cleanly in Table 7)

**Drain.jsonl SKIPPED** (excluded from FILES list in `recompute_bert_f1.py` — its predictions are boolean `predicted_anomaly`, not free text; BERTScore on "True"/"False" pairs is meaningless).

**In session 19**:
1. First action — `python -c "import json; print(json.dumps(json.load(open('benchmark/final/_bert_f1_recompute_summary.json')), indent=2))"` to inspect.
2. Decide BERT-F1 column scope (full ablation vs partial; D-6 Option B vs C — depends on PDF page budget after Phase 4.5 TBD fills).
3. The `bert_f1` field in 14 result files has been updated in place. This will show up in `git diff` for Phase D commits.

---

## §4. Phase C — execution plan for session 19 (PRIMARY DIRECTIVE)

User directive: **Start session 19 with Phase C FIRST. Wait for AWS Phase 4.5 to FINISH before doing Phase B paper edits.**

### §4.1 PATH decision (locked options from `SESSION_17_HANDOFF.md` §3.4)

| Option | Action | Cost | Time | Recommendation |
|---|---|---|---|---|
| **PATH 1** | Patch D-16 ✅ (done session 18) + SCP fresh laptop `src/memory/neo4j_client.py` + `src/benchmark/runner.py` to instance + verify smoke + re-launch | ~$5 | ~5h AWS | Fastest if no other instance drift |
| **PATH 2** | Re-clone instance from origin/main + SCP src/ + re-launch (cleanest) | ~$5 | ~6h AWS + ~1h setup | Best if you want zero "what else is outdated" surprises |
| **PATH 3** | Defer 4.5 entirely — leave [TBD] cells in sandbox Table 6 | $0 | 0 | If paper reviewer-visible [TBD] is acceptable |
| **PATH 4** | Drop 4.5b/4.5c rows from sandbox Table 6 — keep only 4.5a heterogeneous (real data 82.2%) | $0 | ~10 min | Cleanest visual; loses homogeneous-defense story |

**Recommendation for session 19**: **PATH 2** then **PATH 1**. The cleanest start eliminates "what else is outdated on instance" surprise class. If PATH 2 takes too long or hits more snags, fall back to PATH 4.

### §4.2 Pre-launch checklist (ALL must be done BEFORE starting AWS)

1. **Verify D-16 patch on laptop**: `grep "r.get(\"correct\")" benchmark/scripts/run/run_graph_experiments.py` → expect 0 matches (already patched session 18, 6 instances)
2. **Verify D-14 patch on laptop**: `grep "D-14" benchmark/scripts/run/run_graph_experiments.py` → expect 1+ match (already added session 18)
3. **Re-pull instance src/**: from instance ssh: `cd /mnt/aiops-repo && git fetch && git pull origin main` (this will get the session-16 commits but NOT yet the session-18 patches). After pull, ALSO scp the patched `run_graph_experiments.py` directly: `scp benchmark/scripts/run/run_graph_experiments.py ubuntu@<eip>:/mnt/aiops-repo/benchmark/scripts/run/`.
4. **Verify instance has `find_similar_episodes_by_embedding`**: from instance: `grep "find_similar_episodes_by_embedding" /mnt/aiops-repo/src/memory/neo4j_client.py` → must return a match. If not, SCP fresh: `scp src/memory/neo4j_client.py src/benchmark/runner.py ubuntu@<eip>:/mnt/aiops-repo/src/...`
5. **Disable CloudWatch idle-stop alarm** (Phase 4.5 has long Neo4j-writing pauses): `aws cloudwatch disable-alarm-actions --alarm-names aiops-idle-stop --profile aiops-operator --region us-east-1`. Re-enable after.
6. **Confirm Neo4j running on instance**: `ssh ubuntu@<eip> docker ps | grep aiops-neo4j`
7. **Confirm Ollama running** with qwen3:14b loaded: `ssh ubuntu@<eip> curl -s localhost:11434/api/tags`

### §4.3 Launch command (for PATH 1 or 2)

```bash
# On instance, in tmux session:
ssh ubuntu@<eip>
tmux new -s phase45
cd /mnt/aiops-repo
PYTHONIOENCODING=utf-8 python benchmark/scripts/run/run_graph_experiments.py \
  --exp all \
  --dataset /mnt/aiops-repo/benchmark/datasets/processed/benchmark_431_seed42.json \
  --out /mnt/aiops-repo/benchmark/final/phase45_graph \
  2>&1 | tee /mnt/runs/phase45_$(date -u +%Y%m%dT%H%M%SZ).log
# Detach: Ctrl+B then D
# Re-attach: tmux attach -t phase45
```

Expected runtime: ~4–5 hours. Outputs to `/mnt/aiops-repo/benchmark/final/phase45_graph/`.

### §4.4 After AWS run completes

1. **scp results back** to laptop: `scp -r ubuntu@<eip>:/mnt/aiops-repo/benchmark/final/phase45_graph ./benchmark/final/`
2. **Inspect** `benchmark/final/phase45_graph/exp_4_5b_summary.json` + `exp_4_5c_summary.json`
3. **Re-enable CloudWatch alarm**: `aws cloudwatch enable-alarm-actions --alarm-names aiops-idle-stop ...`
4. **Stop instance**: `aws ec2 stop-instances --instance-ids i-091c4de0e95d63154 ...`
5. **THEN proceed to Phase B** (paper edits including Table 6 [TBD] fill-in)

---

## §5. Phase B — sandbox paper edits (DEFERRED until Phase C completes)

This is where session 18 LEFT OFF. No edits were applied; only reads/grep were done.

### §5.1 Pre-existing investigation (done in session 18, no edits applied)

I have FULL knowledge of the sandbox `.tex` content:
- Tables that need NUMBER updates from D-1:
  - **Table 2** `tab:overall` (line ~457): Ann 82.6 stays, **RCA 80.3%→82.0% (114/139)**, **Overall 81.7%→82.4% (294/357)**. Footnote: "**71** RCA cases" → "**74** RCA cases (41 Chinese + 33 OpsEval-remined MCQ)"; the "142 evaluable" → "139 evaluable"; "Ablation Full 83.8%" → "85.6%"; numerators on the variance footnote also shift.
  - **Table 6a** `tab:ablation_arch` (line ~497): all `142` → `139`, `360` → `357`, plus accuracy % changes per `phase5_stats.md` (Full RCA 83.8→85.6, Single-4B 81.0→82.7, etc.)
  - **Table 6b** `tab:ablation_comp` (line ~524): same N shifts + accuracy % updates (No-structured RCA 73.9→75.5, No-sys-prompt 79.6→81.3, etc.)
  - **Table 7** `tab:sota` (line ~562): Ours 80.3→82.0, Llama 71.1→71.2, DeepSeek 66.9→66.9 (denominators 142→139 throughout); ΔRCA values: -9.2 → -10.8pp (Llama), -13.4 → -15.1pp (DeepSeek)
- Other prose with stale numbers:
  - Line 455: "81.7% overall accuracy (294/360 evaluable cases)" → "82.4% overall accuracy (294/357 evaluable cases)"
  - Line 460 caption: "matched-substring, 431-case bench" — same
  - Line 632 conclusion: "81.7% overall accuracy ... 360 evaluable" → "82.4% / 357"
  - Line 649 declarations: "uniformly-excluded 71-case RCA list" → "74-case RCA list (41 Chinese + 33 OpsEval-remined MCQ)"
  - Line 564 caption: "wins RCA by 9.2pp vs Llama-3.3-70B and 13.4pp vs DeepSeek-V3.2" → "by 10.8pp ... 15.1pp"

### §5.2 New sentences to ADD (per user-locked decisions from session 17)

- **D-1 disclosure** (§4 Experimentation, ~line 410-440 ish — find the right paragraph): 1 sentence: "74 RCA candidates were excluded at evaluation time (41 Chinese-language plus 33 OpsEval-remined MCQ-format cases mis-classified during curation; see audit), yielding 139 evaluable RCA cases."
- **D-2 OpenSSH caveat** (§5.3 or §6.2): 1 sentence: "On OpenSSH, the model reports 50% accuracy; all 20 errors are false positives (over-flagging single failed-login events as security incidents) with zero false negatives on the 20 brute-force attacks. This conservative bias may be desirable in production triage settings."
- **D-3 launch-date framing** (§5.7 SOTA, ~line 558-560): 1 sentence: "DeepSeek V3.2 and Llama 3.3-70B are used as closed-source and open-weight frontier baselines from the 2024-2025 release window."
- **Conflict-4 calibration** (§6.2 Limitations, ~line 619-622, end of paragraph): 1 sentence: "The confidence weight coefficients (α=0.4, β=0.35, γ=0.25) were chosen heuristically; empirical calibration on a held-out tuning set is left for future work." (Note: line 622 already mentions confidence weights but only as "theoretically motivated... require empirical calibration in production" — the Conflict-4 sentence makes this more specific. Decide whether to REPLACE or APPEND.)
- **B-4 variance footnotes** (Tables 2 + 6 — already partially exists at Table 2 footnote line 472 and Table 6 footnote line 552; just need to verify both are still accurate post-D-1 number update — same 5-case variance still holds since A_full RCA - main RCA = 119-114 = 5 cases still)

### §5.3 Table 6 [TBD] fills (DEPENDS on Phase C results)

`tab:graphsub` (line ~590) has [TBD] cells for rows 4.5b + 4.5c. Fill these with numbers from the Phase 4.5 run completed in §4 above.

### §5.4 D-6 BERT-F1 integration (depends on background completion)

After background BERT-F1 recompute completes:
- Update [SUMMARY.md](constitutional-aiops/benchmark/final/SUMMARY.md) with BERT-F1 averages per config (add to §3.3 or new sub-section)
- Update [phase5_stats.md](constitutional-aiops/benchmark/final/ablation_v4/phase5_stats.md) BERT-F1 column (or sentence summary)
- **Sandbox paper**: per D-6 Option B → add BERT-F1 column to Tables 2 + 3. If PDF > 16 pages after add → fall back to D-6 Option C (1 sentence in §5).

### §5.5 Recompile + verify

After all edits: `cd sn-article-template.v2.sandbox-session16/ && pdflatex sn-article.tex && pdflatex sn-article.tex && pdfinfo sn-article.pdf | grep Pages` → expect Pages: 16 (must NOT exceed 16).

---

## §6. Phase D — commits + rsync + push (deferred until B done)

After Phase B paper recompile succeeds at ≤16 pages:

| Step | What | Requires user GO? |
|---|---|---|
| D.1 | Stage + commit 3-4 themed local commits (no Claude trailer) | NO (local commits OK) |
| D.2 | Rsync sandbox `sn-article-template.v2.sandbox-session16/` → real `sn-article-template.v2/` | **YES** — explicit GO required |
| D.3 | Push commits to `origin/main` (3 local commits now: `57035cf`, `ee8f125` + new ones from this work) | **YES** — explicit GO required |

**Suggested commit grouping**:
1. `data(D-1): re-label 33 OpsEval-remined cases as qa_mcq + sync 16 result files + Phase 5 recompute`
2. `docs: update SUMMARY/METHODOLOGY/MANIFEST/BUG_HISTORY/AUDIT_REPORT for post-D-1 numbers + D-2/D-3/D-4/D-5/Conflict-5 disclosures`
3. `fix(benchmark/scripts): D-7 test_5plus5 ref + D-14 path fallback + D-16 dataclass attr + D-15 dict-wrap`
4. `eval: D-6 BERT-F1 recompute + new script + 14-file SHA refresh`
5. `docs(audit): SESSION_18_HANDOFF.md close-out`
6. (If Phase 4.5 ran): `data(4.5): LEMMA homogeneous 5-fold + cold-start curve results`
7. (After paper edits): `paper(sandbox→real): Tables 2/6/7 post-D-1 numbers + 4 new sentences + variance footnotes [+ BERT col]`

---

## §7. State verification commands for session 19 startup

```powershell
# Git state
cd "c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops"
git status                 # expect: 29 modified + ~11 untracked
git log --oneline -3       # expect: 57035cf, ee8f125, 2c70872

# Paper sandbox state (UNCHANGED)
pdfinfo "..\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\sn-article.pdf" | findstr /R "Pages ModDate"
# expect: Pages: 16, ModDate: Mon May 25 11:05:57 2026

# Real paper (must be UNCHANGED)
pdfinfo "..\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2\sn-article.pdf" | findstr /R "Pages ModDate"
# expect: Pages: 17, ModDate: Sun May 24 21:24:32 2026

# Confirm BERT recompute summary file exists and is non-empty
Get-Item "benchmark\final\_bert_f1_recompute_summary.json" | Select-Object Name, Length, LastWriteTime
# expect: non-empty, recent timestamp

# AWS state
aws ec2 describe-instances --instance-ids i-091c4de0e95d63154 --profile aiops-operator --region us-east-1 --query "Reservations[0].Instances[0].State.Name" --output text
# expect: stopped

# Quick verification of Phase A data sanity
python -c "import json; recs = json.load(open('benchmark/final/main_benchmark/results_sota_eval_431.json', encoding='utf-8')); ann=[r for r in recs if r['task_type']=='annotation']; rca=[r for r in recs if r['task_type']=='rca' and r.get('correct') is not None]; print(f'Ann: {sum(1 for r in ann if r[\"correct\"])}/{len(ann)}'); print(f'RCA: {sum(1 for r in rca if r[\"correct\"])}/{len(rca)}')"
# expect: Ann 180/218, RCA 114/139

python -c "import json; recs = json.load(open('benchmark/intermediate/datasets/benchmark_431_seed42.json', encoding='utf-8'))['test_cases']; from collections import Counter; print(Counter(c.get('task_type') for c in recs))"
# expect: Counter({'annotation': 218, 'rca': 180, 'qa_mcq': 33})
```

---

## §8. Hard constraints (carry forward — UNCHANGED)

1. **No Claude co-author trailer** on any commit (verify before commit)
2. **No push without user GO** — local commits OK, push requires explicit confirmation
3. **Paper tree is OUTSIDE constitutional-aiops/ git** — paper edits are local-filesystem only
4. **Paper sandbox is the active edit target** — `sn-article-template.v2.sandbox-session16/` NOT `sn-article-template.v2/`
5. **Real paper untouched until rsync after user GO**
6. **Heading depth FROZEN** — preserve all \section/\subsection/\subsubsection in sandbox
7. **AWS instance STOPPED when not in use** — i-091c4de0e95d63154; EIP 44.195.172.165 retained; EBS snapshot snap-01b191aedbf46b598 held; do NOT release/delete
8. **MASTER_BACKUP_MANIFEST_2026-05-20.json**: do NOT regenerate
9. **Stage J helper scripts**: do NOT recreate
10. **74 RCA cases excluded uniformly post-D-1** (41 Chinese + 33 OpsEval-remined MCQ); `excluded_rca_cases.json` itself is EMPTY (exclusion happens via task_type filter now)
11. **annotation_test.json + rca_test.json dirty in local — do NOT commit content changes**
12. **Be reluctant to delete v1 original bib entries** even if unused
13. **CloudWatch idle-stop alarm `aiops-idle-stop`** — fires when CPU < 5% for 30 min. **DISABLE BEFORE PHASE 4.5 LAUNCH** to avoid premature stop during slow Neo4j writes.
14. **Read-before-Edit** on any moved file
15. **Sealed forensic docs untouched** (FULL_TRANSCRIPT_AUDIT, CV_PASS1/2, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, prior SESSION_12-17 handoffs)
16. **NEW from session 18**: BERT-F1 recompute uses `roberta-large` on CUDA; drain.jsonl is INTENTIONALLY excluded (boolean output, not free text)
17. **NEW from session 18**: User directive to start session 19 with Phase C FIRST, wait for AWS to finish before Phase B paper edits

---

## §9. First actions in session 19 (in order — DO NOT IMPROVISE)

1. Read `MEMORY.md` (auto-loaded — has SESSION 19 STARTUP block)
2. Read **THIS FILE** in full
3. Read `SESSION_17_HANDOFF.md` §3 (PATH 1/2/3/4) + `SESSION_17_AUDIT_TRIAGE.md` Tier 1 locked decisions
4. Run state verification commands from §7
5. Check D-6 BERT background completion: `Test-Path benchmark/final/_bert_f1_recompute_summary.json` + `Get-Content` it
6. Report status to user in ONE short paragraph: Phase A done; BERT background status; AWS stopped; sandbox unchanged
7. ASK user: "Phase C path decision: which of PATH 1/2/3/4 (recommend PATH 2 then 1)? Then I'll execute Phase C and wait for AWS to finish before Phase B paper edits."
8. WAIT for user direction
9. Once GO on PATH 1/2: execute pre-launch checklist (§4.2), launch AWS (§4.3), monitor (use ScheduleWakeup or background poll)
10. After AWS finishes: scp results, stop instance, **THEN** proceed to Phase B (§5)
11. After Phase B sandbox PDF ≤ 16 pages: Phase D (§6) with explicit user GO per step

---

## §10. Conversation transcript pointer

**Transcript file**: `C:\Users\partha\.claude\projects\c--Users-partha-Downloads-files-AIOPS-NEW\f63e3e73-b5a5-476e-9373-0ee35d7c1476.jsonl`

Key session-18 turns (for archaeology if needed):
- User: "re gather all context carefully, DO NOT BE DESPARATE AND READ EVERYTHING CAREFULLY"
- User: "need to do all these phases using very targeted agent edits, previously AGENTS HAVE GONE ROUGUE OFF SANDBOX AND RAN WRONG COMMANDS, can you handle this safely? sequential deatiled agents required without fail"
- User: "do very targeted edits yourslef then Phase A no need of agents. You do the edits verify and gate before next phase"
- User: "no agents this session, me direct, gated at the checkpoints above, make sure each phases is verfied and stop on completion and show me summary before proceeding to the next"
- User: "continue and finish entire phase A"
- User: "1" (choosing kick-off D-6 BERT background + proceed to Phase B)
- User: "compact context right now we start next session and make sure to start from C first need to run the aws test too and let it finish before phase C edits, PLEASE COMPACT VERU CAREFULLY SO NEXT SESSION READS ALL FILES AND DOESNT SKIP CONTEXT GATHERING"

End of handoff.
