#!/usr/bin/env python3
"""Smoke test: verify RCA agent now answers knowledge queries instead of refusing.

Targets 3 known cases that previously triggered the "this is a conceptual
inquiry, not an incident" refusal pattern. After the RCA_SYSTEM_PROMPT edit
in src/agents/reasoning_agent.py, the model should give the substantive
technical answer in the root_cause field.

Usage (on AWS instance with Ollama on localhost:11434):
    JARVIS_OLLAMA_URL=http://localhost:11434 python3 benchmark/scripts/smoke_knowledge_query.py
"""
import os
import sys
import asyncio
import importlib

os.environ.setdefault("FAST_AGENT_URL", "http://localhost:11434/v1")
os.environ.setdefault("REASONING_AGENT_URL", "http://localhost:11434/v1")
os.environ.setdefault("FAST_AGENT_MODEL", "qwen3:4b-instruct")
os.environ.setdefault("REASONING_AGENT_MODEL", "qwen3:14b")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

import src.config  # noqa: E402
importlib.reload(src.config)

from src.agents.reasoning_agent import ReasoningAgent  # noqa: E402

KNOWN_REFUSAL_CASES = [
    {
        "id": "RCA_002",
        "question": "Which protocol is the preferred choice for network device access control? Options: A) RADIUS B) TACACS+ C) Kerberos D) LDAP",
        "expected": "TACACS+",
    },
    {
        "id": "RCA_028",
        "question": "What is the main difference between IGMPv2 and IGMPv3?",
        "expected": "IGMPv3",
    },
    {
        "id": "RCA_067",
        "question": "What is the maximum channel bandwidth supported by 5G sub-6GHz?",
        "expected": "100MHz",
    },
]


async def smoke():
    agent = ReasoningAgent()
    if hasattr(agent, "initialize"):
        await agent.initialize()
    hits = 0
    refusals = 0
    for c in KNOWN_REFUSAL_CASES:
        sep = "=" * 70
        print(f"\n{sep}")
        print(f"CASE: {c['id']}  EXPECTED: {c['expected']}")
        print(sep)
        incident = {
            "title": "Knowledge query",
            "logs": [c["question"]],
            "severity": "low",
            "context": c["question"],
        }
        try:
            resp = await agent.analyze_rca(incident)
            content = resp.content if hasattr(resp, "content") else str(resp)
            print(f"RESPONSE (first 700 chars):\n{content[:700]}")
            hit = c["expected"].lower() in content.lower()
            refusal_markers = [
                "conceptual inquiry",
                "not an incident",
                "knowledge question",
                "not requiring root cause",
                "not a system incident",
            ]
            refused = any(m in content.lower() for m in refusal_markers)
            print()
            print(f"*** Expected answer found in response: {hit}")
            print(f"*** Refusal-pattern detected:          {refused}")
            if hit:
                hits += 1
            if refused:
                refusals += 1
        except Exception as e:
            print(f"ERROR: {e}")

    if hasattr(agent, "close"):
        try:
            await agent.close()
        except Exception:
            pass

    print(f"\n{'='*70}\nSMOKE SUMMARY")
    print(f"  Expected-answer hits: {hits}/{len(KNOWN_REFUSAL_CASES)}")
    print(f"  Refusal-pattern hits: {refusals}/{len(KNOWN_REFUSAL_CASES)}")
    print(f"  Goal: hits >= 2/3 AND refusals == 0  (was 0/3 hits + 3/3 refusals before edit)")


if __name__ == "__main__":
    asyncio.run(smoke())
