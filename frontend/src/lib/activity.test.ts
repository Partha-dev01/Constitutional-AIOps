import { describe, it, expect } from 'vitest'
import { describeEvent, RECENT_ACTIVITY_LIMIT } from './activity'
import { EventType, type WebSocketEvent } from './websocket'

function evt(type: EventType, payload: unknown = {}, timestamp = '2026-09-06T10:00:00Z'): WebSocketEvent {
  return { type, payload, timestamp }
}

describe('describeEvent', () => {
  it('maps a known event to a labelled item with severity', () => {
    const item = describeEvent(evt(EventType.INCIDENT_CREATED))
    expect(item).not.toBeNull()
    expect(item!.label).toBe('Incident created')
    expect(item!.severity).toBe('warning')
    expect(item!.type).toBe(EventType.INCIDENT_CREATED)
    expect(item!.at).toBe('2026-09-06T10:00:00Z')
  })

  it('marks failures as error severity', () => {
    expect(describeEvent(evt(EventType.ACTION_FAILED))!.severity).toBe('error')
  })

  it('pulls a human detail from the payload', () => {
    const item = describeEvent(evt(EventType.RCA_COMPLETED, { title: 'DB pool exhausted' }))
    expect(item!.detail).toBe('DB pool exhausted')
  })

  it('falls back across detail keys and trims', () => {
    expect(describeEvent(evt(EventType.ALERT, { service: '  api  ' }))!.detail).toBe('api')
    expect(describeEvent(evt(EventType.ALERT, { nothing: 1 }))!.detail).toBeUndefined()
  })

  it('returns null for events we do not surface', () => {
    expect(describeEvent(evt(EventType.PING))).toBeNull()
    expect(describeEvent(evt(EventType.CONNECTED))).toBeNull()
  })

  it('generates unique ids across successive events', () => {
    const a = describeEvent(evt(EventType.ALERT))!
    const b = describeEvent(evt(EventType.ALERT))!
    expect(a.id).not.toBe(b.id)
  })

  it('exposes a sane feed cap', () => {
    expect(RECENT_ACTIVITY_LIMIT).toBeGreaterThan(0)
  })
})
