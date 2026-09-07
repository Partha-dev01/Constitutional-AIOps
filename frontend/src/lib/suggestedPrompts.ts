/**
 * Suggested-prompt helpers for the empty Chat state.
 *
 * Prompts are split into a curated default set plus a small, de-duped ring of
 * the user's most recent queries (persisted in localStorage) so returning
 * users see what they last asked. Selection is pure; persistence is isolated
 * to the two helpers below and degrades silently when storage is unavailable
 * (private mode, quota, SSR).
 */

// Deployment-agnostic defaults: they showcase the product without hard-wiring a
// specific service or backend, so they work on the lite tier (no LGTM/Neo4j)
// just as well as the full stack. The old set named nextcloud/neo4j/prometheus
// and forced tool calls that hard-fail when those backends are not deployed.
export const DEFAULT_PROMPTS: string[] = [
  'Summarize the current health of my system',
  'Which services are running right now?',
  'How would you diagnose a sudden spike in errors?',
  'What does the constitutional safety gate do before an action runs?',
]

const RECENTS_KEY = 'aiops.chat.recentPrompts'
const MAX_RECENTS = 5
const MAX_PROMPTS = 6

/**
 * A recent query is worth resurfacing as a chip only if it reads like a real
 * question, not a one-word reply (`yes`, `ok`, `no`) that leaked into the ring.
 * Requires a little length and more than one word, which filters trivial turns
 * without touching genuine questions. Applied on read, write, and selection so
 * junk already sitting in localStorage is dropped the next time chips render.
 */
export function isSubstantivePrompt(prompt: string): boolean {
  const trimmed = prompt.trim()
  return trimmed.length >= 10 && /\s/.test(trimmed)
}

/** Read the recent-query ring from localStorage. Never throws. */
export function getRecentPrompts(): string[] {
  try {
    const raw = window.localStorage.getItem(RECENTS_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
      .filter((p): p is string => typeof p === 'string')
      .filter(isSubstantivePrompt)
      .slice(0, MAX_RECENTS)
  } catch {
    return []
  }
}

/**
 * Prepend a freshly-issued query to the recent ring (most-recent first,
 * de-duped, capped). Returns the updated list. Never throws.
 */
export function pushRecentPrompt(query: string): string[] {
  const trimmed = query.trim()
  if (!isSubstantivePrompt(trimmed)) return getRecentPrompts()
  const existing = getRecentPrompts().filter(
    (p) => p.toLowerCase() !== trimmed.toLowerCase(),
  )
  const next = [trimmed, ...existing].slice(0, MAX_RECENTS)
  try {
    window.localStorage.setItem(RECENTS_KEY, JSON.stringify(next))
  } catch {
    // Storage unavailable — recents are best-effort only.
  }
  return next
}

/**
 * Build the chip list: recent user queries first (de-duped against defaults,
 * case-insensitively), then defaults, capped at MAX_PROMPTS.
 */
export function selectPrompts(
  recent: string[] = getRecentPrompts(),
  defaults: string[] = DEFAULT_PROMPTS,
): string[] {
  const seen = new Set<string>()
  const out: string[] = []
  // Filter recents (defaults are curated and always substantive) so a trivial
  // recent never leaks through even when a caller passes a raw list.
  for (const prompt of [...recent.filter(isSubstantivePrompt), ...defaults]) {
    const key = prompt.trim().toLowerCase()
    if (!key || seen.has(key)) continue
    seen.add(key)
    out.push(prompt)
    if (out.length >= MAX_PROMPTS) break
  }
  return out
}
