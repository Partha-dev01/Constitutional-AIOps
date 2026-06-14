"""
Constitutional AIOps - durable app-state store (stdlib sqlite3 only).

Conversations, incidents, pending remediation actions and the incident
counter live in a small SQLite database at
``${AIOPS_DATA_DIR:-./data}/state.db`` — the same data-dir convention as
``src/auth/store.py`` (which lands on the EBS bind-mount in production).
WAL mode, one short-lived connection per operation; these payloads are
small and traffic is low, so synchronous writes are fine (mirrors the auth
store). The in-memory dicts in the chat/incident routes remain the read
fast-path: this module is the write-through durable sink, hydrated once at
startup.

Tables:
    conversations(id TEXT PK, owner TEXT, created_at TEXT, updated_at TEXT,
                  data_json TEXT NOT NULL)
    incidents(id TEXT PK, created_at TEXT, updated_at TEXT, data_json TEXT NOT NULL)
    pending_actions(id TEXT PK, created_at TEXT, data_json TEXT NOT NULL)
    counters(name TEXT PK, value INTEGER NOT NULL)

Serialization uses pydantic ``model_dump_json()`` / ``Model.model_validate_json()``
for the typed rows and plain ``json`` for the pending-action dict. Corrupt
rows are logged and skipped on load — a bad row never crashes startup.
"""

import json
import logging
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Optional

from src.api.schemas.chat import ConversationHistory
from src.api.schemas.incident import Incident

logger = logging.getLogger(__name__)


def data_dir() -> Path:
    """Return the app data directory (AIOPS_DATA_DIR env or repo-local ./data).

    Mirrors ``src/auth/store.py:data_dir`` so persisted state lands in the
    same EBS-backed directory in production and falls back to ``./data``
    locally when the env var is unset.
    """
    base = os.environ.get("AIOPS_DATA_DIR") or os.path.join(
        os.path.dirname(__file__), "..", "..", "data"
    )
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _db_path() -> Path:
    return data_dir() / "state.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create the persistence tables if they do not exist (idempotent)."""
    with closing(_connect()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                owner TEXT,
                created_at TEXT,
                updated_at TEXT,
                data_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                created_at TEXT,
                updated_at TEXT,
                data_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_actions (
                id TEXT PRIMARY KEY,
                created_at TEXT,
                data_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS counters (
                name TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            )
            """
        )
        # Editable platform-topology schema (single-document key/value rows).
        # Holds the operator's applied custom schema (key "custom_schema") and
        # the active mode flag (key "mode" ∈ {"discovered","custom"}). Additive:
        # never touched by the conversation/incident/action/counter paths.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS topology_state (
                key TEXT PRIMARY KEY,
                data_json TEXT NOT NULL
            )
            """
        )


def _iso(value: Any) -> Optional[str]:
    """Best-effort ISO string for an optional datetime (for the index columns)."""
    if value is None:
        return None
    try:
        return value.isoformat()
    except AttributeError:
        return str(value)


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------

def save_conversation(conversation: ConversationHistory) -> None:
    """Write-through persist (insert-or-replace) a full conversation."""
    init_db()
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO conversations (id, owner, created_at, updated_at, data_json)"
            " VALUES (?, ?, ?, ?, ?)"
            " ON CONFLICT(id) DO UPDATE SET"
            "   owner = excluded.owner,"
            "   created_at = excluded.created_at,"
            "   updated_at = excluded.updated_at,"
            "   data_json = excluded.data_json",
            (
                conversation.conversation_id,
                getattr(conversation, "owner", None),
                _iso(conversation.created_at),
                _iso(conversation.updated_at),
                conversation.model_dump_json(),
            ),
        )


def delete_conversation(conversation_id: str) -> None:
    """Remove a conversation from durable storage (no-op when absent)."""
    init_db()
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))


