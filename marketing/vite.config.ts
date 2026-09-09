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
      // Static entries: the landing (index.html) plus each standalone content
      // page. All emit to dist/ and upload to S3.
      input: {
        main: path.resolve(__dirname, 'index.html'),
        docs: path.resolve(__dirname, 'docs.html'),
        safety: path.resolve(__dirname, 'safety.html'),
        architecture: path.resolve(__dirname, 'architecture.html'),
        features: path.resolve(__dirname, 'features.html'),
        benchmark: path.resolve(__dirname, 'benchmark.html'),
        usecases: path.resolve(__dirname, 'usecases.html'),
        faq: path.resolve(__dirname, 'faq.html'),
        opensource: path.resolve(__dirname, 'opensource.html'),
        selfhost: path.resolve(__dirname, 'selfhost.html'),
      },
    },
  },
})
