import React from 'react'
import ReactDOM from 'react-dom/client'
import { Architecture } from './pages/Architecture'
import './index.css'
import './styles/landing.css'

// Static entry for the standalone Architecture page (architecture.html).
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Architecture />
  </React.StrictMode>,
)