def load_all_conversations() -> dict[str, ConversationHistory]:
    """Load every persisted conversation, skipping corrupt rows.

    Returns a dict keyed by ``conversation_id`` ready to ``.update()`` the
    in-memory ``_conversations`` store at startup.
    """
    init_db()
    out: dict[str, ConversationHistory] = {}
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, data_json FROM conversations"
        ).fetchall()
    for row in rows:
        try:
            conv = ConversationHistory.model_validate_json(row["data_json"])
        except Exception as exc:  # noqa: BLE001 - tolerate any bad/legacy row
            logger.warning(
                "Skipping corrupt conversation row id=%s: %s", row["id"], exc
            )
            continue
        out[conv.conversation_id] = conv
    return out


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------

def save_incident(incident: Incident) -> None:
    """Write-through persist (insert-or-replace) a full incident."""
    init_db()
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO incidents (id, created_at, updated_at, data_json)"
            " VALUES (?, ?, ?, ?)"
            " ON CONFLICT(id) DO UPDATE SET"
            "   created_at = excluded.created_at,"
            "   updated_at = excluded.updated_at,"
            "   data_json = excluded.data_json",
            (
                incident.id,
                _iso(incident.created_at),
                _iso(incident.updated_at),
                incident.model_dump_json(),
            ),
        )


def delete_incident(incident_id: str) -> None:
    """Remove an incident from durable storage (no-op when absent)."""
    init_db()
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))


def load_all_incidents() -> dict[str, Incident]:
    """Load every persisted incident, skipping corrupt rows."""
    init_db()
    out: dict[str, Incident] = {}
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT id, data_json FROM incidents").fetchall()
    for row in rows:
        try:
            inc = Incident.model_validate_json(row["data_json"])
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Skipping corrupt incident row id=%s: %s", row["id"], exc
            )
            continue
        out[inc.id] = inc
    return out


# ---------------------------------------------------------------------------
# Pending remediation actions (plain dicts, not pydantic models)
# ---------------------------------------------------------------------------

def save_pending_action(action_id: str, entry: dict[str, Any]) -> None:
    """Write-through persist a pending remediation action cache entry.

    ``entry`` is the same dict the chat route caches:
    ``{tool_name, parameters, owner, conversation_id, created_at, proposed_action}``.
    """
    init_db()
    created_at = entry.get("created_at")
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO pending_actions (id, created_at, data_json)"
            " VALUES (?, ?, ?)"
            " ON CONFLICT(id) DO UPDATE SET"
            "   created_at = excluded.created_at,"
            "   data_json = excluded.data_json",
            (
                action_id,
                str(created_at) if created_at is not None else None,
                json.dumps(entry, default=str),
            ),
        )


def delete_pending_action(action_id: str) -> None:
    """Remove a pending action from durable storage (no-op when absent)."""
    init_db()
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM pending_actions WHERE id = ?", (action_id,))


def load_all_pending_actions() -> dict[str, dict[str, Any]]:
    """Load every persisted pending action, skipping corrupt rows."""
    init_db()
    out: dict[str, dict[str, Any]] = {}
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, data_json FROM pending_actions"
        ).fetchall()
    for row in rows:
        try:
            parsed = json.loads(row["data_json"])
            if not isinstance(parsed, dict):
                raise ValueError("pending action row is not a JSON object")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Skipping corrupt pending_action row id=%s: %s", row["id"], exc
            )
            continue
        out[row["id"]] = parsed
    return out


# ---------------------------------------------------------------------------
# Counters (durable incident sequence, etc.)
# ---------------------------------------------------------------------------

def set_counter(name: str, value: int) -> None:
    """Persist an integer counter under ``name`` (insert-or-replace)."""
    init_db()
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO counters (name, value) VALUES (?, ?)"
            " ON CONFLICT(name) DO UPDATE SET value = excluded.value",
            (name, int(value)),
        )


def get_counter(name: str, default: int = 0) -> int:
    """Return the persisted counter value, or ``default`` when absent/corrupt."""
    init_db()
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT value FROM counters WHERE name = ?", (name,)
        ).fetchone()
    if row is None:
        return default
    try:
        return int(row["value"])
    except (TypeError, ValueError):
        logger.warning("Corrupt counter value for '%s'; using default", name)
        return default


