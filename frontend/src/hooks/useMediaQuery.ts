import { useEffect, useState } from 'react'

/**
 * Tiny dependency-free media-query hook. Returns whether `query` currently
 * matches, and keeps the value in sync via a `matchMedia` change listener.
 * SSR-safe: defaults to `false` when `window`/`matchMedia` is unavailable so it
 * never throws during a non-browser render.
 */
export function useMediaQuery(query: string): boolean {
  const getMatch = (): boolean =>
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia(query).matches

  const [matches, setMatches] = useState<boolean>(getMatch)

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return
    }
    const mql = window.matchMedia(query)
    const onChange = (event: MediaQueryListEvent) => setMatches(event.matches)

    // Sync immediately in case the query changed between render and effect.
    setMatches(mql.matches)
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [query])

  return matches
}
