/**
 * Constitutional AIOps - WebSocket Client
 *
 * React hook and utilities for real-time updates via WebSocket.
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { DEMO_MODE } from './demo/flag'

// WebSocket event types (must match backend EventType enum)
export enum EventType {
  // Connection events
  CONNECTED = 'connected',
  PING = 'ping',
  PONG = 'pong',

  // Incident events
  INCIDENT_CREATED = 'incident.created',
  INCIDENT_UPDATED = 'incident.updated',
  INCIDENT_RESOLVED = 'incident.resolved',
  INCIDENT_DELETED = 'incident.deleted',

  // Action events
  ACTION_CREATED = 'action.created',
  ACTION_APPROVED = 'action.approved',
  ACTION_REJECTED = 'action.rejected',
  ACTION_EXECUTED = 'action.executed',
  ACTION_FAILED = 'action.failed',

  // Analysis events
  RCA_STARTED = 'rca.started',
  RCA_COMPLETED = 'rca.completed',
  REMEDIATION_PLANNED = 'remediation.planned',

  // System events
  SYSTEM_HEALTH = 'system.health',
  AGENT_STATUS = 'agent.status',
  ALERT = 'alert',
}

// WebSocket event structure
export interface WebSocketEvent<T = unknown> {
  type: EventType
  payload: T
  timestamp: string
  correlation_id?: string
}

// Connection state
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'

// WebSocket hook options
export interface UseWebSocketOptions {
  url?: string
  clientId?: string
  autoConnect?: boolean
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

// Default WebSocket URL - use relative path that works with nginx proxy in Docker
// Also handle secure WebSocket (wss) for HTTPS
// Guard the module-level window access so this file is importable in a non-DOM
// context (e.g. unit tests of helpers that import EventType). Identical in the
// browser; the fallback URL is never used server-side.
const protocol =
  typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const DEFAULT_WS_URL =
  typeof window !== 'undefined' ? `${protocol}//${window.location.host}/ws` : '/ws'

// Module-level cache for the app-layer WS token. Caddy basic_auth gates /api/* but
// cannot ride the WS upgrade handshake, so the SPA fetches this token (same-origin,
// the browser replays the cached basic-auth credentials) and appends it to the WS
// URL. Empty string means the backend has no WS_TOKEN set (local/dev) and connects
// unauthenticated.
let wsTokenCache: string | undefined

async function getWsToken(): Promise<string> {
  if (wsTokenCache !== undefined) {
    return wsTokenCache
  }
  let token: string
  try {
    const res = await fetch('/api/v1/ws/token')
    const data = await res.json()
    token = typeof data?.token === 'string' ? data.token : ''
  } catch {
    // On any failure, treat the token as empty so local/dev still connects.
    token = ''
  }
  wsTokenCache = token
  return token
}

/**
 * React hook for WebSocket connection management.
 *
 * @example
 * ```tsx
 * const { isConnected, subscribe, lastEvent } = useWebSocket()
 *
 * useEffect(() => {
 *   const unsubscribe = subscribe(EventType.INCIDENT_CREATED, (event) => {
 *     console.log('New incident:', event.payload)
 *   })
 *   return unsubscribe
 * }, [subscribe])
 * ```
 */
