"""
Constitutional AIOps - Chat API Routes

Chat endpoints for interactive conversation with the Reasoning Agent.
Supports general chat, RCA analysis, and remediation planning.
"""

import json
import logging
import os
import re
import time
import uuid
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.auth.deps import User, coerce_user, require_user
from src.api.routes.settings import get_remediation_settings
from src.api.schemas.chat import (
    AnalysisRequest,
    AnalysisResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatRole,
    ConversationHistory,
    DecisionRequest,
    DecisionResponse,
)

# Import MCP tool executor for automatic tool calls during chat
from src.api.routes.tools import execute_tool_call

# Agentic tool-calling (LangChain-style tool loop) for the chat path. Routes
# named/implied tools to the REAL executors in tools.py, runs a bounded model
# loop, and produces the ordered metadata.tool_calls contract the UI consumes.
from src.agents.tool_calling import (
    ToolCallRecord,
    ToolLoopResult,
    plan_forced_tool_calls,
    run_tool_calling_loop,
)
from src.agents.reasoning_agent import CHAT_SYSTEM_PROMPT

# Durable persistence (write-through): the in-memory dicts below stay the read
# fast-path; these helpers mirror each mutation into SQLite so conversations and
# pending actions survive a backend restart/redeploy.
from src.persistence import store as persistence_store

logger = logging.getLogger(__name__)

# Known services in the Constitutional AIOps stack
KNOWN_SERVICES = [
    "nextcloud", "neo4j", "loki", "prometheus", "grafana", "tempo",
    "backend", "frontend", "promtail", "otel-collector", "mimir"
]


def _extract_service_from_query(message: str) -> Optional[str]:
    """
    Extract service name from user query using keyword matching.

    Args:
        message: User's message/query

    Returns:
        Service name if found, None otherwise
    """
    message_lower = message.lower()
    for service in KNOWN_SERVICES:
        if service in message_lower:
            return service
    return None


# Selection-context rendering (session-14: Graph "Schema mode" → chat).
# The Schema view sends the user's node/edge selection as ChatRequest.context
# with source=="schema-graph". Before session-14 ChatRequest.context was a dead
# field (stored on the conversation, never read); now a recognised selection is
# rendered into the LLM runtime context so "ask AI about these" is grounded.
_SELECTION_MAX_ITEMS = 8           # nodes + edges combined
_SELECTION_MAX_RECENT = 2          # episode titles per node
_SELECTION_TITLE_CHARS = 80        # per episode title
_SELECTION_MAX_CHARS = 1200        # hard cap on the whole block


def _selected_known_service(ctx: Optional[dict[str, Any]]) -> Optional[str]:
    """Return the single known service in a schema-graph selection, else None.

    Lets the chat path auto-run telemetry/MCP tools for a node the user selected
    even when they didn't name it in free text.
    """
    if not isinstance(ctx, dict) or ctx.get("source") != "schema-graph":
        return None
    selection = ctx.get("selection") or {}
    nodes = selection.get("nodes") or []
    services = {
        n.get("id")
        for n in nodes
        if isinstance(n, dict) and n.get("id") in KNOWN_SERVICES
    }
    return next(iter(services)) if len(services) == 1 else None


def _render_selection_context(ctx: Optional[dict[str, Any]]) -> str:
    """Render a schema-graph selection into a compact, capped context block.

    Returns "" when ctx is absent or not a recognised schema-graph selection.
    """
    if not isinstance(ctx, dict) or ctx.get("source") != "schema-graph":
        return ""
    selection = ctx.get("selection") or {}
    nodes = [n for n in (selection.get("nodes") or []) if isinstance(n, dict)]
    edges = [e for e in (selection.get("edges") or []) if isinstance(e, dict)]
    if not nodes and not edges:
        return ""

    lines: list[str] = [
        "## User Selection (Architecture Schema view)",
        "The user selected these elements in the Graph Explorer and is asking "
        "about them. Treat the selection as the primary subject of the question.",
    ]
    shown = 0
    for n in nodes:
        if shown >= _SELECTION_MAX_ITEMS:
            break
        label = str(n.get("label") or n.get("id") or "unknown")
        kind = str(n.get("kind") or "service")
        health = str(n.get("health") or "unknown")
        eps = n.get("episode_count")
        inc = n.get("incident_count")
        detail = f"- Service \"{label}\" (kind {kind}, health {health})"
        if isinstance(eps, int):
            detail += f" — {eps} episodes"
            if isinstance(inc, int):
                detail += f", {inc} incidents"
        recent = [r for r in (n.get("recent") or []) if isinstance(r, dict)]
        if recent:
            titles = []
            for r in recent[:_SELECTION_MAX_RECENT]:
                title = str(r.get("title") or "")[:_SELECTION_TITLE_CHARS]
                sev = str(r.get("severity") or "")
                titles.append(f"\"{title}\" ({sev})" if sev else f"\"{title}\"")
            detail += "; recent: " + ", ".join(titles)
        lines.append(detail)
        shown += 1
    for e in edges:
        if shown >= _SELECTION_MAX_ITEMS:
            break
        src = str(e.get("source") or "?")
        tgt = str(e.get("target") or "?")
        rel = str(e.get("relationship") or "related to")
        co = e.get("co_episode_count")
        detail = f"- Dependency {src} → {tgt} ({rel})"
        if isinstance(co, int) and co:
            detail += f" — {co} correlated episodes"
        lines.append(detail)
        shown += 1

    total = len(nodes) + len(edges)
    if total > shown:
        lines.append(f"- …and {total - shown} more selected element(s)")

    block = "\n".join(lines)
    if len(block) > _SELECTION_MAX_CHARS:
        block = block[:_SELECTION_MAX_CHARS].rstrip() + "\n- …(truncated)"
    return block


async def _build_telemetry_context(
    request: Request,
    service: str,
    duration_minutes: int = 15
) -> tuple[str, Optional[dict[str, Any]]]:
    """
    Build telemetry context with actual logs and metrics from LGTM stack.

    Args:
        request: FastAPI request object
        service: Service name to query telemetry for
        duration_minutes: How far back to query

    Returns:
        Tuple of (formatted telemetry context string for LLM, structured dict).
        The structured dict (B3) matches metadata["tools"]["telemetry"]:
            {service, log_count, error_count, metrics:[{name,value}], sample_logs:[str]}
        Returns (\"\", None) when no telemetry data was obtained.
    """
    telemetry_collector = getattr(request.app.state, "telemetry_collector", None)
    if not telemetry_collector or not service:
        return "", None

    context_parts = []
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=duration_minutes)

    log_count = 0
    error_count = 0
    sample_log_lines: list[str] = []
    metrics_struct: list[dict[str, Any]] = []
    got_data = False

    # Query recent logs from Loki
    try:
        logs = await telemetry_collector.query_logs(
            service=service,
            start_time=start_time,
            end_time=end_time,
            limit=50,
        )
        if logs:
            got_data = True
            error_logs = [l for l in logs if l.level.lower() in ("error", "fatal", "critical")]
            warn_logs = [l for l in logs if l.level.lower() in ("warn", "warning")]
            log_count = len(logs)
            error_count = len(error_logs)

            log_text = f"## Recent Logs for {service} (last {duration_minutes} min)\n"
            log_text += f"Total: {len(logs)} logs ({len(error_logs)} errors, {len(warn_logs)} warnings)\n\n"

            # Prioritize errors, then warnings, then others
            sample_logs = (error_logs + warn_logs + logs)[:10]
            for log in sample_logs:
                timestamp_str = log.timestamp.strftime('%H:%M:%S')
                msg_preview = log.message[:200] if len(log.message) > 200 else log.message
                log_text += f"[{timestamp_str}] [{log.level}] {msg_preview}\n"

            # Structured sample (up to 5 recent lines) for the UI contract
            for log in sample_logs[:5]:
                timestamp_str = log.timestamp.strftime('%H:%M:%S')
                msg_preview = log.message[:200] if len(log.message) > 200 else log.message
                sample_log_lines.append(f"[{timestamp_str}] [{log.level}] {msg_preview}")

            context_parts.append(log_text)
    except Exception as e:
        logger.debug(f"Failed to query logs for {service}: {e}")

    # Query metrics from Prometheus
    try:
        metrics = await telemetry_collector.query_metrics(
            service=service,
            start_time=start_time,
            end_time=end_time,
        )
        if metrics:
            got_data = True
            metric_text = f"## Metrics for {service}\n"
            # Group by metric name and show latest value
            metric_latest: dict[str, float] = {}
            for m in metrics:
                metric_latest[m.name] = m.value

            for name, value in list(metric_latest.items())[:8]:
                metric_text += f"- {name}: {value:.2f}\n"
                metrics_struct.append({"name": name, "value": float(value)})

            context_parts.append(metric_text)
    except Exception as e:
        logger.debug(f"Failed to query metrics for {service}: {e}")

    if not got_data:
        return "", None

    structured = {
        "service": service,
        "log_count": log_count,
        "error_count": error_count,
        "metrics": metrics_struct,
        "sample_logs": sample_log_lines,
    }
    context_str = "\n\n".join(context_parts) if context_parts else ""
    return context_str, structured


