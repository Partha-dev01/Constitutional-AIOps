---
title: SDK Reference
outline: deep
---

# SDK Reference

Official client libraries for the Constitutional AIOps REST API, in Python and
TypeScript. They are hand-written, dependency-free, and the same shape in both
languages, so a script reads the same either way. This page is the complete
reference for the ergonomic client; the [SDK Cookbook](/guide/sdk-cookbook) has
task-shaped recipes.

- **Python** — [`constitutional-aiops`](https://pypi.org/project/constitutional-aiops/) on PyPI.
- **TypeScript** — [`@constitutional-aiops/sdk`](https://www.npmjs.com/package/@constitutional-aiops/sdk) on npm.

Each package ships two layers. The **ergonomic client** (`AIOpsClient`)
documented here returns plain decoded JSON and has zero runtime dependencies
(stdlib `urllib` in Python, global `fetch` in TypeScript). Under it sits a
**generated typed core** covering the full 127-path surface, described in
[The typed core](#the-typed-core).

::: info The constitutional gate is never bypassed
An action you submit through the SDK passes the same validator and human-approval
flow as the UI. A blocked or approval-required action comes back as a
`ConstitutionalRefusal` (or, for the tool and chat-decision endpoints, a uniform
result body), never a silent success. See [Errors](#errors-and-the-constitutional-gate).
:::

## Install

```bash
# Python: ergonomic client only (zero dependencies)
pip install constitutional-aiops
# Python: also install the generated typed core
pip install "constitutional-aiops[typed]"
```

```bash
# TypeScript / JavaScript (Node 18+ or a browser)
npm install @constitutional-aiops/sdk
```

## Authentication

Create a **personal access token** in the app (Settings, or `POST
/api/v1/auth/tokens`) and pass it as the `token`. It is sent as
`Authorization: Bearer aiops_pat_...`, resolves to your user even when
`AUTH_REQUIRED` is off, and keeps calls attributed and cost-fenced. Against a
single-user instance with `AUTH_REQUIRED` unset the token is optional.

## Constructing a client

```python
from constitutional_aiops import AIOpsClient

client = AIOpsClient("https://your-instance.example.com", token="aiops_pat_...")
# `with AIOpsClient(...) as client:` is also supported.
```

```ts
import { AIOpsClient } from '@constitutional-aiops/sdk'

const client = new AIOpsClient({
  baseUrl: 'https://your-instance.example.com',
  token: 'aiops_pat_...',
})
```

| Option | Python | TypeScript | Default | Meaning |
| --- | --- | --- | --- | --- |
| Base URL | `base_url` (positional) | `baseUrl` | — | Instance origin. `/api/v1` is appended unless already present. |
| Token | `token` | `token` | `None` | Bearer token (a PAT or a session token). |
| Timeout | `timeout` (seconds) | `timeoutMs` (ms) | 90s | Per-request timeout. |
| Max retries | `max_retries` | `maxRetries` | `0` | Transient-failure retries; see [Retries](#retries). |
| Backoff | `backoff` (seconds) | `backoffMs` (ms) | 0.5s / 500ms | Base for exponential backoff. |

## Return shapes and pagination

Every ergonomic method returns the decoded JSON (a dict/object or list). List
endpoints share one envelope:

```json
{ "items": [ ... ], "total": 128, "page": 1, "page_size": 50, "has_more": true }
```

`list_*` methods return **one page**. To iterate **every** item, use `paginate`,
which walks the envelope for you and passes extra filters straight through as
query parameters:

```python
for incident in client.paginate("/incidents/", severity="critical"):
    print(incident["id"], incident["title"])
```

```ts
for await (const incident of client.paginate('/incidents/', { severity: 'critical' })) {
  console.log(incident.id, incident.title)
}
```

## Errors and the constitutional gate

Both clients raise a typed error hierarchy on an HTTP error response.

| Error | HTTP | Meaning |
| --- | --- | --- |
| `AIOpsError` | any | Base error. Carries `message`, `status`, `details`. |
| `AuthError` | 401 | Missing or invalid credentials. |
| `NotFound` | 404 | The resource does not exist. |
| `RateLimited` | 429 | A per-user cost fence or throttle rejected the call. |
| `ConstitutionalRefusal` | 4xx | The safety gate blocked an action or requires approval. |

`ConstitutionalRefusal` carries `error_code` (Python) / `errorCode` (TypeScript) —
one of `action_tools_disabled`, `approval_required`, `validation_blocked`,
`container_not_whitelisted` — and the gate's structured `verdict`. It is raised by
the action endpoints (for example `create_action`, `approve_action`,
`execute_action`) when the API returns one of those codes.

```python
from constitutional_aiops import ConstitutionalRefusal

try:
    client.execute_action("act-123")
except ConstitutionalRefusal as refusal:
    print("gate held it:", refusal.error_code, refusal.verdict)
```

```ts
import { ConstitutionalRefusal } from '@constitutional-aiops/sdk'

try {
  await client.executeAction('act-123')
} catch (error) {
  if (error instanceof ConstitutionalRefusal) console.log('gate held it:', error.errorCode)
}
```

::: warning Two endpoints report the gate in the body, not as a throw
`call_tool` and `decide_chat_action` always return a **200-level** uniform
result. A gate refusal there is in the response (`success: false` +
`error_code`, or `status: "refused"`), not a raised `ConstitutionalRefusal`.
Read the body for those two.
:::

## Retries

Retries are **off by default** (`max_retries=0`), so behavior is predictable. When
enabled, a `429` is retried on any method, while `5xx` and network failures are
retried **only for GET** — a `POST` is never silently resent. Backoff is
exponential and honors a `Retry-After` header.

```python
client = AIOpsClient(url, token=tok, max_retries=2)
```

```ts
const client = new AIOpsClient({ baseUrl: url, token: tok, maxRetries: 2 })
```

## Method reference

Every method below returns decoded JSON. Python uses `snake_case`; TypeScript uses
`camelCase` and takes optional arguments as an options object.

### Incidents

| Purpose | Python | TypeScript | Endpoint |
| --- | --- | --- | --- |
| One page of incidents | `list_incidents(**filters)` | `listIncidents(filters?)` | `GET /incidents/` |
| Every incident | `paginate("/incidents/", **filters)` | `paginate('/incidents/', filters?)` | `GET` (auto) |
| One incident | `get_incident(id)` | `getIncident(id)` | `GET /incidents/{id}` |
| Summary counts | `incident_stats()` | `incidentStats()` | `GET /incidents/stats` |
| Create | `create_incident(data)` | `createIncident(data)` | `POST /incidents/` |
| Update | `update_incident(id, data)` | `updateIncident(id, data)` | `PATCH /incidents/{id}` |
| Similar (from memory) | `similar_incidents(id, limit=)` | `similarIncidents(id, {limit?})` | `GET /incidents/{id}/similar` |

### Actions

Every action method still passes the constitutional gate.

| Purpose | Python | TypeScript | Endpoint |
| --- | --- | --- | --- |
| One page of actions | `list_actions(**filters)` | `listActions(filters?)` | `GET /actions/` |
| One action | `get_action(id)` | `getAction(id)` | `GET /actions/{id}` |
| Pending approvals | `pending_actions()` | `pendingActions()` | `GET /actions/pending` |
| Propose an action | `create_action(data)` | `createAction(data)` | `POST /actions/` |
| Approve / reject | `approve_action(id, approved=, approved_by=, comments="")` | `approveAction(id, {approved, approvedBy, comments?})` | `POST /actions/{id}/approve` |
| Execute an approved action | `execute_action(id)` | `executeAction(id)` | `POST /actions/{id}/execute` |
| Cancel | `cancel_action(id, reason=)` | `cancelAction(id, {reason?})` | `POST /actions/{id}/cancel` |
| Summary counts | `action_stats()` | `actionStats()` | `GET /actions/stats` |
| Confidence formula | `confidence_formula()` | `confidenceFormula()` | `GET /actions/confidence/formula` |

### Agents

| Purpose | Python | TypeScript | Endpoint |
| --- | --- | --- | --- |
| Fast-agent stats | `fast_agent_stats()` | `fastAgentStats()` | `GET /agents/fast/stats` |
| Fast-agent activity | `fast_agent_activity(limit=, offset=)` | `fastAgentActivity({limit?, offset?})` | `GET /agents/fast/activity` |
| Reasoning-agent stats | `reasoning_agent_stats()` | `reasoningAgentStats()` | `GET /agents/reasoning/stats` |
| Reasoning-agent activity | `reasoning_agent_activity(limit=, offset=)` | `reasoningAgentActivity({limit?, offset?})` | `GET /agents/reasoning/activity` |

### Episodic graph

| Purpose | Python | TypeScript | Endpoint |
| --- | --- | --- | --- |
| Graph stats | `graph_stats()` | `graphStats()` | `GET /graph/stats` |
| Topology | `topology(window_hours=, buckets=)` | `topology({windowHours?, buckets?})` | `GET /graph/topology` |
| Services | `services(status_filter=)` | `services({statusFilter?})` | `GET /graph/services` |
| Episodes | `episodes(**filters)` | `episodes(filters?)` | `GET /graph/episodes` |
| One episode | `get_episode(id)` | `getEpisode(id)` | `GET /graph/episodes/{id}` |
| Similar episodes | `similar_episodes(id, limit=)` | `similarEpisodes(id, {limit?})` | `GET /graph/episodes/{id}/similar` |

### Audit

| Purpose | Python | TypeScript | Endpoint |
| --- | --- | --- | --- |
| Audit trail | `audit_events(**filters)` | `auditEvents(filters?)` | `GET /audit/` |
| Event types | `audit_event_types()` | `auditEventTypes()` | `GET /audit/event-types` |

Filters: `limit`, `days`, `event_type`, `resource_type`, `actor_id`.

### Personal access tokens

| Purpose | Python | TypeScript | Endpoint |
| --- | --- | --- | --- |
| List tokens | `list_tokens()` | `listTokens()` | `GET /auth/tokens` |
| Create a token | `create_token(data)` | `createToken(data)` | `POST /auth/tokens` |
| Revoke | `revoke_token(id)` | `revokeToken(id)` | `DELETE /auth/tokens/{id}` |

The secret is returned **once**, from `create_token` only.

### Notifications

| Purpose | Python | TypeScript | Endpoint |
| --- | --- | --- | --- |
| Alert inbox | `notifications(**filters)` | `notifications(filters?)` | `GET /notifications/` |
| Unread count | `unread_count()` | `unreadCount()` | `GET /notifications/unread-count` |
| Mark read | `mark_read(data)` | `markRead(data)` | `POST /notifications/read` |
| Clear | `clear_notifications()` | `clearNotifications()` | `DELETE /notifications/` |

Filters: `limit`, `unread_only`, `severity`.

### Benchmark

| Purpose | Python | TypeScript | Endpoint |
| --- | --- | --- | --- |
| Evaluate an endpoint | `evaluate_endpoint(data)` | `evaluateEndpoint(data)` | `POST /benchmark/evaluate-endpoint` |
| Run status | `benchmark_status()` | `benchmarkStatus()` | `GET /benchmark/status` |
| Results | `benchmark_results()` | `benchmarkResults()` | `GET /benchmark/results` |

### Metrics

| Purpose | Python | TypeScript | Endpoint |
| --- | --- | --- | --- |
| Snapshot | `metrics()` | `metrics()` | `GET /metrics` |
| History | `metrics_history(limit=, agent=)` | `metricsHistory({limit?, agent?})` | `GET /metrics/history` |
| Latency | `metrics_latency(agent=)` | `metricsLatency({agent?})` | `GET /metrics/latency` |

### Chat

| Purpose | Python | TypeScript | Endpoint |
| --- | --- | --- | --- |
| One turn (non-streaming) | `chat(message, conversation_id=)` | `chat(message, {conversationId?})` | `POST /chat/` |
| RCA / planning analysis | `analyze(data)` | `analyze(data)` | `POST /chat/analyze` |
| List conversations | `list_conversations(limit=, offset=)` | `listConversations({limit?, offset?})` | `GET /chat/conversations` |
| One conversation | `get_conversation(id)` | `getConversation(id)` | `GET /chat/conversations/{id}` |
| Delete a conversation | `delete_conversation(id)` | `deleteConversation(id)` | `DELETE /chat/conversations/{id}` |
| Resolve a proposed action | `decide_chat_action(id, approved=, comment=)` | `decideChatAction(id, {approved, comment?})` | `POST /chat/actions/{id}/decision` |
| Stream a turn | `stream_chat(message, conversation_id=, on_delta=)` | `streamChat(message, handlers?, conversationId?)` | `POST /chat/stream` (SSE) |

`decide_chat_action` resolves the approve-to-run card a chat turn attaches in
approve/auto mode. It is distinct from `approve_action`, which acts on the
`/actions` queue. Its result `status` is `executed`, `refused` (gate declined), or
`rejected` (you declined).

#### Streaming

`stream_chat` returns the final `done` payload (whose `message.content` is
authoritative) and calls your delta handler as tokens arrive.

```python
result = client.stream_chat("why is nextcloud slow?", on_delta=lambda t: print(t, end=""))
print("\n", result["message"]["content"])
```

```ts
const result = await client.streamChat('why is nextcloud slow?', {
  onDelta: (t) => process.stdout.write(t),
  onToolResult: (r) => {},
  onDone: (payload) => {},
})
```

### Generative UI

The generative-UI surface is the opt-in, cost-fenced "Explain" layer behind the
dashboard widgets and the incident/graph copilots. See the
[Generative UI feature page](/features/generative-ui) for the product view.

| Purpose | Python | TypeScript | Endpoint |
| --- | --- | --- | --- |
| Explain computed data | `explain(kind, payload, tier="fast")` | `explain(kind, payload, {tier?})` | `POST /insights/explain` |
| Read opt-in + budget | `insight_preferences()` | `insightPreferences()` | `GET /insights/preferences` |
| Set opt-in | `set_insight_preferences(enabled=, auto_explain=)` | `setInsightPreferences({enabled?, autoExplain?})` | `PUT /insights/preferences` |

`explain` sends a widget's **already-computed** summary and returns a short,
labelled hypothesis. It **always** returns a uniform `ExplainResponse` — it never
throws for a disabled or over-budget widget, so you can render it without
special-casing status codes:

| Field | Type | Meaning |
| --- | --- | --- |
| `available` | bool | Whether an explanation was produced. Check this first. |
| `explanation` | string \| null | The model text, when `available`. |
| `model_generated` | bool | `true` when `available`. Label it as a hypothesis, not a measurement. |
| `reason` | string \| null | Why it is unavailable (see below), when `available` is `false`. |
| `tokens_used` | int \| null | Tokens billed against the fence. |
| `remaining` | int \| null | Remaining daily budget, or `null` when unlimited. |

**Kinds** (`kind`) select a bounded server-side prompt template. An unknown kind
falls back to `generic` rather than erroring. The exported `INSIGHT_KINDS`,
`INSIGHT_TIERS`, and `INSIGHT_UNAVAILABLE_REASONS` mirror this vocabulary.

| Kind | Explains | Typical tier |
| --- | --- | --- |
| `spike` | A detected metric spike | fast |
| `anomaly` | A statistical anomaly scan | fast |
| `diff` | What changed between two snapshots | fast |
| `blast_radius` | The downstream reach of a change | fast |
| `runbook` | A ranked learned runbook | fast |
| `next_best_action` | The next step from an incident timeline | reasoning |
| `graph_copilot` | An episodic-memory graph summary | reasoning |
| `incident` | A single incident's RCA + remediation | reasoning |
| `generic` | Any bounded payload | fast |

**Tiers** (`tier`): `fast` (default, a short caption) or `reasoning` (the heavier
tier for the incident and graph reads). Both are cost-fenced.

**Unavailable reasons** (`reason` when `available` is `false`): `ai_widgets_disabled`
(turn it on with `set_insight_preferences`), `no_endpoint`, `budget_reached`,
`empty`, `error`.

The [cookbook](/guide/sdk-cookbook#explain-a-dashboard-anomaly) has an
end-to-end example.

### Tools

The MCP tool registry the copilots and the agentic chat loop use.

| Purpose | Python | TypeScript | Endpoint |
| --- | --- | --- | --- |
| List tools | `tools()` | `tools()` | `GET /tools/` |
| One tool | `get_tool(name)` | `getTool(name)` | `GET /tools/{name}` |
| Execute a tool | `call_tool(name, parameters=, context=)` | `callTool(name, parameters?, {context?})` | `POST /tools/call` |

Read/analysis tools run directly; an action tool (restart/scale) passes the
constitutional gate. `call_tool` always returns a uniform `ToolCallResponse`
(`success`, `data`, `error`, `error_code`, `metadata` including the gate
`constitutional` verdict). A refusal is in the body, not a thrown error.

### The escape hatch

Anything not wrapped above is reachable with the generic request layer, which
returns the same decoded JSON and raises the same typed errors:

```python
data = client.request("GET", "/telemetry/logs", params={"service": "nextcloud"})
```

```ts
const data = await client.request('GET', '/telemetry/logs', { params: { service: 'nextcloud' } })
```

`paginate` works with any list endpoint that uses the standard envelope. To
extend the client, subclass it and add methods that call `self.request(...)` /
`this.request(...)`.

## The typed core

For full type safety over every one of the 127 paths, use the generated core. It
is generated from the committed OpenAPI snapshot (`openapi/openapi.json`) and
committed so the packages build offline.

```python
from constitutional_aiops_client import AuthenticatedClient
from constitutional_aiops_client.api.incidents import incidents_get_incident

client = AuthenticatedClient(base_url="https://your-instance.example.com", token="aiops_pat_...")
incident = incidents_get_incident.sync(incident_id="INC-2026-0007", client=client)
print(incident.id, incident.severity)
```

```ts
import { createTypedClient } from '@constitutional-aiops/sdk'

const api = createTypedClient({ baseUrl: 'https://your-instance.example.com', token: 'aiops_pat_...' })
const { data, error } = await api.GET('/api/v1/incidents/{incident_id}', {
  params: { path: { incident_id: 'inc-123' } },
})
```

Regenerate after the snapshot changes:

```bash
# Python (pinned toolchain for byte-identical output)
pip install "openapi-python-client==0.29.1" "ruff==0.15.8"
bash sdk/python/scripts/generate.sh

# TypeScript
cd sdk/typescript && npm run generate && npm run typecheck
```

The `sdk-drift` CI workflow regenerates both cores from the snapshot and fails on
any drift, and `ci-backend` checks the snapshot itself against the live app
(`python scripts/dump_openapi.py --check`), so the generated cores cannot silently
lag the API.

## Versioning and releases

Client `MAJOR.MINOR` tracks the API `MAJOR.MINOR`; `PATCH` is independent for
client-only fixes. Both packages share a version and are released together by
pushing an `sdk-v<version>` tag, which publishes to PyPI and npm tokenlessly via
OIDC Trusted Publishing. See `sdk/CHANGELOG.md` for the per-release history.
