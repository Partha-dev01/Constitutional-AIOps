import { test, expect, type Page, type ConsoleMessage } from '@playwright/test'
import { readFileSync, mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

/**
 * LOCAL pre-deploy UI QA for the layout overhaul.
 *
 * Route-mocked (no backend), HEADLESS. For every viewport ratio we visit every
 * app route, capture a full-page screenshot, and collect console/page errors.
 * Plus targeted interaction checks for the new collapsible sidebar, the mobile
 * off-canvas drawer, the dark native controls on the Benchmark Run tab, the
 * fit-to-viewport Command Center, and horizontal-overflow on mobile widths.
 *
 * Screenshots land in test-results/local-ui/<viewport>__<route>.png.
 */

const here = dirname(fileURLToPath(import.meta.url))
const topology = JSON.parse(readFileSync(join(here, 'fixtures', 'topology.json'), 'utf-8'))

const SHOT_DIR = join(here, '..', 'test-results', 'local-ui')
mkdirSync(SHOT_DIR, { recursive: true })

// ---------------------------------------------------------------------------
// Mock payloads (mirror the console-layout.spec.ts mock style)
// ---------------------------------------------------------------------------

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
  conversation_id: 'conv-local-ui-demo',
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

// Endpoint shapes that DON'T fit the generic {items:[]} envelope. The real
// backend returns these specific shapes; the pages read nested fields and
// (with no ErrorBoundary in the app) a missing field unmounts the whole tree.
const incidentStats = { total: 2, by_status: { open: 1, investigating: 1, resolved: 4 }, by_severity: { critical: 1, high: 1 } }
const actionStats = {
  total: 3,
  by_status: { awaiting_approval: 1, completed: 2 },
  success_rate: 0.92,
  avg_execution_ms: 1800,
}
const allSettings = {
  constitutional: {
    autoThreshold: 90, approvalThreshold: 70, maxActionsPerMinute: 10,
    enableAuditLog: true, enableLearning: true, strictTier1: true,
  },
  notifications: {
    emailEnabled: false, slackEnabled: false, webhookEnabled: false, webhookUrl: '',
    notifyOnCritical: true, notifyOnApproval: true, notifyOnResolution: false,
  },
  telemetry: {
    lokiEnabled: true, lokiUrl: 'http://loki:3100', prometheusEnabled: true,
    prometheusUrl: 'http://prometheus:9090', tempoEnabled: true,
    tempoUrl: 'http://tempo:3200', retentionDays: 30,
  },
  remediation: {
    mode: 'diagnose', autoConfidenceThreshold: 90, requireEvidenceForAuto: true, demoTargetUrl: '',
  },
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
    if (url.includes('/incidents/stats')) return json(incidentStats)
    if (url.includes('/actions/stats')) return json(actionStats)
    // /actions/pending returns a {actions:[...]} shape, NOT {items:[]} — the
    // Incidents page reads actionData.actions and crashes on undefined.
    if (url.includes('/actions/pending')) return json({ actions: [], total: 0 })
    if (url.includes('/settings')) return json(allSettings)
    if (url.includes('/incidents')) return json(incidents)
    if (url.includes('/chat/conversations')) return json({ items: [], total: 0 })
    if (url.includes('/chat')) return json(chatResponse)
    // Catch-all so nothing hangs and no panel error-states distort the layout.
    return json({ items: [], total: 0 })
  })
}

// ---------------------------------------------------------------------------
// Console capture — collect errors, allowlist the EXPECTED backend-less noise.
// ---------------------------------------------------------------------------

// WebSocket / network failures are expected with no backend running.
const ALLOWLIST = /websocket|ws:\/\/|wss:\/\/|WebSocket|ECONNREFUSED|Failed to load resource/i

type Captured = { type: 'console' | 'pageerror'; text: string }

function attachConsole(page: Page, sink: Captured[]) {
  page.on('console', (m: ConsoleMessage) => {
    if (m.type() !== 'error') return
    const text = m.text()
    if (ALLOWLIST.test(text)) return
    sink.push({ type: 'console', text })
  })
  page.on('pageerror', (err) => {
    const text = `${err.name}: ${err.message}`
    if (ALLOWLIST.test(text)) return
    sink.push({ type: 'pageerror', text })
  })
}

// All non-allowlisted errors, keyed by "<viewport> <route/interaction>".
const ALL_ERRORS: Record<string, Captured[]> = {}
const OVERFLOW_FAILURES: string[] = []
const SHOTS: string[] = []

function recordErrors(key: string, sink: Captured[]) {
  if (sink.length) ALL_ERRORS[key] = [...sink]
}

async function shoot(page: Page, name: string) {
  const path = join(SHOT_DIR, name)
  await page.screenshot({ path, fullPage: true })
  SHOTS.push(name)
}

// ---------------------------------------------------------------------------
// Routes + their wait-for "ready" assertion.
// ---------------------------------------------------------------------------

