import { test, expect } from '@playwright/test'

/**
 * API-level checks against the live deployment, exercised through Caddy's
 * path-based routing. The `request` fixture inherits httpCredentials from the
 * config, so basic-auth is applied automatically.
 */

test('GET /api/v1/health returns healthy with all components up', async ({ request }) => {
  const res = await request.get('/api/v1/health')
  expect(res.status()).toBe(200)

  const body = await res.json()
  expect(body.status).toBe('healthy')
  // Version is sourced from src/version.py (single source of truth).
  expect(body.version).toBe('0.7.0')

  const components: Array<{ name: string; healthy: boolean }> = body.components
  const byName = Object.fromEntries(components.map((c) => [c.name, c.healthy]))
  expect(byName.fast_agent).toBe(true)
  expect(byName.reasoning_agent).toBe(true)
  expect(byName.neo4j).toBe(true)
})

test('GET /api/v1/health/ready reports the service ready', async ({ request }) => {
  const res = await request.get('/api/v1/health/ready')
  expect(res.status()).toBe(200)
  const body = await res.json()
  expect(body.ready).toBe(true)
})

test('Grafana is reachable through the /grafana sub-path', async ({ request }) => {
  const res = await request.get('/grafana/login')
  expect(res.status()).toBe(200)
})

test('requests with the wrong password are rejected by Caddy basic-auth', async ({ playwright }) => {
  // A context created via the `playwright` fixture inherits the project's
  // httpCredentials, so an "anonymous" context would still authenticate.
  // Override with a deliberately wrong password to exercise Caddy's rejection
  // path directly; a valid credential is proven by every other test here.
  const bad = await playwright.request.newContext({
    baseURL: process.env.E2E_BASE_URL ?? 'https://aiops.imaginaerium.in',
    httpCredentials: { username: 'admin', password: 'definitely-wrong-password' },
  })
  const res = await bad.get('/api/v1/health')
  expect(res.status()).toBe(401)
  await bad.dispose()
})
