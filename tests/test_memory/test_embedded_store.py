"""Embedded (sqlite) graph backend: persistence, write-through, rehydrate, config.

Each test points AIOPS_DATA_DIR at a fresh tmp dir (same isolation pattern as
tests/test_persistence/test_store.py) so nothing touches the real data dir.
"""

from datetime import datetime

import pytest

from src.config import GraphConfig
from src.memory.episode_store import Episode, EpisodeStore


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    yield tmp_path


def _episode(episode_id: str = "ep-1", embedding=None) -> Episode:
    return Episode(
        episode_id=episode_id,
        incident_id="INC-1",
        title="backend pool exhaustion",
        description="connection pool exhausted",
        severity="error",
        category="performance",
        detected_at=datetime(2026, 1, 1, 12, 0, 0),
        confidence=0.9,
        affected_services=["backend"],
        # Pre-set the embedding so store_episode never lazy-loads the model.
        embedding=embedding if embedding is not None else [0.1, 0.2, 0.3, 0.4],
    )


def test_embedded_store_roundtrip_persists_across_instances(tmp_data_dir):
    from src.memory.embedded_store import EmbeddedEpisodeStore

    store = EmbeddedEpisodeStore()
    store.upsert(_episode("ep-roundtrip"))
    assert store.count() == 1

    # A fresh instance (same data dir) must see the persisted episode.
    reopened = EmbeddedEpisodeStore()
    loaded = reopened.load_all()
    assert len(loaded) == 1
    assert loaded[0].episode_id == "ep-roundtrip"
    assert loaded[0].affected_services == ["backend"]


def test_embedded_store_preserves_embedding(tmp_data_dir):
    from src.memory.embedded_store import EmbeddedEpisodeStore

    store = EmbeddedEpisodeStore()
    store.upsert(_episode("ep-emb", embedding=[0.5, 0.6, 0.7]))

    loaded = EmbeddedEpisodeStore().load_all()
    assert loaded[0].embedding == [0.5, 0.6, 0.7]


def test_embedded_store_upsert_is_idempotent(tmp_data_dir):
    from src.memory.embedded_store import EmbeddedEpisodeStore

    store = EmbeddedEpisodeStore()
    ep = _episode("ep-dup")
    store.upsert(ep)
    ep.title = "updated title"
    store.upsert(ep)

    loaded = EmbeddedEpisodeStore().load_all()
    assert store.count() == 1
    assert loaded[0].title == "updated title"


def test_embedded_store_delete(tmp_data_dir):
    from src.memory.embedded_store import EmbeddedEpisodeStore

    store = EmbeddedEpisodeStore()
    store.upsert(_episode("ep-del"))
    store.delete("ep-del")
    assert store.count() == 0


async def test_episode_store_write_through_and_rehydrate(tmp_data_dir):
    """EpisodeStore(embedded_store=...) persists on store and reloads on init."""
    from src.memory.embedded_store import EmbeddedEpisodeStore

    backend = EmbeddedEpisodeStore()
    store = EpisodeStore(embedded_store=backend)
    await store.store_episode(_episode("ep-wt"))

    # Persisted to the durable backend.
    assert backend.count() == 1

    # A brand-new EpisodeStore over the same backend rehydrates the working set.
    reopened = EpisodeStore(embedded_store=EmbeddedEpisodeStore())
    assert "ep-wt" in reopened._memory_store
    got = await reopened.get_episode("ep-wt")
    assert got is not None
    assert got.title == "backend pool exhaustion"


def test_graph_config_backend_selection(monkeypatch):
    monkeypatch.delenv("AIOPS_GRAPH_BACKEND", raising=False)
    assert GraphConfig().backend == "neo4j"  # safe default

    monkeypatch.setenv("AIOPS_GRAPH_BACKEND", "embedded")
    assert GraphConfig().backend == "embedded"

    monkeypatch.setenv("AIOPS_GRAPH_BACKEND", "MEMORY")
    assert GraphConfig().backend == "memory"  # normalized

    monkeypatch.setenv("AIOPS_GRAPH_BACKEND", "bogus")
    assert GraphConfig().backend == "neo4j"  # unknown -> safe default
