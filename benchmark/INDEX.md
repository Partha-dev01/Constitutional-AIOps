# benchmark/ - Master Index

_Generated: 2026-05-25 (session 16). Baseline: `CV_PASS2_CODEBASE_AUDIT.md` Part B (491 files, 2026-05-20) + `MASTER_BACKUP_MANIFEST_2026-05-20.json` (493 files)._

> **Update protocol**: whenever a file is added/removed/moved under `benchmark/`, this index MUST be regenerated. Also bump the `MEMORY.md` "Hard pointers" block if a canonical artifact location changes.

> **SHA-256 source**: SHAs in this index are short (first 12 hex chars) and cite `MASTER_BACKUP_MANIFEST_2026-05-20.json` via mapped post-reorg paths. Files added since 2026-05-20 (or for which no mapping exists in the manifest) are marked `[unknown - not in 2026-05-20 manifest]`. To recompute, run `python benchmark/scripts/ops/master_backup_manifest.py` (writes a new JSON manifest with full 64-char hashes).

## §1 Partition overview

| Partition | Role | File count | Total size | Key entry-points |
|---|---|---:|---:|---|
| `raw/` | Third-party + mining outputs (gitignored mirrors) | 97 | 6.59 MB | `raw/README.md`, `loghub/`, `opseval/`, `lemma_rca/` |
| `intermediate/` | Processed datasets + candidates (tracked) | 13 | 1.63 MB | `intermediate/README.md`, `datasets/benchmark_431_seed42.json` (canonical paper dataset) |
| `final/` | Paper-ready results + audit + docs | 64 | 7.59 MB | `final/SUMMARY.md`, `final/MANIFEST.md`, `final/AUDIT_REPORT.md`, `final/audit/`, `final/docs/` |
| `archive/` | Historical / superseded artifacts | 207 | 21.38 MB | `archive/README.md`, `originals_2026-05-19/`, `v0.9.1_jarvis_baseline/`, `raw_pre_reorg_mirrors/` (session 33) |
| `scripts/` | 34 Python scripts in 5 sub-folders + README | 40 | 427.9 KB | `scripts/README.md`, `prep/`, `run/`, `eval/`, `ops/`, `_dev/` |
| **TOTAL** | | **422** | **37.62 MB** | |

Walk methodology: `find benchmark -type f` (excluding `__pycache__`, `.git`, `node_modules`). Files in `raw/` are gitignored but present on disk; counted here.

**Session 33 (2026-05-27) — Phase 5 Topology Option A sub-commit A2**: 3 stale raw-mining mirrors (`apache_candidates.jsonl`, `openssh_candidates.jsonl`, `opseval_remine_s2.jsonl`) moved from `raw/` → `archive/raw_pre_reorg_mirrors/` (+1 `_NOTICE.md`). Net: raw 100→97, archive 203→207 (+4). Total count unchanged.

**Session 33 (2026-05-27) — Phase 5 Topology Option A sub-commit A3**: top-level `INDEX_BUILD_REPORT.md` relocated to `final/audit/SESSION_16_INDEX_BUILD_REPORT.md` (R100 git rename) to co-locate with the rest of the session-16 forensic record and match the `SESSION_NN_*.md` audit-dir convention. Net: top-level `.md` count goes from 3 to 2 (`HANDOFF.md` + `INDEX.md` remain); final/ count goes from 64 to 65 (this file). Per-file enumeration in §2.final is intentionally not extended for session-NN audit/handoff docs (consistent with the existing convention there).

## §2 Per-file index

Grouped by partition. Within each partition rows are sorted alphabetically by path. Status legend: `active` = paper-evidence pipeline reads it; `historical` = forensic / superseded; `dev` = smoke / debug; `sealed-forensic` = do-not-modify session-12 forensic; `unknown` = role could not be inferred.

### §2.raw — `raw/` (100 files, 6.65 MB)

