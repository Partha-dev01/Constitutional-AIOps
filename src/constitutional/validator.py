"""
Constitutional AIOps - Constitutional Validator

Validates all proposed actions against constitutional principles.
Implements the three-tier safety hierarchy and authorization matrix.

Authorization Matrix:
- Confidence >90%: AUTOMATIC (audit only)
- Confidence 70-90%: APPROVAL_REQUIRED (human must approve)
- Confidence <70%: ALERT_ONLY (notify, no action)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from src.config import config
from src.constitutional.principles import (
    ALL_PRINCIPLES,
    PRINCIPLES_BY_ID,
    Principle,
    PrincipleTier,
)

logger = logging.getLogger(__name__)


class AuthorizationLevel(Enum):
    """Authorization levels based on confidence."""
    AUTOMATIC = "automatic"           # >90% - proceed with audit
    APPROVAL_REQUIRED = "approval"    # 70-90% - wait for human
    ALERT_ONLY = "alert"              # <70% - notify only


class ValidationResult(Enum):
    """Result of principle validation."""
    PASSED = "passed"
    VIOLATED = "violated"
    WARNING = "warning"


@dataclass
class PrincipleViolation:
    """Details of a principle violation."""
    principle: Principle
    reason: str
    severity: str  # "critical", "high", "medium", "low"
    context: dict[str, Any]


@dataclass 
class ValidationReport:
    """Complete validation report for an action."""
    action_id: str
    action_description: str
    timestamp: datetime
    confidence: float
    authorization_level: AuthorizationLevel
    overall_result: ValidationResult
    tier1_passed: bool
    tier2_passed: bool
    tier3_passed: bool
    violations: list[PrincipleViolation]
    warnings: list[str]
    can_proceed: bool
    requires_approval: bool
    explanation: str


class ConstitutionalValidator:
    """
    Validates actions against constitutional principles.
    
    All actions must pass Tier 1 (Safety) checks.
    Tier 2 violations require human approval.
    Tier 3 violations are logged as warnings.
    """
    
    def __init__(
        self,
        confidence_threshold_auto: Optional[float] = None,
        confidence_threshold_approval: Optional[float] = None,
    ):
        """
        Initialize the validator.
        
        Args:
            confidence_threshold_auto: Threshold for automatic actions (default: 0.90)
            confidence_threshold_approval: Threshold for approval-required (default: 0.70)
        """
        self.confidence_threshold_auto = (
            confidence_threshold_auto or config.constitutional.confidence_threshold_auto
        )
        self.confidence_threshold_approval = (
            confidence_threshold_approval or config.constitutional.confidence_threshold_approval
        )
        
        logger.info(f"ConstitutionalValidator initialized")
        logger.info(f"  Auto threshold: {self.confidence_threshold_auto}")
        logger.info(f"  Approval threshold: {self.confidence_threshold_approval}")
    
    def validate(
        self,
        action_id: str,
        action_description: str,
        action_type: str,
        confidence: float,
        context: dict[str, Any],
    ) -> ValidationReport:
        """
        Validate a proposed action against all principles.
        
        Args:
            action_id: Unique identifier for the action
            action_description: Human-readable description
            action_type: Type of action (restart, scale, modify, etc.)
            confidence: Agent's confidence in the action (0.0-1.0)
            context: Additional context about the action
            
        Returns:
            ValidationReport with complete validation results
        """
        violations = []
        warnings = []
        
        # Determine authorization level based on confidence
        authorization_level = self._get_authorization_level(confidence)
        
        # Validate against Tier 1 (Safety-Critical)
        tier1_passed = True
        for principle in self._get_tier_principles(PrincipleTier.TIER_1_SAFETY):
            result = self._check_principle(principle, action_type, context)
            if result["violated"]:
                tier1_passed = False
                violations.append(PrincipleViolation(
                    principle=principle,
                    reason=result["reason"],
                    severity="critical",
                    context=context,
                ))
        
        # Validate against Tier 2 (Operational)
        tier2_passed = True
        for principle in self._get_tier_principles(PrincipleTier.TIER_2_OPERATIONAL):
            result = self._check_principle(principle, action_type, context)
            if result["violated"]:
                tier2_passed = False
                violations.append(PrincipleViolation(
                    principle=principle,
                    reason=result["reason"],
                    severity="high",
                    context=context,
                ))
        
        # Validate against Tier 3 (Learning)
        tier3_passed = True
        for principle in self._get_tier_principles(PrincipleTier.TIER_3_LEARNING):
            result = self._check_principle(principle, action_type, context)
            if result["violated"]:
                tier3_passed = False
                warnings.append(f"{principle.id}: {result['reason']}")
        
        # Determine overall result
        if not tier1_passed:
            overall_result = ValidationResult.VIOLATED
            can_proceed = False
            requires_approval = False
            explanation = "Tier 1 (Safety) violation - action BLOCKED"
        elif not tier2_passed:
            overall_result = ValidationResult.WARNING
            can_proceed = True
            requires_approval = True
            explanation = "Tier 2 (Operational) violation - requires human approval"
        elif not tier3_passed:
            overall_result = ValidationResult.WARNING
            can_proceed = True
            requires_approval = False
            explanation = "Tier 3 (Learning) warnings logged"
        else:
            overall_result = ValidationResult.PASSED
            can_proceed = authorization_level != AuthorizationLevel.ALERT_ONLY
            requires_approval = authorization_level == AuthorizationLevel.APPROVAL_REQUIRED
            explanation = f"Validation passed - {authorization_level.value}"
        
        # Override based on authorization level
        if authorization_level == AuthorizationLevel.ALERT_ONLY and can_proceed:
            can_proceed = False
            requires_approval = False
            explanation += " (low confidence - alert only)"
        
        return ValidationReport(
            action_id=action_id,
            action_description=action_description,
            timestamp=datetime.utcnow(),
            confidence=confidence,
            authorization_level=authorization_level,
            overall_result=overall_result,
            tier1_passed=tier1_passed,
            tier2_passed=tier2_passed,
            tier3_passed=tier3_passed,
            violations=violations,
            warnings=warnings,
            can_proceed=can_proceed,
            requires_approval=requires_approval,
            explanation=explanation,
        )
    
    def _get_authorization_level(self, confidence: float) -> AuthorizationLevel:
        """Determine authorization level based on confidence."""
        if confidence >= self.confidence_threshold_auto:
            return AuthorizationLevel.AUTOMATIC
        elif confidence >= self.confidence_threshold_approval:
            return AuthorizationLevel.APPROVAL_REQUIRED
        else:
            return AuthorizationLevel.ALERT_ONLY
    
    def _get_tier_principles(self, tier: PrincipleTier) -> list[Principle]:
        """Get principles for a specific tier."""
        return [p for p in ALL_PRINCIPLES if p.tier == tier]
    
    def _check_principle(
        self,
        principle: Principle,
        action_type: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Check if an action violates a specific principle.
        
        This is a simplified implementation. In production, this would use
        more sophisticated checks, possibly involving the LLM for ambiguous cases.
        """
        violated = False
        reason = ""
        
        # Tier 1 checks
        if principle.id == "P1.1":  # Data Protection
            dangerous_actions = ["delete", "drop", "truncate", "remove"]
            if any(d in action_type.lower() for d in dangerous_actions):
                violated = True
                reason = f"Action '{action_type}' could cause data loss"
        
        elif principle.id == "P1.2":  # Active Incident Safety
            if context.get("active_incident") and action_type in ["restart", "deploy", "scale_down"]:
                violated = True
                reason = "Destructive action during active incident"
        
        elif principle.id == "P1.3":  # Cascade Prevention
            if context.get("resource_usage", 0) > 90:
                if action_type in ["scale_up", "spawn", "fork"]:
                    violated = True
                    reason = "Action could exhaust resources"
        
        elif principle.id == "P1.4":  # Security Integrity
            security_actions = ["firewall", "auth", "tls", "certificate", "acl"]
            if any(s in action_type.lower() for s in security_actions):
                violated = True
                reason = "Security configuration change requires explicit approval"
        
        # Tier 2 checks
        elif principle.id == "P2.1":  # Minimal Intervention
            if context.get("action_scope", "single") == "all":
                violated = True
                reason = "Action affects all instances - consider targeted approach"
        
        elif principle.id == "P2.2":  # Evidence-Based
            if not context.get("telemetry_evidence"):
                violated = True
                reason = "No telemetry evidence provided"
        
        elif principle.id == "P2.3":  # Audit Trail
            if not context.get("audit_enabled", True):
                violated = True
                reason = "Audit logging must be enabled"
        
        elif principle.id == "P2.4":  # Uncertainty Escalation
            if context.get("confidence", 1.0) < 0.7:
                violated = True
                reason = "Low confidence - escalate to human"
        
        # Tier 3 checks
        elif principle.id == "P3.1":  # Outcome Tracking
            if not context.get("outcome_tracking", True):
                violated = True
                reason = "Outcome tracking should be enabled"
        
        elif principle.id == "P3.2":  # Human Correction Learning
            # Always pass - learning is optional
            pass
        
        elif principle.id == "P3.3":  # Long-term Optimization
            if context.get("is_temporary_fix") and not context.get("permanent_fix_planned"):
                violated = True
                reason = "Temporary fix without permanent solution planned"
        
        return {"violated": violated, "reason": reason}


__all__ = [
    "AuthorizationLevel",
    "ValidationResult",
    "PrincipleViolation",
    "ValidationReport",
    "ConstitutionalValidator",
]
