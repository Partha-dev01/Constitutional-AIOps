# @constitutional-aiops/sdk (TypeScript)

Official TypeScript client for the Constitutional AIOps REST API. Two layers ship
together: a hand-written ergonomic client (`AIOpsClient`, no runtime dependency,
global `fetch`, Node 18+ or a browser) and a generated typed core
(`createTypedClient`, full type safety over the raw REST surface) that rides on
`openapi-fetch`. See `../README.md` for the full status.

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
