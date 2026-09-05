import { useState, useEffect, useCallback } from 'react'
import {
  Server,
  Box,
  X,
  Play,
  RefreshCw,
  Loader2,
  Radio,
  Copy,
  Check,
  Terminal,
  Link2,
  ExternalLink,
  Search,
  Wifi,
  WifiOff,
  HelpCircle,
  Trash2,
  Zap,
  HeartPulse,
  AlertTriangle,
  Save,
} from 'lucide-react'
import apiClient, { ApiError } from '../lib/api'
import type { DemoScenario, DemoStatus } from '../lib/api'
import { useToast } from '../components/ui/toast'

// Container info type (moved from Agents.tsx)
interface ContainerInfo {
  name: string
  service: string
  status: string
  health: string | null
  port: string | null
  image: string | null
  description: string | null
  monitored: boolean
}

interface InfrastructureStats {
  total: number
  healthy: number
  unhealthy: number
}

// Remote host (edge agent) types
interface RemoteHost {
  edge_label: string
  status: 'up' | 'down' | 'unknown'
  targets_up: number
  targets_total: number
  recent_log_lines: number
  last_seen: string | null
}

interface RemoteHostsResponse {
  hosts: RemoteHost[]
  total: number
  source: string
}

// Telemetry "verify" response (best-effort). Never `any`.
interface TelemetryLogsResponse {
  logs?: unknown[]
}

type VerifyState = 'idle' | 'checking' | 'seen' | 'not-yet'

/** Returns true when the container is part of our own aiops platform stack. */
function isPlatformContainer(name: string): boolean {
  return name.startsWith('aiops-')
}

