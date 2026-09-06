import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
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
  Rocket,
  Wrench,
  Waypoints,
  ArrowLeftRight,
  UserCog,
  Link2,
  KeyRound,
} from 'lucide-react'
import { DEMO_MODE } from '../lib/demo/flag'
import api, {
  HealthResponse,
  isComponentHealthy,
  AllSettings,
  ConstitutionalSettings,
  NotificationSettings,
  TelemetrySettings,
  RemediationSettings,
  RemediationMode,
  ActionToolName,
  ServingModeStatus,
  ModelsConfig,
  ModelsConfigUpdate,
  ModelsTestResult,
  AlertingConfig,
  AlertSeverity,
  AlertingChannel,
} from '../lib/api'
import { buildAlertingUpdate } from '../lib/alerting'
import { TopologySchemaEditor } from '../components/TopologySchemaEditor'
import { AccountSettings } from '../components/AccountSettings'
import useAuthStore from '../lib/auth'

// ── re-export for tests / other imports ─────────────────────────────────────
export type { ConstitutionalSettings, NotificationSettings, TelemetrySettings, RemediationSettings }

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
  webhookSecret: '',
  webhookMinSeverity: 'warning',
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
  dockerEnabled: true,
  retentionDays: 30,
}

const DEFAULT_REMEDIATION: RemediationSettings = {
  mode: 'diagnose',
  autoConfidenceThreshold: 90,
  requireEvidenceForAuto: true,
  autoToolAllowlist: ['restart_service'],
  demoTargetUrl: '',
}

// Helper copy for each remediation mode.
const REMEDIATION_MODE_HELP: Record<RemediationMode, string> = {
  diagnose:
    'Diagnose only — the AI investigates and explains, but never proposes or runs a fix.',
  approve:
    'Approve to run — the AI proposes a fix in chat; nothing executes until you click Approve.',
  auto:
    'Auto-remediate — allowlisted, high-confidence fixes execute automatically once they pass the constitution; everything else still asks for approval.',
}

// The mutating action tools an operator can allow to run autonomously.
const ACTION_TOOL_OPTIONS: { name: ActionToolName; label: string; description: string }[] = [
  {
    name: 'restart_service',
    label: 'restart_service',
    description: 'Restart a whitelisted container',
  },
  {
    name: 'scale_service',
    label: 'scale_service',
    description: 'Scale a whitelisted service (0–5 replicas)',
  },
]

/**
 * Local Docker-socket telemetry source card (Settings -> Telemetry). Toggles
 * the fallback source on/off and live-tests the socket. Self-contained test
 * state so it doesn't touch the page's save cycle.
 */
