// One-off: capture live UI screenshots for the landing page ProofSection.
// Usage (from frontend/):  E2E_USER=.. E2E_PASS=.. node scripts/capture-shots.mjs
import { chromium } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const BASE = process.env.E2E_BASE || 'https://aiops.imaginaerium.in'
const user = process.env.E2E_USER
const pass = process.env.E2E_PASS
if (!user || !pass) {
  console.error('Set E2E_USER and E2E_PASS')
  process.exit(1)
}

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const outDir = path.resolve(__dirname, '../public/screenshots')

const shots = [
  { name: 'dashboard', path: '/', settle: 5000 }, // allow WS to connect -> badge "Live"
  { name: 'agent-hub', path: '/agents', settle: 3000 },
  { name: 'metrics', path: '/metrics', settle: 3500 },
]

const browser = await chromium.launch()
const ctx = await browser.newContext({
  baseURL: BASE,
  httpCredentials: { username: user, password: pass },
  viewport: { width: 1360, height: 850 },
  deviceScaleFactor: 1.5,
})
const page = await ctx.newPage()

async function grab(name, p, settle) {
  await page.goto(p, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.waitForTimeout(settle)
  await page.screenshot({ path: path.join(outDir, `${name}.png`), fullPage: false })
  console.log('captured', name)
}

for (const s of shots) await grab(s.name, s.path, s.settle)

// chat: send a real in-domain question and wait for the reasoning agent's reply
// so the capture shows the system actually working (not an empty greeting).
await page.goto('/chat', { waitUntil: 'domcontentloaded', timeout: 45000 })
await page.waitForTimeout(1500)
try {
  const input = page.getByPlaceholder(/Ask about/i)
  await input.fill('Is the neo4j service healthy, and what is it used for?')
  const [resp] = await Promise.all([
    page.waitForResponse((r) => r.url().includes('/api/v1/chat') && r.request().method() === 'POST', { timeout: 40000 }),
    input.press('Enter'),
  ])
  void resp
  await page.waitForTimeout(2000) // let the answer render
} catch (e) {
  console.warn('chat exchange capture issue, capturing current chat view:', e.message)
}
await page.screenshot({ path: path.join(outDir, 'chat.png'), fullPage: false })
console.log('captured chat')

// graph-explorer lives inside the "Graph Explorer" tab on /agents; click it,
// wait for the force-graph canvas to render and the simulation to settle.
await page.goto('/agents', { waitUntil: 'domcontentloaded', timeout: 45000 })
await page.waitForTimeout(2000)
try {
  await page.getByText('Graph Explorer', { exact: true }).first().click({ timeout: 5000 })
  await page.waitForSelector('canvas', { timeout: 8000 })
  await page.waitForTimeout(5000) // force-directed layout settle
} catch (e) {
  console.warn('graph tab/canvas issue, capturing current /agents view:', e.message)
}
await page.screenshot({ path: path.join(outDir, 'graph-explorer.png'), fullPage: false })
console.log('captured graph-explorer')

await browser.close()
console.log('done ->', outDir)
