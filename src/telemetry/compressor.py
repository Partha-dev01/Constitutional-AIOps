"""
Constitutional AIOps - Token Compressor

Compresses telemetry data to fit within LLM context windows.
Uses smart summarization to preserve critical information while reducing token count.

Target compression ratios:
- Fast Agent: Fit 15 minutes of telemetry into ~1K tokens
- Reasoning Agent: Fit incident context into ~2K tokens
"""

import logging
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from src.telemetry.collector import LogEntry, MetricPoint, TelemetryWindow, TraceSpan

logger = logging.getLogger(__name__)


@dataclass
class CompressedTelemetry:
    """
    Compressed telemetry representation.

    Designed to maximize information density while minimizing token count.
    """

    # Summary statistics
    time_range: str
    log_summary: str
    metric_summary: str
    trace_summary: str

    # Key indicators
    error_count: int
    warning_count: int
    anomaly_indicators: list[str]

    # Top issues
    top_errors: list[str]
    slow_operations: list[str]
    resource_alerts: list[str]

    # Estimated token count
    estimated_tokens: int

    def to_prompt_text(self) -> str:
        """Convert to text format for LLM prompt."""
        sections = []

        sections.append(f"[Telemetry: {self.time_range}]")

        if self.log_summary:
            sections.append(f"Logs: {self.log_summary}")

        if self.metric_summary:
            sections.append(f"Metrics: {self.metric_summary}")

        if self.trace_summary:
            sections.append(f"Traces: {self.trace_summary}")

        if self.top_errors:
            sections.append(f"Errors: {'; '.join(self.top_errors[:3])}")

        if self.slow_operations:
            sections.append(f"Slow ops: {'; '.join(self.slow_operations[:3])}")

        if self.anomaly_indicators:
            sections.append(f"Anomalies: {', '.join(self.anomaly_indicators[:5])}")

        return "\n".join(sections)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "time_range": self.time_range,
            "log_summary": self.log_summary,
            "metric_summary": self.metric_summary,
            "trace_summary": self.trace_summary,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "anomaly_indicators": self.anomaly_indicators,
            "top_errors": self.top_errors,
            "slow_operations": self.slow_operations,
            "resource_alerts": self.resource_alerts,
            "estimated_tokens": self.estimated_tokens,
        }


