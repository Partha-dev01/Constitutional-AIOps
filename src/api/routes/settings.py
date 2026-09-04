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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.agents.serving_profile import resolve_serving_profile
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
        # Local Docker-socket fallback source (lite / self-host with no LGTM).
        # Default ON: it only ever activates when Loki/Prometheus return nothing,
        # so the full observability stack is unaffected; an operator can still
        # turn it off here.
        "dockerEnabled": True,
        "retentionDays": 30,
    },
    "remediation": {
        "mode": "diagnose",
        "autoConfidenceThreshold": 90,
        "requireEvidenceForAuto": True,
        "autoToolAllowlist": ["restart_service"],
        "demoTargetUrl": "",
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


def get_remediation_settings() -> dict[str, Any]:
    """Return the merged ``remediation`` settings section.

    Exported for the chat path (Lane B mode logic) and Lane A's demo helpers.
    ``_merge_with_defaults`` deep-merges persisted values over the defaults so
    an older persisted file that predates this section still upgrades cleanly.
    """
    return _merge_with_defaults(_load_persisted())["remediation"]


def get_telemetry_settings() -> dict[str, Any]:
    """Return the merged ``telemetry`` settings section.

    Exported so the telemetry routes can gate the local Docker-socket fallback
    source on ``dockerEnabled`` (defaults ON for lite / self-host; the full LGTM
    stack can turn it off). Deep-merges persisted over defaults so a legacy file
    upgrades cleanly.
    """
    return _merge_with_defaults(_load_persisted())["telemetry"]


def get_constitutional_settings() -> dict[str, Any]:
    """Return the merged ``constitutional`` settings section.

    Exported so the live call sites can honour persisted operator choices that
    were previously dead no-ops:
      * ``maxActionsPerMinute`` — the chat auto-exec rate limiter.
      * ``enableAuditLog``      — the validator-call audit toggle.
      * ``autoThreshold`` / ``approvalThreshold`` — applied at startup so saved
        thresholds survive a restart (see ``src/main.py`` lifespan).
    Deep-merges persisted over defaults so a legacy file upgrades cleanly.
    """
    return _merge_with_defaults(_load_persisted())["constitutional"]


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
    # Local Docker-socket fallback source (see DEFAULT_SETTINGS). Only activates
    # when Loki/Prometheus yield nothing, so it never shadows a real LGTM stack.
    dockerEnabled: bool = True
    retentionDays: int = Field(30, ge=7, le=365)


class RemediationSettingsModel(BaseModel):
    """AI-remediation behaviour (Lane B demo/chaos feature).

    ``mode`` selects how a proposed restart-style action is handled:
      * ``diagnose`` (default) — never attach/execute anything; pure analysis.
      * ``approve``  — attach a proposed action; execute only on user approval.
      * ``auto``     — attempt gated execution when the interlocks all pass.
    ``autoToolAllowlist`` scopes auto mode per tool: only listed action tools may
    auto-execute; anything else degrades to an approve-style consent card. The
    default preserves the pre-allowlist behaviour (restarts eligible, scaling not).
    ``demoTargetUrl`` is shared with Lane A (chaos demo target endpoint).
    """
    mode: Literal["diagnose", "approve", "auto"] = "diagnose"
    autoConfidenceThreshold: int = Field(90, ge=70, le=99)
    requireEvidenceForAuto: bool = True
    autoToolAllowlist: list[Literal["restart_service", "scale_service"]] = Field(
        default_factory=lambda: ["restart_service"]
    )
    demoTargetUrl: str = ""


class AllSettings(BaseModel):
    constitutional: ConstitutionalSettingsModel = ConstitutionalSettingsModel()
    notifications: NotificationSettingsModel = NotificationSettingsModel()
    telemetry: TelemetrySettingsModel = TelemetrySettingsModel()
    remediation: RemediationSettingsModel = RemediationSettingsModel()


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
                or data["remediation"] != current_global["remediation"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins may change constitutional, telemetry or remediation settings",
                )
        else:
            persisted = _load_persisted()
            persisted["constitutional"] = data["constitutional"]
            persisted["telemetry"] = data["telemetry"]
            # ``remediation`` is a system-wide section (like constitutional /
            # telemetry); it must be persisted on the real-admin path too, else
            # mode/auto-threshold changes silently never stick once AUTH is on.
            persisted["remediation"] = data["remediation"]
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
    description="Delete persisted settings file and return factory defaults. Admin only.",
)
async def reset_settings(user: User = Depends(require_user)) -> AllSettings:
    """Wipe persisted settings and return defaults. Admin only."""
    user = coerce_user(user)
    if not is_synthetic(user) and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins may reset settings",
        )
    try:
        p = _settings_path()
        if p.exists():
            p.unlink()
        logger.info("Settings reset to defaults")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to delete settings file: %s", exc)
    return AllSettings()


