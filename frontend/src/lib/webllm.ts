/**
 * Thin wrapper around @mlc-ai/web-llm (Phase C: in-browser, chat-only fallback).
 *
 * The library ships a large WASM + engine payload, so it is loaded via a dynamic
 * import INSIDE loadLocalEngine — it never enters the main bundle and is only
 * fetched the first time a user actually loads a local model. Everything here is
 * client-side: model weights download to the browser cache and inference runs on
 * the visitor's own WebGPU device. Nothing is sent to our servers.
 */

import type { MLCEngineInterface, InitProgressReport } from '@mlc-ai/web-llm'

export type LocalRole = 'system' | 'user' | 'assistant'

export interface LocalChatMessage {
  role: LocalRole
  content: string
}

export interface LocalModel {
  /** MLC model_id passed to CreateMLCEngine. */
  id: string
  label: string
  /** Rough first-load download size (cached afterwards). */
  sizeLabel: string
  note?: string
}

/**
 * A small, deliberately tiny curated set — big models are impractical to
 * download and run in a browser tab. Ordered smallest/fastest first.
 */
export const LOCAL_MODELS: LocalModel[] = [
  {
    id: 'SmolLM2-360M-Instruct-q4f16_1-MLC',
    label: 'SmolLM2 360M',
    sizeLabel: '~300 MB',
    note: 'Fastest to load, most basic answers',
  },
  {
    id: 'Qwen2.5-0.5B-Instruct-q4f16_1-MLC',
    label: 'Qwen2.5 0.5B',
    sizeLabel: '~500 MB',
    note: 'A good balance for a tiny model',
  },
  {
    id: 'Llama-3.2-1B-Instruct-q4f16_1-MLC',
    label: 'Llama 3.2 1B',
    sizeLabel: '~900 MB',
    note: 'Best quality here, slowest to load',
  },
]

/** WebGPU is required. Absent on non-WebGPU browsers (e.g. most iOS, older FF). */
export function webgpuSupported(): boolean {
  return typeof navigator !== 'undefined' && 'gpu' in navigator
}

export interface LoadProgress {
  /** 0..1 */
  progress: number
  text: string
}

let _enginePromise: Promise<MLCEngineInterface> | null = null
let _loadedModelId: string | null = null

/** The model id the engine is currently (loading or) loaded for, else null. */
export function loadedModelId(): string | null {
  return _loadedModelId
}

/**
 * Load (or reuse) an in-browser engine for ``modelId``. Switching models unloads
 * the previous engine first. The @mlc-ai/web-llm import happens here, lazily.
 */
export async function loadLocalEngine(
  modelId: string,
  onProgress?: (p: LoadProgress) => void,
): Promise<MLCEngineInterface> {
  if (_enginePromise && _loadedModelId === modelId) {
    return _enginePromise
  }
  if (_enginePromise) {
    await unloadLocalEngine()
  }
  _loadedModelId = modelId
  _enginePromise = (async () => {
    const webllm = await import('@mlc-ai/web-llm')
    return webllm.CreateMLCEngine(modelId, {
      initProgressCallback: (report: InitProgressReport) =>
        onProgress?.({ progress: report.progress, text: report.text }),
    })
  })()
  return _enginePromise
}

/** Stream a chat completion, yielding content deltas as they arrive. */
export async function* streamLocalChat(
  engine: MLCEngineInterface,
  messages: LocalChatMessage[],
  opts?: { temperature?: number },
): AsyncGenerator<string> {
  const chunks = await engine.chat.completions.create({
    messages,
    stream: true,
    temperature: opts?.temperature ?? 0.7,
  })
  for await (const chunk of chunks) {
    const delta = chunk.choices[0]?.delta?.content
    if (delta) yield delta
  }
}

/** Dispose the current engine and free its GPU memory. Safe to call anytime. */
export async function unloadLocalEngine(): Promise<void> {
  const pending = _enginePromise
  _enginePromise = null
  _loadedModelId = null
  if (!pending) return
  try {
    const engine = await pending
    await engine.unload()
  } catch {
    // Engine never finished loading, or already gone — nothing to free.
  }
}
