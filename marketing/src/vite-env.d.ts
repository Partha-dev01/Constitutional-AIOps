/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Front-door launch URL the CTAs point at (wakes the demo box). */
  readonly VITE_APP_URL?: string
  /** No-login demo (static, no box wake). Defaults to /demo/. */
  readonly VITE_DEMO_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
