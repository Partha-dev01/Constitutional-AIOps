/**
 * Where the marketing call-to-action buttons send visitors.
 *
 * In production this is the front-door "launch" path that wakes the demo box on
 * genuine human intent (wired in R2). Plain visits to the marketing root must
 * never wake the box, so ONLY these explicit CTAs carry the launch URL.
 *
 * Overridable at build time via VITE_APP_URL. The unset default is a relative
 * path useful only for local preview.
 */
export const APP_URL: string = import.meta.env.VITE_APP_URL ?? '/login?next=/'

/**
 * Route an in-app destination through the CTA / wake URL so a cold box wakes
 * first, THEN lands on the requested path (the wake Lambda validates `next` and
 * only honours a same-origin absolute path). Preserves any existing query on
 * APP_URL. Example: appPath('/docs') → '/launch?next=%2Fdocs' in production.
 */
export function appPath(next: string): string {
  const sep = APP_URL.includes('?') ? '&' : '?'
  return `${APP_URL}${sep}next=${encodeURIComponent(next)}`
}

/**
 * Where "See how it works" sends visitors: the always-on, no-login demo that
 * runs the real app UI from bundled fixture data (no box wake, $0). Hosted
 * statically under /demo/ on this same site. The explicit index.html avoids
 * needing a CloudFront directory-index rewrite (private S3 + OAC does not
 * resolve `/demo/` to `/demo/index.html`); the demo build uses HashRouter so
 * every in-app route lives in the URL fragment. Overridable via VITE_DEMO_URL.
 */
export const DEMO_URL: string = import.meta.env.VITE_DEMO_URL ?? '/demo/index.html'

/**
 * Where the Docs "interactive API reference" opens: the running app's Swagger /
 * OpenAPI UI (served at /docs when the backend opts in via AIOPS_ENABLE_DOCS).
 * Env-overridable (VITE_DOCS_URL) so the hosted build can point at the app
 * origin; the committed default is same-origin /docs (self-host friendly, and
 * never hardcodes a deployment domain).
 */
export const DOCS_URL: string = import.meta.env.VITE_DOCS_URL ?? '/docs'

/**
 * The public documentation site (VitePress on GitHub Pages). The marketing
 * "Docs" nav points here now, and the old /docs.html page is a static redirect
 * to this same URL so existing inbound links keep working. Env-overridable so a
 * fork can point at its own docs.
 */
export const DOCS_SITE_URL: string =
  import.meta.env.VITE_DOCS_SITE_URL ??
  'https://partha-dev01.github.io/Constitutional-AIOps/'

/**
 * Whether to show the "Self-host" section + nav anchor. OFF by default so the
 * public marketing build never ships the self-host walkthrough (a real
 * `git clone` + AGPL notice) while the repository is still private. Set
 * VITE_SHOW_SELFHOST=true for the build made at the public-source flip.
 */
export const SHOW_SELFHOST: boolean = import.meta.env.VITE_SHOW_SELFHOST === 'true'
