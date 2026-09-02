"""Tests for the Docker-socket fallback log source (src/telemetry/docker_source)."""

import sys
import types
from datetime import datetime, timezone

from src.telemetry.docker_source import (
    _compute_cpu_percent,
    _compute_mem,
    collect_container_logs,
    collect_container_stats,
    docker_socket_status,
    _parse_docker_ts,
)

_SINCE = datetime(2026, 9, 1, 12, 0, 0)
_UNTIL = datetime(2026, 9, 1, 13, 0, 0)


class _FakeContainer:
    def __init__(self, name, log_bytes, raise_logs=False):
        self.name = name
        self._log_bytes = log_bytes
        self._raise = raise_logs

    def logs(self, **kwargs):  # noqa: D401 - mimic docker SDK
        if self._raise:
            raise RuntimeError("boom")
        return self._log_bytes


def _fake_docker(containers):
    """A stand-in `docker` module whose from_env() returns a fake client."""
    client = types.SimpleNamespace(
        containers=types.SimpleNamespace(list=lambda **kw: containers),
        close=lambda: None,
    )
    return types.SimpleNamespace(from_env=lambda: client)


def test_parse_docker_ts_nanoseconds():
    dt = _parse_docker_ts("2026-09-01T12:34:56.789012345Z")
    assert (dt.year, dt.month, dt.day) == (2026, 9, 1)
    assert dt.tzinfo is not None


def test_parse_docker_ts_bad_input_falls_back():
    dt = _parse_docker_ts("not-a-timestamp")
    assert isinstance(dt, datetime)


def test_collect_parses_lines(monkeypatch):
    logline = (
        b"2026-09-01T12:34:56.789012345Z ERROR something bad happened\n"
        b"2026-09-01T12:34:57.000000000Z INFO all good\n"
    )
    monkeypatch.setitem(sys.modules, "docker", _fake_docker([_FakeContainer("aiops-backend", logline)]))
    out = collect_container_logs(_SINCE, _UNTIL)
    assert len(out) == 2
    assert out[0].service == "aiops-backend"
    assert out[0].level == "ERROR"
    assert out[0].labels["container"] == "aiops-backend"
    assert "something bad happened" in out[0].message
    assert out[1].level == "INFO"


def test_service_filter(monkeypatch):
    monkeypatch.setitem(sys.modules, "docker", _fake_docker([
        _FakeContainer("aiops-backend", b"2026-09-01T12:34:56Z INFO x\n"),
        _FakeContainer("aiops-caddy", b"2026-09-01T12:34:56Z INFO y\n"),
    ]))
    out = collect_container_logs(_SINCE, _UNTIL, service="caddy")
    assert len(out) == 1
    assert out[0].service == "aiops-caddy"


def test_max_total_cap(monkeypatch):
    many = b"\n".join(b"2026-09-01T12:34:56Z INFO line" for _ in range(50)) + b"\n"
    monkeypatch.setitem(sys.modules, "docker", _fake_docker([
        _FakeContainer("c1", many), _FakeContainer("c2", many),
    ]))
    out = collect_container_logs(_SINCE, _UNTIL, max_total=30)
    assert len(out) == 30


def test_logs_error_never_raises(monkeypatch):
    monkeypatch.setitem(sys.modules, "docker", _fake_docker([_FakeContainer("c1", b"", raise_logs=True)]))
    assert collect_container_logs(_SINCE, _UNTIL) == []


def test_no_reachable_socket_returns_empty(monkeypatch):
    def _boom():
        raise RuntimeError("no socket")
    monkeypatch.setitem(sys.modules, "docker", types.SimpleNamespace(from_env=_boom))
    assert collect_container_logs(_SINCE, _UNTIL) == []


# ---------------------------------------------------------------------------
# Container stats (the metrics half of the Docker fallback source)
# ---------------------------------------------------------------------------

_STATS = {
    "cpu_stats": {"cpu_usage": {"total_usage": 200}, "system_cpu_usage": 2000, "online_cpus": 2},
    "precpu_stats": {"cpu_usage": {"total_usage": 100}, "system_cpu_usage": 1000},
    "memory_stats": {
        "usage": 200 * 1024 * 1024,
        "limit": 1000 * 1024 * 1024,
        "stats": {"inactive_file": 50 * 1024 * 1024},
    },
}


