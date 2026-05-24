#!/usr/bin/env python3
"""
Constitutional AIOps - Benchmark Evaluator

Evaluates benchmark results using multiple metrics:
- Exact Match Accuracy
- BERTScore (semantic similarity)
- Partial Match Rate

Usage:
    python benchmark/scripts/eval/evaluate_results.py
    python benchmark/scripts/eval/evaluate_results.py --model constitutional_aiops
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

BENCHMARK_DIR = PROJECT_ROOT / "benchmark"
RESULTS_DIR = BENCHMARK_DIR / "results"

# Try to import BERTScore (optional dependency)
try:
    from bert_score import score as bert_score
    BERTSCORE_AVAILABLE = True
except ImportError:
    BERTSCORE_AVAILABLE = False
    print("⚠️ bert-score not installed. Run: pip install bert-score")


@dataclass
class EvaluationMetrics:
    """Evaluation metrics for a model."""
    model_name: str
    exact_match_accuracy: float
    partial_match_accuracy: float
    bert_precision: float
    bert_recall: float
    bert_f1: float
    annotation_accuracy: float
    rca_accuracy: float
    total_samples: int
    timestamp: str


class BenchmarkEvaluator:
    """
    Evaluates benchmark results using multiple metrics.
    """

    def __init__(self, use_bertscore: bool = True):
        self.use_bertscore = use_bertscore and BERTSCORE_AVAILABLE

    def load_results(self, model_name: str) -> list[dict]:
        """Load benchmark results for a model."""
        results_path = RESULTS_DIR / model_name / "results.json"

        if not results_path.exists():
            raise FileNotFoundError(f"Results not found: {results_path}")

        with open(results_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def calculate_exact_match(self, results: list[dict]) -> float:
        """Calculate exact match accuracy."""
        if not results:
            return 0.0

        correct = sum(1 for r in results if r.get("correct", False))
        return round(correct / len(results) * 100, 2)

    def calculate_partial_match(self, results: list[dict]) -> float:
        """
        Calculate partial match accuracy.
        A partial match is when the expected answer appears anywhere in the actual output.
        """
        if not results:
            return 0.0

        partial_correct = 0
        for r in results:
            expected = r.get("expected_output", "").lower()
            actual = r.get("actual_output", "").lower()

            # For annotation tasks, check JSON fields
            if r.get("task_type") == "annotation":
                try:
                    expected_dict = json.loads(expected)
                    # Check if key fields match
                    if expected_dict.get("anomaly_detected") and ("true" in actual or "anomaly" in actual):
                        partial_correct += 1
                    elif not expected_dict.get("anomaly_detected") and ("false" in actual or "normal" in actual):
                        partial_correct += 1
                except json.JSONDecodeError:
                    if expected in actual:
                        partial_correct += 1
            else:
                # For RCA tasks, check if any key term matches
                if any(term in actual for term in expected.split("_")):
                    partial_correct += 1

        return round(partial_correct / len(results) * 100, 2)

    def calculate_bertscore(self, results: list[dict]) -> dict[str, float]:
        """Calculate BERTScore for semantic similarity."""
        if not self.use_bertscore:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        candidates = [r.get("actual_output", "")[:512] for r in results]  # Truncate for BERT
        references = [r.get("expected_output", "")[:512] for r in results]

        # Filter out empty strings
        valid_pairs = [(c, r) for c, r in zip(candidates, references) if c and r]
        if not valid_pairs:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        candidates, references = zip(*valid_pairs)

        try:
            print(f"   📊 Calculating BERTScore for {len(candidates)} samples...")
            P, R, F1 = bert_score(
                list(candidates),
                list(references),
                model_type="microsoft/deberta-xlarge-mnli",
                lang="en",
                verbose=False,
            )

            return {
                "precision": round(P.mean().item(), 4),
                "recall": round(R.mean().item(), 4),
                "f1": round(F1.mean().item(), 4),
            }
        except Exception as e:
            print(f"   ⚠️ BERTScore calculation failed: {e}")
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    def evaluate_model(self, model_name: str) -> EvaluationMetrics:
        """Evaluate a single model's benchmark results."""
        print(f"\n📊 Evaluating: {model_name}")

        results = self.load_results(model_name)

        # Split by task type
        annotation_results = [r for r in results if r.get("task_type") == "annotation"]
        rca_results = [r for r in results if r.get("task_type") == "rca"]

        # Calculate metrics
        exact_match = self.calculate_exact_match(results)
        partial_match = self.calculate_partial_match(results)
        bert_scores = self.calculate_bertscore(results)

        annotation_correct = sum(1 for r in annotation_results if r.get("correct", False))
        rca_correct = sum(1 for r in rca_results if r.get("correct", False))

        metrics = EvaluationMetrics(
            model_name=model_name,
            exact_match_accuracy=exact_match,
            partial_match_accuracy=partial_match,
            bert_precision=bert_scores["precision"],
            bert_recall=bert_scores["recall"],
            bert_f1=bert_scores["f1"],
            annotation_accuracy=round(annotation_correct / len(annotation_results) * 100, 2) if annotation_results else 0,
            rca_accuracy=round(rca_correct / len(rca_results) * 100, 2) if rca_results else 0,
            total_samples=len(results),
            timestamp=datetime.utcnow().isoformat(),
        )

        # Save metrics
        self._save_metrics(model_name, metrics)

        return metrics

    def _save_metrics(self, model_name: str, metrics: EvaluationMetrics):
        """Save evaluation metrics."""
        output_path = RESULTS_DIR / model_name / "evaluation.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(metrics), f, indent=2)

        print(f"   💾 Saved: {output_path}")

    def evaluate_all(self) -> list[EvaluationMetrics]:
        """Evaluate all models with benchmark results."""
        all_metrics = []

        for model_dir in RESULTS_DIR.iterdir():
            if model_dir.is_dir() and (model_dir / "results.json").exists():
                try:
                    metrics = self.evaluate_model(model_dir.name)
                    all_metrics.append(metrics)
                except Exception as e:
                    print(f"   ⚠️ Failed to evaluate {model_dir.name}: {e}")

        # Save combined evaluation
        combined_path = RESULTS_DIR / "evaluation_summary.json"
        with open(combined_path, "w", encoding="utf-8") as f:
            json.dump([asdict(m) for m in all_metrics], f, indent=2)

        # Print summary
        print("\n" + "=" * 100)
        print("EVALUATION SUMMARY")
        print("=" * 100)
        print(f"{'Model':<25} {'Exact':>10} {'Partial':>10} {'BERT-F1':>10} {'Ann.':>10} {'RCA':>10}")
        print("-" * 100)
        for m in all_metrics:
            print(f"{m.model_name:<25} {m.exact_match_accuracy:>9.1f}% {m.partial_match_accuracy:>9.1f}% {m.bert_f1:>10.4f} {m.annotation_accuracy:>9.1f}% {m.rca_accuracy:>9.1f}%")
        print("=" * 100)

        return all_metrics


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Evaluate benchmark results")
    parser.add_argument("--model", "-m", help="Evaluate specific model only")
    parser.add_argument("--no-bertscore", action="store_true", help="Skip BERTScore calculation")
    args = parser.parse_args()

    evaluator = BenchmarkEvaluator(use_bertscore=not args.no_bertscore)

    if args.model:
        evaluator.evaluate_model(args.model)
    else:
        evaluator.evaluate_all()

    return 0


if __name__ == "__main__":
    sys.exit(main())
