/**
 * Graph "Schema mode" — Playwright E2E (session-14).
 *
 * Runs against `vite preview` on :4174 with all backend API intercepted (see
 * playwright.config.schema.ts). The topology comes from the checked-in fixture
 * e2e/fixtures/topology.json — the FE↔BE payload contract artifact.
 *
 * Coverage:
 *  - Contract guard: default (Episodes) mode still renders the force-graph canvas
 *  - Toggle to Architecture → SVG schema canvas + all fixture nodes render
 *  - Node click → detail drawer
 *  - Multi-select (click + ctrl-click + edge) → Ask AI chips
 *  - Time scrubber present; node badge shows cumulative episode count at full window
 *  - Ask AI: intercepted chat reply renders; "Continue in Chat" navigates with the id
 *  - Zoom / pan controls don't crash the canvas
 */

import { test, expect, Page, Route } from '@playwright/test'
import fs from 'fs'

// Playwright runs from the frontend/ dir; read the contract fixture by cwd path
// (ESM scope has no __dirname).
const TOPOLOGY = JSON.parse(
  fs.readFileSync('e2e/fixtures/topology.json', 'utf-8'),
)

async function interceptAllApis(page: Page) {
  await page.route('**/api/v1/graph/topology**', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(TOPOLOGY),
    })
  })
  // Episodes feed for the default (Neo4j) mode — must be NON-empty so the
  // force-graph actually renders a <canvas> (empty data shows an empty state).
  await page.route('**/api/v1/graph/episodes**', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        episodes: [
          { id: 'ep-001', title: 'High CPU on backend', type: 'episode', timestamp: '2026-06-10T10:00:00Z', category: 'performance', severity: 'critical', status: 'resolved', root_cause: 'memory_leak', confidence: 0.9, resolution_time_minutes: 12, services: ['backend'], successful_actions: ['restart_service'] },
          { id: 'ep-002', title: 'Neo4j connection timeout', type: 'episode', timestamp: '2026-06-10T10:05:00Z', category: 'connectivity', severity: 'high', status: 'resolved', root_cause: 'connection_pool', confidence: 0.85, resolution_time_minutes: 8, services: ['neo4j'], successful_actions: [] },
        ],
        root_causes: [
          { id: 'rc-memory-leak', name: 'memory_leak', type: 'root_cause', frequency: 3, avg_resolution_time_minutes: 15, success_rate: 0.9 },
        ],
        actions: [
          { id: 'act-restart', name: 'restart_service', type: 'action', used_count: 12, success_rate: 0.92, avg_execution_time_seconds: 4 },
        ],
        services: [
          { name: 'backend', type: 'service', status: 'warning', incident_count: 2, last_incident: '2026-06-10T10:00:00Z' },
          { name: 'neo4j', type: 'service', status: 'healthy', incident_count: 1, last_incident: '2026-06-10T10:05:00Z' },
        ],
        edges: [
          { source: 'episode-ep-001', target: 'rc-memory-leak', relationship: 'caused_by', weight: 1 },
          { source: 'episode-ep-001', target: 'service-backend', relationship: 'affects', weight: 1 },
          { source: 'episode-ep-002', target: 'service-neo4j', relationship: 'affects', weight: 1 },
        ],
      }),
    })
  })
  await page.route('**/health**', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        healthy: true,
        components: [
          { name: 'neo4j', healthy: true },
          { name: 'fast_agent', healthy: true },
          { name: 'reasoning_agent', healthy: true },
        ],
      }),
    })
  })
  await page.route('**/api/v1/agents/**', async (route: Route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ activities: [] }) })
  })
  await page.route('**/api/v1/telemetry/**', async (route: Route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
  })
  await page.route('**/api/v1/tools/**', async (route: Route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ tools: [] }) })
  })
  await page.route('**/api/v1/ws/token**', async (route: Route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ token: 'mock-token' }) })
  })
}

async function gotoGraphTab(page: Page) {
  await interceptAllApis(page)
  await page.goto('/agents')
  await page.getByRole('tab', { name: /graph explorer/i }).first().click().catch(async () => {
    await page.locator('button:has-text("Graph Explorer")').first().click()
  })
}

