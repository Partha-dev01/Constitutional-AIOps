#!/usr/bin/env python3
"""
Constitutional AIOps - Mock LLM Server

Provides mock endpoints for local development without GPU.
Simulates Fast Agent (8081) and Reasoning Agent (8082) responses.
"""

import json
import random
import time
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Create three FastAPI apps (health proxy, fast agent, reasoning agent)
health_app = FastAPI(title="Mock LLM Health Proxy")
fast_app = FastAPI(title="Mock Fast Agent (Qwen3-4B)")
reasoning_app = FastAPI(title="Mock Reasoning Agent (Qwen3-14B)")


# Mock responses for fast agent
FAST_AGENT_RESPONSES = [
    {
        "anomaly_detected": True,
        "severity": "warning",
        "category": "performance",
        "confidence": 0.85,
        "summary": "High CPU usage detected on service",
        "needs_reasoning": True,
        "key_indicators": ["cpu_usage > 80%", "latency_spike"]
    },
    {
        "anomaly_detected": False,
        "severity": "info",
        "category": "unknown",
        "confidence": 0.95,
        "summary": "Normal operation",
        "needs_reasoning": False,
        "key_indicators": []
    },
    {
        "anomaly_detected": True,
        "severity": "critical",
        "category": "error",
        "confidence": 0.92,
        "summary": "Database connection errors increasing",
        "needs_reasoning": True,
        "key_indicators": ["error_rate > 5%", "connection_pool_exhausted"]
    },
]

# Mock responses for reasoning agent
REASONING_AGENT_RESPONSES = {
    "rca": {
        "root_cause": "Database connection pool exhaustion due to leaked connections",
        "causal_chain": [
            "New deployment introduced connection leak",
            "Pool exhaustion over 2 hours",
            "Cascading failures to dependent services"
        ],
        "impact": {
            "services": ["api-gateway", "user-service", "payment-service"],
            "severity": "high",
            "users_affected": "~5000"
        },
        "confidence": 0.82,
        "reasoning": "Analysis of connection metrics shows gradual exhaustion...",
        "remediation_steps": [
            {"action": "Restart affected pods", "risk": "low"},
            {"action": "Rollback to previous deployment", "risk": "medium"}
        ],
        "prevention": "Add connection pool monitoring and alerts"
    },
    "chat": "I've analyzed the incident and identified potential root causes. The primary issue appears to be related to resource constraints. Would you like me to provide a detailed remediation plan?",
    "planning": {
        "plan_name": "Connection Pool Recovery",
        "total_steps": 3,
        "estimated_duration": "15 minutes",
        "overall_risk": "low",
        "rollback_available": True,
        "steps": [
            {
                "order": 1,
                "action": "Scale up connection pool",
                "command": "kubectl scale deployment db-proxy --replicas=3",
                "duration": "30 seconds",
                "risk": "low",
                "requires_approval": False,
                "validation": "Check connection count"
            }
        ],
        "success_criteria": "Error rate below 0.1%",
        "rollback_plan": "Scale back to 1 replica"
    }
}


def create_chat_response(content: str, model: str) -> dict:
    """Create OpenAI-compatible chat completion response."""
    return {
        "id": f"chatcmpl-mock-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": random.randint(50, 200),
            "completion_tokens": random.randint(100, 500),
            "total_tokens": random.randint(150, 700)
        }
    }


# Health Proxy endpoints (port 8080)
@health_app.get("/health")
async def proxy_health():
    return {
        "status": "healthy",
        "service": "mock-llm",
        "agents": {
            "fast": {"port": 8081, "model": "qwen3-4b-mock"},
            "reasoning": {"port": 8082, "model": "qwen3-14b-mock"}
        }
    }


@health_app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "qwen3-4b", "object": "model", "owned_by": "mock"},
            {"id": "qwen3-14b", "object": "model", "owned_by": "mock"}
        ]
    }


# Fast Agent endpoints (port 8081)
@fast_app.get("/health")
async def fast_health():
    return {"status": "healthy", "model": "qwen3-4b-mock"}


@fast_app.get("/v1/models")
async def fast_models():
    return {
        "object": "list",
        "data": [{"id": "qwen3-4b", "object": "model", "owned_by": "mock"}]
    }


@fast_app.post("/v1/chat/completions")
async def fast_completion(request: dict):
    # Simulate processing time
    time.sleep(random.uniform(0.02, 0.05))  # 20-50ms
    
    response_data = random.choice(FAST_AGENT_RESPONSES)
    content = json.dumps(response_data, indent=2)
    
    return create_chat_response(content, "qwen3-4b")


# Reasoning Agent endpoints (port 8082)
@reasoning_app.get("/health")
async def reasoning_health():
    return {"status": "healthy", "model": "qwen3-14b-mock"}


@reasoning_app.get("/v1/models")
async def reasoning_models():
    return {
        "object": "list",
        "data": [{"id": "qwen3-14b", "object": "model", "owned_by": "mock"}]
    }


@reasoning_app.post("/v1/chat/completions")
async def reasoning_completion(request: dict):
    # Simulate longer processing time
    time.sleep(random.uniform(0.1, 0.2))  # 100-200ms
    
    messages = request.get("messages", [])
    user_message = messages[-1].get("content", "") if messages else ""
    
    # Determine response type
    if "rca" in user_message.lower() or "root cause" in user_message.lower():
        content = json.dumps(REASONING_AGENT_RESPONSES["rca"], indent=2)
    elif "plan" in user_message.lower() or "remediat" in user_message.lower():
        content = json.dumps(REASONING_AGENT_RESPONSES["planning"], indent=2)
    else:
        content = REASONING_AGENT_RESPONSES["chat"]
    
    return create_chat_response(content, "qwen3-14b")


def run_servers():
    """Run all three mock servers."""
    import threading

    def run_health():
        uvicorn.run(health_app, host="0.0.0.0", port=8080, log_level="warning")

    def run_fast():
        uvicorn.run(fast_app, host="0.0.0.0", port=8081, log_level="warning")

    def run_reasoning():
        uvicorn.run(reasoning_app, host="0.0.0.0", port=8082, log_level="warning")

    # Run all servers in threads
    health_thread = threading.Thread(target=run_health, daemon=True)
    fast_thread = threading.Thread(target=run_fast, daemon=True)
    reasoning_thread = threading.Thread(target=run_reasoning, daemon=True)

    health_thread.start()
    fast_thread.start()
    reasoning_thread.start()

    print("Mock LLM servers running:")
    print("  Health Proxy:        http://localhost:8080")
    print("  Fast Agent (4B):     http://localhost:8081")
    print("  Reasoning Agent (14B): http://localhost:8082")

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    run_servers()
