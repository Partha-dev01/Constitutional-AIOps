import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, HashRouter } from 'react-router-dom'
import App from './App'
import { ToastProvider } from './components/ui/toast'
import { DEMO_MODE } from './lib/demo/flag'
import './index.css'
import './styles/chat.css'
import './styles/schema.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      refetchOnWindowFocus: false,
    },
  },
})

/**
 * Boot the SPA. In a VITE_DEMO_MODE build we first install the fetch shim (a
 * dynamic import so its fixtures stay out of the normal production bundle) and
 * ONLY THEN mount React, so every page's first request is already intercepted.
 */
async function boot(): Promise<void> {
  if (DEMO_MODE) {
    const { installDemoFetch } = await import('./lib/demo')
    installDemoFetch()
  }

  // Demo build is hosted statically under /demo/ with no server-side rewrite,
  // so it uses HashRouter (all routes live in the URL fragment). The normal
  // app keeps BrowserRouter.
  const Router = DEMO_MODE ? HashRouter : BrowserRouter

  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <Router>
          <ToastProvider>
            <App />
          </ToastProvider>
        </Router>
      </QueryClientProvider>
    </React.StrictMode>,
  )
}

void boot()