# ---------------------------------------------------------------------------
# Serving mode (Mode 1 ⇄ Mode 2) — swap-request channel
# ---------------------------------------------------------------------------
#
# The backend cannot swap the serving stack itself: the swap recreates the
# backend container, and production mounts no docker.sock (by design). So the
# toggle works through a file-based request channel on the EBS-backed data dir
# (AIOPS_DATA_DIR/mode-swap/, host-visible at /mnt/data/app/mode-swap/):
#
#   backend  → writes  request.json   {"requested_mode", "requested_at", "requested_by"}
#   watcher  → reads   request.json, runs scripts/mode-swap.sh up-mode{N},
#              writes  status.json    {"state": swapping|done|error, ...},
#              deletes request.json
#   backend  → GET merges the current ServingProfile with those files.
#
# The host-side executor is scripts/mode-swap-watcher.sh (installed as the
# aiops-mode-swap systemd service on the VM). During the swap the backend is
# recreated, so clients briefly get connection errors — the UI treats that
# window as "swapping" and resumes polling.


def _mode_swap_dir() -> Path:
    """Directory for the swap request/status files (under AIOPS_DATA_DIR)."""
    d = _settings_path().parent / "mode-swap"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read_json_file(p: Path) -> Optional[dict[str, Any]]:
    """Read a JSON object from disk; None when absent/corrupt (never raises)."""
    try:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read %s: %s", p, exc)
    return None


def _write_json_file(p: Path, data: dict[str, Any]) -> None:
    """Atomic-ish JSON write (write tmp, rename), mirroring _save_persisted."""
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(p)


class ServingModeRequest(BaseModel):
    mode: Literal[1, 2]


class ServingModeStatus(BaseModel):
    """Current serving mode + the state of any in-flight swap request."""

    mode: int
    single_engine: bool
    requested_mode: Optional[int] = None
    swap_status: Literal["idle", "pending", "swapping", "error"] = "idle"
    detail: Optional[str] = None
    requested_at: Optional[str] = None
    updated_at: Optional[str] = None


def _current_serving_mode_status() -> ServingModeStatus:
    """Merge the live ServingProfile with the request/status files."""
    profile = resolve_serving_profile()
    d = _mode_swap_dir()
    stat = _read_json_file(d / "status.json")
    req = _read_json_file(d / "request.json")

    swap_status: str = "idle"
    requested_mode: Optional[int] = None
    detail: Optional[str] = None
    requested_at: Optional[str] = None
    updated_at: Optional[str] = None

    if stat:
        updated_at = stat.get("updated_at")
        state = stat.get("state")
        if state == "swapping":
            swap_status = "swapping"
            requested_mode = stat.get("target")
        elif state == "error":
            swap_status = "error"
            detail = stat.get("detail")
        # state == "done" → idle: the profile already reflects the result.

    if req:
        requested_mode = req.get("requested_mode")
        requested_at = req.get("requested_at")
        if swap_status != "swapping":
            swap_status = "pending"

    return ServingModeStatus(
        mode=profile.mode,
        single_engine=profile.single_engine,
        requested_mode=requested_mode,
        swap_status=swap_status,  # type: ignore[arg-type]
        detail=detail,
        requested_at=requested_at,
        updated_at=updated_at,
    )


@router.get(
    "/serving-mode",
    response_model=ServingModeStatus,
    summary="Get Serving Mode",
    description="Current serving mode (1 = frozen dual-engine artifact, 2 = modernized stack) and any in-flight swap request.",
)
async def get_serving_mode(user: User = Depends(require_user)) -> ServingModeStatus:
    return _current_serving_mode_status()


