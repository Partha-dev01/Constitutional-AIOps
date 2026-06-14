"""
Tests for the editable platform-topology schema backend.

Covers:
  * the strict schema model + validator guardrails (unique ids, edge-endpoint
    existence, allowed kind/relationship sets, size caps, default fill, blank
    rejection, sanitisation of malformed input);
  * the GET / PUT / generate / reset endpoints (Preview + Apply, with fallback);
  * persistence round-trip + mode flag under an isolated AIOPS_DATA_DIR;
  * the live GET /api/v1/graph/topology honouring an applied custom schema while
    keeping the FROZEN payload shape (and failing soft to discovered).

Pattern: direct route-fn calls with SimpleNamespace mock requests (NEVER import
src.main — langgraph is not installed in CI). Each test isolates AIOPS_DATA_DIR
to a tmp dir so the SQLite topology_state table is fresh.
"""

import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.memory.topology_seed import PLATFORM_DEPENDENCIES, PLATFORM_SERVICES
from src.topology.schema import (
    ALLOWED_NODE_KINDS,
    MAX_EDGES,
    MAX_NODES,
    SchemaValidationError,
    clamp_raw_schema,
    discovered_schema_from_seed,
    validate_topology_schema,
)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path, monkeypatch):
    """Reload the persistence store with AIOPS_DATA_DIR pointed at a temp dir."""
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    import src.persistence.store as mod
    mod = importlib.reload(mod)
    mod.init_db()
    return mod


@pytest.fixture
def topo_routes(store, monkeypatch):
    """Reload the topology route module so its `persistence_store` reference is
    the freshly reloaded, tmp-dir-bound store."""
    import src.api.routes.topology as mod
    mod = importlib.reload(mod)
    monkeypatch.setattr(mod, "persistence_store", store)
    return mod


def _mock_router(content: str):
    """A model router whose reasoning_completion returns the given content."""
    router = MagicMock()
    router.reasoning_completion = AsyncMock(return_value={
        "choices": [{"message": {"content": content}}]
    })
    return router


def _request(model_router=None):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(model_router=model_router)))


_GOOD_SCHEMA = {
    "nodes": [
        {"id": "caddy", "label": "Caddy", "kind": "gateway", "tier": 0, "port": 443},
        {"id": "backend", "label": "Backend", "kind": "backend", "tier": 1, "port": 8000},
    ],
    "edges": [
        {"source": "caddy", "target": "backend", "relationship": "DEPENDS_ON", "kind": "static"},
    ],
}


# ── schema model / validator ──────────────────────────────────────────────────

