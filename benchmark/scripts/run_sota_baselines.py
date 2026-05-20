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
        --dataset benchmark/intermediate/datasets/benchmark_400_seed42.json \\
        --out benchmark/final/sota_baselines/deepseek_r1.jsonl

    python benchmark/scripts/run_sota_baselines.py --model llama-3.3-70b \\
        --dataset benchmark/intermediate/datasets/benchmark_400_seed42.json \\
        --out benchmark/final/sota_baselines/llama_3_3_70b.jsonl
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
        if system:
            return f"<|begin_of_sentence|>System: {system}\n\nUser: {user}\n\nAssistant:"
        return f"<|begin_of_sentence|>User: {user}\n\nAssistant:"
    if fmt == "deepseek-v3":
        if system:
            return f"System: {system}\n\nUser: {user}\n\nAssistant:"
        return f"User: {user}\n\nAssistant:"
    if fmt == "llama3":
        if system:
            return (
                f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system}\n"
                f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n{user}\n"
                f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
            )
        return (
            f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n{user}\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        )
    raise ValueError(f"Unknown format: {fmt}")


# ── Bedrock call ─────────────────────────────────────────────────────────────

def _call_bedrock(client, model_cfg: dict, prompt: str, max_tokens: int, system: str = "", user: str = "") -> tuple[str, float]:
    """Returns (text, latency_ms). Retries on throttling with exponential backoff."""
    fmt = model_cfg["format"]
    temp = float(model_cfg.get("temperature", 0.0))
    if fmt == "deepseek":
        body = json.dumps({"prompt": prompt, "max_tokens": max_tokens, "temperature": temp})
    elif fmt == "deepseek-v3":
        # DeepSeek V3.2 on Bedrock uses OpenAI-compatible messages API (not prompt field)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        body = json.dumps({
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temp,
        })
    elif fmt == "llama3":
        body = json.dumps({"prompt": prompt, "max_gen_len": max_tokens, "temperature": temp})
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

_NL_ANOMALY_POSITIVE = re.compile(
    r'\b(anomal(?:y|ous)|abnormal|attack(?:ed)?|intrusion|brute.?force|'
    r'unauthorized|malicious|suspicious|corruption|overflow|'
    r'fail(?:ed|ure)|error\s+detected|exception|violation|'
    r'indicates?\s+(?:an?\s+)?(?:anomaly|issue|problem|attack)|'
    r'security\s+(?:issue|threat|breach)|this\s+is\s+an?\s+anomaly)\b',
    re.IGNORECASE,
)
_NL_ANOMALY_NEGATIVE = re.compile(
    r'\b(no\s+anomaly|not\s+an?\s+anomaly|normal\s+operation|normal\s+behavior|'
    r'no\s+(?:issue|error|fault|failure|attack|problem)|'
    r'routine|expected\s+behavior|legitimate|healthy|benign|'
    r'regular\s+operation|typical\s+behavior|this\s+is\s+normal)\b',
    re.IGNORECASE,
)

def _nl_anomaly_predict(text: str) -> bool:
    """Keyword-based anomaly prediction from natural-language response (no-prompt fallback)."""
    pos = bool(_NL_ANOMALY_POSITIVE.search(text))
    neg = bool(_NL_ANOMALY_NEGATIVE.search(text))
    if pos and not neg:
        return True
    if neg and not pos:
        return False
    # Ambiguous — count weighted signals
    pos_words = re.findall(r'\b(?:error|fail(?:ed|ure)?|attack|malicious|suspicious|critical|alert|violation|unauthorized)\b', text, re.IGNORECASE)
    neg_words = re.findall(r'\b(?:normal|routine|expected|regular|legitimate|benign)\b', text, re.IGNORECASE)
    return len(pos_words) > len(neg_words)