async def _invoke_mcp_tools_for_query(
    request: Request, message: str, service: Optional[str]
) -> tuple[str, dict[str, Any]]:
    """
    Automatically invoke relevant MCP tools based on user query.

    This function analyzes the user's query and calls appropriate MCP tools:
    - find_similar: When query mentions "similar", "past", "history", or "incidents"
    - get_dependencies: When query mentions "dependencies", "impact", "upstream/downstream"
    - analyze_logs: When query mentions "logs", "errors", "analyze"

    Args:
        request: FastAPI request object
        message: User's query message
        service: Extracted service name (if any)

    Returns:
        Tuple of (formatted string with MCP tool results for LLM context,
        structured dict). The structured dict (B3) maps tool keys to their
        REAL data and is keyed by: "similar", "dependencies", "logs" (only
        present when that tool ran AND returned data).
    """
    message_lower = message.lower()
    tool_results: list[str] = []
    structured: dict[str, Any] = {}

    # Keywords that trigger each MCP tool
    similar_keywords = ["similar", "past", "history", "previous", "before", "incident"]
    dependency_keywords = ["dependency", "dependencies", "impact", "upstream", "downstream", "affects", "affected"]
    log_keywords = ["log", "logs", "error", "errors", "analyze", "pattern", "debug"]

    # 1. Call find_similar if relevant keywords present
    if any(kw in message_lower for kw in similar_keywords):
        try:
            result = await execute_tool_call(
                request,
                tool_name="find_similar",
                parameters={
                    "title": message[:200],  # Use query as search title
                    "affected_services": [service] if service else [],
                    "limit": 5
                }
            )
            if result.get("success") and result.get("data", {}).get("similar_incidents"):
                incidents = result["data"]["similar_incidents"]
                tool_results.append(f"## Similar Past Incidents (from Neo4j Memory)\n")
                for idx, inc in enumerate(incidents[:3], 1):
                    tool_results.append(
                        f"{idx}. **{inc.get('title', 'Unknown')}** "
                        f"(Severity: {inc.get('severity', 'N/A')}, "
                        f"Root Cause: {inc.get('root_cause', 'Unknown')})"
                    )
                # Structured similar list for the UI contract (C1/B3)
                struct_incidents = []
                for inc in incidents:
                    score = inc.get("similarity_score")
                    struct_incidents.append({
                        "id": inc.get("incident_id") or inc.get("episode_id") or "unknown",
                        "summary": inc.get("title", "Unknown"),
                        "score": float(score) if isinstance(score, (int, float)) else None,
                    })
                structured["similar"] = {
                    "count": len(struct_incidents),
                    "incidents": struct_incidents,
                }
            else:
                tool_results.append("## Similar Past Incidents\nNo similar incidents found in memory.")
        except Exception as e:
            logger.debug(f"find_similar tool call failed: {e}")

    # 2. Call get_dependencies if service mentioned and dependency keywords present
    if service and any(kw in message_lower for kw in dependency_keywords):
        try:
            result = await execute_tool_call(
                request,
                tool_name="get_dependencies",
                parameters={"service_name": service, "depth": 2}
            )
            if result.get("success") and result.get("data"):
                # B1 FIX: upstream/downstream are nested under data["dependencies"],
                # not directly under data.
                deps = result["data"].get("dependencies", {}) or {}
                upstream = deps.get("upstream", []) or []
                downstream = deps.get("downstream", []) or []
                tool_results.append(f"\n## Service Dependencies for {service}")
                if upstream:
                    tool_results.append(f"- Upstream: {', '.join(upstream)}")
                if downstream:
                    tool_results.append(f"- Downstream: {', '.join(downstream)}")
                if not upstream and not downstream:
                    tool_results.append("- No dependencies found in graph")
                structured["dependencies"] = {
                    "upstream": list(upstream),
                    "downstream": list(downstream),
                }
        except Exception as e:
            logger.debug(f"get_dependencies tool call failed: {e}")

    # 3. Call analyze_logs if service mentioned and log keywords present
    if service and any(kw in message_lower for kw in log_keywords):
        try:
            result = await execute_tool_call(
                request,
                tool_name="analyze_logs",
                parameters={
                    "service_name": service,
                    "time_range_minutes": 15,
                    "log_level": "error"
                }
            )
            if result.get("success") and result.get("data"):
                # B2 FIX: counts are nested under data["summary"]; error patterns
                # live under data["top_errors"] (list of {pattern,count}); there is
                # NO top-level "patterns"/"total_logs"/"error_count" key.
                log_data = result["data"]
                summary = log_data.get("summary", {}) or {}
                total_logs = summary.get("total_logs", 0)
                error_count = summary.get("error_count", 0)
                warning_count = summary.get("warning_count", 0)
                top_errors_raw = log_data.get("top_errors", []) or []

                tool_results.append(f"\n## Log Analysis for {service}")
                tool_results.append(f"- Total logs: {total_logs}")
                tool_results.append(f"- Error count: {error_count}")
                if top_errors_raw:
                    top_patterns = [
                        str(e.get("pattern", "")) for e in top_errors_raw[:3]
                        if e.get("pattern")
                    ]
                    if top_patterns:
                        tool_results.append(f"- Top error patterns: {', '.join(top_patterns)}")

                structured["logs"] = {
                    "total_logs": total_logs,
                    "error_count": error_count,
                    "warning_count": warning_count,
                    "top_errors": [
                        {"pattern": str(e.get("pattern", "")), "count": e.get("count", 0)}
                        for e in top_errors_raw
                    ],
                }
        except Exception as e:
            logger.debug(f"analyze_logs tool call failed: {e}")

    if tool_results:
        logger.info(f"MCP tools invoked for query, {len(tool_results)} results")
        return "\n".join(tool_results), structured
    return "", structured


# ---------------------------------------------------------------------------
# Agentic tool-calling integration (proper LangChain-style tool loop)
# ---------------------------------------------------------------------------

# Cap the model-driven tool rounds so chat latency stays bounded. Use ``or "3"``
# so an empty-string env (compose declares CHAT_MAX_TOOL_ITERATIONS=${...:-})
# falls back to the default instead of crashing on int("").
_CHAT_MAX_TOOL_ITERATIONS = int(os.getenv("CHAT_MAX_TOOL_ITERATIONS") or "3")


def _make_chat_executor(request: Request):
    """Build the executor the tool loop calls: routes to the REAL tools.py.

    Wraps ``execute_tool_call`` so every tool the agent runs hits live
    Neo4j/Loki/Prometheus/Docker via the same code path the MCP page uses
    (action tools still flow through the constitutional gate inside it).
    """

    from src.agents.tool_calling import TOOL_SPECS_BY_NAME

    async def _executor(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        spec = TOOL_SPECS_BY_NAME.get(tool_name)
        # Action tools carry evidence/audit context so the constitutional gate
        # can evaluate them (mirrors _maybe_propose_remediation); read tools take
        # the legacy 3-arg signature so existing call sites/mocks stay valid.
        # Never force past the gate — execute_tool_call owns that.
        if spec is not None and spec.is_action:
            context = {
                "source": "chat_agent",
                "audit_enabled": _audit_enabled(),
                "telemetry_evidence": True,
            }
            return await execute_tool_call(
                request, tool_name=tool_name, parameters=arguments, context=context
            )
        return await execute_tool_call(
            request, tool_name=tool_name, parameters=arguments
        )

    return _executor


def _make_chat_completion(reasoning_agent: Any, *, enable_thinking: bool):
    """Build the model-completion callable for the tool loop.

    Prefers the raw ModelRouter (so the model can emit JSON / native tool calls
    in a multi-turn transcript). Falls back to ``reasoning_agent.chat`` when the
    router is unavailable or does not behave like one (e.g. test MagicMocks):
    that path simply returns a single grounded answer from the model, which —
    combined with deterministic pre-routing — still executes every named/implied
    tool and answers WITH the data.
    """
    model_router = getattr(reasoning_agent, "model_router", None)
    system_prompt_for_chat = None
    try:
        system_prompt_for_chat = reasoning_agent.get_system_prompt("chat")
    except Exception:  # noqa: BLE001
        system_prompt_for_chat = None

    async def _completion(
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]],
    ) -> dict[str, Any]:
        # Flatten the transcript into a single user prompt for reasoning_completion
        # (which takes prompt + system_prompt). The system prompt already carries
        # the runtime context + tool-call protocol assembled by the loop.
        prompt_lines: list[str] = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if not content:
                continue
            prompt_lines.append(f"{role}: {content}")
        prompt = "\n".join(prompt_lines) if prompt_lines else ""

        completion_fn = getattr(model_router, "reasoning_completion", None)
        if callable(completion_fn):
            kwargs: dict[str, Any] = {
                "prompt": prompt,
                "max_tokens": 2048,
                "temperature": 0.3,
                "enable_thinking": enable_thinking,
                "system_prompt": system_prompt,
            }
            if tools:
                # Native vLLM tool-calling path (opt-in via AIOPS_NATIVE_TOOL_CALLING).
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            try:
                return await completion_fn(**kwargs)
            except Exception as exc:  # noqa: BLE001 - fall back to .chat below
                logger.debug("reasoning_completion failed, falling back to chat(): %s", exc)

        # Fallback: drive the agent's chat() which injects runtime context itself.
        agent_response = await reasoning_agent.chat(
            message=messages[-1].get("content", "") if messages else "",
            conversation_history=[m for m in messages[:-1]],
            runtime_context=None,
            enable_thinking=enable_thinking,
        )
        return {"choices": [{"message": {"content": getattr(agent_response, "content", "")}}]}

    # The router path needs a real chat system prompt; the loop appends the tool
    # catalogue. When we only have .chat (fallback), the agent injects its own.
    _completion.system_prompt_for_chat = system_prompt_for_chat  # type: ignore[attr-defined]
    return _completion


