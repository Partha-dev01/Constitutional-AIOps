import { useState, useEffect } from 'react'
import { Wrench, RefreshCw, Loader2 } from 'lucide-react'
import { McpToolList } from '../components/mcp/McpToolList'
import { McpExecutePanel } from '../components/mcp/McpExecutePanel'
import type { McpToolInfo } from '../components/mcp/types'

export function Mcp() {
  const [tools, setTools] = useState<McpToolInfo[]>([])
  const [toolsLoading, setToolsLoading] = useState(false)
  const [selectedTool, setSelectedTool] = useState<McpToolInfo | null>(null)

  const fetchTools = async () => {
    setToolsLoading(true)
    try {
      const response = await fetch('/api/v1/tools/')
      if (response.ok) {
        const data = await response.json()
        setTools(data.tools || [])
      } else {
        setTools([])
      }
    } catch (err) {
      console.error('Failed to fetch tools:', err)
      setTools([])
    } finally {
      setToolsLoading(false)
    }
  }

  useEffect(() => {
    fetchTools()
  }, [])

  return (
    <div className="flex h-full min-h-0 flex-col gap-5">
      {/* Header */}
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Wrench className="h-6 w-6" />
            MCP Tools
          </h1>
          <p className="text-muted-foreground">
            Configure and execute infrastructure tools
          </p>
        </div>
        <button
          onClick={fetchTools}
          disabled={toolsLoading}
          className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg text-sm hover:bg-muted/80 disabled:opacity-50"
        >
          {toolsLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Refresh
        </button>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-2">
        <McpToolList
          tools={tools}
          loading={toolsLoading}
          selectedTool={selectedTool}
          onSelect={setSelectedTool}
        />
        <McpExecutePanel tool={selectedTool} />
      </div>
    </div>
  )
}
