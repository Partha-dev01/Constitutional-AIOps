/**
 * Pure table-export helpers (Track 2 QoL).
 *
 * Turns the rows a user is already looking at into a CSV or JSON download. The
 * serializers are dependency-free and side-effect-free at module scope so they
 * are unit testable in the Node test env; only downloadTextFile touches the DOM,
 * and only when actually called.
 */

export interface ExportColumn<T> {
  /** Stable key: the JSON field name and the CSV header fallback. */
  key: string
  /** Human header for the CSV column; defaults to key. */
  header?: string
  /** Extract the cell value for a row. The result is stringified for CSV. */
  value: (row: T) => string | number | boolean | null | undefined
}

export type ExportFormat = 'csv' | 'json'

type Cell = string | number | boolean | null | undefined

function asText(v: Cell): string {
  if (v === null || v === undefined) return ''
  return String(v)
}

/**
 * Neutralize spreadsheet formula injection. A field a spreadsheet would read as
 * a formula (leading = + - @ or a control char) is prefixed with a single quote
 * so Excel/Sheets treat it as literal text. The audit trail can contain
 * attacker-influenced strings (resource ids, descriptions), so this matters.
 */
function guardFormula(raw: string): string {
  if (raw && /^[=+\-@\t\r]/.test(raw)) {
    return `'${raw}`
  }
  return raw
}

/**
 * Escape one CSV field per RFC 4180: wrap in quotes when it contains a comma,
 * quote, CR or LF, doubling any inner quotes.
 */
function csvField(raw: string): string {
  const guarded = guardFormula(raw)
  if (/[",\r\n]/.test(guarded)) {
    return `"${guarded.replace(/"/g, '""')}"`
  }
  return guarded
}

/**
 * Serialize rows to RFC-4180 CSV with a header row. CRLF line breaks so Excel
 * and Sheets both parse it cleanly.
 */
export function toCSV<T>(rows: readonly T[], columns: readonly ExportColumn<T>[]): string {
  const header = columns.map((c) => csvField(c.header ?? c.key)).join(',')
  const body = rows.map((row) => columns.map((c) => csvField(asText(c.value(row)))).join(','))
  return [header, ...body].join('\r\n')
}

/**
 * Serialize rows to pretty JSON, projected through the same columns so the file
 * matches what the table shows (key -> value; undefined normalizes to null).
 */
export function toJSON<T>(rows: readonly T[], columns: readonly ExportColumn<T>[]): string {
  const projected = rows.map((row) => {
    const obj: Record<string, string | number | boolean | null> = {}
    for (const c of columns) {
      const v = c.value(row)
      obj[c.key] = v === undefined ? null : v
    }
    return obj
  })
  return JSON.stringify(projected, null, 2)
}

/** Serialize rows and describe the resulting file (content + mime + extension). */
export function serializeRows<T>(
  rows: readonly T[],
  columns: readonly ExportColumn<T>[],
  format: ExportFormat,
): { content: string; mime: string; ext: ExportFormat } {
  if (format === 'csv') {
    return { content: toCSV(rows, columns), mime: 'text/csv;charset=utf-8', ext: 'csv' }
  }
  return { content: toJSON(rows, columns), mime: 'application/json;charset=utf-8', ext: 'json' }
}

/**
 * Trigger a client-side download of text content. Browser-only: a guard makes it
 * a safe no-op anywhere without a DOM (SSR, the Node test env).
 */
export function downloadTextFile(filename: string, content: string, mime: string): void {
  if (typeof document === 'undefined' || typeof URL === 'undefined' || !URL.createObjectURL) {
    return
  }
  const url = URL.createObjectURL(new Blob([content], { type: mime }))
  try {
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.rel = 'noopener'
    document.body.appendChild(a)
    a.click()
    a.remove()
  } finally {
    URL.revokeObjectURL(url)
  }
}

/** Serialize `rows` and start a dated download in one call. */
export function exportRows<T>(
  rows: readonly T[],
  columns: readonly ExportColumn<T>[],
  format: ExportFormat,
  filenameBase: string,
): void {
  const { content, mime, ext } = serializeRows(rows, columns, format)
  const stamp = new Date().toISOString().slice(0, 10)
  downloadTextFile(`${filenameBase}_${stamp}.${ext}`, content, mime)
}
