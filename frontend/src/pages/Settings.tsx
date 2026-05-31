import { useState, useEffect, useCallback } from 'react'
import {
  Save,
  RefreshCw,
  Shield,
  Cpu,
  Database,
  Bell,
  Network,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Info,
  FileText,
  RotateCcw,
  RotateCw,
} from 'lucide-react'
import api, {
  HealthResponse,
  isComponentHealthy,
  AllSettings,
  ConstitutionalSettings,
  NotificationSettings,
  TelemetrySettings,
} from '../lib/api'

// ── re-export for tests / other imports ─────────────────────────────────────
export type { ConstitutionalSettings, NotificationSettings, TelemetrySettings }

// ── interface for SystemPrompt (local, mirrors backend) ─────────────────────
interface SystemPrompt {
  name: string
  description: string
  prompt: string
  agent: 'fast' | 'reasoning'
  editable: boolean
}

// ── Defaults (must match backend) ────────────────────────────────────────────
const DEFAULT_CONSTITUTIONAL: ConstitutionalSettings = {
  autoThreshold: 90,
  approvalThreshold: 70,
  maxActionsPerMinute: 10,
  enableAuditLog: true,
  enableLearning: true,
  strictTier1: true,
}

const DEFAULT_NOTIFICATIONS: NotificationSettings = {
  emailEnabled: false,
  slackEnabled: false,
  webhookEnabled: false,
  webhookUrl: '',
  notifyOnCritical: true,
  notifyOnApproval: true,
  notifyOnResolution: false,
}

const DEFAULT_TELEMETRY: TelemetrySettings = {
  lokiEnabled: true,
  lokiUrl: 'http://loki:3100',
  prometheusEnabled: true,
  prometheusUrl: 'http://prometheus:9090',
  tempoEnabled: true,
  tempoUrl: 'http://tempo:3200',
  retentionDays: 30,
}

