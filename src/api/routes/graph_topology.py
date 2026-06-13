"""
Constitutional AIOps - Platform Topology API (schema-mode data source)

GET  /api/v1/graph/topology       — layered platform architecture + live health
                                    + per-node episode evolution buckets.
POST /api/v1/graph/seed-topology  — manually (re-)apply the idempotent seed.

The GET payload shape is FROZEN (session 14 contract): the frontend schema
graph is built against it via a fixture. Invariants:
  * every node/edge ``buckets`` array has length == the ``buckets`` query
    param, ordered oldest → newest, and sum(node.buckets) == episode_count;
  * ``recent_episodes`` is capped at 5, most recent first;
  * ``health`` ∈ {healthy, warning, critical, unknown};
  * episode ``severity`` is defensively mapped into
    {info, warning, error, critical} (legacy rows carry e.g. "10" → warning);
  * the endpoint NEVER 5xxes — when Neo4j is empty/down it falls back to the
    static topology constants in ``src/memory/topology_seed.py``.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from src.memory.topology_seed import (
    PLATFORM_DEPENDENCIES,
    PLATFORM_SERVICES,
    seed_service_topology,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# How far back an error/critical episode bumps a healthy service to warning.
ESCALATION_WINDOW_HOURS = 6

# Prometheus scrape job -> platform service id(s) (docker/configs/prometheus.yml).
JOB_TO_SERVICE: dict[str, list[str]] = {
    "prometheus": ["prometheus"],
    "aiops-backend": ["backend"],
    "neo4j": ["neo4j"],
    "otel-collector": ["otel-collector"],
    "grafana": ["grafana"],
    "loki": ["loki"],
    "tempo": ["tempo"],
    "caddy": ["caddy"],
    # llama-swap fronts both always-loaded models.
    "llama-swap": ["qwen3-4b", "qwen3-14b"],
}

# Docker container name -> platform service id (docker-compose.production.yml).
CONTAINER_TO_SERVICE: dict[str, str] = {
    "aiops-frontend": "frontend",
    "aiops-backend": "backend",
    "aiops-neo4j": "neo4j",
    "aiops-loki": "loki",
    "aiops-prometheus": "prometheus",
    "aiops-tempo": "tempo",
    "aiops-grafana": "grafana",
    "aiops-otel-collector": "otel-collector",
    "aiops-promtail": "promtail",
    "aiops-caddy": "caddy",
    "aiops-qwen3-4b": "qwen3-4b",
    "aiops-qwen3-14b": "qwen3-14b",
}

_VALID_SEVERITIES = {"info", "warning", "error", "critical"}
_SEVERITY_ALIASES = {
    "warn": "warning",
    "medium": "warning",
    "high": "error",
    "err": "error",
    "fatal": "critical",
    "crit": "critical",
    "low": "info",
    "debug": "info",
    "none": "info",
}


def _map_severity(raw: Any) -> str:
    """Defensively map any stored severity into {info,warning,error,critical}.

    Live data contains legacy numeric strings (e.g. "10" from the old
    ``str(graph severity int)`` write path) — anything unrecognized maps to
    "warning" per the frozen contract.
    """
    s = str(raw or "").strip().lower()
    if s in _VALID_SEVERITIES:
        return s
    return _SEVERITY_ALIASES.get(s, "warning")


# ---------------------------------------------------------------------------
# Response models (FROZEN payload contract)
# ---------------------------------------------------------------------------

class TopologyEpisode(BaseModel):
    """Recent episode summary attached to a topology node."""
    id: str
    title: str
    severity: str = Field(..., description="info | warning | error | critical")
    at: str | None = Field(None, description="ISO timestamp of detection")


class TopologyNodeMeta(BaseModel):
    """Static metadata for a topology node."""
    port: int | None = None
    description: str | None = None
    edge_label: str | None = None


class TopologyNode(BaseModel):
    """A platform service (or dynamic edge host) in the schema graph."""
    id: str
    label: str
    kind: str
    tier: int
    health: str = Field("unknown", description="healthy | warning | critical | unknown")
    health_reason: str = ""
    episode_count: int = 0
    incident_count: int = Field(0, description="error/critical episodes in window")
    last_episode_at: str | None = None
    buckets: list[int] = Field(..., description="Per-bucket episode counts, oldest → newest")
    recent_episodes: list[TopologyEpisode] = Field(default_factory=list)
    meta: TopologyNodeMeta = Field(default_factory=TopologyNodeMeta)


class TopologyEdge(BaseModel):
    """A dependency or telemetry-shipping link in the schema graph."""
    id: str = Field(..., description='"source->target"')
    source: str
    target: str
    relationship: str = Field(..., description="DEPENDS_ON | SHIPS_TELEMETRY")
    kind: str = Field(..., description="static | dynamic")
    co_episode_count: int = 0
    buckets: list[int] = Field(..., description="Per-bucket co-episode counts, oldest → newest")


class TopologyStats(BaseModel):
    """Aggregate stats for the topology payload."""
    nodes: int
    edges: int
    episodes_in_window: int
    source: str = Field(..., description="neo4j | fallback")


class TopologyResponse(BaseModel):
    """Complete platform topology for the schema-mode graph."""
    generated_at: str
    window_hours: int
    bucket_minutes: float
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    stats: TopologyStats


class SeedTopologyResponse(BaseModel):
    """Result of a manual topology seed run."""
    success: bool
    services: int
    dependencies: int
    message: str


# ---------------------------------------------------------------------------
# Data-gathering helpers (each one fails soft — the endpoint never 5xxes)
# ---------------------------------------------------------------------------

def _fallback_nodes() -> dict[str, dict[str, Any]]:
    """Static topology from the seed constants (Neo4j empty/down)."""
    return {
        s["id"]: {
            "label": s["label"],
            "kind": s["kind"],
            "tier": int(s["tier"]),
            "port": s["port"],
            "description": s["description"],
        }
        for s in PLATFORM_SERVICES
    }


async def _load_topology_nodes(
    neo4j_client: Any,
) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str]], str]:
    """Load Service nodes (kind IS NOT NULL filters episode-derived junk) and
    DEPENDS_ON edges from Neo4j; fall back to the seed constants."""
    if neo4j_client is not None:
        try:
            async with neo4j_client.session() as session:
                result = await session.run(
                    """
                    MATCH (s:Service)
                    WHERE s.kind IS NOT NULL
                    RETURN s.name AS id, s.label AS label, s.kind AS kind,
                           s.tier AS tier, s.port AS port,
                           s.description AS description
                    """
                )
                node_rows = await result.data()

                result = await session.run(
                    """
                    MATCH (a:Service)-[:DEPENDS_ON]->(b:Service)
                    WHERE a.kind IS NOT NULL AND b.kind IS NOT NULL
                    RETURN a.name AS source, b.name AS target
                    """
                )
                edge_rows = await result.data()

            nodes: dict[str, dict[str, Any]] = {}
            for row in node_rows:
                sid = row.get("id")
                if not sid:
                    continue
                try:
                    tier = int(row.get("tier")) if row.get("tier") is not None else 1
                except (TypeError, ValueError):
                    tier = 1
                port = row.get("port")
                try:
                    port = int(port) if port is not None else None
                except (TypeError, ValueError):
                    port = None
                nodes[sid] = {
                    "label": str(row.get("label") or sid),
                    "kind": str(row.get("kind") or "backend"),
                    "tier": tier,
                    "port": port,
                    "description": row.get("description"),
                }

            if nodes:
                edges = [
                    (row["source"], row["target"])
                    for row in edge_rows
                    if row.get("source") in nodes and row.get("target") in nodes
                ]
                return nodes, edges, "neo4j"
        except Exception as e:
            logger.warning(f"Topology node query failed, using fallback: {e}")

    return _fallback_nodes(), list(PLATFORM_DEPENDENCIES), "fallback"


def _coerce_dt(value: Any) -> datetime | None:
    """Coerce a Neo4j DateTime / ISO string / datetime into naive-UTC datetime.

    Live data has BOTH storage shapes: episode_store writes datetime($iso)
    (a Neo4j temporal) while the demo generator wrote plain ISO strings.
    """
    if value is None:
        return None
    if hasattr(value, "to_native"):
        try:
            value = value.to_native()
        except Exception:
            return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is not None:
        value = value.replace(tzinfo=None) - (value.utcoffset() or timedelta())
    return value


async def _load_episodes(
    neo4j_client: Any, window_start: datetime
) -> list[dict[str, Any]]:
    """ONE Cypher over (e:Episode)-[:INVOLVES]->(s:Service); bucket in Python.

    The WHERE handles both temporal and string detected_at storage: a
    mixed-type comparison yields null, and ``null OR true`` is true, so each
    row passes through whichever clause matches its storage type.
    """
    if neo4j_client is None:
        return []
    try:
        since_iso = window_start.isoformat()
        async with neo4j_client.session() as session:
            result = await session.run(
                """
                MATCH (e:Episode)-[:INVOLVES]->(s:Service)
                WHERE e.detected_at >= datetime($since)
                   OR e.detected_at >= $since
                RETURN e.episode_id AS id, e.title AS title,
                       e.severity AS severity, e.detected_at AS detected_at,
                       collect(DISTINCT s.name) AS services
                """,
                since=since_iso,
            )
            rows = await result.data()
    except Exception as e:
        logger.warning(f"Topology episode query failed: {e}")
        return []

    episodes: list[dict[str, Any]] = []
    for row in rows:
        at = _coerce_dt(row.get("detected_at"))
        if at is None or at < window_start:
            continue
        episodes.append({
            "id": str(row.get("id") or ""),
            "title": str(row.get("title") or "Episode"),
            "severity": _map_severity(row.get("severity")),
            "at": at,
            "services": {s for s in (row.get("services") or []) if s},
        })
    return episodes


async def _discover_edge_hosts(telemetry_collector: Any) -> dict[str, int]:
    """Dynamic edge hosts from Prometheus ``count by (edge) (up)`` — the same
    discovery (and dismissed-hosts denylist) as /infrastructure/remote-hosts."""
    if telemetry_collector is None:
        return {}
    try:
        from src.api.routes.infrastructure import _load_dismissed_hosts

        dismissed = _load_dismissed_hosts()
        prom_url = telemetry_collector.prometheus_url
        response = await telemetry_collector._client.get(
            f"{prom_url}/api/v1/query",
            params={"query": "count by (edge) (up)"},
        )
        hosts: dict[str, int] = {}
        if response.status_code == 200:
            data = response.json()
            for result in data.get("data", {}).get("result", []):
                edge = result.get("metric", {}).get("edge", "")
                if not edge or edge in dismissed:
                    continue
                try:
                    targets_up = int(float(result.get("value", [0, "0"])[1]))
                except (TypeError, ValueError, IndexError):
                    targets_up = 0
                hosts[edge] = targets_up
        return hosts
    except Exception as e:
        logger.debug(f"Edge-host discovery failed: {e}")
        return {}


async def _prometheus_health(telemetry_collector: Any) -> dict[str, dict[str, Any]]:
    """service id -> {"up": bool, "job": str} from the Prometheus ``up`` vector."""
    if telemetry_collector is None:
        return {}
    out: dict[str, dict[str, Any]] = {}
    try:
        prom_url = telemetry_collector.prometheus_url
        response = await telemetry_collector._client.get(
            f"{prom_url}/api/v1/query",
            params={"query": "up"},
        )
        if response.status_code != 200:
            return {}
        for result in response.json().get("data", {}).get("result", []):
            metric = result.get("metric", {})
            if metric.get("edge"):
                continue  # edge-host series are handled by _discover_edge_hosts
            services = JOB_TO_SERVICE.get(metric.get("job", ""))
            if not services:
                continue
            try:
                value = float(result.get("value", [0, "0"])[1])
            except (TypeError, ValueError, IndexError):
                value = 0.0
            up = value >= 1.0
            for sid in services:
                current = out.get(sid)
                # Any up=1 series wins over up=0 for the same service.
                if current is None or (up and not current["up"]):
                    out[sid] = {"up": up, "job": metric.get("job", "")}
        return out
    except Exception as e:
        logger.debug(f"Prometheus health query failed: {e}")
        return {}


def _docker_health() -> dict[str, str]:
    """service id -> docker container status (same pattern as the chat
    runtime-context builder)."""
    out: dict[str, str] = {}
    try:
        from src.api.routes.infrastructure import _get_docker_client

        docker_client = _get_docker_client()
        if docker_client is None:
            return {}
        try:
            for container in docker_client.containers.list(all=True):
                sid = CONTAINER_TO_SERVICE.get(container.name)
                if sid:
                    out[sid] = container.status
        finally:
            docker_client.close()
    except Exception as e:
        logger.debug(f"Docker health query failed: {e}")
    return out


def _resolve_health(
    sid: str,
    prom_health: dict[str, dict[str, Any]],
    docker_health: dict[str, str],
    has_recent_incident: bool,
) -> tuple[str, str]:
    """Deterministic health ladder; returns (health, winning rule)."""
    health, reason = "unknown", "no health signal"

    docker_status = docker_health.get(sid)
    docker_running = docker_status == "running"
    if docker_status is not None:
        if docker_status == "running":
            health, reason = "healthy", "docker container running"
        elif docker_status in ("restarting", "paused"):
            health, reason = "warning", f"docker container {docker_status}"
        else:
            health, reason = "critical", f"docker container {docker_status}"

    prom = prom_health.get(sid)
    if prom is not None:
        if prom["up"]:
            # A live scrape only upgrades; it cannot mask a dead container.
            if health != "critical":
                health, reason = "healthy", f"prometheus up=1 (job {prom['job']})"
        elif not docker_running:
            # up=0 is only a real liveness problem when docker does NOT confirm
            # the container is running. Several platform services (neo4j, the
            # vLLM models, promtail) expose no Prometheus metrics by design, so
            # a configured-but-unscraped target must never mark a live container
            # critical — docker "running" is authoritative for liveness.
            health, reason = "critical", f"prometheus up=0 (job {prom['job']})"

    if health == "healthy" and has_recent_incident:
        health = "warning"
        reason = (
            f"error/critical episode within last {ESCALATION_WINDOW_HOURS}h "
            f"(was: {reason})"
        )
    return health, reason


def _bucket_index(
    at: datetime, window_start: datetime, now: datetime, buckets: int
) -> int:
    """Map a timestamp into [0, buckets-1], oldest → newest."""
    total = (now - window_start).total_seconds()
    if total <= 0:
        return buckets - 1
    frac = (at - window_start).total_seconds() / total
    return max(0, min(buckets - 1, int(frac * buckets)))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/topology",
    response_model=TopologyResponse,
    summary="Get Platform Topology",
    description=(
        "Layered platform architecture with live health and per-node episode "
        "evolution buckets. Falls back to the static seed topology when Neo4j "
        "is empty or unreachable (never 5xx)."
    ),
)
async def get_topology(
    request: Request,
    window_hours: int = Query(168, ge=1, le=2160, description="Episode window in hours"),
    buckets: int = Query(28, ge=4, le=96, description="Number of evolution buckets"),
) -> TopologyResponse:
    """Build the schema-mode topology payload (frozen session-14 contract)."""
    now = datetime.utcnow()
    window_start = now - timedelta(hours=window_hours)
    bucket_minutes = round(window_hours * 60 / buckets, 2)

    neo4j_client = getattr(request.app.state, "neo4j_client", None)
    telemetry_collector = getattr(request.app.state, "telemetry_collector", None)

    nodes_raw, dep_edges, source = await _load_topology_nodes(neo4j_client)
    episodes = await _load_episodes(neo4j_client, window_start)
    edge_hosts = await _discover_edge_hosts(telemetry_collector)
    prom_health = await _prometheus_health(telemetry_collector)
    docker_health = _docker_health()

    escalation_cutoff = now - timedelta(hours=ESCALATION_WINDOW_HOURS)
    per_service: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ep in episodes:
        for svc in ep["services"]:
            per_service[svc].append(ep)

    nodes_out: list[TopologyNode] = []
    for sid, info in sorted(nodes_raw.items(), key=lambda kv: (kv[1]["tier"], kv[0])):
        eps = per_service.get(sid, [])
        bucket_counts = [0] * buckets
        for ep in eps:
            bucket_counts[_bucket_index(ep["at"], window_start, now, buckets)] += 1
        incident_count = sum(1 for ep in eps if ep["severity"] in ("error", "critical"))
        recent = sorted(eps, key=lambda e: e["at"], reverse=True)[:5]
        has_recent_incident = any(
            ep["severity"] in ("error", "critical") and ep["at"] >= escalation_cutoff
            for ep in eps
        )
        health, reason = _resolve_health(sid, prom_health, docker_health, has_recent_incident)
        nodes_out.append(TopologyNode(
            id=sid,
            label=info["label"],
            kind=info["kind"],
            tier=info["tier"],
            health=health,
            health_reason=reason,
            episode_count=len(eps),
            incident_count=incident_count,
            last_episode_at=recent[0]["at"].isoformat() + "Z" if recent else None,
            buckets=bucket_counts,
            recent_episodes=[
                TopologyEpisode(
                    id=ep["id"],
                    title=ep["title"],
                    severity=ep["severity"],
                    at=ep["at"].isoformat() + "Z",
                )
                for ep in recent
            ],
            meta=TopologyNodeMeta(
                port=info.get("port"),
                description=info.get("description"),
            ),
        ))

    # Dynamic edge hosts: one node per discovered 'edge' label, pinned one
    # tier past the deepest platform tier, shipping telemetry to loki + prom.
    max_tier = max((n["tier"] for n in nodes_raw.values()), default=0)
    edge_tier = max_tier + 1
    for edge_label in sorted(edge_hosts):
        targets_up = edge_hosts[edge_label]
        nodes_out.append(TopologyNode(
            id=f"edge:{edge_label}",
            label=edge_label,
            kind="edge-host",
            tier=edge_tier,
            health="healthy" if targets_up > 0 else "unknown",
            health_reason=(
                f"{targets_up} scrape target(s) up" if targets_up > 0
                else "no scrape targets up"
            ),
            episode_count=0,
            incident_count=0,
            last_episode_at=None,
            buckets=[0] * buckets,
            recent_episodes=[],
            meta=TopologyNodeMeta(edge_label=edge_label),
        ))

    node_ids = {n.id for n in nodes_out}
    edges_out: list[TopologyEdge] = []
    for src_id, tgt_id in dep_edges:
        if src_id not in node_ids or tgt_id not in node_ids:
            continue
        co = [ep for ep in episodes if src_id in ep["services"] and tgt_id in ep["services"]]
        bucket_counts = [0] * buckets
        for ep in co:
            bucket_counts[_bucket_index(ep["at"], window_start, now, buckets)] += 1
        edges_out.append(TopologyEdge(
            id=f"{src_id}->{tgt_id}",
            source=src_id,
            target=tgt_id,
            relationship="DEPENDS_ON",
            kind="static",
            co_episode_count=len(co),
            buckets=bucket_counts,
        ))
    for edge_label in sorted(edge_hosts):
        src_id = f"edge:{edge_label}"
        for tgt_id in ("loki", "prometheus"):
            if tgt_id in node_ids:
                edges_out.append(TopologyEdge(
                    id=f"{src_id}->{tgt_id}",
                    source=src_id,
                    target=tgt_id,
                    relationship="SHIPS_TELEMETRY",
                    kind="dynamic",
                    co_episode_count=0,
                    buckets=[0] * buckets,
                ))

    return TopologyResponse(
        generated_at=now.isoformat() + "Z",
        window_hours=window_hours,
        bucket_minutes=bucket_minutes,
        nodes=nodes_out,
        edges=edges_out,
        stats=TopologyStats(
            nodes=len(nodes_out),
            edges=len(edges_out),
            episodes_in_window=len(episodes),
            source=source,
        ),
    )


@router.post(
    "/seed-topology",
    response_model=SeedTopologyResponse,
    summary="Seed Service Topology",
    description=(
        "Idempotently MERGE the real platform services and DEPENDS_ON edges "
        "into Neo4j (never deletes anything). Also runs automatically at startup."
    ),
)
async def seed_topology(request: Request) -> SeedTopologyResponse:
    """Manually (re-)apply the canonical topology seed."""
    neo4j_client = getattr(request.app.state, "neo4j_client", None)
    if neo4j_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j client not available",
        )
    try:
        counts = await seed_service_topology(neo4j_client)
    except Exception as e:
        logger.error(f"Manual topology seed failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Topology seed failed: {e}",
        )
    return SeedTopologyResponse(
        success=True,
        services=counts["services"],
        dependencies=counts["dependencies"],
        message=(
            f"Seeded {counts['services']} services and "
            f"{counts['dependencies']} DEPENDS_ON edges (idempotent MERGE)"
        ),
    )


__all__ = ["router"]
