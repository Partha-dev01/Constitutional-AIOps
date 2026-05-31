import { test, expect } from '@playwright/test'

/**
 * Tool-call timeline dropdown tests.
 *
 * Mocks POST /api/v1/chat/ (trailing slash) so no live backend is needed.
 * The mock returns a response that includes related_incidents + metadata so
 * that enriched step results are surfaced in the dropdown detail panels.
 *
 * Run against local vite dev/preview (baseURL http://localhost:3000).
 *
 * NOTE: result-enrichment tests (INC-2024-001 / model name) are handled by
 * the vitest unit test (`src/hooks/useToolSteps.test.ts`) because the
 * post-response 3-second cleanup window is hard to time reliably in
 * browser-level E2E tests. The Playwright suite focuses on structural
 * properties: Thinking…, expand/collapse, aria, type=button contract.
 */

const CHAT_API = '**/api/v1/chat/'
const PLACEHOLDER = 'Ask about incidents, metrics, or request analysis...'

/** A query that triggers all four derived steps (service + similar + dependency + log). */
const QUERY = 'show similar incidents for nextcloud and check its error log dependencies'

const MOCK_RESPONSE = {
  conversation_id: 'test-conv-1',
  message: {
    role: 'assistant',
    content: 'I found 2 similar past incidents for nextcloud. The dependency graph shows upstream: loki, downstream: grafana. Recent error logs show connection timeouts.',
    timestamp: new Date().toISOString(),
  },
  confidence: 0.87,
  suggested_actions: ['Restart nextcloud container', 'Check loki connectivity'],
  related_incidents: ['INC-2024-001', 'INC-2024-042'],
  metadata: {
    model_used: 'qwen3-14b',
    tokens_used: 412,
  },
}

/** Slow mock — delays response by `ms` milliseconds. */
function slowMock(ms: number) {
  return async (route: import('@playwright/test').Route) => {
    await new Promise<void>((r) => setTimeout(r, ms))
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_RESPONSE),
    })
  }
}

const fastMock = async (route: import('@playwright/test').Route) => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(MOCK_RESPONSE),
  })
}

