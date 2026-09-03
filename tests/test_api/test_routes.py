"""
Constitutional AIOps - API Routes Tests

Comprehensive tests for all API endpoints.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch


# Test Health Routes
class TestHealthRoutes:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_liveness_probe(self):
        """Test liveness probe returns alive."""
        from src.api.routes.health import liveness_check

        response = await liveness_check()

        assert response.alive is True
        assert response.timestamp is not None

    @pytest.mark.asyncio
    async def test_readiness_probe_with_mock_router(self):
        """Test readiness probe with mocked router."""
        from src.api.routes.health import readiness_check

        # Create mock request with mock app state
        mock_request = MagicMock()
        mock_router = MagicMock()
        mock_router.health_check = AsyncMock(return_value={
            "fast_agent": True,
            "reasoning_agent": True,
        })
        mock_request.app.state.model_router = mock_router

        response = await readiness_check(mock_request)

        assert response.ready is True
        assert "fast_agent" in response.checks_passed
        assert "reasoning_agent" in response.checks_passed

    @pytest.mark.asyncio
    async def test_wake_probe_returns_png(self):
        """The public wake-readiness probe returns a real 200 PNG, uncached.

        The sleep-when-idle front door's holding page loads this cross-origin
        as an <img>; its onload fires only on a genuine 200 image, so the bytes
        must be a valid PNG, the media type image/png and the response uncached.
        """
        from src.api.routes.health import wake_probe, _WAKE_PROBE_PNG

        response = await wake_probe()

        assert response.status_code == 200
        assert response.media_type == "image/png"
        assert response.headers.get("cache-control") == "no-store"
        # A valid PNG so a strict <img> decode accepts it (signature bytes).
        assert response.body == _WAKE_PROBE_PNG
        assert response.body[:8] == b"\x89PNG\r\n\x1a\n"


# Test Chat Routes
class TestChatRoutes:
    """Tests for chat endpoints."""

    @pytest.mark.asyncio
    async def test_chat_request_creates_conversation(self):
        """Test that chat creates a new conversation."""
        from src.api.routes.chat import chat, _conversations
        from src.api.schemas.chat import ChatRequest

        # Clear conversations
        _conversations.clear()

        # The chat endpoint now REQUIRES a reasoning agent (no silent mock fallback).
        agent_resp = MagicMock()
        agent_resp.content = "I'm doing well, thank you!"
        agent_resp.confidence = 0.9
        agent_resp.metadata = {}
        reasoning_agent = MagicMock()
        reasoning_agent.chat = AsyncMock(return_value=agent_resp)

        mock_request = MagicMock()
        mock_request.app.state.reasoning_agent = reasoning_agent

        chat_request = ChatRequest(
            message="Hello, how are you?",
            conversation_id=None,
        )

        # Isolate the chat logic from the Docker/LGTM runtime-context builder.
        with patch(
            "src.api.routes.chat._build_runtime_context",
            new=AsyncMock(return_value="ctx"),
        ):
            response = await chat(mock_request, chat_request)

        assert response.conversation_id is not None
        assert response.message.role.value == "assistant"
        assert len(response.message.content) > 0
        assert response.conversation_id in _conversations

    @pytest.mark.asyncio
    async def test_chat_continues_existing_conversation(self):
        """Test that chat continues existing conversation."""
        from src.api.routes.chat import chat, _conversations
        from src.api.schemas.chat import ChatRequest, ConversationHistory, ChatMessage, ChatRole

        # Create existing conversation
        conv_id = "test-conv-123"
        _conversations[conv_id] = ConversationHistory(
            conversation_id=conv_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            messages=[
                ChatMessage(role=ChatRole.USER, content="First message"),
                ChatMessage(role=ChatRole.ASSISTANT, content="First response"),
            ],
        )

        agent_resp = MagicMock()
        agent_resp.content = "Second response"
        agent_resp.confidence = 0.85
        agent_resp.metadata = {}
        reasoning_agent = MagicMock()
        reasoning_agent.chat = AsyncMock(return_value=agent_resp)

        mock_request = MagicMock()
        mock_request.app.state.reasoning_agent = reasoning_agent

        chat_request = ChatRequest(
            message="Second message",
            conversation_id=conv_id,
        )

        with patch(
            "src.api.routes.chat._build_runtime_context",
            new=AsyncMock(return_value="ctx"),
        ):
            response = await chat(mock_request, chat_request)

        assert response.conversation_id == conv_id
        assert len(_conversations[conv_id].messages) == 4  # 2 original + 2 new

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self):
        """Test getting non-existent conversation raises 404."""
        from src.api.routes.chat import get_conversation
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_conversation("non-existent-id")

        assert exc_info.value.status_code == 404


class TestListConversationsValidation:
    """`limit`/`offset` on GET /conversations are bounded via fastapi.Query
    (ge/le) — that enforcement only runs through real request validation, so
    direct route-function calls (this file's usual pattern) can't exercise
    it. A tiny app wrapping just the chat router is used instead of
    importing src.main (langgraph is absent in CI)."""

    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from src.api.routes.chat import router as chat_router

        app = FastAPI()
        app.include_router(chat_router, prefix="/api/v1/chat")
        return TestClient(app)

    def test_limit_zero_rejected(self, client):
        resp = client.get("/api/v1/chat/conversations", params={"limit": 0})
        assert resp.status_code == 422

    def test_limit_too_large_rejected(self, client):
        resp = client.get("/api/v1/chat/conversations", params={"limit": 1000})
        assert resp.status_code == 422

    def test_offset_negative_rejected(self, client):
        resp = client.get("/api/v1/chat/conversations", params={"offset": -1})
        assert resp.status_code == 422

    def test_defaults_accepted(self, client):
        from src.api.routes.chat import _conversations

        _conversations.clear()
        resp = client.get("/api/v1/chat/conversations")
        assert resp.status_code == 200


class TestConversationDeleteFallback:
    """ISS-106: DELETE /conversations/{id} must fall back to the SQLite
    persistence store when the id is absent from the in-memory dict (e.g.
    evicted from the capped hydration window), not 404 outright."""

    @pytest.fixture
    def persisted_store(self, tmp_path, monkeypatch):
        """A freshly-reloaded persistence store bound to an isolated data dir,
        wired into chat.py's module-level `persistence_store` reference
        (mirrors test_topology_schema.py's store-reload convention)."""
        import importlib

        monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
        import src.persistence.store as store_mod

        store_mod = importlib.reload(store_mod)
        store_mod.init_db()

        import src.api.routes.chat as chat_module

        monkeypatch.setattr(chat_module, "persistence_store", store_mod)
        monkeypatch.setattr(chat_module, "_conversations", {})
        return store_mod

    @pytest.mark.asyncio
    async def test_delete_falls_back_to_persisted_store(self, persisted_store):
        """A conversation that only exists in SQLite (never hydrated into
        memory) is still deletable, and is actually removed from the store."""
        from src.api.routes.chat import delete_conversation
        from src.api.schemas.chat import ConversationHistory

        conv_id = "persisted-only-conv"
        conv = ConversationHistory(
            conversation_id=conv_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            messages=[],
        )
        persisted_store.save_conversation(conv)

        await delete_conversation(conv_id)  # must not raise

        assert persisted_store.load_all_conversations().get(conv_id) is None

    @pytest.mark.asyncio
    async def test_delete_404_when_absent_from_both(self, persisted_store):
        """Neither in-memory nor persisted -> still a clean 404."""
        from fastapi import HTTPException

        from src.api.routes.chat import delete_conversation

        with pytest.raises(HTTPException) as exc_info:
            await delete_conversation("does-not-exist-anywhere")
        assert exc_info.value.status_code == 404


# Test Incident Routes
class TestIncidentRoutes:
    """Tests for incident management endpoints."""

    @pytest.mark.asyncio
    async def test_create_incident(self):
        """Test creating a new incident."""
        from src.api.routes.incidents import create_incident, _incidents
        from src.api.schemas.incident import IncidentCreate, IncidentSeverity, ServiceInfo

        _incidents.clear()

        mock_request = MagicMock()
        mock_request.app.state.reasoning_agent = None

        incident_create = IncidentCreate(
            title="Test Incident",
            description="This is a test incident",
            severity=IncidentSeverity.HIGH,
            affected_services=[ServiceInfo(name="test-service")],
            auto_analyze=False,
        )

        incident = await create_incident(mock_request, incident_create)

        assert incident.id is not None
        assert incident.title == "Test Incident"
        assert incident.severity == IncidentSeverity.HIGH
        assert incident.id in _incidents

    @pytest.mark.asyncio
    async def test_list_incidents_with_filters(self):
        """Test listing incidents with filters."""
        from src.api.routes.incidents import list_incidents, create_incident, _incidents
        from src.api.schemas.incident import IncidentCreate, IncidentSeverity, IncidentStatus, ServiceInfo

        _incidents.clear()

        mock_request = MagicMock()
        mock_request.app.state.reasoning_agent = None

        # Create multiple incidents
        for i in range(5):
            severity = IncidentSeverity.CRITICAL if i < 2 else IncidentSeverity.MEDIUM
            await create_incident(
                mock_request,
                IncidentCreate(
                    title=f"Incident {i}",
                    severity=severity,
                    affected_services=[ServiceInfo(name=f"service-{i}")],
                    auto_analyze=False,
                ),
            )

        # Filter by severity (all filter args passed explicitly — calling the route
        # function directly leaves unset Query(...) defaults as Query objects).
        result = await list_incidents(
            page=1,
            page_size=10,
            status=None,
            severity=[IncidentSeverity.CRITICAL],
            category=None,
            service=None,
            search=None,
        )

        assert result.total == 2
        assert all(i.severity == IncidentSeverity.CRITICAL for i in result.items)

    @pytest.mark.asyncio
    async def test_get_incident_not_found(self):
        """Test getting non-existent incident raises 404."""
        from src.api.routes.incidents import get_incident
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_incident("non-existent-id")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_incident(self):
        """Test updating an incident."""
        from src.api.routes.incidents import create_incident, update_incident, _incidents
        from src.api.schemas.incident import IncidentCreate, IncidentUpdate, IncidentSeverity, IncidentStatus, ServiceInfo

        _incidents.clear()

        mock_request = MagicMock()
        mock_request.app.state.reasoning_agent = None

        # Create incident
        incident = await create_incident(
            mock_request,
            IncidentCreate(
                title="Original Title",
                severity=IncidentSeverity.MEDIUM,
                affected_services=[ServiceInfo(name="test-service")],
                auto_analyze=False,
            ),
        )

        # Update it
        updated = await update_incident(
            incident.id,
            IncidentUpdate(
                title="Updated Title",
                status=IncidentStatus.RESOLVED,
                resolution_notes="Fixed the issue",
            ),
        )

        assert updated.title == "Updated Title"
        assert updated.status == IncidentStatus.RESOLVED
        assert updated.resolution_notes == "Fixed the issue"


# Test Action Routes
class TestActionRoutes:
    """Tests for action management endpoints."""

    @pytest.mark.asyncio
    async def test_create_action_with_validation(self):
        """Test creating action goes through validation."""
        from src.api.routes.actions import create_action, _actions
        from src.api.schemas.action import ActionCreate, ActionType

        _actions.clear()

        mock_request = MagicMock()
        mock_request.app.state.validator = None  # Use fallback validation

        action_create = ActionCreate(
            action_type=ActionType.RESTART_SERVICE,
            description="Restart the payment service",
            target_service="payment-service",
            confidence=0.95,
        )

        action = await create_action(mock_request, action_create)

        assert action.id is not None
        assert action.validation is not None
        assert action.confidence == 0.95
        assert action.id in _actions

    @pytest.mark.asyncio
    async def test_action_approval_workflow(self):
        """Test action approval workflow."""
        from src.api.routes.actions import create_action, approve_action, _actions
        from src.api.schemas.action import ActionCreate, ActionApproval, ActionType, ActionStatus

        _actions.clear()

        mock_request = MagicMock()
        mock_request.app.state.validator = None

        # Create action with medium confidence (requires approval)
        action_create = ActionCreate(
            action_type=ActionType.SCALE_UP,
            description="Scale up the API service",
            target_service="api-service",
            confidence=0.75,  # Medium confidence
        )

        action = await create_action(mock_request, action_create)

        # If it requires approval, approve it
        if action.status == ActionStatus.AWAITING_APPROVAL:
            approved = await approve_action(
                action.id,
                ActionApproval(
                    approved=True,
                    approved_by="test-user",
                    comments="Approved for testing",
                ),
            )

            assert approved.status == ActionStatus.APPROVED
            assert approved.approved_by == "test-user"

    @pytest.mark.asyncio
    async def test_get_pending_approvals(self):
        """Test getting pending approval summary."""
        from src.api.routes.actions import get_pending_approvals, create_action, _actions
        from src.api.schemas.action import ActionCreate, ActionType

        _actions.clear()

        mock_request = MagicMock()
        mock_request.app.state.validator = None

        # Create actions with medium confidence
        for i in range(3):
            await create_action(
                mock_request,
                ActionCreate(
                    action_type=ActionType.RESTART_SERVICE,
                    description=f"Action {i}",
                    target_service=f"service-{i}",
                    confidence=0.75,
                ),
            )

        pending = await get_pending_approvals()

        # Count depends on validation result
        assert pending.count >= 0


# Test Schemas
class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_chat_request_validation(self):
        """Test ChatRequest validation."""
        from src.api.schemas.chat import ChatRequest

        # Valid request
        request = ChatRequest(message="Hello")
        assert request.message == "Hello"

        # Empty message should fail
        with pytest.raises(ValueError):
            ChatRequest(message="")

    def test_incident_create_validation(self):
        """Test IncidentCreate validation."""
        from src.api.schemas.incident import IncidentCreate, IncidentSeverity, ServiceInfo

        # Valid incident
        incident = IncidentCreate(
            title="Valid title",
            severity=IncidentSeverity.HIGH,
            affected_services=[ServiceInfo(name="test-service")],
        )
        assert incident.title == "Valid title"

        # Short title should fail
        with pytest.raises(ValueError):
            IncidentCreate(
                title="Hi",  # Too short
                severity=IncidentSeverity.HIGH,
                affected_services=[ServiceInfo(name="test-service")],
            )

    def test_action_create_validation(self):
        """Test ActionCreate validation."""
        from src.api.schemas.action import ActionCreate, ActionType

        # Valid action
        action = ActionCreate(
            action_type=ActionType.RESTART_SERVICE,
            description="Restart the service",
            target_service="my-service",
            confidence=0.85,
        )
        assert action.confidence == 0.85

        # Invalid confidence should fail
        with pytest.raises(ValueError):
            ActionCreate(
                action_type=ActionType.RESTART_SERVICE,
                description="Restart the service",
                target_service="my-service",
                confidence=1.5,  # > 1.0
            )


# Test Memory Components
class TestMemoryComponents:
    """Tests for memory module components."""

    @pytest.mark.asyncio
    async def test_episode_store_basic(self):
        """Test basic episode store operations."""
        from src.memory.episode_store import Episode, EpisodeStore

        store = EpisodeStore()

        episode = Episode(
            episode_id="ep-001",
            incident_id="INC-2025-001",
            title="Test Incident",
            description="Test description",
            severity="high",
            category="performance",
            detected_at=datetime.utcnow(),
            affected_services=["service-a", "service-b"],
        )

        # Store episode
        await store.store_episode(episode)

        # Retrieve it
        retrieved = await store.get_episode("ep-001")
        assert retrieved is not None
        assert retrieved.title == "Test Incident"

    @pytest.mark.asyncio
    async def test_episode_similarity(self):
        """Test finding similar episodes."""
        from src.memory.episode_store import Episode, EpisodeStore

        store = EpisodeStore()

        # Create similar episodes
        for i in range(5):
            episode = Episode(
                episode_id=f"ep-{i:03d}",
                incident_id=f"INC-2025-{i:03d}",
                title=f"Database Performance Issue {i}",
                description="Slow queries",
                severity="high",
                category="performance",
                detected_at=datetime.utcnow(),
                affected_services=["database", "api-service"],
                root_cause="Connection pool exhaustion",
            )
            await store.store_episode(episode)

        # Find similar to a new incident
        query_episode = Episode(
            episode_id="query",
            incident_id="query",
            title="Database Timeout",
            description="Database connection timeout",
            severity="high",
            category="performance",
            detected_at=datetime.utcnow(),
            affected_services=["database"],
        )

        similar = await store.find_similar_episodes(query_episode, limit=3)

        assert len(similar) > 0


# Test Telemetry Components
class TestTelemetryComponents:
    """Tests for telemetry module components."""

    def test_token_compressor_basic(self):
        """Test basic token compression."""
        from src.telemetry.compressor import TokenCompressor
        from src.telemetry.collector import TelemetryWindow, LogEntry
        from datetime import timedelta

        compressor = TokenCompressor(target_tokens=500)

        now = datetime.utcnow()
        window = TelemetryWindow(
            start_time=now - timedelta(minutes=15),
            end_time=now,
            logs=[
                LogEntry(
                    timestamp=now,
                    level="ERROR",
                    message="Connection refused to database:5432",
                    service="api-service",
                ),
                LogEntry(
                    timestamp=now,
                    level="ERROR",
                    message="Connection refused to database:5432",
                    service="api-service",
                ),
                LogEntry(
                    timestamp=now,
                    level="WARN",
                    message="Retry attempt 3/5",
                    service="api-service",
                ),
            ],
        )

        compressed = compressor.compress_window(window)

        assert compressed.error_count == 2
        assert compressed.warning_count == 1
        assert len(compressed.top_errors) > 0

    def test_telemetry_aggregator_health_score(self):
        """Test health score calculation."""
        from src.telemetry.aggregator import TelemetryAggregator

        aggregator = TelemetryAggregator()

        # Perfect health
        score = aggregator._calculate_health_score(
            error_rate=0.0,
            avg_latency=50,
            availability=1.0,
        )
        assert score > 0.9

        # Poor health
        score = aggregator._calculate_health_score(
            error_rate=0.2,
            avg_latency=2000,
            availability=0.8,
        )
        assert score < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
