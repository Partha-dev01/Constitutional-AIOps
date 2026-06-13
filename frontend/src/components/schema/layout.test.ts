import { describe, it, expect } from 'vitest'
import { layoutTopology } from './layout'
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
})
