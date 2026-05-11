"""
Constitutional AIOps - Validation Framework

Provides methods to measure, validate, and report system accuracy metrics.
Used to generate verifiable metrics for research documentation.

Source of Truth: docs/KEY_METRICS.md, Research_V7.tex
"""

from src.validation.accuracy_validator import (
    AccuracyValidator,
    ValidationResult,
    BenchmarkSuite,
)
from src.validation.constants import (
    PerformanceTargets,
    AccuracyTargets,
    CompressionMetrics,
    MemorySystemConfig,
    ConstitutionalAIConfig,
    VRAMConfig,
    ObservabilityVersions,
    ResearchGaps,
)

__all__ = [
    # Accuracy validation
    "AccuracyValidator",
    "ValidationResult",
    "BenchmarkSuite",
    # Constants from Research_V7.tex
    "PerformanceTargets",
    "AccuracyTargets",
    "CompressionMetrics",
    "MemorySystemConfig",
    "ConstitutionalAIConfig",
    "VRAMConfig",
    "ObservabilityVersions",
    "ResearchGaps",
]
