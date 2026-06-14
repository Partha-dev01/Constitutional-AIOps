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
# Remediation section (Lane B)
# ---------------------------------------------------------------------------

class TestRemediationSettings:
    def test_defaults_present_in_default_settings(self):
        from src.api.routes.settings import DEFAULT_SETTINGS
        rem = DEFAULT_SETTINGS["remediation"]
        assert rem == {
            "mode": "diagnose",
            "autoConfidenceThreshold": 90,
            "requireEvidenceForAuto": True,
            "demoTargetUrl": "",
        }

    def test_get_remediation_settings_returns_defaults(self, tmp_settings_dir):
        from src.api.routes.settings import get_remediation_settings
        rem = get_remediation_settings()
        assert rem["mode"] == "diagnose"
        assert rem["autoConfidenceThreshold"] == 90
        assert rem["requireEvidenceForAuto"] is True
        assert rem["demoTargetUrl"] == ""

    def test_get_remediation_settings_overlays_persisted(self, tmp_settings_dir):
        from src.api.routes.settings import get_remediation_settings, _save_persisted
        _save_persisted({"remediation": {"mode": "auto", "demoTargetUrl": "http://t3:8080"}})
        rem = get_remediation_settings()
        # Overridden keys win...
        assert rem["mode"] == "auto"
        assert rem["demoTargetUrl"] == "http://t3:8080"
        # ...and missing keys still come from defaults (deep-merge upgrade path).
        assert rem["autoConfidenceThreshold"] == 90
        assert rem["requireEvidenceForAuto"] is True

    def test_legacy_file_without_remediation_upgrades(self, tmp_settings_dir):
        """A persisted file predating this section must still expose remediation."""
        from src.api.routes.settings import get_remediation_settings, _save_persisted
        _save_persisted({"constitutional": {"autoThreshold": 88}})  # no remediation key
        rem = get_remediation_settings()
        assert rem["mode"] == "diagnose"
        assert rem["autoConfidenceThreshold"] == 90

    def test_model_default_and_validation_bounds(self):
        from src.api.routes.settings import RemediationSettingsModel
        import pytest as _pytest
        from pydantic import ValidationError

        default = RemediationSettingsModel()
        assert default.mode == "diagnose"
        assert default.autoConfidenceThreshold == 90
        assert default.requireEvidenceForAuto is True
        assert default.demoTargetUrl == ""

        # Valid custom values.
        ok = RemediationSettingsModel(
            mode="auto", autoConfidenceThreshold=70, requireEvidenceForAuto=False,
            demoTargetUrl="http://x",
        )
        assert ok.mode == "auto"
        assert ok.autoConfidenceThreshold == 70

        # mode must be one of the three literals.
        with _pytest.raises(ValidationError):
            RemediationSettingsModel(mode="nuke")
        # autoConfidenceThreshold bounds: ge=70, le=99.
        with _pytest.raises(ValidationError):
            RemediationSettingsModel(autoConfidenceThreshold=69)
        with _pytest.raises(ValidationError):
            RemediationSettingsModel(autoConfidenceThreshold=100)


# ---------------------------------------------------------------------------
# Constitutional section helper + FE<->BE wiring (W2)
# ---------------------------------------------------------------------------

class TestConstitutionalSettingsHelper:
    def test_returns_defaults(self, tmp_settings_dir):
        from src.api.routes.settings import get_constitutional_settings
        const = get_constitutional_settings()
        assert const["autoThreshold"] == 90
        assert const["approvalThreshold"] == 70
        assert const["maxActionsPerMinute"] == 10
        assert const["enableAuditLog"] is True

    def test_overlays_persisted(self, tmp_settings_dir):
        from src.api.routes.settings import get_constitutional_settings, _save_persisted
        _save_persisted({"constitutional": {"maxActionsPerMinute": 3, "enableAuditLog": False}})
        const = get_constitutional_settings()
        assert const["maxActionsPerMinute"] == 3
        assert const["enableAuditLog"] is False
        # Missing keys still come from defaults (deep-merge upgrade path).
        assert const["autoThreshold"] == 90

    def test_legacy_file_without_constitutional_upgrades(self, tmp_settings_dir):
        from src.api.routes.settings import get_constitutional_settings, _save_persisted
        _save_persisted({"telemetry": {"retentionDays": 14}})  # no constitutional key
        const = get_constitutional_settings()
        assert const["autoThreshold"] == 90
        assert const["enableAuditLog"] is True


