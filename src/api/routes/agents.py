"""
Constitutional AIOps - Agent Activity API Routes

Provides endpoints for viewing agent activity, annotations, and RCA results.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentActivity(BaseModel):
    """Agent activity record."""
    id: str
    timestamp: datetime
    type: str = Field(..., description="Activity type: annotation, classification, rca, chat, planning, action")
    input: str
    output: str
    latency_ms: float
    model: str
    status: str = Field(..., description="Status: success or error")


class ActivityListResponse(BaseModel):
    """Response listing agent activities."""
    activities: list[AgentActivity]
    total: int
    agent_type: str


class AgentStats(BaseModel):
    """Agent statistics."""
    total_requests: int
    success_count: int
    error_count: int
    avg_latency_ms: float
    requests_per_minute: float


@router.get(
    "/fast/activity",
    response_model=ActivityListResponse,
    summary="Get Fast Agent Activity",
    description="Get recent activity from the Fast Agent (Qwen3-4B)",
)
async def get_fast_agent_activity(
    request: Request,
    limit: int = 50,
    offset: int = 0,
) -> ActivityListResponse:
    """
    Get recent Fast Agent activity.

    The Fast Agent handles telemetry annotation and classification.
    """
    fast_annotator = getattr(request.app.state, "fast_annotator", None)

    if fast_annotator is None:
        # Return empty list if not initialized
        return ActivityListResponse(
            activities=[],
            total=0,
            agent_type="fast",
        )

    # Get activity from annotator's internal log (if available)
    activity_log = getattr(fast_annotator, "activity_log", [])

    # Convert to response format
    activities = []
    for i, entry in enumerate(activity_log[offset:offset + limit]):
        activities.append(AgentActivity(
            id=f"fast-{i + offset}",
            timestamp=entry.get("timestamp", datetime.utcnow()),
            type=entry.get("type", "annotation"),
            input=entry.get("input", ""),
            output=entry.get("output", ""),
            latency_ms=entry.get("latency_ms", 0),
            model="qwen3:4b",
            status=entry.get("status", "success"),
        ))

    return ActivityListResponse(
        activities=activities,
        total=len(activity_log),
        agent_type="fast",
    )


@router.get(
    "/fast/stats",
    response_model=AgentStats,
    summary="Get Fast Agent Stats",
    description="Get performance statistics for the Fast Agent",
)
async def get_fast_agent_stats(request: Request) -> AgentStats:
    """Get Fast Agent performance statistics."""
    fast_annotator = getattr(request.app.state, "fast_annotator", None)

    if fast_annotator is None:
        return AgentStats(
            total_requests=0,
            success_count=0,
            error_count=0,
            avg_latency_ms=0,
            requests_per_minute=0,
        )

    stats = getattr(fast_annotator, "stats", {})

    return AgentStats(
        total_requests=stats.get("total_requests", 0),
        success_count=stats.get("success_count", 0),
        error_count=stats.get("error_count", 0),
        avg_latency_ms=stats.get("avg_latency_ms", 0),
        requests_per_minute=stats.get("requests_per_minute", 0),
    )


@router.get(
    "/reasoning/activity",
    response_model=ActivityListResponse,
    summary="Get Reasoning Agent Activity",
    description="Get recent activity from the Reasoning Agent (Qwen3-14B)",
)
async def get_reasoning_agent_activity(
    request: Request,
    limit: int = 50,
    offset: int = 0,
) -> ActivityListResponse:
    """
    Get recent Reasoning Agent activity.

    The Reasoning Agent handles RCA, planning, and human chat.
    """
    reasoning_agent = getattr(request.app.state, "reasoning_agent", None)

    if reasoning_agent is None:
        return ActivityListResponse(
            activities=[],
            total=0,
            agent_type="reasoning",
        )

    # Get activity from agent's internal log (if available)
    activity_log = getattr(reasoning_agent, "activity_log", [])

    # Convert to response format
    activities = []
    for i, entry in enumerate(activity_log[offset:offset + limit]):
        activities.append(AgentActivity(
            id=f"reasoning-{i + offset}",
            timestamp=entry.get("timestamp", datetime.utcnow()),
            type=entry.get("type", "rca"),
            input=entry.get("input", ""),
            output=entry.get("output", ""),
            latency_ms=entry.get("latency_ms", 0),
            model="qwen3:14b",
            status=entry.get("status", "success"),
        ))

    return ActivityListResponse(
        activities=activities,
        total=len(activity_log),
        agent_type="reasoning",
    )


@router.get(
    "/reasoning/stats",
    response_model=AgentStats,
    summary="Get Reasoning Agent Stats",
    description="Get performance statistics for the Reasoning Agent",
)
async def get_reasoning_agent_stats(request: Request) -> AgentStats:
    """Get Reasoning Agent performance statistics."""
    reasoning_agent = getattr(request.app.state, "reasoning_agent", None)

    if reasoning_agent is None:
        return AgentStats(
            total_requests=0,
            success_count=0,
            error_count=0,
            avg_latency_ms=0,
            requests_per_minute=0,
        )

    stats = getattr(reasoning_agent, "stats", {})

    return AgentStats(
        total_requests=stats.get("total_requests", 0),
        success_count=stats.get("success_count", 0),
        error_count=stats.get("error_count", 0),
        avg_latency_ms=stats.get("avg_latency_ms", 0),
        requests_per_minute=stats.get("requests_per_minute", 0),
    )


__all__ = ["router"]