test.describe('Chat tool-call timeline dropdown', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept the chat API endpoint — note trailing slash (required contract).
    await page.route(CHAT_API, fastMock)

    // Also stub conversation list so the sidebar doesn't throw.
    await page.route('**/api/v1/chat/conversations', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, limit: 20, offset: 0 }),
      })
    })

    await page.goto('/chat')
    await expect(page.getByRole('heading', { name: 'Chat' })).toBeVisible()
  })

  test('timeline appears while loading and shows Thinking...', async ({ page }) => {
    // Use a slow mock so we can observe the in-flight state.
    await page.route(CHAT_API, slowMock(500))

    const input = page.getByPlaceholder(PLACEHOLDER)
    await input.fill(QUERY)
    await page.locator('form button[type="submit"]').click()

    // The exact "Thinking..." text must appear (contract).
    await expect(page.getByText('Thinking...', { exact: true })).toBeVisible({ timeout: 5_000 })
  })

  test('step detail dropdowns expand and show service/store/query fields', async ({ page }) => {
    await page.route(CHAT_API, slowMock(2_500))

    const input = page.getByPlaceholder(PLACEHOLDER)
    await input.fill(QUERY)
    await page.locator('form button[type="submit"]').click()

    // Wait for the timeline to appear.
    await expect(page.getByText('Thinking...', { exact: true })).toBeVisible({ timeout: 5_000 })

    // The "similar" step should be visible. Click its expand toggle.
    const similarToggle = page.getByTestId('step-toggle-similar')
    await expect(similarToggle).toBeVisible({ timeout: 5_000 })
    await similarToggle.click()

    // Detail panel should now be open with aria-expanded="true".
    await expect(similarToggle).toHaveAttribute('aria-expanded', 'true')

    // The detail region should show static fields (store, query).
    const similarDetail = page.getByTestId('step-detail-similar')
    await expect(similarDetail).toBeVisible()
    await expect(similarDetail).toContainText('Neo4j')
    await expect(similarDetail).toContainText('find_similar')
    await expect(similarDetail).toContainText('nextcloud')

    // Collapsing should hide the detail.
    await similarToggle.click()
    await expect(similarToggle).toHaveAttribute('aria-expanded', 'false')
    await expect(page.getByTestId('step-detail-similar')).toHaveCount(0)
  })

  test('reasoning step detail shows store and query text', async ({ page }) => {
    await page.route(CHAT_API, slowMock(2_500))

    const input = page.getByPlaceholder(PLACEHOLDER)
    await input.fill(QUERY)
    await page.locator('form button[type="submit"]').click()

    await expect(page.getByText('Thinking...', { exact: true })).toBeVisible({ timeout: 5_000 })

    const reasoningToggle = page.getByTestId('step-toggle-reasoning')
    await expect(reasoningToggle).toBeVisible({ timeout: 5_000 })
    await reasoningToggle.click()

    const detail = page.getByTestId('step-detail-reasoning')
    await expect(detail).toBeVisible()
    // Static fields are always present.
    await expect(detail).toContainText('vLLM')
    await expect(detail).toContainText('Qwen3-14B')
    await expect(detail).toContainText('Store:')
    await expect(detail).toContainText('Query:')
  })

  test('toggle buttons are type="button" (not submit)', async ({ page }) => {
    await page.route(CHAT_API, slowMock(2_500))

    const input = page.getByPlaceholder(PLACEHOLDER)
    await input.fill(QUERY)
    await page.locator('form button[type="submit"]').click()

    await expect(page.getByText('Thinking...', { exact: true })).toBeVisible({ timeout: 5_000 })

    // All step-toggle buttons must have type="button", not "submit".
    const allToggles = page.locator('[data-testid^="step-toggle-"]')
    const count = await allToggles.count()
    expect(count).toBeGreaterThan(0)
    for (let i = 0; i < count; i++) {
      await expect(allToggles.nth(i)).toHaveAttribute('type', 'button')
    }
  })

  test('chat.spec contract: h1 Chat + placeholder + Thinking... remain intact', async ({
    page,
  }) => {
    // H1 must say "Chat".
    await expect(page.getByRole('heading', { name: 'Chat' })).toBeVisible()

    // Placeholder text exact match.
    await expect(page.getByPlaceholder(PLACEHOLDER)).toBeVisible()

    // Only the form submit button should be type="submit".
    const submitButtons = page.locator('form button[type="submit"]')
    await expect(submitButtons).toHaveCount(1)

    // Thinking... appears in-flight.
    await page.route(CHAT_API, slowMock(500))

    const input = page.getByPlaceholder(PLACEHOLDER)
    await input.fill('nextcloud error logs')
    await page.locator('form button[type="submit"]').click()

    await expect(page.getByText('Thinking...', { exact: true })).toBeVisible({ timeout: 5_000 })

    // After response, .prose content must NOT include the dropdown content
    // (no prose class on detail panels — contract).
    await expect(page.locator('.prose').last()).toBeVisible({ timeout: 10_000 })
    const detailPanels = page.locator('.prose [data-testid^="step-detail-"]')
    await expect(detailPanels).toHaveCount(0)
  })

  test('multiple steps can be expanded independently', async ({ page }) => {
    await page.route(CHAT_API, slowMock(2_500))

    const input = page.getByPlaceholder(PLACEHOLDER)
    await input.fill(QUERY)
    await page.locator('form button[type="submit"]').click()

    await expect(page.getByText('Thinking...', { exact: true })).toBeVisible({ timeout: 5_000 })

    // Expand both telemetry and similar steps.
    const telemetryToggle = page.getByTestId('step-toggle-telemetry')
    await expect(telemetryToggle).toBeVisible({ timeout: 5_000 })
    await telemetryToggle.click()
    await expect(telemetryToggle).toHaveAttribute('aria-expanded', 'true')

    const similarToggle = page.getByTestId('step-toggle-similar')
    await similarToggle.click()
    await expect(similarToggle).toHaveAttribute('aria-expanded', 'true')

    // Both detail panels should be visible simultaneously.
    await expect(page.getByTestId('step-detail-telemetry')).toBeVisible()
    await expect(page.getByTestId('step-detail-similar')).toBeVisible()

    // Telemetry detail shows Loki + Prometheus.
    await expect(page.getByTestId('step-detail-telemetry')).toContainText('Loki')
    await expect(page.getByTestId('step-detail-telemetry')).toContainText('Prometheus')
  })
})
