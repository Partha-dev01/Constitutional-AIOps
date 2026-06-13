import { defineConfig } from '@playwright/test'
import liveConfig from './playwright.config.live'

/**
 * Device-ratio HEADED visual sweep against the LIVE site
 * (https://aiops.imaginaerium.in). Reuses the live config's auth wiring
 * verbatim — the same `use` block (Caddy basic-auth via httpCredentials +
 * in-app session storageState), the same globalSetup login, and the same
 * E2E_* env contract. Credentials still come ONLY from the environment.
 *
 * The point of this config (per the user's complaint that headed runs were
 * "too fast and not properly scaled") is that each device runs in a REAL,
 * correctly-sized OS window:
 *   - launchOptions.slowMo = 600ms so the actions are watchable;
 *   - launchOptions.args sets --window-size to the device W×H and pins the
 *     window to the top-left so the visible window IS the device ratio;
 *   - viewport is set to the SAME W×H so the page renders at that scale.
 *
 * Run it HEADED:
 *   E2E_USER=… E2E_PASS=… E2E_APP_USER=… E2E_APP_PASS=… \
 *     npx playwright test --config=playwright.config.live-devices.ts --headed
 */

interface Device {
  name: string
  width: number
  height: number
}

const DEVICES: Device[] = [
  { name: 'desktop', width: 1920, height: 1080 },
  { name: 'laptop', width: 1440, height: 900 },
  { name: 'laptop-short', width: 1366, height: 640 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'mobile', width: 390, height: 844 },
  { name: 'mobile-small', width: 360, height: 740 },
]

export default defineConfig({
  testDir: './e2e/live',
  outputDir: './test-results/live/devices-output',
  // Same login step as the live suite — writes the shared storageState the
  // `use` block (inherited below) reads.
  globalSetup: './e2e/live/global-setup.ts',
  testMatch: /devices\.spec\.ts$/,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  // ONE worker so the headed windows never fight for the screen (past sessions
  // crashed running concurrent headed Playwright).
  workers: 1,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: [['list']],
  use: {
    // Reuse the live config's entire `use` block: baseURL, storageState,
    // httpCredentials (origin-scoped), trace/screenshot/video settings.
    ...liveConfig.use,
  },
  projects: DEVICES.map((d) => ({
    name: d.name,
    use: {
      ...liveConfig.use,
      viewport: { width: d.width, height: d.height },
      launchOptions: {
        slowMo: 600,
        args: [`--window-size=${d.width},${d.height}`, '--window-position=0,0'],
      },
    },
  })),
})
