#!/usr/bin/env python3
"""
Debug script: Test every layer of the benchmark connection pipeline.

Tests:
1. Raw httpx connection to Jarvis Labs
2. ModelRouter initialization and completion
3. FastAnnotator.process() with 1 test case
4. ReasoningAgent.process() with 1 test case
5. Qwen3 thinking mode behavior

Run: python benchmark/scripts/debug_connection.py
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
os.environ["FAST_AGENT_MODEL"] = "qwen3:4b"
os.environ["REASONING_AGENT_MODEL"] = "qwen3:14b"
os.environ["FAST_AGENT_TIMEOUT"] = "120"
os.environ["REASONING_AGENT_TIMEOUT"] = "180"

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"


async def test_1_raw_httpx():
    """Test 1: Raw httpx connection to Jarvis Labs."""
    print("\n" + "=" * 60)
    print("TEST 1: Raw httpx connection")
    print("=" * 60)

    import httpx

    url = f"{JARVIS_URL}/v1/chat/completions"
    payload = {
        "model": "qwen3:4b",
        "messages": [{"role": "user", "content": "/no_think\nSay OK in JSON: {\"status\": \"ok\"}"}],
        "max_tokens": 100,
        "temperature": 0.0,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            start = time.perf_counter()
            resp = await client.post(url, json=payload)
            elapsed = (time.perf_counter() - start) * 1000
            print(f"  Status: {resp.status_code} ({elapsed:.0f}ms)")
            data = resp.json()
            msg = data["choices"][0]["message"]
            content = msg.get("content", "")
            reasoning = msg.get("reasoning", "")
            finish = data["choices"][0].get("finish_reason", "?")
            usage = data.get("usage", {})
            print(f"  finish_reason: {finish}")
            print(f"  tokens: prompt={usage.get('prompt_tokens',0)}, completion={usage.get('completion_tokens',0)}")
            print(f"  content ({len(content)} chars): {repr(content[:200])}")
            print(f"  reasoning ({len(reasoning)} chars): {repr(reasoning[:200])}")

            if content:
                print(f"  {PASS} Content is populated")
            elif reasoning:
                print(f"  {FAIL} Content EMPTY, reasoning has data (THINKING MODE ISSUE)")
                print(f"  -> Qwen3 thinking mode is putting output in 'reasoning' field")
            else:
                print(f"  {FAIL} Both content and reasoning are empty")

            return True
    except Exception as e:
        print(f"  {FAIL} httpx connection failed: {type(e).__name__}: {e}")
        return False


async def test_2_httpx_with_think_false():
    """Test 2: httpx with think:false parameter."""
    print("\n" + "=" * 60)
    print("TEST 2: httpx with think:false parameter")
    print("=" * 60)

    import httpx

    # Test on BOTH /v1/ and /api/ endpoints
    for endpoint, name in [
        (f"{JARVIS_URL}/v1/chat/completions", "OpenAI /v1/"),
        (f"{JARVIS_URL}/api/chat", "Native /api/"),
    ]:
        print(f"\n  --- {name} endpoint ---")

        if "api/chat" in endpoint:
            payload = {
                "model": "qwen3:4b",
                "messages": [{"role": "user", "content": "/no_think\nSay OK"}],
                "think": False,
                "stream": False,
            }
        else:
            payload = {
                "model": "qwen3:4b",
                "messages": [{"role": "user", "content": "/no_think\nSay OK"}],
                "max_tokens": 100,
                "temperature": 0.0,
                "think": False,
            }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                start = time.perf_counter()
                resp = await client.post(endpoint, json=payload)
                elapsed = (time.perf_counter() - start) * 1000

                data = resp.json()
                if "api/chat" in endpoint:
                    msg = data.get("message", {})
                    content = msg.get("content", "")
                    thinking = msg.get("thinking", "")
                    print(f"  content ({len(content)} chars): {repr(content[:200])}")
                    print(f"  thinking ({len(thinking)} chars): {repr(thinking[:200])}")
                    if content and not thinking:
                        print(f"  {PASS} Native API: think:false works ({elapsed:.0f}ms)")
                    else:
                        print(f"  {FAIL} Native API: think:false not working")
                else:
                    msg = data["choices"][0]["message"]
                    content = msg.get("content", "")
                    reasoning = msg.get("reasoning", "")
                    print(f"  content ({len(content)} chars): {repr(content[:200])}")
                    print(f"  reasoning ({len(reasoning)} chars): {repr(reasoning[:200])}")
                    if content:
                        print(f"  {PASS} OpenAI API: content populated ({elapsed:.0f}ms)")
                    elif reasoning:
                        print(f"  {FAIL} OpenAI API: content EMPTY, reasoning has data")
                    else:
                        print(f"  {FAIL} OpenAI API: both empty")

        except Exception as e:
            print(f"  {FAIL} {name} failed: {type(e).__name__}: {e}")


async def test_3_model_router():
    """Test 3: ModelRouter connection."""
    print("\n" + "=" * 60)
    print("TEST 3: ModelRouter connection")
    print("=" * 60)

    # Reimport config after env vars are set
    import importlib
    import src.config
    importlib.reload(src.config)
    from src.config import Config
    # Create fresh config
    fresh_config = Config.from_env()

    print(f"  fast_agent_url: {fresh_config.llm.fast_agent_url}")
    print(f"  reasoning_agent_url: {fresh_config.llm.reasoning_agent_url}")
    print(f"  fast_agent_model: {fresh_config.llm.fast_agent_model}")
    print(f"  fast_agent_timeout: {fresh_config.llm.fast_agent_timeout}s")
    print(f"  reasoning_agent_timeout: {fresh_config.llm.reasoning_agent_timeout}s")

    from src.agents.model_router import ModelRouter

    router = ModelRouter(
        fast_agent_url=fresh_config.llm.fast_agent_url,
        reasoning_agent_url=fresh_config.llm.reasoning_agent_url,
    )

    # Test fast agent
    print("\n  --- Fast Agent (qwen3:4b) ---")
    try:
        start = time.perf_counter()
        result = await router.fast_completion(
            prompt="/no_think\nSay hello in JSON: {\"greeting\": \"hello\"}",
            max_tokens=200,
            temperature=0.0,
        )
        elapsed = (time.perf_counter() - start) * 1000
        msg = result["choices"][0]["message"]
        content = msg.get("content", "")
        reasoning = msg.get("reasoning", "")
        print(f"  Status: OK ({elapsed:.0f}ms)")
        print(f"  content: {repr(content[:200])}")
        print(f"  reasoning: {repr(reasoning[:200])}")
        if content:
            print(f"  {PASS} Fast agent content populated")
        elif reasoning:
            print(f"  {FAIL} Fast agent: content EMPTY, reasoning has data")
        else:
            print(f"  {FAIL} Fast agent: both empty")
    except Exception as e:
        print(f"  {FAIL} Fast agent failed: {type(e).__name__}: {e}")

    # Test reasoning agent
    print("\n  --- Reasoning Agent (qwen3:14b) ---")
    try:
        start = time.perf_counter()
        result = await router.reasoning_completion(
            prompt="/no_think\nSay hello in JSON: {\"greeting\": \"hello\"}",
            max_tokens=200,
            temperature=0.0,
        )
        elapsed = (time.perf_counter() - start) * 1000
        msg = result["choices"][0]["message"]
        content = msg.get("content", "")
        reasoning = msg.get("reasoning", "")
        print(f"  Status: OK ({elapsed:.0f}ms)")
        print(f"  content: {repr(content[:200])}")
        print(f"  reasoning: {repr(reasoning[:200])}")
        if content:
            print(f"  {PASS} Reasoning agent content populated")
        elif reasoning:
            print(f"  {FAIL} Reasoning agent: content EMPTY, reasoning has data")
        else:
            print(f"  {FAIL} Reasoning agent: both empty")
    except Exception as e:
        print(f"  {FAIL} Reasoning agent failed: {type(e).__name__}: {e}")

    await router.close()


async def test_4_fast_annotator():
    """Test 4: FastAnnotator.process() with 1 test case."""
    print("\n" + "=" * 60)
    print("TEST 4: FastAnnotator.process()")
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
        print(f"  Content: {repr(result.content[:200])}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Confidence Level: {result.confidence_level}")
        print(f"  Action: {result.suggested_action}")
        print(f"  Metadata: {json.dumps(result.metadata, indent=2, default=str)[:500]}")

        if result.content and result.content != "Unknown" and result.content != "Parse error":
            print(f"  {PASS} FastAnnotator returned valid content")
        elif result.content == "Unknown":
            print(f"  {FAIL} FastAnnotator returned 'Unknown' (JSON parse failure)")
        else:
            print(f"  {FAIL} FastAnnotator returned: {result.content}")
    except Exception as e:
        print(f"  {FAIL} FastAnnotator.process() failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


async def test_5_reasoning_agent():
    """Test 5: ReasoningAgent.process() with 1 test case."""
    print("\n" + "=" * 60)
    print("TEST 5: ReasoningAgent.process()")
    print("=" * 60)

    import importlib
    import src.config
    importlib.reload(src.config)

    from src.agents.reasoning_agent import ReasoningAgent

    agent = ReasoningAgent()

    input_data = {
        "mode": "rca",
        "query": "Perform root cause analysis",
        "context": json.dumps({
            "title": "Database connection failure",
            "severity": "critical",
            "logs": ["ERROR connection refused to postgres:5432"],
        }),
    }

    try:
        start = time.perf_counter()
        result = await agent.process(input_data)
        elapsed = (time.perf_counter() - start) * 1000

        print(f"  Latency: {elapsed:.0f}ms")
        print(f"  Content (first 300): {repr(result.content[:300])}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Action: {result.suggested_action}")
        meta_str = json.dumps(result.metadata, indent=2, default=str)
        print(f"  Metadata (first 500): {meta_str[:500]}")

        if result.confidence > 0 and "root_cause" in result.metadata:
            print(f"  {PASS} ReasoningAgent returned structured RCA")
        elif "raw_content" in result.metadata:
            print(f"  {FAIL} ReasoningAgent: JSON parse failed, got raw_content")
        else:
            print(f"  {FAIL} ReasoningAgent: unexpected result")
    except Exception as e:
        print(f"  {FAIL} ReasoningAgent.process() failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


async def main():
    print("=" * 60)
    print("CONSTITUTIONAL AIOPS - CONNECTION DEBUG")
    print("=" * 60)
    print(f"Jarvis Labs: {JARVIS_URL}")
    print(f"FAST_AGENT_URL: {os.environ['FAST_AGENT_URL']}")
    print(f"REASONING_AGENT_URL: {os.environ['REASONING_AGENT_URL']}")
    print(f"FAST_AGENT_TIMEOUT: {os.environ['FAST_AGENT_TIMEOUT']}s")
    print(f"REASONING_AGENT_TIMEOUT: {os.environ['REASONING_AGENT_TIMEOUT']}s")

    await test_1_raw_httpx()
    await test_2_httpx_with_think_false()
    await test_3_model_router()
    await test_4_fast_annotator()
    await test_5_reasoning_agent()

    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
