"""
Tests for the GET /api/v1/infrastructure/remote-hosts endpoint.

Exercises the data-merging logic (Prometheus + Loki) using mocked
HTTP clients.  No real network calls are made.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_mock_request(collector=None):
    """Build a minimal FastAPI Request-like mock."""
    req = MagicMock()
    req.app.state.telemetry_collector = collector
    return req


def _prom_count_response(edges: list[tuple[str, int]]):
    """Fake Prometheus 'count by (edge) (up)' response."""
    results = [
        {"metric": {"edge": edge}, "value": [1700000000, str(count)]}
        for edge, count in edges
    ]
    return {"data": {"result": results}}


def _loki_label_values_response(edges: list[str]):
    return {"data": edges}


def _loki_query_range_response(n_lines: int):
    """Fake Loki query_range response with n_lines values."""
    values = [
        [str(1700000000000000000 + i * 1_000_000_000), f"log line {i}"]
        for i in range(n_lines)
    ]
    return {
        "data": {
            "result": [{"stream": {}, "values": values}]
        }
    }


# ── tests ─────────────────────────────────────────────────────────────────────

class TestRemoteHostsEndpoint:

    @pytest.mark.asyncio
    async def test_no_collector_returns_empty(self):
        from src.api.routes.infrastructure import get_remote_hosts

        req = _make_mock_request(collector=None)
        result = await get_remote_hosts(req)

        assert result.total == 0
        assert result.hosts == []
        assert result.source == "none"

    @pytest.mark.asyncio
    async def test_prometheus_only_discovers_edges(self):
        """Prometheus returns two edge labels; Loki label-values call fails."""
        from src.api.routes.infrastructure import get_remote_hosts
        from src.telemetry.collector import TelemetryCollector

        collector = TelemetryCollector(
            loki_url="http://mock-loki:3100",
            prometheus_url="http://mock-prom:9090",
            tempo_url="http://mock-tempo:3200",
        )

        # Map each call URL pattern to a canned response.
        # NOTE: Use "mock-prom" / "mock-loki" to distinguish hosts, since
        # "api/v1/query" is a substring of both Prometheus and Loki query_range URLs.
        call_counter = {"n": 0}

        async def fake_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()

            if "mock-prom" in url:
                # Prometheus instant query calls:
                # 1st call: count by (edge) (up)
                # 2nd/3rd call: totals + timestamps
                call_counter["n"] += 1
                n = call_counter["n"]
                if n == 1:
                    resp.json.return_value = _prom_count_response(
                        [("prod-host-1", 3), ("staging-host-2", 1)]
                    )
                else:
                    resp.json.return_value = {"data": {"result": []}}
            elif "label/edge/values" in url:
                # Loki label-values — return same labels
                resp.json.return_value = _loki_label_values_response(
                    ["prod-host-1", "staging-host-2"]
                )
            elif "query_range" in url:
                resp.json.return_value = _loki_query_range_response(5)
            else:
                resp.json.return_value = {"data": {"result": []}}
            return resp

        with patch.object(collector._client, "get", side_effect=fake_get):
            req = _make_mock_request(collector=collector)
            result = await get_remote_hosts(req)

        await collector.close()

        assert result.total == 2
        edge_labels = {h.edge_label for h in result.hosts}
        assert "prod-host-1" in edge_labels
        assert "staging-host-2" in edge_labels

    @pytest.mark.asyncio
    async def test_host_status_up_when_targets_up(self):
        """A host with targets_up > 0 should have status='up'."""
        from src.api.routes.infrastructure import get_remote_hosts
        from src.telemetry.collector import TelemetryCollector

        collector = TelemetryCollector(
            loki_url="http://mock-loki:3100",
            prometheus_url="http://mock-prom:9090",
            tempo_url="http://mock-tempo:3200",
        )

        call_counter = {"n": 0}

        async def fake_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            if "mock-prom" in url:
                call_counter["n"] += 1
                n = call_counter["n"]
                if n == 1:
                    resp.json.return_value = _prom_count_response([("healthy-host", 2)])
                else:
                    resp.json.return_value = {"data": {"result": []}}
            elif "label/edge/values" in url:
                resp.json.return_value = {"data": []}
            else:
                resp.json.return_value = {"data": {"result": []}}
            return resp

        with patch.object(collector._client, "get", side_effect=fake_get):
            req = _make_mock_request(collector=collector)
            result = await get_remote_hosts(req)

        await collector.close()

        host = next(h for h in result.hosts if h.edge_label == "healthy-host")
        assert host.status == "up"
        assert host.targets_up == 2

    @pytest.mark.asyncio
    async def test_host_status_unknown_when_only_loki_data(self):
        """
        If Prometheus has no data for an edge label but Loki reports log lines,
        the status should be 'up' (data is flowing).
        """
        from src.api.routes.infrastructure import get_remote_hosts
        from src.telemetry.collector import TelemetryCollector

        collector = TelemetryCollector(
            loki_url="http://mock-loki:3100",
            prometheus_url="http://mock-prom:9090",
            tempo_url="http://mock-tempo:3200",
        )

        async def fake_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            # Use host-based discrimination — "api/v1/query" is a substring of
            # Loki's query_range URL so we cannot use it as the first condition.
            if "mock-prom" in url:
                resp.json.return_value = {"data": {"result": []}}
            elif "label/edge/values" in url:
                resp.json.return_value = _loki_label_values_response(["loki-only-host"])
            elif "query_range" in url:
                resp.json.return_value = _loki_query_range_response(10)
            else:
                resp.json.return_value = {"data": {"result": []}}
            return resp

        with patch.object(collector._client, "get", side_effect=fake_get):
            req = _make_mock_request(collector=collector)
            result = await get_remote_hosts(req)

        await collector.close()

        host = next((h for h in result.hosts if h.edge_label == "loki-only-host"), None)
        assert host is not None
        # Logs arrived → status should be "up"
        assert host.status == "up"
        assert host.recent_log_lines == 10

    @pytest.mark.asyncio
    async def test_loki_and_prometheus_merged(self):
        """
        An edge label present in BOTH Loki and Prometheus should appear once
        in the result (no duplicates).
        """
        from src.api.routes.infrastructure import get_remote_hosts
        from src.telemetry.collector import TelemetryCollector

        collector = TelemetryCollector(
            loki_url="http://mock-loki:3100",
            prometheus_url="http://mock-prom:9090",
            tempo_url="http://mock-tempo:3200",
        )

        call_counter = {"n": 0}

        async def fake_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            # Use host-based discrimination — "api/v1/query" is a substring of
            # Loki's query_range URL so we cannot use it as the first condition.
            if "mock-prom" in url:
                call_counter["n"] += 1
                n = call_counter["n"]
                if n == 1:
                    resp.json.return_value = _prom_count_response([("shared-host", 1)])
                else:
                    resp.json.return_value = {"data": {"result": []}}
            elif "label/edge/values" in url:
                resp.json.return_value = _loki_label_values_response(["shared-host"])
            elif "query_range" in url:
                resp.json.return_value = _loki_query_range_response(3)
            else:
                resp.json.return_value = {"data": {"result": []}}
            return resp

        with patch.object(collector._client, "get", side_effect=fake_get):
            req = _make_mock_request(collector=collector)
            result = await get_remote_hosts(req)

        await collector.close()

        # Must appear exactly once despite being in both stores
        shared_hosts = [h for h in result.hosts if h.edge_label == "shared-host"]
        assert len(shared_hosts) == 1
        assert shared_hosts[0].recent_log_lines == 3

    @pytest.mark.asyncio
    async def test_source_field_reflects_stores_queried(self):
        """source field should contain 'prometheus' when Prometheus is reachable."""
        from src.api.routes.infrastructure import get_remote_hosts
        from src.telemetry.collector import TelemetryCollector

        collector = TelemetryCollector(
            loki_url="http://mock-loki:3100",
            prometheus_url="http://mock-prom:9090",
            tempo_url="http://mock-tempo:3200",
        )

        call_counter = {"n": 0}

        async def fake_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            if "mock-prom" in url:
                call_counter["n"] += 1
                n = call_counter["n"]
                if n == 1:
                    resp.json.return_value = _prom_count_response([("host-a", 1)])
                else:
                    resp.json.return_value = {"data": {"result": []}}
            elif "label/edge/values" in url:
                resp.json.return_value = {"data": []}
            else:
                resp.json.return_value = {"data": {"result": []}}
            return resp

        with patch.object(collector._client, "get", side_effect=fake_get):
            req = _make_mock_request(collector=collector)
            result = await get_remote_hosts(req)

        await collector.close()

        assert "prometheus" in result.source
