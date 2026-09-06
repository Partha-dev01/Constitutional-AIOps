import React from 'react'
import ReactDOM from 'react-dom/client'
import { Features } from './pages/Features'
import './index.css'
import './styles/landing.css'

// Static entry for the standalone Features page (features.html).
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Features />
  </React.StrictMode>,
)
