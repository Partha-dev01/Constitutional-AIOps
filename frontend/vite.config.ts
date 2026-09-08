import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// The no-login demo build (VITE_DEMO_MODE=true) is hosted under /demo/ on the
// marketing CloudFront, so its assets must resolve from that sub-path. The
// normal app build keeps the root base. Paired with HashRouter in the demo
// build (see main.tsx), a single /demo/index.html serves every route with no
// server-side rewrite.
const isDemo = process.env.VITE_DEMO_MODE === 'true'

export default defineConfig({
  base: isDemo ? '/demo/' : '/',
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        // Rolldown (Vite 8) wants the function form here, not the v5-era
        // name->packages object. Same intent: a stable vendor chunk shared by
        // every route, plus the two heavy libs split out so only the routes
        // that use them pay for them.
        manualChunks(id: string) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('react-force-graph-2d')) return 'force-graph'
          if (id.includes('/react-markdown/') || id.includes('/remark-gfm/')) return 'markdown'
          if (
            id.includes('/react/') ||
            id.includes('/react-dom/') ||
            id.includes('/react-router-dom/') ||
            id.includes('/@tanstack/react-query/')
          ) {
            return 'vendor'
          }
          return undefined
        },
      },
    },
  },
})
