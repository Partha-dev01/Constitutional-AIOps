/**
 * Graph topology UPDATE - Playwright E2E spec
 *
 * The existing graph.spec.ts serves ONE static payload, so it proves the graph
 * renders and reacts to view controls but never that it re-renders when the
 * underlying topology CHANGES. That update path is what the nextcloud-smoke box
 * exercised by hand: an incident ripples, new services/episodes appear, the
 * operator hits Refresh, and the knowledge graph must reflect the new topology.
 *
 * Graph.tsx drives updates via a react-query key bumped by the Refresh button:
 * each Refresh refetches `/api/v1/graph/episodes` and re-renders the explorer.
 * The page header reports `N nodes · M relationships · E episodes`, computed
 * directly from the fetched payload (not the force sim), so it is the
 * deterministic signal these tests assert on.
 *
 * Runs against `vite preview` (prod build) on localhost:4173. Every backend call
 * is intercepted, so no server or box is needed. `/auth/config` is stubbed
 * auth_required:false because auth.ts fails SAFE (auth required) when it cannot
 * reach the endpoint, which would otherwise bounce /graph to /login.
 */

import { test, expect, Page, Route } from '@playwright/test'

// ---------------------------------------------------------------------------
// Topology payloads: a small nextcloud-flavoured graph that GROWS then SHRINKS
// ---------------------------------------------------------------------------
function meta() {
  return {}
}

// A: baseline - 2 episodes, 1 root cause, 1 action, 2 services => 6 nodes / 3 edges
const PAYLOAD_A = {
  episodes: [
    { id: 'a1', title: 'Disk pressure on nextcloud-host', type: 'episode', timestamp: '2026-09-05T10:00:00Z', category: 'storage', severity: 'high', status: 'resolved', root_cause: 'disk_saturation', confidence: 0.9, services: ['nextcloud-host'], successful_actions: ['restart_service'], metadata: meta() },
    { id: 'a2', title: 'DB connection refused', type: 'episode', timestamp: '2026-09-05T10:05:00Z', category: 'connectivity', severity: 'high', status: 'analyzing', root_cause: 'disk_saturation', confidence: 0.7, services: ['nextcloud-db'], successful_actions: [], metadata: meta() },
  ],
  root_causes: [
    { id: 'rootcause-disk_saturation', name: 'disk_saturation', type: 'root_cause', frequency: 2, avg_resolution_time_minutes: 12, success_rate: 0.8, metadata: meta() },
  ],
  actions: [
    { id: 'action-restart_service', name: 'restart_service', type: 'action', used_count: 5, success_rate: 0.9, avg_execution_time_seconds: 4, metadata: meta() },
  ],
  services: [
    { name: 'nextcloud-host', type: 'service', status: 'warning', incident_count: 1, last_incident: '2026-09-05T10:00:00Z', metadata: meta() },
    { name: 'nextcloud-db', type: 'service', status: 'critical', incident_count: 1, last_incident: '2026-09-05T10:05:00Z', metadata: meta() },
  ],
  entities: [],
  edges: [
    { source: 'episode-a1', target: 'rootcause-disk_saturation', relationship: 'caused_by', weight: 1, metadata: meta() },
    { source: 'episode-a1', target: 'service-nextcloud-host', relationship: 'affects', weight: 1, metadata: meta() },
    { source: 'episode-a2', target: 'service-nextcloud-db', relationship: 'affects', weight: 1, metadata: meta() },
  ],
  stats: { total_episodes: 2, total_root_causes: 1, total_actions: 1, total_services: 2, total_entities: 0, total_edges: 3, critical_episodes: 0, resolved_episodes: 1, dynamic_edges: 0 },
}

// B: the incident ripples - +1 episode, +1 root cause, +1 service, +1 entity
//    => 10 nodes / 6 edges
const PAYLOAD_B = {
  episodes: [
    ...PAYLOAD_A.episodes,
    { id: 'b3', title: 'OOM kill in aiops-backend', type: 'episode', timestamp: '2026-09-05T10:10:00Z', category: 'performance', severity: 'critical', status: 'remediating', root_cause: 'memory_leak', confidence: 0.85, services: ['aiops-backend'], successful_actions: [], metadata: meta() },
  ],
  root_causes: [
    ...PAYLOAD_A.root_causes,
    { id: 'rootcause-memory_leak', name: 'memory_leak', type: 'root_cause', frequency: 1, avg_resolution_time_minutes: 20, success_rate: 0.6, metadata: meta() },
  ],
  actions: [...PAYLOAD_A.actions],
  services: [
    ...PAYLOAD_A.services,
    { name: 'aiops-backend', type: 'service', status: 'critical', incident_count: 1, last_incident: '2026-09-05T10:10:00Z', metadata: meta() },
  ],
  entities: [
    { id: 'entity-oom_killer', name: 'oom_killer', type: 'entity', relation_count: 2, metadata: meta() },
  ],
  edges: [
    ...PAYLOAD_A.edges,
    { source: 'episode-b3', target: 'rootcause-memory_leak', relationship: 'caused_by', weight: 1, metadata: meta() },
    { source: 'episode-b3', target: 'service-aiops-backend', relationship: 'affects', weight: 1, metadata: meta() },
    { source: 'service-aiops-backend', target: 'service-nextcloud-db', relationship: 'depends_on', weight: 1, metadata: meta() },
  ],
  stats: { total_episodes: 3, total_root_causes: 2, total_actions: 1, total_services: 3, total_entities: 1, total_edges: 6, critical_episodes: 1, resolved_episodes: 1, dynamic_edges: 0 },
}