export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    url = DEFAULT_WS_URL,
    clientId,
    autoConnect = true,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onConnect,
    onDisconnect,
    onError,
  } = options

  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [lastEvent, setLastEvent] = useState<WebSocketEvent | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const listenersRef = useRef<Map<EventType | '*', Set<(event: WebSocketEvent) => void>>>(new Map())

  // Clear reconnect timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])

  // Attempt to reconnect
  const attemptReconnect = useCallback(() => {
    if (!reconnect || reconnectAttemptsRef.current >= maxReconnectAttempts) {
      console.log('Max reconnect attempts reached or reconnect disabled')
      return
    }

    reconnectAttemptsRef.current += 1
    console.log(`Attempting reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`)

    reconnectTimeoutRef.current = setTimeout(() => {
      connect()
    }, reconnectInterval)
  }, [reconnect, maxReconnectAttempts, reconnectInterval])

  // Connect to WebSocket
  const connect = useCallback(async () => {
    // Demo build: there is no backend socket. Report a healthy "Live"
    // connection and emit nothing (pages render from the fixture fetches).
    if (DEMO_MODE) {
      setConnectionState('connected')
      reconnectAttemptsRef.current = 0
      onConnect?.()
      return
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected')
      return
    }

    clearReconnectTimeout()
    setConnectionState('connecting')

    // Fetch the app-layer token (cached) before opening the socket. The token
    // rides as a query param because Caddy basic_auth can't gate the WS upgrade.
    const token = await getWsToken()
    const params = new URLSearchParams()
    if (clientId) {
      params.set('client_id', clientId)
    }
    if (token) {
      params.set('token', token)
    }
    const query = params.toString()
    const wsUrl = query ? `${url}?${query}` : url
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected')
      setConnectionState('connected')
      reconnectAttemptsRef.current = 0
      onConnect?.()
    }

    ws.onclose = (event) => {
      console.log('WebSocket disconnected', event.code, event.reason)
      setConnectionState('disconnected')
      wsRef.current = null
      onDisconnect?.()

      // Attempt reconnect if not a clean close
      if (event.code !== 1000 && event.code !== 1001) {
        attemptReconnect()
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnectionState('error')
      onError?.(error)
    }

    ws.onmessage = (event) => {
      try {
        const wsEvent: WebSocketEvent = JSON.parse(event.data)
        setLastEvent(wsEvent)

        // Notify type-specific listeners
        const typeListeners = listenersRef.current.get(wsEvent.type)
        if (typeListeners) {
          typeListeners.forEach((listener) => listener(wsEvent))
        }

        // Notify wildcard listeners
        const wildcardListeners = listenersRef.current.get('*')
        if (wildcardListeners) {
          wildcardListeners.forEach((listener) => listener(wsEvent))
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    wsRef.current = ws
  }, [url, clientId, clearReconnectTimeout, onConnect, onDisconnect, onError, attemptReconnect])

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    clearReconnectTimeout()
    reconnectAttemptsRef.current = maxReconnectAttempts // Prevent auto-reconnect

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect')
      wsRef.current = null
    }

    setConnectionState('disconnected')
  }, [clearReconnectTimeout, maxReconnectAttempts])

  // Send a message through WebSocket
  const send = useCallback((message: WebSocketEvent) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, cannot send message')
    }
  }, [])

  // Send a ping
  const ping = useCallback(() => {
    send({
      type: EventType.PING,
      payload: {},
      timestamp: new Date().toISOString(),
    })
  }, [send])

  // Subscribe to a room (e.g., specific incident)
  const subscribeToRoom = useCallback(
    (room: string) => {
      send({
        type: 'subscribe' as EventType,
        payload: { room },
        timestamp: new Date().toISOString(),
      })
    },
    [send]
  )

  // Unsubscribe from a room
  const unsubscribeFromRoom = useCallback(
    (room: string) => {
      send({
        type: 'unsubscribe' as EventType,
        payload: { room },
        timestamp: new Date().toISOString(),
      })
    },
    [send]
  )

  // Subscribe to event type
  const subscribe = useCallback(
    <T = unknown>(
      eventType: EventType | '*',
      callback: (event: WebSocketEvent<T>) => void
    ): (() => void) => {
      if (!listenersRef.current.has(eventType)) {
        listenersRef.current.set(eventType, new Set())
      }

      const listeners = listenersRef.current.get(eventType)!
      listeners.add(callback as (event: WebSocketEvent) => void)

      // Return unsubscribe function
      return () => {
        listeners.delete(callback as (event: WebSocketEvent) => void)
      }
    },
    []
  )

  // Keep the latest connect/disconnect in refs so the mount effect runs ONCE
  // instead of re-subscribing every render. Consumers pass inline callbacks
  // (e.g. onConnect), which change `connect`/`disconnect` identity on every
  // render; depending on them here previously tore down and reopened the socket
  // each render. Each teardown closed with code 1006 and triggered a reconnect,
  // compounding into a storm that Chrome throttled ("Insufficient resources") —
  // leaving the live-status badge stuck on "Offline".
  const connectRef = useRef(connect)
  const disconnectRef = useRef(disconnect)
  connectRef.current = connect
  disconnectRef.current = disconnect

  // Auto-connect on mount (and only when autoConnect itself changes).
  useEffect(() => {
    if (autoConnect) {
      connectRef.current()
    }

    return () => {
      disconnectRef.current()
    }
  }, [autoConnect])

  return {
    // State
    connectionState,
    isConnected: connectionState === 'connected',
    lastEvent,

    // Actions
    connect,
    disconnect,
    send,
    ping,
    subscribeToRoom,
    unsubscribeFromRoom,
    subscribe,
  }
}

