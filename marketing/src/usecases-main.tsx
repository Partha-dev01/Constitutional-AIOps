import React from 'react'
import ReactDOM from 'react-dom/client'
import { UseCases } from './pages/UseCases'
import './index.css'
import './styles/landing.css'

// Static entry for the standalone Use-cases page (usecases.html).
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <UseCases />
  </React.StrictMode>,
)
