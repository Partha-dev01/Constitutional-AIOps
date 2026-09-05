/**
 * Constitutional AIOps — Settings Page E2E Tests
 *
 * Exercises every control on every Settings tab.
 * Runs against a LOCAL Vite dev server (port 3000) that proxies
 * /api → localhost:8000 (backend).
 *
 * Because the backend may not be running locally, all API calls
 * are intercepted via page.route() so we can exercise UI wiring
 * without a live backend.  The "PROVEN-REAL" vs "COSMETIC" table
 * in the report notes which paths are purely frontend-intercepted
 * and which touch a real server.
 *
 * Run headed:
 *   npx playwright test e2e/settings.spec.ts --headed
 *
 * Run headless (CI):
 *   npx playwright test e2e/settings.spec.ts
 */

import { test, expect, Page } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

// ── Shared mock payloads ──────────────────────────────────────────────────────

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
};

const MOCK_PROMPTS = {
  prompts: [
    {
      name: 'fast_annotator',
      description: 'Fast Agent - Telemetry Annotation',
      agent: 'fast',
      prompt: 'You are a Fast Telemetry Annotator. /no_think',
      editable: true,
    },
    {
      name: 'reasoning_rca',
      description: 'Reasoning Agent - Root Cause Analysis',
      agent: 'reasoning',
      prompt: 'You are an expert RCA agent.',
      editable: true,
    },
  ],
};

const MOCK_HEALTH = {
  status: 'healthy',
  components: [
    { name: 'fast_agent', healthy: true },
    { name: 'reasoning_agent', healthy: true },
    { name: 'neo4j', healthy: false },
  ],
};

// ── Screenshot helper ─────────────────────────────────────────────────────────

async function screenshot(page: Page, name: string) {
  // process.cwd() is the frontend dir under Playwright; __dirname is undefined under ESM.
  const dir = path.resolve(process.cwd(), '..', 'screenshots', 'settings');
  fs.mkdirSync(dir, { recursive: true });
  await page.screenshot({ path: path.join(dir, `${name}.png`), fullPage: true });
}

// ── Mock API routes helper ────────────────────────────────────────────────────

/** Intercept backend calls so tests work without a running backend. */
async function mockApis(page: Page) {
  let currentSettings = { ...DEFAULT_SETTINGS };

  // Auth config: report auth disabled so bootstrap never fails safe to /login.
  // auth.ts routes to /login when /auth/config is unreachable, which would
  // otherwise bounce every /settings navigation before the page renders.
  await page.route('**/auth/config**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ auth_required: false, signup_enabled: false, captcha_provider: '', captcha_site_key: '' }) });
  });

  // Health
  await page.route('**/api/v1/health', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_HEALTH) });
  });

  // Settings GET
  await page.route('**/api/v1/settings/', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(currentSettings) });
    } else if (route.request().method() === 'PUT') {
      const body = JSON.parse(route.request().postData() ?? '{}');
      currentSettings = { ...currentSettings, ...body };
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(currentSettings) });
    }
  });

  // Settings reset
  await page.route('**/api/v1/settings/reset', async (route) => {
    currentSettings = { ...DEFAULT_SETTINGS };
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(DEFAULT_SETTINGS) });
  });

  // Prompts list
  await page.route('**/api/v1/prompts/', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_PROMPTS) });
  });

  // Prompt save
  await page.route('**/api/v1/prompts/**', async (route) => {
    const method = route.request().method();
    if (method === 'PUT') {
      const name = route.request().url().split('/').pop() ?? 'unknown';
      const body = JSON.parse(route.request().postData() ?? '{}');
      const prompt = MOCK_PROMPTS.prompts.find((p) => p.name === name) ?? MOCK_PROMPTS.prompts[0];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...prompt, prompt: body.prompt }),
      });
    } else if (method === 'POST') {
      // reset single prompt
      const name = route.request().url().split('/').slice(-2)[0];
      const prompt = MOCK_PROMPTS.prompts.find((p) => p.name === name) ?? MOCK_PROMPTS.prompts[0];
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(prompt) });
    } else {
      // GET (list): the '/prompts/**' glob shadows the exact-list route under
      // Playwright LIFO, so serve the prompt list here too.
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_PROMPTS) });
    }
  });
}

// ── Navigate to Settings ──────────────────────────────────────────────────────

async function gotoSettings(page: Page) {
  await page.goto('/settings');
  // Wait for the page heading
  await page.waitForSelector('h1:has-text("Settings")', { timeout: 10_000 });
}

