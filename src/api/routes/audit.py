"""
Constitutional AIOps - Audit Log API Routes

Read-only viewer over the JSONL audit trail written by ``src.utils.audit``.
Admin-gated: the trail records who approved or ran what, so it is not exposed
to non-admin users. Reads only -- there is no endpoint that mutates the trail.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.auth.deps import User, coerce_user, is_synthetic, require_user
from src.utils.audit import AuditEventType, get_audit_logger

logger = logging.getLogger(__name__)

router = APIRouter()

# A generous internal cap so "newest first" is computed over the whole window
# rather than the first N chronological rows the underlying scanner returns.
_SCAN_CAP = 5000


def _require_admin(user: User) -> User:
    """Reject non-admin callers (synthetic/AUTH-off callers are treated as admin)."""
    user = coerce_user(user)
    if not is_synthetic(user) and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins may view the audit log",
        )
    return user


@router.get("/")
async def list_audit_events(
    user: User = Depends(require_user),
    limit: int = Query(default=100, ge=1, le=500),
    days: int = Query(default=7, ge=1, le=90),
    event_type: Optional[str] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    actor_id: Optional[str] = Query(default=None),
) -> dict:
    """Return recent audit events, newest first. Admin only.

    An empty list is a normal, honest result on a fresh instance -- the trail
    only fills as validations, approvals and actions happen.
    """
    _require_admin(user)

    event_types = None
    if event_type:
        try:
            event_types = [AuditEventType(event_type)]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown event_type: {event_type}",
            )

    start_date = datetime.utcnow() - timedelta(days=days)
    try:
        raw = get_audit_logger().query_events(
            start_date=start_date,
            event_types=event_types,
            resource_type=resource_type or None,
            actor_id=actor_id or None,
            limit=_SCAN_CAP,
        )
    except Exception as exc:  # never surface a 500 for a read-only viewer
        logger.warning("Audit query failed: %s", exc)
        raw = []

    raw.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    events = raw[:limit]
    return {"events": events, "count": len(events), "truncated": len(raw) > limit}


@router.get("/event-types")
async def list_event_types(user: User = Depends(require_user)) -> dict:
    """Return the known audit event-type values (for a filter dropdown). Admin only."""
    _require_admin(user)
    return {"event_types": [et.value for et in AuditEventType]}


__all__ = ["router"]
