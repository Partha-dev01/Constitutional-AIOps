"""
Constitutional AIOps - Metrics API Routes

Endpoints for retrieving and exporting system metrics, latency data,
and validation results. Used for research paper benchmarking and
operational monitoring.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Models
# =============================================================================


class LatencyStats(BaseModel):
    """Latency statistics for an agent."""
    count: int
    avg_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    success_rate: float
    total_tokens: int = 0


class MetricsSnapshot(BaseModel):
    """Complete metrics snapshot."""
    timestamp: str
    fast_agent: LatencyStats
    reasoning_agent: LatencyStats
    total_requests: int
    success_rate: float
    determinism_config: dict = Field(
        default_factory=lambda: {
            "fast_agent_temperature": 0.0,
            "reasoning_agent_temperature": 0.0,
            "chat_temperature": 0.5,
            "seed_method": "hash(prompt) % 2^32",
        }
    )


class LatencyRecord(BaseModel):
    """Single latency record."""
    agent: str
    latency_ms: float
    timestamp: str
    tokens_generated: int = 0
    success: bool = True


class BenchmarkRequest(BaseModel):
    """Request to run a benchmark."""
    agent: str = Field(..., description="Agent to benchmark: 'fast' or 'reasoning'")
    iterations: int = Field(default=10, ge=1, le=100, description="Number of iterations")
    prompt: str = Field(
        default="Classify this log: ERROR Connection timeout",
        description="Test prompt to use"
    )


class ValidationRequest(BaseModel):
    """Request to run validation."""
    validation_type: str = Field(
        ..., description="Type: 'determinism', 'annotation', 'rca'"
    )
    iterations: int = Field(default=5, ge=1, le=20)
    prompts: list[str] = Field(default_factory=list)


# =============================================================================
# Metrics Endpoints
# =============================================================================


@router.get(
    "",
    response_model=MetricsSnapshot,
    summary="Get Metrics Snapshot",
    description="Get current metrics snapshot including latency stats for both agents",
)
async def get_metrics(request: Request) -> MetricsSnapshot:
    """
    Get current system metrics snapshot.

    Returns latency statistics for:
    - Fast Agent (Qwen3-4B)
    - Reasoning Agent (Qwen3-14B)

    Plus overall success rate and configuration.
    """
    model_router = getattr(request.app.state, "model_router", None)
    if model_router is None:
        raise HTTPException(status_code=503, detail="ModelRouter not initialized")

    snapshot = model_router.get_metrics_snapshot()

    return MetricsSnapshot(
        timestamp=snapshot.timestamp,
        fast_agent=LatencyStats(**snapshot.fast_agent),
        reasoning_agent=LatencyStats(**snapshot.reasoning_agent),
        total_requests=snapshot.total_requests,
        success_rate=snapshot.success_rate,
    )


@router.get(
    "/latency",
    summary="Get Latency Statistics",
    description="Get latency statistics optionally filtered by agent",
)
async def get_latency_stats(
    request: Request,
    agent: Optional[str] = Query(None, description="Filter by agent: 'fast' or 'reasoning'"),
) -> dict[str, Any]:
    """
    Get latency statistics.

    Args:
        agent: Optional filter - 'fast' or 'reasoning'

    Returns:
        Latency statistics with percentiles
    """
    model_router = getattr(request.app.state, "model_router", None)
    if model_router is None:
        raise HTTPException(status_code=503, detail="ModelRouter not initialized")

    if agent and agent not in ("fast", "reasoning"):
        raise HTTPException(
            status_code=400,
            detail="Invalid agent. Use 'fast' or 'reasoning'"
        )

    stats = model_router.get_latency_stats(agent)
    return {
        "agent": agent or "all",
        "stats": stats,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/history",
    summary="Get Latency History",
    description="Get recent latency records for detailed analysis",
)
async def get_latency_history(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000, description="Number of records"),
    agent: Optional[str] = Query(None, description="Filter by agent"),
) -> dict[str, Any]:
    """
    Get recent latency records.

    Args:
        limit: Maximum number of records to return
        agent: Optional filter by agent type

    Returns:
        List of recent latency records
    """
    model_router = getattr(request.app.state, "model_router", None)
    if model_router is None:
        raise HTTPException(status_code=503, detail="ModelRouter not initialized")

    history = model_router.get_latency_history(limit)

    if agent:
        history = [r for r in history if r["agent"] == agent]

    return {
        "count": len(history),
        "records": history,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/export",
    summary="Export Metrics",
    description="Export metrics in JSON or CSV format",
)
async def export_metrics(
    request: Request,
    format: str = Query(default="json", description="Export format: 'json' or 'csv'"),
) -> Response:
    """
    Export metrics in specified format.

    Args:
        format: 'json' or 'csv'

    Returns:
        Metrics data as file download
    """
    model_router = getattr(request.app.state, "model_router", None)
    if model_router is None:
        raise HTTPException(status_code=503, detail="ModelRouter not initialized")

    if format not in ("json", "csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Use 'json' or 'csv'"
        )

    try:
        data = model_router.export_metrics(format)
        media_type = "application/json" if format == "json" else "text/csv"
        filename = f"metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}"

        return Response(
            content=data,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/clear",
    summary="Clear Metrics",
    description="Clear all latency history",
)
async def clear_metrics(request: Request) -> dict[str, str]:
    """Clear all metrics history."""
    model_router = getattr(request.app.state, "model_router", None)
    if model_router is None:
        raise HTTPException(status_code=503, detail="ModelRouter not initialized")

    model_router.clear_metrics()
    return {"status": "cleared", "timestamp": datetime.utcnow().isoformat()}


# =============================================================================
# Benchmark Endpoints
# =============================================================================


@router.post(
    "/benchmark",
    summary="Run Benchmark",
    description="Run a latency benchmark on specified agent",
)
async def run_benchmark(
    request: Request,
    benchmark: BenchmarkRequest,
) -> dict[str, Any]:
    """
    Run a latency benchmark.

    Args:
        benchmark: Benchmark configuration

    Returns:
        Benchmark results with latency statistics
    """
    model_router = getattr(request.app.state, "model_router", None)
    if model_router is None:
        raise HTTPException(status_code=503, detail="ModelRouter not initialized")

    import time
    latencies: list[float] = []
    successes = 0
    errors: list[str] = []

    # Select completion function based on agent
    if benchmark.agent == "fast":
        completion_func = model_router.fast_completion
    elif benchmark.agent == "reasoning":
        completion_func = model_router.reasoning_completion
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid agent. Use 'fast' or 'reasoning'"
        )

    start_time = time.perf_counter()

    for i in range(benchmark.iterations):
        try:
            result = await completion_func(benchmark.prompt)
            latency = result.get("_latency_ms", 0)
            latencies.append(latency)
            successes += 1
        except Exception as e:
            logger.error(f"Benchmark iteration {i} failed: {e}")
            errors.append(str(e))

    total_time = (time.perf_counter() - start_time) * 1000

    if not latencies:
        return {
            "status": "failed",
            "agent": benchmark.agent,
            "iterations": benchmark.iterations,
            "successes": 0,
            "errors": errors[:5],
        }

    sorted_latencies = sorted(latencies)

    def percentile(data: list, p: float) -> float:
        if not data:
            return 0
        k = (len(data) - 1) * p / 100
        f = int(k)
        c = f + 1 if f + 1 < len(data) else f
        return data[f] + (k - f) * (data[c] - data[f]) if c != f else data[f]

    return {
        "status": "completed",
        "agent": benchmark.agent,
        "iterations": benchmark.iterations,
        "successes": successes,
        "total_time_ms": round(total_time, 2),
        "latency": {
            "avg_ms": round(sum(latencies) / len(latencies), 2),
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
            "p50_ms": round(percentile(sorted_latencies, 50), 2),
            "p95_ms": round(percentile(sorted_latencies, 95), 2),
            "p99_ms": round(percentile(sorted_latencies, 99), 2),
        },
        "success_rate": round(successes / benchmark.iterations * 100, 2),
        "errors": errors[:5] if errors else [],
        "timestamp": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Validation Endpoints
# =============================================================================


@router.post(
    "/validate/determinism",
    summary="Validate Determinism",
    description="Test output determinism with temperature=0",
)
async def validate_determinism(
    request: Request,
    iterations: int = Query(default=5, ge=2, le=10),
    prompts: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Validate output determinism.

    With temperature=0.0 and fixed seed, same input should produce same output.

    Args:
        iterations: Number of times to run each prompt
        prompts: Test prompts (default: standard classification prompts)

    Returns:
        Determinism score and consistency details
    """
    model_router = getattr(request.app.state, "model_router", None)
    if model_router is None:
        raise HTTPException(status_code=503, detail="ModelRouter not initialized")

    # Default test prompts
    if not prompts:
        prompts = [
            "Classify this log: ERROR Connection timeout to database",
            "Classify this log: WARN High memory usage detected",
            "Classify this log: INFO Request completed successfully",
        ]

    results: list[dict] = []

    for prompt in prompts:
        outputs: list[str] = []
        seeds: list[int] = []

        for _ in range(iterations):
            try:
                result = await model_router.fast_completion(prompt)
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                outputs.append(content)
                seeds.append(result.get("_seed", 0))
            except Exception as e:
                logger.error(f"Determinism test failed: {e}")
                outputs.append(f"ERROR: {e}")

        unique_outputs = len(set(outputs))
        unique_seeds = len(set(seeds))

        results.append({
            "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
            "iterations": iterations,
            "unique_outputs": unique_outputs,
            "unique_seeds": unique_seeds,
            "is_deterministic": unique_outputs == 1,
            "sample_output": outputs[0][:100] if outputs else "",
        })

    deterministic_count = sum(1 for r in results if r["is_deterministic"])
    determinism_score = deterministic_count / len(results) if results else 0

    return {
        "determinism_score": round(determinism_score * 100, 2),
        "deterministic_prompts": deterministic_count,
        "total_prompts": len(results),
        "iterations_per_prompt": iterations,
        "configuration": {
            "temperature": 0.0,
            "seed_method": "hash(prompt) % 2^32",
        },
        "results": results,
        "passed": determinism_score >= 0.95,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/validation/report",
    summary="Get Validation Report",
    description="Get comprehensive validation report for research documentation",
)
async def get_validation_report(request: Request) -> dict[str, Any]:
    """
    Get comprehensive validation report.

    Includes:
    - Latency statistics
    - Determinism configuration
    - System configuration
    - Disclaimers for unvalidated metrics

    Returns:
        Complete validation report
    """
    model_router = getattr(request.app.state, "model_router", None)
    if model_router is None:
        raise HTTPException(status_code=503, detail="ModelRouter not initialized")

    from src.config import config

    snapshot = model_router.get_metrics_snapshot()

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "system_configuration": {
            "fast_agent": {
                "model": config.llm.fast_agent_model,
                "url": config.llm.fast_agent_url,
                "temperature": 0.0,
                "purpose": "Telemetry annotation, classification",
            },
            "reasoning_agent": {
                "model": config.llm.reasoning_agent_model,
                "url": config.llm.reasoning_agent_url,
                "temperature": 0.0,
                "purpose": "RCA, remediation planning",
            },
            "chat_mode": {
                "temperature": 0.5,
                "purpose": "Human interaction (non-deterministic)",
            },
        },
        "latency_metrics": {
            "fast_agent": snapshot.fast_agent,
            "reasoning_agent": snapshot.reasoning_agent,
            "disclaimer": (
                "Latency measured client-side via time.perf_counter(). "
                "Includes network overhead. Run benchmark for controlled measurements."
            ),
        },
        "determinism_configuration": {
            "temperature": 0.0,
            "seed_method": "hash(prompt) % 2^32",
            "expected_behavior": "Same input + same seed = same output",
            "note": "Chat mode intentionally uses temperature=0.5 for natural variation",
        },
        "accuracy_metrics": {
            "annotation_accuracy": {
                "value": "Pending validation",
                "expected": "85-95% based on similar systems",
                "disclaimer": "Requires labeled test dataset for validation",
            },
            "rca_accuracy": {
                "value": "Pending validation",
                "expected": "80-90% based on preliminary testing",
                "disclaimer": "Requires human-labeled ground truth for validation",
            },
        },
        "validation_status": {
            "latency": "Measured" if snapshot.total_requests > 0 else "No data",
            "determinism": "Configured (run /validate/determinism to verify)",
            "annotation_accuracy": "Pending",
            "rca_accuracy": "Pending",
        },
        "methodology": {
            "latency": "Client-side timing via time.perf_counter()",
            "determinism": "Multiple iterations with same input, compare outputs",
            "accuracy": "Comparison against labeled test dataset (pending)",
        },
    }


__all__ = ["router"]
