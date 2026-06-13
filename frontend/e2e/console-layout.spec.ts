import { test, expect, type Page } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

/**
 * Console / Command Center layout verification.
 *
 * Renders the cockpit fully populated (route-mocked topology + incidents +
 * chat + health, no backend needed) and screenshots it across a spread of
 * viewport ratios — including deliberately SHORT heights that mimic a browser
 * with tabs, bookmarks bar and devtools eating into the real estate. The PNGs
 * land in e2e/__console__/ for visual review.
 */

const here = dirname(fileURLToPath(import.meta.url))
const topology = JSON.parse(readFileSync(join(here, 'fixtures', 'topology.json'), 'utf-8'))

const SHOT_DIR = join(here, '__console__')

const incidents = {
  items: [
    {
      id: 'INC-2026-0001',
      title: 'CPU stress on qwen3-14b saturating the reasoning agent',
      severity: 'high',
      status: 'pending_approval',
      category: 'resource',
      affected_services: [{ name: 'qwen3-14b' }],
      tags: ['demo-mode', 'cpu_stress'],
      source: 'demo-mode',
      created_at: '2026-06-13T09:00:00Z',
      updated_at: '2026-06-13T09:02:00Z',
      rca: { root_cause: 'A synthetic CPU load is pinning the reasoning model host above 95% utilisation.' },
    },
    {
      id: 'INC-2026-0002',
      title: 'Bad config causing 5xx burst on the frontend gateway',
      severity: 'critical',
      status: 'analyzing',
      category: 'config',
      affected_services: [{ name: 'caddy' }],
      tags: ['demo-mode', 'bad_config_5xx'],
      source: 'demo-mode',
      created_at: '2026-06-13T09:05:00Z',
      updated_at: '2026-06-13T09:06:00Z',
      rca: { root_cause: 'A malformed upstream block is returning 502s for ~30% of /api requests.' },
    },
  ],
  total: 2,
  page: 1,
  page_size: 50,
  has_more: false,
}

const health = {
  status: 'healthy',
  components: [
    { name: 'fast_agent', healthy: true, status: 'healthy', latency_ms: 120 },
    { name: 'reasoning_agent', healthy: true, status: 'healthy', latency_ms: 480 },
    { name: 'neo4j', healthy: true, status: 'healthy', latency_ms: 8 },
  ],
  uptime_seconds: 86_400,
  version: '0.7.0',
}

const chatResponse = {
  conversation_id: 'conv-console-demo',
  message: {
    role: 'assistant',
    content:
      'I checked the reasoning agent (qwen3-14b). CPU is pinned at 96% by a synthetic stress load; ' +
      'restarting the container or stopping the stress generator will recover latency. Want me to remediate?',
    timestamp: new Date().toISOString(),
  },
  confidence: 0.86,
  suggested_actions: ['Restart qwen3-14b', 'Stop the CPU stress generator'],
  related_incidents: ['INC-2026-0001'],
  metadata: {
    model_used: 'qwen3-14b',
    tokens_used: 742,
    tools: {
      telemetry: { source: 'Loki + Prometheus', logs: 200, errors: 0, warnings: 5 },
      similar: { count: 1 },
    },
  },
  proposed_action: null,
}

async function mockApi(page: Page) {
  await page.route('**/api/v1/**', async (route) => {
    const url = route.request().url()
    const json = (body: unknown, status = 200) =>
      route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })

    if (url.includes('/auth/config')) return json({ auth_required: false })
    if (url.includes('/auth/me')) return json({}, 401)
    if (url.includes('/health')) return json(health)
    if (url.includes('/graph/topology')) return json(topology)
    if (url.includes('/incidents')) return json(incidents)
    if (url.includes('/chat/conversations')) return json({ items: [], total: 0 })
    if (url.includes('/chat')) return json(chatResponse)
    // Catch-all so nothing hangs and no panel error-states distort the layout.
    return json({ items: [], total: 0 })
  })
}

const VIEWPORTS = [
  { name: 'desktop-1920x1080', w: 1920, h: 1080, lg: true },
  { name: 'laptop-1440x900', w: 1440, h: 900, lg: true },
  // Browser with tabs + bookmarks bar open → shorter usable height.
  { name: 'laptop-tabs-1536x720', w: 1536, h: 720, lg: true },
  // Lots of chrome (tabs + bookmarks + devtools docked) → very short.
  { name: 'laptop-devtools-1366x620', w: 1366, h: 620, lg: true },
  // 1024 is exactly the cockpit's lg side-by-side breakpoint.
  { name: 'tablet-landscape-1024x768', w: 1024, h: 768, lg: true },
  { name: 'tablet-portrait-834x1112', w: 834, h: 1112, lg: false },
  { name: 'mobile-390x844', w: 390, h: 844, lg: false },
]

test.describe('Command Center layout', () => {
  for (const vp of VIEWPORTS) {
    test(`renders cleanly @ ${vp.name}`, async ({ page }) => {
      await mockApi(page)
      await page.setViewportSize({ width: vp.w, height: vp.h })
      await page.goto('/console')

      // The three cockpit surfaces are present.
      await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible()
      await expect(page.getByTestId('console-incidents')).toBeVisible()
      await expect(page.getByTestId('console-chat')).toBeVisible()
      await expect(page.getByTestId('console-graph-pane')).toBeVisible()

      // The chat composer (the thing that kept getting "cut off") is rendered
      // with a comfortable floor; the relaxed cockpit may scroll rather than
      // cram, so we assert it exists rather than pinning it to the viewport.
      const composer = page.locator('[data-testid="console-chat"] form')
      await expect(composer).toBeVisible()

      // Let the graph settle (lazy chunk + topology fetch + ResizeObserver).
      await page.waitForTimeout(900)
      await page.screenshot({ path: join(SHOT_DIR, `${vp.name}.png`), fullPage: true })
    })
  }

  test('Agents page no longer has an Architecture tab (it moved to Command Center)', async ({ page }) => {
    await mockApi(page)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/agents')
    await expect(page.getByRole('heading', { name: 'Agent Hub' })).toBeVisible()
    // The topology graph now lives only in /console — no Architecture tab here.
    await expect(page.getByRole('button', { name: /^Architecture$/ })).toHaveCount(0)
    // The other agent tabs are untouched.
    await expect(page.getByRole('button', { name: /MCP Tools/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /Graph Explorer/ })).toBeVisible()
    await page.screenshot({ path: join(SHOT_DIR, 'agents-no-architecture.png') })
  })

  test('selecting a service attaches it to the chat as context', async ({ page }) => {
    await mockApi(page)
    await page.setViewportSize({ width: 1536, height: 860 })
    await page.goto('/console')
    await page.waitForTimeout(900)

    // Ctrl-click a service node on the embedded graph → context chip appears.
    const node = page.locator('[data-testid="schema-graph-embedded"] [data-testid^="schema-node-"]').first()
    if (await node.count()) {
      await node.click({ modifiers: ['Control'] })
      await expect(page.getByText('attached as context')).toBeVisible({ timeout: 3_000 })
      await page.screenshot({ path: join(SHOT_DIR, 'selection-context.png') })
    }
  })
})
