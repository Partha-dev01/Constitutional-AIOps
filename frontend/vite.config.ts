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
      '@': path.resolve(__dirname, './src'),
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
        manualChunks: {
          // React core + router + query — shared by every route
          vendor: ['react', 'react-dom', 'react-router-dom', '@tanstack/react-query'],
          // Heavy graph renderer — only Graph/Agents/Console use it
          'force-graph': ['react-force-graph-2d'],
          // Markdown renderer — chat and insight cards
          markdown: ['react-markdown', 'remark-gfm'],
        },
      },
    },
  },
})
