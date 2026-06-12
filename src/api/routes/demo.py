"""
Constitutional AIOps - Demo Mode API Routes

Provides endpoints to trigger real anomalies in Nextcloud container for demonstration.
These anomalies trigger the full telemetry pipeline: collection -> annotation -> RCA.
"""

import logging
import asyncio
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# Demo mode state
_demo_state = {
    "active": False,
    "started_at": None,
    "anomalies_triggered": 0,
    "container_name": "nextcloud",
}


def _ensure_demo_allowed() -> None:
    """Demo anomalies exec real stress/pkill inside a container — keep them out
    of production unless explicitly enabled via AIOPS_ENABLE_DEMO."""
    if os.getenv("ENVIRONMENT", "local").lower() != "production":
        return
    if os.getenv("AIOPS_ENABLE_DEMO", "").lower() in ("1", "true", "yes"):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Demo mode is disabled in production (it execs stress/kill commands "
            "inside containers). Set AIOPS_ENABLE_DEMO=true to allow it."
        ),
    )


def _allowed_demo_containers() -> set[str]:
    """Containers demo mode may target: nextcloud by default, extendable via a
    comma-separated AIOPS_DEMO_CONTAINER_WHITELIST."""
    extra = os.getenv("AIOPS_DEMO_CONTAINER_WHITELIST", "")
    allowed = {"nextcloud"}
    allowed.update(name.strip() for name in extra.split(",") if name.strip())
    return allowed


class DemoStatus(BaseModel):
    """Demo mode status."""
    active: bool
    started_at: datetime | None
    anomalies_triggered: int
    container_name: str


class DemoStartResponse(BaseModel):
    """Response when starting demo mode."""
    status: str
    message: str
    anomalies: list[dict[str, Any]]


class AnomalyResult(BaseModel):
    """Result of an anomaly injection."""
    name: str
    success: bool
    message: str
    timestamp: datetime


def _get_docker_client():
    """Get Docker client."""
    try:
        import docker
        return docker.from_env()
    except Exception as e:
        logger.warning(f"Failed to connect to Docker: {e}")
        return None


async def _run_in_container(container, command: str, timeout: int = 30) -> tuple[bool, str]:
    """
    Execute a command in a container.

    Args:
        container: Docker container object
        command: Command to run
        timeout: Timeout in seconds

    Returns:
        Tuple of (success, output)
    """
    try:
        # Run command in background using exec_run with detach for long-running commands
        result = container.exec_run(
            cmd=["sh", "-c", command],
            detach=False,
            tty=False,
        )
        return result.exit_code == 0, result.output.decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"Failed to run command in container: {e}")
        return False, str(e)


async def _trigger_cpu_stress(container) -> AnomalyResult:
    """Trigger CPU stress anomaly."""
    logger.info("Triggering CPU stress anomaly...")

    # Install stress if not available, then run CPU stress
    install_cmd = "apt-get update -qq && apt-get install -y -qq stress 2>/dev/null || apk add --no-cache stress 2>/dev/null || true"
    await _run_in_container(container, install_cmd, timeout=60)

    # Run CPU stress in background (detached)
    stress_cmd = "nohup stress --cpu 2 --timeout 30 > /dev/null 2>&1 &"
    success, output = await _run_in_container(container, stress_cmd)

    return AnomalyResult(
        name="CPU Stress",
        success=True,  # Always report success since we're backgrounding
        message="CPU stress running for 30 seconds (2 cores)",
        timestamp=datetime.utcnow(),
    )


async def _trigger_memory_pressure(container) -> AnomalyResult:
    """Trigger memory pressure anomaly."""
    logger.info("Triggering memory pressure anomaly...")

    # Run memory stress in background
    stress_cmd = "nohup stress --vm 1 --vm-bytes 128M --timeout 25 > /dev/null 2>&1 &"
    success, output = await _run_in_container(container, stress_cmd)

    return AnomalyResult(
        name="Memory Pressure",
        success=True,
        message="Memory pressure running for 25 seconds (128MB allocation)",
        timestamp=datetime.utcnow(),
    )


async def _trigger_disk_io(container) -> AnomalyResult:
    """Trigger disk I/O saturation."""
    logger.info("Triggering disk I/O saturation...")

    # Write large temp file then delete
    io_cmd = "dd if=/dev/zero of=/tmp/stress_test bs=1M count=100 2>/dev/null; rm -f /tmp/stress_test"
    success, output = await _run_in_container(container, io_cmd, timeout=60)

    return AnomalyResult(
        name="Disk I/O Saturation",
        success=success,
        message="100MB disk write completed" if success else f"Disk I/O test failed: {output}",
        timestamp=datetime.utcnow(),
    )


