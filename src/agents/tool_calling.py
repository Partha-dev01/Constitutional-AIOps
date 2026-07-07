"""
Constitutional AIOps - Agentic tool-calling for the chat path.

This module gives the chat route REAL agentic tool-calling. It wraps the live
tool executors in ``src.api.routes.tools`` (the same ones the MCP page uses) and
drives a bounded loop in which the reasoning model itself chooses which tool(s)
to run, we execute the chosen tool against live Neo4j/Loki/Prometheus/Docker,
feed the structured result back, and let the model produce a grounded final
answer.

Two execution backends, behind one clean abstraction (``run_tool_calling_loop``):

* **App-layer loop (default, NO vLLM change required).** The current vLLM launch
  (``aws/docker-compose.vllm.yml``) does NOT pass ``--enable-auto-tool-choice``
  / ``--tool-call-parser hermes``, so native OpenAI ``tools=``/``tool_choice``
  is not honoured. The app-layer loop instead instructs the model (in the system
  prompt) to emit a single strict-JSON tool call of the form
  ``{"tool_call": {"name": ..., "arguments": {...}}}`` OR a final
  ``{"final_answer": "..."}``. We parse that JSON, execute the real tool, append
  the structured result to the transcript, and re-prompt. This works against any
  OpenAI-compatible endpoint with no server flags.

* **Native tool-calling (opt-in).** When ``AIOPS_NATIVE_TOOL_CALLING`` is truthy
  the loop passes ``tools=``/``tool_choice="auto"`` on the chat-completions call
  and reads ``message.tool_calls`` back. Use this only once the vLLM server is
  launched with the flags documented in the module-level constants below.

Routing (which tool runs) is decided in TWO complementary ways:

1. **Deterministic pre-routing** (:func:`plan_forced_tool_calls`): when the user
   explicitly NAMES a tool ("use the get_dependencies tool ...") or clearly
   implies one by keyword + service, we synthesize the tool call up-front and run
   it BEFORE the model speaks, so a named tool ALWAYS executes and the model can
   never just narrate intent. Missing required params surface as a structured
   ``needs_param`` record instead of silent prose.
2. **Model-driven selection** inside the loop: after (1), the model may request
   additional tools via the JSON / native protocol above.

The action tools (``restart_service`` / ``scale_service``) are exposed to the
agent ONLY when ``AIOPS_ENABLE_ACTION_TOOLS`` is set; their execution still flows
through the constitutional gate inside ``execute_tool_call`` — this module never
bypasses it.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# vLLM native-tool-calling toggle + the EXACT server flags it needs.
# ---------------------------------------------------------------------------

# When truthy, run_tool_calling_loop uses OpenAI-native tools=/tool_choice.
NATIVE_TOOL_CALLING_ENV = "AIOPS_NATIVE_TOOL_CALLING"

# vLLM server flags required for the NATIVE path to work for Qwen3 (hermes-style
# tool calls). Documented here so the integrator can copy them verbatim. The
# DEFAULT app-layer loop needs NONE of these.
VLLM_NATIVE_TOOL_FLAGS: tuple[str, ...] = (
    "--enable-auto-tool-choice",
    "--tool-call-parser hermes",
)

# Master kill-switch env for the mutating action tools (mirrors tools.py).
ACTION_TOOLS_ENV = "AIOPS_ENABLE_ACTION_TOOLS"

# Bound the agentic loop so a confused model cannot run tools forever.
DEFAULT_MAX_ITERATIONS = 3


def _native_tool_calling_enabled() -> bool:
    """True when the operator opted into native vLLM tool-calling."""
    return os.getenv(NATIVE_TOOL_CALLING_ENV, "").strip().lower() in ("1", "true", "yes")


def _action_tools_enabled() -> bool:
    """True when the mutating action tools are enabled (same env as tools.py)."""
    return os.getenv(ACTION_TOOLS_ENV, "").strip().lower() in ("1", "true", "yes")


# ---------------------------------------------------------------------------
# Tool catalogue — JSON-Schemas reused from the REST tool definitions.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToolSpec:
    """A tool the chat agent may call.

    ``parameters`` is the JSON-Schema object (mirrors the ``ToolInfo.parameters``
    declared in ``src/api/routes/tools.py``). ``required`` is the list of
    required parameter names pulled from that schema. ``is_action`` marks the
    mutating tools that are gated behind ``AIOPS_ENABLE_ACTION_TOOLS``.
    """

    name: str
    description: str
    parameters: dict[str, Any]
    is_action: bool = False

    @property
    def required(self) -> list[str]:
        req = self.parameters.get("required", [])
        return [str(r) for r in req] if isinstance(req, list) else []


# The 9 tools, schemas copied to match tools.py's ToolInfo declarations exactly.
_TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="find_similar",
        description="Find similar past incidents from Neo4j episodic memory (top-k similar incidents).",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Incident title / search text"},
                "category": {"type": "string", "description": "Incident category"},
                "affected_services": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["title"],
        },
    ),
    ToolSpec(
        name="get_dependencies",
        description="Get a service's upstream/downstream dependency graph from Neo4j for impact analysis.",
        parameters={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service to analyze"},
                "depth": {"type": "integer", "default": 2, "description": "Traversal depth"},
            },
            "required": ["service_name"],
        },
    ),
    ToolSpec(
        name="analyze_logs",
        description="Analyze logs from Loki for a service: counts, top error patterns, samples.",
        parameters={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service to analyze"},
                "time_range_minutes": {"type": "integer", "default": 30},
                "log_level": {"type": "string", "enum": ["all", "error", "warn", "info"], "default": "error"},
            },
            "required": ["service_name"],
        },
    ),
    ToolSpec(
        name="analyze_time_series_anomaly",
        description="Z-score statistical anomaly detection over a service's Prometheus metrics.",
        parameters={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service to analyze"},
                "metric_name": {"type": "string", "description": "Specific PromQL metric (optional)"},
                "time_range_minutes": {"type": "integer", "default": 60},
            },
            "required": ["service_name"],
        },
    ),
    ToolSpec(
        name="query_recent_logs",
        description="Query recent raw log entries from Loki for a service within a time window.",
        parameters={
            "type": "object",
            "properties": {
                "service": {"type": "string", "description": "Service name (use 'all' for all)"},
                "time_range_minutes": {"type": "integer", "default": 15},
                "limit": {"type": "integer", "default": 50},
                "query": {"type": "string", "description": "Optional LogQL query override"},
            },
            "required": ["service"],
        },
    ),
    ToolSpec(
        name="query_metric",
        description="Query Prometheus metrics for a service over a time range.",
        parameters={
            "type": "object",
            "properties": {
                "service": {"type": "string", "description": "Service name"},
                "time_range_minutes": {"type": "integer", "default": 30},
                "metrics": {"type": "array", "items": {"type": "string"}, "description": "Optional PromQL queries"},
            },
            "required": ["service"],
        },
    ),
    ToolSpec(
        name="list_containers",
        description="List Docker containers and their status (running / stopped / health).",
        parameters={
            "type": "object",
            "properties": {
                "all_containers": {"type": "boolean", "default": False, "description": "Include stopped containers"},
                "name_filter": {"type": "string", "description": "Optional substring filter on container name"},
            },
            "required": [],
        },
    ),
    ToolSpec(
        name="restart_service",
        description=(
            "Restart a whitelisted Docker container. ACTION tool — gated by "
            "AIOPS_ENABLE_ACTION_TOOLS and the constitutional validator."
        ),
        parameters={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service to restart (whitelisted, default nextcloud)"},
                "graceful": {"type": "boolean", "default": True},
                "reason": {"type": "string", "description": "Reason for restart (audited)"},
            },
            "required": ["service_name", "reason"],
        },
        is_action=True,
    ),
    ToolSpec(
        name="scale_service",
        description=(
            "Scale a whitelisted Docker Compose service (replicas clamped 0-5). "
            "ACTION tool — gated by AIOPS_ENABLE_ACTION_TOOLS and the validator."
        ),
        parameters={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service to scale (whitelisted, default nextcloud)"},
                "target_replicas": {"type": "integer", "minimum": 0, "maximum": 5},
                "reason": {"type": "string", "description": "Reason for scaling (audited)"},
            },
            "required": ["service_name", "target_replicas", "reason"],
        },
        is_action=True,
    ),
)

TOOL_SPECS_BY_NAME: dict[str, ToolSpec] = {spec.name: spec for spec in _TOOL_SPECS}


def available_tool_specs(include_actions: bool | None = None) -> list[ToolSpec]:
    """Return the tool specs visible to the agent this turn.

    Action tools are only included when enabled (env), unless ``include_actions``
    is forced. Read/query tools are always included.
    """
    enable_actions = _action_tools_enabled() if include_actions is None else include_actions
    return [spec for spec in _TOOL_SPECS if (not spec.is_action) or enable_actions]


def openai_tool_definitions(specs: list[ToolSpec] | None = None) -> list[dict[str, Any]]:
    """Render specs into OpenAI ``tools=`` function definitions (native path)."""
    specs = specs if specs is not None else available_tool_specs()
    return [
        {
            "type": "function",
            "function": {
                "name": spec.name,
                "description": spec.description,
                "parameters": spec.parameters,
            },
        }
        for spec in specs
    ]


# ---------------------------------------------------------------------------
# Tool-call record (THE response contract surfaced in metadata.tool_calls)
# ---------------------------------------------------------------------------


@dataclass
class ToolCallRecord:
    """One executed (or attempted) tool call for ``metadata.tool_calls``."""

    id: str
    name: str
    arguments: dict[str, Any]
    status: str  # "ok" | "error" | "needs_param"
    result: dict[str, Any] | None = None
    error: str | None = None
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


@dataclass
class ToolLoopResult:
    """Outcome of the agentic tool-calling loop."""

    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    final_answer: str | None = None
    iterations: int = 0
    native: bool = False

    @property
    def ran_any_tool(self) -> bool:
        return any(tc.status != "needs_param" for tc in self.tool_calls)


# ---------------------------------------------------------------------------
# Service extraction + deterministic routing
# ---------------------------------------------------------------------------

# Keywords mapping to a read/query tool, so a clearly-implied tool runs even when
# the user did not name it literally.
_KEYWORD_TOOL_HINTS: tuple[tuple[str, str], ...] = (
    ("similar", "find_similar"),
    ("past incident", "find_similar"),
    ("history", "find_similar"),
    ("previous", "find_similar"),
    ("dependenc", "get_dependencies"),
    ("upstream", "get_dependencies"),
    ("downstream", "get_dependencies"),
    ("impact", "get_dependencies"),
    ("analyze log", "analyze_logs"),
    ("error log", "analyze_logs"),
    ("log pattern", "analyze_logs"),
    ("recent log", "query_recent_logs"),
    ("anomaly", "analyze_time_series_anomaly"),
    ("metric", "query_metric"),
    ("container", "list_containers"),
)

# Investigation intent → force the full evidence bundle. The flagship incident
# hand-off prompt ("Investigate INC-… Diagnose the root cause and recommend
# remediation for <service>.", ActiveIncidentsPanel) matches NONE of the
# single-tool hints above, so it previously reached the model with zero
# gathered evidence and the reply degenerated into planning-speak.
_INVESTIGATION_KEYWORDS: tuple[str, ...] = (
    "investigate",
    "diagnose",
    "diagnosis",
    "root cause",
    "root-cause",
    "remediat",  # remediate / remediation
    "troubleshoot",
    "what went wrong",
    "what is wrong",
    "what's wrong",
)

# Ordered: memory first (mirrors the hint order above), then live logs, then
# blast radius. All three are READ tools; the service-requiring ones are
# skipped when no service resolves (find_similar runs regardless).
_INVESTIGATION_BUNDLE: tuple[str, ...] = (
    "find_similar",
    "analyze_logs",
    "get_dependencies",
)


def detect_named_tools(message: str) -> list[str]:
    """Return tool names the user explicitly referenced by name, in order.

    Matches a bare tool token ("get_dependencies") or its spaced form
    ("get dependencies"). The literal name takes priority — when a tool is named
    it MUST run, which is the core bug this module fixes.
    """
    lowered = message.lower()
    found: list[str] = []
    for name in TOOL_SPECS_BY_NAME:
        spaced = name.replace("_", " ")
        # Word-ish boundary so "scale" inside "rescale" doesn't match the token.
        if re.search(rf"(?<![a-z0-9_]){re.escape(name)}(?![a-z0-9_])", lowered) or (
            spaced != name and spaced in lowered
        ):
            if name not in found:
                found.append(name)
    return found


def _default_arguments(
    spec: ToolSpec,
    *,
    service: str | None,
    message: str,
) -> dict[str, Any]:
    """Best-effort default arguments for a deterministically-routed tool.

    Fills the service-identifying param from the resolved ``service`` and seeds
    the find_similar title from the user message, mirroring the prior chat
    behaviour. Anything still missing is reported as ``needs_param`` by the
    caller — never silently dropped.
    """
    args: dict[str, Any] = {}
    props = spec.parameters.get("properties", {})
    if service:
        if "service_name" in props:
            args["service_name"] = service
        if "service" in props:
            args["service"] = service
    if spec.name == "find_similar":
        args["title"] = message[:200]
        if service:
            args["affected_services"] = [service]
    return args


def plan_forced_tool_calls(
    message: str,
    service: str | None,
    *,
    include_actions: bool | None = None,
) -> list[tuple[ToolSpec, dict[str, Any]]]:
    """Deterministic pre-routing: which tool(s) to run BEFORE the model speaks.

    Strategy:
      1. Every tool the user NAMED literally is forced (this is the fix for
         "use the get_dependencies tool" never running).
      2. Otherwise, keyword hints map to a read/query tool when a service is
         resolvable (or the tool needs no service, e.g. list_containers).

    Action tools are only force-routed when explicitly enabled AND named — we
    never auto-trigger a destructive action from a keyword.

    Returns a list of ``(spec, seeded_arguments)`` in execution order; the
    arguments may still be missing required params (the loop reports those as
    ``needs_param``).
    """
    enable_actions = _action_tools_enabled() if include_actions is None else include_actions
    ordered: list[tuple[ToolSpec, dict[str, Any]]] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        if name in seen:
            return
        spec = TOOL_SPECS_BY_NAME.get(name)
        if spec is None:
            return
        if spec.is_action and not enable_actions:
            return
        ordered.append((spec, _default_arguments(spec, service=service, message=message)))
        seen.add(name)

    # 1. Explicitly named tools always run.
    for name in detect_named_tools(message):
        _add(name)

    # 2. Keyword-implied read/query tools (only if a service is resolvable, or
    #    the tool requires none).
    lowered = message.lower()
    for keyword, name in _KEYWORD_TOOL_HINTS:
        if keyword not in lowered:
            continue
        spec = TOOL_SPECS_BY_NAME[name]
        if spec.is_action:
            continue
        needs_service = "service" in spec.required or "service_name" in spec.required
        if needs_service and not service:
            continue
        _add(name)

    # 3. Investigation intent (the Incidents-page hand-off and free-form
    #    "diagnose/root cause/remediation" asks): force the evidence bundle so
    #    the model always has memory + logs + dependency data to reason from.
    if any(kw in lowered for kw in _INVESTIGATION_KEYWORDS):
        for name in _INVESTIGATION_BUNDLE:
            spec = TOOL_SPECS_BY_NAME[name]
            needs_service = "service" in spec.required or "service_name" in spec.required
            if needs_service and not service:
                continue
            _add(name)

    return ordered


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------


def missing_required(spec: ToolSpec, arguments: dict[str, Any]) -> list[str]:
    """Return required params that are absent or empty in ``arguments``."""
    missing: list[str] = []
    for name in spec.required:
        value = arguments.get(name)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(name)
    return missing


# ---------------------------------------------------------------------------
# The agentic loop
# ---------------------------------------------------------------------------

# Type of the model-completion callable: given (system_prompt, messages, tools)
# it returns the raw OpenAI-compatible response dict. ``tools`` is non-None only
# on the native path.
CompletionFn = Callable[..., Awaitable[dict[str, Any]]]

# Type of the tool executor: (tool_name, arguments) -> structured result dict
# with at least {"success": bool, "data": ..., "error": ..., "error_code": ...}.
ExecutorFn = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


def _tool_catalogue_prompt(specs: list[ToolSpec]) -> str:
    """Render the available tools + the strict-JSON protocol for the app loop."""
    lines = [
        "## Tools you can call",
        "You have access to these tools. To CALL one, reply with ONLY a JSON object:",
        '  {"tool_call": {"name": "<tool>", "arguments": { ... }}}',
        "To give your FINAL answer (no more tools needed), reply with ONLY:",
        '  {"final_answer": "<your grounded answer to the user>"}',
        "Never describe a tool call in prose and never promise to do it later — "
        "emit the JSON to actually run it, or emit the final_answer JSON. "
        "Call at most one tool per step; you will receive its result and may then "
        "call another tool or answer.",
        "",
        "Available tools:",
    ]
    for spec in specs:
        props = spec.parameters.get("properties", {})
        param_bits = []
        for pname, pschema in props.items():
            ptype = pschema.get("type", "any") if isinstance(pschema, dict) else "any"
            req = " (required)" if pname in spec.required else ""
            param_bits.append(f"{pname}:{ptype}{req}")
        lines.append(f"- {spec.name}({', '.join(param_bits)}) — {spec.description}")
    return "\n".join(lines)


def _parse_app_tool_message(content: str) -> tuple[dict[str, Any] | None, str | None]:
    """Parse an app-layer model reply into (tool_call, final_answer).

    Tolerant of markdown fences and surrounding prose: extracts the first
    balanced JSON object and reads ``tool_call`` / ``final_answer`` from it.
    Returns (None, None) when neither is present (caller treats the raw content
    as the final answer).
    """
    if not content:
        return None, None
    text = content.strip()
    # Strip a ```json ... ``` or ``` ... ``` fence if present.
    if "```" in text:
        fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if fenced:
            text = fenced.group(1).strip()

    obj = _first_json_object(text)
    if obj is None:
        return None, None

    tc = obj.get("tool_call")
    if isinstance(tc, dict) and tc.get("name"):
        name = str(tc.get("name"))
        args = tc.get("arguments")
        if not isinstance(args, dict):
            args = {}
        return {"name": name, "arguments": args}, None

    fa = obj.get("final_answer")
    if isinstance(fa, str):
        return None, fa

    return None, None


def _first_json_object(text: str) -> dict[str, Any] | None:
    """Extract and parse the first balanced top-level JSON object in ``text``."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    parsed = json.loads(candidate)
                    return parsed if isinstance(parsed, dict) else None
                except json.JSONDecodeError:
                    return None
    return None


