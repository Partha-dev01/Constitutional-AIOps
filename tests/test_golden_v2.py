"""tests/test_golden_v2.py — golden set v2 (Phase 0 of the Mode 2 plan).

15 ADDITIONAL cases in ``tests/golden/cases_v2.jsonl`` extending the frozen
v1 golden set (``tests/golden/cases.jsonl`` + ``test_golden_regression.py``
stay byte-identical — they are the paper's regression gate). Coverage added:

  * GLD_TOOL_2xx (6) — tool-call-shaped queries (log analysis for a named
    service, metric interpretation, dependency questions, similar-incident
    lookups, container status) with the tool RESULT provided as context, so
    the reasoning model's grounding on tool output is regression-guarded.
  * GLD_CTX_2xx  (6) — long-context / multi-service RCA cascades.
  * GLD_OFF_2xx  (3) — clearly off-domain queries that MUST be refused
    (chat-mode scope guard; over-refusal's mirror image).

Runs in the SAME two modes as v1:
  1. Schema-only (default): validates the case file structure, no LLM needed.
  2. Live (opt-in): GOLDEN_SMOKE_LIVE=1 — calls the real agents against the
     configured FAST_AGENT_URL / REASONING_AGENT_URL endpoints.

Scoring reuses the v1 helper ``_check_invariants`` (loaded from the sibling
test module; minimally replicated if that import ever fails), plus a v2-only
refusal check for the chat-scope cases.

Invocation note (deliberate, documented deviation from v1): v1 passes
``{**case["input"], "mode": mode}`` straight to ``ReasoningAgent.process``,
whose signature only reads ``query``/``context`` — structured fields like
``logs`` never reach the model that way. v2 renders every non-query input
field into the ``context`` string so the case content is actually seen by
the model (required for the long-context cases to mean anything).
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Optional

import pytest

CASES_PATH = Path(__file__).parent / "golden" / "cases_v2.jsonl"
V1_CASES_PATH = Path(__file__).parent / "golden" / "cases.jsonl"
V1_TEST_PATH = Path(__file__).parent / "test_golden_regression.py"
LIVE_MODE = os.environ.get("GOLDEN_SMOKE_LIVE", "0") == "1"

_ID_RE = re.compile(r"^GLD_(TOOL|CTX|OFF)_2\d{2}$")
_TASK_TYPES = {"annotation", "rca", "remediation", "chat"}


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


CASES = _load_jsonl(CASES_PATH)


# ----- v1 helper import (same scoring approach) -------------------------------

def _load_v1_check_invariants() -> Optional[Callable[..., list[str]]]:
    """Load ``_check_invariants`` from the sibling v1 test module.

    tests/ is not a package, so import by file path. Returns None when the
    module cannot be loaded (the minimal replica below is used instead).
    """
    try:
        spec = importlib.util.spec_from_file_location("_aiops_golden_v1", V1_TEST_PATH)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, "_check_invariants", None)
    except Exception:  # noqa: BLE001 - fall back to the replica
        return None


def _replica_check_invariants(case: dict, output: dict, raw_response: str) -> list[str]:
    """Minimal replication of v1's ``_check_invariants`` (fallback only)."""
    failures: list[str] = []
    inv = case["output_invariants"]

    for f in inv.get("required_fields", []):
        if f not in output:
            failures.append(f"missing required field: {f}")

    if "min_confidence" in inv and "confidence" in output:
        conf = float(output.get("confidence", 0.0))
        if conf < inv["min_confidence"]:
            failures.append(f"confidence {conf:.2f} below floor {inv['min_confidence']}")

    blob = json.dumps(output) + "\n" + raw_response
    for forbidden in inv.get("forbidden_substrings", []):
        if forbidden.lower() in blob.lower():
            failures.append(f"forbidden substring leaked: '{forbidden}'")

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
            search = " ".join([
                str(output.get("root_cause", "")),
                str(output.get("reasoning", "")),
                json.dumps(output.get("remediation_steps", [])),
            ]).lower()
            if not any(k.lower() in search for k in keywords):
                failures.append(f"remediation lacks expected action keywords {keywords}")

    if case["task_type"] == "annotation":
        expected = case.get("expected", {})
        if expected.get("anomaly_detected") is False and output.get("anomaly_detected") is True:
            failures.append("hallucinated anomaly on normal/empty input")

    return failures


_V1_CHECK = _load_v1_check_invariants()


# ----- refusal detection (chat-scope cases) ----------------------------------

# Broadened marker set: the chat prompt asks the model to decline "in its own
# words", so exact-phrase matching alone is too brittle. A refusal is a SHORT
# reply containing any decline-ish marker (production `_looks_like_refusal`
# semantics, wider vocabulary). The production helper is preferred when its
# import succeeds; these markers back it up for free-form phrasings it misses.
_REFUSAL_MARKERS_V2 = (
    "can only help", "can only assist", "only help with", "only assist with",
    "outside my scope", "outside of my scope", "not within my scope",
    "out of scope", "outside the scope",
    "can't help", "cannot help", "can't assist", "cannot assist",
    "can't answer", "cannot answer", "unable to help", "unable to assist",
    "unable to answer", "not able to help", "not able to assist",
    "i must decline", "i have to decline", "i decline",
    "infrastructure", "operations assistant", "operations-related",
    "aiops",
)
_REFUSAL_MAX_CHARS = 400  # refusals are one brief sentence by policy


