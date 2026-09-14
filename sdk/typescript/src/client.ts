/**
 * A small, dependency-free client over the Constitutional AIOps REST API using
 * the global `fetch` (Node 18+ and browsers). This is the hand-written ergonomic
 * layer; the generated, fully typed core (openapi-typescript + openapi-fetch)
 * slots underneath it (see ../README.md).
 *
 * Since 0.2.0 the ergonomic surface spans the high-value tags an operator or
 * script actually reaches: incidents, actions (through the constitutional gate),
 * agents, the episodic graph, audit, notifications, benchmark, metrics, chat, and
 * self-service personal access tokens. 0.3.0 adds the generative-UI insight
 * widgets (`explain` + preferences), the MCP tool registry (`tools`/`getTool`/
 * `callTool`), and chat decisions (`decideChatAction`/`deleteConversation`). The
 * long tail stays on the typed core.
 */

import {
  AIOpsError,
  AuthError,
  ConstitutionalRefusal,
  CONSTITUTIONAL_CODES,
  NotFound,
  RateLimited,
} from './errors'

export interface AIOpsClientOptions {
  /** Instance origin, e.g. https://host.example.com. `/api/v1` is appended. */
  baseUrl: string
  /** Bearer token: a personal access token (aiops_pat_...) or a session token. */
  token?: string
  /** Per-request timeout in ms. */
  timeoutMs?: number
  /**
   * How many times to retry a transient failure. 0 (default) never retries. A 429
   * is retried on any method; 5xx and network errors are retried only for GET, so
   * a POST is never silently resent. Backoff is exponential and honors Retry-After.
   */
  maxRetries?: number
  /** Base backoff in ms; attempt n waits backoffMs * 2**n unless Retry-After is set. */
  backoffMs?: number
}

/** The uniform list envelope every paginated endpoint returns. */
export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface StreamChatHandlers {
  onDelta?: (chunk: string) => void
  onToolResult?: (result: unknown) => void
  onDone?: (payload: Record<string, unknown>) => void
  onError?: (error: AIOpsError) => void
}

type Json = Record<string, unknown>
type Query = Record<string, unknown>

const RETRY_ANY_METHOD = new Set([429])
const RETRY_GET_ONLY = new Set([502, 503, 504])

/**
 * Generative-UI `explain` vocabulary, mirrored from the server. `kind` selects a
 * bounded server-side prompt template; an unknown kind falls back to "generic"
 * rather than erroring, so a new widget can ship its client first.
 */
export const INSIGHT_KINDS = [
  'spike',
  'anomaly',
  'diff',
  'blast_radius',
  'next_best_action',
  'runbook',
  'graph_copilot',
  'incident',
  'generic',
] as const
export type InsightKind = (typeof INSIGHT_KINDS)[number]

/** The fast tier writes a short caption; reasoning is the heavier tier for the
 * deeper incident/graph reads. Both are cost-fenced. */
export const INSIGHT_TIERS = ['fast', 'reasoning'] as const
export type InsightTier = (typeof INSIGHT_TIERS)[number]

/** When `ExplainResponse.available` is false, `reason` is one of these. */
export const INSIGHT_UNAVAILABLE_REASONS = [
  'ai_widgets_disabled',
  'budget_reached',
  'no_endpoint',
  'empty',
  'error',
] as const
export type InsightUnavailableReason = (typeof INSIGHT_UNAVAILABLE_REASONS)[number]

export class AIOpsClient {
  private readonly base: string
  private readonly token?: string
  private readonly timeoutMs: number
  private readonly maxRetries: number
  private readonly backoffMs: number

  constructor(options: AIOpsClientOptions) {
    const trimmed = options.baseUrl.replace(/\/+$/, '')
    this.base = trimmed.endsWith('/api/v1') ? trimmed : `${trimmed}/api/v1`
    this.token = options.token
    this.timeoutMs = options.timeoutMs ?? 90_000
    this.maxRetries = Math.max(0, options.maxRetries ?? 0)
    this.backoffMs = Math.max(0, options.backoffMs ?? 500)
  }

