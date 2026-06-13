/**
 * Playwright config for LOCAL testing (no Docker, no live site).
 *
 * Starts `vite preview` on port 4173. The specs targeted here mock every API
 * call via page.route(), so no live backend is required. Run headed by adding
 * `--headed` (e.g. for the Settings param sweep).
 *
 * Scope: the mock-based local specs only. The graph explorer has its own config
 * (playwright.config.graph.ts) and the live e2e suite uses playwright.config.live.ts.
 *
 * Usage:
 *   npx playwright test --config=playwright.config.local.ts
 *   npx playwright test --config=playwright.config.local.ts --headed
 */
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testMatch: [
    '**/settings.spec.ts',
    '**/infrastructure-split.spec.ts',
    '**/chat-tool-detail.spec.ts',
    '**/mcp-tools.spec.ts',
    '**/demo-panel.spec.ts',
    '**/remediation-settings.spec.ts',
    '**/chat-approve.spec.ts',
  ],
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
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
})