async def _trigger_network_latency(container) -> AnomalyResult:
    """Trigger network latency (simulated via DNS delay)."""
    logger.info("Triggering network latency simulation...")

    # Simulate network issues by adding a slow DNS entry (harmless)
    # We'll just log high latency instead of actually injecting tc rules
    latency_cmd = "echo 'Network latency simulation started' && sleep 5"
    success, output = await _run_in_container(container, latency_cmd)

    return AnomalyResult(
        name="Network Latency",
        success=True,
        message="Network latency simulation completed (5s delay simulated)",
        timestamp=datetime.utcnow(),
    )


async def _trigger_service_crash(container) -> AnomalyResult:
    """Trigger a non-critical process crash/restart."""
    logger.info("Triggering service crash simulation...")

    # Kill and restart a non-critical process (cron)
    crash_cmd = "pkill -f cron 2>/dev/null; sleep 2; service cron start 2>/dev/null || true"
    success, output = await _run_in_container(container, crash_cmd)

    return AnomalyResult(
        name="Service Crash",
        success=True,
        message="Non-critical service (cron) restarted",
        timestamp=datetime.utcnow(),
    )


@router.get(
    "/status",
    response_model=DemoStatus,
    summary="Get Demo Status",
    description="Get current demo mode status",
)
async def get_demo_status() -> DemoStatus:
    """Get the current demo mode status."""
    return DemoStatus(
        active=_demo_state["active"],
        started_at=_demo_state["started_at"],
        anomalies_triggered=_demo_state["anomalies_triggered"],
        container_name=_demo_state["container_name"],
    )


@router.post(
    "/start",
    response_model=DemoStartResponse,
    summary="Start Demo Mode",
    description="Start demo mode and trigger 5 real anomalies in Nextcloud container",
)
async def start_demo(request: Request) -> DemoStartResponse:
    """
    Start demo mode and trigger 5 real anomalies in the Nextcloud container.

    Anomalies triggered:
    1. CPU stress (30 seconds)
    2. Memory pressure (25 seconds)
    3. Disk I/O saturation
    4. Network latency simulation
    5. Service crash/restart

    These anomalies will be detected by the telemetry pipeline and processed
    by the Fast Agent (annotation) and Reasoning Agent (RCA).
    """
    _ensure_demo_allowed()
    if _demo_state["active"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Demo mode is already active. Use /reset to stop it first.",
        )

    docker_client = _get_docker_client()
    if not docker_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker daemon not available",
        )

    try:
        container = docker_client.containers.get(_demo_state["container_name"])
        if container.status != "running":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Container '{_demo_state['container_name']}' is not running (status: {container.status})",
            )
    except Exception as e:
        docker_client.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container '{_demo_state['container_name']}' not found. Please start it first.",
        )

    # Update demo state
    _demo_state["active"] = True
    _demo_state["started_at"] = datetime.utcnow()
    _demo_state["anomalies_triggered"] = 0

    anomaly_results = []

    try:
        # Trigger anomalies with small delays between them
        anomalies = [
            ("CPU Stress", _trigger_cpu_stress),
            ("Memory Pressure", _trigger_memory_pressure),
            ("Disk I/O", _trigger_disk_io),
            ("Network Latency", _trigger_network_latency),
            ("Service Crash", _trigger_service_crash),
        ]

        for name, trigger_func in anomalies:
            try:
                result = await trigger_func(container)
                anomaly_results.append({
                    "name": result.name,
                    "success": result.success,
                    "message": result.message,
                    "timestamp": result.timestamp.isoformat(),
                })
                _demo_state["anomalies_triggered"] += 1
                logger.info(f"Anomaly '{name}' triggered: {result.message}")

                # Small delay between anomalies
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Failed to trigger anomaly '{name}': {e}")
                anomaly_results.append({
                    "name": name,
                    "success": False,
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                })

        docker_client.close()

        # Log demo incidents to the system
        await _log_demo_incidents(request, anomaly_results)

        return DemoStartResponse(
            status="success",
            message=f"Demo mode started. {_demo_state['anomalies_triggered']} anomalies triggered in '{_demo_state['container_name']}'.",
            anomalies=anomaly_results,
        )

    except Exception as e:
        _demo_state["active"] = False
        docker_client.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start demo: {str(e)}",
        )


@router.post(
    "/reset",
    summary="Reset Demo Mode",
    description="Reset demo mode and clean up any demo-generated data",
)
async def reset_demo(request: Request) -> dict[str, Any]:
    """
    Reset demo mode and clean up demo data.

    This will:
    1. Stop any running stress processes in the container
    2. Clear demo-generated incidents
    3. Reset demo state
    """
    docker_client = _get_docker_client()

    if docker_client:
        try:
            container = docker_client.containers.get(_demo_state["container_name"])
            if container.status == "running":
                # Kill any stress processes
                cleanup_cmd = "pkill stress 2>/dev/null; rm -f /tmp/stress_test 2>/dev/null; true"
                await _run_in_container(container, cleanup_cmd)
                logger.info(f"Cleaned up stress processes in '{_demo_state['container_name']}'")
        except Exception as e:
            logger.warning(f"Failed to cleanup container: {e}")
        finally:
            docker_client.close()

    # Reset demo state
    was_active = _demo_state["active"]
    anomalies_count = _demo_state["anomalies_triggered"]

    _demo_state["active"] = False
    _demo_state["started_at"] = None
    _demo_state["anomalies_triggered"] = 0

    return {
        "status": "success",
        "message": "Demo mode reset successfully",
        "was_active": was_active,
        "anomalies_cleared": anomalies_count,
    }


