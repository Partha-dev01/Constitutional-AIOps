---
layout: home

hero:
  name: Constitutional AIOps
  text: Autonomous infrastructure management with a safety layer
  tagline: A dual-agent system that annotates telemetry, finds root cause, and proposes remediation. Every action passes a constitutional safety gate and, when uncertain, waits for human approval. Bring your own OpenAI-compatible LLM endpoint.
  actions:
    - theme: brand
      text: Get Started
      link: /guide/getting-started
    - theme: alt
      text: Self-Host
      link: /guide/self-hosting
    - theme: alt
      text: View on GitHub
      link: https://github.com/Partha-dev01/Constitutional-AIOps

features:
  - title: Bring your own LLM
    details: Point both agents at any OpenAI-compatible endpoint (vLLM, Ollama, AWS Bedrock, OpenAI). One endpoint and model is enough for a minimal setup, or run two for the dual-engine reference configuration.
  - title: Constitutional safety
    details: Twelve principles across three tiers gate every proposed action. High-confidence actions are audited, uncertain ones require human approval, and low-confidence ones only alert.
  - title: One-command lite self-host
    details: The lite profile runs the backend and frontend on roughly 0.74 GiB of RAM, with no GPU and no bundled models. It degrades gracefully without Neo4j or the observability stack.
  - title: Graph-episodic memory
    details: Optional Neo4j memory correlates incidents and retains context across time. Without it the app falls back to an in-memory episode store with similarity search.
---

## What it is

Constitutional AIOps ingests logs, metrics, and traces, uses a fast agent to
annotate and classify them, and a reasoning agent to correlate incidents,
explain root cause, and draft remediation. Nothing is executed blindly. A
constitutional validator scores each proposed action, and the authorization
matrix decides whether it runs automatically, waits for a human, or only raises
an alert.

The recommended way to run it is the **lite** profile: the backend and frontend
plus your own OpenAI-compatible LLM endpoint. No GPU, no bundled models, no
Neo4j required.

```bash
git clone https://github.com/Partha-dev01/Constitutional-AIOps.git constitutional-aiops
cd constitutional-aiops
cp .env.example .env          # set your LLM endpoint (both agents may share one)
docker compose -f docker/docker-compose.lite.yml --env-file .env up -d
# Frontend  http://localhost:3000
# Backend   http://localhost:8000/docs
```

Continue with the [Overview](/guide/getting-started), or jump to
[Self-Hosting](/guide/self-hosting) for every deployment option.

## License

Constitutional AIOps is released under the **GNU Affero General Public License
v3.0**. If you run a modified version as a network service, you must offer its
users the corresponding source of your modified version.
