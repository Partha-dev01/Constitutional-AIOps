"""Durable persistence layer (stdlib sqlite3) for app state.

Conversations, incidents, pending remediation actions and the incident
counter were previously in-memory only (wiped on every backend restart).
This package provides a tiny write-through SQLite store under
``AIOPS_DATA_DIR`` (the same EBS-backed data dir as ``src/auth/store.py``)
so that state survives restarts/redeploys. The in-memory dicts in the chat
and incident routes stay the read fast-path; this store is the durable sink.
"""

from src.persistence import store

__all__ = ["store"]
