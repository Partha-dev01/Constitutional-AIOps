import { describe, it, expect, vi, beforeEach } from 'vitest'

const metricsMock = vi.fn()
vi.mock('./api', () => ({
  api: { telemetry: { metrics: (...args: unknown[]) => metricsMock(...args) } },
}))

import { fetchMetrics1h, __resetMetrics1h } from './metrics1h'

beforeEach(() => {
  __resetMetrics1h()
  metricsMock.mockReset()
})

describe('fetchMetrics1h', () => {
  it('shares one request across concurrent callers', async () => {
    metricsMock.mockResolvedValue({ metrics: [{ label: 'a', value: 1, timestamp: 't' }] })
    const [a, b, c] = await Promise.all([fetchMetrics1h(), fetchMetrics1h(), fetchMetrics1h()])
    expect(metricsMock).toHaveBeenCalledTimes(1)
    expect(a).toHaveLength(1)
    // Concurrent callers get the same resolved array, not three fetches.
    expect(b).toBe(a)
    expect(c).toBe(a)
  })

  it('reuses the cached result inside the share window', async () => {
    metricsMock.mockResolvedValue({ metrics: [{ label: 'a', value: 1, timestamp: 't' }] })
    await fetchMetrics1h()
    await fetchMetrics1h()
    expect(metricsMock).toHaveBeenCalledTimes(1)
  })

  it('returns an empty array when the instance has no metrics', async () => {
    metricsMock.mockResolvedValue({ metrics: [] })
    expect(await fetchMetrics1h()).toEqual([])
  })

  it('does not cache a failed fetch, so the next call retries', async () => {
    metricsMock.mockRejectedValueOnce(new Error('boom'))
    await expect(fetchMetrics1h()).rejects.toThrow('boom')
    metricsMock.mockResolvedValueOnce({ metrics: [{ label: 'x', value: 2, timestamp: 't' }] })
    const points = await fetchMetrics1h()
    expect(points).toHaveLength(1)
    expect(metricsMock).toHaveBeenCalledTimes(2)
  })
})
