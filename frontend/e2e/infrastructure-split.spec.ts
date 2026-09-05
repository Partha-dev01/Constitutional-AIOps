/**
 * Constitutional AIOps — Infrastructure page: ours-vs-client split + remote hosts
 *
 * This test runs against a locally served Vite preview (or dev server) with all
 * API calls intercepted via Playwright route mocking.  It does NOT require a
 * live backend or a running Docker stack.
 *
 * Run with:
 *   npx playwright test e2e/infrastructure-split.spec.ts --config playwright.config.local.ts
 *
 * The test verifies:
 *  (1) Platform containers (aiops-* prefix) are shown under a "Platform (this stack)" group.
 *  (2) Other local containers are shown under a separate "Other local containers" group.
 *  (3) Monitored remote hosts (from /api/v1/infrastructure/remote-hosts) appear in a
 *      "Monitored remote hosts" section with correct status badges.
 *  (4) When no remote hosts are detected, a helpful empty-state message is shown.
 */

import { test, expect } from '@playwright/test'

// ── Shared mock data ──────────────────────────────────────────────────────────

const PLATFORM_CONTAINER = {
  name: 'aiops-backend',
  service: 'backend',
  status: 'running',
  health: 'healthy',
  port: '8000',
  image: 'constitutional-aiops-backend',
  description: 'FastAPI backend server',
  monitored: true,
}

const CLIENT_CONTAINER = {
  name: 'nextcloud',
  service: 'nextcloud',
  status: 'running',
  health: 'healthy',
  port: '8080',
  image: 'nextcloud:latest',
  description: 'nextcloud service',
  monitored: true,
}

const MOCK_CONTAINERS_RESPONSE = {
  containers: [PLATFORM_CONTAINER, CLIENT_CONTAINER],
  total: 2,
  healthy: 2,
  unhealthy: 0,
}

const MOCK_REMOTE_HOST_UP = {
  edge_label: 'prod-host-1',
  status: 'up',
  targets_up: 3,
  targets_total: 3,
  recent_log_lines: 42,
  last_seen: '2026-05-30T10:00:00Z',
}

const MOCK_REMOTE_HOSTS_RESPONSE = {
  hosts: [MOCK_REMOTE_HOST_UP],
  total: 1,
  source: 'prometheus+loki',
}

const EMPTY_REMOTE_HOSTS_RESPONSE = {
  hosts: [],
  total: 0,
  source: 'none',
}

// ── Helpers ───────────────────────────────────────────────────────────────────

async function mockAPIs(
  page: import('@playwright/test').Page,
  remoteHostsResponse: typeof MOCK_REMOTE_HOSTS_RESPONSE | typeof EMPTY_REMOTE_HOSTS_RESPONSE = MOCK_REMOTE_HOSTS_RESPONSE,
) {
  // Playwright routes fire in LIFO order (last registered = first to run).
  // Register the catch-all first so it runs last (after specific handlers).

  // 1. Catch-all: silence health, telemetry, and other non-infrastructure calls.
  await page.route('**/*', (route) => {
    const url = route.request().url()
    if (url.includes('/api/')) {
      route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
    } else {
      route.continue()
    }
  })

  // 2. Specific infrastructure routes (registered last = fired first by LIFO).
  await page.route('**/api/v1/infrastructure/remote-hosts', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(remoteHostsResponse),
    }),
  )
  await page.route('**/api/v1/infrastructure/containers', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_CONTAINERS_RESPONSE),
    }),
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe('Infrastructure page — ours-vs-client split', () => {
  test('shows Platform group for aiops-* containers', async ({ page }) => {
    await mockAPIs(page)
    await page.goto('/infrastructure')
    await page.waitForLoadState('networkidle')

    // The "Platform (this stack)" section header must be visible
    await expect(page.getByText('Platform (this stack)', { exact: false })).toBeVisible()

    // The platform container should appear under that section (heading, not the
    // "Image: constitutional-aiops-backend" line which also contains the text).
    await expect(page.getByRole('heading', { name: 'aiops-backend' })).toBeVisible()
  })

  test('shows separate group for non-aiops containers', async ({ page }) => {
    await mockAPIs(page)
    await page.goto('/infrastructure')
    await page.waitForLoadState('networkidle')

    // The "Other local containers" section header must be visible
    await expect(page.getByText('Other local containers', { exact: false })).toBeVisible()

    // The non-platform container should appear there (heading, not the Image line).
    await expect(page.getByRole('heading', { name: 'nextcloud' })).toBeVisible()
  })

  test('shows Monitored remote hosts section with up host', async ({ page }) => {
    await mockAPIs(page, MOCK_REMOTE_HOSTS_RESPONSE)
    await page.goto('/infrastructure')
    await page.waitForLoadState('networkidle')

    // Section header
    await expect(page.getByText('Monitored remote hosts', { exact: false })).toBeVisible()

    // Edge label
    await expect(page.getByText('prod-host-1')).toBeVisible()

    // Status badge
    await expect(page.getByText('up', { exact: true })).toBeVisible()
  })

  test('shows empty-state when no remote hosts detected', async ({ page }) => {
    await mockAPIs(page, EMPTY_REMOTE_HOSTS_RESPONSE)
    await page.goto('/infrastructure')
    await page.waitForLoadState('networkidle')

    await expect(page.getByText('No remote hosts detected yet', { exact: false })).toBeVisible()
  })

  test('remote host shows targets up count', async ({ page }) => {
    await mockAPIs(page, MOCK_REMOTE_HOSTS_RESPONSE)
    await page.goto('/infrastructure')
    await page.waitForLoadState('networkidle')

    await expect(page.getByText(/Targets up: 3/i)).toBeVisible()
  })

  test('remote host shows recent log line count', async ({ page }) => {
    await mockAPIs(page, MOCK_REMOTE_HOSTS_RESPONSE)
    await page.goto('/infrastructure')
    await page.waitForLoadState('networkidle')

    await expect(page.getByText(/Recent logs.*42/i)).toBeVisible()
  })
})
