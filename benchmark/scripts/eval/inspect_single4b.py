#!/usr/bin/env python3
"""Inspect single_4b ablation results to verify 99.1% RCA accuracy."""
import json
import random
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/mnt/aiops-repo/benchmark/results/ablation_single_4b/results.json"

with open(path, encoding="utf-8") as f:
    d = json.load(f)

ann = [r for r in d if r.get("task_type") == "annotation"]
rca = [r for r in d if r.get("task_type") == "rca"]
ann_ok = sum(1 for r in ann if r.get("correct"))
rca_ok = sum(1 for r in rca if r.get("correct"))
print(f"Total: {len(d)} | Ann: {ann_ok}/{len(ann)} | RCA: {rca_ok}/{len(rca)}")

wrong_rca = [r for r in rca if not r.get("correct")]
print(f"\nRCA WRONG cases ({len(wrong_rca)}):")
for r in wrong_rca:
    tid = r.get("test_id")
    exp = str(r.get("expected_output"))[:150]
    act = str(r.get("actual_output"))[:200]
    rs = r.get("rule_score")
    to = r.get("term_overlap")
    cs = r.get("cosine_similarity")
    print(f"  {tid}")
    print(f"    expected: {exp}")
    print(f"    actual:   {act}")
    print(f"    rule_score: {rs}  term_overlap: {to}  cosine: {cs}")

right_rca = [r for r in rca if r.get("correct")]
random.seed(42)
print(f"\nSample of 8 CORRECT RCA cases (sanity check):")
for r in random.sample(right_rca, 8):
    tid = r.get("test_id")
    exp = str(r.get("expected_output"))[:120]
    act = str(r.get("actual_output"))[:200]
    rs = r.get("rule_score")
    to = r.get("term_overlap")
    cs = r.get("cosine_similarity")
    print(f"  {tid}")
    print(f"    expected: {exp}")
    print(f"    actual:   {act}")
    print(f"    rule_score: {rs}  term_overlap: {to}  cosine: {cs}")
