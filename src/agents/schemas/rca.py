"""Guided-decoding schema for reasoning-agent RCA output (Phase 5).

Mirrors the JSON contract RCA_SYSTEM_PROMPT (reasoning_agent.py) already
demands. Note the prompt's format B/C escape hatches (knowledge questions,
multiple choice) still work under this grammar: the substantive answer goes
in `root_cause` and the remaining fields are minimal stubs — the schema only
requires they be PRESENT, not populated.
"""

RCA_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "root_cause": {"type": "string"},
        "causal_chain": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 10,
        },
        "impact": {
            "type": "object",
            "properties": {
                "services": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 15,
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                },
                "users_affected": {"type": "string"},
            },
            "required": ["services", "severity"],
        },
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"},
        "remediation_steps": {
            "type": "array",
            "maxItems": 8,
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "risk": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                    },
                },
                "required": ["action", "risk"],
            },
        },
        "prevention": {"type": "string"},
    },
    "required": [
        "root_cause",
        "causal_chain",
        "impact",
        "confidence",
        "reasoning",
        "remediation_steps",
    ],
}

__all__ = ["RCA_JSON_SCHEMA"]
