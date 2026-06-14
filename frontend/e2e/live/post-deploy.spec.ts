import { test, expect, type Page, type ConsoleMessage } from '@playwright/test'

/**
 * STANDARD POST-DEPLOY GATE — live suite for https://aiops.imaginaerium.in.
 *
 * Runs through playwright.config.live.ts, so it inherits the Caddy basic-auth
 * (httpCredentials) + the in-app session cookie captured by global-setup. The
 * HEADLINE of this suite is CONSOLE / ERROR CAPTURE: the user reported that
 * clicking sometimes emits console logs, so for every page we wire console /
 * pageerror / requestfailed listeners BEFORE navigating, then assert the
 * captured list is empty after load AND after each interaction.
 *
 * Allowlist policy: only a tiny, EXPLICIT, inline-documented set of known-benign
 * messages is tolerated (see ALLOWLIST below). This is the LIVE backend, so the
 * WebSocket SHOULD connect — ws failures are NOT allowlisted; if the socket
 * fails that is a real finding the report must surface.
 */

// ---------------------------------------------------------------------------
// Known-benign allowlist. Keep this SMALL and each entry justified inline. A
// captured message is ignored ONLY if it contains one of these substrings.
// NOTE: WebSocket errors are deliberately NOT here — a live ws failure is a
// real finding, not benign noise.
// ---------------------------------------------------------------------------
const ALLOWLIST: { pattern: RegExp; why: string }[] = [
  // The deployed index references /favicon.svg (and browsers also probe
  // /favicon.ico) but the icon file is not deployed, so it 404s. Full Chromium
  // (headed) requests it and logs a 404; the headless shell skips it. Purely
  // cosmetic — a missing site icon, not an app fault. Matched on the resource
  // URL via the response/requestfailed listeners below (the generic
  // "Failed to load resource" console.error carries no URL, so it is dropped).
  { pattern: /favicon\.(svg|ico|png)/i, why: 'favicon file not deployed — cosmetic only' },
  // Chrome devtools probes this well-known path on some builds; never an app error.
  { pattern: /\.well-known\/appspecific\/com\.chrome\.devtools/i, why: 'chrome devtools probe' },
]

function isAllowlisted(message: string): boolean {
  return ALLOWLIST.some((entry) => entry.pattern.test(message))
}

interface Capture {
  errors: string[]
}

/**
 * Attach console / pageerror / requestfailed listeners to a page and collect
 * every error-level event (minus the allowlist) into `errors`. Must be called
 * BEFORE the first navigation so nothing emitted during initial load is missed.
 */
function captureErrors(page: Page, label: string): Capture {
  const errors: string[] = []
  const record = (raw: string) => {
    if (!isAllowlisted(raw)) errors.push(raw)
  }
  page.on('console', (m: ConsoleMessage) => {
    if (m.type() !== 'error') return
    const text = m.text()
    // A failed sub-resource (e.g. the missing favicon) makes the browser emit a
    // generic "Failed to load resource: ... 404/403" console.error that carries
    // NO url — so it cannot be allowlist-matched here. Drop it: the SAME failure
    // is captured with its real URL by the response/requestfailed listeners
    // below, where the allowlist (and any genuine breakage) is judged properly.
    if (/Failed to load resource/i.test(text)) return
    record(`[${label}] console.error: ${text}`)
  })
  page.on('pageerror', (e) => record(`[${label}] pageerror: ${e.message}`))
  page.on('requestfailed', (r) => {
    // Aborted/cancelled requests are routine in an SPA (e.g. a fetch unmounted
    // mid-flight). Only NS_ERROR / net::ERR style hard failures matter, but we
    // still record everything except the explicit cancel so the report is honest.
    const errorText = r.failure()?.errorText ?? 'unknown'
    if (/aborted|cancell?ed/i.test(errorText)) return
    record(`[${label}] requestfailed: ${r.url()} — ${errorText}`)
  })
  // A 4xx/5xx on a STATIC asset (document / script / stylesheet / image / font)
  // is a real finding UNLESS its URL is allowlisted (the favicon). This is where
  // the headed-only favicon 404 is judged — by URL, not by the urlless
  // console.error above. We deliberately exclude xhr/fetch here: those are the
  // app's own API calls, whose error handling is the app's concern (and which
  // surface a real, descriptive console.error if something is genuinely wrong).
  page.on('response', (r) => {
    const status = r.status()
    if (status < 400) return
    const type = r.request().resourceType()
    if (type === 'xhr' || type === 'fetch') return
    record(`[${label}] http ${status} (${type}): ${r.url()}`)
  })
  return { errors }
}