def _tool_records_to_back_compat(
    records: list[ToolCallRecord],
) -> dict[str, Any]:
    """Map executed ToolCallRecords to the legacy metadata['tools'] sub-object.

    Keeps populating ``similar`` / ``dependencies`` / ``logs`` for back-compat so
    existing UI cards keep working alongside the new ordered tool_calls list.
    Only includes a key when that tool ran AND returned real data.
    """
    out: dict[str, Any] = {}
    for rec in records:
        if rec.status != "ok" or not isinstance(rec.result, dict):
            continue
        data = rec.result.get("data") or {}
        if rec.name == "find_similar":
            incidents = data.get("similar_incidents") or []
            if incidents:
                struct_incidents = []
                for inc in incidents:
                    score = inc.get("similarity_score")
                    struct_incidents.append(
                        {
                            "id": inc.get("incident_id") or inc.get("episode_id") or "unknown",
                            "summary": inc.get("title", "Unknown"),
                            "score": float(score) if isinstance(score, (int, float)) else None,
                        }
                    )
                out["similar"] = {"count": len(struct_incidents), "incidents": struct_incidents}
        elif rec.name == "get_dependencies":
            deps = data.get("dependencies", {}) or {}
            upstream = deps.get("upstream", []) or []
            downstream = deps.get("downstream", []) or []
            if upstream or downstream:
                out["dependencies"] = {
                    "upstream": list(upstream),
                    "downstream": list(downstream),
                }
        elif rec.name == "analyze_logs":
            summary = data.get("summary", {}) or {}
            top_errors_raw = data.get("top_errors", []) or []
            out["logs"] = {
                "total_logs": summary.get("total_logs", 0),
                "error_count": summary.get("error_count", 0),
                "warning_count": summary.get("warning_count", 0),
                "top_errors": [
                    {"pattern": str(e.get("pattern", "")), "count": e.get("count", 0)}
                    for e in top_errors_raw
                ],
            }
    return out


# Enable the FULL model-driven tool loop (the 14B chooses extra tools itself)
# on top of deterministic routing. Off by default so the proven single-answer
# chat flow + refusal guard stays the source of truth; flip on once the model
# router reliably emits the JSON/native tool protocol.
def _agentic_loop_enabled() -> bool:
    return os.getenv("CHAT_AGENTIC_TOOL_LOOP", "").strip().lower() in ("1", "true", "yes")


def _records_to_context_string(records: list[ToolCallRecord]) -> str:
    """Render executed tool results into an LLM context block (grounds the answer).

    Mirrors the human-readable summaries the old _invoke_mcp_tools_for_query
    produced, plus a structured needs_param note so the model can ask the user
    for a missing parameter instead of narrating.
    """
    blocks: list[str] = []
    for rec in records:
        if rec.status == "needs_param":
            missing = (rec.result or {}).get("missing", []) if isinstance(rec.result, dict) else []
            blocks.append(
                f"## Tool {rec.name}: needs parameter(s) {', '.join(missing) or 'unknown'}\n"
                f"Ask the user to provide: {', '.join(missing) or 'the missing parameter'}."
            )
            continue
        if rec.status != "ok" or not isinstance(rec.result, dict):
            blocks.append(f"## Tool {rec.name} failed: {rec.error or 'no data'}")
            continue
        data = rec.result.get("data") or {}
        if rec.name == "find_similar":
            incidents = data.get("similar_incidents") or []
            if incidents:
                lines = ["## Similar Past Incidents (from Neo4j Memory)"]
                for idx, inc in enumerate(incidents[:3], 1):
                    lines.append(
                        f"{idx}. {inc.get('title', 'Unknown')} "
                        f"(Severity: {inc.get('severity', 'N/A')}, "
                        f"Root Cause: {inc.get('root_cause', 'Unknown')})"
                    )
                blocks.append("\n".join(lines))
            else:
                blocks.append("## Similar Past Incidents\nNo similar incidents found in memory.")
        elif rec.name == "get_dependencies":
            deps = data.get("dependencies", {}) or {}
            up = deps.get("upstream", []) or []
            down = deps.get("downstream", []) or []
            lines = [f"## Service Dependencies for {data.get('service', '')}"]
            if up:
                lines.append(f"- Upstream: {', '.join(up)}")
            if down:
                lines.append(f"- Downstream: {', '.join(down)}")
            if not up and not down:
                lines.append("- No dependencies found in graph")
            blocks.append("\n".join(lines))
        elif rec.name == "analyze_logs":
            summary = data.get("summary", {}) or {}
            top = data.get("top_errors", []) or []
            lines = [
                f"## Log Analysis for {data.get('service', '')}",
                f"- Total logs: {summary.get('total_logs', 0)}",
                f"- Error count: {summary.get('error_count', 0)}",
            ]
            patterns = [str(e.get("pattern", "")) for e in top[:3] if e.get("pattern")]
            if patterns:
                lines.append(f"- Top error patterns: {', '.join(patterns)}")
            blocks.append("\n".join(lines))
        else:
            # Generic compact rendering for the remaining tools.
            blocks.append(f"## Tool {rec.name} result\n{json.dumps(data, default=str)[:800]}")
    return "\n\n".join(blocks)


async def _execute_chat_tools(
    request: Request,
    reasoning_agent: Any,
    *,
    message: str,
    conversation_history: list[dict[str, str]],
    service: Optional[str],
    runtime_context: str,
    enable_thinking: bool,
) -> ToolLoopResult:
    """Run tool-calling for one chat turn and return the executed tool records.

    Default mode: deterministic pre-routing only (every NAMED or clearly-IMPLIED
    tool is executed against the REAL tools.py executors). When
    ``CHAT_AGENTIC_TOOL_LOOP`` is enabled, the full model-driven loop also runs
    so the 14B itself can request additional tools (app-layer JSON protocol, or
    native vLLM tool-calling when AIOPS_NATIVE_TOOL_CALLING is set).

    The grounded final ANSWER is still produced by the existing
    ``reasoning_agent.chat`` flow in the caller (which carries the refusal
    guard); this function's ``final_answer`` is only populated in agentic mode
    and is treated as advisory.
    """
    executor = _make_chat_executor(request)
    forced = plan_forced_tool_calls(message, service)

    if not _agentic_loop_enabled():
        # Deterministic routing only: execute the planned calls in order.
        from src.agents.tool_calling import _execute_one  # local import: internal helper

        result = ToolLoopResult()
        for spec, args in forced:
            result.tool_calls.append(await _execute_one(executor, spec, args))
        return result

    completion = _make_chat_completion(reasoning_agent, enable_thinking=enable_thinking)
    base_system = getattr(completion, "system_prompt_for_chat", None) or CHAT_SYSTEM_PROMPT
    system_prompt = base_system.replace(
        "{runtime_context}", f"## Current System State\n{runtime_context}"
    )
    return await run_tool_calling_loop(
        message=message,
        system_prompt=system_prompt,
        conversation_history=conversation_history,
        service=service,
        completion=completion,
        executor=executor,
        forced_calls=forced,
        max_iterations=_CHAT_MAX_TOOL_ITERATIONS,
    )


async def _build_runtime_context(request: Request) -> str:
    """
    Build runtime context string for LLM with current system state.

    This provides the LLM with real-time information about:
    - Running containers and their status
    - LLM agent health
    - Demo mode status
    - Available tools and capabilities
    """
    context_parts = []

    # 1. Container Status from infrastructure
    try:
        from src.api.routes.infrastructure import (
            _get_docker_client,
            _monitored_containers,
        )

        docker_client = _get_docker_client()
        if docker_client:
            try:
                all_containers = docker_client.containers.list(all=True)
                container_list = []
                for container in all_containers:
                    if container.name in _monitored_containers:
                        status_str = "RUNNING" if container.status == "running" else container.status.upper()
                        container_list.append(f"  - {container.name}: {status_str}")

                if container_list:
                    context_parts.append("## Current Container Status\n" + "\n".join(container_list))
                else:
                    context_parts.append("## Current Container Status\nNo monitored containers found. Docker is running but no AIOps containers are active.")
            except Exception as e:
                logger.warning(f"Failed to get container status: {e}")
                context_parts.append(f"## Current Container Status\nFailed to query containers: {e}")
            finally:
                docker_client.close()
        else:
            context_parts.append("## Current Container Status\nDocker is not available. Cannot query container status.")
    except Exception as e:
        logger.warning(f"Container context unavailable: {e}")
        context_parts.append("## Current Container Status\nDocker connection unavailable.")

    # 2. LLM Agent Health
    model_router = getattr(request.app.state, "model_router", None)
    if model_router:
        try:
            health = await model_router.health_check()
            fast_status = "ONLINE" if health.get("fast_agent") else "OFFLINE"
            reasoning_status = "ONLINE" if health.get("reasoning_agent") else "OFFLINE"
            context_parts.append(
                f"## LLM Agent Status\n  - Fast Agent (Qwen3-4B): {fast_status}\n  - Reasoning Agent (Qwen3-14B): {reasoning_status}"
            )
        except Exception as e:
            logger.warning(f"Agent health context unavailable: {e}")
            context_parts.append("## LLM Agent Status\n  - Health check failed. Agents may be unavailable.")
    else:
        context_parts.append("## LLM Agent Status\n  - Model router not initialized.")

    # 3. Demo Mode Status
    try:
        from src.api.routes.demo import _demo_state

        if _demo_state.get("active"):
            context_parts.append(
                f"## Demo Mode\n  - Status: ACTIVE\n  - Anomalies triggered: {_demo_state.get('anomalies_triggered', 0)}\n  - Target container: {_demo_state.get('container_name', 'nextcloud')}"
            )
    except Exception as e:
        logger.debug(f"Demo status context unavailable: {e}")

    # 4. Available Tools and Capabilities
    context_parts.append(
        """## Available Tools & Capabilities
  - Container monitoring and real-time status
  - CPU/Memory/Disk stress injection (demo mode)
  - Incident creation and tracking
  - Root Cause Analysis (RCA)
  - Remediation action suggestions
  - Graph-based service dependency analysis (Neo4j)
  - Telemetry from LGTM stack (Loki, Grafana, Tempo, Prometheus)"""
    )

    return "\n\n".join(context_parts) if context_parts else "## Runtime Context\nNo runtime data available"

