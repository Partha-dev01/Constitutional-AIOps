"""Tests for the Docker-socket fallback log source (src/telemetry/docker_source)."""

import sys
import types
from datetime import datetime, timezone

from src.telemetry.docker_source import collect_container_logs, _parse_docker_ts

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
