#!/usr/bin/env python3
"""
Test qwen3:4b-instruct model - single sample verification.

Tests:
1. Raw httpx request (content populated, no reasoning, fast latency)
2. FastAnnotator.process() with 1 test case
3. Determinism check (run same prompt twice, compare outputs)

Usage: python benchmark/scripts/test_instruct.py
"""

import os
import sys
import asyncio
import json
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Force environment variables
JARVIS_URL = "https://96c3f93672471.notebooks.jarvislabs.net"
os.environ["FAST_AGENT_URL"] = f"{JARVIS_URL}/v1"
os.environ["REASONING_AGENT_URL"] = f"{JARVIS_URL}/v1"
os.environ["FAST_AGENT_MODEL"] = "qwen3:4b-instruct"
os.environ["REASONING_AGENT_MODEL"] = "qwen3:14b"
os.environ["FAST_AGENT_TIMEOUT"] = "120"
os.environ["REASONING_AGENT_TIMEOUT"] = "180"

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"


async def test_1_raw_httpx():
    """Test 1: Raw httpx to qwen3:4b-instruct via /v1/."""
    print("\n" + "=" * 60)
    print("TEST 1: Raw httpx to qwen3:4b-instruct")
    print("=" * 60)

    import httpx

    url = f"{JARVIS_URL}/v1/chat/completions"
    payload = {
        "model": "qwen3:4b-instruct",
        "messages": [
            {"role": "system", "content": "You are a JSON API. Respond with only valid JSON."},
            {"role": "user", "content": 'Classify this log: "ERROR connection refused to postgres:5432"\nRespond: {"anomaly_detected": true/false, "severity": "critical/warning/info", "category": "error/performance/resource"}'},
        ],
        "max_tokens": 500,
        "temperature": 0.0,
        "seed": 42,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            start = time.perf_counter()
            resp = await client.post(url, json=payload)
            elapsed = (time.perf_counter() - start) * 1000

            data = resp.json()
            msg = data["choices"][0]["message"]
            content = msg.get("content", "")
            reasoning = msg.get("reasoning", "")
            usage = data.get("usage", {})
            finish = data["choices"][0].get("finish_reason", "?")

            print(f"  Status: {resp.status_code} ({elapsed:.0f}ms)")
            print(f"  Finish: {finish}")
            print(f"  Tokens: prompt={usage.get('prompt_tokens', 0)}, completion={usage.get('completion_tokens', 0)}")
            print(f"  Content ({len(content)} chars): {repr(content[:500])}")
            print(f"  Reasoning ({len(reasoning)} chars): {repr(reasoning[:200])}")

            if content and not reasoning:
                print(f"  {PASS} Content populated, no reasoning (no thinking mode)")
            elif content and reasoning:
                print(f"  {FAIL} Both populated (thinking may be active)")
            elif not content and reasoning:
                print(f"  {FAIL} Content empty, reasoning has data (THINKING ACTIVE)")
            else:
                print(f"  {FAIL} Both empty")

            # Check for <think> in content
            if "<think>" in content:
                print(f"  {FAIL} Content contains <think> tokens (inline thinking)")
            else:
                print(f"  {PASS} No <think> tokens in content")

            # Try to parse JSON
            try:
                parsed = json.loads(content.strip())
                print(f"  {PASS} Valid JSON: {parsed}")
            except json.JSONDecodeError:
                # Try extracting JSON from content
                if "{" in content:
                    start_idx = content.find("{")
                    end_idx = content.rfind("}") + 1
                    try:
                        parsed = json.loads(content[start_idx:end_idx])
                        print(f"  {PASS} JSON extracted: {parsed}")
                    except json.JSONDecodeError:
                        print(f"  {FAIL} Could not parse JSON from content")
                else:
                    print(f"  {FAIL} No JSON found in content")

            return elapsed

    except Exception as e:
        print(f"  {FAIL} Request failed: {type(e).__name__}: {e}")
        return 0


async def test_2_fast_annotator():
    """Test 2: FastAnnotator.process() with qwen3:4b-instruct."""
    print("\n" + "=" * 60)
    print("TEST 2: FastAnnotator.process()")
    print("=" * 60)

    import importlib
    import src.config
    importlib.reload(src.config)

    from src.agents.fast_annotator import FastAnnotator

    annotator = FastAnnotator()

    input_data = {
        "telemetry_type": "log",
        "content": "2024-01-15 10:30:00 ERROR [backend] Connection refused to database postgres:5432 - retrying in 5s",
        "context": "Backend service showing database connectivity issues",
    }

    try:
        start = time.perf_counter()
        result = await annotator.process(input_data)
        elapsed = (time.perf_counter() - start) * 1000

        print(f"  Latency: {elapsed:.0f}ms")
        print(f"  Content: {repr(result.content[:300])}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Confidence Level: {result.confidence_level}")
        print(f"  Action: {result.suggested_action}")
        print(f"  Metadata: {json.dumps(result.metadata, indent=2, default=str)[:600]}")

        # Validate key fields
        checks = []
        if result.content and result.content not in ("Unknown", "Parse error"):
            checks.append(f"  {PASS} Content is meaningful: {result.content[:100]}")
        else:
            checks.append(f"  {FAIL} Content is '{result.content}'")

        if result.metadata.get("anomaly_detected") is True:
            checks.append(f"  {PASS} anomaly_detected=True (correct for DB connection error)")
        else:
            checks.append(f"  {FAIL} anomaly_detected={result.metadata.get('anomaly_detected')}")

        sev = result.metadata.get("severity", "")
        if sev in ("critical", "warning", "high"):
            checks.append(f"  {PASS} severity='{sev}' (reasonable for DB error)")
        else:
            checks.append(f"  {FAIL} severity='{sev}' (expected critical/warning/high)")

        triplets = result.metadata.get("triplets", [])
        if len(triplets) > 0:
            checks.append(f"  {PASS} {len(triplets)} triplets extracted")
            for t in triplets[:3]:
                checks.append(f"         {t['subject']} {t['relation']} {t['object']}")
        else:
            checks.append(f"  {FAIL} No triplets extracted")

        if result.confidence > 0.5:
            checks.append(f"  {PASS} confidence={result.confidence:.2f} (> 0.5)")
        else:
            checks.append(f"  {FAIL} confidence={result.confidence:.2f} (too low)")

        for c in checks:
            print(c)

        return elapsed

    except Exception as e:
        print(f"  {FAIL} FastAnnotator.process() failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def test_3_determinism():
    """Test 3: Determinism check - same prompt, same output."""
    print("\n" + "=" * 60)
    print("TEST 3: Determinism (same prompt -> same output)")
    print("=" * 60)

    import httpx

    url = f"{JARVIS_URL}/v1/chat/completions"
    payload = {
        "model": "qwen3:4b-instruct",
        "messages": [
            {"role": "user", "content": 'Classify: "ERROR OOMKilled pod backend-7f8c"\nJSON: {"anomaly": true/false, "severity": "critical/warning/info"}'},
        ],
        "max_tokens": 200,
        "temperature": 0.0,
        "seed": 12345,
    }

    results = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        for i in range(2):
            start = time.perf_counter()
            resp = await client.post(url, json=payload)
            elapsed = (time.perf_counter() - start) * 1000
            content = resp.json()["choices"][0]["message"].get("content", "")
            results.append(content)
            print(f"  Run {i+1}: ({elapsed:.0f}ms) {repr(content[:200])}")

    if results[0] == results[1]:
        print(f"  {PASS} Deterministic: both outputs identical")
    else:
        print(f"  {FAIL} Non-deterministic: outputs differ")
        # Show diff
        for i, (a, b) in enumerate(zip(results[0], results[1])):
            if a != b:
                print(f"         First difference at char {i}: '{a}' vs '{b}'")
                break


async def main():
    print("=" * 60)
    print("CONSTITUTIONAL AIOPS - qwen3:4b-instruct TEST")
    print("=" * 60)
    print(f"Jarvis Labs: {JARVIS_URL}")
    print(f"FAST_AGENT_MODEL: {os.environ['FAST_AGENT_MODEL']}")
    print(f"Temperature: 0.0 (deterministic)")
    print(f"Seed: hash(prompt) % 2^32")

    raw_ms = await test_1_raw_httpx()
    ann_ms = await test_2_fast_annotator()
    await test_3_determinism()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Raw request latency:    {raw_ms:.0f}ms")
    print(f"  FastAnnotator latency:  {ann_ms:.0f}ms")
    print(f"  Previous (qwen3:4b):    ~28000ms")
    print(f"  Speedup:                ~{28000/max(ann_ms,1):.1f}x" if ann_ms > 0 else "  Speedup: N/A")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
