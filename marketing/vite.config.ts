import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Standalone static marketing site. No dev proxy / websocket: the landing is
// fully static and never talks to the backend. Built to dist/ and uploaded to
// S3 (served at the front-door root behind CloudFront, R2).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3100,
    host: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      // Two static entries: the landing (index.html) and the standalone docs
      // page (docs.html). Both emit to dist/ and upload to S3.
      input: {
        main: path.resolve(__dirname, 'index.html'),
        docs: path.resolve(__dirname, 'docs.html'),
      },
    },
  },
})
