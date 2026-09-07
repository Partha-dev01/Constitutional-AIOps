/**
 * IncidentCopilot - an opt-in, reasoning-tier "explain this incident" panel for
 * the incident detail view (Track 2 W3).
 *
 * The incident's own fields (severity, status, affected services, any computed
 * RCA + causal chain, any planned remediation) are rendered without an LLM. This
 * panel only appears when the user has turned on AI insight widgets, and only
 * calls the cost-fenced /insights/explain endpoint on demand (never on mount). It
 * sends a bounded summary of the one incident and asks the REASONING tier for a
 * short read of what most likely happened and the single most useful next step.
 * The answer is always framed as a model hypothesis, never as measured telemetry.
 */

import { useState } from 'react'
import { Activity, Sparkles, Loader2 } from 'lucide-react'
import { api, type Incident } from '../../lib/api'
import { useAiWidgets } from '../../lib/useAiWidgets'
import { AiGenerated } from '../ui/AiGenerated'
import { incidentExplainPayload, reasonLabel } from '../../lib/insights'

export function IncidentCopilot({ incident }: { incident: Incident }) {
  const ai = useAiWidgets()
  const [explaining, setExplaining] = useState(false)
  const [explanation, setExplanation] = useState<string | null>(null)
  const [note, setNote] = useState<string | null>(null)

  const onExplain = async () => {
    setExplaining(true)
    setNote(null)
    setExplanation(null)
    try {
      const payload = incidentExplainPayload({
        title: incident.title,
        severity: incident.severity,
        status: incident.status,
        category: incident.category,
        description: incident.description,
        services: (incident.affected_services ?? []).map((s) => s.name),
        rootCause: incident.rca?.root_cause,
        rootCauseConfidence: incident.rca?.confidence,
        causalChain: incident.rca?.causal_chain ?? [],
        remediationSteps: (incident.remediation_plan?.steps ?? []).map((s) => s.action),
      })
      const res = await api.insights.explain('incident', payload, 'reasoning')
      if (res.available && res.explanation) setExplanation(res.explanation)
      else setNote(reasonLabel(res.reason))
    } catch {
      setNote(reasonLabel('error'))
    } finally {
      setExplaining(false)
    }
  }

  // Opt-in only: no button, no spend, until the user turns AI widgets on.
  if (!ai.enabled) return null

  return (
    <div className="rounded-lg border border-border bg-card p-4" data-testid="incident-copilot">
      <div className="mb-2 flex items-center justify-between gap-3">
        <h4 className="flex items-center gap-2 text-sm font-semibold">
          <Activity className="h-4 w-4" aria-hidden="true" />
          Incident copilot
        </h4>
        {!explanation && (
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
            {explaining ? 'Reading the incident…' : 'Explain this incident'}
          </button>
        )}
      </div>
      <p className="text-xs text-muted-foreground">
        A reasoning-tier read of what most likely happened here and the single most useful next
        step, grounded in this incident's own fields.
      </p>
      {explanation && (
        <div className="mt-3">
          <AiGenerated>{explanation}</AiGenerated>
        </div>
      )}
      {note && <p className="mt-2 text-xs text-muted-foreground">{note}</p>}
    </div>
  )
}

export default IncidentCopilot
