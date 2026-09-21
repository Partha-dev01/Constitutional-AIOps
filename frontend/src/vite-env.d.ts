/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_URL: string
  /** '"true"' builds a no-backend demo (fetch shim + no login). See lib/demo. */
  readonly VITE_DEMO_MODE?: string
  /** Published docs site the in-app guide links out to. See pages/Docs.tsx. */
  readonly VITE_DOCS_SITE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
