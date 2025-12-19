"""
Constitutional AIOps - Incidents API Routes

Incident management endpoints with CRUD operations.
Incidents are stored in Neo4j graph-episodic memory.
"""

import logging
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

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory incident store (replace with Neo4j in production)
_incidents: dict[str, Incident] = {}

# Counter for incident IDs
_incident_counter = 0


def _generate_incident_id() -> str:
    """Generate unique incident ID."""
    global _incident_counter
    _incident_counter += 1
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
    logger.info(f"Created incident: {incident_id}")

    # Trigger auto-analysis if requested
    if incident_create.auto_analyze:
        await _trigger_analysis(request, incident)

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

    Args:
        incident_id: Unique incident identifier

    Returns:
        Incident details
    """
    if incident_id not in _incidents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    return _incidents[incident_id]


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
    if incident_id not in _incidents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    incident = _incidents[incident_id]
    update_data = incident_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(incident, field, value)

    incident.updated_at = datetime.utcnow()

    # Set resolved_at if status changed to resolved
    if incident_update.status == IncidentStatus.RESOLVED and incident.resolved_at is None:
        incident.resolved_at = datetime.utcnow()

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
    if incident_id not in _incidents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    del _incidents[incident_id]
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
    if incident_id not in _incidents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    incident = _incidents[incident_id]
    incident.status = IncidentStatus.ANALYZING
    incident.updated_at = datetime.utcnow()

    await _trigger_analysis(request, incident, enable_thinking)

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
    if incident_id not in _incidents:
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
        # TODO: Implement Neo4j similarity query
        similar = []  # await neo4j_client.find_similar_incidents(incident_id, limit)

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

async def _trigger_analysis(
    request: Request,
    incident: Incident,
    enable_thinking: bool = True,
) -> None:
    """Trigger RCA analysis for an incident."""
    reasoning_agent = getattr(request.app.state, "reasoning_agent", None)

    if reasoning_agent is None:
        logger.warning("Reasoning agent not available, skipping analysis")
        return

    try:
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

        agent_response = await reasoning_agent.analyze_rca(
            incident_data=incident_data,
            enable_thinking=enable_thinking,
        )

        # Update incident with RCA results
        if agent_response.metadata:
            from src.api.schemas.incident import RCAResult

            incident.rca = RCAResult(
                root_cause=agent_response.metadata.get("root_cause", "Unknown"),
                causal_chain=agent_response.metadata.get("causal_chain", []),
                confidence=agent_response.confidence,
                reasoning=agent_response.metadata.get("reasoning"),
                similar_incidents=agent_response.metadata.get("similar_incidents"),
            )

        # Update status based on confidence
        if agent_response.confidence >= 0.9:
            incident.status = IncidentStatus.REMEDIATING
        elif agent_response.confidence >= 0.7:
            incident.status = IncidentStatus.PENDING_APPROVAL
        else:
            incident.status = IncidentStatus.ANALYZING  # Needs more analysis

        incident.updated_at = datetime.utcnow()
        logger.info(f"Completed RCA for {incident.id} (confidence: {agent_response.confidence})")

    except Exception as e:
        logger.error(f"RCA failed for {incident.id}: {e}")
        # Don't fail the request, just log the error


__all__ = ["router"]
