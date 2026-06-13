import { useState, useEffect } from 'react'
import {
  Play,
  Database,
  CheckCircle2,
  XCircle,
  Loader2,
  FileJson,
  FileSpreadsheet,
  FileCode
} from 'lucide-react'
import { cn } from '../lib/utils'

interface Dataset {
  name: string
  file: string
  total_cases: number
  source: string
  description: string
  distribution?: Record<string, number>
  categories?: Record<string, number>
}

interface Model {
  description: string
  type: string
  vram_gb: number
}

interface BenchmarkResult {
  model_name: string
  annotation_accuracy: number
  rca_accuracy: number
  bert_f1: number
  avg_latency_ms: number
  p95_latency_ms: number
  total_tests: number
  passed_tests: number
  status: string
}

interface BenchmarkStatus {
  is_running: boolean
  progress?: {
    task_type: string
    current: number
    total: number
    percent: number
  }
  current_benchmark?: BenchmarkResult
}

export function Benchmark() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [models, setModels] = useState<Record<string, Model>>({})
  const [results, setResults] = useState<BenchmarkResult[]>([])
  const [status, setStatus] = useState<BenchmarkStatus | null>(null)
  const [selectedModel, setSelectedModel] = useState('constitutional_aiops')
  const [maxAnnotation, setMaxAnnotation] = useState(100)
  const [maxRca, setMaxRca] = useState(50)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'datasets' | 'run' | 'results' | 'compare'>('datasets')

  // Fetch datasets
  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const response = await fetch('/api/v1/benchmark/datasets')
        if (response.ok) {
          const data = await response.json()
          setDatasets(data.datasets || [])
        }
      } catch (err) {
        console.error('Failed to fetch datasets:', err)
      }
    }
    fetchDatasets()
  }, [])

  // Fetch models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch('/api/v1/benchmark/models')
        if (response.ok) {
          const data = await response.json()
          setModels(data.models || {})
        }
      } catch (err) {
        console.error('Failed to fetch models:', err)
      }
    }
    fetchModels()
  }, [])

  // Fetch results
  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch('/api/v1/benchmark/results')
        if (response.ok) {
          const data = await response.json()
          setResults(data.results || [])
        }
      } catch (err) {
        console.error('Failed to fetch results:', err)
      }
    }
    fetchResults()
  }, [])

  // Poll status while running
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('/api/v1/benchmark/status')
        if (response.ok) {
          const data = await response.json()
          setStatus(data)
        }
      } catch (err) {
        console.error('Failed to fetch status:', err)
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 2000)
    return () => clearInterval(interval)
  }, [])

  const handleStartBenchmark = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/v1/benchmark/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_name: selectedModel,
          max_annotation_tests: maxAnnotation,
          max_rca_tests: maxRca,
          temperature: 0.0,
        }),
      })
      if (response.ok) {
        setActiveTab('run')
      } else {
        const error = await response.json()
        alert(`Failed to start benchmark: ${error.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Failed to start benchmark:', err)
      alert('Failed to start benchmark')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (format: 'json' | 'csv' | 'latex') => {
    try {
      const response = await fetch(`/api/v1/benchmark/export?format=${format}`)
      if (response.ok) {
        const data = await response.json()
        if (format === 'json') {
          const blob = new Blob([JSON.stringify(data.results, null, 2)], { type: 'application/json' })
          downloadBlob(blob, 'benchmark_results.json')
        } else {
          const blob = new Blob([data.content], { type: 'text/plain' })
          downloadBlob(blob, `benchmark_results.${format === 'latex' ? 'tex' : format}`)
        }
      }
    } catch (err) {
      console.error('Failed to export:', err)
    }
  }

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Benchmark</h1>
          <p className="text-muted-foreground">
            Evaluate LLM performance on AIOps tasks
          </p>
        </div>
        <div className="flex items-center gap-2">
          {status?.is_running && (
            <span className="flex items-center gap-2 text-sm text-orange-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Running...
            </span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border overflow-x-auto">
        {(['datasets', 'run', 'results', 'compare'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap',
              activeTab === tab
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Datasets Tab */}
      {activeTab === 'datasets' && (
        <div className="grid gap-4 md:grid-cols-2">
          {datasets.map((dataset) => (
            <div key={dataset.name} className="p-4 rounded-lg border border-border bg-card">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-primary" />
                  <h3 className="font-medium capitalize">{dataset.name}</h3>
                </div>
                <span className="text-sm text-muted-foreground">
                  {dataset.total_cases} cases
                </span>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                {dataset.description}
              </p>
              <div className="mt-3 text-xs text-muted-foreground">
                Source: {dataset.source}
              </div>
              {dataset.distribution && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {Object.entries(dataset.distribution).map(([key, value]) => (
                    <span key={key} className="px-2 py-1 text-xs bg-muted rounded">
                      {key}: {value}
                    </span>
                  ))}
                </div>
              )}
              {dataset.categories && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {Object.entries(dataset.categories).map(([key, value]) => (
                    <span key={key} className="px-2 py-1 text-xs bg-muted rounded">
                      {key}: {value}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {datasets.length === 0 && (
            <div className="col-span-2 p-8 text-center text-muted-foreground">
              No datasets found. Run the prepare_datasets.py script first.
            </div>
          )}
        </div>
      )}

      {/* Run Tab */}
      {activeTab === 'run' && (
        <div className="space-y-6">
          {/* Configuration */}
          <div className="p-4 rounded-lg border border-border bg-card">
            <h3 className="font-medium mb-4">Benchmark Configuration</h3>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <label className="block text-sm font-medium mb-2">Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full p-2 rounded border border-border bg-background text-foreground"
                  disabled={status?.is_running}
                >
                  {Object.entries(models).map(([name, info]) => (
                    <option key={name} value={name}>
                      {info.description} ({info.vram_gb}GB)
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Annotation Tests (max)
                </label>
                <input
                  type="number"
                  value={maxAnnotation}
                  onChange={(e) => setMaxAnnotation(parseInt(e.target.value) || 100)}
                  min={1}
                  max={200}
                  className="w-full p-2 rounded border border-border bg-background text-foreground"
                  disabled={status?.is_running}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  RCA Tests (max)
                </label>
                <input
                  type="number"
                  value={maxRca}
                  onChange={(e) => setMaxRca(parseInt(e.target.value) || 50)}
                  min={1}
                  max={100}
                  className="w-full p-2 rounded border border-border bg-background text-foreground"
                  disabled={status?.is_running}
                />
              </div>
            </div>
            <div className="mt-4">
              <button
                onClick={handleStartBenchmark}
                disabled={status?.is_running || loading}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded font-medium',
                  'bg-primary text-primary-foreground',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                {loading || status?.is_running ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                {status?.is_running ? 'Running...' : 'Start Benchmark'}
              </button>
            </div>
          </div>

          {/* Progress */}
          {status?.is_running && status.progress && (
            <div className="p-4 rounded-lg border border-border bg-card">
              <h3 className="font-medium mb-4">Progress</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Task: {status.progress.task_type}</span>
                  <span>{status.progress.current} / {status.progress.total}</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all"
                    style={{ width: `${status.progress.percent}%` }}
                  />
                </div>
                <div className="text-sm text-muted-foreground">
                  {status.progress.percent.toFixed(1)}% complete
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Results Tab */}
      {activeTab === 'results' && (
        <div className="space-y-4">
          <div className="flex justify-end gap-2">
            <button
              onClick={() => handleExport('json')}
              className="flex items-center gap-2 px-3 py-1.5 text-sm rounded border border-border hover:bg-muted"
            >
              <FileJson className="h-4 w-4" />
              JSON
            </button>
            <button
              onClick={() => handleExport('csv')}
              className="flex items-center gap-2 px-3 py-1.5 text-sm rounded border border-border hover:bg-muted"
            >
              <FileSpreadsheet className="h-4 w-4" />
              CSV
            </button>
            <button
              onClick={() => handleExport('latex')}
              className="flex items-center gap-2 px-3 py-1.5 text-sm rounded border border-border hover:bg-muted"
            >
              <FileCode className="h-4 w-4" />
              LaTeX
            </button>
          </div>

          {results.length > 0 ? (
            <div className="rounded-lg border border-border bg-card overflow-x-auto">
              <table className="w-full min-w-[640px]">
                <thead className="bg-muted">
                  <tr>
                    <th className="px-4 py-2 text-left text-sm font-medium">Model</th>
                    <th className="px-4 py-2 text-right text-sm font-medium">Ann. Acc</th>
                    <th className="px-4 py-2 text-right text-sm font-medium">RCA Acc</th>
                    <th className="px-4 py-2 text-right text-sm font-medium">BERT F1</th>
                    <th className="px-4 py-2 text-right text-sm font-medium">Latency (ms)</th>
                    <th className="px-4 py-2 text-right text-sm font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result) => (
                    <tr key={result.model_name} className="border-t border-border">
                      <td className="px-4 py-2 font-medium">{result.model_name}</td>
                      <td className="px-4 py-2 text-right">{result.annotation_accuracy.toFixed(1)}%</td>
                      <td className="px-4 py-2 text-right">{result.rca_accuracy.toFixed(1)}%</td>
                      <td className="px-4 py-2 text-right">{result.bert_f1.toFixed(3)}</td>
                      <td className="px-4 py-2 text-right">{result.avg_latency_ms.toFixed(0)}</td>
                      <td className="px-4 py-2 text-right">
                        {result.status === 'completed' ? (
                          <CheckCircle2 className="h-4 w-4 text-green-500 inline" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500 inline" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-muted-foreground">
              No benchmark results yet. Run a benchmark to see results.
            </div>
          )}
        </div>
      )}

      {/* Compare Tab */}
      {activeTab === 'compare' && (
        <div className="space-y-4">
          {results.length >= 2 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {results.map((result) => (
                <div key={result.model_name} className="p-4 rounded-lg border border-border bg-card">
                  <h3 className="font-medium mb-3">{result.model_name}</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Annotation Accuracy</span>
                      <span className="font-medium">{result.annotation_accuracy.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${result.annotation_accuracy}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">RCA Accuracy</span>
                      <span className="font-medium">{result.rca_accuracy.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${result.rca_accuracy}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-sm pt-2 border-t mt-2">
                      <span className="text-muted-foreground">Avg Latency</span>
                      <span className="font-medium">{result.avg_latency_ms.toFixed(0)}ms</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">BERT F1</span>
                      <span className="font-medium">{result.bert_f1.toFixed(3)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-muted-foreground">
              Run benchmarks on multiple models to compare them.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
