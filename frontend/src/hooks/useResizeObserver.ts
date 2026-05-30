import { useEffect, useRef, useState } from 'react'

export interface Size { width: number; height: number }

export function useResizeObserver<T extends HTMLElement>(fallback: Size) {
  const ref = useRef<T>(null)
  const [size, setSize] = useState<Size>(fallback)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        const w = entry.contentRect.width, h = entry.contentRect.height
        if (w > 0 && h > 0) setSize({ width: w, height: h })
      }
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return { ref, size }
}
