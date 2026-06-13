import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright config for the Graph "Schema mode" tests.
 * Runs against `vite preview` (prod build) on :4174 with all backend API
 * calls intercepted in the spec — mirrors playwright.config.graph.ts.
 */
export default defineConfig({
  testDir: './e2e',
  testMatch: ['**/schema-graph.spec.ts'],
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report-schema', open: 'never' }],
  ],
  use: {
    baseURL: 'http://localhost:4174',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    actionTimeout: 15000,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run preview -- --port 4174 --host',
    url: 'http://localhost:4174',
    reuseExistingServer: false,
    timeout: 30000,
  },
})