router = APIRouter()

# In-memory conversation store (replace with Redis/Neo4j in production)
_conversations: dict[str, ConversationHistory] = {}

# Cap the in-memory store so a long-lived process (plus e2e suites) can't grow
# it unboundedly: beyond the cap, the least-recently-updated conversations are
# evicted on each new-conversation create.
_MAX_CONVERSATIONS = int(os.getenv("CHAT_MAX_CONVERSATIONS", "200"))


# Write-through helpers: persist failures must NEVER break a chat request, so
# every durable write is best-effort (logged, swallowed). The in-memory dict is
# always updated first and remains the read fast-path.
def _persist_save_conversation(conversation: ConversationHistory) -> None:
    try:
        persistence_store.save_conversation(conversation)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist conversation %s: %s", conversation.conversation_id, exc)


def _persist_delete_conversation(conversation_id: str) -> None:
    try:
        persistence_store.delete_conversation(conversation_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to delete persisted conversation %s: %s", conversation_id, exc)


def _persist_save_pending_action(action_id: str, entry: dict[str, Any]) -> None:
    try:
        persistence_store.save_pending_action(action_id, entry)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist pending action %s: %s", action_id, exc)


def _persist_delete_pending_action(action_id: str) -> None:
    try:
        persistence_store.delete_pending_action(action_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to delete persisted pending action %s: %s", action_id, exc)


def _evict_stale_conversations() -> None:
    """Drop the oldest conversations once the store exceeds _MAX_CONVERSATIONS."""
    overflow = len(_conversations) - _MAX_CONVERSATIONS
    if overflow <= 0:
        return
    by_age = sorted(_conversations.values(), key=lambda c: c.updated_at)
    for conv in by_age[:overflow]:
        _conversations.pop(conv.conversation_id, None)
        _persist_delete_conversation(conv.conversation_id)
    logger.info(f"Evicted {overflow} stale conversation(s) (cap {_MAX_CONVERSATIONS})")


def _can_access(conversation: ConversationHistory, user: User) -> bool:
    """Per-user data scoping: a conversation is visible to its owner; legacy
    owner-less (None) conversations are visible to admins only."""
    owner = getattr(conversation, "owner", None)
    if owner == user.username:
        return True
    return owner is None and user.role == "admin"


# ---------------------------------------------------------------------------
# Remediation (Lane B): proposed-action cache + auto-exec interlocks
# ---------------------------------------------------------------------------

# In-memory cache of remediation actions proposed in approve/auto mode but not
# yet decided. Mirrors how _conversations is managed: capped + TTL-evicted on
# each insert. Each entry: {tool_name, parameters, owner, conversation_id,
# created_at, proposed_action}. The constitutional gate still runs inside
# execute_tool_call at decision time — this cache holds intent only, never grants.
_pending_actions: dict[str, dict[str, Any]] = {}

# Cap + TTL so a long-lived process (and the e2e suites) can't grow it forever.
_MAX_PENDING_ACTIONS = int(os.getenv("CHAT_MAX_PENDING_ACTIONS", "100"))
_PENDING_ACTION_TTL_SECONDS = int(os.getenv("CHAT_PENDING_ACTION_TTL", "1800"))  # 30 min

# Restart-style action tool we may propose. Read-only here; execution is gated
# inside execute_tool_call (tools.py owns the whitelist + AIOPS_ENABLE_ACTION_TOOLS).
_REMEDIATION_TOOL_NAME = "restart_service"

# Container names we may propose a restart for. Kept deliberately small and
# display-oriented; the REAL authority is tools.py's gate/whitelist.
_REMEDIATION_WHITELIST = {"nextcloud", "nextcloud-db"}

# Simple in-process auto-exec rate limit: at most _AUTO_EXEC_MAX in the trailing
# window. A module-level deque of recent auto-exec timestamps (monotonic).
_AUTO_EXEC_MAX = int(os.getenv("CHAT_AUTO_EXEC_MAX_PER_MIN", "5"))
_AUTO_EXEC_WINDOW_SECONDS = 60.0
_auto_exec_times: deque[float] = deque()

# Detects an explicit "restart <container>" instruction in RCA / suggested text.
_RESTART_RE = re.compile(
    r"\brestart(?:ing|\s+the)?\s+(?:the\s+|container\s+)?"
    r"([A-Za-z0-9][A-Za-z0-9_.-]*)",
    re.IGNORECASE,
)


def _evict_stale_pending_actions() -> None:
    """Drop expired (TTL) pending actions, then the oldest beyond the cap."""
    now = time.time()
    expired = [
        aid
        for aid, entry in _pending_actions.items()
        if now - entry.get("created_at", now) > _PENDING_ACTION_TTL_SECONDS
    ]
    for aid in expired:
        _pending_actions.pop(aid, None)
        _persist_delete_pending_action(aid)
    overflow = len(_pending_actions) - _MAX_PENDING_ACTIONS
    if overflow > 0:
        by_age = sorted(_pending_actions.items(), key=lambda kv: kv[1].get("created_at", 0.0))
        for aid, _ in by_age[:overflow]:
            _pending_actions.pop(aid, None)
            _persist_delete_pending_action(aid)
    if expired or overflow > 0:
        logger.info(
            "Evicted pending action(s): %d expired, %d over-cap",
            len(expired), max(0, overflow),
        )


def _detect_remediation_action(
    content: str,
    suggested_actions: Optional[list[str]],
    service: Optional[str],
) -> Optional[dict[str, str]]:
    """Detect a concrete restart-style remediation from the RCA reasoning.

    Scans (a) the model's suggested actions and (b) the reply body for an
    explicit "restart <container>" naming a whitelisted container. Returns
    ``{"service_name": <container>, "reason": <line>}`` or None when no clear,
    whitelisted restart action is present. Display-only detection: actual
    authority to run lives behind execute_tool_call's constitutional gate.
    """
    candidates: list[str] = list(suggested_actions or [])
    if content:
        candidates.extend(content.split("\n"))

    for line in candidates:
        if not line or "restart" not in line.lower():
            continue
        m = _RESTART_RE.search(line)
        if not m:
            continue
        target = m.group(1).strip().strip(".,:;").lower()
        if target in _REMEDIATION_WHITELIST:
            return {"service_name": target, "reason": line.strip()[:200]}

    # Fall back to the named service when the model said "restart it/the service"
    # without naming the container explicitly but the query subject is whitelisted.
    if service and service in _REMEDIATION_WHITELIST:
        for line in candidates:
            if line and "restart" in line.lower():
                return {"service_name": service, "reason": line.strip()[:200]}
    return None


def _action_target(service_name: str) -> str:
    """Display-only routing metadata (mirrors Lane A's default: db -> t3)."""
    return "t3" if service_name == "nextcloud-db" else "local"


def _build_proposed_action(
    detected: dict[str, str],
    mode: str,
    status_value: str,
) -> dict[str, Any]:
    """Assemble the proposed_action payload (CONTRACT 3)."""
    service_name = detected["service_name"]
    reason = detected.get("reason", "AI-proposed remediation")
    return {
        "id": f"act-{uuid.uuid4().hex[:12]}",
        "tool_name": _REMEDIATION_TOOL_NAME,
        "parameters": {"service_name": service_name, "reason": reason},
        "target": _action_target(service_name),
        "title": f"Restart {service_name}",
        "rationale": reason,
        "mode": mode,
        "status": status_value,
        "verdict": None,
        "execution_result": None,
    }


def _auto_exec_max_per_min() -> int:
    """Resolve the per-minute auto-exec cap.

    Honours the persisted ``constitutional.maxActionsPerMinute`` operator
    setting (previously a dead no-op), falling back to the
    ``CHAT_AUTO_EXEC_MAX_PER_MIN`` env / default when it is absent or
    unreadable. The settings read is best-effort so a missing store never
    breaks the rate check.
    """
    try:
        from src.api.routes.settings import get_constitutional_settings

        value = get_constitutional_settings().get("maxActionsPerMinute")
        if isinstance(value, (int, float)) and value > 0:
            return int(value)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not read persisted maxActionsPerMinute: %s", exc)
    return _AUTO_EXEC_MAX


def _audit_enabled() -> bool:
    """Resolve the persisted ``constitutional.enableAuditLog`` toggle.

    Previously a dead no-op (call sites hardcoded ``audit_enabled=True``). Reads
    the persisted setting, defaulting to True (audit-on) when unset/unreadable —
    auditing is the safe default for a constitutional system.
    """
    try:
        from src.api.routes.settings import get_constitutional_settings

        return bool(get_constitutional_settings().get("enableAuditLog", True))
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not read persisted enableAuditLog: %s", exc)
        return True


def _auto_exec_rate_ok() -> bool:
    """True when another auto-exec is within the rolling per-minute cap.

    On success the caller records the timestamp via _record_auto_exec(); this
    check is side-effect free so a failed interlock doesn't consume budget.
    The cap comes from the persisted constitutional settings (falling back to
    the env/default).
    """
    now = time.monotonic()
    while _auto_exec_times and now - _auto_exec_times[0] > _AUTO_EXEC_WINDOW_SECONDS:
        _auto_exec_times.popleft()
    return len(_auto_exec_times) < _auto_exec_max_per_min()


def _record_auto_exec() -> None:
    """Record an auto-exec attempt against the rate-limit window."""
    _auto_exec_times.append(time.monotonic())


def _extract_verdict(result: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Pull the constitutional verdict out of an execute_tool_call result.

    execute_tool_call surfaces the verdict via metadata["constitutional"] when
    present (and may also expose a top-level "verdict"); read both defensively
    so the shape change in tools.py — if any — doesn't break us. None otherwise.
    """
    if not isinstance(result, dict):
        return None
    verdict = result.get("verdict")
    if isinstance(verdict, dict):
        return verdict
    meta = result.get("metadata")
    if isinstance(meta, dict) and isinstance(meta.get("constitutional"), dict):
        return meta["constitutional"]
    return None


async def _maybe_propose_remediation(
    request: Request,
    *,
    mode: str,
    content: str,
    suggested_actions: Optional[list[str]],
    service: Optional[str],
    confidence: Optional[float],
    has_tool_data: bool,
    remediation_settings: dict[str, Any],
    owner: str,
    conversation_id: str,
) -> Optional[dict[str, Any]]:
    """Build (and in auto mode, maybe execute) a proposed remediation action.

    Returns the proposed_action dict to attach to the ChatResponse, or None in
    diagnose mode / when no concrete whitelisted restart action was detected.

    approve: status "proposed", cached, NOT executed.
    auto:    if confidence >= threshold AND (evidence not required OR present)
             AND rate-limit OK -> execute via the gated execute_tool_call. The
             gate may DEGRADE the outcome to "proposed" (approval_required /
             validation_blocked) — we never force past the validator. Otherwise
             "auto_executed" (+verdict+execution_result). Any failed interlock
             degrades to "proposed" (cached for later approval).
    """
    if mode == "diagnose":
        return None

    detected = _detect_remediation_action(content, suggested_actions, service)
    if detected is None:
        return None

    proposed = _build_proposed_action(detected, mode, status_value="proposed")

    def _cache(action: dict[str, Any]) -> None:
        entry = {
            "tool_name": action["tool_name"],
            "parameters": action["parameters"],
            "owner": owner,
            "conversation_id": conversation_id,
            "created_at": time.time(),
            "proposed_action": action,
            # Carry the real evidence-based chat confidence so that when the user
            # later approves this action (decide_action), the constitutional gate
            # records the TRUE confidence instead of a synthesized auto-threshold.
            "confidence": confidence,
        }
        _pending_actions[action["id"]] = entry
        _persist_save_pending_action(action["id"], entry)
        _evict_stale_pending_actions()

    if mode == "approve":
        _cache(proposed)
        return proposed

    # mode == "auto": evaluate the interlocks.
    threshold = float(remediation_settings.get("autoConfidenceThreshold", 90)) / 100.0
    require_evidence = bool(remediation_settings.get("requireEvidenceForAuto", True))

    confidence_ok = confidence is not None and confidence >= threshold
    evidence_ok = (not require_evidence) or has_tool_data
    rate_ok = _auto_exec_rate_ok()

    if not (confidence_ok and evidence_ok and rate_ok):
        logger.info(
            "Auto-exec interlocks not met (confidence_ok=%s evidence_ok=%s rate_ok=%s); "
            "degrading to proposed",
            confidence_ok, evidence_ok, rate_ok,
        )
        _cache(proposed)
        return proposed

    # All interlocks held: attempt the gated execution. The constitutional gate
    # + AIOPS_ENABLE_ACTION_TOOLS kill-switch both live inside execute_tool_call.
    _record_auto_exec()
    try:
        # Forward the RCA confidence (already >= threshold) + telemetry evidence
        # to the constitutional gate so it can authorize; without these the gate
        # defaults to confidence 0.5 / no-evidence and ALWAYS blocks. Tier-1
        # safety principles are still enforced independently inside the gate.
        result = await execute_tool_call(
            request,
            tool_name=proposed["tool_name"],
            parameters={**proposed["parameters"], "confidence": confidence},
            context={"telemetry_evidence": bool(has_tool_data), "audit_enabled": _audit_enabled()},
        )
    except Exception as exc:  # noqa: BLE001 - never let remediation break chat
        logger.warning("Auto-exec call raised; degrading to proposed: %s", exc)
        _cache(proposed)
        return proposed

    verdict = _extract_verdict(result)
    error_code = result.get("error_code")

    if result.get("success"):
        proposed["status"] = "auto_executed"
        proposed["verdict"] = verdict
        proposed["execution_result"] = result.get("data")
        # Executed: no pending entry needed (nothing left to approve).
        return proposed

    # Gate asked for a human or blocked the action: DEGRADE, never force past.
    if error_code in ("approval_required", "validation_blocked"):
        proposed["status"] = "proposed"
        proposed["verdict"] = verdict
        _cache(proposed)
        return proposed

    # Any other failure (disabled kill-switch, execution error, …): surface as
    # blocked so the UI shows it didn't run, and cache for a manual retry.
    proposed["status"] = "blocked"
    proposed["verdict"] = verdict
    proposed["execution_result"] = {"error": result.get("error"), "error_code": error_code}
    _cache(proposed)
    return proposed


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Send Chat Message",
    description="Send a message to the Reasoning Agent and get a response",
)
async def chat(
    request: Request,
    chat_request: ChatRequest,
    user: User = Depends(require_user),
) -> ChatResponse:
    """
    Send a message to the Reasoning Agent.

    The agent can help with:
    - Answering questions about incidents
    - Explaining system behavior
    - Suggesting remediation steps
    - Providing context from graph memory

    Args:
        chat_request: User message and optional context

    Returns:
        Assistant's response with confidence and suggestions
    """
    user = coerce_user(user)

    # Get or create conversation
    conversation_id = chat_request.conversation_id or f"conv-{uuid.uuid4().hex[:12]}"

    if conversation_id in _conversations:
        conversation = _conversations[conversation_id]
        if not _can_access(conversation, user):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )
        # Refresh the stored selection context so a fresh Schema-mode selection
        # (or a hand-off from the full Chat page) updates an existing thread.
        if chat_request.context is not None:
            conversation.context = chat_request.context
    else:
        conversation = ConversationHistory(
            conversation_id=conversation_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            messages=[],
            context=chat_request.context,
            owner=user.username,
        )
        _conversations[conversation_id] = conversation
        _persist_save_conversation(conversation)
        _evict_stale_conversations()

    # Add user message
    user_message = ChatMessage(
        role=ChatRole.USER,
        content=chat_request.message,
        timestamp=datetime.utcnow(),
    )
    conversation.messages.append(user_message)
    conversation.updated_at = datetime.utcnow()
    _persist_save_conversation(conversation)

    # Get reasoning agent
    reasoning_agent = getattr(request.app.state, "reasoning_agent", None)

    if reasoning_agent is None:
        logger.error("Reasoning agent not initialized - LLM server may be unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reasoning agent not initialized. Check LLM server connection.",
        )

    try:
        # Build conversation history for context
        history = [
            {"role": msg.role.value, "content": msg.content}
            for msg in conversation.messages[-5:]  # Last 5 messages
        ]

        # Build runtime context with current system state
        runtime_context = await _build_runtime_context(request)

        # Selection context from the Graph "Schema mode" (session-14). Prefer the
        # context on this turn; fall back to the conversation's stored selection.
        selection_ctx = chat_request.context or conversation.context
        selection_context = _render_selection_context(selection_ctx)

        # Extract service from query and get real telemetry data. If the user
        # named no service but selected exactly one in the schema view, use it so
        # the telemetry/MCP auto-tools below run for the selected node.
        service = _extract_service_from_query(chat_request.message)
        if service is None:
            service = _selected_known_service(selection_ctx)
        telemetry_context = ""
        telemetry_struct: Optional[dict[str, Any]] = None
        if service:
            telemetry_context, telemetry_struct = await _build_telemetry_context(request, service)
            logger.info(f"Built telemetry context for service: {service}")

        # Agentic tool-calling: deterministically route NAMED/IMPLIED tools to the
        # REAL executors in tools.py (and optionally let the model drive extra
        # tools when CHAT_AGENTIC_TOOL_LOOP is enabled). This replaces the old
        # keyword-only _invoke_mcp_tools_for_query so a named tool ALWAYS runs.
        loop_result = await _execute_chat_tools(
            request,
            reasoning_agent,
            message=chat_request.message,
            conversation_history=history[:-1],
            service=service,
            runtime_context=runtime_context,
            enable_thinking=chat_request.enable_thinking,
        )
        tool_call_records = loop_result.tool_calls
        # Ordered tool_calls contract (THE UI source of truth).
        tool_calls_meta = [rec.to_dict() for rec in tool_call_records]
        # Human-readable context block grounding the model's answer.
        mcp_tool_context = _records_to_context_string(tool_call_records)
        # Back-compat structured tools (similar / dependencies / logs).
        tool_struct = _tool_records_to_back_compat(tool_call_records)

        # Combine selection + telemetry + MCP tools + runtime context for the LLM.
        # The user's explicit selection leads so the model treats it as the subject.
        full_context = runtime_context
        if mcp_tool_context:
            full_context = mcp_tool_context + "\n\n" + full_context
        if telemetry_context:
            full_context = telemetry_context + "\n\n" + full_context
        if selection_context:
            full_context = selection_context + "\n\n" + full_context

        # Assemble structured tool metadata (B3 / THE CONTRACT). Only include a key
        # for a tool that actually ran and returned real data.
        tools_meta: dict[str, Any] = {}
        if telemetry_struct:
            tools_meta["telemetry"] = telemetry_struct
        if tool_struct.get("similar"):
            tools_meta["similar"] = tool_struct["similar"]
        if tool_struct.get("dependencies"):
            tools_meta["dependencies"] = tool_struct["dependencies"]
        if tool_struct.get("logs"):
            tools_meta["logs"] = tool_struct["logs"]

        # Did any tool / telemetry return real data? (used by the refusal guard + confidence)
        # tool_calls_meta on its own counts as evidence even when no back-compat
        # key matched (e.g. list_containers / query_metric ran).
        any_tool_ran = any(rec.status == "ok" for rec in tool_call_records)
        has_tool_data = bool(tools_meta) or any_tool_ran

        # Get response from reasoning agent with full context (including real telemetry)
        agent_response = await reasoning_agent.chat(
            message=chat_request.message,
            conversation_history=history[:-1],  # Exclude current message
            runtime_context=full_context,
            enable_thinking=chat_request.enable_thinking,  # B5
        )

        content = agent_response.content

        # D1(b): deterministic over-refusal guard. The backend knows the query is
        # in-domain when a known service was named OR any tool returned data. If the
        # model still produced a refusal-shaped reply, re-issue ONCE with a forceful
        # directive; if it STILL refuses, synthesize an answer from gathered data.
        in_domain = service is not None or has_tool_data
        if in_domain and _looks_like_refusal(content):
            logger.info("Chat reply looked like a refusal for an in-domain query; re-issuing")
            forced_context = full_context + (
                "\n\n## IMPORTANT\n"
                f"This request concerns the monitored service '{service or 'this system'}' "
                "and IS in scope. Answer it fully using the data above. Do NOT decline."
            )
            try:
                retry_response = await reasoning_agent.chat(
                    message=chat_request.message,
                    conversation_history=history[:-1],
                    runtime_context=forced_context,
                    enable_thinking=chat_request.enable_thinking,
                )
                if not _looks_like_refusal(retry_response.content):
                    agent_response = retry_response
                    content = retry_response.content
                else:
                    # Still refusing: synthesize a concise answer from gathered data.
                    content = _synthesize_answer_from_data(
                        service, telemetry_struct, tool_struct
                    )
                    agent_response.content = content
            except Exception as e:
                logger.warning(f"Refusal re-issue failed: {e}")
                content = _synthesize_answer_from_data(
                    service, telemetry_struct, tool_struct
                )
                agent_response.content = content

        # A1: confidence follows EVIDENCE, not the model's (free-form) refusal
        # wording. When no known service was named AND no tool/telemetry data was
        # gathered, there is no basis to score the answer (and it's likely an
        # off-domain decline) => None, so the UI hides the gauge. Otherwise it's
        # the evidence-based score. This is deterministic and does not depend on
        # brittle refusal-phrase matching (the model declines in varied wording).
        confidence = (
            _compute_chat_confidence(telemetry_struct, tool_struct)
            if in_domain
            else None
        )

        # A3/C6/B3: enrich metadata with model/tokens (from agent) + structured tools.
        metadata: dict[str, Any] = dict(agent_response.metadata or {})
        metadata.setdefault("mode", "chat")
        if tools_meta:
            metadata["tools"] = tools_meta
        # THE CONTRACT: ordered list of EVERY tool the agent ran this turn. Always
        # present (possibly empty) so the frontend timeline has a stable source.
        metadata["tool_calls"] = tool_calls_meta
        if selection_context:
            metadata["selection_applied"] = True

        suggested_actions = _extract_actions(content)

        # Remediation (Lane B): read the mode AFTER RCA/tool gathering so the
        # decision is based on the evidence we actually collected. diagnose
        # (default) returns None here -> no behavior change on the default path.
        proposed_action: Optional[dict[str, Any]] = None
        try:
            remediation_settings = get_remediation_settings()
            proposed_action = await _maybe_propose_remediation(
                request,
                mode=remediation_settings.get("mode", "diagnose"),
                content=content,
                suggested_actions=suggested_actions,
                service=service,
                confidence=confidence,
                has_tool_data=has_tool_data,
                remediation_settings=remediation_settings,
                owner=user.username,
                conversation_id=conversation_id,
            )
        except Exception as exc:  # noqa: BLE001 - remediation must never break chat
            logger.warning("Remediation proposal step failed (ignored): %s", exc)
            proposed_action = None

        assistant_response = {
            "content": content,
            "confidence": confidence,
            "suggested_actions": suggested_actions,
            "metadata": metadata,
            "tool_struct": tool_struct,
            "proposed_action": proposed_action,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Reasoning agent unavailable: {str(e)}",
        )

    # C1: prefer the find_similar tool's incidents (so card + dropdown agree with the
    # timeline that claims the find_similar tool); else fall back to _find_related_incidents.
    related_incidents = _related_from_similar(assistant_response["tool_struct"])
    if related_incidents is None:
        related_incidents = await _find_related_incidents(request, chat_request.message)

    # Create assistant message, persisting the per-turn metadata ON it so loading
    # this conversation from history can replay the tool-call timeline + insight
    # cards (otherwise reloaded chats show only the text). The shape mirrors the
    # ChatResponse fields the frontend uses (enrichToolStepsWithResponse + insights).
    assistant_message = ChatMessage(
        role=ChatRole.ASSISTANT,
        content=assistant_response["content"],
        timestamp=datetime.utcnow(),
        metadata={
            "confidence": assistant_response.get("confidence"),
            "suggested_actions": assistant_response.get("suggested_actions"),
            "related_incidents": related_incidents,
            "proposed_action": assistant_response.get("proposed_action"),
            "metadata": assistant_response.get("metadata"),
        },
    )
    conversation.messages.append(assistant_message)
    conversation.updated_at = datetime.utcnow()
    # Write-through the completed turn (incl. the assistant_message.metadata) so a
    # reloaded conversation can replay its reasoning timeline + insight cards.
    _persist_save_conversation(conversation)

    # confidence is Optional: None for a genuine off-domain refusal (the UI then
    # hides the confidence gauge), an evidence-based 0.5–0.9 otherwise.
    return ChatResponse(
        conversation_id=conversation_id,
        message=assistant_message,
        confidence=assistant_response.get("confidence"),
        suggested_actions=assistant_response.get("suggested_actions"),
        related_incidents=related_incidents,
        metadata=assistant_response.get("metadata"),
        proposed_action=assistant_response.get("proposed_action"),
    )


@router.post(
    "/actions/{action_id}/decision",
    response_model=DecisionResponse,
    summary="Decide On A Proposed Remediation",
    description=(
        "Approve or reject a remediation action that the AI proposed in approve/auto "
        "mode. On approval the cached action is executed through the constitutionally "
        "gated path (execute_tool_call); on rejection nothing runs."
    ),
)
async def decide_action(
    request: Request,
    action_id: str,
    body: DecisionRequest,
    user: User = Depends(require_user),
) -> DecisionResponse:
    """Act on a pending proposed remediation action (approve-to-run protocol).

    * approved=False  -> status "rejected", drop the pending action, no execution.
    * approved=True   -> look up the cached action (404 if missing/expired), call
      the gated execute_tool_call, and map its return into DecisionResponse:
        - success                       -> status "executed", success True
        - error_code approval_required /
          validation_blocked            -> status "refused" (gate declined)
        - any other failure             -> status "refused" (e.g. disabled / exec error)
    The constitutional gate + AIOPS_ENABLE_ACTION_TOOLS kill-switch run inside
    execute_tool_call; this endpoint never bypasses them.
    """
    user = coerce_user(user)
    _evict_stale_pending_actions()

    entry = _pending_actions.get(action_id)
    # An action owned by someone else is indistinguishable from a missing one
    # (404, not 403) so action ids cannot be probed across users.
    if entry is None or (entry.get("owner") not in (None, user.username)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposed action {action_id} not found or expired",
        )

    if not body.approved:
        # User declined: nothing executes; remove the pending action.
        _pending_actions.pop(action_id, None)
        _persist_delete_pending_action(action_id)
        logger.info("Proposed action %s rejected by %s", action_id, user.username)
        return DecisionResponse(
            action_id=action_id,
            status="rejected",
            success=False,
            error_code=None,
            verdict=None,
            result=None,
        )

    # Approved: run through the gated programmatic path. The pending entry is
    # consumed regardless of outcome (single-use approval).
    _pending_actions.pop(action_id, None)
    _persist_delete_pending_action(action_id)
    tool_name = entry["tool_name"]
    parameters = entry["parameters"]

    # Human approval IS the authorization. The validator now treats
    # human_approved=True as the matrix authorization (Tier-1 still blocks
    # unconditionally), so we carry the REAL evidence-based chat confidence that
    # was cached with the proposed action instead of synthesizing the auto
    # threshold just to clear the matrix — the audit trail then records the true
    # number. Falls back to the approval threshold (neutral, non-inflated) for
    # older cached entries that predate this field. A data-loss/security action
    # still refuses even when approved (Tier-1).
    validator = getattr(request.app.state, "validator", None)
    approval_threshold = getattr(validator, "confidence_threshold_approval", 0.7) or 0.7
    cached_confidence = entry.get("confidence")
    real_confidence = (
        float(cached_confidence)
        if isinstance(cached_confidence, (int, float))
        else float(approval_threshold)
    )
    exec_parameters = {**parameters, "confidence": real_confidence}
    exec_context = {
        "telemetry_evidence": True,
        "audit_enabled": True,
        "human_approved": True,
        "source": "approve_to_run",
    }

    try:
        result = await execute_tool_call(
            request, tool_name=tool_name, parameters=exec_parameters, context=exec_context,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Approved action %s execution raised: %s", action_id, exc)
        return DecisionResponse(
            action_id=action_id,
            status="refused",
            success=False,
            error_code="execution_failed",
            verdict=None,
            result=None,
        )

    verdict = _extract_verdict(result)
    error_code = result.get("error_code")

    if result.get("success"):
        logger.info("Proposed action %s executed by %s", action_id, user.username)
        return DecisionResponse(
            action_id=action_id,
            status="executed",
            success=True,
            error_code=None,
            verdict=verdict,
            result=result.get("data"),
        )

    # The gate (or executor) declined / failed.
    logger.info(
        "Proposed action %s refused/failed (error_code=%s)", action_id, error_code
    )
    return DecisionResponse(
        action_id=action_id,
        status="refused",
        success=False,
        error_code=error_code,
        verdict=verdict,
        result=result.get("data"),
    )


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Run Analysis",
    description="Run RCA or planning analysis on incident data",
)
async def analyze(
    request: Request,
    analysis_request: AnalysisRequest,
    user: User = Depends(require_user),
) -> AnalysisResponse:
    """
    Run specialized analysis (RCA or remediation planning).

    Modes:
    - rca: Root cause analysis on incident data
    - planning: Create remediation plan from RCA results

    Args:
        analysis_request: Analysis mode and input data

    Returns:
        Structured analysis results with confidence
    """
    user = coerce_user(user)
    start_time = time.perf_counter()
    analysis_id = f"ana-{uuid.uuid4().hex[:12]}"

    reasoning_agent = getattr(request.app.state, "reasoning_agent", None)

    if reasoning_agent is None:
        logger.error("Reasoning agent not initialized - LLM server may be unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reasoning agent not initialized. Check LLM server connection.",
        )

    try:
        if analysis_request.mode == "rca":
            # Retrieve historical context from episodic memory for better RCA
            context_retriever = getattr(request.app.state, "context_retriever", None)
            historical_context = ""

            if context_retriever:
                try:
                    historical_context = await context_retriever.retrieve_for_rca(
                        incident=analysis_request.data,
                        telemetry_summary=None,
                    )
                    logger.info(f"Retrieved historical context for RCA ({len(historical_context)} chars)")
                except Exception as e:
                    logger.warning(f"Failed to retrieve RCA context: {e}")

            agent_response = await reasoning_agent.analyze_rca(
                incident_data=analysis_request.data,
                historical_context=historical_context,
                enable_thinking=analysis_request.enable_thinking,
            )

            # Store RCA result as Episode in Neo4j (per Research Paper Section 4.4)
            episode_store = getattr(request.app.state, "episode_store", None)
            if episode_store and agent_response.content:
                try:
                    from src.memory.episode_store import Episode

                    # Extract service from analysis data
                    affected_services = analysis_request.data.get("services", [])
                    if not affected_services:
                        service = _extract_service_from_query(
                            analysis_request.data.get("title", "") +
                            analysis_request.data.get("description", "")
                        )
                        if service:
                            affected_services = [service]

                    # Create Episode for graph storage
                    rca_episode = Episode(
                        episode_id=str(uuid.uuid4()),
                        incident_id=analysis_request.data.get("incident_id", str(uuid.uuid4())),
                        title=f"RCA: {analysis_request.data.get('title', 'Manual Analysis')[:80]}",
                        description=agent_response.content[:2000],
                        severity=analysis_request.data.get("severity", "info"),
                        category="rca",
                        detected_at=datetime.utcnow(),
                        affected_services=affected_services,
                        root_cause=agent_response.metadata.get("root_cause") if agent_response.metadata else None,
                        confidence=agent_response.confidence,
                        outcome="analyzed",
                    )

                    await episode_store.store_episode(rca_episode)
                    logger.info(f"Stored RCA episode in Neo4j: {rca_episode.episode_id}")
                except Exception as e:
                    logger.warning(f"Failed to store RCA episode: {e}")

        else:  # planning
            root_cause = analysis_request.data.get("root_cause", "Unknown")
            agent_response = await reasoning_agent.create_plan(
                root_cause=root_cause,
                incident_context=analysis_request.data,
            )

        result = agent_response.metadata or {"raw_content": agent_response.content}
        confidence = agent_response.confidence

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Analysis failed: {str(e)}",
        )

    processing_time = (time.perf_counter() - start_time) * 1000

    # Determine if approval is required based on suggested actions
    requires_approval = _check_approval_required(result, confidence)

    return AnalysisResponse(
        analysis_id=analysis_id,
        mode=analysis_request.mode,
        result=result,
        confidence=confidence,
        processing_time_ms=round(processing_time, 2),
        requires_approval=requires_approval,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationHistory,
    summary="Get Conversation History",
    description="Retrieve full conversation history by ID",
)
async def get_conversation(
    conversation_id: str,
    user: User = Depends(require_user),
) -> ConversationHistory:
    """
    Get conversation history.

    Args:
        conversation_id: Unique conversation identifier

    Returns:
        Full conversation with all messages
    """
    user = coerce_user(user)
    conversation = _conversations.get(conversation_id)
    # A conversation owned by someone else is indistinguishable from a missing
    # one (404, not 403) so conversation ids cannot be probed across users.
    if conversation is None or not _can_access(conversation, user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    return conversation


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Conversation",
    description="Delete a conversation by ID",
)
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(require_user),
) -> None:
    """
    Delete a conversation.

    Args:
        conversation_id: Unique conversation identifier
    """
    user = coerce_user(user)
    conversation = _conversations.get(conversation_id)
    if conversation is None or not _can_access(conversation, user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    del _conversations[conversation_id]
    _persist_delete_conversation(conversation_id)


@router.get(
    "/conversations",
    summary="List Conversations",
    description="List all active conversations",
)
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(require_user),
) -> dict[str, Any]:
    """
    List active conversations.

    Args:
        limit: Maximum number to return
        offset: Pagination offset

    Returns:
        List of conversation summaries (only those visible to the caller:
        own conversations, plus legacy owner-less ones for admins).
    """
    user = coerce_user(user)
    all_convs = sorted(
        (c for c in _conversations.values() if _can_access(c, user)),
        key=lambda c: c.updated_at,
        reverse=True,
    )

    paginated = all_convs[offset : offset + limit]

    return {
        "items": [
            {
                "conversation_id": c.conversation_id,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "message_count": len(c.messages),
                "preview": c.messages[-1].content[:100] if c.messages else None,
            }
            for c in paginated
        ],
        "total": len(all_convs),
        "limit": limit,
        "offset": offset,
    }


# Helper functions

# Phrases that signal the model declined / refused the request. Kept lowercase.
_REFUSAL_MARKERS = (
    "can only help with infrastructure",
    "can only assist with infrastructure",
    "i can only help with",
    "i can only assist with",
    "i'm the constitutional aiops reasoning agent",
    "i am the constitutional aiops reasoning agent",
    "only help with infrastructure operations",
    "outside my scope",
    "outside of my scope",
    "not within my scope",
    "i can't help with that",
    "i cannot help with that",
    "i'm unable to help with that",
    # Free-form short declines (the prompt now asks the model to decline in its
    # own words, so match common phrasings too).
    "i cannot answer",
    "i can't answer",
    "cannot answer that",
    "can't answer that",
    "i'm not able to assist",
    "i am not able to assist",
    "i'm not able to help",
    "i am not able to help",
)


def _looks_like_refusal(text: Optional[str]) -> bool:
    """Heuristic: does this reply look like a short scope-refusal?

    A refusal is a SHORT reply that declines and points the user back to
    infrastructure/operations topics. We require both the reply to be short
    (refusals are one sentence by policy) AND to contain a refusal marker, so
    a long, substantive answer that merely mentions "infrastructure" is not
    misclassified.
    """
    if not text:
        return False
    lowered = text.strip().lower()
    if not lowered:
        return False
    # Refusals are brief by policy (one sentence). Cap on length avoids
    # flagging genuine, data-rich answers.
    if len(lowered) > 400:
        return False
    return any(marker in lowered for marker in _REFUSAL_MARKERS)


def _compute_chat_confidence(
    telemetry_struct: Optional[dict[str, Any]],
    tool_struct: dict[str, Any],
) -> Optional[float]:
    """Evidence-based chat confidence via the documented composite formula (A1).

    Routes through ``src.agents.confidence.compute_confidence`` — the single,
    tested code path implementing ``C = 0.4*C_LLM + 0.35*C_hist + 0.25*C_sim``
    with weight renormalization over the present components. This replaces the
    earlier coarse bucket that could only emit {0.5, 0.65, 0.7, 0.85}.

    Component sourcing for the (stateless) chat path:
      * ``c_sim``  = ``similarity_confidence(...)`` over the REAL similarity
        scores returned by the find_similar tool (``tool_struct["similar"]
        ["incidents"][].score``).
      * ``c_hist`` = ``None`` — the find_similar results surfaced in chat carry
        no per-incident resolution outcome, so there is no historical signal to
        fold in here (the formula renormalizes over the remaining components).
      * ``c_llm``  = ``None`` — the chat model does not self-report a calibrated
        confidence (its placeholder is a neutral 0.5), so we omit it rather than
        anchor the score to a meaningless value.

    When at least telemetry OR a non-similarity tool returned data but no real
    similarity score is available, fall back to a neutral evidence floor so a
    data-rich answer still shows a sensible gauge (instead of ``None``).
    """
    from src.agents.confidence import compute_confidence, similarity_confidence

    # C_sim: real similarity scores from the find_similar tool results.
    sim_scores: list[float] = []
    similar = tool_struct.get("similar") or {}
    for inc in similar.get("incidents") or []:
        score = inc.get("score")
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            sim_scores.append(float(score))
    c_sim = similarity_confidence(sim_scores)

    composite = compute_confidence(None, None, c_sim)
    if composite is not None:
        return composite

    # No real similarity score available. Fall back to a neutral evidence-based
    # floor so a data-rich (telemetry / dependency / logs) answer still surfaces
    # a gauge rather than None.
    telemetry_has_data = bool(
        telemetry_struct
        and (telemetry_struct.get("log_count", 0) > 0 or telemetry_struct.get("metrics"))
    )
    tool_has_data = False
    deps = tool_struct.get("dependencies")
    if deps and (deps.get("upstream") or deps.get("downstream")):
        tool_has_data = True
    logs = tool_struct.get("logs")
    if logs and (logs.get("total_logs", 0) > 0 or logs.get("top_errors")):
        tool_has_data = True

    floor = 0.5
    if telemetry_has_data:
        floor += 0.2
    if tool_has_data:
        floor += 0.15
    return max(0.5, min(0.9, floor))


def _related_from_similar(tool_struct: dict[str, Any]) -> list[str] | None:
    """C1: build related_incidents from the find_similar tool results when present.

    Returns None when the find_similar tool did not run / returned nothing, so
    the caller can fall back to _find_related_incidents.
    """
    similar = tool_struct.get("similar")
    if not similar:
        return None
    incidents = similar.get("incidents") or []
    if not incidents:
        return None
    related = []
    for inc in incidents:
        summary = _clean_incident_text(str(inc.get("summary", "Unknown"))) or "Past incident"
        score = inc.get("score")
        if isinstance(score, (int, float)):
            related.append(f"{summary} (similarity: {score:.2f})")
        else:
            related.append(summary)
    return related or None


def _synthesize_answer_from_data(
    service: Optional[str],
    telemetry_struct: Optional[dict[str, Any]],
    tool_struct: dict[str, Any],
) -> str:
    """Last-resort: synthesize a concise answer from gathered tool/telemetry data.

    Used only when an in-domain query was (incorrectly) refused twice. Produces a
    short, factual summary from whatever real data we collected rather than
    returning the refusal to the user.
    """
    target = service or "the requested service"
    lines: list[str] = [f"Here is what I found for {target} from current telemetry and memory:"]

    if telemetry_struct:
        log_count = telemetry_struct.get("log_count", 0)
        err_count = telemetry_struct.get("error_count", 0)
        lines.append(f"- Recent logs: {log_count} total ({err_count} errors).")
        metrics = telemetry_struct.get("metrics") or []
        if metrics:
            shown = ", ".join(f"{m['name']}={m['value']:.2f}" for m in metrics[:5])
            lines.append(f"- Metrics: {shown}.")

    logs = tool_struct.get("logs")
    if logs:
        lines.append(
            f"- Log analysis: {logs.get('total_logs', 0)} logs, "
            f"{logs.get('error_count', 0)} errors, {logs.get('warning_count', 0)} warnings."
        )
        top_errors = logs.get("top_errors") or []
        for e in top_errors[:3]:
            lines.append(f"  - {e.get('pattern', '')} (x{e.get('count', 0)})")

    deps = tool_struct.get("dependencies")
    if deps:
        up = ", ".join(deps.get("upstream", [])) or "none"
        down = ", ".join(deps.get("downstream", [])) or "none"
        lines.append(f"- Dependencies: upstream [{up}]; downstream [{down}].")

    similar = tool_struct.get("similar")
    if similar and similar.get("incidents"):
        lines.append("- Similar past incidents:")
        for inc in similar["incidents"][:3]:
            lines.append(f"  - {inc.get('summary', 'Unknown')}")

    if len(lines) == 1:
        lines.append(
            "- No telemetry or memory data is currently available for this service, "
            "but it is a monitored part of this system."
        )

    return "\n".join(lines)


def _strip_markdown_inline(text: str) -> str:
    """Strip inline markdown (bold/italic/code/heading/list markers) → plain text."""
    s = text.strip()
    s = re.sub(r"^\s*#{1,6}\s*", "", s)            # heading markers
    s = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", s)  # leading bullet / number
    s = s.replace("**", "").replace("__", "")        # bold
    s = s.replace("`", "")                            # inline code
    s = re.sub(r"(?<!\*)\*(?!\*)", "", s)            # stray single-* italics
    s = re.sub(r"\s+", " ", s).strip()
    return s


# First-person process narration the model emits while describing what IT is
# about to do ("I will examine…", "First, I will…", "Let me…"). These are NOT
# recommendations for the operator to act on, but they were leaking into the
# Suggested-actions card via substrings like "recommendations" / "suggest".
_NARRATION_PREFIXES = (
    "i will",
    "i'll",
    "i am going to",
    "i'm going to",
    "i am now",
    "i would now",
    "i plan to",
    "first, i",
    "first i ",
    "next, i",
    "next i ",
    "then i ",
    "then, i",
    "let me",
)


def _extract_actions(content: str) -> list[str] | None:
    """Extract clean, human-readable suggested actions from response content.

    Strips markdown so no raw ``**`` / ``#`` leaks into the UI, and drops
    header-only lines (e.g. a bare "Recommendation:") that are not real actions.

    Two collection paths:
    1. Keyword lines anywhere (suggest/recommend/should/…).
    2. Bullet/numbered lines inside a recommendations-style section — the model
       often emits "Recommendations:" followed by keyword-less bullets ("Restart
       the nextcloud container"), which the keyword filter alone would miss.
    """
    actions: list[str] = []
    keywords = ["suggest", "recommend", "should", "could try", "consider"]
    # Standalone section titles the LLM emits that are NOT real actions.
    header_labels = {
        "recommendation", "recommendations", "recommended", "recommended action",
        "recommended actions", "suggestion", "suggestions", "suggested actions",
        "next steps", "action items",
    }
    bullet_re = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")

    in_actions_section = False
    for raw_line in content.split("\n"):
        line = _strip_markdown_inline(raw_line)
        if not line:
            # A blank line ends a recommendations section.
            in_actions_section = False
            continue
        low = line.lower()
        is_header = low.rstrip(":").strip() in header_labels
        if is_header:
            # Entering a recommendations-style section: its bullets are actions
            # even without keywords. The header itself is never an action.
            in_actions_section = True
            continue

        is_section_bullet = in_actions_section and bool(bullet_re.match(raw_line))
        if not is_section_bullet:
            # A non-bullet line ends the section (new prose paragraph/heading).
            if in_actions_section:
                in_actions_section = False
            if not any(kw in low for kw in keywords):
                continue
        # Drop section headers masquerading as actions ("Recommendation:",
        # "Next Steps:", …) — they end with ':' or are just a label, not an
        # actionable sentence.
        if line.endswith(":"):
            continue
        if len(line.split()) < 3:
            continue
        # Skip the assistant narrating its OWN plan ("I will examine…", "First, I
        # will…") — process descriptions, not actions to take. These leaked in via
        # substrings like "recommendations" / "suggest" inside narration sentences.
        if low.startswith(_NARRATION_PREFIXES):
            continue
        if len(line) > 12 and line not in actions:
            # Trim long prose at a WORD boundary (never mid-word) with an ellipsis
            # so the action card never shows an abrupt cutoff like "…I will then".
            clean = line if len(line) <= 160 else line[:160].rsplit(" ", 1)[0].rstrip() + "…"
            if clean not in actions:
                actions.append(clean)

    return actions[:5] if actions else None


def _clean_incident_text(raw: str, max_len: int = 160) -> str:
    """Turn a possibly-JSON-blob incident string into one clean human sentence.

    Stored episodes sometimes carry raw RCA JSON in their title/root_cause
    (e.g. ``RCA: { "root_cause": "…" }``); render a readable summary instead of
    leaking nested/truncated JSON into the Related-incidents card.
    """
    s = (raw or "").strip()
    # Pull a human field out of any embedded JSON.
    if "{" in s and ('"root_cause"' in s or '"summary"' in s or '"title"' in s):
        m = re.search(r'"(?:root_cause|summary|title)"\s*:\s*"([^"]+)"', s)
        if m:
            s = m.group(1)
    s = re.sub(r"^\s*RCA\s*:\s*", "", s, flags=re.IGNORECASE)  # drop "RCA:" label
    s = _strip_markdown_inline(s)
    # Trim dangling open-bracket / punctuation left by truncated source text.
    s = s.rstrip(" ([{,:-")
    if len(s) > max_len:
        s = s[:max_len].rsplit(" ", 1)[0].rstrip() + "…"
    return s


def _check_approval_required(result: dict, confidence: float) -> bool:
    """Check if analysis results require human approval."""
    # High-risk actions require approval
    if "remediation_steps" in result:
        for step in result.get("remediation_steps", []):
            if step.get("risk") == "high":
                return True

    if "steps" in result:
        for step in result.get("steps", []):
            if step.get("risk") == "high":
                return True

    # Low confidence requires approval
    if confidence < 0.7:
        return True

    return False


async def _find_related_incidents(request: Request, query: str) -> list[str] | None:
    """
    Find related incidents from graph-episodic memory.

    Uses EpisodeStore to query Neo4j for similar past incidents
    based on the service mentioned in the query.

    Args:
        request: FastAPI request object
        query: User's query string

    Returns:
        List of related incident descriptions, or None if none found
    """
    episode_store = getattr(request.app.state, "episode_store", None)

    # Extract service from query
    service = _extract_service_from_query(query)

    if episode_store and service:
        try:
            episodes = await episode_store.find_by_service(service, limit=5)
            if episodes:
                related = []
                for ep in episodes:
                    rc = _clean_incident_text(ep.root_cause or "")
                    title = _clean_incident_text(ep.title or "")
                    text = rc if rc and rc.lower() != "unknown" else title
                    text = text or "Past incident"
                    related.append(f"{text} (severity {ep.severity})")
                return related
        except Exception as e:
            logger.warning(f"Failed to find related incidents: {e}")

    return None


__all__ = ["router"]
