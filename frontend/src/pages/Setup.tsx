/**
 * Constitutional AIOps - First-run Quick-Setup wizard (shell).
 *
 * Full-screen guided setup rendered OUTSIDE the app sidebar (its own /setup
 * route, RequireAuth-gated). This is the P2 shell: step framework, progress
 * rail, CSS-only animated transitions (reduced-motion safe), and skip/resume.
 * The five configuration steps carry preview panels here; P3-P5 replace each
 * body with its interactive content (services, topology, prompt, LLM,
 * monitoring). Welcome and Finish are real.
 */

import { useEffect, useState, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Activity,
  CheckCircle2,
  ChevronLeft,
  Cpu,
  Loader2,
  MessageSquare,
  Plus,
  RefreshCw,
  Rocket,
  Save,
  Server,
  Share2,
  ShieldCheck,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react'

import { TopologySchemaEditor } from '../components/TopologySchemaEditor'
import api from '../lib/api'
import type {
  AllSettings,
  ModelsConfig,
  ModelsConfigUpdate,
  ModelsTestResult,
  MonitoringTestResult,
  RemediationMode,
} from '../lib/api'
import { useAuthStore } from '../lib/auth'
import { markByokSetupSeen } from '../lib/useEndpointStatus'
import { useWizardStore } from '../lib/onboarding/store'
import { cleanServices } from '../lib/onboarding/services'
import {
  RAIL_STEPS,
  isFirstStep,
  isLastStep,
  stepIndex,
  stepMeta,
} from '../lib/onboarding/steps'
import type { WizardStepId } from '../lib/onboarding/types'

const STEP_ICON: Record<WizardStepId, typeof Rocket> = {
  welcome: Rocket,
  services: Server,
  topology: Share2,
  prompt: MessageSquare,
  llm: Cpu,
  monitoring: Activity,
  safety: ShieldCheck,
  finish: CheckCircle2,
}

/** Short preview copy for the config steps whose interactive body lands in P3-P5. */
const STEP_PREVIEW: Record<WizardStepId, string> = {
  welcome: '',
  services: 'List the services you run (a name and a role). We prefill from any containers we can already see.',
  topology: 'We generate a dependency map from your services. Preview it, then edit the map before you apply it.',
  prompt: 'We draft a base system prompt describing your platform. Edit it, then save it as the assistant prompt.',
  llm: 'Point the assistant at your OpenAI-compatible model endpoint and key, and test the connection.',
  monitoring: 'Add your Loki, Prometheus and Tempo URLs (or skip), and live-test that each source is reachable.',
  safety: 'Decide how far the assistant may go on its own. Every action still passes the constitution and the audit trail.',
  finish: '',
}

function StepIconBadge({ id }: { id: WizardStepId }) {
  const Icon = STEP_ICON[id]
  return (
    <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
      <Icon className="h-6 w-6" aria-hidden="true" />
    </span>
  )
}

function StepHeading({ id }: { id: WizardStepId }) {
  const meta = stepMeta(id)
  return (
    <div className="flex items-center gap-4">
      <StepIconBadge id={id} />
      <div>
        <h2 className="text-xl font-semibold tracking-tight">{meta.title}</h2>
        <p className="text-sm text-muted-foreground">{meta.subtitle}</p>
      </div>
    </div>
  )
}

function WelcomeStep() {
  return (
    <div className="space-y-6">
      <StepHeading id="welcome" />
      <p className="text-sm leading-relaxed text-muted-foreground">
        This quick setup connects Constitutional AIOps to your platform. It takes
        a couple of minutes and every step is optional, so you can skip anything
        and finish it later from Settings.
      </p>
      <ul className="grid gap-2 sm:grid-cols-2">
        {RAIL_STEPS.map((s) => {
          const Icon = STEP_ICON[s.id]
          return (
            <li
              key={s.id}
              className="flex items-start gap-3 rounded-xl border border-border bg-card/50 p-3"
            >
              <Icon className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
              <span>
                <span className="block text-sm font-medium">{s.title}</span>
                <span className="block text-xs text-muted-foreground">{s.subtitle}</span>
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function FinishStep() {
  return (
    <div className="space-y-6">
      <StepHeading id="finish" />
      <p className="text-sm leading-relaxed text-muted-foreground">
        That is the guided setup. You can revisit any of these from Settings
        whenever you need to. Jump straight into the app:
      </p>
      <div className="grid gap-2 sm:grid-cols-3">
        {[
          { to: '/', label: 'Dashboard' },
          { to: '/chat', label: 'Chat' },
          { to: '/incidents', label: 'Incidents' },
        ].map((l) => (
          <Link
            key={l.to}
            to={l.to}
            className="rounded-xl border border-border bg-card/50 px-4 py-3 text-center text-sm font-medium transition-colors hover:border-primary/40 hover:bg-accent"
          >
            {l.label}
          </Link>
        ))}
      </div>
    </div>
  )
}

const WIZ_INPUT =
  'w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none transition-colors focus:border-primary/60'
const WIZ_BTN_SECONDARY =
  'inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm font-medium transition-colors hover:bg-accent disabled:opacity-50'
const WIZ_BTN_PRIMARY =
  'inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-60'

/** Labelled text input used across the config steps. */
function WizField({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  hint,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  type?: string
  hint?: string
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-muted-foreground">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={WIZ_INPUT}
      />
      {hint && <span className="mt-1 block text-xs text-muted-foreground">{hint}</span>}
    </label>
  )
}

/** Inline error/success banner shared by the config steps. */
function StepBanner({ error, notice }: { error?: string | null; notice?: string | null }) {
  if (error) {
    return (
      <div
        className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
        role="alert"
      >
        {error}
      </div>
    )
  }
  if (notice) {
    return (
      <div className="rounded-lg border border-primary/30 bg-primary/10 p-3 text-sm text-primary">
        {notice}
      </div>
    )
  }
  return null
}

/** Services step: detect live containers, then edit names/roles/dependencies. */
function ServicesStep() {
  const services = useWizardStore((s) => s.services)
  const servicesStatus = useWizardStore((s) => s.servicesStatus)
  const prefillServices = useWizardStore((s) => s.prefillServices)
  const addService = useWizardStore((s) => s.addService)
  const updateService = useWizardStore((s) => s.updateService)
  const removeService = useWizardStore((s) => s.removeService)

  // Seed once from live containers when this step first opens (fails soft).
  useEffect(() => {
    void prefillServices()
  }, [prefillServices])

  const detecting = servicesStatus === 'loading'

  const toggleDep = (index: number, target: string) => {
    const current = services[index]?.dependsOn ?? []
    const next = current.includes(target)
      ? current.filter((d) => d !== target)
      : [...current, target]
    updateService(index, { dependsOn: next })
  }

  return (
    <div className="space-y-6">
      <StepHeading id="services" />
      <p className="text-sm leading-relaxed text-muted-foreground">{STEP_PREVIEW.services}</p>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => void prefillServices()}
          disabled={detecting}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm font-medium transition-colors hover:bg-accent disabled:opacity-50"
        >
          {detecting ? (
            <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
          ) : (
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
          )}
          Detect running services
        </button>
        <button
          type="button"
          onClick={addService}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm font-medium transition-colors hover:bg-accent"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          Add service
        </button>
      </div>

      {services.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-muted/30 p-6 text-center text-sm text-muted-foreground">
          {detecting
            ? 'Looking for services already running…'
            : 'No services yet. Detect the ones already running, or add them by hand.'}
        </div>
      ) : (
        <ul className="space-y-3">
          {services.map((svc, i) => {
            const others = services
              .filter((o, j) => j !== i && o.name.trim())
              .map((o) => o.name.trim())
            const deps = svc.dependsOn ?? []
            return (
              <li key={i} className="space-y-3 rounded-xl border border-border bg-card/50 p-4">
                <div className="flex items-start gap-2">
                  <div className="grid flex-1 gap-3 sm:grid-cols-2">
                    <label className="block">
                      <span className="mb-1 block text-xs font-medium text-muted-foreground">
                        Name
                      </span>
                      <input
                        value={svc.name}
                        onChange={(e) => updateService(i, { name: e.target.value })}
                        placeholder="checkout-api"
                        className={WIZ_INPUT}
                      />
                    </label>
                    <label className="block">
                      <span className="mb-1 block text-xs font-medium text-muted-foreground">
                        Role
                      </span>
                      <input
                        value={svc.role}
                        onChange={(e) => updateService(i, { role: e.target.value })}
                        placeholder="frontend, backend, datastore…"
                        className={WIZ_INPUT}
                      />
                    </label>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeService(i)}
                    aria-label={`Remove ${svc.name.trim() || 'service'}`}
                    className="mt-6 rounded-lg border border-border p-2 text-muted-foreground transition-colors hover:border-destructive/40 hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                  </button>
                </div>
                {others.length > 0 && (
                  <div>
                    <span className="mb-1.5 block text-xs font-medium text-muted-foreground">
                      Depends on
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {others.map((name) => {
                        const on = deps.includes(name)
                        return (
                          <button
                            key={name}
                            type="button"
                            onClick={() => toggleDep(i, name)}
                            aria-pressed={on}
                            className={[
                              'rounded-full border px-2.5 py-1 text-xs transition-colors',
                              on
                                ? 'border-primary bg-primary/10 font-medium text-primary'
                                : 'border-border text-muted-foreground hover:border-primary/40',
                            ].join(' ')}
                          >
                            {name}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

/** Topology step: generate a schema from the entered services, edit, apply. */
function TopologyStep() {
  const services = useWizardStore((s) => s.services)
  const [applied, setApplied] = useState(false)
  const cleaned = cleanServices(services)

  const extraGenerator =
    cleaned.length > 0
      ? {
          label: 'Generate from your services',
          description:
            'Build a dependency map from the services you listed. Shown as a preview — nothing changes until you click Apply.',
          run: () => api.topology.generateFromServices({ services: cleaned, mode: 'template' }),
        }
      : undefined

  return (
    <div className="space-y-6">
      <StepHeading id="topology" />
      <p className="text-sm leading-relaxed text-muted-foreground">{STEP_PREVIEW.topology}</p>
      {cleaned.length === 0 && (
        <p className="rounded-lg border border-dashed border-border bg-muted/30 p-3 text-xs text-muted-foreground">
          Add a service on the previous step to generate a map from it, or sync from live
          infrastructure below.
        </p>
      )}
      {applied && (
        <div className="rounded-lg border border-primary/30 bg-primary/10 p-3 text-sm text-primary">
          Topology applied. You can keep editing, or continue.
        </div>
      )}
      <TopologySchemaEditor extraGenerator={extraGenerator} onApplied={() => setApplied(true)} />
    </div>
  )
}

/** Base-prompt step: draft from services + topology, edit, save as reasoning_chat. */
function PromptStep() {
  const services = useWizardStore((s) => s.services)
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(true)
  const [drafting, setDrafting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    setLoading(true)
    api.prompts
      .get('reasoning_chat')
      .then((p) => {
        if (alive) setText(p.prompt)
      })
      .catch((e) => {
        if (alive) setError(e instanceof Error ? e.message : 'Failed to load the base prompt')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [])

  const handleDraft = async () => {
    setDrafting(true)
    setError(null)
    setNotice(null)
    try {
      const schema = await api.topology.getSchema()
      const draft = await api.prompts.generate({
        services: cleanServices(services),
        topology: { nodes: schema.nodes, edges: schema.edges },
        mode: 'template',
      })
      setText(draft.prompt)
      setNotice(draft.note || 'Draft generated from your services and topology. Edit it, then save.')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not draft a prompt')
    } finally {
      setDrafting(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setNotice(null)
    try {
      await api.prompts.update('reasoning_chat', text)
      setNotice('Saved as the assistant base prompt.')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save the prompt')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <StepHeading id="prompt" />
      <p className="text-sm leading-relaxed text-muted-foreground">{STEP_PREVIEW.prompt}</p>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive" role="alert">
          {error}
        </div>
      )}
      {notice && !error && (
        <div className="rounded-lg border border-primary/30 bg-primary/10 p-3 text-sm text-primary">
          {notice}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={handleDraft}
          disabled={drafting || loading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm font-medium transition-colors hover:bg-accent disabled:opacity-50"
        >
          {drafting ? (
            <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
          ) : (
            <Sparkles className="h-4 w-4" aria-hidden="true" />
          )}
          Draft from services + topology
        </button>
        <button
          type="button"
          onClick={handleSave}
          disabled={saving || loading || text.trim().length < 10}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-60"
        >
          {saving ? (
            <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
          ) : (
            <Save className="h-4 w-4" aria-hidden="true" />
          )}
          Save as assistant prompt
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-10">
          <Loader2 className="h-6 w-6 motion-safe:animate-spin text-muted-foreground" aria-hidden="true" />
        </div>
      ) : (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={16}
          spellCheck={false}
          className="w-full rounded-lg border border-border bg-background p-3 font-mono text-xs outline-none transition-colors focus:border-primary/60 resize-y"
        />
      )}
      <p className="text-xs text-muted-foreground">
        The base prompt (reasoning_chat) steers the assistant. Between 10 and 10000 characters.
      </p>
    </div>
  )
}

/** A single reachable/unreachable pill for a connection test. */
function ProbeChip({ ok }: { ok: boolean }) {
  return ok ? (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-primary">
      <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" /> reachable
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-destructive">
      <X className="h-3.5 w-3.5" aria-hidden="true" /> unreachable
    </span>
  )
}

/** LLM endpoint step: point the assistant at an OpenAI-compatible model + key.
 *
 * ``showTest`` hides the "Test connection" probe (admin-only on the hosted box:
 * it exercises the global endpoint, so it is not offered in the per-tenant BYOK
 * onboarding). ``onSaved`` fires with the fresh config after a successful save. */
function LlmStep({
  showTest = true,
  onSaved,
}: {
  showTest?: boolean
  onSaved?: (cfg: ModelsConfig) => void
} = {}) {
  const [cfg, setCfg] = useState<ModelsConfig | null>(null)
  const [reasoningUrl, setReasoningUrl] = useState('')
  const [reasoningModel, setReasoningModel] = useState('')
  const [fastUrl, setFastUrl] = useState('')
  const [fastModel, setFastModel] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<ModelsTestResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    setLoading(true)
    api.settings
      .getModels()
      .then((c) => {
        if (!alive) return
        setCfg(c)
        setReasoningUrl(c.reasoningAgentUrl)
        setReasoningModel(c.reasoningAgentModel)
        setFastUrl(c.fastAgentUrl)
        setFastModel(c.fastAgentModel)
      })
      .catch((e) => {
        if (alive) setError(e instanceof Error ? e.message : 'Failed to load model settings')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [])

  const useSameForBoth = () => {
    setFastUrl(reasoningUrl)
    setFastModel(reasoningModel)
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setNotice(null)
    setResult(null)
    try {
      const body: ModelsConfigUpdate = {
        reasoningAgentUrl: reasoningUrl.trim(),
        reasoningAgentModel: reasoningModel.trim(),
        fastAgentUrl: fastUrl.trim(),
        fastAgentModel: fastModel.trim(),
      }
      if (apiKey) body.apiKey = apiKey
      const saved = await api.settings.saveModels(body)
      setCfg(saved)
      setApiKey('')
      setNotice('Saved. The assistant now uses this endpoint.')
      onSaved?.(saved)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save the endpoint')
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setError(null)
    setNotice(null)
    try {
      setResult(await api.settings.testModels())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Test failed')
    } finally {
      setTesting(false)
    }
  }

  const keyPlaceholder = cfg?.reasoningApiKeySet || cfg?.fastApiKeySet ? 'Key set — leave blank to keep it' : 'sk-… (optional)'

  return (
    <div className="space-y-6">
      <StepHeading id="llm" />
      <p className="text-sm leading-relaxed text-muted-foreground">{STEP_PREVIEW.llm}</p>

      <StepBanner error={error} notice={notice} />

      {loading ? (
        <div className="flex items-center justify-center py-10">
          <Loader2 className="h-6 w-6 motion-safe:animate-spin text-muted-foreground" aria-hidden="true" />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-card/50 p-4">
            <p className="mb-3 text-sm font-medium">Reasoning model (chat, root-cause analysis)</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <WizField
                label="Endpoint URL"
                value={reasoningUrl}
                onChange={setReasoningUrl}
                placeholder="https://api.example.com/v1"
              />
              <WizField
                label="Model"
                value={reasoningModel}
                onChange={setReasoningModel}
                placeholder="qwen3-14b"
              />
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card/50 p-4">
            <div className="mb-3 flex items-center justify-between gap-2">
              <p className="text-sm font-medium">Fast model (telemetry annotation)</p>
              <button type="button" onClick={useSameForBoth} className="text-xs font-medium text-primary hover:underline">
                Use the reasoning endpoint for both
              </button>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <WizField
                label="Endpoint URL"
                value={fastUrl}
                onChange={setFastUrl}
                placeholder="https://api.example.com/v1"
              />
              <WizField
                label="Model"
                value={fastModel}
                onChange={setFastModel}
                placeholder="qwen3-4b"
              />
            </div>
          </div>

          <WizField
            label="API key"
            value={apiKey}
            onChange={setApiKey}
            type="password"
            placeholder={keyPlaceholder}
            hint="Sent as an Authorization: Bearer header. Write-only — it is never shown back."
          />

          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={handleSave} disabled={saving} className={WIZ_BTN_PRIMARY}>
              {saving ? (
                <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
              ) : (
                <Save className="h-4 w-4" aria-hidden="true" />
              )}
              Save endpoint
            </button>
            {showTest && (
              <button type="button" onClick={handleTest} disabled={testing} className={WIZ_BTN_SECONDARY}>
                {testing ? (
                  <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
                ) : (
                  <RefreshCw className="h-4 w-4" aria-hidden="true" />
                )}
                Test connection
              </button>
            )}
          </div>

          {showTest && result && (
            <div className="flex flex-wrap gap-4 rounded-lg border border-border bg-muted/30 p-3">
              <span className="flex items-center gap-2 text-sm">Reasoning <ProbeChip ok={result.reasoning_agent} /></span>
              <span className="flex items-center gap-2 text-sm">Fast <ProbeChip ok={result.fast_agent} /></span>
            </div>
          )}
          {showTest && (
            <p className="text-xs text-muted-foreground">Test checks the currently saved endpoints — save first to test new values.</p>
          )}
        </div>
      )}
    </div>
  )
}

/** Monitoring step: capture Loki/Prometheus/Tempo URLs and live-test each. */
function MonitoringStep() {
  const [settings, setSettings] = useState<AllSettings | null>(null)
  const [loki, setLoki] = useState('')
  const [prom, setProm] = useState('')
  const [tempo, setTempo] = useState('')
  const [dockerEnabled, setDockerEnabled] = useState(true)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<MonitoringTestResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    setLoading(true)
    api.settings
      .get()
      .then((s) => {
        if (!alive) return
        setSettings(s)
        setLoki(s.telemetry.lokiUrl)
        setProm(s.telemetry.prometheusUrl)
        setTempo(s.telemetry.tempoUrl)
        setDockerEnabled(s.telemetry.dockerEnabled)
      })
      .catch((e) => {
        if (alive) setError(e instanceof Error ? e.message : 'Failed to load monitoring settings')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [])

  const handleTest = async () => {
    setTesting(true)
    setError(null)
    setNotice(null)
    try {
      setResult(
        await api.settings.testMonitoring({
          lokiUrl: loki.trim() || undefined,
          prometheusUrl: prom.trim() || undefined,
          tempoUrl: tempo.trim() || undefined,
          docker: true,
        }),
      )
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Test failed')
    } finally {
      setTesting(false)
    }
  }

  const handleSave = async () => {
    if (!settings) return
    setSaving(true)
    setError(null)
    setNotice(null)
    try {
      const saved = await api.settings.save({
        ...settings,
        telemetry: {
          ...settings.telemetry,
          lokiUrl: loki.trim(),
          lokiEnabled: loki.trim().length > 0,
          prometheusUrl: prom.trim(),
          prometheusEnabled: prom.trim().length > 0,
          tempoUrl: tempo.trim(),
          tempoEnabled: tempo.trim().length > 0,
          dockerEnabled,
        },
      })
      setSettings(saved)
      setNotice('Monitoring sources saved.')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save monitoring settings')
    } finally {
      setSaving(false)
    }
  }

  const rows: { key: keyof MonitoringTestResult; label: string; value: string; set: (v: string) => void; hint: string }[] = [
    { key: 'loki', label: 'Loki (logs)', value: loki, set: setLoki, hint: 'Base URL, e.g. http://loki:3100' },
    { key: 'prometheus', label: 'Prometheus (metrics)', value: prom, set: setProm, hint: 'Base URL, e.g. http://prometheus:9090' },
    { key: 'tempo', label: 'Tempo (traces)', value: tempo, set: setTempo, hint: 'Base URL, e.g. http://tempo:3200' },
  ]

  return (
    <div className="space-y-6">
      <StepHeading id="monitoring" />
      <p className="text-sm leading-relaxed text-muted-foreground">{STEP_PREVIEW.monitoring}</p>

      <StepBanner error={error} notice={notice} />

      {loading ? (
        <div className="flex items-center justify-center py-10">
          <Loader2 className="h-6 w-6 motion-safe:animate-spin text-muted-foreground" aria-hidden="true" />
        </div>
      ) : (
        <div className="space-y-4">
          {rows.map((r) => {
            const probe = result?.[r.key] ?? null
            return (
              <div key={r.key} className="rounded-xl border border-border bg-card/50 p-4">
                <WizField label={r.label} value={r.value} onChange={r.set} placeholder={r.hint} />
                {probe && (
                  <p className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                    <ProbeChip ok={probe.ok} />
                    <span className="truncate">{probe.detail}</span>
                  </p>
                )}
              </div>
            )
          })}

          {/* Local Docker-socket source — no URL, just an on/off + a live test.
              The fallback that makes Telemetry/Dashboard work with no LGTM. */}
          <div className="rounded-xl border border-border bg-card/50 p-4">
            <label className="flex cursor-pointer items-start gap-3">
              <input
                type="checkbox"
                checked={dockerEnabled}
                onChange={(e) => setDockerEnabled(e.target.checked)}
                data-testid="setup-docker-toggle"
                className="mt-1 h-4 w-4 rounded border-border"
              />
              <span>
                <span className="text-sm font-medium">Local Docker socket</span>
                <span className="block text-xs text-muted-foreground">
                  No LGTM stack? Read logs and live CPU / memory metrics from the host's
                  Docker socket. Recommended for the lite / self-host tier.
                </span>
              </span>
            </label>
            {result?.docker && (
              <p className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                <ProbeChip ok={result.docker.ok} />
                <span className="truncate">{result.docker.detail}</span>
              </p>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={handleSave} disabled={saving} className={WIZ_BTN_PRIMARY}>
              {saving ? (
                <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
              ) : (
                <Save className="h-4 w-4" aria-hidden="true" />
              )}
              Save sources
            </button>
            <button type="button" onClick={handleTest} disabled={testing} className={WIZ_BTN_SECONDARY}>
              {testing ? (
                <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
              ) : (
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
              )}
              Test sources
            </button>
          </div>
          <p className="text-xs text-muted-foreground">
            No telemetry yet? Leave these blank and skip — the assistant still works, it just has less
            evidence to draw on.
          </p>
        </div>
      )}
    </div>
  )
}

/** The three remediation modes and their one-line safety copy (mirrors Settings). */
const REMEDIATION_MODES: { mode: RemediationMode; label: string; help: string }[] = [
  {
    mode: 'diagnose',
    label: 'Diagnose only',
    help: 'The assistant investigates and explains, but never proposes or runs a fix. The safest place to start.',
  },
  {
    mode: 'approve',
    label: 'Approve to run',
    help: 'The assistant proposes a fix in chat; nothing executes until you click Approve. Recommended default.',
  },
  {
    mode: 'auto',
    label: 'Auto-remediate',
    help: 'Allowlisted, high-confidence fixes execute automatically once they pass the constitution; everything else still asks for approval.',
  },
]

/** Safety step: choose the remediation mode and keep the audit trail on. */
function SafetyStep() {
  const [settings, setSettings] = useState<AllSettings | null>(null)
  const [mode, setMode] = useState<RemediationMode>('approve')
  const [auditLog, setAuditLog] = useState(true)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    setLoading(true)
    api.settings
      .get()
      .then((s) => {
        if (!alive) return
        setSettings(s)
        setMode(s.remediation.mode)
        setAuditLog(s.constitutional.enableAuditLog)
      })
      .catch((e) => {
        if (alive) setError(e instanceof Error ? e.message : 'Failed to load safety settings')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [])

  const handleSave = async () => {
    if (!settings) return
    setSaving(true)
    setError(null)
    setNotice(null)
    try {
      const saved = await api.settings.save({
        ...settings,
        constitutional: { ...settings.constitutional, enableAuditLog: auditLog },
        remediation: { ...settings.remediation, mode },
      })
      setSettings(saved)
      setNotice('Safety settings saved. You can fine-tune the allowlist later in Settings.')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save safety settings')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <StepHeading id="safety" />
      <p className="text-sm leading-relaxed text-muted-foreground">{STEP_PREVIEW.safety}</p>

      <div className="rounded-xl border border-border bg-card/50 p-4 text-sm leading-relaxed text-muted-foreground">
        Every proposed fix runs through the constitution first: a set of safety principles across
        three tiers. Tier 1 rules (no unconfirmed data loss, keep replicas healthy, reversible
        actions) are never crossed. What you pick below is only how far the assistant may act on its
        own once a fix has already passed those checks.
      </div>

      <StepBanner error={error} notice={notice} />

      {loading ? (
        <div className="flex items-center justify-center py-10">
          <Loader2 className="h-6 w-6 motion-safe:animate-spin text-muted-foreground" aria-hidden="true" />
        </div>
      ) : (
        <div className="space-y-4">
          <fieldset className="space-y-3">
            <legend className="mb-1 text-xs font-medium text-muted-foreground">Remediation mode</legend>
            {REMEDIATION_MODES.map((m) => {
              const on = mode === m.mode
              return (
                <label
                  key={m.mode}
                  className={[
                    'flex cursor-pointer items-start gap-3 rounded-xl border p-4 transition-colors',
                    on ? 'border-primary bg-primary/5' : 'border-border bg-card/50 hover:border-primary/40',
                  ].join(' ')}
                >
                  <input
                    type="radio"
                    name="remediation-mode"
                    value={m.mode}
                    checked={on}
                    onChange={() => setMode(m.mode)}
                    className="mt-1 h-4 w-4"
                  />
                  <span>
                    <span className="block text-sm font-medium capitalize">{m.label}</span>
                    <span className="block text-xs text-muted-foreground">{m.help}</span>
                  </span>
                </label>
              )
            })}
          </fieldset>

          <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-border bg-card/50 p-4">
            <input
              type="checkbox"
              checked={auditLog}
              onChange={(e) => setAuditLog(e.target.checked)}
              data-testid="setup-audit-toggle"
              className="mt-1 h-4 w-4 rounded border-border"
            />
            <span>
              <span className="text-sm font-medium">Keep the audit log on</span>
              <span className="block text-xs text-muted-foreground">
                Record every validation, approval and action so you can review what the assistant
                did and why. Recommended.
              </span>
            </span>
          </label>

          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={handleSave} disabled={saving} className={WIZ_BTN_PRIMARY}>
              {saving ? (
                <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
              ) : (
                <Save className="h-4 w-4" aria-hidden="true" />
              )}
              Save safety settings
            </button>
          </div>
          <p className="text-xs text-muted-foreground">
            You can change the mode, the auto allowlist and the confidence threshold any time from
            Settings &rarr; Remediation.
          </p>
        </div>
      )}
    </div>
  )
}

function renderStep(id: WizardStepId): ReactNode {
  if (id === 'welcome') return <WelcomeStep />
  if (id === 'finish') return <FinishStep />
  if (id === 'services') return <ServicesStep />
  if (id === 'topology') return <TopologyStep />
  if (id === 'prompt') return <PromptStep />
  if (id === 'llm') return <LlmStep />
  if (id === 'monitoring') return <MonitoringStep />
  if (id === 'safety') return <SafetyStep />
  return null // all step ids are handled above
}

/** Horizontal progress rail of the five configuration steps. */
function ProgressRail({ current }: { current: WizardStepId }) {
  const curIdx = stepIndex(current)
  return (
    <ol className="flex items-center justify-center gap-1 sm:gap-2" aria-label="Setup progress">
      {RAIL_STEPS.map((s, i) => {
        const idx = stepIndex(s.id)
        const done = curIdx > idx
        const active = curIdx === idx
        return (
          <li key={s.id} className="flex items-center gap-1 sm:gap-2">
            <span
              className={[
                'flex h-8 w-8 items-center justify-center rounded-full border text-xs font-semibold transition-colors',
                done
                  ? 'border-primary bg-primary text-primary-foreground'
                  : active
                    ? 'border-primary text-primary'
                    : 'border-border text-muted-foreground',
              ].join(' ')}
              aria-current={active ? 'step' : undefined}
              title={s.title}
            >
              {done ? <CheckCircle2 className="h-4 w-4" aria-hidden="true" /> : i + 1}
            </span>
            <span
              className={[
                'hidden text-xs sm:inline',
                active ? 'font-medium text-foreground' : 'text-muted-foreground',
              ].join(' ')}
            >
              {s.title}
            </span>
            {i < RAIL_STEPS.length - 1 && (
              <span
                className={[
                  'mx-0.5 h-px w-4 sm:w-8',
                  done ? 'bg-primary' : 'bg-border',
                ].join(' ')}
                aria-hidden="true"
              />
            )}
          </li>
        )
      })}
    </ol>
  )
}

/** The full admin platform wizard (services -> topology -> prompt -> LLM ->
 * monitoring -> safety). Its topology/prompt steps hit admin-only endpoints, so
 * it is shown only to admins / self-host; a regular tenant gets ByokOnlySetup. */
function AdminWizard() {
  const navigate = useNavigate()
  const status = useWizardStore((s) => s.status)
  const currentStep = useWizardStore((s) => s.currentStep)
  const error = useWizardStore((s) => s.error)
  const load = useWizardStore((s) => s.load)
  const next = useWizardStore((s) => s.next)
  const back = useWizardStore((s) => s.back)
  const skip = useWizardStore((s) => s.skip)
  const complete = useWizardStore((s) => s.complete)

  useEffect(() => {
    void load()
  }, [load])

  const leaveToApp = () => navigate('/', { replace: true })

  const onSkip = async () => {
    await skip()
    leaveToApp()
  }

  const onFinish = async () => {
    await complete()
    leaveToApp()
  }

  if (status === 'idle' || status === 'loading') {
    return (
      <div
        className="flex min-h-screen items-center justify-center bg-background"
        role="status"
        aria-label="Loading setup"
      >
        <Loader2 className="h-8 w-8 motion-safe:animate-spin text-muted-foreground" aria-hidden="true" />
      </div>
    )
  }

  const first = isFirstStep(currentStep)
  const last = isLastStep(currentStep)
  const busy = status === 'saving'
  const primaryLabel = currentStep === 'welcome' ? 'Start setup' : last ? 'Finish' : 'Next'

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border px-4 py-3 sm:px-6">
        <span className="inline-flex items-center gap-2 text-sm font-semibold">
          <Rocket className="h-4 w-4 text-primary" aria-hidden="true" />
          Quick setup
        </span>
        <button
          type="button"
          onClick={onSkip}
          disabled={busy}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-sm text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
        >
          <X className="h-4 w-4" aria-hidden="true" />
          Skip setup
        </button>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-8 sm:px-6">
        <div className="mb-8">
          <ProgressRail current={currentStep} />
        </div>

        <div key={currentStep} className="wiz-step flex-1 rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
          {renderStep(currentStep)}
        </div>

        {error && (
          <p className="mt-3 text-sm text-destructive" role="alert">
            {error}
          </p>
        )}

        <div className="mt-6 flex items-center justify-between">
          <button
            type="button"
            onClick={back}
            disabled={first || busy}
            className="inline-flex items-center gap-1 rounded-lg border border-border px-4 py-2 text-sm font-medium transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            Back
          </button>

          <span className="text-xs text-muted-foreground">
            Step {stepIndex(currentStep) + 1} of {RAIL_STEPS.length + 2}
          </span>

          <button
            type="button"
            onClick={last ? onFinish : next}
            disabled={busy}
            className="inline-flex items-center gap-1 rounded-lg bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-60"
          >
            {busy && <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />}
            {primaryLabel}
          </button>
        </div>
      </main>
    </div>
  )
}

/** Focused BYOK onboarding for a regular (non-admin) tenant: connect an LLM
 * endpoint, then continue. The admin platform steps (topology/prompt generation,
 * all admin-only on the backend) are intentionally not shown to a tenant — their
 * one required first-run step is pointing the app at their own model. */
function ByokOnlySetup() {
  const navigate = useNavigate()

  // Spend the one-shot onboarding redirect the moment this view opens, so a
  // "Continue to app" that returns to "/" is never bounced back here.
  useEffect(() => {
    markByokSetupSeen()
  }, [])

  const leaveToApp = () => navigate('/', { replace: true })

  const handleSaved = (cfg: ModelsConfig) => {
    const complete = Boolean(
      cfg.fastAgentUrl.trim() &&
        cfg.fastAgentModel.trim() &&
        cfg.reasoningAgentUrl.trim() &&
        cfg.reasoningAgentModel.trim(),
    )
    // A complete endpoint is all that is needed — drop straight into the app.
    if (complete) leaveToApp()
  }

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border px-4 py-3 sm:px-6">
        <span className="inline-flex items-center gap-2 text-sm font-semibold">
          <Cpu className="h-4 w-4 text-primary" aria-hidden="true" />
          Connect your model
        </span>
        <button
          type="button"
          onClick={leaveToApp}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <X className="h-4 w-4" aria-hidden="true" />
          Skip for now
        </button>
      </header>

      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-4 py-8 sm:px-6">
        <div className="mb-6">
          <h1 className="text-xl font-semibold tracking-tight">Connect your LLM endpoint</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Constitutional AIOps runs on your own OpenAI-compatible model. Point it at your
            endpoint and key to start — chat and analysis use this, and the key is stored encrypted
            for your account only.
          </p>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
          <LlmStep showTest={false} onSaved={handleSaved} />
        </div>

        <div className="mt-6 flex items-center justify-end">
          <button
            type="button"
            onClick={leaveToApp}
            className="inline-flex items-center gap-1 rounded-lg bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Continue to app
          </button>
        </div>
      </main>
    </div>
  )
}

/** Role dispatcher for /setup: a regular tenant gets the focused BYOK step; an
 * admin / self-host gets the full platform wizard (unchanged). */
export function Setup() {
  const authRequired = useAuthStore((s) => s.authRequired)
  const role = useAuthStore((s) => s.user?.role)
  const authStatus = useAuthStore((s) => s.status)

  if (authStatus !== 'ready') {
    return (
      <div
        className="flex min-h-screen items-center justify-center bg-background"
        role="status"
        aria-label="Loading setup"
      >
        <Loader2 className="h-8 w-8 motion-safe:animate-spin text-muted-foreground" aria-hidden="true" />
      </div>
    )
  }

  const isRegularUser = authRequired && Boolean(role) && role !== 'admin'
  return isRegularUser ? <ByokOnlySetup /> : <AdminWizard />
}

export default Setup
