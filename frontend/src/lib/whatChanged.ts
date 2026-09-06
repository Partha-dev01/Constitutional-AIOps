/**
 * Pure helpers for the Dashboard "What Changed" diff widget (Track 2).
 *
 * Snapshots the live incidents + services, then diffs two snapshots so the
 * widget can show what moved since the last refresh (new / resolved incidents,
 * status changes, added / removed services). Kept out of the component so the
 * diff is unit testable and no LLM is ever involved — purely a view over
 * existing data.
 */

export interface Snapshot {
  incidents: { id: string; status: string; title?: string }[]
  services: string[]
}

export interface SnapshotDiff {
  addedIncidents: { id: string; title?: string }[]
  removedIncidents: { id: string; title?: string }[]
  statusChanges: { id: string; title?: string; from: string; to: string }[]
  addedServices: string[]
  removedServices: string[]
  changed: boolean
}

/**
 * Diff two snapshots by incident id and service-set membership. Added = present
 * in next but not prev; removed = present in prev but not next; a status change
 * is the same id with a different status. Ordering is stable (by id / name) so
 * the render is deterministic. `changed` is true when any list is non-empty.
 */
export function diffSnapshots(prev: Snapshot, next: Snapshot): SnapshotDiff {
  const prevById = new Map(prev.incidents.map((i) => [i.id, i] as const))
  const nextById = new Map(next.incidents.map((i) => [i.id, i] as const))

  const addedIncidents = next.incidents
    .filter((i) => !prevById.has(i.id))
    .map((i) => ({ id: i.id, title: i.title }))
    .sort((a, b) => a.id.localeCompare(b.id))

  const removedIncidents = prev.incidents
    .filter((i) => !nextById.has(i.id))
    .map((i) => ({ id: i.id, title: i.title }))
    .sort((a, b) => a.id.localeCompare(b.id))

  const statusChanges = next.incidents
    .flatMap((i) => {
      const before = prevById.get(i.id)
      if (before && before.status !== i.status) {
        return [{ id: i.id, title: i.title, from: before.status, to: i.status }]
      }
      return []
    })
    .sort((a, b) => a.id.localeCompare(b.id))

  // Set membership dedupes as well, so a doubled label never doubles a diff row.
  const prevServices = new Set(prev.services)
  const nextServices = new Set(next.services)
  const addedServices = [...nextServices]
    .filter((s) => !prevServices.has(s))
    .sort((a, b) => a.localeCompare(b))
  const removedServices = [...prevServices]
    .filter((s) => !nextServices.has(s))
    .sort((a, b) => a.localeCompare(b))

  const changed =
    addedIncidents.length > 0 ||
    removedIncidents.length > 0 ||
    statusChanges.length > 0 ||
    addedServices.length > 0 ||
    removedServices.length > 0

  return {
    addedIncidents,
    removedIncidents,
    statusChanges,
    addedServices,
    removedServices,
    changed,
  }
}
