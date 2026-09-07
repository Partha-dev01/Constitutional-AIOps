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

/** The blast-radius widget's computed downstream view, labels not raw ids. */
export interface BlastRadiusInput {
  service: string
  total: number
  levels: string[][]
}

/**
 * Build a bounded payload for `kind: "blast_radius"` from the computed hop
 * levels. Caps each hop to `maxPerHop` services and drops emptied hops so a wide
 * fan-out cannot drive a huge prompt (the server also truncates).
 */
export function blastRadiusExplainPayload(
  input: BlastRadiusInput,
  maxPerHop = 12,
): { service: string; total: number; hops: { hop: number; services: string[] }[] } {
  const cap = Math.max(0, maxPerHop)
  const hops = input.levels
    .map((services, i) => ({ hop: i + 1, services: services.slice(0, cap) }))
    .filter((h) => h.services.length > 0)
  return { service: input.service, total: input.total, hops }
}

/**
 * Build a bounded payload for `kind: "next_best_action"` from the incident
 * narrative groups. Sends each incident's ordered stage keys (the sequence is
 * what a next-best-action read needs), capped in both dimensions.
 */
export function incidentNarrativeExplainPayload(
  groups: { incidentId: string; stages: { stage: string }[] }[],
  maxIncidents = 3,
  maxStages = 12,
): { incidents: { id: string; stages: string[] }[] } {
  const incidents = groups.slice(0, Math.max(0, maxIncidents)).map((g) => ({
    id: g.incidentId,
    stages: g.stages.slice(0, Math.max(0, maxStages)).map((s) => s.stage),
  }))
  return { incidents }
}

/** One ranked runbook row, the shape the LearnedRunbook widget already holds. */
export interface RunbookEntryLite {
  key: string
  successRate: number
  succeeded: number
  used: number
}

/**
 * Build a bounded payload for `kind: "runbook"` from the ranked runbook rows.
 * Rounds the rate to two places and caps to the strongest `max` rows so a long
 * history cannot drive a huge prompt (the server also truncates).
 */
export function learnedRunbookExplainPayload(
  entries: RunbookEntryLite[],
  max = 6,
): { runbook: { action: string; successRate: number; succeeded: number; used: number }[] } {
  const runbook = entries.slice(0, Math.max(0, max)).map((e) => ({
    action: e.key,
    successRate: Number(e.successRate.toFixed(2)),
    succeeded: e.succeeded,
    used: e.used,
  }))
  return { runbook }
}

/** The episodic-graph pieces the copilot summarises, camelCase + lean. */
export interface GraphCopilotInput {
  stats: {
    episodes: number
    rootCauses: number
    actions: number
    services: number
    entities: number
    edges: number
    critical: number
    resolved: number
  }
  rootCauses: { name: string; frequency: number; successRate: number }[]
  actions: { name: string; usedCount: number; successRate: number }[]
  services: { name: string; incidentCount: number; status?: string }[]
  episodes: { title: string; category: string; severity: string; status: string }[]
}

/**
 * Build a bounded payload for `kind: "graph_copilot"` (reasoning tier). Sends
 * the overall counts plus the strongest few root causes / actions / services and
 * the incidents worth attention (unresolved and higher-severity first), each
 * capped so a large graph cannot drive a huge prompt (the server also truncates).
 */
export function graphCopilotExplainPayload(
  input: GraphCopilotInput,
  maxItems = 6,
  maxEpisodes = 5,
): {
  stats: GraphCopilotInput['stats']
  topRootCauses: { name: string; frequency: number; successRate: number }[]
  topActions: { action: string; usedCount: number; successRate: number }[]
  topServices: { service: string; incidents: number; status?: string }[]
  recentIncidents: { title: string; category: string; severity: string; status: string }[]
} {
  const cap = Math.max(0, maxItems)
  const topRootCauses = [...input.rootCauses]
    .sort((a, b) => b.frequency - a.frequency)
    .slice(0, cap)
    .map((r) => ({ name: r.name, frequency: r.frequency, successRate: Number(r.successRate.toFixed(2)) }))
  const topActions = [...input.actions]
    .sort((a, b) => b.usedCount - a.usedCount)
    .slice(0, cap)
    .map((a) => ({ action: a.name, usedCount: a.usedCount, successRate: Number(a.successRate.toFixed(2)) }))
  const topServices = [...input.services]
    .sort((a, b) => b.incidentCount - a.incidentCount)
    .slice(0, cap)
    .map((s) => ({ service: s.name, incidents: s.incidentCount, status: s.status }))
  // "Where to focus": unresolved first, then higher severity.
  const sevRank: Record<string, number> = { critical: 3, high: 2, warning: 1 }
  const recentIncidents = [...input.episodes]
    .sort((a, b) => {
      const ua = a.status !== 'resolved' ? 1 : 0
      const ub = b.status !== 'resolved' ? 1 : 0
      if (ua !== ub) return ub - ua
      return (sevRank[b.severity] ?? 0) - (sevRank[a.severity] ?? 0)
    })
    .slice(0, Math.max(0, maxEpisodes))
    .map((e) => ({ title: e.title, category: e.category, severity: e.severity, status: e.status }))
  return { stats: input.stats, topRootCauses, topActions, topServices, recentIncidents }
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

export default {
  anomalyExplainPayload,
  blastRadiusExplainPayload,
  incidentNarrativeExplainPayload,
  learnedRunbookExplainPayload,
  graphCopilotExplainPayload,
  reasonLabel,
}
