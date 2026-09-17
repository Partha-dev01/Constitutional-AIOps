/**
 * MetricCorrelation - a Dashboard widget that finds metric series that moved
 * together over the window via pairwise Pearson correlation (Track 2, the
 * no-LLM half). Read-only maths: it computes the coefficients client-side and
 * never proposes an action. The label is explicit that correlation is not
 * causation. The opt-in reasoning-tier "Explain" is the only LLM touch.
 */

import { useEffect, useState } from 'react'
import { Activity, Sparkles, Loader2 } from 'lucide-react'
import { api } from '../lib/api'
import { groupSeries } from '../lib/metricSeries'
import { correlateSeries, type CorrelationPair } from '../lib/metricCorrelation'
import { useAiWidgets } from '../lib/useAiWidgets'
import { AiGenerated } from './ui/AiGenerated'
import { metricCorrelationExplainPayload, reasonLabel } from '../lib/insights'

export function MetricCorrelation({ max = 6 }: { max?: number }) {
  const [pairs, setPairs] = useState<CorrelationPair[]>([])
  const [hasMetrics, setHasMetrics] = useState(false)
  const [loading, setLoading] = useState(true)

  const ai = useAiWidgets()
  const [explaining, setExplaining] = useState(false)
  const [explanation, setExplanation] = useState<string | null>(null)
  const [explainNote, setExplainNote] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      try {
        const res = await api.telemetry.metrics({ range: '1h' })
        if (cancelled) return
        const points = res?.metrics ?? []
        setHasMetrics(points.length > 0)
        setPairs(correlateSeries(groupSeries(points), { max }))
      } catch {
        if (!cancelled) {
          setPairs([])
          setHasMetrics(false)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => {
      cancelled = true
    }
  }, [max])

  const onExplain = async () => {
    setExplaining(true)
    setExplainNote(null)
    setExplanation(null)
    try {
      const res = await api.insights.explain(
        'correlation',
        metricCorrelationExplainPayload(pairs),
        'reasoning',
      )
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
      <div className="mb-1 flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Metric correlation
          {pairs.length > 0 && (
            <span className="rounded-full bg-blue-500/15 px-2 py-0.5 text-xs font-medium text-blue-600 dark:text-blue-400">
              {pairs.length}
            </span>
          )}
        </h2>
      </div>
      <p className="mb-4 text-xs text-muted-foreground">
        Series that moved together this hour (Pearson r). Correlation is not causation.
      </p>

      {loading ? (
        <div className="py-8 text-center text-sm text-muted-foreground">Correlating series...</div>
      ) : pairs.length === 0 ? (
        <div className="py-8 text-center text-muted-foreground">
          <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No strongly correlated metric pairs.</p>
          <p className="text-xs mt-1">
            {hasMetrics
              ? 'No two series moved closely together in this window.'
              : 'Connect a monitoring source to correlate metrics.'}
          </p>
        </div>
      ) : (
        <ul className="space-y-2">
          {pairs.map((pair) => {
            const positive = pair.r >= 0
            return (
              <li
                key={`${pair.a}|${pair.b}`}
                className="rounded-lg border border-border/60 bg-muted/30 px-3 py-2"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="min-w-0 truncate text-sm font-medium">
                    {pair.a} <span className="text-muted-foreground">&harr;</span> {pair.b}
                  </p>
                  <span
                    className={
                      positive
                        ? 'shrink-0 rounded-full bg-blue-500/15 px-2 py-0.5 text-xs font-medium text-blue-600 dark:text-blue-400'
                        : 'shrink-0 rounded-full bg-purple-500/15 px-2 py-0.5 text-xs font-medium text-purple-600 dark:text-purple-400'
                    }
                  >
                    r {pair.r.toFixed(2)}
                  </span>
                </div>
                <div className="mt-1 text-xs text-muted-foreground">
                  {positive ? 'move together' : 'move inversely'} · {pair.n} samples
                </div>
              </li>
            )
          })}
        </ul>
      )}

      {ai.enabled && pairs.length > 0 && (
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
              {explaining ? 'Explaining…' : 'Explain these correlations'}
            </button>
          )}
          {explainNote && <p className="mt-2 text-xs text-muted-foreground">{explainNote}</p>}
        </div>
      )}
    </div>
  )
}

export default MetricCorrelation
