import { describe, it, expect } from 'vitest'
import { buildSuggestedQuestions, pruneStaleRecents } from './suggestedQuestions'
import type { TopologySchemaDoc } from './api'

const schema: TopologySchemaDoc = {
  mode: 'custom',
  nodes: [
    { id: 'caddy', label: 'Caddy', kind: 'gateway', tier: 0 },
    { id: 'backend', label: 'Backend', kind: 'backend', tier: 2 },
    { id: 'frontend', label: 'Frontend', kind: 'frontend', tier: 1 },
  ],
  edges: [
    { source: 'backend', target: 'caddy', relationship: 'DEPENDS_ON', kind: 'static' },
  ],
}

describe('buildSuggestedQuestions', () => {
  it('returns [] with no topology so the caller can fall back to defaults', () => {
    expect(buildSuggestedQuestions(null)).toEqual([])
    expect(buildSuggestedQuestions({ nodes: [] })).toEqual([])
  })

  it('produces service-named questions from the topology', () => {
    const qs = buildSuggestedQuestions(schema)
    expect(qs[0]).toMatch(/current health/i)
    // Entry points first (tier order): Caddy(0), Frontend(1), Backend(2).
    expect(qs).toContain('How is Caddy doing right now?')
    expect(qs).toContain('How is Frontend doing right now?')
    // A dependency question from the real edge (backend depends on caddy).
    expect(qs).toContain('What does Backend depend on?')
    expect(qs).toContain('Show me recent errors across all services')
  })

  it('caps the number of questions', () => {
    expect(buildSuggestedQuestions(schema, 3).length).toBe(3)
  })

  it('does not add a dependency question when the graph has no edges', () => {
    const noEdges = { ...schema, edges: [] }
    const qs = buildSuggestedQuestions(noEdges)
    expect(qs.some((q) => /depend on\?/.test(q))).toBe(false)
  })
})

describe('pruneStaleRecents', () => {
  it('drops recents naming an infra service not in the topology', () => {
    const recents = [
      'Restart neo4j please',
      'Why is nextcloud slow?',
      'How is the backend doing?',
      'Summarize system health',
    ]
    const kept = pruneStaleRecents(recents, schema)
    expect(kept).toEqual(['How is the backend doing?', 'Summarize system health'])
  })

  it('keeps recents naming a service that IS in the topology', () => {
    const topo: TopologySchemaDoc = {
      mode: 'custom',
      nodes: [{ id: 'neo4j', label: 'Neo4j', kind: 'datastore', tier: 3 }],
      edges: [],
    }
    expect(pruneStaleRecents(['Restart neo4j'], topo)).toEqual(['Restart neo4j'])
  })

  it('leaves generic recents untouched', () => {
    const recents = ['What does the safety gate do?', 'Show recent errors']
    expect(pruneStaleRecents(recents, schema)).toEqual(recents)
  })
})
