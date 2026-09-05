import { test, expect } from '@playwright/test'

/**
 * Live deploy smoke for the Command Center cockpit (/console) on
 * https://aiops.example.com. Inherits the logged-in storageState + Caddy
 * basic-auth from playwright.config.live.ts. Proves the three panes render
 * against the REAL backend (topology, incidents, chat).
 */
test.describe('Live — Command Center', () => {
  test('cockpit renders all three panes with real data', async ({ page }) => {
    await page.goto('/console')

    // Header + the three cockpit surfaces.
    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible()
    await expect(page.getByTestId('console-graph-pane')).toBeVisible()
    await expect(page.getByTestId('console-incidents')).toBeVisible()
    await expect(page.getByTestId('console-chat')).toBeVisible()

    // The chat composer (the piece that kept getting cut off) is on-screen.
    await expect(page.locator('[data-testid="console-chat"] form')).toBeVisible()

    // The embedded topology graph fetched REAL data: the seeded platform has
    // multiple service nodes — at least one must render.
    await expect(page.getByTestId('schema-graph-embedded')).toBeVisible({ timeout: 30_000 })
    await expect(
      page.locator('[data-testid="schema-graph-embedded"] [data-testid^="schema-node-"]').first(),
    ).toBeVisible({ timeout: 30_000 })

    await page.screenshot({ path: 'test-results/live/console-live.png' })
  })
})
