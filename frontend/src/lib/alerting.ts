/**
 * Pure helpers for the Settings -> Notifications -> Remote alerting card
 * (Track 1: Telegram / Matrix outbound). The card wires form state to the
 * ready api.settings.getAlerting/saveAlerting/testAlerting client; the one bit
 * of real logic is the write-only-secret convention (null leaves the stored
 * token, "" clears it, a value sets it), which the backend applies verbatim.
 * Extracted here so that rule is unit-tested away from the DOM.
 */

import type { AlertingConfigUpdate, AlertSeverity } from './api'

/**
 * Resolve a write-only secret field to its PUT-body value.
 *  - clear  -> "" (explicitly clear the stored secret)
 *  - a value -> the trimmed value (set/replace the stored secret)
 *  - blank  -> undefined (omit, so the stored secret is left untouched)
 */
export function resolveSecretField(input: string, clear: boolean): string | undefined {
  if (clear) return ''
  const trimmed = input.trim()
  return trimmed ? trimmed : undefined
}

export interface TelegramForm {
  enabled: boolean
  chatId: string
  /** Raw token input; blank means "leave the stored token" unless clearToken. */
  token: string
  clearToken: boolean
  minSeverity: AlertSeverity
}

export interface MatrixForm {
  enabled: boolean
  homeserver: string
  roomId: string
  token: string
  clearToken: boolean
  minSeverity: AlertSeverity
}

/**
 * Build the AlertingConfigUpdate PUT body from the card's form state. Routing
 * ids are trimmed and always sent; token fields are omitted unless set/cleared
 * so a save never wipes a stored secret the admin did not touch.
 */
export function buildAlertingUpdate(tg: TelegramForm, mx: MatrixForm): AlertingConfigUpdate {
  const botToken = resolveSecretField(tg.token, tg.clearToken)
  const accessToken = resolveSecretField(mx.token, mx.clearToken)
  return {
    telegram: {
      enabled: tg.enabled,
      chatId: tg.chatId.trim(),
      minSeverity: tg.minSeverity,
      ...(botToken !== undefined ? { botToken } : {}),
    },
    matrix: {
      enabled: mx.enabled,
      homeserver: mx.homeserver.trim(),
      roomId: mx.roomId.trim(),
      minSeverity: mx.minSeverity,
      ...(accessToken !== undefined ? { accessToken } : {}),
    },
  }
}
