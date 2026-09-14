"""Persistent embedded episode store (stdlib ``sqlite3`` only).

A dependency-free, durable backend for graph-episodic memory. It is the
persistence layer of the ``embedded`` graph backend
(``AIOPS_GRAPH_BACKEND=embedded``), used by the lite self-host tier so the
episodic graph survives restarts without a Neo4j container.

It sits UNDER ``EpisodeStore``'s in-memory working set rather than replacing it:
``EpisodeStore`` keeps its fast in-RAM dict for reads and similarity search, and
every write-through lands here so it persists to
``${AIOPS_DATA_DIR}/episodes.db`` (the same EBS-backed data dir as
``src/auth/store.py`` and ``src/persistence/store.py``). On startup
``EpisodeStore`` calls :meth:`load_all` to rehydrate the working set.

Neo4j remains the default backend for the full/GPU tier; this module is never
imported on that path.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.persistence.store import data_dir

if TYPE_CHECKING:  # avoid a circular import at runtime (episode_store imports us lazily)
    from src.memory.episode_store import Episode

logger = logging.getLogger(__name__)


class EmbeddedEpisodeStore:
    """Durable episode storage backed by a single SQLite file.

    All methods are defensive: a storage failure is logged and swallowed rather
    than raised, so a corrupt or read-only data dir degrades to the in-memory
    working set instead of crashing a request or the app lifespan.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = Path(db_path) if db_path else (data_dir() / "episodes.db")
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def init_db(self) -> None:
        """Create the episodes table if it does not exist (idempotent)."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY,
                    signature TEXT,
                    service TEXT,
                    category TEXT,
                    detected_at TEXT,
                    data TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_episodes_signature ON episodes(signature)"
            )

    def upsert(self, episode: "Episode") -> None:
        """Insert or replace one episode (write-through from EpisodeStore)."""
        try:
            # ``Episode.to_dict`` omits the embedding; persist it explicitly so
            # ``from_dict`` can restore the 384-dim vector on reload.
            payload = episode.to_dict()
            payload["embedding"] = episode.embedding
            service = (episode.affected_services or [None])[0]
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    """
                    INSERT INTO episodes
                        (episode_id, signature, service, category, detected_at, data)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(episode_id) DO UPDATE SET
                        signature=excluded.signature,
                        service=excluded.service,
                        category=excluded.category,
                        detected_at=excluded.detected_at,
                        data=excluded.data
                    """,
                    (
                        episode.episode_id,
                        episode.generate_signature(),
                        service,
                        episode.category,
                        episode.detected_at.isoformat() if episode.detected_at else None,
                        json.dumps(payload),
                    ),
                )
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(
                "EmbeddedEpisodeStore.upsert failed for %s: %s",
                getattr(episode, "episode_id", "?"),
                e,
            )

    def delete(self, episode_id: str) -> None:
        try:
            with closing(self._connect()) as conn, conn:
                conn.execute("DELETE FROM episodes WHERE episode_id=?", (episode_id,))
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("EmbeddedEpisodeStore.delete failed for %s: %s", episode_id, e)

    def load_all(self) -> list["Episode"]:
        """Return every persisted episode (called once on EpisodeStore init)."""
        from src.memory.episode_store import Episode

        episodes: list[Episode] = []
        try:
            with closing(self._connect()) as conn:
                rows = conn.execute("SELECT data FROM episodes").fetchall()
            for row in rows:
                try:
                    episodes.append(Episode.from_dict(json.loads(row["data"])))
                except Exception as e:
                    logger.warning("Skipping unreadable episode row: %s", e)
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("EmbeddedEpisodeStore.load_all failed: %s", e)
        return episodes

    def count(self) -> int:
        try:
            with closing(self._connect()) as conn:
                return int(conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0])
        except Exception:  # pragma: no cover - defensive
            return 0


__all__ = ["EmbeddedEpisodeStore"]
