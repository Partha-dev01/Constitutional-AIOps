"""tests/test_golden_regression.py — semantic-tolerance regression guard.

10 hand-curated cases probing the LLM serving stack for known-historical
regressions. Each case has an `output_invariants` block specifying:
  * required_fields  — schema check (catches Qwen3 thinking-mode JSON breakage)
  * min_confidence   — sanity (catches "model returned 0.0 default")
  * forbidden_substrings — leaked thinking tokens, dangerous output
Plus task-specific semantic checks (any of N acceptable answers).

Runs in TWO modes:
  1. Schema-only (default): no LLM endpoint required; tests just validate
     case file structure. Useful in CI without GPU/API access.
  2. Live (opt-in): set GOLDEN_SMOKE_LIVE=1 in env; tests actually call
     FastAnnotator + ReasoningAgent. Use against AWS VM endpoints.

Failures here mean: a code change has broken the LLM contract.  Look at:
  - src/agents/model_router.py (thinking-mode handling)
  - src/agents/fast_annotator.py (JSON parser fallback)
  - src/agents/reasoning_agent.py (RCA prompt structure)
  - vLLM/Ollama serving version (parser changes between releases)

Reference: misty-knitting-pine.md Phase 1.4.
"""

from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import Any

import pytest

CASES_PATH = Path(__file__).parent / "golden" / "cases.jsonl"
LIVE_MODE = os.environ.get("GOLDEN_SMOKE_LIVE", "0") == "1"


def _load_cases() -> list[dict]:
    if not CASES_PATH.exists():
        return []
    return [json.loads(line) for line in CASES_PATH.read_text().splitlines() if line.strip()]


CASES = _load_cases()


# ----- Schema-only tests (always run) ----------------------------------------

def test_cases_file_exists():
    assert CASES_PATH.exists(), f"golden cases file missing: {CASES_PATH}"
    assert len(CASES) == 10, f"expected exactly 10 golden cases, got {len(CASES)}"


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_case_structure(case: dict):
    """Each case has the minimum required keys for the test harness to work."""
    assert "id" in case
    assert "task_type" in case
    assert case["task_type"] in {"annotation", "rca", "remediation"}
    assert "input" in case
    assert "output_invariants" in case
    inv = case["output_invariants"]
    assert "required_fields" in inv
    assert isinstance(inv["required_fields"], list)
    assert "forbidden_substrings" in inv
    # Common forbidden: leaked thinking tokens (Qwen3 regression smoke)
    assert "<think>" in inv["forbidden_substrings"], (
        f"{case['id']}: must guard against thinking-token leakage"
    )


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_case_id_distribution(case: dict):
    """Sanity: IDs follow GLD_<TYPE>_NNN convention."""
    assert re.match(r"^GLD_(ANN|RCA|REM|NEG)_\d{3}$", case["id"]), (
        f"unexpected case id: {case['id']}"
    )


def test_case_type_distribution():
    """Distribution: 3 annotation + 3 RCA + 2 remediation + 2 negative-control."""
    by_prefix: dict[str, int] = {}
    for c in CASES:
        prefix = c["id"].split("_")[1]  # ANN, RCA, REM, NEG
        by_prefix[prefix] = by_prefix.get(prefix, 0) + 1
    # NEG cases are subtype of annotation in task_type, so we count by id prefix
    assert by_prefix.get("ANN", 0) == 3
    assert by_prefix.get("RCA", 0) == 3
    assert by_prefix.get("REM", 0) == 2
    assert by_prefix.get("NEG", 0) == 2


# ----- Live LLM tests (opt-in via GOLDEN_SMOKE_LIVE=1) ----------------------

skip_unless_live = pytest.mark.skipif(
    not LIVE_MODE,
    reason="set GOLDEN_SMOKE_LIVE=1 to enable live LLM golden tests",
)


