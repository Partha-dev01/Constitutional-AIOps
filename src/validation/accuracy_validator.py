"""
Constitutional AIOps - Accuracy Validation Framework

Provides methods to measure and report system accuracy metrics.
Used to generate verifiable metrics for research documentation.

Metrics Tracked:
- Annotation Accuracy: Fast Agent classification correctness
- RCA Accuracy: Reasoning Agent root cause identification
- Remediation Success: Action effectiveness
- Latency Percentiles: P50, P95, P99 response times
- Determinism Score: Output consistency for identical inputs
"""

import json
import math
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class MetricCategory(Enum):
    """Categories of metrics for validation."""
    ANNOTATION = "annotation"
    RCA = "rca"
    REMEDIATION = "remediation"
    LATENCY = "latency"
    DETERMINISM = "determinism"
    CONSTITUTIONAL = "constitutional"


@dataclass
class ValidationResult:
    """Result of a single validation test."""
    metric_name: str
    category: MetricCategory
    expected: Any
    actual: Any
    passed: bool
    timestamp: str
    details: str = ""
    confidence_interval: Optional[float] = None
    sample_size: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metric_name": self.metric_name,
            "category": self.category.value,
            "expected": self.expected,
            "actual": self.actual,
            "passed": self.passed,
            "timestamp": self.timestamp,
            "details": self.details,
            "confidence_interval": self.confidence_interval,
            "sample_size": self.sample_size,
        }


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    name: str
    duration_ms: float
    iterations: int
    avg_latency_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    success_rate: float
    timestamp: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results."""
    name: str
    results: list[BenchmarkResult] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result to the suite."""
        self.results.append(result)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "results": [r.to_dict() for r in self.results],
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    def to_json(self, indent: int = 2) -> str:
        """Export as JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class AccuracyValidator:
    """
    Validates system accuracy against test datasets.
    Used to generate verifiable metrics for research documentation.

    Features:
    - Annotation accuracy validation
    - RCA accuracy validation
    - Determinism testing (same input -> same output)
    - Latency benchmarking
    - Confidence interval calculation
    """

    def __init__(self):
        self.results: list[ValidationResult] = []
        self._benchmark_history: list[BenchmarkResult] = []

    async def validate_annotation_accuracy(
        self,
        annotator,
        test_dataset: list[dict],
        classification_key: str = "classification",
    ) -> dict:
        """
        Validate Fast Agent annotation accuracy.

        Args:
            annotator: FastAnnotator instance with annotate() method
            test_dataset: List of test cases with expected outputs
                Format: [{input: {...}, expected_classification: "...", expected_severity: int}]
            classification_key: Key in annotator response containing classification

        Returns:
            Accuracy metrics with confidence intervals
        """
        if not test_dataset:
            return self._empty_accuracy_result("annotation")

        correct = 0
        total = len(test_dataset)
        errors: list[dict] = []

        for test_case in test_dataset:
            try:
                result = await annotator.annotate(test_case["input"])
                actual = result.get(classification_key, result.get("severity_level", ""))
                expected = test_case.get("expected_classification", test_case.get("expected_severity"))

                if str(actual).upper() == str(expected).upper():
                    correct += 1
                else:
                    errors.append({
                        "input": test_case["input"],
                        "expected": expected,
                        "actual": actual,
                    })
            except Exception as e:
                logger.error(f"Annotation test failed: {e}")
                errors.append({"input": test_case["input"], "error": str(e)})

        accuracy = correct / total if total > 0 else 0
        ci = self._calculate_confidence_interval(accuracy, total)

        result = ValidationResult(
            metric_name="annotation_accuracy",
            category=MetricCategory.ANNOTATION,
            expected=0.85,  # 85% minimum threshold
            actual=accuracy,
            passed=accuracy >= 0.85,
            timestamp=datetime.utcnow().isoformat(),
            details=f"Correct: {correct}/{total}",
            confidence_interval=ci,
            sample_size=total,
        )
        self.results.append(result)

        return {
            "annotation_accuracy": round(accuracy * 100, 2),
            "confidence_interval_95": round(ci * 100, 2),
            "sample_size": total,
            "correct": correct,
            "errors": errors[:10],  # Return first 10 errors
            "timestamp": datetime.utcnow().isoformat(),
            "passed": accuracy >= 0.85,
        }

    async def validate_rca_accuracy(
        self,
        reasoning_agent,
        test_dataset: list[dict],
    ) -> dict:
        """
        Validate Reasoning Agent RCA accuracy.
        Requires human-labeled ground truth.

        Args:
            reasoning_agent: ReasoningAgent instance
            test_dataset: List of test cases
                Format: [{incident: {...}, expected_root_cause: "...", expected_category: "..."}]

        Returns:
            RCA accuracy metrics
        """
        if not test_dataset:
            return self._empty_accuracy_result("rca")

        correct = 0
        partial_matches = 0
        total = len(test_dataset)
        errors: list[dict] = []

        for test_case in test_dataset:
            try:
                result = await reasoning_agent.analyze(test_case["incident"])
                actual_cause = result.get("root_cause", "").lower()
                expected_cause = test_case.get("expected_root_cause", "").lower()

                # Full match
                if expected_cause in actual_cause or actual_cause in expected_cause:
                    correct += 1
                # Partial match (category)
                elif result.get("category") == test_case.get("expected_category"):
                    partial_matches += 1
                else:
                    errors.append({
                        "incident": test_case["incident"][:100],
                        "expected": expected_cause,
                        "actual": actual_cause,
                    })
            except Exception as e:
                logger.error(f"RCA test failed: {e}")
                errors.append({"incident": str(test_case.get("incident", ""))[:100], "error": str(e)})

        accuracy = correct / total if total > 0 else 0
        partial_accuracy = (correct + partial_matches * 0.5) / total if total > 0 else 0
        ci = self._calculate_confidence_interval(accuracy, total)

        result = ValidationResult(
            metric_name="rca_accuracy",
            category=MetricCategory.RCA,
            expected=0.80,  # 80% minimum threshold
            actual=accuracy,
            passed=accuracy >= 0.80,
            timestamp=datetime.utcnow().isoformat(),
            details=f"Full match: {correct}, Partial: {partial_matches}",
            confidence_interval=ci,
            sample_size=total,
        )
        self.results.append(result)

        return {
            "rca_accuracy": round(accuracy * 100, 2),
            "rca_accuracy_with_partial": round(partial_accuracy * 100, 2),
            "confidence_interval_95": round(ci * 100, 2),
            "sample_size": total,
            "full_matches": correct,
            "partial_matches": partial_matches,
            "errors": errors[:10],
            "timestamp": datetime.utcnow().isoformat(),
            "passed": accuracy >= 0.80,
        }

    async def validate_determinism(
        self,
        completion_func: Callable,
        test_prompts: list[str],
        iterations: int = 5,
    ) -> dict:
        """
        Validate output determinism for identical inputs.

        With temperature=0 and fixed seed, same input should produce same output.

        Args:
            completion_func: Async function that takes prompt and returns response
            test_prompts: List of prompts to test
            iterations: Number of times to run each prompt

        Returns:
            Determinism score and consistency metrics
        """
        if not test_prompts:
            return {"determinism_score": 0, "sample_size": 0}

        consistent_prompts = 0
        total_prompts = len(test_prompts)
        details: list[dict] = []

        for prompt in test_prompts:
            outputs: list[str] = []
            for _ in range(iterations):
                try:
                    result = await completion_func(prompt)
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    outputs.append(content)
                except Exception as e:
                    logger.error(f"Determinism test failed: {e}")
                    outputs.append(f"ERROR: {e}")

            # Check if all outputs are identical
            unique_outputs = set(outputs)
            is_consistent = len(unique_outputs) == 1

            if is_consistent:
                consistent_prompts += 1

            details.append({
                "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                "consistent": is_consistent,
                "unique_outputs": len(unique_outputs),
                "iterations": iterations,
            })

        score = consistent_prompts / total_prompts if total_prompts > 0 else 0

        result = ValidationResult(
            metric_name="determinism_score",
            category=MetricCategory.DETERMINISM,
            expected=1.0,  # 100% determinism expected with temp=0
            actual=score,
            passed=score >= 0.95,  # Allow 5% variance for edge cases
            timestamp=datetime.utcnow().isoformat(),
            details=f"Consistent: {consistent_prompts}/{total_prompts}",
            sample_size=total_prompts * iterations,
        )
        self.results.append(result)

        return {
            "determinism_score": round(score * 100, 2),
            "consistent_prompts": consistent_prompts,
            "total_prompts": total_prompts,
            "iterations_per_prompt": iterations,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "passed": score >= 0.95,
        }

    async def run_latency_benchmark(
        self,
        completion_func: Callable,
        prompts: list[str],
        name: str = "latency_benchmark",
    ) -> BenchmarkResult:
        """
        Run latency benchmark on a completion function.

        Args:
            completion_func: Async function that takes prompt and returns response
            prompts: List of prompts to benchmark
            name: Benchmark name

        Returns:
            BenchmarkResult with latency statistics
        """
        import time

        latencies: list[float] = []
        successes = 0
        start_time = time.perf_counter()

        for prompt in prompts:
            try:
                req_start = time.perf_counter()
                result = await completion_func(prompt)
                req_end = time.perf_counter()

                latency_ms = (req_end - req_start) * 1000
                latencies.append(latency_ms)

                # Check if response has _latency_ms from model_router
                if "_latency_ms" in result:
                    latencies[-1] = result["_latency_ms"]

                successes += 1
            except Exception as e:
                logger.error(f"Benchmark request failed: {e}")
                latencies.append(float("inf"))

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Filter out failed requests for percentile calculations
        valid_latencies = [l for l in latencies if l != float("inf")]

        if not valid_latencies:
            return self._empty_benchmark_result(name, len(prompts))

        sorted_latencies = sorted(valid_latencies)

        result = BenchmarkResult(
            name=name,
            duration_ms=round(duration_ms, 2),
            iterations=len(prompts),
            avg_latency_ms=round(sum(valid_latencies) / len(valid_latencies), 2),
            p50_ms=round(self._percentile(sorted_latencies, 50), 2),
            p95_ms=round(self._percentile(sorted_latencies, 95), 2),
            p99_ms=round(self._percentile(sorted_latencies, 99), 2),
            min_ms=round(min(valid_latencies), 2),
            max_ms=round(max(valid_latencies), 2),
            success_rate=round(successes / len(prompts) * 100, 2),
            timestamp=datetime.utcnow().isoformat(),
        )

        self._benchmark_history.append(result)
        return result

    def generate_metrics_report(self) -> dict:
        """
        Generate comprehensive metrics report for research paper.

        Returns:
            Complete metrics report with all validation results
        """
        # Categorize results
        by_category = {}
        for result in self.results:
            cat = result.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(result.to_dict())

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_validations": len(self.results),
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed),
                "categories": list(by_category.keys()),
            },
            "results_by_category": by_category,
            "benchmarks": [b.to_dict() for b in self._benchmark_history],
            "disclaimer": (
                "Metrics validated against synthetic test dataset. "
                "Production validation with real incidents pending."
            ),
            "methodology": {
                "confidence_interval": "Wilson score interval at 95% confidence",
                "determinism_test": "5 iterations per prompt with temp=0.0",
                "latency_measurement": "Client-side timing via time.perf_counter()",
            },
        }

    def export_report(self, format: str = "json") -> str:
        """
        Export metrics report in specified format.

        Args:
            format: Export format ("json" or "csv")

        Returns:
            Report as string
        """
        report = self.generate_metrics_report()

        if format == "json":
            return json.dumps(report, indent=2)

        elif format == "csv":
            lines = [
                "metric_name,category,expected,actual,passed,confidence_interval,sample_size,timestamp"
            ]
            for result in self.results:
                lines.append(
                    f"{result.metric_name},{result.category.value},{result.expected},"
                    f"{result.actual},{result.passed},{result.confidence_interval},"
                    f"{result.sample_size},{result.timestamp}"
                )
            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def clear(self) -> None:
        """Clear all validation results."""
        self.results.clear()
        self._benchmark_history.clear()
        logger.info("Validation results cleared")

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _calculate_confidence_interval(
        self, proportion: float, n: int, confidence: float = 0.95
    ) -> float:
        """
        Calculate Wilson score confidence interval.

        Args:
            proportion: Observed proportion (0-1)
            n: Sample size
            confidence: Confidence level (default 0.95)

        Returns:
            Half-width of confidence interval
        """
        if n == 0:
            return 0

        # Z-score for confidence level
        z = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}.get(confidence, 1.96)

        # Wilson score interval
        denominator = 1 + z**2 / n
        centre_adjusted_probability = proportion + z**2 / (2 * n)
        adjusted_standard_deviation = math.sqrt(
            (proportion * (1 - proportion) + z**2 / (4 * n)) / n
        )

        lower = (centre_adjusted_probability - z * adjusted_standard_deviation) / denominator
        upper = (centre_adjusted_probability + z * adjusted_standard_deviation) / denominator

        # Return half-width
        return (upper - lower) / 2

    def _percentile(self, data: list[float], p: float) -> float:
        """Calculate percentile from sorted data."""
        if not data:
            return 0
        k = (len(data) - 1) * p / 100
        f = int(k)
        c = f + 1 if f + 1 < len(data) else f
        return data[f] + (k - f) * (data[c] - data[f]) if c != f else data[f]

    def _empty_accuracy_result(self, metric_type: str) -> dict:
        """Return empty accuracy result when no test data."""
        return {
            f"{metric_type}_accuracy": 0,
            "confidence_interval_95": 0,
            "sample_size": 0,
            "correct": 0,
            "errors": [],
            "timestamp": datetime.utcnow().isoformat(),
            "passed": False,
            "warning": "No test dataset provided",
        }

    def _empty_benchmark_result(self, name: str, iterations: int) -> BenchmarkResult:
        """Return empty benchmark result when all requests failed."""
        return BenchmarkResult(
            name=name,
            duration_ms=0,
            iterations=iterations,
            avg_latency_ms=0,
            p50_ms=0,
            p95_ms=0,
            p99_ms=0,
            min_ms=0,
            max_ms=0,
            success_rate=0,
            timestamp=datetime.utcnow().isoformat(),
        )


__all__ = ["AccuracyValidator", "ValidationResult", "BenchmarkResult", "BenchmarkSuite", "MetricCategory"]
