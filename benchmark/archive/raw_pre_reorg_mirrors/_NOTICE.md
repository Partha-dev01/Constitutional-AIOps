# archive/raw_pre_reorg_mirrors/ — pre-2026-05-20 raw mining-stage mirrors

> Forensic provenance only. Do NOT use these files as inputs to any pipeline. The canonical mining-stage candidates live in `benchmark/intermediate/candidates/`.

## Origin

Mined 2026-05-13 by `benchmark/scripts/prep/mine_{apache,openssh,opseval}.py` and (incorrectly) written into `benchmark/raw/` rather than `benchmark/intermediate/candidates/`. The mining scripts were corrected in session 16 to write only into `intermediate/candidates/`, but the stale raw/ mirrors were left in place per the audit trail. Moved here in session 33 (2026-05-27) per Stage 5 §3.2 item 1 + Topology Option A sub-commit A2 to remove the rule violation while preserving the forensic trail.

## File correspondence + SHA verification

| File (this dir) | SHA-256 [:12] | Size | Counterpart in intermediate/candidates/ | Identical? |
|---|---|---:|---|---|
| `apache_candidates.jsonl` | `268999cfb202` | 19,453 B | `apache_candidates.jsonl` | **YES** — byte-identical |
| `openssh_candidates.jsonl` | `2794d6e92224` | 24,021 B | `openssh_candidates.jsonl` | **YES** — byte-identical |
| `opseval_remine_s2.jsonl` | `b9396a58173d` | 21,896 B | `opseval_remine.jsonl` (`15d47964b8de` / 28,554 B) | **NO** — older `_s2` stage-2 mining variant; superseded by the intermediate copy that landed in `benchmark_431_seed42.json` |

The opseval pair is **deliberately preserved as distinct** for forensic traceability of the mining-stage iteration history. See `benchmark/intermediate/README.md` candidates/ table for the canonical version note.

## Pointers

- Canonical paper dataset: `benchmark/intermediate/datasets/benchmark_431_seed42.json` (218 ann + 213 RCA cases)
- Stage 5 audit report: `benchmark/final/audit/paper_audit_session27_2026-05-26/07_benchmark_topology_analysis.md` §3.2 item 1
- Sub-commit plan: Stage 5 §6.1 Option A concrete moves 7-9
- This commit: Gate 39 (session 33, 2026-05-27)
