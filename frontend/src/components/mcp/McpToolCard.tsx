import { Activity, Lock, Search, ShieldCheck, Wrench, Zap } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { McpToolInfo } from './types'
import { disabledReason, isActionTool, isToolDisabled } from './types'

interface McpToolCardProps {
  tool: McpToolInfo
  selected: boolean
  onSelect: (tool: McpToolInfo) => void
}

// Category → icon + tint. Unknown categories fall back to the neutral wrench.
const CATEGORY_ICON: Record<string, LucideIcon> = {
  query: Search,
  analysis: Activity,
  action: Zap,
}

const CATEGORY_TINT: Record<string, string> = {
  query: 'bg-blue-500/10 text-blue-400',
  analysis: 'bg-purple-500/10 text-purple-400',
  action: 'bg-orange-500/10 text-orange-400',
}

// Category → chip colour mapping.
function categoryBadge(cat: string | undefined): string {
  switch (cat) {
    case 'query':    return 'bg-blue-500/10 text-blue-500'
    case 'analysis': return 'bg-purple-500/10 text-purple-500'
    case 'action':   return 'bg-orange-500/10 text-orange-500'
    default:         return 'bg-muted text-muted-foreground'
  }
}

// A single tool card in the tool list. Disabled state is data-driven from the
// backend listing (`enabled`/`gated_by`), not hardcoded per tool name.
export function McpToolCard({ tool, selected, onSelect }: McpToolCardProps) {
  const disabled = isToolDisabled(tool)
  const action = isActionTool(tool)
  const risk = tool.risk_level ?? 'low'
  const Icon = CATEGORY_ICON[tool.category ?? ''] ?? Wrench
  const tint = CATEGORY_TINT[tool.category ?? ''] ?? 'bg-muted text-muted-foreground'

  return (
    <button
      type="button"
      disabled={disabled}
      title={disabled ? disabledReason(tool) : undefined}
      onClick={() => !disabled && onSelect(tool)}
      aria-pressed={selected}
      className={`w-full rounded-lg border p-3 text-left transition-colors ${
        disabled
          ? 'cursor-not-allowed border-border/50 bg-muted/10 opacity-60'
          : selected
            ? 'border-primary/60 bg-primary/[0.08]'
            : 'cursor-pointer border-border/70 bg-muted/20 hover:border-slate-600/70 hover:bg-muted/40'
      }`}
    >
      <div className="flex items-start gap-2.5">
        <span
          className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md ${
            disabled ? 'bg-muted text-muted-foreground' : tint
          }`}
        >
          {disabled ? <Lock className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <h4 className="truncate font-mono text-sm font-medium">{tool.name}</h4>
            <span className="ml-auto flex shrink-0 items-center gap-1.5">
              {tool.category && (
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${categoryBadge(tool.category)}`}>
                  {tool.category}
                </span>
              )}
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                  risk === 'low' ? 'bg-green-500/10 text-green-500' :
                  risk === 'medium' ? 'bg-yellow-500/10 text-yellow-500' :
                  'bg-red-500/10 text-red-500'
                }`}
              >
                {risk} risk
              </span>
            </span>
          </div>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{tool.description}</p>
          {disabled && (
            <p className="mt-1.5 text-xs text-yellow-500">
              Gated off — set {tool.gated_by ?? 'AIOPS_ENABLE_ACTION_TOOLS'}=true on the backend to enable
            </p>
          )}
          {!disabled && action && (
            <p className="mt-1.5 flex items-center gap-1 text-xs text-orange-500">
              <ShieldCheck className="h-3 w-3" />
              Constitutionally gated — every call is validated before execution
            </p>
          )}
        </div>
      </div>
    </button>
  )
}
