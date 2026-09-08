import { useState, useEffect } from 'react'
import {
  Play,
  Database,
  CheckCircle2,
  XCircle,
  Loader2,
  FileJson,
  FileSpreadsheet,
  FileCode,
  Zap,
  Gauge,
} from 'lucide-react'
import { cn } from '../lib/utils'
import { Tabs, TabPanel } from '../components/ui/Tabs'
import { useToast } from '../components/ui/toast'
import { useAuthStore } from '../lib/auth'

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

interface EndpointEvalCase {
  test_id: string
  task_type: string
  correct: boolean
  latency_ms: number
  source: string
}

interface EndpointEval {
  ok: boolean
  model: string
  cases_run: number
  passed: number
  pass_rate: number
  annotation: { run: number; passed: number }
  rca: { run: number; passed: number }
  avg_latency_ms: number
  cases: EndpointEvalCase[]
  detail: string
}

const BENCHMARK_TABS = [
  { id: 'evaluate', label: 'Your setup' },
  { id: 'datasets', label: 'Datasets'   },
  { id: 'run',      label: 'Research run'},
  { id: 'results',  label: 'Results'    },
  { id: 'compare',  label: 'Compare'    },
] as const

type BenchmarkTab = (typeof BENCHMARK_TABS)[number]['id']

