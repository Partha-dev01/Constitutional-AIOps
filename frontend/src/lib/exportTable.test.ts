import { describe, it, expect } from 'vitest'
import { toCSV, toJSON, serializeRows, type ExportColumn } from './exportTable'

interface Row {
  name: string
  count: number
  note?: string | null
}

const columns: ExportColumn<Row>[] = [
  { key: 'name', header: 'Name', value: (r) => r.name },
  { key: 'count', header: 'Count', value: (r) => r.count },
  { key: 'note', header: 'Note', value: (r) => r.note },
]

describe('toCSV', () => {
  it('writes a header row and CRLF-separated rows', () => {
    const csv = toCSV([{ name: 'a', count: 1 }], columns)
    expect(csv).toBe('Name,Count,Note\r\na,1,')
  })

  it('quotes fields containing commas, quotes or newlines and doubles inner quotes', () => {
    const csv = toCSV(
      [{ name: 'a,b', count: 2, note: 'he said "hi"\nbye' }],
      columns,
    )
    expect(csv).toBe('Name,Count,Note\r\n"a,b",2,"he said ""hi""\nbye"')
  })

  it('renders null and undefined as empty cells', () => {
    const csv = toCSV([{ name: 'x', count: 0, note: null }], columns)
    expect(csv).toBe('Name,Count,Note\r\nx,0,')
  })

  it('neutralizes spreadsheet formula injection with a leading quote', () => {
    const csv = toCSV([{ name: '=SUM(A1:A2)', count: 1 }], columns)
    // The =... field is prefixed with ' so a spreadsheet treats it as text.
    expect(csv).toContain("'=SUM(A1:A2)")
  })

  it('handles an empty row set (header only)', () => {
    expect(toCSV([], columns)).toBe('Name,Count,Note')
  })
})

describe('toJSON', () => {
  it('projects rows through the columns and normalizes undefined to null', () => {
    const json = toJSON([{ name: 'a', count: 1 }], columns)
    expect(JSON.parse(json)).toEqual([{ name: 'a', count: 1, note: null }])
  })
})

describe('serializeRows', () => {
  it('reports csv content, mime and extension', () => {
    const out = serializeRows([{ name: 'a', count: 1 }], columns, 'csv')
    expect(out.ext).toBe('csv')
    expect(out.mime).toContain('text/csv')
    expect(out.content.startsWith('Name,Count,Note')).toBe(true)
  })

  it('reports json content, mime and extension', () => {
    const out = serializeRows([{ name: 'a', count: 1 }], columns, 'json')
    expect(out.ext).toBe('json')
    expect(out.mime).toContain('application/json')
    expect(JSON.parse(out.content)).toHaveLength(1)
  })
})
