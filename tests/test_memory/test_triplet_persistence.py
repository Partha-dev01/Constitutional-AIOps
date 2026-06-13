"""D-item4: LLM-extracted semantic triplets persist to Neo4j with confidence,
and the MIN_TRIPLET_CONFIDENCE filter actually screens low-quality relations.

Exercises EpisodeStore._store_episode_graph against a mocked Neo4j session,
capturing every session.run call and inspecting the RELATES (Entity) writes.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.memory.episode_store import MIN_TRIPLET_CONFIDENCE, Episode, EpisodeStore


def _mock_neo4j_session():
    """Return (neo4j_client, run_calls) where run_calls captures every run()."""
    run_calls: list[tuple[str, dict]] = []

    async def _run(query, **params):
        run_calls.append((query, params))
        result = MagicMock()
        result.data = AsyncMock(return_value=[])
        return result

    session = MagicMock()
    session.run = AsyncMock(side_effect=_run)
    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=session)
    session_cm.__aexit__ = AsyncMock(return_value=False)

    client = MagicMock()
    client.session = MagicMock(return_value=session_cm)
    return client, run_calls


def _relates_calls(run_calls):
    return [
        (q, p) for q, p in run_calls
        if "r:RELATES" in q and "extraction_method" in q
    ]


@pytest.mark.asyncio
async def test_high_confidence_triplet_persisted_with_confidence():
    client, run_calls = _mock_neo4j_session()
    store = EpisodeStore(neo4j_client=client)

    episode = Episode(
        episode_id="ep-trip",
        incident_id="INC-9",
        title="backend pool exhaustion",
        description="x",
        severity="error",
        category="performance",
        detected_at=datetime(2026, 1, 1, 12, 0, 0),
        confidence=0.9,
        affected_services=["backend"],
        triplets=[
            {"subject": "backend", "relation": "EXPERIENCED", "object": "pool_exhaustion", "confidence": 0.9},
        ],
    )

    await store._store_episode_graph(episode)

    relates = _relates_calls(run_calls)
    assert len(relates) == 1
    _, params = relates[0]
    assert params["subject"] == "backend"
    assert params["object"] == "pool_exhaustion"
    assert params["confidence"] == 0.9


@pytest.mark.asyncio
async def test_low_confidence_triplet_filtered_out():
    client, run_calls = _mock_neo4j_session()
    store = EpisodeStore(neo4j_client=client)

    low = MIN_TRIPLET_CONFIDENCE - 0.2
    episode = Episode(
        episode_id="ep-trip-low",
        incident_id="INC-10",
        title="speculative",
        description="x",
        severity="warning",
        category="performance",
        detected_at=datetime(2026, 1, 1, 12, 0, 0),
        confidence=0.9,
        affected_services=["backend"],
        triplets=[
            {"subject": "a", "relation": "RELATES_TO", "object": "b", "confidence": low},
        ],
    )

    await store._store_episode_graph(episode)

    # The sub-threshold triplet must NOT be written as an Entity RELATES edge.
    assert _relates_calls(run_calls) == []


@pytest.mark.asyncio
async def test_triplet_confidence_defaults_to_episode_confidence():
    """A triplet without an explicit confidence inherits the episode confidence
    (the documented contract), so the filter operates on a real number."""
    client, run_calls = _mock_neo4j_session()
    store = EpisodeStore(neo4j_client=client)

    episode = Episode(
        episode_id="ep-trip-default",
        incident_id="INC-11",
        title="t",
        description="x",
        severity="error",
        category="performance",
        detected_at=datetime(2026, 1, 1, 12, 0, 0),
        confidence=0.95,
        affected_services=["backend"],
        triplets=[
            {"subject": "backend", "relation": "IMPACTED", "object": "frontend"},  # no confidence
        ],
    )

    await store._store_episode_graph(episode)

    relates = _relates_calls(run_calls)
    assert len(relates) == 1
    assert relates[0][1]["confidence"] == 0.95
