"""
Constitutional AIOps - Infrastructure API Routes

Provides endpoints for infrastructure/container status with dynamic Docker discovery.
"""

import logging
from typing import Any
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

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
    """Get Docker client, handling different environments."""
    try:
        import docker
        return docker.from_env()
    except Exception as e:
        logger.warning(f"Failed to connect to Docker: {e}")
        return None


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

    Uses Docker SDK to get real-time container status.
    """
    containers: list[ContainerInfo] = []
    healthy_count = 0
    unhealthy_count = 0

    docker_client = _get_docker_client()

    if docker_client:
        try:
            all_containers = docker_client.containers.list(all=True)

            for container in all_containers:
                name = container.name
                if name not in _monitored_containers:
                    continue

                # Get container details
                status = container.status  # running, exited, paused, restarting
                health = None
                health_state = container.attrs.get("State", {}).get("Health", {})
                if health_state:
                    health = health_state.get("Status", "unknown")

                # Get image and ports
                image = container.image.tags[0] if container.image.tags else str(container.image.id)[:12]
                ports = _format_ports(container.ports)

                # Determine service name
                service = name.replace("aiops-", "") if name.startswith("aiops-") else name

                # Count health
                if status == "running":
                    if health in ("healthy", None):
                        healthy_count += 1
                    else:
                        unhealthy_count += 1
                else:
                    unhealthy_count += 1

                containers.append(ContainerInfo(
                    name=name,
                    service=service,
                    status=status,
                    health=health,
                    port=ports,
                    image=image,
                    description=_get_container_description(service),
                    monitored=True,
                ))

            docker_client.close()

        except Exception as e:
            logger.error(f"Failed to get container status: {e}")
            # Fall back to static list if Docker fails
            return _get_static_containers(request)
    else:
        # Fall back to static list
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

    Returns all containers regardless of monitoring status.
    """
    docker_client = _get_docker_client()

    if not docker_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker daemon not available",
        )

    try:
        all_containers = docker_client.containers.list(all=True)
        discovered = []

        for container in all_containers:
            name = container.name
            image = container.image.tags[0] if container.image.tags else str(container.image.id)[:12]
            ports = _format_ports(container.ports)
            created = container.attrs.get("Created", "")[:19] if container.attrs.get("Created") else None

            discovered.append(DiscoveredContainer(
                name=name,
                image=image,
                status=container.status,
                ports=ports,
                created=created,
                monitored=name in _monitored_containers,
            ))

        docker_client.close()

        return DiscoveryResponse(
            containers=sorted(discovered, key=lambda c: c.name),
            total=len(discovered),
        )

    except Exception as e:
        logger.error(f"Failed to discover containers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover containers: {str(e)}",
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

    # Verify container exists
    docker_client = _get_docker_client()
    if docker_client:
        try:
            docker_client.containers.get(container_name)
            docker_client.close()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Container '{container_name}' not found",
            )
    else:
        # If Docker not available, still add to list
        pass

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
    added = []
    not_found = []
    logs_collected = 0

    docker_client = _get_docker_client()
    fast_annotator = getattr(request.app.state, "fast_annotator", None)

    for container_name in request_body.containers:
        # Verify container exists if Docker is available
        if docker_client:
            try:
                container = docker_client.containers.get(container_name)

                # Collect recent logs from the container
                if fast_annotator:
                    try:
                        # Get last 50 log lines from container
                        logs = container.logs(tail=50, timestamps=True).decode('utf-8', errors='ignore')
                        log_lines = logs.strip().split('\n')

                        for log_line in log_lines[-20:]:  # Process last 20 lines
                            if log_line.strip():
                                # Process log through Fast Agent
                                await _process_container_log(
                                    fast_annotator,
                                    container_name,
                                    log_line,
                                )
                                logs_collected += 1

                    except Exception as e:
                        logger.warning(f"Failed to collect logs from {container_name}: {e}")

            except Exception:
                not_found.append(container_name)
                continue

        _monitored_containers.add(container_name)
        added.append(container_name)
        logger.info(f"Added container to monitoring: {container_name}")

    if docker_client:
        docker_client.close()

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


__all__ = ["router"]