@router.post(
    "/serving-mode",
    response_model=ServingModeStatus,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request Serving Mode Swap",
    description="Write a mode-swap request for the host-side watcher. Admin only. The stack restarts (~3-5 min) while the swap runs.",
)
async def request_serving_mode(
    body: ServingModeRequest,
    user: User = Depends(require_user),
) -> ServingModeStatus:
    user = coerce_user(user)
    if not is_synthetic(user) and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins may switch the serving mode",
        )

    current = _current_serving_mode_status()
    if body.mode == current.mode and current.swap_status in ("idle", "error"):
        # Already there: clear any stale error/request so the UI settles.
        try:
            (_mode_swap_dir() / "request.json").unlink(missing_ok=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not clear stale mode-swap request: %s", exc)
        return _current_serving_mode_status()
    if current.swap_status in ("pending", "swapping"):
        # One swap at a time; report the in-flight state instead of stacking.
        return current

    payload = {
        "requested_mode": body.mode,
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "requested_by": user.username,
    }
    _write_json_file(_mode_swap_dir() / "request.json", payload)
    logger.info(
        "Serving-mode swap requested: mode %s → %s (by %s)",
        current.mode, body.mode, user.username,
    )
    return _current_serving_mode_status()


# ---------------------------------------------------------------------------
# LLM endpoints (bring-your-own model) — Settings -> Models
# ---------------------------------------------------------------------------
#
# The LLM endpoint config (URL + served model per agent + an optional API key)
# used to be env-only (FAST_AGENT_URL / REASONING_AGENT_URL / *_MODEL / LLM_API_KEY),
# so a self-hoster had to edit .env and rebuild. These endpoints let an operator
# view + change it from the UI. A save both:
#   * persists to the same settings.json (survives a restart), AND
#   * applies LIVE via app.state.model_router.reconfigure() (no restart needed).
# SECURITY: the API key is WRITE-ONLY. GET never returns it — only booleans
# ("…ApiKeySet"). On PUT, apiKey=null leaves the stored key untouched, apiKey=""
# clears it, any other value sets it. The key is never written to a log.


class ModelsConfig(BaseModel):
    """Effective LLM-endpoint config (GET). Never carries the API key itself."""

    fastAgentUrl: str
    fastAgentModel: str
    reasoningAgentUrl: str
    reasoningAgentModel: str
    fastApiKeySet: bool = False
    reasoningApiKeySet: bool = False


class ModelsConfigUpdate(BaseModel):
    """Editable LLM-endpoint config (PUT)."""

    fastAgentUrl: str = Field(..., min_length=1)
    fastAgentModel: str = Field(..., min_length=1)
    reasoningAgentUrl: str = Field(..., min_length=1)
    reasoningAgentModel: str = Field(..., min_length=1)
    # Shared bearer key applied to both agents. None => leave the stored key
    # unchanged; "" => clear it; any other value => set it. Write-only.
    apiKey: Optional[str] = None


class ModelsTestResult(BaseModel):
    """Per-agent liveness result for the 'Test connection' button."""

    fast_agent: bool
    reasoning_agent: bool


def get_models_settings() -> Optional[dict[str, Any]]:
    """Return the persisted LLM-endpoint overrides, or None if unset.

    Exported so main.py can re-apply a UI-saved endpoint config to the freshly
    built ModelRouter at startup (persisted config wins over env, and survives a
    restart). The returned dict may include the stored ``apiKey`` for
    reconfigure() — callers MUST NOT return it to a client.
    """
    models = _load_persisted().get("models")
    return models if isinstance(models, dict) and models else None


def _models_config_response(request: Request) -> ModelsConfig:
    """Build the key-free GET response from the LIVE router (or config fallback)."""
    router_obj = getattr(request.app.state, "model_router", None)
    if router_obj is not None and hasattr(router_obj, "current_endpoint_config"):
        c = router_obj.current_endpoint_config()
        return ModelsConfig(
            fastAgentUrl=c["fast_agent_url"],
            fastAgentModel=c["fast_agent_model"],
            reasoningAgentUrl=c["reasoning_agent_url"],
            reasoningAgentModel=c["reasoning_agent_model"],
            fastApiKeySet=bool(c["fast_api_key_set"]),
            reasoningApiKeySet=bool(c["reasoning_api_key_set"]),
        )
    # Router not built yet (e.g. very early call): fall back to raw config.
    from src.config import config as _cfg

    return ModelsConfig(
        fastAgentUrl=_cfg.llm.fast_agent_url,
        fastAgentModel=_cfg.llm.fast_agent_model,
        reasoningAgentUrl=_cfg.llm.reasoning_agent_url,
        reasoningAgentModel=_cfg.llm.reasoning_agent_model,
        fastApiKeySet=bool((_cfg.llm.fast_agent_api_key or "").strip()),
        reasoningApiKeySet=bool((_cfg.llm.reasoning_agent_api_key or "").strip()),
    )


@router.get(
    "/models",
    response_model=ModelsConfig,
    summary="Get LLM Endpoint Config",
    description="Current bring-your-own LLM endpoint config (URLs + served model names). The API key is never returned — only whether one is set.",
)
async def get_models_config(
    request: Request, user: User = Depends(require_user)
) -> ModelsConfig:
    return _models_config_response(request)


@router.put(
    "/models",
    response_model=ModelsConfig,
    summary="Update LLM Endpoint Config",
    description="Persist + apply the LLM endpoint config live (no restart). Admin only. The API key is write-only: omit it to keep the stored one, send \"\" to clear it.",
)
async def update_models_config(
    request: Request,
    body: ModelsConfigUpdate,
    user: User = Depends(require_user),
) -> ModelsConfig:
    user = coerce_user(user)
    if not is_synthetic(user) and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins may change the LLM endpoints",
        )

    # Persist (including the key). Merge onto any existing stored block so an
    # omitted apiKey keeps the previously stored key.
    persisted = _load_persisted()
    stored = persisted.get("models") if isinstance(persisted.get("models"), dict) else {}
    new_key = stored.get("apiKey", "")
    if body.apiKey is not None:
        new_key = body.apiKey  # "" clears, any other value sets
    persisted["models"] = {
        "fastAgentUrl": body.fastAgentUrl.strip(),
        "fastAgentModel": body.fastAgentModel.strip(),
        "reasoningAgentUrl": body.reasoningAgentUrl.strip(),
        "reasoningAgentModel": body.reasoningAgentModel.strip(),
        "apiKey": new_key,
    }
    _save_persisted(persisted)

    # Apply LIVE to the running router (best-effort — a bad URL simply fails on
    # the next LLM call; the config is persisted regardless).
    router_obj = getattr(request.app.state, "model_router", None)
    if router_obj is not None and hasattr(router_obj, "reconfigure"):
        try:
            await router_obj.reconfigure(
                fast_url=body.fastAgentUrl,
                reasoning_url=body.reasoningAgentUrl,
                fast_model=body.fastAgentModel,
                reasoning_model=body.reasoningAgentModel,
                fast_api_key=new_key,
                reasoning_api_key=new_key,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Live model-router reconfigure failed (persisted anyway): %s", exc)

    return _models_config_response(request)


@router.post(
    "/models/test",
    response_model=ModelsTestResult,
    summary="Test LLM Endpoints",
    description="Probe the currently-configured fast + reasoning endpoints and report which respond. Admin only. Save first to test edited values.",
)
async def test_models_config(
    request: Request, user: User = Depends(require_user)
) -> ModelsTestResult:
    user = coerce_user(user)
    if not is_synthetic(user) and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins may test the LLM endpoints",
        )
    router_obj = getattr(request.app.state, "model_router", None)
    if router_obj is None:
        return ModelsTestResult(fast_agent=False, reasoning_agent=False)
    try:
        health = await router_obj.health_check()
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM endpoint test failed: %s", exc)
        return ModelsTestResult(fast_agent=False, reasoning_agent=False)
    return ModelsTestResult(
        fast_agent=bool(health.get("fast_agent")),
        reasoning_agent=bool(health.get("reasoning_agent")),
    )


