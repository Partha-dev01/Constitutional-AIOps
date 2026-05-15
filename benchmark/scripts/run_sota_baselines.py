#!/usr/bin/env python3
"""benchmark/scripts/run_sota_baselines.py — Phase 4.7 SOTA baseline runner.

Runs single-model monolith baselines on benchmark_400_seed42.json using
AWS Bedrock. Produces per-case JSONL with the same fields as test_5plus5.py
so compare_stacks.py / Phase 5 bootstrap CI scripts can consume them directly.

Supported models:
  deepseek-r1   — us.deepseek.r1-v1:0  (open-weight reasoning frontier)
  llama-3.3-70b — us.meta.llama3-3-70b-instruct-v1:0  (open-weight frontier)

Evaluation (fair single-model criteria):
  Annotation CORRECT if model predicts anomaly_detected matching expected AND/OR
    severity matching expected (score >= 1.0 / 2.0 primary criteria).
  RCA CORRECT if expected_root_cause (or any acceptable_answer) appears
    case-insensitively in the model's free-text response.

Usage:
    python benchmark/scripts/run_sota_baselines.py --model deepseek-r1 \\
        --dataset benchmark/datasets/processed/benchmark_400_seed42.json \\
        --out benchmark/results_aws/sota_deepseek_r1/results.jsonl

    python benchmark/scripts/run_sota_baselines.py --model llama-3.3-70b \\
        --dataset benchmark/datasets/processed/benchmark_400_seed42.json \\
        --out benchmark/results_aws/sota_llama_3_3_70b/results.jsonl
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# ── Model configs ────────────────────────────────────────────────────────────

MODELS = {
    "deepseek-r1": {
        "bedrock_id": "us.deepseek.r1-v1:0",
        "display": "DeepSeek-R1",
        "format": "deepseek",
        # R1 generates a thinking trace before the answer; 2048 ensures the
        # trace + JSON answer fit within the output budget.
        "max_tokens_ann": 2048,
        "max_tokens_rca": 2048,
        # Strict rate limit on Bedrock — 1 RPM observed in practice.
        "inter_request_delay_s": 12,
    },
    "deepseek-v3": {
        "bedrock_id": "deepseek.v3.2",
        "display": "DeepSeek-V3.2",
        "format": "deepseek-v3",
        "max_tokens_ann": 512,
        "max_tokens_rca": 1024,
        "inter_request_delay_s": 2,
    },
    "llama-3.3-70b": {
        "bedrock_id": "us.meta.llama3-3-70b-instruct-v1:0",
        "display": "Llama-3.3-70B",
        "format": "llama3",
        "max_tokens_ann": 256,
        "max_tokens_rca": 512,
        "inter_request_delay_s": 1,
    },
}

# ── Prompts ──────────────────────────────────────────────────────────────────

_ANN_SYSTEM = (
    "You are an IT operations monitoring expert. "
    "Classify the given telemetry log entry. "
    "Respond ONLY with a JSON object with these exact keys: "
    '{"anomaly_detected": <true|false>, "severity": "<info|warning|error|critical>", '
    '"category": "<normal|error|performance|security|resource>"}. '
    "No explanation, no markdown, JSON only."
)

_RCA_SYSTEM = (
    "You are an IT operations root cause analysis expert. "
    "Given the incident description or logs, identify the most likely root cause. "
    "Be concise and specific. State the root cause in 1-2 sentences."
)


def _build_prompt(fmt: str, system: str, user: str) -> str:
    if fmt == "deepseek":
        # Plain text System/User format — special tokens like <|System|> are not
        # part of R1's vocabulary and produce empty completions.
        return f"<|begin_of_sentence|>System: {system}\n\nUser: {user}\n\nAssistant:"
    if fmt == "deepseek-v3":
        # DeepSeek V3.2 on Bedrock uses converse-style messages API
        # We pass the prompt as a plain combined string (system + user)
        return f"System: {system}\n\nUser: {user}\n\nAssistant:"
    if fmt == "llama3":
        return (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system}\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n{user}\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )
    raise ValueError(f"Unknown format: {fmt}")


# ── Bedrock call ─────────────────────────────────────────────────────────────

def _call_bedrock(client, model_cfg: dict, prompt: str, max_tokens: int, system: str = "", user: str = "") -> tuple[str, float]:
    """Returns (text, latency_ms). Retries on throttling with exponential backoff."""
    fmt = model_cfg["format"]
    if fmt == "deepseek":
        body = json.dumps({"prompt": prompt, "max_tokens": max_tokens, "temperature": 0.0})
    elif fmt == "deepseek-v3":
        # DeepSeek V3.2 on Bedrock uses OpenAI-compatible messages API (not prompt field)
        body = json.dumps({
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.0,
        })
    elif fmt == "llama3":
        body = json.dumps({"prompt": prompt, "max_gen_len": max_tokens, "temperature": 0.0})
    else:
        raise ValueError(fmt)

    for attempt in range(5):
        try:
            t0 = time.perf_counter()
            resp = client.invoke_model(
                modelId=model_cfg["bedrock_id"],
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            latency_ms = (time.perf_counter() - t0) * 1000
            raw = json.loads(resp["body"].read())
            break
        except Exception as e:
            if "ThrottlingException" in str(e) and attempt < 4:
                wait = 15 * (2 ** attempt)
                print(f"    [throttle] waiting {wait}s (attempt {attempt+1}/5)...")
                time.sleep(wait)
            else:
                raise

    if fmt == "deepseek":
        text = raw.get("choices", [{}])[0].get("text", "")
        # R1 outputs: <think>...</think> then the answer after |end_of_sentence|
        # Keep only the part after the thinking trace / EOS token.
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = text.replace("<|end_of_sentence|>", "").strip()
    elif fmt == "deepseek-v3":
        # V3.2 messages API response: choices[0].message.content
        choices = raw.get("choices", [{}])
        text = (choices[0].get("message", {}).get("content", "") if choices else "") or raw.get("generation", "")
        text = text.strip()
    elif fmt == "llama3":
        text = raw.get("generation", "").strip()

    return text, latency_ms


# ── Evaluation ───────────────────────────────────────────────────────────────

def _eval_annotation(response_text: str, expected: dict) -> tuple[bool, float]:
    """
    Fair single-model annotation eval. Parses JSON from model response.
    Score: 1pt anomaly_detected match + 1pt severity match. Pass if score >= 1.0.
    """
    score = 0.0
    try:
        # Extract JSON from response (model may add surrounding text)
        m = re.search(r"\{[^{}]+\}", response_text, re.DOTALL)
        if not m:
            return False, 0.0
        parsed = json.loads(m.group())
    except (json.JSONDecodeError, AttributeError):
        return False, 0.0

    exp_anomaly = expected.get("anomaly_detected", False)
    act_anomaly = parsed.get("anomaly_detected", False)
    # Normalize: model may return string "true"/"false"
    if isinstance(act_anomaly, str):
        act_anomaly = act_anomaly.lower() in ("true", "1", "yes", "anomaly", "error")

    if act_anomaly == exp_anomaly:
        score += 1.0

    exp_sev = str(expected.get("severity", "")).lower()
    act_sev = str(parsed.get("severity", "")).lower()
    if exp_sev and act_sev == exp_sev:
        score += 1.0
    elif exp_sev and act_sev in ("warning", "medium") and exp_sev in ("warning", "medium"):
        score += 0.5  # close enough

    return score >= 1.0, score


def _eval_rca(response_text: str, case: dict) -> tuple[bool, float]:
    """
    RCA eval: check if expected_root_cause or any acceptable_answer
    appears case-insensitively in the model's free-text response.
    """
    text_lower = response_text.lower()
    expected = str(case.get("expected_root_cause", "")).lower().strip()
    acceptable = [str(a).lower().strip() for a in case.get("acceptable_answers", [])]

    if acceptable and any(a and a in text_lower for a in acceptable):
        return True, 1.5
    if expected and expected in text_lower:
        return True, 1.0
    # Also check individual words if expected is multi-word (partial credit threshold)
    if expected:
        words = [w for w in expected.split("_") if len(w) > 3]
        if words and sum(1 for w in words if w in text_lower) >= max(1, len(words) // 2):
            return True, 0.8
    return False, 0.0


# ── Case runners ─────────────────────────────────────────────────────────────

def _run_annotation(client, model_cfg: dict, case: dict) -> dict:
    inp = case.get("input", {})
    content = inp.get("content", "")
    context = inp.get("context", "")
    user_msg = f"Log entry: {content}"
    if context:
        user_msg += f"\nContext: {context}"

    prompt = _build_prompt(model_cfg["format"], _ANN_SYSTEM, user_msg)
    try:
        text, lat = _call_bedrock(client, model_cfg, prompt, model_cfg["max_tokens_ann"], system=_ANN_SYSTEM, user=user_msg)
        correct, score = _eval_annotation(text, case.get("expected", {}))
    except Exception as e:
        text, lat, correct, score = str(e)[:200], 0.0, False, 0.0

    return {
        "case_id": case["id"],
        "task_type": "annotation",
        "source": case.get("source", ""),
        "correct": correct,
        "rule_score": round(score, 2),
        "inference_latency_ms": round(lat, 2),
        "model_response": text[:500],
        "expected": case.get("expected", {}),
        "timestamp": datetime.utcnow().isoformat(),
    }


def _run_rca(client, model_cfg: dict, case: dict) -> dict:
    incident = case.get("incident", {})
    question = incident.get("question", "")
    logs = incident.get("logs", [])
    title = incident.get("title", "")

    if question:
        user_msg = question
    else:
        parts = []
        if title:
            parts.append(f"Incident: {title}")
        if logs:
            log_text = "\n".join(str(l) for l in logs[:5])
            parts.append(f"Logs:\n{log_text}")
        user_msg = "\n".join(parts) if parts else "Analyze the incident."

    prompt = _build_prompt(model_cfg["format"], _RCA_SYSTEM, user_msg[:3000])
    try:
        text, lat = _call_bedrock(client, model_cfg, prompt, model_cfg["max_tokens_rca"], system=_RCA_SYSTEM, user=user_msg[:3000])
        correct, score = _eval_rca(text, case)
    except Exception as e:
        text, lat, correct, score = str(e)[:200], 0.0, False, 0.0

    return {
        "case_id": case["id"],
        "task_type": "rca",
        "source": case.get("source", ""),
        "correct": correct,
        "rule_score": round(score, 2),
        "inference_latency_ms": round(lat, 2),
        "model_response": text[:500],
        "expected_root_cause": case.get("expected_root_cause", ""),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", required=True, choices=list(MODELS.keys()),
                    help="Which SOTA baseline to run")
    ap.add_argument("--dataset", type=Path,
                    default=REPO_ROOT / "benchmark/datasets/processed/benchmark_400_seed42.json")
    ap.add_argument("--out", type=Path, required=True,
                    help="Output JSONL path")
    ap.add_argument("--aws-profile", default="aiops-operator")
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--ann", type=int, default=0, help="Limit annotation cases (0=all)")
    ap.add_argument("--rca", type=int, default=0, help="Limit RCA cases (0=all)")
    args = ap.parse_args()

    model_cfg = MODELS[args.model]
    print(f"[sota] Model: {model_cfg['display']} ({model_cfg['bedrock_id']})")
    print(f"[sota] Dataset: {args.dataset}")
    print(f"[sota] Output: {args.out}")

    import boto3
    session = boto3.Session(profile_name=args.aws_profile, region_name=args.region)
    client = session.client("bedrock-runtime")

    # Quick connectivity check
    try:
        _call_bedrock(client, model_cfg, _build_prompt(model_cfg["format"], "You are helpful.", "Say OK"), 8, system="You are helpful.", user="Say OK")
        print(f"[sota] Bedrock connectivity OK")
    except Exception as e:
        print(f"[sota] ERROR: Bedrock connection failed: {e}", file=sys.stderr)
        return 1

    # Load dataset
    raw = json.loads(args.dataset.read_text(encoding="utf-8"))
    cases = raw.get("test_cases", raw) if isinstance(raw, dict) else raw
    ann_cases = [c for c in cases if c.get("task_type") == "annotation"]
    rca_cases = [c for c in cases if c.get("task_type") == "rca"]
    if args.ann:
        ann_cases = ann_cases[:args.ann]
    if args.rca:
        rca_cases = rca_cases[:args.rca]

    print(f"[sota] {len(ann_cases)} annotation + {len(rca_cases)} RCA cases")

    # Resume support — skip already-done case_ids
    args.out.parent.mkdir(parents=True, exist_ok=True)
    done_ids: set[str] = set()
    if args.out.exists():
        for line in args.out.read_text(encoding="utf-8").splitlines():
            try:
                done_ids.add(json.loads(line)["case_id"])
            except Exception:
                pass
    if done_ids:
        print(f"[sota] Resuming — {len(done_ids)} cases already done")

    total = len(ann_cases) + len(rca_cases)
    done = len(done_ids)

    delay = model_cfg.get("inter_request_delay_s", 1)

    with args.out.open("a", encoding="utf-8") as f:
        # Annotation
        for i, case in enumerate(ann_cases):
            if case["id"] in done_ids:
                continue
            if i > 0:
                time.sleep(delay)
            rec = _run_annotation(client, model_cfg, case)
            f.write(json.dumps(rec) + "\n")
            f.flush()
            done += 1
            status = "OK " if rec["correct"] else "FAIL"
            print(f"  [ANN {i+1:3d}/{len(ann_cases)}] {status} {case['id']:20s} lat={rec['inference_latency_ms']:.0f}ms")

        # RCA
        for i, case in enumerate(rca_cases):
            if case["id"] in done_ids:
                continue
            time.sleep(delay)
            rec = _run_rca(client, model_cfg, case)
            f.write(json.dumps(rec) + "\n")
            f.flush()
            done += 1
            status = "OK " if rec["correct"] else "FAIL"
            print(f"  [RCA {i+1:3d}/{len(rca_cases)}] {status} {case['id']:20s} lat={rec['inference_latency_ms']:.0f}ms")

    # Summary
    results = [json.loads(l) for l in args.out.read_text(encoding="utf-8").splitlines() if l.strip()]
    ann_r = [r for r in results if r["task_type"] == "annotation"]
    rca_r = [r for r in results if r["task_type"] == "rca"]
    ann_acc = sum(1 for r in ann_r if r["correct"]) / max(len(ann_r), 1) * 100
    rca_acc = sum(1 for r in rca_r if r["correct"]) / max(len(rca_r), 1) * 100
    overall = sum(1 for r in results if r["correct"]) / max(len(results), 1) * 100

    print(f"\n{'='*60}")
    print(f"  {model_cfg['display']} Results")
    print(f"{'='*60}")
    print(f"  Annotation: {sum(1 for r in ann_r if r['correct'])}/{len(ann_r)} = {ann_acc:.1f}%")
    print(f"  RCA:        {sum(1 for r in rca_r if r['correct'])}/{len(rca_r)} = {rca_acc:.1f}%")
    print(f"  Overall:    {sum(1 for r in results if r['correct'])}/{len(results)} = {overall:.1f}%")
    lats = [r["inference_latency_ms"] for r in results if r["inference_latency_ms"] > 0]
    if lats:
        lats_s = sorted(lats)
        n = len(lats_s)
        pos = 0.95 * (n - 1)
        p95 = lats_s[int(pos)] + (pos - int(pos)) * (lats_s[min(int(pos)+1, n-1)] - lats_s[int(pos)])
        print(f"  Latency avg={sum(lats)/len(lats):.0f}ms  P95={p95:.0f}ms")
    print(f"{'='*60}")
    print(f"[sota] Results -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
