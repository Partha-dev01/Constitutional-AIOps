/**
 * Constitutional AIOps - Service Dependency Graph Component
 *
 * Interactive visualization of service dependencies and their health status.
 * Uses CSS-based positioning for a simple, no-dependency approach.
 */

import { useState, useMemo } from 'react'
import {
  Server,
  Database,
  Globe,
  Cpu,
  HardDrive,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  RefreshCw,
} from 'lucide-react'

// Service types
export type ServiceType = 'api' | 'database' | 'cache' | 'queue' | 'gateway' | 'worker' | 'external'
export type ServiceStatus = 'healthy' | 'degraded' | 'down' | 'unknown'

export interface ServiceNode {
  id: string
  name: string
  type: ServiceType
  status: ServiceStatus
  metrics?: {
    cpu?: number
    memory?: number
    latency?: number
    errorRate?: number
  }
  dependencies?: string[] // IDs of services this depends on
}

export interface DependencyEdge {
  source: string
  target: string
  latency?: number
  errorRate?: number
}

interface DependencyGraphProps {
  services: ServiceNode[]
  edges?: DependencyEdge[]
  onServiceClick?: (service: ServiceNode) => void
  className?: string
}

// Service type icons
const serviceIcons: Record<ServiceType, React.ElementType> = {
  api: Server,
  database: Database,
  cache: HardDrive,
  queue: Cpu,
  gateway: Globe,
  worker: Cpu,
  external: Globe,
}

// Status colors
const statusColors: Record<ServiceStatus, { bg: string; border: string; text: string }> = {
  healthy: {
    bg: 'bg-green-500/10',
    border: 'border-green-500/50',
    text: 'text-green-500',
  },
  degraded: {
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/50',
    text: 'text-yellow-500',
  },
  down: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/50',
    text: 'text-red-500',
  },
  unknown: {
    bg: 'bg-gray-500/10',
    border: 'border-gray-500/50',
    text: 'text-gray-500',
  },
}

// Status icons
const statusIcons: Record<ServiceStatus, React.ElementType> = {
  healthy: CheckCircle,
  degraded: AlertTriangle,
  down: XCircle,
  unknown: AlertTriangle,
}

