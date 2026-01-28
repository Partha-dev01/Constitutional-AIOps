// Constitutional AIOps - Graph Cleanup Script
// Run this in Neo4j Browser to clean up the messy graph
// v0.6.0 - Hairball Prevention

// Step 1: Delete ALL SIMILAR_TO edges (will be recalculated with 0.75 threshold)
MATCH ()-[r:SIMILAR_TO]->()
DELETE r
RETURN count(r) as similar_to_deleted;

// Step 2: Merge duplicate Entity nodes (case-insensitive)
// This requires APOC plugin. If not available, skip this step.
// CALL apoc.periodic.iterate(
//   "MATCH (e1:Entity), (e2:Entity) WHERE toLower(e1.name) = toLower(e2.name) AND id(e1) < id(e2) RETURN e1, e2",
//   "CALL apoc.refactor.mergeNodes([e1, e2], {properties: 'combine'}) YIELD node RETURN node",
//   {batchSize: 100}
// );

// Alternative for Step 2 without APOC: Just delete duplicates
MATCH (e1:Entity)
WITH toLower(e1.name) as name, collect(e1) as nodes
WHERE size(nodes) > 1
UNWIND tail(nodes) as duplicate
DETACH DELETE duplicate
RETURN count(duplicate) as duplicates_deleted;

// Step 3: Delete orphan entities (no relationships)
MATCH (e:Entity)
WHERE NOT (e)--()
DELETE e
RETURN count(e) as orphans_deleted;

// Step 4: Keep only last 50 episodes (prune old data)
MATCH (ep:Episode)
WITH ep ORDER BY ep.detected_at DESC
SKIP 50
DETACH DELETE ep
RETURN count(ep) as old_episodes_deleted;

// Step 5: Delete low-confidence RELATES edges (< 0.70)
MATCH ()-[r:RELATES]->()
WHERE r.confidence < 0.70
DELETE r
RETURN count(r) as low_confidence_deleted;

// Step 6: Verify cleanup - get current stats
MATCH (n) WITH count(n) as nodes
MATCH ()-[r]->() WITH nodes, count(r) as edges
MATCH (e:Episode) WITH nodes, edges, count(e) as episodes
MATCH ()-[s:SIMILAR_TO]->() WITH nodes, edges, episodes, count(s) as similar_to
MATCH (ent:Entity) WITH nodes, edges, episodes, similar_to, count(ent) as entities
RETURN nodes, edges, episodes, similar_to, entities;
