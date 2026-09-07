/**
 * Platform schema graph (Command Center) — Playwright E2E.
 *
 * Runs against `vite preview` on :4174 with all backend API intercepted (see
 * playwright.config.schema.ts). The topology comes from the checked-in fixture
 * e2e/fixtures/topology.json — the FE<->BE payload contract artifact.
 *
 * The schema graph now lives ONLY as the embedded platform view inside the
 * Command Center (`/console`): the old standalone Agent-Hub "Graph Explorer" +
 * "Architecture" tabs were retired, and the docked Ask-AI panel / time scrubber
 * only ever existed on the non-embedded path the app no longer mounts. So this
 * suite drives the cockpit's embedded graph and covers what it actually renders:
 *  - the SVG schema canvas renders with every fixture node (incl. the dynamic
 *    edge-host node)
 *  - a node click opens the detail drawer
 *  - a node's badge shows the cumulative episode count at the full window
 *  - Ctrl-click multi-select attaches the nodes to the cockpit chat as context
 *  - zoom / pan do not crash the canvas
 * Layout/responsiveness of the cockpit itself lives in console-layout.spec.ts.
 */

import { test, expect, Page, Route } from '@playwright/test'
import fs from 'fs'

// Playwright runs from the frontend/ dir; read the contract fixture by cwd path
// (ESM scope has no __dirname).
const TOPOLOGY = JSON.parse(fs.readFileSync('e2e/fixtures/topology.json', 'utf-8'))

// A minimal, well-formed live schema so the cockpit's chat and service-action
// bar render cleanly alongside the graph (mirrors GET /topology/schema).
const SCHEMA = {
  mode: 'discovered',
  nodes: [
    { id: 'caddy', label: 'caddy', kind: 'gateway', tier: 0, port: 443 },
    { id: 'backend', label: 'backend', kind: 'service', tier: 1, port: 8080 },
    { id: 'neo4j', label: 'neo4j', kind: 'database', tier: 2, port: 7687 },
  ],
  edges: [
    { source: 'caddy', target: 'backend', relationship: 'routes_to', kind: 'network' },
    { source: 'backend', target: 'neo4j', relationship: 'depends_on', kind: 'data' },
  ],
}

async function mockApi(page: Page) {
  await page.route('**/api/v1/**', async (route: Route) => {
    const url = route.request().url()
    const json = (body: unknown, status = 200) =>
      route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })

    // Auth disabled so bootstrap doesn't fail safe to /login.
    if (url.includes('/auth/config'))
      return json({ auth_required: false, signup_enabled: false, captcha_provider: '', captcha_site_key: '' })
    if (url.includes('/auth/me')) return json({}, 401)
    if (url.includes('/health'))
      return json({ status: 'healthy', components: [], uptime_seconds: 1, version: '1.0.0' })
    if (url.includes('/topology/schema')) return json(SCHEMA)
    if (url.includes('/graph/topology')) return json(TOPOLOGY)
    if (url.includes('/incidents')) return json({ items: [], total: 0, page: 1, page_size: 50, has_more: false })
    if (url.includes('/chat/conversations')) return json({ items: [], total: 0 })
    // Catch-all so nothing hangs and no panel error-states distort the graph.
    return json({ items: [], total: 0 })
  })
}

// Open the Command Center and wait for the embedded platform graph to settle
// (lazy chunk + topology fetch + ResizeObserver-driven layout).
async function gotoEmbeddedGraph(page: Page) {
  await mockApi(page)
  await page.setViewportSize({ width: 1536, height: 900 })
  await page.goto('/console')
  await expect(page.getByTestId('schema-graph-embedded')).toBeVisible({ timeout: 15000 })
  await expect(page.locator('[data-testid="schema-canvas"]')).toBeVisible({ timeout: 15000 })
}

test.describe('Platform schema graph (Command Center)', () => {
  test('renders the SVG schema canvas with every fixture node', async ({ page }) => {
    await gotoEmbeddedGraph(page)
    const nodes = page.locator('[data-testid="schema-graph-embedded"] [data-testid^="schema-node-"]')
    await expect(nodes).toHaveCount(TOPOLOGY.nodes.length)
    // The dynamic edge-host node is present.
    await expect(page.locator('[data-testid="schema-node-edge:nextcloud-host"]')).toBeVisible()
  })

  test('clicking a node opens the detail drawer', async ({ page }) => {
    await gotoEmbeddedGraph(page)
    await page.locator('[data-testid="schema-node-backend"]').click()
    await expect(page.locator('[data-testid="schema-drawer"]')).toBeVisible()
  })

  test('a node badge shows the cumulative episode count at the full window', async ({ page }) => {
    await gotoEmbeddedGraph(page)
    // backend has 6 episodes in the fixture; the embedded view has no scrubber,
    // so the badge shows the full-window cumulative count.
    const badge = page.locator('[data-testid="schema-node-backend"] [data-count]')
    await expect(badge.first()).toHaveAttribute('data-count', '6')
  })

  test('Ctrl-click multi-select attaches the nodes to the cockpit chat as context', async ({ page }) => {
    await gotoEmbeddedGraph(page)
    // Ctrl-click is additive and (unlike a plain click) does not open the
    // right-side drawer, so it can't cover the next node.
    await page.locator('[data-testid="schema-node-caddy"]').click({ modifiers: ['Control'] })
    await page.locator('[data-testid="schema-node-frontend"]').click({ modifiers: ['Control'] })
    // The Console surfaces the embedded selection as a chat-context banner.
    await expect(page.getByText('2 attached as context')).toBeVisible({ timeout: 3000 })
  })

  test('zoom and pan do not crash the canvas', async ({ page }) => {
    await gotoEmbeddedGraph(page)
    const canvas = page.locator('[data-testid="schema-canvas"]')
    const box = await canvas.boundingBox()
    if (box) {
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
      await page.mouse.wheel(0, -200) // zoom in
      await page.mouse.wheel(0, 200) // zoom out
    }
    await expect(canvas).toBeVisible()
  })
})
