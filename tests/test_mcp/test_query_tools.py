"""Gate 2: MCP query tools (find_similar / get_dependencies).

After dropping the dev mock-fallbacks, the two production query tools must:
  - return ``success=False`` (not mock data) when their backing store is absent, and
  - use the live store results (no ``source=mock`` marker) when a store is present.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.mcp.server import MCPActionServer

# --- find_similar ---------------------------------------------------------

@pytest.mark.asyncio
async def test_find_similar_without_store_returns_failure() -> None:
    server = MCPActionServer()  # no episode_store injected
    result = await server._find_similar({"title": "database connection timeout"})

    assert result.success is False
    assert result.data is None
    assert "episode store" in (result.error or "").lower()
    # crucially: no mock incidents leaked through
    assert result.metadata.get("source") != "mock"


@pytest.mark.asyncio
async def test_find_similar_uses_live_episode_store() -> None:
    episode = MagicMock()
    episode.incident_id = "INC-2025-0001"
    episode.title = "DB pool exhaustion"
    episode.root_cause = "connection pool too small"
    episode.successful_actions = ["raised pool size to 50"]
    episode.resolution_time_minutes = 12

    store = MagicMock()
    store.find_similar_episodes = AsyncMock(return_value=[(episode, 0.91)])
    store._memory_store = {"a": 1, "b": 2, "c": 3}

    server = MCPActionServer(episode_store=store)
    result = await server._find_similar({"title": "db timeout", "limit": 5})

    assert result.success is True
    assert result.metadata.get("source") != "mock"
    store.find_similar_episodes.assert_awaited_once()

    incidents = result.data["similar_incidents"]
    assert len(incidents) == 1
    assert incidents[0]["incident_id"] == "INC-2025-0001"
    assert incidents[0]["similarity_score"] == 0.91
    assert result.data["total_searched"] == 3


# --- get_dependencies -----------------------------------------------------

@pytest.mark.asyncio
async def test_get_dependencies_without_client_returns_failure() -> None:
    server = MCPActionServer()  # no neo4j_client injected
    result = await server._get_dependencies({"service_name": "api-gateway"})

    assert result.success is False
    assert result.data is None
    assert "neo4j" in (result.error or "").lower()
    assert result.metadata.get("source") != "mock"


@pytest.mark.asyncio
async def test_get_dependencies_uses_live_neo4j_client() -> None:
    client = MagicMock()
    client.get_service_dependencies = AsyncMock(return_value=[
        {"name": "postgres-primary", "direction": "downstream"},
        {"name": "load-balancer", "direction": "upstream"},
    ])

    server = MCPActionServer(neo4j_client=client)
    result = await server._get_dependencies(
        {"service_name": "api-gateway", "direction": "both"}
    )

    assert result.success is True
    assert result.metadata.get("source") != "mock"
    client.get_service_dependencies.assert_awaited_once()

    deps = result.data["dependencies"]
    assert deps["downstream"] == ["postgres-primary"]
    assert deps["upstream"] == ["load-balancer"]
    assert result.data["total_dependencies"] == 2
