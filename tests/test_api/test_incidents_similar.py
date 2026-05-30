"""Gate 2: /incidents/{id}/similar wires through to Neo4j graph memory.

The route previously returned a hardcoded empty list (TODO). It now calls the
already-implemented ``neo4j_client.find_similar_incidents(incident_id, limit)``.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


async def _seed_incident(title: str):
    """Create an incident in the in-memory store and return it."""
    from src.api.routes.incidents import _incidents, create_incident
    from src.api.schemas.incident import IncidentCreate, IncidentSeverity, ServiceInfo

    _incidents.clear()
    create_req = MagicMock()
    create_req.app.state.reasoning_agent = None
    return await create_incident(
        create_req,
        IncidentCreate(
            title=title,
            severity=IncidentSeverity.HIGH,
            affected_services=[ServiceInfo(name="api-gateway")],
            auto_analyze=False,
        ),
    )


@pytest.mark.asyncio
async def test_similar_calls_neo4j_when_graph_available() -> None:
    from src.api.routes.incidents import find_similar_incidents

    incident = await _seed_incident("Seed incident for similarity")

    payload = [
        {"id": "INC-9001", "title": "related db timeout", "score": 0.82},
        {"id": "INC-9002", "title": "related latency", "score": 0.61},
    ]
    neo4j = MagicMock()
    neo4j.find_similar_incidents = AsyncMock(return_value=payload)

    req = MagicMock()
    req.app.state.neo4j_client = neo4j

    result = await find_similar_incidents(req, incident.id, limit=5)

    neo4j.find_similar_incidents.assert_awaited_once_with(incident.id, 5)
    assert result["incident_id"] == incident.id
    assert result["similar_incidents"] == payload
    assert result["total"] == 2


@pytest.mark.asyncio
async def test_similar_returns_empty_when_graph_unavailable() -> None:
    from src.api.routes.incidents import find_similar_incidents

    incident = await _seed_incident("Seed incident no graph")

    req = MagicMock()
    req.app.state.neo4j_client = None  # graph memory not wired

    result = await find_similar_incidents(req, incident.id, limit=5)

    assert result["similar_incidents"] == []
    assert "message" in result


@pytest.mark.asyncio
async def test_similar_unknown_incident_raises_404() -> None:
    from fastapi import HTTPException

    from src.api.routes.incidents import _incidents, find_similar_incidents

    _incidents.clear()
    req = MagicMock()
    req.app.state.neo4j_client = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await find_similar_incidents(req, "does-not-exist", limit=5)

    assert exc_info.value.status_code == 404
