"""Guided-decoding schema for fast-agent telemetry annotation (Phase 5).

Mirrors the JSON contract FAST_ANNOTATOR_SYSTEM_PROMPT (fast_annotator.py)
already demands, field for field. The prompt stays the source of the model's
INSTRUCTIONS; this schema makes the FORMAT structurally guaranteed under
vLLM structured outputs, so `_parse_annotation`'s brace-matching rescue
becomes a no-op in Mode 2.

Deliberate laxities (grammar constrains shape, prompt constrains judgment):
- `severity` / `category` are enums (the downstream code switches on them);
- `confidence` is a number; range clamping stays in FastAnnotator.process
  (a grammar can't express 0.0-1.0 tightly across number syntaxes anyway);
- `triplets` items are fixed-shape objects with UPPER_CASE relation left as
  free string (canonicalization happens in canonicalize_entity()).
"""

ANNOTATION_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "anomaly_detected": {"type": "boolean"},
        "severity": {
            "type": "string",
            "enum": ["critical", "warning", "info"],
        },
        "category": {
            "type": "string",
            "enum": ["performance", "error", "security", "resource"],
        },
        "confidence": {"type": "number"},
        "summary": {"type": "string", "maxLength": 500},
        "needs_reasoning": {"type": "boolean"},
        "key_indicators": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 8,
        },
        "triplets": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "relation": {"type": "string"},
                    "object": {"type": "string"},
                },
                "required": ["subject", "relation", "object"],
            },
        },
    },
    "required": [
        "anomaly_detected",
        "severity",
        "category",
        "confidence",
        "summary",
        "needs_reasoning",
        "key_indicators",
        "triplets",
    ],
}

__all__ = ["ANNOTATION_JSON_SCHEMA"]
