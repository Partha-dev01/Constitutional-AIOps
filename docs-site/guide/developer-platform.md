# Developer Platform

Constitutional AIOps is built to be scripted and extended, not just clicked. This
page describes the developer surface: what you can use today, and what is on the
near-term roadmap. Anything not yet shipped is labeled as such, so nothing here is
a promise you cannot check against the code.

## Available today

### The REST API

Every screen in the app is a thin client over a documented REST API under
`/api/v1`. Incidents, actions, tools, telemetry, the knowledge graph, benchmark
runs and settings are all reachable programmatically.

When the backend is started with docs enabled (`AIOPS_ENABLE_DOCS=true`, or any
non-production build), the interactive reference is served at:

- Swagger UI at `/docs`
- ReDoc at `/redoc`
- The raw OpenAPI schema at `/openapi.json`

List endpoints share one envelope, so pagination is uniform:

```json
{ "items": [ ... ], "total": 128, "page": 1, "page_size": 50, "has_more": true }
```

### Custom system prompts

Each agent's system prompt can be overridden through the `/api/v1/prompts` routes
(admin-gated). This is the supported way to steer the reasoning and fast agents
without touching code.

### Bring your own tools, today, in a fork

The tool registry that powers chat and remediation is code-defined. If you run
your own build you can add a tool by editing the registry. A packaged plugin path
that does this without forking is on the roadmap below.

## Client SDKs (pre-release)

Official clients live in the repository under `sdk/`:

- **Python**, `sdk/python` — package `constitutional-aiops`.
- **TypeScript**, `sdk/typescript` — package `@constitutional-aiops/sdk`.

Both are pre-release, hand-written, and dependency-free today. They cover listing
with automatic pagination, reading incidents, approving actions through the
constitutional gate, and streaming a chat turn. Example, Python:

```python
from constitutional_aiops import AIOpsClient

client = AIOpsClient("https://your-instance.example.com", token="caiops_pat_...")
for incident in client.paginate("/incidents/", severity="critical"):
    print(incident["id"], incident["title"])
```

TypeScript:

```ts
import { AIOpsClient } from '@constitutional-aiops/sdk'

const client = new AIOpsClient({ baseUrl: 'https://your-instance.example.com', token: 'caiops_pat_...' })
for await (const incident of client.paginate('/incidents/', { severity: 'critical' })) {
  console.log(incident.id, incident.title)
}
```

The final clients will be generated from the OpenAPI schema, with this
hand-written layer kept on top as the ergonomic surface. The published packages
are gated on the repository going public.

## Authentication for scripts

Today the API accepts the session cookie the UI uses, and against an instance with
`AUTH_REQUIRED` unset (the default single-user mode) no credential is needed.

**Planned: personal access tokens.** A per-user token you create, list and revoke,
sent as `Authorization: Bearer caiops_pat_...`, hashed at rest, scoped to your own
role. This is the clean path for CI and scripts. It is not built yet; this page
will show the exact flow when it ships.

## Extensions (roadmap)

The plan is a packaged plugin system so you can add capability without forking:

- **Custom tools** via a `@tool` decorator and Python entry points, discovered at
  startup only when plugins are explicitly enabled. Any tool that changes
  infrastructure must declare a destructive risk tier and passes the same
  constitutional gate (kill-switch, validator, human approval, audit) as the
  built-in tools. A plugin cannot supply its own gate.
- **Tool result cards.** A plugin returns a small, stable result shape and the
  chat UI renders it, so a plugin gets a usable surface without shipping frontend
  code.

Custom agents and custom React widgets are not runtime-pluggable and are not
presented as if they were. The supported extension path is custom prompts plus
custom tools. Pluggable agents are a future major-version item.

## The safety contract

Everything the SDK or a future plugin does still runs through the constitutional
layer. An action that the validator blocks, or that needs human approval, comes
back as a refusal with the gate's own verdict, not as a silent success. Both SDKs
surface this as a `ConstitutionalRefusal`. See [Constitutional Safety](/guide/safety).
