"""
Constitutional AIOps - Incident Lifecycle State Machine

Enforces legal state transitions for the incident lifecycle.
Prevents invalid transitions (e.g., DETECTING -> RESOLVED directly).

States: detecting -> analyzing -> remediating -> resolved
                             \-> escalated -> analyzing (re-entry)
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class IncidentStateMachine:
    """
    Enforce legal incident lifecycle transitions.

    The state machine ensures incidents follow a valid progression:
    - detecting: Initial anomaly detection (System 1)
    - analyzing: RCA in progress (System 2)
    - remediating: Fix being applied
    - escalated: Human intervention required
    - resolved: Incident closed

    Invalid transitions (e.g., detecting -> resolved) are rejected.
    """

    TRANSITIONS: dict[str, list[str]] = {
        "detecting": ["analyzing"],
        "analyzing": ["remediating", "escalated", "resolved"],
        "remediating": ["resolved", "escalated"],
        "escalated": ["analyzing", "resolved"],
    }

    ALL_STATES = {"detecting", "analyzing", "remediating", "escalated", "resolved"}

    def validate_transition(self, from_state: str, to_state: str) -> bool:
        """
        Check if a state transition is legal.

        Args:
            from_state: Current incident state
            to_state: Desired next state

        Returns:
            True if the transition is allowed
        """
        allowed = self.TRANSITIONS.get(from_state, [])
        is_valid = to_state in allowed

        if not is_valid:
            logger.warning(
                f"Invalid incident transition: {from_state} -> {to_state} "
                f"(allowed: {allowed})"
            )

        return is_valid

    def get_next_states(self, current: str) -> list[str]:
        """
        Get all valid next states from the current state.

        Args:
            current: Current incident state

        Returns:
            List of valid next states
        """
        return self.TRANSITIONS.get(current, [])

    def map_authorization_to_state(
        self,
        authorization_level: str,
        current_state: str = "detecting",
    ) -> Optional[str]:
        """
        Map a LangGraph pipeline authorization result to the next incident state.

        Args:
            authorization_level: "automatic", "approval", or "alert"
            current_state: Current incident state

        Returns:
            Next state, or None if no transition should occur
        """
        mapping = {
            "automatic": "remediating",
            "approval": "escalated",
            "alert": "analyzing",
        }

        target = mapping.get(authorization_level)
        if target and self.validate_transition(current_state, target):
            return target

        # If the mapped transition isn't valid from current state, stay put
        return None


__all__ = ["IncidentStateMachine"]
