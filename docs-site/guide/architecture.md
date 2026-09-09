# Architecture

Constitutional AIOps has four parts: a dual-agent LLM pipeline, a constitutional
safety framework, an optional graph-episodic memory, and human-in-the-loop
approval.

![The platform topology and assistant in Console](/screenshots/console.png)

The topology graph above is rendered by [Console](/features/console). The same
graph structure, with episodes and root causes layered on top, is what
[Graph Explorer](/features/graph-explorer) visualizes in full.

::: tip Full screenshot walkthrough
This page explains how the pieces fit together. For every screen with its own
tutorial, start at [Features and tutorials](/features/).
:::

## Dual-agent pipeline

Two logical agents split the work by latency and depth:

- **Fast agent.** Annotates and classifies incoming telemetry (logs, metrics,
  traces). It is optimized for high volume and low latency.
- **Reasoning agent.** Handles root cause analysis, remediation planning, and
  the human chat. It runs on a larger model when you have one.

Both agents speak to any OpenAI-compatible endpoint. They can share one endpoint
and model for a minimal setup, or use two for the reference configuration. See
[Bring Your Own Endpoint](/guide/bring-your-own-endpoint).

### Reference configuration

The research-paper reference runs both models co-resident on a single 24 GB GPU
with vLLM. This is not a requirement for self-hosting, which is why the lite
profile offloads the LLM to a remote endpoint instead.

```
┌─────────────────────────────────────────────────────────────────┐
│                 24 GB VRAM, both models loaded                   │
├─────────────────────────────────────────────────────────────────┤
│  FAST AGENT (port 8000)                                         │
│  Model: Qwen3-4B  ·  Purpose: telemetry annotation              │
│                                                                 │
│  REASONING AGENT (port 8001)                                    │
│  Model: Qwen3-14B  ·  Purpose: RCA, remediation, chat           │
└─────────────────────────────────────────────────────────────────┘
```

## Graph-episodic memory

An optional Neo4j store keeps past incidents as episodes and links them into a
graph, so the reasoning agent can retrieve similar past incidents and their
successful actions. Retrieval is hybrid: vector similarity plus graph structure.

The lite profile drops Neo4j and falls back to an in-memory episode store with
similarity search, so the Graph page still works with reduced fidelity.

## Human-in-the-loop

Action tools never execute inside the model loop. A proposed action is scored by
the constitutional validator, then routed by the authorization matrix. Depending
on confidence it runs automatically with an audit record, waits for a human
approve or reject decision, or only raises an alert. See
[Constitutional Safety](/guide/safety) for the full model.

## Technology stack

| Component | Technology |
|-----------|------------|
| LLM hosting | Bring your own (vLLM, Ollama, AWS Bedrock, OpenAI) |
| LLM runtime | Any OpenAI-compatible endpoint |
| Graph memory | Neo4j 5.x (optional) |
| Observability | Grafana, Loki, Tempo, Prometheus (full stack) |
| Backend | FastAPI (Python 3.11+) |
| Frontend | React 18 + TypeScript + Tailwind |
| Container | Docker Compose |
