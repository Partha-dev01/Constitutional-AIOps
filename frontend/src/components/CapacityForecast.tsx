/**
 * CapacityForecast - a Dashboard widget that fits a naive linear trend to each
 * utilization metric series and estimates when it would reach a threshold
 * (Track 2, the no-LLM half). Read-only maths: it never calls an LLM for the
 * projection and never proposes an action, it only points at a series worth a
 * human look. The label stays honest - this is a linear extrapolation, not a
 * guarantee. The opt-in reasoning-tier "Explain" is the only LLM touch.
 */

import { useEffect, useState } from 'react'
import { TrendingUp, AlertTriangle, Sparkles, Loader2 } from 'lucide-react'
import { api } from '../lib/api'
import { groupSeries } from '../lib/metricSeries'
import { forecastSeries, isUtilizationSeries, type Forecast } from '../lib/capacityForecast'
import { useAiWidgets } from '../lib/useAiWidgets'
import { AiGenerated } from './ui/AiGenerated'
import {
  capacityForecastExplainPayload,
  reasonLabel,
  type CapacityForecastItem,
} from '../lib/insights'

interface Projected {
  series: string
  forecast: Forecast
}

/** Human ETA from a millisecond estimate, or a sample-count fallback. */
function etaLabel(forecast: Forecast): string {
  const { msToThreshold, samplesToThreshold } = forecast
  if (msToThreshold != null) {
    if (msToThreshold < 60_000) return '<1 min'
    const mins = msToThreshold / 60_000
    if (mins < 90) return `~${Math.round(mins)} min`
    const hrs = mins / 60
    if (hrs < 48) return `~${Math.round(hrs)} h`
    return `~${Math.round(hrs / 24)} d`
  }
  return samplesToThreshold != null ? `~${samplesToThreshold} samples` : '—'
}

export function CapacityForecast({ max = 6 }: { max?: number }) {
  const [projected, setProjected] = useState<Projected[]>([])
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
        const found: Projected[] = []
        for (const [series, seriesPoints] of groupSeries(points)) {
          if (!isUtilizationSeries(seriesPoints)) continue
          const forecast = forecastSeries(seriesPoints)
          // Only surface series rising toward the threshold (a real projection).
          if (forecast && forecast.samplesToThreshold != null) {
            found.push({ series, forecast })
          }
        }
        // Soonest to breach leads.
        found.sort(
          (a, b) => (a.forecast.samplesToThreshold ?? 0) - (b.forecast.samplesToThreshold ?? 0),
        )
        setProjected(found)
      } catch {
        if (!cancelled) {
          setProjected([])
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
  }, [])

  const shown = projected.slice(0, max)

  const onExplain = async () => {
    setExplaining(true)
    setExplainNote(null)
    setExplanation(null)
    try {
      const items: CapacityForecastItem[] = projected.map((p) => ({
        series: p.series,
        current: p.forecast.current,
        threshold: p.forecast.threshold,
        samplesToThreshold: p.forecast.samplesToThreshold ?? 0,
        etaLabel: etaLabel(p.forecast),
      }))
      const res = await api.insights.explain(
        'capacity_forecast',
        capacityForecastExplainPayload(items),
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
          <TrendingUp className="h-5 w-5" />
          Capacity forecast
          {projected.length > 0 && (
            <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
              {projected.length}
            </span>
          )}
        </h2>
      </div>
      <p className="mb-4 text-xs text-muted-foreground">
        Linear trend of utilization metrics, projected to a threshold. Extrapolation, not a
        guarantee.
      </p>

      {loading ? (
        <div className="py-8 text-center text-sm text-muted-foreground">Projecting trends...</div>
      ) : shown.length === 0 ? (
        <div className="py-8 text-center text-muted-foreground">
          <TrendingUp className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No utilization series trending toward a limit.</p>
          <p className="text-xs mt-1">
            {hasMetrics
              ? 'Every utilization metric is flat or falling in this window.'
              : 'Connect a monitoring source to project capacity.'}
          </p>
        </div>
      ) : (
        <ul className="space-y-2">
          {shown.map((item) => (
            <li
              key={item.series}
              className="rounded-lg border border-border/60 bg-muted/30 px-3 py-2"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="truncate text-sm font-medium">{item.series}</p>
                <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-amber-500/15 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                  {etaLabel(item.forecast)} to {item.forecast.threshold}%
                </span>
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <span>now {item.forecast.current.toFixed(1)}%</span>
                <span className="font-mono">
                  +{item.forecast.slopePerSample.toFixed(2)}/sample
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}

      {ai.enabled && projected.length > 0 && (
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
              {explaining ? 'Explaining…' : 'Explain this forecast'}
            </button>
          )}
          {explainNote && <p className="mt-2 text-xs text-muted-foreground">{explainNote}</p>}
        </div>
      )}
    </div>
  )
}

export default CapacityForecast
