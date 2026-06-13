/**
 * Constitutional AIOps — Infrastructure "Demo / Chaos" panel E2E tests
 *
 * Runs against a locally served Vite preview/dev server with every API call
 * intercepted via Playwright route mocking. No live backend or t3 agent needed.
 *
 * Run (mirrors the other mock-based local specs):
 *   npx playwright test e2e/demo-panel.spec.ts --config playwright.config.local.ts
 * (or, against a Docker frontend on :3000)
 *   npx playwright test e2e/demo-panel.spec.ts
 *
 * NOTE: this file is NOT yet listed in playwright.config.local.ts `testMatch`;
 * the integrator should add '**\/demo-panel.spec.ts' there (or pass it
 * explicitly under the default config). See the lane report.
 */

import { test, expect, Page } from '@playwright/test'

// ── Shared mock data ──────────────────────────────────────────────────────────

const SCENARIOS = {
  scenarios: [
    { id: 'db_down', label: 'Database down', description: 'Stop the nextcloud database' },
    { id: 'cpu_stress', label: 'CPU stress', description: 'Peg CPU on nextcloud' },
    { id: 'mem_stress', label: 'Memory stress', description: 'Exhaust memory on nextcloud' },
    { id: 'bad_config_5xx', label: 'Bad config (5xx)', description: 'Break config to return 5xx' },
    { id: 'disk_fill', label: 'Disk fill', description: 'Fill the disk on nextcloud' },
  ],
}

function status(opts: {
  reachable: boolean
  active?: Record<string, boolean>
  containers?: Record<string, boolean>
}) {
  const scenarios: Record<string, { active: boolean }> = {}
  for (const s of SCENARIOS.scenarios) {
    scenarios[s.id] = { active: opts.active?.[s.id] ?? false }
  }
  const containers: Record<string, { running: boolean }> = {
    nextcloud: { running: opts.containers?.['nextcloud'] ?? true },
    'nextcloud-db': { running: opts.containers?.['nextcloud-db'] ?? true },
  }
  return {
    target_url: 'http://t3-demo-agent:9099',
    reachable: opts.reachable,
    scenarios,
    containers,
  }
}

// ── Mock helper ───────────────────────────────────────────────────────────────

async function mockDemo(
  page: Page,
  statusBody: ReturnType<typeof status> = status({ reachable: true }),
) {
  // LIFO: catch-all first (runs last), specific routes after (run first).
  await page.route('**/*', (route) => {
    const url = route.request().url()
    if (url.includes('/api/')) {
      route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
    } else {
      route.continue()
    }
  })

  await page.route('**/api/v1/demo/scenarios', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(SCENARIOS) }),
  )
  await page.route('**/api/v1/demo/status', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(statusBody) }),
  )
  await page.route('**/api/v1/demo/chaos/**', (route) => {
    const parts = route.request().url().split('/')
    const action = parts[parts.length - 1]
    const scenario = parts[parts.length - 2]
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ scenario, action, success: true, detail: 'ok' }),
    })
  })
  await page.route('**/api/v1/demo/target', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ target_url: 'http://changed:9099' }),
    }),
  )
}

async function gotoInfra(page: Page) {
  await page.goto('/infrastructure')
  await expect(page.getByTestId('demo-panel')).toBeVisible({ timeout: 10_000 })
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe('Infrastructure — Demo / Chaos panel', () => {
  test('lists all five scenarios with Start + Heal buttons', async ({ page }) => {
    await mockDemo(page)
    await gotoInfra(page)

    for (const s of SCENARIOS.scenarios) {
      await expect(page.getByTestId(`demo-scenario-${s.id}`)).toBeVisible()
      await expect(page.getByTestId(`demo-scenario-${s.id}-start`)).toBeVisible()
      await expect(page.getByTestId(`demo-scenario-${s.id}-heal`)).toBeVisible()
    }
  })

  test('shows healthy/active status badges from /status', async ({ page }) => {
    await mockDemo(page, status({ reachable: true, active: { db_down: true } }))
    await gotoInfra(page)

    await expect(page.getByTestId('demo-scenario-db_down-badge')).toHaveText('active')
    await expect(page.getByTestId('demo-scenario-cpu_stress-badge')).toHaveText('healthy')
  })

  test('shows nextcloud / nextcloud-db container badges', async ({ page }) => {
    await mockDemo(page, status({ reachable: true, containers: { 'nextcloud-db': false } }))
    await gotoInfra(page)

    await expect(page.getByTestId('demo-container-nextcloud')).toContainText('running')
    await expect(page.getByTestId('demo-container-nextcloud-db')).toContainText('down')
  })

  test('start button POSTs chaos start and refreshes', async ({ page }) => {
    await mockDemo(page)
    let startCalled = false
    page.on('request', (req) => {
      if (req.method() === 'POST' && /\/api\/v1\/demo\/chaos\/db_down\/start$/.test(req.url())) {
        startCalled = true
      }
    })
    await gotoInfra(page)

    await page.getByTestId('demo-scenario-db_down-start').click()
    await expect.poll(() => startCalled).toBe(true)
  })

  test('unreachable agent shows an amber hint', async ({ page }) => {
    await mockDemo(page, status({ reachable: false }))
    await gotoInfra(page)

    await expect(page.getByTestId('demo-unreachable-hint')).toBeVisible()
    await expect(page.getByTestId('demo-unreachable-hint')).toContainText(/unreachable/i)
  })

  test('save target PUTs the new t3 URL', async ({ page }) => {
    await mockDemo(page)
    let putBody: string | null = null
    page.on('request', (req) => {
      if (req.method() === 'PUT' && req.url().includes('/api/v1/demo/target')) {
        putBody = req.postData()
      }
    })
    await gotoInfra(page)

    await page.getByTestId('demo-target-input').fill('http://changed:9099')
    await page.getByTestId('demo-target-save').click()
    await expect.poll(() => putBody).not.toBeNull()
    expect(putBody).toContain('http://changed:9099')
  })
})