export function Infrastructure() {
  const { showToast, showConfirm } = useToast()

  // --- Local container monitoring state (moved from Agents.tsx) ---
  const [containers, setContainers] = useState<ContainerInfo[]>([])
  const [containersLoading, setContainersLoading] = useState(false)
  const [infrastructureStats, setInfrastructureStats] = useState<InfrastructureStats | null>(null)
  const [selectedContainers, setSelectedContainers] = useState<Set<string>>(new Set())
  const [monitoringStarting, setMonitoringStarting] = useState(false)

  // --- Remote (edge) host state ---
  const [remoteHosts, setRemoteHosts] = useState<RemoteHost[]>([])
  const [remoteHostsLoading, setRemoteHostsLoading] = useState(false)

  // --- Demo / Chaos panel state (t3 demo agent orchestration) ---
  const [demoScenarios, setDemoScenarios] = useState<DemoScenario[]>([])
  const [demoStatus, setDemoStatus] = useState<DemoStatus | null>(null)
  // Demo/chaos mode is disabled on lite / bring-your-own-endpoint deployments
  // (the backend returns 403). When that happens we hide the whole panel and
  // stop polling instead of logging console errors on every tick.
  const [demoAvailable, setDemoAvailable] = useState(true)
  /** Per-scenario in-flight flag, keyed by `${scenarioId}:${action}`. */
  const [demoBusy, setDemoBusy] = useState<Record<string, boolean>>({})
  const [demoTargetInput, setDemoTargetInput] = useState<string>('')
  const [demoTargetSaving, setDemoTargetSaving] = useState(false)

  // --- Guided edge onboarding state (NEW, frontend-only, no persisted secrets) ---
  const origin = typeof window !== 'undefined' ? window.location.origin : ''
  const defaultHost = typeof window !== 'undefined' ? window.location.host : 'aiops.example.com'
  const [domain, setDomain] = useState<string>(defaultHost)
  const [edgeLabel, setEdgeLabel] = useState<string>('remote-host-1')
  const [ingestUser, setIngestUser] = useState<string>('edge')
  const [ingestPass, setIngestPass] = useState<string>('') // session-only, never persisted
  const [copied, setCopied] = useState<string | null>(null)
  const [verifyState, setVerifyState] = useState<VerifyState>('idle')

  // Build ingest URLs from the (editable) domain. https assumed for the public host.
  const scheme = origin.startsWith('http://') ? 'http' : 'https'
  const base = `${scheme}://${domain}`
  const lokiPushUrl = `${base}/ingest/loki/loki/api/v1/push`
  const promRwUrl = `${base}/ingest/prom/api/v1/write`
  const otlpHttpUrl = `${base}/ingest/otlp`
  const grafanaUrl = `${origin}/grafana/`

  // --- Container fetch (moved verbatim from Agents.tsx) ---
  const fetchContainers = useCallback(async () => {
    setContainersLoading(true)
    try {
      const response = await fetch('/api/v1/infrastructure/containers')
      if (response.ok) {
        const data = await response.json()
        // Sort containers: monitored first, then by name
        const sortedContainers = (data.containers || []).sort((a: ContainerInfo, b: ContainerInfo) => {
          if (a.monitored && !b.monitored) return -1
          if (!a.monitored && b.monitored) return 1
          return a.name.localeCompare(b.name)
        })
        setContainers(sortedContainers)
        setInfrastructureStats({
          total: data.total || 0,
          healthy: data.healthy || 0,
          unhealthy: data.unhealthy || 0,
        })
      } else {
        setContainers([])
        setInfrastructureStats(null)
      }
    } catch (err) {
      console.error('Failed to fetch containers:', err)
      setContainers([])
      setInfrastructureStats(null)
    } finally {
      setContainersLoading(false)
    }
  }, [])

  const fetchRemoteHosts = useCallback(async () => {
    setRemoteHostsLoading(true)
    try {
      const response = await fetch('/api/v1/infrastructure/remote-hosts')
      if (response.ok) {
        const data: RemoteHostsResponse = await response.json()
        setRemoteHosts(data.hosts || [])
      } else {
        setRemoteHosts([])
      }
    } catch (err) {
      console.error('Failed to fetch remote hosts:', err)
      setRemoteHosts([])
    } finally {
      setRemoteHostsLoading(false)
    }
  }, [])

  const dismissRemoteHost = useCallback(async (edgeLabel: string) => {
    const confirmed = await showConfirm(
      `Remove "${edgeLabel}" from the monitored hosts list?`,
      'The list is auto-derived from live telemetry. If this host keeps shipping logs it will reappear until restored.'
    )
    if (!confirmed) return

    try {
      const response = await fetch(
        `/api/v1/infrastructure/remote-hosts/${encodeURIComponent(edgeLabel)}`,
        { method: 'DELETE' }
      )
      if (response.ok) {
        setRemoteHosts((prev) => prev.filter((h) => h.edge_label !== edgeLabel))
      } else {
        console.error('Failed to dismiss host:', response.status)
      }
    } catch (err) {
      console.error('Failed to dismiss host:', err)
    }
  }, [showConfirm])

  // --- Demo / Chaos: scenario catalog + live status ---
  const fetchDemoScenarios = useCallback(async () => {
    try {
      const data = await apiClient.demo.scenarios()
      setDemoScenarios(data.scenarios || [])
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) { setDemoAvailable(false); return }
      console.error('Failed to fetch demo scenarios:', err)
    }
  }, [])

  const fetchDemoStatus = useCallback(async () => {
    try {
      const data = await apiClient.demo.status()
      setDemoStatus(data)
      // Seed the editable target URL once from the server (don't clobber edits).
      setDemoTargetInput((prev) => (prev ? prev : data.target_url || ''))
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) { setDemoAvailable(false); setDemoStatus(null); return }
      console.error('Failed to fetch demo status:', err)
      setDemoStatus(null)
    }
  }, [])

  const runDemoChaos = useCallback(
    async (scenarioId: string, action: 'start' | 'heal') => {
      const key = `${scenarioId}:${action}`
      setDemoBusy((prev) => ({ ...prev, [key]: true }))
      try {
        if (action === 'start') await apiClient.demo.start(scenarioId)
        else await apiClient.demo.heal(scenarioId)
        // Refresh status so the badge reflects the new scenario state.
        await fetchDemoStatus()
      } catch (err) {
        console.error(`Failed to ${action} scenario ${scenarioId}:`, err)
      } finally {
        setDemoBusy((prev) => ({ ...prev, [key]: false }))
      }
    },
    [fetchDemoStatus],
  )

  const saveDemoTarget = useCallback(async () => {
    setDemoTargetSaving(true)
    try {
      await apiClient.demo.setTarget(demoTargetInput.trim())
      await fetchDemoStatus()
    } catch (err) {
      console.error('Failed to set demo target:', err)
    } finally {
      setDemoTargetSaving(false)
    }
  }, [demoTargetInput, fetchDemoStatus])

  useEffect(() => {
    fetchContainers()
    fetchRemoteHosts()
  }, [fetchContainers, fetchRemoteHosts])

  // Load the demo scenario catalog once, then poll live status every 8s while
  // the panel is mounted (cleared on unmount).
  useEffect(() => {
    if (!demoAvailable) return
    fetchDemoScenarios()
    fetchDemoStatus()
    const id = setInterval(() => {
      void fetchDemoStatus()
    }, 8000)
    return () => clearInterval(id)
  }, [demoAvailable, fetchDemoScenarios, fetchDemoStatus])

  // --- Selection + monitoring handlers (moved verbatim) ---
  const toggleContainerSelection = (containerName: string) => {
    setSelectedContainers(prev => {
      const newSet = new Set(prev)
      if (newSet.has(containerName)) {
        newSet.delete(containerName)
      } else {
        newSet.add(containerName)
      }
      return newSet
    })
  }

  const selectAllContainers = () => {
    setSelectedContainers(new Set(containers.map(c => c.name)))
  }

  const deselectAllContainers = () => {
    setSelectedContainers(new Set())
  }

  const startMonitoring = async () => {
    if (selectedContainers.size === 0) return

    setMonitoringStarting(true)
    try {
      const response = await fetch('/api/v1/infrastructure/monitor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          containers: Array.from(selectedContainers),
        }),
      })

      if (response.ok) {
        setSelectedContainers(new Set())
        await fetchContainers()
      } else {
        const data = await response.json()
        showToast(`Failed to start monitoring: ${data.message || 'Unknown error'}`, 'error')
      }
    } catch (err) {
      console.error('Failed to start monitoring:', err)
      showToast(`Failed to start monitoring: ${err instanceof Error ? err.message : 'Unknown error'}`, 'error')
    } finally {
      setMonitoringStarting(false)
    }
  }

  const stopMonitoring = async (containerName: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      const response = await fetch(`/api/v1/infrastructure/containers/${containerName}/monitor`, {
        method: 'DELETE',
      })

      if (response.ok) {
        await fetchContainers()
      } else {
        const data = await response.json()
        showToast(`Failed to stop monitoring: ${data.message || 'Unknown error'}`, 'error')
      }
    } catch (err) {
      console.error('Failed to stop monitoring:', err)
      showToast(`Failed to stop monitoring: ${err instanceof Error ? err.message : 'Unknown error'}`, 'error')
    }
  }

  // --- Edge onboarding helpers ---
  // Generated .env mirrors monitoring-agent/.env.example keys exactly.
  const passValue = ingestPass.trim()
    ? ingestPass
    : 'CHANGE_ME_match_the_server_ingest_password'
  const envBlock = [
    `EDGE_LABEL=${edgeLabel || 'remote-host-1'}`,
    `INGEST_USER=${ingestUser || 'edge'}`,
    `INGEST_PASS=${passValue}`,
    `LOKI_PUSH_URL=${lokiPushUrl}`,
    `PROM_RW_URL=${promRwUrl}`,
    `OTLP_HTTP_URL=${otlpHttpUrl}`,
  ].join('\n')

  const composeQuickstart = [
    'cd monitoring-agent',
    'cp .env.example .env',
    '# set EDGE_LABEL / INGEST_USER / INGEST_PASS to match the values above',
    'docker compose up -d',
    'docker compose logs -f alloy   # expect no 401/403 on push',
  ].join('\n')

  const logqlCheck = `{edge="${edgeLabel || 'remote-host-1'}"}`
  const promqlCheck = `up{edge="${edgeLabel || 'remote-host-1'}"}`

  const copy = async (key: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(key)
      window.setTimeout(() => setCopied(prev => (prev === key ? null : prev)), 1500)
    } catch (err) {
      console.error('Clipboard write failed:', err)
    }
  }

  // Best-effort verify: hit the telemetry logs endpoint filtered by the edge label.
  const runVerify = async () => {
    setVerifyState('checking')
    try {
      const q = encodeURIComponent(logqlCheck)
      const response = await fetch(`/api/v1/telemetry/logs?query=${q}&limit=5`)
      if (!response.ok) {
        setVerifyState('not-yet')
        return
      }
      const data: TelemetryLogsResponse = await response.json()
      const seen = Array.isArray(data.logs) && data.logs.length > 0
      setVerifyState(seen ? 'seen' : 'not-yet')
    } catch (err) {
      console.error('Verify failed:', err)
      setVerifyState('not-yet')
    }
  }

  return (
    <div className="space-y-6">
      {/* A) Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Server className="h-6 w-6 text-green-500" />
            Infrastructure
          </h1>
          <p className="text-muted-foreground">
            Monitor local Docker containers and onboard remote hosts
          </p>
        </div>
        <button
          onClick={() => { fetchContainers(); fetchRemoteHosts() }}
          disabled={containersLoading || remoteHostsLoading}
          className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg text-sm hover:bg-muted/80 disabled:opacity-50"
        >
          {(containersLoading || remoteHostsLoading) ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Refresh
        </button>
      </div>

      {/* B) Local container monitoring */}
      <div className="space-y-4">
        {/* Infrastructure Stats */}
        {infrastructureStats && (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-card rounded-lg border border-border p-4 text-center">
              <p className="text-3xl font-bold">{infrastructureStats.total}</p>
              <p className="text-sm text-muted-foreground">Total Containers</p>
            </div>
            <div className="bg-card rounded-lg border border-border p-4 text-center">
              <p className="text-3xl font-bold text-green-500">{infrastructureStats.healthy}</p>
              <p className="text-sm text-muted-foreground">Healthy</p>
            </div>
            <div className="bg-card rounded-lg border border-border p-4 text-center">
              <p className="text-3xl font-bold text-red-500">{infrastructureStats.unhealthy}</p>
              <p className="text-sm text-muted-foreground">Unhealthy</p>
            </div>
          </div>
        )}

        {/* Container List — split into Platform (aiops-*) vs Client/other */}
        <div className="bg-card rounded-lg border border-border">
          <div className="p-4 border-b border-border">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="font-semibold flex items-center gap-2">
                <Box className="h-4 w-4" />
                Docker Containers
                {selectedContainers.size > 0 && (
                  <span className="ml-2 px-2 py-0.5 bg-primary/10 text-primary rounded-full text-xs">
                    {selectedContainers.size} selected
                  </span>
                )}
              </h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={selectAllContainers}
                  className="px-2 py-1 text-xs bg-muted rounded hover:bg-muted/80"
                >
                  Select All
                </button>
                <button
                  onClick={deselectAllContainers}
                  className="px-2 py-1 text-xs bg-muted rounded hover:bg-muted/80"
                >
                  Deselect All
                </button>
              </div>
            </div>
          </div>

          {containersLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : containers.length > 0 ? (
            (() => {
              const platformContainers = containers.filter(c => isPlatformContainer(c.name))
              const clientContainers = containers.filter(c => !isPlatformContainer(c.name))

              const renderContainer = (container: ContainerInfo) => (
                <div
                  key={container.name}
                  className={`p-4 hover:bg-muted/50 cursor-pointer ${
                    selectedContainers.has(container.name) ? 'bg-primary/5' : ''
                  }`}
                  onClick={() => toggleContainerSelection(container.name)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={selectedContainers.has(container.name)}
                        onChange={() => toggleContainerSelection(container.name)}
                        onClick={(e) => e.stopPropagation()}
                        className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                      />
                      <div className={`p-2 rounded-lg ${
                        container.health === 'healthy' ? 'bg-green-500/10' :
                        container.health === 'unhealthy' ? 'bg-red-500/10' :
                        'bg-yellow-500/10'
                      }`}>
                        <Box className={`h-5 w-5 ${
                          container.health === 'healthy' ? 'text-green-500' :
                          container.health === 'unhealthy' ? 'text-red-500' :
                          'text-yellow-500'
                        }`} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold">{container.name}</h4>
                          {container.monitored && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary/10 text-primary rounded-full text-xs font-medium">
                              Monitoring
                              <button
                                onClick={(e) => stopMonitoring(container.name, e)}
                                className="ml-1 p-0.5 hover:bg-primary/20 rounded"
                                title="Stop monitoring"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">{container.description}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        container.health === 'healthy' ? 'bg-green-500/10 text-green-500' :
                        container.health === 'unhealthy' ? 'bg-red-500/10 text-red-500' :
                        'bg-yellow-500/10 text-yellow-500'
                      }`}>
                        {container.health || 'unknown'}
                      </span>
                    </div>
                  </div>
                  <div className="mt-2 flex gap-4 text-xs text-muted-foreground">
                    {container.port && (
                      <span>Port: {container.port}</span>
                    )}
                    {container.image && (
                      <span>Image: {container.image}</span>
                    )}
                    <span>Service: {container.service}</span>
                  </div>
                </div>
              )

              return (
                <>
                  {/* Platform (this stack) */}
                  {platformContainers.length > 0 && (
                    <div>
                      <div className="px-4 py-2 bg-muted/30 border-b border-border flex items-center gap-2">
                        <Server className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          Platform (this stack)
                        </span>
                        <span className="ml-auto px-1.5 py-0.5 bg-primary/10 text-primary rounded text-xs">
                          {platformContainers.length}
                        </span>
                      </div>
                      <div className="divide-y divide-border">
                        {platformContainers.map(renderContainer)}
                      </div>
                    </div>
                  )}

                  {/* Client / other local containers */}
                  {clientContainers.length > 0 && (
                    <div>
                      <div className="px-4 py-2 bg-muted/30 border-b border-border flex items-center gap-2">
                        <Box className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          Other local containers
                        </span>
                        <span className="ml-auto px-1.5 py-0.5 bg-primary/10 text-primary rounded text-xs">
                          {clientContainers.length}
                        </span>
                      </div>
                      <div className="divide-y divide-border">
                        {clientContainers.map(renderContainer)}
                      </div>
                    </div>
                  )}
                </>
              )
            })()
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Server className="h-8 w-8 mb-2 opacity-50" />
              <p className="text-sm">No containers found</p>
              <p className="text-xs mt-1">Start the infrastructure to view containers</p>
            </div>
          )}

          {/* Start Monitoring Button */}
          {containers.length > 0 && (
            <div className="p-4 border-t border-border bg-muted/30">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm text-muted-foreground">
                  {selectedContainers.size === 0
                    ? 'Select containers to start monitoring'
                    : `${selectedContainers.size} container(s) selected for monitoring`}
                </p>
                <button
                  onClick={startMonitoring}
                  disabled={selectedContainers.size === 0 || monitoringStarting}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {monitoringStarting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  Start Monitoring
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Monitored Remote Hosts (from edge agents) */}
        <div className="bg-card rounded-lg border border-border">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2">
              <Radio className="h-4 w-4 text-primary" />
              Monitored remote hosts
              <span className="text-xs text-muted-foreground font-normal">(via Grafana Alloy edge agent)</span>
            </h3>
            {remoteHostsLoading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
          </div>
          <div className="divide-y divide-border">
            {remoteHostsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : remoteHosts.length > 0 ? (
              remoteHosts.map((host) => (
                <div key={host.edge_label} className="p-4 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`p-2 rounded-lg shrink-0 ${
                      host.status === 'up' ? 'bg-green-500/10' :
                      host.status === 'down' ? 'bg-red-500/10' :
                      'bg-yellow-500/10'
                    }`}>
                      {host.status === 'up'
                        ? <Wifi className="h-5 w-5 text-green-500" />
                        : host.status === 'down'
                          ? <WifiOff className="h-5 w-5 text-red-500" />
                          : <HelpCircle className="h-5 w-5 text-yellow-500" />
                      }
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-semibold font-mono text-sm">{host.edge_label}</h4>
                        <span className={`px-2 py-0.5 rounded-full text-xs ${
                          host.status === 'up' ? 'bg-green-500/10 text-green-500' :
                          host.status === 'down' ? 'bg-red-500/10 text-red-500' :
                          'bg-yellow-500/10 text-yellow-600'
                        }`}>
                          {host.status}
                        </span>
                      </div>
                      <div className="mt-1 flex flex-wrap gap-3 text-xs text-muted-foreground">
                        <span>Targets up: {host.targets_up}/{Math.max(host.targets_total, host.targets_up)}</span>
                        <span>Recent logs (15 min): {host.recent_log_lines}</span>
                        {host.last_seen && (
                          <span>Last seen: {new Date(host.last_seen).toLocaleString()}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => dismissRemoteHost(host.edge_label)}
                    title="Remove from monitored hosts"
                    aria-label={`Remove ${host.edge_label} from monitored hosts`}
                    className="shrink-0 p-2 rounded-lg text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center py-10 text-muted-foreground">
                <Radio className="h-8 w-8 mb-2 opacity-40" />
                <p className="text-sm">No remote hosts detected yet</p>
                <p className="text-xs mt-1 max-w-xs text-center">
                  Once a Grafana Alloy edge agent is running on a remote Linux host and shipping
                  telemetry here, it will appear automatically. Use the onboarding guide below.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* C) Guided edge onboarding */}
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Radio className="h-5 w-5 text-primary" />
            Monitor a Remote Host
          </h2>
          <p className="text-sm text-muted-foreground">
            Run one Grafana Alloy agent on any Linux Docker host to ship its container
            logs, metrics, and traces into this stack. Onboard the host once — all its
            containers (current and future) appear automatically.
          </p>
        </div>

        {/* Ingest endpoints */}
        <div className="bg-card rounded-lg border border-border p-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-semibold flex items-center gap-2">
              <Link2 className="h-4 w-4" />
              Ingest Endpoints
            </h3>
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              Domain
              <input
                type="text"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="px-2 py-1 rounded border border-border bg-background text-foreground text-xs focus:outline-none focus:ring-1 focus:ring-primary w-full sm:w-56"
              />
            </label>
          </div>
          <div className="space-y-2 text-sm">
            {[
              { label: 'Loki (logs)', url: lokiPushUrl, k: 'loki' },
              { label: 'Prometheus (metrics)', url: promRwUrl, k: 'prom' },
              { label: 'OTLP (traces)', url: otlpHttpUrl, k: 'otlp' },
            ].map(({ label, url, k }) => (
              <div key={k} className="flex items-center gap-2">
                <span className="w-40 shrink-0 text-xs text-muted-foreground">{label}</span>
                <code className="flex-1 px-2 py-1 bg-muted/50 rounded text-xs font-mono break-all">{url}</code>
                <button
                  type="button"
                  onClick={() => copy(k, url)}
                  className="p-1.5 bg-muted rounded hover:bg-muted/80"
                  title="Copy URL"
                >
                  {copied === k ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Edge form + generated .env */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-card rounded-lg border border-border p-4 space-y-3">
            <h3 className="font-semibold">Agent Configuration</h3>
            <div>
              <label className="block text-sm mb-1">Edge label</label>
              <input
                type="text"
                value={edgeLabel}
                onChange={(e) => setEdgeLabel(e.target.value)}
                placeholder="remote-host-1"
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <p className="text-xs text-muted-foreground mt-1">
                A short, stable name stamped onto every series as the <code>edge</code> label.
              </p>
            </div>
            <div>
              <label className="block text-sm mb-1">Ingest user</label>
              <input
                type="text"
                value={ingestUser}
                onChange={(e) => setIngestUser(e.target.value)}
                placeholder="edge"
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm mb-1">Ingest password</label>
              <input
                type="password"
                value={ingestPass}
                onChange={(e) => setIngestPass(e.target.value)}
                placeholder="Set the server ingest password"
                autoComplete="off"
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Session-only — never stored or sent anywhere. Must match the server&apos;s ingest credential.
              </p>
            </div>
          </div>

          {/* Generated .env */}
          <div className="bg-card rounded-lg border border-border p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Generated <code>.env</code></h3>
              <button
                type="button"
                onClick={() => copy('env', envBlock)}
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-muted rounded hover:bg-muted/80"
              >
                {copied === 'env' ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                Copy
              </button>
            </div>
            <pre className="p-3 bg-muted/50 rounded-lg text-xs font-mono overflow-x-auto whitespace-pre-wrap break-all">
              {envBlock}
            </pre>
          </div>
        </div>

        {/* Quickstart */}
        <div className="bg-card rounded-lg border border-border p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2">
              <Terminal className="h-4 w-4" />
              Quickstart (on the remote Linux host)
            </h3>
            <button
              type="button"
              onClick={() => copy('compose', composeQuickstart)}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-muted rounded hover:bg-muted/80"
            >
              {copied === 'compose' ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
              Copy
            </button>
          </div>
          <pre className="p-3 bg-muted/50 rounded-lg text-xs font-mono overflow-x-auto whitespace-pre-wrap">
            {composeQuickstart}
          </pre>
          <p className="text-xs text-muted-foreground">
            The agent is Linux-only (it bind-mounts the Docker socket). A Windows laptop cannot host it.
          </p>
        </div>

        {/* Verify */}
        <div className="bg-card rounded-lg border border-border p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2">
              <Search className="h-4 w-4" />
              Verify Telemetry Arrived
            </h3>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={runVerify}
                disabled={verifyState === 'checking'}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-muted rounded-lg hover:bg-muted/80 disabled:opacity-50"
              >
                {verifyState === 'checking' ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                Check now
              </button>
              <a
                href={grafanaUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-primary/10 text-primary rounded-lg hover:bg-primary/20"
              >
                <ExternalLink className="h-4 w-4" />
                Open Grafana
              </a>
            </div>
          </div>

          {verifyState === 'seen' && (
            <div className="flex items-center gap-2 p-2.5 bg-green-500/10 text-green-600 rounded-lg text-sm">
              <Check className="h-4 w-4" />
              Logs tagged <code className="mx-1">edge=&quot;{edgeLabel || 'remote-host-1'}&quot;</code> are arriving.
            </div>
          )}
          {verifyState === 'not-yet' && (
            <div className="p-2.5 bg-yellow-500/10 text-yellow-600 rounded-lg text-sm">
              No telemetry seen for this edge label yet. Give the agent ~30s after starting,
              then check again — or confirm in Grafana directly.
            </div>
          )}

          <div className="space-y-2 text-sm">
            <p className="text-xs text-muted-foreground">Manual checks in Grafana Explore:</p>
            <div className="flex items-center gap-2">
              <span className="w-24 shrink-0 text-xs text-muted-foreground">Loki (LogQL)</span>
              <code className="flex-1 px-2 py-1 bg-muted/50 rounded text-xs font-mono break-all">{logqlCheck}</code>
              <button
                type="button"
                onClick={() => copy('logql', logqlCheck)}
                className="p-1.5 bg-muted rounded hover:bg-muted/80"
                title="Copy LogQL"
              >
                {copied === 'logql' ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-24 shrink-0 text-xs text-muted-foreground">Prom (PromQL)</span>
              <code className="flex-1 px-2 py-1 bg-muted/50 rounded text-xs font-mono break-all">{promqlCheck}</code>
              <button
                type="button"
                onClick={() => copy('promql', promqlCheck)}
                className="p-1.5 bg-muted rounded hover:bg-muted/80"
                title="Copy PromQL"
              >
                {copied === 'promql' ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* D) Demo / Chaos panel — launch fault scenarios against the t3 demo
          agent and watch live status. Additive section; existing test-ids
          above are untouched. */}
      <div className={`bg-card rounded-lg border border-border${demoAvailable ? '' : ' hidden'}`} data-testid="demo-panel">
        <div className="p-4 border-b border-border">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="font-semibold flex items-center gap-2">
                <Zap className="h-4 w-4 text-yellow-500" />
                Demo / Chaos
              </h3>
              <p className="text-sm text-muted-foreground mt-0.5">
                Inject faults into the demo target, then heal them — to showcase AI remediation.
              </p>
            </div>
            <div className="flex items-center gap-2">
              {demoStatus &&
                (demoStatus.reachable ? (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-green-500/10 text-green-500">
                    <Wifi className="h-3 w-3" />
                    agent reachable
                  </span>
                ) : (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-red-500/10 text-red-500">
                    <WifiOff className="h-3 w-3" />
                    unreachable
                  </span>
                ))}
              <button
                onClick={() => { void fetchDemoStatus() }}
                className="flex items-center gap-2 px-2.5 py-1 text-xs bg-muted rounded hover:bg-muted/80"
                title="Refresh demo status"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Refresh
              </button>
            </div>
          </div>
        </div>

        <div className="p-4 space-y-4">
          {/* Unreachable hint */}
          {demoStatus && !demoStatus.reachable && (
            <div
              data-testid="demo-unreachable-hint"
              className="flex items-start gap-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-sm text-yellow-700"
            >
              <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
              <span>Agent unreachable — set the t3 target URL below and Save.</span>
            </div>
          )}

          {/* Target container status badges */}
          {demoStatus && (
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="text-muted-foreground">Containers:</span>
              {(['nextcloud', 'nextcloud-db'] as const).map((c) => {
                const running = demoStatus.containers?.[c]?.running ?? false
                return (
                  <span
                    key={c}
                    data-testid={`demo-container-${c}`}
                    className={`flex items-center gap-1 px-2 py-0.5 rounded-full ${
                      running
                        ? 'bg-green-500/10 text-green-500'
                        : 'bg-red-500/10 text-red-500'
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${running ? 'bg-green-500' : 'bg-red-500'}`}
                    />
                    {c} {running ? 'running' : 'down'}
                  </span>
                )
              })}
            </div>
          )}

          {/* Scenario list */}
          <div className="space-y-2">
            {demoScenarios.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No scenarios available. Set the t3 target URL and refresh.
              </p>
            ) : (
              demoScenarios.map((sc) => {
                const active = demoStatus?.scenarios?.[sc.id]?.active ?? false
                const startBusy = demoBusy[`${sc.id}:start`] ?? false
                const healBusy = demoBusy[`${sc.id}:heal`] ?? false
                return (
                  <div
                    key={sc.id}
                    data-testid={`demo-scenario-${sc.id}`}
                    className="flex items-center justify-between gap-3 p-3 bg-muted/50 rounded-lg"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{sc.label}</span>
                        <span
                          data-testid={`demo-scenario-${sc.id}-badge`}
                          className={`px-2 py-0.5 rounded-full text-[11px] ${
                            active
                              ? 'bg-red-500/10 text-red-500'
                              : 'bg-green-500/10 text-green-500'
                          }`}
                        >
                          {active ? 'active' : 'healthy'}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground truncate">{sc.description}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        data-testid={`demo-scenario-${sc.id}-start`}
                        onClick={() => { void runDemoChaos(sc.id, 'start') }}
                        disabled={startBusy}
                        className="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-red-500/90 text-white rounded hover:bg-red-500 disabled:opacity-50"
                      >
                        {startBusy ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Play className="h-3.5 w-3.5" />
                        )}
                        Start
                      </button>
                      <button
                        data-testid={`demo-scenario-${sc.id}-heal`}
                        onClick={() => { void runDemoChaos(sc.id, 'heal') }}
                        disabled={healBusy}
                        className="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-green-500/90 text-white rounded hover:bg-green-500 disabled:opacity-50"
                      >
                        {healBusy ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <HeartPulse className="h-3.5 w-3.5" />
                        )}
                        Heal
                      </button>
                    </div>
                  </div>
                )
              })
            )}
          </div>

          {/* t3 target URL config */}
          <div className="pt-2 border-t border-border">
            <label className="block text-sm font-medium mb-2">t3 Target URL</label>
            <div className="flex items-center gap-2">
              <input
                type="url"
                value={demoTargetInput}
                data-testid="demo-target-input"
                onChange={(e) => setDemoTargetInput(e.target.value)}
                placeholder="http://t3-demo-agent:9099"
                className="flex-1 px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <button
                data-testid="demo-target-save"
                onClick={() => { void saveDemoTarget() }}
                disabled={demoTargetSaving}
                className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
              >
                {demoTargetSaving ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Save
              </button>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Base URL of the t3 demo agent that runs chaos scenarios.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Infrastructure
