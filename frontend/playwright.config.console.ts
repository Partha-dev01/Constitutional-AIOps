import { defineConfig, devices } from '@playwright/test'

/**
 * Console (Command Center) layout verification — runs the route-mocked
 * `console-layout.spec.ts` against a local `vite preview` of the production
 * build, capturing screenshots across device ratios (incl. reduced heights
 * that mimic a browser with tabs/bookmarks/devtools open). Deploy-free.
 */
export default defineConfig({
  testDir: './e2e',
  testMatch: 'console-layout.spec.ts',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:4178',
    screenshot: 'off',
    trace: 'off',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run preview -- --port 4178 --strictPort',
    url: 'http://localhost:4178',
    reuseExistingServer: true,
    timeout: 60_000,
  },
})
