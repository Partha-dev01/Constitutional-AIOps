# FINAL/ — Audit Report

_Built: 2026-05-19 04:58 UTC_

Per-file content audit. Looks for:
- Record count mismatches (expected 218 ann + 213 rca = 431; SOTA Drain = 202 ann; phase46 = 431)
- Missing required fields (`task_type`, `test_id`/`case_id`, `correct`, `expected_output`, `actual_output`)
- Wrong number of excluded RCA records (should be 71 = 39 Chinese + 32 MC letter)
- Duplicate test_ids (the bug found in DeepSeek t=0 BAK had 103 dups)
- BERT-F1 zeros (known limitation from disk-full bug #8 — informational only)

## Summary

| Status | Count |
|---|---|
| OK | 23 |
| WARN | 0 |
| FAIL | 0 |

## Per-file findings

### `benchmark\results_aws\FINAL\main_benchmark\results.json` — **OK**

- SHA-256: `d712850bed54dc639389ff69faf49b63b51a180930d889b1f4d9de58beea76df`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 180, 'rca_correct': 197, 'rca_excluded': 0, 'rca_evaluable': 213, 'duplicate_ids': 0, 'bert_zero': 431}

Findings:
- NOTE: all 431 records have bert_f1=0/null (known limitation, disk-full bug #8 — recomputable post-hoc)

### `benchmark\results_aws\FINAL\main_benchmark\results_sota_eval_431.json` — **OK**

- SHA-256: `5a2c38300f2bd085d6cfb7b8fe7ac5aeacf9fc466b46ae18408e652d5b0e1434`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 180, 'rca_correct': 114, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\ablation_v4\ablation_full\results.json` — **OK**

- SHA-256: `0f3d6863384c35631861ac7eecaad26a506ddd09b9946fbf732a5e46a30cdac1`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 181, 'rca_correct': 196, 'rca_excluded': 0, 'rca_evaluable': 213, 'duplicate_ids': 0, 'bert_zero': 431}

Findings:
- NOTE: all 431 records have bert_f1=0/null (known limitation, disk-full bug #8 — recomputable post-hoc)

### `benchmark\results_aws\FINAL\ablation_v4\ablation_full\results_sota_eval_431.json` — **OK**

- SHA-256: `5b14ddfc90d27cac0aee6ed430463ebfa6bbe87ec011a10f54d16471e6224008`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 181, 'rca_correct': 119, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\ablation_v4\ablation_single_4b\results.json` — **OK**

- SHA-256: `3423147db1cbada2e3e9d46fe0c3284e7d1cdbf49553c9cdf3cf3fd816aabf08`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 180, 'rca_correct': 211, 'rca_excluded': 0, 'rca_evaluable': 213, 'duplicate_ids': 0, 'bert_zero': 431}

Findings:
- NOTE: all 431 records have bert_f1=0/null (known limitation, disk-full bug #8 — recomputable post-hoc)

### `benchmark\results_aws\FINAL\ablation_v4\ablation_single_4b\results_sota_eval_431.json` — **OK**

- SHA-256: `69220454e18df0cc89e6b918646bdaa1e5c318ef5260bfd1c6ba1066a42afb71`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 180, 'rca_correct': 115, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\ablation_v4\ablation_single_14b\results.json` — **OK**

- SHA-256: `10f0853bf521826d900c39319aa8e5090daa2965559c92b3ba87cb4928c4e21c`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 184, 'rca_correct': 194, 'rca_excluded': 0, 'rca_evaluable': 213, 'duplicate_ids': 0, 'bert_zero': 431}

Findings:
- NOTE: all 431 records have bert_f1=0/null (known limitation, disk-full bug #8 — recomputable post-hoc)

### `benchmark\results_aws\FINAL\ablation_v4\ablation_single_14b\results_sota_eval_431.json` — **OK**

- SHA-256: `a82cb30247b0e2589322d11359fbda726f05360931f15a2e01d2e16950ad53fc`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 184, 'rca_correct': 115, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\ablation_v4\ablation_no_structured\results.json` — **OK**

- SHA-256: `c377312601fc9c8b9879248a4f2a6c3e63a398936eb1b7830d83768a87fb0856`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 180, 'rca_correct': 124, 'rca_excluded': 0, 'rca_evaluable': 213, 'duplicate_ids': 0, 'bert_zero': 431}

