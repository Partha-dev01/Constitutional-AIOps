/**
 * Constitutional AIOps — Chat "approve-to-run" card E2E tests
 *
 * Mocks POST /api/v1/chat/ (trailing slash) so a chat turn carries a
 * `proposed_action`, then exercises the Approve / Reject flow against a mocked
 * POST /api/v1/chat/actions/{id}/decision. No live backend needed.
 *
 * Run (mirrors chat-tool-detail.spec.ts; baseURL :3000 by default, or :4173):
 *   npx playwright test e2e/chat-approve.spec.ts --config playwright.config.local.ts
 *   npx playwright test e2e/chat-approve.spec.ts
 *
 * NOTE: not yet listed in playwright.config.local.ts `testMatch`; the
 * integrator should add '**\/chat-approve.spec.ts' there. See report.
 *
 * The card renders only once the typewriter finishes; these tests force
 * reduced motion so the answer (and card) appear immediately.
 */

import { test, expect, Page } from '@playwright/test'

const CHAT_API = '**/api/v1/chat/'
const DECISION_API = '**/api/v1/chat/actions/*/decision'
const PLACEHOLDER = 'Ask about incidents, metrics, or request analysis...'
const QUERY = 'nextcloud is throwing 5xx, please fix it'

/** Loosely typed so spread-overrides (status/verdict/execution_result) don't
 *  get narrowed to the literal's inferred `null`/string-union types. */
type ProposedMock = Record<string, unknown>

const PROPOSED: ProposedMock = {
  id: 'act-123',
  tool_name: 'restart_service',
  parameters: { service_name: 'nextcloud', reason: 'restore the unhealthy container' },
  target: 't3',
  title: 'Restart nextcloud',
  rationale: 'The container is returning 5xx; a restart should clear the bad state.',
  mode: 'approve',
  status: 'proposed',
  verdict: { reason: 'Within policy — low-risk restart on a single service.' },
  execution_result: null,
}

function chatResponse(proposed: ProposedMock | null) {
  return {
    conversation_id: 'conv-approve-1',
    message: {
      role: 'assistant',
      content: 'I propose restarting nextcloud to clear the 5xx errors.',
      timestamp: new Date().toISOString(),
    },
    confidence: 0.88,
    suggested_actions: null,
    related_incidents: null,
    metadata: { model_used: 'qwen3-14b' },
    proposed_action: proposed,
  }
}

async function mockChat(page: Page, proposed: ProposedMock | null = PROPOSED) {
  await page.route(CHAT_API, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(chatResponse(proposed)),
    }),
  )
  await page.route('**/api/v1/chat/conversations', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [], total: 0, limit: 20, offset: 0 }),
    }),
  )
}

/** Force reduced motion so the typewriter snaps to full content immediately. */
async function gotoChat(page: Page) {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/chat')
  await expect(page.getByRole('heading', { name: 'Chat' })).toBeVisible()
}

async function ask(page: Page) {
  await page.getByPlaceholder(PLACEHOLDER).fill(QUERY)
  await page.locator('form button[type="submit"]').click()
}

test.describe('Chat — approve-to-run card', () => {
  test('proposed action renders a card with Approve + Reject', async ({ page }) => {
    await mockChat(page)
    await gotoChat(page)
    await ask(page)

    const card = page.getByTestId('proposed-action-card')
    await expect(card).toBeVisible({ timeout: 5000 })
    await expect(card).toHaveAttribute('data-status', 'proposed')
    await expect(page.getByTestId('proposed-action-approve')).toBeVisible()
    await expect(page.getByTestId('proposed-action-reject')).toBeVisible()
    await expect(card).toContainText('Restart nextcloud')
  })

  test('the card lives OUTSIDE the .prose bubble (prose text unchanged)', async ({ page }) => {
    await mockChat(page)
    await gotoChat(page)
    await ask(page)

    await expect(page.getByTestId('proposed-action-card')).toBeVisible({ timeout: 5000 })
    // The .prose body must NOT contain the card's button text.
    const proseText = await page.locator('.prose').last().innerText()
    expect(proseText).not.toContain('Approve')
    expect(proseText).not.toContain('Proposed remediation')
  })

  test('Approve → decision POST → green Executed', async ({ page }) => {
    await mockChat(page)
    let decisionBody: string | null = null
    await page.route(DECISION_API, (route) => {
      decisionBody = route.request().postData()
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          action_id: 'act-123',
          status: 'executed',
          success: true,
          error_code: null,
          verdict: null,
          result: { summary: 'nextcloud restarted; 5xx cleared.' },
        }),
      })
    })
    await gotoChat(page)
    await ask(page)

    await page.getByTestId('proposed-action-approve').click()
    const card = page.getByTestId('proposed-action-card')
    await expect(card).toHaveAttribute('data-status', 'executed', { timeout: 5000 })
    await expect(card).toContainText('Executed')
    expect(decisionBody).toContain('"approved":true')
  })

  test('Approve with error_code → red Failed showing the code', async ({ page }) => {
    await mockChat(page)
    await page.route(DECISION_API, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          action_id: 'act-123',
          status: 'refused',
          success: false,
          error_code: 'TIER1_VIOLATION',
          verdict: { reason: 'Restart would violate a safety-critical principle.' },
          result: null,
        }),
      }),
    )
    await gotoChat(page)
    await ask(page)

    await page.getByTestId('proposed-action-approve').click()
    const card = page.getByTestId('proposed-action-card')
    await expect(card).toHaveAttribute('data-status', 'error', { timeout: 5000 })
    await expect(card).toContainText('TIER1_VIOLATION')
  })

  test('Reject → muted Dismissed', async ({ page }) => {
    await mockChat(page)
    await page.route(DECISION_API, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          action_id: 'act-123',
          status: 'rejected',
          success: false,
          error_code: null,
          verdict: null,
          result: null,
        }),
      }),
    )
    await gotoChat(page)
    await ask(page)

    await page.getByTestId('proposed-action-reject').click()
    const card = page.getByTestId('proposed-action-card')
    await expect(card).toHaveAttribute('data-status', 'dismissed', { timeout: 5000 })
    await expect(card).toContainText('Dismissed')
  })

  test('auto_executed status renders a read-only Auto-remediated card (no buttons)', async ({ page }) => {
    await mockChat(page, {
      ...PROPOSED,
      status: 'auto_executed',
      execution_result: { summary: 'Auto-restarted nextcloud.' },
    })
    await gotoChat(page)
    await ask(page)

    const card = page.getByTestId('proposed-action-card')
    await expect(card).toBeVisible({ timeout: 5000 })
    await expect(card).toHaveAttribute('data-status', 'auto_executed')
    await expect(card).toContainText('Auto-remediated')
    await expect(page.getByTestId('proposed-action-approve')).toHaveCount(0)
  })

  test('blocked status renders a red card with the verdict reason (no buttons)', async ({ page }) => {
    await mockChat(page, {
      ...PROPOSED,
      status: 'blocked',
      verdict: { reason: 'Blocked: would breach the rate limit.' },
    })
    await gotoChat(page)
    await ask(page)

    const card = page.getByTestId('proposed-action-card')
    await expect(card).toBeVisible({ timeout: 5000 })
    await expect(card).toHaveAttribute('data-status', 'blocked')
    await expect(card).toContainText('rate limit')
    await expect(page.getByTestId('proposed-action-approve')).toHaveCount(0)
  })
})