class TestRateLimitWiring:
    def test_rate_limiter_reads_persisted_max(self, tmp_settings_dir, monkeypatch):
        """W2.2: the chat auto-exec rate limiter honours persisted
        maxActionsPerMinute (previously a dead no-op)."""
        import src.api.routes.chat as chat
        from src.api.routes.settings import _save_persisted

        _save_persisted({"constitutional": {"maxActionsPerMinute": 2}})
        # Clear the rolling window so the count starts at zero.
        chat._auto_exec_times.clear()
        assert chat._auto_exec_max_per_min() == 2

        # Two exec records fit; the third is over the persisted cap of 2.
        chat._record_auto_exec()
        assert chat._auto_exec_rate_ok() is True
        chat._record_auto_exec()
        assert chat._auto_exec_rate_ok() is False
        chat._auto_exec_times.clear()

    def test_rate_limiter_falls_back_to_env_default(self, tmp_settings_dir):
        import src.api.routes.chat as chat
        # No persisted constitutional.maxActionsPerMinute override beyond default(10).
        assert chat._auto_exec_max_per_min() == 10


class TestAuditEnabledWiring:
    def test_chat_audit_helper_reads_persisted(self, tmp_settings_dir):
        """W2.3: enableAuditLog is now sourced from settings, not hardcoded."""
        import src.api.routes.chat as chat
        from src.api.routes.settings import _save_persisted

        _save_persisted({"constitutional": {"enableAuditLog": False}})
        assert chat._audit_enabled() is False
        _save_persisted({"constitutional": {"enableAuditLog": True}})
        assert chat._audit_enabled() is True

    def test_incidents_and_actions_audit_helpers(self, tmp_settings_dir):
        import src.api.routes.incidents as incidents
        import src.api.routes.actions as actions
        from src.api.routes.settings import _save_persisted

        _save_persisted({"constitutional": {"enableAuditLog": False}})
        assert incidents._audit_enabled() is False
        assert actions._audit_enabled() is False

    def test_audit_defaults_true_when_unset(self, tmp_settings_dir):
        import src.api.routes.chat as chat
        assert chat._audit_enabled() is True


