/**
 * BlastRadiusPreview - a Dashboard widget that previews which services sit
 * downstream of a chosen one, so an operator can gauge the blast radius before
 * touching it (Track 2 widget). Read-only and no-LLM: a client-side BFS over the
 * live topology schema. Nothing is called, queued, or executed here.
 */

import { useEffect, useMemo, useState } from 'react'
import { Waypoints, Network } from 'lucide-react'
import { api, type TopologySchemaNode, type TopologySchemaEdge } from '../lib/api'
import { computeBlastRadius } from '../lib/blastRadius'

const MAX_DEPTH = 2

export function BlastRadiusPreview() {
  const [nodes, setNodes] = useState<TopologySchemaNode[]>([])
  const [edges, setEdges] = useState<TopologySchemaEdge[]>([])
  const [focus, setFocus] = useState<string>('')

  useEffect(() => {
    let cancelled = false
    api.topology
      .getSchema()
      .then((schema) => {
        if (cancelled) return
        setNodes(schema.nodes ?? [])
        setEdges(schema.edges ?? [])
        const first = schema.nodes?.[0]?.id
        if (first) setFocus((cur) => cur || first)
      })
      .catch(() => {
        /* No topology configured yet, the widget shows its empty state. */
      })
    return () => {
      cancelled = true
    }
  }, [])

  // id -> display label, so hop chips read as service names not raw ids.
  const labelOf = useMemo(() => {
    const map = new Map<string, string>()
    for (const n of nodes) map.set(n.id, n.label || n.id)
    return (id: string) => map.get(id) ?? id
  }, [nodes])

  const { levels, total } = useMemo(
    () => computeBlastRadius(edges, focus, MAX_DEPTH),
    [edges, focus],
  )

  const hasGraph = nodes.length > 0 && edges.length > 0

  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Waypoints className="h-5 w-5" />
          Blast-radius preview
          {hasGraph && total > 0 && (
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
              {total}
            </span>
          )}
        </h2>
      </div>

      {!hasGraph ? (
        <div className="py-8 text-center text-muted-foreground">
          <Network className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No dependency edges known yet</p>
          <p className="text-xs mt-1">
            The graph is empty on a fresh instance. Once services and their
            dependencies are configured, downstream impact shows up here.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <label className="block">
            <span className="text-xs text-muted-foreground">If this service degrades</span>
            <select
              value={focus}
              onChange={(e) => setFocus(e.target.value)}
              className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
            >
              {nodes.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.label || n.id}
                </option>
              ))}
            </select>
          </label>

          {total === 0 ? (
            <p className="text-sm text-muted-foreground">
              Nothing downstream. No service depends on{' '}
              <span className="font-medium text-foreground">{labelOf(focus)}</span> within{' '}
              {MAX_DEPTH} hops.
            </p>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                <span className="font-medium text-foreground">{total}</span> service
                {total === 1 ? '' : 's'} downstream within {MAX_DEPTH} hops.
              </p>
              <ol className="space-y-2">
                {levels.map((ids, depth) => (
                  <li
                    key={depth}
                    className="rounded-lg border border-border/60 bg-muted/30 px-3 py-2"
                  >
                    <div className="mb-1 text-xs font-medium text-muted-foreground">
                      Hop {depth + 1}
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {ids.map((id) => (
                        <span
                          key={id}
                          className="rounded-full bg-amber-500/15 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400"
                        >
                          {labelOf(id)}
                        </span>
                      ))}
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
