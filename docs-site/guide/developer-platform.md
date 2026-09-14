# Developer Platform

Constitutional AIOps is built to be scripted and extended, not just clicked. This
page describes the developer surface: what you can use today, and what is on the
near-term roadmap. Anything not yet shipped is labeled as such, so nothing here is
a promise you cannot check against the code.

![The MCP tools page](/screenshots/mcp.png)

The tool registry described below is the same one [MCP tools](/features/mcp)
exposes directly: every tool, its parameters, and a way to run one yourself
and read the result. [Agent Hub](/features/agent-hub) shows the two agents
that call these tools day to day.

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
that does this without forking is available today; see Extensions below.

## Client SDKs

Official clients live in the repository under `sdk/`:

- **Python**, `sdk/python`: package `constitutional-aiops`.
- **TypeScript**, `sdk/typescript`: package `@constitutional-aiops/sdk`.

Both are published (0.2.0, live on PyPI and npm), hand-written, and dependency-free today. As of 0.2.0 the
ergonomic client covers the high-value tags directly: incidents, actions (each
still passing the constitutional gate), agents, the episodic graph, audit,
notifications, benchmark, metrics, chat (streaming and non-streaming), and
self-service personal access tokens, plus automatic pagination and opt-in retries.
The full 127-path surface stays available through the generated typed core. Each
package README lists every method; see `sdk/CHANGELOG.md`. Example, Python:

```python
from constitutional_aiops import AIOpsClient

client = AIOpsClient("https://your-instance.example.com", token="aiops_pat_...")
for incident in client.paginate("/incidents/", severity="critical"):
    print(incident["id"], incident["title"])
```

TypeScript:

```ts
import { AIOpsClient } from '@constitutional-aiops/sdk'

const client = new AIOpsClient({ baseUrl: 'https://your-instance.example.com', token: 'aiops_pat_...' })
for await (const incident of client.paginate('/incidents/', { severity: 'critical' })) {
  console.log(incident.id, incident.title)
}
```

Each package also ships a generated typed core (from the committed OpenAPI
schema) alongside this hand-written ergonomic layer. The packages publish to
PyPI (`constitutional-aiops`) and npm (`@constitutional-aiops/sdk`) on a pushed
`sdk-v*` tag.

## Authentication for scripts

Today the API accepts the session cookie the UI uses, and against an instance with
`AUTH_REQUIRED` unset (the default single-user mode) no credential is needed.

**Personal access tokens.** A per-user token you create, list and revoke in the
app (Settings, or `POST /api/v1/auth/tokens`), sent as `Authorization: Bearer
aiops_pat_...`, hashed at rest and scoped to your own role. This is the clean path
for CI and scripts, and it resolves to your user even when `AUTH_REQUIRED` is off,
so calls stay attributed and cost-fenced.

## Extensions

**Custom tools via plugins are available today**, off by default. Third-party
packages contribute tools through a Python entry point group
(`constitutional_aiops.tools`), loaded at startup only when `AIOPS_ENABLE_PLUGINS`
is set on the backend; with it unset the plugin surface does not exist. A plugin
tool is registered into the same catalogue, listing and dispatch as the built-in
tools and runs through the identical constitutional gate (kill-switch, validator,
human approval, audit). A plugin cannot supply its own gate, cannot shadow a
built-in tool name, and any action that changes infrastructure requires human
approval. A malformed plugin is logged and skipped rather than breaking the tool
surface. See [MCP tools](/features/mcp) for the full contract.

A plugin tool returns a small, stable result shape that the chat UI renders, so
it gets a usable surface without shipping frontend code.

Custom agents and custom React widgets are not runtime-pluggable and are not
presented as if they were. The supported extension path is custom prompts plus
custom tools. Pluggable agents remain a future major-version item.

## The safety contract

Everything the SDK or a future plugin does still runs through the constitutional
layer. An action that the validator blocks, or that needs human approval, comes
back as a refusal with the gate's own verdict, not as a silent success. Both SDKs
surface this as a `ConstitutionalRefusal`. See [Constitutional Safety](/guide/safety).
