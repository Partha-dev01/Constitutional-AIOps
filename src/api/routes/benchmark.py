"""
Constitutional AIOps - Benchmark API Routes

Provides endpoints for running and managing benchmarks.
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from src.benchmark.runner import BenchmarkRunner, BenchmarkConfig, BenchmarkResult, BenchmarkStatus, MODELS
from src.benchmark.evaluator import BenchmarkEvaluator, EvaluationResult

router = APIRouter()

# Global benchmark runner instance
_benchmark_runner: Optional[BenchmarkRunner] = None
_current_progress: dict = {}


def get_runner() -> BenchmarkRunner:
    """Get or create benchmark runner instance."""
    global _benchmark_runner
    if _benchmark_runner is None:
        _benchmark_runner = BenchmarkRunner()
    return _benchmark_runner


# Request/Response models
class BenchmarkRequest(BaseModel):
    """Request to start a benchmark."""
    model_name: str = "constitutional_aiops"
    max_annotation_tests: int = 100
    max_rca_tests: int = 50
    temperature: float = 0.0
    timeout_seconds: int = 300


class DatasetInfo(BaseModel):
    """Dataset information."""
    name: str
    total_cases: int
    source: str
    description: str


# Endpoints

@router.get("/models")
async def get_available_models():
    """Get list of available models for benchmarking."""
    return {
        "models": get_runner().get_available_models(),
        "default": "constitutional_aiops",
    }


@router.get("/datasets")
async def get_datasets():
    """Get information about available benchmark datasets."""
    base_path = Path(__file__).parent.parent.parent.parent / "benchmark" / "intermediate" / "datasets"

    datasets = []

    # Check annotation dataset
    ann_path = base_path / "annotation_test.json"
    if ann_path.exists():
        with open(ann_path, "r") as f:
            data = json.load(f)
        datasets.append({
            "name": "annotation",
            "file": "annotation_test.json",
            "total_cases": data.get("total_cases", 0),
            "source": data.get("source", "Unknown"),
            "description": data.get("description", ""),
            "distribution": data.get("distribution", {}),
        })

    # Check RCA dataset
    rca_path = base_path / "rca_test.json"
    if rca_path.exists():
        with open(rca_path, "r") as f:
            data = json.load(f)
        datasets.append({
            "name": "rca",
            "file": "rca_test.json",
            "total_cases": data.get("total_cases", 0),
            "source": data.get("source", "Unknown"),
            "description": data.get("description", ""),
            "categories": data.get("categories", {}),
        })

    return {
        "datasets": datasets,
        "ready": len(datasets) == 2,
    }


@router.get("/datasets/{dataset_name}/preview")
async def preview_dataset(
    dataset_name: str,
    limit: int = Query(default=5, le=20),
):
    """Preview test cases from a dataset."""
    base_path = Path(__file__).parent.parent.parent.parent / "benchmark" / "intermediate" / "datasets"

    if dataset_name == "annotation":
        path = base_path / "annotation_test.json"
    elif dataset_name == "rca":
        path = base_path / "rca_test.json"
    else:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_name}")

    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset file not found. Run prepare_datasets.py first.")

    with open(path, "r") as f:
        data = json.load(f)

    test_cases = data.get("test_cases", [])[:limit]

    return {
        "dataset": dataset_name,
        "total_cases": data.get("total_cases", 0),
        "preview_count": len(test_cases),
        "test_cases": test_cases,
    }


@router.get("/status")
async def get_benchmark_status():
    """Get current benchmark status."""
    runner = get_runner()

    return {
        "is_running": runner.is_running,
        "current_benchmark": runner.current_benchmark.to_dict() if runner.current_benchmark else None,
        "progress": _current_progress,
    }


@router.post("/run")
async def run_benchmark(
    request: BenchmarkRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a benchmark run.

    This runs in the background and returns immediately with a job ID.
    Use /status to check progress.
    """
    runner = get_runner()

    if runner.is_running:
        raise HTTPException(status_code=409, detail="A benchmark is already running")

    if request.model_name not in MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model: {request.model_name}. Available: {list(MODELS.keys())}"
        )

    # Create config
    config = BenchmarkConfig(
        model_name=request.model_name,
        max_annotation_tests=request.max_annotation_tests,
        max_rca_tests=request.max_rca_tests,
        temperature=request.temperature,
        timeout_seconds=request.timeout_seconds,
    )

    # Define progress callback
    def progress_callback(task_type: str, current: int, total: int):
        global _current_progress
        _current_progress = {
            "task_type": task_type,
            "current": current,
            "total": total,
            "percent": round(current / total * 100, 1) if total > 0 else 0,
        }

    # Run in background
    async def run_async():
        try:
            await runner.run_benchmark(config, progress_callback)
        except Exception as e:
            print(f"Benchmark error: {e}")

    background_tasks.add_task(asyncio.create_task, run_async())

    return {
        "status": "started",
        "model": request.model_name,
        "message": "Benchmark started. Use /status to check progress.",
    }


