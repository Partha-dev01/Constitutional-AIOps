"""
Constitutional AIOps - Constitutional Validator Tests

Tests for the Constitutional AI framework validation logic.
"""

import pytest
from datetime import datetime

from src.constitutional.principles import (
    ALL_PRINCIPLES,
    TIER_1_PRINCIPLES,
    TIER_2_PRINCIPLES,
    TIER_3_PRINCIPLES,
    PrincipleTier,
    get_principle,
)
from src.constitutional.validator import (
    AuthorizationLevel,
    ConstitutionalValidator,
    ValidationResult,
)


class TestPrinciples:
    """Tests for constitutional principles definitions."""
    
    def test_all_principles_count(self):
        """Test that we have all 12 principles (4 per tier)."""
        assert len(ALL_PRINCIPLES) == 12
        assert len(TIER_1_PRINCIPLES) == 4
        assert len(TIER_2_PRINCIPLES) == 4
        assert len(TIER_3_PRINCIPLES) == 4
    
    def test_principle_tiers(self):
        """Test that principles are in correct tiers."""
        for p in TIER_1_PRINCIPLES:
            assert p.tier == PrincipleTier.TIER_1_SAFETY
            assert p.violation_action == "BLOCK_ALWAYS"
        
        for p in TIER_2_PRINCIPLES:
            assert p.tier == PrincipleTier.TIER_2_OPERATIONAL
            assert p.violation_action == "REQUIRE_APPROVAL"
        
        for p in TIER_3_PRINCIPLES:
            assert p.tier == PrincipleTier.TIER_3_LEARNING
            assert p.violation_action == "LOG_WARNING"
    
    def test_get_principle_by_id(self):
        """Test principle lookup by ID."""
        p1_1 = get_principle("P1.1")
        assert p1_1 is not None
        assert p1_1.name == "Data Protection"
        
        p2_1 = get_principle("P2.1")
        assert p2_1 is not None
        assert p2_1.name == "Minimal Intervention"
        
        assert get_principle("INVALID") is None


class TestAuthorizationLevel:
    """Tests for authorization level determination."""
    
    def test_automatic_high_confidence(self):
        """Test that high confidence triggers automatic authorization."""
        validator = ConstitutionalValidator(
            confidence_threshold_auto=0.90,
            confidence_threshold_approval=0.70
        )
        level = validator._get_authorization_level(0.95)
        assert level == AuthorizationLevel.AUTOMATIC
    
    def test_approval_medium_confidence(self):
        """Test that medium confidence requires approval."""
        validator = ConstitutionalValidator()
        level = validator._get_authorization_level(0.80)
        assert level == AuthorizationLevel.APPROVAL_REQUIRED
    
    def test_alert_low_confidence(self):
        """Test that low confidence is alert only."""
        validator = ConstitutionalValidator()
        level = validator._get_authorization_level(0.50)
        assert level == AuthorizationLevel.ALERT_ONLY


