/**
 * Demo-mode fixtures + route table.
 *
 * When the app is built with VITE_DEMO_MODE=true, lib/demo installs a global
 * fetch shim that answers every same-origin /api/v1/* request from these
 * fixtures instead of a live backend. This lets the marketing "See how it
 * works" button run the REAL UI — no login, no server — purely from bundled
 * JSON.
 *
 * The dataset tells one coherent story that lines up with the Graph topology
 * fixture: the remote edge host `nextcloud-host` degraded (disk pressure ->
 * php-fpm OOM -> database refused), which rippled into the backend API and the
 * Neo4j connection pool. Every page reads from the same narrative.
 */

import topology from './topology.json'

/** What a matched demo route returns. `sse` is used only for the chat stream. */
export interface DemoResult {
  status: number
  json?: unknown
  sse?: Array<{ event: string; data: unknown }>
}

/** ISO timestamp `mins` minutes before now (keeps the demo looking fresh). */
function iso(mins: number): string {
  return new Date(Date.now() - mins * 60_000).toISOString()
}

// ---------------------------------------------------------------------------
// Health + measured agent metrics
// ---------------------------------------------------------------------------

const HEALTH = {
  status: 'degraded',
  version: 'demo',
  uptime_seconds: 60 * 60 * 26 + 15 * 60,
  components: [
    { name: 'backend', healthy: true, latency_ms: 12 },
    { name: 'neo4j', healthy: true, latency_ms: 9 },
    { name: 'fast_agent', healthy: true, latency_ms: 74 },
    { name: 'reasoning_agent', healthy: true, latency_ms: 830 },
    { name: 'loki', healthy: true, latency_ms: 15 },
    { name: 'prometheus', healthy: true, latency_ms: 10 },
    { name: 'tempo', healthy: false, error: 'no telemetry received in window' },
  ],
}

// Full per-agent latency stats. The Dashboard reads count/avg_ms/p95_ms; the
// Metrics page reads the rest (min/max/p50/p99/success_rate/total_tokens).
const LAT_FAST = {
  count: 1284, avg_ms: 74, min_ms: 41, max_ms: 210,
  p50_ms: 70, p95_ms: 121, p99_ms: 180, success_rate: 99.6, total_tokens: 164_352,
}
const LAT_REASONING = {
  count: 342, avg_ms: 830, min_ms: 420, max_ms: 2450,
  p50_ms: 760, p95_ms: 1920, p99_ms: 2280, success_rate: 98.2, total_tokens: 421_000,
}

const DETERMINISM_CONFIG = {
  fast_agent_temperature: 0.0,
  reasoning_agent_temperature: 0.0,
  chat_temperature: 0.5,
  seed_method: 'hash(prompt) % 2^32',
}

/** GET /metrics — a full MetricsSnapshot (Dashboard cards + Metrics overview). */
const AGENT_METRICS = {
  timestamp: new Date().toISOString(),
  fast_agent: LAT_FAST,
  reasoning_agent: LAT_REASONING,
  total_requests: 1626,
  success_rate: 99.1,
  determinism_config: DETERMINISM_CONFIG,
}

// GET /metrics/history — `records` feeds the Metrics "Recent Requests" table;
// `history` is kept for any averaged-series consumer.
const METRICS_HISTORY = {
  history: Array.from({ length: 24 }, (_, i) => ({
    at: iso((23 - i) * 30),
    fast_avg_ms: 60 + Math.round(30 * Math.abs(Math.sin(i / 3))),
    reasoning_avg_ms: 700 + Math.round(500 * Math.abs(Math.sin(i / 4))),
  })),
  records: Array.from({ length: 24 }, (_, i) => {
    const fast = i % 3 !== 0
    return {
      agent: fast ? 'fast' : 'reasoning',
      latency_ms: fast
        ? 60 + Math.round(60 * Math.abs(Math.sin(i / 2)))
        : 700 + Math.round(600 * Math.abs(Math.sin(i / 3))),
      timestamp: iso(i * 7),
      tokens_generated: fast ? 96 + (i % 5) * 24 : 640 + (i % 4) * 160,
      success: i !== 5,
    }
  }),
}

// GET /metrics/validation/report — the Metrics "Validation" tab.
const VALIDATION_REPORT = {
  generated_at: iso(3),
  system_configuration: {
    fast_agent: {
      model: 'Qwen3-4B-AWQ',
      url: 'http://localhost:8000/v1',
      temperature: 0.0,
      purpose: 'Telemetry annotation + severity classification',
    },
    reasoning_agent: {
      model: 'Qwen3-14B-AWQ',
      url: 'http://localhost:8001/v1',
      temperature: 0.0,
      purpose: 'Root-cause analysis + remediation planning',
    },
    chat_mode: { temperature: 0.5, purpose: 'Operator chat + explanations' },
  },
  latency_metrics: {
    fast_agent: LAT_FAST,
    reasoning_agent: LAT_REASONING,
    disclaimer:
      'End-to-end latency measured at the backend (includes queueing + network). Single-node demo figures, not a controlled benchmark.',
  },
  accuracy_metrics: {
    annotation_accuracy: {
      value: 'Not run',
      expected: '87-92%',
      disclaimer: 'Not evaluated in this snapshot. Run the Benchmark page against a labelled corpus.',
    },
    rca_accuracy: {
      value: 'Not run',
      expected: '85-90%',
      disclaimer: 'Not evaluated in this snapshot. See the Benchmark page for scored RCA cases.',
    },
  },
  validation_status: {
    latency: 'Measured',
    determinism: 'Configured (temp=0)',
    annotation_accuracy: 'Pending',
    rca_accuracy: 'Pending',
  },
}

// POST /metrics/validate/determinism — the Metrics determinism panel.
const DETERMINISM_RESULT = {
  determinism_score: 100,
  deterministic_prompts: 5,
  total_prompts: 5,
  iterations_per_prompt: 5,
  configuration: { temperature: 0.0, seed_method: 'hash(prompt) % 2^32' },
  results: [
    { prompt: 'Classify: disk usage on /var/lib/docker at 93%', iterations: 5, unique_outputs: 1, unique_seeds: 1, is_deterministic: true, sample_output: 'severity=warning, component=disk' },
    { prompt: 'Classify: php-fpm worker killed by OOM', iterations: 5, unique_outputs: 1, unique_seeds: 1, is_deterministic: true, sample_output: 'severity=critical, component=runtime' },
    { prompt: 'Classify: connection refused to nextcloud-db', iterations: 5, unique_outputs: 1, unique_seeds: 1, is_deterministic: true, sample_output: 'severity=critical, component=database' },
    { prompt: 'Classify: reasoning queue depth 18', iterations: 5, unique_outputs: 1, unique_seeds: 1, is_deterministic: true, sample_output: 'severity=warning, component=backend' },
    { prompt: 'Classify: GET /api/v1/incidents 200 8ms', iterations: 5, unique_outputs: 1, unique_seeds: 1, is_deterministic: true, sample_output: 'severity=info, component=api' },
  ],
  passed: true,
  timestamp: iso(1),
}