def _summarize_result_for_model(result: dict[str, Any], max_chars: int = 1500) -> str:
    """Compact JSON of a tool result to feed back to the model (bounded)."""
    try:
        payload = {
            "success": result.get("success"),
            "data": result.get("data"),
            "error": result.get("error"),
            "error_code": result.get("error_code"),
        }
        text = json.dumps(payload, default=str)
    except (TypeError, ValueError):
        text = str(result)
    if len(text) > max_chars:
        text = text[:max_chars] + "…(truncated)"
    return text


async def _execute_one(
    executor: ExecutorFn,
    spec: ToolSpec,
    arguments: dict[str, Any],
) -> ToolCallRecord:
    """Validate params, execute the real tool, and build a ToolCallRecord."""
    call_id = f"call-{uuid.uuid4().hex[:12]}"
    missing = missing_required(spec, arguments)
    if missing:
        return ToolCallRecord(
            id=call_id,
            name=spec.name,
            arguments=arguments,
            status="needs_param",
            result={"status": "needs_param", "missing": missing},
            error=f"Missing required parameter(s): {', '.join(missing)}",
            duration_ms=0.0,
        )

    started = time.perf_counter()
    try:
        result = await executor(spec.name, arguments)
    except Exception as exc:  # noqa: BLE001 - a tool failure must not crash chat
        logger.warning("Tool %s raised during chat tool-calling: %s", spec.name, exc)
        return ToolCallRecord(
            id=call_id,
            name=spec.name,
            arguments=arguments,
            status="error",
            result=None,
            error=str(exc),
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )

    duration = round((time.perf_counter() - started) * 1000, 2)
    if not isinstance(result, dict):
        result = {"success": False, "data": None, "error": "Malformed tool result"}
    status = "ok" if result.get("success") else "error"
    return ToolCallRecord(
        id=call_id,
        name=spec.name,
        arguments=arguments,
        status=status,
        result=result if result.get("success") else result,
        error=None if result.get("success") else (result.get("error") or result.get("error_code")),
        duration_ms=duration,
    )


