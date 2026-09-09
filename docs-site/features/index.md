---
title: Features
outline: deep
---

# Features and tutorials

Every screen in Constitutional AIOps, walked through with real screenshots and
step by step. Each page covers what the feature is, what you see on it, and how
to use it. If a feature degrades without an optional dependency (Neo4j, the LGTM
stack, an LLM endpoint), the page says what you see instead.

## Observe

- [Dashboard](/features/dashboard): the live system view covering health,
  agent latency, recent activity, and the event-driven widgets.
- [Generative UI](/features/generative-ui): the computed widgets and the
  opt-in LLM insight layer, explained in full.
- [Incidents and RCA](/features/incidents): the incident list, confidence
  scoring, root-cause detail, and export.
- [Metrics](/features/metrics): measured agent latency and request metrics.
- [Telemetry](/features/telemetry): logs, traces, and where each panel's data
  came from.

## Investigate

- [Graph Explorer](/features/graph-explorer): the episodic knowledge graph of
  incidents, root causes, actions, services, and entities.
- [Console](/features/console): the cockpit that puts the platform topology and
  the assistant side by side.
- [Chat and Assistant](/features/chat): ask questions about your system with
  the constitutional gate in the loop.

## Operate

- [Infrastructure](/features/infrastructure): servers and containers, health,
  and remediation actions.
- [MCP tools](/features/mcp): the tool registry every action is drawn from.
- [Agent Hub](/features/agent-hub): the fast and reasoning agents and their
  configured endpoints.
- [Settings](/features/settings): safety, models, notifications, BYOK, and the
  AI-widget opt-in.

## Evaluate

- [Benchmark](/features/benchmark): run the RCA benchmark against a dataset and
  export the results.

::: tip Bring your own endpoint first
Chat, RCA explanations, and the LLM insight widgets need a configured
OpenAI-compatible endpoint. If you have not set one up yet, start with
[Bring Your Own Endpoint](/guide/bring-your-own-endpoint).
:::
