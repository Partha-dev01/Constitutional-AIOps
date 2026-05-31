import { Loader2, Wrench } from 'lucide-react'
import type { McpToolInfo } from './types'
import { McpToolCard } from './McpToolCard'

interface McpToolListProps {
  tools: McpToolInfo[]
  loading: boolean
  selectedTool: McpToolInfo | null
  onSelect: (tool: McpToolInfo) => void
}

export function McpToolList({ tools, loading, selectedTool, onSelect }: McpToolListProps) {
  return (
    <div className="bg-card rounded-lg border border-border">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <h3 className="font-semibold">Available Tools</h3>
        {!loading && tools.length > 0 && (
          <span className="text-xs text-muted-foreground">{tools.length} tools</span>
        )}
      </div>
      <div className="divide-y divide-border max-h-[480px] overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : tools.length > 0 ? (
          tools.map((tool) => (
            <McpToolCard
              key={tool.name}
              tool={tool}
              selected={selectedTool?.name === tool.name}
              onSelect={onSelect}
            />
          ))
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <Wrench className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">No tools available</p>
            <p className="text-xs mt-1">Configure MCP server in backend</p>
          </div>
        )}
      </div>
    </div>
  )
}
