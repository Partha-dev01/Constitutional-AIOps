"""Unit tests for the deterministic onboarding generators.

Pure functions, no app / network. The critical guarantee is that
``build_topology_from_services`` always produces something
``validate_topology_schema`` accepts, so a generated schema is byte-shape-
identical to a hand-edited / Applied one.
"""

from src.onboarding.generators import (
    build_base_prompt,
    build_topology_from_services,
    infer_kind,
)
from src.topology.schema import (
    ALLOWED_NODE_KINDS,
    MAX_NODES,
    validate_topology_schema,
)


# ── infer_kind ─────────────────────────────────────────────────────────────

def test_infer_kind_explicit_role_wins():
    assert infer_kind("whatever", "datastore") == "datastore"


def test_infer_kind_keyword_heuristics():
    assert infer_kind("Caddy reverse proxy") == "gateway"
    assert infer_kind("Postgres primary") == "datastore"
    assert infer_kind("Grafana") == "observability"
    assert infer_kind("vLLM inference server") == "llm"
    assert infer_kind("React dashboard") == "frontend"
    assert infer_kind("Edge sensor node") == "edge"


def test_infer_kind_defaults_to_backend():
    assert infer_kind("orders-service") == "backend"


def test_infer_kind_word_boundary_avoids_false_positive():
    # "sandbox" contains the substring "db" but is not a datastore.
    assert infer_kind("sandbox runner") == "backend"


def test_infer_kind_only_returns_allowed_kinds():
    for name in ["x", "cache", "ui", "gateway", "model server", "iot device"]:
        assert infer_kind(name) in ALLOWED_NODE_KINDS


# ── build_topology_from_services ───────────────────────────────────────────

def _services():
    return [
        {"name": "Caddy", "role": "gateway", "dependsOn": ["Frontend", "Backend"]},
        {"name": "Frontend", "role": "frontend", "dependsOn": ["Backend"]},
        {"name": "Backend", "role": "backend", "dependsOn": ["Postgres", "Redis"]},
        {"name": "Postgres", "role": "datastore"},
        {"name": "Redis", "role": "datastore"},
    ]


def test_build_topology_is_valid_schema():
    raw = build_topology_from_services(_services())
    schema = validate_topology_schema(raw)  # must not raise
    assert len(schema.nodes) == 5
    ids = {n.id for n in schema.nodes}
    assert ids == {"caddy", "frontend", "backend", "postgres", "redis"}
    # Every declared dependency became an edge to a known node.
    edge_pairs = {(e.source, e.target) for e in schema.edges}
    assert ("caddy", "backend") in edge_pairs
    assert ("backend", "postgres") in edge_pairs


def test_build_topology_drops_unknown_and_self_deps():
    raw = build_topology_from_services(
        [
            {"name": "api", "dependsOn": ["api", "ghost"]},  # self + unknown
            {"name": "db", "role": "datastore"},
        ]
    )
    schema = validate_topology_schema(raw)
    assert len(schema.nodes) == 2
    assert schema.edges == []  # self-edge and unknown target both dropped


def test_build_topology_dedupes_ids():
    raw = build_topology_from_services(
        [{"name": "Order Service"}, {"name": "order-service"}]
    )
    schema = validate_topology_schema(raw)
    ids = [n.id for n in schema.nodes]
    assert len(ids) == len(set(ids)) == 2


def test_build_topology_clamps_tier_and_port():
    raw = build_topology_from_services(
        [{"name": "svc", "tier": 999, "port": "8080"}]
    )
    node = raw["nodes"][0]
    assert node["tier"] == 20  # clamped to the schema max
    assert node["port"] == 8080  # digit-string coerced


def test_build_topology_caps_node_count():
    many = [{"name": f"svc-{i}"} for i in range(MAX_NODES + 10)]
    raw = build_topology_from_services(many)
    assert len(raw["nodes"]) == MAX_NODES
    validate_topology_schema(raw)  # still valid


def test_build_topology_skips_nameless_and_nondict():
    raw = build_topology_from_services(
        [{"name": ""}, "not-a-dict", {"role": "backend"}, {"name": "ok"}]  # type: ignore[list-item]
    )
    schema = validate_topology_schema(raw)
    assert [n.id for n in schema.nodes] == ["ok"]


# ── build_base_prompt ──────────────────────────────────────────────────────

def test_build_base_prompt_from_topology():
    raw = build_topology_from_services(_services())
    prompt = build_base_prompt(_services(), raw)
    assert 10 <= len(prompt) <= 10000
    assert "PLATFORM SERVICES:" in prompt
    assert "Caddy" in prompt and "Postgres" in prompt
    assert "SERVICE DEPENDENCIES:" in prompt
    assert "Constitutional AI approval" in prompt


def test_build_base_prompt_survives_empty_topology():
    prompt = build_base_prompt([], {"nodes": [], "edges": []})
    assert len(prompt) >= 10


def test_build_base_prompt_falls_back_to_services_without_topology():
    prompt = build_base_prompt(
        [{"name": "Billing", "role": "backend"}], {"nodes": [], "edges": []}
    )
    assert "Billing" in prompt
