"""
Constitutional AIOps - Action API Schemas

Pydantic models for action management endpoints.
All actions go through Constitutional AI validation before execution.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of remediation actions."""
    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    ROLLBACK = "rollback"
    MODIFY_CONFIG = "modify_config"
    CLEAR_CACHE = "clear_cache"
    KILL_PROCESS = "kill_process"
    BLOCK_IP = "block_ip"
    ROTATE_CREDENTIALS = "rotate_credentials"
    CUSTOM = "custom"


class ActionStatus(str, Enum):
    """Action execution status."""
    PENDING = "pending"              # Created, not yet validated
    VALIDATING = "validating"        # Constitutional validation in progress
    APPROVED = "approved"            # Validation passed, ready for execution
    REJECTED = "rejected"            # Constitutional violation
    AWAITING_APPROVAL = "awaiting_approval"  # Needs human approval
    EXECUTING = "executing"          # In progress
    COMPLETED = "completed"          # Successfully executed
    FAILED = "failed"                # Execution failed
    CANCELLED = "cancelled"          # User cancelled
    EXPIRED = "expired"              # Approval timeout


class AuthorizationLevel(str, Enum):
    """Authorization levels from Constitutional AI."""
    AUTOMATIC = "automatic"          # >90% confidence - proceed with audit
    APPROVAL_REQUIRED = "approval"   # 70-90% confidence - needs human
    ALERT_ONLY = "alert"             # <70% confidence - notify only


class ConstitutionalValidation(BaseModel):
    """Result of constitutional validation."""
    passed: bool
    authorization_level: AuthorizationLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    tier1_passed: bool = Field(..., description="Safety principles passed")
    tier2_passed: bool = Field(..., description="Operational principles passed")
    tier3_passed: bool = Field(..., description="Learning principles passed")
    violations: list[dict[str, Any]] = Field(
        default=[],
        description="List of principle violations"
    )
    warnings: list[str] = Field(default=[], description="Non-blocking warnings")
    explanation: str = Field(..., description="Human-readable explanation")
    validated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "passed": True,
                "authorization_level": "automatic",
                "confidence": 0.92,
                "tier1_passed": True,
                "tier2_passed": True,
                "tier3_passed": True,
                "violations": [],
                "warnings": [],
                "explanation": "Validation passed - automatic authorization",
                "validated_at": "2025-12-14T10:30:00Z"
            }
        }


class ActionBase(BaseModel):
    """Base action fields."""
    action_type: ActionType = Field(..., description="Type of action")
    description: str = Field(..., min_length=5, max_length=500)
    target_service: str = Field(..., description="Service to act on")
    target_instance: Optional[str] = Field(None, description="Specific instance")
    parameters: Optional[dict[str, Any]] = Field(
        default=None,
        description="Action-specific parameters"
    )


class ActionCreate(ActionBase):
    """Request to create/propose a new action."""
    incident_id: Optional[str] = Field(None, description="Related incident")
    plan_id: Optional[str] = Field(None, description="Part of remediation plan")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Agent's confidence in this action"
    )
    evidence: Optional[dict[str, Any]] = Field(
        default=None,
        description="Telemetry evidence supporting action"
    )
    skip_validation: bool = Field(
        default=False,
        description="Skip constitutional validation (admin only)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "action_type": "restart_service",
                "description": "Restart payment-service to clear memory leak",
                "target_service": "payment-service",
                "target_instance": "payment-service-abc123",
                "parameters": {"graceful": True, "timeout": 30},
                "incident_id": "INC-2024-042",
                "confidence": 0.88,
                "evidence": {
                    "memory_usage": 0.95,
                    "restart_history": "No restarts in 24h"
                }
            }
        }


class ActionApproval(BaseModel):
    """Human approval for an action."""
    approved: bool = Field(..., description="Whether action is approved")
    approved_by: str = Field(..., description="Approver username or ID")
    comments: Optional[str] = Field(None, max_length=500)
    modifications: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional modifications to action parameters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "approved": True,
                "approved_by": "operator@company.com",
                "comments": "Approved - customer impact acceptable"
            }
        }


class ActionExecutionResult(BaseModel):
    """Result of action execution."""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    rollback_available: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "output": "Service restarted successfully. New pod: payment-service-xyz789",
                "started_at": "2025-12-14T10:32:00Z",
                "completed_at": "2025-12-14T10:32:45Z",
                "duration_ms": 45000,
                "rollback_available": True
            }
        }


class Action(ActionBase):
    """Complete action record."""
    id: str = Field(..., description="Unique action ID")
    status: ActionStatus = Field(default=ActionStatus.PENDING)

    # Relationships
    incident_id: Optional[str] = None
    plan_id: Optional[str] = None

    # Confidence and validation
    confidence: float = Field(..., ge=0.0, le=1.0)
    validation: Optional[ConstitutionalValidation] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = Field(
        None,
        description="Approval expiration time"
    )

    # Approval tracking
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_comments: Optional[str] = None

    # Execution
    execution_result: Optional[ActionExecutionResult] = None

    # Audit
    created_by: str = Field(default="system", description="Creator (system or user ID)")
    audit_log: list[dict[str, Any]] = Field(
        default=[],
        description="Action lifecycle audit trail"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ACT-2024-001234",
                "action_type": "restart_service",
                "description": "Restart payment-service to clear memory leak",
                "target_service": "payment-service",
                "status": "completed",
                "incident_id": "INC-2024-042",
                "confidence": 0.88,
                "requires_approval": False,
                "created_at": "2025-12-14T10:30:00Z",
                "updated_at": "2025-12-14T10:32:45Z",
                "created_by": "system"
            }
        }


class ActionList(BaseModel):
    """Paginated list of actions."""
    items: list[Action]
    total: int
    page: int
    page_size: int
    has_more: bool


class ActionFilter(BaseModel):
    """Filters for action queries."""
    status: Optional[list[ActionStatus]] = None
    action_type: Optional[list[ActionType]] = None
    target_service: Optional[str] = None
    incident_id: Optional[str] = None
    requires_approval: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class ActionStats(BaseModel):
    """Action execution statistics."""
    total: int
    by_status: dict[str, int]
    by_type: dict[str, int]
    auto_executed: int = Field(description="Actions executed automatically")
    human_approved: int = Field(description="Actions requiring human approval")
    rejected: int = Field(description="Actions rejected by Constitutional AI")
    success_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Successful execution rate"
    )
    avg_execution_time_ms: Optional[float] = None


class PendingApprovals(BaseModel):
    """Summary of pending approval requests."""
    count: int
    actions: list[Action]
    oldest_pending: Optional[datetime] = None
    urgency_breakdown: dict[str, int] = Field(
        default={},
        description="Count by severity level"
    )


__all__ = [
    "ActionType",
    "ActionStatus",
    "AuthorizationLevel",
    "ConstitutionalValidation",
    "ActionBase",
    "ActionCreate",
    "ActionApproval",
    "ActionExecutionResult",
    "Action",
    "ActionList",
    "ActionFilter",
    "ActionStats",
    "PendingApprovals",
]
