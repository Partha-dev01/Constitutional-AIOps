"""
Constitutional AIOps - Demo Mode API Routes (t3-backed).

Chaos injection no longer execs against the LOCAL docker daemon. nextcloud +
nextcloud-db run on a separate remote t3 host that the backend cannot reach
directly, so these routes call the t3 control agent over HTTP via
``src.remediation.t3_client``. Successful injections still flow through
``_log_demo_incidents`` -> ``_trigger_analysis`` so RCA / episodes / graph fire
exactly as before.

Endpoints (CONTRACT 2, all behind ``_ensure_demo_allowed()``), mounted under
``/api/v1/demo``:
  GET  /scenarios                 -> {"scenarios":[{id,label,description}, ...]}
  GET  /status                    -> proxy t3 /status (reachable flag + maps)
  POST /chaos/{scenario}/start    -> {"scenario","action":"start","success","detail"}
  POST /chaos/{scenario}/heal     -> {"scenario","action":"heal","success","detail"}
  PUT  /target  {"url": ...}      -> {"target_url": ...}
"""

import logging
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from src.remediation import t3_client

logger = logging.getLogger(__name__)

router = APIRouter()

# Demo mode state. KEEP this dict: chat.py imports it and reads
# active/anomalies_triggered/container_name for its system-context block.
_demo_state = {
    "active": False,
    "started_at": None,
    "anomalies_triggered": 0,
    "container_name": "nextcloud",
}


# ---------------------------------------------------------------------------
# Scenario catalog
# ---------------------------------------------------------------------------

# The five chaos scenarios. ``id`` matches the t3 agent's scenario ids exactly.
SCENARIOS: list[dict[str, str]] = [
    {
        "id": "db_down",
        "label": "Database Down",
        "description": "Stops the nextcloud-db container, taking the database offline.",
    },
    {
        "id": "cpu_stress",
        "label": "CPU Stress",
        "description": "Runs self-expiring busy loops inside nextcloud to spike CPU.",
    },
    {
        "id": "mem_stress",
        "label": "Memory Stress",
        "description": "Grows memory inside nextcloud (self-expiring) to create pressure.",
    },
    {
        "id": "bad_config_5xx",
        "label": "Bad Config (5xx)",
        "description": "Toggles nextcloud maintenance mode so requests return 503 errors.",
    },
    {
        "id": "disk_fill",
        "label": "Disk Fill",
        "description": "Writes a large junk file + spams the nextcloud log to simulate disk pressure.",
    },
]

_SCENARIO_IDS = {s["id"] for s in SCENARIOS}

# Map each scenario to the incident properties used when logging the demo
# incident (so RCA gets a meaningful title/severity).
_SCENARIO_INCIDENT = {
    "db_down": ("Database Down", "high", "infrastructure",
                "nextcloud-db is offline — database connectivity lost."),
    "cpu_stress": ("CPU Stress", "high", "performance",
                   "High CPU utilization detected on nextcloud."),
    "mem_stress": ("Memory Stress", "medium", "performance",
                   "Memory pressure detected on nextcloud — potential OOM."),
    "bad_config_5xx": ("Bad Config (5xx)", "high", "application",
                       "nextcloud returning 5xx errors (maintenance mode / bad config)."),
    "disk_fill": ("Disk Fill", "medium", "infrastructure",
                  "Disk pressure detected on nextcloud — data volume filling up."),
}


def _ensure_demo_allowed() -> None:
    """Demo chaos injects real faults on the remote t3 — keep it out of
    production unless explicitly enabled via AIOPS_ENABLE_DEMO."""
    if os.getenv("ENVIRONMENT", "local").lower() != "production":
        return
    if os.getenv("AIOPS_ENABLE_DEMO", "").lower() in ("1", "true", "yes"):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Demo mode is disabled in production (it injects real faults via the "
            "t3 control agent). Set AIOPS_ENABLE_DEMO=true to allow it."
        ),
    )


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ScenarioInfo(BaseModel):
    """A single chaos scenario descriptor."""
    id: str
    label: str
    description: str


class ScenarioListResponse(BaseModel):
    """List of available chaos scenarios."""
    scenarios: list[ScenarioInfo]


class ChaosActionResponse(BaseModel):
    """Result of a chaos start/heal call."""
    scenario: str
    action: str
    success: bool
    detail: str


class TargetUpdateRequest(BaseModel):
    """Body for PUT /target."""
    url: str


class TargetUpdateResponse(BaseModel):
    """Response for PUT /target."""
    target_url: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolved_target_url() -> str:
    """Current demo target url (persisted settings first, then env)."""
    try:
        from src.api.routes.settings import _load_persisted

        persisted = _load_persisted() or {}
        url = (persisted.get("remediation", {}) or {}).get("demoTargetUrl", "") or ""
    except Exception:  # noqa: BLE001
        url = ""
    if not url:
        url = os.getenv("DEMO_TARGET_URL", "") or ""
    return url.strip()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get(
    "/scenarios",
    response_model=ScenarioListResponse,
    summary="List Chaos Scenarios",
    description="List the available chaos scenarios that can be injected on the t3.",
)
async def list_scenarios() -> ScenarioListResponse:
    """Return the catalog of chaos scenarios."""
    _ensure_demo_allowed()
    return ScenarioListResponse(
        scenarios=[ScenarioInfo(**s) for s in SCENARIOS]
    )


