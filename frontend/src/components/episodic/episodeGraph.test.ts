import { describe, it, expect } from 'vitest'
import type { EpisodicLink, EpisodicNode } from '../EpisodicGraphExplorer'
import { buildFocusGraph, buildIndex, resolveEndpoint } from './episodeGraph'

// Mirrors the transformEpisodes output: episode ids are `episode-<id>`, while
// backend root_cause / action / service nodes use their already-prefixed raw id.
function sampleData(): { nodes: EpisodicNode[]; links: EpisodicLink[] } {
  const nodes: EpisodicNode[] = [
    {
      id: 'episode-1',
      label: 'High CPU on backend saturating the reasoning agent',
      type: 'episode',
      status: 'resolved',
      severity: 'critical',
      category: 'performance',
      rootCause: 'memory_leak',
      timestamp: '2026-06-10T10:00:00Z',
    },
    {
      id: 'episode-2',
      label: 'Neo4j connection timeout',
      type: 'episode',
      status: 'analyzing',
      severity: 'high',
      timestamp: '2026-06-11T10:00:00Z',
    },
    { id: 'rootcause-memory_leak', label: 'memory_leak', type: 'root_cause', frequency: 3 },
    { id: 'action-restart', label: 'restart_service', type: 'action', usedCount: 12 },
    { id: 'service-backend', label: 'backend', type: 'service', status: 'warning' },
    { id: 'service-neo4j', label: 'neo4j', type: 'service', status: 'healthy' },
    // An entity + a similar_to peer that must NOT appear in any focus subgraph.
    { id: 'entity-foo', label: 'foo', type: 'entity', relationCount: 4 },
  ]
  const links: EpisodicLink[] = [
    { source: 'episode-1', target: 'rootcause-memory_leak', type: 'caused_by', weight: 1 },
    { source: 'episode-1', target: 'service-backend', type: 'affects', weight: 1 },
    { source: 'episode-1', target: 'action-restart', type: 'resolved_by', weight: 1 },
    { source: 'episode-2', target: 'service-neo4j', type: 'affects', weight: 1 },
    { source: 'episode-1', target: 'episode-2', type: 'similar_to', weight: 0.8 },
    { source: 'entity-foo', target: 'episode-1', type: 'relates', weight: 1 },
  ]
  return { nodes, links }
}

describe('resolveEndpoint', () => {
  it('matches a raw id directly', () => {
    const ids = new Set(['rootcause-memory_leak'])
    expect(resolveEndpoint('rootcause-memory_leak', ids)).toBe('rootcause-memory_leak')
  })
  it('returns undefined when nothing matches', () => {
    expect(resolveEndpoint('nope', new Set(['a', 'b']))).toBeUndefined()
  })
})

describe('buildIndex', () => {
  it('lists every episode, newest first, with full untruncated titles', () => {
    const { nodes, links } = sampleData()
    const index = buildIndex(nodes, links)
    expect(index.episodes.map((e) => e.id)).toEqual(['episode-2', 'episode-1'])
    expect(index.episodes[1].title).toBe('High CPU on backend saturating the reasoning agent')
  })

  it('derives each episode root cause, services and actions from causal edges', () => {
    const { nodes, links } = sampleData()
    const index = buildIndex(nodes, links)
    const ep1 = index.episodes.find((e) => e.id === 'episode-1')!
    expect(ep1.rootCauseId).toBe('rootcause-memory_leak')
    expect(ep1.serviceIds).toEqual(['service-backend'])
    expect(ep1.actionIds).toEqual(['action-restart'])
    expect(ep1.rootCauseLabel).toBe('memory_leak')
  })

  it('never includes similar_to in the resolved causal edge set', () => {
    const { nodes, links } = sampleData()
    const index = buildIndex(nodes, links)
    expect(index.edges.some((e) => e.relation === 'similar_to')).toBe(false)
  })
})

describe('buildFocusGraph', () => {
  it('returns ONLY the episode and its one-hop causal neighbours', () => {
    const { nodes, links } = sampleData()
    const index = buildIndex(nodes, links)
    const focus = buildFocusGraph(index, 'episode-1')!
    const ids = focus.nodes.map((n) => n.id).sort()
    // episode + root cause + action + service — no entity, no episode-2.
    expect(ids).toEqual(['action-restart', 'episode-1', 'rootcause-memory_leak', 'service-backend'])
    expect(ids).not.toContain('entity-foo')
    expect(ids).not.toContain('episode-2')
  })

  it('places nodes on the right tiers for a clean top-down cascade', () => {
    const { nodes, links } = sampleData()
    const index = buildIndex(nodes, links)
    const focus = buildFocusGraph(index, 'episode-1')!
    const tier = (id: string) => focus.nodes.find((n) => n.id === id)!.tier
    expect(tier('episode-1')).toBe(0)
    expect(tier('rootcause-memory_leak')).toBe(1)
    expect(tier('action-restart')).toBe(2)
    expect(tier('service-backend')).toBe(3)
  })

  it('synthesizes an episode→root_cause edge when only a label match exists', () => {
    // Drop the explicit caused_by edge; keep the rootCause text + RC node.
    const { nodes } = sampleData()
    const links: EpisodicLink[] = [
      { source: 'episode-1', target: 'service-backend', type: 'affects', weight: 1 },
    ]
    const index = buildIndex(nodes, links)
    const ep1 = index.episodes.find((e) => e.id === 'episode-1')!
    expect(ep1.rootCauseId).toBe('rootcause-memory_leak') // matched by label
    const focus = buildFocusGraph(index, 'episode-1')!
    expect(
      focus.edges.some(
        (e) => e.source === 'episode-1' && e.target === 'rootcause-memory_leak',
      ),
    ).toBe(true)
  })

  it('returns null for an unknown episode id', () => {
    const { nodes, links } = sampleData()
    const index = buildIndex(nodes, links)
    expect(buildFocusGraph(index, 'episode-nope')).toBeNull()
  })
})
