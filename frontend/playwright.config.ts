import { defineConfig, devices } from '@playwright/test';

/**
 * Constitutional AIOps - Playwright E2E Testing Configuration
 *
 * Tests for:
 * - Graph Explorer visualization
 * - Edge filtering and controls
 * - DAG/Force layout modes
 * - Node interactions
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:3000',  // Docker frontend
    trace: 'on-first-retry',
    screenshot: 'on',  // Always take screenshots for debugging
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // Don't start a webServer since Docker is running the frontend
});
