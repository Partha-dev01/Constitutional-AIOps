"""
Constitutional AIOps - Notification inbox API routes (admin only).

Read + light-mutate access to the in-app alert center backed by
``src.notifications.store``. Admin-gated like the audit log: notifications
describe operational events (actions awaiting approval, blocked actions), so
they are not exposed to non-admin users. There is no endpoint that CREATES a
notification from the client -- alerts are emitted server-side, in-request, at
the point the event actually happens.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.auth.deps import User, coerce_user, is_synthetic, require_user
from src.notifications.store import NOTIFICATION_SEVERITIES, get_notification_store

logger = logging.getLogger(__name__)

router = APIRouter()


def _require_admin(user: User) -> User:
    """Reject non-admin callers (synthetic / AUTH-off callers are admin)."""
    user = coerce_user(user)
    if not is_synthetic(user) and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins may view notifications",
        )
    return user


class MarkReadRequest(BaseModel):
    """Mark specific notifications read, or all of them."""

    ids: list[str] = Field(default_factory=list)
    all: bool = False


@router.get("/")
async def list_notifications(
    user: User = Depends(require_user),
    limit: int = Query(default=100, ge=1, le=500),
    unread_only: bool = Query(default=False),
    severity: Optional[str] = Query(default=None),
) -> dict:
    """Return notifications, newest first. Admin only.

    An empty list is the honest result on a fresh instance -- the inbox fills
    as the system raises alerts (actions awaiting approval, blocked actions).
    """
    _require_admin(user)

    if severity is not None and severity not in NOTIFICATION_SEVERITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown severity: {severity}",
        )

    store = get_notification_store()
    notifications = store.list(limit=limit, unread_only=unread_only, severity=severity)
    return {
        "notifications": notifications,
        "count": len(notifications),
        "unread": store.unread_count(),
    }


@router.get("/unread-count")
async def unread_count(user: User = Depends(require_user)) -> dict:
    """Return the number of unread notifications. Admin only."""
    _require_admin(user)
    return {"unread": get_notification_store().unread_count()}


@router.post("/read")
async def mark_read(
    user: User = Depends(require_user),
    body: MarkReadRequest = Body(default_factory=MarkReadRequest),
) -> dict:
    """Mark notifications read (specific ids, or all). Admin only."""
    _require_admin(user)
    store = get_notification_store()
    changed = store.mark_read(ids=body.ids, mark_all=body.all)
    return {"updated": changed, "unread": store.unread_count()}


@router.delete("/")
async def clear_notifications(user: User = Depends(require_user)) -> dict:
    """Remove every notification. Admin only."""
    _require_admin(user)
    removed = get_notification_store().clear()
    return {"cleared": removed}


__all__ = ["router"]
