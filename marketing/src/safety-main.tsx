import React from 'react'
import ReactDOM from 'react-dom/client'
import { Safety } from './pages/Safety'
import './index.css'
import './styles/landing.css'

// Static entry for the standalone Safety page (see safety.html + vite.config
// rollupOptions). Its own URL (/safety.html) rather than an in-page section.
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Safety />
  </React.StrictMode>,
)
