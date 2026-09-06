/**
 * Pure helpers for the Dashboard "Live Incident Narrative" widget.
 *
 * The widget replays the live WebSocket incident lifecycle as a per-incident
 * staged timeline (detected -> root cause -> remediation planned -> action ->
 * resolved). No LLM. The mapping is kept out of the component so it is unit
 * testable and the component file stays export-clean for fast-refresh, exactly
 * like the sibling Recent Activity helpers in ./activity.
 */

import { EventType, type WebSocketEvent } from './websocket'

export interface NarrativeEntry {
  id: string
  incidentId: string
  stage: string
  label: string
  at: string
  severity: 'info' | 'success' | 'warning' | 'error'
}

type Severity = NarrativeEntry['severity']

/** How many incident groups the widget shows by default. */
export const NARRATIVE_INCIDENT_LIMIT = 4

/**
 * Incident-lifecycle event types worth a timeline stage, with the stage key, a
 * human label, and a severity. Mirrors ./activity's EVENT_META idiom; anything
 * absent here (pings, health, plain alerts) yields no stage.
 */
const STAGE_META: Partial<Record<EventType, { stage: string; label: string; severity: Severity }>> = {
  [EventType.INCIDENT_CREATED]: { stage: 'detected', label: 'Detected', severity: 'warning' },
  [EventType.RCA_COMPLETED]: { stage: 'root cause', label: 'Root cause identified', severity: 'info' },
  [EventType.REMEDIATION_PLANNED]: { stage: 'remediation planned', label: 'Remediation planned', severity: 'info' },
  [EventType.ACTION_CREATED]: { stage: 'action proposed', label: 'Action proposed', severity: 'info' },
  [EventType.ACTION_APPROVED]: { stage: 'action approved', label: 'Action approved', severity: 'info' },
  [EventType.ACTION_EXECUTED]: { stage: 'action executed', label: 'Action executed', severity: 'info' },
  [EventType.ACTION_FAILED]: { stage: 'action failed', label: 'Action failed', severity: 'error' },
  [EventType.ACTION_REJECTED]: { stage: 'action rejected', label: 'Action rejected', severity: 'error' },
  [EventType.INCIDENT_RESOLVED]: { stage: 'resolved', label: 'Resolved', severity: 'success' },
}

/**
 * Pull the incident id out of a heterogeneous event payload. incident.created
 * carries the incident dict (id under `id`); the resolved, RCA, remediation and
 * action events carry `incident_id`. Same object-guarded field access ./activity
 * uses for its detail extraction.
 */
function extractIncidentId(payload: unknown): string | undefined {
  if (!payload || typeof payload !== 'object') return undefined
  const p = payload as Record<string, unknown>
  for (const key of ['incident_id', 'id']) {
    const v = p[key]
    if (typeof v === 'string' && v.trim()) return v.trim()
  }
  return undefined
}

/**
 * Map a live event to one narrative stage, or null for events with no incident
 * id or an unmapped type. Pure. Timestamp and payload access mirror ./activity.
 */
export function narrativeFromEvent(event: WebSocketEvent): NarrativeEntry | null {
  const meta = STAGE_META[event.type]
  if (!meta) return null
  const incidentId = extractIncidentId(event.payload)
  if (!incidentId) return null
  const at = typeof event.timestamp === 'string' && event.timestamp ? event.timestamp : new Date().toISOString()
  return {
    id: `${incidentId}:${meta.stage}:${at}`,
    incidentId,
    stage: meta.stage,
    label: meta.label,
    at,
    severity: meta.severity,
  }
}

/**
 * Group narrative entries by incident, keeping each group's stages in arrival
 * order and putting the most-recently-active incident first (the one whose
 * newest entry arrived latest). Caps the number of groups at `limit`.
 */
export function groupByIncident(
  entries: NarrativeEntry[],
  limit = NARRATIVE_INCIDENT_LIMIT,
): { incidentId: string; stages: NarrativeEntry[] }[] {
  const order: string[] = []
  const groups = new Map<string, NarrativeEntry[]>()
  const lastIndex = new Map<string, number>()

  entries.forEach((entry, i) => {
    let stages = groups.get(entry.incidentId)
    if (!stages) {
      stages = []
      groups.set(entry.incidentId, stages)
      order.push(entry.incidentId)
    }
    stages.push(entry)
    lastIndex.set(entry.incidentId, i)
  })

  const result = order.map((incidentId) => ({ incidentId, stages: groups.get(incidentId)! }))
  // Most-recently-active first: order by the arrival position of each group's
  // newest entry, descending. Array sort is stable, so equal timestamps keep
  // first-seen order.
  result.sort((a, b) => (lastIndex.get(b.incidentId) ?? 0) - (lastIndex.get(a.incidentId) ?? 0))
  return result.slice(0, Math.max(0, limit))
}
