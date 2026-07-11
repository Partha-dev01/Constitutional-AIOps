import { useState, useEffect, useCallback } from 'react'
import {
  BarChart3,
  Download,
  RefreshCw,
  Loader2,
  Clock,
  Zap,
  CheckCircle,
  XCircle,
  Play,
  Gauge,
  FileJson,
  FileSpreadsheet,
  Trash2,
  TestTube
} from 'lucide-react'
import { cn } from '../lib/utils'
import { Tabs, TabPanel } from '../components/ui/Tabs'
import { useToast } from '../components/ui/toast'

// Types for metrics data
interface LatencyStats {
  count: number
  avg_ms: number
  min_ms: number
  max_ms: number
  p50_ms: number
  p95_ms: number
  p99_ms: number
  success_rate: number
  total_tokens?: number
}

interface MetricsSnapshot {
  timestamp: string
  fast_agent: LatencyStats
  reasoning_agent: LatencyStats
  total_requests: number
  success_rate: number
  determinism_config?: {
    fast_agent_temperature: number
    reasoning_agent_temperature: number
    chat_temperature: number
    seed_method: string
  }
}

interface LatencyRecord {
  agent: string
  latency_ms: number
  timestamp: string
  tokens_generated: number
  success: boolean
}

interface BenchmarkResult {
  status: string
  agent: string
  iterations: number
  successes: number
  total_time_ms: number
  latency: LatencyStats
  success_rate: number
  errors: string[]
  timestamp: string
}

interface DeterminismResult {
  determinism_score: number
  deterministic_prompts: number
  total_prompts: number
  iterations_per_prompt: number
  configuration: {
    temperature: number
    seed_method: string
  }
  results: Array<{
    prompt: string
    iterations: number
    unique_outputs: number
    unique_seeds: number
    is_deterministic: boolean
    sample_output: string
  }>
  passed: boolean
  timestamp: string
}

interface ValidationReport {
  generated_at: string
  system_configuration: {
    fast_agent: {
      model: string
      url: string
      temperature: number
      purpose: string
    }
    reasoning_agent: {
      model: string
      url: string
      temperature: number
      purpose: string
    }
    chat_mode: {
      temperature: number
      purpose: string
    }
  }
  latency_metrics: {
    fast_agent: LatencyStats
    reasoning_agent: LatencyStats
    disclaimer: string
  }
  accuracy_metrics: {
    annotation_accuracy: {
      value: string
      expected: string
      disclaimer: string
    }
    rca_accuracy: {
      value: string
      expected: string
      disclaimer: string
    }
  }
  validation_status: {
    latency: string
    determinism: string
    annotation_accuracy: string
    rca_accuracy: string
  }
}

const API_BASE_URL = '/api/v1/metrics'

const METRICS_TABS = [
  { id: 'overview',   label: 'Overview'   },
  { id: 'benchmark',  label: 'Benchmark'  },
  { id: 'validation', label: 'Validation' },
  { id: 'export',     label: 'Export'     },
] as const

type MetricsTab = (typeof METRICS_TABS)[number]['id']

