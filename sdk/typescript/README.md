# @constitutional-aiops/sdk (TypeScript)

[![npm](https://img.shields.io/npm/v/%40constitutional-aiops%2Fsdk?logo=npm&label=npm)](https://www.npmjs.com/package/@constitutional-aiops/sdk)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://github.com/Partha-dev01/Constitutional-AIOps/blob/main/LICENSE)

Official TypeScript client for the Constitutional AIOps REST API. Two layers ship
together: a hand-written ergonomic client (`AIOpsClient`, no runtime dependency,
global `fetch`, Node 18+ or a browser) and a generated typed core
(`createTypedClient`, full type safety over the raw REST surface) that rides on
`openapi-fetch`. See the
[SDK overview](https://github.com/Partha-dev01/Constitutional-AIOps/tree/main/sdk)
for the full status. Using Python? See the sibling package
[`constitutional-aiops`](https://pypi.org/project/constitutional-aiops/) on PyPI.

Published to npm from CI with [provenance](https://docs.npmjs.com/generating-provenance-statements)
(OIDC Trusted Publishing), no long-lived token, so every release links back to the
exact source commit and build.

## Install

```bash
npm install @constitutional-aiops/sdk
```

## Use — ergonomic client

```ts
import { AIOpsClient, ConstitutionalRefusal } from '@constitutional-aiops/sdk'

const client = new AIOpsClient({
  baseUrl: 'https://your-instance.example.com',
  token: 'aiops_pat_...',
})

// List every critical incident (pagination handled for you).
for await (const incident of client.paginate('/incidents/', { severity: 'critical' })) {
  console.log(incident.id, incident.title)
}

// Approve a pending action. This still passes the constitutional gate.
try {
  await client.approveAction('act-123', { approved: true, approvedBy: 'me' })
} catch (error) {
  if (error instanceof ConstitutionalRefusal) console.log('gate held the action:', error.errorCode)
}

// Stream a chat turn.
const result = await client.streamChat('why is nextcloud slow?', {
  onDelta: (token) => process.stdout.write(token),
})
```

## What you can call (ergonomic client, 0.3.0)

Every method returns the decoded JSON. Constructor options: `baseUrl`, `token`,
`timeoutMs`, `maxRetries` (default 0), `backoffMs`.

- **Incidents:** `listIncidents`, `paginate('/incidents/')`, `getIncident`, `incidentStats`, `createIncident`, `updateIncident`, `similarIncidents`
- **Actions** (each still passes the constitutional gate): `listActions`, `getAction`, `pendingActions`, `createAction`, `approveAction`, `executeAction`, `cancelAction`, `actionStats`, `confidenceFormula`
- **Agents:** `fastAgentStats`, `fastAgentActivity`, `reasoningAgentStats`, `reasoningAgentActivity`
- **Episodic graph:** `graphStats`, `topology`, `services`, `episodes`, `getEpisode`, `similarEpisodes`
- **Audit:** `auditEvents`, `auditEventTypes`
- **Tokens (self-service PAT):** `listTokens`, `createToken`, `revokeToken`
- **Notifications:** `notifications`, `unreadCount`, `markRead`, `clearNotifications`
- **Benchmark:** `evaluateEndpoint`, `benchmarkStatus`, `benchmarkResults`
- **Metrics:** `metrics`, `metricsHistory`, `metricsLatency`
- **Chat:** `chat`, `streamChat`, `analyze`, `listConversations`, `getConversation`, `deleteConversation`, `decideChatAction`
- **Generative UI** (opt-in, cost-fenced insight widgets): `explain`, `insightPreferences`, `setInsightPreferences` (plus the exported `INSIGHT_KINDS`, `INSIGHT_TIERS`, `INSIGHT_UNAVAILABLE_REASONS` and their types)
- **Tools** (the MCP registry the copilots and agentic loop share): `tools`, `getTool`, `callTool`

Anything not wrapped here is reachable through the typed core (below) or the
generic escape hatch `client.request(method, path, { params, body })`.

### Generative UI (the "Explain" surface)

`explain` powers the dashboard "Explain" buttons: send a widget's already-computed
summary, get back a short, labelled, model-generated hypothesis. Opt-in per user
and cost-fenced, and it always resolves with a uniform result.

```ts
await client.setInsightPreferences({ enabled: true }) // opt in once

const res = await client.explain('anomaly', { count: 3, top: [{ series: 'cpu', z: 4.1 }] })
if (res.available) {
  console.log(res.explanation) // model_generated; a hypothesis, not a measurement
} else {
  console.log('no explanation:', res.reason) // e.g. no_endpoint, budget_reached
}
```

**Opt-in retries.** `new AIOpsClient({ baseUrl, maxRetries: 2 })` retries a 429 on
any method and 5xx or network failures on GET only, with exponential backoff that
honors a `Retry-After` header. The default (`maxRetries: 0`) never retries.

## Use — typed core

For full type safety over every endpoint, use the generated client. Paths, path
and query params, request bodies and responses are all checked against the API's
OpenAPI schema.

```ts
import { createTypedClient } from '@constitutional-aiops/sdk'

const api = createTypedClient({
  baseUrl: 'https://your-instance.example.com',
  token: 'aiops_pat_...',
})

const { data, error } = await api.GET('/api/v1/incidents/{incident_id}', {
  params: { path: { incident_id: 'inc-123' } },
})
```

## Regenerating the types

`src/schema.d.ts` is generated from the committed API snapshot
(`openapi/openapi.json`) by [`openapi-typescript`](https://openapi-ts.dev). It is
committed so the package builds offline; regenerate it whenever the snapshot
changes:

```bash
npm install
npm run generate     # openapi-typescript ../../openapi/openapi.json -o src/schema.d.ts
npm run typecheck
```

## Auth

Create a personal access token in the app (Settings, or `POST /api/v1/auth/tokens`)
and pass it as `token`; it is sent as `Authorization: Bearer aiops_pat_...` and
resolves to your user even when `AUTH_REQUIRED` is off, so calls are attributed
and cost-fenced. Against a single-user instance with `AUTH_REQUIRED` unset the
token is optional.

## License

AGPL-3.0-or-later, matching the app.
