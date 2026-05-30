"""
Constitutional AIOps - Health API Routes

Health check endpoints for monitoring system status.
Checks connectivity to LLM endpoints, Neo4j, and observability stack.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from src.version import __version__

logger = logging.getLogger(__name__)

router = APIRouter()


class ComponentHealth(BaseModel):
    """Health status of a single component."""
    name: str
    healthy: bool
    latency_ms: float | None = None
    error: str | None = None
    details: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Overall system health response."""
    status: str = Field(..., description="Overall status: healthy, degraded, unhealthy")
    timestamp: datetime
    version: str
    components: list[ComponentHealth]
    uptime_seconds: float | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-12-14T10:00:00Z",
                "version": "0.1.0",
                "components": [
                    {"name": "fast_agent", "healthy": True, "latency_ms": 15.2},
                    {"name": "reasoning_agent", "healthy": True, "latency_ms": 45.8},
                    {"name": "neo4j", "healthy": True, "latency_ms": 8.1}
                ],
                "uptime_seconds": 3600.5
            }
        }


class ReadinessResponse(BaseModel):
    """Kubernetes readiness probe response."""
    ready: bool
    checks_passed: list[str]
    checks_failed: list[str]


class LivenessResponse(BaseModel):
    """Kubernetes liveness probe response."""
    alive: bool
    timestamp: datetime


# Track startup time for uptime calculation
_startup_time: datetime | None = None


def set_startup_time():
    """Set startup time (call from lifespan)."""
    global _startup_time
    _startup_time = datetime.utcnow()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health Check",
    description="Comprehensive health check of all system components",
)
async def health_check(request: Request) -> HealthResponse:
    """
    Check health of all system components.

    Checks:
    - Fast Agent (Qwen3-4B @ port 8081)
    - Reasoning Agent (Qwen3-14B @ port 8082)
    - Neo4j database
    - Observability stack (optional)

    Returns:
        HealthResponse with status of each component
    """
    components: list[ComponentHealth] = []

    # Check Fast Agent
    fast_health = await _check_fast_agent(request)
    components.append(fast_health)

    # Check Reasoning Agent
    reasoning_health = await _check_reasoning_agent(request)
    components.append(reasoning_health)

    # Check Neo4j (if available)
    neo4j_health = await _check_neo4j(request)
    components.append(neo4j_health)

    # Determine overall status
    all_healthy = all(c.healthy for c in components)
    critical_healthy = all(
        c.healthy for c in components
        if c.name in ("fast_agent", "reasoning_agent")
    )

    if all_healthy:
        status = "healthy"
    elif critical_healthy:
        status = "degraded"
    else:
        status = "unhealthy"

    # Calculate uptime
    uptime = None
    if _startup_time:
        uptime = (datetime.utcnow() - _startup_time).total_seconds()

    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow(),
        version=__version__,
        components=components,
        uptime_seconds=uptime,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description="Kubernetes readiness probe - checks if service can accept traffic",
)
async def readiness_check(request: Request) -> ReadinessResponse:
    """
    Kubernetes readiness probe.

    Service is ready if at least one LLM endpoint is available.
    Used by load balancers to route traffic.
    """
    checks_passed = []
    checks_failed = []

    # Check Fast Agent
    fast_health = await _check_fast_agent(request)
    if fast_health.healthy:
        checks_passed.append("fast_agent")
    else:
        checks_failed.append("fast_agent")

    # Check Reasoning Agent
    reasoning_health = await _check_reasoning_agent(request)
    if reasoning_health.healthy:
        checks_passed.append("reasoning_agent")
    else:
        checks_failed.append("reasoning_agent")

    # Ready if at least one agent is available
    ready = len(checks_passed) > 0

    return ReadinessResponse(
        ready=ready,
        checks_passed=checks_passed,
        checks_failed=checks_failed,
    )


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness Probe",
    description="Kubernetes liveness probe - checks if service is alive",
)
async def liveness_check() -> LivenessResponse:
    """
    Kubernetes liveness probe.

    Always returns alive=True if the application is running.
    If this fails, Kubernetes should restart the container.
    """
    return LivenessResponse(
        alive=True,
        timestamp=datetime.utcnow(),
    )


@router.get(
    "/health/agents",
    summary="Agent Health Details",
    description="Detailed health status of LLM agents",
)
async def agent_health(request: Request) -> dict[str, Any]:
    """
    Detailed health check for LLM agents.

    Returns configuration and status for both agents.
    """
    from src.config import config

    fast_health = await _check_fast_agent(request)
    reasoning_health = await _check_reasoning_agent(request)

    return {
        "fast_agent": {
            "url": config.llm.fast_agent_url,
            "model": config.llm.fast_agent_model,
            "context_window": config.llm.fast_agent_context,
            "timeout": config.llm.fast_agent_timeout,
            "healthy": fast_health.healthy,
            "latency_ms": fast_health.latency_ms,
            "error": fast_health.error,
        },
        "reasoning_agent": {
            "url": config.llm.reasoning_agent_url,
            "model": config.llm.reasoning_agent_model,
            "context_window": config.llm.reasoning_agent_context,
            "timeout": config.llm.reasoning_agent_timeout,
            "healthy": reasoning_health.healthy,
            "latency_ms": reasoning_health.latency_ms,
            "error": reasoning_health.error,
        },
        "architecture": "Simultaneous Dual-Model (24GB VRAM)",
    }


# Helper functions for health checks

async def _check_fast_agent(request: Request) -> ComponentHealth:
    """Check Fast Agent health."""
    import time

    try:
        model_router = getattr(request.app.state, "model_router", None)
        if model_router is None:
            return ComponentHealth(
                name="fast_agent",
                healthy=False,
                error="ModelRouter not initialized",
            )

        start = time.perf_counter()
        health = await model_router.health_check()
        latency = (time.perf_counter() - start) * 1000

        return ComponentHealth(
            name="fast_agent",
            healthy=health.get("fast_agent", False),
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        logger.warning(f"Fast agent health check failed: {e}")
        return ComponentHealth(
            name="fast_agent",
            healthy=False,
            error=str(e),
        )


async def _check_reasoning_agent(request: Request) -> ComponentHealth:
    """Check Reasoning Agent health."""
    import time

    try:
        model_router = getattr(request.app.state, "model_router", None)
        if model_router is None:
            return ComponentHealth(
                name="reasoning_agent",
                healthy=False,
                error="ModelRouter not initialized",
            )

        start = time.perf_counter()
        health = await model_router.health_check()
        latency = (time.perf_counter() - start) * 1000

        return ComponentHealth(
            name="reasoning_agent",
            healthy=health.get("reasoning_agent", False),
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        logger.warning(f"Reasoning agent health check failed: {e}")
        return ComponentHealth(
            name="reasoning_agent",
            healthy=False,
            error=str(e),
        )


async def _check_neo4j(request: Request) -> ComponentHealth:
    """Check Neo4j database health."""
    import time

    try:
        neo4j_client = getattr(request.app.state, "neo4j_client", None)
        if neo4j_client is None:
            return ComponentHealth(
                name="neo4j",
                healthy=False,
                error="Neo4j client not initialized",
            )

        start = time.perf_counter()
        # Attempt to verify connectivity
        is_healthy = await neo4j_client.health_check()
        latency = (time.perf_counter() - start) * 1000

        return ComponentHealth(
            name="neo4j",
            healthy=is_healthy,
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        logger.warning(f"Neo4j health check failed: {e}")
        return ComponentHealth(
            name="neo4j",
            healthy=False,
            error=str(e),
        )


__all__ = ["router", "set_startup_time"]
