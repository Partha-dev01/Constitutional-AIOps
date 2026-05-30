import { Lock } from 'lucide-react'
import type { McpToolInfo } from './types'
import { isToolDisabled } from './types'

interface McpToolCardProps {
  tool: McpToolInfo
  selected: boolean
  onSelect: (tool: McpToolInfo) => void
}

// A single tool row in the tool list. Disabled (action) tools are not selectable.
export function McpToolCard({ tool, selected, onSelect }: McpToolCardProps) {
  const disabled = isToolDisabled(tool.name)
  const risk = tool.risk_level ?? 'low'

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => !disabled && onSelect(tool)}
      className={`w-full text-left p-4 transition-colors ${
        disabled
          ? 'opacity-60 cursor-not-allowed'
          : 'cursor-pointer hover:bg-muted/50'
      } ${selected ? 'bg-muted/50' : ''}`}
    >
      <div className="flex items-center justify-between mb-1">
        <h4 className="font-medium flex items-center gap-1.5">
          {disabled && <Lock className="h-3.5 w-3.5 text-muted-foreground" />}
          {tool.name}
        </h4>
        <span className={`px-2 py-0.5 rounded text-xs ${
          risk === 'low' ? 'bg-green-500/10 text-green-500' :
          risk === 'medium' ? 'bg-yellow-500/10 text-yellow-500' :
          'bg-red-500/10 text-red-500'
        }`}>
          {risk} risk
        </span>
      </div>
      <p className="text-sm text-muted-foreground">{tool.description}</p>
      {disabled && (
        <p className="text-xs text-yellow-500 mt-1.5">Requires approval — coming soon</p>
      )}
    </button>
  )
}
