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
 * Where "See how it works" sends visitors: the always-on, no-login demo that
 * runs the real app UI from bundled fixture data (no box wake, $0). Hosted
 * statically under /demo/ on this same site. The explicit index.html avoids
 * needing a CloudFront directory-index rewrite (private S3 + OAC does not
 * resolve `/demo/` to `/demo/index.html`); the demo build uses HashRouter so
 * every in-app route lives in the URL fragment. Overridable via VITE_DEMO_URL.
 */
export const DEMO_URL: string = import.meta.env.VITE_DEMO_URL ?? '/demo/index.html'
