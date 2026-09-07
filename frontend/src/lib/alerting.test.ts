import { describe, it, expect } from 'vitest'
import { resolveSecretField, buildAlertingUpdate, type TelegramForm, type MatrixForm } from './alerting'

const tg = (over: Partial<TelegramForm> = {}): TelegramForm => ({
  enabled: false,
  chatId: '',
  token: '',
  clearToken: false,
  minSeverity: 'warning',
  inboundEnabled: false,
  ...over,
})

const mx = (over: Partial<MatrixForm> = {}): MatrixForm => ({
  enabled: false,
  homeserver: '',
  roomId: '',
  token: '',
  clearToken: false,
  minSeverity: 'warning',
  ...over,
})

describe('resolveSecretField', () => {
  it('omits (undefined) a blank input so the stored secret is left untouched', () => {
    expect(resolveSecretField('', false)).toBeUndefined()
    expect(resolveSecretField('   ', false)).toBeUndefined()
  })

  it('returns the trimmed value when a value is entered', () => {
    expect(resolveSecretField('  abc123  ', false)).toBe('abc123')
  })

  it('returns "" to clear when clear is set, even over a typed value', () => {
    expect(resolveSecretField('', true)).toBe('')
    expect(resolveSecretField('typed', true)).toBe('')
  })
})

describe('buildAlertingUpdate', () => {
  it('trims routing ids and omits both tokens when neither is set or cleared', () => {
    const body = buildAlertingUpdate(
      tg({ enabled: true, chatId: '  123  ', minSeverity: 'error' }),
      mx({ enabled: true, homeserver: ' https://m.example.org ', roomId: ' !r:example.org ' }),
    )
    expect(body.telegram).toEqual({
      enabled: true,
      chatId: '123',
      minSeverity: 'error',
      inboundEnabled: false,
    })
    expect('botToken' in body.telegram).toBe(false)
    expect(body.matrix).toEqual({
      enabled: true,
      homeserver: 'https://m.example.org',
      roomId: '!r:example.org',
      minSeverity: 'warning',
    })
    expect('accessToken' in body.matrix).toBe(false)
  })

  it('sets a token when a value is entered', () => {
    const body = buildAlertingUpdate(tg({ token: '  bottok  ' }), mx({ token: 'mxtok' }))
    expect(body.telegram.botToken).toBe('bottok')
    expect(body.matrix.accessToken).toBe('mxtok')
  })

  it('clears a token with "" when clearToken is set', () => {
    const body = buildAlertingUpdate(tg({ clearToken: true }), mx({ token: 'ignored', clearToken: true }))
    expect(body.telegram.botToken).toBe('')
    expect(body.matrix.accessToken).toBe('')
  })

  it('always sends the inbound toggle so a normal save cannot silently disable it', () => {
    expect(buildAlertingUpdate(tg({ inboundEnabled: true }), mx()).telegram.inboundEnabled).toBe(true)
    expect(buildAlertingUpdate(tg({ inboundEnabled: false }), mx()).telegram.inboundEnabled).toBe(false)
  })
})
