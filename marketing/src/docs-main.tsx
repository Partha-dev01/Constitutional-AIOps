import React from 'react'
import ReactDOM from 'react-dom/client'
import { Docs } from './pages/Docs'
import './index.css'
import './styles/landing.css'

// Second static entry (see docs.html + vite.config rollupOptions). The docs live
// at their own URL (/docs.html) rather than as an in-page landing section.
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Docs />
  </React.StrictMode>,
)
