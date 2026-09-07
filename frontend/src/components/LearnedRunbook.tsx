/**
 * LearnedRunbook - a Dashboard widget that ranks remediation actions by how well
 * they have worked historically, success rate weighted by how often each was used
 * (Track 2 widget). Read-only and no-LLM: the ranking is computed client-side from
 * the actions the system already records. Only terminal outcomes count, so the
 * order reflects real completed/failed history, not queued proposals.
 */

import { useEffect, useState } from 'react'
import { BookOpen, TrendingUp, CheckCircle, Sparkles, Loader2 } from 'lucide-react'
import { cn } from '../lib/utils'
import { api } from '../lib/api'
import { rankRunbook, type RunbookEntry } from '../lib/learnedRunbook'
import { useAiWidgets } from '../lib/useAiWidgets'
import { AiGenerated } from './ui/AiGenerated'
import { learnedRunbookExplainPayload, reasonLabel } from '../lib/insights'

/** Humanize an action_type key (restart_service -> "Restart service"). */
function humanize(key: string): string {
  const spaced = key.replace(/_/g, ' ').trim()
  if (!spaced) return key
  return spaced.charAt(0).toUpperCase() + spaced.slice(1)
}

/** Color the success-rate chip by how reliable the action has been. */
function rateStyle(rate: number): string {
  if (rate >= 0.9) return 'bg-green-500/15 text-green-600 dark:text-green-400'
  if (rate >= 0.6) return 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
  return 'bg-red-500/15 text-red-600 dark:text-red-400'
}

export function LearnedRunbook({ max = 6 }: { max?: number }) {
  const [entries, setEntries] = useState<RunbookEntry[]>([])
  const [loading, setLoading] = useState(true)

  // Opt-in LLM explain (Track 2 W3): on-demand only, never on mount.
  const ai = useAiWidgets()
  const [explaining, setExplaining] = useState(false)
  const [explanation, setExplanation] = useState<string | null>(null)
  const [explainNote, setExplainNote] = useState<string | null>(null)

  const onExplain = async () => {
    setExplaining(true)
    setExplainNote(null)
    setExplanation(null)
    try {
      const res = await api.insights.explain('runbook', learnedRunbookExplainPayload(entries))
      if (res.available && res.explanation) setExplanation(res.explanation)
      else setExplainNote(reasonLabel(res.reason))
    } catch {
      setExplainNote(reasonLabel('error'))
    } finally {
      setExplaining(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      try {
        const res = await api.actions.list({ page_size: 200 })
        if (cancelled) return
        const rows = (res?.items ?? []).map((a) => ({
          action_type: a.action_type,
          target_service: a.target_service,
          status: a.status,
        }))
        setEntries(rankRunbook(rows))
      } catch {
        if (!cancelled) setEntries([])
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => {
      cancelled = true
    }
  }, [])

  const shown = entries.slice(0, max)

  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <div className="mb-1 flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <BookOpen className="h-5 w-5" />
          Learned runbook
          {entries.length > 0 && (
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
              {entries.length}
            </span>
          )}
        </h2>
      </div>
      <p className="mb-4 text-xs text-muted-foreground">
        Remediation actions ranked by past success rate, weighted by how often each ran.
      </p>

      {loading ? (
        <div className="py-8 text-center text-sm text-muted-foreground">
          Reading remediation history...
        </div>
      ) : shown.length === 0 ? (
        <div className="py-8 text-center text-muted-foreground">
          <BookOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No remediation history yet</p>
          <p className="text-xs mt-1">
            Successful and failed actions build this ranking over time.
          </p>
        </div>
      ) : (
        <ul className="space-y-2">
          {shown.map((entry, index) => (
            <li
              key={entry.key}
              className="rounded-lg border border-border/60 bg-muted/30 px-3 py-2"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="truncate text-sm font-medium">
                  <span className="mr-2 text-xs text-muted-foreground">#{index + 1}</span>
                  {humanize(entry.key)}
                </p>
                <span
                  className={cn(
                    'shrink-0 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
                    rateStyle(entry.successRate),
                  )}
                >
                  <TrendingUp className="h-3 w-3" aria-hidden="true" />
                  {Math.round(entry.successRate * 100)}%
                </span>
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <span className="inline-flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" aria-hidden="true" />
                  {entry.succeeded}/{entry.used} succeeded
                </span>
                <span>
                  {entry.used} {entry.used === 1 ? 'run' : 'runs'}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}

      {ai.enabled && entries.length > 0 && (
        <div className="mt-4 border-t border-border/60 pt-3">
          {explanation ? (
            <AiGenerated>{explanation}</AiGenerated>
          ) : (
            <button
              type="button"
              onClick={() => void onExplain()}
              disabled={explaining}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted disabled:opacity-50"
            >
              {explaining ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
              ) : (
                <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
              )}
              {explaining ? 'Explaining…' : 'Explain this runbook'}
            </button>
          )}
          {explainNote && <p className="mt-2 text-xs text-muted-foreground">{explainNote}</p>}
        </div>
      )}
    </div>
  )
}

export default LearnedRunbook
