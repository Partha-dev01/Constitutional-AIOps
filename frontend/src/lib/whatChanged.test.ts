import { describe, it, expect } from 'vitest'
import { diffSnapshots, type Snapshot } from './whatChanged'

function snapshot(overrides: Partial<Snapshot> = {}): Snapshot {
  return {
    incidents: [{ id: 'INC-1', status: 'detecting', title: 'DB slow' }],
    services: ['api', 'web'],
    ...overrides,
  }
}

describe('diffSnapshots', () => {
  it('flags an added incident', () => {
    const prev = snapshot()
    const next = snapshot({
      incidents: [
        { id: 'INC-1', status: 'detecting', title: 'DB slow' },
        { id: 'INC-2', status: 'analyzing', title: 'Cache miss' },
      ],
    })
    const d = diffSnapshots(prev, next)
    expect(d.addedIncidents).toEqual([{ id: 'INC-2', title: 'Cache miss' }])
    expect(d.removedIncidents).toEqual([])
    expect(d.statusChanges).toEqual([])
    expect(d.changed).toBe(true)
  })

  it('flags a removed incident', () => {
    const prev = snapshot({
      incidents: [
        { id: 'INC-1', status: 'detecting', title: 'DB slow' },
        { id: 'INC-2', status: 'analyzing', title: 'Cache miss' },
      ],
    })
    const next = snapshot()
    const d = diffSnapshots(prev, next)
    expect(d.removedIncidents).toEqual([{ id: 'INC-2', title: 'Cache miss' }])
    expect(d.addedIncidents).toEqual([])
    expect(d.changed).toBe(true)
  })

  it('flags a status change on the same incident', () => {
    const prev = snapshot()
    const next = snapshot({
      incidents: [{ id: 'INC-1', status: 'resolved', title: 'DB slow' }],
    })
    const d = diffSnapshots(prev, next)
    expect(d.statusChanges).toEqual([
      { id: 'INC-1', title: 'DB slow', from: 'detecting', to: 'resolved' },
    ])
    expect(d.addedIncidents).toEqual([])
    expect(d.removedIncidents).toEqual([])
    expect(d.changed).toBe(true)
  })

  it('flags added and removed services', () => {
    const prev = snapshot({ services: ['api', 'web'] })
    const next = snapshot({ services: ['api', 'cache'] })
    const d = diffSnapshots(prev, next)
    expect(d.addedServices).toEqual(['cache'])
    expect(d.removedServices).toEqual(['web'])
    expect(d.changed).toBe(true)
  })

  it('reports no change when nothing moved', () => {
    const d = diffSnapshots(snapshot(), snapshot())
    expect(d.addedIncidents).toEqual([])
    expect(d.removedIncidents).toEqual([])
    expect(d.statusChanges).toEqual([])
    expect(d.addedServices).toEqual([])
    expect(d.removedServices).toEqual([])
    expect(d.changed).toBe(false)
  })

  it('handles empty snapshots', () => {
    const empty: Snapshot = { incidents: [], services: [] }
    const d = diffSnapshots(empty, empty)
    expect(d.changed).toBe(false)
    expect(d.addedIncidents).toEqual([])
    expect(d.addedServices).toEqual([])
  })

  it('orders results deterministically by id / name', () => {
    const prev: Snapshot = { incidents: [], services: ['z-svc'] }
    const next: Snapshot = {
      incidents: [
        { id: 'INC-9', status: 'detecting' },
        { id: 'INC-3', status: 'detecting' },
      ],
      services: ['m-svc', 'a-svc', 'z-svc'],
    }
    const d = diffSnapshots(prev, next)
    expect(d.addedIncidents.map((i) => i.id)).toEqual(['INC-3', 'INC-9'])
    expect(d.addedServices).toEqual(['a-svc', 'm-svc'])
  })

  it('dedupes a doubled service label', () => {
    const prev: Snapshot = { incidents: [], services: [] }
    const next: Snapshot = { incidents: [], services: ['api', 'api'] }
    const d = diffSnapshots(prev, next)
    expect(d.addedServices).toEqual(['api'])
  })
})
