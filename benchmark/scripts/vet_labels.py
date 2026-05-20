#!/usr/bin/env python3
"""benchmark/scripts/vet_labels.py — two-LLM-judge label vetting pipeline.

Used after mine_apache.py / mine_openssh.py / mine_opseval.py / mine_logeval.py
produce candidate cases. This script asks two independent LLM judges
(GPT-4o-mini + Claude Haiku/Sonnet) whether each candidate's gold label is
correct. Output splits into:

  Tier 0 (auto-accept):  both judges agree with original_label AND min_conf >= 0.70
  Tier 1 (human review): judges disagree OR min_conf < 0.70
  Tier 2 (sample audit): 20% random sample of Tier 0 (human spot-check)

Typical yield: ~80% Tier 0, ~15% Tier 1, ~5% Tier 2 audit → ~90 min human time
for 200-300 candidates.

Cost: ~$3 in API for 300 candidates (mostly Haiku/mini tiers).

Usage:
    export OPENAI_API_KEY=sk-...
    export ANTHROPIC_API_KEY=sk-ant-...
    python benchmark/scripts/vet_labels.py \\
        --in benchmark/intermediate/candidates/apache_candidates.jsonl \\
        --in benchmark/intermediate/candidates/openssh_candidates.jsonl \\
        --in benchmark/intermediate/candidates/opseval_remine.jsonl \\
        --out-dir benchmark/intermediate/candidates/vetted/

Without API keys: writes everything into Tier 1 (human review queue) — still
a useful manual-review pipeline, just no automatic culling.
"""

from __future__ import annotations
import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Optional

VETTING_SYSTEM_PROMPT = """You are an expert SRE label-quality auditor. \
You are given a benchmark case for an AIOps system, along with its proposed \
gold-truth label. Your job is to decide whether the label is CORRECT.

Respond with ONLY a JSON object on a single line:
{"label_ok": <true|false>, "confidence": <0.0-1.0>, "reason": "<one-sentence>"}

Be strict but realistic. If a log says "Connection reset by peer" and the label \
says anomaly=true, that's correct (genuine error). If a log says "INFO Started \
NameNode" and label says anomaly=true, that's WRONG. Empty input or non-log text \
should NOT be flagged as anomaly."""


def load_candidates(paths: list[Path]) -> list[dict]:
    cases = []
    for p in paths:
        if not p.exists():
            print(f"WARN: {p} not found, skipping", file=sys.stderr)
            continue
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    cases.append(json.loads(line))
    return cases


def case_summary_for_judge(case: dict) -> str:
    """Render a case into a compact prompt for the judge LLM."""
    parts = [f"task_type: {case.get('task_type', '?')}"]
    if case.get("task_type") == "annotation":
        inp = case.get("input", {})
        parts.append(f"telemetry_type: {inp.get('telemetry_type', '?')}")
        parts.append(f"content: {inp.get('content', '')[:500]}")
        parts.append(f"context: {inp.get('context', '')[:300]}")
        exp = case.get("expected", {})
        parts.append(f"proposed_label: anomaly_detected={exp.get('anomaly_detected')}, "
                     f"severity={exp.get('severity')}, category={exp.get('category')}")
    elif case.get("task_type") == "rca":
        inc = case.get("incident", {})
        q = inc.get("question") or "\n".join(inc.get("logs", [])[:5])
        parts.append(f"incident: {q[:800]}")
        parts.append(f"proposed_root_cause: {case.get('expected_root_cause', '')[:300]}")
    return "\n".join(parts)


def judge_openai(case_text: str) -> Optional[dict]:
    """Returns {'label_ok': bool, 'confidence': float, 'reason': str} or None on failure."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": VETTING_SYSTEM_PROMPT},
                {"role": "user", "content": case_text},
            ],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception as e:
        print(f"  WARN openai judge failed: {e}", file=sys.stderr)
        return None


def judge_anthropic(case_text: str) -> Optional[dict]:
    """Returns same shape as judge_openai, or None on failure."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic  # type: ignore
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            temperature=0.0,
            system=VETTING_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": case_text}],
        )
        # Claude returns text; parse first JSON object
        text = msg.content[0].text if msg.content else "{}"
        # Find first {...} block
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        return None
    except Exception as e:
        print(f"  WARN anthropic judge failed: {e}", file=sys.stderr)
        return None


# --- Bedrock judges (preferred per 2026-05-12 lock-in: consolidates billing on AWS) ---

_BEDROCK_CLIENT = None


def _get_bedrock_client():
    global _BEDROCK_CLIENT
    if _BEDROCK_CLIENT is None:
        try:
            import boto3  # type: ignore
            _BEDROCK_CLIENT = boto3.client(
                "bedrock-runtime",
                region_name=os.environ.get("AWS_REGION", "us-east-1"),
            )
        except Exception as e:
            print(f"  WARN bedrock client init failed: {e}", file=sys.stderr)
            _BEDROCK_CLIENT = False
    return _BEDROCK_CLIENT or None


def _extract_first_json(text: str) -> Optional[dict]:
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return None
    return None


