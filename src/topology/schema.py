"""
Constitutional AIOps - Strict editable topology schema.

This is the guardrail that lets an operator (or the 14B reasoning model) supply
a *custom* platform topology WITHOUT ever being able to break the live schema
graph. The model is a strict superset-free mirror of the FROZEN
``TopologyNode`` / ``TopologyEdge`` contract from
``src/api/routes/graph_topology.py`` (and ``frontend/src/components/schema/types.ts``):

    node = {id, label, kind, tier, port?, description?}
    edge = {source, target, relationship, kind}

The remaining contract fields (``health``, ``buckets``, ``episode_count``,
``recent_episodes`` …) are runtime-derived and are filled with safe defaults
when a custom schema is rendered — an editor never supplies them, so we never
let an operator hand-craft a "blank" or broken health/bucket payload.

Validation guarantees (``validate_topology_schema``):
  * at least one node;
  * node ids unique and non-empty;
  * every node ``kind`` is in :data:`ALLOWED_NODE_KINDS`;
  * every edge endpoint references an existing node id;
  * edge ``relationship`` ∈ :data:`ALLOWED_RELATIONSHIPS`,
    edge ``kind`` ∈ :data:`ALLOWED_EDGE_KINDS`;
  * bounded sizes — ≤ :data:`MAX_NODES` nodes, ≤ :data:`MAX_EDGES` edges;
  * sane defaults auto-filled (label defaults to id, tier clamped ≥ 0,
    edge relationship/kind defaulted from the dependency convention).

A malformed schema raises :class:`SchemaValidationError`, which carries a
structured ``errors`` list the route turns into a clean 422 — the "handhold so
the schema doesn't break" guardrail.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

# ---------------------------------------------------------------------------
# Allowed value sets (derived from the frozen contract + topology_seed)
# ---------------------------------------------------------------------------

# Service ``kind`` values. The platform set is the 6 kinds emitted by the seed
# (see ``src/memory/topology_seed.py`` + the types.ts doc-comment on
# ``TopologyNode.kind``: "gateway | frontend | backend | datastore |
# observability | llm | edge"). ``edge`` / ``edge-host`` cover the dynamically
# discovered remote hosts the live endpoint pins to the deepest tier; we accept
# both spellings so a generated/edited schema can include them.
ALLOWED_NODE_KINDS: frozenset[str] = frozenset(
    {
        "gateway",
        "frontend",
        "backend",
        "datastore",
        "observability",
        "llm",
        "edge",
        "edge-host",
    }
)

# Edge ``relationship`` values (TopologyEdge.relationship: "DEPENDS_ON" |
# "SHIPS_TELEMETRY").
ALLOWED_RELATIONSHIPS: frozenset[str] = frozenset({"DEPENDS_ON", "SHIPS_TELEMETRY"})

# Edge ``kind`` values (TopologyEdge.kind: "static" | "dynamic").
ALLOWED_EDGE_KINDS: frozenset[str] = frozenset({"static", "dynamic"})

# Bounded sizes — a custom schema is a hand/LLM-authored architecture diagram,
# not a live graph, so these caps keep it small enough to always render cleanly
# and cheap to validate/persist.
MAX_NODES: int = 40
MAX_EDGES: int = 80

# Field-length caps so a single oversized string can't bloat the persisted doc.
_MAX_ID_LEN = 128
_MAX_LABEL_LEN = 128
_MAX_DESCRIPTION_LEN = 1024


class SchemaValidationError(Exception):
    """Raised when a candidate topology schema fails strict validation.

    ``errors`` is a list of human-readable, structured problem strings so the
    route can return a clean 422 the editor UI can show inline — the operator
    always learns *why* a schema was rejected.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors) if errors else "invalid topology schema")


# ---------------------------------------------------------------------------
# Editable schema models (the EDITABLE subset of the frozen contract)
# ---------------------------------------------------------------------------

