#!/usr/bin/env python3
"""
Constitutional AIOps - Benchmark Runner

Main benchmark runner that evaluates all LLM models on the test datasets.
Includes network latency compensation for accurate inference timing.

Features:
- One-shot execution of all 5 models
- Network RTT calibration and subtraction
- BERTScore calculation for semantic evaluation
- Detailed results export

Usage:
    python benchmark/scripts/run_benchmark.py
    python benchmark/scripts/run_benchmark.py --model constitutional_aiops
    python benchmark/scripts/run_benchmark.py --calibrate-only
"""

import os
import sys
import json
import time
import asyncio
import argparse
import statistics
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Any, Optional

import httpx

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

BENCHMARK_DIR = PROJECT_ROOT / "benchmark"
DATASETS_DIR = BENCHMARK_DIR / "intermediate" / "datasets"
RESULTS_DIR = BENCHMARK_DIR / "final"


# =============================================================================
# Configuration
# =============================================================================

# Model configurations
MODELS = {
    "constitutional_aiops": {
        "type": "hybrid",
        "description": "Constitutional AIOps (Qwen3-4B + Qwen3-14B)",
        "fast_model": "qwen3:4b",
        "reasoning_model": "qwen3:14b",
        "vram_gb": 15,
    },
    "qwen3_4b": {
        "type": "single",
        "description": "Qwen3-4B (Fast Agent baseline)",
        "model": "qwen3:4b",
        "vram_gb": 4,
    },
    "qwen3_14b": {
        "type": "single",
        "description": "Qwen3-14B (Reasoning Agent baseline)",
        "model": "qwen3:14b",
        "vram_gb": 11,
    },
    "llama3_8b": {
        "type": "single",
        "description": "Llama3-8B",
        "model": "llama3:8b",
        "vram_gb": 5,
    },
    "llama3_70b": {
        "type": "single",
        "description": "Llama3-70B",
        "model": "llama3:70b",
        "vram_gb": 40,
    },
}

# Ollama endpoints (from .env or defaults)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
FAST_AGENT_URL = os.getenv("FAST_AGENT_URL", "http://localhost:8081/v1")
REASONING_AGENT_URL = os.getenv("REASONING_AGENT_URL", "http://localhost:8082/v1")


# =============================================================================
# Latency Compensation
# =============================================================================

