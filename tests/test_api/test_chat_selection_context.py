"""
Session-14 — Graph "Schema mode" selection-context rendering for chat.

ChatRequest.context used to be a dead field; these tests pin the rendering +
caps + single-service extraction that ground the "Ask AI about this selection"
flow. Pure-function tests (no langgraph / no src.main import).
"""

from src.api.routes.chat import (
    _render_selection_context,
    _selected_known_service,
    _SELECTION_MAX_CHARS,
)


def _selection(nodes=None, edges=None, source="schema-graph"):
    return {
        "source": source,
        "window_hours": 168,
        "selection": {"nodes": nodes or [], "edges": edges or []},
    }


def test_non_schema_context_renders_nothing():
    assert _render_selection_context(None) == ""
    assert _render_selection_context({"source": "other", "foo": 1}) == ""
    assert _render_selection_context(_selection(source="legacy")) == ""
    assert _render_selection_context(_selection()) == ""  # empty selection


def test_renders_nodes_and_edges_with_header():
    ctx = _selection(
        nodes=[
            {
                "id": "backend",
                "label": "Backend (FastAPI)",
                "kind": "backend",
                "health": "warning",
                "episode_count": 5,
                "incident_count": 2,
                "recent": [
                    {"title": "Neo4j pool exhausted", "severity": "error"},
                    {"title": "Slow query", "severity": "warning"},
                ],
            }
        ],
        edges=[
            {
                "source": "backend",
                "target": "neo4j",
                "relationship": "DEPENDS_ON",
                "co_episode_count": 2,
            }
        ],
    )
    out = _render_selection_context(ctx)
    assert out.startswith("## User Selection")
    assert "Backend (FastAPI)" in out
    assert "5 episodes" in out and "2 incidents" in out
    assert "Neo4j pool exhausted" in out
    assert "backend → neo4j" in out
    assert "2 correlated episodes" in out


def test_recent_titles_capped_at_two_and_truncated():
    long = "x" * 200
    ctx = _selection(
        nodes=[
            {
                "id": "loki",
                "label": "Loki",
                "kind": "observability",
                "health": "healthy",
                "episode_count": 9,
                "incident_count": 0,
                "recent": [
                    {"title": long, "severity": "info"},
                    {"title": "second", "severity": "info"},
                    {"title": "third should not appear", "severity": "info"},
                ],
            }
        ]
    )
    out = _render_selection_context(ctx)
    assert "third should not appear" not in out  # only 2 shown
    assert "x" * 200 not in out                   # title truncated to 80


def test_item_cap_and_overflow_note():
    nodes = [
        {
            "id": f"svc{i}",
            "label": f"svc{i}",
            "kind": "service",
            "health": "healthy",
            "episode_count": 0,
            "incident_count": 0,
        }
        for i in range(12)
    ]
    out = _render_selection_context(_selection(nodes=nodes))
    assert "and 4 more selected element(s)" in out  # 12 nodes, 8 shown


def test_hard_char_cap_enforced():
    nodes = [
        {
            "id": f"svc{i}",
            "label": "L" * 100,
            "kind": "service",
            "health": "healthy",
            "episode_count": 1,
            "incident_count": 0,
            "recent": [{"title": "T" * 80, "severity": "error"}],
        }
        for i in range(8)
    ]
    out = _render_selection_context(_selection(nodes=nodes))
    assert len(out) <= _SELECTION_MAX_CHARS + len("\n- …(truncated)")
    assert out.rstrip().endswith("(truncated)")


def test_selected_known_service_single_vs_ambiguous():
    one = _selection(nodes=[{"id": "nextcloud"}, {"id": "edge:host"}])
    assert _selected_known_service(one) == "nextcloud"

    two = _selection(nodes=[{"id": "nextcloud"}, {"id": "loki"}])
    assert _selected_known_service(two) is None  # ambiguous → None

    none = _selection(nodes=[{"id": "edge:host"}])
    assert _selected_known_service(none) is None

    assert _selected_known_service({"source": "other"}) is None
