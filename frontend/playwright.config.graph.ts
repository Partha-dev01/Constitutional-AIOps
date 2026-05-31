import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright config for Graph Explorer tests.
 * Runs against `vite preview` (the prod build) on a random-ish port.
 * All backend API calls are intercepted via page.route() in the spec.
 */
export default defineConfig({
  testDir: './e2e',
  testMatch: ['**/graph.spec.ts'],
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report-graph', open: 'never' }],
  ],
  use: {
    baseURL: 'http://localhost:4173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    actionTimeout: 15000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run preview -- --port 4173 --host',
    url: 'http://localhost:4173',
    reuseExistingServer: false,
    timeout: 30000,
  },
})