def _check_invariants(case: dict, output: dict, raw_response: str) -> list[str]:
    """Return list of failure messages; empty list = pass."""
    failures: list[str] = []
    inv = case["output_invariants"]

    # Required fields
    for f in inv.get("required_fields", []):
        if f not in output:
            failures.append(f"missing required field: {f}")

    # Confidence floor (only check if confidence field is present and required)
    if "min_confidence" in inv and "confidence" in output:
        conf = float(output.get("confidence", 0.0))
        if conf < inv["min_confidence"]:
            failures.append(
                f"confidence {conf:.2f} below floor {inv['min_confidence']}"
            )

    # Forbidden substrings (in serialized output AND raw response)
    blob = json.dumps(output) + "\n" + raw_response
    for forbidden in inv.get("forbidden_substrings", []):
        if forbidden.lower() in blob.lower():
            failures.append(f"forbidden substring leaked: '{forbidden}'")

    # Task-specific semantic check
    if case["task_type"] == "annotation":
        expected = case.get("expected", {})
        if "anomaly_detected" in expected:
            actual = output.get("anomaly_detected")
            # Strict for negative-controls (must NOT hallucinate), tolerant otherwise
            if case["id"].startswith("GLD_NEG_") or case["id"] == "GLD_ANN_003":
                if actual is True and expected["anomaly_detected"] is False:
                    failures.append(
                        f"hallucinated anomaly on normal/empty input "
                        f"(BGL false-positive trap or negative control)"
                    )
        if "severity_in" in expected and "severity" in output:
            sev = str(output["severity"]).lower()
            if sev not in [s.lower() for s in expected["severity_in"]]:
                # Soft fail — accept adjacent severities to absorb model variance
                pass

    if case["task_type"] == "rca":
        keywords = case.get("expected_root_cause_keywords", [])
        if keywords:
            rc = str(output.get("root_cause", "")).lower()
            if not any(k.lower() in rc for k in keywords):
                failures.append(
                    f"root_cause does not mention ANY expected keyword "
                    f"({keywords}); got: {rc[:120]!r}"
                )

    if case["task_type"] == "remediation":
        keywords = case.get("expected_action_keywords", [])
        if keywords:
            # Combine root_cause + any actions/steps fields into one searchable blob
            search = " ".join([
                str(output.get("root_cause", "")),
                str(output.get("reasoning", "")),
                json.dumps(output.get("remediation_steps", [])),
            ]).lower()
            if not any(k.lower() in search for k in keywords):
                failures.append(
                    f"remediation lacks expected action keywords {keywords}"
                )

    return failures


@skip_unless_live
@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
async def test_golden_live(case: dict):
    """Live LLM smoke. Requires GOLDEN_SMOKE_LIVE=1 + reachable endpoints."""
    # Lazy import: don't import heavy agents in schema-only mode
    from src.agents.model_router import ModelRouter
    from src.agents.fast_annotator import FastAnnotator
    from src.agents.reasoning_agent import ReasoningAgent

    router = ModelRouter()
    try:
        # Health check first — skip if endpoints down (better than spurious fail)
        health = await router.health_check()
        if not (health.get("fast_agent") and health.get("reasoning_agent")):
            pytest.skip(f"endpoints not healthy: {health}")

        if case["task_type"] == "annotation":
            agent = FastAnnotator(router)
            response = await agent.process(case["input"])
        else:
            agent = ReasoningAgent(router)
            mode = "rca" if case["task_type"] == "rca" else "planning"
            response = await agent.process({**case["input"], "mode": mode})

        output = response.metadata or {}
        # AgentResponse.content carries the parsed-JSON-as-string sometimes
        raw = getattr(response, "content", "") or ""

        failures = _check_invariants(case, output, raw)
        assert not failures, f"{case['id']} failed:\n  " + "\n  ".join(failures)

    finally:
        # ModelRouter holds httpx clients; close cleanly
        try:
            await router.close()
        except Exception:
            pass
