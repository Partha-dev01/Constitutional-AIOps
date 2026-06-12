"""
Constitutional AIOps - Platform Topology Seed (single source of truth)

Canonical description of the REAL deployed platform: which services exist,
what kind of component each one is, which layout tier it belongs to, and the
true dependency direction (X DEPENDS_ON Y means "X needs Y to function").

This replaces the retired ``SERVICE_TEMPLATES`` constant that previously lived
in ``src/api/routes/graph.py`` (its dependency direction was backwards and it
was missing caddy, promtail and both LLM services).

``seed_service_topology()`` is idempotent: it only MERGEs nodes/edges and
SETs properties — it never deletes anything, so episode data created by the
background processor is untouched. It MUST set ``kind`` and ``tier`` on every
Service node: the ``/graph/topology`` endpoint filters on ``kind IS NOT NULL``
to separate real platform services from episode-derived junk nodes, and the
frontend schema-mode layout uses ``tier`` as a layering floor.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical platform services
# kind ∈ {gateway, frontend, backend, datastore, observability, llm}
# tier is a layout layering hint (0 = entry point, higher = deeper dependency)
# ---------------------------------------------------------------------------

PLATFORM_SERVICES: list[dict[str, Any]] = [
    {
        "id": "caddy",
        "label": "Caddy",
        "kind": "gateway",
        "tier": 0,
        "port": 443,
        "description": "Reverse proxy and TLS entrypoint routing browser traffic to the frontend, backend API and Grafana",
    },
    {
        "id": "frontend",
        "label": "Frontend",
        "kind": "frontend",
        "tier": 1,
        "port": 3000,
        "description": "React dashboard UI (chat, incidents, graph explorer, settings)",
    },
    {
        "id": "backend",
        "label": "Backend",
        "kind": "backend",
        "tier": 1,
        "port": 8000,
        "description": "FastAPI orchestrator hosting the dual-agent pipeline, constitutional validator and all APIs",
    },
    {
        "id": "grafana",
        "label": "Grafana",
        "kind": "observability",
        "tier": 1,
        "port": 3001,
        "description": "Dashboards and ad-hoc queries over Prometheus, Loki and Tempo",
    },
    {
        "id": "neo4j",
        "label": "Neo4j",
        "kind": "datastore",
        "tier": 2,
        "port": 7687,
        "description": "Graph database holding episodic memory (episodes, services, root causes, actions)",
    },
    {
        "id": "loki",
        "label": "Loki",
        "kind": "observability",
        "tier": 2,
        "port": 3100,
        "description": "Log aggregation store queried for service and edge-host logs",
    },
    {
        "id": "prometheus",
        "label": "Prometheus",
        "kind": "observability",
        "tier": 2,
        "port": 9090,
        "description": "Metrics time-series database and scrape engine (also discovers edge hosts via the 'edge' label)",
    },
    {
        "id": "tempo",
        "label": "Tempo",
        "kind": "observability",
        "tier": 2,
        "port": 3200,
        "description": "Distributed tracing backend storing OpenTelemetry spans",
    },
    {
        "id": "promtail",
        "label": "Promtail",
        "kind": "observability",
        "tier": 3,
        "port": 9080,
        "description": "Log shipper tailing local container logs into Loki",
    },
    {
        "id": "otel-collector",
        "label": "OTel Collector",
        "kind": "observability",
        "tier": 3,
        "port": 4317,
        "description": "OpenTelemetry collector forwarding traces to Tempo and metrics to Prometheus",
    },
    {
        "id": "qwen3-4b",
        "label": "Qwen3-4B",
        "kind": "llm",
        "tier": 2,
        "port": 8081,
        "description": "Fast Annotator model (System 1): telemetry annotation and anomaly classification",
    },
    {
        "id": "qwen3-14b",
        "label": "Qwen3-14B",
        "kind": "llm",
        "tier": 2,
        "port": 8082,
        "description": "Reasoning Agent model (System 2): RCA, remediation planning and operator chat",
    },
]

# Direction: (source, target) == source DEPENDS_ON target.
PLATFORM_DEPENDENCIES: list[tuple[str, str]] = [
    ("caddy", "frontend"),
    ("caddy", "backend"),
    ("caddy", "grafana"),
    ("backend", "neo4j"),
    ("backend", "loki"),
    ("backend", "prometheus"),
    ("backend", "qwen3-4b"),
    ("backend", "qwen3-14b"),
    ("promtail", "loki"),
    ("otel-collector", "tempo"),
    ("otel-collector", "prometheus"),
    ("grafana", "prometheus"),
    ("grafana", "loki"),
    ("grafana", "tempo"),
]


async def seed_service_topology(neo4j_client: Any) -> dict[str, int]:
    """
    Idempotently seed the real platform topology into Neo4j.

    MERGEs every PLATFORM_SERVICES entry as a ``Service`` node (matched on
    ``name``) and SETs label/kind/tier/port/description, then MERGEs the
    PLATFORM_DEPENDENCIES as ``DEPENDS_ON`` edges. Never deletes or detaches
    anything, so re-running is always safe.

    Args:
        neo4j_client: Connected Neo4jClient (must expose ``session()``).

    Returns:
        Dict with the number of services and dependency edges processed.

    Raises:
        Whatever the Neo4j driver raises — callers decide fatality
        (startup treats failures as non-fatal; the manual endpoint surfaces
        them as a 5xx).
    """
    async with neo4j_client.session() as session:
        await session.run(
            """
            UNWIND $services AS svc
            MERGE (s:Service {name: svc.id})
            SET s.label = svc.label,
                s.kind = svc.kind,
                s.tier = svc.tier,
                s.port = svc.port,
                s.description = svc.description
            """,
            services=PLATFORM_SERVICES,
        )

        await session.run(
            """
            UNWIND $deps AS dep
            MATCH (a:Service {name: dep.source})
            MATCH (b:Service {name: dep.target})
            MERGE (a)-[:DEPENDS_ON]->(b)
            """,
            deps=[{"source": s, "target": t} for s, t in PLATFORM_DEPENDENCIES],
        )

    logger.info(
        "Service topology seeded: %d services, %d dependencies",
        len(PLATFORM_SERVICES),
        len(PLATFORM_DEPENDENCIES),
    )
    return {
        "services": len(PLATFORM_SERVICES),
        "dependencies": len(PLATFORM_DEPENDENCIES),
    }


__all__ = ["PLATFORM_SERVICES", "PLATFORM_DEPENDENCIES", "seed_service_topology"]
