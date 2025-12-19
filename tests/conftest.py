"""
Constitutional AIOps - Test Configuration

Pytest fixtures and configuration for the test suite.
"""

import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio

# Set test environment
os.environ["TESTING"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def mock_model_router():
    """Create a mock model router for testing."""
    from unittest.mock import AsyncMock, MagicMock

    router = MagicMock()
    router.fast_completion = AsyncMock(return_value={
        "choices": [{
            "message": {
                "content": '{"anomaly_detected": false, "confidence": 0.9}'
            }
        }]
    })
    router.reasoning_completion = AsyncMock(return_value={
        "choices": [{
            "message": {
                "content": '{"root_cause": "test", "confidence": 0.85}'
            }
        }]
    })
    router.health_check = AsyncMock(return_value={
        "fast_agent": True,
        "reasoning_agent": True
    })
    router.close = AsyncMock()

    yield router


@pytest_asyncio.fixture
async def mock_neo4j_client():
    """Create a mock Neo4j client for testing."""
    from unittest.mock import AsyncMock, MagicMock

    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.close = AsyncMock()
    client.health_check = AsyncMock(return_value=True)
    client.create_incident = AsyncMock(return_value="INC-2025-001")
    client.find_similar_incidents = AsyncMock(return_value=[])
    client.get_service_dependencies = AsyncMock(return_value=[])

    yield client


@pytest.fixture
def sample_log_telemetry() -> dict:
    """Sample log telemetry for testing."""
    return {
        "telemetry_type": "log",
        "content": """
2025-12-14T10:23:45Z ERROR [api-gateway] Connection refused to database:5432
2025-12-14T10:23:46Z ERROR [api-gateway] Connection refused to database:5432
2025-12-14T10:23:47Z WARN [api-gateway] Retry attempt 3/5
""",
        "context": "Production environment"
    }


@pytest.fixture
def sample_metric_telemetry() -> dict:
    """Sample metric telemetry for testing."""
    return {
        "telemetry_type": "metric",
        "content": """
cpu_usage: 85%
memory_usage: 72%
request_rate: 1500/s
error_rate: 2.5%
p99_latency: 450ms
""",
        "context": "Peak traffic period"
    }


@pytest.fixture
def sample_incident_data() -> dict:
    """Sample incident data for RCA testing."""
    return {
        "incident_id": "INC-2025-1214-001",
        "title": "API Gateway 503 Errors",
        "severity": "critical",
        "start_time": "2025-12-14T10:20:00Z",
        "affected_services": ["api-gateway", "user-service"],
        "telemetry": {
            "error_rate": 15.5,
            "latency_p99": 5200,
            "db_connections": 495
        }
    }


@pytest.fixture
def sample_incident_create() -> dict:
    """Sample incident create request."""
    return {
        "title": "Test Incident for Unit Tests",
        "description": "This is a test incident created during unit testing",
        "severity": "high",
        "category": "performance",
        "affected_services": [
            {"name": "api-gateway", "namespace": "production"},
            {"name": "user-service", "namespace": "production"},
        ],
        "tags": ["test", "unit-test"],
        "source": "manual",
        "auto_analyze": False,
    }


@pytest.fixture
def sample_action_create() -> dict:
    """Sample action create request."""
    return {
        "action_type": "restart_service",
        "description": "Restart the payment service to clear memory leak",
        "target_service": "payment-service",
        "target_instance": "payment-service-abc123",
        "parameters": {"graceful": True, "timeout": 30},
        "confidence": 0.88,
        "evidence": {
            "memory_usage": 0.95,
            "restart_history": "No restarts in 24h"
        },
    }


@pytest.fixture
def constitutional_context() -> dict:
    """Sample constitutional context for validation testing."""
    return {
        "active_incident": True,
        "resource_usage": 75,
        "telemetry_evidence": True,
        "audit_enabled": True,
        "action_scope": "single",
        "confidence": 0.85
    }


@pytest.fixture
def sample_episode():
    """Create sample episode for testing."""
    from src.memory.episode_store import Episode

    return Episode(
        episode_id="ep-test-001",
        incident_id="INC-2025-001",
        title="Database Connection Pool Exhaustion",
        description="Connection pool exhausted causing 503 errors",
        severity="critical",
        category="performance",
        detected_at=datetime.utcnow(),
        root_cause="Database connection pool misconfiguration",
        causal_chain=[
            "Traffic spike",
            "Connection pool exhausted",
            "503 errors to users",
        ],
        confidence=0.87,
        successful_actions=["Increased connection pool size"],
        affected_services=["api-gateway", "database"],
        outcome="resolved",
    )


# Markers for slow tests
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "gpu: marks tests that require GPU"
    )
