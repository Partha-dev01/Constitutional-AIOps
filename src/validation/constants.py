"""
Constitutional AIOps - Validation Constants

Source of Truth: docs/KEY_METRICS.md, Research_V6.tex
These values must match the documentation exactly.

This module centralizes all performance targets, accuracy metrics, and
configuration constants from the research paper for validation purposes.
"""

__version__ = "0.4.0"


class PerformanceTargets:
    """Performance targets from Research_V6.tex Section 5."""

    # Latency targets (P95)
    FAST_AGENT_LATENCY_P95_MS = 100  # <100ms
    REASONING_AGENT_LATENCY_MIN_MS = 200  # 200-500ms P95
    REASONING_AGENT_LATENCY_MAX_MS = 500

    # Resolution time
    RESOLUTION_TIME_MAX_MINUTES = 5


class AccuracyTargets:
    """Accuracy targets from Research_V6.tex Section 5.2."""

    # Annotation accuracy by telemetry type
    LOG_ANNOTATION_MIN = 0.90
    LOG_ANNOTATION_MAX = 0.95
    METRIC_ANNOTATION_MIN = 0.85
    METRIC_ANNOTATION_MAX = 0.92
    TRACE_ANNOTATION_MIN = 0.85
    TRACE_ANNOTATION_MAX = 0.90

    # Overall annotation accuracy (weighted average)
    OVERALL_ANNOTATION_MIN = 0.87
    OVERALL_ANNOTATION_MAX = 0.92

    # RCA accuracy
    RCA_MIN = 0.85
    RCA_MAX = 0.90


class CompressionMetrics:
    """Token compression metrics from Research_V6.tex Section 4.3."""

    # Compression rate
    TOKEN_COMPRESSION_RATE = 0.92  # 92%

    # Tool sprawl reduction
    TOOL_SPRAWL_REDUCTION = 0.93  # 93%

    # Telemetry ingestion rate
    RAW_INGESTION_TOKENS_PER_HOUR = 1_700_000  # 1.7M tokens/hour


class MemorySystemConfig:
    """Memory system configuration from Research_V6.tex Section 4.2."""

    # Embedding configuration
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSIONS = 384

    # Similarity threshold
    SIMILARITY_THRESHOLD = 0.70  # Minimum cosine similarity

    # Hybrid retrieval (AriGraph-inspired)
    # score(e) = α · vector_sim(e) + (1-α) · graph_sim(e)
    RETRIEVAL_ALPHA = 0.6  # Weight for vector_sim

    # Graph database
    GRAPH_DATABASE = "Neo4j 5.x"
    RETRIEVAL_COMPLEXITY = "O(log n)"


class ConstitutionalAIConfig:
    """Constitutional AI configuration from Research_V6.tex Section 4.1."""

    # Confidence thresholds for authorization matrix
    AUTO_THRESHOLD = 0.90  # >0.90: AUTOMATIC (audit only)
    APPROVAL_THRESHOLD = 0.70  # 0.70-0.90: APPROVAL_REQUIRED
    # <0.70: ALERT_ONLY

    # Confidence formula weights
    # C(a) = α · C_LLM(a) + β · C_hist(a) + γ · C_sim(a)
    WEIGHT_LLM = 0.40  # α - LLM confidence weight
    WEIGHT_HISTORICAL = 0.35  # β - Historical success rate weight
    WEIGHT_SIMILARITY = 0.25  # γ - Similarity to past incidents weight

    # Constitutional principles count
    TIER1_PRINCIPLES = 4  # Safety-critical (P1.1-P1.4)
    TIER2_PRINCIPLES = 4  # Operational (P2.1-P2.4)
    TIER3_PRINCIPLES = 4  # Learning (P3.1-P3.4)
    TOTAL_PRINCIPLES = 12


class VRAMConfig:
    """VRAM allocation from Research_V6.tex Section 3.2."""

    # Fast Agent (Qwen3-4B Q4_K_M)
    FAST_AGENT_MODEL_GB = 2.5
    FAST_AGENT_KV_CACHE_GB = 1.0
    FAST_AGENT_TOTAL_GB = 4.0
    FAST_AGENT_PORT = 8081
    FAST_AGENT_CONTEXT = 8192  # 8K tokens

    # Reasoning Agent (Qwen3-14B Q4_K_M)
    REASONING_AGENT_MODEL_GB = 9.0
    REASONING_AGENT_KV_CACHE_GB = 1.5
    REASONING_AGENT_TOTAL_GB = 11.0
    REASONING_AGENT_PORT = 8082
    REASONING_AGENT_CONTEXT = 4096  # 4K tokens

    # Total VRAM
    TOTAL_USED_GB = 15.0
    TOTAL_AVAILABLE_GB = 24.0
    UTILIZATION_PERCENT = 63  # ~63%


class ObservabilityVersions:
    """Observability stack versions from implementation."""

    LOKI = "v2.9"
    GRAFANA = "v10.2"
    TEMPO = "v2.3"
    MIMIR = "v2.16"
    OTEL_COLLECTOR = "v0.131.0"

    # Data retention
    LOGS_RETENTION_DAYS = 30
    TRACES_RETENTION_DAYS = 7
    METRICS_RETENTION_DAYS = 90


class ResearchGaps:
    """Research gaps addressed from Research_V6.tex Section 2."""

    RG1 = "Automated Knowledge Extraction"
    RG2 = "Graph-Based Operational Knowledge"
    RG3 = "Observability-Specific Tokenization"
    RG4 = "Constitutional AI for Autonomous Operations"
    RG5 = "Comprehensive AI-Enhanced Observability"

    @classmethod
    def list_all(cls) -> list[tuple[str, str]]:
        """Return all research gaps as (ID, description) tuples."""
        return [
            ("RG1", cls.RG1),
            ("RG2", cls.RG2),
            ("RG3", cls.RG3),
            ("RG4", cls.RG4),
            ("RG5", cls.RG5),
        ]


# Export all classes
__all__ = [
    "PerformanceTargets",
    "AccuracyTargets",
    "CompressionMetrics",
    "MemorySystemConfig",
    "ConstitutionalAIConfig",
    "VRAMConfig",
    "ObservabilityVersions",
    "ResearchGaps",
]