| Path | Role | Status | Size | Last-modified | SHA-256[:12] |
|---|---|---|---:|---|---|
| `raw/README.md` | partition/folder README | active | 1.6 KB | 2026-05-24 19:58:25 | `[unknown - not in 2026-05-20 manifest]` |
| `raw/apache_candidates.jsonl` | raw mining output (gitignored mirror of intermediate/candidates/) | active | 19.5 KB | 2026-05-13 12:41:02 | `268999cfb202` |
| `raw/lemma_rca/.cache/huggingface/.gitignore` | LEMMA-RCA cache marker (gitignored) | active | 1 B | 2026-01-30 18:22:58 | `684888c0ebb1` |
| `raw/lemma_rca/.cache/huggingface/download/Log Data/20231207.zip.metadata` | LEMMA-RCA cache marker (gitignored) | active | 127 B | 2026-01-30 18:22:59 | `8995c231e9ba` |
| `raw/loghub/apache/Apache_2k.log` | Loghub raw dataset (gitignored) | active | 171.2 KB | 2026-05-12 00:17:02 | `c7efa3eb686e` |
| `raw/loghub/apache/Apache_2k.log_structured.csv` | Loghub raw dataset (gitignored) | active | 258.8 KB | 2026-05-12 00:17:02 | `54331d12eedf` |
| `raw/loghub/apache/Apache_2k.log_templates.csv` | Loghub raw dataset (gitignored) | active | 287 B | 2026-05-12 00:17:03 | `64e4bf77bb87` |
| `raw/loghub/bgl/BGL_2k.log` | Loghub raw dataset (gitignored) | active | 317.1 KB | 2026-01-29 10:18:30 | `2a819ea54090` |
| `raw/loghub/bgl/BGL_2k.log_structured.csv` | Loghub raw dataset (gitignored) | active | 425.1 KB | 2026-01-29 10:18:30 | `3fe74103c0b0` |
| `raw/loghub/bgl/BGL_2k.log_templates.csv` | Loghub raw dataset (gitignored) | active | 8.7 KB | 2026-01-29 10:18:31 | `fe156be23d44` |
| `raw/loghub/hdfs/HDFS_2k.log` | Loghub raw dataset (gitignored) | active | 287.8 KB | 2026-01-29 10:18:30 | `7c967000980c` |
| `raw/loghub/hdfs/HDFS_templates.csv` | Loghub raw dataset (gitignored) | active | 1.6 KB | 2026-01-29 10:18:29 | `757cc90a3256` |
| `raw/loghub/linux/Linux_2k.log` | Loghub raw dataset (gitignored) | active | 216.5 KB | 2026-05-12 00:17:03 | `b3e20bc1afe7` |
| `raw/loghub/linux/Linux_2k.log_structured.csv` | Loghub raw dataset (gitignored) | active | 327.8 KB | 2026-05-12 00:17:03 | `7c86d7b0ecb9` |
| `raw/loghub/linux/Linux_2k.log_templates.csv` | Loghub raw dataset (gitignored) | active | 5.5 KB | 2026-05-12 00:17:04 | `60ed088e0aa8` |
| `raw/loghub/openssh/OpenSSH_2k.log` | Loghub raw dataset (gitignored) | active | 225.2 KB | 2026-05-12 00:17:04 | `1e4912727fa8` |
| `raw/loghub/openssh/OpenSSH_2k.log_structured.csv` | Loghub raw dataset (gitignored) | active | 357.7 KB | 2026-05-12 00:17:05 | `c0996a11545f` |
| `raw/loghub/openssh/OpenSSH_2k.log_templates.csv` | Loghub raw dataset (gitignored) | active | 1.9 KB | 2026-05-12 00:17:05 | `c23fb1bb925a` |
| `raw/openssh_candidates.jsonl` | raw mining output (gitignored mirror of intermediate/candidates/) | active | 24.0 KB | 2026-05-13 12:41:06 | `2794d6e92224` |
| `raw/opseval/.gitattributes` | OpsEval raw dataset (gitignored) | active | 2.3 KB | 2026-01-29 10:18:28 | `f4e703ea6e44` |
| `raw/opseval/.gitignore` | OpsEval raw dataset (gitignored) | active | 13 B | 2026-01-29 10:18:28 | `0e42427c8ba1` |
| `raw/opseval/LICENSE` | OpsEval raw dataset (gitignored) | active | 1.1 KB | 2026-01-29 10:18:28 | `05b92196a0ba` |
| `raw/opseval/README.md` | partition/folder README | active | 7.5 KB | 2026-01-29 10:18:28 | `f5db0b8c5a3f` |
| `raw/opseval/annotation/Annotation Guideline for OpsEval Categorization.md` | OpsEval raw dataset (gitignored) | active | 6.0 KB | 2026-01-29 10:18:28 | `d31c655935ef` |
| `raw/opseval/assets/bar_charts/bosc_zh_qa.pdf` | OpsEval raw dataset (gitignored) | active | 15.4 KB | 2026-01-29 10:18:28 | `77614277ec6a` |
| `raw/opseval/assets/bar_charts/owl_en_qa.pdf` | OpsEval raw dataset (gitignored) | active | 15.6 KB | 2026-01-29 10:18:28 | `58251c242840` |
| `raw/opseval/assets/bar_charts/owl_zh_qa.pdf` | OpsEval raw dataset (gitignored) | active | 15.4 KB | 2026-01-29 10:18:28 | `3903408a0e51` |
| `raw/opseval/assets/bar_charts/rzy_zh_qa.pdf` | OpsEval raw dataset (gitignored) | active | 15.5 KB | 2026-01-29 10:18:28 | `fff977f83bc4` |
| `raw/opseval/assets/bar_charts/zabbix_zh_qa.pdf` | OpsEval raw dataset (gitignored) | active | 15.8 KB | 2026-01-29 10:18:28 | `608017592114` |
| `raw/opseval/assets/bar_charts/zjyd_zh_qa.pdf` | OpsEval raw dataset (gitignored) | active | 15.6 KB | 2026-01-29 10:18:28 | `734c5b7d1473` |
| `raw/opseval/assets/radar_charts/bosc_zh_qa.pdf` | OpsEval raw dataset (gitignored) | active | 28.9 KB | 2026-01-29 10:18:28 | `b1a8442d7c49` |
| `raw/opseval/assets/radar_charts/owl_en_qa.pdf` | OpsEval raw dataset (gitignored) | active | 29.0 KB | 2026-01-29 10:18:28 | `98b590dbf7c4` |
| `raw/opseval/assets/radar_charts/owl_zh_qa.pdf` | OpsEval raw dataset (gitignored) | active | 28.9 KB | 2026-01-29 10:18:28 | `34b93f153908` |
| `raw/opseval/assets/radar_charts/rzy_zh_qa.pdf` | OpsEval raw dataset (gitignored) | active | 29.0 KB | 2026-01-29 10:18:28 | `12e04327d27d` |
| `raw/opseval/assets/radar_charts/zabbix_zh_qa.pdf` | OpsEval raw dataset (gitignored) | active | 29.3 KB | 2026-01-29 10:18:28 | `a85bc0db9ce2` |
| `raw/opseval/assets/radar_charts/zjyd_zh_qa.pdf` | OpsEval raw dataset (gitignored) | active | 29.1 KB | 2026-01-29 10:18:28 | `1e8e359a267e` |
| `raw/opseval/case_analysis/qa_metrics_comparison.json` | OpsEval raw dataset (gitignored) | active | 32.0 KB | 2026-01-29 10:18:28 | `1070b41ec56f` |
| `raw/opseval/data/.DS_Store` | OpsEval raw dataset (gitignored) | active | 6.1 KB | 2026-01-29 10:18:28 | `83f2cf16ec1b` |
| `raw/opseval/data/en/dev/5G Communication.json` | OpsEval raw dataset (gitignored) | active | 4.2 KB | 2026-01-29 10:18:28 | `8768936b3846` |
| `raw/opseval/data/en/dev/Huawei Cloud.json` | OpsEval raw dataset (gitignored) | active | 1.4 KB | 2026-01-29 10:18:28 | `7444278fbc89` |
| `raw/opseval/data/en/dev/Mobile Communication Network.json` | OpsEval raw dataset (gitignored) | active | 1.9 KB | 2026-01-29 10:18:28 | `ad73ce8f9901` |
| `raw/opseval/data/en/dev/Wired Network.json` | OpsEval raw dataset (gitignored) | active | 7.1 KB | 2026-01-29 10:18:28 | `cf22f261edf9` |
| `raw/opseval/data/en/test/5G Communication.json` | OpsEval raw dataset (gitignored) | active | 134.5 KB | 2026-01-29 10:18:28 | `d0afb07bb554` |
| `raw/opseval/data/en/test/Huawei Cloud.json` | OpsEval raw dataset (gitignored) | active | 8.2 KB | 2026-01-29 10:18:28 | `19b7e26447c9` |
| `raw/opseval/data/en/test/Mobile Communication Network.json` | OpsEval raw dataset (gitignored) | active | 53.6 KB | 2026-01-29 10:18:28 | `f804c875854e` |
| `raw/opseval/data/en/test/Wired Network.json` | OpsEval raw dataset (gitignored) | active | 1.30 MB | 2026-01-29 10:18:28 | `ecaa1a447559` |
| `raw/opseval/data/zh/dev/5G Communication.json` | OpsEval raw dataset (gitignored) | active | 1.7 KB | 2026-01-29 10:18:28 | `4d4a753d8b47` |
| `raw/opseval/data/zh/dev/Financial IT.json` | OpsEval raw dataset (gitignored) | active | 1.3 KB | 2026-01-29 10:18:28 | `a9d22d651c8f` |
| `raw/opseval/data/zh/dev/Hybrid Cloud.json` | OpsEval raw dataset (gitignored) | active | 2.7 KB | 2026-01-29 10:18:28 | `112212c78542` |
| `raw/opseval/data/zh/dev/Log Analysis.json` | OpsEval raw dataset (gitignored) | active | 2.5 KB | 2026-01-29 10:18:28 | `bce9b1949225` |
| `raw/opseval/data/zh/dev/Mobile Communication Network.json` | OpsEval raw dataset (gitignored) | active | 1.7 KB | 2026-01-29 10:18:28 | `596d9fb77814` |
| `raw/opseval/data/zh/dev/Operations Monitoring.json` | OpsEval raw dataset (gitignored) | active | 2.3 KB | 2026-01-29 10:18:28 | `03b166f587b1` |
| `raw/opseval/data/zh/dev/Oracle Database.json` | OpsEval raw dataset (gitignored) | active | 3.3 KB | 2026-01-29 10:18:28 | `a5f266556255` |
| `raw/opseval/data/zh/dev/Securities Information System.json` | OpsEval raw dataset (gitignored) | active | 5.2 KB | 2026-01-29 10:18:28 | `4dc7f252163a` |
| `raw/opseval/data/zh/dev/Wired Network.json` | OpsEval raw dataset (gitignored) | active | 6.4 KB | 2026-01-29 10:18:28 | `296bef6dd0b7` |
| `raw/opseval/data/zh/test/5G Communication.json` | OpsEval raw dataset (gitignored) | active | 137.7 KB | 2026-01-29 10:18:28 | `2cb443d162a6` |
| `raw/opseval/data/zh/test/Financial IT.json` | OpsEval raw dataset (gitignored) | active | 34.8 KB | 2026-01-29 10:18:28 | `8b3a786502c4` |
| `raw/opseval/data/zh/test/Hybrid Cloud.json` | OpsEval raw dataset (gitignored) | active | 24.4 KB | 2026-01-29 10:18:28 | `f4308e2c8324` |
| `raw/opseval/data/zh/test/Log Analysis.json` | OpsEval raw dataset (gitignored) | active | 190.7 KB | 2026-01-29 10:18:28 | `f79f3ded9764` |
| `raw/opseval/data/zh/test/Mobile Communication Network.json` | OpsEval raw dataset (gitignored) | active | 50.4 KB | 2026-01-29 10:18:28 | `6735878cc675` |
| `raw/opseval/data/zh/test/Operations Monitoring.json` | OpsEval raw dataset (gitignored) | active | 30.9 KB | 2026-01-29 10:18:28 | `ab7784823918` |
| `raw/opseval/data/zh/test/Oracle Database.json` | OpsEval raw dataset (gitignored) | active | 207.8 KB | 2026-01-29 10:18:28 | `b6f9c627f8d8` |
| `raw/opseval/data/zh/test/Securities Information System.json` | OpsEval raw dataset (gitignored) | active | 60.3 KB | 2026-01-29 10:18:28 | `b356d8b8c1e4` |
| `raw/opseval/data/zh/test/Wired Network.json` | OpsEval raw dataset (gitignored) | active | 1.33 MB | 2026-01-29 10:18:28 | `a783c0a7ec2d` |
| `raw/opseval/docs/Annotation Guideline for OpsEval Categorization.md` | OpsEval raw dataset (gitignored) | active | 6.0 KB | 2026-01-29 10:18:29 | `d31c655935ef` |
| `raw/opseval/docs/dataset_distribution.md` | OpsEval raw dataset (gitignored) | active | 2.8 KB | 2026-01-29 10:18:29 | `31348ffa5547` |
| `raw/opseval/leaderboard/.DS_Store` | OpsEval raw dataset (gitignored) | active | 8.2 KB | 2026-01-29 10:18:29 | `1c7b30bebe51` |
| `raw/opseval/leaderboard/bosc_zh_mc.csv` | OpsEval raw dataset (gitignored) | active | 1.0 KB | 2026-01-29 10:18:29 | `b26512fa01cb` |
| `raw/opseval/leaderboard/bosc_zh_qa.csv` | OpsEval raw dataset (gitignored) | active | 1.6 KB | 2026-01-29 10:18:29 | `ad573ba02342` |
| `raw/opseval/leaderboard/dfcdata_zh_mc.csv` | OpsEval raw dataset (gitignored) | active | 1.5 KB | 2026-01-29 10:18:29 | `df05fbf763d7` |
| `raw/opseval/leaderboard/gtja_zh_mc.csv` | OpsEval raw dataset (gitignored) | active | 1.5 KB | 2026-01-29 10:18:29 | `51c1ac0a5bc8` |
| `raw/opseval/leaderboard/huaweicloud_zh_mc.csv` | OpsEval raw dataset (gitignored) | active | 1.3 KB | 2026-01-29 10:18:29 | `63e0c34fe87b` |
| `raw/opseval/leaderboard/lenovo_en_mc.csv` | OpsEval raw dataset (gitignored) | active | 447 B | 2026-01-29 10:18:29 | `cc9406d58fec` |
| `raw/opseval/leaderboard/lenovo_zh_mc.csv` | OpsEval raw dataset (gitignored) | active | 731 B | 2026-01-29 10:18:29 | `53a2d1a8687e` |
| `raw/opseval/leaderboard/network_en_mc.csv` | OpsEval raw dataset (gitignored) | active | 1.9 KB | 2026-01-29 10:18:29 | `90e458a47bf8` |
| `raw/opseval/leaderboard/network_en_qa.csv` | OpsEval raw dataset (gitignored) | active | 556 B | 2026-01-29 10:18:29 | `e98d54b8233d` |
| `raw/opseval/leaderboard/network_zh_mc.csv` | OpsEval raw dataset (gitignored) | active | 2.0 KB | 2026-01-29 10:18:29 | `a08febc78939` |
| `raw/opseval/leaderboard/network_zh_qa.csv` | OpsEval raw dataset (gitignored) | active | 499 B | 2026-01-29 10:18:29 | `96c51bbe9ebc` |
| `raw/opseval/leaderboard/oracle_en_mc.csv` | OpsEval raw dataset (gitignored) | active | 1.9 KB | 2026-01-29 10:18:29 | `b78751a5d975` |
| `raw/opseval/leaderboard/oracle_zh_mc.csv` | OpsEval raw dataset (gitignored) | active | 1.9 KB | 2026-01-29 10:18:29 | `8b7315497290` |
| `raw/opseval/leaderboard/owl_en_qa.csv` | OpsEval raw dataset (gitignored) | active | 1.6 KB | 2026-01-29 10:18:29 | `a3faee3f46c3` |
| `raw/opseval/leaderboard/owl_zh_qa.csv` | OpsEval raw dataset (gitignored) | active | 1.6 KB | 2026-01-29 10:18:29 | `f3456e49cfa9` |
| `raw/opseval/leaderboard/pufa_zh_mc.csv` | OpsEval raw dataset (gitignored) | active | 1.3 KB | 2026-01-29 10:18:29 | `964a2df9328c` |
| `raw/opseval/leaderboard/rzy_zh_mc.csv` | OpsEval raw dataset (gitignored) | active | 1.5 KB | 2026-01-29 10:18:29 | `e48bd8a57b38` |
| `raw/opseval/leaderboard/rzy_zh_qa.csv` | OpsEval raw dataset (gitignored) | active | 1.6 KB | 2026-01-29 10:18:29 | `77d3a9adb2f0` |
| `raw/opseval/leaderboard/tencent_zh_qa.csv` | OpsEval raw dataset (gitignored) | active | 397 B | 2026-01-29 10:18:29 | `dc9f0c1fe740` |
| `raw/opseval/leaderboard/zabbix_zh_mc.csv` | OpsEval raw dataset (gitignored) | active | 862 B | 2026-01-29 10:18:29 | `012f02734773` |
| `raw/opseval/leaderboard/zabbix_zh_qa.csv` | OpsEval raw dataset (gitignored) | active | 1.6 KB | 2026-01-29 10:18:29 | `89b8dc8675d7` |
| `raw/opseval/leaderboard/zjyd_zh_mc.csv` | OpsEval raw dataset (gitignored) | active | 1.6 KB | 2026-01-29 10:18:29 | `132ac9e04419` |
| `raw/opseval/leaderboard/zjyd_zh_qa.csv` | OpsEval raw dataset (gitignored) | active | 1.6 KB | 2026-01-29 10:18:29 | `4676ad291e7d` |
| `raw/opseval/leaderboard/zte_en_mc.csv` | OpsEval raw dataset (gitignored) | active | 1.6 KB | 2026-01-29 10:18:29 | `27300f9ec00f` |
| `raw/opseval/leaderboard/zte_zh_mc.csv` | OpsEval raw dataset (gitignored) | active | 1.6 KB | 2026-01-29 10:18:29 | `ab301148c25a` |
| `raw/opseval/preprocessing/deduplication.md` | OpsEval raw dataset (gitignored) | active | 369 B | 2026-01-29 10:18:29 | `25e0e66be309` |
| `raw/opseval/preprocessing/dependance_filtering.md` | OpsEval raw dataset (gitignored) | active | 1.1 KB | 2026-01-29 10:18:29 | `28cf56de07a2` |
| `raw/opseval/preprocessing/manual_review.md` | OpsEval raw dataset (gitignored) | active | 683 B | 2026-01-29 10:18:29 | `3f3c39d3a1d9` |
| `raw/opseval/preprocessing/question_categorization.md` | OpsEval raw dataset (gitignored) | active | 1.0 KB | 2026-01-29 10:18:29 | `fc2b2eb94f14` |
| `raw/opseval/prompt/auto_generation.py` | OpsEval raw dataset (gitignored) | active | 399 B | 2026-01-29 10:18:29 | `72505c44844d` |
| `raw/opseval/prompt/gpt4_score.py` | OpsEval raw dataset (gitignored) | active | 294 B | 2026-01-29 10:18:29 | `5608e0adf0c2` |
| `raw/opseval/prompt/gpt_screening.py` | OpsEval raw dataset (gitignored) | active | 492 B | 2026-01-29 10:18:29 | `6c91fc75c464` |
| `raw/opseval_remine_s2.jsonl` | OpsEval re-mining stage-2 output (gitignored) | active | 21.9 KB | 2026-05-13 12:40:32 | `b9396a58173d` |

