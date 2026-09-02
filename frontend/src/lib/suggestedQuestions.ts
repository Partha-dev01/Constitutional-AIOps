/**
 * Topology-tuned suggested chat questions.
 *
 * Turns the deployment's ACTUAL service topology (GET /topology/schema) into
 * service-named starter questions, so the chat empty-state reflects what is
 * really deployed instead of generic or stale prompts. Pure + deterministic so
 * it unit-tests in isolation; the caller falls back to the generic
 * DEFAULT_PROMPTS when there is no topology yet.
 */

import type { TopologySchemaNode, TopologySchemaEdge } from './api'

/** Minimal shape this module needs — accepts the full schema doc or a subset. */
interface TopologyLike {
  nodes?: TopologySchemaNode[]
  edges?: TopologySchemaEdge[]
}

const MAX_QUESTIONS = 6

/**
 * Common infrastructure service names. A recent prompt that names one of these
 * but the CURRENT topology does not is treated as stale and pruned (this is what
 * removes leftover `neo4j`/`nextcloud` chips after the topology changed).
 */
const KNOWN_SERVICE_WORDS = [
  'neo4j', 'nextcloud', 'postgres', 'postgresql', 'mysql', 'mariadb', 'redis',
  'loki', 'prometheus', 'grafana', 'tempo', 'mongo', 'mongodb', 'nginx', 'caddy',
  'kafka', 'rabbitmq', 'elasticsearch', 'elastic', 'minio', 'vault', 'consul',
  'ollama', 'vllm', 'qdrant', 'clickhouse', 'cassandra',
]

function validNodes(topology: TopologyLike | null | undefined): TopologySchemaNode[] {
  const nodes = topology?.nodes
  if (!Array.isArray(nodes)) return []
  return nodes.filter((n): n is TopologySchemaNode => !!n && typeof n.label === 'string' && n.label.trim().length > 0)
}

/** Lowercased alnum tokens that appear anywhere in the topology (labels + ids). */
function topologyTokens(topology: TopologyLike | null | undefined): Set<string> {
  const tokens = new Set<string>()
  for (const n of validNodes(topology)) {
    for (const raw of [n.label, n.id]) {
      for (const part of String(raw).toLowerCase().split(/[^a-z0-9]+/)) {
        if (part) tokens.add(part)
      }
    }
  }
  return tokens
}

/**
 * Build service-named starter questions from the topology. Deterministic:
 * a system-wide health question, per-service health questions for the first
 * few services (entry points first, by tier), a dependency question when the
 * graph has one, and an errors question. Empty array when there is no topology
 * (the caller then uses the generic defaults).
 */
export function buildSuggestedQuestions(
  topology: TopologyLike | null | undefined,
  max: number = MAX_QUESTIONS,
): string[] {
  const nodes = validNodes(topology)
  if (nodes.length === 0) return []

  const out: string[] = ['Summarize the current health of my system']

  // Entry points first (lowest tier), then alphabetical for stability.
  const ordered = [...nodes].sort((a, b) => {
    const ta = typeof a.tier === 'number' ? a.tier : 99
    const tb = typeof b.tier === 'number' ? b.tier : 99
    return ta - tb || a.label.localeCompare(b.label)
  })

  for (const node of ordered.slice(0, 3)) {
    out.push(`How is ${node.label} doing right now?`)
  }

  // A dependency question for the first node that actually depends on something.
  const edges = Array.isArray(topology?.edges) ? (topology!.edges as TopologySchemaEdge[]) : []
  const labelById = new Map(nodes.map((n) => [n.id, n.label]))
  const depEdge = edges.find(
    (e) => e && e.relationship === 'DEPENDS_ON' && labelById.has(e.source),
  )
  if (depEdge) {
    out.push(`What does ${labelById.get(depEdge.source)} depend on?`)
  }

  out.push('Show me recent errors across all services')

  // Dedupe (case-insensitive) and cap.
  const seen = new Set<string>()
  const deduped: string[] = []
  for (const q of out) {
    const key = q.trim().toLowerCase()
    if (!key || seen.has(key)) continue
    seen.add(key)
    deduped.push(q)
    if (deduped.length >= max) break
  }
  return deduped
}

/**
 * Drop recent prompts that name a common infra service which is NOT part of the
 * current topology — the fix for stale `neo4j`/`nextcloud` chips lingering after
 * the monitored services changed. Recents that name no such absent service (or
 * name one that IS in the topology) are kept unchanged.
 */
export function pruneStaleRecents(
  recents: string[],
  topology: TopologyLike | null | undefined,
): string[] {
  const tokens = topologyTokens(topology)
  return recents.filter((prompt) => {
    const lower = prompt.toLowerCase()
    for (const word of KNOWN_SERVICE_WORDS) {
      // Word-boundary match so "postgres" doesn't trip on a substring.
      if (new RegExp(`\\b${word}\\b`).test(lower) && !tokens.has(word)) {
        return false // names an absent infra service => stale
      }
    }
    return true
  })
}
