"""
Constitutional AIOps - Configuration Module

This module contains all configuration settings for the Constitutional AIOps system.
Settings are loaded from environment variables with sensible defaults.

Architecture: Simultaneous Dual-Model (Qwen3-4B + Qwen3-14B on 24GB VRAM)
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMConfig:
    """LLM endpoint configuration for simultaneous dual-model setup."""
    
    # Fast Agent (Qwen3-4B) - Always loaded at port 8081
    fast_agent_url: str = field(
        default_factory=lambda: os.getenv("FAST_AGENT_URL", "http://localhost:8081/v1")
    )
    fast_agent_model: str = field(
        default_factory=lambda: os.getenv("FAST_AGENT_MODEL", "qwen3:4b")
    )
    fast_agent_context: int = 8192  # 8K context window
    fast_agent_timeout: float = field(
        default_factory=lambda: float(os.getenv("FAST_AGENT_TIMEOUT", "30"))
    )

    # Reasoning Agent (Qwen3-14B) - Always loaded at port 8082
    reasoning_agent_url: str = field(
        default_factory=lambda: os.getenv("REASONING_AGENT_URL", "http://localhost:8082/v1")
    )
    reasoning_agent_model: str = field(
        default_factory=lambda: os.getenv("REASONING_AGENT_MODEL", "qwen3:14b")
    )
    reasoning_agent_context: int = 4096  # 4K context window
    reasoning_agent_timeout: float = field(
        default_factory=lambda: float(os.getenv("REASONING_AGENT_TIMEOUT", "120"))
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
        default_factory=lambda: os.getenv("NEO4J_PASSWORD", "constitutional_aiops_2025")
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
class ConstitutionalConfig:
    """Constitutional AI framework configuration."""
    
    # Confidence thresholds for authorization matrix
    confidence_threshold_auto: float = field(
        default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD_AUTO", "0.90"))
    )
    confidence_threshold_approval: float = field(
        default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD_APPROVAL", "0.70"))
    )
    
    # Principle enforcement
    strict_tier1: bool = True  # Never allow Tier 1 violations
    log_all_decisions: bool = True  # Audit trail
    
    # Action limits
    max_actions_per_minute: int = 10
    max_concurrent_actions: int = 3


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
    
    # CORS
    cors_origins: list = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    )


@dataclass
class Config:
    """Main configuration class aggregating all config sections."""
    
    llm: LLMConfig = field(default_factory=LLMConfig)
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    constitutional: ConstitutionalConfig = field(default_factory=ConstitutionalConfig)
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
    "AppConfig",
    "config",
]