@router.get(
    "/status",
    summary="Get Demo Status",
    description="Proxy the t3 agent's live scenario + container status.",
)
async def get_demo_status() -> dict[str, Any]:
    """Proxy the t3 ``/status``.

    On success returns the agent's scenario/container maps plus the resolved
    target url and reachable:true. If the agent is unreachable (or no target is
    configured) returns reachable:false with empty maps and HTTP 200.
    """
    _ensure_demo_allowed()
    target_url = _resolved_target_url()
    result = await t3_client.t3_status()

    if not result.get("success"):
        return {
            "target_url": target_url,
            "reachable": False,
            "scenarios": {},
            "containers": {},
        }

    return {
        "target_url": target_url,
        "reachable": True,
        "scenarios": result.get("scenarios", {}) or {},
        "containers": result.get("containers", {}) or {},
    }


@router.post(
    "/chaos/{scenario}/start",
    response_model=ChaosActionResponse,
    summary="Start Chaos Scenario",
    description="Inject a chaos scenario on the t3 and trigger RCA analysis.",
)
async def start_chaos(scenario: str, request: Request) -> ChaosActionResponse:
    """Start a chaos scenario via the t3 agent, then fire RCA on success."""
    _ensure_demo_allowed()
    if scenario not in _SCENARIO_IDS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown scenario '{scenario}'. Known: {sorted(_SCENARIO_IDS)}",
        )

    result = await t3_client.chaos_start(scenario)
    success = bool(result.get("success"))
    detail = str(result.get("detail") or result.get("error") or "")

    if success:
        _demo_state["active"] = True
        if _demo_state["started_at"] is None:
            _demo_state["started_at"] = datetime.utcnow()
        _demo_state["anomalies_triggered"] += 1
        await _log_demo_incidents(request, [scenario])

    return ChaosActionResponse(
        scenario=scenario, action="start", success=success, detail=detail,
    )


@router.post(
    "/chaos/{scenario}/heal",
    response_model=ChaosActionResponse,
    summary="Heal Chaos Scenario",
    description="Heal/undo a chaos scenario on the t3.",
)
async def heal_chaos(scenario: str, request: Request) -> ChaosActionResponse:
    """Heal a chaos scenario via the t3 agent."""
    _ensure_demo_allowed()
    if scenario not in _SCENARIO_IDS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown scenario '{scenario}'. Known: {sorted(_SCENARIO_IDS)}",
        )

    result = await t3_client.chaos_heal(scenario)
    success = bool(result.get("success"))
    detail = str(result.get("detail") or result.get("error") or "")

    return ChaosActionResponse(
        scenario=scenario, action="heal", success=success, detail=detail,
    )


@router.put(
    "/target",
    response_model=TargetUpdateResponse,
    summary="Set Demo Target URL",
    description="Persist the t3 agent base URL used for chaos/remediation calls.",
)
async def set_target(body: TargetUpdateRequest) -> TargetUpdateResponse:
    """Persist ``remediation.demoTargetUrl`` via the settings JSON helpers."""
    _ensure_demo_allowed()
    url = (body.url or "").strip()

    from src.api.routes.settings import _load_persisted, _save_persisted

    data = _load_persisted() or {}
    data.setdefault("remediation", {})["demoTargetUrl"] = url
    _save_persisted(data)

    return TargetUpdateResponse(target_url=url)


# ---------------------------------------------------------------------------
# Incident logging -> RCA (reused so injecting still fires the full pipeline)
# ---------------------------------------------------------------------------

async def _log_demo_incidents(request: Request, scenario_ids: list[str]) -> None:
    """Create a real incident for each injected scenario and trigger RCA.

    Reuses the incidents store + ``_trigger_analysis`` so injecting a fault still
    drives RCA / episode / graph exactly as the legacy demo did.
    """
    from src.api.routes.incidents import (
        _generate_incident_id,
        _incidents,
        _trigger_analysis,
    )
    from src.api.schemas.incident import (
        Incident,
        IncidentCategory,
        IncidentSeverity,
        IncidentStatus,
        ServiceInfo,
    )

    severity_map = {
        "high": IncidentSeverity.HIGH,
        "medium": IncidentSeverity.MEDIUM,
        "low": IncidentSeverity.LOW,
    }
    category_map = {
        "infrastructure": IncidentCategory.INFRASTRUCTURE,
        "performance": IncidentCategory.PERFORMANCE,
        "application": IncidentCategory.APPLICATION,
        "network": IncidentCategory.NETWORK,
    }

    try:
        for scenario in scenario_ids:
            label, sev, cat, description = _SCENARIO_INCIDENT.get(
                scenario,
                (scenario, "medium", "infrastructure",
                 f"Chaos scenario '{scenario}' injected."),
            )

            # nextcloud-db scenarios affect the db container; everything else
            # is the nextcloud app container.
            affected = "nextcloud-db" if scenario == "db_down" else "nextcloud"

            now = datetime.utcnow()
            incident_id = _generate_incident_id()
            incident = Incident(
                id=incident_id,
                title=f"[DEMO] {label} on {affected}",
                description=description,
                severity=severity_map.get(sev, IncidentSeverity.MEDIUM),
                category=category_map.get(cat, IncidentCategory.INFRASTRUCTURE),
                affected_services=[ServiceInfo(name=affected)],
                tags=["demo", "auto-generated", scenario],
                source="demo-mode",
                status=IncidentStatus.DETECTING,
                created_at=now,
                updated_at=now,
                detected_at=now,
            )
            _incidents[incident_id] = incident
            logger.info("Created demo incident: %s - %s", incident_id, scenario)

            try:
                await _trigger_analysis(request, incident, enable_thinking=False)
                logger.info("Triggered RCA for demo incident: %s", incident_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to trigger RCA for %s: %s", incident_id, exc)

    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to create demo incidents: %s", exc)


__all__ = ["router", "_demo_state"]
