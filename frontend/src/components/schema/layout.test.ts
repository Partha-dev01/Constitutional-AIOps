import { describe, it, expect } from 'vitest'
import { layoutTopology, GAP_X, GAP_Y_TD, MAX_TD_ROW, NODE_H, NODE_W } from './layout'
import type { TopologyNode, TopologyEdge } from './types'

function node(id: string, kind: string, tier: number): TopologyNode {
  return {
    id,
    label: id,
    kind,
    tier,
    health: 'healthy',
    episode_count: 0,
    incident_count: 0,
    buckets: [],
    recent_episodes: [],
    meta: {},
  }
}

function edge(
  source: string,
  target: string,
  relationship: 'DEPENDS_ON' | 'SHIPS_TELEMETRY' = 'DEPENDS_ON',
  kind: 'static' | 'dynamic' = 'static',
): TopologyEdge {
  return {
    id: `${source}->${target}`,
    source,
    target,
    relationship,
    kind,
    co_episode_count: 0,
    buckets: [],
  }
}

// The locked platform topology (subset sufficient for layering assertions).
function platform(): { nodes: TopologyNode[]; edges: TopologyEdge[] } {
  const nodes = [
    node('caddy', 'gateway', 0),
    node('frontend', 'frontend', 1),
    node('backend', 'backend', 2),
    node('neo4j', 'datastore', 3),
    node('loki', 'observability', 3),
    node('qwen3-14b', 'llm', 3),
  ]
  const edges = [
    edge('caddy', 'frontend'),
    edge('caddy', 'backend'),
    edge('backend', 'neo4j'),
    edge('backend', 'loki'),
    edge('backend', 'qwen3-14b'),
  ]
  return { nodes, edges }
}

