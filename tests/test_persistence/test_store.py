"""
Tests for src/persistence/store.py — durable SQLite store for conversations,
incidents, pending remediation actions and the incident counter.

Each test points AIOPS_DATA_DIR at a fresh tmp dir (same isolation pattern as
tests/test_auth/test_store.py) so state.db is created clean per test.
"""

import sqlite3
import time
from datetime import datetime

import pytest

from src.api.schemas.chat import ChatMessage, ChatRole, ConversationHistory
from src.api.schemas.incident import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    ServiceInfo,
)
from src.persistence import store


@pytest.fixture
def tmp_store(tmp_path, monkeypatch):
    """Point the persistence store at a fresh temp data dir for each test."""
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    store.init_db()
    yield tmp_path


def _make_conversation(conv_id: str = "conv-abc123") -> ConversationHistory:
    """A conversation with a user turn + an assistant turn carrying metadata."""
    now = datetime.utcnow()
    return ConversationHistory(
        conversation_id=conv_id,
        created_at=now,
        updated_at=now,
        owner="alice",
        context={"service": "payment-service"},
        messages=[
            ChatMessage(role=ChatRole.USER, content="Why is payment-service 503ing?"),
            ChatMessage(
                role=ChatRole.ASSISTANT,
                content="Connection pool exhaustion.",
                metadata={
                    "confidence": 0.85,
                    "suggested_actions": ["Scale up payment-service"],
                    "related_incidents": ["INC-2026-0001"],
                    "proposed_action": {"id": "act-1", "tool_name": "restart_service"},
                    "metadata": {"tool_steps": [{"tool": "find_similar"}]},
                },
            ),
        ],
    )


def _make_incident(inc_id: str = "INC-2026-0001") -> Incident:
    now = datetime.utcnow()
    return Incident(
        id=inc_id,
        title="High latency on payment-service",
        description="Slow checkout",
        severity=IncidentSeverity.HIGH,
        affected_services=[ServiceInfo(name="payment-service", namespace="production")],
        source="manual",
        status=IncidentStatus.DETECTING,
        created_at=now,
        updated_at=now,
        detected_at=now,
        tags=["checkout"],
    )


class TestConversationRoundTrip:
    def test_round_trip_preserves_per_turn_metadata(self, tmp_store):
        conv = _make_conversation()
        store.save_conversation(conv)

        # Fresh empty dict + load (simulates a cold start).
        loaded = store.load_all_conversations()
        assert set(loaded) == {conv.conversation_id}

        reloaded = loaded[conv.conversation_id]
        assert reloaded.owner == "alice"
        assert reloaded.context == {"service": "payment-service"}
        assert len(reloaded.messages) == 2

        user_turn, assistant_turn = reloaded.messages
        assert user_turn.role == ChatRole.USER
        assert user_turn.metadata is None

        # The per-turn assistant metadata must survive verbatim so a reloaded
        # conversation can replay its reasoning timeline + insight cards.
        assert assistant_turn.role == ChatRole.ASSISTANT
        assert assistant_turn.metadata["confidence"] == 0.85
        assert assistant_turn.metadata["suggested_actions"] == ["Scale up payment-service"]
        assert assistant_turn.metadata["related_incidents"] == ["INC-2026-0001"]
        assert assistant_turn.metadata["proposed_action"]["tool_name"] == "restart_service"
        assert assistant_turn.metadata["metadata"]["tool_steps"] == [{"tool": "find_similar"}]

    def test_save_is_upsert(self, tmp_store):
        conv = _make_conversation()
        store.save_conversation(conv)
        conv.messages.append(ChatMessage(role=ChatRole.USER, content="thanks"))
        store.save_conversation(conv)

        loaded = store.load_all_conversations()
        assert len(loaded) == 1
        assert len(loaded[conv.conversation_id].messages) == 3

    def test_delete_conversation(self, tmp_store):
        conv = _make_conversation()
        store.save_conversation(conv)
        store.delete_conversation(conv.conversation_id)
        assert store.load_all_conversations() == {}
        # Deleting an absent id is a no-op (no error).
        store.delete_conversation("nope")


class TestIncidentPersistence:
    def test_persist_and_reload_after_status_change(self, tmp_store):
        inc = _make_incident()
        store.save_incident(inc)

        # Mutate status + resolved_at and re-persist (write-through).
        inc.status = IncidentStatus.RESOLVED
        inc.resolved_at = datetime.utcnow()
        inc.updated_at = datetime.utcnow()
        store.save_incident(inc)

        loaded = store.load_all_incidents()
        assert set(loaded) == {inc.id}
        reloaded = loaded[inc.id]
        # The mutated status must be reflected (no stale first write).
        assert reloaded.status == IncidentStatus.RESOLVED
        assert reloaded.resolved_at is not None
        assert reloaded.affected_services[0].name == "payment-service"

    def test_delete_incident(self, tmp_store):
        inc = _make_incident()
        store.save_incident(inc)
        store.delete_incident(inc.id)
        assert store.load_all_incidents() == {}


class TestIncidentCounter:
    def test_counter_survives_via_counters_table(self, tmp_store):
        assert store.get_counter("incident", 0) == 0
        store.set_counter("incident", 7)
        # A brand-new read (no in-memory state) returns the persisted value.
        assert store.get_counter("incident", 0) == 7

    def test_counter_default_when_absent(self, tmp_store):
        assert store.get_counter("does-not-exist", 42) == 42


