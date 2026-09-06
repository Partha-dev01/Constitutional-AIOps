/**
 * Pure helpers for the Dashboard "Blast-radius preview" widget (Track 2).
 *
 * A client-side BFS over the service topology: given a focus service, which
 * services sit downstream of it (follow each edge source -> target) and would
 * be in the blast radius if it degraded. Kept out of the component so the graph
 * walk is unit testable and no LLM call is ever involved.
 */

export interface BlastEdge {
  source: string
  target: string
}

/**
 * BFS downstream from focusId along source -> target edges, up to maxDepth hops.
 * levels[d] holds the node ids first reached at hop d+1, with focus excluded and
 * every node deduped to its shortest hop. total is the count of distinct
 * affected ids. Empty edges or an unknown/leaf focus yield { levels: [], total: 0 }.
 * The visited set doubles as a cycle guard so the walk always terminates.
 */
export function computeBlastRadius(
  edges: BlastEdge[],
  focusId: string,
  maxDepth = 2,
): { levels: string[][]; total: number } {
  if (!focusId || edges.length === 0 || maxDepth < 1) {
    return { levels: [], total: 0 }
  }

  // Adjacency source -> unique targets, first-seen order preserved.
  const adjacency = new Map<string, string[]>()
  for (const { source, target } of edges) {
    if (!source || !target) continue
    const outs = adjacency.get(source) ?? []
    if (!outs.includes(target)) outs.push(target)
    adjacency.set(source, outs)
  }

  const levels: string[][] = []
  const visited = new Set<string>([focusId]) // excludes focus and blocks cycles back to it
  let frontier: string[] = [focusId]

  for (let depth = 0; depth < maxDepth && frontier.length > 0; depth++) {
    const next: string[] = []
    for (const node of frontier) {
      for (const target of adjacency.get(node) ?? []) {
        if (visited.has(target)) continue // shortest-hop dedupe + cycle guard
        visited.add(target)
        next.push(target)
      }
    }
    if (next.length === 0) break
    levels.push(next)
    frontier = next
  }

  const total = levels.reduce((sum, level) => sum + level.length, 0)
  return { levels, total }
}

/** The services one hop downstream of focusId (the direct dependents). */
export function directDependents(edges: BlastEdge[], focusId: string): string[] {
  return computeBlastRadius(edges, focusId, 1).levels[0] ?? []
}