async def run_tool_calling_loop(
    *,
    message: str,
    system_prompt: str,
    conversation_history: list[dict[str, str]],
    service: str | None,
    completion: CompletionFn,
    executor: ExecutorFn,
    forced_calls: list[tuple[ToolSpec, dict[str, Any]]] | None = None,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    include_actions: bool | None = None,
) -> ToolLoopResult:
    """Drive the agentic tool-calling loop and return executed calls + answer.

    Args:
        message: The user's current message.
        system_prompt: The base chat system prompt (already runtime-grounded).
        conversation_history: Prior turns ``[{"role","content"}, ...]``.
        service: Resolved service for deterministic routing (may be None).
        completion: Async fn (system_prompt, messages, tools=...) -> response dict.
        executor: Async fn (tool_name, arguments) -> structured result dict
            (typically a thin wrapper over ``tools.execute_tool_call``).
        forced_calls: Pre-planned ``(spec, arguments)`` to run BEFORE the model
            speaks (deterministic routing). Defaults to
            :func:`plan_forced_tool_calls`.
        max_iterations: Cap on MODEL-driven tool rounds (bounds latency).
        include_actions: Force action-tool visibility (else env-driven).

    Returns:
        ToolLoopResult with the ordered ToolCallRecords + the final answer text.
    """
    specs = available_tool_specs(include_actions)
    native = _native_tool_calling_enabled()
    result = ToolLoopResult(native=native)

    if forced_calls is None:
        forced_calls = plan_forced_tool_calls(message, service, include_actions=include_actions)

    # 1) Deterministic pre-routing: run named/implied tools first.
    for spec, args in forced_calls:
        record = await _execute_one(executor, spec, args)
        result.tool_calls.append(record)

    # Build the transcript for the model. The app-layer loop teaches the JSON
    # protocol via an appended catalogue; the native path passes tools= instead.
    if native:
        loop_system = system_prompt
    else:
        loop_system = system_prompt + "\n\n" + _tool_catalogue_prompt(specs)

    messages: list[dict[str, Any]] = list(conversation_history or [])
    messages.append({"role": "user", "content": message})

    # Surface the forced-tool results to the model so its answer is grounded.
    for record in result.tool_calls:
        messages.append(
            {
                "role": "user",
                "content": (
                    f"[tool:{record.name} -> {record.status}] "
                    + _summarize_result_for_model(record.result or {"error": record.error})
                ),
            }
        )

    tool_defs = openai_tool_definitions(specs) if native else None

    # 2) Model-driven loop.
    for _ in range(max(0, max_iterations)):
        result.iterations += 1
        response = await completion(loop_system, messages, tool_defs)
        choice = (response.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        content = msg.get("content") or ""

        if native and msg.get("tool_calls"):
            tool_calls = msg.get("tool_calls") or []
            messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
            ran = await _run_native_tool_calls(executor, tool_calls, result, messages)
            if ran:
                continue
            # No runnable tool calls — fall through to treat content as answer.

        tool_call, final_answer = _parse_app_tool_message(content) if not native else (None, content or None)

        if tool_call is not None:
            spec = TOOL_SPECS_BY_NAME.get(tool_call["name"])
            if spec is None or (spec.is_action and spec not in specs):
                # Unknown / disabled tool requested: tell the model and continue.
                messages.append({"role": "assistant", "content": content})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"[tool:{tool_call['name']} -> error] Tool not available. "
                            "Answer using the data already gathered, or call an available tool."
                        ),
                    }
                )
                continue
            record = await _execute_one(executor, spec, tool_call["arguments"])
            result.tool_calls.append(record)
            messages.append({"role": "assistant", "content": content})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"[tool:{record.name} -> {record.status}] "
                        + _summarize_result_for_model(record.result or {"error": record.error})
                    ),
                }
            )
            continue

        # No tool requested: this is the final answer.
        result.final_answer = final_answer if final_answer is not None else content
        break

    # Loop exhausted without an explicit final answer: ask once more, plainly.
    if result.final_answer is None:
        try:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Now give your final answer to the user using the tool results "
                        "above. Reply with plain text only (no JSON, no tool calls)."
                    ),
                }
            )
            response = await completion(system_prompt, messages, None)
            choice = (response.get("choices") or [{}])[0]
            result.final_answer = (choice.get("message") or {}).get("content") or ""
        except Exception as exc:  # noqa: BLE001
            logger.warning("Final-answer completion failed: %s", exc)
            result.final_answer = ""

    return result


