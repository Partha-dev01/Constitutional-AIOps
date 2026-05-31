/**
 * Playwright config for LOCAL dev (no Docker, no live site).
 *
 * Starts `vite preview` (or `vite dev`) on port 4173 so tests
 * work without needing Docker or the live backend.
 * API calls are intercepted by page.route() in the specs.
 *
 * Usage:
 *   npx playwright test --config=playwright.config.local.ts --headed
 *   npx playwright test --config=playwright.config.local.ts
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  // Only run the settings spec in local mode (graph-explorer needs Docker)
  testMatch: ['**/settings.spec.ts'],
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [
    ['html', { outputFolder: 'playwright-report-local', open: 'never' }],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:4173',
    trace: 'on-first-retry',
    screenshot: 'on',
    video: 'on-first-retry',
    headless: false,  // override with --headed / PWHEADLESS=false
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run build && npm run preview -- --port 4173',
    url: 'http://localhost:4173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    stdout: 'pipe',
    stderr: 'pipe',
  },
});
