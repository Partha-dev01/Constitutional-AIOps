"""
Tests for GET /api/v1/graph/topology and POST /api/v1/graph/seed-topology.

Pins the FROZEN session-14 payload contract the frontend schema mode builds
against:
  * fallback topology (Neo4j + collector absent) — never 5xx, health unknown,
    zero buckets of the requested length;
  * bucket placement + sum(node.buckets) == episode_count invariant;
  * incident_count counts error/critical only;
  * recent_episodes capped at 5, most recent first;
  * dynamic edge-host nodes + SHIPS_TELEMETRY edges from Prometheus discovery;
  * co-episode edge buckets;
  * defensive severity mapping (legacy "10" → "warning").

Pattern: direct route-fn calls with mock request objects (NEVER import
src.main — langgraph is not installed in CI).
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.api.routes import graph_topology as topo_module
from src.api.routes.graph_topology import _map_severity, get_topology, seed_topology
from src.memory.topology_seed import (
    PLATFORM_DEPENDENCIES,
    PLATFORM_SERVICES,
    seed_service_topology,
)

# ── helpers ──────────────────────────────────────────────────────────────────

def _make_request(neo4j_client=None, telemetry_collector=None) -> SimpleNamespace:
    return SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                neo4j_client=neo4j_client,
                telemetry_collector=telemetry_collector,
            )
        )
    )


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    async def data(self):
        return self._rows


class _FakeNeo4jClient:
    """Returns canned row lists in run-call order across all sessions.

    get_topology call order: (1) Service nodes, (2) DEPENDS_ON edges,
    (3) episodes.
    """

    def __init__(self, responses):
        self._responses = list(responses)
        self.queries: list[tuple[str, dict]] = []

    @asynccontextmanager
    async def session(self):
        yield self

    async def run(self, query, **params):
        self.queries.append((query, params))
        rows = self._responses.pop(0) if self._responses else []
        return _FakeResult(rows)


def _make_collector(prom_responses: dict[str, list[dict]]):
    """Stub telemetry collector: maps PromQL query string -> result list."""

    async def fake_get(url, params=None, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        query = (params or {}).get("query", "")
        resp.json.return_value = {"data": {"result": prom_responses.get(query, [])}}
        return resp

    client = MagicMock()
    client.get = AsyncMock(side_effect=fake_get)
    return SimpleNamespace(prometheus_url="http://mock-prom:9090", _client=client)


_NODE_ROWS = [
    {"id": "backend", "label": "Backend", "kind": "backend", "tier": 1,
     "port": 8000, "description": "API"},
    {"id": "neo4j", "label": "Neo4j", "kind": "datastore", "tier": 2,
     "port": 7687, "description": "Graph DB"},
]
_DEP_ROWS = [{"source": "backend", "target": "neo4j"}]


def _episode_row(ep_id, title, severity, at: datetime, services: list[str]):
    return {
        "id": ep_id,
        "title": title,
        "severity": severity,
        "detected_at": at.isoformat(),
        "services": services,
    }


@pytest.fixture(autouse=True)
def _no_docker(monkeypatch, tmp_path):
    """Keep tests deterministic: no real Docker, isolated AIOPS_DATA_DIR."""
    monkeypatch.setattr(topo_module, "_docker_health", lambda: {})
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))


# ── fallback topology ─────────────────────────────────────────────────────────

class TestFallbackTopology:

    @pytest.mark.asyncio
    async def test_fallback_when_neo4j_and_collector_absent(self):
        req = _make_request(neo4j_client=None, telemetry_collector=None)
        result = await get_topology(req, window_hours=168, buckets=28)

        assert result.stats.source == "fallback"
        assert result.window_hours == 168
        assert result.bucket_minutes == pytest.approx(360.0)

        expected_ids = {s["id"] for s in PLATFORM_SERVICES}
        assert {n.id for n in result.nodes} == expected_ids
        assert result.stats.nodes == len(PLATFORM_SERVICES)

        for node in result.nodes:
            assert node.health == "unknown"
            assert node.episode_count == 0
            assert node.incident_count == 0
            assert len(node.buckets) == 28
            assert sum(node.buckets) == 0
            assert node.recent_episodes == []
            assert node.kind in {"gateway", "frontend", "backend", "datastore",
                                 "observability", "llm"}

        assert result.stats.edges == len(PLATFORM_DEPENDENCIES)
        edge_pairs = {(e.source, e.target) for e in result.edges}
        assert edge_pairs == set(PLATFORM_DEPENDENCIES)
        for edge in result.edges:
            assert edge.relationship == "DEPENDS_ON"
            assert edge.kind == "static"
            assert edge.id == f"{edge.source}->{edge.target}"
            assert len(edge.buckets) == 28

    @pytest.mark.asyncio
    async def test_fallback_when_neo4j_raises(self):
        """A dead Neo4j must NEVER 5xx — it degrades to the seed constants."""
        broken = MagicMock()
        broken.session = MagicMock(side_effect=RuntimeError("connection refused"))
        req = _make_request(neo4j_client=broken, telemetry_collector=None)

        result = await get_topology(req, window_hours=24, buckets=12)

        assert result.stats.source == "fallback"
        assert {n.id for n in result.nodes} == {s["id"] for s in PLATFORM_SERVICES}
        assert all(len(n.buckets) == 12 for n in result.nodes)

    @pytest.mark.asyncio
    async def test_custom_bucket_count_respected(self):
        req = _make_request()
        result = await get_topology(req, window_hours=48, buckets=96)
        assert all(len(n.buckets) == 96 for n in result.nodes)
        assert all(len(e.buckets) == 96 for e in result.edges)
        assert result.bucket_minutes == pytest.approx(30.0)


# ── neo4j-sourced nodes + episode bucketing ──────────────────────────────────

class TestEpisodeBucketing:

    @pytest.mark.asyncio
    async def test_bucket_placement_and_sum_invariant(self):
        now = datetime.utcnow()
        episodes = [
            # just inside the window start -> bucket 0
            _episode_row("ep-old", "Old incident", "critical",
                         now - timedelta(hours=167, minutes=50), ["backend"]),
            # mid-window -> bucket 14 (168h / 28 buckets = 6h per bucket). Use
            # the CENTRE of bucket 14 (offset 87h => 14.5), not its 84h edge, so
            # the few ms between this `now` and the endpoint's `now` can't floor
            # it down to bucket 13.
            _episode_row("ep-mid", "Mid incident", "info",
                         now - timedelta(hours=81), ["backend"]),
            # most recent -> bucket 27; legacy numeric severity
            _episode_row("ep-new", "New incident", "10",
                         now - timedelta(minutes=1), ["backend"]),
        ]
        client = _FakeNeo4jClient([_NODE_ROWS, _DEP_ROWS, episodes])
        req = _make_request(neo4j_client=client)

        result = await get_topology(req, window_hours=168, buckets=28)

        assert result.stats.source == "neo4j"
        assert result.stats.episodes_in_window == 3
        backend = next(n for n in result.nodes if n.id == "backend")

        # Sum invariant + oldest→newest placement.
        assert backend.episode_count == 3
        assert sum(backend.buckets) == backend.episode_count
        assert backend.buckets[0] == 1
        assert backend.buckets[14] == 1
        assert backend.buckets[27] == 1

        # incident_count = error/critical ONLY ("10"→warning and info excluded).
        assert backend.incident_count == 1

        # neo4j node had no episodes.
        neo4j_node = next(n for n in result.nodes if n.id == "neo4j")
        assert neo4j_node.episode_count == 0
        assert sum(neo4j_node.buckets) == 0

    @pytest.mark.asyncio
    async def test_recent_episodes_cap_and_order(self):
        now = datetime.utcnow()
        episodes = [
            _episode_row(f"ep-{i}", f"Incident {i}", "warning",
                         now - timedelta(hours=i + 1), ["backend"])
            for i in range(7)
        ]
        client = _FakeNeo4jClient([_NODE_ROWS, _DEP_ROWS, episodes])
        req = _make_request(neo4j_client=client)

        result = await get_topology(req, window_hours=168, buckets=28)
        backend = next(n for n in result.nodes if n.id == "backend")

        assert backend.episode_count == 7
        assert len(backend.recent_episodes) == 5  # capped
        # Most recent first: ep-0 (1h ago) ... ep-4 (5h ago).
        assert [e.id for e in backend.recent_episodes] == [
            "ep-0", "ep-1", "ep-2", "ep-3", "ep-4"
        ]
        assert backend.last_episode_at is not None
        assert backend.last_episode_at == backend.recent_episodes[0].at

    @pytest.mark.asyncio
    async def test_severity_10_tolerance(self):
        """Legacy numeric severities map defensively into the closed set."""
        now = datetime.utcnow()
        episodes = [
            _episode_row("ep-legacy", "Legacy row", "10",
                         now - timedelta(hours=1), ["backend"]),
        ]
        client = _FakeNeo4jClient([_NODE_ROWS, _DEP_ROWS, episodes])
        req = _make_request(neo4j_client=client)

        result = await get_topology(req, window_hours=168, buckets=28)
        backend = next(n for n in result.nodes if n.id == "backend")

        assert backend.recent_episodes[0].severity == "warning"
        for node in result.nodes:
            for ep in node.recent_episodes:
                assert ep.severity in {"info", "warning", "error", "critical"}

    def test_map_severity_defensive(self):
        assert _map_severity("critical") == "critical"
        assert _map_severity("error") == "error"
        assert _map_severity("warning") == "warning"
        assert _map_severity("info") == "info"
        assert _map_severity("10") == "warning"       # legacy numeric
        assert _map_severity("high") == "error"
        assert _map_severity("medium") == "warning"
        assert _map_severity(None) == "warning"
        assert _map_severity("garbage") == "warning"

    @pytest.mark.asyncio
    async def test_co_episode_edge_buckets(self):
        now = datetime.utcnow()
        episodes = [
            # involves BOTH endpoints -> counts on the backend->neo4j edge
            _episode_row("ep-both", "Backend cannot reach neo4j", "error",
                         now - timedelta(minutes=5), ["backend", "neo4j"]),
            # involves only one endpoint -> NOT a co-episode
            _episode_row("ep-solo", "Backend latency", "warning",
                         now - timedelta(minutes=5), ["backend"]),
        ]
        client = _FakeNeo4jClient([_NODE_ROWS, _DEP_ROWS, episodes])
        req = _make_request(neo4j_client=client)

        result = await get_topology(req, window_hours=168, buckets=28)
        edge = next(e for e in result.edges if e.id == "backend->neo4j")

        assert edge.co_episode_count == 1
        assert sum(edge.buckets) == 1
        assert edge.buckets[27] == 1


# ── prometheus health + edge hosts ───────────────────────────────────────────

class TestHealthAndEdgeHosts:

    @pytest.mark.asyncio
    async def test_prometheus_up_health_mapping(self):
        collector = _make_collector({
            "up": [
                {"metric": {"job": "aiops-backend"}, "value": [1700000000, "1"]},
                {"metric": {"job": "neo4j"}, "value": [1700000000, "0"]},
            ],
            "count by (edge) (up)": [],
        })
        req = _make_request(telemetry_collector=collector)

        result = await get_topology(req, window_hours=168, buckets=28)

        backend = next(n for n in result.nodes if n.id == "backend")
        neo4j_node = next(n for n in result.nodes if n.id == "neo4j")
        frontend = next(n for n in result.nodes if n.id == "frontend")

        assert backend.health == "healthy"
        assert "up=1" in backend.health_reason
        assert neo4j_node.health == "critical"
        assert "up=0" in neo4j_node.health_reason
        # No signal at all -> unknown.
        assert frontend.health == "unknown"

    @pytest.mark.asyncio
    async def test_escalation_bumps_healthy_to_warning(self):
        now = datetime.utcnow()
        episodes = [
            _episode_row("ep-err", "Recent backend error", "error",
                         now - timedelta(hours=1), ["backend"]),
        ]
        client = _FakeNeo4jClient([_NODE_ROWS, _DEP_ROWS, episodes])
        collector = _make_collector({
            "up": [{"metric": {"job": "aiops-backend"}, "value": [1700000000, "1"]}],
            "count by (edge) (up)": [],
        })
        req = _make_request(neo4j_client=client, telemetry_collector=collector)

        result = await get_topology(req, window_hours=168, buckets=28)
        backend = next(n for n in result.nodes if n.id == "backend")

        assert backend.health == "warning"
        assert "episode" in backend.health_reason.lower()

    @pytest.mark.asyncio
    async def test_edge_host_discovery_creates_node_and_telemetry_edges(self):
        collector = _make_collector({
            "count by (edge) (up)": [
                {"metric": {"edge": "nextcloud-host"}, "value": [1700000000, "2"]},
            ],
            "up": [],
        })
        req = _make_request(telemetry_collector=collector)

        result = await get_topology(req, window_hours=168, buckets=28)

        edge_node = next(n for n in result.nodes if n.id == "edge:nextcloud-host")
        assert edge_node.kind == "edge-host"
        assert edge_node.label == "nextcloud-host"
        assert edge_node.meta.edge_label == "nextcloud-host"
        assert edge_node.health == "healthy"
        max_platform_tier = max(s["tier"] for s in PLATFORM_SERVICES)
        assert edge_node.tier == max_platform_tier + 1
        assert len(edge_node.buckets) == 28

        ships = [e for e in result.edges if e.relationship == "SHIPS_TELEMETRY"]
        assert {(e.source, e.target) for e in ships} == {
            ("edge:nextcloud-host", "loki"),
            ("edge:nextcloud-host", "prometheus"),
        }
        for e in ships:
            assert e.kind == "dynamic"
            assert len(e.buckets) == 28

    @pytest.mark.asyncio
    async def test_edge_host_zero_targets_is_unknown(self):
        collector = _make_collector({
            "count by (edge) (up)": [
                {"metric": {"edge": "dead-host"}, "value": [1700000000, "0"]},
            ],
            "up": [],
        })
        req = _make_request(telemetry_collector=collector)

        result = await get_topology(req, window_hours=168, buckets=28)
        edge_node = next(n for n in result.nodes if n.id == "edge:dead-host")
        assert edge_node.health == "unknown"

    @pytest.mark.asyncio
    async def test_dismissed_edge_hosts_are_hidden(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
        (tmp_path / "dismissed_hosts.json").write_text(
            '{"dismissed": ["stale-host"]}', encoding="utf-8"
        )
        collector = _make_collector({
            "count by (edge) (up)": [
                {"metric": {"edge": "stale-host"}, "value": [1700000000, "1"]},
                {"metric": {"edge": "live-host"}, "value": [1700000000, "1"]},
            ],
            "up": [],
        })
        req = _make_request(telemetry_collector=collector)

        result = await get_topology(req, window_hours=168, buckets=28)
        ids = {n.id for n in result.nodes}
        assert "edge:live-host" in ids
        assert "edge:stale-host" not in ids


# ── seeder ────────────────────────────────────────────────────────────────────

class TestSeedTopology:

    @pytest.mark.asyncio
    async def test_seed_endpoint_503_without_neo4j(self):
        from fastapi import HTTPException

        req = _make_request(neo4j_client=None)
        with pytest.raises(HTTPException) as exc:
            await seed_topology(req)
        assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_seed_is_idempotent_merge_never_deletes(self):
        client = _FakeNeo4jClient([[], []])
        counts = await seed_service_topology(client)

        assert counts == {
            "services": len(PLATFORM_SERVICES),
            "dependencies": len(PLATFORM_DEPENDENCIES),
        }
        assert len(client.queries) == 2
        all_cypher = " ".join(q for q, _ in client.queries).upper()
        assert "MERGE" in all_cypher
        assert "DELETE" not in all_cypher
        assert "DETACH" not in all_cypher
        # The seeder MUST set kind and tier — the topology endpoint and the
        # frontend layout depend on these properties.
        assert "S.KIND" in all_cypher
        assert "S.TIER" in all_cypher

    @pytest.mark.asyncio
    async def test_seed_endpoint_reports_counts(self):
        client = _FakeNeo4jClient([[], []])
        req = _make_request(neo4j_client=client)

        result = await seed_topology(req)
        assert result.success is True
        assert result.services == len(PLATFORM_SERVICES)
        assert result.dependencies == len(PLATFORM_DEPENDENCIES)

    def test_platform_constants_shape(self):
        """The lane contract: 12 services, required keys, valid kinds."""
        assert len(PLATFORM_SERVICES) == 12
        ids = {s["id"] for s in PLATFORM_SERVICES}
        assert ids == {
            "caddy", "frontend", "backend", "grafana", "neo4j", "loki",
            "prometheus", "tempo", "promtail", "otel-collector",
            "qwen3-4b", "qwen3-14b",
        }
        for svc in PLATFORM_SERVICES:
            assert set(svc) == {"id", "label", "kind", "tier", "port", "description"}
            assert svc["kind"] in {"gateway", "frontend", "backend", "datastore",
                                   "observability", "llm"}
            assert isinstance(svc["tier"], int)
        for source, target in PLATFORM_DEPENDENCIES:
            assert source in ids and target in ids
