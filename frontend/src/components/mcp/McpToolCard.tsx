import { Lock, ShieldCheck } from 'lucide-react'
import type { McpToolInfo } from './types'
import { disabledReason, isActionTool, isToolDisabled } from './types'

interface McpToolCardProps {
  tool: McpToolInfo
  selected: boolean
  onSelect: (tool: McpToolInfo) => void
}

// Category → colour mapping.
function categoryBadge(cat: string | undefined): string {
  switch (cat) {
    case 'query':    return 'bg-blue-500/10 text-blue-500'
    case 'analysis': return 'bg-purple-500/10 text-purple-500'
    case 'action':   return 'bg-orange-500/10 text-orange-500'
    default:         return 'bg-muted text-muted-foreground'
  }
}

// A single tool row in the tool list. Disabled state is data-driven from the
// backend listing (`enabled`/`gated_by`), not hardcoded per tool name.
export function McpToolCard({ tool, selected, onSelect }: McpToolCardProps) {
  const disabled = isToolDisabled(tool)
  const action = isActionTool(tool)
  const risk = tool.risk_level ?? 'low'

  return (
    <button
      type="button"
      disabled={disabled}
      title={disabled ? disabledReason(tool) : undefined}
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
        <div className="flex items-center gap-1.5">
          {tool.category && (
            <span className={`px-2 py-0.5 rounded text-xs ${categoryBadge(tool.category)}`}>
              {tool.category}
            </span>
          )}
          <span className={`px-2 py-0.5 rounded text-xs ${
            risk === 'low' ? 'bg-green-500/10 text-green-500' :
            risk === 'medium' ? 'bg-yellow-500/10 text-yellow-500' :
            'bg-red-500/10 text-red-500'
          }`}>
            {risk} risk
          </span>
        </div>
      </div>
      <p className="text-sm text-muted-foreground">{tool.description}</p>
      {disabled && (
        <p className="text-xs text-yellow-500 mt-1.5">
          Gated off — set {tool.gated_by ?? 'AIOPS_ENABLE_ACTION_TOOLS'}=true on the backend to enable
        </p>
      )}
      {!disabled && action && (
        <p className="text-xs text-orange-500 mt-1.5 flex items-center gap-1">
          <ShieldCheck className="h-3 w-3" />
          Constitutionally gated — every call is validated before execution
        </p>
      )}
    </button>
  )
}