class TestPendingActions:
    def test_persist_and_delete(self, tmp_store):
        entry = {
            "tool_name": "restart_service",
            "parameters": {"service_name": "nextcloud", "reason": "memory leak"},
            "owner": "alice",
            "conversation_id": "conv-abc123",
            "created_at": time.time(),
            "proposed_action": {"id": "act-xyz", "status": "proposed"},
        }
        store.save_pending_action("act-xyz", entry)

        loaded = store.load_all_pending_actions()
        assert set(loaded) == {"act-xyz"}
        assert loaded["act-xyz"]["tool_name"] == "restart_service"
        assert loaded["act-xyz"]["owner"] == "alice"
        assert loaded["act-xyz"]["proposed_action"]["status"] == "proposed"

        store.delete_pending_action("act-xyz")
        assert store.load_all_pending_actions() == {}


class TestCorruptRowTolerance:
    def test_corrupt_conversation_row_is_skipped(self, tmp_store):
        good = _make_conversation("conv-good")
        store.save_conversation(good)

        # Inject a deliberately malformed row directly into the DB.
        db = str(store._db_path())
        with sqlite3.connect(db) as conn:
            conn.execute(
                "INSERT INTO conversations (id, owner, created_at, updated_at, data_json)"
                " VALUES (?, ?, ?, ?, ?)",
                ("conv-bad", "alice", "x", "x", "{ this is not valid json"),
            )

        loaded = store.load_all_conversations()
        # Bad row skipped, good row still loads.
        assert set(loaded) == {"conv-good"}

    def test_corrupt_incident_row_is_skipped(self, tmp_store):
        good = _make_incident("INC-2026-0009")
        store.save_incident(good)

        db = str(store._db_path())
        with sqlite3.connect(db) as conn:
            conn.execute(
                "INSERT INTO incidents (id, created_at, updated_at, data_json)"
                " VALUES (?, ?, ?, ?)",
                ("INC-BAD", "x", "x", '{"id": "INC-BAD"}'),  # missing required fields
            )

        loaded = store.load_all_incidents()
        assert set(loaded) == {"INC-2026-0009"}

    def test_corrupt_pending_action_row_is_skipped(self, tmp_store):
        store.save_pending_action("act-good", {"tool_name": "x", "created_at": 1.0})

        db = str(store._db_path())
        with sqlite3.connect(db) as conn:
            conn.execute(
                "INSERT INTO pending_actions (id, created_at, data_json)"
                " VALUES (?, ?, ?)",
                ("act-bad", "1.0", "not json at all"),
            )

        loaded = store.load_all_pending_actions()
        assert set(loaded) == {"act-good"}


class TestRouteLevelRestart:
    """Simulated restart at the route module level: write-through via the route
    helpers, wipe the in-memory dicts, then re-hydrate exactly as main.py's
    lifespan does — proving the startup-load path restores state + counter."""

    def test_simulated_restart_rehydrates_route_dicts(self, tmp_store):
        from src.api.routes import chat as chat_routes
        from src.api.routes import incidents as incident_routes

        # Snapshot + reset module state so the test is hermetic.
        prev_convs = dict(chat_routes._conversations)
        prev_pending = dict(chat_routes._pending_actions)
        prev_incidents = dict(incident_routes._incidents)
        prev_counter = incident_routes._incident_counter
        chat_routes._conversations.clear()
        chat_routes._pending_actions.clear()
        incident_routes._incidents.clear()
        try:
            # --- write-through (as the routes do on mutation) ---
            conv = _make_conversation("conv-restart")
            chat_routes._conversations[conv.conversation_id] = conv
            store.save_conversation(conv)

            inc_id = incident_routes._generate_incident_id()  # advances + persists counter
            inc = _make_incident(inc_id)
            incident_routes._incidents[inc_id] = inc
            store.save_incident(inc)

            pending = {
                "tool_name": "restart_service",
                "parameters": {"service_name": "nextcloud"},
                "owner": "alice",
                "conversation_id": conv.conversation_id,
                "created_at": time.time(),
                "proposed_action": {"id": "act-r", "status": "proposed"},
            }
            chat_routes._pending_actions["act-r"] = pending
            store.save_pending_action("act-r", pending)

            counter_after_create = incident_routes._incident_counter
            assert counter_after_create >= 1

            # --- simulate the restart: in-memory state evaporates ---
            chat_routes._conversations.clear()
            chat_routes._pending_actions.clear()
            incident_routes._incidents.clear()
            incident_routes._incident_counter = 0

            # --- startup-load (mirrors src/main.py lifespan) ---
            chat_routes._conversations.update(store.load_all_conversations())
            chat_routes._pending_actions.update(store.load_all_pending_actions())
            incident_routes._incidents.update(store.load_all_incidents())
            incident_routes._incident_counter = store.get_counter(
                incident_routes._INCIDENT_COUNTER_NAME, 0
            )

            # Conversation (with per-turn metadata) restored.
            assert "conv-restart" in chat_routes._conversations
            restored = chat_routes._conversations["conv-restart"]
            assert restored.messages[1].metadata["confidence"] == 0.85

            # Incident restored.
            assert inc_id in incident_routes._incidents

            # Pending action restored.
            assert "act-r" in chat_routes._pending_actions

            # Counter survived: it's at least the value we created, and the next
            # generated id strictly advances past it (no collision with the
            # pre-restart incident).
            assert incident_routes._incident_counter == counter_after_create
            next_id = incident_routes._generate_incident_id()
            assert next_id != inc_id
            assert incident_routes._incident_counter == counter_after_create + 1
        finally:
            # Restore original module state so other tests are unaffected.
            chat_routes._conversations.clear()
            chat_routes._conversations.update(prev_convs)
            chat_routes._pending_actions.clear()
            chat_routes._pending_actions.update(prev_pending)
            incident_routes._incidents.clear()
            incident_routes._incidents.update(prev_incidents)
            incident_routes._incident_counter = prev_counter