class TestConstitutionalValidator:
    """Tests for the ConstitutionalValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ConstitutionalValidator()
    
    def test_tier1_data_protection_violation(self, validator):
        """Test that data deletion is blocked (P1.1)."""
        report = validator.validate(
            action_id="test-001",
            action_description="Delete user data",
            action_type="delete_table",
            confidence=0.99,
            context={}
        )
        
        assert report.tier1_passed is False
        assert report.can_proceed is False
        assert len(report.violations) > 0
        assert any(v.principle.id == "P1.1" for v in report.violations)
    
    def test_tier1_active_incident_violation(self, validator):
        """Test that destructive actions during incidents are blocked (P1.2)."""
        report = validator.validate(
            action_id="test-002",
            action_description="Restart service",
            action_type="restart",
            confidence=0.95,
            context={"active_incident": True}
        )
        
        assert report.tier1_passed is False
        assert report.can_proceed is False
    
    def test_tier1_security_violation(self, validator):
        """Test that security changes are blocked (P1.4)."""
        report = validator.validate(
            action_id="test-003",
            action_description="Update firewall rules",
            action_type="firewall_update",
            confidence=0.95,
            context={}
        )
        
        assert report.tier1_passed is False
        assert any(v.principle.id == "P1.4" for v in report.violations)
    
    def test_tier2_minimal_intervention_warning(self, validator):
        """Test that broad actions trigger approval (P2.1)."""
        report = validator.validate(
            action_id="test-004",
            action_description="Restart all pods",
            action_type="restart_pods",
            confidence=0.85,
            context={"action_scope": "all"}
        )
        
        # Should pass tier 1 but fail tier 2
        assert report.tier1_passed is True
        assert report.tier2_passed is False
        assert report.requires_approval is True
    
    def test_tier2_evidence_required(self, validator):
        """Test that actions without evidence require approval (P2.2)."""
        report = validator.validate(
            action_id="test-005",
            action_description="Scale up service",
            action_type="scale_up",
            confidence=0.85,
            context={"telemetry_evidence": False}
        )
        
        assert report.tier2_passed is False
        assert report.requires_approval is True
    
    def test_safe_action_high_confidence(self, validator):
        """Test that safe actions with high confidence are automatic."""
        report = validator.validate(
            action_id="test-006",
            action_description="Clear cache",
            action_type="clear_cache",
            confidence=0.95,
            context={
                "active_incident": False,
                "telemetry_evidence": True,
                "audit_enabled": True,
                "action_scope": "single"
            }
        )
        
        assert report.tier1_passed is True
        assert report.tier2_passed is True
        assert report.can_proceed is True
        assert report.requires_approval is False
        assert report.authorization_level == AuthorizationLevel.AUTOMATIC
    
    def test_low_confidence_alert_only(self, validator):
        """Test that low confidence actions are alert only."""
        report = validator.validate(
            action_id="test-007",
            action_description="Uncertain action",
            action_type="scale_up",
            confidence=0.50,
            context={
                "telemetry_evidence": True,
                "audit_enabled": True
            }
        )
        
        assert report.authorization_level == AuthorizationLevel.ALERT_ONLY
        assert report.can_proceed is False
    
    def test_validation_report_completeness(self, validator):
        """Test that validation report has all required fields."""
        report = validator.validate(
            action_id="test-008",
            action_description="Test action",
            action_type="test",
            confidence=0.85,
            context={}
        )
        
        assert report.action_id == "test-008"
        assert report.action_description == "Test action"
        assert isinstance(report.timestamp, datetime)
        assert 0 <= report.confidence <= 1
        assert report.authorization_level in AuthorizationLevel
        assert report.overall_result in ValidationResult
        assert isinstance(report.violations, list)
        assert isinstance(report.warnings, list)
        assert isinstance(report.can_proceed, bool)
        assert isinstance(report.requires_approval, bool)
        assert isinstance(report.explanation, str)


class TestValidationScenarios:
    """Integration tests for real-world validation scenarios."""
    
    @pytest.fixture
    def validator(self):
        return ConstitutionalValidator()
    
    def test_scenario_database_restart_during_incident(self, validator):
        """Scenario: Operator wants to restart database during active incident."""
        report = validator.validate(
            action_id="scenario-001",
            action_description="Restart database pod",
            action_type="restart",
            confidence=0.75,
            context={
                "active_incident": True,
                "resource_usage": 85,
                "telemetry_evidence": True
            }
        )
        
        # Should be blocked due to active incident (P1.2)
        assert report.can_proceed is False
        assert "active incident" in report.explanation.lower() or report.tier1_passed is False
    
    def test_scenario_safe_cache_clear(self, validator):
        """Scenario: Routine cache clear with good evidence."""
        report = validator.validate(
            action_id="scenario-002",
            action_description="Clear Redis cache",
            action_type="clear_cache",
            confidence=0.92,
            context={
                "active_incident": False,
                "resource_usage": 45,
                "telemetry_evidence": True,
                "audit_enabled": True,
                "action_scope": "single"
            }
        )
        
        # Should proceed automatically
        assert report.can_proceed is True
        assert report.requires_approval is False
    
    def test_scenario_uncertain_scaling(self, validator):
        """Scenario: Scaling decision with low confidence."""
        report = validator.validate(
            action_id="scenario-003",
            action_description="Scale up API pods",
            action_type="scale_up",
            confidence=0.65,
            context={
                "active_incident": False,
                "telemetry_evidence": True,
                "audit_enabled": True
            }
        )
        
        # Should be alert only due to low confidence
        assert report.authorization_level == AuthorizationLevel.ALERT_ONLY
