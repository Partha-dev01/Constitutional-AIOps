/**
 * Typed-core example: full type safety over the raw REST surface.
 * Paths, params and responses are checked against the committed OpenAPI snapshot.
 *
 *   AIOPS_URL=https://your-instance.example.com AIOPS_TOKEN=... npx tsx examples/typed.ts
 */

import { createTypedClient } from '../src/index'

async function main(): Promise<void> {
  const api = createTypedClient({
    baseUrl: process.env.AIOPS_URL ?? 'http://localhost:8000',
    token: process.env.AIOPS_TOKEN,
  })

  // Path, query and response are all inferred from the schema.
  const { data, error } = await api.GET('/api/v1/incidents/', {
    params: { query: { page: 1, page_size: 25 } },
  })
  if (error) {
    console.error('request failed:', error)
    return
  }
  console.log(`Incidents: ${data.total}`)
  for (const incident of data.items) {
    console.log(`  ${incident.id}  ${incident.severity}  ${incident.title}`)
  }
}

void main()
