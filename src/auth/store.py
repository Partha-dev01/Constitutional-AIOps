"""
Constitutional AIOps - SQLite user store (stdlib only).

Users + per-user settings live in a small SQLite database at
``${AIOPS_DATA_DIR:-./data}/users.db`` (same data-dir convention as
src/api/routes/settings.py). WAL mode, one short-lived connection per
operation — traffic on these tables is tiny (login + admin CRUD).

Tables:
    users(id TEXT PK, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
          role TEXT NOT NULL DEFAULT 'user', token_version INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL)
    user_settings(user_id TEXT PK REFERENCES users(id), settings_json TEXT NOT NULL)
"""

import json
import logging
import os
import sqlite3
import uuid
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.auth.passwords import hash_password, validate_password_policy, verify_password

logger = logging.getLogger(__name__)

VALID_ROLES = ("user", "admin")

# A real (but throwaway) scrypt hash used to equalise the timing of
# authenticate() for unknown usernames, mitigating user enumeration.
_DUMMY_HASH = hash_password(uuid.uuid4().hex)


@dataclass(frozen=True)
class UserRecord:
    """Full user row as stored in SQLite (includes the password hash)."""

    id: str
    username: str
    password_hash: str
    role: str
    token_version: int
    created_at: str
    # Added for public self-service signup (R3). Existing admin/operator-created
    # rows have email=None, email_verified=False; both are optional everywhere.
    email: Optional[str] = None
    email_verified: bool = False


@dataclass(frozen=True)
class AccessTokenRecord:
    """A personal access token row. Only the SHA-256 of the token is stored.

    The plaintext token is shown to the user exactly once at creation and never
    persisted. ``prefix`` is a non-secret display fragment so the owner can tell
    their tokens apart in a listing.
    """

    id: str
    user_id: str
    name: str
    token_hash: str
    prefix: str
    created_at: str
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None


def data_dir() -> Path:
    """Return the app data directory (AIOPS_DATA_DIR env or repo-local ./data)."""
    base = os.environ.get("AIOPS_DATA_DIR") or os.path.join(
        os.path.dirname(__file__), "..", "..", "data"
    )
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _db_path() -> Path:
    return data_dir() / "users.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create the auth tables if they do not exist (idempotent)."""
    with closing(_connect()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                token_version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY REFERENCES users(id),
                settings_json TEXT NOT NULL
            )
            """
        )
        # Migration (R3 signup): add email columns to pre-existing databases.
        # CREATE TABLE IF NOT EXISTS never alters an existing table, so add the
        # columns idempotently based on the live schema.
        existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        if "email" not in existing_cols:
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
        if "email_verified" not in existing_cols:
            conn.execute(
                "ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0"
            )
        # Personal access tokens (Track 3). Only the SHA-256 hash is stored.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS access_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id),
                name TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                prefix TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_used_at TEXT,
                expires_at TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_access_tokens_user ON access_tokens(user_id)"
        )


def _row_to_record(row: sqlite3.Row) -> UserRecord:
    keys = row.keys()
    return UserRecord(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
        role=row["role"],
        token_version=int(row["token_version"]),
        created_at=row["created_at"],
        email=row["email"] if "email" in keys else None,
        email_verified=bool(row["email_verified"]) if "email_verified" in keys else False,
    )


def _row_to_access_token(row: sqlite3.Row) -> AccessTokenRecord:
    return AccessTokenRecord(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        token_hash=row["token_hash"],
        prefix=row["prefix"],
        created_at=row["created_at"],
        last_used_at=row["last_used_at"],
        expires_at=row["expires_at"],
    )


def create_user(
    username: str,
    password: str,
    role: str = "user",
    email: Optional[str] = None,
    email_verified: bool = False,
) -> UserRecord:
    """Create a user. Raises ValueError for bad input or a duplicate username/email."""
    username = (username or "").strip()
    if not username:
        raise ValueError("Username must not be empty")
    if role not in VALID_ROLES:
        raise ValueError(f"Role must be one of {VALID_ROLES}")
    validate_password_policy(password, username)

    email = (email or "").strip().lower() or None
    if email is not None and get_by_email(email) is not None:
        raise ValueError(f"Email '{email}' already exists")

    record = UserRecord(
        id=uuid.uuid4().hex,
        username=username,
        password_hash=hash_password(password),
        role=role,
        token_version=1,
        created_at=datetime.now(timezone.utc).isoformat(),
        email=email,
        email_verified=bool(email_verified),
    )
    init_db()
    try:
        with closing(_connect()) as conn, conn:
            conn.execute(
                "INSERT INTO users (id, username, password_hash, role, token_version,"
                " created_at, email, email_verified) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.id,
                    record.username,
                    record.password_hash,
                    record.role,
                    record.token_version,
                    record.created_at,
                    record.email,
                    1 if record.email_verified else 0,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"Username '{username}' already exists") from exc
    return record


def get_by_username(username: str) -> Optional[UserRecord]:
    init_db()
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    return _row_to_record(row) if row else None


def get_by_email(email: str) -> Optional[UserRecord]:
    """Look up a user by (case-insensitive) email. None when absent."""
    email = (email or "").strip().lower()
    if not email:
        return None
    init_db()
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    return _row_to_record(row) if row else None


def get_by_id(user_id: str) -> Optional[UserRecord]:
    """Look up a user by primary-key id. None when absent."""
    user_id = (user_id or "").strip()
    if not user_id:
        return None
    init_db()
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return _row_to_record(row) if row else None


def mark_email_verified(user_id: str) -> bool:
    """Flag a user's email as verified. Returns False when the id is unknown."""
    init_db()
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "UPDATE users SET email_verified = 1 WHERE id = ?", (user_id,)
        )
    return cur.rowcount > 0