async def _run_native_tool_calls(
    executor: ExecutorFn,
    tool_calls: list[dict[str, Any]],
    result: ToolLoopResult,
    messages: list[dict[str, Any]],
) -> bool:
    """Execute OpenAI-native tool_calls; append tool-role results. True if any ran."""
    ran = False
    for tc in tool_calls:
        fn = (tc or {}).get("function") or {}
        name = fn.get("name")
        spec = TOOL_SPECS_BY_NAME.get(name)
        raw_args = fn.get("arguments")
        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
        except json.JSONDecodeError:
            args = {}
        if spec is None:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": json.dumps({"error": f"Unknown tool {name}"}),
                }
            )
            continue
        record = await _execute_one(executor, spec, args if isinstance(args, dict) else {})
        result.tool_calls.append(record)
        ran = True
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": _summarize_result_for_model(record.result or {"error": record.error}),
            }
        )
    return ran


__all__ = [
    "ToolSpec",
    "ToolCallRecord",
    "ToolLoopResult",
    "TOOL_SPECS_BY_NAME",
    "available_tool_specs",
    "openai_tool_definitions",
    "detect_named_tools",
    "plan_forced_tool_calls",
    "missing_required",
    "run_tool_calling_loop",
    "NATIVE_TOOL_CALLING_ENV",
    "VLLM_NATIVE_TOOL_FLAGS",
    "ACTION_TOOLS_ENV",
    "DEFAULT_MAX_ITERATIONS",
]
