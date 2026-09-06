import { useEffect, useRef, useState } from 'react'
import {
  Laptop,
  Loader2,
  Send,
  ShieldCheck,
  AlertTriangle,
  Download,
  Square,
} from 'lucide-react'
import {
  LOCAL_MODELS,
  webgpuSupported,
  loadLocalEngine,
  streamLocalChat,
  unloadLocalEngine,
  loadedModelId,
  type LocalChatMessage,
  type LoadProgress,
} from '../lib/webllm'

const SYSTEM_PROMPT: LocalChatMessage = {
  role: 'system',
  content:
    'You are a helpful assistant running entirely in the user\'s web browser. ' +
    'Keep answers concise. You have no access to their infrastructure or the ' +
    'Constitutional AIOps backend.',
}

/**
 * In-browser, chat-only fallback (Phase C). Runs a small model locally via
 * WebGPU with @mlc-ai/web-llm — no endpoint required and nothing leaves the
 * device. This is intentionally separate from the server-backed Chat page: it
 * offers a way to try the assistant before wiring up a real LLM endpoint.
 */
export function LocalChat() {
  const supported = webgpuSupported()
  const [modelId, setModelId] = useState(LOCAL_MODELS[0].id)
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready'>(
    loadedModelId() ? 'ready' : 'idle',
  )
  const [progress, setProgress] = useState<LoadProgress | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [messages, setMessages] = useState<LocalChatMessage[]>([])
  const [input, setInput] = useState('')
  const [generating, setGenerating] = useState(false)

  const scrollRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight })
  }, [messages, generating])

  // Free GPU memory when leaving the page.
  useEffect(() => {
    return () => {
      void unloadLocalEngine()
    }
  }, [])

  const onLoad = async () => {
    setError(null)
    setStatus('loading')
    setProgress({ progress: 0, text: 'Preparing…' })
    try {
      await loadLocalEngine(modelId, setProgress)
      setStatus('ready')
    } catch (err) {
      setStatus('idle')
      setError(err instanceof Error ? err.message : 'Could not load the model.')
    }
  }

  const onSend = async () => {
    const text = input.trim()
    if (!text || generating || status !== 'ready') return
    setInput('')
    const history: LocalChatMessage[] = [...messages, { role: 'user', content: text }]
    setMessages([...history, { role: 'assistant', content: '' }])
    setGenerating(true)
    setError(null)
    try {
      const engine = await loadLocalEngine(modelId)
      let reply = ''
      for await (const delta of streamLocalChat(engine, [SYSTEM_PROMPT, ...history])) {
        reply += delta
        setMessages([...history, { role: 'assistant', content: reply }])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed.')
      setMessages(history) // drop the empty assistant bubble
    } finally {
      setGenerating(false)
    }
  }

  const activeModel = LOCAL_MODELS.find((m) => m.id === modelId)

  if (!supported) {
    return (
      <div className="mx-auto max-w-2xl space-y-4 py-8">
        <PageHeader />
        <div className="flex items-start gap-3 rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4 text-sm text-yellow-700">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <p className="font-medium">WebGPU is not available in this browser.</p>
            <p className="mt-1">
              The in-browser model needs WebGPU. Try a recent Chrome or Edge on desktop,
              or configure a real LLM endpoint in Settings → Models instead.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col gap-4 py-6">
      <PageHeader />

      <div className="flex items-start gap-3 rounded-lg border border-primary/20 bg-primary/5 p-3 text-xs text-muted-foreground">
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
        <p>
          Runs entirely in your browser on WebGPU. The model downloads once (then it is
          cached) and every message is processed on your device — nothing is sent to our
          servers. Small local models are slower and far less capable than a configured
          endpoint; treat this as a preview.
        </p>
      </div>

      {status !== 'ready' ? (
        <div className="rounded-lg border border-border bg-card p-6">
          <label className="mb-2 block text-sm font-medium">Choose a model</label>
          <div className="flex flex-wrap items-end gap-3">
            <select
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              disabled={status === 'loading'}
              className="rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {LOCAL_MODELS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label} ({m.sizeLabel})
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => void onLoad()}
              disabled={status === 'loading'}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {status === 'loading' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              {status === 'loading' ? 'Loading…' : 'Load model'}
            </button>
          </div>
          {activeModel?.note && (
            <p className="mt-2 text-xs text-muted-foreground">{activeModel.note}.</p>
          )}
          {status === 'loading' && progress && (
            <div className="mt-4">
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-primary transition-all"
                  style={{ width: `${Math.round((progress.progress || 0) * 100)}%` }}
                />
              </div>
              <p className="mt-1.5 truncate text-xs text-muted-foreground">{progress.text}</p>
            </div>
          )}
          {error && (
            <p className="mt-3 flex items-center gap-1.5 text-sm text-destructive">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </p>
          )}
        </div>
      ) : (
        <>
          <div
            ref={scrollRef}
            className="flex-1 space-y-4 overflow-y-auto rounded-lg border border-border bg-card p-4"
          >
            {messages.length === 0 && (
              <p className="py-8 text-center text-sm text-muted-foreground">
                {activeModel?.label} is loaded. Ask it anything.
              </p>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}
              >
                <div
                  className={`max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                    m.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-foreground'
                  }`}
                >
                  {m.content || (generating && i === messages.length - 1 ? '…' : '')}
                </div>
              </div>
            ))}
          </div>

          {error && (
            <p className="flex items-center gap-1.5 text-sm text-destructive">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </p>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault()
              void onSend()
            }}
            className="flex items-center gap-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Message ${activeModel?.label ?? 'the model'}…`}
              className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <button
              type="submit"
              disabled={generating || !input.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {generating ? <Square className="h-4 w-4" /> : <Send className="h-4 w-4" />}
            </button>
          </form>
          <p className="text-center text-xs text-muted-foreground">
            {activeModel?.label} · running locally on WebGPU
          </p>
        </>
      )}
    </div>
  )
}

function PageHeader() {
  return (
    <div className="flex items-center gap-2">
      <Laptop className="h-6 w-6 text-primary" />
      <div>
        <h1 className="text-xl font-semibold">Local browser model</h1>
        <p className="text-sm text-muted-foreground">
          Chat with a small model that runs entirely on your device.
        </p>
      </div>
    </div>
  )
}
