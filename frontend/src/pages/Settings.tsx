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
  Wrench,
  Waypoints,
  ArrowLeftRight,
  UserCog,
} from 'lucide-react'
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
} from '../lib/api'
import { TopologySchemaEditor } from '../components/TopologySchemaEditor'
import { AccountSettings } from '../components/AccountSettings'

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

// ── main component ────────────────────────────────────────────────────────────
export function Settings() {
  const [activeTab, setActiveTab] = useState<
    'constitutional' | 'remediation' | 'notifications' | 'telemetry' | 'models' | 'prompts' | 'topology' | 'account'
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
        )}

        {/* ━━ Models ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        {activeTab === 'models' && (
          <div className="space-y-6">
          <ServingModeCard />
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
                  model="Qwen3-4B-AWQ"
                  port={8000}
                  status={isComponentHealthy(health, 'fast_agent') ? 'online' : 'offline'}
                  purpose="Telemetry annotation, classification"
                  context="4K tokens"
                  latency="<100ms P95"
                />
                <ModelStatusCard
                  name="Reasoning Agent"
                  model="Qwen3-14B-AWQ"
                  port={8001}
                  status={isComponentHealthy(health, 'reasoning_agent') ? 'online' : 'offline'}
                  purpose="RCA, remediation planning, human chat"
                  context="8K tokens"
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
          </div>
        )}

        {/* ━━ System Prompts ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        {activeTab === 'prompts' && (
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
        {/* ━━ Topology Schema (editable + LLM-generated platform topology) ━━ */}
        {activeTab === 'topology' && <TopologySchemaEditor />}

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

function ServingModeCard() {
  const [status, setStatus] = useState<ServingModeStatus | null>(null)
  const [confirmTarget, setConfirmTarget] = useState<1 | 2 | null>(null)
  // Persists through the backend-restart window so fetch failures render as
  // "swapping" instead of an error.
  const [swapTarget, setSwapTarget] = useState<1 | 2 | null>(null)
  const [unreachable, setUnreachable] = useState(false)
  const [requestError, setRequestError] = useState<string | null>(null)
  const [posting, setPosting] = useState(false)

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
