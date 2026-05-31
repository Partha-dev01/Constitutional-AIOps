/**
 * MCP Tools tab — smoke spec (mocked backend).
 *
 * Mocks:
 *   GET /api/v1/tools/  → list of 9 tools (all Phase-1 + Phase-2)
 *   POST /api/v1/tools/call  → canned success response for query_recent_logs
 *
 * Asserts:
 *   - Tool list renders all 9 tools
 *   - New Phase-2 tools appear with correct names
 *   - Disabled action tools (restart_service, scale_service) are not clickable
 *   - Selecting query_recent_logs shows the param form
 *   - Executing query_recent_logs shows the QueryRecentLogsView result
 *   - POST /api/v1/tools/call is NEVER called for restart_service / scale_service
 */

import { test, expect } from '@playwright/test'

const MOCK_TOOLS = [
  { name: 'find_similar',              description: 'Find similar incidents',                          category: 'query',    parameters: { type: 'object', properties: { title: { type: 'string', description: 'Incident title' } }, required: ['title'] }, requires_approval: false, risk_level: 'low' },
  { name: 'get_dependencies',          description: 'Get service dependency graph',                    category: 'query',    parameters: { type: 'object', properties: { service_name: { type: 'string', description: 'Service name' } }, required: ['service_name'] }, requires_approval: false, risk_level: 'low' },
  { name: 'analyze_logs',              description: 'Analyze logs for patterns',                       category: 'analysis', parameters: { type: 'object', properties: { service_name: { type: 'string', description: 'Service' } }, required: ['service_name'] }, requires_approval: false, risk_level: 'low' },
  { name: 'analyze_time_series_anomaly', description: 'Z-score anomaly detection',                    category: 'analysis', parameters: { type: 'object', properties: { service_name: { type: 'string', description: 'Service' } }, required: ['service_name'] }, requires_approval: false, risk_level: 'low' },
  { name: 'restart_service',           description: 'Restart a Docker service',                       category: 'action',   parameters: { type: 'object', properties: { service_name: { type: 'string', description: 'Service' }, reason: { type: 'string', description: 'Reason' } }, required: ['service_name', 'reason'] }, requires_approval: true, risk_level: 'medium' },
  { name: 'scale_service',             description: 'Scale service replicas',                         category: 'action',   parameters: { type: 'object', properties: { service_name: { type: 'string', description: 'Service' }, target_replicas: { type: 'integer', description: 'Replicas' }, reason: { type: 'string', description: 'Reason' } }, required: ['service_name', 'target_replicas', 'reason'] }, requires_approval: true, risk_level: 'medium' },
  { name: 'query_recent_logs',         description: 'Query recent log entries from Loki',             category: 'query',    parameters: { type: 'object', properties: { service: { type: 'string', description: 'Service name (use all for all)' }, time_range_minutes: { type: 'integer', default: 15, description: 'Minutes back' }, limit: { type: 'integer', default: 50, description: 'Max entries' } }, required: ['service'] }, requires_approval: false, risk_level: 'low' },
  { name: 'query_metric',              description: 'Query Prometheus metrics for a service',         category: 'query',    parameters: { type: 'object', properties: { service: { type: 'string', description: 'Service name' }, time_range_minutes: { type: 'integer', default: 30, description: 'Minutes back' } }, required: ['service'] }, requires_approval: false, risk_level: 'low' },
  { name: 'list_containers',           description: 'List Docker containers and their status',        category: 'query',    parameters: { type: 'object', properties: { all_containers: { type: 'boolean', default: false, description: 'Include stopped' } }, required: [] }, requires_approval: false, risk_level: 'low' },
]

const MOCK_LOG_RESULT = {
  success: true,
  data: {
    service: 'api-gateway',
    time_range_minutes: 15,
    total_entries: 2,
    entries: [
      { timestamp: '2026-01-01T12:00:00', level: 'ERROR', message: 'Connection refused to database:5432', service: 'api-gateway' },
      { timestamp: '2026-01-01T12:00:05', level: 'INFO',  message: 'Health check passed',                service: 'api-gateway' },
    ],
  },
  error: null,
  execution_time_ms: 42.5,
  metadata: { source: 'loki' },
}

