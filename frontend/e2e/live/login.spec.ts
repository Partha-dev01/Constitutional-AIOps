import { test, expect } from '@playwright/test'

/**
 * In-app login flow against the live deployment. Runs in a FRESH context
 * WITHOUT the shared storageState (Caddy basic-auth httpCredentials still
 * apply from the project config), so every test starts logged out.
 *
 * When the deployment runs with AUTH_REQUIRED=false set E2E_AUTH_ENFORCED=false:
 * the only meaningful assertion then is that /login never blocks anyone.
 */

const ENFORCED = (process.env.E2E_AUTH_ENFORCED ?? 'true') !== 'false'
const APP_USER = process.env.E2E_APP_USER ?? process.env.E2E_USER ?? ''
const APP_PASS = process.env.E2E_APP_PASS ?? process.env.E2E_PASS ?? ''

test.use({ storageState: { cookies: [], origins: [] } })

test('the login page renders (or auto-redirects when auth is off)', async ({ page }) => {
  await page.goto('/login')

  if (!ENFORCED) {
    // Pre-flip the page must never block: it immediately forwards to next (/).
    await expect(page).toHaveURL(/\/$/)
    return
  }

  await expect(page.getByTestId('login-heading')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
  await expect(page.getByLabel('Username')).toBeVisible()
  await expect(page.getByLabel('Password')).toBeVisible()
})

test('bad credentials show an inline error and stay on /login', async ({ page }) => {
  test.skip(!ENFORCED, 'auth not enforced: /login auto-redirects')

  await page.goto('/login')
  await page.getByLabel('Username').fill('definitely-not-a-user')
  await page.getByLabel('Password').fill('definitely-wrong-password')
  await page.getByRole('button', { name: 'Sign in' }).click()

  await expect(page.getByTestId('login-error')).toBeVisible()
  await expect(page).toHaveURL(/\/login/)
})

test('good credentials land on the dashboard; logout returns to /login', async ({ page }) => {
  test.skip(!ENFORCED, 'auth not enforced: /login auto-redirects')

  await page.goto('/login')
  await page.getByLabel('Username').fill(APP_USER)
  await page.getByLabel('Password').fill(APP_PASS)
  await page.getByRole('button', { name: 'Sign in' }).click()

  // Default next target is the root, which shows the Dashboard app shell.
  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByRole('heading', { name: 'Constitutional' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible()

  // The sidebar footer shows the signed-in identity with a Logout button.
  await page.getByRole('button', { name: 'Logout' }).click()
  await expect(page).toHaveURL(/\/login/)
})
