/**
 * Official TypeScript client for the Constitutional AIOps REST API.
 *
 * Pre-release scaffold, no runtime dependencies (global fetch). See ../README.md.
 *
 * ```ts
 * import { AIOpsClient } from '@constitutional-aiops/sdk'
 *
 * const client = new AIOpsClient({ baseUrl: 'https://your-instance.example.com', token: 'aiops_pat_...' })
 * for await (const incident of client.paginate('/incidents/', { severity: 'critical' })) {
 *   console.log(incident.id, incident.title)
 * }
 * ```
 *
 * For full type safety over the raw REST surface, use the generated typed core:
 *
 * ```ts
 * import { createTypedClient } from '@constitutional-aiops/sdk'
 *
 * const api = createTypedClient({ baseUrl: 'https://your-instance.example.com', token: 'aiops_pat_...' })
 * const { data } = await api.GET('/api/v1/incidents/{incident_id}', {
 *   params: { path: { incident_id: 'inc-123' } },
 * })
 * ```
 */

export { AIOpsClient } from './client'
export type { AIOpsClientOptions, Page, StreamChatHandlers } from './client'
export {
  AIOpsError,
  AuthError,
  ConstitutionalRefusal,
  NotFound,
  RateLimited,
  CONSTITUTIONAL_CODES,
} from './errors'
export type { ConstitutionalCode } from './errors'

// Generated typed core (openapi-fetch over openapi-typescript output).
export { createTypedClient } from './typed'
export type { TypedClient, TypedClientOptions } from './typed'
export type { paths, components, operations } from './schema'