class TestStartupThresholdLoad:
    def test_persisted_thresholds_applied_to_validator(self, tmp_settings_dir):
        """W2.1: the startup-load logic mirrors persisted thresholds onto a fresh
        validator so they survive a restart (asserted via the same
        get_constitutional_settings helper the lifespan uses)."""
        from unittest.mock import MagicMock
        from src.api.routes.settings import _save_persisted, get_constitutional_settings

        _save_persisted({"constitutional": {"autoThreshold": 80, "approvalThreshold": 60}})

        # Replicate the main.py lifespan startup-load block against a mock validator.
        validator = MagicMock()
        validator.confidence_threshold_auto = 0.90
        validator.confidence_threshold_approval = 0.70
        const = get_constitutional_settings()
        validator.confidence_threshold_auto = float(const["autoThreshold"]) / 100.0
        validator.confidence_threshold_approval = float(const["approvalThreshold"]) / 100.0

        assert abs(validator.confidence_threshold_auto - 0.80) < 1e-9
        assert abs(validator.confidence_threshold_approval - 0.60) < 1e-9

    def test_main_lifespan_has_startup_threshold_load(self):
        """Static check: the lifespan applies persisted constitutional thresholds."""
        main_src = Path(__file__).resolve().parents[2] / "src" / "main.py"
        text = main_src.read_text(encoding="utf-8")
        assert "get_constitutional_settings" in text
        assert "confidence_threshold_auto" in text


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

    @pytest.mark.asyncio
    async def test_get_includes_remediation_defaults(self, tmp_settings_dir):
        from src.api.routes.settings import get_settings, DEFAULT_SETTINGS
        result = await get_settings()
        assert result.remediation.mode == DEFAULT_SETTINGS["remediation"]["mode"]
        assert result.remediation.autoConfidenceThreshold == 90
        assert result.remediation.requireEvidenceForAuto is True
        assert result.remediation.demoTargetUrl == ""


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
        mock_request.app.state = MagicMock(spec=[])  # no validator attr

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
    async def test_save_remediation_roundtrips(self, tmp_settings_dir):
        from src.api.routes.settings import (
            save_settings,
            get_remediation_settings,
            AllSettings,
            RemediationSettingsModel,
        )

        mock_request = MagicMock()
        mock_request.app.state = MagicMock(spec=[])  # no validator attr

        body = AllSettings(
            remediation=RemediationSettingsModel(
                mode="approve",
                autoConfidenceThreshold=85,
                requireEvidenceForAuto=False,
                demoTargetUrl="http://t3:9000",
            ),
        )
        result = await save_settings(mock_request, body)
        assert result.remediation.mode == "approve"

        # Persisted + readable through the exported helper.
        rem = get_remediation_settings()
        assert rem["mode"] == "approve"
        assert rem["autoConfidenceThreshold"] == 85
        assert rem["requireEvidenceForAuto"] is False
        assert rem["demoTargetUrl"] == "http://t3:9000"

    @pytest.mark.asyncio
    async def test_save_remediation_persists_for_real_admin(self, tmp_settings_dir, monkeypatch):
        """Regression (found in live deploy validation): a REAL (non-synthetic)
        admin's remediation changes must persist. The auth-scoping branch
        originally wrote only constitutional + telemetry to the global file, so
        mode / threshold edits silently never stuck once AUTH_REQUIRED was on —
        the headline approve/auto feature was unconfigurable in production."""
        import src.api.routes.settings as settings_mod
        from src.api.routes.settings import (
            save_settings,
            get_remediation_settings,
            AllSettings,
            RemediationSettingsModel,
        )
        from src.auth.deps import User

        # A real DB admin (id is NOT the synthetic sentinel).
        admin = User(id="real-admin-1", username="admin", role="admin")
        # Don't touch the SQLite user store (notifications write).
        monkeypatch.setattr(settings_mod, "user_store", MagicMock())

        mock_request = MagicMock()
        mock_request.app.state = MagicMock(spec=[])  # no validator attr

        body = AllSettings(
            remediation=RemediationSettingsModel(mode="auto", autoConfidenceThreshold=95),
        )
        await save_settings(mock_request, body, admin)

        rem = get_remediation_settings()
        assert rem["mode"] == "auto"
        assert rem["autoConfidenceThreshold"] == 95

    @pytest.mark.asyncio
    async def test_save_updates_live_validator(self, tmp_settings_dir):
        from src.api.routes.settings import save_settings, AllSettings
        from src.api.routes.settings import (
            ConstitutionalSettingsModel,
            NotificationSettingsModel,
            TelemetrySettingsModel,
        )

        # Mock a live validator. main.py stores it as app.state.validator —
        # the route must read THAT attribute (a previous bug read the
        # nonexistent app.state.constitutional_validator and silently never
        # pushed thresholds).
        validator = MagicMock()
        validator.confidence_threshold_auto = 0.90
        validator.confidence_threshold_approval = 0.70

        mock_request = MagicMock()
        mock_request.app.state = MagicMock(spec=["validator"])
        mock_request.app.state.validator = validator

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
        """Ensure the settings router is wired into main.py.

        Verified by static inspection of main.py rather than importing the full
        app: importing src.main pulls in heavy runtime deps (e.g. langgraph)
        that are intentionally absent from the minimal CI install.
        """
        main_src = Path(__file__).resolve().parents[2] / "src" / "main.py"
        text = main_src.read_text(encoding="utf-8")
        assert "settings_router" in text, "settings router not imported in main.py"
        assert "include_router(settings_router" in text, (
            "No app.include_router(settings_router, ...) found in main.py"
        )
