# Ablation v4 — final

**For paper Table 6**: use `matched_eval_table.md` (computed from each config's
`results_sota_eval_431.json`).

**Per-config files**:
- `ablation_<cfg>/results.json` — raw model outputs + runner.py rich-eval flags
  (provenance; rich-eval `correct` flag is **broken** in 7 of 8 configs — see
  `../AUDIT_REPORT.md` for the audit; do NOT cite rich-eval RCA accuracies)
- `ablation_<cfg>/results_sota_eval_431.json` — re-scored with SOTA strict-substring
  matched eval (**AUTHORITATIVE for Table 6**)
- `ablation_<cfg>/summary.json` — runner.py aggregate (rich eval), kept for provenance
