/**
 * A small, dependency-free client over the Constitutional AIOps REST API using
 * the global `fetch` (Node 18+ and browsers). This is the hand-written ergonomic
 * layer; the generated, fully typed core (openapi-typescript + openapi-fetch)
 * slots underneath it later. The surface here is stable.
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

export class AIOpsClient {
  private readonly base: string
  private readonly token?: string
  private readonly timeoutMs: number

  constructor(options: AIOpsClientOptions) {
    const trimmed = options.baseUrl.replace(/\/+$/, '')
    this.base = trimmed.endsWith('/api/v1') ? trimmed : `${trimmed}/api/v1`
    this.token = options.token
    this.timeoutMs = options.timeoutMs ?? 90_000
  }

  /** Issue one request and return the decoded JSON, throwing a typed error. */
  async request<T = unknown>(
    method: string,
    path: string,
    options: { params?: Record<string, unknown>; body?: unknown } = {},
  ): Promise<T> {
    const url = this.url(path, options.params)
    const headers: Record<string, string> = { Accept: 'application/json' }
    if (options.body !== undefined) headers['Content-Type'] = 'application/json'
    if (this.token) headers.Authorization = `Bearer ${this.token}`

    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), this.timeoutMs)
    let response: Response
    try {
      response = await fetch(url, {
        method: method.toUpperCase(),
        headers,
        body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      })
    } catch (cause) {
      throw new AIOpsError(`request failed: ${String(cause)}`)
    } finally {
      clearTimeout(timer)
    }

    if (!response.ok) throw await this.toError(response)
    const text = await response.text()
    return (text ? JSON.parse(text) : undefined) as T
  }

  /** Yield every item across pages of a list endpoint. */
  async *paginate<T = Record<string, unknown>>(
    path: string,
    filters: Record<string, unknown> = {},
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

  listIncidents(filters: Record<string, unknown> = {}): Promise<Page<Record<string, unknown>>> {
    return this.request('GET', '/incidents/', { params: filters })
  }

  getIncident(id: string): Promise<Record<string, unknown>> {
    return this.request('GET', `/incidents/${id}`)
  }

  pendingActions(): Promise<Record<string, unknown>> {
    return this.request('GET', '/actions/pending')
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

  private url(path: string, params?: Record<string, unknown>): string {
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