# ---------------------------------------------------------------------------
# Editable platform-topology schema (single-document store)
# ---------------------------------------------------------------------------

# Row keys for the ``topology_state`` table.
_TOPOLOGY_SCHEMA_KEY = "custom_schema"
_TOPOLOGY_MODE_KEY = "mode"

# Active-mode flag values.
TOPOLOGY_MODE_DISCOVERED = "discovered"
TOPOLOGY_MODE_CUSTOM = "custom"


def save_topology_schema(schema: dict[str, Any]) -> None:
    """Persist the applied custom topology schema and flip mode to ``custom``.

    ``schema`` is the validated ``{"nodes": [...], "edges": [...]}`` document
    (already strict-validated by the topology route). Insert-or-replace, so a
    re-Apply overwrites the prior custom schema atomically.
    """
    init_db()
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO topology_state (key, data_json) VALUES (?, ?)"
            " ON CONFLICT(key) DO UPDATE SET data_json = excluded.data_json",
            (_TOPOLOGY_SCHEMA_KEY, json.dumps(schema)),
        )
        conn.execute(
            "INSERT INTO topology_state (key, data_json) VALUES (?, ?)"
            " ON CONFLICT(key) DO UPDATE SET data_json = excluded.data_json",
            (_TOPOLOGY_MODE_KEY, json.dumps(TOPOLOGY_MODE_CUSTOM)),
        )


def load_topology_schema() -> Optional[dict[str, Any]]:
    """Return the persisted custom topology schema dict, or ``None`` if absent/corrupt."""
    init_db()
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT data_json FROM topology_state WHERE key = ?",
            (_TOPOLOGY_SCHEMA_KEY,),
        ).fetchone()
    if row is None:
        return None
    try:
        parsed = json.loads(row["data_json"])
        if not isinstance(parsed, dict):
            raise ValueError("topology schema row is not a JSON object")
        return parsed
    except Exception as exc:  # noqa: BLE001 - tolerate any bad/legacy row
        logger.warning("Skipping corrupt topology schema row: %s", exc)
        return None


def get_topology_mode() -> str:
    """Return the active topology mode (``discovered`` | ``custom``).

    Defaults to ``discovered`` when unset/corrupt, and never reports ``custom``
    without a persisted schema actually present — so a missing schema can never
    leave the live endpoint pointing at nothing.
    """
    init_db()
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT data_json FROM topology_state WHERE key = ?",
            (_TOPOLOGY_MODE_KEY,),
        ).fetchone()
    mode = TOPOLOGY_MODE_DISCOVERED
    if row is not None:
        try:
            value = json.loads(row["data_json"])
            if value == TOPOLOGY_MODE_CUSTOM:
                mode = TOPOLOGY_MODE_CUSTOM
        except Exception as exc:  # noqa: BLE001
            logger.warning("Corrupt topology mode row; defaulting to discovered: %s", exc)
    # Safety: only honour "custom" when a schema is actually persisted.
    if mode == TOPOLOGY_MODE_CUSTOM and load_topology_schema() is None:
        return TOPOLOGY_MODE_DISCOVERED
    return mode


def reset_topology_mode() -> None:
    """Revert to discovered mode (drop the custom schema + mode rows)."""
    init_db()
    with closing(_connect()) as conn, conn:
        conn.execute(
            "DELETE FROM topology_state WHERE key IN (?, ?)",
            (_TOPOLOGY_SCHEMA_KEY, _TOPOLOGY_MODE_KEY),
        )


__all__ = [
    "data_dir",
    "init_db",
    "save_conversation",
    "delete_conversation",
    "load_all_conversations",
    "save_incident",
    "delete_incident",
    "load_all_incidents",
    "save_pending_action",
    "delete_pending_action",
    "load_all_pending_actions",
    "set_counter",
    "get_counter",
    "TOPOLOGY_MODE_DISCOVERED",
    "TOPOLOGY_MODE_CUSTOM",
    "save_topology_schema",
    "load_topology_schema",
    "get_topology_mode",
    "reset_topology_mode",
]
