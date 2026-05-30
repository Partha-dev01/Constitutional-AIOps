// Pure helpers deriving a form from a JSON-Schema object parameter spec.
//
// Form values are held as primitive UI values (string | boolean) keyed by field
// name; `coerceForApi` converts them to the JSON types the backend expects.

import type { JsonSchemaProp, ToolParameterSchema } from './types'

export interface FormField {
  name: string
  schema: JsonSchemaProp
  required: boolean
}

// Field UI value: text inputs/selects/arrays hold strings; booleans hold a bool.
export type FieldValue = string | boolean
export type FormValues = Record<string, FieldValue>

export function getFields(schema: ToolParameterSchema | undefined): FormField[] {
  if (!schema || !schema.properties) return []
  const required = new Set(schema.required ?? [])
  return Object.entries(schema.properties).map(([name, propSchema]) => ({
    name,
    schema: propSchema,
    required: required.has(name),
  }))
}

export function initialValues(schema: ToolParameterSchema | undefined): FormValues {
  const values: FormValues = {}
  for (const { name, schema: propSchema } of getFields(schema)) {
    if (propSchema.type === 'boolean') {
      values[name] = typeof propSchema.default === 'boolean' ? propSchema.default : false
    } else if (propSchema.default !== undefined && propSchema.default !== null) {
      values[name] = String(propSchema.default)
    } else {
      values[name] = ''
    }
  }
  return values
}

// Convert a single UI value to the JSON type declared by the field schema.
function coerceField(schema: JsonSchemaProp, value: FieldValue): unknown {
  const type = schema.type ?? 'string'

  if (type === 'boolean') {
    return typeof value === 'boolean' ? value : value === 'true'
  }

  const str = typeof value === 'string' ? value.trim() : String(value)

  if (type === 'integer' || type === 'number') {
    if (str === '') return undefined
    const n = type === 'integer' ? parseInt(str, 10) : parseFloat(str)
    return Number.isNaN(n) ? undefined : n
  }

  if (type === 'array') {
    if (str === '') return undefined
    // Comma-split text → trimmed non-empty items.
    return str.split(',').map(s => s.trim()).filter(Boolean)
  }

  // string (default)
  return str === '' ? undefined : str
}

// Build the parameters object to POST. Omits empty/undefined optional fields.
export function coerceForApi(
  values: FormValues,
  schema: ToolParameterSchema | undefined,
): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const { name, schema: propSchema } of getFields(schema)) {
    const coerced = coerceField(propSchema, values[name])
    if (coerced !== undefined) {
      out[name] = coerced
    }
  }
  return out
}

// Returns a map of field-name → error string for invalid/missing-required fields.
export function validate(
  values: FormValues,
  schema: ToolParameterSchema | undefined,
): Record<string, string> {
  const errors: Record<string, string> = {}
  for (const { name, schema: propSchema, required } of getFields(schema)) {
    const raw = values[name]
    const str = typeof raw === 'string' ? raw.trim() : ''
    const type = propSchema.type ?? 'string'

    if (required && type !== 'boolean' && str === '') {
      errors[name] = 'Required'
      continue
    }

    if ((type === 'integer' || type === 'number') && str !== '') {
      const n = type === 'integer' ? Number(str) : parseFloat(str)
      if (Number.isNaN(n) || (type === 'integer' && !Number.isInteger(n))) {
        errors[name] = type === 'integer' ? 'Must be an integer' : 'Must be a number'
        continue
      }
      if (propSchema.minimum !== undefined && n < propSchema.minimum) {
        errors[name] = `Must be ≥ ${propSchema.minimum}`
        continue
      }
      if (propSchema.maximum !== undefined && n > propSchema.maximum) {
        errors[name] = `Must be ≤ ${propSchema.maximum}`
        continue
      }
    }
  }
  return errors
}
