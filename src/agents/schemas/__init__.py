"""Structured-output JSON schemas for guided decoding (Mode 2 plan, Phase 5).

Each module exports a plain JSON-schema dict handed to vLLM structured
outputs (``response_format: json_schema``; the server's ``auto`` backend
compiles it with xgrammar). Schemas are hand-written — no Pydantic
``model_json_schema()`` — so there is no ``$defs``/``$ref`` indirection and
what the grammar constrains is exactly what is written here.

The schemas mirror the JSON contracts the system prompts already demand
(FAST_ANNOTATOR_SYSTEM_PROMPT, RCA_SYSTEM_PROMPT); guided decoding makes the
"MUST respond ONLY valid JSON" instruction structurally guaranteed instead of
regex-rescued. In Mode 1 the ``guided_schema`` kwarg is ignored by
ModelRouter (profile gate), so passing these is always safe.
"""

from src.agents.schemas.annotation import ANNOTATION_JSON_SCHEMA
from src.agents.schemas.rca import RCA_JSON_SCHEMA

__all__ = ["ANNOTATION_JSON_SCHEMA", "RCA_JSON_SCHEMA"]