export function Metrics() {
  const { showConfirm } = useToast()
  const [metrics, setMetrics] = useState<MetricsSnapshot | null>(null)
  const [latencyHistory, setLatencyHistory] = useState<LatencyRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  // Benchmark state
  const [benchmarkRunning, setBenchmarkRunning] = useState(false)
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkResult | null>(null)
  const [benchmarkAgent, setBenchmarkAgent] = useState<'fast' | 'reasoning'>('fast')
  const [benchmarkIterations, setBenchmarkIterations] = useState(10)

  // Determinism test state
  const [determinismRunning, setDeterminismRunning] = useState(false)
  const [determinismResult, setDeterminismResult] = useState<DeterminismResult | null>(null)

  // Validation report
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null)

  // Active tab
  const [activeTab, setActiveTab] = useState<MetricsTab>('overview')

  const fetchMetrics = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [metricsRes, historyRes] = await Promise.all([
        fetch(`${API_BASE_URL}`),
        fetch(`${API_BASE_URL}/history?limit=50`),
      ])

      if (!metricsRes.ok || !historyRes.ok) {
        throw new Error('Failed to fetch metrics')
      }

      const metricsData = await metricsRes.json()
      const historyData = await historyRes.json()

      setMetrics(metricsData)
      setLatencyHistory(historyData.records || [])
      setLastRefresh(new Date())
    } catch (err) {
      console.error('Metrics fetch error:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchValidationReport = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/validation/report`)
      if (res.ok) {
        const data = await res.json()
        setValidationReport(data)
      }
    } catch (err) {
      console.error('Validation report fetch error:', err)
    }
  }, [])

  useEffect(() => {
    fetchMetrics()
    fetchValidationReport()
    const interval = setInterval(fetchMetrics, 30000)
    return () => clearInterval(interval)
  }, [fetchMetrics, fetchValidationReport])

  const runBenchmark = async () => {
    setBenchmarkRunning(true)
    setBenchmarkResult(null)
    try {
      const res = await fetch(`${API_BASE_URL}/benchmark`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent: benchmarkAgent,
          iterations: benchmarkIterations,
          prompt: benchmarkAgent === 'fast'
            ? 'Classify this log: ERROR Connection timeout to database server'
            : 'Analyze root cause: Database connection pool exhausted, API latency spike, payment failures',
        }),
      })

      if (!res.ok) throw new Error('Benchmark failed')

      const data = await res.json()
      setBenchmarkResult(data)
      fetchMetrics() // Refresh metrics after benchmark
    } catch (err) {
      console.error('Benchmark error:', err)
      setError(err instanceof Error ? err.message : 'Benchmark failed')
    } finally {
      setBenchmarkRunning(false)
    }
  }

  const runDeterminismTest = async () => {
    setDeterminismRunning(true)
    setDeterminismResult(null)
    try {
      const res = await fetch(`${API_BASE_URL}/validate/determinism?iterations=5`, {
        method: 'POST',
      })

      if (!res.ok) throw new Error('Determinism test failed')

      const data = await res.json()
      setDeterminismResult(data)
    } catch (err) {
      console.error('Determinism test error:', err)
      setError(err instanceof Error ? err.message : 'Determinism test failed')
    } finally {
      setDeterminismRunning(false)
    }
  }

  const clearMetrics = async () => {
    const confirmed = await showConfirm(
      'Clear all metrics history?',
      'This will permanently delete all recorded latency and request data. This cannot be undone.'
    )
    if (!confirmed) return

    try {
      const res = await fetch(`${API_BASE_URL}/clear`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to clear metrics')
      fetchMetrics()
    } catch (err) {
      console.error('Clear metrics error:', err)
      setError(err instanceof Error ? err.message : 'Failed to clear metrics')
    }
  }

  const exportMetrics = async (format: 'json' | 'csv') => {
    try {
      const res = await fetch(`${API_BASE_URL}/export?format=${format}`)
      if (!res.ok) throw new Error('Export failed')

      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `metrics_${new Date().toISOString().split('T')[0]}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Export error:', err)
      setError(err instanceof Error ? err.message : 'Export failed')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            Metrics & Validation
          </h1>
          <p className="text-muted-foreground">
            LLM performance metrics, benchmarking, and validation
          </p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs text-muted-foreground">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </span>
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="p-2 rounded-lg hover:bg-muted disabled:opacity-50"
            aria-label="Refresh metrics"
            title="Refresh"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
            ) : (
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-600 text-sm">
          Error: {error}
        </div>
      )}

      {/* Accessible Tabs */}
      <Tabs
        value={activeTab}
        onChange={(id) => setActiveTab(id as MetricsTab)}
        tabs={METRICS_TABS}
      >
      {/* Tab Content */}
      <TabPanel id="overview" activeTab={activeTab} className="pt-6">
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MetricCard
              title="Total Requests"
              value={metrics?.total_requests?.toString() || '0'}
              icon={Zap}
              color="text-primary"
            />
            <MetricCard
              title="Success Rate"
              value={`${metrics?.success_rate?.toFixed(1) || '100'}%`}
              icon={CheckCircle}
              color={
                (metrics?.success_rate || 100) >= 95
                  ? 'text-green-500'
                  : (metrics?.success_rate || 100) >= 80
                    ? 'text-yellow-500'
                    : 'text-red-500'
              }
            />
            <MetricCard
              title="Fast Agent Avg"
              value={`${metrics?.fast_agent?.avg_ms?.toFixed(0) || '0'}ms`}
              icon={Clock}
              color="text-primary"
            />
            <MetricCard
              title="Reasoning Agent Avg"
              value={`${metrics?.reasoning_agent?.avg_ms?.toFixed(0) || '0'}ms`}
              icon={Clock}
              color="text-primary"
            />
          </div>

          {/* Agent Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <AgentStatsCard
              title="Fast Agent (Qwen3-4B)"
              stats={metrics?.fast_agent}
              color="cyan"
            />
            <AgentStatsCard
              title="Reasoning Agent (Qwen3-14B)"
              stats={metrics?.reasoning_agent}
              color="purple"
            />
          </div>

          {/* Determinism Config */}
          <div className="bg-card rounded-lg border border-border p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Gauge className="h-5 w-5" />
              Determinism Configuration
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground">Fast Agent Temperature</p>
                <p className="text-2xl font-bold">{metrics?.determinism_config?.fast_agent_temperature ?? 0.0}</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground">Reasoning Agent Temperature</p>
                <p className="text-2xl font-bold">{metrics?.determinism_config?.reasoning_agent_temperature ?? 0.0}</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground">Chat Temperature</p>
                <p className="text-2xl font-bold">{metrics?.determinism_config?.chat_temperature ?? 0.5}</p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-4">
              Seed method: {metrics?.determinism_config?.seed_method || 'hash(prompt) % 2^32'}
            </p>
          </div>

          {/* Recent Latency History */}
          <div className="bg-card rounded-lg border border-border p-6">
            <h2 className="text-lg font-semibold mb-4">Recent Requests</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 px-3">Agent</th>
                    <th className="text-left py-2 px-3">Latency</th>
                    <th className="text-left py-2 px-3">Tokens</th>
                    <th className="text-left py-2 px-3">Status</th>
                    <th className="text-left py-2 px-3">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {latencyHistory.length > 0 ? (
                    latencyHistory.slice(0, 10).map((record, idx) => (
                      <tr key={idx} className="border-b border-border/50">
                        <td className="py-2 px-3">
                          <span className={cn(
                            'px-2 py-0.5 rounded text-xs',
                            record.agent === 'fast'
                              ? 'bg-primary/10 text-primary'
                              : 'bg-primary/20 text-primary'
                          )}>
                            {record.agent}
                          </span>
                        </td>
                        <td className="py-2 px-3">{record.latency_ms != null ? `${record.latency_ms.toFixed(1)}ms` : '—'}</td>
                        <td className="py-2 px-3">{record.tokens_generated}</td>
                        <td className="py-2 px-3">
                          {record.success ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-500" />
                          )}
                        </td>
                        <td className="py-2 px-3 text-muted-foreground">
                          {new Date(record.timestamp).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-muted-foreground">
                        No request history yet. Run a benchmark to generate data.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </TabPanel>

      <TabPanel id="benchmark" activeTab={activeTab} className="pt-6">
        <div className="space-y-6">
          {/* Benchmark Controls */}
          <div className="bg-card rounded-lg border border-border p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Play className="h-5 w-5" />
              Run Benchmark
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium mb-2">Agent</label>
                <select
                  value={benchmarkAgent}
                  onChange={(e) => setBenchmarkAgent(e.target.value as 'fast' | 'reasoning')}
                  className="w-full p-2 rounded-lg bg-muted border border-border"
                >
                  <option value="fast">Fast Agent (Qwen3-4B)</option>
                  <option value="reasoning">Reasoning Agent (Qwen3-14B)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Iterations</label>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={benchmarkIterations}
                  onChange={(e) => setBenchmarkIterations(parseInt(e.target.value) || 10)}
                  className="w-full p-2 rounded-lg bg-muted border border-border"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={runBenchmark}
                  disabled={benchmarkRunning}
                  className={cn(
                    'w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg',
                    'bg-primary text-primary-foreground hover:bg-primary/90',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  {benchmarkRunning ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Run Benchmark
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Benchmark Results */}
          {benchmarkResult && (
            <div className="bg-card rounded-lg border border-border p-6">
              <h2 className="text-lg font-semibold mb-4">Benchmark Results</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                <div className="p-4 bg-muted/50 rounded-lg">
                  <p className="text-sm text-muted-foreground">Agent</p>
                  <p className="text-xl font-bold capitalize">{benchmarkResult.agent}</p>
                </div>
                <div className="p-4 bg-muted/50 rounded-lg">
                  <p className="text-sm text-muted-foreground">Iterations</p>
                  <p className="text-xl font-bold">{benchmarkResult.iterations}</p>
                </div>
                <div className="p-4 bg-muted/50 rounded-lg">
                  <p className="text-sm text-muted-foreground">Success Rate</p>
                  <p className={cn(
                    'text-xl font-bold',
                    benchmarkResult.success_rate >= 95 ? 'text-green-500' : 'text-yellow-500'
                  )}>
                    {benchmarkResult.success_rate}%
                  </p>
                </div>
                <div className="p-4 bg-muted/50 rounded-lg">
                  <p className="text-sm text-muted-foreground">Total Time</p>
                  <p className="text-xl font-bold">{(benchmarkResult.total_time_ms / 1000).toFixed(2)}s</p>
                </div>
              </div>

              <h3 className="font-semibold mb-2">Latency Statistics</h3>
              <div className="grid grid-cols-2 md:grid-cols-7 gap-4">
                <LatencyStat label="Avg" value={benchmarkResult.latency.avg_ms} />
                <LatencyStat label="Min" value={benchmarkResult.latency.min_ms} />
                <LatencyStat label="Max" value={benchmarkResult.latency.max_ms} />
                <LatencyStat label="P50" value={benchmarkResult.latency.p50_ms} />
                <LatencyStat label="P95" value={benchmarkResult.latency.p95_ms} />
                <LatencyStat label="P99" value={benchmarkResult.latency.p99_ms} />
              </div>

              {benchmarkResult.errors.length > 0 && (
                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <p className="text-sm font-medium text-red-600">Errors:</p>
                  <ul className="text-xs text-red-600 mt-1">
                    {benchmarkResult.errors.map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Determinism Test */}
          <div className="bg-card rounded-lg border border-border p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <TestTube className="h-5 w-5" />
              Determinism Validation
            </h2>
            <p className="text-sm text-muted-foreground mb-4">
              Tests if identical inputs produce identical outputs with temperature=0
            </p>
            <button
              onClick={runDeterminismTest}
              disabled={determinismRunning}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg',
                'bg-secondary text-secondary-foreground hover:bg-secondary/80',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {determinismRunning ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <TestTube className="h-4 w-4" />
                  Run Determinism Test
                </>
              )}
            </button>

            {determinismResult && (
              <div className="mt-4">
                <div className="flex items-center gap-4 mb-4">
                  <div className={cn(
                    'text-3xl font-bold',
                    determinismResult.passed ? 'text-green-500' : 'text-yellow-500'
                  )}>
                    {determinismResult.determinism_score}%
                  </div>
                  <div>
                    <p className="font-medium">Determinism Score</p>
                    <p className="text-sm text-muted-foreground">
                      {determinismResult.deterministic_prompts}/{determinismResult.total_prompts} prompts consistent
                    </p>
                  </div>
                  {determinismResult.passed ? (
                    <CheckCircle className="h-6 w-6 text-green-500" />
                  ) : (
                    <XCircle className="h-6 w-6 text-yellow-500" />
                  )}
                </div>

                <div className="space-y-2">
                  {determinismResult.results.map((result, idx) => (
                    <div
                      key={idx}
                      className={cn(
                        'p-3 rounded-lg border',
                        result.is_deterministic
                          ? 'bg-green-500/5 border-green-500/20'
                          : 'bg-yellow-500/5 border-yellow-500/20'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{result.prompt}</span>
                        <span className={cn(
                          'text-xs px-2 py-0.5 rounded',
                          result.is_deterministic
                            ? 'bg-green-500/10 text-green-500'
                            : 'bg-yellow-500/10 text-yellow-500'
                        )}>
                          {result.unique_outputs} unique output{result.unique_outputs > 1 ? 's' : ''}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </TabPanel>

      <TabPanel id="validation" activeTab={activeTab} className="pt-6">
        <div className="space-y-6">
          {validationReport ? (
            <>
              {/* System Configuration */}
              <div className="bg-card rounded-lg border border-border p-6">
                <h2 className="text-lg font-semibold mb-4">System Configuration</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <ConfigCard
                    title="Fast Agent"
                    model={validationReport.system_configuration.fast_agent.model}
                    temperature={validationReport.system_configuration.fast_agent.temperature}
                    purpose={validationReport.system_configuration.fast_agent.purpose}
                    color="cyan"
                  />
                  <ConfigCard
                    title="Reasoning Agent"
                    model={validationReport.system_configuration.reasoning_agent.model}
                    temperature={validationReport.system_configuration.reasoning_agent.temperature}
                    purpose={validationReport.system_configuration.reasoning_agent.purpose}
                    color="purple"
                  />
                  <ConfigCard
                    title="Chat Mode"
                    model="Qwen3-14B"
                    temperature={validationReport.system_configuration.chat_mode.temperature}
                    purpose={validationReport.system_configuration.chat_mode.purpose}
                    color="blue"
                  />
                </div>
              </div>

              {/* Validation Status */}
              <div className="bg-card rounded-lg border border-border p-6">
                <h2 className="text-lg font-semibold mb-4">Validation Status</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(validationReport.validation_status).map(([key, value]) => (
                    <div key={key} className="p-4 bg-muted/50 rounded-lg">
                      <p className="text-sm text-muted-foreground capitalize">
                        {key.replace(/_/g, ' ')}
                      </p>
                      <p className={cn(
                        'text-lg font-medium',
                        value === 'Measured' || value.includes('Configured')
                          ? 'text-green-500'
                          : value === 'Pending'
                            ? 'text-yellow-500'
                            : 'text-muted-foreground'
                      )}>
                        {value}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Accuracy Metrics (with disclaimers) */}
              <div className="bg-card rounded-lg border border-border p-6">
                <h2 className="text-lg font-semibold mb-4">Accuracy Metrics</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
                    <p className="font-medium">Annotation Accuracy</p>
                    <p className="text-2xl font-bold text-yellow-500 mt-1">
                      {validationReport.accuracy_metrics.annotation_accuracy.value}
                    </p>
                    <p className="text-sm text-muted-foreground mt-2">
                      Expected: {validationReport.accuracy_metrics.annotation_accuracy.expected}
                    </p>
                    <p className="text-xs text-yellow-600/80 mt-1">
                      {validationReport.accuracy_metrics.annotation_accuracy.disclaimer}
                    </p>
                  </div>
                  <div className="p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
                    <p className="font-medium">RCA Accuracy</p>
                    <p className="text-2xl font-bold text-yellow-500 mt-1">
                      {validationReport.accuracy_metrics.rca_accuracy.value}
                    </p>
                    <p className="text-sm text-muted-foreground mt-2">
                      Expected: {validationReport.accuracy_metrics.rca_accuracy.expected}
                    </p>
                    <p className="text-xs text-yellow-600/80 mt-1">
                      {validationReport.accuracy_metrics.rca_accuracy.disclaimer}
                    </p>
                  </div>
                </div>
              </div>

              {/* Latency Disclaimer */}
              <div className="p-4 bg-muted/50 rounded-lg text-sm text-muted-foreground">
                <p className="font-medium mb-1">Latency Measurement Disclaimer</p>
                <p>{validationReport.latency_metrics.disclaimer}</p>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Loader2 className="h-8 w-8 motion-safe:animate-spin mx-auto mb-4" />
              Loading validation report...
            </div>
          )}
        </div>
      </TabPanel>

      <TabPanel id="export" activeTab={activeTab} className="pt-6">
        <div className="space-y-6">
          <div className="bg-card rounded-lg border border-border p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Download className="h-5 w-5" />
              Export Metrics
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              Download metrics data for research documentation and analysis
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => exportMetrics('json')}
                className="flex items-center justify-center gap-3 p-6 rounded-lg border border-border hover:bg-muted/50 transition-colors"
              >
                <FileJson className="h-8 w-8 text-primary" />
                <div className="text-left">
                  <p className="font-medium">Export as JSON</p>
                  <p className="text-sm text-muted-foreground">
                    Full metrics with metadata
                  </p>
                </div>
              </button>
              <button
                onClick={() => exportMetrics('csv')}
                className="flex items-center justify-center gap-3 p-6 rounded-lg border border-border hover:bg-muted/50 transition-colors"
              >
                <FileSpreadsheet className="h-8 w-8 text-green-500" />
                <div className="text-left">
                  <p className="font-medium">Export as CSV</p>
                  <p className="text-sm text-muted-foreground">
                    Tabular format for spreadsheets
                  </p>
                </div>
              </button>
            </div>
          </div>

          <div className="bg-card rounded-lg border border-border p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-red-500">
              <Trash2 className="h-5 w-5" />
              Clear Metrics
            </h2>
            <p className="text-sm text-muted-foreground mb-4">
              Remove all latency history and reset counters. This action cannot be undone.
            </p>
            <button
              onClick={clearMetrics}
              className="px-4 py-2 rounded-lg bg-red-500 text-white hover:bg-red-600"
            >
              Clear All Metrics
            </button>
          </div>
        </div>
      </TabPanel>
      </Tabs>
    </div>
  )
}

function MetricCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string
  value: string
  icon: React.ElementType
  color: string
}) {
  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">{title}</span>
        <Icon className={cn('h-5 w-5', color)} />
      </div>
      <div className="mt-2">
        <span className="text-2xl font-bold">{value}</span>
      </div>
    </div>
  )
}

function AgentStatsCard({
  title,
  stats,
  color,
}: {
  title: string
  stats?: LatencyStats
  color: 'cyan' | 'purple'
}) {
  const colorClasses = color === 'cyan'
    ? 'border-primary/20 bg-primary/5'
    : 'border-primary/30 bg-primary/10'

  return (
    <div className={cn('rounded-lg border p-6', colorClasses)}>
      <h3 className="font-semibold mb-4">{title}</h3>
      {stats && stats.count > 0 ? (
        <div className="grid grid-cols-3 gap-4">
          <LatencyStat label="Requests" value={stats.count} isCount />
          <LatencyStat label="Avg" value={stats.avg_ms} />
          <LatencyStat label="P50" value={stats.p50_ms} />
          <LatencyStat label="P95" value={stats.p95_ms} />
          <LatencyStat label="P99" value={stats.p99_ms} />
          <LatencyStat label="Success" value={stats.success_rate} isPercent />
        </div>
      ) : (
        <p className="text-muted-foreground text-sm">No data yet</p>
      )}
    </div>
  )
}

function LatencyStat({
  label,
  value,
  isCount = false,
  isPercent = false,
}: {
  label: string
  value: number
  isCount?: boolean
  isPercent?: boolean
}) {
  const displayValue = isCount
    ? value.toString()
    : isPercent
      ? `${value.toFixed(1)}%`
      : `${value.toFixed(0)}ms`

  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{displayValue}</p>
    </div>
  )
}

function ConfigCard({
  title,
  model,
  temperature,
  purpose,
  color,
}: {
  title: string
  model: string
  temperature: number
  purpose: string
  color: 'cyan' | 'purple' | 'blue'
}) {
  const colorClasses = {
    cyan: 'border-primary/20 bg-primary/5',
    purple: 'border-primary/30 bg-primary/10',
    blue: 'border-primary/25 bg-primary/[0.07]',
  }

  return (
    <div className={cn('rounded-lg border p-4', colorClasses[color])}>
      <h3 className="font-semibold mb-2">{title}</h3>
      <div className="space-y-1 text-sm">
        <p><span className="text-muted-foreground">Model:</span> {model}</p>
        <p><span className="text-muted-foreground">Temperature:</span> {temperature}</p>
        <p><span className="text-muted-foreground">Purpose:</span> {purpose}</p>
      </div>
    </div>
  )
}

export default Metrics