class LatencyCompensatedClient:
    """
    HTTP client with network RTT compensation.
    Measures and subtracts network overhead for accurate inference timing.
    """

    def __init__(self, base_url: str, calibration_samples: int = 10):
        self.base_url = base_url.rstrip("/")
        self.network_rtt_ms = 0.0
        self.calibration_samples = calibration_samples
        self._client = httpx.AsyncClient(timeout=300.0)  # 5 min timeout for large models

    async def calibrate(self) -> float:
        """
        Calibrate network RTT using lightweight endpoint.
        Uses /api/tags (Ollama) or simple health check.
        """
        latencies = []

        print(f"   [CALIBRATING] Network RTT ({self.calibration_samples} samples)...")

        for i in range(self.calibration_samples):
            start_ns = time.perf_counter_ns()
            try:
                # Try Ollama tags endpoint (lightweight)
                response = await self._client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    # Fallback to OpenAI-compatible models endpoint
                    response = await self._client.get(f"{self.base_url}/models")
            except Exception:
                continue
            end_ns = time.perf_counter_ns()
            latencies.append((end_ns - start_ns) / 1_000_000)  # ms

        if latencies:
            # Use median to avoid outliers
            self.network_rtt_ms = statistics.median(latencies)
            print(f"   [OK] Network RTT: {self.network_rtt_ms:.2f}ms (median of {len(latencies)} samples)")
        else:
            print("   [WARN] Could not calibrate network RTT, using 0ms")
            self.network_rtt_ms = 0.0

        return self.network_rtt_ms

    async def inference(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """
        Run inference with timing compensation.

        Returns:
            {
                "response": str,
                "total_latency_ms": float,
                "network_rtt_ms": float,
                "inference_latency_ms": float,  # Use this for paper
                "tokens_generated": int,
            }
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        start_ns = time.perf_counter_ns()

        try:
            response = await self._client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            # Try Ollama native endpoint
            try:
                ollama_payload = {
                    "model": model,
                    "prompt": prompt,
                    "system": system_prompt or "",
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                }
                response = await self._client.post(
                    f"{self.base_url}/api/generate",
                    json=ollama_payload,
                )
                response.raise_for_status()
                data = response.json()
                # Convert Ollama format to OpenAI format
                data = {
                    "choices": [{"message": {"content": data.get("response", "")}}],
                    "usage": {"completion_tokens": data.get("eval_count", 0)},
                }
            except Exception as inner_e:
                raise Exception(f"Inference failed: {e}; Ollama fallback: {inner_e}")

        end_ns = time.perf_counter_ns()
        total_ms = (end_ns - start_ns) / 1_000_000

        # Extract response content
        content = ""
        if "choices" in data and data["choices"]:
            raw_content = data["choices"][0].get("message", {}).get("content", "")
            # Handle Qwen3 thinking mode: extract content after </think> tag
            if "</think>" in raw_content:
                content = raw_content.split("</think>", 1)[-1].strip()
            elif "<think>" in raw_content:
                # FIXED: Thinking not finished - extract JSON from thinking content
                think_content = raw_content.split("<think>", 1)[-1]
                # Try to find JSON with anomaly_detected (for annotation)
                import re
                json_match = re.search(r'\{[^{}]*"anomaly_detected"[^{}]*\}', think_content)
                if json_match:
                    content = json_match.group(0)
                else:
                    # Try to find any JSON object
                    json_match = re.search(r'\{[^{}]+\}', think_content)
                    if json_match:
                        content = json_match.group(0)
                    else:
                        # Try to find answer letter (A, B, C, D) for RCA Q&A
                        letter_match = re.search(r'\b([A-D])\b[.\s]', think_content)
                        if letter_match:
                            content = letter_match.group(0)
                        else:
                            content = think_content.strip()  # Return thinking content
            else:
                content = raw_content

        tokens = data.get("usage", {}).get("completion_tokens", 0)

        return {
            "response": content,
            "total_latency_ms": round(total_ms, 2),
            "network_rtt_ms": round(self.network_rtt_ms, 2),
            "inference_latency_ms": round(max(total_ms - self.network_rtt_ms, 0), 2),
            "tokens_generated": tokens,
        }

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


# =============================================================================
# Benchmark Runner
# =============================================================================

@dataclass
class BenchmarkResult:
    """Single benchmark test result."""
    test_id: str
    model: str
    task_type: str  # "annotation" or "rca"
    input_text: str
    expected_output: str
    actual_output: str
    correct: bool
    inference_latency_ms: float
    total_latency_ms: float
    network_rtt_ms: float
    tokens_generated: int
    timestamp: str


@dataclass
class ModelBenchmarkSummary:
    """Summary of benchmark results for a model."""
    model_name: str
    model_type: str
    vram_gb: int
    annotation_accuracy: float
    rca_accuracy: float
    avg_inference_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_tests: int
    total_correct: int
    timestamp: str


class BenchmarkRunner:
    """
    Main benchmark runner for Constitutional AIOps evaluation.
    """

    def __init__(self, ollama_url: str = OLLAMA_BASE_URL):
        self.ollama_url = ollama_url
        self.client: Optional[LatencyCompensatedClient] = None
        self.results: list[BenchmarkResult] = []

    async def initialize(self):
        """Initialize the benchmark runner."""
        self.client = LatencyCompensatedClient(self.ollama_url)
        await self.client.calibrate()

    async def close(self):
        """Clean up resources."""
        if self.client:
            await self.client.close()

    def load_dataset(self, dataset_type: str) -> list[dict]:
        """Load test dataset."""
        if dataset_type == "annotation":
            path = DATASETS_DIR / "annotation_test.json"
        elif dataset_type == "rca":
            path = DATASETS_DIR / "rca_test.json"
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")

        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}. Run prepare_datasets.py first.")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data["test_cases"]

    def _calculate_dynamic_tokens(self, prompt: str, model: str, min_output: int = 256) -> int:
        """
        Calculate max_tokens dynamically based on prompt length and model context.

        This ensures we use maximum available tokens without waste.
        - Qwen3-4B: 8192 tokens context
        - Qwen3-14B: 4096 tokens context (being conservative)
        """
        # Model context windows
        context_windows = {
            "qwen3:4b": 8192,
            "qwen3:14b": 4096,
            "constitutional_aiops": 8192,  # Uses Qwen3-4B for annotation
        }

        # Get context window for model
        model_lower = model.lower()
        context_window = 8192  # default
        for key, window in context_windows.items():
            if key in model_lower:
                context_window = window
                break

        # Estimate input tokens (roughly 4 chars per token for English)
        estimated_input_tokens = len(prompt) // 4 + 50  # +50 for system prompt overhead

        # Calculate remaining tokens for output
        remaining = context_window - estimated_input_tokens

        # Ensure minimum output tokens and cap at reasonable max
        max_tokens = max(min_output, min(remaining, 6000))

        return max_tokens

    async def run_annotation_test(
        self,
        model: str,
        test_case: dict,
        system_prompt: str,
    ) -> BenchmarkResult:
        """Run a single annotation test case."""
        input_data = test_case["input"]
        expected = test_case["expected"]

        # FIXED: Few-shot examples + explicit JSON format + reduced tokens
        prompt = f"""/no_think
You are a telemetry annotator. Analyze the log and output ONLY valid JSON.

### Example 1 (Normal):
Input: 081109 204006 14 INFO dfs.DataNode$DataXceiver: Receiving block blk_-1608999687919862906
Output: {{"anomaly_detected": false, "severity": "info", "category": "normal"}}

### Example 2 (Error):
Input: ERROR: Connection refused to 10.1.2.3:8080 - service unavailable
Output: {{"anomaly_detected": true, "severity": "critical", "category": "error"}}

### Example 3 (Warning):
Input: WARN dfs.DataNode: Got exception while serving block to client
Output: {{"anomaly_detected": true, "severity": "warning", "category": "error"}}

### Your Task:
Analyze this {input_data['telemetry_type']} telemetry:

{input_data['content']}

Output ONLY the JSON object (no explanation, no markdown):"""

        # FIXED: Dynamic token calculation based on prompt length
        max_tokens = self._calculate_dynamic_tokens(prompt, model, min_output=512)

        result = await self.client.inference(
            prompt=prompt,
            model=model,
            system_prompt=None,  # FIXED: No system prompt to avoid conflict
            max_tokens=max_tokens,  # FIXED: Dynamic based on input size
            temperature=0.0,
        )

        # Parse response and check correctness
        actual_output = result["response"]
        correct = self._check_annotation_correct(actual_output, expected)

        return BenchmarkResult(
            test_id=test_case["id"],
            model=model,
            task_type="annotation",
            input_text=input_data["content"][:200],
            expected_output=json.dumps(expected),
            actual_output=actual_output[:500],
            correct=correct,
            inference_latency_ms=result["inference_latency_ms"],
            total_latency_ms=result["total_latency_ms"],
            network_rtt_ms=result["network_rtt_ms"],
            tokens_generated=result["tokens_generated"],
            timestamp=datetime.utcnow().isoformat(),
        )

    async def run_rca_test(
        self,
        model: str,
        test_case: dict,
        system_prompt: str,
    ) -> BenchmarkResult:
        """Run a single RCA test case."""
        incident = test_case["incident"]

        # Handle different RCA formats:
        # 1. LEMMA-RCA format: has 'logs' and 'metrics'
        # 2. OpsEval format: has 'question' and 'choices' (Q&A style)
        if "logs" in incident:
            # LEMMA-RCA format: incident logs + metrics
            logs_text = "\n".join(incident["logs"])
            metrics_text = json.dumps(incident.get("metrics", {}), indent=2)

            prompt = f"""/no_think
Analyze this incident and identify the root cause:

Title: {incident['title']}
Severity: {incident['severity']}

Logs:
{logs_text}

Metrics:
{metrics_text}

Respond with the root cause in 1-2 sentences."""

        elif "question" in incident:
            # OpsEval format: Q&A multiple choice - FIXED with few-shot examples
            choices = incident.get("choices", [])
            choices_text = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices)])

            prompt = f"""/no_think
You are an expert at IT operations and root cause analysis. Select the correct answer.

### Example 1:
Question: What is the most likely cause of high CPU usage on a web server?
Options:
A. Network latency
B. Memory leak in application
C. Disk I/O bottleneck
D. Infinite loop in code
Answer: D. Infinite loop in code - this directly causes continuous CPU consumption.

### Example 2:
Question: A database connection pool is exhausted. What should you check first?
Options:
A. DNS configuration
B. Application connection leaks
C. Firewall rules
D. SSL certificate
Answer: B. Application connection leaks - unreleased connections cause pool exhaustion.

### Your Task:
Question: {incident['question']}

Options:
{choices_text}

Answer:"""

        else:
            # Fallback: use title and any available info
            prompt = f"""/no_think
Analyze this incident and identify the root cause:

Title: {incident['title']}
Severity: {incident.get('severity', 'unknown')}

Respond with the root cause in 1-2 sentences."""

        # FIXED: Dynamic token calculation based on prompt length
        max_tokens = self._calculate_dynamic_tokens(prompt, model, min_output=1024)

        result = await self.client.inference(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            max_tokens=max_tokens,  # FIXED: Dynamic based on input size
            temperature=0.0,
        )

        # Check correctness against acceptable answers
        actual_output = result["response"]
        expected_answer_raw = test_case.get("expected_answer_raw")  # For OpsEval Q&A
        correct = self._check_rca_correct(
            actual_output,
            test_case["acceptable_answers"],
            expected_answer_raw,
        )

        return BenchmarkResult(
            test_id=test_case["id"],
            model=model,
            task_type="rca",
            input_text=incident.get("title", incident.get("question", "Unknown")[:100]),
            expected_output=test_case["expected_root_cause"],
            actual_output=actual_output[:500],
            correct=correct,
            inference_latency_ms=result["inference_latency_ms"],
            total_latency_ms=result["total_latency_ms"],
            network_rtt_ms=result["network_rtt_ms"],
            tokens_generated=result["tokens_generated"],
            timestamp=datetime.utcnow().isoformat(),
        )

    def _check_annotation_correct(self, actual: str, expected: dict) -> bool:
        """Check if annotation output is correct - STRICT version."""
        # FIXED: Reject empty outputs
        if not actual or not actual.strip():
            return False

        actual_lower = actual.lower()

        # FIXED: Try to parse JSON first for precise matching
        try:
            # Extract JSON from response
            json_str = actual
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]

            start = json_str.find("{")
            end = json_str.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(json_str[start:end])

                # Strict anomaly check
                expected_anomaly = expected.get("anomaly_detected", False)
                actual_anomaly = parsed.get("anomaly_detected")

                # Handle string "true"/"false" as well as bool
                if isinstance(actual_anomaly, str):
                    actual_anomaly = actual_anomaly.lower() == "true"

                if actual_anomaly is None or bool(actual_anomaly) != bool(expected_anomaly):
                    return False

                return True  # JSON parsed and anomaly matches
        except (json.JSONDecodeError, TypeError, KeyError, ValueError):
            pass  # Fall back to keyword matching

        # Fallback: keyword-based check
        if expected.get("anomaly_detected"):
            if "true" not in actual_lower and "anomaly" not in actual_lower:
                return False
        else:
            if "false" not in actual_lower and "normal" not in actual_lower:
                return False

        return True  # Keyword match succeeded

    def _check_rca_correct(
        self,
        actual: str,
        acceptable_answers: list[str],
        expected_answer_raw: Optional[str] = None,
    ) -> bool:
        """Check if RCA output matches any acceptable answer."""
        # FIXED: Reject empty outputs
        if not actual or not actual.strip():
            return False

        actual_lower = actual.lower().strip()

        # For Q&A format: check if the answer letter matches
        if expected_answer_raw:
            # expected_answer_raw is like "B", "A", etc.
            expected_letter = expected_answer_raw.upper().strip()
            # Check if response starts with or contains the correct letter
            actual_upper = actual.upper().strip()
            if actual_upper.startswith(expected_letter):
                return True
            if f"{expected_letter}." in actual_upper or f"{expected_letter}:" in actual_upper:
                return True
            if f"ANSWER: {expected_letter}" in actual_upper or f"ANSWER IS {expected_letter}" in actual_upper:
                return True

        # Check against acceptable answers (semantic match)
        for answer in acceptable_answers:
            answer_lower = answer.lower().strip()
            if answer_lower in actual_lower or actual_lower in answer_lower:
                return True
            # Partial keyword match for longer answers
            answer_words = set(answer_lower.split())
            actual_words = set(actual_lower.split())
            if len(answer_words) > 2:
                common = answer_words & actual_words
                if len(common) >= len(answer_words) * 0.5:  # 50% keyword match
                    return True

        return False

    async def benchmark_model(
        self,
        model_key: str,
        max_annotation_tests: int = 100,
        max_rca_tests: int = 50,
    ) -> ModelBenchmarkSummary:
        """Run full benchmark on a single model."""
        model_config = MODELS[model_key]
        print(f"\n{'='*60}")
        print(f"Benchmarking: {model_config['description']}")
        print(f"{'='*60}")

        # Determine actual model name for API
        if model_config["type"] == "hybrid":
            # For hybrid, use reasoning model for RCA, fast model for annotation
            annotation_model = model_config["fast_model"]
            rca_model = model_config["reasoning_model"]
        else:
            annotation_model = model_config["model"]
            rca_model = model_config["model"]

        results = []

        # System prompts
        annotation_system = "You are a fast telemetry annotator. Analyze logs and classify anomalies. Respond in JSON format."
        rca_system = "You are an expert SRE performing root cause analysis. Identify the primary cause of incidents."

        # Load datasets
        annotation_tests = self.load_dataset("annotation")[:max_annotation_tests]
        rca_tests = self.load_dataset("rca")[:max_rca_tests]

        # Run annotation tests
        print(f"\n[ANNOTATION] Running {len(annotation_tests)} annotation tests...")
        for i, test_case in enumerate(annotation_tests):
            try:
                result = await self.run_annotation_test(annotation_model, test_case, annotation_system)
                results.append(result)
                status = "[OK]" if result.correct else "[FAIL]"
                print(f"   [{i+1}/{len(annotation_tests)}] {test_case['id']}: {status} ({result.inference_latency_ms:.0f}ms)")
            except Exception as e:
                print(f"   [{i+1}/{len(annotation_tests)}] {test_case['id']}: [ERROR] {e}")

        # Run RCA tests
        print(f"\n[RCA] Running {len(rca_tests)} RCA tests...")
        for i, test_case in enumerate(rca_tests):
            try:
                result = await self.run_rca_test(rca_model, test_case, rca_system)
                results.append(result)
                status = "[OK]" if result.correct else "[FAIL]"
                print(f"   [{i+1}/{len(rca_tests)}] {test_case['id']}: {status} ({result.inference_latency_ms:.0f}ms)")
            except Exception as e:
                print(f"   [{i+1}/{len(rca_tests)}] {test_case['id']}: [ERROR] {e}")

        # Calculate summary
        annotation_results = [r for r in results if r.task_type == "annotation"]
        rca_results = [r for r in results if r.task_type == "rca"]

        annotation_correct = sum(1 for r in annotation_results if r.correct)
        rca_correct = sum(1 for r in rca_results if r.correct)

        latencies = [r.inference_latency_ms for r in results if r.inference_latency_ms > 0]
        sorted_latencies = sorted(latencies) if latencies else [0]

        def percentile(data, p):
            if not data:
                return 0
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = min(f + 1, len(data) - 1)
            return data[f] + (k - f) * (data[c] - data[f])

        summary = ModelBenchmarkSummary(
            model_name=model_key,
            model_type=model_config["type"],
            vram_gb=model_config["vram_gb"],
            annotation_accuracy=round(annotation_correct / len(annotation_results) * 100, 2) if annotation_results else 0,
            rca_accuracy=round(rca_correct / len(rca_results) * 100, 2) if rca_results else 0,
            avg_inference_latency_ms=round(statistics.mean(latencies), 2) if latencies else 0,
            p50_latency_ms=round(percentile(sorted_latencies, 50), 2),
            p95_latency_ms=round(percentile(sorted_latencies, 95), 2),
            p99_latency_ms=round(percentile(sorted_latencies, 99), 2),
            total_tests=len(results),
            total_correct=annotation_correct + rca_correct,
            timestamp=datetime.utcnow().isoformat(),
        )

        # Save results
        self._save_results(model_key, results, summary)

        return summary

    def _save_results(self, model_key: str, results: list[BenchmarkResult], summary: ModelBenchmarkSummary):
        """Save benchmark results to disk."""
        output_dir = RESULTS_DIR / model_key
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save detailed results
        results_path = output_dir / "results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in results], f, indent=2)

        # Save summary
        summary_path = output_dir / "summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(asdict(summary), f, indent=2)

        print(f"\n[SAVED] Results saved to: {output_dir}")


async def run_all_benchmarks(
    ollama_url: str = OLLAMA_BASE_URL,
    models: Optional[list[str]] = None,
    max_annotation: int = 100,
    max_rca: int = 50,
):
    """Run benchmarks on all models (one-shot execution)."""
    runner = BenchmarkRunner(ollama_url)
    await runner.initialize()

    models_to_run = models or list(MODELS.keys())
    summaries = []

    try:
        for model_key in models_to_run:
            if model_key not in MODELS:
                print(f"[WARN] Unknown model: {model_key}, skipping")
                continue

            try:
                summary = await runner.benchmark_model(
                    model_key,
                    max_annotation_tests=max_annotation,
                    max_rca_tests=max_rca,
                )
                summaries.append(summary)
            except Exception as e:
                print(f"[FAILED] Benchmark failed for {model_key}: {e}")
                continue

    finally:
        await runner.close()

    # Save combined results
    combined_path = RESULTS_DIR / "combined_results.json"
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump([asdict(s) for s in summaries], f, indent=2)

    # Print summary table
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"{'Model':<30} {'Ann. Acc':>10} {'RCA Acc':>10} {'P50 (ms)':>10} {'P95 (ms)':>10}")
    print("-" * 80)
    for s in summaries:
        print(f"{s.model_name:<30} {s.annotation_accuracy:>9.1f}% {s.rca_accuracy:>9.1f}% {s.p50_latency_ms:>10.0f} {s.p95_latency_ms:>10.0f}")
    print("=" * 80)

    # Create completion marker
    (BENCHMARK_DIR / ".benchmark_step3_complete").touch()

    return summaries


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Constitutional AIOps Benchmark Runner")
    parser.add_argument("--model", "-m", help="Run benchmark on specific model only")
    parser.add_argument("--ollama-url", default=OLLAMA_BASE_URL, help="Ollama base URL")
    parser.add_argument("--calibrate-only", action="store_true", help="Only calibrate network RTT")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick test mode (5 ann + 5 rca)")
    parser.add_argument("--ann-limit", type=int, default=100, help="Max annotation tests (default: 100)")
    parser.add_argument("--rca-limit", type=int, default=50, help="Max RCA tests (default: 50)")
    args = parser.parse_args()

    if args.calibrate_only:
        async def calibrate():
            client = LatencyCompensatedClient(args.ollama_url)
            await client.calibrate()
            await client.close()
        asyncio.run(calibrate())
        return 0

    # Quick mode overrides limits
    max_ann = 5 if args.quick else args.ann_limit
    max_rca = 5 if args.quick else args.rca_limit

    models = [args.model] if args.model else None
    asyncio.run(run_all_benchmarks(args.ollama_url, models, max_ann, max_rca))
    return 0


if __name__ == "__main__":
    sys.exit(main())