def _is_refusal(text: str) -> bool:
    lowered = (text or "").strip().lower()
    if not lowered or len(lowered) > _REFUSAL_MAX_CHARS:
        return False
    try:  # Prefer the production heuristic when importable.
        from src.api.routes.chat import _looks_like_refusal

        if _looks_like_refusal(text):
            return True
    except Exception:  # noqa: BLE001 - fall through to the local markers
        pass
    return any(marker in lowered for marker in _REFUSAL_MARKERS_V2)


# ----- case -> agent-call mapping ---------------------------------------------

def _query_for(case: dict) -> str:
    inp = case["input"]
    query = inp.get("query") or inp.get("question")
    if query:
        return str(query)
    return (
        "Perform root cause analysis"
        if case["task_type"] == "rca"
        else "Create a remediation plan"
    )


def _context_for(case: dict) -> str:
    """Render every non-query input field into the context string (see module
    docstring: this is how logs/service/tool-result content reaches the model)."""
    ctx = {k: v for k, v in case["input"].items() if k not in ("query", "question")}
    return json.dumps(ctx, indent=2) if ctx else ""


def _check_case(case: dict, output: dict, raw: str) -> list[str]:
    check = _V1_CHECK or _replica_check_invariants
    failures = list(check(case, output, raw))
    if case["task_type"] == "chat":
        expected = case.get("expected", {})
        if expected.get("refusal") and not _is_refusal(raw):
            failures.append(
                f"expected a brief off-domain refusal, got: {raw[:160]!r}"
            )
    return failures


# ----- Schema-only tests (always run) ----------------------------------------

def test_cases_v2_file_exists():
    assert CASES_PATH.exists(), f"golden v2 cases file missing: {CASES_PATH}"
    assert len(CASES) == 15, f"expected exactly 15 golden v2 cases, got {len(CASES)}"


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_case_v2_structure(case: dict):
    """Each case carries the minimum keys the harness needs (v1 schema shape)."""
    assert "id" in case
    assert _ID_RE.match(case["id"]), f"unexpected v2 case id: {case['id']}"
    assert "task_type" in case
    assert case["task_type"] in _TASK_TYPES
    assert "input" in case
    assert "output_invariants" in case
    inv = case["output_invariants"]
    assert "required_fields" in inv
    assert isinstance(inv["required_fields"], list)
    assert "forbidden_substrings" in inv
    # Same guard the v1 file enforces: thinking-token leakage is the known
    # historical regression every golden case must smoke.
    assert "<think>" in inv["forbidden_substrings"], (
        f"{case['id']}: must guard against thinking-token leakage"
    )


def test_case_v2_type_distribution():
    """Distribution: 6 tool-call-shaped + 6 long-context RCA + 3 off-domain."""
    by_prefix: dict[str, int] = {}
    for c in CASES:
        prefix = c["id"].split("_")[1]  # TOOL, CTX, OFF
        by_prefix[prefix] = by_prefix.get(prefix, 0) + 1
    assert by_prefix.get("TOOL", 0) == 6
    assert by_prefix.get("CTX", 0) == 6
    assert by_prefix.get("OFF", 0) == 3


def test_case_v2_semantic_expectations_present():
    """Every case has a scorable expectation, not just invariants."""
    for c in CASES:
        if c["task_type"] == "rca":
            assert c.get("expected_root_cause_keywords"), f"{c['id']}: no keywords"
        elif c["task_type"] == "chat":
            assert c.get("expected", {}).get("refusal") is True, (
                f"{c['id']}: chat cases in v2 are refusal probes"
            )


def test_no_id_collision_with_v1():
    """v2 ids must never collide with the frozen v1 set."""
    v1_ids = {c["id"] for c in _load_jsonl(V1_CASES_PATH)}
    v2_ids = {c["id"] for c in CASES}
    assert len(v2_ids) == len(CASES), "duplicate ids within cases_v2.jsonl"
    assert not (v1_ids & v2_ids), f"id collision with v1: {v1_ids & v2_ids}"


# ----- Live LLM tests (opt-in via GOLDEN_SMOKE_LIVE=1) ------------------------

skip_unless_live = pytest.mark.skipif(
    not LIVE_MODE,
    reason="set GOLDEN_SMOKE_LIVE=1 to enable live LLM golden v2 tests",
)


@skip_unless_live
@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
async def test_golden_v2_live(case: dict):
    """Live LLM smoke. Requires GOLDEN_SMOKE_LIVE=1 + reachable endpoints."""
    # Lazy import: don't import heavy agents in schema-only mode (v1 pattern).
    from src.agents.fast_annotator import FastAnnotator
    from src.agents.model_router import ModelRouter
    from src.agents.reasoning_agent import ReasoningAgent

    router = ModelRouter()
    try:
        health = await router.health_check()
        if not (health.get("fast_agent") and health.get("reasoning_agent")):
            pytest.skip(f"endpoints not healthy: {health}")

        task = case["task_type"]
        if task == "annotation":
            response = await FastAnnotator(router).process(case["input"])
        elif task == "chat":
            # Chat mode: scope-refusal probe through the real chat prompt (no
            # runtime context — the scope rules alone must trigger the decline).
            response = await ReasoningAgent(router).chat(message=_query_for(case))
        else:
            mode = "rca" if task == "rca" else "planning"
            response = await ReasoningAgent(router).process({
                "mode": mode,
                "query": _query_for(case),
                "context": _context_for(case),
                "enable_thinking": False,
            })

        output = response.metadata or {}
        raw = getattr(response, "content", "") or ""

        failures = _check_case(case, output, raw)
        assert not failures, f"{case['id']} failed:\n  " + "\n  ".join(failures)

    finally:
        # ModelRouter holds httpx clients; close cleanly (v1 pattern).
        try:
            await router.close()
        except Exception:  # noqa: BLE001
            pass
