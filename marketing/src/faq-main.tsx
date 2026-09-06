import React from 'react'
import ReactDOM from 'react-dom/client'
import { Faq } from './pages/Faq'
import './index.css'
import './styles/landing.css'

// Static entry for the standalone FAQ page (faq.html).
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Faq />
  </React.StrictMode>,
)
