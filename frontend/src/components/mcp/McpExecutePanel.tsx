import { useEffect, useMemo, useState } from 'react'
import { Loader2, Play, Wrench, History, AlertCircle, AlertTriangle, ShieldCheck, X } from 'lucide-react'
import type { McpToolInfo, McpToolCallResult, McpExecutionRecord } from './types'
import { disabledReason, isActionTool, isToolDisabled } from './types'
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
  const [confirming, setConfirming] = useState(false)
  const [result, setResult] = useState<McpToolCallResult | null>(null)
  const [history, setHistory] = useState<McpExecutionRecord[]>([])

  const disabled = tool ? isToolDisabled(tool) : false
  const action = tool ? isActionTool(tool) : false

  // Reset the form whenever the selected tool changes.
  useEffect(() => {
    setValues(initialValues(tool?.parameters))
    setErrors({})
    setResult(null)
    setConfirming(false)
  }, [tool])

  const setField = (name: string, value: FieldValue) => {
    setValues(prev => ({ ...prev, [name]: value }))
    setConfirming(false)
  }

  // Actually POST the call (after confirmation for action tools).
  const runExecute = async () => {
    if (!tool || disabled) return
    const parameters = coerceForApi(values, tool.parameters)
    setConfirming(false)
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

  // Entry point from the Execute button: validates the form, then either runs
  // directly (read-only tools) or shows the destructive-action confirmation.
  const requestExecute = async () => {
    if (!tool || disabled) return

    const validationErrors = validate(values, tool.parameters)
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) {
      setConfirming(false)
      return
    }

    if (action && !confirming) {
      setConfirming(true)
      return
    }
    await runExecute()
  }

  const confirmParams = tool ? coerceForApi(values, tool.parameters) : {}

  return (
    <div className="flex h-full min-h-0 flex-col rounded-xl border border-border bg-card">
      <div className="flex shrink-0 flex-wrap items-center gap-2 border-b border-border p-3.5">
        <h3 className="text-sm font-semibold">
          {tool ? `Execute: ${tool.name}` : 'Tool Execution'}
        </h3>
        {tool && (
          <span className="ml-auto flex shrink-0 items-center gap-1.5">
            {tool.category && (
              <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium capitalize text-muted-foreground">
                {tool.category}
              </span>
            )}
            {action && !disabled && (
              <span className="rounded-full bg-orange-500/10 px-2 py-0.5 text-[10px] font-medium text-orange-500">
                gated
              </span>
            )}
          </span>
        )}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {!tool ? (
          <div className="flex h-full min-h-[200px] flex-col items-center justify-center rounded-lg border border-dashed border-border/70 text-muted-foreground">
            <span className="mb-2.5 flex h-10 w-10 items-center justify-center rounded-xl bg-muted/50">
              <Wrench className="h-5 w-5 opacity-60" />
            </span>
            <p className="text-sm font-medium">Select a tool to execute</p>
            <p className="mt-1 max-w-[240px] text-center text-xs">
              Pick a tool from the list — its parameters and results appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">{tool.description}</p>

            {disabled && (
              <div className="flex items-start gap-2 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                <AlertCircle className="h-4 w-4 text-yellow-500 mt-0.5 shrink-0" />
                <p className="text-sm text-yellow-600">{disabledReason(tool)}</p>
              </div>
            )}

            {!disabled && action && (
              <div className="flex items-start gap-2 p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
                <ShieldCheck className="h-4 w-4 text-orange-500 mt-0.5 shrink-0" />
                <p className="text-sm text-orange-600">
                  Action tool: the backend validates every call against the constitutional
                  principles first. Verdicts requiring human approval are surfaced here and
                  are not executed.
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

            {confirming ? (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg space-y-3">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                  <div className="text-sm text-red-600">
                    <p className="font-medium">
                      Confirm {tool.name === 'restart_service' ? 'container restart' : 'service scaling'}
                    </p>
                    <p className="mt-1">
                      This runs a real Docker operation on the host. It is only executed if the
                      constitutional validator authorizes it automatically.
                    </p>
                  </div>
                </div>
                <div className="rounded bg-muted/40 px-2.5 py-1.5 text-xs font-mono break-all">
                  {tool.name}({Object.entries(confirmParams)
                    .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
                    .join(', ')})
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={runExecute}
                    disabled={executing}
                    className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {executing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                    Confirm &amp; Execute
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirming(false)}
                    className="flex items-center gap-2 px-4 py-2 bg-muted rounded-lg text-sm hover:bg-muted/80"
                  >
                    <X className="h-4 w-4" />
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={requestExecute}
                disabled={executing || disabled}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {executing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                Execute Tool
              </button>
            )}

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
                      <span className={
                        rec.result.success ? 'text-green-500 shrink-0' :
                        rec.result.error_code === 'approval_required' ? 'text-amber-500 shrink-0' :
                        'text-red-500 shrink-0'
                      }>
                        {rec.result.success ? 'ok' :
                          rec.result.error_code === 'approval_required' ? 'approval' : 'error'}
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
