/**
 * insights - pure helpers for the LLM insight widgets (Track 2 W3).
 *
 * The widgets compute their view without an LLM and only call the opt-in,
 * cost-fenced `/insights/explain` endpoint when the user clicks "Explain".
 * These helpers turn a widget's computed data into a bounded explain payload
 * and turn the endpoint's `reason` code into a short, honest UI message. Both
 * are side-effect free so they unit-test without a network or React.
 */

/** One flagged anomaly, the shape the AnomalyScan widget already holds. */
export interface AnomalyItem {
  series: string
  value: number
  z: number
  direction: 'high' | 'low'
}

/**
 * Build a small, bounded payload for `kind: "anomaly"` from the flagged points.
 * Caps to the strongest `max` items so a noisy scan cannot drive a huge prompt
 * (the server also truncates, this keeps the request itself small).
 */
export function anomalyExplainPayload(
  items: AnomalyItem[],
  max = 5,
): { count: number; top: AnomalyItem[] } {
  const top = items.slice(0, Math.max(0, max)).map((it) => ({
    series: it.series,
    value: it.value,
    z: Number(it.z.toFixed(2)),
    direction: it.direction,
  }))
  return { count: items.length, top }
}

/**
 * Map an explain `reason` (available=false) to a short user-facing message.
 * Keeps the widget on its computed view and tells the user what to do next.
 */
export function reasonLabel(reason: string | null | undefined): string {
  switch (reason) {
    case 'ai_widgets_disabled':
      return 'Turn on AI insight widgets in Settings to explain this.'
    case 'budget_reached':
      return 'Daily AI budget reached. Explanations resume tomorrow.'
    case 'no_endpoint':
      return 'Add an LLM endpoint in Settings to enable explanations.'
    case 'empty':
      return 'The model returned no explanation. Try again.'
    case 'error':
      return 'Could not reach the LLM endpoint just now.'
    default:
      return 'Explanation is unavailable right now.'
  }
}

export default { anomalyExplainPayload, reasonLabel }
