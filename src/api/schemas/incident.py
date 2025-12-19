"""
Constitutional AIOps - Incident API Schemas

Pydantic models for incident management endpoints.
Incidents are stored in Neo4j graph-episodic memory.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    """Incident severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentStatus(str, Enum):
    """Incident lifecycle status."""
    DETECTING = "detecting"      # Initial detection
    ANALYZING = "analyzing"      # RCA in progress
    PENDING_APPROVAL = "pending_approval"  # Awaiting human approval
    REMEDIATING = "remediating"  # Action in progress
    RESOLVED = "resolved"        # Issue fixed
    CLOSED = "closed"           # Verified and archived


class IncidentCategory(str, Enum):
    """Incident category types."""
    PERFORMANCE = "performance"
    ERROR = "error"
    SECURITY = "security"
    RESOURCE = "resource"
    AVAILABILITY = "availability"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class ServiceInfo(BaseModel):
    """Information about an affected service."""
    name: str = Field(..., description="Service name")
    namespace: Optional[str] = Field(None, description="Kubernetes namespace or environment")
    instance: Optional[str] = Field(None, description="Specific instance identifier")
    dependencies: Optional[list[str]] = Field(default=None, description="Dependent services")


class TelemetrySnapshot(BaseModel):
    """Telemetry data at time of incident."""
    logs: Optional[list[str]] = Field(default=None, description="Relevant log entries")
    metrics: Optional[dict[str, float]] = Field(default=None, description="Key metrics")
    traces: Optional[list[str]] = Field(default=None, description="Trace IDs")
    compressed_context: Optional[str] = Field(
        default=None,
        description="Token-compressed telemetry summary"
    )


class IncidentBase(BaseModel):
    """Base incident fields."""
    title: str = Field(..., min_length=5, max_length=200, description="Incident title")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description")
    severity: IncidentSeverity = Field(..., description="Incident severity")
    category: IncidentCategory = Field(default=IncidentCategory.UNKNOWN)
    affected_services: list[ServiceInfo] = Field(
        ...,
        min_length=1,
        description="List of affected services"
    )
    tags: Optional[list[str]] = Field(default=None, description="Custom tags")


class IncidentCreate(IncidentBase):
    """Request to create a new incident."""
    source: str = Field(
        default="manual",
        description="Source of incident (manual, alert, telemetry)"
    )
    telemetry: Optional[TelemetrySnapshot] = Field(
        default=None,
        description="Initial telemetry data"
    )
    auto_analyze: bool = Field(
        default=True,
        description="Automatically trigger RCA"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "High latency on payment-service",
                "description": "Users reporting slow checkout times",
                "severity": "high",
                "category": "performance",
                "affected_services": [
                    {"name": "payment-service", "namespace": "production"}
                ],
                "tags": ["checkout", "latency"],
                "source": "alert",
                "auto_analyze": True
            }
        }


class IncidentUpdate(BaseModel):
    """Request to update an incident."""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    category: Optional[IncidentCategory] = None
    tags: Optional[list[str]] = None
    resolution_notes: Optional[str] = Field(None, max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "resolved",
                "resolution_notes": "Increased connection pool size from 10 to 50"
            }
        }


class RCAResult(BaseModel):
    """Root cause analysis result."""
    root_cause: str
    causal_chain: list[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    similar_incidents: Optional[list[str]] = Field(
        default=None,
        description="IDs of similar past incidents"
    )


class RemediationStep(BaseModel):
    """Single remediation step."""
    order: int
    action: str
    command: Optional[str] = None
    risk: str = Field(..., pattern="^(low|medium|high)$")
    requires_approval: bool = False
    status: str = Field(default="pending", pattern="^(pending|in_progress|completed|failed|skipped)$")
    executed_at: Optional[datetime] = None
    result: Optional[str] = None


class RemediationPlan(BaseModel):
    """Complete remediation plan."""
    plan_id: str
    incident_id: str
    created_at: datetime
    steps: list[RemediationStep]
    overall_risk: str = Field(..., pattern="^(low|medium|high)$")
    estimated_duration: Optional[str] = None
    requires_approval: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class Incident(IncidentBase):
    """Complete incident record."""
    id: str = Field(..., description="Unique incident ID (e.g., INC-2024-042)")
    status: IncidentStatus = Field(default=IncidentStatus.DETECTING)
    source: str

    # Timestamps
    created_at: datetime
    updated_at: datetime
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # Analysis
    rca: Optional[RCAResult] = None
    remediation_plan: Optional[RemediationPlan] = None

    # Telemetry
    telemetry: Optional[TelemetrySnapshot] = None

    # Tracking
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None

    # Graph memory
    similar_incidents: Optional[list[str]] = Field(
        default=None,
        description="Related incident IDs from graph memory"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "INC-2024-042",
                "title": "High latency on payment-service",
                "description": "Users reporting slow checkout times",
                "severity": "high",
                "status": "analyzing",
                "category": "performance",
                "affected_services": [
                    {"name": "payment-service", "namespace": "production"}
                ],
                "source": "alert",
                "created_at": "2025-12-14T10:00:00Z",
                "updated_at": "2025-12-14T10:15:00Z",
                "tags": ["checkout", "latency"]
            }
        }


class IncidentList(BaseModel):
    """Paginated list of incidents."""
    items: list[Incident]
    total: int
    page: int
    page_size: int
    has_more: bool


class IncidentFilter(BaseModel):
    """Filters for incident queries."""
    status: Optional[list[IncidentStatus]] = None
    severity: Optional[list[IncidentSeverity]] = None
    category: Optional[list[IncidentCategory]] = None
    service: Optional[str] = None
    tags: Optional[list[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search: Optional[str] = Field(None, description="Full-text search in title/description")


class IncidentStats(BaseModel):
    """Incident statistics."""
    total: int
    by_status: dict[str, int]
    by_severity: dict[str, int]
    by_category: dict[str, int]
    mean_time_to_resolution: Optional[float] = Field(
        None,
        description="Average resolution time in minutes"
    )
    auto_resolved_count: int = Field(
        default=0,
        description="Incidents resolved automatically"
    )
    approval_required_count: int = Field(
        default=0,
        description="Incidents requiring human approval"
    )


__all__ = [
    "IncidentSeverity",
    "IncidentStatus",
    "IncidentCategory",
    "ServiceInfo",
    "TelemetrySnapshot",
    "IncidentBase",
    "IncidentCreate",
    "IncidentUpdate",
    "RCAResult",
    "RemediationStep",
    "RemediationPlan",
    "Incident",
    "IncidentList",
    "IncidentFilter",
    "IncidentStats",
]
