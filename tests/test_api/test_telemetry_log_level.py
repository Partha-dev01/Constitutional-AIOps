"""
Tests for Loki log-level parsing fix and the container-label pipeline.

Verifies that _parse_log_level extracts the level correctly from both
Loki stream labels (when available) and from the log message body
(the common case for Docker/promtail pipelines where the level label
is not set or defaults to "info").

Also verifies the `container` label path end-to-end:
- promtail-config.yaml now derives `container` from
  `__meta_docker_container_name` (via docker_sd_configs + relabel_configs),
  mirroring the Alloy edge agent rule in monitoring-agent/config.alloy:32-36.
- The collector's query_logs builds a `{container=~…}` LogQL selector (not
  `job=containerlogs`) so both local and remote streams are visible.
- The collector maps the `container` stream label to LogEntry.service so
  callers get the real container name rather than a query fallback.
"""

import pytest
from src.telemetry.collector import _parse_log_level


class TestParseLoglevel:
    """Tests for the _parse_log_level helper."""

    # ── Label-based extraction ────────────────────────────────────────────────

    def test_explicit_error_label(self):
        assert _parse_log_level({"level": "error"}, "some message") == "ERROR"

    def test_explicit_warn_label(self):
        assert _parse_log_level({"level": "warn"}, "some message") == "WARN"

    def test_explicit_warning_label(self):
        assert _parse_log_level({"level": "warning"}, "some message") == "WARN"

    def test_explicit_debug_label(self):
        assert _parse_log_level({"level": "debug"}, "some message") == "DEBUG"

    def test_explicit_info_label_trusts_label(self):
        # When a structured logger explicitly sets level=info, honour it.
        assert _parse_log_level({"level": "info"}, "some message") == "INFO"

    def test_fatal_label_normalised_to_error(self):
        assert _parse_log_level({"level": "fatal"}, "") == "ERROR"

    def test_critical_label_normalised_to_error(self):
        assert _parse_log_level({"level": "critical"}, "") == "ERROR"

    def test_uppercase_label(self):
        assert _parse_log_level({"level": "ERROR"}, "msg") == "ERROR"

    # ── Message-body regex extraction (the broken path before the fix) ────────

    def test_message_error_keyword(self):
        # Common Docker / unstructured log format
        msg = "2025-12-14T10:23:45Z ERROR [api-gateway] Connection refused to database:5432"
        assert _parse_log_level({}, msg) == "ERROR"

    def test_message_warn_keyword(self):
        msg = "2025-12-14T10:23:47Z WARN [api-gateway] Retry attempt 3/5"
        assert _parse_log_level({}, msg) == "WARN"

    def test_message_debug_keyword(self):
        msg = "DEBUG initialising config loader"
        assert _parse_log_level({}, msg) == "DEBUG"

    def test_message_warning_keyword_normalised(self):
        msg = "[WARNING] disk usage at 91%"
        assert _parse_log_level({}, msg) == "WARN"

    def test_message_info_keyword(self):
        msg = "INFO server started on port 8080"
        assert _parse_log_level({}, msg) == "INFO"

    def test_message_case_insensitive(self):
        msg = "error: connection pool exhausted"
        assert _parse_log_level({}, msg) == "ERROR"

    def test_no_label_no_keyword_defaults_to_info(self):
        msg = "server started on port 8080"
        assert _parse_log_level({}, msg) == "INFO"

    def test_empty_label_falls_back_to_message(self):
        # promtail may emit {"level": ""} when it cannot detect a level
        msg = "ERROR [svc] bad gateway"
        assert _parse_log_level({"level": ""}, msg) == "ERROR"

    def test_default_info_label_does_not_mask_message_error(self):
        # When the stream label says "info" (the promtail default) but the log
        # message contains a clear level keyword, the regex wins.  This is the
        # primary use-case of the fix: Docker/promtail pipelines where the level
        # label is always "info" regardless of the actual log level in the line.
        msg = "2025-01-01 ERROR [db] query timeout"
        # label "info" is the ambiguous default → regex falls through and returns ERROR
        assert _parse_log_level({"level": "info"}, msg) == "ERROR"
        # Empty label → also falls through to regex
        assert _parse_log_level({"level": ""}, msg) == "ERROR"

    def test_fatal_in_message(self):
        msg = "FATAL signal: killed"
        assert _parse_log_level({}, msg) == "ERROR"


