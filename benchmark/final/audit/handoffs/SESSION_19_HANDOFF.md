# Session 19 → Session 20 Handoff (2026-05-26)

> ## ⚠⚠⚠ SESSION 20 STARTUP — READ THIS FIRST, THEN MEMORY.md, THEN BEGIN AT §4 (FIRST ACTIONS)
>
> Session 19 (2026-05-26, ~3h elapsed): kicked off Phase C — launched **AWS Phase 4.5 graph experiments** in tmux on instance `i-091c4de0e95d63154` (EIP `44.195.172.165`) with all D-14/D-16 patches + post-D-1 dataset + smoke-verified end-to-end. Saved D-6 BERT context to canonical docs (SUMMARY.md §3.5 + BUG_HISTORY.md D-6 → RESOLVED). User hibernated laptop with **Phase 4.5 still running on AWS** (run will continue independently — survives SSH disconnect because it's inside tmux). When session 20 starts (3-8h later), Phase 4.5 should be **COMPLETE** (.DONE marker file present in `/mnt/runs/`). Remaining work: scp results → apply decision rule → Phase B paper edits → Phase D commits.
>
> **PRIMARY ENTRY POINTS** (read in order):
> 1. `MEMORY.md` (auto-loaded — SESSION 20 STARTUP block points here)
> 2. **THIS FILE** in full — start at §4 (FIRST ACTIONS)
> 3. `SESSION_18_HANDOFF.md` — for Phase B sentence drafts + commit groupings (still valid)
> 4. `SESSION_17_AUDIT_TRIAGE.md` — for any decision context

---

## §0. One-line state at session-19 close

Phase A ✅ (session 18). BERT ✅ (session 18 compute, session-19 docs). **Phase C launched in session 19, RUNNING on AWS — user hibernated**. Phase B + Phase D deferred to session 20.

---

## §1. Mandatory reads (in order, no skipping)

| # | File | Purpose |
|---|---|---|
| 1 | `MEMORY.md` (auto-loaded) | SESSION 20 STARTUP block |
| 2 | **`benchmark/final/audit/SESSION_19_HANDOFF.md`** (THIS FILE) | session-19 close-out + session-20 execution plan |
| 3 | `benchmark/final/audit/SESSION_18_HANDOFF.md` | Phase B sentence drafts (§5), commit groupings (§6) |
| 4 | `benchmark/final/audit/SESSION_17_AUDIT_TRIAGE.md` | per-item locked decisions (D-1..D-16, Conflicts) |
| 5 | `benchmark/final/audit/SESSION_17_RECALC_SCOPE.md` | Phase A file-by-file recalc plan (most done) |
| 6 | `benchmark/final/SUMMARY.md` (post-D-1 numbers + **NEW §3.5 BERT-F1 table**) | source-of-truth for Phase B Tables 2/6/7 |
| 7 | `benchmark/final/ablation_v4/phase5_stats.md` | source-of-truth for Phase B Tables 6a/6b |
| 8 | `benchmark/final/docs/BUG_HISTORY.md` (D-6 NOW RESOLVED footnote) | reference |
| 9 | `benchmark/final/_bert_f1_recompute_summary.json` ⭐ | **authoritative BERT-F1 source** (SESSION_18_HANDOFF §3 table had row-shift errors; SUMMARY.md §3.5 + this JSON are the canonical truth) |
| 10 | Phase 4.5 outputs (after scp): `benchmark/final/phase45_graph/exp_4_5b_summary.json` + `exp_4_5c_summary.json` | Phase B Table 6 graphsub fills (or PATH 4 trigger) |
| 11 | Sandbox paper `.tex`: `PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2.sandbox-session16/sn-article.tex` (670 lines, 16-page PDF) | Phase B edit target |
| 12 | `aws/start-vm.sh`, `aws/stop-vm.sh` | helper scripts (start-vm.sh times out on vLLM-not-running — see §3 caveat) |

---

## §2. What changed on disk in session 19

### Modified (uncommitted, working tree)
- `benchmark/final/SUMMARY.md` — header line 3 appended D-6 note; **NEW §3.5 BERT-F1 table** (15 rows) with filter caveat + paper integration plan; §5 BERT row updated ⚠ → ✅ RESOLVED; §5 verdict updated
- `benchmark/final/docs/BUG_HISTORY.md` — D-6 footnote updated to ✅ RESOLVED with headline numbers

### NEW files (untracked)
- `benchmark/final/audit/SESSION_19_HANDOFF.md` (THIS FILE)

### Carried over from session 18 (still uncommitted)
- 29 files from session 18 (D-1 dataset re-label + 16 result files + 4 stats + 5 docs + 3 scripts + 2 audit docs + HANDOFF.md)
- 14 result files with `bert_f1` field updated in place (from BERT recompute)
- NEW files from session 18: `benchmark/scripts/eval/recompute_bert_f1.py`, `benchmark/final/_bert_f1_recompute_summary.json`, `benchmark/final/_bert_recompute.log`, `benchmark/final/audit/SESSION_18_HANDOFF.md`, 6 helper scripts at `benchmark/scripts/_*.py`

### Git state (UNCHANGED)
- Local HEAD: `57035cf` (D-13 patch from session 16)
- Origin: `a5e9005` (still 2 commits behind: `ee8f125` + `57035cf`)
- No new commits in session 19 (per "no commits without GO" rule)

### Paper state (UNCHANGED)
- Sandbox: 16 pages, ModDate Mon May 25 11:05:57 2026
- Real: 17 pages, ModDate Sun May 24 21:24:32 2026

---

## §3. AWS state at session-19 close (CRITICAL)

| Resource | State at close | Implication for session 20 |
|---|---|---|
| Instance `i-091c4de0e95d63154` | **RUNNING** | will continue running until session 20 stops it; ~$0.80/hr accruing |
| EIP `44.195.172.165` | retained (do NOT release) | use this for SSH |
| CloudWatch alarm `aiops-idle-stop` | **ActionsEnabled=false** (DISABLED) | **CRITICAL — re-enable in session 20 after stopping instance, or before next launch** |
| EBS root + data volumes | intact | results + tmux session preserved |
| Tmux session `phase45` | active | survives SSH disconnect; `tmux a -t phase45` to attach |
| Python PID 3610 (`run_graph_experiments.py --exp all`) | running | child of tmux pane |
| Launch script | `/tmp/launch_phase45.sh` | will touch `.DONE` on success, `.FAIL` on failure |
| Live log (buffered by tee) | `/mnt/runs/phase45_20260525T204802Z.log` | flushes every ~4KB |
| Pane log (unbuffered, via pipe-pane) | `/mnt/runs/phase45_pane.log` | started ~9 min into run; real-time |
| Results output dir | `/mnt/aiops-repo/benchmark/final/phase45_graph/` | `exp_4_5b_summary.json` + `exp_4_5c_summary.json` on completion |
| Completion markers | `/mnt/runs/phase45_20260525T204802Z.DONE` (success) OR `.FAIL` | check first |

**Caveat — `aws/start-vm.sh`**: it polls vLLM ports 8000/8001 for health and exits with timeout 5 min if not ready. **Do NOT use it for this run** — Phase 4.5 uses Ollama (port 11434), not vLLM. Use `aws ec2 start-instances ...` directly if you need to re-start (instance should already be running when session 20 opens).

**Caveat — instance SSH SG**: rule allows 6 CIDRs including `49.37.33.243/32` (session-19 laptop IP). If session 20's laptop public IP differs, re-authorize:
```powershell
$IP = (curl -s checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --group-id sg-09680d8eb448fb704 --protocol tcp --port 22 --cidr "$IP/32" --profile aiops-operator --region us-east-1
```

**Phase 4.5 progress at session-19 close** (sanity check 2026-05-25 21:09 UTC, ~21 min into run):
- Fold 1/5 ✅ complete: **no-graph=100.0%, with-graph=100.0%** (16/16 each — ceiling effect — see §5.1 below)
- Fold 2/5 — Running without-graph (`_tmp_f1_no.json` 11300 bytes being written)
- GPU 98% util, Python alive, log/pane flowing

**Expected completion**: Launch was 20:48:02 UTC; each fold ≈ 17 min; 4.5b total ≈ 85 min ⇒ ends ~22:13 UTC; 4.5c ≈ 40-50 min ⇒ end-to-end ETA **~22:55-23:15 UTC** (≈ 2h 10m total).

**Cost note**: If session 20 wakes 6h after launch (~02:48 UTC), instance has been idle ~3.5h post-completion = ~$2.80 wasted. Acceptable; well within $120 ceiling (~$48 used + ~$5 this session = ~$53 / $120).

---

## §4. FIRST ACTIONS in session 20 (in order — DO NOT IMPROVISE)

### §4.0 ⚡⚡⚡ AWS OUTPUT VALIDATION (MANDATORY before consuming any number)

User-requested explicit validation. The Phase 4.5 run is async, multi-stage, and has multiple known failure modes (silent crash mid-fold, partial cold-start cleanup, ceiling-effect masquerading as bug). Run ALL 10 checks below; if ANY check fails, DO NOT use the numbers — diagnose first.

**Copy-paste validation block** (run on instance via SSH):
```bash
ssh -i C:/Users/partha/.ssh/aiops-key.pem ubuntu@44.195.172.165 << 'VALIDATE_EOF'
LOGFILE=/mnt/runs/phase45_20260525T204802Z.log
DONEFILE=${LOGFILE%.log}.DONE
FAILFILE=${LOGFILE%.log}.FAIL
OUTDIR=/mnt/aiops-repo/benchmark/final/phase45_graph

echo "===CHECK 1: completion marker==="
ls -la $DONEFILE $FAILFILE 2>&1 | grep -v "No such"

echo ""
echo "===CHECK 2: tmux + python gone (clean exit)==="
tmux ls 2>&1
ps -ef | grep "python3 -u benchmark/scripts/run/run_graph" | grep -v grep | head -3 || echo "(no python process — good)"

echo ""
echo "===CHECK 3: final log line==="
tail -5 $LOGFILE

echo ""
echo "===CHECK 4: exp_4_5b_summary.json schema==="
python3 -c "
import json, sys
d = json.load(open('$OUTDIR/exp_4_5b_summary.json'))
assert d.get('experiment') == '4.5b', f'wrong experiment: {d.get(\"experiment\")}'
assert d.get('n_folds') == 5, f'wrong n_folds: {d.get(\"n_folds\")}'
fr = d.get('fold_results', [])
assert len(fr) == 5, f'wrong fold count: {len(fr)}'
for i, f in enumerate(fr):
    assert 0 <= f.get('no_graph', -1) <= 100, f'fold {i+1} no_graph out of range: {f.get(\"no_graph\")}'
    assert 0 <= f.get('with_graph', -1) <= 100, f'fold {i+1} with_graph out of range: {f.get(\"with_graph\")}'
wo = d.get('without_graph_acc'); wg = d.get('with_graph_acc'); dp = d.get('delta_pp')
print(f'  PASS: 4.5b 5 folds, aggregate no_graph={wo}%, with_graph={wg}%, delta={dp:+.1f}pp')
"

echo ""
echo "===CHECK 5: exp_4_5c_summary.json schema==="
python3 -c "
import json
d = json.load(open('$OUTDIR/exp_4_5c_summary.json'))
assert d.get('experiment') == '4.5c'
curve = d.get('curve', [])
assert len(curve) == 4, f'wrong curve length: {len(curve)}'
ns_expected = [0, 20, 40, 60]
ns_actual = [p.get('n') for p in curve]
assert ns_actual == ns_expected, f'wrong N values: {ns_actual}'
for p in curve:
    assert 0 <= p.get('acc', -1) <= 100
    assert p.get('correct', -1) <= p.get('total', 0)
print(f'  PASS: 4.5c curve {ns_actual}, accs={[p[\"acc\"] for p in curve]}')
"

echo ""
echo "===CHECK 6: per-fold jsonl files==="
wc -l $OUTDIR/exp_4_5b_no_graph.jsonl $OUTDIR/exp_4_5b_with_graph.jsonl 2>&1

echo ""
echo "===CHECK 7: no NaN in any summary==="
grep -i "nan\|null\|none" $OUTDIR/*.json 2>&1 | head -5 || echo "(no NaN/null found — good)"

echo ""
echo "===CHECK 8: aggregate accuracy sanity==="
python3 -c "
import json
d = json.load(open('$OUTDIR/exp_4_5b_summary.json'))
fold_accs = d.get('fold_results', [])
unique_wo = set(f['no_graph'] for f in fold_accs)
unique_wg = set(f['with_graph'] for f in fold_accs)
if len(unique_wo) == 1 and len(unique_wg) == 1 and 100.0 in unique_wo and 100.0 in unique_wg:
    print(f'  CEILING EFFECT confirmed: all 5 folds = 100/100. Triggers PATH 4 decision (see locked rule).')
elif d['delta_pp'] == 0 and d['without_graph_acc'] == d['with_graph_acc']:
    print(f'  Δ=0 but non-100 — graph context likely not injecting. Investigate.')
else:
    print(f'  REAL VARIANCE: delta={d[\"delta_pp\"]:+.1f}pp — eligible for include-Δ in Table 6 per decision rule.')
"

echo ""
echo "===CHECK 9: dead session-17 partial data NOT in our scope==="
ls -la /mnt/aiops-repo/runs/2026-05-25T10-18-31_bench_constitutional_aiops/results.jsonl 2>&1 | head -2
echo "  ↑ this is session-17 dead data (pre-D-1, crashed) — IGNORE for paper"

echo ""
echo "===CHECK 10: 4.5c cleanup audit==="
docker exec aiops-neo4j cypher-shell -u neo4j -p constitutional_aiops_2025 "MATCH (e:Episode {_cold_start:true}) RETURN count(e) AS leftover;" 2>&1 | head -5
echo "  ↑ should be 0; if > 0, 4.5c crashed mid-run before cleanup"

echo ""
echo "===VALIDATION COMPLETE==="
VALIDATE_EOF
```

**Interpretation**:
- ALL CHECKS PASS → proceed to §4.3 (scp results)
- CHECK 1 says only `.FAIL` exists → script crashed; read full log, do NOT scp; diagnose first
- CHECK 1 says neither marker + CHECK 2 shows tmux/python alive → still running; wait
- CHECK 1 says neither + CHECK 2 dead → silent crash; pane log is most truthful (`/mnt/runs/phase45_pane.log`)
- CHECK 4/5 schema fails → output truncated; investigate before using
- CHECK 6 shows < 80 records each → fold(s) crashed silently
- CHECK 8 says "Δ=0 but non-100" → graph injection bug; verify `find_similar_episodes_by_embedding` actually called
- CHECK 10 says leftover > 0 → 4.5c partial; only N values that completed before crash are usable

### §4.1 State verification (5 min)
```powershell
# Git state (expect: 29+ modified, 4 new files added in session 19)
cd "c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops"
git status --short | wc -l
git log --oneline -3                                   # expect: 57035cf, ee8f125, 2c70872

# Paper sandbox state (must be UNCHANGED until Phase B)
pdfinfo "..\PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16\sn-article.pdf" | findstr /R "Pages ModDate"
# expect: Pages: 16, ModDate: Mon May 25 11:05:57 2026

# AWS state
aws ec2 describe-instances --instance-ids i-091c4de0e95d63154 --profile aiops-operator --region us-east-1 --query "Reservations[0].Instances[0].State.Name" --output text
# expect: running  (still running from session 19)

aws cloudwatch describe-alarms --alarm-names aiops-idle-stop --profile aiops-operator --region us-east-1 --query "MetricAlarms[0].ActionsEnabled" --output text
# expect: False  (still disabled from session 19)
```

### §4.2 Phase 4.5 completion check (2 min)
```powershell
# Re-authorize laptop IP for SSH if needed
$IP = (curl -s checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --group-id sg-09680d8eb448fb704 --protocol tcp --port 22 --cidr "$IP/32" --profile aiops-operator --region us-east-1
# (ignore "InvalidPermission.Duplicate" if rule already exists)

# Check completion markers + tmux + last log lines
ssh -i C:/Users/partha/.ssh/aiops-key.pem -o StrictHostKeyChecking=no ubuntu@44.195.172.165 'ls -la /mnt/runs/phase45_20260525T204802Z.DONE /mnt/runs/phase45_20260525T204802Z.FAIL 2>&1; echo ---; tmux ls 2>&1; echo ---; tail -40 /mnt/runs/phase45_pane.log; echo ---; ls -la /mnt/aiops-repo/benchmark/final/phase45_graph/'
```

**Possible outcomes**:
- **DONE file exists**: ✅ proceed to §4.3
- **FAIL file exists**: read full log + diagnose; do NOT touch instance until cause known
- **Neither + tmux dead + python gone**: silent crash; read pane log to last line
- **Neither + tmux alive + python alive**: still running (rare if 6h+ elapsed); inspect log progress, wait

### §4.3 Pull results to laptop (1 min)
```powershell
scp -i C:/Users/partha/.ssh/aiops-key.pem -o StrictHostKeyChecking=no -r ubuntu@44.195.172.165:/mnt/aiops-repo/benchmark/final/phase45_graph "c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\benchmark\final\"
```

### §4.4 Apply decision rule + plan Table 6 cell content (5 min)
```powershell
PYTHONIOENCODING=utf-8 python -c "import json; b=json.load(open('benchmark/final/phase45_graph/exp_4_5b_summary.json')); c=json.load(open('benchmark/final/phase45_graph/exp_4_5c_summary.json')); print('4.5b:', b); print('---'); print('4.5c:', c)"
```

**Decision rule** (locked session 19):
- **If `4.5b |Δ| ≥ 2pp` (with_graph_acc - without_graph_acc, aggregate over 80 cases)** OR **`4.5c monotone lift ≥ 3pp from N=0 to N=60`** → **OPTION A: include real Δ data in sandbox Table 6 `tab:graphsub` rows 4.5b + 4.5c**
- Else → **OPTION B = PATH 4: drop 4.5b/4.5c rows from `tab:graphsub`**, replace with one disclosure sentence in §4.5:
  > *"Both homogeneous-LEMMA sub-experiments saturated at the model's accuracy ceiling on this difficulty (no-graph=with-graph=100% across all 5 folds), confirming that graph memory's architectural value emerges in heterogeneous distributions (see §4.5a Table 6 row 1, real Δ=−2.2pp) rather than in homogeneous-easy regimes."*

Document the decision in commit message + sandbox §4.5 prose.

### §4.5 Stop instance + re-enable CloudWatch alarm (CRITICAL — before Phase B)
```powershell
aws ec2 stop-instances --instance-ids i-091c4de0e95d63154 --profile aiops-operator --region us-east-1
aws cloudwatch enable-alarm-actions --alarm-names aiops-idle-stop --profile aiops-operator --region us-east-1

# Verify both:
aws ec2 describe-instances --instance-ids i-091c4de0e95d63154 --profile aiops-operator --region us-east-1 --query "Reservations[0].Instances[0].State.Name" --output text
# expect: stopping → stopped
aws cloudwatch describe-alarms --alarm-names aiops-idle-stop --profile aiops-operator --region us-east-1 --query "MetricAlarms[0].ActionsEnabled" --output text
# expect: True
```

### §4.6 Phase B sandbox paper edits (~45 min — see §5 for full list)

### §4.7 Phase D commits + rsync + push (requires explicit USER GO per step — see §6)

---

## §5. Phase B detailed edit list (sandbox `sn-article.tex` only)

> **Important**: All edits go to `PAPER AND FORMAL DOCUMENTATION/PAPER/New Draft Paper (Not Accepted v.2)/sn-article-template.v2.sandbox-session16/sn-article.tex` — NOT the real `sn-article-template.v2/`. The real paper is rsync'd only after explicit USER GO in Phase D.

### §5.1 Table 6 `tab:graphsub` (line ~590) — DECISION POINT
Fill 4.5b + 4.5c row cells per §4.4 decision rule. If PATH 4 chosen: delete the two `[TBD]` rows and add the disclosure sentence in §4.5 prose.

### §5.2 Table 2 `tab:overall` (line ~457)
| Replace | With |
|---|---|
| Ann 82.6% (180/218) | (unchanged) |
| RCA 80.3% (114/142) | **RCA 82.0% (114/139)** |
| Overall 81.7% (294/360) | **Overall 82.4% (294/357)** |
| Footnote: "71 RCA cases excluded" | **"74 RCA cases excluded (41 Chinese + 33 OpsEval-remined MCQ)"** |
| "Ablation Full RCA 83.8% (119/142)" in variance footnote | **"85.6% (119/139)"** |
| "142 evaluable" | **"139 evaluable"** |

### §5.3 Table 6a `tab:ablation_arch` (line ~497) + Table 6b `tab:ablation_comp` (line ~524)
All N shifts `142 → 139` and `360 → 357` + accuracy percentages per `phase5_stats.md`:
| Config | RCA OLD | RCA NEW |
|---|---|---|
| Full Hybrid | 83.8% (119/142) | **85.6% (119/139)** |
| Single-4B | 81.0% (115/142) | **82.7% (115/139)** |
| Single-14B | 81.0% (115/142) | **82.7% (115/139)** |
| No-structured | 73.9% (105/142) | **75.5% (105/139)** |
| No-system-prompt | 79.6% (113/142) | **81.3% (113/139)** |
| With-graph | 81.7% (116/142) | **83.5% (116/139)** |
| No-constitutional | 71.1% (101/142) | **72.7% (101/139)** |
| With-orchestrator | 81.7% (116/142) | **83.5% (116/139)** |
Overall column: shift each `(X/360)` → `(X/357)` and recompute %. McNemar p / Cohen's h **already in phase5_stats.md** — just copy.

### §5.4 Table 7 `tab:sota` (line ~562)
| Row | OLD | NEW |
|---|---|---|
| Ours RCA | 80.3% (114/142) | **82.0% (114/139)** |
| Llama 3.3-70B RCA | 71.1% (101/142) | **71.2% (99/139)** |
| DeepSeek V3.2 RCA | 66.9% (95/142) | **66.9% (93/139)** |
| ΔRCA Ours-Llama | +9.2pp | **+10.8pp** |
| ΔRCA Ours-DeepSeek | +13.4pp | **+15.1pp** |
Caption: update wins from "9.2pp vs Llama / 13.4pp vs DeepSeek" → **"10.8pp / 15.1pp"**.

### §5.5 Other prose with stale numbers
| Line ~ | OLD | NEW |
|---|---|---|
| 455 | "81.7% overall accuracy (294/360 evaluable cases)" | **"82.4% overall accuracy (294/357 evaluable)"** |
| 564 | "wins RCA by 9.2pp vs Llama-3.3-70B and 13.4pp vs DeepSeek-V3.2" | **"by 10.8pp ... 15.1pp"** |
| 632 | "81.7% overall accuracy ... 360 evaluable" | **"82.4% / 357"** |
| 649 | "uniformly-excluded 71-case RCA list" | **"74-case RCA list (41 Chinese + 33 OpsEval-remined MCQ)"** |

### §5.6 NEW sentences to ADD (locked session 17, all texts pre-drafted)

| ID | Where (sandbox §) | Sentence |
|---|---|---|
| **D-1** | §4 Experimentation | "74 RCA candidates were excluded at evaluation time (41 Chinese-language plus 33 OpsEval-remined MCQ-format cases mis-classified during curation; see audit doc), yielding 139 evaluable RCA cases." |
| **D-2** | §5.3 or §6.2 | "On OpenSSH, the model reports 50% accuracy; all 20 errors are false positives (over-flagging single failed-login events as security incidents) with zero false negatives on the 20 brute-force attacks. This conservative bias may be desirable in production triage settings." |
| **D-3** | §5.7 SOTA, near line 558-560 | "DeepSeek V3.2 and Llama 3.3-70B are used as closed-source and open-weight frontier baselines from the 2024-2025 release window." |
| **Conflict-4** | §6.2 Limitations, near line 619-622 | "The confidence weight coefficients (α=0.4, β=0.35, γ=0.25) were chosen heuristically; empirical calibration on a held-out tuning set is left for future work." (REPLACE or APPEND existing nearby sentence on confidence weights) |
| **B-4** | Tables 2 + 6 footnotes | verify already-present variance footnote: "5-case temp=0 nondeterminism between runs" — still valid post-D-1 (Full RCA 119 vs main RCA 114 = 5 cases) |
| **D-6 PATH 4 fallback** (if chosen) | §4.5 | see §5.1 above |

### §5.7 BERT-F1 integration (D-6 Option B preferred, fallback to C)
Per SUMMARY.md §3.5 + `_bert_f1_recompute_summary.json` (authoritative):
- Add BERT-F1 column to sandbox Tables 2 + 7 with values:
  - Table 2 Ours: **0.8124**
  - Table 7 Ours: 0.8124, Llama: **0.8269**, DeepSeek: **0.8264**, Drain: — (skipped, boolean output)
- After adding: recompile, check page count
- **Decision gate**: if PDF > 16 pages, fall back to Option C — drop the column and add 1 sentence in §5: *"Mean BERTScore F1 was 0.81 ± 0.01 across all configurations and SOTA baselines (recomputed with roberta-large; see Appendix / Supplementary), supporting semantic adequacy of the model outputs alongside the accuracy metrics."*

### §5.8 Recompile + verify
```powershell
cd "PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16"
pdflatex sn-article.tex
pdflatex sn-article.tex
pdfinfo sn-article.pdf | findstr Pages
# MUST be ≤ 16
```

---

## §6. Phase D plan (requires explicit USER GO per step)

### §6.1 Suggested commit grouping (no Claude trailer; HEREDOC for messages)
1. `data(D-1): re-label 33 OpsEval-remined cases as qa_mcq + sync 16 result files + Phase 5 recompute`
2. `docs: update SUMMARY/METHODOLOGY/MANIFEST/BUG_HISTORY/AUDIT_REPORT for post-D-1 + D-2/D-3/D-5/Conflict-5 disclosures`
3. `fix(benchmark/scripts): D-7 test_5plus5 ref + D-14 path fallback + D-16 dataclass attr`
4. `eval(D-6): BERT-F1 recompute via roberta-large on CUDA + recompute_bert_f1.py + SUMMARY.md §3.5 + BUG_HISTORY.md D-6 → RESOLVED`
5. `data(4.5): Phase 4.5 LEMMA homogeneous 5-fold + cold-start curve results` (only if real Δ data; otherwise integrate into commit 6)
6. `paper(sandbox→real): Tables 2/6a/6b/7 post-D-1 numbers + Table 6 graphsub [DECISION_RESULT] + 4 new sentences + variance footnotes + BERT-F1 column [Option B/C]`
7. `docs(audit): SESSION_19_HANDOFF.md close-out`

### §6.2 Rsync (REQUIRES USER GO)
```powershell
# After Phase B PDF verified ≤ 16p:
robocopy "PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2.sandbox-session16" "PAPER AND FORMAL DOCUMENTATION\PAPER\New Draft Paper (Not Accepted v.2)\sn-article-template.v2" /MIR /XD .git
```
or equivalent rsync. Then recompile in real path too.

### §6.3 Push to origin (REQUIRES SEPARATE USER GO)
```powershell
git push origin main
```

---

## §7. Hard constraints (carry forward — UNCHANGED)

1. **No Claude co-author trailer** on any commit
2. **No push without user GO** — local commits OK, push requires explicit confirmation
3. **Paper tree is OUTSIDE constitutional-aiops/ git** — paper edits are local-filesystem only
4. **Paper sandbox is the active edit target** — `sn-article-template.v2.sandbox-session16/` NOT `sn-article-template.v2/`
5. **Real paper untouched until rsync after user GO**
6. **Heading depth FROZEN** — preserve all \section/\subsection/\subsubsection in sandbox
7. **AWS instance STOPPED when not in use** — i-091c4de0e95d63154; EIP 44.195.172.165 retained; EBS snapshot snap-01b191aedbf46b598 held; do NOT release/delete
8. **MASTER_BACKUP_MANIFEST_2026-05-20.json**: do NOT regenerate
9. **Stage J helper scripts**: do NOT recreate
10. **74 RCA cases excluded uniformly post-D-1** (41 Chinese + 33 OpsEval-remined MCQ); `excluded_rca_cases.json` itself is EMPTY (exclusion via task_type filter)
11. **annotation_test.json + rca_test.json dirty in local — do NOT commit content changes**
12. **Be reluctant to delete v1 original bib entries** even if unused
13. **CloudWatch idle-stop alarm `aiops-idle-stop`** — fires when CPU < 5% for 30 min. **CURRENTLY DISABLED (session 19) — MUST RE-ENABLE after stopping instance in session 20**
14. **Read-before-Edit** on any moved file
15. **Sealed forensic docs untouched** (FULL_TRANSCRIPT_AUDIT, CV_PASS1/2, REORG_PROPOSAL, MASTER_BACKUP_MANIFEST, prior SESSION_12-18 handoffs)
16. **BERT-F1 numbers — `_bert_f1_recompute_summary.json` + SUMMARY.md §3.5 are authoritative** (SESSION_18_HANDOFF §3 table had row-shift errors — IGNORE that table)
17. **NEVER pkill -f on a pattern that might match the SSH command line** (session-19 lesson — caused mysterious SSH 255 exits)
18. **NEVER `tmux kill-session` then re-launch in same SSH command** — the SSH session can die between the two (session-19 lesson)
19. **Use `PYTHONUNBUFFERED=1` + `python3 -u`** when launching long-running Python via tmux + `tee` (otherwise log file buffers up to 4KB and looks frozen for minutes)
20. **For real-time tmux visibility under tee buffering**: `tmux pipe-pane -t <session> -o 'cat >> /path/log'` gives an unbuffered side-log

---

## §8. Risk register (session 20 specific)

| Risk | Likelihood | Mitigation |
|---|---|---|
| Instance still running after wakeup with no .DONE → wasted hours | Low | §4.2 check first; stop manually if hung |
| CloudWatch alarm not re-enabled → future runs unprotected | Medium | §4.5 mandatory step; verify post-stop |
| Phase 4.5 .FAIL file present → diagnosis needed | Low | run survived smoke test + Fold 1; if FAIL, read full log before any action |
| Both 4.5b + 4.5c saturate at 100% → PATH 4 only option | Medium-High (Fold 1 was 100/100) | PATH 4 disclosure is pre-drafted in §5.1 |
| SSH SG IP changed after hibernate | Medium | §4.2 first command re-authorizes new IP |
| PDF overflows 16p after BERT column addition | Medium | §5.7 Option C fallback (1-sentence) |
| Push to origin requires GitHub auth tokens after hibernate | Low | re-authenticate via `gh auth status` if needed |

---

## §9. Conversation transcript pointer

**Transcript file**: `C:\Users\partha\.claude\projects\c--Users-partha-Downloads-files-AIOPS-NEW\f63e3e73-b5a5-476e-9373-0ee35d7c1476.jsonl`

Key session-19 turns (for archaeology):
- User: "re gather all context carefully, DO NOT BE DESPARATE AND READ EVERYTHING CAREFULLY"
- User chose PATH 2 then PATH 1 for Phase C
- Smoke test (1 case each side) passed cleanly
- Phase 4.5 launched 20:48:02 UTC; Fold 1 done 21:05:21Z (no-graph=100%, with-graph=100%)
- User: "save the bert score context properly and monitor the aws run for the next 10 mins"
- User: "then do we need to change and re run tests?" — answered NO, wait for full data; decision rule pre-baked
- User: "include real Δ data in Table 6 if any signal emerged, or (b) PATH 4 + 1-sentence honest disclosure. Both are defensible." + "schedule this too properly so that we have results back to back"
- User: hibernating laptop, will resume in next session

---

## §10. First-action quickref card (printable summary)

```
SESSION 20 STARTUP — 5-STEP QUICKREF
1. Read MEMORY.md + this handoff (10 min)
2. State verify: git, sandbox PDF, AWS state (running?), CW alarm (disabled?) (5 min)
3. SSH check: ls /mnt/runs/*.DONE | tmux ls | tail pane log (re-authorize IP if needed) (2 min)
4. If .DONE → scp results → apply decision rule → STOP instance → re-enable alarm (10 min)
5. Phase B sandbox edits per §5 (~45 min) → halt for Phase D user GO
```

End of handoff. Wake-up time: instance has been running since 20:48 UTC; cost meter ticking at ~$0.80/hr. Priority on wake-up: §4.2 → §4.5 (verify + stop within first 15 min of session).