def _eval_annotation(response_text: str, expected: dict, no_prompt: bool = False) -> tuple[bool, float]:
    """
    Fair single-model annotation eval. Parses JSON from model response.
    Score: 1pt anomaly_detected match + 1pt severity match. Pass if score >= 1.0.
    When no_prompt=True and JSON is absent, falls back to NL keyword matching
    for anomaly_detected only (severity cannot be inferred without structure).
    """
    score = 0.0
    parsed = None
    try:
        m = re.search(r"\{[^{}]+\}", response_text, re.DOTALL)
        if m:
            parsed = json.loads(m.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    if parsed is None:
        if not no_prompt:
            return False, 0.0
        # No-prompt fallback: NL keyword matching for anomaly_detected only
        predicted_anomaly = _nl_anomaly_predict(response_text)
        exp_anomaly = expected.get("anomaly_detected", False)
        score = 1.0 if predicted_anomaly == exp_anomaly else 0.0
        return score >= 1.0, score

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

    no_prompt = model_cfg.get("no_prompt", False)
    system = "" if no_prompt else _ANN_SYSTEM
    prompt = _build_prompt(model_cfg["format"], system, user_msg)
    try:
        text, lat = _call_bedrock(client, model_cfg, prompt, model_cfg["max_tokens_ann"], system=system, user=user_msg)
        correct, score = _eval_annotation(text, case.get("expected", {}), no_prompt=no_prompt)
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

    no_prompt = model_cfg.get("no_prompt", False)
    system = "" if no_prompt else _RCA_SYSTEM
    prompt = _build_prompt(model_cfg["format"], system, user_msg[:3000])
    try:
        text, lat = _call_bedrock(client, model_cfg, prompt, model_cfg["max_tokens_rca"], system=system, user=user_msg[:3000])
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
                    default=REPO_ROOT / "benchmark/intermediate/datasets/benchmark_400_seed42.json")
    ap.add_argument("--out", type=Path, required=True,
                    help="Output JSONL path")
    ap.add_argument("--aws-profile", default="aiops-operator")
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--ann", type=int, default=None, help="Max annotation cases (omit=all, 0=skip)")
    ap.add_argument("--rca", type=int, default=None, help="Max RCA cases (omit=all, 0=skip)")
    ap.add_argument("--no-prompt", action="store_true",
                    help="Phase 4.6 Part B: strip system prompt entirely (cross-model robustness test)")
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="Sampling temperature (default 0.0 deterministic; 0.05-0.1 introduces natural variance for reproducibility across re-runs)")
    args = ap.parse_args()

    model_cfg = MODELS[args.model]
    # Phase 4.6 Part B: strip prompts to test cross-model robustness
    model_cfg = dict(model_cfg)  # shallow copy — don't mutate global (needed for both temp and no_prompt overrides)
    model_cfg["temperature"] = args.temperature
    if args.no_prompt:
        model_cfg["no_prompt"] = True
        print(f"[sota] Mode: NO-PROMPT (Phase 4.6 Part B)")
    if args.temperature != 0.0:
        print(f"[sota] Temperature: {args.temperature} (non-zero — variance will affect reproducibility)")
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
    if args.ann is not None:
        ann_cases = ann_cases[:args.ann]   # 0 means skip all annotation
    if args.rca is not None:
        rca_cases = rca_cases[:args.rca]   # 0 means skip all RCA

    # Load excluded RCA case IDs (71 cases: 39 Chinese expected + 32 bare-letter MC)
    _excluded_path = REPO_ROOT / "benchmark/intermediate/datasets/excluded_rca_cases.json"
    excluded_ids: set[str] = set()
    if _excluded_path.exists():
        _ex = json.loads(_excluded_path.read_text(encoding="utf-8"))
        excluded_ids = {item["id"] for item in _ex.get("excluded_ids", [])}
    if excluded_ids:
        print(f"[sota] {len(excluded_ids)} RCA cases will be marked correct=null (Chinese/MC excluded)")

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
            if case["id"] in excluded_ids:
                rec = {
                    "case_id": case["id"], "task_type": "rca",
                    "source": case.get("source", ""),
                    "correct": None, "rule_score": None,
                    "skip_reason": "excluded_unevaluable",
                    "inference_latency_ms": 0.0,
                    "model_response": "",
                    "expected_root_cause": case.get("expected_root_cause", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                f.write(json.dumps(rec) + "\n")
                f.flush()
                done_ids.add(case["id"])
                print(f"  [RCA {i+1:3d}/{len(rca_cases)}] SKIP {case['id']:20s} (excluded)")
                continue
            time.sleep(delay)
            rec = _run_rca(client, model_cfg, case)
            f.write(json.dumps(rec) + "\n")
            f.flush()
            done += 1
            status = "OK " if rec["correct"] else "FAIL"
            print(f"  [RCA {i+1:3d}/{len(rca_cases)}] {status} {case['id']:20s} lat={rec['inference_latency_ms']:.0f}ms")

    # Summary (excluded RCA cases have correct=None; only count evaluable)
    results = [json.loads(l) for l in args.out.read_text(encoding="utf-8").splitlines() if l.strip()]
    ann_r = [r for r in results if r.get("task_type") == "annotation"]
    rca_r = [r for r in results if r.get("task_type") == "rca"]
    rca_eval = [r for r in rca_r if r.get("correct") is not None]
    rca_excl = len(rca_r) - len(rca_eval)
    ann_acc = sum(1 for r in ann_r if r.get("correct")) / max(len(ann_r), 1) * 100
    rca_acc = sum(1 for r in rca_eval if r.get("correct")) / max(len(rca_eval), 1) * 100
    all_eval = ann_r + rca_eval
    overall = sum(1 for r in all_eval if r.get("correct")) / max(len(all_eval), 1) * 100

    excl_note = f" ({rca_excl} excluded)" if rca_excl else ""
    print(f"\n{'='*60}")
    print(f"  {model_cfg['display']} Results")
    print(f"{'='*60}")
    print(f"  Annotation: {sum(1 for r in ann_r if r.get('correct'))}/{len(ann_r)} = {ann_acc:.1f}%")
    print(f"  RCA:        {sum(1 for r in rca_eval if r.get('correct'))}/{len(rca_eval)} evaluable = {rca_acc:.1f}%{excl_note}")
    print(f"  Overall:    {sum(1 for r in all_eval if r.get('correct'))}/{len(all_eval)} evaluable = {overall:.1f}%")
    lats = [r["inference_latency_ms"] for r in results if r.get("inference_latency_ms", 0) > 0]
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
