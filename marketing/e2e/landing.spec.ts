import { test, expect } from '@playwright/test'

/**
 * Marketing site tests (the standalone front-door landing).
 *
 * The landing was extracted from the app into this separate `marketing/`
 * project (R1). It is fully static: no router, no backend, no app sidebar. Its
 * CTAs point at the front-door "launch" URL (VITE_APP_URL) that wakes the demo
 * box on genuine human intent — NOT an in-app route.
 *
 * NOTE: the Playwright runner + config for the marketing site is wired in R2
 * (S3 + CloudFront deploy). Until then these assertions document the invariants;
 * the launch-URL assertion is finalised once VITE_APP_URL is set at deploy time
 * (pass the expected value as E2E_LAUNCH_URL to assert it exactly).
 */

const LAUNCH_URL = process.env.E2E_LAUNCH_URL

test('the landing hero renders without an app sidebar/nav', async ({ page }) => {
  await page.goto('/')

  // Hero heading is visible (split across nodes: "Constitutional" + "AIOps").
  // Scope to the H1 hero — a feature card lower on the page is an <h3>
  // "Constitutional AI Safety", so an unscoped match is ambiguous.
  await expect(page.getByRole('heading', { level: 1, name: /Constitutional/ })).toBeVisible()

  // The marketing site is a non-app surface: it has NO <nav> (the LandingHeader
  // is deliberately a <header>, not a <nav>) and none of the app sidebar chrome.
  await expect(page.locator('nav')).toHaveCount(0)
  await expect(page.getByText('System Healthy')).toHaveCount(0)
  await expect(page.getByText('System Degraded')).toHaveCount(0)
})

test('the primary CTA points at the launch URL, not an in-app route', async ({ page }) => {
  await page.goto('/')

  // Two "Open the Dashboard" CTAs (hero + footer); the first is the hero CTA.
  const cta = page.getByRole('link', { name: 'Open the Dashboard' }).first()
  const href = await cta.getAttribute('href')
  expect(href, 'the hero CTA must carry an href').toBeTruthy()
  if (LAUNCH_URL) {
    expect(href).toBe(LAUNCH_URL)
  }
})