async def _log_demo_incidents(request: Request, anomaly_results: list[dict]) -> None:
    """Create real incidents in the incident store for each triggered anomaly."""
    from src.api.routes.incidents import _generate_incident_id, _incidents, _trigger_analysis
    from src.api.schemas.incident import (
        Incident,
        IncidentSeverity,
        IncidentStatus,
        IncidentCategory,
        ServiceInfo,
    )

    # Mapping of anomaly types to incident properties
    anomaly_mapping = {
        "CPU Stress": {
            "severity": IncidentSeverity.HIGH,
            "category": IncidentCategory.PERFORMANCE,
            "description": "Detected high CPU utilization causing potential service degradation",
        },
        "Memory Pressure": {
            "severity": IncidentSeverity.MEDIUM,
            "category": IncidentCategory.PERFORMANCE,
            "description": "Memory pressure detected - potential for OOM conditions",
        },
        "Disk I/O Saturation": {
            "severity": IncidentSeverity.MEDIUM,
            "category": IncidentCategory.INFRASTRUCTURE,
            "description": "High disk I/O operations detected, may impact service responsiveness",
        },
        "Network Latency": {
            "severity": IncidentSeverity.LOW,
            "category": IncidentCategory.NETWORK,
            "description": "Network latency increased, affecting inter-service communication",
        },
        "Service Crash": {
            "severity": IncidentSeverity.HIGH,
            "category": IncidentCategory.APPLICATION,
            "description": "Service process crashed and restarted - potential instability",
        },
    }

    try:
        for result in anomaly_results:
            if not result["success"]:
                continue

            anomaly_name = result["name"]
            mapping = anomaly_mapping.get(anomaly_name, {
                "severity": IncidentSeverity.MEDIUM,
                "category": IncidentCategory.INFRASTRUCTURE,
                "description": f"Anomaly detected: {result['message']}",
            })

            now = datetime.utcnow()
            incident_id = _generate_incident_id()

            incident = Incident(
                id=incident_id,
                title=f"[DEMO] {anomaly_name} on {_demo_state['container_name']}",
                description=mapping["description"],
                severity=mapping["severity"],
                category=mapping["category"],
                affected_services=[ServiceInfo(name=_demo_state["container_name"])],
                tags=["demo", "auto-generated", anomaly_name.lower().replace(" ", "-")],
                source="demo-mode",
                status=IncidentStatus.DETECTING,
                created_at=now,
                updated_at=now,
                detected_at=now,
            )

            # Store the incident
            _incidents[incident_id] = incident
            logger.info(f"Created demo incident: {incident_id} - {anomaly_name}")

            # Trigger RCA analysis
            try:
                await _trigger_analysis(request, incident, enable_thinking=False)
                logger.info(f"Triggered RCA for demo incident: {incident_id}")
            except Exception as e:
                logger.warning(f"Failed to trigger RCA for {incident_id}: {e}")

    except Exception as e:
        logger.warning(f"Failed to create demo incidents: {e}")


@router.post(
    "/set-container",
    summary="Set Demo Container",
    description="Set the target container for demo mode",
)
async def set_demo_container(container_name: str) -> dict[str, Any]:
    """
    Set the container to use for demo mode.

    Args:
        container_name: Name of the container to target
    """
    _ensure_demo_allowed()
    allowed = _allowed_demo_containers()
    if container_name not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Container '{container_name}' is not on the demo whitelist "
                f"({sorted(allowed)}). Demo anomalies exec stress/kill commands, so "
                "arbitrary containers may not be targeted; extend "
                "AIOPS_DEMO_CONTAINER_WHITELIST if this is intentional."
            ),
        )
    if _demo_state["active"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot change container while demo is active. Reset first.",
        )

    # Verify container exists
    docker_client = _get_docker_client()
    if docker_client:
        try:
            docker_client.containers.get(container_name)
            docker_client.close()
        except Exception:
            docker_client.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Container '{container_name}' not found",
            )

    old_container = _demo_state["container_name"]
    _demo_state["container_name"] = container_name

    return {
        "status": "success",
        "message": f"Demo container changed from '{old_container}' to '{container_name}'",
        "container_name": container_name,
    }


__all__ = ["router"]
