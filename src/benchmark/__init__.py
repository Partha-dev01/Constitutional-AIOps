"""
Constitutional AIOps - Benchmark Module

Provides benchmarking infrastructure for evaluating LLM performance
on AIOps tasks including log annotation and root cause analysis.

Components:
- runner.py: Main benchmark execution engine
- evaluator.py: Metrics calculation (BERTScore, accuracy)

Usage:
    from src.benchmark import BenchmarkRunner, BenchmarkEvaluator

    runner = BenchmarkRunner()
    results = await runner.run_benchmark("constitutional_aiops")

    evaluator = BenchmarkEvaluator()
    metrics = evaluator.calculate_metrics(results)
"""

from src.benchmark.runner import BenchmarkRunner, BenchmarkConfig
from src.benchmark.evaluator import BenchmarkEvaluator, EvaluationResult

__all__ = [
    "BenchmarkRunner",
    "BenchmarkConfig",
    "BenchmarkEvaluator",
    "EvaluationResult",
]
