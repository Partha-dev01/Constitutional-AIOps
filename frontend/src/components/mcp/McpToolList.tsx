import { Loader2, SearchX, Wrench } from 'lucide-react'
import type { McpToolInfo } from './types'
import { McpToolCard } from './McpToolCard'

interface McpToolListProps {
  tools: McpToolInfo[]
  loading: boolean
  selectedTool: McpToolInfo | null
  onSelect: (tool: McpToolInfo) => void
  /**
   * Total before search/category filtering — lets the empty state distinguish
   * "nothing matches your filters" from "no tools configured at all".
   */
  totalCount?: number
}

export function McpToolList({ tools, loading, selectedTool, onSelect, totalCount }: McpToolListProps) {
  const filteredOut = !loading && tools.length === 0 && (totalCount ?? 0) > 0

  return (
    <div className="flex h-full min-h-0 flex-col rounded-xl border border-border bg-card">
      <div className="flex shrink-0 items-center justify-between border-b border-border p-3.5">
        <h3 className="text-sm font-semibold">Available Tools</h3>
        {!loading && tools.length > 0 && (
          <span className="rounded-full border border-border bg-muted/40 px-2 py-0.5 text-[11px] text-muted-foreground">
            {tools.length} tool{tools.length === 1 ? '' : 's'}
          </span>
        )}
      </div>
      <div className="min-h-0 flex-1 space-y-2 overflow-y-auto p-3">
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
        ) : filteredOut ? (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <SearchX className="mb-2 h-8 w-8 opacity-50" />
            <p className="text-sm">No tools match your filters</p>
            <p className="mt-1 text-xs">Try a different search or category</p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <Wrench className="mb-2 h-8 w-8 opacity-50" />
            <p className="text-sm">No tools available</p>
            <p className="mt-1 text-xs">Configure MCP server in backend</p>
          </div>
        )}
      </div>
    </div>
  )
}
