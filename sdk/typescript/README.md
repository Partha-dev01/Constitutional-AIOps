# @constitutional-aiops/sdk (TypeScript)

Official TypeScript client for the Constitutional AIOps REST API. Pre-release
scaffold, no runtime dependencies (global `fetch`, Node 18+ or a browser). See
`../README.md` for the full status and the generated-core plan.

## Use

```ts
import { AIOpsClient, ConstitutionalRefusal } from '@constitutional-aiops/sdk'

const client = new AIOpsClient({
  baseUrl: 'https://your-instance.example.com',
  token: 'caiops_pat_...',
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

## Auth note

Personal access tokens are planned. Until they ship, run against an instance with
`AUTH_REQUIRED` unset, or pass a session token as `token`.

## License

AGPL-3.0-or-later, matching the app.