describe('layoutTopology', () => {
  it('assigns every node a finite position', () => {
    const { nodes, edges } = platform()
    const { positions } = layoutTopology(nodes, edges)
    expect(positions.size).toBe(nodes.length)
    for (const n of nodes) {
      const p = positions.get(n.id)
      expect(p).toBeDefined()
      expect(Number.isFinite(p!.x)).toBe(true)
      expect(Number.isFinite(p!.y)).toBe(true)
      expect(Number.isFinite(p!.layer)).toBe(true)
    }
  })

  it('layers downstream services strictly right of their dependency', () => {
    const { nodes, edges } = platform()
    const { positions } = layoutTopology(nodes, edges)
    const caddy = positions.get('caddy')!
    const backend = positions.get('backend')!
    const neo4j = positions.get('neo4j')!
    const qwen = positions.get('qwen3-14b')!
    expect(caddy.layer).toBe(0)
    expect(backend.layer).toBeGreaterThan(caddy.layer)
    expect(neo4j.layer).toBeGreaterThan(backend.layer)
    expect(qwen.layer).toBeGreaterThan(backend.layer)
    // Greater layer => greater x.
    expect(backend.x).toBeGreaterThan(caddy.x)
    expect(neo4j.x).toBeGreaterThan(backend.x)
  })

  it('pins edge-host nodes to the final (right-most) layer', () => {
    const { nodes, edges } = platform()
    const ext = [
      ...nodes,
      node('edge:nextcloud-host', 'edge', 0),
    ]
    const extEdges = [
      ...edges,
      edge('edge:nextcloud-host', 'loki', 'SHIPS_TELEMETRY', 'dynamic'),
      edge('edge:nextcloud-host', 'prometheus', 'SHIPS_TELEMETRY', 'dynamic'),
    ]
    const { positions } = layoutTopology(ext, extEdges)
    const host = positions.get('edge:nextcloud-host')!
    const maxLayer = Math.max(
      ...nodes.map((n) => positions.get(n.id)!.layer),
    )
    expect(host.layer).toBeGreaterThan(maxLayer)
  })

  it('does not throw or NaN on a cyclic input', () => {
    const nodes = [node('a', 'backend', 0), node('b', 'backend', 0), node('c', 'backend', 0)]
    const edges = [edge('a', 'b'), edge('b', 'c'), edge('c', 'a')]
    let result!: ReturnType<typeof layoutTopology>
    expect(() => {
      result = layoutTopology(nodes, edges)
    }).not.toThrow()
    expect(result.positions.size).toBe(3)
    expect(result.backEdgeIds.size).toBeGreaterThanOrEqual(1)
    for (const n of nodes) {
      expect(Number.isFinite(result.positions.get(n.id)!.x)).toBe(true)
    }
  })

  it('is deterministic for a given topology', () => {
    const a = platform()
    const b = platform()
    const r1 = layoutTopology(a.nodes, a.edges)
    const r2 = layoutTopology(b.nodes, b.edges)
    for (const n of a.nodes) {
      expect(r2.positions.get(n.id)).toEqual(r1.positions.get(n.id))
    }
  })

  it("defaults to 'lr' and is unchanged by passing the default direction", () => {
    const { nodes, edges } = platform()
    const implicit = layoutTopology(nodes, edges)
    const explicit = layoutTopology(nodes, edges, 'lr')
    for (const n of nodes) {
      expect(explicit.positions.get(n.id)).toEqual(implicit.positions.get(n.id))
    }
    expect(explicit.width).toBe(implicit.width)
    expect(explicit.height).toBe(implicit.height)
  })

  it("'td' transposes the flow: deeper tiers move DOWN (greater y), not right", () => {
    const { nodes, edges } = platform()
    const td = layoutTopology(nodes, edges, 'td')
    const lr = layoutTopology(nodes, edges, 'lr')
    const caddy = td.positions.get('caddy')!
    const backend = td.positions.get('backend')!
    const neo4j = td.positions.get('neo4j')!
    // Same layering (direction-free), but advancing along Y instead of X.
    expect(td.layers).toEqual(lr.layers)
    expect(backend.layer).toBeGreaterThan(caddy.layer)
    expect(backend.y).toBeGreaterThan(caddy.y)
    expect(neo4j.y).toBeGreaterThan(backend.y)
    // Layer count drives td height; the widest layer drives td width.
    expect(td.height).toBeGreaterThan(0)
    expect(td.width).toBeGreaterThan(0)
  })

  it("'td' keeps every node finite and tolerates cycles", () => {
    const nodes = [node('a', 'episode', 0), node('b', 'root_cause', 1), node('c', 'service', 3)]
    const edges = [edge('a', 'b'), edge('b', 'c'), edge('c', 'a')]
    let result!: ReturnType<typeof layoutTopology>
    expect(() => {
      result = layoutTopology(nodes, edges, 'td')
    }).not.toThrow()
    expect(result.positions.size).toBe(3)
    for (const n of nodes) {
      const p = result.positions.get(n.id)!
      expect(Number.isFinite(p.x)).toBe(true)
      expect(Number.isFinite(p.y)).toBe(true)
    }
  })

  // --- Episodic causal-tree layout (td-only) ------------------------------
  // The episodic view feeds layoutTopology a causal tree
  // incident/episode → root_cause → action → service. These lock in the
  // graceful 'td' rendering the Command Center relies on.

  it("'td' lays out a full causal tree tier-by-tier, strictly downward", () => {
    // episode(0) → root_cause(1) → action(2) → service(3): one node per tier.
    const nodes = [
      node('ep', 'episode', 0),
      node('rc', 'root_cause', 1),
      node('act', 'action', 2),
      node('svc', 'service', 3),
    ]
    const edges = [edge('ep', 'rc'), edge('rc', 'act'), edge('act', 'svc')]
    const td = layoutTopology(nodes, edges, 'td')
    const ep = td.positions.get('ep')!
    const rc = td.positions.get('rc')!
    const act = td.positions.get('act')!
    const svc = td.positions.get('svc')!
    // Each causal step sits strictly below the previous one.
    expect(rc.y).toBeGreaterThan(ep.y)
    expect(act.y).toBeGreaterThan(rc.y)
    expect(svc.y).toBeGreaterThan(act.y)
    // Adjacent tiers are spaced by exactly one node height + the td gap (no overlap).
    expect(rc.y - ep.y).toBe(svc.y - act.y)
    expect(td.height).toBeGreaterThan(0)
  })

  it("'td' COMPACTS empty tiers (episode → service with no root_cause/action)", () => {
    // Only tiers 0 and 3 are occupied; tiers 1 and 2 are empty. The transpose
    // must collapse the gap so the two rows are adjacent, not separated by two
    // blank bands (otherwise the cascade is a sliver in a tall pane).
    const nodes = [node('ep', 'episode', 0), node('svc', 'service', 3)]
    const edges = [edge('ep', 'svc')]
    const td = layoutTopology(nodes, edges, 'td')
    const ep = td.positions.get('ep')!
    const svc = td.positions.get('svc')!
    expect(svc.y).toBeGreaterThan(ep.y)
    // Two occupied tiers collapse to two ADJACENT visual rows: exactly one
    // (node height + td gap) apart, with the empty tiers 1 & 2 squeezed out.
    expect(svc.y - ep.y).toBe(NODE_H + GAP_Y_TD)
    // Total height spans exactly those two rows + the single gap between them.
    expect(td.height).toBe(2 * NODE_H + GAP_Y_TD)
  })

  it("'td' WRAPS a tier wider than MAX_TD_ROW into balanced sub-rows", () => {
    // A single tier with more than MAX_TD_ROW siblings (e.g. many episodes) must
    // wrap into multiple visual rows instead of one long thin line.
    const wide = MAX_TD_ROW + 3
    const nodes = Array.from({ length: wide }, (_, i) => node(`e${i}`, 'episode', 0))
    const td = layoutTopology(nodes, [], 'td')
    // Distinct (x,y) for every node — nothing stacked on top of another card.
    const seen = new Set<string>()
    let maxY = 0
    for (const n of nodes) {
      const p = td.positions.get(n.id)!
      seen.add(`${p.x},${p.y}`)
      maxY = Math.max(maxY, p.y)
    }
    expect(seen.size).toBe(wide)
    // Wrapped ⇒ more than one row ⇒ some node sits below the first row.
    expect(maxY).toBeGreaterThan(0)
    // Width reflects the widest SUB-row, not the full unwrapped tier.
    expect(td.width).toBeLessThan(wide * NODE_W + (wide - 1) * GAP_X)
  })
})
