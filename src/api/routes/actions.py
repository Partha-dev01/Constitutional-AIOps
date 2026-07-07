"""
Constitutional AIOps - Actions API Routes

Action management endpoints with Constitutional AI validation.
All actions are validated against 12 constitutional principles before execution.

Confidence Formula (from Research_V7.tex):
  C(a) = 0.4·C_LLM + 0.35·C_hist + 0.25·C_sim

Authorization levels based on composite confidence:
  - >90%: Automatic execution
  - 70-90%: Requires human approval
  - <70%: Alert only, no execution
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status

from src.api.schemas.action import (
    Action,
    ActionApproval,
    ActionCreate,
    ActionExecutionResult,
    ActionFilter,
    ActionList,
    ActionStats,
    ActionStatus,
    ActionType,
    AuthorizationLevel,
    ConstitutionalValidation,
    PendingApprovals,
)
from src.confidence import ConfidenceCalculator, ConfidenceBreakdown

logger = logging.getLogger(__name__)


def _audit_enabled() -> bool:
    """Resolve the persisted ``constitutional.enableAuditLog`` toggle.

    Previously a dead no-op (the validation context hardcoded ``audit_enabled=
    True``). Defaults to True (audit-on) when unset/unreadable — auditing is the
    safe default for a constitutional system.
    """
    try:
        from src.api.routes.settings import get_constitutional_settings

        return bool(get_constitutional_settings().get("enableAuditLog", True))
    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not read persisted enableAuditLog: %s", exc)
        return True

router = APIRouter()

# In-memory action store (replace with persistent storage in production)
_actions: dict[str, Action] = {}

# Action counter
_action_counter = 0


def _generate_action_id() -> str:
    """Generate unique action ID."""
    global _action_counter
    _action_counter += 1
    year = datetime.utcnow().year
    return f"ACT-{year}-{_action_counter:06d}"


@router.post(
    "/",
    response_model=Action,
    status_code=status.HTTP_201_CREATED,
    summary="Create Action",
    description="Create and validate a new action through Constitutional AI",
)
async def create_action(
    request: Request,
    action_create: ActionCreate,
) -> Action:
    """
    Create and validate a new action.

    The action goes through Constitutional AI validation:
    1. Tier 1 (Safety) - Must pass or action is blocked
    2. Tier 2 (Operational) - Violations require approval
    3. Tier 3 (Learning) - Soft warnings logged

    Confidence Formula (Research_V7.tex):
      C(a) = 0.4·C_LLM + 0.35·C_hist + 0.25·C_sim

    Authorization levels based on composite confidence:
    - >90%: Automatic execution
    - 70-90%: Requires human approval
    - <70%: Alert only, no execution

    Args:
        action_create: Action creation data with confidence

    Returns:
        Created action with validation results
    """
    action_id = _generate_action_id()
    now = datetime.utcnow()

    # Get confidence calculator from app state
    calculator: Optional[ConfidenceCalculator] = getattr(
        request.app.state, "confidence_calculator", None
    )

    # Calculate composite confidence using the formula from Research_V7.tex
    llm_confidence = action_create.confidence
    composite_confidence = llm_confidence
    confidence_breakdown: Optional[ConfidenceBreakdown] = None

    if calculator:
        try:
            # Build incident context for similarity lookup
            incident_context = None
            if action_create.incident_id:
                # Try to get incident details for similarity matching
                incident_context = {
                    "incident_id": action_create.incident_id,
                    "affected_services": [action_create.target_service] if action_create.target_service else [],
                    "category": action_create.action_type.value,
                }

            composite_confidence, confidence_breakdown = await calculator.calculate_composite(
                llm_confidence=llm_confidence,
                action_type=action_create.action_type.value,
                incident_context=incident_context,
            )

            logger.info(
                f"Composite confidence for {action_id}: {composite_confidence:.4f} "
                f"(LLM={llm_confidence:.2f}, hist={confidence_breakdown.c_hist:.2f}, "
                f"sim={confidence_breakdown.c_sim:.2f})"
            )
        except Exception as e:
            logger.warning(f"Failed to calculate composite confidence: {e}")
            # Fall back to LLM confidence only

    # Create initial action with composite confidence
    action = Action(
        id=action_id,
        action_type=action_create.action_type,
        description=action_create.description,
        target_service=action_create.target_service,
        target_instance=action_create.target_instance,
        parameters=action_create.parameters,
        incident_id=action_create.incident_id,
        plan_id=action_create.plan_id,
        confidence=composite_confidence,  # Use composite confidence
        status=ActionStatus.PENDING,
        created_at=now,
        updated_at=now,
        created_by="system",
        audit_log=[{
            "timestamp": now.isoformat(),
            "event": "created",
            "details": {
                "llm_confidence": llm_confidence,
                "composite_confidence": composite_confidence,
                "confidence_breakdown": confidence_breakdown.to_dict() if confidence_breakdown else None,
            },
        }],
    )

    # Skip validation if requested (admin only)
    if action_create.skip_validation:
        action.status = ActionStatus.APPROVED
        action.audit_log.append({
            "timestamp": now.isoformat(),
            "event": "validation_skipped",
            "details": {"reason": "skip_validation=True"},
        })
        _actions[action_id] = action
        logger.warning(f"Validation skipped for action {action_id}")
        return action

    # Run Constitutional AI validation with composite confidence
    action.status = ActionStatus.VALIDATING
    validation = await _validate_action(request, action, action_create.evidence or {})

    action.validation = validation
    action.updated_at = datetime.utcnow()

    # Add validation to audit log
    action.audit_log.append({
        "timestamp": action.updated_at.isoformat(),
        "event": "validated",
        "details": {
            "passed": validation.passed,
            "authorization_level": validation.authorization_level.value,
            "explanation": validation.explanation,
        },
    })

    # Determine action status based on validation
    if not validation.passed:
        action.status = ActionStatus.REJECTED
        logger.info(f"Action {action_id} rejected: {validation.explanation}")
    elif validation.authorization_level == AuthorizationLevel.AUTOMATIC:
        action.status = ActionStatus.APPROVED
        action.requires_approval = False
        logger.info(f"Action {action_id} auto-approved (composite confidence: {composite_confidence:.4f})")
    elif validation.authorization_level == AuthorizationLevel.APPROVAL_REQUIRED:
        action.status = ActionStatus.AWAITING_APPROVAL
        action.requires_approval = True
        action.expires_at = now + timedelta(hours=4)  # 4 hour approval window
        logger.info(f"Action {action_id} awaiting approval")
    else:  # ALERT_ONLY
        action.status = ActionStatus.REJECTED
        action.requires_approval = False
        logger.info(f"Action {action_id} alert-only (low confidence)")

    _actions[action_id] = action
    return action


@router.get(
    "/",
    response_model=ActionList,
    summary="List Actions",
    description="Get paginated list of actions with optional filters",
)
async def list_actions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: list[ActionStatus] | None = Query(None),
    action_type: list[ActionType] | None = Query(None),
    target_service: str | None = Query(None),
    incident_id: str | None = Query(None),
    requires_approval: bool | None = Query(None),
) -> ActionList:
    """
    List actions with pagination and filters.

    Args:
        page: Page number
        page_size: Items per page
        status: Filter by status
        action_type: Filter by action type
        target_service: Filter by target service
        incident_id: Filter by related incident
        requires_approval: Filter by approval requirement

    Returns:
        Paginated list of actions
    """
    filtered = list(_actions.values())

    if status:
        filtered = [a for a in filtered if a.status in status]

    if action_type:
        filtered = [a for a in filtered if a.action_type in action_type]

    if target_service:
        filtered = [a for a in filtered if a.target_service == target_service]

    if incident_id:
        filtered = [a for a in filtered if a.incident_id == incident_id]

    if requires_approval is not None:
        filtered = [a for a in filtered if a.requires_approval == requires_approval]

    # Sort by created_at descending
    filtered.sort(key=lambda a: a.created_at, reverse=True)

    # Paginate
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    return ActionList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )


@router.get(
    "/pending",
    response_model=PendingApprovals,
    summary="Get Pending Approvals",
    description="Get all actions awaiting human approval",
)
async def get_pending_approvals() -> PendingApprovals:
    """
    Get all actions pending approval.

    Returns:
        Summary of pending approval requests
    """
    pending = [
        a for a in _actions.values()
        if a.status == ActionStatus.AWAITING_APPROVAL
    ]

    # Sort by creation time (oldest first for FIFO processing)
    pending.sort(key=lambda a: a.created_at)

    # Calculate urgency breakdown (based on related incident severity)
    urgency: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for action in pending:
        # Default to medium urgency
        urgency["medium"] += 1

    oldest = pending[0].created_at if pending else None

    return PendingApprovals(
        count=len(pending),
        actions=pending,
        oldest_pending=oldest,
        urgency_breakdown=urgency,
    )


@router.get(
    "/confidence/formula",
    summary="Get Confidence Formula",
    description="Get the composite confidence formula from Research_V7.tex",
    tags=["confidence"],
)
async def get_confidence_formula():
    """
    Get the confidence formula used for action authorization.

    Returns the formula and current weights from Research_V7.tex:
    C(a) = α·C_LLM + β·C_hist + γ·C_sim

    Returns:
        Formula description and weight configuration
    """
    return {
        "formula": "C(a) = α·C_LLM + β·C_hist + γ·C_sim",
        "description": ConfidenceCalculator.get_formula_description(),
        "weights": ConfidenceCalculator.get_weights(),
        "thresholds": {
            "automatic": 0.90,
            "approval_required": 0.70,
            "alert_only": 0.00,
        },
        "defaults": {
            "historical_no_data": ConfidenceCalculator.DEFAULT_HISTORICAL,
            "similarity_no_data": ConfidenceCalculator.DEFAULT_SIMILARITY,
        },
    }


@router.get(
    "/stats",
    response_model=ActionStats,
    summary="Get Action Statistics",
    description="Get aggregated action statistics",
)
async def get_action_stats() -> ActionStats:
    """
    Get action statistics.

    Returns:
        Aggregated action statistics
    """
    actions = list(_actions.values())

    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}

    auto_executed = 0
    human_approved = 0
    rejected = 0
    successful = 0
    total_with_result = 0
    execution_times: list[float] = []

    for action in actions:
        # Count by status
        status_key = action.status.value
        by_status[status_key] = by_status.get(status_key, 0) + 1

        # Count by type
        type_key = action.action_type.value
        by_type[type_key] = by_type.get(type_key, 0) + 1

        # Track approval types
        if action.validation:
            if action.validation.authorization_level == AuthorizationLevel.AUTOMATIC:
                auto_executed += 1
            elif action.approved_by:
                human_approved += 1

        if action.status == ActionStatus.REJECTED:
            rejected += 1

        # Track success rate
        if action.execution_result:
            total_with_result += 1
            if action.execution_result.success:
                successful += 1
            execution_times.append(action.execution_result.duration_ms)

    success_rate = successful / total_with_result if total_with_result > 0 else 1.0
    avg_execution = sum(execution_times) / len(execution_times) if execution_times else None

    return ActionStats(
        total=len(actions),
        by_status=by_status,
        by_type=by_type,
        auto_executed=auto_executed,
        human_approved=human_approved,
        rejected=rejected,
        success_rate=round(success_rate, 3),
        avg_execution_time_ms=avg_execution,
    )


@router.get(
    "/{action_id}",
    response_model=Action,
    summary="Get Action",
    description="Get action by ID",
)
async def get_action(action_id: str) -> Action:
    """
    Get action by ID.

    Args:
        action_id: Unique action identifier

    Returns:
        Action details
    """
    if action_id not in _actions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action {action_id} not found",
        )

    return _actions[action_id]


@router.post(
    "/{action_id}/approve",
    response_model=Action,
    summary="Approve Action",
    description="Human approval for an action",
)
async def approve_action(
    action_id: str,
    approval: ActionApproval,
) -> Action:
    """
    Approve or reject an action.

    Args:
        action_id: Action to approve/reject
        approval: Approval decision and details

    Returns:
        Updated action
    """
    if action_id not in _actions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action {action_id} not found",
        )

    action = _actions[action_id]

    if action.status != ActionStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Action {action_id} is not awaiting approval (status: {action.status.value})",
        )

    now = datetime.utcnow()

    # Check expiration
    if action.expires_at and now > action.expires_at:
        action.status = ActionStatus.EXPIRED
        action.updated_at = now
        action.audit_log.append({
            "timestamp": now.isoformat(),
            "event": "expired",
            "details": {"expired_at": action.expires_at.isoformat()},
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Action {action_id} approval window has expired",
        )

    action.approved_by = approval.approved_by
    action.approved_at = now
    action.approval_comments = approval.comments
    action.updated_at = now

    if approval.approved:
        action.status = ActionStatus.APPROVED
        # Apply modifications if provided
        if approval.modifications:
            action.parameters = {**(action.parameters or {}), **approval.modifications}

        action.audit_log.append({
            "timestamp": now.isoformat(),
            "event": "approved",
            "details": {
                "approved_by": approval.approved_by,
                "comments": approval.comments,
                "modifications": approval.modifications,
            },
        })
        logger.info(f"Action {action_id} approved by {approval.approved_by}")
    else:
        action.status = ActionStatus.REJECTED
        action.audit_log.append({
            "timestamp": now.isoformat(),
            "event": "rejected",
            "details": {
                "rejected_by": approval.approved_by,
                "reason": approval.comments,
            },
        })
        logger.info(f"Action {action_id} rejected by {approval.approved_by}")

    return action


@router.post(
    "/{action_id}/execute",
    response_model=Action,
    summary="Execute Action",
    description="Execute an approved action",
)
async def execute_action(
    request: Request,
    action_id: str,
) -> Action:
    """
    Execute an approved action.

    Only actions with status=APPROVED can be executed.

    Args:
        action_id: Action to execute

    Returns:
        Updated action with execution result
    """
    if action_id not in _actions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action {action_id} not found",
        )

    action = _actions[action_id]

    if action.status != ActionStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Action {action_id} is not approved (status: {action.status.value})",
        )

    now = datetime.utcnow()
    action.status = ActionStatus.EXECUTING
    action.updated_at = now
    action.audit_log.append({
        "timestamp": now.isoformat(),
        "event": "execution_started",
    })

    # Execute the action
    result = await _execute_action(request, action)

    action.execution_result = result
    action.status = ActionStatus.COMPLETED if result.success else ActionStatus.FAILED
    action.updated_at = datetime.utcnow()

    action.audit_log.append({
        "timestamp": action.updated_at.isoformat(),
        "event": "execution_completed",
        "details": {
            "success": result.success,
            "duration_ms": result.duration_ms,
            "error": result.error,
        },
    })

    logger.info(f"Action {action_id} executed: success={result.success}")
    return action


@router.post(
    "/{action_id}/cancel",
    response_model=Action,
    summary="Cancel Action",
    description="Cancel a pending or awaiting-approval action",
)
async def cancel_action(
    action_id: str,
    reason: str = Query(None, description="Cancellation reason"),
) -> Action:
    """
    Cancel an action.

    Args:
        action_id: Action to cancel
        reason: Optional cancellation reason

    Returns:
        Updated action
    """
    if action_id not in _actions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action {action_id} not found",
        )

    action = _actions[action_id]

    cancelable_statuses = [
        ActionStatus.PENDING,
        ActionStatus.AWAITING_APPROVAL,
        ActionStatus.APPROVED,
    ]

    if action.status not in cancelable_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Action {action_id} cannot be cancelled (status: {action.status.value})",
        )

    now = datetime.utcnow()
    action.status = ActionStatus.CANCELLED
    action.updated_at = now
    action.audit_log.append({
        "timestamp": now.isoformat(),
        "event": "cancelled",
        "details": {"reason": reason},
    })

    logger.info(f"Action {action_id} cancelled")
    return action


# Helper functions

async def _validate_action(
    request: Request,
    action: Action,
    evidence: dict[str, Any],
) -> ConstitutionalValidation:
    """Validate action through Constitutional AI."""
    validator = getattr(request.app.state, "validator", None)

    now = datetime.utcnow()

    if validator is None:
        # Fallback validation based on confidence
        logger.warning("Constitutional validator not available, using fallback")

        if action.confidence >= 0.9:
            auth_level = AuthorizationLevel.AUTOMATIC
        elif action.confidence >= 0.7:
            auth_level = AuthorizationLevel.APPROVAL_REQUIRED
        else:
            auth_level = AuthorizationLevel.ALERT_ONLY

        return ConstitutionalValidation(
            passed=action.confidence >= 0.7,
            authorization_level=auth_level,
            confidence=action.confidence,
            tier1_passed=True,
            tier2_passed=True,
            tier3_passed=True,
            violations=[],
            warnings=["Validator not available - using confidence-based authorization"],
            explanation=f"Fallback validation: {auth_level.value}",
            validated_at=now,
        )

    try:
        # Build validation context
        context = {
            "telemetry_evidence": bool(evidence),
            "action_scope": action.parameters.get("scope", "single") if action.parameters else "single",
            "active_incident": bool(action.incident_id),
            "confidence": action.confidence,
            "audit_enabled": _audit_enabled(),
            **evidence,
        }

        # Run validation
        report = validator.validate(
            action_id=action.id,
            action_description=action.description,
            action_type=action.action_type.value,
            confidence=action.confidence,
            context=context,
        )

        # Map authorization level
        from src.constitutional.validator import AuthorizationLevel as ValidatorAuthLevel
        auth_map = {
            ValidatorAuthLevel.AUTOMATIC: AuthorizationLevel.AUTOMATIC,
            ValidatorAuthLevel.APPROVAL_REQUIRED: AuthorizationLevel.APPROVAL_REQUIRED,
            ValidatorAuthLevel.ALERT_ONLY: AuthorizationLevel.ALERT_ONLY,
        }

        return ConstitutionalValidation(
            passed=report.can_proceed or report.requires_approval,
            authorization_level=auth_map[report.authorization_level],
            confidence=report.confidence,
            tier1_passed=report.tier1_passed,
            tier2_passed=report.tier2_passed,
            tier3_passed=report.tier3_passed,
            violations=[
                {
                    "principle_id": v.principle.id,
                    "principle_name": v.principle.name,
                    "reason": v.reason,
                    "severity": v.severity,
                }
                for v in report.violations
            ],
            warnings=report.warnings,
            explanation=report.explanation,
            validated_at=now,
        )

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return ConstitutionalValidation(
            passed=False,
            authorization_level=AuthorizationLevel.ALERT_ONLY,
            confidence=0.0,
            tier1_passed=False,
            tier2_passed=False,
            tier3_passed=False,
            violations=[{"error": str(e)}],
            warnings=[],
            explanation=f"Validation error: {str(e)}",
            validated_at=now,
        )


# Action types that map onto a real, whitelisted tool executor. Everything
# else has NO executor wired and must fail honestly instead of pretending.
_REAL_EXECUTOR_TOOLS: dict[ActionType, str] = {
    ActionType.RESTART_SERVICE: "restart_service",
    ActionType.SCALE_UP: "scale_service",
    ActionType.SCALE_DOWN: "scale_service",
}


async def _execute_action(
    request: Request,
    action: Action,
) -> ActionExecutionResult:
    """Execute the action through the real gated tool pipeline.

    Routes restart/scale actions through ``execute_tool_call`` so the
    ``AIOPS_ENABLE_ACTION_TOOLS`` kill-switch, container whitelist and the
    constitutional gate are all enforced — the same path chat and incident
    remediation use. Action types with no real executor return an explicit
    failure rather than a simulated success (this replaces the old
    ``random() < 0.9`` mock).
    """
    from src.api.routes.tools import execute_tool_call

    start_time = datetime.utcnow()
    params = action.parameters or {}

    tool_name = _REAL_EXECUTOR_TOOLS.get(action.action_type)
    if tool_name is None:
        end_time = datetime.utcnow()
        return ActionExecutionResult(
            success=False,
            output=None,
            error=(
                f"No real executor is wired for action type "
                f"'{action.action_type.value}'. Only restart_service / scale_up / "
                f"scale_down execute (via the gated tool pipeline); refusing to "
                f"simulate success."
            ),
            started_at=start_time,
            completed_at=end_time,
            duration_ms=round((end_time - start_time).total_seconds() * 1000, 2),
            rollback_available=False,
        )

    parameters: dict[str, Any] = {
        "service_name": action.target_service,
        "reason": action.description or f"Action {action.id}",
        "confidence": action.confidence,
    }
    if tool_name == "restart_service":
        parameters["graceful"] = params.get("graceful", True)
    else:
        parameters["target_replicas"] = params.get(
            "target_replicas", params.get("replicas")
        )

    result = await execute_tool_call(
        request,
        tool_name=tool_name,
        parameters=parameters,
        context={
            # Honest signals only: APPROVED can be automatic, so assert a human
            # only when one actually approved; incident linkage as recorded.
            "human_approved": action.approved_by is not None,
            "active_incident": bool(action.incident_id),
            "telemetry_evidence": bool(action.validation),
            "audit_enabled": _audit_enabled(),
            "source": "actions_execute",
            "action_id": action.id,
        },
    )

    end_time = datetime.utcnow()

    success = bool(result.get("success"))
    if success:
        data = result.get("data") or {}
        output = (
            f"Executed {tool_name} on {data.get('container', action.target_service)}"
            f" (status: {data.get('status', 'completed')})"
        )
        error = None
    else:
        output = None
        error = result.get("error") or "Execution failed"
        error_code = result.get("error_code")
        if error_code:
            error = f"[{error_code}] {error}"

    return ActionExecutionResult(
        success=success,
        output=output,
        error=error,
        started_at=start_time,
        completed_at=end_time,
        duration_ms=round((end_time - start_time).total_seconds() * 1000, 2),
        rollback_available=success,
    )


__all__ = ["router"]