/** POST /metrics/benchmark — a single-agent micro-benchmark result. */
function metricsBenchmark(bodyText?: string) {
  let agent = 'fast'
  let iterations = 10
  if (bodyText) {
    try {
      const b = JSON.parse(bodyText) as { agent?: string; iterations?: number }
      if (b.agent) agent = b.agent
      if (b.iterations) iterations = b.iterations
    } catch {
      // keep defaults
    }
  }
  const lat = agent === 'reasoning' ? LAT_REASONING : LAT_FAST
  return {
    status: 'completed',
    agent,
    iterations,
    successes: iterations,
    total_time_ms: lat.avg_ms * iterations,
    latency: lat,
    success_rate: 100,
    errors: [] as string[],
    timestamp: iso(0),
  }
}

// ---------------------------------------------------------------------------
// Incidents
// ---------------------------------------------------------------------------

const RCA_NEXTCLOUD = {
  root_cause:
    'Disk pressure on /var/lib/docker on nextcloud-host forced php-fpm OOM kills, which dropped the Nextcloud database connection and surfaced as 5xx errors upstream.',
  causal_chain: [
    'Disk usage on /var/lib/docker crossed 92%',
    'php-fpm workers OOM-killed under write pressure',
    'Nextcloud lost its database connection pool',
    'Backend API /chat and /incidents returned 5xx to Caddy',
  ],
  confidence: 0.91,
  reasoning:
    'Loki shows the OOM kill 40s before the first DB-refused log; Prometheus disk-usage series crosses threshold in the same window. Matches 2 prior incidents on this host.',
  similar_incidents: ['inc-1007', 'inc-1002'],
}

const REMEDIATION_NEXTCLOUD = {
  plan_id: 'plan-2043',
  incident_id: 'inc-2043',
  created_at: iso(38),
  steps: [
    {
      order: 1,
      action: 'Prune dangling Docker images/volumes on nextcloud-host',
      command: 'docker system prune -af --volumes',
      risk: 'medium' as const,
      requires_approval: true,
      status: 'pending' as const,
    },
    {
      order: 2,
      action: 'Restart php-fpm and the nextcloud-db container',
      command: 'docker restart nextcloud-db nextcloud-app',
      risk: 'medium' as const,
      requires_approval: true,
      status: 'pending' as const,
    },
    {
      order: 3,
      action: 'Verify /chat and /incidents return 200 through Caddy',
      command: null,
      risk: 'low' as const,
      requires_approval: false,
      status: 'pending' as const,
    },
  ],
  overall_risk: 'medium' as const,
  estimated_duration: '~3 min',
  requires_approval: true,
  approved_by: null,
  approved_at: null,
}

const INCIDENTS = [
  {
    id: 'inc-2043',
    title: 'Nextcloud database connection refused on nextcloud-host',
    description:
      'Repeated 5xx from the backend traced to a lost database connection on the remote edge host.',
    severity: 'critical' as const,
    status: 'pending_approval' as const,
    category: 'availability',
    affected_services: [{ name: 'nextcloud-host' }, { name: 'backend' }],
    tags: ['edge', 'database', 'oom'],
    source: 'loki',
    created_at: iso(42),
    updated_at: iso(6),
    rca: RCA_NEXTCLOUD,
    remediation_plan: REMEDIATION_NEXTCLOUD,
  },
  {
    id: 'inc-2041',
    title: 'Backend API 5xx spike after deploy',
    description: 'Error rate on /chat and /incidents jumped following a rolling deploy.',
    severity: 'high' as const,
    status: 'remediating' as const,
    category: 'errors',
    affected_services: [{ name: 'backend' }],
    tags: ['deploy', '5xx'],
    source: 'prometheus',
    created_at: iso(190),
    updated_at: iso(12),
    rca: {
      root_cause: 'A slow Neo4j query path under the new build backed up the reasoning queue.',
      causal_chain: ['Deploy shipped', 'Neo4j pool saturated', 'Reasoning queue backlog', '5xx to clients'],
      confidence: 0.78,
      reasoning: null,
      similar_incidents: ['inc-2039'],
    },
    remediation_plan: null,
  },
  {
    id: 'inc-2039',
    title: 'Neo4j connection pool exhausted in backend',
    severity: 'high' as const,
    status: 'pending_approval' as const,
    category: 'saturation',
    affected_services: [{ name: 'neo4j' }, { name: 'backend' }],
    tags: ['neo4j', 'pool'],
    source: 'backend',
    created_at: iso(340),
    updated_at: iso(48),
    rca: null,
    remediation_plan: null,
  },
  {
    id: 'inc-2036',
    title: 'Reasoning agent p95 latency elevated',
    severity: 'medium' as const,
    status: 'analyzing' as const,
    category: 'latency',
    affected_services: [{ name: 'qwen3-14b' }],
    tags: ['llm', 'latency'],
    source: 'prometheus',
    created_at: iso(520),
    updated_at: iso(90),
    rca: null,
    remediation_plan: null,
  },
  {
    id: 'inc-2030',
    title: 'Grafana datasource query timeout',
    severity: 'medium' as const,
    status: 'resolved' as const,
    category: 'observability',
    affected_services: [{ name: 'grafana' }, { name: 'prometheus' }],
    tags: ['grafana'],
    source: 'grafana',
    created_at: iso(1500),
    updated_at: iso(1440),
    resolved_at: iso(1440),
    rca: null,
    remediation_plan: null,
  },
  {
    id: 'inc-2021',
    title: 'Loki ingester flush backlog',
    severity: 'low' as const,
    status: 'resolved' as const,
    category: 'observability',
    affected_services: [{ name: 'loki' }],
    tags: ['loki', 'auto-resolved'],
    source: 'loki',
    created_at: iso(2900),
    updated_at: iso(2860),
    resolved_at: iso(2860),
    rca: null,
    remediation_plan: null,
  },
]

const INCIDENT_STATS = {
  total: 6,
  by_status: {
    detecting: 0,
    analyzing: 1,
    pending_approval: 2,
    remediating: 1,
    resolved: 2,
    closed: 0,
  },
  by_severity: { critical: 1, high: 2, medium: 2, low: 1, info: 0 },
  auto_resolved_count: 1,
  mean_time_to_resolution: 4.2,
}

// ---------------------------------------------------------------------------
// Actions (constitutional gate)
// ---------------------------------------------------------------------------

function validation(passed: boolean, level: string, confidence: number) {
  return {
    passed,
    authorization_level: level,
    confidence,
    tier1_passed: true,
    tier2_passed: passed,
    tier3_passed: true,
    violations: [],
    warnings: passed ? [] : ['Requires human approval: touches a stateful service'],
    explanation: passed
      ? 'All tiers satisfied; within the auto-execution confidence band.'
      : 'Confidence in the approval band (0.70–0.90): a human must approve before execution.',
  }
}

