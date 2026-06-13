import { defineConfig, devices } from '@playwright/test'

/**
 * LOCAL pre-deploy UI QA — drives the route-mocked `local-ui.spec.ts` against
 * an ALREADY-RUNNING `vite preview` of the production build at :4319.
 *
 * There is intentionally NO `webServer` block: the preview server is started
 * and owned outside of Playwright, so this config must never spawn or kill it.
 * Viewports/device ratios are driven inside the test via `page.setViewportSize`,
 * so a single chromium project is enough. Screenshots land in
 * `test-results/local-ui/`.
 */
export default defineConfig({
  testDir: './e2e',
  testMatch: 'local-ui.spec.ts',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  outputDir: 'test-results/local-ui/.pw',
  use: {
    baseURL: 'http://localhost:4319',
    screenshot: 'off',
    trace: 'off',
  },
  // ONE project; the spec resizes the page per viewport so we control ratios.
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
