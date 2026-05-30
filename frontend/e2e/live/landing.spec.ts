import { test, expect } from '@playwright/test'

/**
 * Landing page (/welcome) tests against the live deployment. The landing page
 * is rendered OUTSIDE the sidebar Layout, so it must NOT show the app sidebar.
 * It makes no network calls, so these assertions are deterministic and do not
 * depend on backend health or on any screenshots being present.
 */

test('the welcome hero renders without the app sidebar', async ({ page }) => {
  await page.goto('/welcome')

  // Hero heading is visible (split across nodes: "Constitutional" + "AIOps").
  // Scope to the H1 hero — a feature card lower on the page is an <h3>
  // "Constitutional AI Safety", so an unscoped match is ambiguous.
  await expect(page.getByRole('heading', { level: 1, name: /Constitutional/ })).toBeVisible()

  // The Layout (sidebar) is absent on /welcome: the sidebar renders the app
  // navigation inside a <nav>, and the only <nav> in the app lives in Layout.
  await expect(page.locator('nav')).toHaveCount(0)

  // The sidebar-only health footer text must not be present either.
  await expect(page.getByText('System Healthy')).toHaveCount(0)
  await expect(page.getByText('System Degraded')).toHaveCount(0)
})

test('the primary CTA navigates into the authed dashboard', async ({ page }) => {
  await page.goto('/welcome')

  // There are two "Open the Dashboard" links (hero + footer); the first is the
  // primary hero CTA.
  await page.getByRole('link', { name: 'Open the Dashboard' }).first().click()

  // URL becomes the dashboard root.
  await expect(page).toHaveURL(/\/$/)

  // The Layout brand heading appears, proving navigation landed in the app shell.
  await expect(page.getByRole('heading', { name: 'Constitutional' })).toBeVisible()
})