class TestValidator:

    def test_valid_schema_passes_and_fills_label(self):
        schema = validate_topology_schema({
            "nodes": [{"id": "x", "kind": "backend"}],
            "edges": [],
        })
        assert len(schema.nodes) == 1
        # Blank label auto-filled from id.
        assert schema.nodes[0].label == "x"
        assert schema.nodes[0].tier == 1  # default

    def test_empty_schema_rejected(self):
        with pytest.raises(SchemaValidationError) as exc:
            validate_topology_schema({"nodes": [], "edges": []})
        assert any("at least one node" in e for e in exc.value.errors)

    def test_duplicate_node_ids_rejected(self):
        with pytest.raises(SchemaValidationError) as exc:
            validate_topology_schema({
                "nodes": [
                    {"id": "a", "kind": "backend"},
                    {"id": "a", "kind": "frontend"},
                ],
                "edges": [],
            })
        assert any("duplicate node id" in e for e in exc.value.errors)

    def test_invalid_kind_rejected(self):
        with pytest.raises(SchemaValidationError) as exc:
            validate_topology_schema({
                "nodes": [{"id": "a", "kind": "wormhole"}],
                "edges": [],
            })
        assert any("invalid kind" in e for e in exc.value.errors)

    def test_edge_to_unknown_node_rejected(self):
        with pytest.raises(SchemaValidationError) as exc:
            validate_topology_schema({
                "nodes": [{"id": "a", "kind": "backend"}],
                "edges": [{"source": "a", "target": "ghost"}],
            })
        assert any("unknown node 'ghost'" in e for e in exc.value.errors)

    def test_bad_edge_relationship_rejected(self):
        with pytest.raises(SchemaValidationError) as exc:
            validate_topology_schema({
                "nodes": [
                    {"id": "a", "kind": "backend"},
                    {"id": "b", "kind": "datastore"},
                ],
                "edges": [{"source": "a", "target": "b", "relationship": "LOVES"}],
            })
        assert any("invalid relationship" in e for e in exc.value.errors)

    def test_too_many_nodes_rejected(self):
        nodes = [{"id": f"n{i}", "kind": "backend"} for i in range(MAX_NODES + 5)]
        with pytest.raises(SchemaValidationError) as exc:
            validate_topology_schema({"nodes": nodes, "edges": []})
        # clamp truncates to MAX_NODES, so the surfaced error is structural, not
        # the size check — but it must still REJECT (never silently accept >cap).
        assert exc.value.errors

    def test_clamp_drops_unknown_keys_and_truncates(self):
        # Unknown keys (incl. runtime-only fields) are stripped; a non-list
        # edges value becomes []. Huge lists are truncated to the DoS ceiling
        # (MAX_NODES * 4), well above the cap so modest overages still reject.
        clamped = clamp_raw_schema({
            "nodes": [{"id": "a", "kind": "backend", "evil": "x", "health": "critical"}]
                     + [{"id": f"n{i}", "kind": "backend"} for i in range(MAX_NODES * 8)],
            "edges": "not-a-list",
        })
        assert len(clamped["nodes"]) == MAX_NODES * 4
        assert "evil" not in clamped["nodes"][0]
        assert "health" not in clamped["nodes"][0]
        assert clamped["edges"] == []

    def test_clamp_non_dict_input_is_safe(self):
        assert clamp_raw_schema("garbage") == {"nodes": [], "edges": []}
        assert clamp_raw_schema(None) == {"nodes": [], "edges": []}
        assert clamp_raw_schema([1, 2, 3]) == {"nodes": [], "edges": []}

    def test_defaults_applied_to_edges(self):
        schema = validate_topology_schema({
            "nodes": [
                {"id": "a", "kind": "backend"},
                {"id": "b", "kind": "datastore"},
            ],
            "edges": [{"source": "a", "target": "b"}],
        })
        assert schema.edges[0].relationship == "DEPENDS_ON"
        assert schema.edges[0].kind == "static"

    def test_discovered_schema_matches_seed(self):
        schema = discovered_schema_from_seed()
        assert {n.id for n in schema.nodes} == {s["id"] for s in PLATFORM_SERVICES}
        assert len(schema.edges) == len(PLATFORM_DEPENDENCIES)
        for node in schema.nodes:
            assert node.kind in ALLOWED_NODE_KINDS
        # The discovered seed must itself be strictly valid.
        validate_topology_schema({
            "nodes": [n.model_dump() for n in schema.nodes],
            "edges": [e.model_dump() for e in schema.edges],
        })


# ── persistence ───────────────────────────────────────────────────────────────

class TestPersistence:

    def test_default_mode_is_discovered(self, store):
        assert store.get_topology_mode() == store.TOPOLOGY_MODE_DISCOVERED
        assert store.load_topology_schema() is None

    def test_save_sets_custom_mode_and_round_trips(self, store):
        store.save_topology_schema(_GOOD_SCHEMA)
        assert store.get_topology_mode() == store.TOPOLOGY_MODE_CUSTOM
        assert store.load_topology_schema() == _GOOD_SCHEMA

    def test_reset_reverts_to_discovered(self, store):
        store.save_topology_schema(_GOOD_SCHEMA)
        store.reset_topology_mode()
        assert store.get_topology_mode() == store.TOPOLOGY_MODE_DISCOVERED
        assert store.load_topology_schema() is None

    def test_custom_mode_without_schema_falls_back(self, store):
        # Mode says custom but no schema persisted -> never report custom.
        store.save_topology_schema(_GOOD_SCHEMA)
        # Drop only the schema row, leave mode.
        with store._connect() as conn:  # type: ignore[attr-defined]
            conn.execute("DELETE FROM topology_state WHERE key = ?", ("custom_schema",))
            conn.commit()
        assert store.get_topology_mode() == store.TOPOLOGY_MODE_DISCOVERED


