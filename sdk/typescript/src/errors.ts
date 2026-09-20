/**
 * Typed error hierarchy for the Constitutional AIOps client. Mirrors the Python
 * client. The one domain-specific error is ConstitutionalRefusal, thrown when the
 * safety gate blocks an action or holds it for approval. That is the product
 * working as designed, so it carries the gate's own verdict.
 */

export class AIOpsError extends Error {
  readonly status?: number
  readonly details?: unknown

  constructor(message: string, options: { status?: number; details?: unknown } = {}) {
    super(message)
    this.name = 'AIOpsError'
    this.status = options.status
    this.details = options.details
  }
}

export class AuthError extends AIOpsError {
  constructor(message: string, options: { status?: number; details?: unknown } = {}) {
    super(message, options)
    this.name = 'AuthError'
  }
}

export class NotFound extends AIOpsError {
  constructor(message: string, options: { status?: number; details?: unknown } = {}) {
    super(message, options)
    this.name = 'NotFound'
  }
}

/**
 * 429. A per-user cost fence or throttle rejected the call.
 *
 * `retryAfter` is the server's Retry-After header in seconds when it sent one,
 * and undefined otherwise. The hourly windows on chat, tools and actions send
 * it, so a caller that catches this can wait the stated time instead of
 * guessing.
 */
export class RateLimited extends AIOpsError {
  readonly retryAfter?: number

  constructor(
    message: string,
    options: { status?: number; details?: unknown; retryAfter?: number } = {},
  ) {
    super(message, options)
    this.name = 'RateLimited'
    this.retryAfter = options.retryAfter
  }
}

export const CONSTITUTIONAL_CODES = [
  'action_tools_disabled',
  'approval_required',
  'validation_blocked',
  'container_not_whitelisted',
] as const

export type ConstitutionalCode = (typeof CONSTITUTIONAL_CODES)[number]

export class ConstitutionalRefusal extends AIOpsError {
  readonly errorCode?: string
  readonly verdict?: unknown

  constructor(
    message: string,
    options: { errorCode?: string; verdict?: unknown; status?: number } = {},
  ) {
    super(message, { status: options.status, details: options.verdict })
    this.name = 'ConstitutionalRefusal'
    this.errorCode = options.errorCode
    this.verdict = options.verdict
  }
}