// C: pruned after resolution - 1 episode, 1 root cause, 1 service => 3 nodes / 1 edge
const PAYLOAD_C = {
  episodes: [PAYLOAD_A.episodes[0]],
  root_causes: [PAYLOAD_A.root_causes[0]],
  actions: [],
  services: [PAYLOAD_A.services[0]],
  entities: [],
  edges: [
    { source: 'episode-a1', target: 'service-nextcloud-host', relationship: 'affects', weight: 1, metadata: meta() },
  ],
  stats: { total_episodes: 1, total_root_causes: 1, total_actions: 0, total_services: 1, total_entities: 0, total_edges: 1, critical_episodes: 0, resolved_episodes: 1, dynamic_edges: 0 },
}

// ---------------------------------------------------------------------------
// Test harness
// ---------------------------------------------------------------------------
test.describe.configure({ mode: 'serial' })

test.describe('Graph topology updates', () => {
  // Mutable so a test can swap the topology the API serves mid-run, then Refresh.
  let payload: unknown = PAYLOAD_A

  async function installRoutes(page: Page) {
    // Broad fallback FIRST so the specific handlers added below win (Playwright
    // checks the most-recently-registered matching route first).
    await page.route('**/api/v1/**', async (route: Route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
    })
    await page.route('**/auth/config**', async (route: Route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ auth_required: false, signup_enabled: false, captcha_provider: '', captcha_site_key: '' }) })
    })
    await page.route('**/health**', async (route: Route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ healthy: true, components: [] }) })
    })
    await page.route('**/api/v1/ws/token**', async (route: Route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ token: 'mock-token' }) })
    })
    // The graph data - serves whatever `payload` currently holds.
    await page.route('**/api/v1/graph/episodes**', async (route: Route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(payload) })
    })
  }

  async function gotoGraph(page: Page) {
    await installRoutes(page)
    await page.goto('/graph')
    await page.waitForSelector('canvas', { timeout: 15000 })
  }

  // Reads the deterministic header line "N nodes · M relationships · E episodes".
  async function readHeaderCounts(page: Page): Promise<{ nodes: number; links: number; episodes: number }> {
    const header = page.locator('p', { hasText: 'relationships' }).first()
    await expect(header).toBeVisible({ timeout: 5000 })
    const text = (await header.textContent()) ?? ''
    const m = text.match(/(\d+)\s+nodes.*?(\d+)\s+relationships.*?(\d+)\s+episodes/)
    if (!m) throw new Error(`graph header not parseable: "${text}"`)
    return { nodes: Number(m[1]), links: Number(m[2]), episodes: Number(m[3]) }
  }

  async function refresh(page: Page): Promise<void> {
    const btn = page.getByRole('button', { name: /^Refresh$/ }).first()
    await expect(btn).toBeVisible()
    await Promise.all([
      page.waitForResponse((r) => r.url().includes('/api/v1/graph/episodes')),
      btn.click(),
    ])
  }

  test.beforeEach(() => {
    payload = PAYLOAD_A
  })

  test('renders the initial topology from the graph API', async ({ page }) => {
    await gotoGraph(page)

    const counts = await readHeaderCounts(page)
    expect(counts).toEqual({ nodes: 6, links: 3, episodes: 2 })

    // The explorer canvas mounted and did not crash on the payload.
    await expect(page.locator('canvas').first()).toBeVisible()
  })

  test('Refresh refetches and re-renders when the topology grows', async ({ page }) => {
    await gotoGraph(page)
    expect((await readHeaderCounts(page)).nodes).toBe(6)

    // The incident rippled: swap in the larger topology, then Refresh. The
    // Promise.all in refresh() also proves a NEW fetch actually fired.
    payload = PAYLOAD_B
    await refresh(page)

    await expect
      .poll(async () => (await readHeaderCounts(page)).nodes, { timeout: 8000 })
      .toBe(10)

    const grown = await readHeaderCounts(page)
    expect(grown).toEqual({ nodes: 10, links: 6, episodes: 3 })
    // Still a live canvas, no crash on the bigger graph.
    await expect(page.locator('canvas').first()).toBeVisible()
  })

  test('Refresh reflects both growth and pruning of the topology', async ({ page }) => {
    await gotoGraph(page)
    expect((await readHeaderCounts(page)).nodes).toBe(6)

    // Grow A -> B
    payload = PAYLOAD_B
    await refresh(page)
    await expect.poll(async () => (await readHeaderCounts(page)).nodes, { timeout: 8000 }).toBe(10)

    // Prune B -> C (resolution collapses the graph)
    payload = PAYLOAD_C
    await refresh(page)
    await expect.poll(async () => (await readHeaderCounts(page)).nodes, { timeout: 8000 }).toBe(3)

    const pruned = await readHeaderCounts(page)
    expect(pruned).toEqual({ nodes: 3, links: 1, episodes: 1 })
    await expect(page.locator('canvas').first()).toBeVisible()
  })
})