### §2.intermediate — `intermediate/` (13 files, 1.63 MB)

| Path | Role | Status | Size | Last-modified | SHA-256[:12] |
|---|---|---|---:|---|---|
| `intermediate/README.md` | partition/folder README | active | 2.5 KB | 2026-05-24 19:58:25 | `[unknown - not in 2026-05-20 manifest]` |
| `intermediate/candidates/apache_candidates.jsonl` | mining-stage candidate JSONL | active | 19.5 KB | 2026-05-12 00:18:04 | `268999cfb202` |
| `intermediate/candidates/openssh_candidates.jsonl` | mining-stage candidate JSONL | active | 24.0 KB | 2026-05-12 00:18:41 | `2794d6e92224` |
| `intermediate/candidates/opseval_remine.jsonl` | mining-stage candidate JSONL | active | 28.6 KB | 2026-05-12 00:19:30 | `15d47964b8de` |
| `intermediate/datasets/annotation_clean.json` | canonical benchmark dataset | active | 80.3 KB | 2026-02-01 14:13:54 | `45e41f117d43` |
| `intermediate/datasets/annotation_test.json` | canonical benchmark dataset | active | 106.8 KB | 2026-05-15 13:46:03 | `950f83fb5284` |
| `intermediate/datasets/benchmark_150_seed42.json` | canonical benchmark dataset | active | 111.6 KB | 2026-02-06 16:24:22 | `d2cb5be2414b` |
| `intermediate/datasets/benchmark_150_seed42_with_chinese.json` | canonical benchmark dataset | active | 119.3 KB | 2026-02-06 13:34:53 | `f250b90a5865` |
| `intermediate/datasets/benchmark_400_seed42.json` | canonical benchmark dataset | active | 343.8 KB | 2026-05-13 12:49:32 | `ff8ee1a715ee` |
| `intermediate/datasets/benchmark_431_seed42.json` | canonical benchmark dataset | active | 346.8 KB | 2026-05-13 15:26:41 | `4f2d3c729e46` |
| `intermediate/datasets/excluded_rca_cases.json` | canonical benchmark dataset | active | 9.9 KB | 2026-05-15 15:37:32 | `873ce60c05fd` |
| `intermediate/datasets/rca_clean.json` | canonical benchmark dataset | active | 198.2 KB | 2026-02-01 14:13:54 | `62a3ae0a6f29` |
| `intermediate/datasets/rca_test.json` | canonical benchmark dataset | active | 236.1 KB | 2026-05-15 13:46:03 | `e3b52c28b7e0` |

### §2.final — `final/` (64 files, 7.59 MB)

| Path | Role | Status | Size | Last-modified | SHA-256[:12] |
|---|---|---|---:|---|---|
| `final/AUDIT_REPORT.md` | per-file content audit (23 files) | active | 10.4 KB | 2026-05-19 10:28:13 | `974c95d06d7c` |
| `final/MANIFEST.md` | 47-file FINAL build manifest + SHAs | active | 8.7 KB | 2026-05-24 19:58:25 | `a01d47fc2ff2` |
| `final/README.md` | partition/folder README | active | 2.4 KB | 2026-05-24 19:58:25 | `1b3d51b6cc47` |
| `final/SUMMARY.md` | results landscape + Phase 5 narrative | active | 19.0 KB | 2026-05-24 19:58:24 | `44673886b75d` |
| `final/ablation_v4/README.md` | partition/folder README | active | 632 B | 2026-05-19 10:28:13 | `b1225d94bd34` |
| `final/ablation_v4/ablation_full/results.json` | ablation rich-eval (provenance only — see AUDIT_REPORT) | active | 376.5 KB | 2026-05-17 13:01:09 | `0f3d6863384c` |
| `final/ablation_v4/ablation_full/results_sota_eval_431.json` | ablation matched-eval (Table 6 raw) | active | 319.4 KB | 2026-05-17 13:03:02 | `5b14ddfc90d2` |
| `final/ablation_v4/ablation_full/summary.json` | ablation aggregate (provenance) | active | 767 B | 2026-05-17 13:01:10 | `23e5a0b7b3b5` |
| `final/ablation_v4/ablation_no_constitutional/results.json` | ablation rich-eval (provenance only — see AUDIT_REPORT) | active | 336.4 KB | 2026-05-17 13:01:31 | `f37058ffdc25` |
| `final/ablation_v4/ablation_no_constitutional/results_sota_eval_431.json` | ablation matched-eval (Table 6 raw) | active | 265.2 KB | 2026-05-17 13:03:03 | `3010abd7ac4d` |
| `final/ablation_v4/ablation_no_constitutional/summary.json` | ablation aggregate (provenance) | active | 814 B | 2026-05-17 13:01:32 | `692b27ba2a51` |
| `final/ablation_v4/ablation_no_structured/results.json` | ablation rich-eval (provenance only — see AUDIT_REPORT) | active | 278.4 KB | 2026-05-17 13:01:37 | `c377312601fc` |
| `final/ablation_v4/ablation_no_structured/results_sota_eval_431.json` | ablation matched-eval (Table 6 raw) | active | 207.3 KB | 2026-05-17 13:03:02 | `0299547d52b8` |
| `final/ablation_v4/ablation_no_structured/summary.json` | ablation aggregate (provenance) | active | 805 B | 2026-05-17 13:01:38 | `29eaa5468e7f` |
| `final/ablation_v4/ablation_no_system_prompt/results.json` | ablation rich-eval (provenance only — see AUDIT_REPORT) | active | 335.2 KB | 2026-05-17 13:01:12 | `820155721d62` |
| `final/ablation_v4/ablation_no_system_prompt/results_sota_eval_431.json` | ablation matched-eval (Table 6 raw) | active | 264.1 KB | 2026-05-17 13:03:02 | `93c5341d748c` |
| `final/ablation_v4/ablation_no_system_prompt/summary.json` | ablation aggregate (provenance) | active | 813 B | 2026-05-17 13:01:13 | `85f6e813a3b6` |
| `final/ablation_v4/ablation_single_14b/results.json` | ablation rich-eval (provenance only — see AUDIT_REPORT) | active | 364.7 KB | 2026-05-17 13:01:28 | `10f0853bf521` |
| `final/ablation_v4/ablation_single_14b/results_sota_eval_431.json` | ablation matched-eval (Table 6 raw) | active | 310.3 KB | 2026-05-17 13:03:02 | `a82cb30247b0` |
| `final/ablation_v4/ablation_single_14b/summary.json` | ablation aggregate (provenance) | active | 783 B | 2026-05-17 13:01:29 | `3598939b844f` |
| `final/ablation_v4/ablation_single_4b/results.json` | ablation rich-eval (provenance only — see AUDIT_REPORT) | active | 368.9 KB | 2026-05-17 13:01:19 | `3423147db1cb` |
| `final/ablation_v4/ablation_single_4b/results_sota_eval_431.json` | ablation matched-eval (Table 6 raw) | active | 301.5 KB | 2026-05-17 13:02:40 | `69220454e18d` |
| `final/ablation_v4/ablation_single_4b/summary.json` | ablation aggregate (provenance) | active | 795 B | 2026-05-17 13:01:20 | `7745634df87f` |
| `final/ablation_v4/ablation_with_graph/results.json` | ablation rich-eval (provenance only — see AUDIT_REPORT) | active | 375.9 KB | 2026-05-17 13:01:21 | `6d259c5d7dac` |
| `final/ablation_v4/ablation_with_graph/results_sota_eval_431.json` | ablation matched-eval (Table 6 raw) | active | 317.6 KB | 2026-05-17 13:03:03 | `8317aa973d4e` |
| `final/ablation_v4/ablation_with_graph/summary.json` | ablation aggregate (provenance) | active | 801 B | 2026-05-17 13:01:22 | `2db76adcb51f` |
| `final/ablation_v4/ablation_with_orchestrator/results.json` | ablation rich-eval (provenance only — see AUDIT_REPORT) | active | 376.2 KB | 2026-05-17 13:01:41 | `14307f88a3be` |
| `final/ablation_v4/ablation_with_orchestrator/results_sota_eval_431.json` | ablation matched-eval (Table 6 raw) | active | 317.8 KB | 2026-05-17 13:03:03 | `bd461d11852c` |
| `final/ablation_v4/ablation_with_orchestrator/summary.json` | ablation aggregate (provenance) | active | 826 B | 2026-05-17 13:01:42 | `288c11ff810d` |
| `final/ablation_v4/matched_eval_table.md` | Table 6 matched-eval canonical | active | 1.5 KB | 2026-05-24 19:58:25 | `1e822aa08dde` |
| `final/ablation_v4/phase5_stats.json` | Phase 5 ablation stats | active | 14.8 KB | 2026-05-19 10:51:00 | `691d329df265` |
| `final/ablation_v4/phase5_stats.md` | Phase 5 ablation stats | active | 4.3 KB | 2026-05-24 19:58:25 | `4d55ce42c64a` |
| `final/audit/CV_PASS1_DISCREPANCIES.md` | cross-validation pass (sealed forensic) | sealed-forensic | 23.1 KB | 2026-05-20 09:27:57 | `fbf63c6165cb` |
| `final/audit/CV_PASS2_CODEBASE_AUDIT.md` | cross-validation pass (sealed forensic) | sealed-forensic | 63.8 KB | 2026-05-20 09:42:41 | `c67a0a365d91` |
| `final/audit/FULL_TRANSCRIPT_AUDIT.md` | sessions 1–11 transcript forensic audit | sealed-forensic | 223.3 KB | 2026-05-20 09:59:22 | `f3cfc16435ad` |
| `final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json` | pre-zip SHA-256 manifest (493 files, 2026-05-20) | sealed-forensic | 98.7 KB | 2026-05-24 20:01:50 | `[unknown - not in 2026-05-20 manifest]` |
| `final/audit/REORG_PROPOSAL_2026-05-20.md` | 2026-05-20 4-partition reorg plan | sealed-forensic | 11.1 KB | 2026-05-20 10:10:01 | `[unknown - not in 2026-05-20 manifest]` |
| `final/audit/SESSION_12_HANDOFF.md` | session handoff doc | sealed-forensic | 13.9 KB | 2026-05-20 15:34:32 | `[unknown - not in 2026-05-20 manifest]` |
| `final/audit/SESSION_13_HANDOFF.md` | session handoff doc | sealed-forensic | 13.8 KB | 2026-05-24 20:02:07 | `[unknown - not in 2026-05-20 manifest]` |
| `final/audit/SESSION_14_HANDOFF.md` | session handoff doc | sealed-forensic | 26.1 KB | 2026-05-24 20:39:43 | `[unknown - not in 2026-05-20 manifest]` |
| `final/audit/SESSION_15_HANDOFF.md` | session handoff doc | sealed-forensic | 26.4 KB | 2026-05-24 21:29:46 | `[unknown - not in 2026-05-20 manifest]` |
| `final/docs/BROKEN_ABLATIONS.md` | active runbook / methodology doc | active | 3.1 KB | 2026-05-16 01:18:31 | `b24e2e3c125a` |
| `final/docs/BUG_HISTORY.md` | active runbook / methodology doc | active | 13.0 KB | 2026-05-24 19:55:19 | `1474cf09fc86` |
| `final/docs/CURRENT_RUNS.md` | active runbook / methodology doc | active | 8.9 KB | 2026-05-24 19:56:11 | `b1571b2e54b1` |
| `final/docs/METHODOLOGY.md` | active runbook / methodology doc | active | 17.1 KB | 2026-05-24 19:55:58 | `82a17e826d10` |
| `final/docs/_archived_session_history/FILE_PROVENANCE.md` | session 9 historical doc (sealed) | sealed-forensic | 9.8 KB | 2026-05-19 10:45:25 | `8190e023697a` |
| `final/docs/_archived_session_history/RESULTS_SUMMARY.md` | session 9 historical doc (sealed) | sealed-forensic | 6.0 KB | 2026-05-19 10:46:12 | `1cec8db35f3d` |
| `final/docs/_archived_session_history/RUNS_INDEX.md` | session 9 historical doc (sealed) | sealed-forensic | 9.8 KB | 2026-05-19 10:46:01 | `a3615dcc960e` |
| `final/infrastructure/gate15_comparison.md` | dual-stack gate evidence (§3) | active | 1.0 KB | 2026-05-13 12:29:20 | `83706a84e4e8` |
| `final/main_benchmark/README.md` | partition/folder README | active | 8.1 KB | 2026-05-24 19:58:25 | `fd128c7c645a` |
| `final/main_benchmark/benchmark_result.json` | runner.py aggregate (provenance) | active | 1.2 KB | 2026-05-16 13:10:31 | `b56253786917` |
| `final/main_benchmark/paper_tables.md` | README / paper-table doc | active | 2.3 KB | 2026-05-16 13:10:36 | `0282e70f593e` |
| `final/main_benchmark/paper_tables.tex` | paper-table LaTeX | active | 3.0 KB | 2026-05-16 13:10:30 | `c2ad34a7f9c5` |
| `final/main_benchmark/phase5_stats.json` | Phase 5 stats (main re-run) | active | 894 B | 2026-05-19 10:51:00 | `c21d0c145f2e` |
| `final/main_benchmark/results.json` | Table 2 rich-eval source | active | 429.9 KB | 2026-05-16 13:10:35 | `d712850bed54` |
| `final/main_benchmark/results_sota_eval_431.json` | Table 2 matched-eval source | active | 320.2 KB | 2026-05-16 13:11:01 | `5a2c38300f2b` |
| `final/main_benchmark/summary.json` | runner.py aggregate (provenance) | active | 1.2 KB | 2026-05-16 13:10:37 | `b56253786917` |
| `final/phase46_no_prompt/README.md` | partition/folder README | active | 5.0 KB | 2026-05-24 19:58:25 | `1b9ca9a0e45b` |
| `final/phase46_no_prompt/deepseek_noprompt_v2.jsonl` | no-prompt baseline JSONL (Table 8) | active | 328.1 KB | 2026-05-16 10:38:58 | `b19f9943b7a7` |
| `final/phase46_no_prompt/llama_noprompt_clean.jsonl` | no-prompt baseline JSONL (Table 8) | active | 322.9 KB | 2026-05-16 10:38:12 | `aaf5d7cdf80c` |
| `final/sota_baselines/deepseek_v3.jsonl` | SOTA baseline JSONL (Table 7) | active | 182.0 KB | 2026-05-16 10:33:00 | `b003589dfa64` |
| `final/sota_baselines/drain.jsonl` | SOTA baseline JSONL (Table 7) | active | 38.9 KB | 2026-05-15 15:02:26 | `64850478676e` |
| `final/sota_baselines/drain_summary.json` | SOTA baseline JSONL (Table 7) | active | 339 B | 2026-05-15 15:02:26 | `d6de47525816` |
| `final/sota_baselines/llama_3_3_70b.jsonl` | SOTA baseline JSONL (Table 7) | active | 196.0 KB | 2026-05-16 10:34:11 | `ed468f8fbe0b` |

