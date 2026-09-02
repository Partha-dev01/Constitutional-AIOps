/**
 * useContainerStats — live per-service CPU%/mem% for the lite tier.
 *
 * Polls GET /telemetry/metrics (which falls back to the local Docker socket
 * when no Prometheus is present) and accumulates a rolling, client-side window
 * of the REAL sampled points — no fabricated history. Each poll contributes at
 * most one point per service per metric; a service that stops reporting simply
 * stops growing. Shared by the Dashboard live graphs, the chat live-services
 * card, and the Command Center.
 */

import { useEffect, useRef, useState } from 'react'
import api from '../lib/api'

export interface ServiceSeries {
  /** Raw container name (e.g. aiops-backend). */
  service: string
  /** Display label (aiops- prefix stripped). */
  label: string
  cpu: number[]
  mem: number[]
  memMb: number[]
  latestCpu: number | null
  latestMem: number | null
  latestMemMb: number | null
}

export interface ContainerStatsState {
  series: ServiceSeries[]
  /** 'docker' | 'prometheus' | 'none' — where the metrics came from. */
  source: string
  loading: boolean
  error: string | null
}

interface Options {
  /** Poll cadence in ms (default 5000). */
  intervalMs?: number
  /** Rolling window length (samples kept per series, default 30). */
  window?: number
  /** When false, stop polling entirely (e.g. the Docker source is disabled). */
  enabled?: boolean
}

function displayLabel(service: string): string {
  return service.startsWith('aiops-') ? service.slice(6) : service
}

export function useContainerStats({
  intervalMs = 5000,
  window = 30,
  enabled = true,
}: Options = {}): ContainerStatsState {
  const [state, setState] = useState<ContainerStatsState>({
    series: [],
    source: 'none',
    loading: enabled,
    error: null,
  })
  const seriesRef = useRef<Map<string, ServiceSeries>>(new Map())

  useEffect(() => {
    if (!enabled) {
      setState((s) => ({ ...s, loading: false }))
      return
    }
    let cancelled = false

    const poll = async () => {
      try {
        const res = await api.telemetry.metrics()
        if (cancelled) return

        // Collapse this poll's points into per-service instantaneous values.
        const byService = new Map<string, { cpu?: number; mem?: number; memMb?: number }>()
        for (const p of res.metrics) {
          const svc = p.service
          if (!svc) continue
          const cur = byService.get(svc) || {}
          if (p.metric === 'cpu_percent') cur.cpu = p.value
          else if (p.metric === 'mem_percent') cur.mem = p.value
          else if (p.metric === 'mem_mb') cur.memMb = p.value
          byService.set(svc, cur)
        }

        const next = new Map<string, ServiceSeries>()
        for (const [svc, vals] of byService) {
          const prev = seriesRef.current.get(svc)
          const cpu = prev ? prev.cpu.slice() : []
          const mem = prev ? prev.mem.slice() : []
          const memMb = prev ? prev.memMb.slice() : []
          if (typeof vals.cpu === 'number') { cpu.push(vals.cpu); if (cpu.length > window) cpu.shift() }
          if (typeof vals.mem === 'number') { mem.push(vals.mem); if (mem.length > window) mem.shift() }
          if (typeof vals.memMb === 'number') { memMb.push(vals.memMb); if (memMb.length > window) memMb.shift() }
          next.set(svc, {
            service: svc,
            label: displayLabel(svc),
            cpu,
            mem,
            memMb,
            latestCpu: cpu.length ? cpu[cpu.length - 1] : null,
            latestMem: mem.length ? mem[mem.length - 1] : null,
            latestMemMb: memMb.length ? memMb[memMb.length - 1] : null,
          })
        }
        seriesRef.current = next

        setState({
          series: [...next.values()].sort((a, b) => a.label.localeCompare(b.label)),
          source: res.source,
          loading: false,
          error: null,
        })
      } catch (err) {
        if (cancelled) return
        setState((s) => ({
          ...s,
          loading: false,
          error: err instanceof Error ? err.message : 'Failed to load live metrics',
        }))
      }
    }

    void poll()
    const timer = setInterval(poll, intervalMs)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [intervalMs, window, enabled])

  return state
}