// ── main component ────────────────────────────────────────────────────────────
export function Settings() {
  const [activeTab, setActiveTab] = useState<
    'constitutional' | 'notifications' | 'telemetry' | 'models' | 'prompts'
  >('constitutional')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [settingsLoading, setSettingsLoading] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const [constitutional, setConstitutional] =
    useState<ConstitutionalSettings>(DEFAULT_CONSTITUTIONAL)
  const [notifications, setNotifications] =
    useState<NotificationSettings>(DEFAULT_NOTIFICATIONS)
  const [telemetry, setTelemetry] = useState<TelemetrySettings>(DEFAULT_TELEMETRY)

  // System prompts state
  const [prompts, setPrompts] = useState<SystemPrompt[]>([])
  const [promptsLoading, setPromptsLoading] = useState(false)
  const [editingPrompt, setEditingPrompt] = useState<string | null>(null)
  const [editedPromptText, setEditedPromptText] = useState('')

  // ── load persisted settings on mount ────────────────────────────────────
  const fetchSettings = useCallback(async () => {
    setSettingsLoading(true)
    try {
      const data: AllSettings = await api.settings.get()
      setConstitutional(data.constitutional)
      setNotifications(data.notifications)
      setTelemetry(data.telemetry)
    } catch {
      // Backend not available → stay on defaults; this is expected in local-frontend-only dev
    } finally {
      setSettingsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSettings()
    fetchHealth()
  }, [fetchSettings])

  // ── load prompts when prompts tab is active ───────────────────────────────
  useEffect(() => {
    if (activeTab === 'prompts') {
      fetchPrompts()
    }
  }, [activeTab])

  const fetchPrompts = async () => {
    setPromptsLoading(true)
    try {
      const response = await fetch('/api/v1/prompts/')
      if (response.ok) {
        const data = await response.json()
        setPrompts(data.prompts || [])
      }
    } catch (err) {
      console.error('Failed to fetch prompts:', err)
    } finally {
      setPromptsLoading(false)
    }
  }

  const handleSavePrompt = async (promptName: string) => {
    try {
      const response = await fetch(`/api/v1/prompts/${promptName}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: editedPromptText }),
      })
      if (response.ok) {
        setEditingPrompt(null)
        fetchPrompts()
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
      }
    } catch (err) {
      console.error('Failed to save prompt:', err)
    }
  }

  const handleResetPrompt = async (promptName: string) => {
    try {
      const response = await fetch(`/api/v1/prompts/${promptName}/reset`, {
        method: 'POST',
      })
      if (response.ok) {
        fetchPrompts()
      }
    } catch (err) {
      console.error('Failed to reset prompt:', err)
    }
  }

  const fetchHealth = async () => {
    setLoading(true)
    try {
      const data = await api.health.check()
      setHealth(data)
    } catch (err) {
      console.error('Failed to fetch health:', err)
    } finally {
      setLoading(false)
    }
  }

  // ── Save all settings to the backend ─────────────────────────────────────
  const handleSave = async () => {
    setSaving(true)
    setSaveError(null)
    try {
      const payload: AllSettings = { constitutional, notifications, telemetry }
      await api.settings.save(payload)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch {
      setSaveError('Save failed — backend unavailable. Changes are shown in UI but not persisted.')
      setTimeout(() => setSaveError(null), 4000)
    } finally {
      setSaving(false)
    }
  }

  // ── Reset persisted settings to factory defaults ──────────────────────────
  const handleResetSettings = async () => {
    setSaving(true)
    setSaveError(null)
    try {
      const defaults: AllSettings = await api.settings.reset()
      setConstitutional(defaults.constitutional)
      setNotifications(defaults.notifications)
      setTelemetry(defaults.telemetry)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch {
      // If backend is down, just reset locally
      setConstitutional(DEFAULT_CONSTITUTIONAL)
      setNotifications(DEFAULT_NOTIFICATIONS)
      setTelemetry(DEFAULT_TELEMETRY)
    } finally {
      setSaving(false)
    }
  }

  const tabs = [
    { id: 'constitutional', label: 'Constitutional AI', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'telemetry', label: 'Telemetry', icon: Network },
    { id: 'models', label: 'Models', icon: Cpu },
    { id: 'prompts', label: 'System Prompts', icon: FileText },
  ] as const

  return (
    <div className="space-y-6">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Configure Constitutional AIOps system</p>
        </div>
        <div className="flex items-center gap-2">
          {settingsLoading && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              Loading…
            </span>
          )}
          <button
            onClick={handleResetSettings}
            disabled={saving}
            aria-label="Reset to defaults"
            className="flex items-center gap-2 px-3 py-2 bg-muted text-muted-foreground rounded-lg font-medium hover:bg-muted/80 disabled:opacity-50 text-sm"
          >
            <RotateCw className="h-4 w-4" />
            Reset
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50"
          >
            {saving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : saved ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            {saved ? 'Saved!' : 'Save Settings'}
          </button>
        </div>
      </div>

      {/* ── Save error banner ────────────────────────────────────────────── */}
      {saveError && (
        <div className="flex items-start gap-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-sm text-yellow-700">
          <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
          <span>{saveError}</span>
        </div>
      )}

      {/* ── Tab navigation ──────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-1 p-1 bg-muted rounded-lg w-fit">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* ── Tab content — max-width widened; 2-col grid where sensible ──── */}
      <div className="max-w-6xl">

        {/* ━━ Constitutional AI ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        {activeTab === 'constitutional' && (
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Authorization Matrix */}
            <div className="bg-card rounded-lg border border-border p-6">
              <h2 className="text-lg font-semibold mb-4">Authorization Matrix</h2>
              <div className="space-y-6">
                {/* Auto threshold slider */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Automatic Action Threshold</label>
                    <span
                      data-testid="auto-threshold-value"
                      className="text-sm font-semibold text-primary"
                    >
                      {constitutional.autoThreshold}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min={70}
                    max={99}
                    value={constitutional.autoThreshold}
                    data-testid="auto-threshold-slider"
                    onChange={(e) =>
                      setConstitutional({ ...constitutional, autoThreshold: Number(e.target.value) })
                    }
                    className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>70%</span>
                    <span>99%</span>
                  </div>
                  <p
                    data-testid="auto-threshold-hint"
                    className="text-xs text-muted-foreground mt-2 flex items-center gap-1"
                  >
                    <Info className="h-3 w-3" />
                    Actions with confidence ≥ {constitutional.autoThreshold}% execute automatically
                  </p>
                </div>

                {/* Approval threshold slider */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Approval Required Threshold</label>
                    <span
                      data-testid="approval-threshold-value"
                      className="text-sm font-semibold text-yellow-500"
                    >
                      {constitutional.approvalThreshold}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min={50}
                    max={89}
                    value={constitutional.approvalThreshold}
                    data-testid="approval-threshold-slider"
                    onChange={(e) =>
                      setConstitutional({ ...constitutional, approvalThreshold: Number(e.target.value) })
                    }
                    className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>50%</span>
                    <span>89%</span>
                  </div>
                  <p
                    data-testid="approval-threshold-hint"
                    className="text-xs text-muted-foreground mt-2 flex items-center gap-1"
                  >
                    <Info className="h-3 w-3" />
                    Actions with {constitutional.approvalThreshold}–{constitutional.autoThreshold - 1}%
                    confidence require human approval
                  </p>
                </div>

                {/* Max actions */}
                <div>
                  <label className="block text-sm font-medium mb-2">Max Actions Per Minute</label>
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={constitutional.maxActionsPerMinute}
                    data-testid="max-actions-input"
                    onChange={(e) =>
                      setConstitutional({ ...constitutional, maxActionsPerMinute: Number(e.target.value) })
                    }
                    className="w-32 px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                  <p className="text-xs text-muted-foreground mt-2">Rate limit for automated actions</p>
                </div>

                {/* Visual Authorization Levels */}
                <div className="p-4 bg-muted/50 rounded-lg">
                  <h3 className="text-sm font-medium mb-3">Authorization Levels</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-green-500 shrink-0" />
                      <span className="text-sm">
                        <strong>Automatic</strong>: ≥ {constitutional.autoThreshold}% confidence
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-yellow-500 shrink-0" />
                      <span className="text-sm">
                        <strong>Approval Required</strong>: {constitutional.approvalThreshold}–
                        {constitutional.autoThreshold - 1}% confidence
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-gray-400 shrink-0" />
                      <span className="text-sm">
                        <strong>Alert Only</strong>: &lt; {constitutional.approvalThreshold}% confidence
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Safety & Compliance */}
            <div className="bg-card rounded-lg border border-border p-6">
              <h2 className="text-lg font-semibold mb-4">Safety &amp; Compliance</h2>
              <div className="space-y-4">
                <ToggleSetting
                  label="Strict Tier 1 Enforcement"
                  description="Never allow safety-critical principle violations (required)"
                  checked={constitutional.strictTier1}
                  testId="toggle-strictTier1"
                  disabled
                />
                <ToggleSetting
                  label="Audit Logging"
                  description="Log all actions and decisions for compliance"
                  checked={constitutional.enableAuditLog}
                  testId="toggle-auditLog"
                  onChange={(checked) =>
                    setConstitutional({ ...constitutional, enableAuditLog: checked })
                  }
                />
                <ToggleSetting
                  label="Continuous Learning"
                  description="Learn from operator corrections and feedback"
                  checked={constitutional.enableLearning}
                  testId="toggle-learning"
                  onChange={(checked) =>
                    setConstitutional({ ...constitutional, enableLearning: checked })
                  }
                />
              </div>

              {/* Persistence note */}
              <div className="mt-6 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs text-blue-600">
                <p className="font-semibold mb-1">Persistence</p>
                <p>
                  Constitutional thresholds are saved to the backend (
                  <code>GET/PUT /api/v1/settings/</code>) and applied live to the validator.
                  Changes survive restart.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ━━ Notifications ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        {activeTab === 'notifications' && (
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="bg-card rounded-lg border border-border p-6">
              <h2 className="text-lg font-semibold mb-4">Notification Channels</h2>
              <div className="space-y-4">
                <ToggleSetting
                  label="Email Notifications"
                  description="Send email alerts for incidents and approvals"
                  checked={notifications.emailEnabled}
                  testId="toggle-email"
                  onChange={(checked) => setNotifications({ ...notifications, emailEnabled: checked })}
                />
                <ToggleSetting
                  label="Slack Integration"
                  description="Post updates to a Slack channel"
                  checked={notifications.slackEnabled}
                  testId="toggle-slack"
                  onChange={(checked) => setNotifications({ ...notifications, slackEnabled: checked })}
                />
                <ToggleSetting
                  label="Webhook"
                  description="Send notifications to a custom webhook URL"
                  checked={notifications.webhookEnabled}
                  testId="toggle-webhook"
                  onChange={(checked) =>
                    setNotifications({ ...notifications, webhookEnabled: checked })
                  }
                />
                {notifications.webhookEnabled && (
                  <div className="ml-6">
                    <label className="block text-sm font-medium mb-2">Webhook URL</label>
                    <input
                      type="url"
                      value={notifications.webhookUrl}
                      data-testid="webhook-url-input"
                      onChange={(e) =>
                        setNotifications({ ...notifications, webhookUrl: e.target.value })
                      }
                      placeholder="https://example.com/webhook"
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="bg-card rounded-lg border border-border p-6">
              <h2 className="text-lg font-semibold mb-4">Notification Events</h2>
              <div className="space-y-4">
                <ToggleSetting
                  label="Critical Incidents"
                  description="Notify when critical severity incidents are created"
                  checked={notifications.notifyOnCritical}
                  testId="toggle-notifyCritical"
                  onChange={(checked) =>
                    setNotifications({ ...notifications, notifyOnCritical: checked })
                  }
                />
                <ToggleSetting
                  label="Pending Approvals"
                  description="Notify when actions require human approval"
                  checked={notifications.notifyOnApproval}
                  testId="toggle-notifyApproval"
                  onChange={(checked) =>
                    setNotifications({ ...notifications, notifyOnApproval: checked })
                  }
                />
                <ToggleSetting
                  label="Incident Resolution"
                  description="Notify when incidents are resolved"
                  checked={notifications.notifyOnResolution}
                  testId="toggle-notifyResolution"
                  onChange={(checked) =>
                    setNotifications({ ...notifications, notifyOnResolution: checked })
                  }
                />
              </div>

              <div className="mt-6 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-xs text-yellow-700">
                <p className="font-semibold mb-1">Status</p>
                <p>
                  Channel toggles and event preferences are persisted via{' '}
                  <code>/api/v1/settings/</code>. Actual delivery (SMTP / Slack webhook) requires
                  environment-variable configuration on the server.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ━━ Telemetry ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        {activeTab === 'telemetry' && (
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="bg-card rounded-lg border border-border p-6">
              <h2 className="text-lg font-semibold mb-4">LGTM Stack Configuration</h2>
              <div className="space-y-4">
                {/* Loki */}
                <div>
                  <ToggleSetting
                    label="Loki (Logs)"
                    description="Log aggregation and querying"
                    checked={telemetry.lokiEnabled}
                    testId="toggle-loki"
                    onChange={(checked) => setTelemetry({ ...telemetry, lokiEnabled: checked })}
                  />
                  {telemetry.lokiEnabled && (
                    <div className="ml-6 mt-2">
                      <input
                        type="url"
                        value={telemetry.lokiUrl}
                        data-testid="loki-url-input"
                        onChange={(e) => setTelemetry({ ...telemetry, lokiUrl: e.target.value })}
                        placeholder="http://loki:3100"
                        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                  )}
                </div>

                {/* Prometheus */}
                <div>
                  <ToggleSetting
                    label="Prometheus (Metrics)"
                    description="Metrics collection and alerting"
                    checked={telemetry.prometheusEnabled}
                    testId="toggle-prometheus"
                    onChange={(checked) =>
                      setTelemetry({ ...telemetry, prometheusEnabled: checked })
                    }
                  />
                  {telemetry.prometheusEnabled && (
                    <div className="ml-6 mt-2">
                      <input
                        type="url"
                        value={telemetry.prometheusUrl}
                        data-testid="prometheus-url-input"
                        onChange={(e) =>
                          setTelemetry({ ...telemetry, prometheusUrl: e.target.value })
                        }
                        placeholder="http://prometheus:9090"
                        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                  )}
                </div>

                {/* Tempo */}
                <div>
                  <ToggleSetting
                    label="Tempo (Traces)"
                    description="Distributed tracing"
                    checked={telemetry.tempoEnabled}
                    testId="toggle-tempo"
                    onChange={(checked) => setTelemetry({ ...telemetry, tempoEnabled: checked })}
                  />
                  {telemetry.tempoEnabled && (
                    <div className="ml-6 mt-2">
                      <input
                        type="url"
                        value={telemetry.tempoUrl}
                        data-testid="tempo-url-input"
                        onChange={(e) => setTelemetry({ ...telemetry, tempoUrl: e.target.value })}
                        placeholder="http://tempo:3200"
                        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-card rounded-lg border border-border p-6">
              <h2 className="text-lg font-semibold mb-4">Retention &amp; Storage</h2>
              <div className="space-y-6">
                <div className="pt-2">
                  <label className="block text-sm font-medium mb-2">Data Retention (days)</label>
                  <input
                    type="number"
                    min={7}
                    max={365}
                    value={telemetry.retentionDays}
                    data-testid="retention-days-input"
                    onChange={(e) =>
                      setTelemetry({ ...telemetry, retentionDays: Number(e.target.value) })
                    }
                    className="w-32 px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    How long to keep logs, metrics, and traces (7–365 days)
                  </p>
                </div>

                <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs text-blue-600">
                  <p className="font-semibold mb-1">Persistence</p>
                  <p>
                    Telemetry settings are persisted via <code>/api/v1/settings/</code>. Changes to
                    URLs or retention take effect on next backend restart / collector reload.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ━━ Models ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        {activeTab === 'models' && (
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="bg-card rounded-lg border border-border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Model Status</h2>
                <button
                  onClick={fetchHealth}
                  disabled={loading}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 disabled:opacity-50"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                  Refresh
                </button>
              </div>
              <div className="space-y-4">
                <ModelStatusCard
                  name="Fast Agent"
                  model="Qwen3-4B Q4_K_M"
                  port={8081}
                  status={isComponentHealthy(health, 'fast_agent') ? 'online' : 'offline'}
                  purpose="Telemetry annotation, classification"
                  context="8K tokens"
                  latency="<100ms P95"
                />
                <ModelStatusCard
                  name="Reasoning Agent"
                  model="Qwen3-14B Q4_K_M"
                  port={8082}
                  status={isComponentHealthy(health, 'reasoning_agent') ? 'online' : 'offline'}
                  purpose="RCA, remediation planning, human chat"
                  context="4K tokens"
                  latency="200-500ms P95"
                />
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-card rounded-lg border border-border p-6">
                <h2 className="text-lg font-semibold mb-4">Architecture</h2>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between py-2 border-b border-border">
                    <span className="text-muted-foreground">Configuration</span>
                    <span className="font-medium">Simultaneous Dual-Model</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-border">
                    <span className="text-muted-foreground">Total VRAM</span>
                    <span className="font-medium">24GB (NVIDIA L4)</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-border">
                    <span className="text-muted-foreground">Used VRAM</span>
                    <span className="font-medium">~15GB</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-border">
                    <span className="text-muted-foreground">Model Loading</span>
                    <span className="font-medium">Always Loaded (TTL: -1)</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-muted-foreground">Swap Latency</span>
                    <span className="font-medium text-green-500">0ms (simultaneous)</span>
                  </div>
                </div>
              </div>

              {/* Graph Memory */}
              <div className="bg-card rounded-lg border border-border p-6">
                <h2 className="text-lg font-semibold mb-4">Graph Memory</h2>
                <div className="flex items-center gap-3 mb-4">
                  <Database className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <span className="font-medium">Neo4j</span>
                    <span
                      className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                        isComponentHealthy(health, 'neo4j')
                          ? 'bg-green-500/10 text-green-500'
                          : 'bg-yellow-500/10 text-yellow-500'
                      }`}
                    >
                      {isComponentHealthy(health, 'neo4j') ? 'Connected' : 'In-memory fallback'}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  {isComponentHealthy(health, 'neo4j')
                    ? 'Using Neo4j for persistent episodic memory and service dependency graphs.'
                    : 'Neo4j not available. Using in-memory episode store with similarity search.'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ━━ System Prompts ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        {activeTab === 'prompts' && (
          <div className="space-y-6">
            <div className="bg-card rounded-lg border border-border p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold">System Prompts</h2>
                  <p className="text-sm text-muted-foreground">
                    Customize prompts for Fast Agent and Reasoning Agent
                  </p>
                </div>
                <button
                  onClick={fetchPrompts}
                  disabled={promptsLoading}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 disabled:opacity-50"
                >
                  {promptsLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  Refresh
                </button>
              </div>

              {promptsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : prompts.length > 0 ? (
                <div className="grid gap-4 lg:grid-cols-2">
                  {prompts.map((prompt) => (
                    <div key={prompt.name} className="p-4 bg-muted/50 rounded-lg">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="font-semibold">{prompt.description}</h3>
                          <div className="flex items-center gap-2 mt-1">
                            <span
                              className={`px-2 py-0.5 rounded text-xs ${
                                prompt.agent === 'fast'
                                  ? 'bg-yellow-500/10 text-yellow-500'
                                  : 'bg-purple-500/10 text-purple-500'
                              }`}
                            >
                              {prompt.agent === 'fast' ? 'Fast Agent' : 'Reasoning Agent'}
                            </span>
                            <span className="text-xs text-muted-foreground">{prompt.name}</span>
                          </div>
                        </div>
                        <div className="flex gap-2 shrink-0 ml-2">
                          {editingPrompt === prompt.name ? (
                            <>
                              <button
                                onClick={() => handleSavePrompt(prompt.name)}
                                className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
                              >
                                Save
                              </button>
                              <button
                                onClick={() => setEditingPrompt(null)}
                                className="px-3 py-1 bg-muted text-muted-foreground rounded text-sm hover:bg-muted/80"
                              >
                                Cancel
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => {
                                  setEditingPrompt(prompt.name)
                                  setEditedPromptText(prompt.prompt)
                                }}
                                disabled={!prompt.editable}
                                className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm hover:bg-primary/90 disabled:opacity-50"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleResetPrompt(prompt.name)}
                                className="px-3 py-1 bg-muted text-muted-foreground rounded text-sm hover:bg-muted/80 flex items-center gap-1"
                              >
                                <RotateCcw className="h-3 w-3" />
                                Reset
                              </button>
                            </>
                          )}
                        </div>
                      </div>

                      {editingPrompt === prompt.name ? (
                        <textarea
                          value={editedPromptText}
                          onChange={(e) => setEditedPromptText(e.target.value)}
                          rows={10}
                          className="w-full mt-2 p-3 text-sm font-mono bg-background rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-primary resize-y"
                        />
                      ) : (
                        <pre className="mt-2 p-3 text-sm font-mono bg-background/50 rounded-lg overflow-x-auto max-h-32 overflow-y-auto whitespace-pre-wrap">
                          {prompt.prompt}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No prompts available</p>
                  <p className="text-xs mt-1">Start the backend to load system prompts</p>
                </div>
              )}
            </div>

            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-blue-600">About System Prompts</h3>
                  <p className="text-sm text-blue-600/80 mt-1">
                    System prompts define how each agent behaves. The Fast Agent handles quick
                    classification tasks, while the Reasoning Agent performs deep analysis and
                    planning. Changes take effect immediately for new requests.
                  </p>
                  <p className="text-xs text-blue-600/60 mt-2">
                    Persisted in-process via <code>/api/v1/prompts/</code> (resets on restart).
                    Use Save Settings above to persist Constitutional / Notification / Telemetry
                    configuration across restarts.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ToggleSetting({
  label,
  description,
  checked,
  onChange,
  disabled = false,
  testId,
}: {
  label: string
  description: string
  checked: boolean
  onChange?: (checked: boolean) => void
  disabled?: boolean
  testId?: string
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="font-medium">{label}</p>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <button
        onClick={() => !disabled && onChange?.(!checked)}
        disabled={disabled}
        data-testid={testId}
        aria-pressed={checked}
        aria-label={label}
        className={`relative w-11 h-6 rounded-full transition-colors ${
          checked ? 'bg-primary' : 'bg-muted'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
            checked ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  )
}

function ModelStatusCard({
  name,
  model,
  port,
  status,
  purpose,
  context,
  latency,
}: {
  name: string
  model: string
  port: number
  status: 'online' | 'offline'
  purpose: string
  context: string
  latency: string
}) {
  return (
    <div className="p-4 bg-muted/50 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Cpu className="h-5 w-5 text-muted-foreground" />
          <h3 className="font-semibold">{name}</h3>
        </div>
        <span
          className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${
            status === 'online' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
          }`}
        >
          {status === 'online' ? (
            <CheckCircle className="h-3 w-3" />
          ) : (
            <AlertTriangle className="h-3 w-3" />
          )}
          {status}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-muted-foreground">Model:</span>
          <span className="ml-2">{model}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Port:</span>
          <span className="ml-2">{port}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Context:</span>
          <span className="ml-2">{context}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Latency:</span>
          <span className="ml-2">{latency}</span>
        </div>
      </div>
      <p className="text-xs text-muted-foreground mt-2">{purpose}</p>
    </div>
  )
}
