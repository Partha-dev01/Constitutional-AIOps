import { test, expect, type Page } from '@playwright/test'

/**
 * Setup wizard e2e: walk all seven steps end to end against a route-mocked
 * backend, assert onboarding is marked complete, and assert the skip path
 * leaves the wizard without looping back into it.
 */

type Onboarding = { completed: boolean; skipped: boolean; step: number }

const generatedSchema = {
  preview: true,
  nodes: [
    { id: 'backend', label: 'backend', kind: 'backend', tier: 2 },
    { id: 'nextcloud', label: 'nextcloud', kind: 'backend', tier: 2 },
  ],
  edges: [] as Array<{ source: string; target: string; relationship: string; kind: string }>,
  note: 'Generated from your services.',
}

const liveSchema = {
  mode: 'discovered' as const,
  nodes: generatedSchema.nodes,
  edges: generatedSchema.edges,
}

const containers = {
  containers: [
    { name: 'aiops-backend', service: 'aiops-backend', status: 'running', health: 'healthy', port: null, image: null, description: null, monitored: true },
    { name: 'nextcloud', service: 'nextcloud', status: 'running', health: 'healthy', port: null, image: null, description: null, monitored: true },
  ],
  total: 2,
  healthy: 2,
  unhealthy: 0,
}

const models = {
  fastAgentUrl: 'http://fast:8000/v1',
  fastAgentModel: 'qwen3-4b',
  reasoningAgentUrl: 'http://reason:8001/v1',
  reasoningAgentModel: 'qwen3-14b',
  fastApiKeySet: false,
  reasoningApiKeySet: false,
}

const allSettings = {
  constitutional: {},
  notifications: {},
  telemetry: {
    lokiEnabled: false,
    lokiUrl: '',
    prometheusEnabled: false,
    prometheusUrl: '',
    tempoEnabled: false,
    tempoUrl: '',
    retentionDays: 30,
  },
  remediation: {},
}

const reasoningPrompt = {
  name: 'reasoning_chat',
  description: 'Reasoning Agent - Human Chat Interface',
  prompt: 'You are an intelligent AIOps assistant helping infrastructure operators.',
  agent: 'reasoning',
  editable: true,
}

interface MockState {
  onboarding: Onboarding
}

async function mockWizard(page: Page, state: MockState) {
  await page.route('**/api/v1/**', async (route) => {
    const req = route.request()
    const url = req.url()
    const method = req.method()
    const json = (body: unknown, status = 200) =>
      route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })

    if (url.includes('/auth/config')) return json({ auth_required: false })
    if (url.includes('/auth/me')) return json({}, 401)
    if (url.includes('/health')) return json({ status: 'healthy', components: [] })

    // Onboarding is stateful so the walk's final PUT is observable.
    if (url.includes('/settings/onboarding')) {
      if (method === 'PUT') {
        state.onboarding = { ...state.onboarding, ...(req.postDataJSON() as Onboarding) }
        return json(state.onboarding)
      }
      return json(state.onboarding)
    }
    if (url.includes('/settings/models/test'))
      return json({ fast_agent: true, reasoning_agent: true })
    if (url.includes('/settings/models')) return json(models)
    if (url.includes('/settings/monitoring/test'))
      return json({
        loki: { ok: true, detail: 'ready' },
        prometheus: { ok: true, detail: 'healthy' },
        tempo: null,
      })
    if (url.includes('/settings')) {
      if (method === 'PUT') return json(req.postDataJSON())
      return json(allSettings)
    }

    if (url.includes('/infrastructure/containers')) return json(containers)

    if (url.includes('/topology/generate')) return json(generatedSchema)
    if (url.includes('/topology/schema')) {
      if (method === 'PUT') {
        const b = req.postDataJSON() as { nodes: unknown[]; edges: unknown[] }
        return json({ mode: 'custom', nodes: b.nodes, edges: b.edges })
      }
      return json(liveSchema)
    }

    if (url.includes('/prompts/generate'))
      return json({
        prompt: 'Drafted base prompt describing the platform services and their topology.',
        note: '',
      })
    if (url.includes('/prompts/reasoning_chat')) {
      if (method === 'PUT') {
        const b = req.postDataJSON() as { prompt: string }
        return json({ ...reasoningPrompt, prompt: b.prompt })
      }
      return json(reasoningPrompt)
    }

    // Catch-all so nothing hangs (dashboard lands after finish).
    return json({ items: [], total: 0 })
  })
}

test.describe('Setup wizard', () => {
  test('walks all steps and marks onboarding complete', async ({ page }) => {
    const state: MockState = { onboarding: { completed: false, skipped: false, step: 0 } }
    await mockWizard(page, state)

    await page.goto('/setup')

    // Welcome
    await expect(page.getByRole('heading', { name: 'Welcome', exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'Start setup', exact: true }).click()

    // Services — prefilled from live containers
    await expect(page.getByRole('heading', { name: 'Services', exact: true })).toBeVisible()
    await expect(page.getByPlaceholder('checkout-api').first()).toHaveValue('backend')
    await page.getByRole('button', { name: 'Next', exact: true }).click()

    // Topology — generate from services, then apply
    await expect(page.getByRole('heading', { name: 'Topology', exact: true })).toBeVisible()
    await page.getByTestId('topology-generate-from-services').click()
    await expect(page.getByTestId('topology-preview-badge')).toBeVisible()
    await page.getByTestId('topology-apply').click()
    await expect(page.getByText('Topology applied', { exact: false })).toBeVisible()
    await page.getByRole('button', { name: 'Next', exact: true }).click()

    // Base prompt — draft, then save
    await expect(page.getByRole('heading', { name: 'Base prompt', exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'Draft from services + topology' }).click()
    await page.getByRole('button', { name: 'Save as assistant prompt' }).click()
    await expect(page.getByText('Saved as the assistant base prompt.')).toBeVisible()
    await page.getByRole('button', { name: 'Next', exact: true }).click()

    // LLM — save endpoint
    await expect(page.getByRole('heading', { name: 'LLM endpoint', exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'Save endpoint' }).click()
    await expect(page.getByText('Saved. The assistant now uses this endpoint.')).toBeVisible()
    await page.getByRole('button', { name: 'Next', exact: true }).click()

    // Monitoring
    await expect(page.getByRole('heading', { name: 'Monitoring', exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'Next', exact: true }).click()

    // Finish
    await expect(page.getByRole('heading', { name: 'Finish', exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'Finish', exact: true }).click()

    // Landed back in the app; onboarding marked complete.
    await expect(page).toHaveURL(/\/$/)
    expect(state.onboarding.completed).toBe(true)
  })

  test('skip leaves the wizard and does not loop back', async ({ page }) => {
    const state: MockState = { onboarding: { completed: false, skipped: false, step: 0 } }
    await mockWizard(page, state)

    await page.goto('/setup')
    await expect(page.getByRole('heading', { name: 'Welcome', exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'Skip setup', exact: true }).click()

    await expect(page).toHaveURL(/\/$/)
    await page.waitForTimeout(500)
    await expect(page).not.toHaveURL(/\/setup$/)
    expect(state.onboarding.skipped).toBe(true)
  })
})
