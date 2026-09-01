import { defineConfig, devices } from '@playwright/test'

/**
 * Setup-wizard e2e — walks the guided /setup wizard end to end against a
 * fully route-mocked backend (no server needed). Playwright owns a `vite
 * preview` of the production build, so run `npm run build` first. Headless
 * chromium, single worker.
 */
export default defineConfig({
  testDir: './e2e',
  testMatch: 'setup-wizard.spec.ts',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  outputDir: 'test-results/setup-wizard/.pw',
  use: {
    baseURL: 'http://localhost:4320',
    screenshot: 'off',
    trace: 'off',
  },
  webServer: {
    command: 'npm run preview -- --port 4320 --strictPort',
    url: 'http://localhost:4320',
    timeout: 120_000,
    reuseExistingServer: !process.env.CI,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