  /** Issue one request and return the decoded JSON, throwing a typed error. */
  async request<T = unknown>(
    method: string,
    path: string,
    options: { params?: Query; body?: unknown } = {},
  ): Promise<T> {
    const verb = method.toUpperCase()
    const url = this.url(path, options.params)
    const headers: Record<string, string> = { Accept: 'application/json' }
    if (options.body !== undefined) headers['Content-Type'] = 'application/json'
    if (this.token) headers.Authorization = `Bearer ${this.token}`

    let attempt = 0
    for (;;) {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), this.timeoutMs)
      let response: Response
      try {
        response = await fetch(url, {
          method: verb,
          headers,
          body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
          signal: controller.signal,
        })
      } catch (cause) {
        if (verb === 'GET' && attempt < this.maxRetries) {
          await this.sleep(attempt, null)
          attempt += 1
          continue
        }
        throw new AIOpsError(`request failed: ${String(cause)}`)
      } finally {
        clearTimeout(timer)
      }

      if (!response.ok) {
        if (this.retryable(verb, response.status) && attempt < this.maxRetries) {
          await this.sleep(attempt, response)
          attempt += 1
          continue
        }
        throw await this.toError(response)
      }
      const text = await response.text()
      return (text ? JSON.parse(text) : undefined) as T
    }
  }

  /** Yield every item across pages of a list endpoint. */
  async *paginate<T = Record<string, unknown>>(
    path: string,
    filters: Query = {},
    pageSize = 50,
  ): AsyncGenerator<T> {
    let page = 1
    for (;;) {
      const payload = await this.request<Page<T>>('GET', path, {
        params: { page, page_size: pageSize, ...filters },
      })
      for (const item of payload.items ?? []) yield item
      if (!payload.has_more) return
      page += 1
    }
  }

  // ── incidents ──────────────────────────────────────────────────────────────
  listIncidents(filters: Query = {}): Promise<Page<Json>> {
    return this.request('GET', '/incidents/', { params: filters })
  }

  getIncident(id: string): Promise<Json> {
    return this.request('GET', `/incidents/${id}`)
  }

  incidentStats(): Promise<Json> {
    return this.request('GET', '/incidents/stats')
  }

  createIncident(data: Json): Promise<Json> {
    return this.request('POST', '/incidents/', { body: data })
  }

  updateIncident(id: string, data: Json): Promise<Json> {
    return this.request('PATCH', `/incidents/${id}`, { body: data })
  }

  similarIncidents(id: string, opts: { limit?: number } = {}): Promise<Json> {
    return this.request('GET', `/incidents/${id}/similar`, { params: { limit: opts.limit } })
  }

  // ── actions (every method still passes the constitutional gate) ─────────────
  listActions(filters: Query = {}): Promise<Page<Json>> {
    return this.request('GET', '/actions/', { params: filters })
  }

  getAction(id: string): Promise<Json> {
    return this.request('GET', `/actions/${id}`)
  }

  pendingActions(): Promise<Json> {
    return this.request('GET', '/actions/pending')
  }

  /** Propose an action. The validator may hold it for approval or block it. */
  createAction(data: Json): Promise<Json> {
    return this.request('POST', '/actions/', { body: data })
  }

  /** Approve or reject a pending action. Still passes the constitutional gate. */
  approveAction(
    id: string,
    input: { approved: boolean; approvedBy: string; comments?: string },
  ): Promise<unknown> {
    return this.request('POST', `/actions/${id}/approve`, {
      body: { approved: input.approved, approved_by: input.approvedBy, comments: input.comments ?? '' },
    })
  }

  /** Execute an approved action. The kill-switch and validator still apply. */
  executeAction(id: string): Promise<unknown> {
    return this.request('POST', `/actions/${id}/execute`)
  }

  cancelAction(id: string, opts: { reason?: string } = {}): Promise<unknown> {
    return this.request('POST', `/actions/${id}/cancel`, { params: { reason: opts.reason } })
  }

  actionStats(): Promise<Json> {
    return this.request('GET', '/actions/stats')
  }

  /** The graduated-autonomy confidence formula the gate uses. */
  confidenceFormula(): Promise<Json> {
    return this.request('GET', '/actions/confidence/formula')
  }

  // ── agents ───────────────────────────────────────────────────────────────────
  fastAgentStats(): Promise<Json> {
    return this.request('GET', '/agents/fast/stats')
  }

  fastAgentActivity(opts: { limit?: number; offset?: number } = {}): Promise<Json> {
    return this.request('GET', '/agents/fast/activity', { params: { limit: opts.limit, offset: opts.offset } })
  }

  reasoningAgentStats(): Promise<Json> {
    return this.request('GET', '/agents/reasoning/stats')
  }

  reasoningAgentActivity(opts: { limit?: number; offset?: number } = {}): Promise<Json> {
    return this.request('GET', '/agents/reasoning/activity', { params: { limit: opts.limit, offset: opts.offset } })
  }

  // ── episodic graph ────────────────────────────────────────────────────────────
  graphStats(): Promise<Json> {
    return this.request('GET', '/graph/stats')
  }

  topology(opts: { windowHours?: number; buckets?: number } = {}): Promise<Json> {
    return this.request('GET', '/graph/topology', { params: { window_hours: opts.windowHours, buckets: opts.buckets } })
  }

  services(opts: { statusFilter?: string } = {}): Promise<Json> {
    return this.request('GET', '/graph/services', { params: { status_filter: opts.statusFilter } })
  }

  /** Episodic-memory episodes. Filters: limit, since_hours, min_confidence and more. */
  episodes(filters: Query = {}): Promise<Json> {
    return this.request('GET', '/graph/episodes', { params: filters })
  }

  getEpisode(id: string): Promise<Json> {
    return this.request('GET', `/graph/episodes/${id}`)
  }

  similarEpisodes(id: string, opts: { limit?: number } = {}): Promise<Json> {
    return this.request('GET', `/graph/episodes/${id}/similar`, { params: { limit: opts.limit } })
  }

  // ── audit ────────────────────────────────────────────────────────────────────
  /** The audit trail. Filters: limit, days, event_type, resource_type, actor_id. */
  auditEvents(filters: Query = {}): Promise<Json> {
    return this.request('GET', '/audit/', { params: filters })
  }

  auditEventTypes(): Promise<unknown> {
    return this.request('GET', '/audit/event-types')
  }

  // ── personal access tokens (self-service) ────────────────────────────────────
  listTokens(): Promise<unknown> {
    return this.request('GET', '/auth/tokens')
  }

  /** Mint a personal access token. The secret is returned once, here only. */
  createToken(data: Json): Promise<Json> {
    return this.request('POST', '/auth/tokens', { body: data })
  }

  revokeToken(id: string): Promise<unknown> {
    return this.request('DELETE', `/auth/tokens/${id}`)
  }

  // ── notifications ─────────────────────────────────────────────────────────────
  /** The alert inbox. Filters: limit, unread_only, severity. */
  notifications(filters: Query = {}): Promise<Json> {
    return this.request('GET', '/notifications/', { params: filters })
  }

  unreadCount(): Promise<Json> {
    return this.request('GET', '/notifications/unread-count')
  }

  markRead(data: Json): Promise<unknown> {
    return this.request('POST', '/notifications/read', { body: data })
  }

  clearNotifications(): Promise<unknown> {
    return this.request('DELETE', '/notifications/')
  }

  // ── benchmark (reproduce the paper, or evaluate your own endpoint) ────────────
  /** Run a few sample cases through the configured endpoint and score them. */
  evaluateEndpoint(data: Json): Promise<Json> {
    return this.request('POST', '/benchmark/evaluate-endpoint', { body: data })
  }

  benchmarkStatus(): Promise<Json> {
    return this.request('GET', '/benchmark/status')
  }

  benchmarkResults(): Promise<unknown> {
    return this.request('GET', '/benchmark/results')
  }

  // ── metrics ────────────────────────────────────────────────────────────────────
  metrics(): Promise<Json> {
    return this.request('GET', '/metrics')
  }

  metricsHistory(opts: { limit?: number; agent?: string } = {}): Promise<Json> {
    return this.request('GET', '/metrics/history', { params: { limit: opts.limit, agent: opts.agent } })
  }

  metricsLatency(opts: { agent?: string } = {}): Promise<Json> {
    return this.request('GET', '/metrics/latency', { params: { agent: opts.agent } })
  }

  // ── chat ──────────────────────────────────────────────────────────────────────
  /** One non-streaming chat turn. Use streamChat for token-by-token output. */
  chat(message: string, opts: { conversationId?: string } = {}): Promise<Json> {
    const body: Json = { message }
    if (opts.conversationId) body.conversation_id = opts.conversationId
    return this.request('POST', '/chat/', { body })
  }

  /** Root-cause analysis over supplied context (the reasoning agent). */
  analyze(data: Json): Promise<Json> {
    return this.request('POST', '/chat/analyze', { body: data })
  }

  listConversations(opts: { limit?: number; offset?: number } = {}): Promise<unknown> {
    return this.request('GET', '/chat/conversations', { params: { limit: opts.limit, offset: opts.offset } })
  }

  getConversation(id: string): Promise<Json> {
    return this.request('GET', `/chat/conversations/${id}`)
  }

  deleteConversation(id: string): Promise<unknown> {
    return this.request('DELETE', `/chat/conversations/${id}`)
  }

  /** Approve or reject a chat-proposed remediation (the approve-to-run card).
   * Distinct from approveAction (which acts on the /actions queue): this resolves
   * the proposed_action a chat turn attached. Execution still passes the
   * constitutional gate; `status` is 'executed', 'refused' or 'rejected'. */
  decideChatAction(actionId: string, input: { approved: boolean; comment?: string }): Promise<Json> {
    const body: Json = { approved: input.approved }
    if (input.comment !== undefined) body.comment = input.comment
    return this.request('POST', `/chat/actions/${actionId}/decision`, { body })
  }

  /** Stream a chat turn, resolving with the final `done` payload. */
  async streamChat(
    message: string,
    handlers: StreamChatHandlers = {},
    conversationId?: string,
  ): Promise<Record<string, unknown>> {
    const headers: Record<string, string> = {
      Accept: 'text/event-stream',
      'Content-Type': 'application/json',
    }
    if (this.token) headers.Authorization = `Bearer ${this.token}`

    const response = await fetch(this.url('/chat/stream'), {
      method: 'POST',
      headers,
      body: JSON.stringify(conversationId ? { message, conversation_id: conversationId } : { message }),
    })
    if (!response.ok || !response.body) throw await this.toError(response)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let done: Record<string, unknown> = {}

    for (;;) {
      const { value, done: finished } = await reader.read()
      if (finished) break
      buffer += decoder.decode(value, { stream: true })
      const frames = buffer.split('\n\n')
      buffer = frames.pop() ?? ''
      for (const frame of frames) {
        let event = 'message'
        let data = ''
        for (const line of frame.split('\n')) {
          if (line.startsWith('event:')) event = line.slice(6).trim()
          else if (line.startsWith('data:')) data += line.slice(5).trim()
        }
        if (!data) continue
        const parsed = JSON.parse(data) as Record<string, unknown>
        if (event === 'delta') handlers.onDelta?.(String(parsed.content ?? ''))
        else if (event === 'tool_result') handlers.onToolResult?.(parsed)
        else if (event === 'done') {
          done = parsed
          handlers.onDone?.(parsed)
        } else if (event === 'error') {
          const err = new AIOpsError(String(parsed.message ?? 'chat stream error'))
          handlers.onError?.(err)
          throw err
        }
      }
    }
    return done
  }

  // ── generative UI (opt-in, cost-fenced insight explanations) ─────────────────
  /** Ask the model to explain a widget's already-computed data — the generative-UI
   * surface behind the dashboard "Explain" buttons. `kind` selects a bounded
   * server-side prompt template (see INSIGHT_KINDS); `payload` is the small
   * computed summary the widget already shows; `tier` is 'fast' (default) or
   * 'reasoning'. Always resolves with an ExplainResponse (never throws for a
   * disabled or over-budget widget): check `available`, and on false read
   * `reason` (one of INSIGHT_UNAVAILABLE_REASONS). Opt-in per user
   * (setInsightPreferences) and cost-fenced. */
  explain(kind: InsightKind | string, payload: Json, opts: { tier?: InsightTier } = {}): Promise<Json> {
    return this.request('POST', '/insights/explain', {
      body: { kind, tier: opts.tier ?? 'fast', payload },
    })
  }

  /** The per-user insight-widget opt-in state plus the fence budget snapshot. */
  insightPreferences(): Promise<Json> {
    return this.request('GET', '/insights/preferences')
  }

  /** Turn the opt-in LLM insight widgets on or off (per user). An omitted field is
   * left unchanged, so you can flip one flag without reading the other first. */
  setInsightPreferences(prefs: { enabled?: boolean; autoExplain?: boolean }): Promise<Json> {
    const body: Json = {}
    if (prefs.enabled !== undefined) body.enabled = prefs.enabled
    if (prefs.autoExplain !== undefined) body.autoExplain = prefs.autoExplain
    return this.request('PUT', '/insights/preferences', { body })
  }

  // ── tools (the MCP registry the copilots and agentic loop share) ─────────────
  /** List the available tools: read/analysis tools plus gated action tools (each
   * action tool reports `enabled` / `gated_by`). */
  tools(): Promise<Json> {
    return this.request('GET', '/tools/')
  }

  getTool(toolName: string): Promise<Json> {
    return this.request('GET', `/tools/${toolName}`)
  }

  /** Execute a tool and return the uniform ToolCallResponse. Read/analysis tools
   * run directly; an action tool (restart/scale) passes the constitutional gate
   * first. Always a 200-level result: read `success`, and on refusal `error_code`
   * (e.g. 'action_tools_disabled', 'approval_required'). A gate refusal is in the
   * body, not thrown as a ConstitutionalRefusal. */
  callTool(toolName: string, parameters: Json = {}, opts: { context?: Json } = {}): Promise<Json> {
    const body: Json = { tool_name: toolName, parameters }
    if (opts.context !== undefined) body.context = opts.context
    return this.request('POST', '/tools/call', { body })
  }

  private url(path: string, params?: Query): string {
    let url = `${this.base}/${path.replace(/^\/+/, '')}`
    if (params) {
      const search = new URLSearchParams()
      for (const [key, value] of Object.entries(params)) {
        if (value === undefined || value === null) continue
        if (Array.isArray(value)) value.forEach((v) => search.append(key, String(v)))
        else search.append(key, String(value))
      }
      const query = search.toString()
      if (query) url += `?${query}`
    }
    return url
  }

  private retryable(method: string, status: number): boolean {
    if (RETRY_ANY_METHOD.has(status)) return true
    return method === 'GET' && RETRY_GET_ONLY.has(status)
  }

  private async sleep(attempt: number, response: Response | null): Promise<void> {
    let delay = this.backoffMs * 2 ** attempt
    const retryAfter = response?.headers.get('Retry-After')
    if (retryAfter) {
      const seconds = Number(retryAfter)
      if (!Number.isNaN(seconds)) delay = Math.min(seconds * 1000, 60_000)
    }
    if (delay > 0) await new Promise((resolve) => setTimeout(resolve, delay))
  }

  private async toError(response: Response): Promise<AIOpsError> {
    let detail: unknown
    let errorCode: string | undefined
    try {
      const parsed = (await response.json()) as unknown
      detail =
        parsed && typeof parsed === 'object' && 'detail' in parsed
          ? (parsed as { detail: unknown }).detail
          : parsed
      if (detail && typeof detail === 'object' && 'error_code' in detail) {
        errorCode = String((detail as { error_code: unknown }).error_code)
      }
    } catch {
      detail = undefined
    }
    const message = detail ? String(typeof detail === 'object' ? JSON.stringify(detail) : detail) : response.statusText
    const status = response.status

    if (errorCode && (CONSTITUTIONAL_CODES as readonly string[]).includes(errorCode)) {
      return new ConstitutionalRefusal(message, { errorCode, verdict: detail, status })
    }
    if (status === 401) return new AuthError(message, { status, details: detail })
    if (status === 404) return new NotFound(message, { status, details: detail })
    if (status === 429) return new RateLimited(message, { status, details: detail })
    return new AIOpsError(message, { status, details: detail })
  }
}
