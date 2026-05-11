"""
Constitutional AIOps - Chat API Routes

Chat endpoints for interactive conversation with the Reasoning Agent.
Supports general chat, RCA analysis, and remediation planning.
"""

import logging
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
) -> str:
    """
    Build telemetry context with actual logs and metrics from LGTM stack.

    Args:
        request: FastAPI request object
        service: Service name to query telemetry for
        duration_minutes: How far back to query

    Returns:
        Formatted telemetry context string for LLM
    """
    telemetry_collector = getattr(request.app.state, "telemetry_collector", None)
    if not telemetry_collector or not service:
        return ""

    context_parts = []
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=duration_minutes)

    # Query recent logs from Loki
    try:
        logs = await telemetry_collector.query_logs(
            service=service,
            start_time=start_time,
            end_time=end_time,
            limit=50,
        )
        if logs:
            error_logs = [l for l in logs if l.level.lower() in ("error", "fatal", "critical")]
            warn_logs = [l for l in logs if l.level.lower() in ("warn", "warning")]

            log_text = f"## Recent Logs for {service} (last {duration_minutes} min)\n"
            log_text += f"Total: {len(logs)} logs ({len(error_logs)} errors, {len(warn_logs)} warnings)\n\n"

            # Prioritize errors, then warnings, then others
            sample_logs = (error_logs + warn_logs + logs)[:10]
            for log in sample_logs:
                timestamp_str = log.timestamp.strftime('%H:%M:%S')
                msg_preview = log.message[:200] if len(log.message) > 200 else log.message
                log_text += f"[{timestamp_str}] [{log.level}] {msg_preview}\n"

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
            metric_text = f"## Metrics for {service}\n"
            # Group by metric name and show latest value
            metric_latest: dict[str, float] = {}
            for m in metrics:
                metric_latest[m.name] = m.value

            for name, value in list(metric_latest.items())[:8]:
                metric_text += f"- {name}: {value:.2f}\n"

            context_parts.append(metric_text)
    except Exception as e:
        logger.debug(f"Failed to query metrics for {service}: {e}")

    return "\n\n".join(context_parts) if context_parts else ""


async def _invoke_mcp_tools_for_query(request: Request, message: str, service: Optional[str]) -> str:
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
        Formatted string with MCP tool results for LLM context
    """
    message_lower = message.lower()
    tool_results = []

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
                deps = result["data"]
                tool_results.append(f"\n## Service Dependencies for {service}")
                upstream = deps.get("upstream", [])
                downstream = deps.get("downstream", [])
                if upstream:
                    tool_results.append(f"- Upstream: {', '.join(upstream)}")
                if downstream:
                    tool_results.append(f"- Downstream: {', '.join(downstream)}")
                if not upstream and not downstream:
                    tool_results.append("- No dependencies found in graph")
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
                log_data = result["data"]
                tool_results.append(f"\n## Log Analysis for {service}")
                tool_results.append(f"- Total logs: {log_data.get('total_logs', 0)}")
                tool_results.append(f"- Error count: {log_data.get('error_count', 0)}")
                patterns = log_data.get("patterns", [])
                if patterns:
                    tool_results.append(f"- Top patterns: {', '.join(patterns[:3])}")
        except Exception as e:
            logger.debug(f"analyze_logs tool call failed: {e}")

    if tool_results:
        logger.info(f"MCP tools invoked for query, {len(tool_results)} results")
        return "\n".join(tool_results)
    return ""


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
        if service:
            telemetry_context = await _build_telemetry_context(request, service)
            logger.info(f"Built telemetry context for service: {service}")

        # Invoke MCP tools automatically based on query keywords
        mcp_tool_context = await _invoke_mcp_tools_for_query(request, chat_request.message, service)

        # Combine telemetry + MCP tools + runtime context for comprehensive LLM input
        full_context = runtime_context
        if mcp_tool_context:
            full_context = mcp_tool_context + "\n\n" + full_context
        if telemetry_context:
            full_context = telemetry_context + "\n\n" + full_context

        # Get response from reasoning agent with full context (including real telemetry)
        agent_response = await reasoning_agent.chat(
            message=chat_request.message,
            conversation_history=history[:-1],  # Exclude current message
            runtime_context=full_context,
        )

        assistant_response = {
            "content": agent_response.content,
            "confidence": agent_response.confidence,
            "suggested_actions": _extract_actions(agent_response.content),
            "metadata": agent_response.metadata,
        }

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

    # Look up related incidents from graph memory (if available)
    related_incidents = await _find_related_incidents(
        request, chat_request.message
    )

    return ChatResponse(
        conversation_id=conversation_id,
        message=assistant_message,
        confidence=assistant_response.get("confidence", 0.8),
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

def _extract_actions(content: str) -> list[str] | None:
    """Extract suggested actions from response content."""
    # Simple extraction - could be enhanced with NLP
    actions = []
    keywords = ["suggest", "recommend", "should", "could try", "consider"]

    for line in content.split("\n"):
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            # Clean up the line
            cleaned = line.strip("- ").strip()
            if len(cleaned) > 10:
                actions.append(cleaned[:200])

    return actions[:5] if actions else None


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
                    root_cause = ep.root_cause or "Unknown"
                    related.append(
                        f"{ep.title} (Severity: {ep.severity}, Root Cause: {root_cause})"
                    )
                return related
        except Exception as e:
            logger.warning(f"Failed to find related incidents: {e}")

    return None


__all__ = ["router"]
