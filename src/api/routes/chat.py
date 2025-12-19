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
        # Fallback for development - return mock response
        logger.warning("Reasoning agent not initialized, returning mock response")
        assistant_response = _mock_chat_response(chat_request.message)
    else:
        try:
            # Build conversation history for context
            history = [
                {"role": msg.role.value, "content": msg.content}
                for msg in conversation.messages[-5:]  # Last 5 messages
            ]

            # Get response from reasoning agent
            agent_response = await reasoning_agent.chat(
                message=chat_request.message,
                conversation_history=history[:-1],  # Exclude current message
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
        logger.warning("Reasoning agent not initialized, returning mock analysis")
        result = _mock_analysis_response(analysis_request.mode, analysis_request.data)
        confidence = 0.75
    else:
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

def _mock_chat_response(message: str) -> dict[str, Any]:
    """Generate mock response for development."""
    return {
        "content": (
            f"I understand you're asking about: '{message[:50]}...'\n\n"
            "As an AI operations assistant, I can help you analyze incidents, "
            "understand system behavior, and suggest remediation steps.\n\n"
            "Note: Running in mock mode - LLM agents not connected."
        ),
        "confidence": 0.75,
        "suggested_actions": ["Check system logs", "Review recent deployments"],
        "metadata": {"mock": True},
    }


def _mock_analysis_response(mode: str, data: dict) -> dict[str, Any]:
    """Generate mock analysis response."""
    if mode == "rca":
        return {
            "root_cause": "Mock root cause analysis",
            "causal_chain": ["Event A", "Event B", "Issue detected"],
            "confidence": 0.75,
            "reasoning": "This is a mock analysis for development",
            "remediation_steps": [
                {"action": "Investigate further", "risk": "low"},
            ],
            "mock": True,
        }
    else:
        return {
            "plan_name": "Mock Remediation Plan",
            "total_steps": 2,
            "overall_risk": "low",
            "steps": [
                {"order": 1, "action": "Step 1", "risk": "low"},
                {"order": 2, "action": "Step 2", "risk": "low"},
            ],
            "mock": True,
        }


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
