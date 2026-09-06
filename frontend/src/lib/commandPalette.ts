/**
 * Pure helpers for the global command palette (Cmd/Ctrl-K).
 *
 * The palette is a zero-dependency quick-nav over the app's own routes: type a
 * few characters, get a ranked list, Enter to navigate. Keeping the match and
 * ranking logic here (out of the component) makes it unit-testable and keeps
 * the component file export-clean for fast-refresh, exactly like the sibling
 * pure helpers in ./activity and ./approvalTicker.
 *
 * Matching is a case-insensitive fuzzy pass: an exact title beats a prefix
 * beats a substring beats a scattered subsequence, and a title hit always
 * outranks one that only landed in the group label or a keyword. An empty
 * query returns every command in its declared order (the "browse all" view).
 */

export interface PaletteCommand {
  /** Stable id (also the React key). */
  id: string
  /** Primary label shown and searched at full weight. */
  title: string
  /** Optional section label (e.g. "Observe"), searched at low weight. */
  group?: string
  /** Extra search terms not shown as the title (synonyms), low weight. */
  keywords?: string[]
  /** Router path to navigate to on select. Omit when `action` is set. */
  href?: string
  /** Run on select instead of navigating (e.g. open a modal). Takes priority. */
  action?: () => void
}

/**
 * Score `query` against a single text, or null when `query` is not even a
 * subsequence of it. Higher is better. An empty query scores 0 (matches all).
 */
export function matchText(text: string, query: string): number | null {
  const q = query.toLowerCase()
  if (!q) return 0
  const t = text.toLowerCase()
  if (t === q) return 1000
  const idx = t.indexOf(q)
  if (idx === 0) return 700 // prefix
  if (idx > 0) return 500 - Math.min(idx, 100) // substring, earlier is better
  // Scattered subsequence: every query char in order, penalize the gaps.
  let ti = 0
  let gaps = 0
  let last = -1
  for (const ch of q) {
    let found = -1
    while (ti < t.length) {
      if (t[ti] === ch) {
        found = ti
        ti += 1
        break
      }
      ti += 1
    }
    if (found === -1) return null
    if (last >= 0) gaps += found - last - 1
    last = found
  }
  return 200 - Math.min(gaps, 150)
}

/**
 * Best score for a command across its title (full weight) and its group +
 * keywords (kept a full tier below any title hit), or null if nothing matched.
 */
export function scoreCommand(cmd: PaletteCommand, query: string): number | null {
  const q = query.trim()
  if (!q) return 0
  const title = matchText(cmd.title, q)
  if (title !== null) return title + 1000
  let best: number | null = null
  for (const field of [cmd.group ?? '', ...(cmd.keywords ?? [])]) {
    if (!field) continue
    const s = matchText(field, q)
    if (s !== null) best = best === null ? s : Math.max(best, s)
  }
  return best
}

/**
 * Filter + rank commands for `query`. An empty query keeps the declared order;
 * matches sort by score descending, ties broken by original position (stable).
 */
export function rankCommands(
  commands: PaletteCommand[],
  query: string,
): PaletteCommand[] {
  const q = query.trim()
  if (!q) return commands.slice()
  const scored: { cmd: PaletteCommand; i: number; score: number }[] = []
  commands.forEach((cmd, i) => {
    const score = scoreCommand(cmd, q)
    if (score !== null) scored.push({ cmd, i, score })
  })
  scored.sort((a, b) => b.score - a.score || a.i - b.i)
  return scored.map((x) => x.cmd)
}
