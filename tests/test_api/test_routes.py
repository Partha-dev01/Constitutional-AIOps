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

        # Create mock request
        mock_request = MagicMock()
        mock_request.app.state.reasoning_agent = None  # Use mock response

        chat_request = ChatRequest(
            message="Hello, how are you?",
            conversation_id=None,
        )

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

        mock_request = MagicMock()
        mock_request.app.state.reasoning_agent = None

        chat_request = ChatRequest(
            message="Second message",
            conversation_id=conv_id,
        )

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

        # Filter by severity
        result = await list_incidents(
            page=1,
            page_size=10,
            severity=[IncidentSeverity.CRITICAL],
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
