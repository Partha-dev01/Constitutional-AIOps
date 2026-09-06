import { describe, it, expect } from 'vitest'
import { narrativeFromEvent, groupByIncident, type NarrativeEntry } from './incidentNarrative'
import { EventType, type WebSocketEvent } from './websocket'

function evt(type: EventType, payload: unknown = {}, timestamp = '2026-09-06T10:00:00Z'): WebSocketEvent {
  return { type, payload, timestamp }
}

describe('narrativeFromEvent', () => {
  it('maps incident created to the detected stage (id read from `id`)', () => {
    const e = narrativeFromEvent(evt(EventType.INCIDENT_CREATED, { id: 'inc-1' }))
    expect(e).not.toBeNull()
    expect(e!.stage).toBe('detected')
    expect(e!.severity).toBe('warning')
    expect(e!.incidentId).toBe('inc-1')
    expect(e!.at).toBe('2026-09-06T10:00:00Z')
  })

  it('reads the incident id from `incident_id` on later stages', () => {
    const e = narrativeFromEvent(evt(EventType.RCA_COMPLETED, { incident_id: 'inc-2', result: {} }))
    expect(e!.stage).toBe('root cause')
    expect(e!.incidentId).toBe('inc-2')
  })

  it('maps remediation planned', () => {
    const e = narrativeFromEvent(evt(EventType.REMEDIATION_PLANNED, { incident_id: 'inc-3' }))
    expect(e!.stage).toBe('remediation planned')
    expect(e!.severity).toBe('info')
  })

  it('maps each action stage with its severity', () => {
    const cases: Array<[EventType, string, NarrativeEntry['severity']]> = [
      [EventType.ACTION_CREATED, 'action proposed', 'info'],
      [EventType.ACTION_APPROVED, 'action approved', 'info'],
      [EventType.ACTION_EXECUTED, 'action executed', 'info'],
      [EventType.ACTION_FAILED, 'action failed', 'error'],
      [EventType.ACTION_REJECTED, 'action rejected', 'error'],
    ]
    for (const [type, stage, severity] of cases) {
      const e = narrativeFromEvent(evt(type, { incident_id: 'inc-4' }))!
      expect(e.stage).toBe(stage)
      expect(e.severity).toBe(severity)
    }
  })

  it('maps incident resolved to a success entry', () => {
    const e = narrativeFromEvent(evt(EventType.INCIDENT_RESOLVED, { incident_id: 'inc-5' }))!
    expect(e.stage).toBe('resolved')
    expect(e.severity).toBe('success')
  })

  it('returns null for an unmapped event type even with an incident id', () => {
    expect(narrativeFromEvent(evt(EventType.PING, { incident_id: 'inc-6' }))).toBeNull()
    expect(narrativeFromEvent(evt(EventType.INCIDENT_UPDATED, { id: 'inc-6' }))).toBeNull()
  })

  it('returns null when the event has no incident id', () => {
    expect(narrativeFromEvent(evt(EventType.RCA_COMPLETED, {}))).toBeNull()
    expect(narrativeFromEvent(evt(EventType.INCIDENT_CREATED, { name: 'no-id' }))).toBeNull()
  })

  it('derives a stable id from incident, stage and timestamp', () => {
    const e = narrativeFromEvent(evt(EventType.INCIDENT_CREATED, { id: 'inc-7' }, '2026-09-06T11:00:00Z'))!
    expect(e.id).toBe('inc-7:detected:2026-09-06T11:00:00Z')
  })
})

describe('groupByIncident', () => {
  it('groups entries by incident with stages in arrival order', () => {
    const entries = [
      narrativeFromEvent(evt(EventType.INCIDENT_CREATED, { id: 'a' }, '2026-09-06T10:00:00Z'))!,
      narrativeFromEvent(evt(EventType.RCA_COMPLETED, { incident_id: 'a' }, '2026-09-06T10:01:00Z'))!,
      narrativeFromEvent(evt(EventType.REMEDIATION_PLANNED, { incident_id: 'a' }, '2026-09-06T10:02:00Z'))!,
    ]
    const groups = groupByIncident(entries)
    expect(groups).toHaveLength(1)
    expect(groups[0].incidentId).toBe('a')
    expect(groups[0].stages.map((s) => s.stage)).toEqual(['detected', 'root cause', 'remediation planned'])
  })

  it('puts the most-recently-active incident first', () => {
    const entries = [
      narrativeFromEvent(evt(EventType.INCIDENT_CREATED, { id: 'a' }))!, // index 0
      narrativeFromEvent(evt(EventType.INCIDENT_CREATED, { id: 'b' }))!, // index 1
      narrativeFromEvent(evt(EventType.RCA_COMPLETED, { incident_id: 'a' }))!, // index 2 -> a is newest
    ]
    expect(groupByIncident(entries).map((g) => g.incidentId)).toEqual(['a', 'b'])
  })

  it('caps the number of incident groups (default 4, override honoured)', () => {
    const entries = ['a', 'b', 'c', 'd', 'e', 'f'].map(
      (id) => narrativeFromEvent(evt(EventType.INCIDENT_CREATED, { id }))!,
    )
    expect(groupByIncident(entries)).toHaveLength(4)
    expect(groupByIncident(entries, 2)).toHaveLength(2)
    // The cap keeps the most recent groups: f and e came last.
    expect(groupByIncident(entries, 2).map((g) => g.incidentId)).toEqual(['f', 'e'])
  })

  it('returns an empty array for no entries', () => {
    expect(groupByIncident([])).toEqual([])
  })
})