class SchemaNode(BaseModel):
    """One editable platform-service node.

    Mirrors the editable subset of the frozen ``TopologyNode``. Runtime-derived
    fields (health, buckets, episode counts …) are intentionally absent here:
    they are filled with safe defaults at render time, so an editor can never
    author a broken health/bucket payload.
    """

    id: str = Field(..., min_length=1, max_length=_MAX_ID_LEN)
    label: str = Field("", max_length=_MAX_LABEL_LEN)
    kind: str = Field(..., description="One of ALLOWED_NODE_KINDS")
    tier: int = Field(1, ge=0, le=20)
    port: int | None = Field(None, ge=0, le=65535)
    description: str | None = Field(None, max_length=_MAX_DESCRIPTION_LEN)

    @field_validator("id", "kind", mode="before")
    @classmethod
    def _strip_required(cls, v: Any) -> Any:
        """Trim surrounding whitespace on the required string fields."""
        return v.strip() if isinstance(v, str) else v

    @field_validator("label", mode="before")
    @classmethod
    def _label_default(cls, v: Any) -> Any:
        """Coerce a None/blank label to an empty string (id-default applied later)."""
        if v is None:
            return ""
        return v.strip() if isinstance(v, str) else v


class SchemaEdge(BaseModel):
    """One editable dependency / telemetry link.

    Mirrors the editable subset of the frozen ``TopologyEdge``. The runtime
    ``id`` ("source->target"), ``co_episode_count`` and ``buckets`` are derived
    at render time, not authored here.
    """

    source: str = Field(..., min_length=1, max_length=_MAX_ID_LEN)
    target: str = Field(..., min_length=1, max_length=_MAX_ID_LEN)
    relationship: str = Field("DEPENDS_ON", description="One of ALLOWED_RELATIONSHIPS")
    kind: str = Field("static", description="One of ALLOWED_EDGE_KINDS")

    @field_validator("source", "target", "relationship", "kind", mode="before")
    @classmethod
    def _strip(cls, v: Any) -> Any:
        return v.strip() if isinstance(v, str) else v


class TopologySchema(BaseModel):
    """A complete editable platform topology (the persisted custom document)."""

    nodes: list[SchemaNode] = Field(default_factory=list)
    edges: list[SchemaEdge] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Sanitisation + strict validation
# ---------------------------------------------------------------------------

def clamp_raw_schema(raw: Any) -> dict[str, list[dict[str, Any]]]:
    """Best-effort sanitise/clamp arbitrary (LLM or client) input into the
    ``{"nodes": [...], "edges": [...]}`` shape BEFORE pydantic validation.

    This is the "sanitize/clamp parsed output before validation" guardrail: it
    never raises — it coerces a wide variety of malformed shapes into something
    pydantic can either accept or reject cleanly:
      * a non-dict / missing keys → empty lists;
      * nodes/edges that are not lists → empty list;
      * pathologically huge lists truncated to a DoS ceiling (well above the
        cap, so a modest overage still surfaces as a real ``> MAX_NODES``
        rejection in :func:`validate_topology_schema` rather than being silently
        accepted after truncation);
      * non-dict list entries dropped;
      * unknown keys on a node/edge dropped (only the contract subset kept).
    """
    if not isinstance(raw, dict):
        return {"nodes": [], "edges": []}

    raw_nodes = raw.get("nodes")
    raw_edges = raw.get("edges")

    node_keys = {"id", "label", "kind", "tier", "port", "description"}
    edge_keys = {"source", "target", "relationship", "kind"}

    # DoS ceiling: bound how much we ever materialise/validate, but keep it
    # comfortably above the contract cap so the strict size check still fires.
    node_ceiling = MAX_NODES * 4
    edge_ceiling = MAX_EDGES * 4

    nodes: list[dict[str, Any]] = []
    if isinstance(raw_nodes, list):
        for item in raw_nodes[:node_ceiling]:
            if isinstance(item, dict):
                nodes.append({k: v for k, v in item.items() if k in node_keys})

    edges: list[dict[str, Any]] = []
    if isinstance(raw_edges, list):
        for item in raw_edges[:edge_ceiling]:
            if isinstance(item, dict):
                edges.append({k: v for k, v in item.items() if k in edge_keys})

    return {"nodes": nodes, "edges": edges}


