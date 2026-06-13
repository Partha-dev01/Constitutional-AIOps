/**
 * Schema mode — pure layered-DAG layout.
 *
 * Layering: Kahn/longest-path over DEPENDS_ON edges with the backend-supplied
 * `tier` as a floor, after excluding DFS back-edges (returned separately so a
 * cyclic input can never throw or loop). Edge-host nodes are pinned to
 * maxLayer + 1. Crossing reduction: 4 alternating barycenter sweeps with a
 * stable sort so the output is fully deterministic for a given topology.
 *
 * The result is memoized on TOPOLOGY IDENTITY ONLY (node ids + tiers, edge
 * ids) — scrub / hover / selection changes never recompute the layout.
 */

import { TopologyEdge, TopologyNode, isEdgeHostNode } from './types'

export const NODE_W = 150
export const NODE_H = 56
export const GAP_X = 90
export const GAP_Y = 28

export interface LayoutPosition {
  id: string
  x: number
  y: number
  layer: number
}

export interface SchemaLayout {
  /** Top-left coordinates per node id. */
  positions: Map<string, LayoutPosition>
  /** DEPENDS_ON edge ids excluded from layering as DFS back-edges. */
  backEdgeIds: Set<string>
  /** Node ids per layer, in final (crossing-reduced) order. */
  layers: string[][]
  /** Content bounding box (no padding). */
  width: number
  height: number
}

/** Identity key: node ids + tiers and edge ids only (scrub-independent). */
function topologyKey(nodes: TopologyNode[], edges: TopologyEdge[]): string {
  const n = nodes.map((node) => `${node.id}:${node.tier}:${node.kind}`).join(',')
  const e = edges.map((edge) => `${edge.id}:${edge.relationship}`).join(',')
  return `${n}||${e}`
}

let memoKey: string | null = null
let memoResult: SchemaLayout | null = null

export function layoutTopology(
  nodes: TopologyNode[],
  edges: TopologyEdge[],
): SchemaLayout {
  const key = topologyKey(nodes, edges)
  if (memoKey === key && memoResult) return memoResult
  const result = computeLayout(nodes, edges)
  memoKey = key
  memoResult = result
  return result
}

