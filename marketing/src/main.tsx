import React from 'react'
import ReactDOM from 'react-dom/client'
import { Landing } from './pages/Landing'
import { installPrewarm } from './lib/prewarm'
import './index.css'
import './styles/landing.css'

// Static marketing site: no router, no query client, no toasts. Just the
// landing. Any in-page navigation is plain anchor hrefs; CTAs go to VITE_APP_URL
// (see src/config.ts).
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Landing />
  </React.StrictMode>,
)

// Smart pre-warm: start watching for genuine intent so the sleeping demo box is
// already booting by the time a real visitor clicks launch. Never fires on load,
// never from a bot, at most once per session (see src/lib/prewarm.ts). Deferred
// to after first paint so the launch CTAs exist in the DOM for hover intent.
if (typeof window !== 'undefined') {
  window.requestAnimationFrame(() => installPrewarm())
}
