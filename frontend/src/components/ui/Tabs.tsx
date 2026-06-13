/**
 * Accessible Tabs primitive — WAI-ARIA tablist pattern.
 *
 * Usage:
 *   <Tabs value={activeTab} onChange={setActiveTab} tabs={[
 *     { id: 'overview', label: 'Overview' },
 *     { id: 'details',  label: 'Details'  },
 *   ]}>
 *     <TabPanel id="overview"><OverviewContent /></TabPanel>
 *     <TabPanel id="details"><DetailsContent /></TabPanel>
 *   </Tabs>
 */
import React, { useRef, KeyboardEvent } from 'react'
import { cn } from '../../lib/utils'

export interface TabDef {
  id: string
  label: string
  /** Optional lucide icon component */
  icon?: React.ElementType
}

interface TabsProps {
  /** Currently active tab id */
  value: string
  onChange: (id: string) => void
  tabs: readonly TabDef[]
  children?: React.ReactNode
  /** Extra classes on the tablist wrapper div */
  className?: string
  /** Visual variant: 'underline' (default) | 'pill' */
  variant?: 'underline' | 'pill'
}

/**
 * Accessible tablist with roving tabIndex and arrow-key navigation.
 * Left/Right cycle through tabs; Home/End jump to first/last.
 */
export function Tabs({
  value,
  onChange,
  tabs,
  children,
  className,
  variant = 'underline',
}: TabsProps) {
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([])

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const currentIdx = tabs.findIndex((t) => t.id === value)
    let next = currentIdx

    switch (e.key) {
      case 'ArrowLeft':
        next = (currentIdx - 1 + tabs.length) % tabs.length
        break
      case 'ArrowRight':
        next = (currentIdx + 1) % tabs.length
        break
      case 'Home':
        next = 0
        break
      case 'End':
        next = tabs.length - 1
        break
      default:
        return
    }

    e.preventDefault()
    onChange(tabs[next].id)
    tabRefs.current[next]?.focus()
  }

  const wrapperCls =
    variant === 'pill'
      ? 'flex gap-1 p-1 bg-muted rounded-lg overflow-x-auto'
      : 'flex border-b border-border overflow-x-auto'

  return (
    <div>
      {/* tablist */}
      <div
        role="tablist"
        className={cn(wrapperCls, className)}
        onKeyDown={handleKeyDown}
        aria-label="Page sections"
      >
        {tabs.map((tab, idx) => {
          const isSelected = tab.id === value
          const Icon = tab.icon

          const tabCls =
            variant === 'pill'
              ? cn(
                  'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap',
                  isSelected
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground',
                )
              : cn(
                  'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap',
                  isSelected
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground',
                )

          return (
            <button
              key={tab.id}
              ref={(el) => {
                tabRefs.current[idx] = el
              }}
              role="tab"
              id={`tab-${tab.id}`}
              aria-selected={isSelected}
              aria-controls={`tabpanel-${tab.id}`}
              tabIndex={isSelected ? 0 : -1}
              onClick={() => onChange(tab.id)}
              className={tabCls}
            >
              {Icon && <Icon className="h-4 w-4" aria-hidden="true" />}
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* tab panels — only the active one is visible */}
      {children}
    </div>
  )
}

interface TabPanelProps {
  id: string
  activeTab: string
  children: React.ReactNode
  className?: string
}

/** Wrap each page's tab content in this so the panel gets correct ARIA attrs. */
export function TabPanel({ id, activeTab, children, className }: TabPanelProps) {
  if (id !== activeTab) return null
  return (
    <div
      role="tabpanel"
      id={`tabpanel-${id}`}
      aria-labelledby={`tab-${id}`}
      tabIndex={0}
      className={cn('focus:outline-none', className)}
    >
      {children}
    </div>
  )
}