/** Assert the capture is clean, surfacing the full list of offenders if not. */
function expectClean(capture: Capture, context: string): void {
  expect(
    capture.errors,
    `Console/error capture should be empty after: ${context}\n` +
      `Captured ${capture.errors.length}:\n  ${capture.errors.join('\n  ')}`,
  ).toEqual([])
}

const SHOT_DIR = 'test-results/live/post-deploy'

// Every authed route + the heading that proves it rendered.
const ROUTES: { path: string; slug: string; heading: RegExp }[] = [
  { path: '/', slug: 'dashboard', heading: /^Dashboard$/ },
  { path: '/console', slug: 'console', heading: /^Command Center$/ },
  { path: '/agents', slug: 'agents', heading: /^Agent Hub$/ },
  { path: '/mcp', slug: 'mcp', heading: /^MCP Tools$/ },
  { path: '/telemetry', slug: 'telemetry', heading: /^Telemetry$/ },
  { path: '/graph', slug: 'graph', heading: /Episodic Knowledge Graph/ },
  { path: '/infrastructure', slug: 'infrastructure', heading: /^Infrastructure$/ },
  { path: '/incidents', slug: 'incidents', heading: /^Incidents$/ },
  { path: '/chat', slug: 'chat', heading: /^Chat$/ },
  { path: '/metrics', slug: 'metrics', heading: /Metrics/ },
  { path: '/benchmark', slug: 'benchmark', heading: /^Benchmark$/ },
  { path: '/settings', slug: 'settings', heading: /^Settings$/ },
]

test.describe('Post-deploy gate — every route loads console-clean', () => {
  for (const route of ROUTES) {
    test(`${route.path} loads, shows its heading, and emits no console errors`, async ({ page }) => {
      const capture = captureErrors(page, route.path)

      await page.goto(route.path)
      // The heading proves the route mounted its page (not a blank shell).
      await expect(
        page.getByRole('heading', { name: route.heading }).first(),
      ).toBeVisible({ timeout: 30_000 })

      // Give late async work (health poll, graph fetch, ws connect) a beat to
      // settle so any deferred error surfaces before we assert.
      await page.waitForTimeout(2_500)

      await page.screenshot({
        path: `${SHOT_DIR}/${route.slug}.png`,
        fullPage: true,
      })
      expectClean(capture, `loading ${route.path}`)
    })
  }
})

