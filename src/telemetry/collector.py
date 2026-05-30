"""
Constitutional AIOps - Telemetry Collector

Collects telemetry data from LGTM stack (Loki, Grafana, Tempo, Mimir/Prometheus).
Provides unified interface for accessing logs, metrics, and traces.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from src.config import config

logger = logging.getLogger(__name__)


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
            # Use job="containerlogs" which is how promtail labels Docker logs
            # Filter by container name pattern if service specified
            if service and service != "all":
                query = f'{{job="containerlogs"}} |~ "{service}"'
            else:
                query = '{job="containerlogs"}'

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
                        level=labels.get("level", "info"),
                        message=message,
                        service=labels.get("service", service),
                        labels=labels,
                        trace_id=labels.get("trace_id"),
                    ))

            return logs

        except httpx.HTTPError as e:
            logger.warning(f"Loki query failed: {e}")
            return []

    async def query_metrics(
        self,
        service: str,
        start_time: datetime,
        end_time: datetime,
        metrics: Optional[list[str]] = None,
    ) -> list[MetricPoint]:
        """
        Query metrics from Prometheus.

        Args:
            service: Service name
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
        default_summary = metrics is None
        if default_summary:
            metric_defs: list[tuple[str, Optional[str]]] = [
                ('count(up == 1)', 'Targets Up'),
                ('sum(process_resident_memory_bytes) / 1024 / 1024', 'Memory (MB)'),
                ('sum(go_goroutines)', 'Goroutines'),
                ('rate(process_cpu_seconds_total[5m])', 'CPU (s/s)'),
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

        params = {
            "tags": f"service.name={service}",
            "start": str(int(start_utc.timestamp() * 1e9)),
            "end": str(int(end_utc.timestamp() * 1e9)),
            "limit": limit,
        }

        try:
            response = await self._client.get(
                f"{self.tempo_url}/api/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            spans = []
            for trace in data.get("traces", []):
                trace_id = trace.get("traceID", "")

                # Get full trace details
                trace_response = await self._client.get(
                    f"{self.tempo_url}/api/traces/{trace_id}",
                )
                if trace_response.status_code == 200:
                    trace_data = trace_response.json()

                    for batch in trace_data.get("batches", []):
                        for span_data in batch.get("spans", []):
                            spans.append(TraceSpan(
                                trace_id=trace_id,
                                span_id=span_data.get("spanID", ""),
                                operation=span_data.get("operationName", ""),
                                service=service,
                                duration_ms=span_data.get("duration", 0) / 1000,  # μs to ms
                                status=span_data.get("status", {}).get("code", "OK"),
                                start_time=datetime.fromtimestamp(
                                    span_data.get("startTime", 0) / 1e6
                                ),
                                tags={
                                    tag.get("key", ""): tag.get("value", "")
                                    for tag in span_data.get("tags", [])
                                },
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

        query = f'{{service="{service}"}} |= "error" or |= "ERROR" or |= "Error"'

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
]
