"""Route tests for the Docker-socket telemetry fallback (WS-A / WS-B).

Direct route-fn calls with ``SimpleNamespace`` mock requests (never import
``src.main`` — langgraph is not installed in CI). Verifies that
``/telemetry/logs`` and ``/telemetry/metrics`` fall back to the local Docker
source when no LGTM collector/data is present AND the source is enabled, that a
custom PromQL query skips the (Docker-less) fallback, that disabling the source
suppresses it, and that ``/settings/monitoring/test`` can probe the socket.
"""

from datetime import datetime, timezone
from types import SimpleNamespace

import src.api.routes.settings as settings_mod
import src.api.routes.telemetry as telemetry_mod
import src.telemetry.docker_source as docker_source
from src.telemetry.collector import LogEntry, MetricPoint


def _request(collector=None):
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(telemetry_collector=collector))
    )


# ── /telemetry/logs fallback ────────────────────────────────────────────────

async def test_logs_fall_back_to_docker_when_no_collector(monkeypatch):
    monkeypatch.setattr(telemetry_mod, "_docker_source_enabled", lambda: True)
    sentinel = [LogEntry(
        timestamp=datetime.now(timezone.utc), level="ERROR", message="boom",
        service="aiops-backend", labels={"container": "aiops-backend"},
    )]
    monkeypatch.setattr(docker_source, "collect_container_logs", lambda **kw: sentinel)
    # Pass Query-defaulted params explicitly (a direct call bypasses FastAPI's
    # dependency resolution, so unpassed Query(...) defaults stay Query objects).
    resp = await telemetry_mod.get_logs(
        _request(collector=None), limit=50, level=None, service=None,
        query=None, since_minutes=60,
    )
    assert resp.source == "docker"
    assert resp.total == 1
    assert resp.logs[0].service == "aiops-backend"


async def test_logs_docker_disabled_returns_empty(monkeypatch):
    monkeypatch.setattr(telemetry_mod, "_docker_source_enabled", lambda: False)
    called = {"n": 0}

    def _should_not_be_called(**kw):
        called["n"] += 1
        return []

    monkeypatch.setattr(docker_source, "collect_container_logs", _should_not_be_called)
    resp = await telemetry_mod.get_logs(
        _request(collector=None), limit=50, level=None, service=None,
        query=None, since_minutes=60,
    )
    assert resp.source == "none"
    assert resp.total == 0
    assert called["n"] == 0  # disabled => the socket is never touched


# ── /telemetry/metrics fallback ─────────────────────────────────────────────

async def test_metrics_fall_back_to_docker(monkeypatch):
    monkeypatch.setattr(telemetry_mod, "_docker_source_enabled", lambda: True)
    pts = [MetricPoint(
        timestamp=datetime.now(timezone.utc), name="backend CPU %", value=12.5,
        labels={"container": "aiops-backend", "metric": "cpu_percent"},
    )]
    monkeypatch.setattr(docker_source, "collect_container_stats", lambda **kw: pts)
    resp = await telemetry_mod.get_metrics(
        _request(collector=None), range="1h", step="1m", query=None,
        metric=None, service=None,
    )
    assert resp.source == "docker"
    assert resp.metrics[0].service == "aiops-backend"
    assert resp.metrics[0].metric == "cpu_percent"
    assert resp.metrics[0].value == 12.5


async def test_metrics_custom_query_skips_docker_fallback(monkeypatch):
    # A raw PromQL query has no Docker equivalent -> no fallback, source "none".
    monkeypatch.setattr(telemetry_mod, "_docker_source_enabled", lambda: True)

    def _must_not_run(**kw):
        raise AssertionError("collect_container_stats must not run for a PromQL query")

    monkeypatch.setattr(docker_source, "collect_container_stats", _must_not_run)
    resp = await telemetry_mod.get_metrics(
        _request(collector=None), range="1h", step="1m", query="up",
        metric=None, service=None,
    )
    assert resp.source == "none"
    assert resp.metrics == []


# ── /settings/monitoring/test docker probe ──────────────────────────────────

async def test_monitoring_test_docker_probe_reachable(monkeypatch):
    monkeypatch.setattr(
        docker_source, "docker_socket_status",
        lambda: {"available": True, "containers": 3},
    )
    resp = await settings_mod.test_monitoring(
        settings_mod.MonitoringTestRequest(docker=True)
    )
    assert resp.docker is not None and resp.docker.ok is True
    assert "3 container" in resp.docker.detail


async def test_monitoring_test_docker_probe_unreachable(monkeypatch):
    monkeypatch.setattr(
        docker_source, "docker_socket_status",
        lambda: {"available": False, "containers": 0},
    )
    resp = await settings_mod.test_monitoring(
        settings_mod.MonitoringTestRequest(docker=True)
    )
    assert resp.docker is not None and resp.docker.ok is False


async def test_monitoring_test_docker_not_requested_stays_none():
    resp = await settings_mod.test_monitoring(settings_mod.MonitoringTestRequest())
    assert resp.docker is None
