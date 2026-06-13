import { useCallback, useEffect, useMemo, useRef } from 'react'
import { History, Radio } from 'lucide-react'

interface TimeScrubberProps {
  /** Global per-bucket episode totals, oldest → newest. */
  buckets: number[]
  /** null = Live (full window). */
  activeBucket: number | null
  onChange: (bucket: number | null) => void
  generatedAt: string
  windowHours: number
  bucketMinutes: number
}

/**
 * Bottom time strip: a per-bucket histogram with a draggable handle. Pointer
 * drags are rAF-throttled; ArrowLeft/ArrowRight step buckets; "Live" resets
 * to the full window. Emits only `activeBucket` — all visual binding upstream
 * is derived (zero refetch, zero layout recompute).
 */
export function TimeScrubber({
  buckets,
  activeBucket,
  onChange,
  generatedAt,
  windowHours,
  bucketMinutes,
}: TimeScrubberProps) {
  const trackRef = useRef<HTMLDivElement>(null)
  const draggingRef = useRef(false)
  const rafRef = useRef<number | null>(null)
  const pendingXRef = useRef(0)

  const count = buckets.length
  const maxBucket = useMemo(() => buckets.reduce((m, v) => Math.max(m, v), 0), [buckets])
  const cumulative = useMemo(() => {
    if (activeBucket === null) return buckets.reduce((a, b) => a + b, 0)
    return buckets.slice(0, activeBucket + 1).reduce((a, b) => a + b, 0)
  }, [buckets, activeBucket])

  const bucketEndTime = useCallback(
    (idx: number): Date => {
      const end = new Date(generatedAt).getTime() - windowHours * 3_600_000
      return new Date(end + (idx + 1) * bucketMinutes * 60_000)
    },
    [generatedAt, windowHours, bucketMinutes],
  )

  const bucketFromClientX = useCallback(
    (clientX: number): number => {
      const el = trackRef.current
      if (!el || count === 0) return 0
      const rect = el.getBoundingClientRect()
      if (rect.width <= 0) return 0
      const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width))
      return Math.min(count - 1, Math.floor(ratio * count))
    },
    [count],
  )

  const flushDrag = useCallback(() => {
    rafRef.current = null
    onChange(bucketFromClientX(pendingXRef.current))
  }, [onChange, bucketFromClientX])

  useEffect(() => {
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    draggingRef.current = true
    e.currentTarget.setPointerCapture(e.pointerId)
    onChange(bucketFromClientX(e.clientX))
  }

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!draggingRef.current) return
    pendingXRef.current = e.clientX
    if (rafRef.current === null) {
      rafRef.current = requestAnimationFrame(flushDrag)
    }
  }

  const handlePointerUp = () => {
    draggingRef.current = false
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault()
      onChange(activeBucket === null ? count - 1 : Math.max(0, activeBucket - 1))
    } else if (e.key === 'ArrowRight') {
      e.preventDefault()
      if (activeBucket !== null) {
        onChange(activeBucket >= count - 1 ? null : activeBucket + 1)
      }
    }
  }

  const isLive = activeBucket === null
  const effectiveActive = isLive ? count - 1 : activeBucket

  return (
    <div className="mt-2 rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2">
      <div className="flex items-center gap-3">
        <div
          ref={trackRef}
          className="schema-scrubber relative flex h-10 flex-1 cursor-ew-resize items-end gap-px"
          data-testid="time-scrubber"
          role="slider"
          aria-label="Episode time scrubber"
          aria-valuemin={0}
          aria-valuemax={Math.max(0, count - 1)}
          aria-valuenow={effectiveActive}
          aria-valuetext={
            isLive ? 'Live, full window' : `Through ${bucketEndTime(effectiveActive).toLocaleString()}`
          }
          tabIndex={0}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
          onKeyDown={handleKeyDown}
        >
          {buckets.map((value, idx) => {
            const heightPct = maxBucket > 0 ? (value / maxBucket) * 100 : 0
            const included = idx <= effectiveActive
            return (
              <div
                key={idx}
                className={`schema-scrubber-bar min-w-0 flex-1 rounded-t-sm ${
                  included ? 'bg-blue-500/80' : 'bg-slate-700/50'
                }`}
                style={{ height: `${Math.max(6, heightPct)}%`, opacity: value > 0 ? 1 : 0.45 }}
              />
            )
          })}
          {/* Handle: marks the end boundary of the active bucket. */}
          <div
            data-testid="scrubber-handle"
            className="pointer-events-none absolute inset-y-0 w-0.5 rounded bg-blue-300"
            style={{ left: `${((effectiveActive + 1) / Math.max(1, count)) * 100}%` }}
          />
        </div>

        <div className="flex shrink-0 flex-col items-end gap-1">
          <button
            type="button"
            onClick={() => onChange(null)}
            className={`flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs transition-colors ${
              isLive
                ? 'border-green-500/50 bg-green-500/10 text-green-400'
                : 'border-slate-700 bg-slate-800/80 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Radio className="h-3 w-3" />
            Live
          </button>
          <span className="flex items-center gap-1 whitespace-nowrap text-[10px] text-slate-500">
            <History className="h-3 w-3" />
            {isLive
              ? `${cumulative} episodes · full ${windowHours}h window`
              : `${cumulative} episodes through ${bucketEndTime(effectiveActive).toLocaleString([], {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}`}
          </span>
        </div>
      </div>
    </div>
  )
}