export function DependencyGraph({
  services,
  edges = [],
  onServiceClick,
  className = '',
}: DependencyGraphProps) {
  const [selectedService, setSelectedService] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1)

  // Calculate positions for services in a layered layout
  const layout = useMemo(() => {
    // Group services by type for layered positioning
    const layers: Record<string, ServiceNode[]> = {
      gateway: [],
      api: [],
      worker: [],
      database: [],
      cache: [],
      queue: [],
      external: [],
    }

    services.forEach((service) => {
      const layer = layers[service.type] || layers.api
      layer.push(service)
    })

    // Calculate positions
    const positions: Record<string, { x: number; y: number }> = {}
    const layerOrder = ['gateway', 'api', 'worker', 'database', 'cache', 'queue', 'external']
    const layerY: Record<string, number> = {
      gateway: 50,
      api: 150,
      worker: 150,
      database: 250,
      cache: 250,
      queue: 250,
      external: 350,
    }

    layerOrder.forEach((layerName) => {
      const layerServices = layers[layerName]
      const spacing = 180
      const startX = (800 - layerServices.length * spacing) / 2 + spacing / 2

      layerServices.forEach((service, index) => {
        positions[service.id] = {
          x: startX + index * spacing,
          y: layerY[layerName],
        }
      })
    })

    return positions
  }, [services])

  // Generate edges from dependencies if not provided
  const allEdges = useMemo(() => {
    if (edges.length > 0) return edges

    const generatedEdges: DependencyEdge[] = []
    services.forEach((service) => {
      if (service.dependencies) {
        service.dependencies.forEach((depId) => {
          generatedEdges.push({
            source: service.id,
            target: depId,
          })
        })
      }
    })
    return generatedEdges
  }, [services, edges])

  const handleServiceClick = (service: ServiceNode) => {
    setSelectedService(service.id === selectedService ? null : service.id)
    onServiceClick?.(service)
  }

  const selectedServiceData = services.find((s) => s.id === selectedService)

  return (
    <div className={`relative ${className}`}>
      {/* Controls */}
      <div className="absolute top-2 right-2 z-10 flex items-center gap-1 bg-card/80 backdrop-blur-sm rounded-lg p-1 border border-border">
        <button
          onClick={() => setZoom((z) => Math.min(z + 0.1, 1.5))}
          className="p-1.5 hover:bg-muted rounded-sm"
          title="Zoom in"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          onClick={() => setZoom((z) => Math.max(z - 0.1, 0.5))}
          className="p-1.5 hover:bg-muted rounded-sm"
          title="Zoom out"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <button
          onClick={() => setZoom(1)}
          className="p-1.5 hover:bg-muted rounded-sm"
          title="Reset zoom"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Graph container */}
      <div
        className="relative w-full h-[400px] overflow-hidden bg-muted/20 rounded-lg border border-border"
        style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
      >
        {/* SVG for edges */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill="currentColor" className="text-muted-foreground" />
            </marker>
          </defs>

          {allEdges.map((edge, index) => {
            const sourcePos = layout[edge.source]
            const targetPos = layout[edge.target]

            if (!sourcePos || !targetPos) return null

            // Calculate edge color based on error rate
            let strokeColor = 'stroke-muted-foreground'
            if (edge.errorRate && edge.errorRate > 5) {
              strokeColor = 'stroke-red-500'
            } else if (edge.errorRate && edge.errorRate > 1) {
              strokeColor = 'stroke-yellow-500'
            }

            // Highlight edges connected to selected service
            const isHighlighted =
              selectedService && (edge.source === selectedService || edge.target === selectedService)

            return (
              <g key={`${edge.source}-${edge.target}-${index}`}>
                <line
                  x1={sourcePos.x}
                  y1={sourcePos.y + 20}
                  x2={targetPos.x}
                  y2={targetPos.y - 20}
                  className={`${strokeColor} ${isHighlighted ? 'stroke-2' : 'stroke-1'}`}
                  strokeDasharray={isHighlighted ? undefined : '4,4'}
                  markerEnd="url(#arrowhead)"
                  opacity={selectedService ? (isHighlighted ? 1 : 0.3) : 0.6}
                />
                {edge.latency && (
                  <text
                    x={(sourcePos.x + targetPos.x) / 2}
                    y={(sourcePos.y + targetPos.y) / 2}
                    className="text-xs fill-muted-foreground"
                    textAnchor="middle"
                  >
                    {edge.latency}ms
                  </text>
                )}
              </g>
            )
          })}
        </svg>

        {/* Service nodes */}
        {services.map((service) => {
          const pos = layout[service.id]
          if (!pos) return null

          const Icon = serviceIcons[service.type]
          const StatusIcon = statusIcons[service.status]
          const colors = statusColors[service.status]
          const isSelected = service.id === selectedService

          return (
            <div
              key={service.id}
              className={`absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-all duration-200 ${
                isSelected ? 'scale-110 z-20' : 'z-10'
              } ${selectedService && !isSelected ? 'opacity-50' : ''}`}
              style={{ left: pos.x, top: pos.y }}
              onClick={() => handleServiceClick(service)}
            >
              <div
                className={`w-32 p-2 rounded-lg border-2 ${colors.bg} ${colors.border} ${
                  isSelected ? 'ring-2 ring-primary' : ''
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Icon className={`h-4 w-4 ${colors.text}`} />
                  <span className="text-xs font-medium truncate">{service.name}</span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <StatusIcon className={`h-3 w-3 ${colors.text}`} />
                    <span className={`text-xs ${colors.text}`}>{service.status}</span>
                  </div>

                  {service.metrics?.latency && (
                    <span className="text-xs text-muted-foreground">{service.metrics.latency}ms</span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Selected service details panel */}
      {selectedServiceData && (
        <div className="mt-4 p-4 bg-card rounded-lg border border-border">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {(() => {
                const Icon = serviceIcons[selectedServiceData.type]
                const colors = statusColors[selectedServiceData.status]
                return <Icon className={`h-5 w-5 ${colors.text}`} />
              })()}
              <h3 className="font-semibold">{selectedServiceData.name}</h3>
              <span
                className={`px-2 py-0.5 rounded-full text-xs ${
                  statusColors[selectedServiceData.status].bg
                } ${statusColors[selectedServiceData.status].text}`}
              >
                {selectedServiceData.status}
              </span>
            </div>
            <button
              onClick={() => setSelectedService(null)}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Close
            </button>
          </div>

          {selectedServiceData.metrics && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {selectedServiceData.metrics.cpu !== undefined && (
                <MetricCard label="CPU" value={`${selectedServiceData.metrics.cpu}%`} />
              )}
              {selectedServiceData.metrics.memory !== undefined && (
                <MetricCard label="Memory" value={`${selectedServiceData.metrics.memory}%`} />
              )}
              {selectedServiceData.metrics.latency !== undefined && (
                <MetricCard label="Latency" value={`${selectedServiceData.metrics.latency}ms`} />
              )}
              {selectedServiceData.metrics.errorRate !== undefined && (
                <MetricCard
                  label="Error Rate"
                  value={`${selectedServiceData.metrics.errorRate.toFixed(2)}%`}
                />
              )}
            </div>
          )}

          {selectedServiceData.dependencies && selectedServiceData.dependencies.length > 0 && (
            <div className="mt-3 pt-3 border-t border-border">
              <p className="text-xs text-muted-foreground mb-2">Dependencies</p>
              <div className="flex flex-wrap gap-2">
                {selectedServiceData.dependencies.map((depId) => {
                  const dep = services.find((s) => s.id === depId)
                  return (
                    <span
                      key={depId}
                      className="px-2 py-1 bg-muted rounded-sm text-xs flex items-center gap-1"
                    >
                      <ChevronRight className="h-3 w-3" />
                      {dep?.name || depId}
                    </span>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
        <span className="font-medium">Status:</span>
        {Object.entries(statusColors).map(([status, colors]) => (
          <div key={status} className="flex items-center gap-1">
            <div className={`w-3 h-3 rounded-full ${colors.bg} border ${colors.border}`} />
            <span className="capitalize">{status}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-2 bg-muted/50 rounded-sm">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-semibold">{value}</p>
    </div>
  )
}

// Sample data generator for demo
export function generateSampleServices(): ServiceNode[] {
  return [
    {
      id: 'api-gateway',
      name: 'API Gateway',
      type: 'gateway',
      status: 'healthy',
      metrics: { cpu: 45, memory: 62, latency: 12, errorRate: 0.1 },
      dependencies: ['user-service', 'order-service', 'payment-service'],
    },
    {
      id: 'user-service',
      name: 'User Service',
      type: 'api',
      status: 'healthy',
      metrics: { cpu: 35, memory: 48, latency: 25, errorRate: 0.05 },
      dependencies: ['postgres-primary', 'redis-cache'],
    },
    {
      id: 'order-service',
      name: 'Order Service',
      type: 'api',
      status: 'degraded',
      metrics: { cpu: 78, memory: 85, latency: 150, errorRate: 2.5 },
      dependencies: ['postgres-primary', 'rabbitmq'],
    },
    {
      id: 'payment-service',
      name: 'Payment Service',
      type: 'api',
      status: 'healthy',
      metrics: { cpu: 42, memory: 55, latency: 45, errorRate: 0.2 },
      dependencies: ['postgres-primary', 'stripe-api'],
    },
    {
      id: 'postgres-primary',
      name: 'PostgreSQL',
      type: 'database',
      status: 'healthy',
      metrics: { cpu: 55, memory: 70, latency: 5, errorRate: 0 },
    },
    {
      id: 'redis-cache',
      name: 'Redis Cache',
      type: 'cache',
      status: 'healthy',
      metrics: { cpu: 15, memory: 45, latency: 1, errorRate: 0 },
    },
    {
      id: 'rabbitmq',
      name: 'RabbitMQ',
      type: 'queue',
      status: 'degraded',
      metrics: { cpu: 65, memory: 72, latency: 8, errorRate: 0.5 },
    },
    {
      id: 'stripe-api',
      name: 'Stripe API',
      type: 'external',
      status: 'healthy',
      metrics: { latency: 120, errorRate: 0.1 },
    },
  ]
}

export default DependencyGraph