function DockerSourceCard({
  telemetry,
  setTelemetry,
}: {
  telemetry: TelemetrySettings
  setTelemetry: (t: TelemetrySettings) => void
}) {
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<{ ok: boolean; detail: string } | null>(null)

  const runTest = async () => {
    setTesting(true)
    setResult(null)
    try {
      const res = await api.settings.testMonitoring({ docker: true })
      setResult(res.docker ?? { ok: false, detail: 'no result' })
    } catch (e) {
      setResult({ ok: false, detail: e instanceof Error ? e.message : 'test failed' })
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <h2 className="mb-1 flex items-center gap-2 text-lg font-semibold">
        <Database className="h-5 w-5" />
        Local source (no LGTM required)
      </h2>
      <p className="mb-4 text-sm text-muted-foreground">
        Reads logs and live CPU / memory metrics straight from the host's Docker
        socket. It only activates when Loki / Prometheus return nothing, so a full
        observability stack is never shadowed. Recommended for the lite / self-host tier.
      </p>
      <ToggleSetting
        label="Local Docker socket"
        description="Fallback logs & metrics when no LGTM stack is present"
        checked={telemetry.dockerEnabled}
        testId="toggle-docker-source"
        onChange={(checked) => setTelemetry({ ...telemetry, dockerEnabled: checked })}
      />
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={runTest}
          disabled={testing}
          data-testid="test-docker-source"
          className="flex items-center gap-2 rounded-lg border border-border bg-muted px-3 py-1.5 text-sm hover:bg-muted/80 disabled:opacity-50"
        >
          {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Test connection
        </button>
        {result && (
          <span className={`inline-flex items-center gap-1.5 text-sm ${result.ok ? 'text-green-500' : 'text-red-500'}`}>
            {result.ok ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
            {result.detail}
          </span>
        )}
      </div>
    </div>
  )
}

// ── main component ────────────────────────────────────────────────────────────
export function Settings() {
  const [activeTab, setActiveTab] = useState<
    'constitutional' | 'remediation' | 'notifications' | 'telemetry' | 'models' | 'prompts' | 'topology' | 'account'
  >('constitutional')
  // Admin gate: the topology + system-prompt tabs are full editors whose backend
  // mutations are admin-only (SEC-004), so hide them (and the webhook live-test)
  // from non-admins. When AUTH is off (authRequired=false) every caller is the
  // synthetic admin, so treat as admin — this keeps local dev and the demo tier
  // unchanged.
  const authRequired = useAuthStore((s) => s.authRequired)
  const currentRole = useAuthStore((s) => s.user?.role)
  const isAdmin = !authRequired || currentRole === 'admin'
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [settingsLoading, setSettingsLoading] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const [constitutional, setConstitutional] =
    useState<ConstitutionalSettings>(DEFAULT_CONSTITUTIONAL)
  const [notifications, setNotifications] =
    useState<NotificationSettings>(DEFAULT_NOTIFICATIONS)
  // Webhook live-test (admin only) — self-contained so it never touches the
  // page's save cycle, same pattern as the Docker source / LLM endpoint tests.
  const [webhookTesting, setWebhookTesting] = useState(false)
  const [webhookTestResult, setWebhookTestResult] =
    useState<{ ok: boolean; detail: string } | null>(null)
  const [telemetry, setTelemetry] = useState<TelemetrySettings>(DEFAULT_TELEMETRY)
  const [remediation, setRemediation] = useState<RemediationSettings>(DEFAULT_REMEDIATION)

  // System prompts state
  const [prompts, setPrompts] = useState<SystemPrompt[]>([])
  const [promptsLoading, setPromptsLoading] = useState(false)
  const [editingPrompt, setEditingPrompt] = useState<string | null>(null)
  const [editedPromptText, setEditedPromptText] = useState('')
  // Loud feedback for prompt save/reset: the backend now fails with a 5xx
  // when an edit cannot actually be applied to the live agent, so a non-2xx
  // must surface as a visible error (never silent false-success).
  const [promptError, setPromptError] = useState<string | null>(null)
  const [promptNotice, setPromptNotice] = useState<string | null>(null)

  // ── load persisted settings on mount ────────────────────────────────────
  const fetchSettings = useCallback(async () => {
    setSettingsLoading(true)
    try {
      const data: AllSettings = await api.settings.get()
      setConstitutional(data.constitutional)
      setNotifications(data.notifications)
      setTelemetry(data.telemetry)
      // `remediation` is a newer block; tolerate a backend that omits it.
      setRemediation(data.remediation ?? DEFAULT_REMEDIATION)
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

  /** Pull a human-readable error out of a non-2xx prompts response. */
  const promptFailureDetail = async (response: Response): Promise<string> => {
    let detail = `HTTP ${response.status}`
    try {
      const data: unknown = await response.json()
      if (data && typeof data === 'object') {
        const obj = data as Record<string, unknown>
        if (typeof obj.detail === 'string') detail = obj.detail
        else if (typeof obj.message === 'string') detail = obj.message
      }
    } catch {
      // Non-JSON error body — keep the status code message.
    }
    return detail
  }

  const handleSavePrompt = async (promptName: string) => {
    setPromptError(null)
    setPromptNotice(null)
    try {
      const response = await fetch(`/api/v1/prompts/${promptName}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: editedPromptText }),
      })
      if (response.ok) {
        // Success only on 2xx: the edit was applied to the live agent and
        // persisted. Confirm explicitly so "saved" actually means saved.
        setEditingPrompt(null)
        fetchPrompts()
        setPromptNotice(`Prompt "${promptName}" applied to the live agent and persisted.`)
        setTimeout(() => setPromptNotice(null), 5000)
      } else {
        // Keep the editor open so the user's text isn't lost.
        const detail = await promptFailureDetail(response)
        setPromptError(`Failed to apply prompt "${promptName}": ${detail}`)
      }
    } catch (err) {
      console.error('Failed to save prompt:', err)
      setPromptError(
        `Failed to save prompt "${promptName}": ${err instanceof Error ? err.message : 'network error'}`,
      )
    }
  }

  const handleResetPrompt = async (promptName: string) => {
    setPromptError(null)
    setPromptNotice(null)
    try {
      const response = await fetch(`/api/v1/prompts/${promptName}/reset`, {
        method: 'POST',
      })
      if (response.ok) {
        fetchPrompts()
        setPromptNotice(`Prompt "${promptName}" reset to its default.`)
        setTimeout(() => setPromptNotice(null), 5000)
      } else {
        const detail = await promptFailureDetail(response)
        setPromptError(`Failed to reset prompt "${promptName}": ${detail}`)
      }
    } catch (err) {
      console.error('Failed to reset prompt:', err)
      setPromptError(
        `Failed to reset prompt "${promptName}": ${err instanceof Error ? err.message : 'network error'}`,
      )
    }
  }

  const fetchHealth = async () => {
    try {
      const data = await api.health.check()
      setHealth(data)
    } catch (err) {
      console.error('Failed to fetch health:', err)
    }
  }

  // ── Save all settings to the backend ─────────────────────────────────────
  const handleSave = async () => {
    setSaving(true)
    setSaveError(null)
    try {
      const payload: AllSettings = { constitutional, notifications, telemetry, remediation }
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
      setRemediation(defaults.remediation ?? DEFAULT_REMEDIATION)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch {
      // If backend is down, just reset locally
      setConstitutional(DEFAULT_CONSTITUTIONAL)
      setNotifications(DEFAULT_NOTIFICATIONS)
      setTelemetry(DEFAULT_TELEMETRY)
      setRemediation(DEFAULT_REMEDIATION)
    } finally {
      setSaving(false)
    }
  }

  const handleTestWebhook = async () => {
    const url = notifications.webhookUrl.trim()
    if (!url) return
    setWebhookTesting(true)
    setWebhookTestResult(null)
    try {
      setWebhookTestResult(await api.settings.testWebhook(url))
    } catch (e) {
      setWebhookTestResult({
        ok: false,
        detail: e instanceof Error ? e.message : 'test failed',
      })
    } finally {
      setWebhookTesting(false)
    }
  }

  const tabs = [
    { id: 'constitutional', label: 'Constitutional AI', icon: Shield },
    { id: 'remediation', label: 'Remediation', icon: Wrench },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'telemetry', label: 'Telemetry', icon: Network },
    { id: 'models', label: 'Models', icon: Cpu },
    { id: 'prompts', label: 'System Prompts', icon: FileText },
    { id: 'topology', label: 'Topology Schema', icon: Waypoints },
    { id: 'account', label: 'Account', icon: UserCog },
  ] as const

  // Non-admins never see the admin-only editor tabs (they'd 403 on save anyway).
  const adminOnlyTabs = new Set(['prompts', 'topology'])
  const visibleTabs = tabs.filter((tab) => isAdmin || !adminOnlyTabs.has(tab.id))

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
          {!DEMO_MODE && (
            <Link
              to="/setup"
              className="flex items-center gap-2 px-3 py-2 bg-muted text-muted-foreground rounded-lg font-medium hover:bg-muted/80 text-sm"
            >
              <Rocket className="h-4 w-4" />
              Setup guide
            </Link>
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
        {visibleTabs.map((tab) => {
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

      {/* ── Tab content — full width (2-col grid stays symmetric); pulled up
             slightly to tighten the gap under the tab ribbon ──── */}
      <div className="-mt-2">

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
                    <label htmlFor="auto-threshold-slider" className="text-sm font-medium">Automatic Action Threshold</label>
                    <span
                      data-testid="auto-threshold-value"
                      className="text-sm font-semibold text-primary"
                    >
                      {constitutional.autoThreshold}%
                    </span>
                  </div>
                  <input
                    id="auto-threshold-slider"
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
                    <label htmlFor="approval-threshold-slider" className="text-sm font-medium">Approval Required Threshold</label>
                    <span
                      data-testid="approval-threshold-value"
                      className="text-sm font-semibold text-yellow-500"
                    >
                      {constitutional.approvalThreshold}%
                    </span>
                  </div>
                  <input
                    id="approval-threshold-slider"
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
              <div className="mt-6 p-3 bg-primary/10 border border-primary/20 rounded-lg text-xs text-primary">
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

        {/* ━━ Remediation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        {activeTab === 'remediation' && (
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Mode + thresholds */}
            <div className="bg-card rounded-lg border border-border p-6">
              <h2 className="text-lg font-semibold mb-4">Remediation Mode</h2>
              <div className="space-y-6">
                {/* 3-way mode selector */}
                <div>
                  <label className="block text-sm font-medium mb-2">How fixes are handled</label>
                  <div className="grid grid-cols-3 gap-2" role="radiogroup" aria-label="Remediation mode">
                    {(['diagnose', 'approve', 'auto'] as const).map((mode) => (
                      <button
                        key={mode}
                        type="button"
                        role="radio"
                        aria-checked={remediation.mode === mode}
                        data-testid={`remediation-mode-${mode}`}
                        onClick={() => setRemediation({ ...remediation, mode })}
                        className={`px-3 py-2 rounded-lg text-sm font-medium capitalize transition-colors border ${
                          remediation.mode === mode
                            ? 'bg-primary text-primary-foreground border-primary'
                            : 'bg-background text-muted-foreground border-border hover:bg-muted'
                        }`}
                      >
                        {mode}
                      </button>
                    ))}
                  </div>
                  <p
                    data-testid="remediation-mode-help"
                    className="text-xs text-muted-foreground mt-2 flex items-start gap-1"
                  >
                    <Info className="h-3 w-3 mt-0.5 shrink-0" />
                    {REMEDIATION_MODE_HELP[remediation.mode]}
                  </p>
                </div>

                {/* Auto-confidence slider (only meaningful for auto) */}
                <div className={remediation.mode === 'auto' ? '' : 'opacity-50'}>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Auto-execute Confidence</label>
                    <span
                      data-testid="remediation-confidence-value"
                      className="text-sm font-semibold text-primary"
                    >
                      {remediation.autoConfidenceThreshold}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min={70}
                    max={99}
                    value={remediation.autoConfidenceThreshold}
                    data-testid="remediation-confidence"
                    disabled={remediation.mode !== 'auto'}
                    onChange={(e) =>
                      setRemediation({
                        ...remediation,
                        autoConfidenceThreshold: Number(e.target.value),
                      })
                    }
                    className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer disabled:cursor-not-allowed"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>70%</span>
                    <span>99%</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Only auto-remediate fixes with confidence ≥{' '}
                    {remediation.autoConfidenceThreshold}%
                  </p>
                </div>

                {/* Require evidence toggle (only meaningful for auto) */}
                <ToggleSetting
                  label="Require telemetry evidence for auto"
                  description="Block auto-remediation unless backed by live telemetry evidence"
                  checked={remediation.requireEvidenceForAuto}
                  testId="remediation-evidence"
                  disabled={remediation.mode !== 'auto'}
                  onChange={(checked) =>
                    setRemediation({ ...remediation, requireEvidenceForAuto: checked })
                  }
                />

                {/* Per-tool autonomy allowlist (only meaningful for auto) */}
                <div className={remediation.mode === 'auto' ? '' : 'opacity-50'}>
                  <p className="text-sm font-medium">Autonomous action tools</p>
                  <p className="text-xs text-muted-foreground mt-0.5 mb-2">
                    Only checked tools may execute without approval in Auto mode; unchecked
                    tools always show an Approve/Reject card in chat.
                  </p>
                  <div className="space-y-2" role="group" aria-label="Autonomous action tools">
                    {ACTION_TOOL_OPTIONS.map((tool) => {
                      const allowlist = remediation.autoToolAllowlist ?? []
                      const checked = allowlist.includes(tool.name)
                      return (
                        <label
                          key={tool.name}
                          className="flex items-center gap-3 rounded-lg border border-border/60 bg-background/50 px-3 py-2 cursor-pointer has-[:disabled]:cursor-not-allowed"
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            disabled={remediation.mode !== 'auto'}
                            data-testid={`remediation-auto-tool-${tool.name}`}
                            onChange={(e) =>
                              setRemediation({
                                ...remediation,
                                autoToolAllowlist: e.target.checked
                                  ? [...allowlist, tool.name]
                                  : allowlist.filter((name) => name !== tool.name),
                              })
                            }
                            className="h-4 w-4 accent-primary"
                          />
                          <span className="font-mono text-sm">{tool.label}</span>
                          <span className="text-xs text-muted-foreground">{tool.description}</span>
                        </label>
                      )
                    })}
                  </div>
                </div>
              </div>
            </div>

            {/* Demo target + persistence note */}
            <div className="bg-card rounded-lg border border-border p-6">
              <h2 className="text-lg font-semibold mb-4">Demo Target</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">t3 Demo Agent URL</label>
                  <input
                    type="url"
                    value={remediation.demoTargetUrl}
                    data-testid="remediation-demo-target"
                    onChange={(e) =>
                      setRemediation({ ...remediation, demoTargetUrl: e.target.value })
                    }
                    placeholder="http://t3-demo-agent:9099"
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    Base URL of the t3 demo agent that runs chaos scenarios and applies fixes.
                  </p>
                </div>
              </div>

              <div className="mt-6 p-3 bg-primary/10 border border-primary/20 rounded-lg text-xs text-primary">
                <p className="font-semibold mb-1">Persistence</p>
                <p>
                  Remediation settings are saved to the backend (
                  <code>GET/PUT /api/v1/settings/</code>) and applied live. Use{' '}
                  <strong>Approve</strong> to keep a human in the loop, or <strong>Auto</strong> to
                  let high-confidence fixes run on their own.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ━━ Notifications ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        {activeTab === 'notifications' && (
          <div className="space-y-6">
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
                    <div className="mt-3 grid gap-3 sm:grid-cols-2">
                      <div>
                        <label className="block text-sm font-medium mb-1">Minimum severity</label>
                        <select
                          value={notifications.webhookMinSeverity}
                          data-testid="webhook-severity-select"
                          onChange={(e) =>
                            setNotifications({
                              ...notifications,
                              webhookMinSeverity: e.target
                                .value as NotificationSettings['webhookMinSeverity'],
                            })
                          }
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        >
                          <option value="info">Info and above</option>
                          <option value="warning">Warning and above</option>
                          <option value="error">Error and above</option>
                          <option value="critical">Critical only</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">
                          Signing secret <span className="text-muted-foreground">(optional)</span>
                        </label>
                        <input
                          type="password"
                          value={notifications.webhookSecret}
                          data-testid="webhook-secret-input"
                          onChange={(e) =>
                            setNotifications({ ...notifications, webhookSecret: e.target.value })
                          }
                          placeholder="Leave blank for unsigned"
                          autoComplete="off"
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        />
                      </div>
                    </div>
                    {isAdmin && (
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          onClick={handleTestWebhook}
                          disabled={webhookTesting || !notifications.webhookUrl.trim()}
                          data-testid="webhook-test-button"
                          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 disabled:opacity-50"
                        >
                          {webhookTesting ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Bell className="h-4 w-4" />
                          )}
                          Send test
                        </button>
                        {webhookTestResult && (
                          <span
                            data-testid="webhook-test-result"
                            className={`flex items-center gap-1 text-xs ${
                              webhookTestResult.ok ? 'text-green-600' : 'text-red-500'
                            }`}
                          >
                            {webhookTestResult.ok ? (
                              <CheckCircle className="h-3.5 w-3.5 shrink-0" />
                            ) : (
                              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                            )}
                            {webhookTestResult.detail}
                          </span>
                        )}
                      </div>
                    )}
                    <p className="mt-2 text-xs text-muted-foreground">
                      Alerts at or above the chosen severity are POSTed to this URL as
                      they fire. With a secret set, each delivery carries an{' '}
                      <code>X-AIOPS-Signature: sha256=…</code> HMAC header. Public URLs only.
                    </p>
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
                  <code>/api/v1/settings/</code>. Webhook delivery is active: enabled webhooks
                  receive alerts server-side. Email / Slack delivery still needs
                  environment-variable configuration on the server.
                </p>
              </div>
            </div>
          </div>
          {isAdmin && <RemoteAlertingCard />}
          </div>
        )}

        {/* ━━ Telemetry ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        {activeTab === 'telemetry' && (
          <div className="space-y-6">
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
                      <label htmlFor="loki-url" className="block text-xs font-medium text-muted-foreground mb-1">
                        Loki endpoint URL
                      </label>
                      <input
                        id="loki-url"
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
                      <label htmlFor="prometheus-url" className="block text-xs font-medium text-muted-foreground mb-1">
                        Prometheus endpoint URL
                      </label>
                      <input
                        id="prometheus-url"
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
                      <label htmlFor="tempo-url" className="block text-xs font-medium text-muted-foreground mb-1">
                        Tempo endpoint URL
                      </label>
                      <input
                        id="tempo-url"
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

                <div className="p-3 bg-primary/10 border border-primary/20 rounded-lg text-xs text-primary">
                  <p className="font-semibold mb-1">Persistence</p>
                  <p>
                    Telemetry settings are persisted via <code>/api/v1/settings/</code>. Changes to
                    URLs or retention take effect on next backend restart / collector reload.
                  </p>
                </div>
              </div>
            </div>
          </div>
          <DockerSourceCard telemetry={telemetry} setTelemetry={setTelemetry} />
          </div>
        )}

        {/* ━━ Models ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        {activeTab === 'models' && (
          <div className="space-y-6">
            <ServingModeCard />
            <LlmEndpointsCard health={health} />
          </div>
        )}

        {/* ━━ System Prompts (admin-only editor) ━━━━━━━━━━━━━━━━━━━━━━━━ */}
        {isAdmin && activeTab === 'prompts' && (
          <div className="space-y-6">
            {/* Loud prompt feedback: errors stay until the next action. */}
            {promptError && (
              <div
                className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-red-500"
                role="alert"
                data-testid="prompt-error-banner"
              >
                <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                <span className="text-sm">{promptError}</span>
              </div>
            )}
            {promptNotice && !promptError && (
              <div
                className="flex items-start gap-2 rounded-lg border border-green-500/30 bg-green-500/10 p-3 text-green-600"
                data-testid="prompt-success-banner"
              >
                <CheckCircle className="h-4 w-4 mt-0.5 shrink-0" />
                <span className="text-sm">{promptNotice}</span>
              </div>
            )}
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
                                  : 'bg-primary/10 text-primary'
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

            <div className="bg-primary/10 border border-primary/20 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-primary mt-0.5" />
                <div>
                  <h3 className="font-semibold text-primary">About System Prompts</h3>
                  <p className="text-sm text-primary/80 mt-1">
                    System prompts define how each agent behaves. The Fast Agent handles quick
                    classification tasks, while the Reasoning Agent performs deep analysis and
                    planning. Changes take effect immediately for new requests.
                  </p>
                  <p className="text-xs text-primary/60 mt-2">
                    Saved via <code>/api/v1/prompts/</code>: a save succeeds only when the edit is
                    applied to the live agent and persisted; failures surface as an error banner
                    above. Use Save Settings above for Constitutional / Notification / Telemetry
                    configuration.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
        {/* ━━ Topology Schema (admin-only editor + LLM-generated topology) ━━ */}
        {isAdmin && activeTab === 'topology' && <TopologySchemaEditor />}

        {/* ━━ Account (self password change + admin user management) ━━ */}
        {activeTab === 'account' && <AccountSettings />}
      </div>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

const SERVING_MODE_INFO: Record<1 | 2, { title: string; description: string }> = {
  1: {
    title: 'Mode 1 — Dual engine',
    description:
      'Qwen3-4B (fast) + Qwen3-14B (reasoning) on dedicated engines. The frozen research-paper configuration.',
  },
  2: {
    title: 'Mode 2 — Modernized stack',
    description:
      'Single engine serving both agent roles via the mode-2 overlay, with streaming / guided JSON / priority scheduling as those phases land.',
  },
}

/** True when the agent endpoint is a local engine on this host — the only case
 *  where the Mode 1 <-> Mode 2 serving swap (the host-side aiops-mode-swap
 *  watcher restarting local vLLM engines) applies. Remote / bring-your-own
 *  endpoints (e.g. Bedrock) have no local engines to swap, so the card hides. */
function isLocalEngineUrl(url?: string): boolean {
  if (!url) return false
  try {
    const h = new URL(url).hostname
    return h === 'localhost' || h === '127.0.0.1' || h === '::1'
  } catch {
    return false
  }
}

function ServingModeCard() {
  const [status, setStatus] = useState<ServingModeStatus | null>(null)
  const [confirmTarget, setConfirmTarget] = useState<1 | 2 | null>(null)
  // Persists through the backend-restart window so fetch failures render as
  // "swapping" instead of an error.
  const [swapTarget, setSwapTarget] = useState<1 | 2 | null>(null)
  const [unreachable, setUnreachable] = useState(false)
  const [requestError, setRequestError] = useState<string | null>(null)
  const [posting, setPosting] = useState(false)
  // null = not yet known; the card only renders once confirmed local so it never
  // flashes on remote/BYO deployments where the swap does not apply.
  const [localEngines, setLocalEngines] = useState<boolean | null>(null)

  const refresh = useCallback(async () => {
    try {
      const s = await api.settings.servingMode()
      setStatus(s)
      setUnreachable(false)
      setSwapTarget((target) => {
        if (s.swap_status === 'error') return null
        if (target !== null && s.mode === target && s.swap_status === 'idle') return null
        return target
      })
    } catch {
      // Expected mid-swap: the backend container itself is being recreated.
      setUnreachable(true)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  // Decide whether local engines back the agents (see isLocalEngineUrl).
  useEffect(() => {
    let alive = true
    api.settings
      .getModels()
      .then((m) => { if (alive) setLocalEngines(isLocalEngineUrl(m.fastAgentUrl)) })
      .catch(() => { if (alive) setLocalEngines(false) })
    return () => { alive = false }
  }, [])

  const swapActive =
    swapTarget !== null ||
    status?.swap_status === 'pending' ||
    status?.swap_status === 'swapping'

  useEffect(() => {
    if (!swapActive) return
    const timer = setInterval(refresh, 5000)
    return () => clearInterval(timer)
  }, [swapActive, refresh])

  const requestSwap = async (mode: 1 | 2) => {
    setPosting(true)
    setRequestError(null)
    try {
      const s = await api.settings.requestServingMode(mode)
      setStatus(s)
      setSwapTarget(mode)
    } catch (err) {
      setRequestError(
        err instanceof Error ? err.message : 'Failed to request the mode swap',
      )
    } finally {
      setPosting(false)
      setConfirmTarget(null)
    }
  }

  const currentMode = status?.mode ?? null
  const targetMode = swapTarget ?? status?.requested_mode ?? null

  // Remote / bring-your-own endpoints have no local engines to swap — hide the
  // whole card there (null while still resolving, so it never flashes).
  if (localEngines !== true) return null

  return (
    <div className="bg-card rounded-lg border border-border p-6" data-testid="serving-mode-card">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <ArrowLeftRight className="h-5 w-5 text-muted-foreground" />
          Serving Mode
        </h2>
        {currentMode !== null && (
          <span
            data-testid="serving-mode-badge"
            className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              currentMode === 2
                ? 'bg-primary/10 text-primary'
                : 'bg-green-500/10 text-green-500'
            }`}
          >
            Mode {currentMode} active
          </span>
        )}
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        Which LLM serving stack backs the agents. Swapping restarts the engines —
        chat and analysis are unavailable for ~3–5 minutes while it runs.
      </p>

      <div
        className="grid grid-cols-1 sm:grid-cols-2 gap-3"
        role="radiogroup"
        aria-label="Serving mode"
      >
        {([1, 2] as const).map((m) => {
          const info = SERVING_MODE_INFO[m]
          const isCurrent = currentMode === m
          return (
            <button
              key={m}
              type="button"
              role="radio"
              aria-checked={isCurrent}
              data-testid={`serving-mode-${m}`}
              disabled={swapActive || posting || isCurrent}
              onClick={() => setConfirmTarget(m)}
              className={`text-left p-4 rounded-lg border transition-colors ${
                isCurrent
                  ? 'border-primary bg-primary/5'
                  : 'border-border bg-background hover:bg-muted disabled:opacity-50'
              } ${swapActive || posting ? 'cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-sm">{info.title}</span>
                {isCurrent && <CheckCircle className="h-4 w-4 text-primary shrink-0" />}
              </div>
              <p className="text-xs text-muted-foreground mt-1">{info.description}</p>
            </button>
          )
        })}
      </div>

      {/* Confirmation step — a swap takes the LLM stack down for minutes. */}
      {confirmTarget !== null && !swapActive && (
        <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <p className="text-sm text-yellow-700 flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
            Swap to Mode {confirmTarget}? The LLM engines restart and the assistant
            is unavailable for roughly 3–5 minutes. Data (incidents, memory,
            conversations) is untouched.
          </p>
          <div className="flex gap-2 mt-3">
            <button
              type="button"
              data-testid="serving-mode-confirm"
              disabled={posting}
              onClick={() => requestSwap(confirmTarget)}
              className="px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
            >
              {posting ? 'Requesting…' : `Swap to Mode ${confirmTarget}`}
            </button>
            <button
              type="button"
              disabled={posting}
              onClick={() => setConfirmTarget(null)}
              className="px-3 py-1.5 bg-muted text-muted-foreground rounded-lg text-sm hover:bg-muted/80"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {swapActive && (
        <div
          className="mt-4 p-3 bg-primary/10 border border-primary/30 rounded-lg flex items-start gap-2 text-sm text-primary"
          data-testid="serving-mode-swapping"
        >
          <Loader2 className="h-4 w-4 mt-0.5 animate-spin shrink-0" />
          <span>
            {unreachable
              ? 'Swapping — the backend is restarting; reconnecting…'
              : `Swap ${targetMode !== null ? `to Mode ${targetMode} ` : ''}in progress — engines are restarting (~3–5 min). This page keeps polling.`}
          </span>
        </div>
      )}

      {status?.swap_status === 'error' && !swapActive && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-2 text-sm text-red-500">
          <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
          <span>Last swap failed: {status.detail || 'see mode-swap/last-swap.log on the server'}.</span>
        </div>
      )}

      {requestError && (
        <p className="mt-3 text-sm text-red-500">{requestError}</p>
      )}

      <div className="mt-4 p-3 bg-primary/10 border border-primary/20 rounded-lg text-xs text-primary">
        <p className="font-semibold mb-1">How it works</p>
        <p>
          The toggle writes a swap request that the host-side{' '}
          <code>aiops-mode-swap</code> watcher executes via{' '}
          <code>scripts/mode-swap.sh</code> (the backend itself has no Docker
          access). Data stores are shared by both modes, so nothing is migrated
          or lost.
        </p>
      </div>
    </div>
  )
}

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

/**
 * Settings -> Models: view + edit the bring-your-own LLM endpoint config
 * (URL + served model per agent + an optional API key). Reads the REAL config
 * from GET /settings/models (no more hardcoded VRAM / GPU / port claims), saves
 * via PUT (applied live, no restart), and can probe the endpoints on demand.
 * The API key is write-only: it is never returned, and a blank field on save
 * keeps whatever key is already stored.
 */
function LlmEndpointsCard({ health }: { health: HealthResponse | null }) {
  // The connection test probes the box's global endpoint (admin-only), so only
  // admins see it; a regular tenant edits their own per-user endpoint here and
  // validates it by using chat.
  const authRequired = useAuthStore((s) => s.authRequired)
  const currentRole = useAuthStore((s) => s.user?.role)
  const isAdmin = !authRequired || currentRole === 'admin'
  const [cfg, setCfg] = useState<ModelsConfig | null>(null)
  const [fastUrl, setFastUrl] = useState('')
  const [fastModel, setFastModel] = useState('')
  const [reasoningUrl, setReasoningUrl] = useState('')
  const [reasoningModel, setReasoningModel] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [sameEndpoint, setSameEndpoint] = useState(true)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<ModelsTestResult | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const c = await api.settings.getModels()
      setCfg(c)
      setFastUrl(c.fastAgentUrl)
      setFastModel(c.fastAgentModel)
      setReasoningUrl(c.reasoningAgentUrl)
      setReasoningModel(c.reasoningAgentModel)
      setSameEndpoint(
        c.fastAgentUrl === c.reasoningAgentUrl && c.fastAgentModel === c.reasoningAgentModel,
      )
    } catch {
      setError('Could not load the LLM endpoint configuration — is the backend running?')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const keyIsSet = Boolean(cfg?.fastApiKeySet || cfg?.reasoningApiKeySet)

  const persist = async (clearKey: boolean) => {
    setSaving(true)
    setError(null)
    setTestResult(null)
    try {
      const body: ModelsConfigUpdate = {
        fastAgentUrl: fastUrl.trim(),
        fastAgentModel: fastModel.trim(),
        reasoningAgentUrl: (sameEndpoint ? fastUrl : reasoningUrl).trim(),
        reasoningAgentModel: (sameEndpoint ? fastModel : reasoningModel).trim(),
      }
      if (clearKey) body.apiKey = ''
      else if (apiKey.trim()) body.apiKey = apiKey.trim()

      const updated = await api.settings.saveModels(body)
      setCfg(updated)
      setFastUrl(updated.fastAgentUrl)
      setFastModel(updated.fastAgentModel)
      setReasoningUrl(updated.reasoningAgentUrl)
      setReasoningModel(updated.reasoningAgentModel)
      setApiKey('')
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Save failed — only an admin can change the LLM endpoints.',
      )
    } finally {
      setSaving(false)
    }
  }

  const runTest = async () => {
    setTesting(true)
    setTestResult(null)
    setError(null)
    try {
      setTestResult(await api.settings.testModels())
    } catch {
      setError('Could not run the connection test.')
    } finally {
      setTesting(false)
    }
  }

  const canSave = Boolean(
    fastUrl.trim() &&
      fastModel.trim() &&
      (sameEndpoint || (reasoningUrl.trim() && reasoningModel.trim())),
  )

  const inputClass =
    'w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary'

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Editable endpoint form */}
      <div className="bg-card rounded-lg border border-border p-6">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Link2 className="h-5 w-5 text-muted-foreground" />
            LLM Endpoints
          </h2>
          {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
        </div>
        <p className="text-sm text-muted-foreground mb-4">
          Bring your own OpenAI-compatible endpoint. Saved changes apply live — no restart.
        </p>

        {error && (
          <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-500">
            <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="space-y-4">
          <label className="flex items-center gap-3 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={sameEndpoint}
              onChange={(e) => setSameEndpoint(e.target.checked)}
              className="h-4 w-4 accent-primary"
            />
            <span>Use the same endpoint and model for both agents</span>
          </label>

          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">
              {sameEndpoint ? 'Endpoint URL' : 'Fast agent — endpoint URL'}
            </label>
            <input
              type="url"
              value={fastUrl}
              onChange={(e) => setFastUrl(e.target.value)}
              placeholder="https://api.example.com/v1"
              className={inputClass}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">
              {sameEndpoint ? 'Model name' : 'Fast agent — model name'}
            </label>
            <input
              type="text"
              value={fastModel}
              onChange={(e) => setFastModel(e.target.value)}
              placeholder="qwen3-4b"
              className={inputClass}
            />
          </div>

          {!sameEndpoint && (
            <>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Reasoning agent — endpoint URL
                </label>
                <input
                  type="url"
                  value={reasoningUrl}
                  onChange={(e) => setReasoningUrl(e.target.value)}
                  placeholder="https://api.example.com/v1"
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Reasoning agent — model name
                </label>
                <input
                  type="text"
                  value={reasoningModel}
                  onChange={(e) => setReasoningModel(e.target.value)}
                  placeholder="qwen3-14b"
                  className={inputClass}
                />
              </div>
            </>
          )}

          <div>
            <label className="flex items-center gap-1 text-xs font-medium text-muted-foreground mb-1">
              <KeyRound className="h-3 w-3" />
              API key {keyIsSet && <span className="text-green-500">(set)</span>}
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={keyIsSet ? '•••••••• (leave blank to keep)' : 'Optional — for a secured endpoint'}
              autoComplete="off"
              className={inputClass}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Sent as <code>Authorization: Bearer</code>. Stored on the server and never shown again.
              {keyIsSet && (
                <>
                  {' '}
                  <button
                    type="button"
                    onClick={() => persist(true)}
                    disabled={saving}
                    className="text-red-500 hover:underline disabled:opacity-50"
                  >
                    Remove key
                  </button>
                </>
              )}
            </p>
          </div>

          <div className="flex items-center gap-2 pt-1">
            <button
              onClick={() => persist(false)}
              disabled={saving || !canSave}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : saved ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              {saved ? 'Saved!' : 'Save endpoints'}
            </button>
            {isAdmin && (
              <button
                onClick={runTest}
                disabled={testing}
                className="flex items-center gap-2 px-4 py-2 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80 disabled:opacity-50"
              >
                {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                Test connection
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Live status + graph memory (all real, no hardcoded hardware claims) */}
      <div className="space-y-6">
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Cpu className="h-5 w-5 text-muted-foreground" />
            Live Status
          </h2>
          <div className="space-y-3">
            <EndpointStatusRow
              label="Fast agent"
              model={cfg?.fastAgentModel}
              online={isComponentHealthy(health, 'fast_agent')}
              tested={testResult?.fast_agent}
            />
            <EndpointStatusRow
              label="Reasoning agent"
              model={cfg?.reasoningAgentModel}
              online={isComponentHealthy(health, 'reasoning_agent')}
              tested={testResult?.reasoning_agent}
            />
          </div>
          <p className="text-xs text-muted-foreground mt-4">
            Online reflects the periodic health probe. Test connection runs an on-demand probe of
            the saved endpoints.
          </p>
        </div>

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
              : 'Neo4j not deployed. Using the in-memory episode store with similarity search.'}
          </p>
        </div>
      </div>
    </div>
  )
}

function EndpointStatusRow({
  label,
  model,
  online,
  tested,
}: {
  label: string
  model?: string
  online: boolean
  tested?: boolean
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/30 px-3 py-2">
      <div className="min-w-0">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground truncate font-mono">
          {model || 'not configured'}
        </p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {tested !== undefined && (
          <span className={`text-xs ${tested ? 'text-green-500' : 'text-red-500'}`}>
            {tested ? 'reachable' : 'unreachable'}
          </span>
        )}
        <span
          className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${
            online ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
          }`}
        >
          {online ? <CheckCircle className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
          {online ? 'online' : 'offline'}
        </span>
      </div>
    </div>
  )
}

// The severity floors shared by both alerting channels (mirrors the webhook select).
const ALERT_SEVERITIES: { value: AlertSeverity; label: string }[] = [
  { value: 'info', label: 'Info and above' },
  { value: 'warning', label: 'Warning and above' },
  { value: 'error', label: 'Error and above' },
  { value: 'critical', label: 'Critical only' },
]

function SeveritySelect({
  value,
  onChange,
  testId,
}: {
  value: AlertSeverity
  onChange: (v: AlertSeverity) => void
  testId?: string
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-muted-foreground mb-1">Minimum severity</label>
      <select
        value={value}
        data-testid={testId}
        onChange={(e) => onChange(e.target.value as AlertSeverity)}
        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
      >
        {ALERT_SEVERITIES.map((s) => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </select>
    </div>
  )
}

/**
 * Settings -> Notifications -> Remote alerting (Track 1, admin-only). Forwards
 * fired alerts at or above a chosen severity to a Telegram chat and/or a Matrix
 * room through the outbound adapters. Self-contained load/save/test state,
 * mirroring LlmEndpointsCard. Bot tokens are write-only: blank keeps the stored
 * secret, "Remove token" clears it, a value replaces it (encrypted server-side).
 * The Test button probes the SAVED config, so save before testing edited values.
 */
function RemoteAlertingCard() {
  const [cfg, setCfg] = useState<AlertingConfig | null>(null)

  const [tgEnabled, setTgEnabled] = useState(false)
  const [tgChatId, setTgChatId] = useState('')
  const [tgToken, setTgToken] = useState('')
  const [tgSeverity, setTgSeverity] = useState<AlertSeverity>('warning')

  const [mxEnabled, setMxEnabled] = useState(false)
  const [mxHomeserver, setMxHomeserver] = useState('')
  const [mxRoomId, setMxRoomId] = useState('')
  const [mxToken, setMxToken] = useState('')
  const [mxSeverity, setMxSeverity] = useState<AlertSeverity>('warning')

  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [testing, setTesting] = useState<AlertingChannel | null>(null)
  const [testResult, setTestResult] = useState<
    Partial<Record<AlertingChannel, { ok: boolean; detail: string }>>
  >({})

  const applyConfig = (c: AlertingConfig) => {
    setCfg(c)
    setTgEnabled(c.telegram.enabled)
    setTgChatId(c.telegram.chatId)
    setTgSeverity(c.telegram.minSeverity)
    setMxEnabled(c.matrix.enabled)
    setMxHomeserver(c.matrix.homeserver)
    setMxRoomId(c.matrix.roomId)
    setMxSeverity(c.matrix.minSeverity)
    // Tokens are never returned — always reset the write-only inputs to blank.
    setTgToken('')
    setMxToken('')
  }

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      applyConfig(await api.settings.getAlerting())
    } catch {
      setError('Could not load remote alerting settings — admin only, and the backend must be running.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const persist = async (clear?: { telegram?: boolean; matrix?: boolean }) => {
    setSaving(true)
    setError(null)
    setTestResult({})
    try {
      const body = buildAlertingUpdate(
        {
          enabled: tgEnabled,
          chatId: tgChatId,
          token: tgToken,
          clearToken: Boolean(clear?.telegram),
          minSeverity: tgSeverity,
        },
        {
          enabled: mxEnabled,
          homeserver: mxHomeserver,
          roomId: mxRoomId,
          token: mxToken,
          clearToken: Boolean(clear?.matrix),
          minSeverity: mxSeverity,
        },
      )
      applyConfig(await api.settings.saveAlerting(body))
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed — only an admin can change remote alerting.')
    } finally {
      setSaving(false)
    }
  }

  const testChannel = async (channel: AlertingChannel) => {
    setTesting(channel)
    setTestResult((prev) => ({ ...prev, [channel]: undefined }))
    try {
      const r = await api.settings.testAlerting(channel)
      setTestResult((prev) => ({ ...prev, [channel]: r }))
    } catch (err) {
      setTestResult((prev) => ({
        ...prev,
        [channel]: { ok: false, detail: err instanceof Error ? err.message : 'test failed' },
      }))
    } finally {
      setTesting(null)
    }
  }

  const tgTokenSet = Boolean(cfg?.telegram.tokenSet)
  const mxTokenSet = Boolean(cfg?.matrix.accessTokenSet)
  // A channel can only be enabled once it has its routing ids and a token
  // (already stored, or entered now) — otherwise a save would arm a dead channel.
  const tgIncomplete = tgEnabled && !(tgChatId.trim() && (tgTokenSet || tgToken.trim()))
  const mxIncomplete =
    mxEnabled && !(mxHomeserver.trim() && mxRoomId.trim() && (mxTokenSet || mxToken.trim()))

  const inputClass =
    'w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary'

  return (
    <div className="bg-card rounded-lg border border-border p-6" data-testid="remote-alerting-card">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Bell className="h-5 w-5 text-muted-foreground" />
          Remote alerting
        </h2>
        {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        Forward fired alerts at or above a chosen severity to a Telegram chat or a Matrix room.
        Admin only. Bot tokens are encrypted at rest and never shown again.
      </p>

      {error && (
        <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-500">
          <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Telegram */}
        <div className="space-y-3">
          <ToggleSetting
            label="Telegram"
            description="Send alerts to a Telegram chat via a bot"
            checked={tgEnabled}
            testId="toggle-telegram-alerting"
            onChange={setTgEnabled}
          />
          {tgEnabled && (
            <div className="ml-6 space-y-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Chat ID</label>
                <input
                  type="text"
                  value={tgChatId}
                  data-testid="telegram-chat-id"
                  onChange={(e) => setTgChatId(e.target.value)}
                  placeholder="123456789 or -1001234567890"
                  className={inputClass}
                />
              </div>
              <div>
                <label className="flex items-center gap-1 text-xs font-medium text-muted-foreground mb-1">
                  <KeyRound className="h-3 w-3" />
                  Bot token {tgTokenSet && <span className="text-green-500">(set)</span>}
                </label>
                <input
                  type="password"
                  value={tgToken}
                  data-testid="telegram-bot-token"
                  onChange={(e) => setTgToken(e.target.value)}
                  placeholder={tgTokenSet ? '•••••••• (leave blank to keep)' : 'From @BotFather'}
                  autoComplete="off"
                  className={inputClass}
                />
                {tgTokenSet && (
                  <button
                    type="button"
                    onClick={() => persist({ telegram: true })}
                    disabled={saving}
                    className="mt-1 text-xs text-red-500 hover:underline disabled:opacity-50"
                  >
                    Remove token
                  </button>
                )}
              </div>
              <SeveritySelect value={tgSeverity} onChange={setTgSeverity} testId="telegram-severity" />
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => testChannel('telegram')}
                  disabled={testing !== null}
                  data-testid="telegram-test-button"
                  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 disabled:opacity-50"
                >
                  {testing === 'telegram' ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Bell className="h-4 w-4" />
                  )}
                  Send test
                </button>
                {testResult.telegram && (
                  <span
                    data-testid="telegram-test-result"
                    className={`flex items-center gap-1 text-xs ${
                      testResult.telegram.ok ? 'text-green-600' : 'text-red-500'
                    }`}
                  >
                    {testResult.telegram.ok ? (
                      <CheckCircle className="h-3.5 w-3.5 shrink-0" />
                    ) : (
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                    )}
                    {testResult.telegram.detail}
                  </span>
                )}
              </div>
              {tgIncomplete && (
                <p className="text-xs text-yellow-600">
                  Add a chat ID and bot token to enable Telegram alerts.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Matrix */}
        <div className="space-y-3">
          <ToggleSetting
            label="Matrix"
            description="Send alerts to a Matrix room via an access token"
            checked={mxEnabled}
            testId="toggle-matrix-alerting"
            onChange={setMxEnabled}
          />
          {mxEnabled && (
            <div className="ml-6 space-y-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Homeserver URL</label>
                <input
                  type="url"
                  value={mxHomeserver}
                  data-testid="matrix-homeserver"
                  onChange={(e) => setMxHomeserver(e.target.value)}
                  placeholder="https://matrix.org"
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Room ID</label>
                <input
                  type="text"
                  value={mxRoomId}
                  data-testid="matrix-room-id"
                  onChange={(e) => setMxRoomId(e.target.value)}
                  placeholder="!roomid:matrix.org"
                  className={inputClass}
                />
              </div>
              <div>
                <label className="flex items-center gap-1 text-xs font-medium text-muted-foreground mb-1">
                  <KeyRound className="h-3 w-3" />
                  Access token {mxTokenSet && <span className="text-green-500">(set)</span>}
                </label>
                <input
                  type="password"
                  value={mxToken}
                  data-testid="matrix-access-token"
                  onChange={(e) => setMxToken(e.target.value)}
                  placeholder={mxTokenSet ? '•••••••• (leave blank to keep)' : 'Bot account access token'}
                  autoComplete="off"
                  className={inputClass}
                />
                {mxTokenSet && (
                  <button
                    type="button"
                    onClick={() => persist({ matrix: true })}
                    disabled={saving}
                    className="mt-1 text-xs text-red-500 hover:underline disabled:opacity-50"
                  >
                    Remove token
                  </button>
                )}
              </div>
              <SeveritySelect value={mxSeverity} onChange={setMxSeverity} testId="matrix-severity" />
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => testChannel('matrix')}
                  disabled={testing !== null}
                  data-testid="matrix-test-button"
                  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 disabled:opacity-50"
                >
                  {testing === 'matrix' ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Bell className="h-4 w-4" />
                  )}
                  Send test
                </button>
                {testResult.matrix && (
                  <span
                    data-testid="matrix-test-result"
                    className={`flex items-center gap-1 text-xs ${
                      testResult.matrix.ok ? 'text-green-600' : 'text-red-500'
                    }`}
                  >
                    {testResult.matrix.ok ? (
                      <CheckCircle className="h-3.5 w-3.5 shrink-0" />
                    ) : (
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                    )}
                    {testResult.matrix.detail}
                  </span>
                )}
              </div>
              {mxIncomplete && (
                <p className="text-xs text-yellow-600">
                  Add a homeserver, room ID and access token to enable Matrix alerts.
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => persist()}
          disabled={saving || tgIncomplete || mxIncomplete}
          data-testid="save-alerting"
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
        >
          {saving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : saved ? (
            <CheckCircle className="h-4 w-4" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          {saved ? 'Saved!' : 'Save alerting'}
        </button>
        <p className="text-xs text-muted-foreground">
          Send test uses the last saved config — save before testing edited values.
        </p>
      </div>
    </div>
  )
}
