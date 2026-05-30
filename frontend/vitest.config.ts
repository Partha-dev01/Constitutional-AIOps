import { defineConfig } from 'vitest/config'

// Unit-test layer for the frontend. Uses the Node environment (the current
// suite covers pure helpers in src/lib); switch `environment` to 'jsdom' and add
// @testing-library/react when component/DOM tests are introduced.
export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    // Playwright e2e specs live under frontend/e2e — keep them out of vitest.
    exclude: ['node_modules/**', 'e2e/**', 'dist/**', 'playwright-report/**', 'test-results/**'],
  },
})