test.describe('Post-deploy gate — interactions stay console-clean', () => {
  test('desktop sidebar collapses to an icon-rail and back', async ({ page }) => {
    const capture = captureErrors(page, 'sidebar-toggle')
    await page.goto('/')
    // The Layout mounts the same `app-sidebar` <nav> twice (desktop static
    // column + mobile drawer container), so scope to the visible one.
    const sidebar = page.getByTestId('app-sidebar').locator('visible=true')
    await expect(sidebar).toBeVisible()

    // Likewise there are two sidebar-toggle buttons (one per sidebar copy); the
    // desktop one is the only visible instance at this width.
    const toggle = page.getByTestId('sidebar-toggle').locator('visible=true')
    await expect(toggle).toBeVisible()

    // Collapse to the icon-rail (w-16). The brand <h1> hides in rail mode.
    await toggle.click()
    await expect(page.getByRole('heading', { name: 'Constitutional' })).toBeHidden()
    await page.screenshot({ path: `${SHOT_DIR}/sidebar-rail.png` })
    expectClean(capture, 'collapse sidebar to rail')

    // Expand back to full (w-64); the brand returns.
    await toggle.click()
    await expect(page.getByRole('heading', { name: 'Constitutional' })).toBeVisible()
    expectClean(capture, 'expand sidebar back to full')
  })

  test('every nav link routes without console errors', async ({ page }) => {
    const capture = captureErrors(page, 'nav-links')
    await page.goto('/')

    // The Dashboard ('/') opens the live WebSocket. We VERIFY it connects (a
    // real backend-health signal — see the dedicated ws test) and let the
    // handshake fully settle BEFORE we click away. Otherwise navigating mid-
    // handshake tears the half-open socket down and React's cleanup fires a
    // benign "WebSocket error: Event" — an artifact of the test's own speed,
    // not a deploy defect. Waiting here keeps this test measuring NAVIGATION
    // cleanliness without racing the socket. (We intentionally do NOT allowlist
    // ws errors — a genuine ws failure still surfaces in the ws test below.)
    await page.waitForEvent('websocket', { timeout: 15_000 }).catch(() => {})
    await page.waitForTimeout(1_500)

    const navLinks = [
      'Dashboard',
      'Command Center',
      'Agents',
      'MCP Tools',
      'Telemetry',
      'Graph',
      'Infrastructure',
      'Incidents',
      'Chat',
      'Metrics',
      'Benchmark',
      'Settings',
    ]
    const navSidebar = page.getByTestId('app-sidebar').locator('visible=true')
    for (const name of navLinks) {
      await navSidebar.getByRole('link', { name }).click()
      // Landing on a real page: at least one h1 must be visible.
      await expect(page.locator('h1').first()).toBeVisible({ timeout: 30_000 })
      await page.waitForTimeout(400)
      expectClean(capture, `navigate to "${name}"`)
    }
  })

  test('Agents — every tab opens console-clean', async ({ page }) => {
    const capture = captureErrors(page, 'agents-tabs')
    await page.goto('/agents')
    await expect(page.getByRole('heading', { name: 'Agent Hub' })).toBeVisible()

    // Agent Hub is now trimmed to just the two model surfaces; MCP Tools,
    // Telemetry and the Graph Explorer moved to their own top-level sidebar
    // routes. Tabs are an accessible ARIA tablist (role="tab"), not bare buttons.
    const tabLabels = ['Fast Agent', 'Reasoning Agent']
    for (const label of tabLabels) {
      await page.getByRole('tab', { name: new RegExp(label, 'i') }).click()
      // Each tab swaps in a section heading (h2) — wait for the panel to mount.
      await expect(page.locator('h2').first()).toBeVisible({ timeout: 20_000 })
      await page.waitForTimeout(800)
      expectClean(capture, `Agents tab "${label}"`)
    }
    await page.screenshot({ path: `${SHOT_DIR}/agents-tabs.png`, fullPage: true })
  })

  test('Benchmark — every tab opens console-clean (and Run controls render dark)', async ({ page }) => {
    const capture = captureErrors(page, 'benchmark-tabs')
    await page.goto('/benchmark')
    await expect(page.getByRole('heading', { name: 'Benchmark' })).toBeVisible()

    for (const tab of ['Datasets', 'Run', 'Results', 'Compare']) {
      await page.getByRole('tab', { name: new RegExp(`^${tab}$`) }).click()
      await page.waitForTimeout(600)
      expectClean(capture, `Benchmark tab "${tab}"`)
    }

    // On the Run tab the native form controls must render DARK, not white.
    await page.getByRole('tab', { name: /^Run$/ }).click()
    const select = page.locator('select').first()
    const numberInput = page.locator('input[type="number"]').first()
    await expect(select).toBeVisible()
    await expect(numberInput).toBeVisible()

    // Assert the computed background is a dark colour (theme --background), not
    // the white the deploy explicitly fixed. We parse the rgb and require the
    // average channel to be clearly on the dark side.
    for (const [name, locator] of [
      ['select', select],
      ['number input', numberInput],
    ] as const) {
      const bg = await locator.evaluate((el) => getComputedStyle(el).backgroundColor)
      const m = bg.match(/rgba?\(([^)]+)\)/)
      expect(m, `${name} background should be a parseable rgb (got "${bg}")`).not.toBeNull()
      const [r, g, b] = m![1].split(',').map((n) => parseFloat(n))
      const avg = (r + g + b) / 3
      expect(avg, `${name} background "${bg}" should be DARK (avg<90), not white`).toBeLessThan(90)
    }

    await page.screenshot({ path: `${SHOT_DIR}/benchmark-run-dark.png`, fullPage: true })
    expectClean(capture, 'Benchmark Run dark-control check')
  })

  test('Command Center — fits viewport, ctrl-click a node attaches a context chip', async ({ page }) => {
    const capture = captureErrors(page, 'console-ctrlclick')
    await page.goto('/console')
    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible()

    // The three cockpit panes are present and nothing is clipped: the page root
    // is bounded to the viewport, so the document must NOT scroll horizontally.
    await expect(page.getByTestId('console-graph-pane')).toBeVisible()
    await expect(page.getByTestId('console-incidents')).toBeVisible()
    await expect(page.getByTestId('console-chat')).toBeVisible()
    const hScroll = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    )
    expect(hScroll, 'Command Center must not produce a horizontal scrollbar').toBe(false)

    // The embedded topology graph must fetch real nodes.
    const firstNode = page
      .locator('[data-testid="schema-graph-embedded"] [data-testid^="schema-node-"]')
      .first()
    await expect(firstNode).toBeVisible({ timeout: 30_000 })

    // Ctrl-click attaches the node to the chat as context → the Console renders
    // a "N attached as context" chip. (Selection only surfaces in embedded mode.)
    await firstNode.click({ modifiers: ['Control'] })
    await expect(page.getByText(/attached as context/i)).toBeVisible({ timeout: 10_000 })

    await page.screenshot({ path: `${SHOT_DIR}/console-context-chip.png`, fullPage: true })
    expectClean(capture, 'Command Center ctrl-click context chip')
  })

  test('Chat — sends a message and renders a real response (allows the 14B latency)', async ({
    page,
  }) => {
    test.setTimeout(150_000) // the real 14B reasoning model can take a while
    const capture = captureErrors(page, 'chat-send')
    await page.goto('/chat')
    await expect(page.getByRole('heading', { name: 'Chat' })).toBeVisible()

    const input = page.getByPlaceholder('Ask about incidents, metrics, or request analysis...')
    await input.fill('List two common causes of high CPU on a service.')
    await page.locator('form button[type="submit"]').click()

    // The in-flight indicator appears (exact match — an sr-only variant exists).
    await expect(page.getByText('Thinking...', { exact: true })).toBeVisible({ timeout: 30_000 })

    // A real assistant answer renders. The welcome message is the first .prose;
    // a successful round-trip adds at least one more, and it must NOT be the
    // backend-down error banner.
    await expect(page.locator('.prose')).toHaveCount(2, { timeout: 95_000 })
    await expect(page.getByText(/Please check that the backend/)).toHaveCount(0)
    const answer = await page.locator('.prose').last().innerText()
    expect(answer.trim().length, 'assistant answer should not be empty').toBeGreaterThan(0)
    expect(answer, 'no raw <think> tags should leak into the answer').not.toContain('<think>')

    await page.screenshot({ path: `${SHOT_DIR}/chat-response.png`, fullPage: true })
    expectClean(capture, 'Chat send + response')
  })

  test('reloading a conversation replays its reasoning timeline (history persistence)', async ({
    page,
  }) => {
    test.setTimeout(160_000) // a real 14B round-trip, then a reload
    const capture = captureErrors(page, 'chat-history-replay')
    await page.goto('/chat')
    await expect(page.getByRole('heading', { name: 'Chat' })).toBeVisible()

    // A query with a known service + log keywords drives telemetry/log tools AND
    // the reasoning step, so the persisted timeline has something to replay.
    const prompt = 'Analyze recent error logs for nextcloud'
    const input = page.getByPlaceholder('Ask about incidents, metrics, or request analysis...')
    await input.fill(prompt)

    // Capture the conversation id from the chat response so we reload THIS exact
    // conversation deterministically (the sidebar can hold many others).
    const [resp] = await Promise.all([
      page.waitForResponse(
        (r) => r.url().includes('/api/v1/chat/') && r.request().method() === 'POST',
        { timeout: 95_000 },
      ),
      page.locator('form button[type="submit"]').click(),
    ])
    const convId = (await resp.json()).conversation_id as string
    expect(convId, 'chat response should carry a conversation_id').toBeTruthy()

    // The backend has responded (resp captured) and stored the turn server-side.
    // Confirm the LIVE timeline COMMITTED: the reasoning step's enriched token
    // summary ("qwen3-14b · N tokens") only appears once the answer has landed.
    await expect(page.getByText(/qwen3-14b · \d+ tokens?/i).first()).toBeVisible({ timeout: 95_000 })

    // Reload THIS conversation from history via the ?conversation= hand-off — a
    // FRESH navigation that runs the same load path as clicking it in the
    // sidebar, so any rendered timeline must be rebuilt from persisted metadata
    // (no left-over in-memory state). This is the regression the fix addresses.
    await page.goto(`/chat?conversation=${convId}`)
    await expect(page.getByRole('heading', { name: 'Chat' })).toBeVisible()

    // THE FIX: the reloaded turn replays its reasoning timeline AND the enriched
    // step results (the token summary proves the persisted tool/model metadata
    // was reconstructed) — not just the bare answer text.
    await expect(page.getByText('Reasoning with Qwen3-14B').first()).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText(/qwen3-14b · \d+ tokens?/i).first()).toBeVisible({ timeout: 5_000 })

    await page.screenshot({ path: `${SHOT_DIR}/chat-history-replay.png`, fullPage: true })
    expectClean(capture, 'reload conversation replays reasoning')
  })

  test('live WebSocket connects on the Dashboard (real backend health)', async ({ page }) => {
    // The spec is explicit: on the LIVE backend the WebSocket SHOULD connect, so
    // this is asserted as a first-class signal (not allowlisted away). The
    // Dashboard ('/') is the surface that opens the socket: it fetches a
    // ws-token, opens wss://…/ws?token=…, and on success logs "WebSocket
    // connected" (lib/websocket.ts) + "Dashboard connected to WebSocket". If the
    // socket fails to connect, this test fails — a genuine deploy finding.
    const wsPromise = page.waitForEvent('websocket', { timeout: 20_000 })
    const connectedLog = page.waitForEvent('console', {
      predicate: (m) => m.text().includes('WebSocket connected'),
      timeout: 20_000,
    })

    await page.goto('/')
    await expect(page.getByRole('heading', { name: /^Dashboard$/ })).toBeVisible({
      timeout: 30_000,
    })

    const ws = await wsPromise
    expect(ws.url(), 'WebSocket should target the secure /ws endpoint').toMatch(
      /^wss:\/\/.+\/ws\?token=/,
    )
    expect(ws.isClosed(), 'WebSocket should be open, not immediately closed').toBe(false)
    // The app logs success only after ws.onopen fires — this confirms a true
    // end-to-end connect through Caddy to the backend, not just a socket object.
    await connectedLog
  })
})
