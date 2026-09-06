import { describe, it, expect, afterEach, vi } from 'vitest'
import { LOCAL_MODELS, webgpuSupported, loadedModelId } from './webllm'

describe('webllm wrapper helpers', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('exposes a non-empty, well-formed curated model list', () => {
    expect(LOCAL_MODELS.length).toBeGreaterThan(0)
    for (const m of LOCAL_MODELS) {
      expect(m.id).toBeTruthy()
      expect(m.label).toBeTruthy()
      expect(m.sizeLabel).toBeTruthy()
    }
    // ids are unique
    const ids = new Set(LOCAL_MODELS.map((m) => m.id))
    expect(ids.size).toBe(LOCAL_MODELS.length)
  })

  it('reports WebGPU support from navigator.gpu presence', () => {
    vi.stubGlobal('navigator', { gpu: {} })
    expect(webgpuSupported()).toBe(true)
    vi.stubGlobal('navigator', {})
    expect(webgpuSupported()).toBe(false)
  })

  it('has no engine loaded before any load call', () => {
    expect(loadedModelId()).toBeNull()
  })
})
