"""
Constitutional AIOps - Benchmark Evaluator Module

Provides evaluation metrics for LLM benchmark results.
Uses BERTScore for semantic similarity and exact/partial match for accuracy.
"""

import json
import logging
import re
from dataclasses import dataclass, asdict, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# BERTScore model - using deberta for high accuracy
BERTSCORE_MODEL = "microsoft/deberta-xlarge-mnli"


@dataclass
class EvaluationResult:
    """Complete evaluation result with all metrics."""
    model_name: str
    total_samples: int = 0

    # Annotation metrics
    annotation_exact_match: float = 0.0
    annotation_partial_match: float = 0.0
    annotation_samples: int = 0

    # RCA metrics
    rca_exact_match: float = 0.0
    rca_partial_match: float = 0.0
    rca_samples: int = 0

    # BERTScore metrics
    bert_precision: float = 0.0
    bert_recall: float = 0.0
    bert_f1: float = 0.0

    # Latency metrics
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0

    # Confidence metrics
    avg_confidence: float = 0.0
    confidence_calibration_error: float = 0.0

    # Breakdown by category
    category_breakdown: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class BenchmarkEvaluator:
    """
    Evaluator for benchmark results.

    Provides multiple evaluation metrics:
    - Exact match accuracy
    - Partial match accuracy
    - BERTScore (semantic similarity)
    - Latency percentiles
    - Confidence calibration
    """

    def __init__(self, use_bertscore: bool = True):
        """
        Initialize the evaluator.

        Args:
            use_bertscore: Whether to use BERTScore (requires GPU for speed)
        """
        self.use_bertscore = use_bertscore
        self._bertscore_loaded = False
        self._bert_model = None

    def _load_bertscore(self):
        """Lazy load BERTScore to avoid import delays."""
        if self._bertscore_loaded:
            return

        try:
            from bert_score import score as bert_score
            self._bert_score_fn = bert_score
            self._bertscore_loaded = True
            logger.info("BERTScore loaded successfully")
        except ImportError:
            logger.warning("BERTScore not available. Install with: pip install bert-score")
            self._bertscore_loaded = False
            self.use_bertscore = False

    def evaluate_results(
        self,
        model_name: str,
        test_results: list[dict],
    ) -> EvaluationResult:
        """
        Evaluate benchmark results for a model.

        Args:
            model_name: Name of the model evaluated
            test_results: List of test case results with actual/expected outputs

        Returns:
            EvaluationResult with all metrics
        """
        result = EvaluationResult(model_name=model_name)

        if not test_results:
            return result

        # Separate by task type
        annotation_results = [r for r in test_results if r.get("task_type") == "annotation"]
        rca_results = [r for r in test_results if r.get("task_type") == "rca"]

        result.total_samples = len(test_results)
        result.annotation_samples = len(annotation_results)
        result.rca_samples = len(rca_results)

        # Calculate annotation metrics
        if annotation_results:
            ann_metrics = self._evaluate_annotation_results(annotation_results)
            result.annotation_exact_match = ann_metrics["exact_match"]
            result.annotation_partial_match = ann_metrics["partial_match"]

        # Calculate RCA metrics
        if rca_results:
            rca_metrics = self._evaluate_rca_results(rca_results)
            result.rca_exact_match = rca_metrics["exact_match"]
            result.rca_partial_match = rca_metrics["partial_match"]

        # Calculate BERTScore
        if self.use_bertscore:
            self._load_bertscore()
            if self._bertscore_loaded:
                candidates = [r.get("actual_output", "") for r in test_results]
                references = [r.get("expected_output", "") for r in test_results]
                bert_metrics = self._calculate_bertscore(candidates, references)
                result.bert_precision = bert_metrics["precision"]
                result.bert_recall = bert_metrics["recall"]
                result.bert_f1 = bert_metrics["f1"]

        # Calculate latency metrics
        latencies = [r.get("inference_latency_ms", 0) for r in test_results if r.get("inference_latency_ms", 0) > 0]
        if latencies:
            latency_metrics = self._calculate_latency_percentiles(latencies)
            result.avg_latency_ms = latency_metrics["avg"]
            result.p50_latency_ms = latency_metrics["p50"]
            result.p95_latency_ms = latency_metrics["p95"]
            result.p99_latency_ms = latency_metrics["p99"]

        # Calculate category breakdown
        result.category_breakdown = self._calculate_category_breakdown(test_results)

        return result

    def _evaluate_annotation_results(self, results: list[dict]) -> dict:
        """Evaluate annotation task results."""
        exact_matches = 0
        partial_matches = 0

        for r in results:
            actual = r.get("actual_output", "").lower()
            expected = r.get("expected_output", "")

            # Parse expected if JSON string
            if isinstance(expected, str):
                try:
                    expected = json.loads(expected)
                except json.JSONDecodeError:
                    pass

            # Check anomaly detection
            if isinstance(expected, dict):
                expected_anomaly = expected.get("anomaly_detected", False)

                # Check for exact match on anomaly detection
                if expected_anomaly:
                    if "true" in actual or "anomaly" in actual:
                        if "false" not in actual and "normal" not in actual.replace("abnormal", ""):
                            exact_matches += 1
                            partial_matches += 1
                        else:
                            # Partial match if severity/category is correct
                            if expected.get("severity", "").lower() in actual:
                                partial_matches += 1
                else:
                    if "false" in actual or "normal" in actual:
                        if "true" not in actual and "anomaly" not in actual.replace("no anomaly", "").replace("not anomaly", ""):
                            exact_matches += 1
                            partial_matches += 1
                        else:
                            partial_matches += 1
            else:
                # Simple string comparison
                if str(expected).lower() in actual:
                    exact_matches += 1
                    partial_matches += 1

        total = len(results) if results else 1
        return {
            "exact_match": round(exact_matches / total * 100, 2),
            "partial_match": round(partial_matches / total * 100, 2),
        }

    def _evaluate_rca_results(self, results: list[dict]) -> dict:
        """Evaluate RCA task results."""
        exact_matches = 0
        partial_matches = 0

        for r in results:
            actual = r.get("actual_output", "").lower()
            expected = r.get("expected_output", "").lower()

            # Normalize text for comparison
            actual_normalized = re.sub(r'[^a-z0-9\s]', '', actual)
            expected_normalized = re.sub(r'[^a-z0-9\s]', '', expected)

            # Extract key terms from expected
            expected_terms = set(expected_normalized.split())
            actual_terms = set(actual_normalized.split())

            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'is', 'was', 'were', 'be', 'been', 'being',
                         'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                         'could', 'should', 'may', 'might', 'must', 'shall', 'can',
                         'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from'}
            expected_terms -= stop_words
            actual_terms -= stop_words

            # Calculate overlap
            if expected_terms:
                overlap = len(expected_terms & actual_terms) / len(expected_terms)

                if overlap >= 0.8:
                    exact_matches += 1
                    partial_matches += 1
                elif overlap >= 0.5:
                    partial_matches += 1

            # Also check if expected root cause phrase is in actual
            if expected in actual:
                exact_matches += 1
                partial_matches += 1

        total = len(results) if results else 1
        return {
            "exact_match": round(exact_matches / total * 100, 2),
            "partial_match": round(partial_matches / total * 100, 2),
        }

    def _calculate_bertscore(
        self,
        candidates: list[str],
        references: list[str],
    ) -> dict:
        """Calculate BERTScore metrics."""
        if not self._bertscore_loaded:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        try:
            # Filter out empty strings
            valid_pairs = [
                (c, r) for c, r in zip(candidates, references)
                if c.strip() and r.strip()
            ]

            if not valid_pairs:
                return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

            filtered_candidates = [p[0] for p in valid_pairs]
            filtered_references = [p[1] for p in valid_pairs]

            P, R, F1 = self._bert_score_fn(
                filtered_candidates,
                filtered_references,
                model_type=BERTSCORE_MODEL,
                lang="en",
                verbose=False,
            )

            return {
                "precision": round(P.mean().item(), 4),
                "recall": round(R.mean().item(), 4),
                "f1": round(F1.mean().item(), 4),
            }
        except Exception as e:
            logger.error(f"BERTScore calculation failed: {e}")
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    def _calculate_latency_percentiles(self, latencies: list[float]) -> dict:
        """Calculate latency percentiles."""
        if not latencies:
            return {"avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)

        def percentile(p: float) -> float:
            k = (n - 1) * p / 100
            f = int(k)
            c = min(f + 1, n - 1)
            return sorted_latencies[f] + (k - f) * (sorted_latencies[c] - sorted_latencies[f])

        return {
            "avg": round(sum(latencies) / n, 2),
            "p50": round(percentile(50), 2),
            "p95": round(percentile(95), 2),
            "p99": round(percentile(99), 2),
        }

    def _calculate_category_breakdown(self, results: list[dict]) -> dict:
        """Calculate accuracy breakdown by category."""
        categories = {}

        for r in results:
            task_type = r.get("task_type", "unknown")
            correct = r.get("correct", False)

            if task_type not in categories:
                categories[task_type] = {"total": 0, "correct": 0}

            categories[task_type]["total"] += 1
            if correct:
                categories[task_type]["correct"] += 1

        # Calculate accuracy for each category
        breakdown = {}
        for cat, counts in categories.items():
            if counts["total"] > 0:
                breakdown[cat] = {
                    "total": counts["total"],
                    "correct": counts["correct"],
                    "accuracy": round(counts["correct"] / counts["total"] * 100, 2),
                }

        return breakdown

    def compare_models(
        self,
        evaluation_results: list[EvaluationResult],
    ) -> dict:
        """
        Compare evaluation results across multiple models.

        Args:
            evaluation_results: List of EvaluationResult objects

        Returns:
            Dictionary with comparison metrics and rankings
        """
        if not evaluation_results:
            return {}

        comparison = {
            "models": [],
            "rankings": {
                "annotation_accuracy": [],
                "rca_accuracy": [],
                "bert_f1": [],
                "latency": [],
            },
            "summary": {},
        }

        # Build model data
        for result in evaluation_results:
            model_data = {
                "name": result.model_name,
                "annotation_accuracy": result.annotation_exact_match,
                "rca_accuracy": result.rca_exact_match,
                "bert_f1": result.bert_f1,
                "avg_latency_ms": result.avg_latency_ms,
                "total_samples": result.total_samples,
            }
            comparison["models"].append(model_data)

        # Calculate rankings (higher is better for accuracy, lower for latency)
        comparison["rankings"]["annotation_accuracy"] = sorted(
            comparison["models"],
            key=lambda x: x["annotation_accuracy"],
            reverse=True
        )
        comparison["rankings"]["rca_accuracy"] = sorted(
            comparison["models"],
            key=lambda x: x["rca_accuracy"],
            reverse=True
        )
        comparison["rankings"]["bert_f1"] = sorted(
            comparison["models"],
            key=lambda x: x["bert_f1"],
            reverse=True
        )
        comparison["rankings"]["latency"] = sorted(
            comparison["models"],
            key=lambda x: x["avg_latency_ms"],
            reverse=False
        )

        # Summary statistics
        comparison["summary"] = {
            "best_annotation": comparison["rankings"]["annotation_accuracy"][0]["name"] if comparison["rankings"]["annotation_accuracy"] else None,
            "best_rca": comparison["rankings"]["rca_accuracy"][0]["name"] if comparison["rankings"]["rca_accuracy"] else None,
            "best_bert_f1": comparison["rankings"]["bert_f1"][0]["name"] if comparison["rankings"]["bert_f1"] else None,
            "fastest": comparison["rankings"]["latency"][0]["name"] if comparison["rankings"]["latency"] else None,
        }

        return comparison


__all__ = ["BenchmarkEvaluator", "EvaluationResult", "BERTSCORE_MODEL"]
