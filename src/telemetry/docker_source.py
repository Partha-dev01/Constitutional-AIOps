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

from src.telemetry.collector import LogEntry, _parse_log_level

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


__all__ = ["collect_container_logs"]
