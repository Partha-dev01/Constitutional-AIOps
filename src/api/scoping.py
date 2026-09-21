"""Per-user data scoping for the operational record stores (SEC-M1).

The problem this closes: `_actions` in `routes/actions.py` and `_incidents` in
`routes/incidents.py` are process-global dicts with no notion of an owner, so
any authenticated account could list and read every other account's records,
and read any record by guessing or observing its id. That stayed latent while
the box had a single admin, but public signup is ON, so a second account can
exist at any time.

**Two deliberately different rules, and the difference is the point.**

* **Chat conversations are private.** `routes/chat.py` already enforces its own
  rule via `_can_access` and is NOT changed by this module: an admin does not
  get to read another person's conversations. Do not "unify" the two.
* **Actions and incidents are operational records about shared
  infrastructure.** The admin operator has to see all of them or they cannot
  run the system, so here an admin sees everything and a non-admin sees only
  what they created.

Records that predate this change, and everything the telemetry pipeline files
on its own, carry no real owner. Those are **admin-only**, which is the same
way `chat.py` treats its legacy owner-less rows: fail closed rather than
exposing an unowned record to whoever asks first.

Ownership is deliberately kept OFF the public schema. `Action.created_by`
already existed for this (its description reads "Creator (system or user ID)")
and was hardcoded to `"system"`, so actions needed no schema change at all, and
incident ownership lives in a server-side column rather than on the model. That
keeps `openapi/openapi.json` byte-identical, which keeps both generated SDK
cores valid and `sdk-drift` green.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from src.auth.deps import User

# `Action.created_by` defaults to this, and the telemetry pipeline files
# incidents under no user at all. Either way it means "not a person", so it
# must never match a real account, not even one that managed to register the
# username "system".
PIPELINE_OWNER = "system"

__all__ = ["PIPELINE_OWNER", "can_access", "owner_or_404", "visible_owner"]


def can_access(owner: str | None, user: User) -> bool:
    """May `user` see a record owned by `owner`?

    Admin sees everything. Everyone else sees only their own records, and an
    unowned or pipeline-owned record is nobody's, so it is admin-only.
    """
    if user.role == "admin":
        return True
    if not owner or owner == PIPELINE_OWNER:
        return False
    return owner == user.username


def visible_owner(owner: str | None) -> str | None:
    """Normalise a stored owner to a real username, or None for 'not a person'."""
    if not owner or owner == PIPELINE_OWNER:
        return None
    return owner


def owner_or_404(owner: str | None, user: User, detail: str) -> None:
    """Raise 404 (never 403) when `user` may not see this record.

    404 rather than 403 on purpose: a 403 confirms the id exists, which hands a
    prober a way to enumerate other accounts' record ids one request at a time.
    The caller has already established the record IS there, so this reads as
    "not found for you".
    """
    if not can_access(owner, user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
