/**
 * Official TypeScript client for the Constitutional AIOps REST API.
 *
 * Pre-release scaffold, no runtime dependencies (global fetch). See ../README.md.
 *
 * ```ts
 * import { AIOpsClient } from '@constitutional-aiops/sdk'
 *
 * const client = new AIOpsClient({ baseUrl: 'https://your-instance.example.com', token: 'caiops_pat_...' })
 * for await (const incident of client.paginate('/incidents/', { severity: 'critical' })) {
 *   console.log(incident.id, incident.title)
 * }
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
