/**
 * Saved views (Track 2 QoL) — a per-browser quick-access list of named filter
 * presets for a page whose filters live in the URL query string (e.g. the
 * Incidents page). A "view" is just a saved query string; applying one re-writes
 * the URL, so views layer on top of the existing deep-linkable filters without
 * any new state model.
 *
 * Storage is localStorage, scoped per page and keyed per browser — the same
 * convention the sidebar-collapsed preference uses. Cross-device sharing is
 * already covered by the deep-link URL (copy the address); saved views are the
 * local "jump back to a filter I use a lot" convenience on top of that. The
 * array operations are pure so they unit-test without touching storage; the thin
 * load/save wrappers swallow storage errors (private windows, quota, blocked
 * site data) because a missing convenience must never break the page.
 */

export interface SavedView {
  /** Stable id (also the React key). */
  id: string
  /** User-given label. */
  name: string
  /** URL query string without a leading '?', e.g. "status=pending_approval". */
  query: string
}

const PREFIX = 'aiops.savedViews.'

/** localStorage key for a page scope, e.g. viewsKey('incidents'). */
export function viewsKey(scope: string): string {
  return `${PREFIX}${scope}`
}

/** Drop a leading '?' so stored queries are canonical. */
export function normalizeQuery(query: string): string {
  return query.replace(/^\?/, '')
}

function makeId(): string {
  return `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}`
}

/**
 * Parse a raw localStorage string into a clean SavedView[]. Anything malformed
 * (not JSON, not an array, wrong-shaped entries) yields []. Never throws.
 */
export function parseViews(raw: string | null): SavedView[] {
  if (!raw) return []
  try {
    const data = JSON.parse(raw)
    if (!Array.isArray(data)) return []
    return data
      .filter(
        (v): v is SavedView =>
          !!v &&
          typeof v.id === 'string' &&
          typeof v.name === 'string' &&
          typeof v.query === 'string',
      )
      .map((v) => ({ id: v.id, name: v.name, query: normalizeQuery(v.query) }))
  } catch {
    return []
  }
}

/**
 * Add (or, when the name already exists case-insensitively, overwrite) a view.
 * An empty/whitespace name is a no-op — returns the input unchanged. Pure.
 */
export function addView(views: SavedView[], name: string, query: string): SavedView[] {
  const trimmed = name.trim()
  if (!trimmed) return views
  const q = normalizeQuery(query)
  const without = views.filter(
    (v) => v.name.toLowerCase() !== trimmed.toLowerCase(),
  )
  return [...without, { id: makeId(), name: trimmed, query: q }]
}

/** Remove the view with the given id. Pure. */
export function removeView(views: SavedView[], id: string): SavedView[] {
  return views.filter((v) => v.id !== id)
}

/** Load a scope's saved views from localStorage; [] on any error. */
export function loadViews(scope: string): SavedView[] {
  try {
    return parseViews(window.localStorage.getItem(viewsKey(scope)))
  } catch {
    return []
  }
}

/** Persist a scope's saved views; silently no-ops when storage is unavailable. */
export function saveViews(scope: string, views: SavedView[]): void {
  try {
    window.localStorage.setItem(viewsKey(scope), JSON.stringify(views))
  } catch {
    /* private window / quota / blocked site data — a convenience, so ignore */
  }
}