Findings:
- NOTE: all 431 records have bert_f1=0/null (known limitation, disk-full bug #8 — recomputable post-hoc)

### `benchmark\results_aws\FINAL\ablation_v4\ablation_no_structured\results_sota_eval_431.json` — **OK**

- SHA-256: `0299547d52b8d8b30a59112a18104730db05c64c3516b841f04c608d0d03a295`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 180, 'rca_correct': 105, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\ablation_v4\ablation_no_system_prompt\results.json` — **OK**

- SHA-256: `820155721d629d10385d6a1c4711221753311e89582afdf965931c8424c4f5a5`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 106, 'rca_correct': 168, 'rca_excluded': 0, 'rca_evaluable': 213, 'duplicate_ids': 0, 'bert_zero': 431}

Findings:
- NOTE: all 431 records have bert_f1=0/null (known limitation, disk-full bug #8 — recomputable post-hoc)

### `benchmark\results_aws\FINAL\ablation_v4\ablation_no_system_prompt\results_sota_eval_431.json` — **OK**

- SHA-256: `93c5341d748c2f45556bb92d675c3185f27e70c3c49e07b01da7bdb9c3e60d3a`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 106, 'rca_correct': 113, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\ablation_v4\ablation_with_graph\results.json` — **OK**

- SHA-256: `6d259c5d7dacd38f5ca1429a6bc84e9e89f901d516a0dc7208f505bcdf5be067`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 180, 'rca_correct': 196, 'rca_excluded': 0, 'rca_evaluable': 213, 'duplicate_ids': 0, 'bert_zero': 431}

Findings:
- NOTE: all 431 records have bert_f1=0/null (known limitation, disk-full bug #8 — recomputable post-hoc)

### `benchmark\results_aws\FINAL\ablation_v4\ablation_with_graph\results_sota_eval_431.json` — **OK**

- SHA-256: `8317aa973d4ecab377a6509e22be7249fff74dcbb74b55064a5604b948e9495a`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 180, 'rca_correct': 116, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\ablation_v4\ablation_no_constitutional\results.json` — **OK**

- SHA-256: `f37058ffdc2535cade80cf7489f5d7c8285c0a129c3885926f338d047def57e4`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 195, 'rca_correct': 88, 'rca_excluded': 0, 'rca_evaluable': 213, 'duplicate_ids': 0, 'bert_zero': 431}

Findings:
- NOTE: all 431 records have bert_f1=0/null (known limitation, disk-full bug #8 — recomputable post-hoc)

### `benchmark\results_aws\FINAL\ablation_v4\ablation_no_constitutional\results_sota_eval_431.json` — **OK**

- SHA-256: `3010abd7ac4d99592a940c8a403d212a3e8aa1f2ba9798b2a67504f341945324`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 195, 'rca_correct': 101, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\ablation_v4\ablation_with_orchestrator\results.json` — **OK**

- SHA-256: `14307f88a3be6757e98f66c605bd493b4fb508fe84c057ca03d390ed85178b4e`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 180, 'rca_correct': 198, 'rca_excluded': 0, 'rca_evaluable': 213, 'duplicate_ids': 0, 'bert_zero': 431}

Findings:
- NOTE: all 431 records have bert_f1=0/null (known limitation, disk-full bug #8 — recomputable post-hoc)

### `benchmark\results_aws\FINAL\ablation_v4\ablation_with_orchestrator\results_sota_eval_431.json` — **OK**

- SHA-256: `bd461d11852c10006ad0e5ccaa947312ec4f809db3894542ac23fff5447796b0`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 180, 'rca_correct': 116, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\sota_baselines\llama_3_3_70b.jsonl` — **OK**

- SHA-256: `ed468f8fbe0bf4e083e925a6847be60b2250de399ff8abd93169554fcd973705`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 199, 'rca_correct': 101, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\sota_baselines\deepseek_v3.jsonl` — **OK**

- SHA-256: `b003589dfa6465c9415e6ed45fe15883e3ce5745c7c74d5dec5bed8b3875cd2f`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 197, 'rca_correct': 95, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\sota_baselines\drain.jsonl` — **OK**

- SHA-256: `64850478676e6328882e402df3d30c52f08b6cebe9a5c59451b8addbacb1f83a`
- Stats: {'n': 202, 'ann_total': 202, 'rca_total': 0, 'ann_correct': 102, 'rca_correct': 0, 'rca_excluded': 0, 'rca_evaluable': 0, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\phase46_no_prompt\llama_noprompt_clean.jsonl` — **OK**

- SHA-256: `aaf5d7cdf80cdcbcf0e68edec76db06de342300b58c204e7a13f9cc1fba5585d`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 148, 'rca_correct': 104, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

### `benchmark\results_aws\FINAL\phase46_no_prompt\deepseek_noprompt_v2.jsonl` — **OK**

- SHA-256: `b19f9943b7a75d9ba61a9c10207a1280b8a001ac87d7147858f569989ae0489e`
- Stats: {'n': 431, 'ann_total': 218, 'rca_total': 213, 'ann_correct': 193, 'rca_correct': 105, 'rca_excluded': 71, 'rca_evaluable': 142, 'duplicate_ids': 0, 'bert_zero': 0}

- _no findings — all checks passed_

