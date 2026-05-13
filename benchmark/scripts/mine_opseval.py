#!/usr/bin/env python3
"""benchmark/scripts/mine_opseval.py — re-mine OpsEval EN for diagnostic-style RCA cases.

The v2.0 benchmark used only ~22 of 1,959 OpsEval EN QA pairs because most are
KNOWLEDGE questions ("What is OSPF?") rather than DIAGNOSTIC scenarios
("Why are users seeing 503s after the latest deploy?"). This script applies a
two-stage filter to expose ~100 high-quality diagnostic cases.

Stage 1 (regex, free, fast):
  - Drop "What is X" / "Which command" / "Define X" knowledge questions
  - Keep questions with diagnostic verbs: troubleshoot, investigate, "users cannot",
    "after upgrade", "intermittent", "log shows", "error", "fails"

Stage 2 (LLM classifier, ~$1, gated by --llm-filter flag):
  - Submit Stage-1 survivors to GPT-4o-mini (or Claude Haiku) for
    DIAGNOSTIC vs KNOWLEDGE binary classification.
  - Requires OPENAI_API_KEY env var (or set --judge-provider=anthropic + ANTHROPIC_API_KEY).

Output: list of candidate RCA cases — still needs human spot-check via vet_labels.py.

Usage (regex-only):
    python benchmark/scripts/mine_opseval.py --target 100 --out benchmark/v0.11/opseval_remine.jsonl

Usage (with LLM filter):
    python benchmark/scripts/mine_opseval.py --target 100 --out ... --llm-filter
"""

from __future__ import annotations
import argparse
import json
import os
import random
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OPSEVAL_EN = Path(os.environ.get("OPSEVAL_EN_DIR",
                                  str(REPO_ROOT / "benchmark/datasets/raw/opseval/data/en")))

# Stage 1: regex patterns

KNOWLEDGE_PATTERNS = [
    re.compile(r"^\s*(what|which)\s+(is|are|does)\b.*\b(stand for|mean|refer to)", re.IGNORECASE),
    re.compile(r"^\s*(define|definition of)\b", re.IGNORECASE),
    re.compile(r"\b(OSI|TCP)\s+(model|layer|stack)\b", re.IGNORECASE),
    re.compile(r"^\s*which\s+(command|protocol|standard|RFC|version|port)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+does\b.*\babbreviation\b", re.IGNORECASE),
]

DIAGNOSTIC_KEYWORDS = [
    "troubleshoot", "investigate", "diagnose", "diagnosis", "root cause",
    "users? (cannot|can't|unable)", "intermittent", "intermittently",
    "after .* (upgrade|reboot|change|deploy)",
    "(ping|traceroute|telnet) (fails|shows|times out)",
    "log shows", "error message", "high latency", "packet loss",
    "no response", "slow response", "service is down", "fails to start",
    "outage", "degraded", "saturat", "overload",
    "why", "experiencing",
]
DIAG_RE = re.compile("|".join(DIAGNOSTIC_KEYWORDS), re.IGNORECASE)


def load_opseval_pool() -> list[dict]:
    """Load all English OpsEval QA pairs from dev+test splits across categories."""
    if not OPSEVAL_EN.exists():
        print(f"ERROR: OpsEval EN dir not found at {OPSEVAL_EN}", file=sys.stderr)
        sys.exit(2)
    pool: list[dict] = []
    for split in ("test", "dev"):
        split_dir = OPSEVAL_EN / split
        if not split_dir.is_dir():
            continue
        for json_file in split_dir.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if not isinstance(data, list):
                    continue
                category = json_file.stem
                for item in data:
                    item["_category"] = category
                    item["_split"] = split
                    pool.append(item)
            except Exception as e:
                print(f"WARN: failed to parse {json_file}: {e}", file=sys.stderr)
    return pool


def is_knowledge_question(question: str) -> bool:
    """True if the question looks like factual recall, not incident diagnosis."""
    if not question:
        return False
    for p in KNOWLEDGE_PATTERNS:
        if p.search(question):
            return True
    return False


def has_diagnostic_signal(question: str) -> bool:
    """True if any diagnostic verb/phrase is present."""
    return bool(DIAG_RE.search(question or ""))


