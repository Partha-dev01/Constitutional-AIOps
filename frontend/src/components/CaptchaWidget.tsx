import { useEffect, useRef, useState } from 'react'

/**
 * Renders a Cloudflare Turnstile or hCaptcha widget for the signup form. Both
 * expose a compatible explicit-render API (`window.<global>.render(el, opts)`),
 * so one component covers both. The provider + site key come from the backend
 * /auth/config; when neither is set the widget renders nothing (captcha off).
 */

interface CaptchaApi {
  render: (
    el: HTMLElement,
    opts: {
      sitekey: string
      callback: (token: string) => void
      'expired-callback'?: () => void
      'error-callback'?: () => void
    },
  ) => string
  reset: (widgetId?: string) => void
}

declare global {
  interface Window {
    turnstile?: CaptchaApi
    hcaptcha?: CaptchaApi
  }
}

type ProviderKey = 'turnstile' | 'hcaptcha'

const SCRIPTS: Record<ProviderKey, string> = {
  turnstile: 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit',
  hcaptcha: 'https://js.hcaptcha.com/1/api.js?render=explicit',
}

function isProvider(value: string): value is ProviderKey {
  return value === 'turnstile' || value === 'hcaptcha'
}

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = src
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('captcha script failed to load'))
    document.head.appendChild(script)
  })
}

function waitForGlobal(name: ProviderKey): Promise<CaptchaApi> {
  return new Promise((resolve, reject) => {
    const started = Date.now()
    const tick = () => {
      const apiObj = window[name]
      if (apiObj && typeof apiObj.render === 'function') {
        resolve(apiObj)
      } else if (Date.now() - started > 10000) {
        reject(new Error('captcha global unavailable'))
      } else {
        window.setTimeout(tick, 100)
      }
    }
    tick()
  })
}

export interface CaptchaWidgetProps {
  provider: string
  siteKey: string
  /** Fires with the solved token, or null when it expires/errors. */
  onToken: (token: string | null) => void
}

export function CaptchaWidget({ provider, siteKey, onToken }: CaptchaWidgetProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    if (!isProvider(provider) || !siteKey) return
    const el = containerRef.current
    if (!el) return
    let cancelled = false
    loadScript(SCRIPTS[provider])
      .then(() => waitForGlobal(provider))
      .then((apiObj) => {
        if (cancelled) return
        el.innerHTML = ''
        apiObj.render(el, {
          sitekey: siteKey,
          callback: (token: string) => onToken(token),
          'expired-callback': () => onToken(null),
          'error-callback': () => onToken(null),
        })
      })
      .catch(() => {
        if (!cancelled) setFailed(true)
      })
    return () => {
      cancelled = true
    }
  }, [provider, siteKey, onToken])

  if (!isProvider(provider) || !siteKey) return null
  if (failed) {
    return (
      <p className="text-sm text-red-400" role="alert">
        Could not load the verification widget. Refresh and try again.
      </p>
    )
  }
  return <div ref={containerRef} className="min-h-[65px]" />
}

export default CaptchaWidget
