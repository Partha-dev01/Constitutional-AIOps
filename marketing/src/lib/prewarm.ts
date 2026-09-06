/**
 * Smart pre-warm (Track 4).
 *
 * Fires ONE background ping at the CloudFront `/prewarm` behavior once the
 * visitor shows genuine human intent, so the sleeping demo box is already
 * booting by the time they click a launch CTA. The ping is idempotent on the
 * server (only a stopped -> start transition costs anything), but this client
 * still guards hard against waking a paid box for nothing:
 *
 *   - never on load; only after real dwell AND interaction (or a CTA hover),
 *   - never from automation (webdriver) or a hidden/prerendered tab,
 *   - at most once per session, with a cross-session cooldown for repeat tabs.
 *
 * The intent decision is a pure function (`hasGenuineIntent`) so it is unit
 * tested; `installPrewarm()` is the thin impure wiring around it. Zero deps.
 */

/** Where the background ping goes. Same-origin `/prewarm` in production (its own
 *  CloudFront behavior on the wake Lambda); overridable for other setups. */
export const PREWARM_URL: string = import.meta.env.VITE_PREWARM_URL ?? '/prewarm'

/** Minimum dwell before an engaged visitor counts as intent. */
export const MIN_DWELL_MS = 6000
/** A hover over a launch CTA fires sooner, but still not instantly on load. */
export const CTA_MIN_DWELL_MS = 1500
/** Do not re-ping within this window across sessions (repeat visitors / tabs). */
export const COOLDOWN_MS = 4 * 60 * 1000

const SESSION_KEY = 'aiops.prewarm.fired'
const COOLDOWN_KEY = 'aiops.prewarm.at'

export interface IntentState {
  visible: boolean
  prerendering: boolean
  wasDiscarded: boolean
  dwellMs: number
  pointerMoved: boolean
  scrolledPastViewport: boolean
  touched: boolean
  keyed: boolean
  ctaHover: boolean
}

/**
 * Pure: does this state represent genuine human intent worth a box wake?
 * A deliberate hover over a launch CTA (after a brief settle) is strong intent
 * on its own; otherwise we need meaningful dwell AND some real interaction.
 */
export function hasGenuineIntent(s: IntentState): boolean {
  if (!s.visible) return false
  if (s.prerendering || s.wasDiscarded) return false
  if (s.ctaHover && s.dwellMs >= CTA_MIN_DWELL_MS) return true
  const engaged = s.pointerMoved || s.scrolledPastViewport || s.touched || s.keyed
  return s.dwellMs >= MIN_DWELL_MS && engaged
}

/** Pure: reject obvious automation. A real click always comes from a browser
 *  whose `webdriver` flag is not set. */
export function isLikelyRealBrowser(nav: { webdriver?: boolean } | undefined): boolean {
  if (!nav) return false
  return nav.webdriver !== true
}

let installed = false

function alreadyFiredThisSession(): boolean {
  try {
    return sessionStorage.getItem(SESSION_KEY) === '1'
  } catch {
    return false
  }
}

function cooldownActive(now: number): boolean {
  try {
    const raw = localStorage.getItem(COOLDOWN_KEY)
    if (!raw) return false
    const at = Number(raw)
    return Number.isFinite(at) && now - at < COOLDOWN_MS
  } catch {
    return false
  }
}

function markFired(now: number): void {
  try {
    sessionStorage.setItem(SESSION_KEY, '1')
  } catch {
    /* private mode / disabled storage: still fine, just no once-guard */
  }
  try {
    localStorage.setItem(COOLDOWN_KEY, String(now))
  } catch {
    /* ignore */
  }
}

/**
 * Watch for genuine intent and fire the pre-warm ping at most once. Safe to call
 * on any page: it never fires on load and no-ops in a non-browser / automated /
 * cooled-down / already-fired context. Returns a teardown function.
 */
export function installPrewarm(): () => void {
  const noop = () => {}
  if (installed) return noop
  if (typeof window === 'undefined' || typeof document === 'undefined') return noop
  installed = true

  const nav = typeof navigator !== 'undefined' ? navigator : undefined
  if (!isLikelyRealBrowser(nav)) return noop
  if (alreadyFiredThisSession()) return noop
  if (cooldownActive(Date.now())) return noop

  const doc = document as Document & { prerendering?: boolean; wasDiscarded?: boolean }
  const start = Date.now()
  const flags = { pointerMoved: false, scrolled: false, touched: false, keyed: false, ctaHover: false }
  let done = false
  let timer = 0
  let ctas: HTMLAnchorElement[] = []

  const cleanup = () => {
    window.removeEventListener('pointermove', onPointer)
    window.removeEventListener('scroll', onScroll)
    window.removeEventListener('touchstart', onTouch)
    window.removeEventListener('keydown', onKey)
    ctas.forEach((el) => el.removeEventListener('mouseenter', onCtaHover))
    if (timer) window.clearTimeout(timer)
  }

  const snapshot = (): IntentState => ({
    visible: doc.visibilityState === 'visible',
    prerendering: doc.prerendering === true,
    wasDiscarded: doc.wasDiscarded === true,
    dwellMs: Date.now() - start,
    pointerMoved: flags.pointerMoved,
    scrolledPastViewport: flags.scrolled,
    touched: flags.touched,
    keyed: flags.keyed,
    ctaHover: flags.ctaHover,
  })

  const fire = () => {
    if (done) return
    if (!hasGenuineIntent(snapshot())) return
    done = true
    markFired(Date.now())
    cleanup()
    try {
      // keepalive so it survives the navigation that usually follows a CTA click;
      // the response is same-origin (CloudFront) and ignored. Failures are silent.
      void fetch(PREWARM_URL, { method: 'GET', keepalive: true, cache: 'no-store' }).catch(noop)
    } catch {
      /* ignore */
    }
  }

  const onPointer = () => {
    flags.pointerMoved = true
    fire()
  }
  const onScroll = () => {
    if (window.scrollY > window.innerHeight) flags.scrolled = true
    fire()
  }
  const onTouch = () => {
    flags.touched = true
    fire()
  }
  const onKey = () => {
    flags.keyed = true
    fire()
  }
  const onCtaHover = () => {
    flags.ctaHover = true
    fire()
  }

  window.addEventListener('pointermove', onPointer, { passive: true })
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('touchstart', onTouch, { passive: true })
  window.addEventListener('keydown', onKey)
  ctas = Array.from(document.querySelectorAll<HTMLAnchorElement>('a[href*="launch"]'))
  ctas.forEach((el) => el.addEventListener('mouseenter', onCtaHover, { passive: true }))

  // Re-check once the dwell threshold passes, in case the visitor engaged early
  // then sat still (their event fired before dwell was long enough to qualify).
  timer = window.setTimeout(fire, MIN_DWELL_MS + 100)

  return cleanup
}
