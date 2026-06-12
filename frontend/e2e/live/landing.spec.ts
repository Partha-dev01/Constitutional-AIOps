import { test, expect } from '@playwright/test'

/**
 * Public landing page tests against the live deployment. The landing now
 * lives at the PUBLIC ROOT (/): logged-out visitors (with enforcement on)
 * see it instead of the dashboard, and /welcome permanently redirects to /.
 *
 * Runs in a fresh context WITHOUT the shared storageState so the visitor is
 * genuinely logged out (Caddy basic-auth httpCredentials still apply).
 * It makes no backend-dependent assertions beyond routing.
 */

const ENFORCED = (process.env.E2E_AUTH_ENFORCED ?? 'true') !== 'false'

test.use({ storageState: { cookies: [], origins: [] } })

test('the landing hero renders at / without the app sidebar', async ({ page }) => {
  test.skip(!ENFORCED, 'auth not enforced: / shows the dashboard, not the landing')

  await page.goto('/')

  // Hero heading is visible (split across nodes: "Constitutional" + "AIOps").
  // Scope to the H1 hero — a feature card lower on the page is an <h3>
  // "Constitutional AI Safety", so an unscoped match is ambiguous.
  await expect(page.getByRole('heading', { level: 1, name: /Constitutional/ })).toBeVisible()

  // The Layout (sidebar) is absent for logged-out visitors: the sidebar
  // renders the app navigation inside a <nav>, and the only <nav> in the app
  // lives in Layout.
  await expect(page.locator('nav')).toHaveCount(0)

  // The sidebar-only health footer text must not be present either.
  await expect(page.getByText('System Healthy')).toHaveCount(0)
  await expect(page.getByText('System Degraded')).toHaveCount(0)
})

test('the primary CTA routes through the login page', async ({ page }) => {
  await page.goto('/')

  if (!ENFORCED) {
    // Enforcement off: the root IS the dashboard already; there is no landing
    // CTA to click and nothing to log into.
    await expect(page).toHaveURL(/\/$/)
    await expect(page.getByRole('heading', { name: 'Constitutional' })).toBeVisible()
    return
  }

  // There are two "Open the Dashboard" links (hero + footer); the first is the
  // primary hero CTA. It now points at the login page, carrying / as next.
  const cta = page.getByRole('link', { name: 'Open the Dashboard' }).first()
  await expect(cta).toHaveAttribute('href', /\/login\?next=(\/|%2F)$/)
  await cta.click()

  await expect(page).toHaveURL(/\/login/)
})

test('/welcome redirects to the public root', async ({ page }) => {
  await page.goto('/welcome')
  await expect(page).toHaveURL(/\/$/)
})