# ── GET / PUT / reset endpoints ───────────────────────────────────────────────

class TestSchemaEndpoints:

    @pytest.mark.asyncio
    async def test_get_returns_discovered_when_unset(self, topo_routes):
        result = await topo_routes.get_topology_schema()
        assert result.mode == "discovered"
        assert {n["id"] for n in result.nodes} == {s["id"] for s in PLATFORM_SERVICES}

    @pytest.mark.asyncio
    async def test_put_applies_and_persists(self, topo_routes, store):
        body = topo_routes.TopologySchemaUpdate(**_GOOD_SCHEMA)
        result = await topo_routes.put_topology_schema(body)
        assert result.mode == "custom"
        assert {n["id"] for n in result.nodes} == {"caddy", "backend"}
        assert store.get_topology_mode() == "custom"

        # GET now returns the custom schema.
        got = await topo_routes.get_topology_schema()
        assert got.mode == "custom"
        assert {n["id"] for n in got.nodes} == {"caddy", "backend"}

    @pytest.mark.asyncio
    async def test_put_invalid_is_422_and_not_persisted(self, topo_routes, store):
        bad = topo_routes.TopologySchemaUpdate(
            nodes=[{"id": "a", "kind": "not-a-kind"}], edges=[]
        )
        with pytest.raises(HTTPException) as exc:
            await topo_routes.put_topology_schema(bad)
        assert exc.value.status_code == 422
        assert "errors" in exc.value.detail
        # Nothing half-written.
        assert store.get_topology_mode() == "discovered"
        assert store.load_topology_schema() is None

    @pytest.mark.asyncio
    async def test_reset_reverts_to_discovered(self, topo_routes, store):
        await topo_routes.put_topology_schema(topo_routes.TopologySchemaUpdate(**_GOOD_SCHEMA))
        result = await topo_routes.reset_topology_schema()
        assert result.mode == "discovered"
        assert store.get_topology_mode() == "discovered"
        assert {n["id"] for n in result.nodes} == {s["id"] for s in PLATFORM_SERVICES}


# ── LLM generate (Preview, never persists) ────────────────────────────────────

class TestGenerate:

    @pytest.mark.asyncio
    async def test_generate_returns_validated_preview(self, topo_routes, store):
        import json

        router = _mock_router(json.dumps(_GOOD_SCHEMA))
        req = _request(model_router=router)
        result = await topo_routes.generate_topology_schema(
            req, topo_routes.GenerateSchemaRequest(prompt="add a gateway and backend")
        )
        assert result.preview is True
        assert {n["id"] for n in result.nodes} == {"caddy", "backend"}
        # PREVIEW only — generation must NOT persist or flip mode.
        assert store.get_topology_mode() == "discovered"
        assert store.load_topology_schema() is None

    @pytest.mark.asyncio
    async def test_generate_strips_fences_and_think_tags(self, topo_routes):
        import json

        content = f"<think>planning...</think>\n```json\n{json.dumps(_GOOD_SCHEMA)}\n```"
        router = _mock_router(content)
        req = _request(model_router=router)
        result = await topo_routes.generate_topology_schema(
            req, topo_routes.GenerateSchemaRequest(prompt="x")
        )
        assert {n["id"] for n in result.nodes} == {"caddy", "backend"}

    @pytest.mark.asyncio
    async def test_generate_retries_once_then_succeeds(self, topo_routes):
        import json

        router = MagicMock()
        router.reasoning_completion = AsyncMock(side_effect=[
            {"choices": [{"message": {"content": "not json at all"}}]},
            {"choices": [{"message": {"content": json.dumps(_GOOD_SCHEMA)}}]},
        ])
        req = _request(model_router=router)
        result = await topo_routes.generate_topology_schema(
            req, topo_routes.GenerateSchemaRequest(prompt="x")
        )
        assert {n["id"] for n in result.nodes} == {"caddy", "backend"}
        assert router.reasoning_completion.await_count == 2
        assert "retry" in result.note.lower()

    @pytest.mark.asyncio
    async def test_generate_invalid_twice_is_422(self, topo_routes, store):
        router = MagicMock()
        router.reasoning_completion = AsyncMock(
            return_value={"choices": [{"message": {"content": "garbage"}}]}
        )
        req = _request(model_router=router)
        with pytest.raises(HTTPException) as exc:
            await topo_routes.generate_topology_schema(
                req, topo_routes.GenerateSchemaRequest(prompt="x")
            )
        assert exc.value.status_code == 422
        assert "errors" in exc.value.detail
        assert router.reasoning_completion.await_count == 2
        # Nothing persisted on failure.
        assert store.get_topology_mode() == "discovered"

    @pytest.mark.asyncio
    async def test_generate_invalid_kind_from_llm_rejected(self, topo_routes):
        import json

        bad = {"nodes": [{"id": "a", "kind": "starship"}], "edges": []}
        router = _mock_router(json.dumps(bad))
        req = _request(model_router=router)
        with pytest.raises(HTTPException) as exc:
            await topo_routes.generate_topology_schema(
                req, topo_routes.GenerateSchemaRequest(prompt="x")
            )
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_503_without_router(self, topo_routes):
        req = _request(model_router=None)
        with pytest.raises(HTTPException) as exc:
            await topo_routes.generate_topology_schema(
                req, topo_routes.GenerateSchemaRequest(prompt="x")
            )
        assert exc.value.status_code == 503