### §2.archive — `archive/` (203 files, 21.32 MB)

| Path | Role | Status | Size | Last-modified | SHA-256[:12] |
|---|---|---|---:|---|---|
| `archive/README.md` | partition/folder README | active | 3.3 KB | 2026-05-20 15:33:02 | `[unknown - not in 2026-05-20 manifest]` |
| `archive/aiops_archive_2026-05-17.tar.gz` | instance-side session-10 tarball backup | historical | 5.75 MB | 2026-05-17 13:07:22 | `351aa6734b30` |
| `archive/originals_2026-05-19/_ARCHIVED.md` | archive notice / reorg note | historical | 2.0 KB | 2026-05-19 10:42:47 | `cacd1a34e873` |
| `archive/originals_2026-05-19/_REORG_NOTE_2026-05-20.md` | archive notice / reorg note | historical | 1.3 KB | 2026-05-20 15:33:05 | `[unknown - not in 2026-05-20 manifest]` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/_ARCHIVED_NOTICE.md` | archive notice / reorg note | historical | 516 B | 2026-05-19 10:42:47 | `9a519b9987c9` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_full/benchmark_result.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 767 B | 2026-05-17 13:01:07 | `23e5a0b7b3b5` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_full/results.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 376.5 KB | 2026-05-17 13:01:09 | `0f3d6863384c` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_full/results_sota_eval_431.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 319.4 KB | 2026-05-17 13:03:02 | `5b14ddfc90d2` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_full/summary.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 767 B | 2026-05-17 13:01:10 | `23e5a0b7b3b5` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_no_constitutional/benchmark_result.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 814 B | 2026-05-17 13:01:29 | `692b27ba2a51` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_no_constitutional/results.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 336.4 KB | 2026-05-17 13:01:31 | `f37058ffdc25` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_no_constitutional/results_sota_eval_431.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 265.2 KB | 2026-05-17 13:03:03 | `3010abd7ac4d` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_no_constitutional/summary.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 814 B | 2026-05-17 13:01:32 | `692b27ba2a51` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_no_structured/benchmark_result.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 805 B | 2026-05-17 13:01:35 | `29eaa5468e7f` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_no_structured/results.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 278.4 KB | 2026-05-17 13:01:37 | `c377312601fc` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_no_structured/results_sota_eval_431.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 207.3 KB | 2026-05-17 13:03:02 | `0299547d52b8` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_no_structured/summary.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 805 B | 2026-05-17 13:01:38 | `29eaa5468e7f` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_no_system_prompt/benchmark_result.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 813 B | 2026-05-17 13:01:10 | `85f6e813a3b6` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_no_system_prompt/results.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 335.2 KB | 2026-05-17 13:01:12 | `820155721d62` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_no_system_prompt/results_sota_eval_431.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 264.1 KB | 2026-05-17 13:03:02 | `93c5341d748c` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_no_system_prompt/summary.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 813 B | 2026-05-17 13:01:13 | `85f6e813a3b6` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_results.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 6.9 KB | 2026-05-17 13:01:23 | `4b9e4c9600f5` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_single_14b/benchmark_result.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 783 B | 2026-05-17 13:01:26 | `3598939b844f` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_single_14b/results.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 364.7 KB | 2026-05-17 13:01:28 | `10f0853bf521` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_single_14b/results_sota_eval_431.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 310.3 KB | 2026-05-17 13:03:02 | `a82cb30247b0` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_single_14b/summary.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 783 B | 2026-05-17 13:01:29 | `3598939b844f` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_single_4b/benchmark_result.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 795 B | 2026-05-17 13:01:16 | `7745634df87f` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_single_4b/results.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 368.9 KB | 2026-05-17 13:01:19 | `3423147db1cb` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_single_4b/results_sota_eval_431.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 301.5 KB | 2026-05-17 13:02:40 | `69220454e18d` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_single_4b/summary.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 795 B | 2026-05-17 13:01:20 | `7745634df87f` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_table.md` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 1.3 KB | 2026-05-17 13:01:12 | `e5a2aa0d8b20` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_table.tex` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 1.2 KB | 2026-05-17 13:01:17 | `cfc606095309` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_with_graph/benchmark_result.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 801 B | 2026-05-17 13:01:19 | `2db76adcb51f` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_with_graph/results.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 375.9 KB | 2026-05-17 13:01:21 | `6d259c5d7dac` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_with_graph/results_sota_eval_431.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 317.6 KB | 2026-05-17 13:03:03 | `8317aa973d4e` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_with_graph/summary.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 801 B | 2026-05-17 13:01:22 | `2db76adcb51f` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_with_orchestrator/benchmark_result.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 826 B | 2026-05-17 13:01:38 | `288c11ff810d` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_with_orchestrator/results.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 376.2 KB | 2026-05-17 13:01:41 | `14307f88a3be` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_with_orchestrator/results_sota_eval_431.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 317.8 KB | 2026-05-17 13:03:03 | `bd461d11852c` |
| `archive/originals_2026-05-19/ablation_v4_newprompt/ablation_with_orchestrator/summary.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 826 B | 2026-05-17 13:01:42 | `288c11ff810d` |
| `archive/originals_2026-05-19/phase46_noprompt/README.md` | partition/folder README | active | 4.9 KB | 2026-05-16 01:18:07 | `1b9ca9a0e45b` |
| `archive/originals_2026-05-19/phase46_noprompt/_ARCHIVED_NOTICE.md` | archive notice / reorg note | historical | 517 B | 2026-05-19 10:42:47 | `480d88e8f344` |
| `archive/originals_2026-05-19/phase46_noprompt/deepseek_noprompt.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 384.2 KB | 2026-05-15 16:14:49 | `fb3e3cd8d105` |
| `archive/originals_2026-05-19/phase46_noprompt/deepseek_noprompt_to431.log` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 3.3 KB | 2026-05-16 10:38:58 | `176c42126024` |
| `archive/originals_2026-05-19/phase46_noprompt/deepseek_noprompt_v2.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 328.1 KB | 2026-05-16 10:38:58 | `b19f9943b7a7` |
| `archive/originals_2026-05-19/phase46_noprompt/deepseek_noprompt_v2_t0_BAK.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 301.7 KB | 2026-05-15 16:46:45 | `10335b070c12` |
| `archive/originals_2026-05-19/phase46_noprompt/deepseek_v2.log` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 23.3 KB | 2026-05-15 16:46:45 | `72b478959d75` |
| `archive/originals_2026-05-19/phase46_noprompt/deepseek_v2_t005.log` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 23.5 KB | 2026-05-16 10:16:30 | `42757fa64504` |
| `archive/originals_2026-05-19/phase46_noprompt/llama_clean.log` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 23.3 KB | 2026-05-16 00:35:39 | `ee38843bb487` |
| `archive/originals_2026-05-19/phase46_noprompt/llama_clean_t005.log` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 26.0 KB | 2026-05-16 10:20:59 | `c61244ac18e3` |
| `archive/originals_2026-05-19/phase46_noprompt/llama_noprompt_bak.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 118.3 KB | 2026-05-15 15:23:28 | `c61c7bd0d707` |
| `archive/originals_2026-05-19/phase46_noprompt/llama_noprompt_clean.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 322.9 KB | 2026-05-16 10:38:12 | `aaf5d7cdf80c` |
| `archive/originals_2026-05-19/phase46_noprompt/llama_noprompt_clean_t0_BAK.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 295.7 KB | 2026-05-16 00:35:39 | `10c54607ffbd` |
| `archive/originals_2026-05-19/phase46_noprompt/llama_noprompt_final_bak.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 386.0 KB | 2026-05-15 15:56:40 | `cea16aba29ee` |
| `archive/originals_2026-05-19/phase46_noprompt/llama_noprompt_rescored_bak.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 109.0 KB | 2026-05-15 15:19:24 | `ccec1593dc15` |
| `archive/originals_2026-05-19/phase46_noprompt/llama_noprompt_to431.log` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 3.5 KB | 2026-05-16 10:38:12 | `6f949175f6b9` |
| `archive/originals_2026-05-19/phase46_noprompt/llama_noprompt_v2.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 461.7 KB | 2026-05-15 17:02:08 | `23895f20db95` |
| `archive/originals_2026-05-19/phase46_noprompt/llama_v2.log` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 24.7 KB | 2026-05-15 17:02:08 | `43f4aac474fc` |
| `archive/originals_2026-05-19/run_stackA_main431_newprompt/README.md` | partition/folder README | active | 8.0 KB | 2026-05-16 13:18:02 | `fd128c7c645a` |
| `archive/originals_2026-05-19/run_stackA_main431_newprompt/_ARCHIVED_NOTICE.md` | archive notice / reorg note | historical | 526 B | 2026-05-19 10:42:47 | `1b87c7323f3d` |
| `archive/originals_2026-05-19/run_stackA_main431_newprompt/benchmark_result.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 1.2 KB | 2026-05-16 13:10:31 | `b56253786917` |
| `archive/originals_2026-05-19/run_stackA_main431_newprompt/paper_tables.md` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 2.3 KB | 2026-05-16 13:10:36 | `0282e70f593e` |
| `archive/originals_2026-05-19/run_stackA_main431_newprompt/paper_tables.tex` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 3.0 KB | 2026-05-16 13:10:30 | `c2ad34a7f9c5` |
| `archive/originals_2026-05-19/run_stackA_main431_newprompt/results.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 429.9 KB | 2026-05-16 13:10:35 | `d712850bed54` |
| `archive/originals_2026-05-19/run_stackA_main431_newprompt/results_sota_eval_431.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 320.2 KB | 2026-05-16 13:11:01 | `5a2c38300f2b` |
| `archive/originals_2026-05-19/run_stackA_main431_newprompt/summary.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 1.2 KB | 2026-05-16 13:10:37 | `b56253786917` |
| `archive/originals_2026-05-19/sota_deepseek_v3/_ARCHIVED_NOTICE.md` | archive notice / reorg note | historical | 531 B | 2026-05-19 10:42:47 | `9ab618bd5bc6` |
| `archive/originals_2026-05-19/sota_deepseek_v3/results.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 182.0 KB | 2026-05-16 10:33:00 | `b003589dfa64` |
| `archive/originals_2026-05-19/sota_deepseek_v3/results_t0_BAK.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 249.9 KB | 2026-05-15 13:25:53 | `fa87bb465a78` |
| `archive/originals_2026-05-19/sota_deepseek_v3/run_t005.log` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 23.3 KB | 2026-05-16 09:43:28 | `3f6d2aab3709` |
| `archive/originals_2026-05-19/sota_deepseek_v3/run_to431.log` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 3.3 KB | 2026-05-16 10:33:00 | `e4a13275a093` |
| `archive/originals_2026-05-19/sota_drain/_ARCHIVED_NOTICE.md` | archive notice / reorg note | historical | 540 B | 2026-05-19 10:42:47 | `f93c7458acf9` |
| `archive/originals_2026-05-19/sota_drain/results.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 38.9 KB | 2026-05-15 15:02:26 | `64850478676e` |
| `archive/originals_2026-05-19/sota_drain/summary.json` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 339 B | 2026-05-15 15:02:26 | `d6de47525816` |
| `archive/originals_2026-05-19/sota_llama_3_3_70b/_ARCHIVED_NOTICE.md` | archive notice / reorg note | historical | 535 B | 2026-05-19 10:42:47 | `250261928dd9` |
| `archive/originals_2026-05-19/sota_llama_3_3_70b/results.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 196.0 KB | 2026-05-16 10:34:11 | `ed468f8fbe0b` |
| `archive/originals_2026-05-19/sota_llama_3_3_70b/results_t0_BAK.jsonl` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 204.3 KB | 2026-05-13 17:05:56 | `ddb6680a85ec` |
| `archive/originals_2026-05-19/sota_llama_3_3_70b/run_t005.log` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 27.1 KB | 2026-05-16 10:25:43 | `7f53f5f06b21` |
| `archive/originals_2026-05-19/sota_llama_3_3_70b/run_to431.log` | originals snapshot (sessions 10–11, pre-FINAL build) | historical | 3.3 KB | 2026-05-16 10:34:11 | `00aab65ae5d4` |
| `archive/originals_backup_2026-05-19.zip` | defense-in-depth zip of originals_2026-05-19/ | historical | 1.70 MB | 2026-05-19 10:42:47 | `b48fb2b7b07f` |
| `archive/rerun_remine33_enriched/results.json` | partial re-run after L5614 enrichment fix | historical | 38.4 KB | 2026-05-13 15:47:40 | `b9e514a8ef5a` |
| `archive/run_stackA_main431_OLD_PROMPT/all_tables.md` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 3.0 KB | 2026-05-13 16:12:22 | `b37f0ba42f6c` |
| `archive/run_stackA_main431_OLD_PROMPT/all_tables.tex` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 2.9 KB | 2026-05-13 15:02:46 | `278ae5703657` |
| `archive/run_stackA_main431_OLD_PROMPT/benchmark.log` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 133.0 KB | 2026-05-13 15:02:53 | `3e88822c13dc` |
| `archive/run_stackA_main431_OLD_PROMPT/benchmark_result.json` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 1.2 KB | 2026-05-13 15:02:48 | `3a11a65e05f7` |
| `archive/run_stackA_main431_OLD_PROMPT/combined_results.md` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 966 B | 2026-05-13 16:26:49 | `43ea6b3d9759` |
| `archive/run_stackA_main431_OLD_PROMPT/manifest.json` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 295 B | 2026-05-13 15:02:55 | `8b7ef6171ddf` |
| `archive/run_stackA_main431_OLD_PROMPT/paper_tables.md` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 2.6 KB | 2026-05-13 16:26:23 | `a751d605d900` |
| `archive/run_stackA_main431_OLD_PROMPT/paper_tables.tex` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 3.0 KB | 2026-05-13 15:02:47 | `aae741b548dd` |
| `archive/run_stackA_main431_OLD_PROMPT/results.json` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 396.6 KB | 2026-05-13 15:02:52 | `dfbdfc91d101` |
| `archive/run_stackA_main431_OLD_PROMPT/results_merged.json` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 421.0 KB | 2026-05-13 16:11:25 | `4f40a792d7b6` |
| `archive/run_stackA_main431_OLD_PROMPT/results_merged_enriched.json` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 421.0 KB | 2026-05-13 16:10:57 | `4f40a792d7b6` |
| `archive/run_stackA_main431_OLD_PROMPT/results_sota_eval_431.json` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 295.4 KB | 2026-05-16 10:37:03 | `abac48bb4e26` |
| `archive/run_stackA_main431_OLD_PROMPT/run.log` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 133.8 KB | 2026-05-13 15:02:50 | `c3160232e179` |
| `archive/run_stackA_main431_OLD_PROMPT/summary.json` | main run with OLD RCA prompt (pre-fix; v1-paper anchor) | historical | 1.2 KB | 2026-05-13 15:02:58 | `3a11a65e05f7` |
| `archive/smoke_tests/run_stackA_15plus15/all_tables.md` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 1.5 KB | 2026-05-13 15:02:26 | `98ce1bdbd0c4` |
| `archive/smoke_tests/run_stackA_15plus15/all_tables.tex` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 2.1 KB | 2026-05-13 15:02:27 | `930a8e915083` |
| `archive/smoke_tests/run_stackA_15plus15/benchmark.log` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 12.0 KB | 2026-05-13 15:02:34 | `6fff5b405f99` |
| `archive/smoke_tests/run_stackA_15plus15/benchmark_result.json` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 1.2 KB | 2026-05-13 15:02:29 | `768889401f2f` |
| `archive/smoke_tests/run_stackA_15plus15/combined_results.md` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 512 B | 2026-05-13 15:02:35 | `80284d30815f` |
| `archive/smoke_tests/run_stackA_15plus15/manifest.json` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 258 B | 2026-05-13 15:02:36 | `f45a2acfc661` |
| `archive/smoke_tests/run_stackA_15plus15/paper_tables.md` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 1.5 KB | 2026-05-13 15:02:37 | `3957d5b7007b` |
| `archive/smoke_tests/run_stackA_15plus15/paper_tables.tex` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 2.2 KB | 2026-05-13 15:02:28 | `dc2642e3a93c` |
| `archive/smoke_tests/run_stackA_15plus15/results.json` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 28.5 KB | 2026-05-13 15:02:32 | `b0e66716da83` |
| `archive/smoke_tests/run_stackA_15plus15/run.log` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 12.9 KB | 2026-05-13 15:02:31 | `48f2d10ea077` |
| `archive/smoke_tests/run_stackA_15plus15/summary.json` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 1.2 KB | 2026-05-13 15:02:39 | `768889401f2f` |
| `archive/smoke_tests/run_stackA_5plus5_oninstance/manifest.json` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 572 B | 2026-05-13 15:02:41 | `774f0503b681` |
| `archive/smoke_tests/run_stackB_15plus15/all_tables.md` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 1.4 KB | 2026-05-13 15:03:01 | `d6a3f45d6a00` |
| `archive/smoke_tests/run_stackB_15plus15/benchmark.log` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 11.7 KB | 2026-05-13 15:03:05 | `a3fee82ffa7c` |
| `archive/smoke_tests/run_stackB_15plus15/manifest.json` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 782 B | 2026-05-13 15:03:06 | `a00560a3e5c7` |
| `archive/smoke_tests/run_stackB_15plus15/paper_tables.md` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 1.4 KB | 2026-05-13 15:03:07 | `ce808a725f79` |
| `archive/smoke_tests/run_stackB_15plus15/paper_tables.tex` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 2.1 KB | 2026-05-13 15:03:02 | `7dfd489bcb61` |
| `archive/smoke_tests/run_stackB_15plus15/results.json` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 27.9 KB | 2026-05-13 15:03:03 | `025cd0b804e1` |
| `archive/smoke_tests/run_stackB_15plus15/summary.json` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 1.2 KB | 2026-05-13 15:03:08 | `2262030ae519` |
| `archive/smoke_tests/run_stackB_5plus5_v1_bad/benchmark.log` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 5.7 KB | 2026-05-13 15:03:11 | `12ddd26f3c1a` |
| `archive/smoke_tests/run_stackB_5plus5_v1_bad/manifest.json` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 381 B | 2026-05-13 15:03:12 | `a5db78bb7f85` |
| `archive/smoke_tests/run_stackB_5plus5_v2/benchmark.log` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 5.7 KB | 2026-05-13 15:03:18 | `f4682fc64f7b` |
| `archive/smoke_tests/run_stackB_5plus5_v2/manifest.json` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 609 B | 2026-05-13 15:03:19 | `21d4d585d5fc` |
| `archive/smoke_tests/run_stackB_5plus5_v2/paper_tables.md` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 1.3 KB | 2026-05-13 15:03:20 | `8be268829784` |
| `archive/smoke_tests/run_stackB_5plus5_v2/paper_tables.tex` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 2.0 KB | 2026-05-13 15:03:15 | `001cc38d7895` |
| `archive/smoke_tests/run_stackB_5plus5_v2/results.json` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 9.3 KB | 2026-05-13 15:03:17 | `0a2e7d89e0ea` |
| `archive/smoke_tests/run_stackB_5plus5_v2/summary.json` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 1.2 KB | 2026-05-13 15:03:21 | `44291aa98f4f` |
| `archive/smoke_tests/sota_smoke_deepseek/results.jsonl` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 2.3 KB | 2026-05-13 14:21:18 | `889b6aa7a843` |
| `archive/smoke_tests/sota_smoke_deepseek_v2/results.jsonl` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 2.5 KB | 2026-05-13 14:26:21 | `3a751d680cf0` |
| `archive/smoke_tests/sota_smoke_llama/results.jsonl` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 2.3 KB | 2026-05-13 14:26:55 | `cab85e7b3228` |
| `archive/smoke_tests/stackB_15plus15.log` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 11.7 KB | 2026-05-13 15:03:23 | `a3fee82ffa7c` |
| `archive/smoke_tests/stackB_awqmarlin_5plus5_v2.log` | 5+5 / 15+15 dual-stack smoke runs (sessions 2–4) | historical | 5.7 KB | 2026-05-13 15:03:24 | `f4682fc64f7b` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/FINDINGS.md` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 7.7 KB | 2026-02-10 20:03:53 | `8f45adcb69c4` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/FINDINGS.pdf` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 76.2 KB | 2026-02-10 20:03:53 | `498d81fc5a4c` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_full/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 770 B | 2026-02-10 20:03:53 | `e710a5fa0aaf` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_full/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 119.4 KB | 2026-02-10 20:03:53 | `2037d4dd4f16` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_full/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 770 B | 2026-02-10 20:03:53 | `e710a5fa0aaf` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_no_structured/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 807 B | 2026-02-10 20:03:53 | `94bce4954f45` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_no_structured/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 119.4 KB | 2026-02-10 20:03:53 | `bf2f9a789fe9` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_no_structured/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 807 B | 2026-02-10 20:03:53 | `94bce4954f45` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 3.4 KB | 2026-02-10 20:03:53 | `11d0cd61949e` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_single_14b/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 786 B | 2026-02-10 20:03:53 | `1d46201e7403` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_single_14b/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 118.6 KB | 2026-02-10 20:03:53 | `9572524b4905` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_single_14b/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 786 B | 2026-02-10 20:03:53 | `1d46201e7403` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_single_4b/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 799 B | 2026-02-10 20:03:53 | `5addc7fd4d3a` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_single_4b/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 119.8 KB | 2026-02-10 20:03:53 | `a5fd0f3dfcd9` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/ablation_single_4b/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 799 B | 2026-02-10 20:03:53 | `5addc7fd4d3a` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/all_tables.md` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 2.5 KB | 2026-02-10 20:03:53 | `7ed756680c79` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/all_tables.pdf` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 61.8 KB | 2026-02-10 20:03:53 | `0e21dd968962` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/all_tables.tex` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 3.2 KB | 2026-02-10 20:03:53 | `c7965beb4bc1` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/constitutional_aiops/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.2 KB | 2026-02-10 20:03:53 | `a8891904d999` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/constitutional_aiops/paper_tables.md` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.7 KB | 2026-02-10 20:03:53 | `da763b27000b` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/constitutional_aiops/paper_tables.tex` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 2.4 KB | 2026-02-10 20:03:53 | `59d0a76b3996` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/constitutional_aiops/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 139.1 KB | 2026-02-10 20:03:53 | `4958cf07b0f3` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/constitutional_aiops/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.2 KB | 2026-02-10 20:03:53 | `a8891904d999` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/paper_tables.tex` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 2.4 KB | 2026-02-10 20:03:53 | `59d0a76b3996` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/reports/all_tables.tex` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.2 KB | 2026-02-05 11:52:41 | `f40029d69038` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/reports/benchmark_results.csv` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 280 B | 2026-02-05 11:52:41 | `06d222760393` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/reports/benchmark_results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 405 B | 2026-02-05 11:52:41 | `fec2da9b5931` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/reports/paper_tables.md` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 2.0 KB | 2026-02-05 11:52:41 | `ab2317d2af12` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/reports/paper_tables_unified.tex` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 4.1 KB | 2026-02-05 11:52:41 | `dc62392975f9` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/reports/table_accuracy.tex` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 356 B | 2026-02-05 11:52:41 | `84f10982755f` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/reports/table_latency.tex` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 378 B | 2026-02-05 11:52:41 | `7bddd7e8efd1` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/reports/table_llm_comparison.tex` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 408 B | 2026-02-05 11:52:41 | `d12109b337a9` |
| `archive/v0.9.1_jarvis_baseline/2026-02-06_v0.9.1/results_index.md` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.2 KB | 2026-02-10 20:03:53 | `4ab4fe595b8e` |
| `archive/v0.9.1_jarvis_baseline/FINDINGS.md` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 15.6 KB | 2026-02-10 22:41:18 | `c7077efe3ae4` |
| `archive/v0.9.1_jarvis_baseline/FINDINGS.pdf` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 106.8 KB | 2026-02-10 23:12:43 | `96c3ff427d15` |
| `archive/v0.9.1_jarvis_baseline/ablation_full.log` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 16.8 KB | 2026-02-10 20:02:59 | `615b8320b1a9` |
| `archive/v0.9.1_jarvis_baseline/ablation_full/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 769 B | 2026-02-10 20:02:58 | `f6371631ed02` |
| `archive/v0.9.1_jarvis_baseline/ablation_full/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 119.4 KB | 2026-02-10 20:02:58 | `821912aa2b1e` |
| `archive/v0.9.1_jarvis_baseline/ablation_full/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 769 B | 2026-02-10 20:02:58 | `f6371631ed02` |
| `archive/v0.9.1_jarvis_baseline/ablation_no_constitutional/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 817 B | 2026-02-10 20:03:06 | `91b280da9f9a` |
| `archive/v0.9.1_jarvis_baseline/ablation_no_constitutional/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 119.5 KB | 2026-02-10 20:03:05 | `6fbfd5463cf7` |
| `archive/v0.9.1_jarvis_baseline/ablation_no_constitutional/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 817 B | 2026-02-10 20:03:05 | `91b280da9f9a` |
| `archive/v0.9.1_jarvis_baseline/ablation_no_structured/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 808 B | 2026-02-10 20:02:59 | `24b1f06cd6d5` |
| `archive/v0.9.1_jarvis_baseline/ablation_no_structured/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 119.4 KB | 2026-02-10 20:02:59 | `37c25930c435` |
| `archive/v0.9.1_jarvis_baseline/ablation_no_structured/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 808 B | 2026-02-10 20:02:59 | `24b1f06cd6d5` |
| `archive/v0.9.1_jarvis_baseline/ablation_no_system_prompt/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 814 B | 2026-02-10 20:03:04 | `88606f240238` |
| `archive/v0.9.1_jarvis_baseline/ablation_no_system_prompt/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 106.0 KB | 2026-02-10 20:03:04 | `234ad42e5a9a` |
| `archive/v0.9.1_jarvis_baseline/ablation_no_system_prompt/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 814 B | 2026-02-10 20:03:04 | `88606f240238` |
| `archive/v0.9.1_jarvis_baseline/ablation_results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 6.0 KB | 2026-02-10 20:03:00 | `fe939c564141` |
| `archive/v0.9.1_jarvis_baseline/ablation_single_14b/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 785 B | 2026-02-10 20:03:00 | `8cd2083e13eb` |
| `archive/v0.9.1_jarvis_baseline/ablation_single_14b/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 118.7 KB | 2026-02-10 20:03:00 | `16657553ad68` |
| `archive/v0.9.1_jarvis_baseline/ablation_single_14b/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 785 B | 2026-02-10 20:03:00 | `8cd2083e13eb` |
| `archive/v0.9.1_jarvis_baseline/ablation_single_4b/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 798 B | 2026-02-10 20:03:01 | `91a13d6885aa` |
| `archive/v0.9.1_jarvis_baseline/ablation_single_4b/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 119.8 KB | 2026-02-10 20:03:01 | `3d63bf0ba05c` |
| `archive/v0.9.1_jarvis_baseline/ablation_single_4b/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 798 B | 2026-02-10 20:03:01 | `91a13d6885aa` |
| `archive/v0.9.1_jarvis_baseline/ablation_table.md` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.2 KB | 2026-02-10 20:03:06 | `b51b5760a27d` |
| `archive/v0.9.1_jarvis_baseline/ablation_table.pdf` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 46.8 KB | 2026-02-10 23:10:59 | `6465dbbf9631` |
| `archive/v0.9.1_jarvis_baseline/ablation_table.tex` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.0 KB | 2026-02-10 20:03:06 | `d6b5b1b3e80f` |
| `archive/v0.9.1_jarvis_baseline/ablation_with_graph/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 805 B | 2026-02-10 20:03:05 | `d367dff3e8ca` |
| `archive/v0.9.1_jarvis_baseline/ablation_with_graph/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 119.6 KB | 2026-02-10 20:03:05 | `fd9d71a3e051` |
| `archive/v0.9.1_jarvis_baseline/ablation_with_graph/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 805 B | 2026-02-10 20:03:05 | `d367dff3e8ca` |
| `archive/v0.9.1_jarvis_baseline/all_tables.md` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 2.9 KB | 2026-05-15 13:46:03 | `b57228a2b982` |
| `archive/v0.9.1_jarvis_baseline/all_tables.pdf` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 71.6 KB | 2026-02-10 23:11:54 | `6f73cde48df6` |
| `archive/v0.9.1_jarvis_baseline/all_tables.tex` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 3.5 KB | 2026-05-15 13:46:03 | `f0d5f409ce24` |
| `archive/v0.9.1_jarvis_baseline/benchmark_full.log` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 50.3 KB | 2026-02-10 20:03:01 | `2a214d85c832` |
| `archive/v0.9.1_jarvis_baseline/combined_results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.3 KB | 2026-05-15 13:46:03 | `3200423982d9` |
| `archive/v0.9.1_jarvis_baseline/combined_results.md` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 513 B | 2026-05-15 13:46:03 | `53fbfe6e3ab7` |
| `archive/v0.9.1_jarvis_baseline/constitutional_aiops/benchmark_result.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.2 KB | 2026-05-15 13:46:03 | `860a21253b19` |
| `archive/v0.9.1_jarvis_baseline/constitutional_aiops/paper_tables.md` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.7 KB | 2026-05-15 13:46:03 | `f0607e3f1482` |
| `archive/v0.9.1_jarvis_baseline/constitutional_aiops/paper_tables.pdf` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 69.4 KB | 2026-02-10 23:08:49 | `c139a15c6894` |
| `archive/v0.9.1_jarvis_baseline/constitutional_aiops/paper_tables.tex` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 2.3 KB | 2026-05-15 13:46:03 | `8e20b2801d52` |
| `archive/v0.9.1_jarvis_baseline/constitutional_aiops/results.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 139.1 KB | 2026-05-15 13:46:03 | `2dbfa44047a3` |
| `archive/v0.9.1_jarvis_baseline/constitutional_aiops/summary.json` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.2 KB | 2026-05-15 13:46:03 | `860a21253b19` |
| `archive/v0.9.1_jarvis_baseline/paper_tables.md` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.7 KB | 2026-05-15 13:46:03 | `f0607e3f1482` |
| `archive/v0.9.1_jarvis_baseline/paper_tables.tex` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 2.3 KB | 2026-05-15 13:46:03 | `8e20b2801d52` |
| `archive/v0.9.1_jarvis_baseline/results_index.md` | Jarvis Labs A5000 v1 baseline (Feb 2026) | historical | 1.5 KB | 2026-05-15 13:46:03 | `e2cd497932cf` |

### §2.scripts — `scripts/` (40 files, 427.9 KB)

| Path | Role | Status | Size | Last-modified | SHA-256[:12] |
|---|---|---|---:|---|---|
| `scripts/README.md` | partition/folder README | active | 13.2 KB | 2026-05-24 20:00:00 | `[unknown - not in 2026-05-20 manifest]` |
| `scripts/__init__.py` | package marker | active | 28 B | 2026-01-28 23:50:20 | `19dab35a4118` |
| `scripts/_dev/__init__.py` | package marker | active | 1 B | 2026-05-20 15:43:08 | `19dab35a4118` |
| `scripts/_dev/create_nothink_model.py` | smoke / debug / dev script | historical | 8.3 KB | 2026-05-24 19:53:19 | `c17c350bd084` |
| `scripts/_dev/debug_connection.py` | smoke / debug / dev script | dev | 13.0 KB | 2026-05-24 19:53:19 | `b45a03d65e11` |
| `scripts/_dev/demo_test.py` | smoke / debug / dev script | dev | 5.1 KB | 2026-05-24 19:53:19 | `07322b8c2402` |
| `scripts/_dev/smoke_knowledge_query.py` | smoke / debug / dev script | dev | 3.6 KB | 2026-05-24 19:53:19 | `707370e9b23b` |
| `scripts/_dev/test_instruct.py` | smoke / debug / dev script | dev | 9.5 KB | 2026-05-24 19:53:19 | `0a61d6e9493a` |
| `scripts/eval/__init__.py` | package marker | active | 1 B | 2026-05-20 15:43:08 | `19dab35a4118` |
| `scripts/eval/compile_results.py` | eval / scoring / stats script | active | 5.8 KB | 2026-05-24 19:53:19 | `cd4a142ebbdd` |
| `scripts/eval/compute_semantic_metrics.py` | eval / scoring / stats script | active | 7.3 KB | 2026-05-24 19:53:19 | `55fbbc83ce95` |
| `scripts/eval/evaluate_results.py` | eval / scoring / stats script | historical | 8.9 KB | 2026-05-24 19:53:19 | `302886652cac` |
| `scripts/eval/export_metrics.py` | eval / scoring / stats script | active | 22.1 KB | 2026-05-24 19:53:19 | `ef108bb4d583` |
| `scripts/eval/inspect_all_configs.py` | eval / scoring / stats script | active | 4.2 KB | 2026-05-24 19:42:16 | `87e36eed4847` |
| `scripts/eval/inspect_single4b.py` | eval / scoring / stats script | historical | 1.6 KB | 2026-05-17 13:02:07 | `28a47d76eacd` |
| `scripts/eval/phase5_stats.py` | eval / scoring / stats script | active | 13.2 KB | 2026-05-24 19:53:19 | `22a15f435ed6` |
| `scripts/eval/rescore_ours_with_sota_eval.py` | eval / scoring / stats script | active | 8.0 KB | 2026-05-24 19:53:19 | `b6647bcdfbda` |
| `scripts/eval/verify_authoritative_numbers.py` | eval / scoring / stats script | active | 4.8 KB | 2026-05-24 19:42:16 | `e7f3a6aaca61` |
| `scripts/ops/__init__.py` | package marker | active | 1 B | 2026-05-20 15:43:08 | `19dab35a4118` |
| `scripts/ops/archive_originals.py` | build / archive / e2e utility | historical | 13.6 KB | 2026-05-24 19:42:16 | `dec928b550cc` |
| `scripts/ops/build_final_results.py` | build / archive / e2e utility | historical | 25.0 KB | 2026-05-24 19:53:19 | `f8c44f3cdb96` |
| `scripts/ops/e2e_tests.py` | build / archive / e2e utility | active | 9.0 KB | 2026-05-24 19:53:19 | `318781f07af5` |
| `scripts/ops/master_backup_manifest.py` | build / archive / e2e utility | active | 1.4 KB | 2026-05-20 15:32:05 | `e6b9b5df5576` |
| `scripts/prep/__init__.py` | package marker | active | 1 B | 2026-05-20 15:43:08 | `19dab35a4118` |
| `scripts/prep/clean_dataset.py` | dataset prep / mining script | active | 9.3 KB | 2026-05-24 19:53:19 | `76e99adaf3ba` |
| `scripts/prep/download_datasets.py` | dataset prep / mining script | active | 26.9 KB | 2026-05-24 19:53:19 | `782d8676218a` |
| `scripts/prep/fix_benchmark_dataset.py` | dataset prep / mining script | historical | 2.3 KB | 2026-05-24 19:45:12 | `04aeea268dfd` |
| `scripts/prep/mine_apache.py` | dataset prep / mining script | active | 6.1 KB | 2026-05-24 19:53:19 | `a6a4fdfe484f` |
| `scripts/prep/mine_openssh.py` | dataset prep / mining script | active | 6.9 KB | 2026-05-24 19:53:19 | `67cf070703b1` |
| `scripts/prep/mine_opseval.py` | dataset prep / mining script | active | 13.5 KB | 2026-05-24 19:53:19 | `452640b4b887` |
| `scripts/prep/prepare_datasets.py` | dataset prep / mining script | active | 60.7 KB | 2026-05-24 19:53:19 | `1cace8dd1c54` |
| `scripts/prep/remove_chinese.py` | dataset prep / mining script | historical | 4.9 KB | 2026-05-24 19:45:12 | `b6058aaa9f15` |
| `scripts/prep/vet_labels.py` | dataset prep / mining script | active | 12.9 KB | 2026-05-24 19:53:19 | `2822248b08e6` |
| `scripts/run/__init__.py` | package marker | active | 1 B | 2026-05-20 15:43:08 | `19dab35a4118` |
| `scripts/run/run_ablation.py` | benchmark runner script | active | 18.0 KB | 2026-05-24 19:53:19 | `ee84321be8a7` |
| `scripts/run/run_benchmark.py` | benchmark runner script | active | 30.4 KB | 2026-05-24 19:53:19 | `16c1d05c9ef0` |
| `scripts/run/run_drain_baseline.py` | benchmark runner script | active | 8.7 KB | 2026-05-24 19:53:19 | `78b0ebdee47a` |
| `scripts/run/run_graph_experiments.py` | benchmark runner script | active | 10.9 KB | 2026-05-24 19:53:19 | `46c7499d27a2` |
| `scripts/run/run_sota_baselines.py` | benchmark runner script | active | 22.5 KB | 2026-05-24 19:53:19 | `40a7f4a20c48` |
| `scripts/run/test_5plus5.py` | benchmark runner script | active | 16.2 KB | 2026-05-24 19:53:19 | `b90548d4e489` |

### §2.other — `other/` (2 files, 408 B)

| Path | Role | Status | Size | Last-modified | SHA-256[:12] |
|---|---|---|---:|---|---|
| `.benchmark_step2_complete` | benchmark step-2 sentinel | historical | 0 B | 2026-05-13 12:43:21 | `e3b0c44298fc` |
| `.progress.json` | benchmark progress marker | historical | 408 B | 2026-05-13 12:43:21 | `ada6bdf12a3b` |

## §3 Delta vs 2026-05-20 baseline

Baseline = `MASTER_BACKUP_MANIFEST_2026-05-20.json` (493 entries, full filesystem) + `CV_PASS2_CODEBASE_AUDIT.md` Part B (491 git-tracked entries). The 2-file gap between the two baselines reflects 2 files that were on disk but not git-tracked at 2026-05-20 (`.benchmark_step2_complete` and `.progress.json`).

### §3.1 Added since baseline (file in current tree, not in baseline)

| Path | Size | Role / guess |
|---|---:|---|
| `archive/README.md` | 3.3 KB | partition/folder README |
| `archive/originals_2026-05-19/_REORG_NOTE_2026-05-20.md` | 1.3 KB | archive notice / reorg note |
| `final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json` | 98.7 KB | pre-zip SHA-256 manifest (493 files, 2026-05-20) |
| `final/audit/REORG_PROPOSAL_2026-05-20.md` | 11.1 KB | 2026-05-20 4-partition reorg plan |
| `final/audit/SESSION_12_HANDOFF.md` | 13.9 KB | session handoff doc |
| `final/audit/SESSION_13_HANDOFF.md` | 13.8 KB | session handoff doc |
| `final/audit/SESSION_14_HANDOFF.md` | 26.1 KB | session handoff doc |
| `final/audit/SESSION_15_HANDOFF.md` | 26.4 KB | session handoff doc |
| `intermediate/README.md` | 2.5 KB | partition/folder README |
| `raw/README.md` | 1.6 KB | partition/folder README |
| `scripts/README.md` | 13.2 KB | partition/folder README |

**Total added: 11 files.** All are documentation / metadata: 5 partition READMEs created during the 2026-05-20 reorg, 4 session handoffs (SESSION_12-15), the reorg proposal, the reorg note in originals/, and the MASTER_BACKUP_MANIFEST itself (which was generated AT 2026-05-20 and so appears in its own contents only as a post-baseline artifact).

### §3.2 Deleted since baseline (in baseline, not in current tree)

| Path (baseline) | Last-known SHA-256[:12] | Size | Reason / replacement |
|---|---|---:|---|
| `benchmark/results_aws/FILE_PROVENANCE.md` | `8190e023697a` | 9.8 KB | moved → `final/docs/_archived_session_history/FILE_PROVENANCE.md` |
| `benchmark/results_aws/FINAL/BUG_HISTORY.md` | `1474cf09fc86` | 13.0 KB | deduplicated; canonical at `final/docs/BUG_HISTORY.md` |
| `benchmark/results_aws/FINAL/METHODOLOGY.md` | `82a17e826d10` | 17.1 KB | deduplicated; canonical at `final/docs/METHODOLOGY.md` |
| `benchmark/results_aws/RESULTS_SUMMARY.md` | `1cec8db35f3d` | 6.0 KB | moved → `final/docs/_archived_session_history/RESULTS_SUMMARY.md` |
| `benchmark/results_aws/RUNS_INDEX.md` | `a3615dcc960e` | 9.8 KB | moved → `final/docs/_archived_session_history/RUNS_INDEX.md` |
| `benchmark/scripts/__pycache__/__init__.cpython-312.pyc` | `461d375ca54a` | 189 B | build artifact (Python `__pycache__/*.pyc`) — not needed in source tree |
| `benchmark/scripts/__pycache__/download_datasets.cpython-312.pyc` | `e1d0ab27b42d` | 31.2 KB | build artifact (Python `__pycache__/*.pyc`) — not needed in source tree |
| `benchmark/scripts/__pycache__/export_metrics.cpython-311.pyc` | `2497200db528` | 25.6 KB | build artifact (Python `__pycache__/*.pyc`) — not needed in source tree |
| `benchmark/scripts/__pycache__/export_metrics.cpython-312.pyc` | `c612d8fc0058` | 31.6 KB | build artifact (Python `__pycache__/*.pyc`) — not needed in source tree |
| `benchmark/scripts/__pycache__/prepare_datasets.cpython-312.pyc` | `e6e56f7f1784` | 59.7 KB | build artifact (Python `__pycache__/*.pyc`) — not needed in source tree |
| `benchmark/scripts/__pycache__/run_ablation.cpython-311.pyc` | `a4c365550b96` | 21.2 KB | build artifact (Python `__pycache__/*.pyc`) — not needed in source tree |
| `benchmark/scripts/__pycache__/run_sota_baselines.cpython-312.pyc` | `26c44d8732a5` | 27.6 KB | build artifact (Python `__pycache__/*.pyc`) — not needed in source tree |
| `benchmark/scripts/__pycache__/test_5plus5.cpython-311.pyc` | `7a7446b20e8b` | 23.8 KB | build artifact (Python `__pycache__/*.pyc`) — not needed in source tree |

**Total deleted: 13 files.** Breakdown: 5 documentation files were moved/deduplicated under the 4-partition reorg (locations preserved or content unchanged), and 8 are Python bytecode files (`__pycache__/*.pyc`) that should not be in the source tree.

### §3.3 Possibly modified (same path-mapping, mtime newer than 2026-05-20)

`mtime > 2026-05-20` means the file has been touched on disk since the manifest was generated. This does NOT prove content change — `touch` updates mtime without changing content. To detect actual content drift, re-run `python benchmark/scripts/ops/master_backup_manifest.py` and diff the new SHA-256 against the baseline. Files below either had content changes during sessions 13–15, or were re-touched by a build/move operation.

| Path | Baseline SHA-256[:12] | Current mtime |
|---|---|---|
| `final/MANIFEST.md` | `a01d47fc2ff2` | 2026-05-24 19:58:25 |
| `final/README.md` | `1b3d51b6cc47` | 2026-05-24 19:58:25 |
| `final/SUMMARY.md` | `44673886b75d` | 2026-05-24 19:58:24 |
| `final/ablation_v4/matched_eval_table.md` | `1e822aa08dde` | 2026-05-24 19:58:25 |
| `final/ablation_v4/phase5_stats.md` | `4d55ce42c64a` | 2026-05-24 19:58:25 |
| `final/docs/BUG_HISTORY.md` | `1474cf09fc86` | 2026-05-24 19:55:19 |
| `final/docs/CURRENT_RUNS.md` | `b1571b2e54b1` | 2026-05-24 19:56:11 |
| `final/docs/METHODOLOGY.md` | `82a17e826d10` | 2026-05-24 19:55:58 |
| `final/main_benchmark/README.md` | `fd128c7c645a` | 2026-05-24 19:58:25 |
| `final/phase46_no_prompt/README.md` | `1b9ca9a0e45b` | 2026-05-24 19:58:25 |
| `scripts/_dev/create_nothink_model.py` | `c17c350bd084` | 2026-05-24 19:53:19 |
| `scripts/_dev/debug_connection.py` | `b45a03d65e11` | 2026-05-24 19:53:19 |
| `scripts/_dev/demo_test.py` | `07322b8c2402` | 2026-05-24 19:53:19 |
| `scripts/_dev/smoke_knowledge_query.py` | `707370e9b23b` | 2026-05-24 19:53:19 |
| `scripts/_dev/test_instruct.py` | `0a61d6e9493a` | 2026-05-24 19:53:19 |
| `scripts/eval/compile_results.py` | `cd4a142ebbdd` | 2026-05-24 19:53:19 |
| `scripts/eval/compute_semantic_metrics.py` | `55fbbc83ce95` | 2026-05-24 19:53:19 |
| `scripts/eval/evaluate_results.py` | `302886652cac` | 2026-05-24 19:53:19 |
| `scripts/eval/export_metrics.py` | `ef108bb4d583` | 2026-05-24 19:53:19 |
| `scripts/eval/inspect_all_configs.py` | `87e36eed4847` | 2026-05-24 19:42:16 |
| `scripts/eval/phase5_stats.py` | `22a15f435ed6` | 2026-05-24 19:53:19 |
| `scripts/eval/rescore_ours_with_sota_eval.py` | `b6647bcdfbda` | 2026-05-24 19:53:19 |
| `scripts/eval/verify_authoritative_numbers.py` | `e7f3a6aaca61` | 2026-05-24 19:42:16 |
| `scripts/ops/archive_originals.py` | `dec928b550cc` | 2026-05-24 19:42:16 |
| `scripts/ops/build_final_results.py` | `f8c44f3cdb96` | 2026-05-24 19:53:19 |
| `scripts/ops/e2e_tests.py` | `318781f07af5` | 2026-05-24 19:53:19 |
| `scripts/prep/clean_dataset.py` | `76e99adaf3ba` | 2026-05-24 19:53:19 |
| `scripts/prep/download_datasets.py` | `782d8676218a` | 2026-05-24 19:53:19 |
| `scripts/prep/fix_benchmark_dataset.py` | `04aeea268dfd` | 2026-05-24 19:45:12 |
| `scripts/prep/mine_apache.py` | `a6a4fdfe484f` | 2026-05-24 19:53:19 |
| `scripts/prep/mine_openssh.py` | `67cf070703b1` | 2026-05-24 19:53:19 |
| `scripts/prep/mine_opseval.py` | `452640b4b887` | 2026-05-24 19:53:19 |
| `scripts/prep/prepare_datasets.py` | `1cace8dd1c54` | 2026-05-24 19:53:19 |
| `scripts/prep/remove_chinese.py` | `b6058aaa9f15` | 2026-05-24 19:45:12 |
| `scripts/prep/vet_labels.py` | `2822248b08e6` | 2026-05-24 19:53:19 |
| `scripts/run/run_ablation.py` | `ee84321be8a7` | 2026-05-24 19:53:19 |
| `scripts/run/run_benchmark.py` | `16c1d05c9ef0` | 2026-05-24 19:53:19 |
| `scripts/run/run_drain_baseline.py` | `78b0ebdee47a` | 2026-05-24 19:53:19 |
| `scripts/run/run_graph_experiments.py` | `46c7499d27a2` | 2026-05-24 19:53:19 |
| `scripts/run/run_sota_baselines.py` | `40a7f4a20c48` | 2026-05-24 19:53:19 |
| `scripts/run/test_5plus5.py` | `b90548d4e489` | 2026-05-24 19:53:19 |

**Total possibly-modified: 41 files.** Most are in `final/` (docs + ablation_v4/main_benchmark READMEs touched during the session-14 Stage J reflow + matched_eval_table regen) or `scripts/` (sub-folder moves on 2026-05-20 + session-14 source-of-truth re-touches).

## §4 Cross-references

- For per-file SHA-256 of paper-evidence files in `final/` (47 files at FINAL build time): see [`final/MANIFEST.md`](final/MANIFEST.md)
- For per-file content audit of `final/` (record counts, missing fields, BERT-zero scan): see [`final/AUDIT_REPORT.md`](final/AUDIT_REPORT.md)
- For 34-script breakdown by sub-folder (`prep/run/eval/ops/_dev`): see [`scripts/README.md`](scripts/README.md)
- For canonical results landscape + Phase 5 statistics: see [`final/SUMMARY.md`](final/SUMMARY.md)
- For forensic per-file metadata as of 2026-05-20 (491 git-tracked files with first-add/last-modify commits + flags): see [`final/audit/CV_PASS2_CODEBASE_AUDIT.md`](final/audit/CV_PASS2_CODEBASE_AUDIT.md) Part B
- For pre-zip SHA-256 manifest of every file at 2026-05-20 (493 files): see [`final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json`](final/audit/MASTER_BACKUP_MANIFEST_2026-05-20.json)
- For the 4-partition reorg plan + rationale: see [`final/audit/REORG_PROPOSAL_2026-05-20.md`](final/audit/REORG_PROPOSAL_2026-05-20.md)
- For session-by-session handoff docs: see [`final/audit/SESSION_12_HANDOFF.md`](final/audit/SESSION_12_HANDOFF.md), [`13`](final/audit/SESSION_13_HANDOFF.md), [`14`](final/audit/SESSION_14_HANDOFF.md), [`15`](final/audit/SESSION_15_HANDOFF.md)
- For runbook / methodology / bug history: see [`final/docs/METHODOLOGY.md`](final/docs/METHODOLOGY.md), [`BUG_HISTORY.md`](final/docs/BUG_HISTORY.md), [`BROKEN_ABLATIONS.md`](final/docs/BROKEN_ABLATIONS.md), [`CURRENT_RUNS.md`](final/docs/CURRENT_RUNS.md)

## §5 Memory-update suggestion

Suggested addition to `C:/Users/partha/.claude/projects/c--Users-partha-Downloads-files-AIOPS-NEW/memory/MEMORY.md` under "Hard pointers (updated 2026-05-20 - POST-REORG + POST-SUB-FOLDER paths)":

```markdown
- **Master `benchmark/` index** (canonical entry-point as of 2026-05-25): `benchmark/INDEX.md` - 422-file index with per-file role/status/SHA/mtime, partition tally, delta-vs-2026-05-20-baseline. Regenerate whenever files are added/removed/moved under `benchmark/`.
```
