"""
Constitutional AIOps - Settings API Routes

Persistent settings storage for Constitutional AI, Notifications, and Telemetry
configuration.  Uses a single JSON file under the app data directory (stdlib
json only — zero new deps).  Constitutional thresholds are written back to the
live ConstitutionalValidator instance on save.

Endpoints:
  GET  /api/v1/settings/          → return current merged settings
  PUT  /api/v1/settings/          → save settings, return saved values
  POST /api/v1/settings/reset     → wipe persisted file, return defaults
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.auth import store as user_store
from src.auth.deps import User, coerce_user, is_synthetic, require_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def _settings_path() -> Path:
    """Return the path to the persisted settings JSON file.

    Priority (first writable path wins):
      1. AIOPS_DATA_DIR env var (production bind-mount, e.g. /mnt/data/app)
      2. ./data/settings  (repo-local, works for local dev)
    """
    base = os.environ.get("AIOPS_DATA_DIR") or os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "settings"
    )
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path / "settings.json"


def _load_persisted() -> dict[str, Any]:
    """Load persisted settings from disk; return {} on any error."""
    try:
        p = _settings_path()
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read persisted settings: %s", exc)
    return {}


def _save_persisted(data: dict[str, Any]) -> None:
    """Write settings dict to disk (atomic-ish: write then rename)."""
    p = _settings_path()
    tmp = p.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(p)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist settings: %s", exc)


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

DEFAULT_SETTINGS: dict[str, Any] = {
    "constitutional": {
        "autoThreshold": 90,
        "approvalThreshold": 70,
        "maxActionsPerMinute": 10,
        "enableAuditLog": True,
        "enableLearning": True,
        "strictTier1": True,
    },
    "notifications": {
        "emailEnabled": False,
        "slackEnabled": False,
        "webhookEnabled": False,
        "webhookUrl": "",
        "notifyOnCritical": True,
        "notifyOnApproval": True,
        "notifyOnResolution": False,
    },
    "telemetry": {
        "lokiEnabled": True,
        "lokiUrl": "http://loki:3100",
        "prometheusEnabled": True,
        "prometheusUrl": "http://prometheus:9090",
        "tempoEnabled": True,
        "tempoUrl": "http://tempo:3200",
        "retentionDays": 30,
    },
}


def _merge_with_defaults(persisted: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge persisted on top of defaults so new keys always appear."""
    result: dict[str, Any] = {}
    for key, default_val in DEFAULT_SETTINGS.items():
        if isinstance(default_val, dict):
            merged_section: dict[str, Any] = dict(default_val)
            if key in persisted and isinstance(persisted[key], dict):
                merged_section.update(persisted[key])
            result[key] = merged_section
        else:
            result[key] = persisted.get(key, default_val)
    return result


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ConstitutionalSettingsModel(BaseModel):
    autoThreshold: int = Field(90, ge=70, le=99)
    approvalThreshold: int = Field(70, ge=50, le=89)
    maxActionsPerMinute: int = Field(10, ge=1, le=100)
    enableAuditLog: bool = True
    enableLearning: bool = True
    strictTier1: bool = True


class NotificationSettingsModel(BaseModel):
    emailEnabled: bool = False
    slackEnabled: bool = False
    webhookEnabled: bool = False
    webhookUrl: str = ""
    notifyOnCritical: bool = True
    notifyOnApproval: bool = True
    notifyOnResolution: bool = False


class TelemetrySettingsModel(BaseModel):
    lokiEnabled: bool = True
    lokiUrl: str = "http://loki:3100"
    prometheusEnabled: bool = True
    prometheusUrl: str = "http://prometheus:9090"
    tempoEnabled: bool = True
    tempoUrl: str = "http://tempo:3200"
    retentionDays: int = Field(30, ge=7, le=365)


class AllSettings(BaseModel):
    constitutional: ConstitutionalSettingsModel = ConstitutionalSettingsModel()
    notifications: NotificationSettingsModel = NotificationSettingsModel()
    telemetry: TelemetrySettingsModel = TelemetrySettingsModel()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=AllSettings,
    summary="Get Settings",
    description="Return current persisted settings (merged with defaults for any missing keys).",
)
async def get_settings(user: User = Depends(require_user)) -> AllSettings:
    """Return current settings, merging persisted file with built-in defaults.

    For a REAL DB user the per-user `notifications` row (if any) is overlaid
    on the global values; the pre-rollout synthetic admin keeps reading the
    global file only — zero behavior change until AUTH_REQUIRED flips.
    """
    user = coerce_user(user)
    merged = _merge_with_defaults(_load_persisted())
    if not is_synthetic(user):
        try:
            per_user = user_store.get_user_settings(user.id) or {}
            notifications = per_user.get("notifications")
            if isinstance(notifications, dict):
                merged["notifications"].update(notifications)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to read per-user settings for %s: %s", user.username, exc)
    return AllSettings(**merged)


@router.put(
    "/",
    response_model=AllSettings,
    summary="Save Settings",
    description="Persist all settings and apply constitutional thresholds to the live validator.",
)
async def save_settings(
    request: Request,
    body: AllSettings,
    user: User = Depends(require_user),
) -> AllSettings:
    """Persist settings and push constitutional thresholds to the live validator.

    Scoping rules:
    * synthetic admin (AUTH_REQUIRED off): whole payload to the global file,
      exactly as before — zero behavior change pre-flip.
    * real DB user: `notifications` goes to THEIR user row. The system-wide
      `constitutional` + `telemetry` sections may only be CHANGED by admins
      (403 for everyone else); admin changes go to the global file.
    """
    user = coerce_user(user)
    data = body.model_dump()

    if is_synthetic(user):
        _save_persisted(data)
    else:
        current_global = _merge_with_defaults(_load_persisted())
        if user.role != "admin":
            # Non-admins may not touch the system-wide sections. The UI sends
            # the full settings object, so "touch" means "differs from the
            # current global values".
            if (
                data["constitutional"] != current_global["constitutional"]
                or data["telemetry"] != current_global["telemetry"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins may change constitutional or telemetry settings",
                )
        else:
            persisted = _load_persisted()
            persisted["constitutional"] = data["constitutional"]
            persisted["telemetry"] = data["telemetry"]
            _save_persisted(persisted)
        try:
            user_store.set_user_settings(user.id, {"notifications": data["notifications"]})
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to save per-user settings for %s: %s", user.username, exc)

    # Apply constitutional thresholds to the live ConstitutionalValidator (best-effort).
    # NOTE: main.py stores the validator as app.state.validator — the old
    # "constitutional_validator" attribute name silently never matched, so saved
    # thresholds never reached the live validator.
    try:
        validator = getattr(request.app.state, "validator", None)
        if validator is not None:
            new_auto = body.constitutional.autoThreshold / 100.0
            new_approval = body.constitutional.approvalThreshold / 100.0
            validator.confidence_threshold_auto = new_auto
            validator.confidence_threshold_approval = new_approval
            logger.info(
                "Updated constitutional thresholds → auto=%.2f  approval=%.2f",
                new_auto,
                new_approval,
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not update live validator thresholds: %s", exc)

    return body


@router.post(
    "/reset",
    response_model=AllSettings,
    summary="Reset Settings",
    description="Delete persisted settings file and return factory defaults.",
)
async def reset_settings() -> AllSettings:
    """Wipe persisted settings and return defaults."""
    try:
        p = _settings_path()
        if p.exists():
            p.unlink()
        logger.info("Settings reset to defaults")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to delete settings file: %s", exc)
    return AllSettings()


__all__ = ["router"]
