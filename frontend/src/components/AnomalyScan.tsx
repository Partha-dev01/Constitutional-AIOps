/**
 * AnomalyScan - a Dashboard widget that runs a client-side z-score scan over the
 * live telemetry metric series and flags points sitting far from their series
 * mean (Track 2 widget, the free/no-LLM half of the Anomaly-to-Hypothesis Feed).
 * Read-only and purely statistical: it never calls an LLM and never proposes an
 * action, it only points at a value worth a human look. The label stays honest -
 * this is a heuristic, not a diagnosis.
 */

import { useEffect, useState } from 'react'
import { Activity, TrendingUp, TrendingDown, AlertTriangle, Sparkles, Loader2 } from 'lucide-react'
import { cn } from '../lib/utils'
import { api, type TelemetryMetricPoint } from '../lib/api'
import { scanSeries, type Anomaly, type SeriesPoint } from '../lib/anomalyScan'
import { useAiWidgets } from '../lib/useAiWidgets'
import { AiGenerated } from './ui/AiGenerated'
import { anomalyExplainPayload, reasonLabel, type AnomalyItem } from '../lib/insights'

interface FlaggedPoint {
  key: string
  series: string
  anomaly: Anomaly
}

/** Series name for a point: service + metric when present, else the label. */
function seriesKey(p: TelemetryMetricPoint): string {
  if (p.service && p.metric) return `${p.service} · ${p.metric}`
  return p.label
}

/** Bucket raw points into per-series {timestamp, value} lists, input order kept. */
function groupSeries(points: TelemetryMetricPoint[]): Map<string, SeriesPoint[]> {
  const groups = new Map<string, SeriesPoint[]>()
  for (const p of points) {
    const key = seriesKey(p)
    const point: SeriesPoint = { timestamp: p.timestamp, value: p.value }
    const bucket = groups.get(key)
    if (bucket) bucket.push(point)
    else groups.set(key, [point])
  }
  return groups
}

function formatNum(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2)
}

export function AnomalyScan({ max = 6 }: { max?: number }) {
  const [flagged, setFlagged] = useState<FlaggedPoint[]>([])
  const [hasMetrics, setHasMetrics] = useState(false)
  const [loading, setLoading] = useState(true)

  // Opt-in LLM explain (Track 2 W3): the button appears only when the user has
  // turned on AI insight widgets; it never fires on mount.
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
        const found: FlaggedPoint[] = []
        for (const [name, seriesPoints] of groupSeries(points)) {
          for (const anomaly of scanSeries(seriesPoints)) {
            found.push({ key: `${name}@${anomaly.timestamp}`, series: name, anomaly })
          }
        }
        // Strongest deviation first so the sharpest spike leads.
        found.sort((a, b) => Math.abs(b.anomaly.z) - Math.abs(a.anomaly.z))
        setFlagged(found)
      } catch {
        if (!cancelled) {
          setFlagged([])
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

  const shown = flagged.slice(0, max)

  const onExplain = async () => {
    setExplaining(true)
    setExplainNote(null)
    setExplanation(null)
    try {
      const items: AnomalyItem[] = flagged.map((f) => ({
        series: f.series,
        value: f.anomaly.value,
        z: f.anomaly.z,
        direction: f.anomaly.direction,
      }))
      const res = await api.insights.explain('anomaly', anomalyExplainPayload(items))
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
          Anomaly scan
          {flagged.length > 0 && (
            <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
              {flagged.length}
            </span>
          )}
        </h2>
      </div>
      <p className="mb-4 text-xs text-muted-foreground">
        z-score scan of the last hour of metrics. Statistical heuristic, not a diagnosis.
      </p>

      {loading ? (
        <div className="py-8 text-center text-sm text-muted-foreground">Scanning metrics...</div>
      ) : shown.length === 0 ? (
        <div className="py-8 text-center text-muted-foreground">
          <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No metric anomalies in the current window.</p>
          <p className="text-xs mt-1">
            {hasMetrics
              ? 'Every metric series sits within its normal spread.'
              : 'Connect a monitoring source to scan live metrics.'}
          </p>
        </div>
      ) : (
        <ul className="space-y-2">
          {shown.map((item) => {
            const high = item.anomaly.direction === 'high'
            const Arrow = high ? TrendingUp : TrendingDown
            return (
              <li
                key={item.key}
                className="rounded-lg border border-border/60 bg-muted/30 px-3 py-2"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="truncate text-sm font-medium">{item.series}</p>
                  <span
                    className={cn(
                      'shrink-0 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
                      high
                        ? 'bg-red-500/15 text-red-600 dark:text-red-400'
                        : 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
                    )}
                  >
                    <Arrow className="h-3 w-3" aria-hidden="true" />
                    {high ? 'spike high' : 'spike low'}
                  </span>
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                    possible spike
                  </span>
                  <span>value {formatNum(item.anomaly.value)}</span>
                  <span className="font-mono">z {item.anomaly.z.toFixed(1)}</span>
                </div>
              </li>
            )
          })}
        </ul>
      )}

      {ai.enabled && flagged.length > 0 && (
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
              {explaining ? 'Explaining…' : 'Explain these anomalies'}
            </button>
          )}
          {explainNote && <p className="mt-2 text-xs text-muted-foreground">{explainNote}</p>}
        </div>
      )}
    </div>
  )
}

export default AnomalyScan
