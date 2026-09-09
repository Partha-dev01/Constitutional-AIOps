import React from 'react'
import ReactDOM from 'react-dom/client'
import { SelfHost } from './pages/SelfHost'
import './index.css'
import './styles/landing.css'

// Static entry for the standalone Self-host page (see selfhost.html + vite.config
// rollupOptions). Its own URL (/selfhost.html) rather than an in-page section.
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <SelfHost />
  </React.StrictMode>,
)
