import { useMemo } from 'react'

/**
 * Renders a string as pretty-printed JSON when it parses as valid JSON,
 * otherwise falls back to the raw trimmed text. Never throws, never blank.
 *
 * Backend often truncates output at 1000 chars (producing invalid JSON) and
 * error rows are plain strings, so parsing is always attempted safely.
 */
export function JsonView({ raw }: { raw: string }) {
  const pretty = useMemo<string | null>(() => {
    try {
      return JSON.stringify(JSON.parse(raw.trim()), null, 2)
    } catch {
      return null
    }
  }, [raw])

  return (
    <pre className="text-xs font-mono whitespace-pre-wrap wrap-break-word overflow-x-auto max-h-[400px] overflow-y-auto p-3 bg-muted/50 rounded-sm">
      {pretty ?? raw.trim()}
    </pre>
  )
}
