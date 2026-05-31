"""
Tests for dismissing/restoring monitored remote hosts.

  DELETE /api/v1/infrastructure/remote-hosts/{edge_label}        → dismiss (denylist)
  POST   /api/v1/infrastructure/remote-hosts/{edge_label}/restore → undo
  GET    /api/v1/infrastructure/remote-hosts                      → filters dismissed

The denylist persists as JSON under AIOPS_DATA_DIR (stdlib only, no network).
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """Redirect the dismissed-hosts file to a fresh temp dir per test."""
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    yield tmp_path


def _make_mock_request(collector=None):
    req = MagicMock()
    req.app.state.telemetry_collector = collector
    return req


class TestDismissPersistence:
    def test_load_empty_when_no_file(self, tmp_data_dir):
        from src.api.routes.infrastructure import _load_dismissed_hosts
        assert _load_dismissed_hosts() == set()

    @pytest.mark.asyncio
    async def test_dismiss_then_restore_roundtrip(self, tmp_data_dir):
        from src.api.routes.infrastructure import (
            dismiss_remote_host,
            restore_remote_host,
            _load_dismissed_hosts,
        )
        r = await dismiss_remote_host("cred-rotate-test")
        assert r.dismissed is True
        assert _load_dismissed_hosts() == {"cred-rotate-test"}

        r2 = await restore_remote_host("cred-rotate-test")
        assert r2.dismissed is False
        assert _load_dismissed_hosts() == set()

    @pytest.mark.asyncio
    async def test_dismiss_blank_label_rejected(self, tmp_data_dir):
        from fastapi import HTTPException
        from src.api.routes.infrastructure import dismiss_remote_host
        with pytest.raises(HTTPException):
            await dismiss_remote_host("   ")


class TestDismissedFilteredFromList:
    @pytest.mark.asyncio
    async def test_dismissed_edge_is_hidden(self, tmp_data_dir):
        from src.api.routes.infrastructure import get_remote_hosts, dismiss_remote_host
        from src.telemetry.collector import TelemetryCollector

        collector = TelemetryCollector(
            loki_url="http://mock-loki:3100",
            prometheus_url="http://mock-prom:9090",
            tempo_url="http://mock-tempo:3200",
        )

        prom_calls = {"n": 0}

        async def fake_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            if "mock-prom" in url:
                prom_calls["n"] += 1
                if prom_calls["n"] == 1:
                    resp.json.return_value = {
                        "data": {"result": [
                            {"metric": {"edge": "keep-host"}, "value": [1700000000, "2"]},
                            {"metric": {"edge": "cred-rotate-test"}, "value": [1700000000, "0"]},
                        ]}
                    }
                else:
                    resp.json.return_value = {"data": {"result": []}}
            elif "label/edge/values" in url:
                resp.json.return_value = {"data": ["keep-host", "cred-rotate-test"]}
            elif "query_range" in url:
                resp.json.return_value = {"data": {"result": []}}
            else:
                resp.json.return_value = {"data": {"result": []}}
            return resp

        # Dismiss one of the two edges, then list.
        await dismiss_remote_host("cred-rotate-test")
        with patch.object(collector._client, "get", side_effect=fake_get):
            result = await get_remote_hosts(_make_mock_request(collector))
        await collector.close()

        labels = [h.edge_label for h in result.hosts]
        assert "keep-host" in labels
        assert "cred-rotate-test" not in labels