export function Benchmark() {
  const { showToast } = useToast()
  // Admin gate: starting a benchmark run or the endpoint quick-check spends the
  // box's configured (owner) endpoint, so both are admin actions (the backend
  // enforces 403). Non-admins still see results, datasets and models.
  const authRequired = useAuthStore((s) => s.authRequired)
  const role = useAuthStore((s) => s.user?.role)
  const isAdmin = !authRequired || role === 'admin'
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [models, setModels] = useState<Record<string, Model>>({})
  const [results, setResults] = useState<BenchmarkResult[]>([])
  const [status, setStatus] = useState<BenchmarkStatus | null>(null)
  const [selectedModel, setSelectedModel] = useState('constitutional_aiops')
  const [maxAnnotation, setMaxAnnotation] = useState(100)
  const [maxRca, setMaxRca] = useState(50)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<BenchmarkTab>('evaluate')
  const [evalResult, setEvalResult] = useState<EndpointEval | null>(null)
  const [evalLoading, setEvalLoading] = useState(false)
  const [evalError, setEvalError] = useState<string | null>(null)

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

  // Poll status ONLY while a run is active AND the page is visible
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

    // Always do one initial fetch on mount to learn current state
    fetchStatus()

    // Only set up the interval while a run is active
    if (!status?.is_running) return

    const handleVisibilityChange = () => {
      // Interval cleanup is handled by the effect return; no action needed here
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)

    const interval = setInterval(() => {
      if (!document.hidden) {
        fetchStatus()
      }
    }, 2000)

    return () => {
      clearInterval(interval)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [status?.is_running])

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
        showToast(`Failed to start benchmark: ${error.detail || 'Unknown error'}`, 'error')
      }
    } catch (err) {
      console.error('Failed to start benchmark:', err)
      showToast('Failed to start benchmark', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleEvaluate = async () => {
    setEvalLoading(true)
    setEvalError(null)
    try {
      const response = await fetch('/api/v1/benchmark/evaluate-endpoint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_annotation: 3, max_rca: 2 }),
      })
      if (response.ok) {
        setEvalResult(await response.json())
      } else {
        const error = await response.json().catch(() => ({}))
        setEvalError(error.detail || 'Quick check failed')
      }
    } catch (err) {
      console.error('Failed to evaluate endpoint:', err)
      setEvalError('Could not reach the backend for the quick check')
    } finally {
      setEvalLoading(false)
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
            Check the model you configured, or reproduce the research paper
          </p>
        </div>
        <div className="flex items-center gap-2">
          {status?.is_running && (
            <span className="flex items-center gap-2 text-sm text-orange-500" aria-live="polite">
              <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
              Running...
            </span>
          )}
        </div>
      </div>

      {/* Accessible tab strip */}
      <Tabs
        value={activeTab}
        onChange={(id) => setActiveTab(id as BenchmarkTab)}
        tabs={BENCHMARK_TABS}
      >
        {/* Your setup Tab — quick check against the configured endpoint */}
        <TabPanel id="evaluate" activeTab={activeTab} className="pt-6">
          <div className="space-y-6">
            <div className="p-4 rounded-lg border border-border bg-card">
              <div className="flex items-start gap-3">
                <Zap className="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
                <div className="space-y-1">
                  <h3 className="font-medium">Is your model good enough?</h3>
                  <p className="text-sm text-muted-foreground">
                    Runs a few sample annotation and root-cause cases through the exact agents the
                    app uses, against the LLM endpoint you configured in Settings. Same scoring as
                    the research benchmark, on a handful of cases, so it finishes in one go. Nothing
                    is stored.
                  </p>
                </div>
              </div>
              <div className="mt-4">
                {isAdmin ? (
                  <button
                    onClick={handleEvaluate}
                    disabled={evalLoading || status?.is_running}
                    className={cn(
                      'flex items-center gap-2 px-4 py-2 rounded-sm font-medium',
                      'bg-primary text-primary-foreground',
                      'disabled:opacity-50 disabled:cursor-not-allowed',
                    )}
                  >
                    {evalLoading ? (
                      <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
                    ) : (
                      <Zap className="h-4 w-4" aria-hidden="true" />
                    )}
                    {evalLoading ? 'Checking your endpoint…' : 'Run quick check'}
                  </button>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    The quick check runs against the box&apos;s configured endpoint, so it is an
                    admin action.
                  </p>
                )}
                {status?.is_running && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    A research run is in progress. Wait for it to finish before the quick check.
                  </p>
                )}
              </div>
            </div>

            {evalError && (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive" role="alert">
                {evalError}
              </div>
            )}

            {evalResult && (
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="p-4 rounded-lg border border-border bg-card">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <CheckCircle2 className="h-4 w-4 text-primary" aria-hidden="true" /> Pass rate
                    </div>
                    <div className="mt-1 text-2xl font-bold">{evalResult.pass_rate.toFixed(0)}%</div>
                    <div className="text-xs text-muted-foreground">
                      {evalResult.passed} / {evalResult.cases_run} cases
                    </div>
                  </div>
                  <div className="p-4 rounded-lg border border-border bg-card">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Gauge className="h-4 w-4 text-primary" aria-hidden="true" /> Avg latency
                    </div>
                    <div className="mt-1 text-2xl font-bold">{evalResult.avg_latency_ms.toFixed(0)}ms</div>
                    <div className="text-xs text-muted-foreground">per inference</div>
                  </div>
                  <div className="p-4 rounded-lg border border-border bg-card">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Database className="h-4 w-4 text-primary" aria-hidden="true" /> Breakdown
                    </div>
                    <div className="mt-1 text-sm">
                      Annotation {evalResult.annotation.passed}/{evalResult.annotation.run}
                    </div>
                    <div className="text-sm">
                      RCA {evalResult.rca.passed}/{evalResult.rca.run}
                    </div>
                  </div>
                </div>

                <div className="rounded-lg border border-border bg-card overflow-x-auto">
                  <table className="w-full min-w-[520px] text-sm">
                    <thead className="bg-muted">
                      <tr>
                        <th className="px-4 py-2 text-left font-medium">Case</th>
                        <th className="px-4 py-2 text-left font-medium">Task</th>
                        <th className="px-4 py-2 text-left font-medium">Source</th>
                        <th className="px-4 py-2 text-right font-medium">Latency</th>
                        <th className="px-4 py-2 text-right font-medium">Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      {evalResult.cases.map((c) => (
                        <tr key={c.test_id} className="border-t border-border">
                          <td className="px-4 py-2 font-mono text-xs">{c.test_id}</td>
                          <td className="px-4 py-2 capitalize">{c.task_type}</td>
                          <td className="px-4 py-2 text-muted-foreground">{c.source || '—'}</td>
                          <td className="px-4 py-2 text-right">{c.latency_ms.toFixed(0)}ms</td>
                          <td className="px-4 py-2 text-right">
                            {c.correct ? (
                              <CheckCircle2 className="ml-auto h-4 w-4 text-green-500" aria-hidden="true" />
                            ) : (
                              <XCircle className="ml-auto h-4 w-4 text-red-500" aria-hidden="true" />
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-xs text-muted-foreground">
                  This is a small smoke check, not the full 431-case benchmark. Use the Research run
                  tab for a complete evaluation.
                </p>
              </div>
            )}
          </div>
        </TabPanel>

        {/* Datasets Tab */}
        <TabPanel id="datasets" activeTab={activeTab} className="pt-6">
          <p className="mb-4 text-sm text-muted-foreground">
            These are the research datasets used to reproduce the paper. To bring your own,
            replace the files under <code className="rounded-sm bg-muted px-1 py-0.5 text-xs">data/benchmark</code>.
            To just check the model you configured, use the <span className="font-medium">Your setup</span> tab.
          </p>
          <div className="grid gap-4 md:grid-cols-2">
            {datasets.map((dataset) => (
              <div key={dataset.name} className="p-4 rounded-lg border border-border bg-card">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="h-5 w-5 text-primary" aria-hidden="true" />
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
                      <span key={key} className="px-2 py-1 text-xs bg-muted rounded-sm">
                        {key}: {value}
                      </span>
                    ))}
                  </div>
                )}
                {dataset.categories && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {Object.entries(dataset.categories).map(([key, value]) => (
                      <span key={key} className="px-2 py-1 text-xs bg-muted rounded-sm">
                        {key}: {value}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {datasets.length === 0 && (
              <div className="col-span-2 p-8 text-center text-muted-foreground">
                No datasets found. Upload or configure a dataset to get started.
              </div>
            )}
          </div>
        </TabPanel>

        {/* Run Tab */}
        <TabPanel id="run" activeTab={activeTab} className="pt-6">
          <div className="space-y-6">
            {/* Configuration */}
            <div className="p-4 rounded-lg border border-border bg-card">
              <h3 className="font-medium mb-4">Benchmark Configuration</h3>
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <label htmlFor="model-select" className="block text-sm font-medium mb-2">Model</label>
                  <select
                    id="model-select"
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full p-2 rounded-sm border border-border bg-background text-foreground"
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
                  <label htmlFor="max-annotation" className="block text-sm font-medium mb-2">
                    Annotation Tests (max)
                  </label>
                  <input
                    id="max-annotation"
                    type="number"
                    value={maxAnnotation}
                    onChange={(e) => setMaxAnnotation(parseInt(e.target.value) || 100)}
                    min={1}
                    max={200}
                    className="w-full p-2 rounded-sm border border-border bg-background text-foreground"
                    disabled={status?.is_running}
                  />
                </div>
                <div>
                  <label htmlFor="max-rca" className="block text-sm font-medium mb-2">
                    RCA Tests (max)
                  </label>
                  <input
                    id="max-rca"
                    type="number"
                    value={maxRca}
                    onChange={(e) => setMaxRca(parseInt(e.target.value) || 50)}
                    min={1}
                    max={100}
                    className="w-full p-2 rounded-sm border border-border bg-background text-foreground"
                    disabled={status?.is_running}
                  />
                </div>
              </div>
              <div className="mt-4">
                {isAdmin ? (
                  <button
                    onClick={handleStartBenchmark}
                    disabled={status?.is_running || loading}
                    className={cn(
                      'flex items-center gap-2 px-4 py-2 rounded-sm font-medium',
                      'bg-primary text-primary-foreground',
                      'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                  >
                    {loading || status?.is_running ? (
                      <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
                    ) : (
                      <Play className="h-4 w-4" aria-hidden="true" />
                    )}
                    {status?.is_running ? 'Running...' : 'Start Benchmark'}
                  </button>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    Starting a research benchmark run is an admin action.
                  </p>
                )}
              </div>
            </div>

            {/* Progress */}
            {status?.is_running && status.progress && (
              <div className="p-4 rounded-lg border border-border bg-card" aria-live="polite" aria-label="Benchmark progress">
                <h3 className="font-medium mb-4">Progress</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Task: {status.progress.task_type}</span>
                    <span>{status.progress.current} / {status.progress.total}</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2" role="progressbar" aria-valuenow={status.progress.percent} aria-valuemin={0} aria-valuemax={100}>
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
        </TabPanel>

        {/* Results Tab */}
        <TabPanel id="results" activeTab={activeTab} className="pt-6">
          <div className="space-y-4">
            <div className="flex justify-end gap-2">
              <button
                onClick={() => handleExport('json')}
                className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-sm border border-border hover:bg-muted"
              >
                <FileJson className="h-4 w-4" aria-hidden="true" />
                JSON
              </button>
              <button
                onClick={() => handleExport('csv')}
                className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-sm border border-border hover:bg-muted"
              >
                <FileSpreadsheet className="h-4 w-4" aria-hidden="true" />
                CSV
              </button>
              <button
                onClick={() => handleExport('latex')}
                className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-sm border border-border hover:bg-muted"
              >
                <FileCode className="h-4 w-4" aria-hidden="true" />
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
                            <span className="inline-flex items-center gap-1">
                              <CheckCircle2 className="h-4 w-4 text-green-500" aria-hidden="true" />
                              <span className="sr-only">Completed</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1">
                              <XCircle className="h-4 w-4 text-red-500" aria-hidden="true" />
                              <span className="sr-only">Failed</span>
                            </span>
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
        </TabPanel>

        {/* Compare Tab */}
        <TabPanel id="compare" activeTab={activeTab} className="pt-6">
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
        </TabPanel>
      </Tabs>
    </div>
  )
}
