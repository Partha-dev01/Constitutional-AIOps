/**
 * Pure helpers for the Dashboard "Recent Activity" widget (Track 2).
 *
 * The widget is event-triggered: it turns live WebSocket events into a bounded,
 * newest-first feed. Kept out of the page component so the mapping is unit
 * testable and the component file stays export-clean for fast-refresh.
 */

import { EventType, type WebSocketEvent } from './websocket'

export type ActivitySeverity = 'info' | 'success' | 'warning' | 'error'

export interface ActivityItem {
  id: string
  type: EventType
  label: string
  detail?: string
  severity: ActivitySeverity
  at: string
}

/** How many events the feed keeps client-side. */
export const RECENT_ACTIVITY_LIMIT = 20

/** Event types worth surfacing in the feed, with a human label + severity. */
const EVENT_META: Partial<Record<EventType, { label: string; severity: ActivitySeverity }>> = {
  [EventType.INCIDENT_CREATED]: { label: 'Incident created', severity: 'warning' },
  [EventType.INCIDENT_RESOLVED]: { label: 'Incident resolved', severity: 'success' },
  [EventType.ACTION_CREATED]: { label: 'Action proposed', severity: 'info' },
  [EventType.ACTION_APPROVED]: { label: 'Action approved', severity: 'info' },
  [EventType.ACTION_REJECTED]: { label: 'Action rejected', severity: 'warning' },
  [EventType.ACTION_EXECUTED]: { label: 'Action executed', severity: 'success' },
  [EventType.ACTION_FAILED]: { label: 'Action failed', severity: 'error' },
  [EventType.RCA_COMPLETED]: { label: 'Root-cause analysis completed', severity: 'info' },
  [EventType.REMEDIATION_PLANNED]: { label: 'Remediation planned', severity: 'info' },
  [EventType.ALERT]: { label: 'Alert raised', severity: 'warning' },
}

/** Pull a short human detail out of a heterogeneous event payload, if any. */
function extractDetail(payload: unknown): string | undefined {
  if (!payload || typeof payload !== 'object') return undefined
  const p = payload as Record<string, unknown>
  for (const key of ['title', 'name', 'message', 'summary', 'incident_id', 'service']) {
    const v = p[key]
    if (typeof v === 'string' && v.trim()) return v.trim()
  }
  return undefined
}

let _seq = 0

/**
 * Map a live event to an ActivityItem, or null for events we do not surface
 * (connection pings, unmapped types). Pure aside from a monotonic id counter.
 */
export function describeEvent(event: WebSocketEvent): ActivityItem | null {
  const meta = EVENT_META[event.type]
  if (!meta) return null
  _seq += 1
  return {
    id: event.correlation_id ? `${event.correlation_id}-${_seq}` : `evt-${_seq}`,
    type: event.type,
    label: meta.label,
    detail: extractDetail(event.payload),
    severity: meta.severity,
    at: typeof event.timestamp === 'string' && event.timestamp ? event.timestamp : new Date().toISOString(),
  }
}
