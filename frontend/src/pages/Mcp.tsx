import { useState, useEffect, useMemo } from 'react'
import { Wrench, RefreshCw, Loader2, Search } from 'lucide-react'
import { McpToolList } from '../components/mcp/McpToolList'
import { McpExecutePanel } from '../components/mcp/McpExecutePanel'
import { isToolDisabled } from '../components/mcp/types'
import type { McpToolInfo } from '../components/mcp/types'

export function Mcp() {
  const [tools, setTools] = useState<McpToolInfo[]>([])
  const [toolsLoading, setToolsLoading] = useState(false)
  const [selectedTool, setSelectedTool] = useState<McpToolInfo | null>(null)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')

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

  // Category chips are data-driven from the listing so a new backend category
  // shows up here without a frontend change.
  const categories = useMemo(() => {
    const cats = new Set<string>()
    for (const tool of tools) {
      if (tool.category) cats.add(tool.category)
    }
    return ['all', ...Array.from(cats).sort()]
  }, [tools])

  const visibleTools = useMemo(() => {
    const q = search.trim().toLowerCase()
    return tools.filter((tool) => {
      if (category !== 'all' && tool.category !== category) return false
      if (q && !tool.name.toLowerCase().includes(q) && !tool.description.toLowerCase().includes(q)) {
        return false
      }
      return true
    })
  }, [tools, search, category])

  const gatedCount = useMemo(() => tools.filter(isToolDisabled).length, [tools])

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      {/* Header */}
      <div className="flex shrink-0 flex-wrap items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-primary/30 bg-primary/10">
          <Wrench className="h-5 w-5 text-primary" />
        </div>
        <div className="min-w-0">
          <h1 className="text-xl font-bold leading-tight">MCP Tools</h1>
          <p className="text-xs text-muted-foreground">
            The platform's tool surface — read-only queries run directly; action tools pass
            constitutional validation first.
          </p>
        </div>
        <div className="ml-auto flex shrink-0 flex-wrap items-center gap-2">
          {!toolsLoading && tools.length > 0 && (
            <>
              <span className="rounded-full border border-border bg-muted/40 px-2.5 py-0.5 text-xs text-muted-foreground">
                {tools.length} tools
              </span>
              {gatedCount > 0 && (
                <span
                  className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 text-xs text-amber-400"
                  title="Action tools stay locked until AIOPS_ENABLE_ACTION_TOOLS is set on the backend"
                >
                  {gatedCount} gated
                </span>
              )}
            </>
          )}
          <button
            onClick={fetchTools}
            disabled={toolsLoading}
            className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-1.5 text-sm transition-colors hover:bg-muted disabled:opacity-50"
          >
            {toolsLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Refresh
          </button>
        </div>
      </div>

      {/* Search + category filter strip */}
      <div className="flex shrink-0 flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tools…"
            aria-label="Search tools"
            className="w-56 max-w-full rounded-lg border border-border bg-card py-1.5 pl-8 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/50"
          />
        </div>
        {categories.length > 1 && (
          <div
            className="flex shrink-0 items-center rounded-md bg-muted p-0.5 text-xs"
            role="group"
            aria-label="Filter by category"
          >
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategory(cat)}
                aria-pressed={category === cat}
                className={`rounded px-2 py-0.5 font-medium capitalize transition-colors ${
                  category === cat
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <McpToolList
          tools={visibleTools}
          loading={toolsLoading}
          selectedTool={selectedTool}
          onSelect={setSelectedTool}
          totalCount={tools.length}
        />
        <McpExecutePanel tool={selectedTool} />
      </div>
    </div>
  )
}
