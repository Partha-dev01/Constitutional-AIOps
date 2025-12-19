"""
Constitutional AIOps - Telemetry Aggregator

Aggregates telemetry data from multiple sources and time windows.
Provides statistical analysis and anomaly detection for incidents.
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from src.telemetry.collector import LogEntry, MetricPoint, TelemetryWindow, TraceSpan

logger = logging.getLogger(__name__)


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for a time period."""
    name: str
    count: int
    min_value: float
    max_value: float
    avg_value: float
    std_dev: float
    percentile_50: float
    percentile_90: float
    percentile_99: float
    trend: str  # "stable", "increasing", "decreasing", "volatile"


@dataclass
class ServiceHealth:
    """Health summary for a service."""
    service_name: str
    timestamp: datetime
    health_score: float  # 0.0 - 1.0
    error_rate: float
    avg_latency_ms: float
    request_rate: float
    availability: float
    anomalies: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)


@dataclass
class IncidentContext:
    """
    Aggregated context for an incident.

    Combines telemetry from multiple windows and sources.
    """
    incident_id: str
    service: str

    # Time range
    start_time: datetime
    end_time: datetime

    # Log analysis
    total_logs: int
    error_logs: int
    warning_logs: int
    unique_errors: list[str]
    error_timeline: list[tuple[datetime, int]]

    # Metric analysis
    metrics: dict[str, AggregatedMetrics]
    metric_anomalies: list[str]

    # Trace analysis
    total_traces: int
    failed_traces: int
    avg_latency_ms: float
    latency_percentiles: dict[str, float]
    slow_endpoints: list[tuple[str, float]]

    # Overall assessment
    health_score: float
    severity_indicators: list[str]
    likely_causes: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "incident_id": self.incident_id,
            "service": self.service,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_logs": self.total_logs,
            "error_logs": self.error_logs,
            "warning_logs": self.warning_logs,
            "unique_errors": self.unique_errors,
            "metrics": {
                name: {
                    "avg": m.avg_value,
                    "max": m.max_value,
                    "p99": m.percentile_99,
                    "trend": m.trend,
                }
                for name, m in self.metrics.items()
            },
            "metric_anomalies": self.metric_anomalies,
            "total_traces": self.total_traces,
            "failed_traces": self.failed_traces,
            "avg_latency_ms": self.avg_latency_ms,
            "latency_percentiles": self.latency_percentiles,
            "slow_endpoints": self.slow_endpoints,
            "health_score": self.health_score,
            "severity_indicators": self.severity_indicators,
            "likely_causes": self.likely_causes,
        }