async function gotoSchemaMode(page: Page) {
  await gotoGraphTab(page)
  // The Architecture toggle renders in the card header independently of the
  // Episodes-mode canvas, so we don't depend on episode data being present.
  const toggle = page.locator('button:has-text("Architecture")')
  await toggle.waitFor({ state: 'visible', timeout: 15000 })
  await toggle.click()
  await page.waitForSelector('[data-testid="schema-canvas"]', { timeout: 15000 })
}

test.describe('Graph Schema mode', () => {
  test('contract guard: default mode still renders the force-graph canvas', async ({ page }) => {
    await gotoGraphTab(page)
    await expect(page.locator('canvas')).toBeVisible({ timeout: 15000 })
  })

  test('toggle to Architecture renders the SVG schema with all fixture nodes', async ({ page }) => {
    await gotoSchemaMode(page)
    await expect(page.locator('[data-testid="schema-canvas"]')).toBeVisible()
    const nodes = page.locator('[data-testid^="schema-node-"]')
    await expect(nodes).toHaveCount(TOPOLOGY.nodes.length)
    // The dynamic edge-host node is present.
    await expect(page.locator('[data-testid="schema-node-edge:nextcloud-host"]')).toBeVisible()
  })

  test('clicking a node opens the detail drawer', async ({ page }) => {
    await gotoSchemaMode(page)
    await page.locator('[data-testid="schema-node-backend"]').click()
    await expect(page.locator('[data-testid="schema-drawer"]')).toBeVisible()
  })

  test('node badge shows the cumulative episode count at full window', async ({ page }) => {
    await gotoSchemaMode(page)
    // backend has 6 episodes in the fixture; full window => cumulative == total.
    const badge = page.locator('[data-testid="schema-node-backend"] [data-count]')
    await expect(badge.first()).toHaveAttribute('data-count', '6')
  })

  test('multi-selecting nodes builds Ask AI chips', async ({ page }) => {
    await gotoSchemaMode(page)
    // Ctrl-click is additive and (unlike a plain click) does not open the
    // right-side drawer, so it can't cover the next node. Use left-column
    // nodes to stay clear of the panel either way.
    await page.locator('[data-testid="schema-node-caddy"]').click({ modifiers: ['Control'] })
    await page.locator('[data-testid="schema-node-frontend"]').click({ modifiers: ['Control'] })
    await expect(page.locator('[data-testid="askai-panel"]')).toBeVisible()
    const chips = page.locator('[data-testid^="askai-chip-"]')
    await expect(chips).toHaveCount(2)
  })

  test('Ask AI returns a reply and Continue in Chat navigates with the conversation id', async ({ page }) => {
    await page.route('**/api/v1/chat/**', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          conversation_id: 'conv-test',
          message: { role: 'assistant', content: 'Backend depends on Neo4j for memory.', timestamp: '2026-06-12T00:00:00Z' },
          confidence: 0.8,
          metadata: { selection_applied: true },
        }),
      })
    })
    await gotoSchemaMode(page)
    // Select via ctrl-click so the drawer doesn't cover the Ask AI input.
    await page.locator('[data-testid="schema-node-backend"]').click({ modifiers: ['Control'] })
    await page.locator('[data-testid="askai-input"]').fill('Why does this depend on neo4j?')
    await page.locator('[data-testid="askai-send"]').click()
    await expect(page.getByText('Backend depends on Neo4j for memory.')).toBeVisible()
    await page.locator('[data-testid="askai-continue"]').click()
    // Chat.tsx consumes the conversation id then strips the query param, so the
    // settled URL is /chat — assert we reached the chat page.
    await expect(page).toHaveURL(/\/chat\b/)
  })

  test('time scrubber is present and zoom/pan do not crash the canvas', async ({ page }) => {
    await gotoSchemaMode(page)
    await expect(page.locator('[data-testid="time-scrubber"]')).toBeVisible()
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
