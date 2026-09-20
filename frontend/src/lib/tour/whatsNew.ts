/**
 * whatsNew - version-gated "what's new" notes plus the tour/what's-new flags.
 *
 * All per-browser, stored in localStorage and read through try/catch so a
 * private window or disabled storage degrades to sensible defaults rather than
 * throwing. The pure helpers (parseVersion / compareVersions / entriesSince)
 * are side-effect free so they unit-test without a DOM.
 *
 * Coordination: a brand-new browser (no lastSeen recorded) is greeted by the
 * first-run tour, not the what's-new banner; the banner is for a returning user
 * who last saw an older version. Keep APP_VERSION in sync with package.json.
 */

/** Current app version. Bump alongside frontend/package.json "version". */
export const APP_VERSION = '1.1.0'

export interface ReleaseNote {
  version: string
  date: string
  title: string
  items: string[]
}

/** Newest first. Only list real, shipped, user-facing changes. */
export const WHATS_NEW: ReleaseNote[] = [
  {
    version: '1.1.0',
    date: 'September 2026',
    title: "What's new in 1.1",
    items: [
      'Approving, executing and remediating now require an admin account',
      'The approver in the audit trail is taken from your session, so it always names the real person',
      'Chat, tool calls and actions now have hourly limits, which keeps a runaway loop from running up a bill',
      'A personal LLM endpoint has to be a public address; an admin can still point the whole instance at localhost',
    ],
  },
  {
    version: '1.0.0',
    date: 'September 2026',
    title: "What's new in 1.0",
    items: [
      'A guided product tour and this what’s-new panel',
      'New capacity-forecast and metric-correlation insight widgets on the dashboard',
      'Opt-in, cost-fenced AI explanations across metrics, incidents and the graph',
      'Graph-episodic memory now runs on the lite tier with no external database',
      'Command palette: press Ctrl or Command K to jump to any page',
    ],
  },
]

const TOUR_KEY = 'aiops.tour.completed'
const WHATSNEW_KEY = 'aiops.whatsNew.lastSeenVersion'

/** Parse a dotted version into numeric parts; missing parts read as 0. */
export function parseVersion(v: string): number[] {
  return String(v)
    .split('.')
    .map((p) => {
      const n = Number.parseInt(p, 10)
      return Number.isFinite(n) ? n : 0
    })
}

/** Compare two dotted versions: -1 if a<b, 0 if equal, 1 if a>b. */
export function compareVersions(a: string, b: string): number {
  const pa = parseVersion(a)
  const pb = parseVersion(b)
  const len = Math.max(pa.length, pb.length)
  for (let i = 0; i < len; i++) {
    const da = pa[i] ?? 0
    const db = pb[i] ?? 0
    if (da !== db) return da < db ? -1 : 1
  }
  return 0
}

/**
 * Notes strictly newer than `lastSeen`, capped at APP_VERSION so a future-dated
 * entry never leaks early. Newest first (as authored).
 */
export function entriesSince(lastSeen: string, notes: ReleaseNote[] = WHATS_NEW): ReleaseNote[] {
  return notes.filter(
    (n) => compareVersions(n.version, lastSeen) > 0 && compareVersions(n.version, APP_VERSION) <= 0,
  )
}

function readLS(key: string): string | null {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

function writeLS(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value)
  } catch {
    /* ignore storage failures (private mode / disabled) */
  }
}

export function tourCompleted(): boolean {
  return readLS(TOUR_KEY) === 'true'
}

export function markTourCompleted(): void {
  writeLS(TOUR_KEY, 'true')
}

export function whatsNewLastSeen(): string | null {
  return readLS(WHATSNEW_KEY)
}

export function markWhatsNewSeen(version: string = APP_VERSION): void {
  writeLS(WHATSNEW_KEY, version)
}

const SPOTLIGHT_KEY = 'aiops.tour.spotlight.completed'
const SPOTLIGHT_PENDING_KEY = 'aiops.tour.spotlight.pending'

/** The upgraded spotlight tour has been completed or skipped once (per browser). */
export function spotlightTourCompleted(): boolean {
  return readLS(SPOTLIGHT_KEY) === 'true'
}

export function markSpotlightTourCompleted(): void {
  writeLS(SPOTLIGHT_KEY, 'true')
}

/**
 * Session-scoped handoff: "the user just finished setup, start the tour on the
 * next app view". sessionStorage (not localStorage) so it fires once, right
 * after setup, and never re-arms in a later session.
 */
export function markSpotlightTourPending(): void {
  try {
    window.sessionStorage.setItem(SPOTLIGHT_PENDING_KEY, '1')
  } catch {
    /* ignore storage failures (private mode / disabled) */
  }
}

export function spotlightTourPending(): boolean {
  try {
    return window.sessionStorage.getItem(SPOTLIGHT_PENDING_KEY) === '1'
  } catch {
    return false
  }
}

export function clearSpotlightTourPending(): void {
  try {
    window.sessionStorage.removeItem(SPOTLIGHT_PENDING_KEY)
  } catch {
    /* ignore storage failures (private mode / disabled) */
  }
}

/** First-run: auto-open the tour until it has been completed or skipped once. */
export function shouldAutoStartTour(): boolean {
  return !tourCompleted()
}

/**
 * What's-new notes to surface now. Empty for a brand-new browser (no lastSeen
 * recorded) so the tour, not the banner, greets first-run users.
 */
export function pendingWhatsNew(): ReleaseNote[] {
  const last = whatsNewLastSeen()
  if (!last) return []
  return entriesSince(last)
}