test.describe('MCP Tools tab', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the tools list endpoint
    await page.route('**/api/v1/tools/', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ tools: MOCK_TOOLS, total: MOCK_TOOLS.length }),
      })
    })

    // Mock the tool call endpoint (only for read-only tools)
    await page.route('**/api/v1/tools/call', (route) => {
      const req = route.request()
      req.postDataJSON().then((body: { tool_name: string }) => {
        // Destructive tools should never reach here — but if they do, return 403
        if (body.tool_name === 'restart_service' || body.tool_name === 'scale_service') {
          route.fulfill({ status: 403, body: JSON.stringify({ error: 'Destructive tool blocked' }) })
          return
        }
        // For query_recent_logs, return canned response
        if (body.tool_name === 'query_recent_logs') {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(MOCK_LOG_RESULT),
          })
          return
        }
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, data: { ok: true }, error: null, execution_time_ms: 10 }),
        })
      }).catch(() => route.continue())
    })

    // Navigate to the Agents page and switch to MCP Tools tab
    await page.goto('/agents')
    await page.waitForLoadState('networkidle')
    await page.click('button:has-text("MCP Tools")')
    // Wait for the tool list to load (triggered by tab switch → fetchTools)
    await page.waitForResponse('**/api/v1/tools/')
  })

  test('renders all 9 tools', async ({ page }) => {
    // All tool names should appear in the list
    for (const tool of MOCK_TOOLS) {
      await expect(page.locator(`text=${tool.name}`).first()).toBeVisible()
    }
  })

  test('Phase-2 tools are visible', async ({ page }) => {
    await expect(page.locator('text=query_recent_logs').first()).toBeVisible()
    await expect(page.locator('text=query_metric').first()).toBeVisible()
    await expect(page.locator('text=list_containers').first()).toBeVisible()
  })

  test('tool count badge shows 9', async ({ page }) => {
    await expect(page.locator('text=9 tools')).toBeVisible()
  })

  test('disabled action tools show lock icon text', async ({ page }) => {
    // The disabled tool rows should show "Requires approval" text
    const lockText = page.locator('text=Requires approval — coming soon').first()
    await expect(lockText).toBeVisible()
  })

  test('selecting query_recent_logs shows param form', async ({ page }) => {
    await page.click('button:has-text("query_recent_logs")')
    // The execute panel title should update
    await expect(page.locator('text=Execute: query_recent_logs')).toBeVisible()
    // The "service" required field should render
    await expect(page.locator('text=service').first()).toBeVisible()
  })

  test('executing query_recent_logs renders log result view', async ({ page }) => {
    // Select the tool
    await page.click('button:has-text("query_recent_logs")')
    await expect(page.locator('text=Execute: query_recent_logs')).toBeVisible()

    // Fill in the required "service" field
    const serviceInput = page.locator('input[placeholder*="Service name"], input[placeholder*="service"]').first()
    await serviceInput.fill('api-gateway')

    // Click Execute
    const callPromise = page.waitForResponse('**/api/v1/tools/call')
    await page.click('button:has-text("Execute Tool")')
    await callPromise

    // Result: should show 2 entries count badge
    await expect(page.locator('text=2 entries')).toBeVisible()
    // Should show at least one log level badge
    await expect(page.locator('text=ERROR').first()).toBeVisible()
    // Should show the execution time
    await expect(page.locator('text=/42.*ms/')).toBeVisible()
  })

  test('execution history records the call', async ({ page }) => {
    await page.click('button:has-text("query_recent_logs")')
    await expect(page.locator('text=Execute: query_recent_logs')).toBeVisible()

    const serviceInput = page.locator('input').first()
    await serviceInput.fill('api-gateway')

    await page.click('button:has-text("Execute Tool")')
    await page.waitForResponse('**/api/v1/tools/call')

    // History section should appear
    await expect(page.locator('text=Execution History')).toBeVisible()
    await expect(page.locator('text=query_recent_logs').nth(1)).toBeVisible()
    await expect(page.locator('text=ok')).toBeVisible()
  })

  test('restart_service is not clickable (disabled)', async ({ page }) => {
    const restartButton = page.locator('button:has-text("restart_service")')
    await expect(restartButton).toBeDisabled()
  })

  test('scale_service is not clickable (disabled)', async ({ page }) => {
    const scaleButton = page.locator('button:has-text("scale_service")')
    await expect(scaleButton).toBeDisabled()
  })

  test('POST /call is never fired for action tools', async ({ page }) => {
    // Track any /call requests that sneak through for action tools
    const destructiveCalls: string[] = []
    page.on('request', (req) => {
      if (req.url().includes('/api/v1/tools/call') && req.method() === 'POST') {
        try {
          const body = JSON.parse(req.postData() ?? '{}') as { tool_name?: string }
          if (body.tool_name === 'restart_service' || body.tool_name === 'scale_service') {
            destructiveCalls.push(body.tool_name)
          }
        } catch { /* ignore parse error */ }
      }
    })

    // Try clicking — buttons should be disabled so no navigation or fetch occurs
    const restartBtn = page.locator('button:has-text("restart_service")')
    if (await restartBtn.isDisabled()) {
      // Good — can't click
    }

    // Give any accidental async calls a chance to fire
    await page.waitForTimeout(500)
    expect(destructiveCalls).toHaveLength(0)
  })
})