def list_users() -> list[UserRecord]:
    init_db()
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at").fetchall()
    return [_row_to_record(r) for r in rows]


def count_users() -> int:
    init_db()
    with closing(_connect()) as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    return int(count)


def delete_user(username: str) -> bool:
    """Delete a user (and their settings + access tokens). False when absent."""
    record = get_by_username(username)
    if record is None:
        return False
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM access_tokens WHERE user_id = ?", (record.id,))
        conn.execute("DELETE FROM user_settings WHERE user_id = ?", (record.id,))
        conn.execute("DELETE FROM users WHERE id = ?", (record.id,))
    return True


def set_password(username: str, password: str) -> bool:
    """Set a new password and bump token_version (invalidates old sessions).

    Returns False when the user does not exist. Raises ValueError when the
    new password violates the policy.
    """
    record = get_by_username(username)
    if record is None:
        return False
    validate_password_policy(password, username)
    with closing(_connect()) as conn, conn:
        conn.execute(
            "UPDATE users SET password_hash = ?, token_version = token_version + 1"
            " WHERE id = ?",
            (hash_password(password), record.id),
        )
    return True


def authenticate(username: str, password: str) -> Optional[UserRecord]:
    """Return the user record when username+password match, else None."""
    record = get_by_username(username)
    if record is None:
        # Burn comparable CPU to a real verification (timing-equalisation).
        verify_password(password or "", _DUMMY_HASH)
        return None
    if not verify_password(password or "", record.password_hash):
        return None
    return record


def bump_token_version(username: str) -> Optional[int]:
    """Increment token_version (invalidates all sessions). Returns new value."""
    record = get_by_username(username)
    if record is None:
        return None
    with closing(_connect()) as conn, conn:
        conn.execute(
            "UPDATE users SET token_version = token_version + 1 WHERE id = ?",
            (record.id,),
        )
        (new_version,) = conn.execute(
            "SELECT token_version FROM users WHERE id = ?", (record.id,)
        ).fetchone()
    return int(new_version)


def get_user_settings(user_id: str) -> Optional[dict[str, Any]]:
    """Return the per-user settings dict, or None when absent/corrupt."""
    init_db()
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT settings_json FROM user_settings WHERE user_id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    try:
        parsed = json.loads(row["settings_json"])
        return parsed if isinstance(parsed, dict) else None
    except (json.JSONDecodeError, TypeError):
        logger.warning("Corrupt settings_json for user %s; ignoring", user_id)
        return None


def set_user_settings(user_id: str, settings: dict[str, Any]) -> None:
    init_db()
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO user_settings (user_id, settings_json) VALUES (?, ?)"
            " ON CONFLICT(user_id) DO UPDATE SET settings_json = excluded.settings_json",
            (user_id, json.dumps(settings)),
        )


# ---------------------------------------------------------------------------
# Personal access tokens (Track 3)
# ---------------------------------------------------------------------------


