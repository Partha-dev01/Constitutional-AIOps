"""
Constitutional AIOps - Chat API Routes

Chat endpoints for interactive conversation with the Reasoning Agent.
Supports general chat, RCA analysis, and remediation planning.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any

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

logger = logging.getLogger(__name__)


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
                        status_icon = "🟢" if container.status == "running" else "🔴"
                        container_list.append(f"  - {container.name}: {status_icon} {container.status}")

                if container_list:
                    context_parts.append("## Current Container Status\n" + "\n".join(container_list))
                docker_client.close()
            except Exception as e:
                logger.debug(f"Failed to get container status: {e}")
                docker_client.close()
    except Exception as e:
        logger.debug(f"Container context unavailable: {e}")

    # 2. LLM Agent Health
    model_router = getattr(request.app.state, "model_router", None)
    if model_router:
        try:
            health = await model_router.health_check()
            fast_status = "🟢 Online" if health.get("fast_agent") else "🔴 Offline"
            reasoning_status = "🟢 Online" if health.get("reasoning_agent") else "🔴 Offline"
            context_parts.append(
                f"## LLM Agent Status\n  - Fast Agent (Qwen3-4B): {fast_status}\n  - Reasoning Agent (Qwen3-14B): {reasoning_status}"
            )
        except Exception as e:
            logger.debug(f"Agent health context unavailable: {e}")

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

        # Get response from reasoning agent with runtime context
        agent_response = await reasoning_agent.chat(
            message=chat_request.message,
            conversation_history=history[:-1],  # Exclude current message
            runtime_context=runtime_context,
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
            agent_response = await reasoning_agent.analyze_rca(
                incident_data=analysis_request.data,
                enable_thinking=analysis_request.enable_thinking,
            )
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
    """Find related incidents from graph memory."""
    neo4j_client = getattr(request.app.state, "neo4j_client", None)

    if neo4j_client is None:
        return None

    try:
        # This would use Neo4j full-text search or vector similarity
        # For now, return None until memory module is implemented
        return None
    except Exception as e:
        logger.warning(f"Failed to find related incidents: {e}")
        return None


__all__ = ["router"]
