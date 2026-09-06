import React from 'react'
import ReactDOM from 'react-dom/client'
import { OpenSource } from './pages/OpenSource'
import './index.css'
import './styles/landing.css'

// Static entry for the standalone Open-source page (opensource.html).
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <OpenSource />
  </React.StrictMode>,
)
