"""
Constitutional AIOps - Configuration Module

This module contains all configuration settings for the Constitutional AIOps system.
Settings are loaded from environment variables with sensible defaults.

Architecture: Simultaneous Dual-Model (Qwen3-4B + Qwen3-14B on 24GB VRAM)
"""

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from dotenv import load_dotenv
load_dotenv()  # Load .env before any os.getenv() calls in dataclass defaults

if TYPE_CHECKING:  # import for type hints only — see ServingConfig note below
    from src.agents.serving_profile import ServingProfile


def _require_password(env_var: str, dev_default: str) -> str:
    """Resolve a secret from the environment.

    In production (``ENVIRONMENT=production``) the variable is mandatory and there
    is no built-in default; outside production a clearly-marked dev default is used
    so local ``docker compose up`` keeps working.
    """
    value = os.getenv(env_var)
    if value:
        return value
    if os.getenv("ENVIRONMENT", "local").lower() == "production":
        raise RuntimeError(
            f"{env_var} must be set in production (no built-in default). "
            "Provide it via .env.production or a secrets manager."
        )
    return dev_default


def _resolve_cors_origins() -> list:
    """Parse ``CORS_ORIGINS`` and refuse the unsafe ``*`` + credentials combo.

    The app sends credentials (``allow_credentials=True`` in ``main.py``), so a
    wildcard origin is BOTH browser-invalid (Starlette can't reflect ``*`` with
    credentials) AND unsafe (it would make the credentialed API readable by any
    site). We therefore:
      * strip empty entries left by a stray trailing comma;
      * reject a literal ``*`` origin in production (fail-fast — the operator
        must pin a real origin list);
      * outside production, drop a ``*`` and fall back to the localhost dev
        origin with a warning instead of booting an unsafe config.
    """
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    is_production = os.getenv("ENVIRONMENT", "local").lower() == "production"

    if "*" in origins:
        if is_production:
            raise RuntimeError(
                "CORS_ORIGINS='*' is not allowed: the API sends credentials, so a "
                "wildcard origin is both browser-invalid and unsafe. Set CORS_ORIGINS "
                "to an explicit comma-separated origin list in .env.production."
            )
        # Dev: don't honour the wildcard; drop it and keep any explicit origins.
        import logging as _logging

        _logging.getLogger(__name__).warning(
            "CORS_ORIGINS contained '*' with credentials enabled; ignoring the "
            "wildcard (unsafe). Using explicit origins only."
        )
        origins = [o for o in origins if o != "*"]

    if not origins:
        # Never boot with an empty allow-list (would make every CORS preflight
        # fail); fall back to the documented dev default.
        origins = ["http://localhost:3000"]
    return origins


@dataclass
class LLMConfig:
    """LLM endpoint configuration for simultaneous dual-model setup."""
    
    # Fast Agent (Qwen3-4B) - vLLM served as "qwen3-4b" on port 8000.
    # Colon-free served-model-name triggers ModelRouter's enable_thinking=false path.
    fast_agent_url: str = field(
        default_factory=lambda: os.getenv("FAST_AGENT_URL", "http://localhost:8000/v1")
    )
    fast_agent_model: str = field(
        default_factory=lambda: os.getenv("FAST_AGENT_MODEL", "qwen3-4b")
    )
    fast_agent_context: int = 8192  # 8K context window
    fast_agent_timeout: float = field(
        default_factory=lambda: float(os.getenv("FAST_AGENT_TIMEOUT", "120"))
    )

    # Reasoning Agent (Qwen3-14B) - vLLM served as "qwen3-14b" on port 8001.
    reasoning_agent_url: str = field(
        default_factory=lambda: os.getenv("REASONING_AGENT_URL", "http://localhost:8001/v1")
    )
    reasoning_agent_model: str = field(
        default_factory=lambda: os.getenv("REASONING_AGENT_MODEL", "qwen3-14b")
    )
    reasoning_agent_context: int = 4096  # 4K context window
    reasoning_agent_timeout: float = field(
        default_factory=lambda: float(os.getenv("REASONING_AGENT_TIMEOUT", "180"))
    )


@dataclass
class Neo4jConfig:
    """Neo4j graph database configuration for episodic memory."""
    
    uri: str = field(
        default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687")
    )
    user: str = field(
        default_factory=lambda: os.getenv("NEO4J_USER", "neo4j")
    )
    password: str = field(
        default_factory=lambda: _require_password("NEO4J_PASSWORD", "devpassword")
    )
    database: str = field(
        default_factory=lambda: os.getenv("NEO4J_DATABASE", "neo4j")
    )


@dataclass
class ObservabilityConfig:
    """LGTM stack configuration."""
    
    loki_url: str = field(
        default_factory=lambda: os.getenv("LOKI_URL", "http://localhost:3100")
    )
    tempo_url: str = field(
        default_factory=lambda: os.getenv("TEMPO_URL", "http://localhost:3200")
    )
    prometheus_url: str = field(
        default_factory=lambda: os.getenv("PROMETHEUS_URL", "http://localhost:9090")
    )
    grafana_url: str = field(
        default_factory=lambda: os.getenv("GRAFANA_URL", "http://localhost:3000")
    )


