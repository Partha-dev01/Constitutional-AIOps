import { useEffect, useMemo, useState } from 'react'
import { Loader2, Play, Wrench, History, AlertCircle } from 'lucide-react'
import type { McpToolInfo, McpToolCallResult, McpExecutionRecord } from './types'
import { isToolDisabled } from './types'
import {
  getFields,
  initialValues,
  coerceForApi,
  validate,
  type FormValues,
  type FieldValue,
} from './schemaForm'
import { McpParamField } from './McpParamField'
import { McpResultView } from './McpResultView'

interface McpExecutePanelProps {
  tool: McpToolInfo | null
}

export function McpExecutePanel({ tool }: McpExecutePanelProps) {
  const fields = useMemo(() => getFields(tool?.parameters), [tool])
  const [values, setValues] = useState<FormValues>(() => initialValues(tool?.parameters))
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [executing, setExecuting] = useState(false)
  const [result, setResult] = useState<McpToolCallResult | null>(null)
  const [history, setHistory] = useState<McpExecutionRecord[]>([])

  const disabled = tool ? isToolDisabled(tool.name) : false

  // Reset the form whenever the selected tool changes.
  useEffect(() => {
    setValues(initialValues(tool?.parameters))
    setErrors({})
    setResult(null)
  }, [tool])

  const setField = (name: string, value: FieldValue) => {
    setValues(prev => ({ ...prev, [name]: value }))
  }

  const execute = async () => {
    if (!tool || disabled) return

    const validationErrors = validate(values, tool.parameters)
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    const parameters = coerceForApi(values, tool.parameters)
    setExecuting(true)
    setResult(null)
    try {
      const response = await fetch('/api/v1/tools/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool_name: tool.name, parameters }),
      })
      const data: McpToolCallResult = await response.json()
      setResult(data)
      setHistory(prev => [
        {
          id: `${tool.name}-${Date.now()}`,
          toolName: tool.name,
          parameters,
          result: data,
          at: new Date(),
        },
        ...prev,
      ].slice(0, 20))
    } catch (err) {
      const failure: McpToolCallResult = {
        success: false,
        data: null,
        error: err instanceof Error ? err.message : 'Unknown error',
      }
      setResult(failure)
    } finally {
      setExecuting(false)
    }
  }

  return (
    <div className="bg-card rounded-lg border border-border">
      <div className="p-4 border-b border-border">
        <h3 className="font-semibold">
          {tool ? `Execute: ${tool.name}` : 'Tool Execution'}
        </h3>
      </div>
      <div className="p-4">
        {!tool ? (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <Wrench className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">Select a tool to execute</p>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">{tool.description}</p>

            {disabled && (
              <div className="flex items-start gap-2 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                <AlertCircle className="h-4 w-4 text-yellow-500 mt-0.5 shrink-0" />
                <p className="text-sm text-yellow-600">
                  This action tool runs destructive operations and requires approval.
                  Execution from the UI is disabled (coming soon).
                </p>
              </div>
            )}

            {fields.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-sm font-medium">Parameters</h4>
                {fields.map((field) => (
                  <McpParamField
                    key={field.name}
                    field={field}
                    value={values[field.name]}
                    error={errors[field.name]}
                    disabled={disabled}
                    onChange={(v) => setField(field.name, v)}
                  />
                ))}
              </div>
            )}

            <button
              type="button"
              onClick={execute}
              disabled={executing || disabled}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {executing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              Execute Tool
            </button>

            {result && (
              <div className="mt-2">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium">Result</h4>
                  {typeof result.execution_time_ms === 'number' && (
                    <span className="text-xs text-muted-foreground">
                      {result.execution_time_ms.toFixed(0)}ms
                    </span>
                  )}
                </div>
                <McpResultView toolName={tool.name} result={result} />
              </div>
            )}

            {history.length > 0 && (
              <div className="mt-4 pt-4 border-t border-border">
                <h4 className="text-sm font-medium flex items-center gap-1.5 mb-2">
                  <History className="h-4 w-4" />
                  Execution History
                </h4>
                <div className="space-y-1.5 max-h-[200px] overflow-y-auto">
                  {history.map((rec) => (
                    <div
                      key={rec.id}
                      className="flex items-center justify-between gap-2 px-2.5 py-1.5 rounded bg-muted/40 text-xs"
                    >
                      <span className="font-mono truncate">{rec.toolName}</span>
                      <span className="text-muted-foreground shrink-0">
                        {rec.at.toLocaleTimeString()}
                      </span>
                      <span className={rec.result.success ? 'text-green-500 shrink-0' : 'text-red-500 shrink-0'}>
                        {rec.result.success ? 'ok' : 'error'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
