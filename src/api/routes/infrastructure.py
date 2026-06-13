"""
Constitutional AIOps - Infrastructure API Routes

Provides endpoints for infrastructure/container status with dynamic Docker discovery.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Dismissed remote hosts — persisted denylist
#
# The "Monitored remote hosts" list is auto-derived from live Prometheus/Loki
# `edge` labels, so a stale or one-off host (e.g. a decommissioned box) lingers
# until Loki retention ages it out. Dismissing an edge label hides it from the
# list. Persisted under AIOPS_DATA_DIR (same convention as settings.py) so it
# survives backend rebuilds. Stdlib json only — zero new deps.
# ---------------------------------------------------------------------------

def _dismissed_hosts_path() -> Path:
    """Path to the persisted dismissed-edge-labels JSON file."""
    base = os.environ.get("AIOPS_DATA_DIR") or os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "settings"
    )
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path / "dismissed_hosts.json"


def _load_dismissed_hosts() -> set[str]:
    """Load the set of dismissed edge labels; return empty set on any error."""
    try:
        p = _dismissed_hosts_path()
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            return set(data.get("dismissed", []))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read dismissed hosts: %s", exc)
    return set()


def _save_dismissed_hosts(labels: set[str]) -> None:
    """Persist the dismissed edge labels (atomic-ish: write then rename)."""
    p = _dismissed_hosts_path()
    tmp = p.with_suffix(".tmp")
    try:
        tmp.write_text(
            json.dumps({"dismissed": sorted(labels)}, indent=2), encoding="utf-8"
        )
        tmp.replace(p)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist dismissed hosts: %s", exc)

# In-memory store for monitored containers
_monitored_containers: set[str] = {
    "aiops-frontend",
    "aiops-backend",
    "aiops-neo4j",
    "aiops-loki",
    "aiops-prometheus",
    "aiops-tempo",
    "aiops-grafana",
    "aiops-otel-collector",
    "nextcloud",
}


class ContainerInfo(BaseModel):
    """Container information."""
    name: str
    service: str
    status: str = Field(..., description="running, stopped, restarting, exited")
    health: str | None = Field(None, description="healthy, unhealthy, starting, none")
    port: str | None = None
    image: str | None = None
    description: str | None = None
    monitored: bool = False


class InfrastructureResponse(BaseModel):
    """Infrastructure status response."""
    containers: list[ContainerInfo]
    total: int
    healthy: int
    unhealthy: int


class DiscoveredContainer(BaseModel):
    """Discovered container from Docker."""
    name: str
    image: str
    status: str
    ports: str | None
    created: str | None
    monitored: bool


class DiscoveryResponse(BaseModel):
    """Container discovery response."""
    containers: list[DiscoveredContainer]
    total: int


class MonitorRequest(BaseModel):
    """Request to monitor a container."""
    container_name: str


class BulkMonitorRequest(BaseModel):
    """Request to monitor multiple containers."""
    containers: list[str]


def _get_docker_client():
    """Get Docker client, handling different environments (sync — call from a thread)."""
    try:
        import docker
        return docker.from_env()
    except Exception as e:
        logger.warning(f"Failed to connect to Docker: {e}")
        return None


def _collect_container_status(
    monitored: set[str],
) -> tuple[list[ContainerInfo], int, int]:
    """Synchronous helper: list containers and read their attrs.

    Called via ``asyncio.to_thread`` so the blocking Docker SDK socket I/O never
    runs on the event loop.  Returns (containers, healthy_count, unhealthy_count).
    Raises on unrecoverable errors so the caller can fall back to the static list.
    """
    import docker  # guarded inside helper; callers catch ImportError

    docker_client = docker.from_env()
    try:
        all_containers = docker_client.containers.list(all=True)
        containers: list[ContainerInfo] = []
        healthy_count = 0
        unhealthy_count = 0

        for container in all_containers:
            name = container.name
            if name not in monitored:
                continue

            c_status = container.status
            health: str | None = None
            health_state = container.attrs.get("State", {}).get("Health", {})
            if health_state:
                health = health_state.get("Status", "unknown")

            image = (
                container.image.tags[0]
                if container.image.tags
                else str(container.image.id)[:12]
            )
            ports = _format_ports(container.ports)
            service = (
                name.replace("aiops-", "") if name.startswith("aiops-") else name
            )

            if c_status == "running":
                if health in ("healthy", None):
                    healthy_count += 1
                    if health is None:
                        health = "healthy"
                else:
                    unhealthy_count += 1
            else:
                unhealthy_count += 1
                if health is None:
                    health = "unhealthy"

            containers.append(
                ContainerInfo(
                    name=name,
                    service=service,
                    status=c_status,
                    health=health,
                    port=ports,
                    image=image,
                    description=_get_container_description(service),
                    monitored=True,
                )
            )
    finally:
        docker_client.close()

    return containers, healthy_count, unhealthy_count


def _discover_all_containers(monitored: set[str]) -> list[DiscoveredContainer]:
    """Synchronous helper: discover all containers via the Docker SDK.

    Called via ``asyncio.to_thread``.
    """
    import docker

    docker_client = docker.from_env()
    try:
        all_containers = docker_client.containers.list(all=True)
        discovered: list[DiscoveredContainer] = []
        for container in all_containers:
            name = container.name
            image = (
                container.image.tags[0]
                if container.image.tags
                else str(container.image.id)[:12]
            )
            ports = _format_ports(container.ports)
            created = (
                container.attrs.get("Created", "")[:19]
                if container.attrs.get("Created")
                else None
            )
            discovered.append(
                DiscoveredContainer(
                    name=name,
                    image=image,
                    status=container.status,
                    ports=ports,
                    created=created,
                    monitored=name in monitored,
                )
            )
    finally:
        docker_client.close()

    return discovered


def _format_ports(ports: dict) -> str | None:
    """Format Docker ports dict into readable string."""
    if not ports:
        return None
    port_strs = []
    for container_port, host_bindings in ports.items():
        if host_bindings:
            for binding in host_bindings:
                host_port = binding.get('HostPort', '')
                port_strs.append(f"{host_port}->{container_port}")
        else:
            port_strs.append(container_port)
    return ", ".join(port_strs[:3])  # Limit to 3 for display


@router.get(
    "/containers",
    response_model=InfrastructureResponse,
    summary="Get Container Status",
    description="Get status of all monitored infrastructure containers",
)
async def get_containers(request: Request) -> InfrastructureResponse:
    """
    Get status of monitored infrastructure containers.

    Uses Docker SDK to get real-time container status.  The blocking Docker SDK
    calls run in a thread via ``asyncio.to_thread`` so the event loop is never
    stalled while waiting for the Docker daemon.
    """
    try:
        # Capture the monitored set snapshot for the thread (avoids sharing mutable state).
        monitored_snapshot = frozenset(_monitored_containers)
        containers, healthy_count, unhealthy_count = await asyncio.to_thread(
            _collect_container_status, monitored_snapshot
        )
    except Exception as e:
        logger.error(f"Failed to get container status: {e}")
        return await _get_static_containers(request)

    return InfrastructureResponse(
        containers=sorted(containers, key=lambda c: c.name),
        total=len(containers),
        healthy=healthy_count,
        unhealthy=unhealthy_count,
    )


@router.get(
    "/containers/discover",
    response_model=DiscoveryResponse,
    summary="Discover Docker Containers",
    description="Discover all Docker containers available for monitoring",
)
async def discover_containers() -> DiscoveryResponse:
    """
    Discover all Docker containers on the host.

    Returns all containers regardless of monitoring status.  The blocking Docker
    SDK calls run in a thread via ``asyncio.to_thread`` so the event loop is not
    stalled while waiting for the Docker daemon.
    """
    try:
        monitored_snapshot = frozenset(_monitored_containers)
        discovered = await asyncio.to_thread(_discover_all_containers, monitored_snapshot)
    except Exception as e:
        logger.error(f"Failed to discover containers: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker daemon not available",
        )

    return DiscoveryResponse(
        containers=sorted(discovered, key=lambda c: c.name),
        total=len(discovered),
    )


@router.post(
    "/containers/monitor",
    summary="Add Container to Monitoring",
    description="Add a container to the monitored list",
)
async def add_monitored_container(request_body: MonitorRequest) -> dict[str, Any]:
    """
    Add a container to the monitored list.

    Args:
        request_body: Container name to monitor
    """
    container_name = request_body.container_name

    # Verify container exists (blocking lookup offloaded to thread)
    def _check_container_exists(name: str) -> bool:
        """Return True if the container exists; False if Docker is unavailable."""
        client = _get_docker_client()
        if client is None:
            return True  # Docker unavailable — allow add anyway
        try:
            client.containers.get(name)
            return True
        finally:
            client.close()

    try:
        found = await asyncio.to_thread(_check_container_exists, container_name)
    except Exception:
        found = False

    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container '{container_name}' not found",
        )

    _monitored_containers.add(container_name)
    logger.info(f"Added container to monitoring: {container_name}")

    return {
        "status": "success",
        "message": f"Container '{container_name}' added to monitoring",
        "monitored_containers": list(_monitored_containers),
    }


@router.post(
    "/monitor",
    summary="Start Monitoring Containers",
    description="Add multiple containers to monitoring list and collect initial telemetry",
)
async def start_monitoring(request: Request, request_body: BulkMonitorRequest) -> dict[str, Any]:
    """
    Add multiple containers to the monitored list and start collecting telemetry.

    Args:
        request: FastAPI request with app state
        request_body: List of container names to monitor
    """
    added: list[str] = []
    not_found: list[str] = []
    logs_collected = 0

    fast_annotator = getattr(request.app.state, "fast_annotator", None)

    def _fetch_container_logs(name: str) -> list[str] | None:
        """Return the last 20 log lines for *name*, or None if not found/unavailable."""
        client = _get_docker_client()
        if client is None:
            return []  # Docker unavailable — allow add with no logs
        try:
            container = client.containers.get(name)
            raw = container.logs(tail=50, timestamps=True).decode("utf-8", errors="ignore")
            return raw.strip().split("\n")[-20:] if raw.strip() else []
        except Exception:
            return None  # container not found
        finally:
            client.close()

    for container_name in request_body.containers:
        # Blocking Docker log fetch offloaded to thread pool.
        log_lines = await asyncio.to_thread(_fetch_container_logs, container_name)

        if log_lines is None:
            # _fetch_container_logs returns None only when the container is absent.
            not_found.append(container_name)
            continue

        _monitored_containers.add(container_name)
        added.append(container_name)
        logger.info(f"Added container to monitoring: {container_name}")

        if fast_annotator and log_lines:
            for log_line in log_lines:
                if log_line.strip():
                    try:
                        await _process_container_log(fast_annotator, container_name, log_line)
                        logs_collected += 1
                    except Exception as e:
                        logger.warning(f"Failed to collect logs from {container_name}: {e}")

    return {
        "status": "success",
        "message": f"Added {len(added)} container(s) to monitoring, processed {logs_collected} log entries",
        "added": added,
        "not_found": not_found,
        "logs_collected": logs_collected,
        "monitored_containers": sorted(list(_monitored_containers)),
    }


async def _process_container_log(
    fast_annotator,
    container_name: str,
    log_line: str,
) -> None:
    """
    Process a container log line through the Fast Agent.

    Args:
        fast_annotator: Fast Agent instance
        container_name: Source container name
        log_line: Raw log line to process
    """
    import time

    try:
        start_time = time.perf_counter()

        # Process through Fast Agent for annotation
        result = await fast_annotator.process({
            "log_line": log_line,
            "source": container_name,
            "task": "annotate",
        })

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Log the activity
        fast_annotator._log_activity(
            activity_type="annotation",
            input_text=f"[{container_name}] {log_line[:200]}",
            output_text=result.content[:500] if result.content else "No output",
            latency_ms=latency_ms,
            status="success" if result.confidence > 0.5 else "warning",
        )

    except Exception as e:
        logger.warning(f"Failed to process log: {e}")
        # Still log the activity as an error
        if hasattr(fast_annotator, '_log_activity'):
            fast_annotator._log_activity(
                activity_type="annotation",
                input_text=f"[{container_name}] {log_line[:200]}",
                output_text=f"Error: {str(e)}",
                latency_ms=0,
                status="error",
            )


@router.delete(
    "/containers/{container_name}/monitor",
    summary="Remove Container from Monitoring",
    description="Remove a container from the monitored list",
)
async def remove_monitored_container(container_name: str) -> dict[str, Any]:
    """
    Remove a container from the monitored list.

    Args:
        container_name: Name of the container to remove from monitoring
    """
    if container_name not in _monitored_containers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container '{container_name}' not in monitoring list",
        )

    _monitored_containers.discard(container_name)
    logger.info(f"Removed container from monitoring: {container_name}")

    return {
        "status": "success",
        "message": f"Container '{container_name}' removed from monitoring",
        "monitored_containers": list(_monitored_containers),
    }


@router.get(
    "/containers/monitored",
    summary="Get Monitored Container List",
    description="Get the list of containers being monitored",
)
async def get_monitored_containers() -> dict[str, Any]:
    """Get the list of containers currently being monitored."""
    return {
        "monitored_containers": sorted(list(_monitored_containers)),
        "total": len(_monitored_containers),
    }


@router.get(
    "/services",
    summary="Get Services Status",
    description="Get status of LLM and core services",
)
async def get_services(request: Request) -> dict[str, Any]:
    """Get status of LLM services and other core components."""
    model_router = getattr(request.app.state, "model_router", None)

    services = {
        "fast_agent": {
            "name": "Fast Agent (Qwen3-4B)",
            "purpose": "Telemetry annotation & classification",
            "port": 8081,
            "healthy": False,
            "latency_ms": None,
        },
        "reasoning_agent": {
            "name": "Reasoning Agent (Qwen3-14B)",
            "purpose": "RCA & remediation planning",
            "port": 8082,
            "healthy": False,
            "latency_ms": None,
        },
    }

    if model_router:
        try:
            health = await model_router.health_check()
            if health.get("fast_agent"):
                services["fast_agent"]["healthy"] = True
                services["fast_agent"]["latency_ms"] = health.get("fast_agent_latency_ms")
            if health.get("reasoning_agent"):
                services["reasoning_agent"]["healthy"] = True
                services["reasoning_agent"]["latency_ms"] = health.get("reasoning_agent_latency_ms")
        except Exception as e:
            logger.warning(f"Failed to check services: {e}")

    return {"services": services}


def _get_container_description(service: str) -> str:
    """Get description for known services."""
    descriptions = {
        "frontend": "React frontend with nginx proxy",
        "backend": "FastAPI backend server",
        "neo4j": "Graph database for episodic memory",
        "loki": "Log aggregation system",
        "prometheus": "Metrics collection and storage",
        "tempo": "Distributed tracing backend",
        "grafana": "Observability dashboard",
        "otel-collector": "OpenTelemetry collector",
        "nextcloud": "Cloud storage and collaboration platform",
    }
    return descriptions.get(service, f"{service} service")


async def _get_static_containers(request: Request) -> InfrastructureResponse:
    """Fallback static container list when Docker is unavailable."""
    expected_containers = [
        {"name": "aiops-frontend", "service": "frontend", "image": "constitutional-aiops-frontend", "port": "3000"},
        {"name": "aiops-backend", "service": "backend", "image": "constitutional-aiops-backend", "port": "8000"},
        {"name": "aiops-neo4j", "service": "neo4j", "image": "neo4j:5.15-community", "port": "7474, 7687"},
        {"name": "aiops-loki", "service": "loki", "image": "grafana/loki:2.9.3", "port": "3100"},
        {"name": "aiops-prometheus", "service": "prometheus", "image": "prom/prometheus:v2.48.0", "port": "9090"},
        {"name": "aiops-tempo", "service": "tempo", "image": "grafana/tempo:2.3.1", "port": "3200"},
        {"name": "aiops-grafana", "service": "grafana", "image": "grafana/grafana:10.2.3", "port": "3001"},
        {"name": "aiops-otel-collector", "service": "otel-collector", "image": "otel/opentelemetry-collector-contrib", "port": "4317, 4318"},
        {"name": "nextcloud", "service": "nextcloud", "image": "nextcloud:latest", "port": "8080"},
    ]

    containers = []
    for c in expected_containers:
        containers.append(ContainerInfo(
            name=c["name"],
            service=c["service"],
            status="unknown",
            health="unknown",
            port=c["port"],
            image=c["image"],
            description=_get_container_description(c["service"]),
            monitored=c["name"] in _monitored_containers,
        ))

    return InfrastructureResponse(
        containers=containers,
        total=len(containers),
        healthy=0,
        unhealthy=0,
    )


class RemoteHost(BaseModel):
    """Remote/edge host monitored via Grafana Alloy edge agent."""
    edge_label: str = Field(..., description="The 'edge' label value set in the agent .env")
    status: str = Field(..., description="up, down, or unknown")
    targets_up: int = Field(0, description="Number of Prometheus scrape targets reporting up=1")
    targets_total: int = Field(0, description="Total Prometheus scrape targets seen")
    recent_log_lines: int = Field(0, description="Log lines seen in Loki in the last 15 minutes (0 = no data or Loki unreachable)")
    last_seen: str | None = Field(None, description="ISO timestamp of most recent metric/log activity")


class RemoteHostsResponse(BaseModel):
    """Response containing all known remote/edge hosts."""
    hosts: list[RemoteHost]
    total: int
    source: str = Field(..., description="Which telemetry store was queried: prometheus, loki, both, or none")


@router.get(
    "/remote-hosts",
    response_model=RemoteHostsResponse,
    summary="Get Remote Edge Hosts",
    description=(
        "Return all remote hosts that are shipping telemetry via a Grafana Alloy edge agent. "
        "Queries Prometheus for distinct 'edge' label values (up metric) and Loki for recent "
        "log volume per edge label. Read-only — does not modify monitoring state."
    ),
)
async def get_remote_hosts(request: Request) -> RemoteHostsResponse:
    """
    Surface remote/edge hosts as first-class entries.

    Data sources:
    - Prometheus: ``count by (edge) (up)`` to find active edge labels + scrape-target counts.
    - Loki: label-values for ``edge`` + last-15-min log volume per label.
    """
    telemetry_collector = getattr(request.app.state, "telemetry_collector", None)

    if telemetry_collector is None:
        return RemoteHostsResponse(hosts=[], total=0, source="none")

    dismissed = _load_dismissed_hosts()
    hosts_map: dict[str, dict] = {}
    sources_used: list[str] = []

    # ── Prometheus: discover edge labels via `count by (edge) (up == 1)` ─────
    # The `up` series exists for DOWN targets too (value 0), so `count(up)` would
    # count a fully-down host as "up". Filter to `up == 1` so targets_up only
    # counts healthy scrape targets; the total (up + down) is fetched separately.
    try:
        prom_url = telemetry_collector.prometheus_url
        response = await telemetry_collector._client.get(
            f"{prom_url}/api/v1/query",
            params={"query": "count by (edge) (up == 1)"},
        )
        if response.status_code == 200:
            data = response.json()
            sources_used.append("prometheus")
            for result in data.get("data", {}).get("result", []):
                edge = result.get("metric", {}).get("edge", "")
                if not edge:
                    continue
                targets_up = int(float(result.get("value", [0, "0"])[1]))
                hosts_map.setdefault(edge, {
                    "targets_up": 0,
                    "targets_total": 0,
                    "recent_log_lines": 0,
                    "last_seen": None,
                })
                hosts_map[edge]["targets_up"] = targets_up

            # Second pass: total targets per edge (up + down). `count by (edge)(up)`
            # counts every target regardless of value, so it is the real total.
            # This pass also DISCOVERS edges whose targets are all down (absent from
            # the `up == 1` pass above) and seeds them with targets_up=0 so a fully
            # down host still surfaces — as unhealthy, not green.
            total_resp = await telemetry_collector._client.get(
                f"{prom_url}/api/v1/query",
                params={"query": "count by (edge) (up)"},
            )
            if total_resp.status_code == 200:
                total_data = total_resp.json()
                for result in total_data.get("data", {}).get("result", []):
                    edge = result.get("metric", {}).get("edge", "")
                    if not edge:
                        continue
                    hosts_map.setdefault(edge, {
                        "targets_up": 0,
                        "targets_total": 0,
                        "recent_log_lines": 0,
                        "last_seen": None,
                    })
                    hosts_map[edge]["targets_total"] = int(float(result.get("value", [0, "0"])[1]))

            # Get last-seen timestamp for each edge (max timestamp of any `up` series)
            ts_resp = await telemetry_collector._client.get(
                f"{prom_url}/api/v1/query",
                params={"query": "max by (edge) (timestamp(up))"},
            )
            if ts_resp.status_code == 200:
                ts_data = ts_resp.json()
                for result in ts_data.get("data", {}).get("result", []):
                    edge = result.get("metric", {}).get("edge", "")
                    ts_val = result.get("value", [0, "0"])[1]
                    if edge and edge in hosts_map:
                        try:
                            hosts_map[edge]["last_seen"] = datetime.utcfromtimestamp(
                                float(ts_val)
                            ).isoformat() + "Z"
                        except (ValueError, TypeError):
                            pass

    except Exception as e:
        logger.debug(f"Prometheus remote-hosts query failed: {e}")

    # ── Loki: label-values for 'edge' + recent log volume ────────────────────
    try:
        loki_url = telemetry_collector.loki_url
        # Get all known edge label values from Loki
        lv_resp = await telemetry_collector._client.get(
            f"{loki_url}/loki/api/v1/label/edge/values",
        )
        if lv_resp.status_code == 200:
            lv_data = lv_resp.json()
            sources_used.append("loki")
            for edge in lv_data.get("data", []):
                if not edge:
                    continue
                hosts_map.setdefault(edge, {
                    "targets_up": 0,
                    "targets_total": 0,
                    "recent_log_lines": 0,
                    "last_seen": None,
                })

        # Count recent log lines per edge label (last 15 minutes)
        from datetime import timezone as _tz
        now = datetime.now(_tz.utc)
        start_ns = int((now.timestamp() - 15 * 60) * 1e9)
        end_ns = int(now.timestamp() * 1e9)

        for edge in list(hosts_map.keys()):
            try:
                q_resp = await telemetry_collector._client.get(
                    f"{loki_url}/loki/api/v1/query_range",
                    params={
                        "query": f'{{edge="{edge}"}}',
                        "start": str(start_ns),
                        "end": str(end_ns),
                        "limit": 200,
                    },
                )
                if q_resp.status_code == 200:
                    q_data = q_resp.json()
                    line_count = sum(
                        len(stream.get("values", []))
                        for stream in q_data.get("data", {}).get("result", [])
                    )
                    hosts_map[edge]["recent_log_lines"] = line_count
                    # Update last_seen from Loki if we have log data and no prom timestamp yet
                    if line_count > 0 and hosts_map[edge]["last_seen"] is None:
                        # Find the most recent timestamp across all streams
                        latest_ns: int | None = None
                        for stream in q_data.get("data", {}).get("result", []):
                            for val in stream.get("values", []):
                                try:
                                    ts = int(val[0])
                                    if latest_ns is None or ts > latest_ns:
                                        latest_ns = ts
                                except (ValueError, TypeError):
                                    pass
                        if latest_ns is not None:
                            hosts_map[edge]["last_seen"] = (
                                datetime.utcfromtimestamp(latest_ns / 1e9).isoformat() + "Z"
                            )
            except Exception as e:
                logger.debug(f"Loki log-count query failed for edge={edge!r}: {e}")

    except Exception as e:
        logger.debug(f"Loki remote-hosts label query failed: {e}")

    # ── Build response ────────────────────────────────────────────────────────
    hosts: list[RemoteHost] = []
    for edge, info in sorted(hosts_map.items()):
        if edge in dismissed:
            continue  # user dismissed this host from the monitored list
        targets_up = info["targets_up"]
        targets_total = info["targets_total"] or targets_up  # fallback: assume all up
        if targets_up > 0:
            host_status = "up"
        elif targets_total > 0:
            host_status = "down"
        else:
            # Only Loki data — consider "up" if logs arrived recently
            host_status = "up" if info["recent_log_lines"] > 0 else "unknown"

        hosts.append(RemoteHost(
            edge_label=edge,
            status=host_status,
            targets_up=targets_up,
            targets_total=targets_total,
            recent_log_lines=info["recent_log_lines"],
            last_seen=info["last_seen"],
        ))

    source = "+".join(sources_used) if sources_used else "none"
    return RemoteHostsResponse(hosts=hosts, total=len(hosts), source=source)


class DismissHostResponse(BaseModel):
    """Result of dismissing/restoring a monitored remote host."""
    edge_label: str
    dismissed: bool
    message: str


@router.delete(
    "/remote-hosts/{edge_label}",
    response_model=DismissHostResponse,
    summary="Dismiss Remote Edge Host",
    description=(
        "Hide a remote host from the monitored-hosts list by dismissing its `edge` "
        "label. The list is auto-derived from live telemetry, so this adds the label "
        "to a persisted denylist rather than deleting telemetry. If the host keeps "
        "shipping it stays hidden until restored. Use to clear stale/one-off hosts."
    ),
)
async def dismiss_remote_host(edge_label: str) -> DismissHostResponse:
    """Add an edge label to the persisted denylist so it stops showing."""
    if not edge_label.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="edge_label is required"
        )
    dismissed = _load_dismissed_hosts()
    dismissed.add(edge_label)
    _save_dismissed_hosts(dismissed)
    logger.info("Dismissed remote host: %s", edge_label)
    return DismissHostResponse(
        edge_label=edge_label,
        dismissed=True,
        message=f"'{edge_label}' removed from the monitored-hosts list.",
    )


@router.post(
    "/remote-hosts/{edge_label}/restore",
    response_model=DismissHostResponse,
    summary="Restore Dismissed Remote Host",
    description="Undo a dismissal — the host reappears if it is still shipping telemetry.",
)
async def restore_remote_host(edge_label: str) -> DismissHostResponse:
    """Remove an edge label from the persisted denylist."""
    dismissed = _load_dismissed_hosts()
    dismissed.discard(edge_label)
    _save_dismissed_hosts(dismissed)
    logger.info("Restored remote host: %s", edge_label)
    return DismissHostResponse(
        edge_label=edge_label,
        dismissed=False,
        message=f"'{edge_label}' restored to the monitored-hosts list.",
    )


__all__ = ["router"]
