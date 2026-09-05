import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright config for end-to-end tests against the LIVE AWS deployment
 * (https://aiops.example.com) which sits behind Caddy basic-auth + TLS.
 *
 * Credentials are read from the environment ONLY — never hard-coded — because
 * this repository is public. Provide the Caddy basic-auth pair before running:
 *
 *   PowerShell:  $env:E2E_USER="admin"; $env:E2E_PASS="…"; npm run test:e2e:live
 *   bash:        E2E_USER=admin E2E_PASS=… npm run test:e2e:live
 *
 * Override the target with E2E_BASE_URL (defaults to the production domain).
 * Run headed with `npm run test:e2e:live:headed`.
 */

const BASE_URL = process.env.E2E_BASE_URL ?? 'https://aiops.example.com'
const USER = process.env.E2E_USER ?? ''
const PASS = process.env.E2E_PASS ?? ''

if (!USER || !PASS) {
  throw new Error(
    'Live e2e requires Caddy basic-auth credentials.\n' +
      'Set E2E_USER and E2E_PASS in the environment first, e.g.\n' +
      '  PowerShell:  $env:E2E_USER="admin"; $env:E2E_PASS="<pass>"; npm run test:e2e:live\n' +
      '  bash:        E2E_USER=admin E2E_PASS=<pass> npm run test:e2e:live',
  )
}

export default defineConfig({
  testDir: './e2e/live',
  outputDir: './test-results/live',
  // Logs into the in-app auth (POST /api/v1/auth/login) once and saves the
  // session cookie to the storageState below. Set E2E_AUTH_ENFORCED=false to
  // skip (an empty storage state is written instead).
  globalSetup: './e2e/live/global-setup.ts',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  timeout: 150_000,
  expect: { timeout: 15_000 },
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report-live', open: 'never' }],
  ],
  use: {
    baseURL: BASE_URL,
    // In-app session cookie captured by e2e/live/global-setup.ts. Tests that
    // need an anonymous session override this with a fresh storageState.
    storageState: 'test-results/live/.auth.json',
    httpCredentials: {
      username: USER,
      password: PASS,
      // Restrict the credentials to the target origin so they are never
      // leaked to a redirect or third-party host.
      origin: new URL(BASE_URL).origin,
    },
    ignoreHTTPSErrors: false,
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    trace: 'retain-on-failure',
    screenshot: 'on',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
