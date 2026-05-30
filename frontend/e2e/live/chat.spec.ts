import { test, expect } from '@playwright/test'

/**
 * Full chat round-trip against the live dual-vLLM backend. This is the most
 * end-to-end path: browser -> Caddy -> backend -> ModelRouter -> vLLM (14B
 * reasoning agent) and back. It also asserts that thinking tokens are
 * suppressed (no raw <think> bleed in the rendered answer).
 */

const PLACEHOLDER = 'Ask about incidents, metrics, or request analysis...'

test('chat sends a message and renders a model response', async ({ page }) => {
  test.slow() // the reasoning model can take a while to answer

  await page.goto('/chat')

  await expect(page.getByRole('heading', { name: 'Chat' })).toBeVisible()

  const input = page.getByPlaceholder(PLACEHOLDER)
  await input.fill('In one short sentence, what is the capital of France?')
  await page.locator('form button[type="submit"]').click()

  // The "Thinking..." indicator appears while the request is in flight.
  await expect(page.getByText('Thinking...')).toBeVisible({ timeout: 20_000 })

  // The answer for this prompt is essentially deterministic. Waiting for it
  // also implicitly waits for the loading state to clear and the typewriter
  // to render the text.
  await expect(page.getByText(/Paris/i)).toBeVisible({ timeout: 120_000 })

  // No error banner should be shown.
  await expect(page.getByText(/Please check that the backend/)).toHaveCount(0)

  // Thinking suppression: the rendered conversation must not contain raw
  // <think> tags leaking from the model.
  const conversation = await page.locator('.prose').last().innerText()
  expect(conversation).not.toContain('<think>')
})