function computeLayout(nodes: TopologyNode[], edges: TopologyEdge[]): SchemaLayout {
  const ids = nodes.map((n) => n.id)
  const byId = new Map(nodes.map((n) => [n.id, n]))
  const edgeHosts = new Set(nodes.filter((n) => isEdgeHostNode(n)).map((n) => n.id))

  // Layering graph: DEPENDS_ON edges between known, non-edge-host nodes.
  const layeringEdges = edges.filter(
    (e) =>
      e.relationship === 'DEPENDS_ON' &&
      byId.has(e.source) &&
      byId.has(e.target) &&
      !edgeHosts.has(e.source) &&
      !edgeHosts.has(e.target),
  )

  // --- DFS back-edge exclusion (cycle safety) ------------------------------
  const outgoing = new Map<string, TopologyEdge[]>()
  for (const e of layeringEdges) {
    const list = outgoing.get(e.source)
    if (list) list.push(e)
    else outgoing.set(e.source, [e])
  }
  const backEdgeIds = new Set<string>()
  // 0 = unvisited, 1 = on stack, 2 = done
  const state = new Map<string, number>()
  const dfs = (root: string) => {
    // Iterative DFS for safety on larger graphs; deterministic edge order.
    const stack: { id: string; nextIdx: number }[] = [{ id: root, nextIdx: 0 }]
    state.set(root, 1)
    while (stack.length > 0) {
      const frame = stack[stack.length - 1]
      const outs = outgoing.get(frame.id) ?? []
      if (frame.nextIdx < outs.length) {
        const edge = outs[frame.nextIdx]
        frame.nextIdx += 1
        const tgtState = state.get(edge.target) ?? 0
        if (tgtState === 1) {
          backEdgeIds.add(edge.id)
        } else if (tgtState === 0) {
          state.set(edge.target, 1)
          stack.push({ id: edge.target, nextIdx: 0 })
        }
      } else {
        state.set(frame.id, 2)
        stack.pop()
      }
    }
  }
  for (const id of ids) {
    if (!edgeHosts.has(id) && (state.get(id) ?? 0) === 0) dfs(id)
  }

  const dagEdges = layeringEdges.filter((e) => !backEdgeIds.has(e.id))

  // --- Kahn / longest-path layering with tier floor -------------------------
  const layer = new Map<string, number>()
  const indegree = new Map<string, number>()
  for (const id of ids) {
    if (edgeHosts.has(id)) continue
    layer.set(id, Math.max(0, Math.floor(byId.get(id)?.tier ?? 0)))
    indegree.set(id, 0)
  }
  for (const e of dagEdges) {
    indegree.set(e.target, (indegree.get(e.target) ?? 0) + 1)
  }
  const queue: string[] = []
  for (const id of ids) {
    if (!edgeHosts.has(id) && (indegree.get(id) ?? 0) === 0) queue.push(id)
  }
  const dagOut = new Map<string, TopologyEdge[]>()
  for (const e of dagEdges) {
    const list = dagOut.get(e.source)
    if (list) list.push(e)
    else dagOut.set(e.source, [e])
  }
  let head = 0
  while (head < queue.length) {
    const id = queue[head]
    head += 1
    const base = layer.get(id) ?? 0
    for (const e of dagOut.get(id) ?? []) {
      const current = layer.get(e.target) ?? 0
      if (base + 1 > current) layer.set(e.target, base + 1)
      const deg = (indegree.get(e.target) ?? 1) - 1
      indegree.set(e.target, deg)
      if (deg === 0) queue.push(e.target)
    }
  }
  // Any node not drained by Kahn (only possible on pathological input) keeps
  // its tier floor — never throw, never produce NaN.

  let maxLayer = 0
  for (const value of layer.values()) maxLayer = Math.max(maxLayer, value)

  // Edge hosts pinned to the column after everything else.
  const edgeHostLayer = maxLayer + 1
  for (const id of edgeHosts) layer.set(id, edgeHostLayer)
  const totalLayers = edgeHosts.size > 0 ? edgeHostLayer + 1 : maxLayer + 1

  // --- Initial per-layer order: input order (deterministic) ----------------
  const layers: string[][] = Array.from({ length: totalLayers }, () => [])
  for (const id of ids) {
    layers[layer.get(id) ?? 0].push(id)
  }

  // --- Barycenter crossing reduction (4 alternating sweeps) ----------------
  // Neighbors come from EVERY edge between known nodes (back-edges and
  // SHIPS_TELEMETRY included) so visually-connected nodes get pulled together.
  const neighbors = new Map<string, string[]>()
  const addNeighbor = (a: string, b: string) => {
    const list = neighbors.get(a)
    if (list) list.push(b)
    else neighbors.set(a, [b])
  }
  for (const e of edges) {
    if (!byId.has(e.source) || !byId.has(e.target)) continue
    addNeighbor(e.source, e.target)
    addNeighbor(e.target, e.source)
  }

  const orderIndex = new Map<string, number>()
  const refreshIndices = () => {
    for (const row of layers) {
      row.forEach((id, idx) => orderIndex.set(id, idx))
    }
  }
  refreshIndices()

  const sweep = (downward: boolean) => {
    const sequence = downward
      ? Array.from({ length: totalLayers }, (_, i) => i)
      : Array.from({ length: totalLayers }, (_, i) => totalLayers - 1 - i)
    for (const li of sequence) {
      const row = layers[li]
      if (row.length < 2) continue
      const scored = row.map((id, idx) => {
        const relevant = (neighbors.get(id) ?? []).filter((nb) => {
          const nbLayer = layer.get(nb)
          if (nbLayer === undefined) return false
          return downward ? nbLayer < li : nbLayer > li
        })
        if (relevant.length === 0) return { id, idx, bary: idx }
        const sum = relevant.reduce((acc, nb) => acc + (orderIndex.get(nb) ?? 0), 0)
        return { id, idx, bary: sum / relevant.length }
      })
      // Stable sort: ties keep the previous order — deterministic output.
      scored.sort((a, b) => a.bary - b.bary || a.idx - b.idx)
      layers[li] = scored.map((s) => s.id)
      layers[li].forEach((id, idx) => orderIndex.set(id, idx))
    }
    refreshIndices()
  }
  for (let i = 0; i < 4; i += 1) sweep(i % 2 === 0)

  // --- Coordinates: x by layer, layers centered vertically ------------------
  const stackHeight = (count: number) =>
    count > 0 ? count * NODE_H + (count - 1) * GAP_Y : 0
  const contentHeight = layers.reduce((acc, row) => Math.max(acc, stackHeight(row.length)), 0)
  const contentWidth =
    totalLayers > 0 ? totalLayers * NODE_W + (totalLayers - 1) * GAP_X : 0

  const positions = new Map<string, LayoutPosition>()
  layers.forEach((row, li) => {
    const x = li * (NODE_W + GAP_X)
    const yStart = (contentHeight - stackHeight(row.length)) / 2
    row.forEach((id, idx) => {
      positions.set(id, {
        id,
        x,
        y: yStart + idx * (NODE_H + GAP_Y),
        layer: li,
      })
    })
  })

  return {
    positions,
    backEdgeIds,
    layers,
    width: contentWidth,
    height: contentHeight,
  }
}
