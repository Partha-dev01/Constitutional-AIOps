import { test, expect } from '@playwright/test'

/**
 * Smoke tests against the live deployment: the SPA loads through Caddy
 * (basic-auth handled by httpCredentials), every route renders, and the
 * frontend successfully talks to the backend (health footer turns healthy).
 */

const ROUTES = [
  { path: '/', name: 'Dashboard' },
  { path: '/agents', name: 'Agents' },
  { path: '/incidents', name: 'Incidents' },
  { path: '/chat', name: 'Chat' },
  { path: '/metrics', name: 'Metrics' },
  { path: '/benchmark', name: 'Benchmark' },
  { path: '/settings', name: 'Settings' },
]

test('SPA loads and the sidebar renders', async ({ page }) => {
  await page.goto('/')
  // Brand in the sidebar header
  await expect(page.getByRole('heading', { name: 'Constitutional' })).toBeVisible()
  // All nav links are present
  for (const route of ROUTES) {
    await expect(page.getByRole('link', { name: route.name })).toBeVisible()
  }
})

test('every route is reachable via sidebar navigation', async ({ page }) => {
  await page.goto('/')
  for (const route of ROUTES) {
    await page.getByRole('link', { name: route.name }).click()
    await expect(page).toHaveURL(new RegExp(`${route.path === '/' ? '/$' : route.path}`))
    // Each page renders at least one heading
    await expect(page.locator('h1').first()).toBeVisible()
  }
})

test('system health footer reports the backend as healthy', async ({ page }) => {
  await page.goto('/')
  // The Layout polls /api/v1/health on mount; a healthy live backend flips
  // the footer text. This proves frontend -> Caddy -> backend wiring works.
  // The sidebar markup renders twice (desktop column + mobile drawer); at the
  // desktop gate viewport the mobile copy is display:none, so scope to the
  // VISIBLE footer to avoid a strict-mode match on both.
  await expect(page.locator('span:visible', { hasText: 'System Healthy' })).toBeVisible({
    timeout: 30_000,
  })
  // The agent status lines split text across nodes ("Fast Agent: ● Online"),
  // so assert against the combined text of their (visible) container.
  const agentStatus = page.locator('div:visible', { hasText: 'Fast Agent:' }).last()
  await expect(agentStatus).toContainText('Fast Agent:')
  await expect(agentStatus).toContainText('Reasoning Agent:')
  await expect(agentStatus).toContainText('Online')
  await expect(agentStatus).not.toContainText('Offline')
})
