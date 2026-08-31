/**
 * Demo-mode fetch shim.
 *
 * Installed once at boot (from main.tsx) ONLY when VITE_DEMO_MODE=true. It wraps
 * window.fetch so every same-origin `/api/v1/*` request — whether it comes from
 * lib/api.ts's request()/streamChat, a raw `fetch('/api/v1/...')` in a page, or
 * a react-query queryFn — is answered from bundled fixtures (see ./fixtures)
 * instead of a live backend. Anything not under /api/v1 (the HTML, JS, CSS,
 * fonts, screenshots) passes straight through to the real fetch.
 *
 * The chat SSE endpoint is handled here too: it returns a streaming Response so
 * the existing streamChat() reader animates the canned answer token-by-token.
 */

import { DEMO_MODE } from './flag'
import { matchRoute, type DemoResult } from './fixtures'

const API_PREFIX = '/api/v1'

const wait = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms))

function jsonResponse(data: unknown, status: number): Response {
  if (status === 204) return new Response(null, { status })
  return new Response(JSON.stringify(data ?? {}), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function sseResponse(frames: Array<{ event: string; data: unknown }>): Response {
  const encoder = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      for (const frame of frames) {
        controller.enqueue(
          encoder.encode(`event: ${frame.event}\ndata: ${JSON.stringify(frame.data)}\n\n`),
        )
        // Pause between frames so the deltas stream like a live model would.
        await wait(frame.event === 'delta' ? 85 : 160)
      }
      controller.close()
    },
  })
  return new Response(stream, {
    status: 200,
    headers: { 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-store' },
  })
}

function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === 'string') return input
  if (input instanceof URL) return input.toString()
  return input.url
}

function requestMethod(input: RequestInfo | URL, init?: RequestInit): string {
  if (init?.method) return init.method
  if (input instanceof Request) return input.method
  return 'GET'
}

function requestBodyText(init?: RequestInit): string | undefined {
  return typeof init?.body === 'string' ? init.body : undefined
}

let installed = false

/** Patch window.fetch to serve fixtures for /api/v1/*. No-op unless DEMO_MODE. */
export function installDemoFetch(): void {
  if (!DEMO_MODE || installed) return
  installed = true

  const realFetch = window.fetch.bind(window)

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    let pathname: string
    try {
      pathname = new URL(requestUrl(input), window.location.origin).pathname
    } catch {
      return realFetch(input, init)
    }
    if (!pathname.startsWith(API_PREFIX)) return realFetch(input, init)

    const method = requestMethod(input, init).toUpperCase()
    const route = pathname.slice(API_PREFIX.length) || '/'
    const result: DemoResult = matchRoute(method, route, requestBodyText(init))

    // A little latency so the UI shows its genuine loading states.
    await wait(160 + Math.floor(Math.random() * 200))

    return result.sse ? sseResponse(result.sse) : jsonResponse(result.json, result.status)
  }
}