def create_access_token(
    user_id: str,
    name: str,
    token_hash: str,
    prefix: str,
    expires_at: Optional[str] = None,
) -> AccessTokenRecord:
    """Persist a new access token (hash only). Raises ValueError on a hash clash."""
    record = AccessTokenRecord(
        id=uuid.uuid4().hex,
        user_id=user_id,
        name=name,
        token_hash=token_hash,
        prefix=prefix,
        created_at=datetime.now(timezone.utc).isoformat(),
        last_used_at=None,
        expires_at=expires_at,
    )
    init_db()
    try:
        with closing(_connect()) as conn, conn:
            conn.execute(
                "INSERT INTO access_tokens (id, user_id, name, token_hash, prefix,"
                " created_at, last_used_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.id,
                    record.user_id,
                    record.name,
                    record.token_hash,
                    record.prefix,
                    record.created_at,
                    record.last_used_at,
                    record.expires_at,
                ),
            )
    except sqlite3.IntegrityError as exc:  # pragma: no cover - astronomically rare
        raise ValueError("Token hash collision; retry") from exc
    return record


def list_access_tokens(user_id: str) -> list[AccessTokenRecord]:
    """Return a user's access tokens (newest first). Never includes plaintext."""
    init_db()
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM access_tokens WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return [_row_to_access_token(r) for r in rows]


def count_access_tokens(user_id: str) -> int:
    init_db()
    with closing(_connect()) as conn:
        (count,) = conn.execute(
            "SELECT COUNT(*) FROM access_tokens WHERE user_id = ?", (user_id,)
        ).fetchone()
    return int(count)


def get_access_token_by_hash(token_hash: str) -> Optional[AccessTokenRecord]:
    init_db()
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM access_tokens WHERE token_hash = ?", (token_hash,)
        ).fetchone()
    return _row_to_access_token(row) if row else None


def touch_access_token(token_id: str, when_iso: str) -> None:
    """Best-effort last_used_at update (swallows errors; never blocks a request)."""
    try:
        with closing(_connect()) as conn, conn:
            conn.execute(
                "UPDATE access_tokens SET last_used_at = ? WHERE id = ?",
                (when_iso, token_id),
            )
    except sqlite3.Error:  # pragma: no cover - best-effort telemetry only
        logger.debug("Could not update last_used_at for token %s", token_id)


def delete_access_token(user_id: str, token_id: str) -> bool:
    """Delete one of the user's own tokens. False when it is not theirs/absent."""
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "DELETE FROM access_tokens WHERE id = ? AND user_id = ?",
            (token_id, user_id),
        )
    return cur.rowcount > 0


def ensure_initial_admin() -> Optional[UserRecord]:
    """Bootstrap the first admin from env on an EMPTY users table.

    Creates AUTH_ADMIN_USER/AUTH_ADMIN_PASSWORD as role=admin only when the
    table has no users at all (so it never overrides operator-managed users).
    Idempotent: subsequent calls are no-ops. Returns the created record, or
    None when nothing was created.
    """
    init_db()
    if count_users() > 0:
        return None
    admin_user = os.environ.get("AUTH_ADMIN_USER", "").strip()
    admin_password = os.environ.get("AUTH_ADMIN_PASSWORD", "")
    if not admin_user or not admin_password:
        return None
    try:
        record = create_user(admin_user, admin_password, role="admin")
    except ValueError as exc:
        # e.g. password policy violation — refuse to create a weak bootstrap
        # admin; with AUTH_REQUIRED=true the startup guard-rail will then fail
        # fast on the still-empty table.
        logger.warning("Initial admin bootstrap skipped: %s", exc)
        return None
    logger.info("Bootstrapped initial admin user '%s'", record.username)
    return record


__all__ = [
    "AccessTokenRecord",
    "UserRecord",
    "VALID_ROLES",
    "authenticate",
    "bump_token_version",
    "count_access_tokens",
    "count_users",
    "create_access_token",
    "create_user",
    "data_dir",
    "delete_access_token",
    "delete_user",
    "ensure_initial_admin",
    "get_access_token_by_hash",
    "get_by_email",
    "get_by_id",
    "get_by_username",
    "get_user_settings",
    "init_db",
    "list_access_tokens",
    "list_users",
    "mark_email_verified",
    "set_password",
    "set_user_settings",
    "touch_access_token",
]
