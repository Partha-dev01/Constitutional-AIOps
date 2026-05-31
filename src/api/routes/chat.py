"""
Constitutional AIOps - Chat API Routes

Chat endpoints for interactive conversation with the Reasoning Agent.
Supports general chat, RCA analysis, and remediation planning.
"""

import logging
import re
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, status

from src.api.schemas.chat import (
    AnalysisRequest,
    AnalysisResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatRole,
    ConversationHistory,
)

# Import MCP tool executor for automatic tool calls during chat
from src.api.routes.tools import execute_tool_call

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


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Send Chat Message",
    description="Send a message to the Reasoning Agent and get a response",
)
async def chat(request: Request, chat_request: ChatRequest) -> ChatResponse:
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
    # Get or create conversation
    conversation_id = chat_request.conversation_id or f"conv-{uuid.uuid4().hex[:12]}"

    if conversation_id in _conversations:
        conversation = _conversations[conversation_id]
    else:
        conversation = ConversationHistory(
            conversation_id=conversation_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            messages=[],
            context=chat_request.context,
        )
        _conversations[conversation_id] = conversation

    # Add user message
    user_message = ChatMessage(
        role=ChatRole.USER,
        content=chat_request.message,
        timestamp=datetime.utcnow(),
    )
    conversation.messages.append(user_message)

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

        # Extract service from query and get real telemetry data
        service = _extract_service_from_query(chat_request.message)
        telemetry_context = ""
        telemetry_struct: Optional[dict[str, Any]] = None
        if service:
            telemetry_context, telemetry_struct = await _build_telemetry_context(request, service)
            logger.info(f"Built telemetry context for service: {service}")

        # Invoke MCP tools automatically based on query keywords
        mcp_tool_context, tool_struct = await _invoke_mcp_tools_for_query(
            request, chat_request.message, service
        )

        # Combine telemetry + MCP tools + runtime context for comprehensive LLM input
        full_context = runtime_context
        if mcp_tool_context:
            full_context = mcp_tool_context + "\n\n" + full_context
        if telemetry_context:
            full_context = telemetry_context + "\n\n" + full_context

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
        has_tool_data = bool(tools_meta)

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

        assistant_response = {
            "content": content,
            "confidence": confidence,
            "suggested_actions": _extract_actions(content),
            "metadata": metadata,
            "tool_struct": tool_struct,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Reasoning agent unavailable: {str(e)}",
        )

    # Create assistant message
    assistant_message = ChatMessage(
        role=ChatRole.ASSISTANT,
        content=assistant_response["content"],
        timestamp=datetime.utcnow(),
    )
    conversation.messages.append(assistant_message)
    conversation.updated_at = datetime.utcnow()

    # C1: prefer the find_similar tool's incidents (so card + dropdown agree with the
    # timeline that claims the find_similar tool); else fall back to _find_related_incidents.
    related_incidents = _related_from_similar(assistant_response["tool_struct"])
    if related_incidents is None:
        related_incidents = await _find_related_incidents(request, chat_request.message)

    # confidence is Optional: None for a genuine off-domain refusal (the UI then
    # hides the confidence gauge), an evidence-based 0.5–0.9 otherwise.
    return ChatResponse(
        conversation_id=conversation_id,
        message=assistant_message,
        confidence=assistant_response.get("confidence"),
        suggested_actions=assistant_response.get("suggested_actions"),
        related_incidents=related_incidents,
        metadata=assistant_response.get("metadata"),
    )


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Run Analysis",
    description="Run RCA or planning analysis on incident data",
)
async def analyze(request: Request, analysis_request: AnalysisRequest) -> AnalysisResponse:
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
async def get_conversation(conversation_id: str) -> ConversationHistory:
    """
    Get conversation history.

    Args:
        conversation_id: Unique conversation identifier

    Returns:
        Full conversation with all messages
    """
    if conversation_id not in _conversations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    return _conversations[conversation_id]


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Conversation",
    description="Delete a conversation by ID",
)
async def delete_conversation(conversation_id: str) -> None:
    """
    Delete a conversation.

    Args:
        conversation_id: Unique conversation identifier
    """
    if conversation_id not in _conversations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    del _conversations[conversation_id]


@router.get(
    "/conversations",
    summary="List Conversations",
    description="List all active conversations",
)
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List active conversations.

    Args:
        limit: Maximum number to return
        offset: Pagination offset

    Returns:
        List of conversation summaries
    """
    all_convs = sorted(
        _conversations.values(),
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
) -> float:
    """Evidence-based chat confidence (A1).

    Start at 0.5; +0.2 if telemetry returned real data (logs or metrics);
    +0.15 if any tool (similar / dependencies / logs) returned non-empty data;
    clamp to [0.5, 0.9].
    """
    confidence = 0.5

    telemetry_has_data = False
    if telemetry_struct:
        if telemetry_struct.get("log_count", 0) > 0 or telemetry_struct.get("metrics"):
            telemetry_has_data = True
    if telemetry_has_data:
        confidence += 0.2

    tool_has_data = False
    similar = tool_struct.get("similar")
    if similar and similar.get("count", 0) > 0:
        tool_has_data = True
    deps = tool_struct.get("dependencies")
    if deps and (deps.get("upstream") or deps.get("downstream")):
        tool_has_data = True
    logs = tool_struct.get("logs")
    if logs and (logs.get("total_logs", 0) > 0 or logs.get("top_errors")):
        tool_has_data = True
    if tool_has_data:
        confidence += 0.15

    return max(0.5, min(0.9, confidence))


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


def _extract_actions(content: str) -> list[str] | None:
    """Extract clean, human-readable suggested actions from response content.

    Strips markdown so no raw ``**`` / ``#`` leaks into the UI, and drops
    header-only lines (e.g. a bare "Recommendation:") that are not real actions.
    """
    actions: list[str] = []
    keywords = ["suggest", "recommend", "should", "could try", "consider"]
    # Standalone section titles the LLM emits that are NOT real actions.
    header_labels = {
        "recommendation", "recommendations", "recommended", "recommended action",
        "recommended actions", "suggestion", "suggestions", "suggested actions",
        "next steps", "action items",
    }

    for raw_line in content.split("\n"):
        line = _strip_markdown_inline(raw_line)
        if not line:
            continue
        low = line.lower()
        if not any(kw in low for kw in keywords):
            continue
        # Drop section headers masquerading as actions ("Recommendation:",
        # "Recommendations", "Next Steps:", …) — they end with ':' or are just
        # a label, not an actionable sentence.
        if line.endswith(":"):
            continue
        if low.rstrip(":").strip() in header_labels:
            continue
        if len(line.split()) < 3:
            continue
        if len(line) > 12:
            actions.append(line[:200])

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
