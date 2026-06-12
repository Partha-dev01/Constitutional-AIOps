"""
Constitutional AIOps - In-app authentication (stdlib-only).

Modules:
    passwords  - scrypt password hashing + policy
    tokens     - HMAC-SHA256-signed session tokens
    store      - SQLite user store (users + per-user settings)
    deps       - FastAPI dependencies (require_user / require_admin)
"""

from src.auth.deps import (
    User,
    auth_required,
    coerce_user,
    get_current_user,
    is_synthetic,
    require_admin,
    require_user,
    synthetic_admin,
)
from src.auth.passwords import hash_password, validate_password_policy, verify_password
from src.auth.store import (
    UserRecord,
    authenticate,
    bump_token_version,
    count_users,
    create_user,
    delete_user,
    ensure_initial_admin,
    get_by_username,
    get_user_settings,
    init_db,
    list_users,
    set_password,
    set_user_settings,
)
from src.auth.tokens import COOKIE_NAME, SESSION_TTL_SECONDS, sign_session, verify_session

__all__ = [
    "COOKIE_NAME",
    "SESSION_TTL_SECONDS",
    "User",
    "UserRecord",
    "auth_required",
    "authenticate",
    "bump_token_version",
    "coerce_user",
    "count_users",
    "create_user",
    "delete_user",
    "ensure_initial_admin",
    "get_by_username",
    "get_current_user",
    "get_user_settings",
    "hash_password",
    "init_db",
    "is_synthetic",
    "list_users",
    "require_admin",
    "require_user",
    "set_password",
    "set_user_settings",
    "sign_session",
    "synthetic_admin",
    "validate_password_policy",
    "verify_password",
    "verify_session",
]