// ═════════════════════════════════════════════════════════════════════════════
// Tests
// ═════════════════════════════════════════════════════════════════════════════

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await mockApis(page);
    await gotoSettings(page);
  });

  // ── Constitutional AI tab ─────────────────────────────────────────────────
  test.describe('Constitutional AI tab', () => {
    test.beforeEach(async ({ page }) => {
      // Already on Constitutional tab by default
      await expect(page.locator('h2:has-text("Authorization Matrix")')).toBeVisible();
    });

    test('auto-threshold slider updates value label and hint text', async ({ page }) => {
      const slider = page.locator('[data-testid="auto-threshold-slider"]');
      const valueLabel = page.locator('[data-testid="auto-threshold-value"]');
      const hintText = page.locator('[data-testid="auto-threshold-hint"]');

      // Initial value
      await expect(valueLabel).toHaveText('90%');

      // Move slider to 95
      await slider.fill('95');
      await expect(valueLabel).toHaveText('95%');
      await expect(hintText).toContainText('95%');
    });

    test('approval-threshold slider updates value label and hint text', async ({ page }) => {
      const slider = page.locator('[data-testid="approval-threshold-slider"]');
      const valueLabel = page.locator('[data-testid="approval-threshold-value"]');
      const hintText = page.locator('[data-testid="approval-threshold-hint"]');

      await expect(valueLabel).toHaveText('70%');
      await slider.fill('80');
      await expect(valueLabel).toHaveText('80%');
      await expect(hintText).toContainText('80');
    });

    test('max-actions-per-minute input updates', async ({ page }) => {
      const input = page.locator('[data-testid="max-actions-input"]');
      await input.fill('25');
      await expect(input).toHaveValue('25');
    });

    test('audit-log toggle changes state', async ({ page }) => {
      const toggle = page.locator('[data-testid="toggle-auditLog"]');
      // Initial: checked (true) → aria-pressed="true"
      await expect(toggle).toHaveAttribute('aria-pressed', 'true');
      await toggle.click();
      await expect(toggle).toHaveAttribute('aria-pressed', 'false');
    });

    test('learning toggle changes state', async ({ page }) => {
      const toggle = page.locator('[data-testid="toggle-learning"]');
      await expect(toggle).toHaveAttribute('aria-pressed', 'true');
      await toggle.click();
      await expect(toggle).toHaveAttribute('aria-pressed', 'false');
    });

    test('strictTier1 toggle is disabled and stays checked', async ({ page }) => {
      const toggle = page.locator('[data-testid="toggle-strictTier1"]');
      await expect(toggle).toBeDisabled();
      await expect(toggle).toHaveAttribute('aria-pressed', 'true');
    });

    test('Save Settings calls backend PUT and shows Saved!', async ({ page }) => {
      // Track that the PUT was made
      let putCalled = false;
      page.on('request', (req) => {
        if (req.method() === 'PUT' && req.url().includes('/api/v1/settings/')) {
          putCalled = true;
        }
      });

      // Modify something
      await page.locator('[data-testid="auto-threshold-slider"]').fill('88');

      // Save
      await page.locator('button:has-text("Save Settings")').click();
      await expect(page.locator('button:has-text("Saved!")')).toBeVisible({ timeout: 3000 });
      expect(putCalled).toBe(true);
    });

    test('screenshot: constitutional tab', async ({ page }) => {
      await screenshot(page, '01-constitutional');
    });
  });

  // ── Notifications tab ─────────────────────────────────────────────────────
  test.describe('Notifications tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.locator('button:has-text("Notifications")').click();
      await expect(page.locator('h2:has-text("Notification Channels")')).toBeVisible();
    });

    test('email toggle changes state', async ({ page }) => {
      const toggle = page.locator('[data-testid="toggle-email"]');
      await expect(toggle).toHaveAttribute('aria-pressed', 'false');
      await toggle.click();
      await expect(toggle).toHaveAttribute('aria-pressed', 'true');
    });

    test('slack toggle changes state', async ({ page }) => {
      const toggle = page.locator('[data-testid="toggle-slack"]');
      await toggle.click();
      await expect(toggle).toHaveAttribute('aria-pressed', 'true');
    });

    test('webhook toggle reveals URL input', async ({ page }) => {
      const toggle = page.locator('[data-testid="toggle-webhook"]');
      await expect(page.locator('[data-testid="webhook-url-input"]')).not.toBeVisible();
      await toggle.click();
      await expect(page.locator('[data-testid="webhook-url-input"]')).toBeVisible();

      // Type a URL
      await page.locator('[data-testid="webhook-url-input"]').fill('https://my.server/hook');
      await expect(page.locator('[data-testid="webhook-url-input"]')).toHaveValue('https://my.server/hook');
    });

    test('notification event toggles work', async ({ page }) => {
      const critical = page.locator('[data-testid="toggle-notifyCritical"]');
      const approval = page.locator('[data-testid="toggle-notifyApproval"]');
      const resolution = page.locator('[data-testid="toggle-notifyResolution"]');

      await expect(critical).toHaveAttribute('aria-pressed', 'true');
      await expect(approval).toHaveAttribute('aria-pressed', 'true');
      await expect(resolution).toHaveAttribute('aria-pressed', 'false');

      await critical.click();
      await expect(critical).toHaveAttribute('aria-pressed', 'false');
      await resolution.click();
      await expect(resolution).toHaveAttribute('aria-pressed', 'true');
    });

    test('Save Settings persists notification changes', async ({ page }) => {
      let putCalled = false;
      page.on('request', (req) => {
        if (req.method() === 'PUT' && req.url().includes('/api/v1/settings/')) putCalled = true;
      });

      await page.locator('[data-testid="toggle-email"]').click();
      await page.locator('button:has-text("Save Settings")').click();
      await expect(page.locator('button:has-text("Saved!")')).toBeVisible({ timeout: 3000 });
      expect(putCalled).toBe(true);
    });

    test('screenshot: notifications tab', async ({ page }) => {
      await screenshot(page, '02-notifications');
    });
  });

  // ── Telemetry tab ─────────────────────────────────────────────────────────
  test.describe('Telemetry tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.locator('button:has-text("Telemetry")').click();
      await expect(page.locator('h2:has-text("LGTM Stack Configuration")')).toBeVisible();
    });

    test('loki toggle hides/shows URL', async ({ page }) => {
      const toggle = page.locator('[data-testid="toggle-loki"]');
      await expect(page.locator('[data-testid="loki-url-input"]')).toBeVisible();
      await toggle.click();
      await expect(page.locator('[data-testid="loki-url-input"]')).not.toBeVisible();
    });

    test('prometheus toggle hides/shows URL', async ({ page }) => {
      const toggle = page.locator('[data-testid="toggle-prometheus"]');
      await expect(page.locator('[data-testid="prometheus-url-input"]')).toBeVisible();
      await toggle.click();
      await expect(page.locator('[data-testid="prometheus-url-input"]')).not.toBeVisible();
    });

    test('tempo toggle hides/shows URL', async ({ page }) => {
      const toggle = page.locator('[data-testid="toggle-tempo"]');
      await expect(page.locator('[data-testid="tempo-url-input"]')).toBeVisible();
      await toggle.click();
      await expect(page.locator('[data-testid="tempo-url-input"]')).not.toBeVisible();
    });

    test('loki URL input editable', async ({ page }) => {
      const input = page.locator('[data-testid="loki-url-input"]');
      await input.fill('http://my-loki:3100');
      await expect(input).toHaveValue('http://my-loki:3100');
    });

    test('prometheus URL input editable', async ({ page }) => {
      const input = page.locator('[data-testid="prometheus-url-input"]');
      await input.fill('http://my-prometheus:9090');
      await expect(input).toHaveValue('http://my-prometheus:9090');
    });

    test('tempo URL input editable', async ({ page }) => {
      const input = page.locator('[data-testid="tempo-url-input"]');
      await input.fill('http://my-tempo:3200');
      await expect(input).toHaveValue('http://my-tempo:3200');
    });

    test('retention days input editable', async ({ page }) => {
      const input = page.locator('[data-testid="retention-days-input"]');
      await input.fill('90');
      await expect(input).toHaveValue('90');
    });

    test('Save Settings persists telemetry changes', async ({ page }) => {
      let putCalled = false;
      page.on('request', (req) => {
        if (req.method() === 'PUT' && req.url().includes('/api/v1/settings/')) putCalled = true;
      });

      await page.locator('[data-testid="retention-days-input"]').fill('45');
      await page.locator('button:has-text("Save Settings")').click();
      await expect(page.locator('button:has-text("Saved!")')).toBeVisible({ timeout: 3000 });
      expect(putCalled).toBe(true);
    });

    test('screenshot: telemetry tab', async ({ page }) => {
      await screenshot(page, '03-telemetry');
    });
  });

  // ── Models tab ────────────────────────────────────────────────────────────
  test.describe('Models tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.locator('button:has-text("Models")').click();
      await expect(page.locator('h2:has-text("LLM Endpoints")')).toBeVisible();
    });

    test('shows Fast Agent and Reasoning Agent cards', async ({ page }) => {
      await expect(page.locator('text=Fast Agent').first()).toBeVisible();
      await expect(page.locator('text=Reasoning Agent').first()).toBeVisible();
    });

    test('shows Live Status panel', async ({ page }) => {
      await expect(page.locator('h2:has-text("Live Status")')).toBeVisible();
    });

    test('shows Graph Memory panel', async ({ page }) => {
      await expect(page.locator('h2:has-text("Graph Memory")')).toBeVisible();
    });

    test('screenshot: models tab', async ({ page }) => {
      await screenshot(page, '04-models');
    });
  });

  // ── System Prompts tab ────────────────────────────────────────────────────
  test.describe('System Prompts tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.locator('button:has-text("System Prompts")').click();
      await expect(page.locator('h2:has-text("System Prompts")')).toBeVisible();
      // Wait for prompts to load (mocked)
      await page.waitForTimeout(300);
    });

    test('shows prompt cards for both agents', async ({ page }) => {
      await expect(page.locator('text=Fast Agent - Telemetry Annotation')).toBeVisible();
      await expect(page.locator('text=Reasoning Agent - Root Cause Analysis')).toBeVisible();
    });

    test('edit prompt → textarea appears → save → prompt updated', async ({ page }) => {
      // Click Edit on the first prompt
      const editBtn = page.locator('button:has-text("Edit")').first();
      await editBtn.click();

      // Textarea should appear
      const textarea = page.locator('textarea').first();
      await expect(textarea).toBeVisible();

      // Edit the content
      await textarea.fill('Updated prompt text for testing.');

      // Track PUT request
      let putCalled = false;
      page.on('request', (req) => {
        if (req.method() === 'PUT' && req.url().includes('/api/v1/prompts/')) putCalled = true;
      });

      // Save (exact match so we don't hit the page-level "Save Settings" button)
      await page.getByRole('button', { name: 'Save', exact: true }).first().click();

      // Textarea should disappear
      await expect(textarea).not.toBeVisible({ timeout: 2000 });
      expect(putCalled).toBe(true);
    });

    test('cancel edit restores view mode', async ({ page }) => {
      await page.locator('button:has-text("Edit")').first().click();
      const textarea = page.locator('textarea').first();
      await expect(textarea).toBeVisible();

      await page.locator('button:has-text("Cancel")').first().click();
      await expect(textarea).not.toBeVisible({ timeout: 2000 });
    });

    test('reset prompt calls POST /{name}/reset', async ({ page }) => {
      let resetCalled = false;
      page.on('request', (req) => {
        if (req.method() === 'POST' && req.url().includes('/reset')) resetCalled = true;
      });

      await page.locator('button:has-text("Reset")').first().click();
      // Small wait for async
      await page.waitForTimeout(300);
      expect(resetCalled).toBe(true);
    });

    test('screenshot: system prompts tab', async ({ page }) => {
      await screenshot(page, '05-prompts');
    });
  });

  // ── Persistence across reload (mocked) ───────────────────────────────────
  test.describe('Persistence across reload', () => {
    test('settings loaded from backend on mount (GET called)', async ({ page }) => {
      let getCalled = false;
      // Already navigated; check a fresh navigation
      page.on('request', (req) => {
        if (req.method() === 'GET' && req.url().includes('/api/v1/settings/')) getCalled = true;
      });
      await page.reload();
      await page.waitForSelector('h1:has-text("Settings")', { timeout: 5000 });
      expect(getCalled).toBe(true);
    });

    test('saved value reflected after reload', async ({ page }) => {
      // Set slider to 92 and save
      const slider = page.locator('[data-testid="auto-threshold-slider"]');
      await slider.fill('92');
      await page.locator('button:has-text("Save Settings")').click();
      await expect(page.locator('button:has-text("Saved!")')).toBeVisible({ timeout: 3000 });

      // Now the mock returns the PUT'd body; re-intercept for next GET
      await page.route('**/api/v1/settings/', async (route) => {
        if (route.request().method() === 'GET') {
          const saved = { ...DEFAULT_SETTINGS, constitutional: { ...DEFAULT_SETTINGS.constitutional, autoThreshold: 92 } };
          await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(saved) });
        } else {
          await route.continue();
        }
      });

      await page.reload();
      await page.waitForSelector('h1:has-text("Settings")', { timeout: 5000 });

      // Value should be 92 after reload
      await expect(page.locator('[data-testid="auto-threshold-value"]')).toHaveText('92%');
    });
  });

  // ── Reset Settings button ─────────────────────────────────────────────────
  test.describe('Reset Settings', () => {
    test('Reset button calls POST /reset and restores defaults', async ({ page }) => {
      let resetCalled = false;
      page.on('request', (req) => {
        if (req.method() === 'POST' && req.url().includes('/api/v1/settings/reset')) resetCalled = true;
      });

      // First change something
      await page.locator('[data-testid="auto-threshold-slider"]').fill('95');
      await expect(page.locator('[data-testid="auto-threshold-value"]')).toHaveText('95%');

      // Click reset
      await page.locator('button[aria-label="Reset to defaults"]').click();
      await expect(page.locator('button:has-text("Saved!")')).toBeVisible({ timeout: 3000 });
      expect(resetCalled).toBe(true);

      // Defaults restored
      await expect(page.locator('[data-testid="auto-threshold-value"]')).toHaveText('90%');
    });
  });
});
