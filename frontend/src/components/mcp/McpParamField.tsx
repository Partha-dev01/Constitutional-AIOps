import type { FormField, FieldValue } from './schemaForm'

interface McpParamFieldProps {
  field: FormField
  value: FieldValue
  error?: string
  disabled?: boolean
  onChange: (value: FieldValue) => void
}

// Renders a single tool parameter input, chosen by its JSON-Schema type.
export function McpParamField({ field, value, error, disabled, onChange }: McpParamFieldProps) {
  const { name, schema, required } = field
  const type = schema.type ?? 'string'
  const inputBase =
    'w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 ' +
    (error ? 'border-red-500/60' : 'border-border')

  const renderInput = () => {
    // enum → select
    if (schema.enum && schema.enum.length > 0) {
      return (
        <select
          value={typeof value === 'string' ? value : ''}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          className={inputBase}
        >
          <option value="">Select…</option>
          {schema.enum.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      )
    }

    // boolean → toggle
    if (type === 'boolean') {
      const checked = value === true
      return (
        <label className="inline-flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={checked}
            disabled={disabled}
            onChange={(e) => onChange(e.target.checked)}
            className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
          />
          <span className="text-sm text-muted-foreground">{checked ? 'true' : 'false'}</span>
        </label>
      )
    }

    // integer / number → number input
    if (type === 'integer' || type === 'number') {
      return (
        <input
          type="number"
          value={typeof value === 'string' ? value : ''}
          disabled={disabled}
          min={schema.minimum}
          max={schema.maximum}
          step={type === 'integer' ? 1 : 'any'}
          onChange={(e) => onChange(e.target.value)}
          placeholder={schema.description}
          className={inputBase}
        />
      )
    }

    // array → comma-split text
    if (type === 'array') {
      return (
        <input
          type="text"
          value={typeof value === 'string' ? value : ''}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          placeholder={schema.description ? `${schema.description} (comma-separated)` : 'item1, item2, …'}
          className={inputBase}
        />
      )
    }

    // string (default) → text
    return (
      <input
        type="text"
        value={typeof value === 'string' ? value : ''}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        placeholder={schema.description}
        className={inputBase}
      />
    )
  }

  return (
    <div>
      <label className="block text-sm mb-1">
        {name}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {renderInput()}
      {schema.description && type !== 'array' && (
        <p className="text-xs text-muted-foreground mt-1">{schema.description}</p>
      )}
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  )
}
