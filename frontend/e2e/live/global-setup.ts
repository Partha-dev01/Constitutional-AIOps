import fs from 'node:fs'
import path from 'node:path'
import { request } from '@playwright/test'
import type { FullConfig } from '@playwright/test'

/**
 * Live-suite global setup: perform the in-app login ONCE via the API and
 * persist the httpOnly session cookie as a Playwright storageState that every
 * test context inherits (see use.storageState in playwright.config.live.ts).
 *
 * Credentials:
 *   - Caddy basic-auth (outer wall): E2E_USER / E2E_PASS (required by config)
 *   - In-app login:                  E2E_APP_USER / E2E_APP_PASS
 *                                    (falls back to E2E_USER / E2E_PASS)
 *
 * Set E2E_AUTH_ENFORCED=false when the deployment runs with
 * AUTH_REQUIRED=false — an empty storage state is written and no login is
 * attempted (the app behaves exactly as pre-auth).
 */

const STORAGE_STATE_PATH = path.join('test-results', 'live', '.auth.json')

export default async function globalSetup(_config: FullConfig): Promise<void> {
  const baseURL = process.env.E2E_BASE_URL ?? 'https://aiops.imaginaerium.in'

  fs.mkdirSync(path.dirname(STORAGE_STATE_PATH), { recursive: true })

  if (process.env.E2E_AUTH_ENFORCED === 'false') {
    fs.writeFileSync(STORAGE_STATE_PATH, JSON.stringify({ cookies: [], origins: [] }))
    return
  }

  const appUser = process.env.E2E_APP_USER ?? process.env.E2E_USER ?? ''
  const appPass = process.env.E2E_APP_PASS ?? process.env.E2E_PASS ?? ''
  if (!appUser || !appPass) {
    throw new Error(
      'Live e2e needs in-app login credentials: set E2E_APP_USER/E2E_APP_PASS ' +
        '(or rely on E2E_USER/E2E_PASS), or set E2E_AUTH_ENFORCED=false.',
    )
  }

  const context = await request.newContext({
    baseURL,
    httpCredentials: {
      username: process.env.E2E_USER ?? '',
      password: process.env.E2E_PASS ?? '',
      origin: new URL(baseURL).origin,
    },
  })
  try {
    const response = await context.post('/api/v1/auth/login', {
      data: { username: appUser, password: appPass },
    })
    if (!response.ok()) {
      throw new Error(
        `In-app login failed during global setup: HTTP ${response.status()} ${await response.text()}`,
      )
    }
    await context.storageState({ path: STORAGE_STATE_PATH })
  } finally {
    await context.dispose()
  }
}