# ---------------------------------------------------------------------------
# Onboarding state (first-run Quick-Setup wizard)
# ---------------------------------------------------------------------------
#
# Instance-global (the wizard configures instance-level things: services,
# topology, base prompt, LLM endpoint, monitoring). Stored in its OWN file
# under AIOPS_DATA_DIR — NOT in settings.json and NOT in AllSettings — so a
# ``PUT /settings`` (which rewrites the whole settings.json) can never wipe it,
# and it stays clear of the per-user / admin role-scoping on that endpoint.


class OnboardingState(BaseModel):
    """First-run wizard progress. ``step`` is the furthest step reached."""

    completed: bool = False
    skipped: bool = False
    step: int = Field(0, ge=0, le=50)


def _onboarding_path() -> Path:
    """Path to the persisted onboarding-state JSON (beside settings.json)."""
    return _settings_path().parent / "onboarding.json"


def _load_onboarding() -> OnboardingState:
    """Load onboarding state; defaults (fresh instance) on absent/corrupt."""
    raw = _read_json_file(_onboarding_path()) or {}
    try:
        return OnboardingState(
            **{k: v for k, v in raw.items() if k in {"completed", "skipped", "step"}}
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Invalid persisted onboarding state, using defaults: %s", exc)
        return OnboardingState()


@router.get(
    "/onboarding",
    response_model=OnboardingState,
    summary="Get Onboarding State",
    description="First-run Quick-Setup wizard progress (instance-global).",
)
async def get_onboarding(user: User = Depends(require_user)) -> OnboardingState:
    return _load_onboarding()


@router.put(
    "/onboarding",
    response_model=OnboardingState,
    summary="Save Onboarding State",
    description=(
        "Persist wizard progress (mark completed / skipped, or record the "
        "furthest step reached). Admin only."
    ),
)
async def put_onboarding(
    body: OnboardingState, user: User = Depends(require_user)
) -> OnboardingState:
    user = coerce_user(user)
    if not is_synthetic(user) and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins may change onboarding state",
        )
    _write_json_file(_onboarding_path(), body.model_dump())
    return body