/**
 * Type-safe event subscription hooks for specific event types.
 */
export function useIncidentEvents(
  onCreated?: (incident: unknown) => void,
  onUpdated?: (incident: unknown) => void,
  onResolved?: (data: { incident_id: string }) => void
) {
  const { subscribe, isConnected } = useWebSocket()

  useEffect(() => {
    const unsubscribers: (() => void)[] = []

    if (onCreated) {
      unsubscribers.push(subscribe(EventType.INCIDENT_CREATED, (e) => onCreated(e.payload)))
    }
    if (onUpdated) {
      unsubscribers.push(subscribe(EventType.INCIDENT_UPDATED, (e) => onUpdated(e.payload)))
    }
    if (onResolved) {
      unsubscribers.push(
        subscribe(EventType.INCIDENT_RESOLVED, (e) => onResolved(e.payload as { incident_id: string }))
      )
    }

    return () => {
      unsubscribers.forEach((unsub) => unsub())
    }
  }, [subscribe, onCreated, onUpdated, onResolved])

  return { isConnected }
}

export function useActionEvents(
  onCreated?: (action: unknown) => void,
  onApproved?: (action: unknown) => void,
  onRejected?: (action: unknown) => void,
  onExecuted?: (action: unknown) => void
) {
  const { subscribe, isConnected } = useWebSocket()

  useEffect(() => {
    const unsubscribers: (() => void)[] = []

    if (onCreated) {
      unsubscribers.push(subscribe(EventType.ACTION_CREATED, (e) => onCreated(e.payload)))
    }
    if (onApproved) {
      unsubscribers.push(subscribe(EventType.ACTION_APPROVED, (e) => onApproved(e.payload)))
    }
    if (onRejected) {
      unsubscribers.push(subscribe(EventType.ACTION_REJECTED, (e) => onRejected(e.payload)))
    }
    if (onExecuted) {
      unsubscribers.push(subscribe(EventType.ACTION_EXECUTED, (e) => onExecuted(e.payload)))
    }

    return () => {
      unsubscribers.forEach((unsub) => unsub())
    }
  }, [subscribe, onCreated, onApproved, onRejected, onExecuted])

  return { isConnected }
}

export function useSystemEvents(onHealth?: (health: unknown) => void, onAlert?: (alert: unknown) => void) {
  const { subscribe, isConnected } = useWebSocket()

  useEffect(() => {
    const unsubscribers: (() => void)[] = []

    if (onHealth) {
      unsubscribers.push(subscribe(EventType.SYSTEM_HEALTH, (e) => onHealth(e.payload)))
    }
    if (onAlert) {
      unsubscribers.push(subscribe(EventType.ALERT, (e) => onAlert(e.payload)))
    }

    return () => {
      unsubscribers.forEach((unsub) => unsub())
    }
  }, [subscribe, onHealth, onAlert])

  return { isConnected }
}

// Export singleton context for shared WebSocket connection
export { DEFAULT_WS_URL }
