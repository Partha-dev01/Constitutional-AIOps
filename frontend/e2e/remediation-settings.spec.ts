/**
 * Constitutional AIOps — Settings "Remediation" tab E2E tests
 *
 * Runs against a locally served Vite preview/dev server with every API call
 * intercepted via Playwright route mocking. No live backend needed.
 *
 * Run (mirrors settings.spec.ts):
 *   npx playwright test e2e/remediation-settings.spec.ts --config playwright.config.local.ts
 * (or, against a Docker frontend on :3000)
 *   npx playwright test e2e/remediation-settings.spec.ts
 *
 * NOTE: not yet listed in playwright.config.local.ts `testMatch`; the
 * integrator should add '**\/remediation-settings.spec.ts' there. See report.
 */

import { test, expect, Page } from '@playwright/test'

const DEFAULT_SETTINGS = {
  constitutional: {
    autoThreshold: 90,
    approvalThreshold: 70,
    maxActionsPerMinute: 10,
    enableAuditLog: true,
    enableLearning: true,
    strictTier1: true,
  },
  notifications: {
    emailEnabled: false,
    slackEnabled: false,
    webhookEnabled: false,
    webhookUrl: '',
    notifyOnCritical: true,
    notifyOnApproval: true,
    notifyOnResolution: false,
  },
  telemetry: {
    lokiEnabled: true,
    lokiUrl: 'http://loki:3100',
    prometheusEnabled: true,
    prometheusUrl: 'http://prometheus:9090',
    tempoEnabled: true,
    tempoUrl: 'http://tempo:3200',
    retentionDays: 30,
  },
  remediation: {
    mode: 'diagnose',
    autoConfidenceThreshold: 90,
    requireEvidenceForAuto: true,
    demoTargetUrl: 'http://t3:9099',
  },
}

const MOCK_HEALTH = {
  status: 'healthy',
  components: [
    { name: 'fast_agent', healthy: true },
    { name: 'reasoning_agent', healthy: true },
  ],
}

async function mockApis(page: Page) {
  let current = JSON.parse(JSON.stringify(DEFAULT_SETTINGS))

  // Auth disabled so bootstrap doesn't fail safe to /login.
  await page.route('**/auth/config**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ auth_required: false, signup_enabled: false, captcha_provider: '', captcha_site_key: '' }) }),
  )

  await page.route('**/api/v1/health', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_HEALTH) }),
  )

  await page.route('**/api/v1/settings/', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(current) })
    } else if (route.request().method() === 'PUT') {
      const body = JSON.parse(route.request().postData() ?? '{}')
      current = { ...current, ...body }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(current) })
    }
  })
}

async function gotoRemediation(page: Page) {
  await page.goto('/settings')
  await page.waitForSelector('h1:has-text("Settings")', { timeout: 10_000 })
  await page.locator('button:has-text("Remediation")').click()
  await expect(page.locator('h2:has-text("Remediation Mode")')).toBeVisible()
}

test.describe('Settings — Remediation tab', () => {
  test.beforeEach(async ({ page }) => {
    await mockApis(page)
    await gotoRemediation(page)
  })

  test('mode selector switches between the three modes', async ({ page }) => {
    const diagnose = page.getByTestId('remediation-mode-diagnose')
    const approve = page.getByTestId('remediation-mode-approve')
    const auto = page.getByTestId('remediation-mode-auto')

    await expect(diagnose).toHaveAttribute('aria-checked', 'true')

    await approve.click()
    await expect(approve).toHaveAttribute('aria-checked', 'true')
    await expect(diagnose).toHaveAttribute('aria-checked', 'false')

    await auto.click()
    await expect(auto).toHaveAttribute('aria-checked', 'true')
  })

  test('helper text changes with the selected mode', async ({ page }) => {
    const help = page.getByTestId('remediation-mode-help')
    await expect(help).toContainText(/Diagnose only/i)

    await page.getByTestId('remediation-mode-approve').click()
    await expect(help).toContainText(/Approve to run/i)

    await page.getByTestId('remediation-mode-auto').click()
    await expect(help).toContainText(/Auto-remediate/i)
  })

  test('confidence slider + evidence toggle are disabled unless mode=auto', async ({ page }) => {
    const slider = page.getByTestId('remediation-confidence')
    const evidence = page.getByTestId('remediation-evidence')

    // diagnose (default): disabled
    await expect(slider).toBeDisabled()
    await expect(evidence).toBeDisabled()

    // auto: enabled
    await page.getByTestId('remediation-mode-auto').click()
    await expect(slider).toBeEnabled()
    await expect(evidence).toBeEnabled()
  })

  test('confidence slider updates its value label (in auto mode)', async ({ page }) => {
    await page.getByTestId('remediation-mode-auto').click()
    const slider = page.getByTestId('remediation-confidence')
    await slider.fill('95')
    await expect(page.getByTestId('remediation-confidence-value')).toHaveText('95%')
  })

  test('demo target URL field is editable', async ({ page }) => {
    const input = page.getByTestId('remediation-demo-target')
    await expect(input).toHaveValue('http://t3:9099')
    await input.fill('http://new-t3:9099')
    await expect(input).toHaveValue('http://new-t3:9099')
  })

  test('Save Settings persists remediation changes via PUT', async ({ page }) => {
    let putBody: string | null = null
    page.on('request', (req) => {
      if (req.method() === 'PUT' && req.url().includes('/api/v1/settings/')) {
        putBody = req.postData()
      }
    })

    await page.getByTestId('remediation-mode-approve').click()
    await page.locator('button:has-text("Save Settings")').click()
    await expect(page.locator('button:has-text("Saved!")')).toBeVisible({ timeout: 3000 })

    expect(putBody).not.toBeNull()
    expect(putBody).toContain('"mode":"approve"')
  })
})