const ACTIONS = [
  {
    id: 'act-5011',
    action_type: 'restart_service' as const,
    description: 'Restart nextcloud-db to recover the dropped connection pool',
    target_service: 'nextcloud-db',
    parameters: { reason: 'DB connection refused after OOM' },
    incident_id: 'inc-2043',
    confidence: 0.82,
    status: 'awaiting_approval' as const,
    requires_approval: true,
    validation: validation(false, 'approval_required', 0.82),
    created_at: iso(35),
    updated_at: iso(35),
  },
  {
    id: 'act-5009',
    action_type: 'scale_up' as const,
    description: 'Scale the backend to 3 replicas to drain the reasoning backlog',
    target_service: 'backend',
    parameters: { target_replicas: 3 },
    incident_id: 'inc-2039',
    confidence: 0.74,
    status: 'awaiting_approval' as const,
    requires_approval: true,
    validation: validation(false, 'approval_required', 0.74),
    created_at: iso(46),
    updated_at: iso(46),
  },
  {
    id: 'act-4998',
    action_type: 'restart_service' as const,
    description: 'Restart grafana to clear the datasource timeout',
    target_service: 'grafana',
    parameters: {},
    incident_id: 'inc-2030',
    confidence: 0.94,
    status: 'completed' as const,
    requires_approval: false,
    validation: validation(true, 'automatic', 0.94),
    created_at: iso(1445),
    updated_at: iso(1443),
    execution_result: { success: true, output: 'grafana restarted; datasource healthy', duration_ms: 4200 },
  },
]

const ACTION_STATS = {
  total: 9,
  by_status: { awaiting_approval: 2, completed: 5, rejected: 1, executing: 1 },
  success_rate: 0.86,
}

const PENDING_APPROVALS = {
  count: 2,
  actions: ACTIONS.filter((a) => a.status === 'awaiting_approval'),
  oldest_pending: iso(46),
  urgency_breakdown: { high: 1, medium: 1 },
}

// ---------------------------------------------------------------------------
// Tools (MCP registry)
// ---------------------------------------------------------------------------

