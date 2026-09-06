import React from 'react'
import ReactDOM from 'react-dom/client'
import { Benchmark } from './pages/Benchmark'
import './index.css'
import './styles/landing.css'

// Static entry for the standalone Benchmark page (benchmark.html).
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Benchmark />
  </React.StrictMode>,
)