def stage1_regex_filter(pool: list[dict]) -> list[dict]:
    """Apply regex prefilter. Returns list of (likely) diagnostic items."""
    out = []
    for item in pool:
        q = item.get("question") or item.get("query") or ""
        if not isinstance(q, str):
            continue
        if is_knowledge_question(q):
            continue
        if not has_diagnostic_signal(q):
            continue
        out.append(item)
    return out


_SYS_MSG = (
    "Classify this IT-Ops question as DIAGNOSTIC (engineer is given a "
    "symptom/incident and must identify cause/fix) or KNOWLEDGE "
    "(factual recall about protocols/standards/syntax). "
    "Answer ONE WORD: DIAGNOSTIC or KNOWLEDGE."
)


def _classify_openai(q: str, client: "OpenAI") -> str:  # type: ignore[name-defined]
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": _SYS_MSG}, {"role": "user", "content": q[:2000]}],
        temperature=0.0,
        max_tokens=8,
    )
    return (resp.choices[0].message.content or "").strip().upper()


def _classify_bedrock(q: str, client) -> str:
    import json as _json
    body = _json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 8,
        "temperature": 0.0,
        "system": _SYS_MSG,
        "messages": [{"role": "user", "content": q[:2000]}],
    })
    resp = client.invoke_model(
        modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    result = _json.loads(resp["body"].read())
    return (result.get("content", [{}])[0].get("text", "")).strip().upper()


def stage2_llm_filter(survivors: list[dict], provider: str = "bedrock") -> list[dict]:
    """Optional LLM classifier — calls API.

    Returns a NEW list of items predicted DIAGNOSTIC. Items predicted
    KNOWLEDGE are filtered out. On API/network failure, returns the input
    unfiltered (graceful degradation — better to keep noise than lose data).

    Providers:
      bedrock  — Claude Haiku 4.5 via AWS Bedrock (profile aiops-operator, preferred)
      openai   — GPT-4o-mini (requires OPENAI_API_KEY)
    """
    classify_fn = None

    if provider == "bedrock":
        try:
            import boto3  # type: ignore
            profile = os.environ.get("AWS_PROFILE", "aiops-operator")
            session = boto3.Session(profile_name=profile, region_name="us-east-1")
            client = session.client("bedrock-runtime")
            classify_fn = lambda q: _classify_bedrock(q, client)
            print(f"[mine_opseval] Stage 2: using Bedrock Haiku 4.5 (profile: {profile})")
        except Exception as e:
            print(f"WARN: Bedrock init failed ({e}) — skipping LLM filter", file=sys.stderr)
            return survivors

    elif provider in ("openai", "ollama"):
        base_url = os.environ.get("LLM_JUDGE_URL", None)
        api_key = "ollama" if provider == "ollama" else os.environ.get("OPENAI_API_KEY", "")
        model = "qwen3:4b-instruct" if provider == "ollama" else "gpt-4o-mini"
        if provider == "openai" and not api_key:
            print("WARN: OPENAI_API_KEY not set — skipping Stage 2 LLM filter", file=sys.stderr)
            return survivors
        if provider == "ollama" and not base_url:
            base_url = os.environ.get("FAST_AGENT_URL", "http://localhost:11434/v1")
        try:
            from openai import OpenAI  # type: ignore
            client_oa = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            # Override _classify_openai to use the configured model
            def _classify_for_provider(q: str) -> str:
                resp = client_oa.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": _SYS_MSG}, {"role": "user", "content": q[:2000]}],
                    temperature=0.0,
                    max_tokens=8,
                )
                return (resp.choices[0].message.content or "").strip().upper()
            classify_fn = _classify_for_provider
            print(f"[mine_opseval] Stage 2: using {provider} ({model})")
        except ImportError:
            print("WARN: openai package not installed — pip install openai", file=sys.stderr)
            return survivors

    if classify_fn is None:
        print(f"WARN: provider '{provider}' not available — skipping Stage 2", file=sys.stderr)
        return survivors

    kept = []
    for i, item in enumerate(survivors):
        q = item.get("question") or item.get("query") or ""
        try:
            verdict = classify_fn(q)
            if "DIAGNOSTIC" in verdict:
                kept.append(item)
        except Exception as e:
            print(f"WARN: classifier failed on item {i}: {e}", file=sys.stderr)
            kept.append(item)  # keep on failure (graceful degradation)
        if (i + 1) % 50 == 0:
            print(f"  classified {i+1}/{len(survivors)}, kept {len(kept)}")
    return kept


_LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def to_case(item: dict, idx: int) -> dict:
    """Convert an OpsEval QA item into a runner-compatible RCA case."""
    import re as _re
    q = item.get("question") or item.get("query") or ""
    answer_raw = item.get("answer") or item.get("solution") or item.get("std_ans") or ""
    if isinstance(answer_raw, list):
        answer_raw = "; ".join(str(a) for a in answer_raw)
    answer_raw = str(answer_raw)
    category = item.get("_category", "unknown")

    # Embed multiple-choice options into the question text so the model can
    # reference them.  OpsEval stores choices as a list; answer is letter(s).
    choices: list[str] = item.get("choices", [])
    acceptable_answers: list[str] = []
    if choices:
        opts_text = "\n".join(f"{_LETTERS[i]}. {ch}" for i, ch in enumerate(choices))
        q = q.rstrip() + "\n\n" + opts_text
        # Convert letter answer(s) to option text for semantic evaluation
        correct_letters = [l.strip() for l in _re.split(r"[,;]", answer_raw) if l.strip()]
        correct_texts = []
        for letter in correct_letters:
            letter_up = letter.upper()
            if letter_up in _LETTERS:
                idx_c = _LETTERS.index(letter_up)
                if 0 <= idx_c < len(choices):
                    correct_texts.append(choices[idx_c])
        if correct_texts:
            answer_raw = "; ".join(correct_texts)
            acceptable_answers = correct_texts + correct_letters

    case: dict = {
        "id": f"RCA_OPSEVAL_RM_{idx:03d}",
        "source": f"opseval_remine_{category}",
        "task_type": "rca",
        "incident": {
            # Required for runner.py compatibility (per Phase 1.5 guard):
            # RCA cases MUST have logs OR question — we always supply question.
            "question": q,
            "title": f"OpsEval re-mined ({category})",
            "logs": [],
        },
        "expected_root_cause": answer_raw,
        "_provenance": {
            "opseval_category": category,
            "opseval_split": item.get("_split", "unknown"),
            "filter_stage": "regex+llm" if item.get("_llm_kept") else "regex",
        },
    }
    if acceptable_answers:
        case["acceptable_answers"] = acceptable_answers
    return case


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", type=int, default=100)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--llm-filter", action="store_true",
                    help="Run Stage 2 LLM classifier (bedrock=Haiku 4.5, ollama=qwen3:4b-instruct)")
    ap.add_argument("--judge-provider", default="bedrock", choices=["bedrock", "openai", "ollama"])
    args = ap.parse_args()

    pool = load_opseval_pool()
    print(f"[mine_opseval] loaded {len(pool)} OpsEval EN QA pairs")

    s1 = stage1_regex_filter(pool)
    print(f"[mine_opseval] Stage 1 (regex): {len(pool)} -> {len(s1)}")

    if args.llm_filter:
        s2 = stage2_llm_filter(s1, provider=args.judge_provider)
        for item in s2:
            item["_llm_kept"] = True
        print(f"[mine_opseval] Stage 2 (LLM): {len(s1)} -> {len(s2)}")
    else:
        s2 = s1
        print("[mine_opseval] Stage 2 SKIPPED (pass --llm-filter to enable)")

    rng = random.Random(args.seed)
    rng.shuffle(s2)
    selected = s2[: args.target]
    cases = [to_case(item, i + 1) for i, item in enumerate(selected)]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")

    print(f"[mine_opseval] wrote {args.out} ({len(cases)} cases)")
    cat_counts: dict[str, int] = {}
    for c in cases:
        cat = c["_provenance"]["opseval_category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    for cat, n in sorted(cat_counts.items()):
        print(f"  {cat}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
