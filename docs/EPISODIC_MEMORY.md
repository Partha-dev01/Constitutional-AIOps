# Graph-Episodic Memory System

**Source**: `src/memory/episode_store.py`, `src/memory/neo4j_client.py`, `src/memory/retrieval.py`
**Inspiration**: AriGraph dual-memory architecture (semantic + episodic)
**Storage**: Neo4j 5.x (Community Edition, bolt://localhost:7687)

---

## Neo4j Node & Edge Schema

```mermaid
graph TD

    %% ── NODE TYPES ──────────────────────────────────────────────
    EP["📋 Episode\n─────────────────\nepisode_id\nincident_id\ntitle · category\nseverity · outcome\nroot_cause\nconfidence: float\ndetected_at: datetime\nembedding: JSON str\n384-dim vector"]

    SVC["⚙️ Service\n─────────────────\nname\nnamespace"]

    RCT["🔍 RootCauseType\n─────────────────\nname\n(memory · cpu · storage\nnetwork · database\nconfiguration\ndeployment · dependency)"]

    ACT["🔧 Action\n─────────────────\nname\n(remediation step\ne.g. restart pod\nscale deployment)"]

    ENT["🏷️ Entity\n─────────────────\nname\n(canonicalized)\n(LLM-extracted —\nany free-form entity)"]

    INC["⚠️ Incident\n─────────────────\nid · title\nseverity · status\ncategory · source\ncreated_at"]

    %% ── RELATIONSHIPS ────────────────────────────────────────────

    EP -- "INVOLVES\n(which services\nwere affected)" --> SVC
    EP -- "CAUSED_BY\nconfidence: float" --> RCT
    RCT -- "RESOLVED_BY\nconfidence: float\nsource_episode" --> ACT
    SVC -- "EXPERIENCED\nconfidence: float\nsource_episode" --> RCT
    EP -. "SIMILAR_TO\ncosine ≥ 0.75\nmax 3 edges/episode\n(recalc at query time)" .-> EP
    SVC -- "IMPACTED\nconfidence: float" --> SVC
    SVC -- "DEPENDS_ON\ntype: calls/uses" --> SVC
    ENT -- "RELATES\ntype: dynamic label\nconfidence: float\nextraction: llm" --> ENT
    EP -- "EXTRACTED\n(LLM triplets only)" --> ENT
    INC -- "AFFECTS" --> SVC
    ACT -. "REMEDIATES" .-> INC

    %% ── STYLING ─────────────────────────────────────────────────
    style EP  fill:#1a3a5c,color:#aaddff,stroke:#4488bb
    style SVC fill:#1a3a1a,color:#aaffaa,stroke:#44aa44
    style RCT fill:#3a2a1a,color:#ffddaa,stroke:#aa8844
    style ACT fill:#3a1a3a,color:#ffaaff,stroke:#aa44aa
    style ENT fill:#2d2d2d,color:#cccccc,stroke:#666666
    style INC fill:#4a2020,color:#ffaaaa,stroke:#aa4444
```

---

## How an Episode Gets Stored

```mermaid
sequenceDiagram
    participant P as Pipeline<br/>(LangGraph / Runner)
    participant ES as EpisodeStore
    participant EMB as EmbeddingService<br/>(all-MiniLM-L6-v2)
    participant N4J as Neo4j

    P->>ES: store_episode(episode)

    ES->>EMB: encode(get_embedding_text())<br/>title + description + category<br/>+ severity + root_cause + services
    EMB-->>ES: 384-dim float[] vector

    ES->>ES: generate_signature()<br/>md5(category + sorted_services<br/>+ root_cause_type)
    ES->>ES: _memory_store[episode_id] = episode<br/>_signature_index[sig].append(id)

    ES->>N4J: MERGE (e:Episode {episode_id})<br/>SET all fields + embedding as JSON str

    loop for each affected_service
        ES->>N4J: MERGE (s:Service {name})<br/>MERGE (e)-[:INVOLVES]->(s)
    end

    ES->>N4J: MERGE (rct:RootCauseType {name})<br/>MERGE (e)-[:CAUSED_BY {confidence}]->(rct)

    Note over ES,N4J: Rule-based triplets (extract_semantic_triplets)
    loop EXPERIENCED / IMPACTED / RESOLVED_BY
        ES->>N4J: MERGE nodes + edges with confidence
    end

    Note over ES,N4J: LLM-extracted triplets (episode.triplets)<br/>filtered: confidence ≥ 0.70
    loop LLM triplet
        ES->>N4J: MERGE (s:Entity)-[:RELATES {type, confidence}]->(o:Entity)
    end
```

---

## How Retrieval Works (Hybrid)

```mermaid
flowchart TD
    Q([New Incident / Query]) --> A

    A["Build query embedding\nall-MiniLM-L6-v2\n→ 384-dim vector"]

    A --> B & C

    B["🔢 Vector Similarity\n─────────────────\nFetch all Episode.embedding\nfrom Neo4j (JSON → numpy)\nCompute cosine similarity\nFilter: sim ≥ 0.60\nTop-K = 3"]

    C["🕸️ Graph Similarity\n─────────────────\nRule-based score:\n• category match   → 0.3\n• service overlap  → 0.4\n  (Jaccard: |A∩B|/|A∪B|)\n• root_cause match → 0.3"]

    B --> D
    C --> D

    D["Hybrid Score\n─────────────────\nscore = α · vector_sim\n      + (1-α) · graph_sim\n\nα = 0.6 (from paper §3.4)\nO(log n) retrieval complexity"]

    D --> E["Sort descending\nFilter: score ≥ 0.70\nReturn top-5 episodes"]

    E --> F["Build RetrievalContext\n─────────────────\nsimilar_incidents\nservice_dependencies\nsuccessful_remediation_patterns\ncommon_root_causes\ncategory_stats"]

    F --> G["to_prompt_context(max_tokens=2000)\n→ injected into ReasoningAgent prompt\nas prior_context for RCA"]

    style Q fill:#1a1a2e,color:#eee,stroke:#444
    style D fill:#1a3a5c,color:#aaddff,stroke:#4488bb
    style G fill:#1a3a1a,color:#aaffaa,stroke:#44aa44
```

---

## Triplet Types — Explained

| Relationship | Source → Target | Extracted by | Example |
|---|---|---|---|
| `INVOLVES` | Episode → Service | Rule (affected_services list) | episode_42 → payment-svc |
| `CAUSED_BY` | Episode → RootCauseType | Rule (_extract_root_cause_type) | episode_42 → memory |
| `EXPERIENCED` | Service → RootCauseType | Rule (service × root_cause_type) | payment-svc → memory |
| `IMPACTED` | Service → Service | Rule (primary → each other affected) | payment-svc → order-svc |
| `RESOLVED_BY` | RootCauseType → Action | Rule (successful_actions) | memory → restart pod |
| `RELATES` | Entity → Entity | **LLM-extracted** (confidence ≥ 0.70) | OOM → heap exhaustion |
| `EXTRACTED` | Episode → Entity | LLM triplets traceability | episode_42 → OOM |
| `SIMILAR_TO` | Episode → Episode | Computed at query time (cosine ≥ 0.75, max 3/node) | episode_42 → episode_17 |
| `DEPENDS_ON` | Service → Service | Service topology / traces | frontend → auth-svc |
| `AFFECTS` | Incident → Service | Incident management API | INC-001 → db-replica |

---

## Semantic Triplet Extraction (AriGraph Pattern)

Each episode produces two classes of triplets:

**1. Rule-based** — deterministic, always produced:
```
for service in episode.affected_services:
    (service)  -[EXPERIENCED]->  (root_cause_type)

for i in causal_chain[:-1]:
    (causal_chain[i])  -[CAUSED]->  (causal_chain[i+1])

for dependent in affected_services[1:]:
    (primary_service)  -[IMPACTED]->  (dependent)

for action in successful_actions:
    (root_cause_type)  -[RESOLVED_BY]->  (action)
```

**2. LLM-extracted** — dynamic labels, stored as `Entity -[:RELATES {type}]-> Entity`:
- Produced by `FastAnnotator` during annotation
- Filtered: `confidence ≥ MIN_TRIPLET_CONFIDENCE (0.70)`
- Entities are canonicalized before storage to prevent duplicates
- Stored with `extraction_method: 'llm'` tag on the edge

---

## Graph Degree Caps (anti-hairball, v0.6.0)

| Constant | Value | Purpose |
|---|---|---|
| `SIMILAR_TO_THRESHOLD` | 0.75 cosine | Minimum to draw a SIMILAR_TO edge |
| `MAX_SIMILAR_EDGES_PER_EPISODE` | 3 | Prevents a single episode linking to everything |
| `MIN_TRIPLET_CONFIDENCE` | 0.70 | Filters low-quality LLM triplets |
| `MAX_EDGES_PER_NODE` | 5 | Global degree cap (Graph Explorer) |

---

## Current Graph State (Post Phase 4.4, 2026-05-13)

| Label | Count |
|---|---|
| Episode | 431 |
| Service | 49 |
| RootCauseType | 8 |
| **INVOLVES** edges | 531 |
| **CAUSED_BY** edges | 431 |
| **EXPERIENCED** edges | 531 |
| **IMPACTED** edges | 100 |

Populated in 28 seconds via `scripts/populate_neo4j.py` from `benchmark_431_seed42.json`.
Embedding: `sentence-transformers/all-MiniLM-L6-v2` (384-dim), stored as JSON string in `Episode.embedding` (Neo4j Community Edition has no native vector type — cosine similarity computed in Python/numpy at query time).
