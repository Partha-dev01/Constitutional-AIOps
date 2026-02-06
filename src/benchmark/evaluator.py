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

    # Semantic similarity metrics
    avg_cosine_similarity: float = 0.0
    avg_term_overlap: float = 0.0
    annotation_bert_f1: float = 0.0
    rca_bert_f1: float = 0.0
    annotation_cosine_sim: float = 0.0
    rca_cosine_sim: float = 0.0
    annotation_term_overlap: float = 0.0
    rca_term_overlap: float = 0.0

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

    def __init__(self, use_bertscore: bool = True, use_embeddings: bool = True):
        """
        Initialize the evaluator.

        Args:
            use_bertscore: Whether to use BERTScore (requires GPU for speed)
            use_embeddings: Whether to use sentence-transformer cosine similarity
        """
        self.use_bertscore = use_bertscore
        self.use_embeddings = use_embeddings
        self._bertscore_loaded = False
        self._bert_model = None
        self._embedding_service = None

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

    def _load_embedding_service(self):
        """Lazy load the embedding service for cosine similarity."""
        if self._embedding_service is not None:
            return
        try:
            from src.memory.embedding_service import EmbeddingService
            self._embedding_service = EmbeddingService()
            logger.info("Embedding service loaded for cosine similarity")
        except Exception as e:
            logger.warning(f"Embedding service unavailable: {e}")
            self._embedding_service = None
            self.use_embeddings = False

    def _calculate_term_overlap(self, candidate: str, reference: str) -> float:
        """Calculate normalized term overlap between candidate and reference."""
        if not reference.strip() or not candidate.strip():
            return 0.0

        stop_words = {
            'the', 'a', 'an', 'is', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'and', 'or', 'but', 'not', 'no', 'if', 'then', 'else',
            'this', 'that', 'it', 'its', 'as', 'so', 'up', 'out',
        }

        ref_normalized = re.sub(r'[^a-z0-9\s]', '', reference.lower())
        cand_normalized = re.sub(r'[^a-z0-9\s]', '', candidate.lower())

        ref_terms = set(ref_normalized.split()) - stop_words
        cand_terms = set(cand_normalized.split()) - stop_words

        if not ref_terms:
            return 0.0

        overlap = len(ref_terms & cand_terms) / len(ref_terms)
        return round(overlap, 4)

    def _calculate_cosine_similarity_batch(
        self,
        candidates: list[str],
        references: list[str],
    ) -> list[float]:
        """Calculate cosine similarity for each (candidate, reference) pair."""
        if not self.use_embeddings or self._embedding_service is None:
            return [0.0] * len(candidates)

        try:
            all_texts = candidates + references
            all_embeddings = self._embedding_service.encode_batch(all_texts)

            n = len(candidates)
            similarities = []
            for i in range(n):
                cand_emb = all_embeddings[i]
                ref_emb = all_embeddings[n + i]
                if cand_emb is not None and ref_emb is not None:
                    sim = self._embedding_service.cosine_similarity(cand_emb, ref_emb)
                    similarities.append(round(sim, 4))
                else:
                    similarities.append(0.0)
            return similarities

        except Exception as e:
            logger.error(f"Cosine similarity batch failed: {e}")
            return [0.0] * len(candidates)

    def _calculate_bertscore_per_item(
        self,
        candidates: list[str],
        references: list[str],
    ) -> list[float]:
        """Calculate per-item BERTScore F1 (not just mean)."""
        if not self.use_bertscore or not self._bertscore_loaded:
            return [0.0] * len(candidates)

        try:
            valid_indices = []
            valid_cands = []
            valid_refs = []
            for i, (c, r) in enumerate(zip(candidates, references)):
                if c.strip() and r.strip():
                    valid_indices.append(i)
                    valid_cands.append(c)
                    valid_refs.append(r)

            if not valid_cands:
                return [0.0] * len(candidates)

            P, R, F1 = self._bert_score_fn(
                valid_cands,
                valid_refs,
                model_type=BERTSCORE_MODEL,
                lang="en",
                verbose=False,
            )

            results = [0.0] * len(candidates)
            for i, idx in enumerate(valid_indices):
                results[idx] = round(F1[i].item(), 4)
            return results

        except Exception as e:
            logger.error(f"Per-item BERTScore failed: {e}")
            return [0.0] * len(candidates)

    def _normalize_for_comparison(self, text: str, task_type: str, role: str) -> str:
        """
        Normalize text for semantic comparison to fix format mismatch.

        The raw expected/actual outputs have incompatible formats:
        - Annotation expected: JSON metadata like {"anomaly_detected": true, "severity": "warning"}
        - Annotation actual: natural language description
        - RCA expected: short keyword/slug like "loadgenerator_cpu_spike"
        - RCA actual: full JSON with root_cause, causal_chain, etc.

        This normalizes both sides to natural language for fair comparison.
        """
        if not text or not text.strip():
            return ""

        if task_type == "annotation" and role == "expected":
            # Convert annotation JSON metadata to natural language
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    parts = []
                    if data.get("anomaly_detected"):
                        parts.append("anomaly detected")
                    else:
                        parts.append("normal operation, no anomaly")
                    if data.get("severity"):
                        parts.append(f"severity {data['severity']}")
                    if data.get("category"):
                        parts.append(f"category {data['category']}")
                    if data.get("classification"):
                        parts.append(f"classified as {data['classification']}")
                    return ", ".join(parts) if parts else text
            except (json.JSONDecodeError, TypeError):
                pass
            return text

        if task_type == "rca" and role == "expected":
            # Convert underscore-separated slugs to natural language
            # "loadgenerator_cpu_spike" -> "load generator cpu spike"
            normalized = text.replace("_", " ").replace("-", " ")
            return normalized

        if task_type == "rca" and role == "actual":
            # Extract root_cause from JSON response
            try:
                data = json.loads(text)
                if isinstance(data, dict) and "root_cause" in data:
                    return data["root_cause"]
            except (json.JSONDecodeError, TypeError):
                pass
            return text

        # annotation actual is already natural language, return as-is
        return text

    def compute_all_metrics(self, test_results: list[dict]) -> list[dict]:
        """
        Compute all semantic metrics for test results (post-processing).

        Enriches each test result dict with:
        - bert_f1: per-item BERTScore F1
        - cosine_similarity: sentence embedding cosine similarity
        - term_overlap: normalized term overlap

        Before computing metrics, normalizes expected/actual outputs to comparable
        natural language to avoid format mismatch (JSON vs text, slugs vs sentences).

        Args:
            test_results: List of test result dicts with actual_output and expected_output

        Returns:
            The same list, enriched with metric fields
        """
        if not test_results:
            return test_results

        # Normalize outputs for fair semantic comparison
        candidates = []
        references = []
        for r in test_results:
            task_type = r.get("task_type", "")
            actual = r.get("actual_output", "")
            expected = r.get("expected_output", "")
            candidates.append(self._normalize_for_comparison(actual, task_type, "actual"))
            references.append(self._normalize_for_comparison(expected, task_type, "expected"))

        # Term overlap (always available, no model needed)
        logger.info("Computing term overlap...")
        for i, (c, r) in enumerate(zip(candidates, references)):
            test_results[i]["term_overlap"] = self._calculate_term_overlap(c, r)

        # Cosine similarity (sentence-transformers)
        if self.use_embeddings:
            logger.info("Loading embedding service for cosine similarity...")
            self._load_embedding_service()
            if self._embedding_service is not None:
                logger.info(f"Computing cosine similarity for {len(candidates)} pairs...")
                cosine_scores = self._calculate_cosine_similarity_batch(candidates, references)
                for i, score in enumerate(cosine_scores):
                    test_results[i]["cosine_similarity"] = score

        # BERTScore (per-item F1)
        if self.use_bertscore:
            self._load_bertscore()
            if self._bertscore_loaded:
                logger.info(f"Computing BERTScore F1 for {len(candidates)} pairs...")
                bert_scores = self._calculate_bertscore_per_item(candidates, references)
                for i, score in enumerate(bert_scores):
                    test_results[i]["bert_f1"] = score

        return test_results

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