class _FakeStatsContainer:
    def __init__(self, name, stats, raise_stats=False):
        self.name = name
        self._stats = stats
        self._raise = raise_stats

    def stats(self, **kwargs):  # noqa: D401 - mimic docker SDK
        if self._raise:
            raise RuntimeError("boom")
        return self._stats


def test_compute_cpu_percent():
    # cpu_delta=100, system_delta=1000, online=2 -> (100/1000)*2*100 = 20.0
    assert _compute_cpu_percent(_STATS) == 20.0


def test_compute_cpu_percent_first_sample_none():
    # No precpu data (first sample after start) -> not computable.
    assert _compute_cpu_percent({"cpu_stats": {}, "precpu_stats": {}}) is None


def test_compute_mem_subtracts_inactive_file():
    # used = (200 - 50)MB; pct = 150/1000*100 = 15.0; mb = 150.0
    mem_pct, mem_mb = _compute_mem(_STATS)
    assert mem_pct == 15.0
    assert mem_mb == 150.0


def test_collect_container_stats_emits_points(monkeypatch):
    monkeypatch.setitem(sys.modules, "docker", _fake_docker([
        _FakeStatsContainer("aiops-backend", _STATS),
    ]))
    points = collect_container_stats()
    by_metric = {p.labels["metric"]: p for p in points}
    assert by_metric["cpu_percent"].value == 20.0
    assert by_metric["cpu_percent"].name == "backend CPU %"  # aiops- prefix stripped
    assert by_metric["cpu_percent"].labels["container"] == "aiops-backend"
    assert by_metric["mem_percent"].value == 15.0
    assert by_metric["mem_mb"].value == 150.0


def test_collect_container_stats_service_filter(monkeypatch):
    monkeypatch.setitem(sys.modules, "docker", _fake_docker([
        _FakeStatsContainer("aiops-backend", _STATS),
        _FakeStatsContainer("aiops-caddy", _STATS),
    ]))
    points = collect_container_stats(service="caddy")
    assert {p.labels["container"] for p in points} == {"aiops-caddy"}


def test_collect_container_stats_bad_container_never_raises(monkeypatch):
    monkeypatch.setitem(sys.modules, "docker", _fake_docker([
        _FakeStatsContainer("c1", _STATS, raise_stats=True),
        _FakeStatsContainer("aiops-backend", _STATS),
    ]))
    points = collect_container_stats()
    # The raising container is skipped; the good one still yields points.
    assert {p.labels["container"] for p in points} == {"aiops-backend"}


def test_collect_container_stats_no_socket_returns_empty(monkeypatch):
    def _boom():
        raise RuntimeError("no socket")
    monkeypatch.setitem(sys.modules, "docker", types.SimpleNamespace(from_env=_boom))
    assert collect_container_stats() == []


def test_docker_socket_status_available(monkeypatch):
    monkeypatch.setitem(sys.modules, "docker", _fake_docker([
        _FakeStatsContainer("c1", _STATS), _FakeStatsContainer("c2", _STATS),
    ]))
    assert docker_socket_status() == {"available": True, "containers": 2}


def test_docker_socket_status_unreachable(monkeypatch):
    def _boom():
        raise RuntimeError("no socket")
    monkeypatch.setitem(sys.modules, "docker", types.SimpleNamespace(from_env=_boom))
    assert docker_socket_status() == {"available": False, "containers": 0}


def test_collect_window_falls_back_to_docker_when_loki_empty(monkeypatch):
    """When Loki yields no logs, collect_window must use the Docker fallback."""
    import asyncio

    from src.telemetry.collector import LogEntry, TelemetryCollector

    tc = TelemetryCollector(loki_url="http://x", prometheus_url="http://x", tempo_url="http://x")
    sentinel = [LogEntry(timestamp=datetime.now(timezone.utc), level="INFO", message="m", service="s")]

    async def _empty(**kwargs):
        return []

    async def _fallback(**kwargs):
        return sentinel

    monkeypatch.setattr(tc, "query_logs", _empty)
    monkeypatch.setattr(tc, "query_metrics", _empty)
    monkeypatch.setattr(tc, "query_traces", _empty)
    monkeypatch.setattr(tc, "_collect_docker_logs", _fallback)

    window = asyncio.run(tc.collect_window(service="all", duration_minutes=5))
    assert window.logs == sentinel
