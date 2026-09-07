/**
 * GraphCopilot - an opt-in, reasoning-tier "explain my incident memory" panel
 * for the Episodic Knowledge Graph page (Track 2 W3).
 *
 * The graph itself is computed and rendered without an LLM. This panel only
 * appears when the user has turned on AI insight widgets, and only calls the
 * cost-fenced /insights/explain endpoint on demand (never on mount). It sends a
 * bounded summary of the graph (counts + strongest root causes / actions /
 * services + the incidents worth attention) and asks the REASONING tier for a
 * short read of the dominant failure themes and where to focus. The answer is
 * always framed as a model hypothesis, never as measured telemetry.
 */

import { useState } from 'react'
import { Network, Sparkles, Loader2 } from 'lucide-react'
import { api } from '../lib/api'
import { useAiWidgets } from '../lib/useAiWidgets'
import { AiGenerated } from './ui/AiGenerated'
import { graphCopilotExplainPayload, reasonLabel, type GraphCopilotInput } from '../lib/insights'

export function GraphCopilot({ input }: { input: GraphCopilotInput | null }) {
  const ai = useAiWidgets()
  const [explaining, setExplaining] = useState(false)
  const [explanation, setExplanation] = useState<string | null>(null)
  const [note, setNote] = useState<string | null>(null)

  const hasData = input != null && input.stats.episodes + input.stats.services > 0

  const onExplain = async () => {
    if (input == null) return
    setExplaining(true)
    setNote(null)
    setExplanation(null)
    try {
      const res = await api.insights.explain(
        'graph_copilot',
        graphCopilotExplainPayload(input),
        'reasoning',
      )
      if (res.available && res.explanation) setExplanation(res.explanation)
      else setNote(reasonLabel(res.reason))
    } catch {
      setNote(reasonLabel('error'))
    } finally {
      setExplaining(false)
    }
  }

  // Opt-in only, and only when there is a graph to reason about.
  if (!ai.enabled || !hasData) return null

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-2 flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Network className="h-4 w-4" aria-hidden="true" />
          Graph copilot
        </h2>
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
            {explaining ? 'Reading the graph…' : 'Explain this graph'}
          </button>
        )}
      </div>
      <p className="text-xs text-muted-foreground">
        A reasoning-tier read of what this incident memory suggests: the dominant failure
        themes, which remediations have actually worked, and where to focus next.
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

export default GraphCopilot
