/**
 * useAiWidgets - read the per-user LLM-insight opt-in state.
 *
 * The insight widgets (AnomalyScan and the rest) call this to decide whether to
 * show their opt-in "Explain" button. It is a plain read: the Settings card owns
 * writing the preference. A failed fetch degrades to "off" so a widget never
 * shows an explain button it cannot back.
 */

import { useEffect, useState } from 'react'
import { api } from './api'

interface AiWidgetsState {
  enabled: boolean
  autoExplain: boolean
  loading: boolean
}

export function useAiWidgets(): AiWidgetsState {
  const [state, setState] = useState<AiWidgetsState>({
    enabled: false,
    autoExplain: false,
    loading: true,
  })

  useEffect(() => {
    let cancelled = false
    api.insights
      .getPreferences()
      .then((prefs) => {
        if (cancelled) return
        setState({
          enabled: prefs.aiWidgets.enabled,
          autoExplain: prefs.aiWidgets.autoExplain,
          loading: false,
        })
      })
      .catch(() => {
        if (!cancelled) setState({ enabled: false, autoExplain: false, loading: false })
      })
    return () => {
      cancelled = true
    }
  }, [])

  return state
}

export default useAiWidgets
