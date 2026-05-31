"""
Tests for the Settings persistence endpoint.

Covers:
  GET  /api/v1/settings/   → returns AllSettings (merged with defaults)
  PUT  /api/v1/settings/   → persists and echoes back
  POST /api/v1/settings/reset → deletes file, returns defaults
  Validator live-update  → constitutional thresholds pushed to validator
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers to patch the storage path to a temp dir during tests
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_settings_dir(tmp_path, monkeypatch):
    """Redirect _settings_path() to a fresh temp directory for each test."""
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    yield tmp_path


# ---------------------------------------------------------------------------
# Unit tests for storage helpers (no FastAPI involved)
# ---------------------------------------------------------------------------

class TestStorageHelpers:
    def test_load_returns_empty_when_no_file(self, tmp_settings_dir):
        from src.api.routes.settings import _load_persisted
        assert _load_persisted() == {}

    def test_save_and_load_roundtrip(self, tmp_settings_dir):
        from src.api.routes.settings import _save_persisted, _load_persisted
        payload = {"constitutional": {"autoThreshold": 85}}
        _save_persisted(payload)
        loaded = _load_persisted()
        assert loaded == payload

    def test_load_survives_corrupt_file(self, tmp_settings_dir):
        from src.api.routes.settings import _load_persisted, _settings_path
        _settings_path().write_text("not valid json", encoding="utf-8")
        # Must not raise — should return empty dict
        result = _load_persisted()
        assert result == {}

    def test_merge_fills_missing_keys(self, tmp_settings_dir):
        from src.api.routes.settings import _merge_with_defaults, DEFAULT_SETTINGS
        # Only override one nested key
        partial = {"constitutional": {"autoThreshold": 95}}
        merged = _merge_with_defaults(partial)
        assert merged["constitutional"]["autoThreshold"] == 95
        # All default keys still present
        for key in DEFAULT_SETTINGS["constitutional"]:
            assert key in merged["constitutional"]
        # Other sections fully populated
        for key in DEFAULT_SETTINGS["notifications"]:
            assert key in merged["notifications"]


# ---------------------------------------------------------------------------
# FastAPI endpoint tests via async invocation
# ---------------------------------------------------------------------------

class TestGetSettings:
    @pytest.mark.asyncio
    async def test_get_returns_defaults_when_no_file(self, tmp_settings_dir):
        from src.api.routes.settings import get_settings, DEFAULT_SETTINGS
        result = await get_settings()
        assert result.constitutional.autoThreshold == DEFAULT_SETTINGS["constitutional"]["autoThreshold"]
        assert result.notifications.emailEnabled == DEFAULT_SETTINGS["notifications"]["emailEnabled"]
        assert result.telemetry.retentionDays == DEFAULT_SETTINGS["telemetry"]["retentionDays"]

    @pytest.mark.asyncio
    async def test_get_returns_persisted_values(self, tmp_settings_dir):
        from src.api.routes.settings import get_settings, _save_persisted
        _save_persisted({
            "constitutional": {"autoThreshold": 95, "approvalThreshold": 75,
                               "maxActionsPerMinute": 5, "enableAuditLog": False,
                               "enableLearning": False, "strictTier1": True},
        })
        result = await get_settings()
        assert result.constitutional.autoThreshold == 95
        assert result.constitutional.enableAuditLog is False


class TestPutSettings:
    @pytest.mark.asyncio
    async def test_save_persists_to_disk(self, tmp_settings_dir):
        from src.api.routes.settings import save_settings, _load_persisted, AllSettings
        from src.api.routes.settings import (
            ConstitutionalSettingsModel,
            NotificationSettingsModel,
            TelemetrySettingsModel,
        )

        mock_request = MagicMock()
        mock_request.app.state = MagicMock(spec=[])  # no constitutional_validator attr

        body = AllSettings(
            constitutional=ConstitutionalSettingsModel(autoThreshold=88),
            notifications=NotificationSettingsModel(emailEnabled=True),
            telemetry=TelemetrySettingsModel(retentionDays=60),
        )
        result = await save_settings(mock_request, body)

        assert result.constitutional.autoThreshold == 88
        assert result.notifications.emailEnabled is True
        assert result.telemetry.retentionDays == 60

        # Verify written to disk
        disk = _load_persisted()
        assert disk["constitutional"]["autoThreshold"] == 88

    @pytest.mark.asyncio
    async def test_save_updates_live_validator(self, tmp_settings_dir):
        from src.api.routes.settings import save_settings, AllSettings
        from src.api.routes.settings import (
            ConstitutionalSettingsModel,
            NotificationSettingsModel,
            TelemetrySettingsModel,
        )

        # Mock a live validator
        validator = MagicMock()
        validator.confidence_threshold_auto = 0.90
        validator.confidence_threshold_approval = 0.70

        mock_request = MagicMock()
        mock_request.app.state.constitutional_validator = validator

        body = AllSettings(
            constitutional=ConstitutionalSettingsModel(autoThreshold=85, approvalThreshold=65),
            notifications=NotificationSettingsModel(),
            telemetry=TelemetrySettingsModel(),
        )
        await save_settings(mock_request, body)

        # Validator thresholds updated
        assert abs(validator.confidence_threshold_auto - 0.85) < 1e-9
        assert abs(validator.confidence_threshold_approval - 0.65) < 1e-9


class TestResetSettings:
    @pytest.mark.asyncio
    async def test_reset_deletes_file_and_returns_defaults(self, tmp_settings_dir):
        from src.api.routes.settings import (
            reset_settings,
            _save_persisted,
            _load_persisted,
            DEFAULT_SETTINGS,
        )
        # Put something custom on disk
        _save_persisted({"constitutional": {"autoThreshold": 99}})
        assert _load_persisted() != {}

        result = await reset_settings()

        # File should be gone
        assert _load_persisted() == {}
        # Returned values are defaults
        assert result.constitutional.autoThreshold == DEFAULT_SETTINGS["constitutional"]["autoThreshold"]

    @pytest.mark.asyncio
    async def test_reset_idempotent_when_no_file(self, tmp_settings_dir):
        from src.api.routes.settings import reset_settings
        # Should not raise
        result = await reset_settings()
        assert result is not None


# ---------------------------------------------------------------------------
# Integration: router is registered in main app
# ---------------------------------------------------------------------------

class TestRouterRegistration:
    def test_settings_router_imported_in_main(self):
        """Ensure the settings router is actually wired up in main.py."""
        import importlib
        import src.main as main_mod
        # Check the app has the /api/v1/settings prefix registered
        routes = [r.path for r in main_mod.app.routes]
        settings_routes = [r for r in routes if "settings" in r]
        assert len(settings_routes) > 0, (
            "No settings routes found in app. Did you forget to add "
            "app.include_router(settings_router, ...) in main.py?"
        )
