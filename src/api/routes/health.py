"""
Constitutional AIOps - Health API Routes

Health check endpoints for monitoring system status.
Checks connectivity to LLM endpoints, Neo4j, and observability stack.
"""

import base64
import logging
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request, Response
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


# ---------------------------------------------------------------------------
# Short TTL cache for /health probe results.
#
# Each call to health_check() fires 2+ outbound LLM probes.  When the endpoint
# is polled rapidly (Layout + Dashboard + Agents each every 30s) these probes
# pile up.  A short cache lets concurrent polls reuse a recent result without
# re-firing all probes; the first call after the TTL re-probes as normal.
#
# HEALTH_CACHE_TTL_SECONDS is intentionally small (5-10s) so the cache never
# makes an incident recovery look delayed to the operator.
# ---------------------------------------------------------------------------
HEALTH_CACHE_TTL_SECONDS: float = 8.0  # module constant — tunable via import

_health_cache_result: list[ComponentHealth] | None = None  # cached component list
_health_cache_ts: float = 0.0  # monotonic timestamp of last probe

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

    Results are cached for ``HEALTH_CACHE_TTL_SECONDS`` so rapid polls from
    Layout / Dashboard / Agents do not re-fire all LLM probes on every request.

    Returns:
        HealthResponse with status of each component
    """
    global _health_cache_result, _health_cache_ts

    now = time.monotonic()
    if _health_cache_result is not None and (now - _health_cache_ts) < HEALTH_CACHE_TTL_SECONDS:
        components = _health_cache_result
    else:
        components = []

        # Check Fast Agent
        fast_health = await _check_fast_agent(request)
        components.append(fast_health)

        # Check Reasoning Agent
        reasoning_health = await _check_reasoning_agent(request)
        components.append(reasoning_health)

        # Check Neo4j (if available)
        neo4j_health = await _check_neo4j(request)
        components.append(neo4j_health)

        _health_cache_result = components
        _health_cache_ts = time.monotonic()

    # Determine overall status
    all_healthy = all(c.healthy for c in components)
    critical_healthy = all(
        c.healthy for c in components
        if c.name in ("fast_agent", "reasoning_agent")
    )

    if all_healthy:
        overall_status = "healthy"
    elif critical_healthy:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    # Calculate uptime
    uptime = None
    if _startup_time:
        uptime = (datetime.utcnow() - _startup_time).total_seconds()

    return HealthResponse(
        status=overall_status,
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


# ---------------------------------------------------------------------------
# Wake readiness probe (lite / sleep-when-idle tier).
#
# The wake holding page (aws/lambda/wake_on_visit) must hand the visitor over to
# the app ONLY once the BACKEND is actually serving -- not merely once the
# frontend's static files are up. On the lite box nginx answers static requests
# (e.g. /favicon.ico) ~20-30s BEFORE the backend finishes booting, so a probe
# against a static file hands off early and drops the visitor on a login whose
# API calls then 502. This endpoint is the backend-readiness signal that closes
# that gap.
#
# Why a 1x1 PNG rather than JSON: the holding page is served from a DIFFERENT
# origin (the CloudFront / Lambda front door) than the app, so its readiness
# check is a cross-origin <img> load -- which needs no CORS and whose onload
# fires ONLY on a genuine 200 image. While the backend is starting the edge
# returns 502 for /api/* (img.onerror -> no hand-off); the moment it answers
# this PNG the page navigates. A JSON body cannot drive <img>, and a no-cors
# fetch cannot tell 200 from 502, so the image is the clean gate. It is public:
# the health router is mounted at /api/v1 WITHOUT the auth dependency (main.py).
# ---------------------------------------------------------------------------
# A verified 1x1 transparent PNG (68 bytes), decoded once at import.
_WAKE_PROBE_PNG: bytes = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mNgAAIAAAUAAen63NgAAAAASUVORK5CYII="
)


@router.get(
    "/wake-probe.png",
    summary="Wake Readiness Probe",
    description=(
        "Tiny always-200 PNG the sleep-when-idle front door's holding page loads "
        "cross-origin to detect that THIS backend is serving before handing the "
        "visitor to the app. Public and unauthenticated."
    ),
    include_in_schema=False,
)
async def wake_probe() -> Response:
    """Return a 1x1 PNG so the holding page's cross-origin ``<img>`` readiness
    probe fires ``onload`` only once the backend is genuinely up. Never cached
    (each wake serves from a fresh boot)."""
    return Response(
        content=_WAKE_PROBE_PNG,
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
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


@router.get(
    "/health/serving",
    summary="Serving Mode Health",
    description=(
        "Reports which serving mode is live (Mode 1 = frozen dual-engine "
        "artifact, Mode 2 = modernized stack), the engine feature flags, and "
        "the engine endpoints with best-effort live probes."
    ),
)
async def serving_health(request: Request) -> dict[str, Any]:
    """Serving-mode health check (Mode 2 plan, Phase 1).

    This is the "which mode is live" endpoint the swap runbook checks after
    every ``scripts/mode-swap.sh`` swap. The mode/features/engine block comes
    from the resolved :class:`~src.agents.serving_profile.ServingProfile`;
    the probe fields are best-effort (reusing the existing agent health-check
    helpers) and degrade to ``null`` — this endpoint never returns a 500 just
    because an engine is down.
    """
    from src.agents.serving_profile import ServingProfile, resolve_serving_profile

    # Prefer the live router's profile (what the app is actually serving
    # with, resolved once at startup); fall back to a fresh env resolution.
    profile = None
    model_router = getattr(request.app.state, "model_router", None)
    if model_router is not None:
        candidate = getattr(model_router, "profile", None)
        if isinstance(candidate, ServingProfile):
            profile = candidate
    if profile is None:
        profile = resolve_serving_profile()

    engine: dict[str, Any] = {
        "fast_url": profile.fast_url,
        "reasoning_url": profile.reasoning_url,
        "fast_model": profile.fast_model,
        "reasoning_model": profile.reasoning_model,
        # Best-effort probe results; null = could not probe (no router yet /
        # probe raised), boolean = probe outcome.
        "fast_agent_healthy": None,
        "reasoning_agent_healthy": None,
        "fast_agent_latency_ms": None,
        "reasoning_agent_latency_ms": None,
    }

    if model_router is not None:
        try:
            fast = await _check_fast_agent(request)
            if fast.error is None:
                engine["fast_agent_healthy"] = fast.healthy
                engine["fast_agent_latency_ms"] = fast.latency_ms
        except Exception as e:  # noqa: BLE001 — probes must never 500 this route
            logger.warning(f"Serving-health fast-agent probe failed: {e}")
        try:
            reasoning = await _check_reasoning_agent(request)
            if reasoning.error is None:
                engine["reasoning_agent_healthy"] = reasoning.healthy
                engine["reasoning_agent_latency_ms"] = reasoning.latency_ms
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Serving-health reasoning-agent probe failed: {e}")

    return {
        "mode": profile.mode,
        "single_engine": profile.single_engine,
        "features": {
            "streaming": profile.supports_streaming,
            "native_tools": profile.supports_native_tools,
            "guided_json": profile.supports_guided_json,
            "priority": profile.supports_priority,
        },
        "engine": engine,
    }


# Helper functions for health checks

# Floor (ms) applied to a reachable agent's probe latency. A cached / very fast
# probe can round to 0.0; the Dashboard "Avg Response Time" card then shows 0,
# which reads as "no data". A reachable agent always took *some* round-trip, so
# we floor the reported latency to a small positive value to keep the card
# meaningful. Unreachable agents report no latency (None).
_MIN_REACHABLE_LATENCY_MS: float = 0.01


async def _check_fast_agent(request: Request) -> ComponentHealth:
    """Check Fast Agent health (timed probe; latency_ms > 0 when reachable)."""
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
        healthy = health.get("fast_agent", False)

        # Guarantee a present, positive latency for a reachable agent (a cached
        # probe can round to 0.0, which the Dashboard reads as "no data").
        latency_ms = max(round(latency, 2), _MIN_REACHABLE_LATENCY_MS) if healthy else round(latency, 2)

        return ComponentHealth(
            name="fast_agent",
            healthy=healthy,
            latency_ms=latency_ms,
        )
    except Exception as e:
        logger.warning(f"Fast agent health check failed: {e}")
        return ComponentHealth(
            name="fast_agent",
            healthy=False,
            error=str(e),
        )


async def _check_reasoning_agent(request: Request) -> ComponentHealth:
    """Check Reasoning Agent health (timed probe; latency_ms > 0 when reachable)."""
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
        healthy = health.get("reasoning_agent", False)

        latency_ms = max(round(latency, 2), _MIN_REACHABLE_LATENCY_MS) if healthy else round(latency, 2)

        return ComponentHealth(
            name="reasoning_agent",
            healthy=healthy,
            latency_ms=latency_ms,
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
