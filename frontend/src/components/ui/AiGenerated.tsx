/**
 * AiGenerated - an honesty-framed container for model-generated widget text.
 *
 * Every LLM insight widget renders its explanation inside this, so the "this is
 * a model hypothesis, not measured telemetry" caption is consistent and never
 * forgotten. Used only for the opt-in explain output, never for computed data.
 */

import type { ReactNode } from 'react'
import { Sparkles } from 'lucide-react'

export function AiGenerated({ children }: { children?: ReactNode }) {
  return (
    <div className="rounded-lg border border-primary/20 bg-primary/5 p-3">
      <div className="mb-1 flex items-center gap-1.5 text-[11px] font-medium text-primary">
        <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
        AI explanation
      </div>
      {children != null && <div className="text-sm text-foreground">{children}</div>}
      <p className="mt-1.5 text-[11px] text-muted-foreground">
        Model-generated hypothesis, not measured telemetry.
      </p>
    </div>
  )
}

export default AiGenerated
