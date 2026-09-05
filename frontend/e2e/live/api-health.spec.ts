import { test, expect } from '@playwright/test'

/**
 * API-level checks against the live deployment, exercised through Caddy's
 * path-based routing. The `request` fixture inherits httpCredentials AND the
 * logged-in storageState from the config; tests that need an anonymous
 * (no in-app session) client build a fresh request context with Caddy creds
 * but no storage state.
 */

const ENFORCED = (process.env.E2E_AUTH_ENFORCED ?? 'true') !== 'false'
const BASE_URL = process.env.E2E_BASE_URL ?? 'https://aiops.example.com'

/** Caddy-authenticated context WITHOUT the in-app session cookie. */
function anonContextOptions() {
  return {
    baseURL: BASE_URL,
    httpCredentials: {
      username: process.env.E2E_USER ?? '',
      password: process.env.E2E_PASS ?? '',
    },
    // Contexts created through the `playwright` fixture inherit the project's
    // use.storageState (the logged-in session cookie) just like they inherit
    // httpCredentials — force an empty cookie jar so "anonymous" is real.
    storageState: { cookies: [], origins: [] },
  }
}

test('GET /api/v1/health returns healthy with all components up', async ({ request }) => {
  const res = await request.get('/api/v1/health')
  expect(res.status()).toBe(200)

  const body = await res.json()
  expect(body.status).toBe('healthy')
  // Version is sourced from src/version.py (single source of truth).
  expect(body.version).toBe('1.0.0')

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
    baseURL: process.env.E2E_BASE_URL ?? 'https://aiops.example.com',
    httpCredentials: { username: 'admin', password: 'definitely-wrong-password' },
  })
  const res = await bad.get('/api/v1/health')
  expect(res.status()).toBe(401)
  await bad.dispose()
})

test('protected API rejects requests without an in-app session', async ({ playwright }) => {
  test.skip(!ENFORCED, 'auth not enforced: API is open behind Caddy')

  // Caddy credentials, but NO storageState/session cookie.
  const anon = await playwright.request.newContext(anonContextOptions())
  const res = await anon.get('/api/v1/chat/conversations')
  expect(res.status()).toBe(401)
  await anon.dispose()
})

test('in-app login with a wrong app password is rejected', async ({ playwright }) => {
  const anon = await playwright.request.newContext(anonContextOptions())
  const res = await anon.post('/api/v1/auth/login', {
    data: { username: 'admin', password: 'definitely-wrong-app-password' },
  })
  expect(res.status()).toBe(401)
  await anon.dispose()
})

test('GET /api/v1/auth/config is public and reports enforcement', async ({ playwright }) => {
  const anon = await playwright.request.newContext(anonContextOptions())
  const res = await anon.get('/api/v1/auth/config')
  expect(res.status()).toBe(200)
  const body = await res.json()
  expect(typeof body.auth_required).toBe('boolean')
  expect(body.auth_required).toBe(ENFORCED)
  await anon.dispose()
})