# ── live topology endpoint honours the custom schema ──────────────────────────

class TestLiveTopologyHonoursCustom:

    @pytest.mark.asyncio
    async def test_custom_schema_served_with_frozen_shape(self, store, monkeypatch):
        import src.api.routes.graph_topology as gt

        monkeypatch.setattr(gt, "_docker_health", lambda: {})
        # Point graph_topology's lazily-imported store at the tmp-dir store.
        monkeypatch.setattr("src.persistence.store.get_topology_mode", store.get_topology_mode)
        monkeypatch.setattr("src.persistence.store.load_topology_schema", store.load_topology_schema)

        store.save_topology_schema(_GOOD_SCHEMA)

        req = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
            neo4j_client=None, telemetry_collector=None,
        )))
        result = await gt.get_topology(req, window_hours=168, buckets=28)

        assert result.stats.source == "custom"
        assert {n.id for n in result.nodes} == {"caddy", "backend"}
        # Frozen shape invariants preserved.
        for node in result.nodes:
            assert len(node.buckets) == 28
            assert sum(node.buckets) == node.episode_count == 0
            assert node.recent_episodes == []
            assert node.health in {"healthy", "warning", "critical", "unknown"}
        edge = next(e for e in result.edges if e.id == "caddy->backend")
        assert edge.relationship == "DEPENDS_ON"
        assert edge.kind == "static"
        assert len(edge.buckets) == 28

    @pytest.mark.asyncio
    async def test_discovered_mode_unchanged(self, store, monkeypatch):
        import src.api.routes.graph_topology as gt

        monkeypatch.setattr(gt, "_docker_health", lambda: {})
        monkeypatch.setattr("src.persistence.store.get_topology_mode", store.get_topology_mode)
        monkeypatch.setattr("src.persistence.store.load_topology_schema", store.load_topology_schema)

        # No custom schema applied -> discovered fallback, source != "custom".
        req = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
            neo4j_client=None, telemetry_collector=None,
        )))
        result = await gt.get_topology(req, window_hours=168, buckets=28)
        assert result.stats.source == "fallback"
        assert {n.id for n in result.nodes} == {s["id"] for s in PLATFORM_SERVICES}

    @pytest.mark.asyncio
    async def test_render_custom_overlays_prom_health(self, store):
        import src.api.routes.graph_topology as gt

        schema = validate_topology_schema(_GOOD_SCHEMA)
        result = gt.render_custom_topology(
            schema,
            window_hours=168,
            buckets=28,
            prom_health={"backend": {"up": True, "job": "aiops-backend"}},
            docker_health={},
        )
        backend = next(n for n in result.nodes if n.id == "backend")
        caddy = next(n for n in result.nodes if n.id == "caddy")
        assert backend.health == "healthy"
        assert "up=1" in backend.health_reason
        assert caddy.health == "unknown"  # no signal
