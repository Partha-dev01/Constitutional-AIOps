/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Front-door launch URL the CTAs point at (wakes the demo box). */
  readonly VITE_APP_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