const ROUTES: Array<{ path: string; ready: (page: Page) => Promise<unknown> }> = [
  { path: '/', ready: (p) => expect(p.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible() },
  { path: '/console', ready: (p) => expect(p.getByRole('heading', { name: 'Command Center' })).toBeVisible() },
  { path: '/agents', ready: (p) => expect(p.getByRole('heading', { name: 'Agent Hub' })).toBeVisible() },
  { path: '/infrastructure', ready: (p) => expect(p.getByRole('heading', { name: 'Infrastructure', level: 1 })).toBeVisible() },
  { path: '/incidents', ready: (p) => expect(p.getByRole('heading', { name: 'Incidents', level: 1 })).toBeVisible() },
  { path: '/chat', ready: (p) => expect(p.getByRole('heading', { name: 'Chat', level: 1 })).toBeVisible() },
  { path: '/metrics', ready: (p) => expect(p.getByRole('heading', { name: /Metrics/, level: 1 })).toBeVisible() },
  { path: '/benchmark', ready: (p) => expect(p.getByRole('heading', { name: 'Benchmark', level: 1 })).toBeVisible() },
  { path: '/settings', ready: (p) => expect(p.getByRole('heading', { name: 'Settings', level: 1 })).toBeVisible() },
]

const VIEWPORTS = [
  { name: 'desktop-1920x1080', w: 1920, h: 1080 },
  { name: 'laptop-1440x900', w: 1440, h: 900 },
  { name: 'laptop-short-1366x640', w: 1366, h: 640 },
  { name: 'tablet-768x1024', w: 768, h: 1024 },
  { name: 'mobile-390x844', w: 390, h: 844 },
  { name: 'mobile-small-360x740', w: 360, h: 740 },
]

const MOBILE_NAMES = new Set(['mobile-390x844', 'mobile-small-360x740'])

// ---------------------------------------------------------------------------
// STEP 2 — per-viewport sweep over every route.
// ---------------------------------------------------------------------------

test.describe('Local UI QA — route sweep', () => {
  for (const vp of VIEWPORTS) {
    test(`sweep @ ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.w, height: vp.h })

      for (const route of ROUTES) {
        const sink: Captured[] = []
        attachConsole(page, sink)
        await mockApi(page)

        await page.goto(route.path)
        // Wait for the page's own ready signal; tolerate slow lazy chunks.
        await route.ready(page).catch(async () => {
          // Re-throw with context so the report pins the failing route.
          throw new Error(`Ready-assertion failed @ ${vp.name} ${route.path}`)
        })
        // Let graphs / lazy chunks / ResizeObservers settle.
        await page.waitForTimeout(route.path === '/console' ? 1000 : 500)

        const routeSlug = route.path === '/' ? 'root' : route.path.replace(/^\//, '').replace(/\//g, '-')
        await shoot(page, `${vp.name}__${routeSlug}.png`)
        recordErrors(`${vp.name} ${route.path}`, sink)

        // Mobile widths: assert NO horizontal scrollbar on representative pages.
        if (MOBILE_NAMES.has(vp.name) && (route.path === '/' || route.path === '/incidents' || route.path === '/metrics')) {
          const noOverflow = await page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth + 1
          )
          if (!noOverflow) {
            const sw = await page.evaluate(() => document.documentElement.scrollWidth)
            OVERFLOW_FAILURES.push(`${vp.name} ${route.path} — scrollWidth=${sw} > innerWidth=${vp.w}`)
          }
        }

        // Detach listeners so the next route starts clean.
        page.removeAllListeners('console')
        page.removeAllListeners('pageerror')
      }
    })
  }
})

// ---------------------------------------------------------------------------
// STEP 2 — targeted interaction checks.
// ---------------------------------------------------------------------------

test.describe('Local UI QA — interactions', () => {
  test('desktop sidebar collapses to an icon rail and back @ 1440', async ({ page }) => {
    const sink: Captured[] = []
    attachConsole(page, sink)
    await mockApi(page)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/console')
    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible()

    // Use the STATIC desktop sidebar (the md:block copy), not the hidden drawer.
    const desktopSidebar = page.locator('.md\\:block [data-testid="app-sidebar"]')
    await expect(desktopSidebar).toBeVisible()
    const fullBox = await desktopSidebar.boundingBox()
    expect(fullBox?.width ?? 0).toBeGreaterThan(200) // w-64 ≈ 256 * 0.8 root scale

    // Collapse → icon rail (w-16 ≈ 64 * 0.8).
    await page.locator('.md\\:block [data-testid="sidebar-toggle"]').click()
    await expect.poll(async () => (await desktopSidebar.boundingBox())?.width ?? 0).toBeLessThan(120)
    await page.waitForTimeout(150)
    await shoot(page, 'interaction__desktop-1440__rail.png')

    // Expand back to full.
    await page.locator('.md\\:block [data-testid="sidebar-toggle"]').click()
    await expect.poll(async () => (await desktopSidebar.boundingBox())?.width ?? 0).toBeGreaterThan(200)

    recordErrors('desktop-1440 sidebar-toggle', sink)
  })

  test('mobile drawer: static sidebar hidden; toggle/backdrop/Escape close it @ 390', async ({ page }) => {
    const sink: Captured[] = []
    attachConsole(page, sink)
    await mockApi(page)
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/console')
    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible()

    // The static desktop sidebar column is display:none on mobile.
    const desktopSidebar = page.locator('.md\\:block [data-testid="app-sidebar"]')
    await expect(desktopSidebar).toBeHidden()

    // No backdrop until the drawer is opened.
    await expect(page.getByTestId('sidebar-backdrop')).toHaveCount(0)

    // Open drawer → drawer sidebar + backdrop visible.
    await page.getByTestId('mobile-nav-toggle').click()
    const drawerSidebar = page.locator('.md\\:hidden [data-testid="app-sidebar"]')
    await expect(drawerSidebar).toBeVisible()
    await expect(page.getByTestId('sidebar-backdrop')).toBeVisible()
    await page.waitForTimeout(250) // let the slide-in transition finish
    await shoot(page, 'interaction__mobile-390__drawer.png')

    // Escape closes it.
    await page.keyboard.press('Escape')
    await expect(page.getByTestId('sidebar-backdrop')).toHaveCount(0)

    // Re-open, then click the backdrop to close.
    await page.getByTestId('mobile-nav-toggle').click()
    await expect(page.getByTestId('sidebar-backdrop')).toBeVisible()
    await page.getByTestId('sidebar-backdrop').click({ position: { x: 350, y: 400 } })
    await expect(page.getByTestId('sidebar-backdrop')).toHaveCount(0)

    recordErrors('mobile-390 drawer', sink)
  })

  test('benchmark Run tab native controls render dark; Results tab loads @ 1440', async ({ page }) => {
    const sink: Captured[] = []
    attachConsole(page, sink)
    await mockApi(page)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/benchmark')
    await expect(page.getByRole('heading', { name: 'Benchmark', level: 1 })).toBeVisible()

    // Switch to Run tab.
    await page.getByRole('button', { name: 'Run', exact: true }).click()
    const select = page.locator('select').first()
    await expect(select).toBeVisible()
    const numberInput = page.locator('input[type="number"]').first()
    await expect(numberInput).toBeVisible()

    // color-scheme:dark should give the native controls a dark canvas. Read the
    // computed background to flag if it came through white (a regression).
    const selectBg = await select.evaluate((el) => getComputedStyle(el).backgroundColor)
    const colorScheme = await page.evaluate(() => getComputedStyle(document.documentElement).colorScheme)
    sink.push({ type: 'console', text: `__INFO select bg=${selectBg} colorScheme=${colorScheme}` })

    await shoot(page, 'interaction__benchmark__run.png')

    // Results tab loads without error.
    await page.getByRole('button', { name: 'Results', exact: true }).click()
    await page.waitForTimeout(300)
    await shoot(page, 'interaction__benchmark__results.png')

    // Strip the INFO marker out of the real-error sink before recording.
    recordErrors('benchmark run/results', sink.filter((c) => !c.text.startsWith('__INFO')))
    // Surface the diagnostic separately (never counts as a failure).
    const info = sink.find((c) => c.text.startsWith('__INFO'))
    if (info) console.log(`[diag] benchmark ${info.text}`)
  })

  test('command center fits the viewport with all three panes @ 1440', async ({ page }) => {
    const sink: Captured[] = []
    attachConsole(page, sink)
    await mockApi(page)
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/console')
    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible()
    await page.waitForTimeout(1000)

    await expect(page.getByTestId('console-graph-pane')).toBeVisible()
    await expect(page.getByTestId('console-incidents')).toBeVisible()
    await expect(page.getByTestId('console-chat')).toBeVisible()

    // The page body itself must NOT overflow the viewport beyond ~1px; the
    // internal panes scroll, the document does not.
    const docOverflow = await page.evaluate(() => ({
      docScrollH: document.documentElement.scrollHeight,
      innerH: window.innerHeight,
      bodyScrollW: document.documentElement.scrollWidth,
      innerW: window.innerWidth,
    }))
    // Vertical: the shell uses 100dvh with overflow-hidden, so the document
    // should not grow a page-level scrollbar.
    expect(docOverflow.docScrollH).toBeLessThanOrEqual(docOverflow.innerH + 2)
    expect(docOverflow.bodyScrollW).toBeLessThanOrEqual(docOverflow.innerW + 2)

    recordErrors('console fit-viewport', sink)
  })
})

// ---------------------------------------------------------------------------
// STEP 3 — emit a machine-readable summary into the test output.
// ---------------------------------------------------------------------------

test.afterAll(() => {
  const summary = {
    nonAllowlistedErrors: ALL_ERRORS,
    overflowFailures: OVERFLOW_FAILURES,
    screenshots: SHOTS.sort(),
  }
  console.log('\n===== LOCAL-UI-QA-SUMMARY-BEGIN =====')
  console.log(JSON.stringify(summary, null, 2))
  console.log('===== LOCAL-UI-QA-SUMMARY-END =====\n')
})
