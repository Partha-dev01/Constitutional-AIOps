/**
 * Typed core for the Constitutional AIOps SDK.
 *
 * `createTypedClient` returns an openapi-fetch client whose paths, path/query
 * params, request bodies and responses are all checked against the committed
 * OpenAPI snapshot (`openapi/openapi.json`, regenerated into `schema.d.ts` by
 * `npm run generate`). Reach for it when you want full type safety over the raw
 * REST surface; reach for the hand-written `AIOpsClient` when you want the
 * ergonomic helpers (pagination, chat streaming, typed errors). Both talk to the
 * same instance and pass the same constitutional gate.
 */

import createClient, { type Client } from 'openapi-fetch'
import type { paths } from './schema'

export interface TypedClientOptions {
  /**
   * Instance origin, for example `https://host.example.com`. The generated
   * paths already carry the `/api/v1` prefix, so a trailing `/api/v1` on the
   * URL is accepted and trimmed rather than doubled.
   */
  baseUrl: string
  /**
   * Bearer token: a personal access token (`aiops_pat_...`) or a session token
   * you already hold. Optional against an instance running with `AUTH_REQUIRED`
   * unset.
   */
  token?: string
  /** Extra default headers merged into every request. */
  headers?: Record<string, string>
  /** Custom fetch implementation (defaults to the global `fetch`). */
  fetch?: typeof fetch
}

/** The fully-typed openapi-fetch client over the Constitutional AIOps API. */
export type TypedClient = Client<paths>

/**
 * Build a fully-typed client over the REST surface.
 *
 * ```ts
 * const api = createTypedClient({ baseUrl: 'https://host.example.com', token: 'aiops_pat_...' })
 * const { data, error } = await api.GET('/api/v1/incidents/{incident_id}', {
 *   params: { path: { incident_id: 'inc-123' } },
 * })
 * ```
 */
export function createTypedClient(options: TypedClientOptions): TypedClient {
  const origin = options.baseUrl.replace(/\/+$/, '').replace(/\/api\/v1$/, '')
  const headers: Record<string, string> = { ...options.headers }
  if (options.token) headers.Authorization = `Bearer ${options.token}`
  return createClient<paths>({
    baseUrl: origin,
    headers,
    ...(options.fetch ? { fetch: options.fetch } : {}),
  })
}