class TestQueryLogsLevelIntegration:
    """
    Integration-style tests for query_logs level extraction using a mocked
    Loki HTTP response.  Verifies that the collector correctly maps stream
    labels + message content to normalised log levels.
    """

    @pytest.mark.asyncio
    async def test_query_logs_extracts_error_from_message(self):
        """
        Simulates a Loki response where the stream has no 'level' label
        (typical for Docker containers with promtail).  The collector must
        extract the level from the log message.

        The `container` label in the mocked stream payload represents what
        promtail now emits after the docker_sd_configs + relabel_configs fix in
        promtail-config.yaml (rule: __meta_docker_container_name → container,
        mirroring monitoring-agent/config.alloy:32-36).  The collector's
        query_logs must:
          1. build a {container=~"…"} selector (not job="containerlogs"), and
          2. map the `container` stream label to LogEntry.service.
        """
        import httpx
        from unittest.mock import AsyncMock, MagicMock, patch, call
        from datetime import datetime, timezone

        from src.telemetry.collector import TelemetryCollector

        # This payload represents a real promtail docker_sd stream: the
        # `container` label is set by the relabel rule (not injected by the
        # test), and there is no hand-added level label — level comes from
        # the log message body via _parse_log_level.
        loki_payload = {
            "data": {
                "result": [
                    {
                        "stream": {
                            "job": "containerlogs",
                            # `container` is now set by promtail's relabel rule
                            # (__meta_docker_container_name → container).
                            # This label is what the collector's {container=~…}
                            # selector matches against.
                            "container": "aiops-nextcloud",
                            # No 'level' key — promtail raw Docker logs
                        },
                        "values": [
                            ["1700000001000000000", "ERROR [nextcloud] disk quota exceeded"],
                            ["1700000002000000000", "WARN [nextcloud] cache miss rate high"],
                            ["1700000003000000000", "DEBUG [nextcloud] request received"],
                            ["1700000004000000000", "INFO [nextcloud] user logged in"],
                            ["1700000005000000000", "plain log line with no keyword"],
                        ],
                    }
                ]
            }
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = loki_payload

        collector = TelemetryCollector(
            loki_url="http://mock-loki:3100",
            prometheus_url="http://mock-prom:9090",
            tempo_url="http://mock-tempo:3200",
        )

        mock_get = AsyncMock(return_value=mock_response)
        with patch.object(collector._client, "get", mock_get):
            logs = await collector.query_logs(
                service="nextcloud",
                start_time=datetime(2023, 11, 14, tzinfo=timezone.utc),
                end_time=datetime(2023, 11, 15, tzinfo=timezone.utc),
            )

        await collector.close()

        # ── Level extraction from message body ─────────────────────────────
        assert len(logs) == 5
        levels = [e.level for e in logs]
        assert levels[0] == "ERROR"
        assert levels[1] == "WARN"
        assert levels[2] == "DEBUG"
        assert levels[3] == "INFO"
        assert levels[4] == "INFO"  # no keyword → defaults INFO

        # ── Prove the `container` label flows to LogEntry.service ──────────
        # The collector maps labels["container"] → LogEntry.service so callers
        # can identify which container a log came from using the same label
        # that promtail's docker_sd_configs relabel rule now emits.
        assert all(e.service == "aiops-nextcloud" for e in logs), (
            "LogEntry.service must be populated from the 'container' stream "
            "label (set by promtail's relabel rule), not a fallback string."
        )

        # ── Prove the collector queries by container= (not job=) ───────────
        # The {container=~"…"} selector is what makes both local (promtail)
        # and remote (Alloy) logs visible; the old job="containerlogs" query
        # silently dropped all edge-agent streams.
        called_url = mock_get.call_args[0][0]
        called_params = mock_get.call_args[1].get("params", mock_get.call_args[0][1] if len(mock_get.call_args[0]) > 1 else {})
        loki_query = called_params.get("query", "")
        assert "container" in loki_query, (
            f"Loki selector must filter by 'container' label; got: {loki_query!r}"
        )
        assert "job" not in loki_query, (
            f"Loki selector must NOT filter by 'job' (drops edge streams); got: {loki_query!r}"
        )

    @pytest.mark.asyncio
    async def test_query_logs_honours_stream_level_label(self):
        """
        When the Loki stream already has a proper 'level' label (e.g. from a
        structured logger), it takes priority over the message body.
        """
        import httpx
        from unittest.mock import AsyncMock, MagicMock, patch
        from datetime import datetime, timezone

        from src.telemetry.collector import TelemetryCollector

        loki_payload = {
            "data": {
                "result": [
                    {
                        "stream": {
                            "level": "error",
                            "service": "api-gateway",
                        },
                        "values": [
                            ["1700000001000000000", "INFO this is actually an error stream"],
                        ],
                    }
                ]
            }
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = loki_payload

        collector = TelemetryCollector(
            loki_url="http://mock-loki:3100",
            prometheus_url="http://mock-prom:9090",
            tempo_url="http://mock-tempo:3200",
        )

        mock_get = AsyncMock(return_value=mock_response)
        with patch.object(collector._client, "get", mock_get):
            logs = await collector.query_logs(
                service="api-gateway",
                start_time=datetime(2023, 11, 14, tzinfo=timezone.utc),
                end_time=datetime(2023, 11, 15, tzinfo=timezone.utc),
            )

        await collector.close()

        assert len(logs) == 1
        # level label "error" should win over "INFO" in the message body
        assert logs[0].level == "ERROR"


class TestMetricsSummaryFilter:
    """
    Tests that the /metrics summary path honours the service/edge filter
    and does NOT hard-default to 'nextcloud'.

    Previously telemetry.py:186 set `service_name = service or "nextcloud"`,
    causing the summary to always scope to a single demo host.  After the fix
    the caller passes the actual service value (or None for all-hosts), and
    collector.py builds filtered PromQL selectors when a service is given.
    """

    @pytest.mark.asyncio
    async def test_summary_with_no_service_sends_global_queries(self):
        """
        When no service is specified the summary PromQL must be global
        (no edge/job filter) — the old hardcoded 'nextcloud' must not appear.
        """
        from unittest.mock import AsyncMock, MagicMock, patch
        from datetime import datetime, timezone

        from src.telemetry.collector import TelemetryCollector

        empty_prom_response = {"data": {"result": []}}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = empty_prom_response

        collector = TelemetryCollector(
            loki_url="http://mock-loki:3100",
            prometheus_url="http://mock-prom:9090",
            tempo_url="http://mock-tempo:3200",
        )

        mock_get = AsyncMock(return_value=mock_response)
        with patch.object(collector._client, "get", mock_get):
            await collector.query_metrics(
                service=None,
                start_time=datetime(2023, 11, 14, tzinfo=timezone.utc),
                end_time=datetime(2023, 11, 15, tzinfo=timezone.utc),
            )

        await collector.close()

        # All four summary queries must have been fired.
        assert mock_get.call_count == 4

        # None of the queries should reference "nextcloud" (the old hard default)
        for c in mock_get.call_args_list:
            params = c[1].get("params", {})
            q = params.get("query", "")
            assert "nextcloud" not in q, (
                f"Summary query must not hard-default to 'nextcloud'; got: {q!r}"
            )

    @pytest.mark.asyncio
    async def test_summary_with_service_scopes_promql_to_edge(self):
        """
        When a service/edge name is provided the summary PromQL selectors must
        include a label matcher for that name so the result is scoped to the
        requested host.
        """
        from unittest.mock import AsyncMock, MagicMock, patch
        from datetime import datetime, timezone

        from src.telemetry.collector import TelemetryCollector

        empty_prom_response = {"data": {"result": []}}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = empty_prom_response

        collector = TelemetryCollector(
            loki_url="http://mock-loki:3100",
            prometheus_url="http://mock-prom:9090",
            tempo_url="http://mock-tempo:3200",
        )

        mock_get = AsyncMock(return_value=mock_response)
        with patch.object(collector._client, "get", mock_get):
            await collector.query_metrics(
                service="my-edge-host",
                start_time=datetime(2023, 11, 14, tzinfo=timezone.utc),
                end_time=datetime(2023, 11, 15, tzinfo=timezone.utc),
            )

        await collector.close()

        assert mock_get.call_count == 4

        # Every summary query must contain the requested service/edge name so
        # the Metrics panel is scoped to the selected host.
        for c in mock_get.call_args_list:
            params = c[1].get("params", {})
            q = params.get("query", "")
            assert "my-edge-host" in q, (
                f"Summary query must contain the requested service filter; got: {q!r}"
            )