def validate_topology_schema(raw: Any) -> TopologySchema:
    """Strictly validate a candidate schema, returning a clean ``TopologySchema``.

    Performs the structural pydantic parse (after :func:`clamp_raw_schema`) plus
    the cross-field invariants pydantic can't express per-field: unique ids,
    edge endpoints referencing real nodes, allowed kind/relationship sets and
    bounded sizes. Auto-fills sane defaults (label←id, edge relationship/kind).

    Raises:
        SchemaValidationError: with a structured ``errors`` list on any problem.
    """
    errors: list[str] = []
    clamped = clamp_raw_schema(raw)

    # ── structural parse ──────────────────────────────────────────────────
    try:
        schema = TopologySchema.model_validate(clamped)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", ()))
            errors.append(f"{loc or 'schema'}: {err.get('msg', 'invalid')}")
        raise SchemaValidationError(errors)

    # ── size bounds ───────────────────────────────────────────────────────
    if len(schema.nodes) == 0:
        errors.append("schema must contain at least one node")
    if len(schema.nodes) > MAX_NODES:
        errors.append(f"too many nodes: {len(schema.nodes)} > {MAX_NODES}")
    if len(schema.edges) > MAX_EDGES:
        errors.append(f"too many edges: {len(schema.edges)} > {MAX_EDGES}")

    # ── nodes: unique ids + allowed kinds, with auto-filled label ─────────
    seen_ids: set[str] = set()
    for node in schema.nodes:
        if node.id in seen_ids:
            errors.append(f"duplicate node id: {node.id!r}")
        seen_ids.add(node.id)
        if node.kind not in ALLOWED_NODE_KINDS:
            errors.append(
                f"node {node.id!r}: invalid kind {node.kind!r} "
                f"(allowed: {', '.join(sorted(ALLOWED_NODE_KINDS))})"
            )
        # Auto-fill: a blank label defaults to the id so a node always renders.
        if not node.label:
            node.label = node.id

    # ── edges: endpoints must reference existing nodes + valid enums ──────
    for edge in schema.edges:
        if edge.source not in seen_ids:
            errors.append(
                f"edge {edge.source!r}->{edge.target!r}: source references "
                f"unknown node {edge.source!r}"
            )
        if edge.target not in seen_ids:
            errors.append(
                f"edge {edge.source!r}->{edge.target!r}: target references "
                f"unknown node {edge.target!r}"
            )
        if edge.relationship not in ALLOWED_RELATIONSHIPS:
            errors.append(
                f"edge {edge.source!r}->{edge.target!r}: invalid relationship "
                f"{edge.relationship!r} (allowed: "
                f"{', '.join(sorted(ALLOWED_RELATIONSHIPS))})"
            )
        if edge.kind not in ALLOWED_EDGE_KINDS:
            errors.append(
                f"edge {edge.source!r}->{edge.target!r}: invalid kind "
                f"{edge.kind!r} (allowed: {', '.join(sorted(ALLOWED_EDGE_KINDS))})"
            )

    if errors:
        raise SchemaValidationError(errors)

    return schema


# ---------------------------------------------------------------------------
# Discovered topology → editable starting point
# ---------------------------------------------------------------------------

def discovered_schema_from_seed() -> TopologySchema:
    """Build an editable :class:`TopologySchema` from the canonical seed.

    Used as the starting point in the editor (and the LLM-generate prompt) when
    no custom schema has been saved yet — the operator edits the *real* platform
    topology rather than a blank canvas. Mirrors ``_fallback_nodes`` /
    ``PLATFORM_DEPENDENCIES`` in ``graph_topology`` / ``topology_seed``.
    """
    from src.memory.topology_seed import PLATFORM_DEPENDENCIES, PLATFORM_SERVICES

    nodes = [
        SchemaNode(
            id=str(s["id"]),
            label=str(s["label"]),
            kind=str(s["kind"]),
            tier=int(s["tier"]),
            port=s.get("port"),
            description=s.get("description"),
        )
        for s in PLATFORM_SERVICES
    ]
    edges = [
        SchemaEdge(
            source=source,
            target=target,
            relationship="DEPENDS_ON",
            kind="static",
        )
        for source, target in PLATFORM_DEPENDENCIES
    ]
    return TopologySchema(nodes=nodes, edges=edges)


__all__ = [
    "ALLOWED_EDGE_KINDS",
    "ALLOWED_NODE_KINDS",
    "ALLOWED_RELATIONSHIPS",
    "MAX_EDGES",
    "MAX_NODES",
    "SchemaEdge",
    "SchemaNode",
    "SchemaValidationError",
    "TopologySchema",
    "clamp_raw_schema",
    "discovered_schema_from_seed",
    "validate_topology_schema",
]
