import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright config for the graph topology-update validation.
 * Runs BOTH the existing graph interaction suite (graph.spec.ts) and the new
 * update suite (graph-topology-update.spec.ts) against `vite preview` (prod
 * build) on localhost:4173. All backend calls are intercepted in the specs.
 */
export default defineConfig({
  testDir: './e2e',
  testMatch: ['**/graph.spec.ts', '**/graph-topology-update.spec.ts'],
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:4173',
    trace: 'off',
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
