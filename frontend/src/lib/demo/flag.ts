/**
 * Demo-mode flag (isolated so websocket.ts can read it without pulling the
 * fixture dataset into the main production bundle).
 *
 * Set at build time: `VITE_DEMO_MODE=true npm run build`. When true, lib/demo
 * installs a global fetch shim (see ./index) that answers every /api/v1/*
 * request from bundled JSON, so the app runs with no backend and no login.
 * The default build leaves this false and ships zero demo code.
 */
export const DEMO_MODE: boolean = import.meta.env.VITE_DEMO_MODE === 'true'
