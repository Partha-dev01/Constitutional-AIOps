"""
Constitutional AIOps - Constitutional AI Principles

Defines the 11 constitutional principles organized into 3 tiers.
These principles govern all autonomous actions taken by the system.

Tier 1 (Safety-Critical): NEVER violate under any circumstances
Tier 2 (Operational): Best practices, require approval to violate
Tier 3 (Learning): Soft guidelines for continuous improvement
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PrincipleTier(Enum):
    """Tiers of constitutional principles."""
    TIER_1_SAFETY = 1      # Never violate
    TIER_2_OPERATIONAL = 2  # Require approval to violate
    TIER_3_LEARNING = 3     # Soft guidelines


@dataclass
class Principle:
    """A constitutional principle."""
    id: str
    tier: PrincipleTier
    name: str
    description: str
    violation_action: str  # What happens on violation
    examples: list[str]    # Example scenarios


# Tier 1: Safety-Critical Principles (NEVER violate)
PRINCIPLE_P1_1 = Principle(
    id="P1.1",
    tier=PrincipleTier.TIER_1_SAFETY,
    name="Data Protection",
    description="Never execute actions that could cause data loss or corruption",
    violation_action="BLOCK_ALWAYS",
    examples=[
        "Deleting database tables",
        "Truncating logs without backup",
        "Modifying production data directly",
        "Dropping indexes during high load",
    ],
)

PRINCIPLE_P1_2 = Principle(
    id="P1.2",
    tier=PrincipleTier.TIER_1_SAFETY,
    name="Active Incident Safety",
    description="Never take destructive actions during active incidents without explicit approval",
    violation_action="BLOCK_ALWAYS",
    examples=[
        "Restarting services during outage investigation",
        "Scaling down during incident triage",
        "Deploying changes during active alerts",
        "Modifying configs while debugging",
    ],
)

PRINCIPLE_P1_3 = Principle(
    id="P1.3",
    tier=PrincipleTier.TIER_1_SAFETY,
    name="Cascade Prevention",
    description="Never exceed resource limits that could cause cascade failures",
    violation_action="BLOCK_ALWAYS",
    examples=[
        "Scaling beyond cluster capacity",
        "Creating too many connections",
        "Exhausting memory limits",
        "Triggering thundering herd",
    ],
)

PRINCIPLE_P1_4 = Principle(
    id="P1.4",
    tier=PrincipleTier.TIER_1_SAFETY,
    name="Security Integrity",
    description="Never modify security configurations without explicit approval",
    violation_action="BLOCK_ALWAYS",
    examples=[
        "Changing firewall rules",
        "Modifying authentication settings",
        "Updating TLS certificates",
        "Changing access controls",
    ],
)

# Tier 2: Operational Principles (require approval to violate)
PRINCIPLE_P2_1 = Principle(
    id="P2.1",
    tier=PrincipleTier.TIER_2_OPERATIONAL,
    name="Minimal Intervention",
    description="Prefer the smallest effective action to resolve issues",
    violation_action="REQUIRE_APPROVAL",
    examples=[
        "Restart single pod before full deployment",
        "Clear specific cache before full flush",
        "Kill single query before connection reset",
        "Scale incrementally before big jumps",
    ],
)

PRINCIPLE_P2_2 = Principle(
    id="P2.2",
    tier=PrincipleTier.TIER_2_OPERATIONAL,
    name="Evidence-Based Actions",
    description="Require telemetry evidence before taking action",
    violation_action="REQUIRE_APPROVAL",
    examples=[
        "Metrics showing resource exhaustion",
        "Logs indicating specific errors",
        "Traces showing latency spikes",
        "Alerts with corroborating data",
    ],
)

PRINCIPLE_P2_3 = Principle(
    id="P2.3",
    tier=PrincipleTier.TIER_2_OPERATIONAL,
    name="Audit Trail",
    description="Log all actions for audit and rollback capability",
    violation_action="REQUIRE_APPROVAL",
    examples=[
        "Recording action timestamp",
        "Capturing pre-action state",
        "Logging decision reasoning",
        "Storing rollback commands",
    ],
)

PRINCIPLE_P2_4 = Principle(
    id="P2.4",
    tier=PrincipleTier.TIER_2_OPERATIONAL,
    name="Uncertainty Escalation",
    description="Escalate to humans when confidence is below threshold",
    violation_action="REQUIRE_APPROVAL",
    examples=[
        "Novel failure patterns",
        "Conflicting telemetry signals",
        "Actions affecting multiple services",
        "First-time remediation attempts",
    ],
)

# Tier 3: Learning Principles (soft guidelines)
PRINCIPLE_P3_1 = Principle(
    id="P3.1",
    tier=PrincipleTier.TIER_3_LEARNING,
    name="Outcome Tracking",
    description="Track outcomes of actions for continuous improvement",
    violation_action="LOG_WARNING",
    examples=[
        "Recording action success/failure",
        "Measuring resolution time",
        "Tracking recurrence rates",
        "Comparing predicted vs actual impact",
    ],
)

PRINCIPLE_P3_2 = Principle(
    id="P3.2",
    tier=PrincipleTier.TIER_3_LEARNING,
    name="Human Correction Learning",
    description="Learn from human corrections and overrides",
    violation_action="LOG_WARNING",
    examples=[
        "Updating confidence models",
        "Refining classification rules",
        "Adjusting thresholds",
        "Incorporating feedback",
    ],
)

PRINCIPLE_P3_3 = Principle(
    id="P3.3",
    tier=PrincipleTier.TIER_3_LEARNING,
    name="Long-term Optimization",
    description="Optimize for long-term system health over short-term fixes",
    violation_action="LOG_WARNING",
    examples=[
        "Addressing root cause over symptoms",
        "Preventing recurrence",
        "Improving system resilience",
        "Reducing technical debt",
    ],
)

# All principles organized by tier
TIER_1_PRINCIPLES = [PRINCIPLE_P1_1, PRINCIPLE_P1_2, PRINCIPLE_P1_3, PRINCIPLE_P1_4]
TIER_2_PRINCIPLES = [PRINCIPLE_P2_1, PRINCIPLE_P2_2, PRINCIPLE_P2_3, PRINCIPLE_P2_4]
TIER_3_PRINCIPLES = [PRINCIPLE_P3_1, PRINCIPLE_P3_2, PRINCIPLE_P3_3]

ALL_PRINCIPLES = TIER_1_PRINCIPLES + TIER_2_PRINCIPLES + TIER_3_PRINCIPLES

# Quick lookup by ID
PRINCIPLES_BY_ID = {p.id: p for p in ALL_PRINCIPLES}


def get_principle(principle_id: str) -> Optional[Principle]:
    """Get a principle by its ID."""
    return PRINCIPLES_BY_ID.get(principle_id)


def get_principles_by_tier(tier: PrincipleTier) -> list[Principle]:
    """Get all principles for a specific tier."""
    return [p for p in ALL_PRINCIPLES if p.tier == tier]


__all__ = [
    "PrincipleTier",
    "Principle",
    "TIER_1_PRINCIPLES",
    "TIER_2_PRINCIPLES", 
    "TIER_3_PRINCIPLES",
    "ALL_PRINCIPLES",
    "PRINCIPLES_BY_ID",
    "get_principle",
    "get_principles_by_tier",
]
