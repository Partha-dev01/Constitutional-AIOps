/**
 * Suggested-prompt helpers for the empty Chat state.
 *
 * Prompts are split into a curated default set plus a small, de-duped ring of
 * the user's most recent queries (persisted in localStorage) so returning
 * users see what they last asked. Selection is pure; persistence is isolated
 * to the two helpers below and degrades silently when storage is unavailable
 * (private mode, quota, SSR).
 */

export const DEFAULT_PROMPTS: string[] = [
  'Show similar past incidents for nextcloud',
  'What are the dependencies of neo4j?',
  'Analyze recent error logs for prometheus',
  'Summarize current system health',
]

const RECENTS_KEY = 'aiops.chat.recentPrompts'
const MAX_RECENTS = 5
const MAX_PROMPTS = 6

/** Read the recent-query ring from localStorage. Never throws. */
export function getRecentPrompts(): string[] {
  try {
    const raw = window.localStorage.getItem(RECENTS_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter((p): p is string => typeof p === 'string').slice(0, MAX_RECENTS)
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
  if (!trimmed) return getRecentPrompts()
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
  for (const prompt of [...recent, ...defaults]) {
    const key = prompt.trim().toLowerCase()
    if (!key || seen.has(key)) continue
    seen.add(key)
    out.push(prompt)
    if (out.length >= MAX_PROMPTS) break
  }
  return out
}