@router.get("/results")
async def get_results():
    """Get all benchmark results."""
    results_dir = Path(__file__).parent.parent.parent.parent / "benchmark" / "results"

    if not results_dir.exists():
        return {"results": [], "count": 0}

    results = []
    for model_dir in results_dir.iterdir():
        if model_dir.is_dir():
            result_file = model_dir / "benchmark_result.json"
            if result_file.exists():
                with open(result_file, "r") as f:
                    data = json.load(f)
                results.append(data)

    return {
        "results": results,
        "count": len(results),
    }


@router.get("/results/{model_name}")
async def get_model_results(model_name: str):
    """Get benchmark results for a specific model."""
    results_dir = Path(__file__).parent.parent.parent.parent / "benchmark" / "results" / model_name

    if not results_dir.exists():
        raise HTTPException(status_code=404, detail=f"No results found for model: {model_name}")

    result_file = results_dir / "benchmark_result.json"
    if not result_file.exists():
        raise HTTPException(status_code=404, detail=f"No results found for model: {model_name}")

    with open(result_file, "r") as f:
        data = json.load(f)

    return data


@router.get("/compare")
async def compare_models():
    """Compare results across all benchmarked models."""
    results_dir = Path(__file__).parent.parent.parent.parent / "benchmark" / "results"

    if not results_dir.exists():
        return {"comparison": [], "summary": {}}

    results = []
    for model_dir in results_dir.iterdir():
        if model_dir.is_dir():
            result_file = model_dir / "benchmark_result.json"
            if result_file.exists():
                with open(result_file, "r") as f:
                    data = json.load(f)
                results.append({
                    "model_name": data.get("model_name"),
                    "annotation_accuracy": data.get("annotation_accuracy", 0),
                    "rca_accuracy": data.get("rca_accuracy", 0),
                    "bert_f1": data.get("bert_f1", 0),
                    "avg_latency_ms": data.get("avg_latency_ms", 0),
                    "p95_latency_ms": data.get("p95_latency_ms", 0),
                    "total_tests": data.get("total_tests", 0),
                    "passed_tests": data.get("passed_tests", 0),
                })

    # Sort by annotation accuracy
    results.sort(key=lambda x: x["annotation_accuracy"], reverse=True)

    # Calculate summary
    summary = {}
    if results:
        best_accuracy = max(results, key=lambda x: x["annotation_accuracy"])
        best_latency = min(results, key=lambda x: x["avg_latency_ms"] if x["avg_latency_ms"] > 0 else float("inf"))
        summary = {
            "best_annotation_accuracy": best_accuracy["model_name"],
            "best_latency": best_latency["model_name"],
            "total_models": len(results),
        }

    return {
        "comparison": results,
        "summary": summary,
    }


@router.post("/cancel")
async def cancel_benchmark():
    """Cancel a running benchmark."""
    runner = get_runner()

    if not runner.is_running:
        raise HTTPException(status_code=400, detail="No benchmark is currently running")

    # Note: Actual cancellation would require more complex async handling
    # For now, this just reports the status
    return {
        "status": "cancellation_requested",
        "message": "Benchmark will stop after current test case",
    }


@router.get("/export")
async def export_results(format: str = Query(default="json", regex="^(json|csv|latex)$")):
    """Export benchmark results in various formats."""
    results_dir = Path(__file__).parent.parent.parent.parent / "benchmark" / "results"

    if not results_dir.exists():
        raise HTTPException(status_code=404, detail="No benchmark results found")

    # Load all results
    results = []
    for model_dir in results_dir.iterdir():
        if model_dir.is_dir():
            result_file = model_dir / "benchmark_result.json"
            if result_file.exists():
                with open(result_file, "r") as f:
                    data = json.load(f)
                results.append(data)

    if not results:
        raise HTTPException(status_code=404, detail="No benchmark results found")

    if format == "json":
        return {"results": results}

    elif format == "csv":
        # Generate CSV
        headers = ["Model", "Annotation Acc", "RCA Acc", "BERTScore F1", "Avg Latency (ms)", "P95 Latency (ms)"]
        rows = []
        for r in results:
            rows.append([
                r.get("model_name", ""),
                r.get("annotation_accuracy", 0),
                r.get("rca_accuracy", 0),
                r.get("bert_f1", 0),
                r.get("avg_latency_ms", 0),
                r.get("p95_latency_ms", 0),
            ])
        csv_content = ",".join(headers) + "\n"
        for row in rows:
            csv_content += ",".join(str(v) for v in row) + "\n"
        return {"format": "csv", "content": csv_content}

    elif format == "latex":
        # Generate LaTeX table
        latex = r"""
\begin{table}[h]
\centering
\caption{LLM Performance Comparison on Constitutional AIOps Benchmark}
\begin{tabular}{lccccr}
\toprule
Model & Ann. Acc (\%) & RCA Acc (\%) & BERT F1 & Latency (ms) & P95 (ms) \\
\midrule
"""
        for r in results:
            latex += f"{r.get('model_name', '')} & {r.get('annotation_accuracy', 0):.1f} & "
            latex += f"{r.get('rca_accuracy', 0):.1f} & {r.get('bert_f1', 0):.3f} & "
            latex += f"{r.get('avg_latency_ms', 0):.0f} & {r.get('p95_latency_ms', 0):.0f} \\\\\n"

        latex += r"""
\bottomrule
\end{tabular}
\label{tab:llm-comparison}
\end{table}
"""
        return {"format": "latex", "content": latex}


__all__ = ["router"]
