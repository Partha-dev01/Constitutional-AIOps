"""
Constitutional AIOps - Docker-socket log source.

A fallback telemetry source for deployments with no LGTM/Loki stack (e.g. the
lite tier, or any self-host without observability wired up yet). Reads recent
logs from the containers on the host's Docker socket so the background System-1
scanner has REAL telemetry to annotate instead of an empty window.

Fully self-contained and best-effort: any failure (no docker SDK, no socket,
permission denied, a container that refuses logs()) yields the logs gathered so
far, never an exception. TelemetryCollector calls this via asyncio.to_thread
because the Docker SDK is blocking.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from src.telemetry.collector import LogEntry, MetricPoint, _parse_log_level

logger = logging.getLogger(__name__)


def _to_epoch(dt: datetime) -> int:
    """Naive datetimes here are UTC (datetime.utcnow); pass epoch seconds to the
    Docker SDK to avoid its naive-datetime local-time assumption."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _parse_docker_ts(ts_str: str) -> datetime:
    """Parse a Docker ``timestamps=True`` RFC3339Nano prefix, e.g.
    ``2026-09-01T12:34:56.789012345Z``. Python's fromisoformat rejects a 9-digit
    nanosecond fraction, so trim it to microseconds. Falls back to now (UTC)."""
    try:
        s = ts_str.replace("Z", "+00:00")
        if "." in s:
            head, rest = s.split(".", 1)
            tz = ""
            for sep in ("+", "-"):
                idx = rest.find(sep)
                if idx != -1:
                    tz = rest[idx:]
                    rest = rest[:idx]
                    break
            s = f"{head}.{rest[:6]}{tz}"
        return datetime.fromisoformat(s)
    except Exception:  # noqa: BLE001 - best-effort timestamp parse
        return datetime.now(timezone.utc)


def collect_container_logs(
    since: datetime,
    until: datetime,
    service: Optional[str] = None,
    per_container_tail: int = 100,
    max_total: int = 500,
) -> list[LogEntry]:
    """Collect recent container logs as LogEntry objects. Never raises.

    Args:
        since / until: window bounds (naive -> treated as UTC).
        service: optional case-insensitive substring filter on container name
            ("all"/None = every running container).
        per_container_tail: max lines read per container.
        max_total: hard cap on returned entries.
    """
    try:
        import docker  # type: ignore[import]
    except Exception:  # noqa: BLE001 - SDK not installed (e.g. dev box)
        return []

    try:
        client = docker.from_env()
    except Exception as e:  # noqa: BLE001 - no reachable socket
        logger.debug("Docker socket unavailable for log source: %s", e)
        return []

    since_epoch = _to_epoch(since)
    until_epoch = _to_epoch(until)
    want = (service or "").strip().lower()
    logs: list[LogEntry] = []

    try:
        containers = client.containers.list()  # running containers only
        for container in containers:
            if len(logs) >= max_total:
                break
            name = getattr(container, "name", "") or ""
            if want and want != "all" and want not in name.lower():
                continue
            try:
                raw = container.logs(
                    since=since_epoch,
                    until=until_epoch,
                    timestamps=True,
                    tail=per_container_tail,
                    stream=False,
                )
            except Exception:  # noqa: BLE001 - one bad container must not abort
                continue
            text = (
                raw.decode("utf-8", errors="ignore")
                if isinstance(raw, (bytes, bytearray))
                else str(raw)
            )
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Docker timestamps=True emits "<rfc3339nano> <message>".
                ts_str, _, message = line.partition(" ")
                if not message:
                    ts_str, message = "", line
                labels = {"container": name}
                logs.append(LogEntry(
                    timestamp=_parse_docker_ts(ts_str) if ts_str else datetime.now(timezone.utc),
                    level=_parse_log_level(labels, message),
                    message=message,
                    service=name,
                    labels=labels,
                ))
                if len(logs) >= max_total:
                    break
    except Exception as e:  # noqa: BLE001 - return whatever we gathered
        logger.debug("Docker log collection error: %s", e)
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass

    return logs


# ---------------------------------------------------------------------------
# Container resource stats (the metrics half of the Docker fallback source)
# ---------------------------------------------------------------------------
#
# `container.stats(stream=False)` returns ONE current-stats dict that already
# includes `precpu_stats`, so CPU% is computable from a single call using the
# same formula the `docker stats` CLI uses. Everything here is best-effort and
# never raises: a missing field or an odd cgroup layout yields fewer points, not
# an exception.


def _display_name(name: str) -> str:
    """Human label for a container: drop the platform `aiops-` prefix so tiles
    read `backend` / `frontend`, not `aiops-backend`. The raw name is kept in
    the point labels for grouping."""
    return name[6:] if name.startswith("aiops-") else name


