"""
Constitutional AIOps - Incidents API Routes

Incident management endpoints with CRUD operations.
Incidents are stored in Neo4j graph-episodic memory.
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status

from src.api.schemas.incident import (
    Incident,
    IncidentCategory,
    IncidentCreate,
    IncidentList,
    IncidentSeverity,
    IncidentStats,
    IncidentStatus,
    IncidentUpdate,
    ServiceInfo,
)

# Durable persistence (write-through): the in-memory _incidents dict below stays
# the read fast-path; these helpers mirror each mutation into SQLite so incidents
# and the incident-id counter survive a backend restart/redeploy.
from src.persistence import store as persistence_store

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory incident store (durable write-through to SQLite under AIOPS_DATA_DIR;
# also correlated into Neo4j graph memory via /{id}/similar).
_incidents: dict[str, Incident] = {}

# Maximum number of incidents kept in the in-memory fast-path dict.  Eviction
# drops the oldest resolved/closed incidents first, then the oldest active ones,
# so hot/open incidents are not flushed while they are being worked.  Evicted
# incidents remain loadable from SQLite persistence.
_MAX_INCIDENTS: int = int(os.getenv("INCIDENTS_MAX", "500"))

# Counter for incident IDs (persisted via persistence_store.set_counter so IDs
# keep advancing across restarts and never collide with pre-restart references).
_incident_counter = 0

# Name of the persisted counter row backing _incident_counter.
_INCIDENT_COUNTER_NAME = "incident"

# Demo remediation pacing (W4-B). Module constants so the staged-progress demo
# has realistic spacing live, while tests can shrink them to run fast.
#   _DEMO_STAGE_DELAYS: seconds slept between the 4 staged progress events.
#   _DEMO_VERIFY_RETRIES / _DEMO_VERIFY_INTERVAL: t3_status verification poll.
_DEMO_STAGE_DELAY_VALIDATE: float = 1.5
_DEMO_STAGE_DELAY_EXECUTE: float = 2.0
_DEMO_STAGE_DELAY_VERIFY: float = 1.5
_DEMO_VERIFY_RETRIES: int = 5
_DEMO_VERIFY_INTERVAL: float = 2.0


def _audit_enabled() -> bool:
    """Resolve the persisted ``constitutional.enableAuditLog`` toggle.

    Previously a dead no-op (validator call sites hardcoded ``audit_enabled=
    True``). Defaults to True (audit-on) when the setting is unset/unreadable —
    auditing is the safe default for a constitutional system.
    """
    try:
        from src.api.routes.settings import get_constitutional_settings

        return bool(get_constitutional_settings().get("enableAuditLog", True))
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not read persisted enableAuditLog: %s", exc)
        return True


async def _broadcast_incident_update(incident: Incident, stage: str | None = None) -> None:
    """Push an incident status/progress update to the frontend over WebSocket.

    Reuses the existing ``broadcast_incident_updated`` emitter + the
    ``INCIDENT_UPDATED`` event type (src/utils/websocket.py). The serialized
    incident is the payload; an optional ``stage`` (human-readable progress
    label) is merged in so the UI can show the staged remediation steps. Failures
    are swallowed — a missing/closed socket must never break remediation.
    """
    try:
        from src.utils.websocket import broadcast_incident_updated

        payload = incident.model_dump(mode="json")
        if stage is not None:
            payload["stage"] = stage
        await broadcast_incident_updated(payload)
    except Exception as exc:  # noqa: BLE001
        logger.debug("WS incident update broadcast failed (ignored): %s", exc)


def _scenario_active(scenarios: dict, scenario: str) -> bool | None:
    """Interpret a scenario's active flag from a t3 status map.

    Returns True (still active), False (healed) or None (unknown — scenario not
    present in the map). Tolerates both the dict form (``{"active": bool}``) and
    a bare bool form.
    """
    if scenario not in scenarios:
        return None
    entry = scenarios.get(scenario)
    if isinstance(entry, dict):
        active = entry.get("active")
        if isinstance(active, bool):
            return active
        return None
    if isinstance(entry, bool):
        return entry
    if entry is None:  # key present but null -> treat as cleared
        return False
    return None


async def _verify_scenario_healed(scenario: str, container: str | None) -> bool:
    """Poll the t3 status until recovery is confirmed.

    Recovery is confirmed when the scenario reads INACTIVE. The affected
    container's ``running`` flag is used ONLY as a fallback signal when the
    scenario is not present in the status map at all (so there is no direct
    scenario signal to read) — it is NOT an independent success condition, so a
    still-active scenario whose container happens to be running (e.g. cpu_stress)
    is correctly treated as not-yet-healed.

    Polls up to ``_DEMO_VERIFY_RETRIES`` times with a ``_DEMO_VERIFY_INTERVAL``
    gap. Returns False if recovery is never confirmed — the caller then refuses
    to mark the incident RESOLVED. Never raises (t3 calls fail closed).
    """
    from src.remediation import t3_client

    for attempt in range(_DEMO_VERIFY_RETRIES):
        if attempt > 0:
            await asyncio.sleep(_DEMO_VERIFY_INTERVAL)
        try:
            status_result = await t3_client.t3_status()
        except Exception as exc:  # noqa: BLE001
            logger.debug("t3_status probe raised during verify (ignored): %s", exc)
            continue
        if not status_result.get("success"):
            continue

        scenarios = status_result.get("scenarios") or {}
        containers = status_result.get("containers") or {}

        active = _scenario_active(scenarios, scenario)
        if active is False:
            return True
        if active is True:
            # Scenario is still active — explicitly not healed yet. Do NOT fall
            # back to the container check (it may stay up during cpu/mem stress).
            continue

        # active is None: scenario not in the map -> use the container fallback.
        if container is not None:
            container_entry = containers.get(container)
            if isinstance(container_entry, dict) and container_entry.get("running") is True:
                return True

    return False


def _persist_save_incident(incident: Incident) -> None:
    """Best-effort durable write of an incident — never break the request path."""
    try:
        persistence_store.save_incident(incident)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist incident %s: %s", incident.id, exc)


def _persist_delete_incident(incident_id: str) -> None:
    try:
        persistence_store.delete_incident(incident_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to delete persisted incident %s: %s", incident_id, exc)


def _persist_incident_counter() -> None:
    try:
        persistence_store.set_counter(_INCIDENT_COUNTER_NAME, _incident_counter)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist incident counter: %s", exc)


def _evict_stale_incidents() -> None:
    """Drop the oldest incidents once the in-memory store exceeds _MAX_INCIDENTS.

    Eviction strategy:
    1. Prefer dropping resolved/closed incidents (finished work) ordered by
       ``updated_at`` ascending (oldest first).
    2. If still over cap, drop the oldest active incidents by ``updated_at``.

    Evicted incidents are NOT deleted from SQLite — they remain loadable via
    ``_load_incident_from_persistence`` if a direct GET is requested later.
    """
    overflow = len(_incidents) - _MAX_INCIDENTS
    if overflow <= 0:
        return

    terminal = {IncidentStatus.RESOLVED, IncidentStatus.CLOSED}
    candidates_terminal = sorted(
        [i for i in _incidents.values() if i.status in terminal],
        key=lambda i: i.updated_at,
    )
    candidates_active = sorted(
        [i for i in _incidents.values() if i.status not in terminal],
        key=lambda i: i.updated_at,
    )
    eviction_order = candidates_terminal + candidates_active

    evicted = 0
    for incident in eviction_order:
        if evicted >= overflow:
            break
        _incidents.pop(incident.id, None)
        evicted += 1

    logger.info("Evicted %d incident(s) from in-memory cache (cap %d)", evicted, _MAX_INCIDENTS)


def _load_incident_from_persistence(incident_id: str) -> Incident | None:
    """Try to load a single incident from the SQLite store (cache-miss path).

    Returns the incident (and re-populates the in-memory cache) or None if not
    found in persistence.  This ensures that incidents evicted from the fast-path
    dict are still reachable via GET /{id}.
    """
    try:
        all_persisted = persistence_store.load_all_incidents()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to query persistence for incident %s: %s", incident_id, exc)
        return None

    incident = all_persisted.get(incident_id)
    if incident is not None:
        # Warm the cache so subsequent accesses are in-memory fast-path.
        _incidents[incident_id] = incident
        _evict_stale_incidents()
        logger.debug("Loaded evicted incident %s from persistence", incident_id)
    return incident


def _generate_incident_id() -> str:
    """Generate unique incident ID."""
    global _incident_counter
    _incident_counter += 1
    _persist_incident_counter()
    year = datetime.utcnow().year
    return f"INC-{year}-{_incident_counter:04d}"


@router.post(
    "/",
    response_model=Incident,
    status_code=status.HTTP_201_CREATED,
    summary="Create Incident",
    description="Create a new incident and optionally trigger auto-analysis",
)
async def create_incident(
    request: Request,
    incident_create: IncidentCreate,
) -> Incident:
    """
    Create a new incident.

    If auto_analyze is True, triggers RCA using the Reasoning Agent.

    Args:
        incident_create: Incident creation data

    Returns:
        Created incident with generated ID
    """
    incident_id = _generate_incident_id()
    now = datetime.utcnow()

    incident = Incident(
        id=incident_id,
        title=incident_create.title,
        description=incident_create.description,
        severity=incident_create.severity,
        category=incident_create.category,
        affected_services=incident_create.affected_services,
        tags=incident_create.tags,
        source=incident_create.source,
        status=IncidentStatus.DETECTING,
        telemetry=incident_create.telemetry,
        created_at=now,
        updated_at=now,
        detected_at=now,
    )

    _incidents[incident_id] = incident
    _persist_save_incident(incident)
    _evict_stale_incidents()
    logger.info(f"Created incident: {incident_id}")

    # Trigger auto-analysis if requested
    if incident_create.auto_analyze:
        await _trigger_analysis(request, incident)
        # _trigger_analysis mutates status/rca/updated_at in place — re-persist.
        _persist_save_incident(incident)

    return incident


@router.get(
    "/",
    response_model=IncidentList,
    summary="List Incidents",
    description="Get paginated list of incidents with optional filters",
)
async def list_incidents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: list[IncidentStatus] | None = Query(None, description="Filter by status"),
    severity: list[IncidentSeverity] | None = Query(None, description="Filter by severity"),
    category: list[IncidentCategory] | None = Query(None, description="Filter by category"),
    service: str | None = Query(None, description="Filter by affected service"),
    search: str | None = Query(None, description="Search in title/description"),
) -> IncidentList:
    """
    List incidents with pagination and filters.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status: Filter by incident status
        severity: Filter by severity level
        category: Filter by category
        service: Filter by affected service name
        search: Full-text search query

    Returns:
        Paginated list of incidents
    """
    # Filter incidents
    filtered = list(_incidents.values())

    if status:
        filtered = [i for i in filtered if i.status in status]

    if severity:
        filtered = [i for i in filtered if i.severity in severity]

    if category:
        filtered = [i for i in filtered if i.category in category]

    if service:
        filtered = [
            i for i in filtered
            if any(s.name == service for s in i.affected_services)
        ]

    if search:
        search_lower = search.lower()
        filtered = [
            i for i in filtered
            if search_lower in i.title.lower()
            or (i.description and search_lower in i.description.lower())
        ]

    # Sort by created_at descending
    filtered.sort(key=lambda i: i.created_at, reverse=True)

    # Paginate
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    return IncidentList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )


@router.get(
    "/stats",
    response_model=IncidentStats,
    summary="Get Incident Statistics",
    description="Get aggregated statistics about incidents",
)
async def get_incident_stats() -> IncidentStats:
    """
    Get incident statistics.

    Returns:
        Aggregated incident statistics
    """
    incidents = list(_incidents.values())

    by_status: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}

    resolution_times: list[float] = []
    auto_resolved = 0
    approval_required = 0

    for incident in incidents:
        # Count by status
        status_key = incident.status.value
        by_status[status_key] = by_status.get(status_key, 0) + 1

        # Count by severity
        severity_key = incident.severity.value
        by_severity[severity_key] = by_severity.get(severity_key, 0) + 1

        # Count by category
        category_key = incident.category.value
        by_category[category_key] = by_category.get(category_key, 0) + 1

        # Track resolution times
        if incident.resolved_at and incident.detected_at:
            duration = (incident.resolved_at - incident.detected_at).total_seconds() / 60
            resolution_times.append(duration)

        # Track auto-resolved and approval-required
        if incident.rca and incident.rca.confidence >= 0.9:
            auto_resolved += 1
        if incident.status == IncidentStatus.PENDING_APPROVAL:
            approval_required += 1

    mttr = sum(resolution_times) / len(resolution_times) if resolution_times else None

    return IncidentStats(
        total=len(incidents),
        by_status=by_status,
        by_severity=by_severity,
        by_category=by_category,
        mean_time_to_resolution=mttr,
        auto_resolved_count=auto_resolved,
        approval_required_count=approval_required,
    )


@router.get(
    "/{incident_id}",
    response_model=Incident,
    summary="Get Incident",
    description="Get incident by ID",
)
async def get_incident(incident_id: str) -> Incident:
    """
    Get incident by ID.

    First checks the in-memory fast-path; if absent (evicted by the LRU cap)
    falls back to the SQLite persistence layer so no incident is silently lost.

    Args:
        incident_id: Unique incident identifier

    Returns:
        Incident details
    """
    incident = _incidents.get(incident_id)
    if incident is None:
        # Cache miss — may have been evicted; try persistence.
        incident = _load_incident_from_persistence(incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    return incident


@router.patch(
    "/{incident_id}",
    response_model=Incident,
    summary="Update Incident",
    description="Update incident fields",
)
async def update_incident(
    incident_id: str,
    incident_update: IncidentUpdate,
) -> Incident:
    """
    Update an incident.

    Args:
        incident_id: Unique incident identifier
        incident_update: Fields to update

    Returns:
        Updated incident
    """
    incident = _incidents.get(incident_id) or _load_incident_from_persistence(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )
    update_data = incident_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(incident, field, value)

    incident.updated_at = datetime.utcnow()

    # Set resolved_at if status changed to resolved
    if incident_update.status == IncidentStatus.RESOLVED and incident.resolved_at is None:
        incident.resolved_at = datetime.utcnow()

    _persist_save_incident(incident)
    logger.info(f"Updated incident: {incident_id}")
    return incident


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Incident",
    description="Delete an incident (soft delete in production)",
)
async def delete_incident(incident_id: str) -> None:
    """
    Delete an incident.

    Args:
        incident_id: Unique incident identifier
    """
    # Check in-memory then persistence (handles evicted incidents).
    if incident_id not in _incidents:
        if _load_incident_from_persistence(incident_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident {incident_id} not found",
            )

    _incidents.pop(incident_id, None)
    _persist_delete_incident(incident_id)
    logger.info(f"Deleted incident: {incident_id}")


@router.post(
    "/{incident_id}/analyze",
    response_model=Incident,
    summary="Trigger RCA",
    description="Trigger root cause analysis for an incident",
)
async def analyze_incident(
    request: Request,
    incident_id: str,
    enable_thinking: bool = Query(True, description="Enable extended thinking"),
) -> Incident:
    """
    Trigger RCA for an incident.

    Updates the incident with RCA results.

    Args:
        incident_id: Incident to analyze
        enable_thinking: Enable extended thinking mode

    Returns:
        Updated incident with RCA results
    """
    incident = _incidents.get(incident_id) or _load_incident_from_persistence(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )
    incident.status = IncidentStatus.ANALYZING
    incident.updated_at = datetime.utcnow()

    await _trigger_analysis(request, incident, enable_thinking)
    # _trigger_analysis mutates status/rca/updated_at in place — persist the result.
    _persist_save_incident(incident)

    return incident


@router.post(
    "/{incident_id}/remediate",
    summary="Remediate Incident",
    description=(
        "Approve-and-remediate an incident. Demo incidents heal the injected "
        "fault on the t3 control agent; real incidents restart the affected "
        "service through the constitutional gate (same path as chat "
        "approve-to-run, so Tier-1 safety + the action kill-switch + whitelist "
        "all still apply). The verdict is surfaced in the response."
    ),
)
async def remediate_incident(request: Request, incident_id: str) -> dict[str, Any]:
    """Run the remediation for an incident and resolve it on success.

    Demo incidents (source ``demo-mode`` / a scenario tag) call the matching t3
    chaos heal — the action that actually clears them. Real incidents restart the
    first affected service through ``execute_tool_call`` so the Tier-1 safety
    principles, ``AIOPS_ENABLE_ACTION_TOOLS`` kill-switch and container whitelist
    are all enforced. Status goes REMEDIATING during the attempt, RESOLVED on
    success, or back to PENDING_APPROVAL when the gate/executor declines so the
    incident stays actionable (retry / open in chat).
    """
    incident = _incidents.get(incident_id) or _load_incident_from_persistence(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    prior_status = incident.status

    # Anti-storm / idempotency: refuse a second remediation while one is already
    # in flight — every call drives a real restart/heal control action.
    if prior_status == IncidentStatus.REMEDIATING:
        return {
            "incident_id": incident_id,
            "status": "in_progress",
            "success": False,
            "method": None,
            "error_code": "already_remediating",
            "detail": "A remediation is already in progress for this incident.",
            "verdict": None,
            "incident": incident,
        }

    incident.status = IncidentStatus.REMEDIATING
    incident.updated_at = datetime.utcnow()
    _persist_save_incident(incident)

    # Demo incidents heal via the t3 agent (the action that truly clears them).
    from src.api.routes.demo import _SCENARIO_IDS

    scenario = next((t for t in (incident.tags or []) if t in _SCENARIO_IDS), None)
    is_demo = incident.source == "demo-mode" or "demo" in (incident.tags or [])

    verdict: Any = None
    error_code: Any = None

    if is_demo and scenario:
        # ── PACED + STAGED + GATED + VERIFIED demo remediation (W4-B) ────────
        # The demo heal drives a real control action on the remote t3, so honour
        # the same production kill-switch the demo routes enforce.
        from src.api.routes.demo import _ensure_demo_allowed

        _ensure_demo_allowed()

        return await _run_demo_remediation(request, incident, scenario)
    else:
        service = (
            incident.affected_services[0].name
            if incident.affected_services
            else None
        )
        if not service:
            incident.status = prior_status
            incident.updated_at = datetime.utcnow()
            _persist_save_incident(incident)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Incident has no affected service to remediate",
            )

        from src.api.routes.tools import execute_tool_call

        # Carry the REAL evidence-based confidence (the RCA confidence when the
        # incident has been analysed) rather than synthesizing the auto-threshold
        # just to clear the authorization matrix. human_approved=True is the
        # actual authorization here, and the validator now treats explicit human
        # approval as the matrix authorization (Tier-1 still blocks
        # unconditionally), so the audit trail records the true confidence instead
        # of a misleading 0.90. Unanalysed incidents have no RCA confidence, so
        # fall back to the approval threshold as a neutral, non-inflated value.
        validator = getattr(request.app.state, "validator", None)
        approval_threshold = (
            getattr(validator, "confidence_threshold_approval", 0.7) or 0.7
        )
        real_confidence = (
            incident.rca.confidence
            if incident.rca and incident.rca.confidence is not None
            else float(approval_threshold)
        )
        try:
            result = await execute_tool_call(
                request,
                tool_name="restart_service",
                parameters={
                    "service_name": service,
                    "reason": f"Operator-approved remediation for {incident.id}",
                    "confidence": float(real_confidence),
                },
                context={
                    # Evidence-based: only assert telemetry evidence when the
                    # incident has actually been analysed (carries an RCA),
                    # rather than hardcoding True regardless.
                    "telemetry_evidence": bool(incident.rca),
                    "audit_enabled": _audit_enabled(),
                    "human_approved": True,
                    "source": "incident_remediate",
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Remediation for %s raised: %s", incident_id, exc)
            incident.status = IncidentStatus.PENDING_APPROVAL
            incident.updated_at = datetime.utcnow()
            _persist_save_incident(incident)
            return {
                "incident_id": incident_id,
                "status": "refused",
                "success": False,
                "method": "restart_service",
                "error_code": "execution_failed",
                "detail": str(exc),
                "verdict": None,
                "incident": incident,
            }

        success = bool(result.get("success"))
        meta = result.get("metadata")
        verdict = result.get("verdict") or (
            meta.get("constitutional") if isinstance(meta, dict) else None
        )
        error_code = result.get("error_code")
        detail = (
            "Service restart executed."
            if success
            else str(result.get("error") or error_code or "Remediation declined.")
        )
        method = "restart_service"

    if success:
        incident.status = IncidentStatus.RESOLVED
        if incident.resolved_at is None:
            incident.resolved_at = datetime.utcnow()
    else:
        # Keep it actionable so the operator can retry / open it in chat.
        incident.status = IncidentStatus.PENDING_APPROVAL
    incident.updated_at = datetime.utcnow()
    _persist_save_incident(incident)
    logger.info(
        "Remediation for %s via %s -> success=%s", incident_id, method, success
    )

    return {
        "incident_id": incident_id,
        "status": "resolved" if success else "refused",
        "success": success,
        "method": method,
        "error_code": error_code,
        "detail": detail,
        "verdict": verdict,
        "incident": incident,
    }


@router.post(
    "/{incident_id}/dismiss",
    response_model=Incident,
    summary="Dismiss Incident",
    description="Reject remediation and archive the incident (status -> closed).",
)
async def dismiss_incident(incident_id: str) -> Incident:
    """Operator rejected the remediation: archive the incident (CLOSED)."""
    incident = _incidents.get(incident_id) or _load_incident_from_persistence(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )
    incident.status = IncidentStatus.CLOSED
    if incident.resolved_at is None:
        incident.resolved_at = datetime.utcnow()
    incident.updated_at = datetime.utcnow()
    _persist_save_incident(incident)
    logger.info("Dismissed incident: %s", incident_id)
    return incident


@router.get(
    "/{incident_id}/similar",
    summary="Find Similar Incidents",
    description="Find similar incidents from graph memory",
)
async def find_similar_incidents(
    request: Request,
    incident_id: str,
    limit: int = Query(5, ge=1, le=20),
) -> dict[str, Any]:
    """
    Find similar incidents using graph-episodic memory.

    Args:
        incident_id: Reference incident
        limit: Maximum similar incidents to return

    Returns:
        List of similar incidents with similarity scores
    """
    if _incidents.get(incident_id) is None and _load_incident_from_persistence(incident_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    # This will use Neo4j graph queries when implemented
    neo4j_client = getattr(request.app.state, "neo4j_client", None)

    if neo4j_client is None:
        return {
            "incident_id": incident_id,
            "similar_incidents": [],
            "message": "Graph memory not available",
        }

    try:
        similar = await neo4j_client.find_similar_incidents(incident_id, limit)

        return {
            "incident_id": incident_id,
            "similar_incidents": similar,
            "total": len(similar),
        }
    except Exception as e:
        logger.error(f"Failed to find similar incidents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar incidents: {str(e)}",
        )


# Helper functions

_VALID_RISKS = {"low", "medium", "high"}


def _build_remediation_plan(incident: Incident, rca_metadata: dict[str, Any]):
    """Map the RCA's remediation steps into a ``RemediationPlan`` (W4-A).

    The reasoning agent emits ``remediation_steps`` as a list of
    ``{"action": <str>, "risk": "low|medium|high"}`` (see reasoning_agent.py's
    RCA prompt). Each becomes a ``RemediationStep``. When no structured steps are
    present, a minimal single-step plan describing the heal is built so the UI
    still renders a plan. ``overall_risk`` is the highest step risk; the plan
    requires approval whenever any step does or any step is medium/high risk.
    """
    from src.api.schemas.incident import RemediationPlan, RemediationStep

    raw_steps = rca_metadata.get("remediation_steps") or []
    steps: list[RemediationStep] = []
    risk_rank = {"low": 0, "medium": 1, "high": 2}
    highest = 0

    for idx, raw in enumerate(raw_steps, start=1):
        if not isinstance(raw, dict):
            continue
        action = str(raw.get("action") or "").strip()
        if not action:
            continue
        risk = str(raw.get("risk") or "medium").strip().lower()
        if risk not in _VALID_RISKS:
            risk = "medium"
        highest = max(highest, risk_rank[risk])
        steps.append(
            RemediationStep(
                order=idx,
                action=action,
                risk=risk,
                # Anything riskier than low needs an operator's nod.
                requires_approval=risk != "low",
            )
        )

    if not steps:
        # Minimal 1-step fallback describing the heal.
        affected = (
            incident.affected_services[0].name
            if incident.affected_services
            else "the affected service"
        )
        steps.append(
            RemediationStep(
                order=1,
                action=f"Remediate {affected} for incident {incident.id}",
                risk="medium",
                requires_approval=True,
            )
        )
        highest = max(highest, risk_rank["medium"])

    overall_risk = {0: "low", 1: "medium", 2: "high"}[highest]
    requires_approval = any(s.requires_approval for s in steps)

    now = datetime.utcnow()
    return RemediationPlan(
        plan_id=f"plan-{incident.id}-{uuid.uuid4().hex[:8]}",
        incident_id=incident.id,
        created_at=now,
        steps=steps,
        overall_risk=overall_risk,
        requires_approval=requires_approval,
    )


def _validate_and_audit_demo_heal(
    request: Request,
    incident: Incident,
    scenario: str,
) -> Any:
    """Run the demo-incident heal through the constitutional validator + audit.

    The demo heal is a chaos-reversal control action on the remote t3 host, not a
    container restart/scale, so it cannot use ``execute_tool_call``'s whitelist
    gate. To keep the "every action is validated" guarantee true (and to stop the
    demo branch being a silent bypass), we validate the heal directly with the
    live ``ConstitutionalValidator`` and write an audit line either way. Returns
    the serialized verdict dict (or ``None`` if no validator is available — in
    which case the caller proceeds, matching demo's permissive intent but now
    with an audit trail).
    """
    validator = getattr(request.app.state, "validator", None)

    # W4-B: gate with the REAL evidence-based confidence (the analysed incident's
    # RCA confidence) instead of synthesizing the auto threshold (which always
    # cleared the matrix). human_approved=True is the actual authorization (the
    # operator clicked Approve), so Tier-1 still authorizes a benign reversible
    # heal even when the RCA confidence is modest. Unanalysed incidents have no
    # RCA confidence — fall back to the approval threshold as a neutral,
    # non-inflated value rather than the auto threshold.
    approval_threshold = (
        getattr(validator, "confidence_threshold_approval", 0.7) or 0.7
        if validator is not None
        else 0.7
    )
    real_confidence = (
        incident.rca.confidence
        if incident.rca and incident.rca.confidence is not None
        else float(approval_threshold)
    )

    verdict = None
    if validator is not None:
        try:
            from src.api.routes.tools import _constitutional_verdict

            report = validator.validate(
                action_id=f"demo-heal-{incident.id}-{int(datetime.utcnow().timestamp() * 1000)}",
                action_description=f"Demo chaos-heal '{scenario}' for incident {incident.id}",
                # A heal RESTORES service health — it is not a destructive
                # restart/deploy/scale_down, so P1.2 does not classify it as a
                # destructive action. It is operator-approved and reversible.
                action_type="heal",
                confidence=float(real_confidence),
                context={
                    "active_incident": True,
                    "human_approved": True,
                    "telemetry_evidence": bool(incident.rca),
                    "audit_enabled": _audit_enabled(),
                    "action_scope": "single",
                    "source": "demo_heal",
                },
            )
            verdict = _constitutional_verdict(report)
        except Exception as exc:  # noqa: BLE001 - validation must not break heal
            logger.warning("Demo-heal constitutional validation failed: %s", exc)
            verdict = None

    # Audit the attempt regardless of validator availability.
    try:
        from src.api.routes.tools import _audit_action_attempt

        _audit_action_attempt(
            "demo_heal",
            {"scenario": scenario, "incident_id": incident.id},
            outcome=(
                "refused"
                if verdict is not None and not verdict.get("can_proceed", True)
                else "validated"
            ),
            error_code=None,
            verdict=verdict,
        )
    except Exception as exc:  # noqa: BLE001 - audit must not break heal
        logger.warning("Demo-heal audit logging failed: %s", exc)

    return verdict


async def _run_demo_remediation(
    request: Request,
    incident: Incident,
    scenario: str,
) -> dict[str, Any]:
    """Paced + staged + gated + verified REAL demo remediation (W4-B).

    Replaces the old instant rubber-stamp. The flow:
      1. Mark REMEDIATING, persist, broadcast (already REMEDIATING on entry).
      2. Stage 1 — validate against constitutional principles using the REAL
         RCA confidence (``_validate_and_audit_demo_heal``). If blocked, set
         PENDING_APPROVAL, persist, broadcast, and return the rejection — NO heal.
      3. Stage 2 — execute the REAL t3 ``chaos_heal``.
      4. Stage 3 — VERIFY recovery by polling ``t3_status`` until the scenario
         reads inactive / the affected container is running. Only then resolve.
      5. Stage 4 — RESOLVED & archived (set resolved_at so MTTR populates), or
         leave REMEDIATING/FAILED with a clear detail if verification never
         confirms — never a false resolve.

    Pacing uses ``asyncio.sleep`` between stages so the UI shows real progress.
    t3 failures fail closed (the client never raises); we surface them.
    """
    from src.remediation import t3_client

    # The affected container: nextcloud-db for db_down, else the first affected
    # service (the demo always tags the app container as nextcloud).
    affected_container = (
        incident.affected_services[0].name
        if incident.affected_services
        else ("nextcloud-db" if scenario == "db_down" else "nextcloud")
    )

    # Stage 1: constitutional validation (REAL confidence gate).
    await _broadcast_incident_update(
        incident, stage="Validating against constitutional principles"
    )
    await asyncio.sleep(_DEMO_STAGE_DELAY_VALIDATE)

    verdict = _validate_and_audit_demo_heal(request, incident, scenario)
    if verdict is not None and not verdict.get("can_proceed", True):
        # Gate refused the heal — keep the incident actionable, surface why,
        # do NOT heal (mirrors the real-path refusal contract).
        incident.status = IncidentStatus.PENDING_APPROVAL
        incident.updated_at = datetime.utcnow()
        _persist_save_incident(incident)
        await _broadcast_incident_update(incident, stage="Remediation blocked")
        return {
            "incident_id": incident.id,
            "status": "refused",
            "success": False,
            "method": "demo_heal",
            "error_code": "validation_blocked",
            "detail": verdict.get("explanation")
            or "Demo heal blocked by constitutional validation.",
            "verdict": verdict,
            "incident": incident,
        }

    # Stage 2: execute the REAL t3 heal.
    heal_action = f"chaos-heal '{scenario}' on {affected_container}"
    await _broadcast_incident_update(
        incident, stage=f"Executing remediation — {heal_action}"
    )
    await asyncio.sleep(_DEMO_STAGE_DELAY_EXECUTE)

    result = await t3_client.chaos_heal(scenario)
    heal_ok = bool(result.get("success"))
    detail = str(result.get("detail") or result.get("error") or "")

    if not heal_ok:
        # The t3 heal itself failed — never resolve; keep it actionable.
        incident.status = IncidentStatus.PENDING_APPROVAL
        incident.updated_at = datetime.utcnow()
        _persist_save_incident(incident)
        await _broadcast_incident_update(incident, stage="Remediation failed")
        return {
            "incident_id": incident.id,
            "status": "refused",
            "success": False,
            "method": "demo_heal",
            "error_code": "execution_failed",
            "detail": detail or "t3 chaos-heal failed.",
            "verdict": verdict,
            "incident": incident,
        }

    # Stage 3: verify recovery before resolving.
    await _broadcast_incident_update(incident, stage="Verifying recovery")
    await asyncio.sleep(_DEMO_STAGE_DELAY_VERIFY)

    verified = await _verify_scenario_healed(scenario, affected_container)

    if not verified:
        # Heal call succeeded but recovery never confirmed — DO NOT falsely
        # resolve. Leave it actionable with a clear message.
        incident.status = IncidentStatus.PENDING_APPROVAL
        incident.updated_at = datetime.utcnow()
        _persist_save_incident(incident)
        await _broadcast_incident_update(incident, stage="Recovery not confirmed")
        return {
            "incident_id": incident.id,
            "status": "refused",
            "success": False,
            "method": "demo_heal",
            "error_code": "verification_failed",
            "detail": (
                "Heal command sent but recovery was not confirmed by the t3 "
                "status within the verification window."
            ),
            "verdict": verdict,
            "incident": incident,
        }

    # Stage 4: resolved & archived (set resolved_at so MTTR populates).
    incident.status = IncidentStatus.RESOLVED
    if incident.resolved_at is None:
        incident.resolved_at = datetime.utcnow()
    incident.updated_at = datetime.utcnow()
    _persist_save_incident(incident)
    await _broadcast_incident_update(incident, stage="Resolved & archived")
    logger.info(
        "Demo remediation for %s via demo_heal -> RESOLVED (verified)", incident.id
    )

    return {
        "incident_id": incident.id,
        "status": "resolved",
        "success": True,
        "method": "demo_heal",
        "error_code": None,
        "detail": detail or "Scenario healed and recovery verified.",
        "verdict": verdict,
        "incident": incident,
    }


async def _trigger_analysis(
    request: Request,
    incident: Incident,
    enable_thinking: bool = True,
) -> None:
    """Trigger RCA analysis for an incident using the LangGraph orchestration pipeline.

    Raises:
        HTTPException(503): If the orchestration pipeline is not initialized.
    """
    # Verify orchestration pipeline is available (MANDATORY)
    incident_graph = getattr(request.app.state, "incident_graph", None)
    if incident_graph is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestration pipeline not initialized. Cannot analyze incidents.",
        )

    # Build incident data for analysis
    incident_data = {
        "id": incident.id,
        "title": incident.title,
        "description": incident.description,
        "severity": incident.severity.value,
        "category": incident.category.value,
        "affected_services": [s.model_dump() for s in incident.affected_services],
        "telemetry": incident.telemetry.model_dump() if incident.telemetry else None,
        "detected_at": incident.detected_at.isoformat() if incident.detected_at else None,
    }

    # ── LangGraph Orchestrated Pipeline (MANDATORY) ────────────────
    try:
        graph_result = await incident_graph.ainvoke({
            "telemetry_data": incident_data,
            "correlation_id": incident.id,
            "steps_completed": [],
            "latency_ms": {},
        })

        # Extract RCA from graph state
        rca_data = graph_result.get("rca_result")
        if rca_data and rca_data.get("metadata"):
            from src.api.schemas.incident import RCAResult

            incident.rca = RCAResult(
                root_cause=rca_data["metadata"].get("root_cause", "Unknown"),
                causal_chain=rca_data["metadata"].get("causal_chain", []),
                confidence=graph_result.get("confidence", 0.0),
                reasoning=rca_data["metadata"].get("reasoning"),
                similar_incidents=rca_data["metadata"].get("similar_incidents"),
            )

            # W4-A: build the remediation_plan the UI renders, from the RCA's
            # remediation_steps (the reasoning agent emits a list of
            # {"action": ..., "risk": "low|medium|high"}). Falls back to a
            # minimal 1-step plan describing the heal when no structured steps
            # are present. Plan-building must never break analysis.
            try:
                incident.remediation_plan = _build_remediation_plan(
                    incident, rca_data["metadata"]
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to build remediation_plan for %s: %s", incident.id, exc
                )

        # Use authorization level from constitutional validation.
        #
        # IMPORTANT: analysis performs NO execution — there is no executor that
        # picks up a REMEDIATING incident and runs anything; the actual restart
        # only happens when a human hits "Approve & Remediate" (-> remediate_
        # incident -> the gated execute_tool_call). Previously an "automatic"
        # auth_level flipped the incident to REMEDIATING here, which then made the
        # anti-storm guard in remediate_incident refuse the operator's manual
        # remediation with `already_remediating` — permanently locking the
        # incident in a "Remediating" state that nothing was remediating.
        #
        # Until autonomous execution is wired, cap a high-confidence verdict at
        # PENDING_APPROVAL so it stays actionable by an operator. (Setting
        # REMEDIATING from analysis is a no-op-with-deadlock, not autonomy.)
        # AUDIT-D5 TODO: if/when an executor consumes REMEDIATING incidents and
        # runs the gated restart end-to-end, switch "automatic" back to entering
        # REMEDIATING immediately before that execute_tool_call (and clear it on
        # completion) rather than from analysis.
        auth_level = graph_result.get("authorization_level", "alert")
        if auth_level in ("automatic", "approval"):
            incident.status = IncidentStatus.PENDING_APPROVAL
        else:
            incident.status = IncidentStatus.ANALYZING

        incident.updated_at = datetime.utcnow()
        steps = graph_result.get("steps_completed", [])
        logger.info(
            f"LangGraph RCA for {incident.id}: auth={auth_level}, steps={steps}"
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"LangGraph pipeline failed for {incident.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration pipeline failed: {str(e)}",
        )


__all__ = ["router"]
