"""
Constitutional AIOps - Agent Tests

Tests for the dual-agent architecture (Fast Annotator + Reasoning Agent).
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.base_agent import AgentResponse, AgentRole, ConfidenceLevel
from src.agents.fast_annotator import FastAnnotator
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.model_router import ModelRouter


class TestModelRouter:
    """Tests for the ModelRouter class."""
    
    def test_initialization(self):
        """Test ModelRouter initializes with correct URLs."""
        router = ModelRouter(
            fast_agent_url="http://localhost:8081/v1",
            reasoning_agent_url="http://localhost:8082/v1"
        )
        assert router.fast_agent_url == "http://localhost:8081/v1"
        assert router.reasoning_agent_url == "http://localhost:8082/v1"
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_model_router):
        """Test health check returns status for both agents."""
        health = await mock_model_router.health_check()
        assert "fast_agent" in health
        assert "reasoning_agent" in health


class TestFastAnnotator:
    """Tests for the Fast Annotator agent."""
    
    @pytest.mark.asyncio
    async def test_process_normal_telemetry(self, mock_model_router, sample_metric_telemetry):
        """Test processing normal metric telemetry."""
        mock_model_router.fast_completion = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "anomaly_detected": False,
                        "severity": "info",
                        "category": "performance",
                        "confidence": 0.92,
                        "summary": "Normal operation",
                        "needs_reasoning": False,
                        "key_indicators": []
                    })
                }
            }]
        })
        
        annotator = FastAnnotator(model_router=mock_model_router)
        response = await annotator.process(sample_metric_telemetry)
        
        assert isinstance(response, AgentResponse)
        assert response.confidence >= 0.9
        assert response.metadata["anomaly_detected"] is False
    
    @pytest.mark.asyncio
    async def test_process_anomaly_telemetry(self, mock_model_router, sample_log_telemetry):
        """Test processing telemetry with anomaly."""
        mock_model_router.fast_completion = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "anomaly_detected": True,
                        "severity": "critical",
                        "category": "error",
                        "confidence": 0.88,
                        "summary": "Database connection failures",
                        "needs_reasoning": True,
                        "key_indicators": ["connection_refused", "retry_failures"]
                    })
                }
            }]
        })
        
        annotator = FastAnnotator(model_router=mock_model_router)
        response = await annotator.process(sample_log_telemetry)
        
        assert response.metadata["anomaly_detected"] is True
        assert response.metadata["needs_reasoning"] is True
        assert response.metadata["severity"] == "critical"
    
    def test_confidence_level_calculation(self):
        """Test confidence level thresholds."""
        annotator = FastAnnotator.__new__(FastAnnotator)
        annotator.role = AgentRole.FAST_ANNOTATOR
        
        assert annotator.calculate_confidence_level(0.95) == ConfidenceLevel.HIGH
        assert annotator.calculate_confidence_level(0.85) == ConfidenceLevel.MEDIUM
        assert annotator.calculate_confidence_level(0.60) == ConfidenceLevel.LOW


class TestReasoningAgent:
    """Tests for the Reasoning Agent."""
    
    @pytest.mark.asyncio
    async def test_analyze_rca(self, mock_model_router, sample_incident_data):
        """Test root cause analysis."""
        mock_model_router.reasoning_completion = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "root_cause": "Database connection pool exhaustion",
                        "causal_chain": ["Slow queries", "Pool exhaustion", "503 errors"],
                        "impact": {
                            "services": ["api-gateway"],
                            "severity": "critical",
                            "users_affected": "5000"
                        },
                        "confidence": 0.85,
                        "reasoning": "Correlation analysis shows...",
                        "remediation_steps": [
                            {"action": "Kill slow queries", "risk": "low"}
                        ],
                        "prevention": "Add connection pool alerts"
                    })
                }
            }]
        })
        
        agent = ReasoningAgent(model_router=mock_model_router)
        response = await agent.analyze_rca(sample_incident_data)
        
        assert isinstance(response, AgentResponse)
        assert "root_cause" in response.metadata
        assert response.confidence > 0.7
    
    @pytest.mark.asyncio
    async def test_chat_mode(self, mock_model_router):
        """Test chat interaction."""
        mock_model_router.reasoning_completion = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": "The payment service is currently healthy with 0.1% error rate."
                }
            }]
        })
        
        agent = ReasoningAgent(model_router=mock_model_router)
        response = await agent.chat("What's the status of payment service?")
        
        assert isinstance(response, AgentResponse)
        assert "payment" in response.content.lower()
    
    @pytest.mark.asyncio
    async def test_create_plan(self, mock_model_router):
        """Test remediation plan creation."""
        mock_model_router.reasoning_completion = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "plan_name": "Connection Pool Recovery",
                        "total_steps": 3,
                        "estimated_duration": "15 minutes",
                        "overall_risk": "low",
                        "rollback_available": True,
                        "steps": [
                            {"order": 1, "action": "Kill slow queries", "risk": "low"}
                        ],
                        "success_criteria": "Error rate < 1%",
                        "rollback_plan": "Restore connections"
                    })
                }
            }]
        })
        
        agent = ReasoningAgent(model_router=mock_model_router)
        response = await agent.create_plan(
            root_cause="Connection pool exhaustion",
            incident_context={"severity": "critical"}
        )
        
        assert "plan_name" in response.metadata


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""
    
    def test_requires_approval_medium_confidence(self):
        """Test that medium confidence requires approval."""
        response = AgentResponse(
            content="Test",
            confidence=0.80,
            confidence_level=ConfidenceLevel.MEDIUM
        )
        assert response.requires_approval is True
        assert response.is_automatic is False
    
    def test_automatic_high_confidence(self):
        """Test that high confidence is automatic."""
        response = AgentResponse(
            content="Test",
            confidence=0.95,
            confidence_level=ConfidenceLevel.HIGH
        )
        assert response.is_automatic is True
        assert response.requires_approval is False