@dataclass
class MemoryConfig:
    """Memory system configuration (from Research_V7.tex)."""

    # Embedding configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    similarity_threshold: float = 0.70  # Minimum cosine similarity for matching

    # Hybrid retrieval
    retrieval_alpha: float = 0.6  # Weight for vector_sim in hybrid scoring


@dataclass
class PerformanceConfig:
    """Performance targets configuration (from Research_V7.tex)."""

    # Latency targets (P95)
    fast_agent_latency_target_ms: int = 100  # <100ms P95
    reasoning_agent_latency_min_ms: int = 200  # 200-500ms P95
    reasoning_agent_latency_max_ms: int = 500

    # Accuracy targets
    annotation_accuracy_min: float = 0.87
    annotation_accuracy_max: float = 0.92
    rca_accuracy_min: float = 0.85
    rca_accuracy_max: float = 0.90

    # Compression
    token_compression_rate: float = 0.92

    # Resolution time
    resolution_time_max_minutes: int = 5


@dataclass
class ConstitutionalConfig:
    """Constitutional AI framework configuration."""

    # Confidence thresholds for authorization matrix (from Research_V7.tex)
    # C(a) = 0.4 · C_LLM + 0.35 · C_hist + 0.25 · C_sim
    confidence_threshold_auto: float = field(
        default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD_AUTO", "0.90"))
    )
    confidence_threshold_approval: float = field(
        default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD_APPROVAL", "0.70"))
    )

    # Confidence formula weights
    confidence_weight_llm: float = 0.40
    confidence_weight_historical: float = 0.35
    confidence_weight_similarity: float = 0.25

    # Principle enforcement
    strict_tier1: bool = True  # Never allow Tier 1 violations
    log_all_decisions: bool = True  # Audit trail

    # Constitutional AI principles count
    tier1_principles: int = 4  # Safety-critical (P1.1-P1.4)
    tier2_principles: int = 4  # Operational (P2.1-P2.4)
    tier3_principles: int = 4  # Learning (P3.1-P3.4)
    total_principles: int = 12

    # Action limits
    max_actions_per_minute: int = 10
    max_concurrent_actions: int = 3


def _parse_serving_mode() -> int:
    """Parse ``AIOPS_MODE`` (Mode 2 plan, Phase 1).

    Unset / empty / anything other than ``"2"`` resolves to Mode 1, so a bare
    deploy is byte-identical to today. Kept in lockstep with the CANONICAL
    resolver ``src.agents.serving_profile.resolve_serving_profile()`` — that
    module is deliberately import-free of this one (no circular import), so
    the two-line mode parse is mirrored here.
    """
    return 2 if (os.getenv("AIOPS_MODE") or "").strip() == "2" else 1


@dataclass
class ServingConfig:
    """Serving-mode selection (Mode 2 plan, Phase 1) — purely ADDITIVE.

    Mode 1 (``AIOPS_MODE`` unset/empty/``1``/unrecognized) is the frozen
    dual-engine paper artifact; Mode 2 (``AIOPS_MODE=2``) is the modernized
    stack applied via ``docker/docker-compose.mode2.yml``.

    NOTE: like every other section, this is resolved once at import time.
    Runtime consumers that must observe the *current* environment (the
    ``ModelRouter`` constructor, ``GET /api/v1/health/serving``, tests) call
    ``resolve_serving_profile()`` directly instead — see
    :meth:`resolve_profile`.
    """

    # Resolved serving mode: 1 (default, frozen artifact) or 2.
    mode: int = field(default_factory=_parse_serving_mode)

    def resolve_profile(self) -> "ServingProfile":
        """Return the fully-resolved :class:`ServingProfile` from current env.

        Lazy import: ``src.agents.serving_profile`` is pure stdlib, but going
        through ``src.agents`` at module-import time would pull the whole
        agents package (which imports this module) — resolving lazily keeps
        the import graph acyclic.
        """
        from src.agents.serving_profile import resolve_serving_profile

        return resolve_serving_profile()


@dataclass
class AppConfig:
    """Application-wide configuration."""
    
    # Server settings
    host: str = field(
        default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.getenv("APP_PORT", "8000"))
    )
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true"
    )
    
    # Logging
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS — validated: never a wildcard while credentials are enabled.
    cors_origins: list = field(default_factory=_resolve_cors_origins)


@dataclass
class Config:
    """Main configuration class aggregating all config sections."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    constitutional: ConstitutionalConfig = field(default_factory=ConstitutionalConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    serving: ServingConfig = field(default_factory=ServingConfig)
    app: AppConfig = field(default_factory=AppConfig)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls()


# Global configuration instance
config = Config.from_env()


# Export for convenience
__all__ = [
    "Config",
    "LLMConfig",
    "Neo4jConfig",
    "ObservabilityConfig",
    "ConstitutionalConfig",
    "MemoryConfig",
    "PerformanceConfig",
    "ServingConfig",
    "AppConfig",
    "config",
]
