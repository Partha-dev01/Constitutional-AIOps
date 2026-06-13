"""D-item4: legacy /graph/* routes must no longer 500 / silently return [].

Covers the routes the audit found broken-but-quiet:
  * GET /graph/episodes/{id}          (was always 500: un-awaited coroutine +
                                        nonexistent .id/.timestamp/.resolution attrs)
  * GET /graph/episodes/{id}/similar  (was always []: called a nonexistent
                                        ContextRetriever.find_similar method)
  * GET /graph/services               (was always []: passed dependencies/
                                        dependents kwargs ServiceNode doesn't have)
  * GET /graph/stats fallback         (was always 0: called nonexistent
                                        episode_store.list_episodes)
  * triplet persistence + min_confidence filter (the entity-edge weight now
    carries r.confidence so min_confidence actually filters).

Route functions are called directly with a SimpleNamespace request (no src.main
import, no FastAPI DI), mirroring the established test style. Neo4j is mocked.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.memory.episode_store import Episode, EpisodeStore


def _make_request(**state) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(**state)))


def _seed_episode(store: EpisodeStore, episode_id: str = "ep-1") -> Episode:
    ep = Episode(
        episode_id=episode_id,
        incident_id="INC-1",
        title="Pool exhaustion on backend",
        description="connection pool exhausted",
        severity="critical",
        category="performance",
        detected_at=datetime(2026, 1, 1, 12, 0, 0),
        root_cause="db pool misconfig",
        confidence=0.88,
        affected_services=["backend", "db"],
        outcome="resolved",
        resolution_notes="raised pool size",
    )
    # Populate the in-memory store directly (avoid the embedding-service load).
    store._memory_store[ep.episode_id] = ep
    signature = ep.generate_signature()
    store._signature_index.setdefault(signature, []).append(ep.episode_id)
    return ep


class TestGetEpisodeById:
    @pytest.mark.asyncio
    async def test_returns_episode_not_500(self):
        from src.api.routes.graph import get_episode

        store = EpisodeStore(neo4j_client=None)
        ep = _seed_episode(store)
        req = _make_request(episode_store=store)

        result = await get_episode(req, ep.episode_id)

        # Maps off the real dataclass attrs, not the nonexistent id/timestamp/...
        assert result.id == "ep-1"
        assert result.title == "Pool exhaustion on backend"
        assert result.timestamp == ep.detected_at
        assert result.services == ["backend", "db"]
        assert result.resolution == "raised pool size"
        assert result.confidence == 0.88
        assert result.metadata["incident_id"] == "INC-1"

    @pytest.mark.asyncio
    async def test_missing_episode_404(self):
        from fastapi import HTTPException

        from src.api.routes.graph import get_episode

        store = EpisodeStore(neo4j_client=None)
        req = _make_request(episode_store=store)

        with pytest.raises(HTTPException) as ei:
            await get_episode(req, "nope")
        assert ei.value.status_code == 404


class TestFindSimilarEpisodes:
    @pytest.mark.asyncio
    async def test_returns_similar_not_empty(self):
        from src.api.routes.graph import find_similar_episodes

        store = EpisodeStore(neo4j_client=None)
        source = _seed_episode(store, "ep-src")
        # A second episode sharing category+services+rc-type -> same signature ->
        # the in-memory similarity path returns it.
        other = Episode(
            episode_id="ep-other",
            incident_id="INC-2",
            title="Another pool exhaustion",
            description="same shape",
            severity="critical",
            category="performance",
            detected_at=datetime(2026, 1, 2, 12, 0, 0),
            root_cause="db pool misconfig",
            confidence=0.7,
            affected_services=["backend", "db"],
            outcome="resolved",
        )
        store._memory_store[other.episode_id] = other
        store._signature_index.setdefault(other.generate_signature(), []).append(other.episode_id)

        req = _make_request(episode_store=store)
        result = await find_similar_episodes(req, source.episode_id, limit=5)

        assert isinstance(result, list)
        assert len(result) >= 1
        # The source episode itself is excluded.
        assert all(item.episode.id != "ep-src" for item in result)
        assert any(item.episode.id == "ep-other" for item in result)

    @pytest.mark.asyncio
    async def test_no_store_returns_empty(self):
        from src.api.routes.graph import find_similar_episodes

        req = _make_request(episode_store=None)
        result = await find_similar_episodes(req, "x", limit=5)
        assert result == []


class TestListServices:
    @pytest.mark.asyncio
    async def test_services_built_without_validation_error(self):
        """ServiceNode no longer receives dependencies/dependents kwargs it lacks;
        the dependency info goes into metadata so the route returns real rows
        instead of swallowing a ValidationError and returning []."""
        from src.api.routes.graph import list_services

        # Mock the async Neo4j session/run/data chain.
        session = MagicMock()
        run_result = MagicMock()
        run_result.data = AsyncMock(return_value=[
            {
                "name": "backend",
                "status": "healthy",
                "type": "service",
                "dependencies": ["db"],
                "dependents": ["frontend"],
            }
        ])
        session.run = AsyncMock(return_value=run_result)
        session_cm = MagicMock()
        session_cm.__aenter__ = AsyncMock(return_value=session)
        session_cm.__aexit__ = AsyncMock(return_value=False)
        neo4j_client = MagicMock()
        neo4j_client.session = MagicMock(return_value=session_cm)

        req = _make_request(neo4j_client=neo4j_client)
        result = await list_services(req)

        assert len(result) == 1
        node = result[0]
        assert node.name == "backend"
        assert node.status == "healthy"
        assert node.metadata["dependencies"] == ["db"]
        assert node.metadata["dependents"] == ["frontend"]


class TestGraphStatsFallback:
    @pytest.mark.asyncio
    async def test_in_memory_episode_count(self):
        """With no Neo4j, /graph/stats counts the in-memory store instead of
        calling the nonexistent list_episodes (which returned 0)."""
        from src.api.routes.graph import get_graph_stats

        store = EpisodeStore(neo4j_client=None)
        _seed_episode(store, "ep-a")
        _seed_episode(store, "ep-b")

        req = _make_request(neo4j_client=None, episode_store=store)
        result = await get_graph_stats(req)

        assert result.connected is False
        assert result.episode_count == 2
