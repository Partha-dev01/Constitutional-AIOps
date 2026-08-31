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
