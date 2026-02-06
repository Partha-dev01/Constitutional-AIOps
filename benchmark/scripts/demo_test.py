#!/usr/bin/env python3
"""
Constitutional AIOps - Demo Benchmark Test (15+15 Debug)

30-sample test (15 annotation + 15 RCA) with detailed debug output.
Uses the actual FastAnnotator and ReasoningAgent classes
against the curated 150-sample benchmark (seed=42, English only).

Usage:
    python benchmark/scripts/demo_test.py
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables (optional - try to import dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # dotenv not installed, rely on shell environment

from src.benchmark.runner import BenchmarkRunner, BenchmarkConfig, BenchmarkStatus


async def run_demo_test():
    """Run a 15+15 demo test with detailed debug output."""
    print("=" * 70)
    print("CONSTITUTIONAL AIOPS - 15+15 DEBUG BENCHMARK TEST")
    print("=" * 70)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print(f"FAST_AGENT_URL: {os.getenv('FAST_AGENT_URL', 'not set')}")
    print(f"REASONING_AGENT_URL: {os.getenv('REASONING_AGENT_URL', 'not set')}")
    print(f"Dataset: curated 150-sample (seed=42, English only)")
    print("=" * 70)

    # Create config for 15+15 demo test
    config = BenchmarkConfig(
        model_name="constitutional_aiops",
        max_annotation_tests=15,
        max_rca_tests=15,
        temperature=0.0,
        timeout_seconds=300,
        calibrate_network=True,
        use_curated_150=True,  # Use curated 150-sample benchmark
    )

    runner = BenchmarkRunner()

    def progress_callback(task_type: str, current: int, total: int):
        print(f"   [{task_type.upper()}] {current}/{total}")

    try:
        print("\n[STARTING] 15+15 demo benchmark...")
        result = await runner.run_benchmark(config, progress_callback)

        print("\n" + "=" * 70)
        print("RESULTS SUMMARY")
        print("=" * 70)
        print(f"Status:              {result.status.value}")
        print(f"Total Tests:         {result.total_tests}")
        print(f"Passed:              {result.passed_tests}")
        print(f"Annotation Accuracy: {result.annotation_accuracy:.2f}%")
        print(f"RCA Accuracy:        {result.rca_accuracy:.2f}%")
        print(f"Avg Latency:         {result.avg_latency_ms:.2f}ms")
        print(f"P50 Latency:         {result.p50_latency_ms:.2f}ms")
        print(f"P95 Latency:         {result.p95_latency_ms:.2f}ms")
        print(f"Network RTT:         {result.network_rtt_ms:.2f}ms")
        print("=" * 70)

        if result.status == BenchmarkStatus.COMPLETED:
            # Split results by type
            ann_results = [tr for tr in result.test_results if tr.task_type == "annotation"]
            rca_results = [tr for tr in result.test_results if tr.task_type == "rca"]
            ann_passed = sum(1 for r in ann_results if r.correct)
            rca_passed = sum(1 for r in rca_results if r.correct)

            # Detailed annotation results
            print(f"\n--- ANNOTATION TESTS ({ann_passed}/{len(ann_results)} passed) ---")
            for tr in ann_results:
                status = "[PASS]" if tr.correct else "[FAIL]"
                print(f"\n   {status} {tr.test_id} ({tr.inference_latency_ms:.0f}ms)")
                print(f"         Expected: {tr.expected_output[:200]}")
                print(f"         Actual:   {tr.actual_output[:200]}")

            # Detailed RCA results
            print(f"\n--- RCA TESTS ({rca_passed}/{len(rca_results)} passed) ---")
            for tr in rca_results:
                status = "[PASS]" if tr.correct else "[FAIL]"
                print(f"\n   {status} {tr.test_id} ({tr.inference_latency_ms:.0f}ms)")
                print(f"         Expected: {tr.expected_output[:200]}")
                print(f"         Actual:   {tr.actual_output[:200]}")

            # Final score summary
            total_pct = result.passed_tests / max(result.total_tests, 1) * 100
            print("\n" + "=" * 70)
            print("SCORE SUMMARY")
            print("=" * 70)
            print(f"Annotation: {ann_passed}/{len(ann_results)} = {result.annotation_accuracy:.1f}%")
            print(f"RCA:        {rca_passed}/{len(rca_results)} = {result.rca_accuracy:.1f}%")
            print(f"Overall:    {result.passed_tests}/{result.total_tests} = {total_pct:.1f}%")
            print("=" * 70)

            return 0
        else:
            print(f"\n[FAILED] Demo test FAILED: {result.error}")
            return 1

    except Exception as e:
        print(f"\n[ERROR] Error running demo test: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Entry point."""
    return asyncio.run(run_demo_test())


if __name__ == "__main__":
    sys.exit(main())
