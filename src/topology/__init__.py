"""
Constitutional AIOps - Editable platform-topology schema package.

Houses the strict Pydantic model for a *custom* platform topology that an
operator can edit in Settings (or have the 14B reasoning model generate from a
natural-language prompt). The model mirrors the FROZEN ``TopologyNode`` /
``TopologyEdge`` payload contract of ``GET /api/v1/graph/topology`` so that an
applied custom schema renders byte-identically to the auto-discovered one.

See ``src/topology/schema.py`` for the model, the allowed-kind set, the strict
validator and the helpers that turn the auto-discovered fallback topology into
an editable starting point.
"""

from src.topology.schema import (
    ALLOWED_EDGE_KINDS,
    ALLOWED_NODE_KINDS,
    ALLOWED_RELATIONSHIPS,
    MAX_EDGES,
    MAX_NODES,
    SchemaEdge,
    SchemaNode,
    SchemaValidationError,
    TopologySchema,
    clamp_raw_schema,
    discovered_schema_from_seed,
    validate_topology_schema,
)

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