class TokenCompressor:
    """
    Compresses telemetry data for LLM consumption.

    Strategies:
    1. Deduplication - Remove duplicate log messages
    2. Sampling - Take representative samples of high-volume data
    3. Aggregation - Summarize metrics into statistical highlights
    4. Extraction - Pull out key indicators and anomalies
    """

    def __init__(
        self,
        target_tokens: int = 1000,
        chars_per_token: float = 4.0,  # Rough estimate
    ):
        """
        Initialize compressor.

        Args:
            target_tokens: Target compressed size in tokens
            chars_per_token: Estimated characters per token
        """
        self.target_tokens = target_tokens
        self.chars_per_token = chars_per_token
        self.target_chars = int(target_tokens * chars_per_token)

        # Patterns for log analysis
        self._error_patterns = [
            r"error",
            r"exception",
            r"failed",
            r"failure",
            r"timeout",
            r"refused",
            r"denied",
            r"crash",
            r"panic",
            r"fatal",
        ]

        self._warning_patterns = [
            r"warn",
            r"warning",
            r"deprecated",
            r"slow",
            r"retry",
            r"backoff",
        ]

        logger.info(f"TokenCompressor initialized (target: {target_tokens} tokens)")

    def compress_window(self, window: TelemetryWindow) -> CompressedTelemetry:
        """
        Compress a telemetry window.

        Args:
            window: TelemetryWindow to compress

        Returns:
            CompressedTelemetry with summarized data
        """
        # Generate time range string
        time_range = self._format_time_range(window.start_time, window.end_time)

        # Process logs
        log_summary, top_errors, error_count, warning_count = self._compress_logs(window.logs)

        # Process metrics
        metric_summary, resource_alerts = self._compress_metrics(window.metrics)

        # Process traces
        trace_summary, slow_operations = self._compress_traces(window.traces)

        # Detect anomalies
        anomaly_indicators = self._detect_anomalies(window)

        # Calculate estimated tokens
        full_text = "\n".join([
            time_range, log_summary, metric_summary, trace_summary,
            str(top_errors), str(slow_operations), str(anomaly_indicators),
        ])
        estimated_tokens = int(len(full_text) / self.chars_per_token)

        return CompressedTelemetry(
            time_range=time_range,
            log_summary=log_summary,
            metric_summary=metric_summary,
            trace_summary=trace_summary,
            error_count=error_count,
            warning_count=warning_count,
            anomaly_indicators=anomaly_indicators,
            top_errors=top_errors,
            slow_operations=slow_operations,
            resource_alerts=resource_alerts,
            estimated_tokens=estimated_tokens,
        )

    def compress_for_fast_agent(
        self,
        window: TelemetryWindow,
        max_tokens: int = 500,
    ) -> str:
        """
        Ultra-compact compression for fast agent annotation.

        Args:
            window: Telemetry window
            max_tokens: Maximum tokens

        Returns:
            Compact string representation
        """
        compressed = self.compress_window(window)

        # Build ultra-compact format
        parts = []

        parts.append(f"T:{window.duration_minutes:.0f}m")
        parts.append(f"E:{compressed.error_count}")
        parts.append(f"W:{compressed.warning_count}")

        if compressed.top_errors:
            # Just first error, truncated
            parts.append(f"ERR:{compressed.top_errors[0][:50]}")

        if compressed.anomaly_indicators:
            parts.append(f"ANO:{','.join(compressed.anomaly_indicators[:3])}")

        result = "|".join(parts)

        # Truncate if needed
        max_chars = int(max_tokens * self.chars_per_token)
        if len(result) > max_chars:
            result = result[:max_chars - 3] + "..."

        return result

    def compress_for_reasoning_agent(
        self,
        window: TelemetryWindow,
        max_tokens: int = 1500,
    ) -> str:
        """
        Detailed compression for reasoning agent RCA.

        Args:
            window: Telemetry window
            max_tokens: Maximum tokens

        Returns:
            Detailed string representation
        """
        compressed = self.compress_window(window)
        return compressed.to_prompt_text()

    def _format_time_range(self, start: datetime, end: datetime) -> str:
        """Format time range concisely."""
        duration_mins = (end - start).total_seconds() / 60
        return f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')} ({duration_mins:.0f}m)"

    def _compress_logs(
        self,
        logs: list[LogEntry],
    ) -> tuple[str, list[str], int, int]:
        """
        Compress log entries.

        Returns:
            (summary, top_errors, error_count, warning_count)
        """
        if not logs:
            return "No logs", [], 0, 0

        # Count by level
        level_counts = Counter(log.level.lower() for log in logs)
        error_count = sum(level_counts.get(lvl, 0) for lvl in ["error", "fatal", "critical"])
        warning_count = sum(level_counts.get(lvl, 0) for lvl in ["warn", "warning"])

        # Extract unique error messages (deduplicate)
        error_messages: dict[str, int] = {}
        for log in logs:
            if log.level.lower() in ("error", "fatal", "critical"):
                # Normalize message (remove timestamps, IDs)
                normalized = self._normalize_log_message(log.message)
                error_messages[normalized] = error_messages.get(normalized, 0) + 1

        # Get top errors by frequency
        top_errors = sorted(
            error_messages.keys(),
            key=lambda x: error_messages[x],
            reverse=True,
        )[:5]

        # Truncate error messages
        top_errors = [self._truncate(msg, 100) for msg in top_errors]

        # Build summary
        total = len(logs)
        summary = f"{total} logs ({error_count} errors, {warning_count} warnings)"

        return summary, top_errors, error_count, warning_count

    def _compress_metrics(
        self,
        metrics: list[MetricPoint],
    ) -> tuple[str, list[str]]:
        """
        Compress metrics.

        Returns:
            (summary, resource_alerts)
        """
        if not metrics:
            return "No metrics", []

        # Group by metric name
        metric_groups: dict[str, list[float]] = {}
        for m in metrics:
            name = m.name
            if name not in metric_groups:
                metric_groups[name] = []
            metric_groups[name].append(m.value)

        # Detect alerts
        resource_alerts = []

        # Check for high values
        for name, values in metric_groups.items():
            if not values:
                continue

            max_val = max(values)
            avg_val = sum(values) / len(values)

            # Memory alerts (assuming bytes)
            if "memory" in name.lower() and max_val > 0.9:
                resource_alerts.append(f"High memory: {max_val:.1%}")

            # CPU alerts
            if "cpu" in name.lower() and max_val > 0.8:
                resource_alerts.append(f"High CPU: {max_val:.1%}")

            # Error rate alerts
            if "error" in name.lower() and "rate" in name.lower() and max_val > 0.05:
                resource_alerts.append(f"High error rate: {max_val:.2%}")

            # Latency alerts (assuming seconds)
            if "duration" in name.lower() or "latency" in name.lower():
                if max_val > 1.0:  # > 1 second
                    resource_alerts.append(f"High latency: {max_val*1000:.0f}ms")

        # Build summary
        summary_parts = []
        for name, values in list(metric_groups.items())[:5]:
            if values:
                avg = sum(values) / len(values)
                summary_parts.append(f"{self._short_metric_name(name)}={avg:.2f}")

        summary = ", ".join(summary_parts) if summary_parts else "No significant metrics"

        return summary, resource_alerts[:5]

    def _compress_traces(
        self,
        traces: list[TraceSpan],
    ) -> tuple[str, list[str]]:
        """
        Compress traces.

        Returns:
            (summary, slow_operations)
        """
        if not traces:
            return "No traces", []

        # Find slow operations
        sorted_by_duration = sorted(traces, key=lambda t: t.duration_ms, reverse=True)
        slow_ops = []

        for trace in sorted_by_duration[:5]:
            if trace.duration_ms > 100:  # > 100ms
                slow_ops.append(f"{trace.operation}: {trace.duration_ms:.0f}ms")

        # Calculate statistics
        durations = [t.duration_ms for t in traces]
        avg_duration = sum(durations) / len(durations) if durations else 0
        error_traces = sum(1 for t in traces if t.status != "OK")

        summary = f"{len(traces)} spans, avg {avg_duration:.0f}ms, {error_traces} errors"

        return summary, slow_ops

    def _detect_anomalies(self, window: TelemetryWindow) -> list[str]:
        """Detect anomalous patterns in telemetry."""
        anomalies = []

        # High error rate
        if window.log_count > 0:
            error_rate = window.error_count / window.log_count
            if error_rate > 0.1:
                anomalies.append(f"high_error_rate:{error_rate:.1%}")

        # Sudden spike in warnings
        if window.warning_count > 50:
            anomalies.append(f"warning_spike:{window.warning_count}")

        # Check log patterns
        if window.logs:
            messages = " ".join(log.message.lower() for log in window.logs[:100])

            if "connection refused" in messages:
                anomalies.append("connection_refused")
            if "out of memory" in messages or "oom" in messages:
                anomalies.append("memory_pressure")
            if "timeout" in messages:
                anomalies.append("timeouts_detected")
            if "disk full" in messages or "no space" in messages:
                anomalies.append("disk_full")
            if "certificate" in messages and ("expired" in messages or "invalid" in messages):
                anomalies.append("cert_issue")

        # Check traces for errors
        if window.traces:
            trace_errors = sum(1 for t in window.traces if t.status != "OK")
            if trace_errors > len(window.traces) * 0.1:
                anomalies.append(f"trace_errors:{trace_errors}")

        return anomalies[:10]

    def _normalize_log_message(self, message: str) -> str:
        """
        Normalize log message for deduplication.

        Removes:
        - Timestamps
        - UUIDs
        - IP addresses
        - Numeric IDs
        """
        # Remove timestamps
        message = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.\d]*Z?', '[TIME]', message)

        # Remove UUIDs
        message = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '[UUID]', message, flags=re.I)

        # Remove IP addresses
        message = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '[IP]', message)

        # Remove numeric IDs (sequences of digits)
        message = re.sub(r'\b\d{6,}\b', '[ID]', message)

        # Remove port numbers
        message = re.sub(r':\d{4,5}\b', ':[PORT]', message)

        return message.strip()

    def _short_metric_name(self, name: str) -> str:
        """Shorten metric name for display."""
        # Remove common prefixes
        for prefix in ["container_", "http_", "node_", "process_"]:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        # Truncate
        if len(name) > 20:
            name = name[:17] + "..."

        return name

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis."""
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."


__all__ = ["CompressedTelemetry", "TokenCompressor"]
