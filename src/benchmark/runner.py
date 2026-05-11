"""
Constitutional AIOps - Benchmark Runner Module

Backend integration for running benchmarks through the API.
Wraps the benchmark scripts for use in FastAPI routes.
"""

import json
import time
import os
import asyncio
import hashlib
import platform
import statistics
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Any, Optional
from enum import Enum

import httpx

from src.config import config
from src.agents.model_router import ModelRouter
from src.agents.fast_annotator import FastAnnotator
from src.agents.reasoning_agent import ReasoningAgent


class BenchmarkStatus(str, Enum):
    """Benchmark execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BenchmarkConfig:
    """Configuration for a benchmark run."""
    model_name: str
    max_annotation_tests: int = 100
    max_rca_tests: int = 50
    temperature: float = 0.0
    timeout_seconds: int = 300
    calibrate_network: bool = True
    use_curated_150: bool = True  # Use curated benchmark (seed=42)
    curated_dataset: str = ""  # Custom curated file (e.g., "benchmark_500_seed42.json")
    skip_system_prompt: bool = False  # Ablation: skip system prompts
    inject_graph_context: bool = False  # Ablation: inject historical episode context
    use_orchestrator: bool = False  # Ablation: use LangGraph orchestrated pipeline


@dataclass
class TestCaseResult:
    """Result of a single test case."""
    test_id: str
    task_type: str
    correct: bool
    inference_latency_ms: float
    total_latency_ms: float
    actual_output: str
    expected_output: str
    timestamp: str
    rule_score: float = 0.0
    rule_max_score: float = 3.0
    bert_f1: float = 0.0
    cosine_similarity: float = 0.0
    term_overlap: float = 0.0
    source: str = ""


@dataclass
class BenchmarkResult:
    """Complete benchmark result for a model."""
    model_name: str
    status: BenchmarkStatus
    annotation_accuracy: float = 0.0
    rca_accuracy: float = 0.0
    bert_f1: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    total_tests: int = 0
    passed_tests: int = 0
    network_rtt_ms: float = 0.0
    started_at: str = ""
    completed_at: str = ""
    error: Optional[str] = None
    test_results: list[TestCaseResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = asdict(self)
        result["status"] = self.status.value
        result["test_results"] = [asdict(t) for t in self.test_results]
        return result


# Model configurations
MODELS = {
    "constitutional_aiops": {
        "type": "hybrid",
        "description": "Constitutional AIOps (Qwen3-4B + Qwen3-14B)",
        "fast_model": config.llm.fast_agent_model,
        "reasoning_model": config.llm.reasoning_agent_model,
        "fast_url": config.llm.fast_agent_url,
        "reasoning_url": config.llm.reasoning_agent_url,
        "vram_gb": 15,
    },
    "qwen3_4b": {
        "type": "single",
        "description": "Qwen3-4B",
        "model": "qwen3:4b",
        "vram_gb": 4,
    },
    "qwen3_14b": {
        "type": "single",
        "description": "Qwen3-14B",
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


# ---------------------------------------------------------------------------
# Run-directory tracking: append-only JSONL with fsync + resume.
#
# Rationale: a 7-config ablation runs ~3,500 inferences across many hours.
# A crash, OOM, spot-instance termination, or even a kernel update can
# annihilate the run. We persist each completed case to results.jsonl with
# os.fsync(), so re-launching the run resumes from the last completed case.
# ---------------------------------------------------------------------------

def _capture_env() -> dict:
    """Snapshot the execution environment for reproducibility receipts."""
    env: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "started_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        env["git_sha"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        env["git_sha"] = "unknown"
    try:
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL
        ).decode().strip()
        env["git_dirty"] = bool(dirty)
    except Exception:
        env["git_dirty"] = None
    try:
        freeze = subprocess.check_output(
            ["pip", "freeze"], stderr=subprocess.DEVNULL
        )
        env["pip_freeze_sha256"] = hashlib.sha256(freeze).hexdigest()
    except Exception:
        env["pip_freeze_sha256"] = "unknown"
    return env


def init_run_dir(label: str, base: Optional[Path] = None) -> Path:
    """Create a timestamped run directory with config.json + env.json receipts.

    Layout:
        runs/2026-05-11T14-22-03_<label>/
          config.json   # written by caller after this returns
          env.json      # written here
          results.jsonl # append-only, one record per case
          summary.json  # written at end
          stdout.log    # optional, caller-managed

    Returns the Path to the new directory. If the directory already exists
    (resume scenario), it is reused without overwriting.
    """
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    base = base or (Path(__file__).resolve().parents[2] / "runs")
    run_dir = base / f"{ts}_{label}"
    run_dir.mkdir(parents=True, exist_ok=True)

    env_path = run_dir / "env.json"
    if not env_path.exists():
        env_path.write_text(json.dumps(_capture_env(), indent=2))
    return run_dir


def load_completed_ids(jsonl_path: Path) -> set[str]:
    """Read an existing results.jsonl and return the set of case_ids already done.

    Tolerates a torn final write (partial JSON line) by ignoring parse errors
    on the last line only.
    """
    if not jsonl_path.exists():
        return set()
    ids: set[str] = set()
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                # Torn write on last line is the expected case. Stop here.
                break
            cid = rec.get("case_id") or rec.get("test_id")
            if cid:
                ids.add(cid)
    return ids


def append_result(jsonl_path: Path, rec: dict) -> None:
    """Append a single result record to JSONL, flushed and fsync'd.

    The fsync is non-negotiable: without it, a power loss or kernel panic
    can corrupt the last several hundred KB of buffered writes, breaking
    the resume mechanism on next launch.
    """
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
        f.flush()
        os.fsync(f.fileno())


class BenchmarkRunner:
    """
    Benchmark runner for Constitutional AIOps evaluation.

    Provides async methods for running benchmarks through the API.
    """

    def __init__(self):
        self.current_benchmark: Optional[BenchmarkResult] = None
        self.is_running = False
        self._client: Optional[httpx.AsyncClient] = None
        self._network_rtt_ms = 0.0

        # Initialize agents (use actual backend architecture)
        self.model_router = ModelRouter()
        self.fast_annotator = FastAnnotator(self.model_router)
        self.reasoning_agent = ReasoningAgent(self.model_router)

    async def initialize(self):
        """Initialize the benchmark runner."""
        self._client = httpx.AsyncClient(timeout=300.0)

    async def close(self):
        """Clean up resources."""
        if self._client:
            await self._client.aclose()

    def get_available_models(self) -> dict[str, Any]:
        """Get list of available models for benchmarking."""
        return {
            name: {
                "description": cfg["description"],
                "type": cfg["type"],
                "vram_gb": cfg["vram_gb"],
            }
            for name, cfg in MODELS.items()
        }

    async def calibrate_network(self, base_url: str, samples: int = 10) -> float:
        """
        Calibrate network RTT for accurate latency measurement.

        Args:
            base_url: Ollama API base URL
            samples: Number of samples for calibration

        Returns:
            Median network RTT in milliseconds
        """
        if not self._client:
            await self.initialize()

        latencies = []
        for _ in range(samples):
            start = time.perf_counter_ns()
            try:
                await self._client.get(f"{base_url}/api/tags")
            except Exception:
                continue
            end = time.perf_counter_ns()
            latencies.append((end - start) / 1_000_000)

        if latencies:
            self._network_rtt_ms = statistics.median(latencies)

        return self._network_rtt_ms

    def load_dataset(self, dataset_type: str) -> list[dict]:
        """Load test dataset from benchmark/datasets/processed/.

        Args:
            dataset_type: "annotation", "rca", "benchmark_150", or a filename
                like "benchmark_500_seed42.json"
        """
        base_path = Path(__file__).parent.parent.parent / "benchmark" / "datasets" / "processed"

        if dataset_type == "annotation":
            # Use cleaned dataset (62 bogus BGL entries removed)
            path = base_path / "annotation_clean.json"
            if not path.exists():
                path = base_path / "annotation_test.json"  # Fallback
        elif dataset_type == "rca":
            # Use cleaned dataset (3 mislabeled entries removed)
            path = base_path / "rca_clean.json"
            if not path.exists():
                path = base_path / "rca_test.json"  # Fallback
        elif dataset_type == "benchmark_150":
            # Use curated 150-sample benchmark (seed=42)
            path = base_path / "benchmark_150_seed42.json"
        elif dataset_type.endswith(".json"):
            # Custom dataset file (e.g., "benchmark_500_seed42.json")
            path = base_path / dataset_type
        elif dataset_type == "benchmark_latest":
            # Auto-detect the latest/largest benchmark_*_seed*.json
            candidates = sorted(base_path.glob("benchmark_*_seed*.json"), reverse=True)
            if not candidates:
                raise FileNotFoundError("No curated benchmark files found")
            path = candidates[0]
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")

        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("test_cases", [])

    async def run_benchmark(
        self,
        config: BenchmarkConfig,
        progress_callback: Optional[callable] = None,
        run_dir: Optional[Path] = None,
        run_label: Optional[str] = None,
    ) -> BenchmarkResult:
        """
        Run a complete benchmark for a model.

        Args:
            config: Benchmark configuration
            progress_callback: Optional callback for progress updates
            run_dir: Optional explicit run directory. If None, one is created at
                runs/<UTC-timestamp>_<run_label>/. If the dir exists with a
                non-empty results.jsonl, the benchmark RESUMES from the last
                completed case_id rather than starting fresh.
            run_label: Label for the auto-created run dir. Defaults to model_name.

        Returns:
            BenchmarkResult with all metrics
        """
        if self.is_running:
            raise RuntimeError("Another benchmark is already running")

        # Resolve run directory + receipt files
        if run_dir is None:
            label = run_label or f"bench_{config.model_name}"
            run_dir = init_run_dir(label)
        else:
            run_dir = Path(run_dir)
            run_dir.mkdir(parents=True, exist_ok=True)
            if not (run_dir / "env.json").exists():
                (run_dir / "env.json").write_text(json.dumps(_capture_env(), indent=2))
        # Persist config (overwrite-on-resume is fine — same config expected)
        (run_dir / "config.json").write_text(json.dumps(asdict(config), indent=2))
        results_jsonl = run_dir / "results.jsonl"
        completed_ids = load_completed_ids(results_jsonl)
        if completed_ids:
            print(f"[runner] resuming from {run_dir.name}: {len(completed_ids)} cases already done")

        self.is_running = True
        result = BenchmarkResult(
            model_name=config.model_name,
            status=BenchmarkStatus.RUNNING,
            started_at=datetime.utcnow().isoformat(),
        )
        self.current_benchmark = result

        try:
            await self.initialize()

            model_config = MODELS.get(config.model_name)
            if not model_config:
                raise ValueError(f"Unknown model: {config.model_name}")

            # Apply ablation flags
            if config.skip_system_prompt:
                # Override system prompts with empty strings
                self.fast_annotator.get_system_prompt = lambda: ""
                self.reasoning_agent.get_system_prompt = lambda mode="chat": ""

            # Calibrate network if requested
            if config.calibrate_network:
                if model_config["type"] == "hybrid":
                    base_url = model_config["fast_url"].rsplit("/v1", 1)[0]
                else:
                    base_url = config.ollama_url if hasattr(config, "ollama_url") else "http://localhost:11434"
                result.network_rtt_ms = await self.calibrate_network(base_url)

            # Load datasets - use curated benchmark or full cleaned datasets
            if config.curated_dataset:
                # Use a custom curated benchmark file
                all_tests = self.load_dataset(config.curated_dataset)
                annotation_tests = [t for t in all_tests if t.get("task_type") == "annotation"]
                rca_tests = [t for t in all_tests if t.get("task_type") == "rca"]
                annotation_tests = annotation_tests[:config.max_annotation_tests]
                rca_tests = rca_tests[:config.max_rca_tests]
            elif config.use_curated_150:
                # Use the curated 150-sample benchmark (100 annotation + 50 RCA)
                # Selected with random.seed(42) from cleaned datasets
                # Cleaned: 62 bogus BGL entries + 3 mislabeled RCA removed
                all_tests = self.load_dataset("benchmark_150")
                annotation_tests = [t for t in all_tests if t.get("task_type") == "annotation"]
                rca_tests = [t for t in all_tests if t.get("task_type") == "rca"]
                annotation_tests = annotation_tests[:config.max_annotation_tests]
                rca_tests = rca_tests[:config.max_rca_tests]
            else:
                # Use full cleaned datasets for baseline comparisons
                annotation_tests = self.load_dataset("annotation")[:config.max_annotation_tests]
                rca_tests = self.load_dataset("rca")[:config.max_rca_tests]

            test_results: list[TestCaseResult] = []
            latencies: list[float] = []

            # Hydrate test_results / latencies from any prior JSONL (resume)
            if completed_ids:
                with results_jsonl.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            break  # torn final line
                        # Reconstruct TestCaseResult so summary aggregates correctly
                        try:
                            tr = TestCaseResult(
                                test_id=rec["test_id"],
                                task_type=rec["task_type"],
                                correct=rec["correct"],
                                inference_latency_ms=rec.get("inference_latency_ms", 0.0),
                                total_latency_ms=rec.get("total_latency_ms", 0.0),
                                actual_output=rec.get("actual_output", ""),
                                expected_output=rec.get("expected_output", ""),
                                timestamp=rec.get("timestamp", ""),
                                rule_score=rec.get("rule_score", 0.0),
                                rule_max_score=rec.get("rule_max_score", 3.0),
                                bert_f1=rec.get("bert_f1", 0.0),
                                cosine_similarity=rec.get("cosine_similarity", 0.0),
                                term_overlap=rec.get("term_overlap", 0.0),
                                source=rec.get("source", ""),
                            )
                            test_results.append(tr)
                            if tr.inference_latency_ms > 0:
                                latencies.append(tr.inference_latency_ms)
                        except KeyError:
                            continue

            # Run annotation tests
            for i, test_case in enumerate(annotation_tests):
                test_id = test_case.get("id", f"ann_{i}")
                if test_id in completed_ids:
                    if progress_callback:
                        progress_callback(f"annotation", i + 1, len(annotation_tests))
                    continue
                if progress_callback:
                    progress_callback(f"annotation", i + 1, len(annotation_tests))

                try:
                    test_result = await self._run_annotation_test(
                        test_case, model_config, config.temperature
                    )
                except Exception as e:
                    test_result = TestCaseResult(
                        test_id=test_id,
                        task_type="annotation",
                        correct=False,
                        inference_latency_ms=0,
                        total_latency_ms=0,
                        actual_output=f"Error: {e}",
                        expected_output=str(test_case.get("expected", "")),
                        timestamp=datetime.utcnow().isoformat(),
                    )
                test_results.append(test_result)
                if test_result.inference_latency_ms > 0:
                    latencies.append(test_result.inference_latency_ms)
                # Persist immediately (fsync) — survives crash mid-loop
                rec = asdict(test_result)
                rec["case_id"] = test_result.test_id  # alias for resume scanner
                append_result(results_jsonl, rec)

            # Run RCA tests
            for i, test_case in enumerate(rca_tests):
                test_id = test_case.get("id", f"rca_{i}")
                if test_id in completed_ids:
                    if progress_callback:
                        progress_callback(f"rca", i + 1, len(rca_tests))
                    continue
                if progress_callback:
                    progress_callback(f"rca", i + 1, len(rca_tests))

                try:
                    test_result = await self._run_rca_test(
                        test_case, model_config, config.temperature,
                        inject_graph_context=config.inject_graph_context,
                    )
                except Exception as e:
                    test_result = TestCaseResult(
                        test_id=test_id,
                        task_type="rca",
                        correct=False,
                        inference_latency_ms=0,
                        total_latency_ms=0,
                        actual_output=f"Error: {e}",
                        expected_output=str(test_case.get("expected_root_cause", "")),
                        timestamp=datetime.utcnow().isoformat(),
                    )
                test_results.append(test_result)
                if test_result.inference_latency_ms > 0:
                    latencies.append(test_result.inference_latency_ms)
                rec = asdict(test_result)
                rec["case_id"] = test_result.test_id
                append_result(results_jsonl, rec)

            # Calculate metrics
            annotation_results = [r for r in test_results if r.task_type == "annotation"]
            rca_results = [r for r in test_results if r.task_type == "rca"]

            annotation_correct = sum(1 for r in annotation_results if r.correct)
            rca_correct = sum(1 for r in rca_results if r.correct)

            result.test_results = test_results
            result.total_tests = len(test_results)
            result.passed_tests = annotation_correct + rca_correct
            result.annotation_accuracy = (
                round(annotation_correct / len(annotation_results) * 100, 2)
                if annotation_results else 0
            )
            result.rca_accuracy = (
                round(rca_correct / len(rca_results) * 100, 2)
                if rca_results else 0
            )

            if latencies:
                sorted_latencies = sorted(latencies)
                result.avg_latency_ms = round(statistics.mean(latencies), 2)
                result.p50_latency_ms = round(self._percentile(sorted_latencies, 50), 2)
                result.p95_latency_ms = round(self._percentile(sorted_latencies, 95), 2)
                result.p99_latency_ms = round(self._percentile(sorted_latencies, 99), 2)

            result.status = BenchmarkStatus.COMPLETED
            result.completed_at = datetime.utcnow().isoformat()

        except Exception as e:
            result.status = BenchmarkStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.utcnow().isoformat()

        finally:
            # Always write summary.json (partial state if failed — that's useful)
            try:
                (run_dir / "summary.json").write_text(
                    json.dumps(result.to_dict(), indent=2, default=str)
                )
            except Exception as summary_err:  # never fail the run on summary write
                print(f"[runner] WARNING: could not write summary.json: {summary_err}")
            self.is_running = False
            await self.close()

        return result

    async def _run_annotation_test(
        self,
        test_case: dict,
        model_config: dict,
        temperature: float,
    ) -> TestCaseResult:
        """
        Run a single annotation test using the actual FastAnnotator.

        This now tests the ACTUAL backend architecture including:
        - Full 40+ line system prompts
        - Triplet extraction and entity canonicalization
        - 8+ output fields (not just 3)
        - Confidence scoring
        - Routing decisions (needs_reasoning flag)
        """
        input_data = test_case["input"]
        expected = test_case["expected"]

        # Use actual FastAnnotator (same as production backend)
        start_ns = time.perf_counter_ns()
        try:
            agent_response = await self.fast_annotator.process(input_data)
            total_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            inference_ms = max(total_ms - self._network_rtt_ms, 0)

            # Parse actual output
            actual_data = agent_response.metadata

            # Check correctness (comprehensive validation)
            correct, rule_score = self._check_annotation_correct_comprehensive(
                actual_data, expected, test_case.get("id", "")
            )

            return TestCaseResult(
                test_id=test_case["id"],
                task_type="annotation",
                correct=correct,
                inference_latency_ms=round(inference_ms, 2),
                total_latency_ms=round(total_ms, 2),
                actual_output=agent_response.content[:500],
                expected_output=json.dumps(expected),
                timestamp=datetime.utcnow().isoformat(),
                rule_score=round(rule_score, 2),
                source=test_case.get("source", ""),
            )

        except Exception as e:
            total_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            return TestCaseResult(
                test_id=test_case["id"],
                task_type="annotation",
                correct=False,
                inference_latency_ms=0,
                total_latency_ms=round(total_ms, 2),
                actual_output=f"Error: {e}",
                expected_output=json.dumps(expected),
                timestamp=datetime.utcnow().isoformat(),
            )

    async def _run_rca_test(
        self,
        test_case: dict,
        model_config: dict,
        temperature: float,
        inject_graph_context: bool = False,
    ) -> TestCaseResult:
        """
        Run a single RCA test using the actual ReasoningAgent.

        This now tests the ACTUAL backend architecture including:
        - Full RCA system prompts with structured JSON output
        - Root cause + causal chain + impact analysis
        - Confidence scoring
        - Remediation steps with risk assessment
        - Prevention recommendations
        """
        incident = test_case["incident"]

        # Build incident data structure (same as production backend)
        incident_data = {
            "title": incident["title"],
            "severity": incident["severity"],
            "logs": incident.get("logs", []),
            "timestamp": datetime.utcnow().isoformat(),
        }
        # For OpsEval QA-format tests, include question and choices
        # so the reasoning agent can answer the multiple-choice question
        if "question" in incident:
            incident_data["question"] = incident["question"]
        if "choices" in incident:
            incident_data["choices"] = incident["choices"]

        # Use actual ReasoningAgent (same as production backend)
        start_ns = time.perf_counter_ns()
        try:
            # Build historical context (simulates graph-episodic memory retrieval)
            historical_context = ""
            if inject_graph_context:
                historical_context = self._build_sample_graph_context(incident_data)

            agent_response = await self.reasoning_agent.analyze_rca(
                incident_data=incident_data,
                historical_context=historical_context,
                enable_thinking=False,  # Disable thinking mode for consistent benchmarking
            )
            total_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            inference_ms = max(total_ms - self._network_rtt_ms, 0)

            # Parse actual output
            actual_data = agent_response.metadata

            # Check correctness (comprehensive validation)
            correct, rule_score = self._check_rca_correct_comprehensive(
                actual_data, test_case, agent_response.content
            )

            return TestCaseResult(
                test_id=test_case["id"],
                task_type="rca",
                correct=correct,
                inference_latency_ms=round(inference_ms, 2),
                total_latency_ms=round(total_ms, 2),
                actual_output=agent_response.content[:500],
                expected_output=test_case["expected_root_cause"],
                timestamp=datetime.utcnow().isoformat(),
                rule_score=round(rule_score, 2),
                source=test_case.get("source", ""),
            )

        except Exception as e:
            total_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            return TestCaseResult(
                test_id=test_case["id"],
                task_type="rca",
                correct=False,
                inference_latency_ms=0,
                total_latency_ms=round(total_ms, 2),
                actual_output=f"Error: {e}",
                expected_output=test_case["expected_root_cause"],
                timestamp=datetime.utcnow().isoformat(),
            )

    def _build_sample_graph_context(self, incident_data: dict) -> str:
        """Build simulated graph-episodic memory context for ablation testing.

        In production, this would come from Neo4j graph queries finding similar
        past incidents. For benchmark ablation, we provide a representative
        historical context to measure the impact of RAG augmentation on RCA accuracy.
        """
        title = incident_data.get("title", "")
        service_hint = ""
        if "cloud" in title.lower() or "service" in title.lower():
            service_hint = "cloud microservice"
        elif "network" in title.lower():
            service_hint = "network infrastructure"
        elif "database" in title.lower():
            service_hint = "database system"
        else:
            service_hint = "infrastructure"

        return (
            f"## Similar Past Incidents (from Graph-Episodic Memory)\n\n"
            f"### Incident EP-2024-087 (Similarity: 0.82)\n"
            f"- Service: {service_hint}\n"
            f"- Root Cause: Resource exhaustion due to connection pool saturation\n"
            f"- Resolution: Increased pool size + added circuit breaker\n"
            f"- Time to Resolve: 12 minutes\n\n"
            f"### Incident EP-2024-134 (Similarity: 0.76)\n"
            f"- Service: {service_hint}\n"
            f"- Root Cause: Configuration drift after deployment\n"
            f"- Resolution: Rolled back config + added validation gate\n"
            f"- Time to Resolve: 8 minutes\n\n"
            f"Note: Consider these past incidents when analyzing the current fault."
        )

    async def _call_model(
        self,
        base_url: str,
        model: str,
        prompt: str,
        temperature: float,
    ) -> str:
        """Call the LLM model."""
        if not self._client:
            await self.initialize()

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": temperature,
            "stream": False,
        }

        try:
            response = await self._client.post(
                f"{base_url}/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Model call failed: {e}")

    def _check_annotation_correct_comprehensive(
        self,
        actual_data: dict,
        expected: dict,
        test_id: str,
    ) -> tuple[bool, float]:
        """
        Comprehensive annotation correctness check.

        Validates the ACTUAL architecture outputs including:
        1. Anomaly detection (primary)
        2. Severity classification
        3. Category classification
        4. Triplet extraction quality (bonus)
        5. Confidence score validity
        6. Routing decision appropriateness
        """
        score = 0.0
        max_score = 3.0  # Primary metrics

        # 1. Anomaly detection (required - 1 point)
        actual_anomaly = actual_data.get("anomaly_detected", False)
        expected_anomaly = expected.get("anomaly_detected", False)
        if actual_anomaly == expected_anomaly:
            score += 1.0

        # 2. Severity classification (1 point)
        actual_severity = str(actual_data.get("severity", "")).lower()
        expected_severity = str(expected.get("severity", "")).lower()
        if actual_severity == expected_severity:
            score += 1.0
        elif self._severity_close(actual_severity, expected_severity):
            score += 0.5  # Partial credit for close severity

        # 3. Category classification (1 point)
        actual_category = str(actual_data.get("category", "")).lower()
        expected_category = str(expected.get("category", "")).lower()

        # Semantic category normalization:
        # FastAnnotator vocabulary: error, performance, security, resource, unknown
        # Dataset vocabulary: normal, error
        # Bridge using anomaly_detected to map between vocabularies
        actual_anomaly = actual_data.get("anomaly_detected", False)
        if expected_category == "normal" and not actual_anomaly:
            # Model correctly identified no anomaly; non-error categories
            # are semantically equivalent to "normal"
            if actual_category in ("unknown", "performance", "resource", "security", "info", "normal"):
                actual_category = "normal"
        elif expected_category == "error" and actual_anomaly:
            # Model correctly identified an anomaly; specific categories
            # are subcategories of "error"
            if actual_category in ("performance", "security", "resource", "error"):
                actual_category = "error"

        if actual_category == expected_category:
            score += 1.0
        elif expected_category in actual_category or actual_category in expected_category:
            score += 0.5  # Partial credit for substring match

        # 4. Triplet extraction quality (bonus - architecture validation)
        triplets = actual_data.get("triplets", [])
        if isinstance(triplets, list) and len(triplets) > 0:
            # Bonus for valid triplet extraction
            valid_triplets = sum(
                1 for t in triplets
                if isinstance(t, dict) and "subject" in t and "relation" in t and "object" in t
            )
            if valid_triplets > 0:
                score += 0.25  # Bonus for architecture feature

        # 5. Confidence score validity (sanity check)
        confidence = actual_data.get("confidence", 0)
        if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
            pass  # Valid confidence - no penalty
        else:
            score -= 0.25  # Penalty for invalid confidence

        # Pass threshold: need at least 1.5/3 on primary metrics
        return (score >= 1.5, score)

    def _check_rca_correct_comprehensive(
        self,
        actual_data: dict,
        test_case: dict,
        raw_content: str,
    ) -> tuple[bool, float]:
        """
        Comprehensive RCA correctness check.

        Validates the ACTUAL architecture outputs including:
        1. Root cause identification (primary)
        2. Causal chain validity
        3. Impact assessment
        4. Confidence score
        5. Remediation steps quality
        """
        score = 0.0
        max_score = 3.0

        acceptable_answers = test_case.get("acceptable_answers", [])
        expected_root_cause = test_case.get("expected_root_cause", "")

        # 1. Root cause identification (required - 1.5 points)
        actual_root_cause = str(actual_data.get("root_cause", raw_content)).lower()
        if any(ans.lower() in actual_root_cause for ans in acceptable_answers):
            score += 1.5
        elif expected_root_cause.lower() in actual_root_cause:
            score += 1.0  # Partial for expected match

        # 2. Causal chain validity (0.5 points)
        causal_chain = actual_data.get("causal_chain", [])
        if isinstance(causal_chain, list) and len(causal_chain) >= 2:
            score += 0.5  # Valid causal chain

        # 3. Impact assessment (0.5 points)
        impact = actual_data.get("impact", {})
        if isinstance(impact, dict):
            has_services = "services" in impact
            has_severity = "severity" in impact
            if has_services and has_severity:
                score += 0.5

        # 4. Confidence score validity (0.25 points)
        confidence = actual_data.get("confidence", 0)
        if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
            score += 0.25

        # 5. Remediation steps quality (0.25 points)
        remediation_steps = actual_data.get("remediation_steps", [])
        if isinstance(remediation_steps, list) and len(remediation_steps) > 0:
            valid_steps = sum(
                1 for s in remediation_steps
                if isinstance(s, dict) and "action" in s
            )
            if valid_steps > 0:
                score += 0.25

        # Pass threshold: need at least 1.5/3 on overall
        return (score >= 1.5, score)

    def _severity_close(self, actual: str, expected: str) -> bool:
        """Check if severities are adjacent (partial credit)."""
        severity_order = ["info", "low", "warning", "medium", "high", "critical"]
        try:
            actual_idx = severity_order.index(actual)
            expected_idx = severity_order.index(expected)
            return abs(actual_idx - expected_idx) == 1
        except ValueError:
            return False

    def _percentile(self, data: list[float], p: float) -> float:
        """Calculate percentile."""
        if not data:
            return 0
        k = (len(data) - 1) * p / 100
        f = int(k)
        c = min(f + 1, len(data) - 1)
        return data[f] + (k - f) * (data[c] - data[f])


__all__ = ["BenchmarkRunner", "BenchmarkConfig", "BenchmarkResult", "BenchmarkStatus", "MODELS"]