class TelemetryAggregator:
    """
    Aggregates and analyzes telemetry data.

    Provides:
    - Statistical aggregation of metrics
    - Anomaly detection
    - Service health scoring
    - Incident context building
    """

    def __init__(
        self,
        anomaly_threshold: float = 2.0,  # Standard deviations
        error_rate_alert: float = 0.05,  # 5% error rate triggers alert
        latency_alert_ms: float = 500,  # 500ms latency triggers alert
    ):
        """
        Initialize aggregator.

        Args:
            anomaly_threshold: Standard deviations for anomaly detection
            error_rate_alert: Error rate threshold for alerts
            latency_alert_ms: Latency threshold for alerts
        """
        self.anomaly_threshold = anomaly_threshold
        self.error_rate_alert = error_rate_alert
        self.latency_alert_ms = latency_alert_ms

        # Baseline storage for anomaly detection
        self._baselines: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

        logger.info("TelemetryAggregator initialized")

    def aggregate_window(
        self,
        window: TelemetryWindow,
        service: str,
    ) -> IncidentContext:
        """
        Aggregate a telemetry window into incident context.

        Args:
            window: TelemetryWindow to aggregate
            service: Service name

        Returns:
            IncidentContext with aggregated data
        """
        # Aggregate logs
        log_analysis = self._aggregate_logs(window.logs)

        # Aggregate metrics
        metric_analysis = self._aggregate_metrics(window.metrics, service)

        # Aggregate traces
        trace_analysis = self._aggregate_traces(window.traces)

        # Calculate health score
        health_score = self._calculate_health_score(
            error_rate=log_analysis["error_rate"],
            avg_latency=trace_analysis["avg_latency_ms"],
            availability=1.0 - trace_analysis["failure_rate"],
        )

        # Identify severity indicators
        severity_indicators = self._identify_severity_indicators(
            log_analysis, metric_analysis, trace_analysis
        )

        # Identify likely causes
        likely_causes = self._identify_likely_causes(
            log_analysis, metric_analysis, trace_analysis
        )

        return IncidentContext(
            incident_id="",  # To be set by caller
            service=service,
            start_time=window.start_time,
            end_time=window.end_time,
            total_logs=log_analysis["total"],
            error_logs=log_analysis["errors"],
            warning_logs=log_analysis["warnings"],
            unique_errors=log_analysis["unique_errors"],
            error_timeline=log_analysis["timeline"],
            metrics=metric_analysis["aggregated"],
            metric_anomalies=metric_analysis["anomalies"],
            total_traces=trace_analysis["total"],
            failed_traces=trace_analysis["failed"],
            avg_latency_ms=trace_analysis["avg_latency_ms"],
            latency_percentiles=trace_analysis["percentiles"],
            slow_endpoints=trace_analysis["slow_endpoints"],
            health_score=health_score,
            severity_indicators=severity_indicators,
            likely_causes=likely_causes,
        )

    def aggregate_multiple_windows(
        self,
        windows: list[TelemetryWindow],
        service: str,
    ) -> IncidentContext:
        """
        Aggregate multiple windows into single context.

        Args:
            windows: List of windows to aggregate
            service: Service name

        Returns:
            Combined IncidentContext
        """
        if not windows:
            return self._empty_context(service)

        # Combine all data
        all_logs: list[LogEntry] = []
        all_metrics: list[MetricPoint] = []
        all_traces: list[TraceSpan] = []

        for window in windows:
            all_logs.extend(window.logs)
            all_metrics.extend(window.metrics)
            all_traces.extend(window.traces)

        # Create combined window
        start_time = min(w.start_time for w in windows)
        end_time = max(w.end_time for w in windows)

        combined = TelemetryWindow(
            start_time=start_time,
            end_time=end_time,
            logs=all_logs,
            metrics=all_metrics,
            traces=all_traces,
        )

        return self.aggregate_window(combined, service)

    def calculate_service_health(
        self,
        window: TelemetryWindow,
        service: str,
    ) -> ServiceHealth:
        """
        Calculate service health from telemetry.

        Args:
            window: Telemetry window
            service: Service name

        Returns:
            ServiceHealth summary
        """
        # Calculate error rate
        total_logs = len(window.logs)
        error_logs = sum(1 for log in window.logs if log.level.lower() in ("error", "fatal", "critical"))
        error_rate = error_logs / total_logs if total_logs > 0 else 0.0

        # Calculate latency
        latencies = [t.duration_ms for t in window.traces]
        avg_latency = statistics.mean(latencies) if latencies else 0.0

        # Calculate request rate (requests per minute)
        duration_minutes = window.duration_minutes
        request_rate = len(window.traces) / duration_minutes if duration_minutes > 0 else 0.0

        # Calculate availability
        failed_traces = sum(1 for t in window.traces if t.status != "OK")
        availability = 1.0 - (failed_traces / len(window.traces)) if window.traces else 1.0

        # Calculate overall health score
        health_score = self._calculate_health_score(error_rate, avg_latency, availability)

        # Identify anomalies
        anomalies = []
        if error_rate > self.error_rate_alert:
            anomalies.append(f"High error rate: {error_rate:.1%}")
        if avg_latency > self.latency_alert_ms:
            anomalies.append(f"High latency: {avg_latency:.0f}ms")
        if availability < 0.99:
            anomalies.append(f"Low availability: {availability:.1%}")

        # Generate alerts
        alerts = []
        if health_score < 0.5:
            alerts.append("CRITICAL: Service health severely degraded")
        elif health_score < 0.7:
            alerts.append("WARNING: Service health degraded")

        return ServiceHealth(
            service_name=service,
            timestamp=datetime.utcnow(),
            health_score=health_score,
            error_rate=error_rate,
            avg_latency_ms=avg_latency,
            request_rate=request_rate,
            availability=availability,
            anomalies=anomalies,
            alerts=alerts,
        )

    def update_baseline(
        self,
        service: str,
        metric_name: str,
        values: list[float],
    ) -> None:
        """
        Update baseline for anomaly detection.

        Args:
            service: Service name
            metric_name: Metric name
            values: New values to add to baseline
        """
        baseline = self._baselines[service][metric_name]
        baseline.extend(values)

        # Keep only recent values (rolling window)
        max_size = 1000
        if len(baseline) > max_size:
            self._baselines[service][metric_name] = baseline[-max_size:]

    def detect_anomalies(
        self,
        service: str,
        metric_name: str,
        current_value: float,
    ) -> Optional[str]:
        """
        Detect if a value is anomalous compared to baseline.

        Args:
            service: Service name
            metric_name: Metric name
            current_value: Current value to check

        Returns:
            Anomaly description or None
        """
        baseline = self._baselines[service][metric_name]

        if len(baseline) < 10:
            return None  # Not enough data

        mean = statistics.mean(baseline)
        std_dev = statistics.stdev(baseline) if len(baseline) > 1 else 0

        if std_dev == 0:
            return None

        z_score = (current_value - mean) / std_dev

        if abs(z_score) > self.anomaly_threshold:
            direction = "high" if z_score > 0 else "low"
            return f"Anomaly: {metric_name} is {direction} ({z_score:.1f} std devs from mean)"

        return None

    def _aggregate_logs(self, logs: list[LogEntry]) -> dict[str, Any]:
        """Aggregate log entries."""
        total = len(logs)
        errors = sum(1 for log in logs if log.level.lower() in ("error", "fatal", "critical"))
        warnings = sum(1 for log in logs if log.level.lower() in ("warn", "warning"))

        # Get unique errors
        unique_errors: dict[str, int] = {}
        for log in logs:
            if log.level.lower() in ("error", "fatal", "critical"):
                # Simplified message for grouping
                key = log.message[:100]
                unique_errors[key] = unique_errors.get(key, 0) + 1

        sorted_errors = sorted(unique_errors.keys(), key=lambda x: unique_errors[x], reverse=True)

        # Build error timeline (errors per minute)
        timeline: list[tuple[datetime, int]] = []
        if logs:
            from collections import Counter
            minute_counts = Counter(
                log.timestamp.replace(second=0, microsecond=0)
                for log in logs
                if log.level.lower() in ("error", "fatal", "critical")
            )
            timeline = sorted(minute_counts.items())

        error_rate = errors / total if total > 0 else 0.0

        return {
            "total": total,
            "errors": errors,
            "warnings": warnings,
            "error_rate": error_rate,
            "unique_errors": sorted_errors[:10],
            "timeline": timeline,
        }

    def _aggregate_metrics(
        self,
        metrics: list[MetricPoint],
        service: str,
    ) -> dict[str, Any]:
        """Aggregate metric points."""
        # Group by metric name
        groups: dict[str, list[float]] = defaultdict(list)
        for m in metrics:
            groups[m.name].append(m.value)

        aggregated: dict[str, AggregatedMetrics] = {}
        anomalies: list[str] = []

        for name, values in groups.items():
            if not values:
                continue

            # Calculate statistics
            sorted_values = sorted(values)
            count = len(values)
            min_val = min(values)
            max_val = max(values)
            avg_val = statistics.mean(values)
            std_dev = statistics.stdev(values) if count > 1 else 0

            # Calculate percentiles
            p50 = sorted_values[int(count * 0.5)] if count > 0 else 0
            p90 = sorted_values[int(count * 0.9)] if count > 0 else 0
            p99 = sorted_values[int(count * 0.99)] if count > 0 else 0

            # Determine trend
            trend = self._calculate_trend(values)

            aggregated[name] = AggregatedMetrics(
                name=name,
                count=count,
                min_value=min_val,
                max_value=max_val,
                avg_value=avg_val,
                std_dev=std_dev,
                percentile_50=p50,
                percentile_90=p90,
                percentile_99=p99,
                trend=trend,
            )

            # Check for anomalies
            anomaly = self.detect_anomalies(service, name, avg_val)
            if anomaly:
                anomalies.append(anomaly)

            # Update baseline
            self.update_baseline(service, name, values)

        return {
            "aggregated": aggregated,
            "anomalies": anomalies,
        }

    def _aggregate_traces(self, traces: list[TraceSpan]) -> dict[str, Any]:
        """Aggregate trace spans."""
        total = len(traces)
        failed = sum(1 for t in traces if t.status != "OK")

        latencies = [t.duration_ms for t in traces]
        avg_latency = statistics.mean(latencies) if latencies else 0.0

        # Calculate percentiles
        percentiles = {}
        if latencies:
            sorted_lat = sorted(latencies)
            percentiles = {
                "p50": sorted_lat[int(len(sorted_lat) * 0.5)],
                "p90": sorted_lat[int(len(sorted_lat) * 0.9)],
                "p99": sorted_lat[min(int(len(sorted_lat) * 0.99), len(sorted_lat) - 1)],
            }

        # Find slow endpoints
        operation_latencies: dict[str, list[float]] = defaultdict(list)
        for trace in traces:
            operation_latencies[trace.operation].append(trace.duration_ms)

        slow_endpoints = []
        for op, lats in operation_latencies.items():
            avg = statistics.mean(lats)
            if avg > self.latency_alert_ms:
                slow_endpoints.append((op, avg))

        slow_endpoints.sort(key=lambda x: x[1], reverse=True)

        failure_rate = failed / total if total > 0 else 0.0

        return {
            "total": total,
            "failed": failed,
            "failure_rate": failure_rate,
            "avg_latency_ms": avg_latency,
            "percentiles": percentiles,
            "slow_endpoints": slow_endpoints[:5],
        }

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend from values."""
        if len(values) < 5:
            return "stable"

        # Split into halves and compare
        mid = len(values) // 2
        first_half = statistics.mean(values[:mid])
        second_half = statistics.mean(values[mid:])

        # Calculate coefficient of variation
        cv = statistics.stdev(values) / statistics.mean(values) if statistics.mean(values) != 0 else 0

        if cv > 0.5:
            return "volatile"
        elif second_half > first_half * 1.2:
            return "increasing"
        elif second_half < first_half * 0.8:
            return "decreasing"
        else:
            return "stable"

    def _calculate_health_score(
        self,
        error_rate: float,
        avg_latency: float,
        availability: float,
    ) -> float:
        """
        Calculate overall health score.

        Args:
            error_rate: Error rate (0.0-1.0)
            avg_latency: Average latency in ms
            availability: Availability (0.0-1.0)

        Returns:
            Health score (0.0-1.0)
        """
        # Error rate component (weight: 0.4)
        error_score = max(0, 1 - error_rate * 10)  # Penalize heavily

        # Latency component (weight: 0.3)
        latency_score = max(0, 1 - avg_latency / 1000)  # 1000ms = 0 score

        # Availability component (weight: 0.3)
        availability_score = availability

        health = (error_score * 0.4 + latency_score * 0.3 + availability_score * 0.3)
        return round(max(0, min(1, health)), 2)

    def _identify_severity_indicators(
        self,
        log_analysis: dict[str, Any],
        metric_analysis: dict[str, Any],
        trace_analysis: dict[str, Any],
    ) -> list[str]:
        """Identify severity indicators from analysis."""
        indicators = []

        if log_analysis["error_rate"] > 0.1:
            indicators.append(f"CRITICAL: Error rate {log_analysis['error_rate']:.1%}")

        if trace_analysis["failure_rate"] > 0.05:
            indicators.append(f"HIGH: Request failure rate {trace_analysis['failure_rate']:.1%}")

        if trace_analysis["avg_latency_ms"] > 500:
            indicators.append(f"MEDIUM: High latency {trace_analysis['avg_latency_ms']:.0f}ms")

        if metric_analysis["anomalies"]:
            indicators.append(f"Detected {len(metric_analysis['anomalies'])} metric anomalies")

        return indicators

    def _identify_likely_causes(
        self,
        log_analysis: dict[str, Any],
        metric_analysis: dict[str, Any],
        trace_analysis: dict[str, Any],
    ) -> list[str]:
        """Identify likely causes based on patterns."""
        causes = []

        # Check for common patterns in errors
        for error in log_analysis["unique_errors"][:5]:
            error_lower = error.lower()

            if "connection" in error_lower and ("refused" in error_lower or "timeout" in error_lower):
                causes.append("Network connectivity issue")
            elif "memory" in error_lower or "oom" in error_lower:
                causes.append("Memory exhaustion")
            elif "disk" in error_lower or "space" in error_lower:
                causes.append("Disk space issue")
            elif "database" in error_lower or "query" in error_lower:
                causes.append("Database issue")
            elif "timeout" in error_lower:
                causes.append("Upstream dependency timeout")
            elif "auth" in error_lower or "unauthorized" in error_lower:
                causes.append("Authentication/authorization issue")

        # Check metric patterns
        for name, metric in metric_analysis["aggregated"].items():
            if "cpu" in name.lower() and metric.avg_value > 0.8:
                causes.append("CPU saturation")
            if "memory" in name.lower() and metric.avg_value > 0.9:
                causes.append("Memory pressure")

        # Check trace patterns
        if trace_analysis["slow_endpoints"]:
            causes.append(f"Slow endpoint: {trace_analysis['slow_endpoints'][0][0]}")

        return list(set(causes))[:5]  # Deduplicate and limit

    def _empty_context(self, service: str) -> IncidentContext:
        """Create empty context."""
        now = datetime.utcnow()
        return IncidentContext(
            incident_id="",
            service=service,
            start_time=now,
            end_time=now,
            total_logs=0,
            error_logs=0,
            warning_logs=0,
            unique_errors=[],
            error_timeline=[],
            metrics={},
            metric_anomalies=[],
            total_traces=0,
            failed_traces=0,
            avg_latency_ms=0.0,
            latency_percentiles={},
            slow_endpoints=[],
            health_score=1.0,
            severity_indicators=[],
            likely_causes=[],
        )


__all__ = [
    "AggregatedMetrics",
    "ServiceHealth",
    "IncidentContext",
    "TelemetryAggregator",
]
