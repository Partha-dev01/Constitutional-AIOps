import { useEffect, useRef, useState } from 'react'

export interface Size { width: number; height: number }

export function useResizeObserver<T extends HTMLElement>(fallback: Size) {
  const ref = useRef<T>(null)
  const [size, setSize] = useState<Size>(fallback)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    // FIX: Measure immediately on mount so the first ForceGraph paint gets the
    // real container width instead of the fallback. ResizeObserver callbacks are
    // async (next microtask frame), so without this the initial render uses the
    // fallback 800px width and nodes lay out in a smaller virtual space.
    const rect = el.getBoundingClientRect()
    if (rect.width > 0 && rect.height > 0) {
      setSize({ width: rect.width, height: rect.height })
    }

    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        const w = entry.contentRect.width
        const h = entry.contentRect.height
        if (w > 0 && h > 0) setSize({ width: w, height: h })
      }
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  return { ref, size }
}