def judge_bedrock_haiku(case_text: str) -> Optional[dict]:
    """Haiku 4.5 via inference profile (anthropic native format)."""
    client = _get_bedrock_client()
    if client is None:
        return None
    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "temperature": 0.0,
            "system": VETTING_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": case_text}],
        })
        resp = client.invoke_model(
            modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        out = json.loads(resp["body"].read())
        text = out["content"][0]["text"] if out.get("content") else ""
        return _extract_first_json(text)
    except Exception as e:
        print(f"  WARN bedrock haiku judge failed: {e}", file=sys.stderr)
        return None


def judge_bedrock_deepseek(case_text: str) -> Optional[dict]:
    """DeepSeek V3.2 direct (OpenAI-compatible format)."""
    client = _get_bedrock_client()
    if client is None:
        return None
    try:
        body = json.dumps({
            "messages": [
                {"role": "system", "content": VETTING_SYSTEM_PROMPT},
                {"role": "user", "content": case_text},
            ],
            "max_tokens": 200,
            "temperature": 0.0,
        })
        resp = client.invoke_model(
            modelId="deepseek.v3.2",
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        out = json.loads(resp["body"].read())
        text = out["choices"][0]["message"]["content"] if out.get("choices") else ""
        return _extract_first_json(text)
    except Exception as e:
        print(f"  WARN bedrock deepseek judge failed: {e}", file=sys.stderr)
        return None


def vet_one(case: dict) -> dict:
    """Run both judges and decide the tier. Returns case enriched with vetting metadata.

    Backend preference: Bedrock (Haiku 4.5 + DeepSeek V3.2) when AWS creds present;
    falls back to OpenAI + Anthropic direct SDKs when only API keys are present.
    Lockdown 2026-05-12: Bedrock is the production path; direct SDKs kept for offline dev only.
    """
    case_text = case_summary_for_judge(case)

    use_bedrock = bool(
        os.environ.get("AWS_PROFILE")
        or os.environ.get("AWS_ACCESS_KEY_ID")
        or os.environ.get("AWS_DEFAULT_PROFILE")
    )

    if use_bedrock:
        j_a = judge_bedrock_haiku(case_text)
        j_b = judge_bedrock_deepseek(case_text)
        backend = "bedrock"
    else:
        j_a = judge_openai(case_text)
        j_b = judge_anthropic(case_text)
        backend = "direct_sdk"

    verdicts = [j for j in (j_a, j_b) if j is not None]
    case["_vetting"] = {
        "judge_a": j_a,
        "judge_b": j_b,
        "n_judges": len(verdicts),
        "backend": backend,
    }

    if not verdicts:
        # No judges available — everything goes to manual review
        case["_vetting"]["tier"] = 1
        case["_vetting"]["decision"] = "manual_review_no_judges"
        return case

    # All judges agree label is OK + min confidence high
    all_ok = all(j.get("label_ok") is True for j in verdicts)
    min_conf = min(float(j.get("confidence", 0.0)) for j in verdicts)

    if all_ok and min_conf >= 0.70:
        case["_vetting"]["tier"] = 0
        case["_vetting"]["decision"] = "auto_accept"
    elif not all_ok:
        case["_vetting"]["tier"] = 1
        case["_vetting"]["decision"] = "manual_review_disagree"
    else:
        case["_vetting"]["tier"] = 1
        case["_vetting"]["decision"] = "manual_review_low_confidence"

    return case


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="inputs", action="append", required=True, type=Path,
                    help="Input candidates JSONL file. Pass --in multiple times.")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--audit-fraction", type=float, default=0.20,
                    help="Fraction of Tier-0 to random-sample into Tier-2 audit")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    cases = load_candidates(args.inputs)
    print(f"[vet_labels] loaded {len(cases)} candidates from {len(args.inputs)} files")

    # Sanity check key availability
    have_openai = bool(os.environ.get("OPENAI_API_KEY"))
    have_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    print(f"  OPENAI_API_KEY: {'present' if have_openai else 'MISSING'}")
    print(f"  ANTHROPIC_API_KEY: {'present' if have_anthropic else 'MISSING'}")
    if not (have_openai or have_anthropic):
        print("WARN: no API keys — all candidates will route to Tier 1 (manual review)")

    # Vet each
    args.out_dir.mkdir(parents=True, exist_ok=True)
    tier0, tier1 = [], []
    for i, case in enumerate(cases):
        vetted = vet_one(case)
        tier = vetted["_vetting"]["tier"]
        if tier == 0:
            tier0.append(vetted)
        else:
            tier1.append(vetted)
        if (i + 1) % 25 == 0:
            print(f"  vetted {i+1}/{len(cases)} (T0={len(tier0)} T1={len(tier1)})")

    # Tier 2 sample
    rng = random.Random(args.seed)
    n_audit = max(1, int(round(args.audit_fraction * len(tier0))))
    rng.shuffle(tier0)
    tier2 = tier0[:n_audit]
    tier0_remaining = tier0[n_audit:]

    # Write outputs
    def write_jsonl(name: str, items: list[dict]) -> None:
        path = args.out_dir / f"{name}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")
        print(f"  wrote {path} ({len(items)})")

    write_jsonl("tier0_auto_accept", tier0_remaining)
    write_jsonl("tier1_needs_review", tier1)
    write_jsonl("tier2_audit_sample", tier2)

    print(f"\n[vet_labels] summary:")
    print(f"  Tier 0 (auto-accept):         {len(tier0_remaining)}")
    print(f"  Tier 1 (needs human review):  {len(tier1)}")
    print(f"  Tier 2 (audit sample of T0):  {len(tier2)}")
    print(f"  Total:                        {len(cases)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
