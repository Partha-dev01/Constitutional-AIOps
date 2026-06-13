import { test, expect, type Page } from '@playwright/test'

/**
 * Device-ratio visual sweep — runs once PER DEVICE PROJECT defined in
 * playwright.config.live-devices.ts (each in its own correctly-sized, paced
 * window). For each device it visits the key pages, exercises the sidebar
 * (icon-rail on desktop ≥768, off-canvas drawer on mobile <768), takes a
 * full-page screenshot, and on the mobile widths asserts there is NO horizontal
 * scrollbar (flow pages must reflow to one column).
 *
 * Screenshots: test-results/live/devices/<device>__<route>.png
 */

const SHOT_DIR = 'test-results/live/devices'

const ROUTES: { path: string; slug: string; heading: RegExp }[] = [
  { path: '/', slug: 'dashboard', heading: /^Dashboard$/ },
  { path: '/console', slug: 'console', heading: /^Command Center$/ },
  { path: '/agents', slug: 'agents', heading: /^Agent Hub$/ },
  { path: '/benchmark', slug: 'benchmark', heading: /^Benchmark$/ },
  { path: '/settings', slug: 'settings', heading: /^Settings$/ },
]

/** True when the page produces a horizontal scrollbar (off-screen overflow). */
async function hasHorizontalScroll(page: Page): Promise<boolean> {
  return page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  )
}

test.describe('Device sweep', () => {
  test('key pages render at this device ratio with a working sidebar', async ({
    page,
  }, testInfo) => {
    const device = testInfo.project.name
    const width = page.viewportSize()?.width ?? 0
    const isMobile = width < 768 // matches the app's md breakpoint

    for (const route of ROUTES) {
      await page.goto(route.path)
      await expect(
        page.getByRole('heading', { name: route.heading }).first(),
      ).toBeVisible({ timeout: 30_000 })
      // Let async content (graph fetch, charts) settle before the screenshot.
      await page.waitForTimeout(1_200)

      await page.screenshot({
        path: `${SHOT_DIR}/${device}__${route.slug}.png`,
        fullPage: true,
      })

      // Mobile widths must NEVER scroll horizontally — flow pages reflow to a
      // single column. (Console is bounded too, but graph canvases on a few
      // pages can momentarily exceed by a hair; the +1px tolerance in the helper
      // absorbs sub-pixel rounding.)
      if (isMobile) {
        expect(
          await hasHorizontalScroll(page),
          `${device} ${route.path} must not scroll horizontally`,
        ).toBe(false)
      }
    }

    // ---- Exercise the sidebar for this device class. -----------------------
    await page.goto('/')
    await expect(page.getByRole('heading', { name: /^Dashboard$/ })).toBeVisible({
      timeout: 30_000,
    })

    if (isMobile) {
      // Mobile: the slim top bar's toggle opens the off-canvas drawer over the
      // backdrop; tapping the backdrop closes it.
      const mobileToggle = page.getByTestId('mobile-nav-toggle')
      await expect(mobileToggle).toBeVisible()
      await mobileToggle.click()
      // Two app-sidebar copies exist (desktop column is display:none here, the
      // drawer one is the visible one) — assert on the visible instance.
      await expect(page.getByTestId('app-sidebar').locator('visible=true')).toBeVisible()
      const backdrop = page.getByTestId('sidebar-backdrop')
      await expect(backdrop).toBeVisible()
      await page.screenshot({ path: `${SHOT_DIR}/${device}__drawer-open.png` })
      // The open drawer (w-64 = 256px) overlays the LEFT of the full-screen
      // backdrop, so a default centre-click lands on the drawer, not the dim.
      // Tap the EXPOSED dim area on the far right (where a real user taps to
      // dismiss) — `position` is relative to the backdrop's top-left box.
      const box = await backdrop.boundingBox()
      await backdrop.click({ position: { x: (box?.width ?? 360) - 10, y: 200 } })
      await expect(backdrop).toBeHidden()
    } else {
      // Desktop/tablet ≥768: the hamburger collapses the static column to an
      // icon-rail and back. Two toggle copies exist; use the visible one.
      const toggle = page.getByTestId('sidebar-toggle').locator('visible=true')
      await expect(toggle).toBeVisible()
      await toggle.click()
      await expect(page.getByRole('heading', { name: 'Constitutional' })).toBeHidden()
      await page.screenshot({ path: `${SHOT_DIR}/${device}__sidebar-rail.png` })
      await toggle.click()
      await expect(page.getByRole('heading', { name: 'Constitutional' })).toBeVisible()
    }
  })
})
