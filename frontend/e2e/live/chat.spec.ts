import { test, expect } from '@playwright/test'

/**
 * Full chat round-trip against the live dual-vLLM backend. This is the most
 * end-to-end path: browser -> Caddy -> backend -> ModelRouter -> vLLM (14B
 * reasoning agent) and back. The reasoning agent is domain-scoped, so an
 * off-topic prompt must be REFUSED with its fixed redirect (not answered) —
 * which makes the round-trip deterministic. It also asserts that thinking
 * tokens are suppressed (no raw <think> bleed in the rendered answer).
 */

const PLACEHOLDER = 'Ask about incidents, metrics, or request analysis...'

test('chat refuses an off-domain prompt and renders cleanly', async ({ page }) => {
  test.slow() // the reasoning model can take a while to answer

  await page.goto('/chat')

  await expect(page.getByRole('heading', { name: 'Chat' })).toBeVisible()

  const input = page.getByPlaceholder(PLACEHOLDER)
  await input.fill('In one short sentence, what is the capital of France?')
  await page.locator('form button[type="submit"]').click()

  // The "Thinking..." indicator appears while the request is in flight. Use an
  // exact match: the revamped chat also renders an sr-only "Thinking... running
  // tools and reasoning." live-region for a11y, which a substring match would
  // ambiguously also hit.
  await expect(page.getByText('Thinking...', { exact: true })).toBeVisible({ timeout: 20_000 })

  // The scoped agent must decline rather than answering the geography question.
  // The refusal is phrased by the model in its own words (the canned redirect
  // was removed), so match the refusal INTENT, not a fixed phrase. Scope to the
  // assistant message body (.prose) — the conversation sidebar also lists past
  // chats whose titles a page-wide match would hit.
  await expect(page.locator('.prose').last()).toContainText(
    /cannot (answer|help|assist|provide)|unrelated to|not related to|outside.*(scope|domain)|only (help|assist).*(infrastructure|operations|IT)/i,
    { timeout: 120_000 }
  )

  // It must NOT have actually answered the off-topic question.
  await expect(page.getByText(/\bParis\b/i)).toHaveCount(0)

  // No error banner should be shown.
  await expect(page.getByText(/Please check that the backend/)).toHaveCount(0)

  // Thinking suppression: the rendered conversation must not contain raw
  // <think> tags leaking from the model.
  const conversation = await page.locator('.prose').last().innerText()
  expect(conversation).not.toContain('<think>')
})
