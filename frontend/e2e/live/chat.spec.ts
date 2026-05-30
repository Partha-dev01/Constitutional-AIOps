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

  // The "Thinking..." indicator appears while the request is in flight.
  await expect(page.getByText('Thinking...')).toBeVisible({ timeout: 20_000 })

  // The scoped agent must decline with its fixed redirect rather than answering
  // the geography question. Waiting for it also waits for the loading state to
  // clear and the typewriter to render the text.
  await expect(
    page.getByText(/can only help with infrastructure operations/i)
  ).toBeVisible({ timeout: 120_000 })

  // It must NOT have actually answered the off-topic question.
  await expect(page.getByText(/\bParis\b/i)).toHaveCount(0)

  // No error banner should be shown.
  await expect(page.getByText(/Please check that the backend/)).toHaveCount(0)

  // Thinking suppression: the rendered conversation must not contain raw
  // <think> tags leaking from the model.
  const conversation = await page.locator('.prose').last().innerText()
  expect(conversation).not.toContain('<think>')
})
