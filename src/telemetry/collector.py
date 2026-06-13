"""
Constitutional AIOps - Telemetry Collector

Collects telemetry data from LGTM stack (Loki, Grafana, Tempo, Mimir/Prometheus).
Provides unified interface for accessing logs, metrics, and traces.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from src.config import config

logger = logging.getLogger(__name__)

# Regex to extract log level from common log-line formats.
# Examples: "ERROR [api] ...", "2025-01-01 WARN ...", "[WARNING] ...", "level=debug ..."
_LEVEL_RE = re.compile(
    r'\b(ERROR|FATAL|CRITICAL|WARN(?:ING)?|DEBUG|INFO)\b',
    re.IGNORECASE,
)

_LEVEL_NORMALISE: dict[str, str] = {
    "fatal": "ERROR",
    "critical": "ERROR",
    "warning": "WARN",
    "warn": "WARN",
    "error": "ERROR",
    "debug": "DEBUG",
    "info": "INFO",
}

# Characters allowed when interpolating a caller-supplied value (service name,
# level, …) inside a LogQL selector / regex literal. Everything else — quotes,
# braces, backslashes, regex metacharacters — is stripped so the value can
# never break out of the selector it is embedded in.
_LOGQL_UNSAFE = re.compile(r"[^a-zA-Z0-9_\-./: ]")


def logql_escape(value: str) -> str:
    """Sanitize a value for safe interpolation into a LogQL query string."""
    return _LOGQL_UNSAFE.sub("", value or "")


def _parse_log_level(stream_labels: dict[str, str], message: str) -> str:
    """
    Determine the log level for a Loki log entry.

    Strategy (in priority order):
    1. Use the ``level`` stream label if present and not the default ``"info"``
       placeholder that promtail emits when it cannot detect a level.
    2. Regex-scan the log message for a case-insensitive level keyword.
    3. Fall back to ``"INFO"``.

    Returns the level as uppercase, normalised to one of: INFO, WARN, ERROR, DEBUG.
    """
    raw = stream_labels.get("level", "")
    # Trust the label when it's something other than the generic "info" default
    # or when the label is explicitly set by a structured logger.
    detected_level = raw.strip().lower()
    if detected_level and detected_level != "info":
        return _LEVEL_NORMALISE.get(detected_level, detected_level.upper())

    # Try to extract from the message body.
    m = _LEVEL_RE.search(message)
    if m:
        return _LEVEL_NORMALISE.get(m.group(1).lower(), m.group(1).upper())

    # If the label explicitly said "info" (structured logger), honour it.
    if detected_level == "info":
        return "INFO"

    return "INFO"


@dataclass
class LogEntry:
    """Single log entry."""
    timestamp: datetime
    level: str
    message: str
    service: str
    labels: dict[str, str] = field(default_factory=dict)
    trace_id: Optional[str] = None


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: datetime
    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class TraceSpan:
    """Single trace span."""
    trace_id: str
    span_id: str
    operation: str
    service: str
    duration_ms: float
    status: str
    start_time: datetime
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class TelemetryWindow:
    """
    A window of telemetry data.

    Contains logs, metrics, and traces for a specific time range.
    """
    start_time: datetime
    end_time: datetime
    logs: list[LogEntry] = field(default_factory=list)
    metrics: list[MetricPoint] = field(default_factory=list)
    traces: list[TraceSpan] = field(default_factory=list)

    @property
    def duration_minutes(self) -> float:
        """Get window duration in minutes."""
        return (self.end_time - self.start_time).total_seconds() / 60

    @property
    def log_count(self) -> int:
        return len(self.logs)

    @property
    def error_count(self) -> int:
        return sum(1 for log in self.logs if log.level.lower() in ("error", "fatal", "critical"))

    @property
    def warning_count(self) -> int:
        return sum(1 for log in self.logs if log.level.lower() in ("warn", "warning"))


class TelemetryCollector:
    """
    Collects telemetry from observability stack.

    Supports:
    - Loki for logs
    - Prometheus/Mimir for metrics
    - Tempo for traces
    """

    def __init__(
        self,
        loki_url: Optional[str] = None,
        prometheus_url: Optional[str] = None,
        tempo_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize telemetry collector.

        Args:
            loki_url: Loki API URL
            prometheus_url: Prometheus API URL
            tempo_url: Tempo API URL
            timeout: HTTP request timeout
        """
        self.loki_url = loki_url or config.observability.loki_url
        self.prometheus_url = prometheus_url or config.observability.prometheus_url
        self.tempo_url = tempo_url or config.observability.tempo_url
        self.timeout = timeout

        self._client = httpx.AsyncClient(timeout=timeout)

        logger.info(f"TelemetryCollector initialized")
        logger.info(f"  Loki: {self.loki_url}")
        logger.info(f"  Prometheus: {self.prometheus_url}")
        logger.info(f"  Tempo: {self.tempo_url}")

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()

    async def health_check(self) -> dict[str, bool]:
        """
        Check health of all telemetry backends.

        Returns:
            Dictionary with health status
        """
        health = {
            "loki": False,
            "prometheus": False,
            "tempo": False,
        }

        # Check Loki
        try:
            response = await self._client.get(f"{self.loki_url}/ready")
            health["loki"] = response.status_code == 200
        except Exception as e:
            logger.debug(f"Loki health check failed: {e}")

        # Check Prometheus
        try:
            response = await self._client.get(f"{self.prometheus_url}/-/ready")
            health["prometheus"] = response.status_code == 200
        except Exception as e:
            logger.debug(f"Prometheus health check failed: {e}")

        # Check Tempo
        try:
            response = await self._client.get(f"{self.tempo_url}/ready")
            health["tempo"] = response.status_code == 200
        except Exception as e:
            logger.debug(f"Tempo health check failed: {e}")

        return health

    async def collect_window(
        self,
        service: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        duration_minutes: int = 15,
    ) -> TelemetryWindow:
        """
        Collect telemetry for a time window.

        Args:
            service: Service name to collect for
            start_time: Window start (default: duration_minutes ago)
            end_time: Window end (default: now)
            duration_minutes: Duration if start_time not specified

        Returns:
            TelemetryWindow with collected data
        """
        if end_time is None:
            end_time = datetime.utcnow()
        if start_time is None:
            start_time = end_time - timedelta(minutes=duration_minutes)

        window = TelemetryWindow(start_time=start_time, end_time=end_time)

        # Collect logs
        try:
            window.logs = await self.query_logs(
                service=service,
                start_time=start_time,
                end_time=end_time,
            )
        except Exception as e:
            logger.warning(f"Failed to collect logs: {e}")

        # Collect metrics
        try:
            window.metrics = await self.query_metrics(
                service=service,
                start_time=start_time,
                end_time=end_time,
            )
        except Exception as e:
            logger.warning(f"Failed to collect metrics: {e}")

        # Collect traces
        try:
            window.traces = await self.query_traces(
                service=service,
                start_time=start_time,
                end_time=end_time,
            )
        except Exception as e:
            logger.warning(f"Failed to collect traces: {e}")

        logger.info(
            f"Collected telemetry for {service}: "
            f"{window.log_count} logs, {len(window.metrics)} metrics, {len(window.traces)} traces"
        )

        return window

    async def query_logs(
        self,
        service: str,
        start_time: datetime,
        end_time: datetime,
        query: Optional[str] = None,
        limit: int = 1000,
    ) -> list[LogEntry]:
        """
        Query logs from Loki.

        Args:
            service: Service name
            start_time: Query start
            end_time: Query end
            query: Optional LogQL query override
            limit: Maximum logs to return

        Returns:
            List of log entries
        """
        if query is None:
            # Select streams by the `container` label, which BOTH the local
            # promtail (job="containerlogs") and the remote Alloy edge agents
            # stamp on every Docker log stream. The previous job="containerlogs"
            # selector silently dropped edge-agent logs — those streams carry
            # `edge=`/`container=` but no `job` label — so remotely-monitored
            # hosts always reported zero logs. The substring match also absorbs
            # the local `aiops-` container-name prefix (service "neo4j" matches
            # container "aiops-neo4j").
            if service and service != "all":
                query = f'{{container=~"(?i).*{logql_escape(service)}.*"}}'
            else:
                query = '{container=~".+"}'

        # Ensure naive datetimes are treated as UTC (not local time)
        # datetime.utcnow() returns naive datetimes; .timestamp() wrongly
        # assumes local timezone on naive datetimes, causing offset errors.
        start_utc = start_time.replace(tzinfo=timezone.utc) if start_time.tzinfo is None else start_time
        end_utc = end_time.replace(tzinfo=timezone.utc) if end_time.tzinfo is None else end_time

        params = {
            "query": query,
            "start": str(int(start_utc.timestamp() * 1e9)),  # Nanoseconds
            "end": str(int(end_utc.timestamp() * 1e9)),
            "limit": limit,
        }

        try:
            response = await self._client.get(
                f"{self.loki_url}/loki/api/v1/query_range",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            logs = []
            for stream in data.get("data", {}).get("result", []):
                labels = stream.get("stream", {})
                for value in stream.get("values", []):
                    timestamp_ns, message = value
                    logs.append(LogEntry(
                        timestamp=datetime.fromtimestamp(int(timestamp_ns) / 1e9),
                        level=_parse_log_level(labels, message),
                        message=message,
                        service=labels.get("container", labels.get("service", service)),
                        labels=labels,
                        trace_id=labels.get("trace_id"),
                    ))

            return logs

        except httpx.HTTPError as e:
            logger.warning(f"Loki query failed: {e}")
            return []

    async def query_metrics(
        self,
        service: Optional[str],
        start_time: datetime,
        end_time: datetime,
        metrics: Optional[list[str]] = None,
    ) -> list[MetricPoint]:
        """
        Query metrics from Prometheus.

        Args:
            service: Service/edge name to filter on, or None for all hosts.
            start_time: Query start
            end_time: Query end
            metrics: Optional list of metric names (default: common SRE metrics)

        Returns:
            List of metric points
        """
        # default_summary: the Telemetry "Metrics Summary" case (no explicit
        # query/metric passed). Each entry is an aggregation PromQL that returns a
        # SINGLE scalar series, paired with a clean human label. We emit only the
        # latest point per metric so the frontend gets one distinct, labeled value
        # per metric instead of a long single-metric time series.
        #
        # When a service/edge filter is provided the summary queries are scoped to
        # that host so the Metrics panel reflects the selected host rather than the
        # whole cluster.  The filter value is sanitised before interpolation.
        default_summary = metrics is None
        if default_summary:
            svc = logql_escape(service) if service else ""
            edge_filter = f'{{edge="{svc}"}}' if svc else ""
            job_filter = f'{{job=~".*{svc}.*"}}' if svc else ""
            metric_defs: list[tuple[str, Optional[str]]] = [
                (f'count(up{edge_filter} == 1)', 'Targets Up'),
                (f'sum(process_resident_memory_bytes{job_filter}) / 1024 / 1024', 'Memory (MB)'),
                (f'sum(go_goroutines{job_filter})', 'Goroutines'),
                (f'rate(process_cpu_seconds_total{job_filter}[5m])', 'CPU (s/s)'),
            ]
        else:
            # Explicit single-metric query path: label override is None so the raw
            # Prometheus __name__ (or the query string) is used, as before.
            metric_defs = [(metric_query, None) for metric_query in metrics]

        all_metrics = []

        for metric_query, label_override in metric_defs:
            params = {
                "query": metric_query,
                "start": start_time.isoformat() + "Z",
                "end": end_time.isoformat() + "Z",
                "step": "60",  # 1 minute resolution
            }

            try:
                response = await self._client.get(
                    f"{self.prometheus_url}/api/v1/query_range",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                for result in data.get("data", {}).get("result", []):
                    metric_name = label_override or result.get("metric", {}).get("__name__", metric_query)
                    labels = result.get("metric", {})

                    values = result.get("values", [])
                    if default_summary and values:
                        # Keep only the latest (max-timestamp) point per metric.
                        values = [max(values, key=lambda tv: float(tv[0]))]

                    for timestamp, value in values:
                        try:
                            all_metrics.append(MetricPoint(
                                timestamp=datetime.fromtimestamp(float(timestamp)),
                                name=metric_name,
                                value=float(value),
                                labels=labels,
                            ))
                        except (ValueError, TypeError):
                            continue

            except httpx.HTTPError as e:
                logger.debug(f"Prometheus query failed for {metric_query}: {e}")

        return all_metrics

    async def query_traces(
        self,
        service: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100,
    ) -> list[TraceSpan]:
        """
        Query traces from Tempo.

        Uses the TraceQL ``q=`` parameter (Tempo 2.x) rather than the legacy
        ``tags=`` form which is version-sensitive and brittle on Tempo 2.3.1.
        The search endpoint returns enough metadata (rootName, rootServiceName,
        durationMs) to build a representative ``TraceSpan`` without a per-trace
        detail GET, avoiding the previous N+1 fan-out.  The per-trace detail
        fetch is kept only for the ``trace_id`` lookup path (not used here).

        Args:
            service: Service name
            start_time: Query start
            end_time: Query end
            limit: Maximum traces to return

        Returns:
            List of trace spans
        """
        # Ensure naive datetimes are treated as UTC
        start_utc = start_time.replace(tzinfo=timezone.utc) if start_time.tzinfo is None else start_time
        end_utc = end_time.replace(tzinfo=timezone.utc) if end_time.tzinfo is None else end_time

        # TraceQL query (Tempo 2.x) — avoids the legacy logfmt `tags=` form.
        # Sanitise the service name with logql_escape (same safe-char set works
        # for TraceQL string literals).
        safe_svc = logql_escape(service)
        traceql = f'{{.service.name = "{safe_svc}"}}' if safe_svc else '{}'

        params: dict[str, str | int] = {
            "q": traceql,
            # Tempo /api/search expects epoch seconds, not nanoseconds.
            "start": str(int(start_utc.timestamp())),
            "end": str(int(end_utc.timestamp())),
            "limit": limit,
        }

        try:
            response = await self._client.get(
                f"{self.tempo_url}/api/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            spans: list[TraceSpan] = []
            for trace in data.get("traces", []):
                trace_id = trace.get("traceID", "")
                # The search response includes rootName and durationMs — enough
                # to populate a representative TraceSpan without a second GET.
                root_name = trace.get("rootName", "")
                root_svc = trace.get("rootServiceName", service)
                duration_ms = float(trace.get("durationMs", 0))
                start_time_ms = trace.get("startTimeUnixNano", 0)
                span_start = datetime.fromtimestamp(
                    int(start_time_ms) / 1e9,
                    tz=timezone.utc,
                ) if start_time_ms else start_utc

                # Build one representative TraceSpan per trace summary.
                # The OTLP detail shape uses scopeSpans[].spans[].attributes[]
                # (not the Jaeger-style batch.spans[].tags[]) — skipping the
                # detail fetch here keeps this O(1) per search response.
                spans.append(TraceSpan(
                    trace_id=trace_id,
                    span_id=trace_id[:16] if trace_id else "",
                    operation=root_name,
                    service=root_svc,
                    duration_ms=duration_ms,
                    status="OK",
                    start_time=span_start,
                    tags={},
                ))

            return spans

        except httpx.HTTPError as e:
            logger.debug(f"Tempo query failed: {e}")
            return []

    async def get_error_logs(
        self,
        service: str,
        duration_minutes: int = 15,
        limit: int = 100,
    ) -> list[LogEntry]:
        """
        Get recent error logs for a service.

        Args:
            service: Service name
            duration_minutes: How far back to look
            limit: Maximum logs

        Returns:
            List of error logs
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=duration_minutes)

        # Match on the `container` label (the only service-identifying label that
        # both local promtail and remote Alloy streams share — there is no
        # `service` label in this stack), then line-filter for error markers.
        query = f'{{container=~"(?i).*{logql_escape(service)}.*"}} |~ "(?i)error"'

        return await self.query_logs(
            service=service,
            start_time=start_time,
            end_time=end_time,
            query=query,
            limit=limit,
        )

    async def get_latency_percentiles(
        self,
        service: str,
        duration_minutes: int = 15,
    ) -> dict[str, float]:
        """
        Get latency percentiles for a service.

        Args:
            service: Service name
            duration_minutes: Time window

        Returns:
            Dictionary with p50, p90, p99 latencies in ms
        """
        percentiles = {}

        for p in [50, 90, 99]:
            query = f'histogram_quantile(0.{p:02d}, rate(http_request_duration_seconds_bucket{{service="{service}"}}[{duration_minutes}m]))'

            params = {
                "query": query,
                "time": datetime.utcnow().isoformat() + "Z",
            }

            try:
                response = await self._client.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                results = data.get("data", {}).get("result", [])
                if results:
                    value = float(results[0].get("value", [0, 0])[1])
                    percentiles[f"p{p}"] = round(value * 1000, 2)  # Convert to ms

            except Exception as e:
                logger.debug(f"Failed to get p{p} latency: {e}")

        return percentiles


__all__ = [
    "LogEntry",
    "MetricPoint",
    "TraceSpan",
    "TelemetryWindow",
    "TelemetryCollector",
    "_parse_log_level",
]
