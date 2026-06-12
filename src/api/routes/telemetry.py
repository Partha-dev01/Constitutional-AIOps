"""
Constitutional AIOps - Telemetry API Routes

Provides endpoints for accessing logs, metrics, and traces from the LGTM stack.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Request, Query
from pydantic import BaseModel, Field

from src.telemetry.collector import logql_escape

logger = logging.getLogger(__name__)

router = APIRouter()


class LogEntry(BaseModel):
    """Log entry from Loki."""
    timestamp: str
    level: str = Field(..., description="Log level: INFO, WARN, ERROR, DEBUG")
    service: str
    message: str
    labels: dict[str, str] = Field(default_factory=dict)


class LogsResponse(BaseModel):
    """Response containing log entries."""
    logs: list[LogEntry]
    total: int
    query: str | None = None


class MetricPoint(BaseModel):
    """Metric data point."""
    timestamp: str
    value: float
    label: str


class MetricsResponse(BaseModel):
    """Response containing metrics."""
    metrics: list[MetricPoint]
    range: str
    step: str


class TraceSpan(BaseModel):
    """Trace span from Tempo."""
    trace_id: str
    span_id: str
    operation: str
    service: str
    duration_ms: float
    status: str
    parent_span_id: str | None = None


class TracesResponse(BaseModel):
    """Response containing traces."""
    traces: list[TraceSpan]
    total: int


class TelemetryHealthResponse(BaseModel):
    """Telemetry backends health status."""
    loki: bool
    prometheus: bool
    tempo: bool


@router.get(
    "/logs",
    response_model=LogsResponse,
    summary="Get Logs",
    description="Query logs from Loki",
)
async def get_logs(
    request: Request,
    limit: int = Query(50, ge=1, le=1000),
    level: str | None = Query(None, description="Filter by log level"),
    service: str | None = Query(None, description="Filter by service name"),
    query: str | None = Query(None, description="LogQL query"),
    since_minutes: int = Query(60, description="Get logs from last N minutes"),
) -> LogsResponse:
    """
    Query logs from Loki.

    Returns recent log entries with optional filtering.
    """
    telemetry_collector = getattr(request.app.state, "telemetry_collector", None)

    if telemetry_collector is None:
        # Return empty response
        return LogsResponse(logs=[], total=0, query=query)

    try:
        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=since_minutes)

        # Build LogQL query. Select by the `container` label, which both the local
        # promtail and the remote Alloy edge streams carry; a substring match lets a
        # service name also resolve the local `aiops-` container-name prefix and the
        # remote container name alike. (When service is None the collector applies
        # its own '{container=~".+"}' default.)
        logql_query = query
        if logql_query is None and service:
            logql_query = f'{{container=~"(?i).*{logql_escape(service)}.*"}}'

        if level:
            # Anchor on a stream selector before appending the level line-filter;
            # match every container stream when no service was specified.
            base = logql_query if logql_query is not None else '{container=~".+"}'
            logql_query = f'{base} |~ "(?i){logql_escape(level)}"'

        # Query Loki via collector
        logs_data = await telemetry_collector.query_logs(
            service=service or "all",
            start_time=start_time,
            end_time=end_time,
            query=logql_query,
            limit=limit,
        )

        logs = [
            LogEntry(
                timestamp=entry.timestamp.isoformat() if hasattr(entry, 'timestamp') else str(entry.get("timestamp", datetime.utcnow().isoformat())),
                level=entry.level if hasattr(entry, 'level') else entry.get("level", "INFO"),
                service=entry.service if hasattr(entry, 'service') else entry.get("service", "unknown"),
                message=entry.message if hasattr(entry, 'message') else entry.get("message", ""),
                labels=entry.labels if hasattr(entry, 'labels') else entry.get("labels", {}),
            )
            for entry in logs_data
        ]

        return LogsResponse(logs=logs, total=len(logs), query=logql_query)

    except Exception as e:
        logger.warning(f"Failed to query logs: {e}")
        return LogsResponse(logs=[], total=0, query=query)


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Get Metrics",
    description="Query metrics from Prometheus",
)
async def get_metrics(
    request: Request,
    range: str = Query("1h", description="Time range (e.g., 1h, 6h, 24h)"),
    step: str = Query("1m", description="Step interval (e.g., 1m, 5m)"),
    query: str | None = Query(None, description="PromQL query"),
    metric: str | None = Query(None, description="Specific metric name"),
    service: str | None = Query(None, description="Filter by service/container"),
) -> MetricsResponse:
    """
    Query metrics from Prometheus.

    Returns metric data points for visualization.
    """
    telemetry_collector = getattr(request.app.state, "telemetry_collector", None)

    if telemetry_collector is None:
        return MetricsResponse(metrics=[], range=range, step=step)

    try:
        # Parse time range (e.g., "1h" -> 60 minutes)
        range_value = int(range[:-1])
        range_unit = range[-1]
        if range_unit == 'h':
            minutes = range_value * 60
        elif range_unit == 'd':
            minutes = range_value * 60 * 24
        else:
            minutes = range_value

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)

        # Build metrics queries for container/service
        service_name = service or "nextcloud"
        metrics_queries = None
        if query:
            metrics_queries = [query]
        elif metric:
            metrics_queries = [metric]

        # Query Prometheus via collector
        metrics_data = await telemetry_collector.query_metrics(
            service=service_name,
            start_time=start_time,
            end_time=end_time,
            metrics=metrics_queries,
        )

        metrics = [
            MetricPoint(
                timestamp=point.timestamp.isoformat() if hasattr(point, 'timestamp') else str(point.get("timestamp", datetime.utcnow().isoformat())),
                value=float(point.value if hasattr(point, 'value') else point.get("value", 0)),
                label=point.name if hasattr(point, 'name') else point.get("label", "unknown"),
            )
            for point in metrics_data
        ]

        return MetricsResponse(metrics=metrics, range=range, step=step)

    except Exception as e:
        logger.warning(f"Failed to query metrics: {e}")
        return MetricsResponse(metrics=[], range=range, step=step)


@router.get(
    "/traces",
    response_model=TracesResponse,
    summary="Get Traces",
    description="Query traces from Tempo",
)
async def get_traces(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    service: str | None = Query(None, description="Filter by service name"),
    trace_id: str | None = Query(None, description="Get specific trace"),
    min_duration_ms: int | None = Query(None, description="Minimum duration filter"),
    since_minutes: int = Query(60, description="Get traces from last N minutes"),
) -> TracesResponse:
    """
    Query traces from Tempo.

    Returns distributed trace spans for analysis.
    """
    telemetry_collector = getattr(request.app.state, "telemetry_collector", None)

    if telemetry_collector is None:
        return TracesResponse(traces=[], total=0)

    try:
        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=since_minutes)

        # Query Tempo via collector
        traces_data = await telemetry_collector.query_traces(
            service=service or "nextcloud",
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        traces = [
            TraceSpan(
                trace_id=span.trace_id if hasattr(span, 'trace_id') else span.get("trace_id", ""),
                span_id=span.span_id if hasattr(span, 'span_id') else span.get("span_id", ""),
                operation=span.operation if hasattr(span, 'operation') else span.get("operation", "unknown"),
                service=span.service if hasattr(span, 'service') else span.get("service", "unknown"),
                duration_ms=float(span.duration_ms if hasattr(span, 'duration_ms') else span.get("duration_ms", 0)),
                status=span.status if hasattr(span, 'status') else span.get("status", "unknown"),
                parent_span_id=None,
            )
            for span in traces_data
        ]

        # Filter by min duration if specified
        if min_duration_ms:
            traces = [t for t in traces if t.duration_ms >= min_duration_ms]

        return TracesResponse(traces=traces, total=len(traces))

    except Exception as e:
        logger.warning(f"Failed to query traces: {e}")
        return TracesResponse(traces=[], total=0)


class BackgroundProcessorStats(BaseModel):
    """Background telemetry processor statistics."""
    running: bool = Field(..., description="Whether processor is running")
    total_cycles: int = Field(0, description="Total processing cycles completed")
    telemetry_processed: int = Field(0, description="Total telemetry windows processed")
    anomalies_detected: int = Field(0, description="Total anomalies detected")
    escalations_to_reasoning: int = Field(0, description="Times escalated to Reasoning Agent")
    episodes_created: int = Field(0, description="Episodes stored in graph")
    errors: int = Field(0, description="Processing errors")
    last_run: str | None = Field(None, description="Timestamp of last processing cycle")
    services_monitored: int = Field(0, description="Number of services being monitored")
    processing_interval_seconds: int = Field(30, description="Seconds between cycles")


@router.get(
    "/processor/status",
    response_model=BackgroundProcessorStats,
    summary="Background Processor Status",
    description="Get status and statistics of the background telemetry processor",
)
async def get_processor_status(request: Request) -> BackgroundProcessorStats:
    """
    Get background telemetry processor status.

    The processor continuously scans telemetry and annotates anomalies
    using the Fast Agent (System 1 pattern recognition).
    """
    processor = getattr(request.app.state, "background_processor", None)

    if processor is None:
        return BackgroundProcessorStats(
            running=False,
            total_cycles=0,
            telemetry_processed=0,
            anomalies_detected=0,
            escalations_to_reasoning=0,
            episodes_created=0,
            errors=0,
            last_run=None,
            services_monitored=0,
            processing_interval_seconds=30,
        )

    stats = processor.get_stats()
    return BackgroundProcessorStats(
        running=stats.get("running", False),
        total_cycles=stats.get("total_cycles", 0),
        telemetry_processed=stats.get("telemetry_processed", 0),
        anomalies_detected=stats.get("anomalies_detected", 0),
        escalations_to_reasoning=stats.get("escalations_to_reasoning", 0),
        episodes_created=stats.get("episodes_created", 0),
        errors=stats.get("errors", 0),
        last_run=stats.get("last_run"),
        services_monitored=stats.get("services_monitored", 0),
        processing_interval_seconds=stats.get("processing_interval_seconds", 30),
    )


@router.get(
    "/health",
    response_model=TelemetryHealthResponse,
    summary="Telemetry Health",
    description="Check health of telemetry backends",
)
async def check_telemetry_health(request: Request) -> TelemetryHealthResponse:
    """Check health status of Loki, Prometheus, and Tempo."""
    telemetry_collector = getattr(request.app.state, "telemetry_collector", None)

    if telemetry_collector is None:
        return TelemetryHealthResponse(loki=False, prometheus=False, tempo=False)

    try:
        health = await telemetry_collector.health_check()
        return TelemetryHealthResponse(
            loki=health.get("loki", False),
            prometheus=health.get("prometheus", False),
            tempo=health.get("tempo", False),
        )
    except Exception as e:
        logger.warning(f"Telemetry health check failed: {e}")
        return TelemetryHealthResponse(loki=False, prometheus=False, tempo=False)


__all__ = ["router"]
