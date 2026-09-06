/**
 * Pure helpers for the Dashboard "Learned Runbook" widget (Track 2 widget).
 *
 * Ranks remediation actions by how well they have worked historically, scoring
 * each group by success rate weighted by how often it was used. Computed entirely
 * from the existing actions list, no LLM and no new backend endpoint. Kept out of
 * the component so the grouping and scoring stay unit testable.
 *
 * Only terminal outcomes count: 'completed' is a success, 'failed' is a failure.
 * Non-terminal statuses (pending, validating, awaiting_approval, approved,
 * executing, ...) are ignored so a queued action never distorts a ranking.
 */

export interface RunbookEntry {
  key: string
  succeeded: number
  failed: number
  used: number
  successRate: number
  score: number
}

interface RankInput {
  action_type: string
  target_service?: string
  status: string
}

interface RankOptions {
  by?: 'action' | 'service'
}

/**
 * Rank remediation groups by score (successRate * used), highest first.
 *
 * Groups by action_type by default, or by target_service when opts.by is
 * 'service' (rows with no target_service are skipped in that mode). Groups with
 * no terminal outcomes are excluded. Ties break by used desc then key asc so the
 * order is stable.
 */
export function rankRunbook(actions: RankInput[], opts?: RankOptions): RunbookEntry[] {
  const byService = opts?.by === 'service'
  const groups = new Map<string, { succeeded: number; failed: number }>()

  for (const action of actions) {
    const key = byService ? action.target_service : action.action_type
    if (!key) continue // no target_service in service mode - skip

    const terminal = action.status === 'completed' || action.status === 'failed'
    if (!terminal) continue

    const bucket = groups.get(key) ?? { succeeded: 0, failed: 0 }
    if (action.status === 'completed') bucket.succeeded += 1
    else bucket.failed += 1
    groups.set(key, bucket)
  }

  const entries: RunbookEntry[] = []
  for (const [key, { succeeded, failed }] of groups) {
    const used = succeeded + failed
    if (used === 0) continue // no terminal outcomes - nothing learned
    const successRate = succeeded / used
    entries.push({ key, succeeded, failed, used, successRate, score: successRate * used })
  }

  entries.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score
    if (b.used !== a.used) return b.used - a.used
    return a.key < b.key ? -1 : a.key > b.key ? 1 : 0
  })

  return entries
}