def _compute_cpu_percent(stats: dict) -> Optional[float]:
    """CPU% from one stats sample, per the docker-stats formula:
    (cpu_delta / system_delta) * online_cpus * 100. None when the sample lacks
    the fields needed (e.g. the very first sample after start)."""
    try:
        cpu = stats.get("cpu_stats") or {}
        precpu = stats.get("precpu_stats") or {}
        cpu_total = (cpu.get("cpu_usage") or {}).get("total_usage")
        precpu_total = (precpu.get("cpu_usage") or {}).get("total_usage")
        system = cpu.get("system_cpu_usage")
        presystem = precpu.get("system_cpu_usage")
        if cpu_total is None or precpu_total is None or system is None or presystem is None:
            return None
        cpu_delta = cpu_total - precpu_total
        system_delta = system - presystem
        online = cpu.get("online_cpus")
        if not online:
            percpu = (cpu.get("cpu_usage") or {}).get("percpu_usage") or []
            online = len(percpu) or 1
        if system_delta > 0 and cpu_delta >= 0:
            return (cpu_delta / system_delta) * online * 100.0
        return 0.0
    except Exception:  # noqa: BLE001 - a bad sample yields no point, never raises
        return None


def _compute_mem(stats: dict) -> tuple[Optional[float], Optional[float]]:
    """(mem_percent, mem_mb) from one sample. Mirrors `docker stats`: subtract
    the reclaimable page cache (cgroup v2 `inactive_file`, v1 `cache`/
    `total_inactive_file`) from usage so the figure reflects real working set."""
    try:
        mem = stats.get("memory_stats") or {}
        usage = mem.get("usage")
        limit = mem.get("limit")
        if usage is None:
            return None, None
        detail = mem.get("stats") or {}
        inactive = (
            detail.get("inactive_file")
            or detail.get("total_inactive_file")
            or detail.get("cache")
            or 0
        )
        used = usage - inactive
        if used < 0:
            used = usage
        mem_mb = used / (1024 * 1024)
        mem_pct = (used / limit * 100.0) if limit else None
        return mem_pct, mem_mb
    except Exception:  # noqa: BLE001
        return None, None


def collect_container_stats(
    service: Optional[str] = None,
    max_containers: int = 40,
) -> list[MetricPoint]:
    """Collect per-container CPU% / mem% / mem-MB as MetricPoints. Never raises.

    One MetricPoint per (container, metric); `name` is a human tile label and
    `labels` carries the raw ``container`` name plus a stable ``metric`` key
    (``cpu_percent`` / ``mem_percent`` / ``mem_mb``) so the caller can group by
    service without parsing the label. ``service`` filters containers by
    case-insensitive substring ("all"/None = every running container).
    """
    try:
        import docker  # type: ignore[import]
    except Exception:  # noqa: BLE001 - SDK not installed
        return []

    try:
        client = docker.from_env()
    except Exception as e:  # noqa: BLE001 - no reachable socket
        logger.debug("Docker socket unavailable for stats source: %s", e)
        return []

    want = (service or "").strip().lower()
    now = datetime.now(timezone.utc)
    points: list[MetricPoint] = []

    try:
        containers = client.containers.list()  # running only
        for container in containers[:max_containers]:
            name = getattr(container, "name", "") or ""
            if want and want != "all" and want not in name.lower():
                continue
            try:
                stats = container.stats(stream=False)
            except Exception:  # noqa: BLE001 - one bad container must not abort
                continue
            if not isinstance(stats, dict):
                continue
            display = _display_name(name)
            cpu_pct = _compute_cpu_percent(stats)
            mem_pct, mem_mb = _compute_mem(stats)
            if cpu_pct is not None:
                points.append(MetricPoint(
                    timestamp=now, name=f"{display} CPU %", value=round(cpu_pct, 2),
                    labels={"container": name, "metric": "cpu_percent"},
                ))
            if mem_pct is not None:
                points.append(MetricPoint(
                    timestamp=now, name=f"{display} Mem %", value=round(mem_pct, 2),
                    labels={"container": name, "metric": "mem_percent"},
                ))
            if mem_mb is not None:
                points.append(MetricPoint(
                    timestamp=now, name=f"{display} Mem MB", value=round(mem_mb, 1),
                    labels={"container": name, "metric": "mem_mb"},
                ))
    except Exception as e:  # noqa: BLE001 - return whatever we gathered
        logger.debug("Docker stats collection error: %s", e)
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass

    return points


def docker_socket_status() -> dict:
    """Report whether the local Docker socket is reachable and how many
    containers are running. ``{"available": bool, "containers": int}``. Never
    raises — used by Settings/Quick-Setup to live-test the source."""
    try:
        import docker  # type: ignore[import]
    except Exception:  # noqa: BLE001
        return {"available": False, "containers": 0}

    client = None
    try:
        client = docker.from_env()
        containers = client.containers.list()
        return {"available": True, "containers": len(containers)}
    except Exception as e:  # noqa: BLE001 - unreachable socket / perm denied
        logger.debug("Docker socket status check failed: %s", e)
        return {"available": False, "containers": 0}
    finally:
        try:
            if client is not None:
                client.close()
        except Exception:  # noqa: BLE001
            pass


__all__ = [
    "collect_container_logs",
    "collect_container_stats",
    "docker_socket_status",
]