# ---------------------------------------------------------------------------
# Monitoring source live-test (onboarding wizard Monitoring step)
# ---------------------------------------------------------------------------
#
# Server-side reachability probe of the operator's Loki / Prometheus / Tempo
# URLs (browser CORS would otherwise block a client-side check). Admin only:
# it issues a GET from the server to an arbitrary URL, so gate it and return
# only reachability + the HTTP status, never the response body. Redirects are
# NOT followed (httpx AsyncClient default) so it can't be bounced internally.


class MonitoringTestRequest(BaseModel):
    """Monitoring sources to probe. URLs: any subset (blanks are skipped). The
    local Docker socket has no URL, so a ``docker=true`` flag requests it."""

    lokiUrl: Optional[str] = None
    prometheusUrl: Optional[str] = None
    tempoUrl: Optional[str] = None
    docker: Optional[bool] = None


class ProbeResult(BaseModel):
    ok: bool
    detail: str = ""


class MonitoringTestResult(BaseModel):
    """Per-source result; a source is absent when it was not requested."""

    loki: Optional[ProbeResult] = None
    prometheus: Optional[ProbeResult] = None
    tempo: Optional[ProbeResult] = None
    docker: Optional[ProbeResult] = None


async def _probe_health(url: str, health_path: str) -> ProbeResult:
    """GET a source's health endpoint with a fast-fail timeout.

    2xx → ok. A non-2xx means the host is reachable but the path/service looks
    wrong. Any network/timeout error (``httpx.RequestError`` covers the
    ConnectTimeout/ReadTimeout/ConnectError family) → not reachable.
    """
    base = (url or "").strip().rstrip("/")
    if not base:
        return ProbeResult(ok=False, detail="no URL supplied")
    target = base + health_path
    timeout = httpx.Timeout(4.0, connect=3.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(target)
    except httpx.RequestError as exc:
        return ProbeResult(ok=False, detail=f"unreachable ({type(exc).__name__})")
    except Exception as exc:  # noqa: BLE001 - a probe must never raise
        return ProbeResult(ok=False, detail=f"error ({type(exc).__name__})")
    if 200 <= resp.status_code < 300:
        return ProbeResult(ok=True, detail=f"reachable (HTTP {resp.status_code})")
    return ProbeResult(ok=False, detail=f"reachable but HTTP {resp.status_code}")


@router.post(
    "/monitoring/test",
    response_model=MonitoringTestResult,
    summary="Test Monitoring Sources",
    description=(
        "Server-side reachability probe of the supplied Loki (/ready), "
        "Prometheus (/-/healthy) and Tempo (/ready) URLs. Admin only. Returns "
        "reachability + HTTP status only, never response bodies."
    ),
)
async def test_monitoring(
    body: MonitoringTestRequest, user: User = Depends(require_user)
) -> MonitoringTestResult:
    user = coerce_user(user)
    if not is_synthetic(user) and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins may test monitoring sources",
        )
    result = MonitoringTestResult()
    if body.lokiUrl and body.lokiUrl.strip():
        result.loki = await _probe_health(body.lokiUrl, "/ready")
    if body.prometheusUrl and body.prometheusUrl.strip():
        result.prometheus = await _probe_health(body.prometheusUrl, "/-/healthy")
    if body.tempoUrl and body.tempoUrl.strip():
        result.tempo = await _probe_health(body.tempoUrl, "/ready")
    if body.docker:
        # Local Docker socket: not a URL probe. Run the blocking SDK call off the
        # event loop; report reachability + running-container count.
        import asyncio

        from src.telemetry.docker_source import docker_socket_status

        status_info = await asyncio.to_thread(docker_socket_status)
        if status_info.get("available"):
            n = status_info.get("containers", 0)
            result.docker = ProbeResult(ok=True, detail=f"reachable ({n} container{'s' if n != 1 else ''})")
        else:
            result.docker = ProbeResult(ok=False, detail="socket unreachable")
    return result


__all__ = [
    "router",
    "get_remediation_settings",
    "get_constitutional_settings",
    "get_telemetry_settings",
    "get_models_settings",
]
