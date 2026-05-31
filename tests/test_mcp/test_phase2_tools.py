"""Phase-2 MCP tools — query_recent_logs, query_metric, list_containers,
analyze_time_series_anomaly.

Mirrors the fixture/mocking style used in test_query_tools.py.  Each new
tool is tested for:
  - failure when the required dependency (collector / docker) is absent, and
  - correct wrapping when a mock dependency is present.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp.server import MCPActionServer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_log_entry(message: str = "test log", level: str = "INFO") -> MagicMock:
    entry = MagicMock()
    entry.timestamp = datetime(2026, 1, 1, 12, 0, 0)
    entry.level = level
    entry.message = message
    entry.service = "test-service"
    return entry


def _make_metric_point(name: str = "cpu_usage", value: float = 0.5) -> MagicMock:
    point = MagicMock()
    point.timestamp = datetime(2026, 1, 1, 12, 0, 0)
    point.name = name
    point.value = value
    return point


# ---------------------------------------------------------------------------
# query_recent_logs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_query_recent_logs_without_collector_returns_failure() -> None:
    server = MCPActionServer()  # no telemetry_collector
    result = await server._query_recent_logs({"service": "api-gateway"})

    assert result.success is False
    assert result.data is None
    assert "telemetry collector" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_query_recent_logs_uses_live_collector() -> None:
    log1 = _make_log_entry("Connection refused", "ERROR")
    log2 = _make_log_entry("Health check ok", "INFO")

    collector = MagicMock()
    collector.query_logs = AsyncMock(return_value=[log1, log2])

    server = MCPActionServer(telemetry_collector=collector)
    result = await server._query_recent_logs({"service": "api-gateway", "time_range_minutes": 10, "limit": 20})

    assert result.success is True
    collector.query_logs.assert_awaited_once()

    assert result.data["service"] == "api-gateway"
    assert result.data["total_entries"] == 2
    entries = result.data["entries"]
    assert len(entries) == 2
    assert entries[0]["level"] == "ERROR"
    assert entries[0]["message"] == "Connection refused"
    assert entries[1]["level"] == "INFO"


@pytest.mark.asyncio
async def test_query_recent_logs_with_query_override() -> None:
    collector = MagicMock()
    collector.query_logs = AsyncMock(return_value=[])

    server = MCPActionServer(telemetry_collector=collector)
    await server._query_recent_logs({
        "service": "all",
        "query": '{job="containerlogs"} |= "error"',
    })

    _call_kwargs = collector.query_logs.call_args.kwargs
    assert _call_kwargs.get("query") == '{job="containerlogs"} |= "error"'


# ---------------------------------------------------------------------------
# query_metric
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_query_metric_without_collector_returns_failure() -> None:
    server = MCPActionServer()  # no telemetry_collector
    result = await server._query_metric({"service": "prometheus"})

    assert result.success is False
    assert result.data is None
    assert "telemetry collector" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_query_metric_uses_live_collector() -> None:
    p1 = _make_metric_point("Targets Up", 5.0)
    p2 = _make_metric_point("Memory (MB)", 1024.0)

    collector = MagicMock()
    collector.query_metrics = AsyncMock(return_value=[p1, p2])

    server = MCPActionServer(telemetry_collector=collector)
    result = await server._query_metric({"service": "api", "time_range_minutes": 30})

    assert result.success is True
    collector.query_metrics.assert_awaited_once()

    assert result.data["service"] == "api"
    assert result.data["total_points"] == 2
    metrics = result.data["metrics"]
    assert metrics[0]["name"] == "Targets Up"
    assert metrics[0]["value"] == 5.0


@pytest.mark.asyncio
async def test_query_metric_passes_metrics_filter() -> None:
    collector = MagicMock()
    collector.query_metrics = AsyncMock(return_value=[])

    server = MCPActionServer(telemetry_collector=collector)
    await server._query_metric({"service": "api", "metrics": ["up", "go_goroutines"]})

    _call_kwargs = collector.query_metrics.call_args.kwargs
    assert _call_kwargs.get("metrics") == ["up", "go_goroutines"]


# ---------------------------------------------------------------------------
# list_containers
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_containers_docker_unavailable() -> None:
    """If docker SDK import fails, return a clear error."""
    server = MCPActionServer()

    with patch("builtins.__import__", side_effect=ImportError("no docker")):
        # Trigger through normal path — docker not available
        result = await server._list_containers({})

    # Should be failure with informative message
    assert result.success is False
    assert result.data is None


@pytest.mark.asyncio
async def test_list_containers_returns_running_containers() -> None:
    """When docker is available, returns parsed container list."""
    # Build a minimal fake container object
    fake_container = MagicMock()
    fake_container.name = "aiops-backend"
    fake_container.status = "running"
    fake_container.image.tags = ["constitutional-aiops-backend:latest"]
    fake_container.attrs = {"State": {}}  # no healthcheck

    fake_client = MagicMock()
    fake_client.containers.list.return_value = [fake_container]
    fake_client.close = MagicMock()

    fake_docker_module = MagicMock()
    fake_docker_module.from_env.return_value = fake_client

    server = MCPActionServer()

    # Patch the local `docker` name inside server.py's _list_containers.
    # We inject via sys.modules so the `import docker` inside the handler
    # resolves to our mock even on environments where the real docker SDK
    # is unavailable or shadowed by the repo's /docker directory.
    import sys
    original = sys.modules.get("docker")
    sys.modules["docker"] = fake_docker_module  # type: ignore[assignment]
    try:
        result = await server._list_containers({"all_containers": False})
    finally:
        if original is None:
            sys.modules.pop("docker", None)
        else:
            sys.modules["docker"] = original

    assert result.success is True
    assert result.data["total"] == 1
    containers = result.data["containers"]
    assert containers[0]["name"] == "aiops-backend"
    assert containers[0]["status"] == "running"
    assert containers[0]["image"] == "constitutional-aiops-backend:latest"
    # No health key on this container
    assert containers[0]["health"] is None


@pytest.mark.asyncio
async def test_list_containers_name_filter() -> None:
    c1 = MagicMock()
    c1.name = "aiops-backend"
    c1.status = "running"
    c1.image.tags = ["img:latest"]
    c1.attrs = {"State": {}}

    c2 = MagicMock()
    c2.name = "aiops-loki"
    c2.status = "running"
    c2.image.tags = ["loki:latest"]
    c2.attrs = {"State": {}}

    fake_client = MagicMock()
    fake_client.containers.list.return_value = [c1, c2]
    fake_client.close = MagicMock()

    fake_docker_module = MagicMock()
    fake_docker_module.from_env.return_value = fake_client

    server = MCPActionServer()

    import sys
    original = sys.modules.get("docker")
    sys.modules["docker"] = fake_docker_module  # type: ignore[assignment]
    try:
        result = await server._list_containers({"name_filter": "loki"})
    finally:
        if original is None:
            sys.modules.pop("docker", None)
        else:
            sys.modules["docker"] = original

    assert result.success is True
    containers = result.data["containers"]
    assert len(containers) == 1
    assert containers[0]["name"] == "aiops-loki"


# ---------------------------------------------------------------------------
# analyze_time_series_anomaly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_anomaly_without_collector_returns_failure() -> None:
    server = MCPActionServer()
    result = await server._analyze_time_series_anomaly({"service_name": "api"})

    assert result.success is False
    assert result.data is None
    assert "telemetry collector" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_anomaly_no_metrics_returns_zero_anomalies() -> None:
    collector = MagicMock()
    collector.query_metrics = AsyncMock(return_value=[])

    server = MCPActionServer(telemetry_collector=collector)
    result = await server._analyze_time_series_anomaly({"service_name": "api"})

    assert result.success is True
    assert result.data["anomalies_detected"] == 0


@pytest.mark.asyncio
async def test_anomaly_detects_zscore_outlier() -> None:
    # Values: 1.0 x10 (baseline) + one huge spike of 100.0
    baseline = [_make_metric_point("cpu", float(i % 3) + 1.0) for i in range(10)]
    spike = _make_metric_point("cpu", 100.0)
    all_points = baseline + [spike]

    collector = MagicMock()
    collector.query_metrics = AsyncMock(return_value=all_points)

    server = MCPActionServer(telemetry_collector=collector)
    result = await server._analyze_time_series_anomaly(
        {"service_name": "api", "time_range_minutes": 60}
    )

    assert result.success is True
    assert result.data["anomalies_detected"] > 0
    # The spike value should appear in the anomalies list
    anomalies = result.data["anomalies"]
    assert any(a["value"] == 100.0 for a in anomalies)
    # All anomalies have |z_score| > 2
    assert all(abs(a["z_score"]) > 2 for a in anomalies)
    assert result.data["metrics_analyzed"] == 1


@pytest.mark.asyncio
async def test_anomaly_metric_name_filter_passed_to_collector() -> None:
    collector = MagicMock()
    collector.query_metrics = AsyncMock(return_value=[])

    server = MCPActionServer(telemetry_collector=collector)
    await server._analyze_time_series_anomaly(
        {"service_name": "api", "metric_name": "memory_bytes"}
    )

    _call_kwargs = collector.query_metrics.call_args.kwargs
    assert _call_kwargs.get("metrics") == ["memory_bytes"]


# ---------------------------------------------------------------------------
# Verify tools are registered in MCPActionServer
# ---------------------------------------------------------------------------

def test_all_phase2_tools_registered() -> None:
    server = MCPActionServer()
    tool_names = set(server._tools.keys())
    for name in ("query_recent_logs", "query_metric", "list_containers", "analyze_time_series_anomaly"):
        assert name in tool_names, f"Tool '{name}' not registered"


def test_phase2_tools_risk_level_is_low() -> None:
    server = MCPActionServer()
    for name in ("query_recent_logs", "query_metric", "list_containers", "analyze_time_series_anomaly"):
        tool = server._tools[name]
        assert tool.risk_level == "low", f"{name} should have risk_level='low'"
        assert tool.requires_approval is False, f"{name} should not require approval"