const TOOLS = {
  total: 6,
  tools: [
    { name: 'query_telemetry', description: 'Fetch recent logs/metrics/errors for a service', category: 'query', parameters: {}, requires_approval: false, risk_level: 'low' },
    { name: 'find_similar_incidents', description: 'Search episodic memory for similar past incidents', category: 'query', parameters: {}, requires_approval: false, risk_level: 'low' },
    { name: 'get_dependencies', description: 'Resolve upstream/downstream dependencies of a service', category: 'query', parameters: {}, requires_approval: false, risk_level: 'low' },
    { name: 'analyze_logs', description: 'Summarize error/warning patterns in a log window', category: 'analysis', parameters: {}, requires_approval: false, risk_level: 'low' },
    { name: 'restart_service', description: 'Restart a container/service (gated)', category: 'action', parameters: {}, requires_approval: true, risk_level: 'medium' },
    { name: 'scale_service', description: 'Change replica count for a service (gated)', category: 'action', parameters: {}, requires_approval: true, risk_level: 'medium' },
  ],
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

const SETTINGS = {
  constitutional: {
    autoThreshold: 0.9,
    approvalThreshold: 0.7,
    maxActionsPerMinute: 10,
    enableAuditLog: true,
    enableLearning: true,
    strictTier1: true,
  },
  notifications: {
    emailEnabled: false,
    slackEnabled: false,
    webhookEnabled: false,
    webhookUrl: '',
    notifyOnCritical: true,
    notifyOnApproval: true,
    notifyOnResolution: false,
  },
  telemetry: {
    lokiEnabled: true,
    lokiUrl: 'http://loki:3100',
    prometheusEnabled: true,
    prometheusUrl: 'http://prometheus:9090',
    tempoEnabled: false,
    tempoUrl: 'http://tempo:3200',
    retentionDays: 30,
  },
  remediation: {
    mode: 'approve',
    autoConfidenceThreshold: 90,
    requireEvidenceForAuto: true,
    autoToolAllowlist: [],
    demoTargetUrl: 'https://demo.example.com',
  },
}

const SERVING_MODE = {
  mode: 1,
  single_engine: false,
  requested_mode: null,
  swap_status: 'idle',
  detail: null,
  requested_at: null,
  updated_at: iso(120),
}

// GET/PUT /settings/models — the bring-your-own LLM endpoint config the Models
// tab renders. Key is never present (write-only); the demo runs unauthenticated.
const MODELS_CONFIG = {
  fastAgentUrl: 'http://localhost:8000/v1',
  fastAgentModel: 'qwen3-4b',
  reasoningAgentUrl: 'http://localhost:8001/v1',
  reasoningAgentModel: 'qwen3-14b',
  fastApiKeySet: false,
  reasoningApiKeySet: false,
}

// ---------------------------------------------------------------------------
// Demo / chaos orchestration (shown on the Console/Infrastructure surfaces)
// ---------------------------------------------------------------------------

const DEMO_SCENARIOS = {
  scenarios: [
    { id: 'db_outage', label: 'Database outage', description: 'Take the Nextcloud database down' },
    { id: 'disk_pressure', label: 'Disk pressure', description: 'Fill /var/lib/docker to trigger OOM' },
    { id: 'cpu_spike', label: 'CPU spike', description: 'Saturate CPU on the edge host' },
  ],
}

const DEMO_STATUS = {
  target_url: 'https://demo.example.com',
  reachable: true,
  scenarios: { db_outage: { active: false }, disk_pressure: { active: true }, cpu_spike: { active: false } },
  containers: { 'nextcloud-db': { running: true }, 'nextcloud-app': { running: true } },
}

// ---------------------------------------------------------------------------
// Infrastructure
// ---------------------------------------------------------------------------

const CONTAINERS = {
  total: 8,
  healthy: 6,
  unhealthy: 1,
  containers: [
    { name: 'backend', image: 'aiops/backend', health: 'unhealthy', status: 'running', monitored: true, uptime: '26h' },
    { name: 'neo4j', image: 'neo4j:5', health: 'healthy', status: 'running', monitored: true, uptime: '26h' },
    { name: 'caddy', image: 'caddy:2', health: 'healthy', status: 'running', monitored: true, uptime: '26h' },
    { name: 'frontend', image: 'aiops/frontend', health: 'healthy', status: 'running', monitored: true, uptime: '26h' },
    { name: 'loki', image: 'grafana/loki:2.9', health: 'healthy', status: 'running', monitored: true, uptime: '26h' },
    { name: 'prometheus', image: 'prom/prometheus:2.48', health: 'healthy', status: 'running', monitored: true, uptime: '26h' },
    { name: 'grafana', image: 'grafana/grafana:10.2', health: 'healthy', status: 'running', monitored: true, uptime: '26h' },
    { name: 'tempo', image: 'grafana/tempo:2.3', health: 'unknown', status: 'running', monitored: false, uptime: '26h' },
  ],
}

const REMOTE_HOSTS = {
  hosts: [
    { edge_label: 'nextcloud-host', health: 'critical', last_seen: iso(6), episode_count: 8, incident_count: 3 },
  ],
}

// ---------------------------------------------------------------------------
// Agent activity
// ---------------------------------------------------------------------------

// Each activity matches the page's AgentActivity shape: input/output are
// strings (output is JSON so the row's expand view + summary render), plus
// model and a 'success'|'error' status.
const FAST_ACTIVITY = {
  activities: [
    {
      id: 'fa-1', timestamp: iso(2), type: 'annotation', model: 'qwen3-4b', latency_ms: 68, status: 'success',
      input: 'Annotate 34 log lines from nextcloud-host around the OOM event',
      output: JSON.stringify({ summary: 'Annotated 34 log lines for nextcloud-host', severity: 'critical', component: 'runtime', tags: ['oom', 'edge'] }),
    },
    {
      id: 'fa-2', timestamp: iso(5), type: 'classification', model: 'qwen3-4b', latency_ms: 71, status: 'success',
      input: 'Classify: nextcloud-db connection refused (ECONNREFUSED)',
      output: JSON.stringify({ summary: 'Classified severity: critical (DB refused)', severity: 'critical', component: 'database' }),
    },
    {
      id: 'fa-3', timestamp: iso(9), type: 'annotation', model: 'qwen3-4b', latency_ms: 80, status: 'success',
      input: 'Annotate Prometheus disk-usage series for /var/lib/docker',
      output: JSON.stringify({ summary: 'Annotated disk-usage series; threshold crossed at 92%', severity: 'warning', component: 'disk' }),
    },
  ],
}

const REASONING_ACTIVITY = {
  activities: [
    {
      id: 'ra-1', timestamp: iso(4), type: 'rca', model: 'qwen3-14b', latency_ms: 910, status: 'success',
      input: 'Perform root-cause analysis for inc-2043 (Nextcloud DB connection refused)',
      output: JSON.stringify({ summary: 'Root-cause analysis for inc-2043 (confidence 0.91)', root_cause: 'Disk pressure -> php-fpm OOM -> dropped DB connection', confidence: 0.91 }),
    },
    {
      id: 'ra-2', timestamp: iso(7), type: 'planning', model: 'qwen3-14b', latency_ms: 840, status: 'success',
      input: 'Draft a remediation plan for inc-2043',
      output: JSON.stringify({ summary: 'Drafted 3-step remediation plan, queued for approval', steps: 3, requires_approval: true }),
    },
    {
      id: 'ra-3', timestamp: iso(38), type: 'chat', model: 'qwen3-14b', latency_ms: 760, status: 'success',
      input: 'Operator asked about the current backlog',
      output: JSON.stringify({ summary: 'Answered operator question about the backlog', related_incidents: ['inc-2043', 'inc-2039'] }),
    },
  ],
}

// ---------------------------------------------------------------------------
// Telemetry
// ---------------------------------------------------------------------------

const TELEMETRY_LOGS = {
  logs: [
    { timestamp: iso(6), level: 'error', service: 'backend', message: 'nextcloud-db: connection refused (ECONNREFUSED)' },
    { timestamp: iso(6), level: 'error', service: 'nextcloud-host', message: 'php-fpm: worker 12 killed by OOM' },
    { timestamp: iso(7), level: 'warn', service: 'nextcloud-host', message: 'disk usage on /var/lib/docker at 93%' },
    { timestamp: iso(12), level: 'warn', service: 'backend', message: 'reasoning queue depth 18 (backlog)' },
    { timestamp: iso(20), level: 'info', service: 'caddy', message: 'GET /api/v1/incidents 200 8ms' },
    { timestamp: iso(31), level: 'error', service: 'neo4j', message: 'connection pool exhausted (max 40)' },
  ],
}

const TELEMETRY_METRICS = {
  metrics: [
    { name: 'backend_5xx_rate', value: 4.7, unit: '/min' },
    { name: 'reasoning_queue_depth', value: 18, unit: 'jobs' },
    { name: 'nextcloud_host_disk_pct', value: 93, unit: '%' },
    { name: 'neo4j_pool_in_use', value: 40, unit: 'conns' },
  ],
}

// ---------------------------------------------------------------------------
// Episodic knowledge graph (GET /graph/episodes -> the default Graph view).
// Node ids must carry the prefixes the Graph transform expects: episode-*,
// rootcause-*, action-*, entity-*, and service-<name>. Edges reference those
// final ids so the causal chain renders connected, not as floating dots.
// ---------------------------------------------------------------------------

const EPISODES_GRAPH = {
  episodes: [
    { id: '2043', title: 'Nextcloud DB connection refused', timestamp: iso(42), category: 'availability', severity: 'critical', status: 'pending_approval', root_cause: 'Disk pressure → php-fpm OOM', confidence: 0.91 },
    { id: '2041', title: 'Backend API 5xx after deploy', timestamp: iso(190), category: 'errors', severity: 'high', status: 'remediating', root_cause: 'Deploy regression', confidence: 0.78 },
    { id: '2039', title: 'Neo4j connection pool exhausted', timestamp: iso(340), category: 'saturation', severity: 'high', status: 'pending_approval', confidence: 0.7 },
    { id: '2036', title: 'Reasoning agent p95 elevated', timestamp: iso(520), category: 'latency', severity: 'medium', status: 'analyzing', confidence: 0.66 },
    { id: '2030', title: 'Grafana datasource query timeout', timestamp: iso(1500), category: 'observability', severity: 'medium', status: 'resolved', confidence: 0.82 },
    { id: '2021', title: 'Loki ingester flush backlog', timestamp: iso(2900), category: 'observability', severity: 'low', status: 'resolved', confidence: 0.88 },
  ],
  root_causes: [
    { id: 'rootcause-disk-pressure', name: 'Disk pressure → OOM', frequency: 3, avg_resolution_time_minutes: 5, success_rate: 0.8 },
    { id: 'rootcause-neo4j-pool', name: 'Neo4j pool exhaustion', frequency: 2, avg_resolution_time_minutes: 4, success_rate: 0.9 },
    { id: 'rootcause-deploy-regression', name: 'Deploy regression', frequency: 1, avg_resolution_time_minutes: 8, success_rate: 1 },
  ],
  actions: [
    { id: 'action-restart', name: 'restart_service', used_count: 12, success_rate: 0.92, avg_execution_time_seconds: 4 },
    { id: 'action-scale', name: 'scale_service', used_count: 5, success_rate: 0.8, avg_execution_time_seconds: 9 },
  ],
  services: [
    { name: 'nextcloud-host', status: 'critical', incident_count: 3, last_incident: iso(6) },
    { name: 'backend', status: 'warning', incident_count: 2, last_incident: iso(12) },
    { name: 'neo4j', status: 'healthy', incident_count: 1, last_incident: iso(48) },
    { name: 'qwen3-14b', status: 'warning', incident_count: 1, last_incident: iso(90) },
    { name: 'grafana', status: 'healthy', incident_count: 0 },
    { name: 'loki', status: 'healthy', incident_count: 0 },
  ],
  entities: [
    { id: 'entity-qwen3-14b', name: 'Qwen3-14B', relation_count: 4 },
    { id: 'entity-var-lib-docker', name: '/var/lib/docker', relation_count: 2 },
  ],
  edges: [
    { source: 'episode-2043', target: 'rootcause-disk-pressure', relationship: 'CAUSED_BY', weight: 0.91 },
    { source: 'episode-2043', target: 'service-nextcloud-host', relationship: 'AFFECTS', weight: 1 },
    { source: 'rootcause-disk-pressure', target: 'action-restart', relationship: 'RESOLVED_BY', weight: 0.8 },
    { source: 'rootcause-disk-pressure', target: 'entity-var-lib-docker', relationship: 'MENTIONS', weight: 0.7 },
    { source: 'episode-2041', target: 'rootcause-deploy-regression', relationship: 'CAUSED_BY', weight: 0.78 },
    { source: 'episode-2041', target: 'service-backend', relationship: 'AFFECTS', weight: 1 },
    { source: 'episode-2039', target: 'rootcause-neo4j-pool', relationship: 'CAUSED_BY', weight: 0.7 },
    { source: 'episode-2039', target: 'service-neo4j', relationship: 'AFFECTS', weight: 1 },
    { source: 'rootcause-neo4j-pool', target: 'action-scale', relationship: 'RESOLVED_BY', weight: 0.9 },
    { source: 'episode-2036', target: 'service-qwen3-14b', relationship: 'AFFECTS', weight: 1 },
    { source: 'episode-2036', target: 'entity-qwen3-14b', relationship: 'MENTIONS', weight: 0.6 },
    { source: 'episode-2030', target: 'service-grafana', relationship: 'AFFECTS', weight: 1 },
    { source: 'episode-2021', target: 'service-loki', relationship: 'AFFECTS', weight: 1 },
    { source: 'episode-2043', target: 'episode-2041', relationship: 'SIMILAR_TO', weight: 0.72 },
    { source: 'episode-2039', target: 'episode-2043', relationship: 'SIMILAR_TO', weight: 0.68 },
  ],
  stats: {
    total_episodes: 6,
    total_root_causes: 3,
    total_actions: 2,
    total_services: 6,
    total_entities: 2,
    total_edges: 15,
    critical_episodes: 1,
    resolved_episodes: 2,
    dynamic_edges: 15,
  },
}

// ---------------------------------------------------------------------------
// Chat (canned reply + SSE frames)
// ---------------------------------------------------------------------------

const CHAT_CONVERSATIONS = { items: [], total: 0, limit: 20, offset: 0 }

interface ChatToolCall {
  id: string
  name: string
  arguments: Record<string, unknown>
  status: string
  duration_ms: number
  result: Record<string, unknown>
}

interface ChatAnswer {
  text: string
  confidence: number
  tokens_used: number
  suggested_actions: string[]
  related_incidents: string[]
  tool_calls: ChatToolCall[]
}

const TOOL_TELEMETRY: ChatToolCall = {
  id: 't1', name: 'query_telemetry', arguments: { service: 'nextcloud-host' }, status: 'ok', duration_ms: 60,
  result: { service: 'nextcloud-host', log_count: 214, error_count: 12 },
}
const TOOL_SIMILAR: ChatToolCall = {
  id: 't2', name: 'find_similar_incidents', arguments: { query: 'db connection refused' }, status: 'ok', duration_ms: 40,
  result: { count: 2, incidents: [{ id: 'inc-1007', summary: 'Prior DB outage', score: 0.88 }] },
}
const TOOL_DEPS: ChatToolCall = {
  id: 't3', name: 'get_dependencies', arguments: { service: 'backend' }, status: 'ok', duration_ms: 35,
  result: { upstream: ['nextcloud-host', 'neo4j'], downstream: ['frontend'] },
}

/**
 * The demo answers from a fixed incident snapshot, but chooses its reply from
 * the question so the chat feels live. Keyword-routed, most specific first;
 * deterministic (no randomness) so the streamed deltas match the authoritative
 * `done` frame exactly.
 */
function answerFor(message: string): ChatAnswer {
  const q = message.trim().toLowerCase()
  const has = (...k: string[]): boolean => k.some((w) => q.includes(w))

  if (has('root cause', 'rca', 'why', 'cause')) {
    return {
      text:
        'Root cause of **inc-2043** (confidence 0.91): disk pressure on `/var/lib/docker` on `nextcloud-host` crossed 92%, ' +
        "which OOM-killed the php-fpm workers. That dropped Nextcloud's database connection pool, and the backend API then " +
        'returned 5xx upstream. Loki shows the OOM kill about 40s before the first DB-refused log, and the Prometheus ' +
        'disk-usage series crosses the threshold in the same window. The pattern matches 2 prior incidents on this host.',
      confidence: 0.91, tokens_used: 812,
      suggested_actions: ['View the full RCA for inc-2043', 'Open the causal chain in the Graph'],
      related_incidents: ['inc-2043', 'inc-1007'],
      tool_calls: [TOOL_TELEMETRY, TOOL_SIMILAR],
    }
  }
  if (has('remediat', 'fix', 'resolve', 'mitigat', 'how do i', 'what should')) {
    return {
      text:
        'The queued 3-step remediation plan for **inc-2043** is:\n\n' +
        '1. Prune dangling Docker images/volumes on `nextcloud-host` (`docker system prune -af --volumes`) — medium risk, needs approval.\n' +
        '2. Restart `php-fpm` and the `nextcloud-db` container — medium risk, needs approval.\n' +
        '3. Verify `/chat` and `/incidents` return 200 through Caddy — low risk, automatic.\n\n' +
        'Steps 1 and 2 sit above the 0.90 auto-execution band, so they wait for your approval on the Incidents page.',
      confidence: 0.86, tokens_used: 690,
      suggested_actions: ['Approve the restart of nextcloud-db', 'Open the remediation plan for inc-2043'],
      related_incidents: ['inc-2043'],
      tool_calls: [TOOL_TELEMETRY],
    }
  }
  if (has('similar', 'past', 'before', 'memory', 'graph', 'episod', 'history')) {
    return {
      text:
        'The episodic memory has 2 close matches to the active incident. `inc-1007` (score 0.88) was a prior DB outage on ' +
        'the same edge host, resolved by a `restart_service` in about 5 min. `inc-2039` (Neo4j pool exhaustion) is linked ' +
        'SIMILAR_TO because both trace back to saturation. The Graph page shows the full causal chain: episode -> root ' +
        'cause -> resolving action.',
      confidence: 0.84, tokens_used: 604,
      suggested_actions: ['Open the Graph explorer', 'Compare with inc-1007'],
      related_incidents: ['inc-2043', 'inc-2039', 'inc-1007'],
      tool_calls: [TOOL_SIMILAR],
    }
  }
  if (has('latency', 'agent', 'model', 'fast', 'reasoning', 'slow', 'performance', 'p95')) {
    return {
      text:
        'Both agents are online. The **fast agent** (Qwen3-4B) is averaging 74ms (p95 121ms) across 1,284 requests — it ' +
        'handles annotation and severity classification. The **reasoning agent** (Qwen3-14B) is averaging 830ms (p95 ' +
        '1,920ms) across 342 requests — it owns RCA, remediation planning, and this chat. The Metrics page has the full ' +
        'latency breakdown.',
      confidence: 0.88, tokens_used: 520,
      suggested_actions: ['Open the Metrics page', 'Run a latency benchmark'],
      related_incidents: ['inc-2036'],
      tool_calls: [],
    }
  }
  if (has('benchmark', 'accuracy', 'eval', 'score')) {
    return {
      text:
        'On the demo corpus (168 scored cases) Constitutional AIOps reaches 84.2% annotation accuracy and 82.4% RCA ' +
        'accuracy (BERT-F1 0.861) — about +10.8pp RCA over the Llama-3.3-70B baseline and +15.1pp over DeepSeek-V3.2, at a ' +
        'fraction of the latency. Full per-model numbers and JSON/CSV/LaTeX export live on the Benchmark page.',
      confidence: 0.9, tokens_used: 560,
      suggested_actions: ['Open the Benchmark page', 'Compare models'],
      related_incidents: [],
      tool_calls: [],
    }
  }
  if (has('constitution', 'approval', 'approve', 'gate', 'safe', 'autonom', 'risk', 'principle')) {
    return {
      text:
        'Every proposed action passes a 3-tier constitutional gate before it can run. Confidence above 0.90 auto-executes ' +
        '(audit only); 0.70-0.90 needs human approval; below 0.70 is alert-only. Tier-1 safety principles (no unconfirmed ' +
        'data deletion, keep at least 2 healthy replicas, reversible within 60s) can never be violated. That is why the two ' +
        'open restart/scale actions are waiting on your approval rather than firing on their own.',
      confidence: 0.92, tokens_used: 640,
      suggested_actions: ['Review pending approvals', 'Open Settings -> Remediation'],
      related_incidents: ['inc-2043', 'inc-2039'],
      tool_calls: [TOOL_DEPS],
    }
  }
  if (q === 'hi' || q === 'hello' || has('hello', 'hey', 'help', 'what can you', 'who are you')) {
    return {
      text:
        'Hi — this is the Constitutional AIOps operator chat, running in a read-only demo. I can walk you through the active ' +
        'incidents, explain a root cause, show the queued remediation plan, or point you at the Graph, Metrics, and ' +
        'Benchmark pages. Right now 1 critical incident is open (**inc-2043**). What would you like to look at?',
      confidence: 0.9, tokens_used: 300,
      suggested_actions: ['Summarize the current incidents', 'What is the root cause of inc-2043?'],
      related_incidents: ['inc-2043'],
      tool_calls: [],
    }
  }
  // Default: incident overview, and echo the question so it reads as a real reply.
  const echo = message.trim() ? `You asked: "${message.trim()}". ` : ''
  return {
    text:
      echo +
      'From the current snapshot there are 4 active incidents, 1 of them critical: **inc-2043** — Nextcloud database ' +
      'connection refused on `nextcloud-host`, root-caused (0.91) to disk pressure -> php-fpm OOM -> dropped DB connection. ' +
      'A 3-step remediation plan is queued for approval and 2 actions are waiting on the constitutional gate. Ask me about ' +
      'the root cause, the fix, similar past incidents, the agents, or the benchmark.',
    confidence: 0.87, tokens_used: 480,
    suggested_actions: ['What is the root cause of inc-2043?', 'How do I fix it?'],
    related_incidents: ['inc-2043', 'inc-2039'],
    tool_calls: [TOOL_TELEMETRY, TOOL_SIMILAR],
  }
}

function chatResponse(conversationId: string, message = '') {
  const a = answerFor(message)
  return {
    conversation_id: conversationId || 'demo-conv-1',
    message: { role: 'assistant', content: a.text, timestamp: new Date().toISOString() },
    confidence: a.confidence,
    suggested_actions: a.suggested_actions,
    related_incidents: a.related_incidents,
    metadata: {
      mode: 'demo',
      model_used: 'qwen3-14b (fixture)',
      tokens_used: a.tokens_used,
      tool_calls: a.tool_calls,
    },
    proposed_action: null,
  }
}

/** Break the chosen answer into word-chunks so the stream animates like the real thing. */
function chatSseFrames(conversationId: string, message = ''): Array<{ event: string; data: unknown }> {
  const cid = conversationId || 'demo-conv-1'
  const a = answerFor(message)
  const frames: Array<{ event: string; data: unknown }> = [
    { event: 'meta', data: { conversation_id: cid, streaming: true, mode: 2 } },
  ]
  if (a.tool_calls.length > 0) {
    const t = a.tool_calls[0]
    frames.push({ event: 'tool_result', data: { name: t.name, ...t.result } })
  }
  const words = a.text.split(' ')
  for (let i = 0; i < words.length; i += 4) {
    frames.push({ event: 'delta', data: { text: words.slice(i, i + 4).join(' ') + ' ' } })
  }
  frames.push({ event: 'done', data: chatResponse(cid, message) })
  return frames
}

// ---------------------------------------------------------------------------
// Benchmark page (datasets / models / results / compare)
// ---------------------------------------------------------------------------

const BENCH_DATASETS = [
  {
    name: 'annotation',
    file: 'annotation_demo.jsonl',
    total_cases: 120,
    source: 'synthetic (logs / metrics / traces)',
    description: 'Labelled telemetry lines scored for annotation accuracy: severity, component, and category tags.',
    distribution: { logs: 70, metrics: 32, traces: 18 },
  },
  {
    name: 'rca',
    file: 'rca_demo.jsonl',
    total_cases: 48,
    source: 'synthetic incident bundles',
    description: 'Incidents with a known root cause for end-to-end RCA scoring against the reasoning agent.',
    categories: { availability: 16, saturation: 12, latency: 11, errors: 9 },
  },
]

const BENCH_MODELS = {
  constitutional_aiops: { description: 'Constitutional AIOps (Qwen3-4B + 14B dual)', type: 'dual-agent', vram_gb: 24 },
  qwen3_14b_base: { description: 'Qwen3-14B (base, single agent)', type: 'single', vram_gb: 15 },
  llama3_3_70b: { description: 'Llama-3.3-70B (baseline)', type: 'baseline', vram_gb: 40 },
  deepseek_v3_2: { description: 'DeepSeek-V3.2 (baseline)', type: 'baseline', vram_gb: 48 },
}

const BENCH_RESULTS = [
  { model_name: 'constitutional_aiops', annotation_accuracy: 84.2, rca_accuracy: 82.4, bert_f1: 0.861, avg_latency_ms: 118, p95_latency_ms: 210, total_tests: 168, passed_tests: 141, status: 'completed' },
  { model_name: 'qwen3_14b_base', annotation_accuracy: 78.5, rca_accuracy: 71.6, bert_f1: 0.802, avg_latency_ms: 96, p95_latency_ms: 180, total_tests: 168, passed_tests: 129, status: 'completed' },
  { model_name: 'llama3_3_70b', annotation_accuracy: 80.1, rca_accuracy: 71.6, bert_f1: 0.821, avg_latency_ms: 540, p95_latency_ms: 980, total_tests: 168, passed_tests: 131, status: 'completed' },
  { model_name: 'deepseek_v3_2', annotation_accuracy: 79.2, rca_accuracy: 67.3, bert_f1: 0.808, avg_latency_ms: 610, p95_latency_ms: 1120, total_tests: 168, passed_tests: 127, status: 'completed' },
]

/** A small LaTeX table so the Benchmark "Export -> LaTeX" download has content. */
function benchLatex(): string {
  const rows = BENCH_RESULTS.map(
    (r) => `${r.model_name} & ${r.annotation_accuracy} & ${r.rca_accuracy} & ${r.bert_f1} & ${r.avg_latency_ms} \\\\`,
  ).join('\n')
  return `\\begin{tabular}{lrrrr}\nModel & Ann. Acc & RCA Acc & BERT F1 & Latency (ms) \\\\\n\\hline\n${rows}\n\\end{tabular}`
}

// ---------------------------------------------------------------------------
// Route table
// ---------------------------------------------------------------------------

const ok = (json: unknown): DemoResult => ({ status: 200, json })

/** conversation id out of a JSON request body, if present. */
function bodyConversationId(bodyText?: string): string {
  if (!bodyText) return ''
  try {
    const parsed = JSON.parse(bodyText) as { conversation_id?: string }
    return parsed.conversation_id ?? ''
  } catch {
    return ''
  }
}

/** user message out of a JSON chat request body, if present. */
function bodyMessage(bodyText?: string): string {
  if (!bodyText) return ''
  try {
    const parsed = JSON.parse(bodyText) as { message?: string }
    return parsed.message ?? ''
  } catch {
    return ''
  }
}

// ---------------------------------------------------------------------------
// Audit log (admin viewer) — a short trail matching the nextcloud-host story.
// ---------------------------------------------------------------------------
const AUDIT_EVENTS = [
  {
    event_id: 'demo-aud-5', event_type: 'action.executed', timestamp: iso(3), severity: 'info',
    actor_type: 'system', actor_id: 'executor', resource_type: 'action', resource_id: 'act-1042',
    description: 'Action execution completed', outcome: 'success',
  },
  {
    event_id: 'demo-aud-4', event_type: 'action.approved', timestamp: iso(4), severity: 'info',
    actor_type: 'user', actor_id: 'admin', resource_type: 'action', resource_id: 'act-1042',
    description: 'Action approved by admin', outcome: 'success',
  },
  {
    event_id: 'demo-aud-3', event_type: 'constitutional.validation', timestamp: iso(4), severity: 'info',
    actor_type: 'agent', actor_id: 'constitutional-ai', resource_type: 'action', resource_id: 'act-1042',
    description: 'Constitutional validation: passed', outcome: 'success',
  },
  {
    event_id: 'demo-aud-2', event_type: 'action.created', timestamp: iso(5), severity: 'info',
    actor_type: 'system', actor_id: 'reasoning-agent', resource_type: 'action', resource_id: 'act-1042',
    description: 'Action created: restart_service on nextcloud-db', outcome: 'success',
  },
  {
    event_id: 'demo-aud-1', event_type: 'incident.analyzed', timestamp: iso(6), severity: 'warning',
    actor_type: 'agent', actor_id: 'reasoning-agent', resource_type: 'incident', resource_id: 'INC-2043',
    description: 'Root-cause analysis completed for nextcloud-host disk pressure', outcome: 'success',
  },
]

const AUDIT_EVENT_TYPES = [
  'incident.created', 'incident.analyzed', 'action.created', 'action.validated',
  'action.approved', 'action.rejected', 'action.executed', 'action.failed',
  'constitutional.validation', 'constitutional.violation', 'tool.invoked',
]

// ---------------------------------------------------------------------------
// Notification inbox (admin alert center) — matches the nextcloud-host story.
// ---------------------------------------------------------------------------
const NOTIFICATIONS = [
  {
    id: 'demo-note-3', timestamp: iso(4), type: 'action.approval', severity: 'warning',
    title: 'Action awaiting approval',
    message: 'restart_service on nextcloud-db needs a human decision (confidence 82%).',
    source: 'actions', resource_id: 'act-1042', read: false,
  },
  {
    id: 'demo-note-2', timestamp: iso(9), type: 'action.alert', severity: 'info',
    title: 'Low-confidence action flagged',
    message: 'scale_up on nextcloud-host was alert-only (confidence 61%); no action taken.',
    source: 'constitutional-ai', resource_id: 'act-1039', read: false,
  },
  {
    id: 'demo-note-1', timestamp: iso(48), type: 'webhook.test', severity: 'info',
    title: 'Test webhook delivered',
    message: 'A test notification was accepted by hooks.example.com (HTTP 200).',
    source: 'settings', resource_id: null, read: true,
  },
]

/** POST /benchmark/evaluate-endpoint — a canned "your setup" quick-check. */
const ENDPOINT_EVAL = {
  ok: true,
  model: 'constitutional_aiops',
  cases_run: 5,
  passed: 4,
  pass_rate: 80.0,
  annotation: { run: 3, passed: 3 },
  rca: { run: 2, passed: 1 },
  avg_latency_ms: 742.0,
  cases: [
    { test_id: 'ann_0', task_type: 'annotation', correct: true, latency_ms: 71, source: 'HDFS' },
    { test_id: 'ann_1', task_type: 'annotation', correct: true, latency_ms: 66, source: 'BGL' },
    { test_id: 'ann_2', task_type: 'annotation', correct: true, latency_ms: 74, source: 'HDFS' },
    { test_id: 'rca_0', task_type: 'rca', correct: true, latency_ms: 1840, source: 'LEMMA-RCA' },
    { test_id: 'rca_1', task_type: 'rca', correct: false, latency_ms: 1620, source: 'OpsEval' },
  ],
  detail: 'demo: 5 sample cases against the demo endpoint.',
}

/**
 * Resolve a demo response for an /api/v1 request. `route` is the path with the
 * `/api/v1` prefix already stripped and no query string. Unknown routes get a
 * benign empty 200 so no page throws.
 */
export function matchRoute(method: string, route: string, bodyText?: string): DemoResult {
  const m = method.toUpperCase()

  // Health
  if (route === '/health' || route === '/health/') return ok(HEALTH)
  if (route === '/health/ready') return ok({ ready: true })
  if (route === '/health/live') return ok({ alive: true })

  // Auth: no enforcement in the demo -> Dashboard renders with no login.
  if (route === '/auth/config') {
    return ok({ auth_required: false, signup_enabled: false, captcha_provider: '', captcha_site_key: '' })
  }
  if (route === '/auth/me') return { status: 401, json: { detail: 'demo: no session' } }
  if (route.startsWith('/auth/')) return ok({ ok: true })

  // Metrics (Dashboard model cards + Metrics page)
  if (route === '/metrics' || route === '/metrics/') return ok(AGENT_METRICS)
  if (route === '/metrics/history') return ok(METRICS_HISTORY)
  if (route === '/metrics/validation/report') return ok(VALIDATION_REPORT)
  if (route === '/metrics/benchmark') return ok(metricsBenchmark(bodyText))
  if (route === '/metrics/validate/determinism') return ok(DETERMINISM_RESULT)
  if (route === '/metrics/export') return ok(AGENT_METRICS)
  if (route.startsWith('/metrics/')) return ok({}) // clear, misc

  // Incidents
  if (route === '/incidents/stats') return ok(INCIDENT_STATS)
  if (route === '/incidents/' || route === '/incidents') {
    if (m === 'POST') return ok(INCIDENTS[0])
    return ok({ items: INCIDENTS, total: INCIDENTS.length, page: 1, page_size: 20, has_more: false })
  }
  const incSimilar = route.match(/^\/incidents\/([^/]+)\/similar$/)
  if (incSimilar) return ok({ similar: INCIDENTS.filter((i) => i.id !== incSimilar[1]).slice(0, 2) })
  const incRemediate = route.match(/^\/incidents\/([^/]+)\/remediate$/)
  if (incRemediate) {
    const inc = INCIDENTS.find((i) => i.id === incRemediate[1]) ?? INCIDENTS[0]
    return ok({ incident_id: incRemediate[1], status: 'resolved', success: true, method: 'demo_heal', detail: 'demo: healed', incident: { ...inc, status: 'resolved' } })
  }
  const incId = route.match(/^\/incidents\/([^/]+)$/)
  if (incId) return ok(INCIDENTS.find((i) => i.id === incId[1]) ?? INCIDENTS[0])

  // Actions
  if (route === '/actions/stats') return ok(ACTION_STATS)
  if (route === '/actions/pending') return ok(PENDING_APPROVALS)
  if (route === '/actions/' || route === '/actions') {
    return ok({ items: ACTIONS, total: ACTIONS.length, page: 1, page_size: 20, has_more: false })
  }
  const actId = route.match(/^\/actions\/([^/]+)$/)
  if (actId) return ok(ACTIONS.find((a) => a.id === actId[1]) ?? ACTIONS[0])
  if (route.startsWith('/actions/')) return ok({ ok: true }) // approve/execute/cancel

  // Tools (MCP)
  if (route === '/tools' || route === '/tools/') return ok(TOOLS)
  if (route === '/tools/call') return ok({ success: true, data: { note: 'demo: read-only, no tool executed' }, execution_time_ms: 12 })
  const toolName = route.match(/^\/tools\/([^/]+)$/)
  if (toolName) return ok(TOOLS.tools.find((t) => t.name === toolName[1]) ?? TOOLS.tools[0])

  // Graph
  if (route === '/graph/topology') return ok(topology)
  if (route === '/graph/episodes') return ok(EPISODES_GRAPH)

  // Topology schema editor
  if (route.startsWith('/topology/schema')) return ok({ nodes: [], edges: [] })

  // Settings
  if (route === '/settings/' || route === '/settings') {
    if (m === 'PUT') return ok(SETTINGS)
    return ok(SETTINGS)
  }
  if (route === '/settings/serving-mode') return ok(SERVING_MODE)
  if (route === '/settings/models') return ok(MODELS_CONFIG)
  if (route === '/settings/models/test') return ok({ fast_agent: true, reasoning_agent: true })
  if (route === '/settings/notifications/test-webhook') return ok({ ok: true, detail: 'demo: webhook not actually sent' })
  if (route === '/settings/reset') return ok(SETTINGS)
  if (route.startsWith('/prompts')) return ok({ prompts: [] })

  // Demo / chaos
  if (route === '/demo/scenarios') return ok(DEMO_SCENARIOS)
  if (route === '/demo/status') return ok(DEMO_STATUS)
  if (route.startsWith('/demo/chaos/')) {
    const parts = route.split('/')
    return ok({ scenario: parts[3] ?? 'db_outage', action: parts[4] ?? 'start', success: true, detail: 'demo: acknowledged' })
  }
  if (route === '/demo/target') return ok({ target_url: DEMO_STATUS.target_url })

  // Infrastructure
  if (route === '/infrastructure/containers') return ok(CONTAINERS)
  if (route === '/infrastructure/remote-hosts') return ok(REMOTE_HOSTS)
  if (route.startsWith('/infrastructure/')) return ok({ ok: true })

  // Agents
  if (route === '/agents/fast/activity') return ok(FAST_ACTIVITY)
  if (route === '/agents/reasoning/activity') return ok(REASONING_ACTIVITY)

  // Telemetry
  if (route === '/telemetry/logs') return ok(TELEMETRY_LOGS)
  if (route === '/telemetry/metrics') return ok(TELEMETRY_METRICS)

  // Chat
  if (route === '/chat/stream') return { status: 200, sse: chatSseFrames(bodyConversationId(bodyText), bodyMessage(bodyText)) }
  if (route === '/chat/' || route === '/chat') return ok(chatResponse(bodyConversationId(bodyText), bodyMessage(bodyText)))
  if (route === '/chat/conversations') return ok(CHAT_CONVERSATIONS)
  if (route.startsWith('/chat/conversations/')) {
    if (m === 'DELETE') return { status: 204 }
    return ok({ conversation_id: 'demo-conv-1', created_at: iso(60), updated_at: iso(4), messages: [], context: null })
  }
  if (route.startsWith('/chat/actions/')) return ok({ action_id: 'demo', status: 'executed', success: true, error_code: null, verdict: null, result: null })

  // Audit log (admin viewer)
  if (route === '/audit/event-types') return ok({ event_types: AUDIT_EVENT_TYPES })
  if (route === '/audit/' || route === '/audit') {
    return ok({ events: AUDIT_EVENTS, count: AUDIT_EVENTS.length, truncated: false })
  }

  // Notification inbox (admin alert center) — read-only in the demo.
  if (route === '/notifications/unread-count') {
    return ok({ unread: NOTIFICATIONS.filter((n) => !n.read).length })
  }
  if (route === '/notifications/read') {
    return ok({ updated: 0, unread: NOTIFICATIONS.filter((n) => !n.read).length })
  }
  if (route === '/notifications/' || route === '/notifications') {
    if (m === 'DELETE') return ok({ cleared: 0 })
    return ok({
      notifications: NOTIFICATIONS,
      count: NOTIFICATIONS.length,
      unread: NOTIFICATIONS.filter((n) => !n.read).length,
    })
  }

  // Benchmark page
  if (route === '/benchmark/datasets') return ok({ datasets: BENCH_DATASETS })
  if (route === '/benchmark/models') return ok({ models: BENCH_MODELS })
  if (route === '/benchmark/results') return ok({ results: BENCH_RESULTS })
  if (route === '/benchmark/status') return ok({ is_running: false })
  if (route === '/benchmark/run') return ok({ status: 'started', detail: 'demo: benchmark not executed' })
  if (route === '/benchmark/evaluate-endpoint') return ok(ENDPOINT_EVAL)
  if (route === '/benchmark/export') return ok({ results: BENCH_RESULTS, content: benchLatex() })
  if (route.startsWith('/benchmark')) return ok({ datasets: [], models: {}, results: [], status: { is_running: false } })

  // WebSocket token (demo has no live socket; empty token)
  if (route === '/ws/token') return ok({ token: '' })

  // Unknown: benign empty 200.
  return ok({})
}
