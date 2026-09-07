/**
 * IncidentNarrative - a Dashboard widget that replays the live incident
 * lifecycle as a per-incident staged timeline (detected -> root cause ->
 * remediation planned -> action -> resolved). Read-only and no-LLM: purely a
 * view over the NarrativeEntry list the parent builds from WebSocket events.
 * It opens no socket and fetches nothing itself, matching the ApprovalTicker /
 * Recent Activity presentational idiom.
 *
 * The opt-in "Next best action" overlay (Track 2 W3) is the one reasoning-tier
 * widget: it asks the caller's own reasoning model for the least-invasive next
 * step given the timeline. On-demand only, never on mount, and only when the
 * user has turned AI insight widgets on.
 */

import { useEffect, useMemo, useState } from 'react'
import { GitBranch, Sparkles, Loader2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { groupByIncident, type NarrativeEntry } from '../lib/incidentNarrative'
import { useAiWidgets } from '../lib/useAiWidgets'
import { AiGenerated } from './ui/AiGenerated'
import { incidentNarrativeExplainPayload, reasonLabel } from '../lib/insights'
import { api } from '../lib/api'

const DOT: Record<NarrativeEntry['severity'], string> = {
  info: 'bg-blue-500',
  success: 'bg-green-500',
  warning: 'bg-yellow-500',
  error: 'bg-red-500',
}

/** Relative "3 minutes ago" label, guarding against an unparseable timestamp. */
function relativeTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return formatDistanceToNow(d, { addSuffix: true })
}

export function IncidentNarrative({ items }: { items: NarrativeEntry[] }) {
  const groups = useMemo(() => groupByIncident(items), [items])

  // Opt-in reasoning-tier explain (Track 2 W3): on-demand only, never on mount.
  const ai = useAiWidgets()
  const [explaining, setExplaining] = useState(false)
  const [explanation, setExplanation] = useState<string | null>(null)
  const [explainNote, setExplainNote] = useState<string | null>(null)

  // A newly-active incident is a new question, so drop any prior answer when the
  // most-recently-active incident changes.
  const topId = groups[0]?.incidentId ?? ''
  useEffect(() => {
    setExplanation(null)
    setExplainNote(null)
  }, [topId])

  const onExplain = async () => {
    setExplaining(true)
    setExplainNote(null)
    setExplanation(null)
    try {
      const payload = incidentNarrativeExplainPayload(groups)
      const res = await api.insights.explain('next_best_action', payload, 'reasoning')
      if (res.available && res.explanation) setExplanation(res.explanation)
      else setExplainNote(reasonLabel(res.reason))
    } catch {
      setExplainNote(reasonLabel('error'))
    } finally {
      setExplaining(false)
    }
  }

  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <GitBranch className="h-5 w-5" />
          Live Incident Narrative
        </h2>
        {groups.length > 0 && (
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
            {groups.length}
          </span>
        )}
      </div>
      {groups.length === 0 ? (
        <div className="py-8 text-center text-muted-foreground">
          <GitBranch className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No live incident activity</p>
          <p className="text-xs mt-1">
            Incidents fill in here as they move through detection, root-cause analysis, and
            remediation.
          </p>
        </div>
      ) : (
        <ul className="space-y-4">
          {groups.map((group) => (
            <li
              key={group.incidentId}
              className="rounded-lg border border-border/60 bg-muted/30 px-3 py-2"
            >
              <p className="mb-2 truncate font-mono text-xs text-muted-foreground">
                {group.incidentId}
              </p>
              <ol className="space-y-1">
                {group.stages.map((entry) => (
                  <li key={entry.id} className="flex items-center gap-3">
                    <span className={`h-2 w-2 shrink-0 rounded-full ${DOT[entry.severity]}`} />
                    <span className="min-w-0 flex-1 truncate text-sm font-medium">{entry.label}</span>
                    <time
                      className="shrink-0 text-xs text-muted-foreground"
                      dateTime={entry.at}
                      title={new Date(entry.at).toLocaleString()}
                    >
                      {relativeTime(entry.at)}
                    </time>
                  </li>
                ))}
              </ol>
            </li>
          ))}
        </ul>
      )}

      {ai.enabled && groups.length > 0 && (
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
              {explaining ? 'Thinking…' : 'Suggest next best action'}
            </button>
          )}
          {explainNote && <p className="mt-2 text-xs text-muted-foreground">{explainNote}</p>}
        </div>
      )}
    </div>
  )
}

export default IncidentNarrative
