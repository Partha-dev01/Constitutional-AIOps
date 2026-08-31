import React from 'react'
import ReactDOM from 'react-dom/client'
import { Landing } from './pages/Landing'
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
