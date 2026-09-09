---
title: Graph Explorer
outline: deep
---

# Graph Explorer

The Graph Explorer visualizes the episodic knowledge graph: how incidents, their
root causes, the actions taken, the services involved, and the entities the model
extracted all connect to each other.

![The episodic knowledge graph](/screenshots/graph-explorer.png)

## What you see

Nodes are typed and colored by what they are:

- **Episodes and incidents**: a thing that happened.
- **Root causes**: what the analysis concluded was behind it.
- **Actions**: what was done in response.
- **Services**: the components involved.
- **Entities**: items the LLM extracted from the incident context.

Nodes also carry a status such as healthy, warning, critical, detected,
analyzing, remediating, or resolved, so the graph shows not just structure but
current state.

## How to use it

1. **Start from an incident node** and follow its edges to the root cause and the
   actions that addressed it.
2. **Use the edge filtering controls** to hide relationship types you do not care
   about, so a dense graph stays readable.
3. **Switch on DAG mode** to lay the graph out top-down when you want a clear
   hierarchy rather than a force-directed cloud.
4. **Trace a service** to see every episode it was part of, which is how a
   recurring cause becomes obvious.

## Requires the graph memory

The episodic graph is backed by Neo4j. This is the one feature that depends on
it. If you run the lite profile without Neo4j, the app falls back to an in-memory
episode store with similarity search for the rest of the product, but the full
graph visualization is the part that wants the graph database. See
[Configuration](/guide/configuration) for enabling Neo4j.

## Related

- [Console](/features/console) renders the platform topology and an episodic view
  through the same schema stage, next to the assistant.
- [Incidents](/features/incidents) is the tabular counterpart to the same data.
