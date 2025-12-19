# Constitutional AIOps - Mega Prompt Part 3: Constitutional AI, Frontend, and Deployment

---

## 7. Constitutional AI Framework

### 7.1 Safety Principles

```python
# src/constitutional/principles.py
"""
Constitutional AI safety principles for AIOps.
"""

from enum import Enum
from typing import List
from pydantic import BaseModel


class PrincipleTier(int, Enum):
    """Safety principle tiers - higher tier = stricter enforcement."""
    TIER_1_SAFETY = 1      # Never violate
    TIER_2_OPERATIONAL = 2  # Best practices
    TIER_3_LEARNING = 3     # Continuous improvement


class Principle(BaseModel):
    """A constitutional principle."""
    id: str
    tier: PrincipleTier
    name: str
    description: str
    check_function: str  # Name of validation function


# Tier 1: Safety-Critical Principles (NEVER VIOLATE)
TIER_1_PRINCIPLES = [
    Principle(
        id="P1.1",
        tier=PrincipleTier.TIER_1_SAFETY,
        name="No Data Deletion Without Confirmation",
        description="Never delete data, databases, or persistent storage without explicit human confirmation",
        check_function="check_no_data_deletion"
    ),
    Principle(
        id="P1.2",
        tier=PrincipleTier.TIER_1_SAFETY,
        name="Maintain Minimum Replicas",
        description="Always maintain at least 2 healthy replicas of critical services",
        check_function="check_minimum_replicas"
    ),
    Principle(
        id="P1.3",
        tier=PrincipleTier.TIER_1_SAFETY,
        name="No Cascade Actions",
        description="No single action should affect more than 5 services simultaneously",
        check_function="check_cascade_limit"
    ),
    Principle(
        id="P1.4",
        tier=PrincipleTier.TIER_1_SAFETY,
        name="Reversibility Requirement",
        description="All automated actions must be reversible within 60 seconds",
        check_function="check_reversibility"
    ),
    Principle(
        id="P1.5",
        tier=PrincipleTier.TIER_1_SAFETY,
        name="No Credential Exposure",
        description="Never log, transmit, or expose credentials or sensitive data",
        check_function="check_no_credential_exposure"
    ),
]

# Tier 2: Operational Principles (Best Practices)
TIER_2_PRINCIPLES = [
    Principle(
        id="P2.1",
        tier=PrincipleTier.TIER_2_OPERATIONAL,
        name="Minimal Intervention",
        description="Prefer the smallest effective action to resolve an issue",
        check_function="check_minimal_intervention"
    ),
    Principle(
        id="P2.2",
        tier=PrincipleTier.TIER_2_OPERATIONAL,
        name="Evidence-Based Decisions",
        description="All actions must be justified by telemetry evidence",
        check_function="check_evidence_based"
    ),
    Principle(
        id="P2.3",
        tier=PrincipleTier.TIER_2_OPERATIONAL,
        name="Historical Precedent",
        description="Check if similar incidents have been resolved before",
        check_function="check_historical_precedent"
    ),
    Principle(
        id="P2.4",
        tier=PrincipleTier.TIER_2_OPERATIONAL,
        name="Graceful Degradation",
        description="Prefer degraded operation over complete shutdown",
        check_function="check_graceful_degradation"
    ),
    Principle(
        id="P2.5",
        tier=PrincipleTier.TIER_2_OPERATIONAL,
        name="Rate Limiting",
        description="Limit action frequency to prevent oscillation",
        check_function="check_rate_limit"
    ),
]

# Tier 3: Learning Principles (Continuous Improvement)
TIER_3_PRINCIPLES = [
    Principle(
        id="P3.1",
        tier=PrincipleTier.TIER_3_LEARNING,
        name="Outcome Attribution",
        description="Track outcomes of all automated actions",
        check_function="check_outcome_tracking"
    ),
    Principle(
        id="P3.2",
        tier=PrincipleTier.TIER_3_LEARNING,
        name="Failure Analysis",
        description="Analyze and learn from unsuccessful actions",
        check_function="check_failure_analysis"
    ),
    Principle(
        id="P3.3",
        tier=PrincipleTier.TIER_3_LEARNING,
        name="Pattern Reinforcement",
        description="Reinforce successful resolution patterns",
        check_function="check_pattern_reinforcement"
    ),
]

ALL_PRINCIPLES = TIER_1_PRINCIPLES + TIER_2_PRINCIPLES + TIER_3_PRINCIPLES


def get_principles_by_tier(tier: PrincipleTier) -> List[Principle]:
    """Get all principles for a specific tier."""
    return [p for p in ALL_PRINCIPLES if p.tier == tier]
```

### 7.2 Constitutional Validator

```python
# src/constitutional/validator.py
"""
Constitutional AI validator for action approval.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from src.constitutional.principles import (
    ALL_PRINCIPLES,
    PrincipleTier,
    Principle
)


class ValidationResult(str, Enum):
    APPROVED = "approved"
    REQUIRES_APPROVAL = "requires_approval"
    REJECTED = "rejected"


class ViolationDetail(BaseModel):
    principle_id: str
    principle_name: str
    tier: int
    reason: str


class ValidationResponse(BaseModel):
    result: ValidationResult
    confidence: float
    violations: List[ViolationDetail]
    warnings: List[str]
    approval_required_reason: Optional[str]
    timestamp: str


class Action(BaseModel):
    """Proposed action to validate."""
    action_type: str
    target_service: str
    parameters: Dict[str, Any]
    confidence: float
    reasoning: str
    reversible: bool
    affected_services: List[str]


class ConstitutionalValidator:
    """
    Validates proposed actions against Constitutional AI principles.
    
    Authorization Matrix:
    - Confidence >= 0.9 + No violations → APPROVED (automatic)
    - Confidence 0.7-0.9 or Tier 2 violations → REQUIRES_APPROVAL
    - Confidence < 0.7 or Tier 1 violations → REJECTED
    """
    
    def __init__(
        self,
        confidence_high: float = 0.9,
        confidence_medium: float = 0.7
    ):
        self.confidence_high = confidence_high
        self.confidence_medium = confidence_medium
        self.principles = ALL_PRINCIPLES
        
        # Action history for rate limiting
        self._recent_actions: List[Dict] = []
    
    async def validate(self, action: Action) -> ValidationResponse:
        """
        Validate a proposed action against all principles.
        """
        violations = []
        warnings = []
        
        # Check each principle
        for principle in self.principles:
            check_result = await self._check_principle(principle, action)
            
            if check_result["violated"]:
                violations.append(ViolationDetail(
                    principle_id=principle.id,
                    principle_name=principle.name,
                    tier=principle.tier.value,
                    reason=check_result["reason"]
                ))
            elif check_result.get("warning"):
                warnings.append(f"{principle.id}: {check_result['warning']}")
        
        # Determine result based on violations and confidence
        result = self._determine_result(action, violations)
        
        # Build response
        approval_reason = None
        if result == ValidationResult.REQUIRES_APPROVAL:
            if violations:
                approval_reason = f"Tier 2 violations: {', '.join(v.principle_id for v in violations if v.tier == 2)}"
            else:
                approval_reason = f"Confidence {action.confidence:.2f} below threshold {self.confidence_high}"
        
        return ValidationResponse(
            result=result,
            confidence=action.confidence,
            violations=violations,
            warnings=warnings,
            approval_required_reason=approval_reason,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def _determine_result(
        self,
        action: Action,
        violations: List[ViolationDetail]
    ) -> ValidationResult:
        """Determine validation result based on confidence and violations."""
        
        # Check for Tier 1 violations - always reject
        tier1_violations = [v for v in violations if v.tier == 1]
        if tier1_violations:
            logger.warning(f"Action rejected: Tier 1 violations - {[v.principle_id for v in tier1_violations]}")
            return ValidationResult.REJECTED
        
        # Check confidence
        if action.confidence < self.confidence_medium:
            logger.info(f"Action rejected: Low confidence {action.confidence:.2f}")
            return ValidationResult.REJECTED
        
        # Check for Tier 2 violations - require approval
        tier2_violations = [v for v in violations if v.tier == 2]
        if tier2_violations:
            return ValidationResult.REQUIRES_APPROVAL
        
        # Check confidence threshold for automatic approval
        if action.confidence >= self.confidence_high:
            return ValidationResult.APPROVED
        else:
            return ValidationResult.REQUIRES_APPROVAL
    
    async def _check_principle(
        self,
        principle: Principle,
        action: Action
    ) -> Dict[str, Any]:
        """Check if an action violates a specific principle."""
        
        # Dispatch to specific check function
        check_method = getattr(self, f"_{principle.check_function}", None)
        
        if check_method:
            return await check_method(action)
        else:
            # Default: no violation
            return {"violated": False}
    
    # Tier 1 Check Functions
    async def _check_no_data_deletion(self, action: Action) -> Dict:
        dangerous_actions = ["delete", "drop", "truncate", "purge", "destroy"]
        if any(d in action.action_type.lower() for d in dangerous_actions):
            return {
                "violated": True,
                "reason": "Data deletion actions require explicit human confirmation"
            }
        return {"violated": False}
    
    async def _check_minimum_replicas(self, action: Action) -> Dict:
        if action.action_type == "scale_service":
            target_replicas = action.parameters.get("replicas", 1)
            if target_replicas < 2 and action.parameters.get("critical", False):
                return {
                    "violated": True,
                    "reason": f"Cannot scale critical service below 2 replicas (requested: {target_replicas})"
                }
        return {"violated": False}
    
    async def _check_cascade_limit(self, action: Action) -> Dict:
        if len(action.affected_services) > 5:
            return {
                "violated": True,
                "reason": f"Action affects {len(action.affected_services)} services (limit: 5)"
            }
        return {"violated": False}
    
    async def _check_reversibility(self, action: Action) -> Dict:
        if not action.reversible:
            return {
                "violated": True,
                "reason": "Action is not reversible within 60 seconds"
            }
        return {"violated": False}
    
    async def _check_no_credential_exposure(self, action: Action) -> Dict:
        sensitive_keys = ["password", "secret", "token", "key", "credential"]
        for key, value in action.parameters.items():
            if any(s in key.lower() for s in sensitive_keys):
                return {
                    "violated": True,
                    "reason": f"Action contains sensitive parameter: {key}"
                }
        return {"violated": False}
    
    # Tier 2 Check Functions
    async def _check_minimal_intervention(self, action: Action) -> Dict:
        # This would check if there's a smaller action that could work
        # For now, just return no violation
        return {"violated": False, "warning": None}
    
    async def _check_evidence_based(self, action: Action) -> Dict:
        if not action.reasoning or len(action.reasoning) < 20:
            return {
                "violated": True,
                "reason": "Action lacks sufficient reasoning/evidence"
            }
        return {"violated": False}
    
    async def _check_historical_precedent(self, action: Action) -> Dict:
        # Would check graph memory for similar past actions
        return {"violated": False}
    
    async def _check_graceful_degradation(self, action: Action) -> Dict:
        if action.action_type in ["stop_service", "kill_process", "shutdown"]:
            return {
                "violated": True,
                "reason": "Prefer graceful degradation over complete shutdown"
            }
        return {"violated": False}
    
    async def _check_rate_limit(self, action: Action) -> Dict:
        # Check if same action was taken recently
        recent = [
            a for a in self._recent_actions
            if a["target"] == action.target_service
            and a["type"] == action.action_type
            and (datetime.utcnow() - a["timestamp"]).seconds < 300
        ]
        if len(recent) >= 3:
            return {
                "violated": True,
                "reason": f"Rate limit exceeded: {len(recent)} similar actions in last 5 minutes"
            }
        return {"violated": False}
    
    # Tier 3 Check Functions (informational)
    async def _check_outcome_tracking(self, action: Action) -> Dict:
        return {"violated": False, "warning": "Remember to track outcome"}
    
    async def _check_failure_analysis(self, action: Action) -> Dict:
        return {"violated": False}
    
    async def _check_pattern_reinforcement(self, action: Action) -> Dict:
        return {"violated": False}
```

---

## 8. Frontend Implementation

### 8.1 React Project Setup

```typescript
// frontend/src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
```

```typescript
// frontend/src/App.tsx
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import ChatPage from './pages/ChatPage'
import DashboardPage from './pages/DashboardPage'
import IncidentsPage from './pages/IncidentsPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/incidents" element={<IncidentsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Layout>
  )
}

export default App
```

### 8.2 Layout Component

```typescript
// frontend/src/components/Layout/Layout.tsx
import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  HomeIcon, 
  ChatBubbleLeftRightIcon, 
  ExclamationTriangleIcon,
  Cog6ToothIcon 
} from '@heroicons/react/24/outline'

interface LayoutProps {
  children: React.ReactNode
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Chat', href: '/chat', icon: ChatBubbleLeftRightIcon },
  { name: 'Incidents', href: '/incidents', icon: ExclamationTriangleIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  
  return (
    <div className="min-h-screen bg-gray-900">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-gray-800 border-r border-gray-700">
        <div className="flex items-center h-16 px-4 border-b border-gray-700">
          <span className="text-xl font-bold text-white">Constitutional AIOps</span>
        </div>
        
        <nav className="mt-4 px-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`
                  flex items-center px-4 py-3 mb-1 rounded-lg transition-colors
                  ${isActive 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }
                `}
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </Link>
            )
          })}
        </nav>
        
        {/* Model Status */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
          <ModelStatusIndicator />
        </div>
      </div>
      
      {/* Main Content */}
      <div className="pl-64">
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  )
}

function ModelStatusIndicator() {
  const [status, setStatus] = React.useState<any>(null)
  
  React.useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('/api/status/models')
        const data = await response.json()
        setStatus(data)
      } catch (error) {
        console.error('Failed to fetch model status:', error)
      }
    }
    
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [])
  
  if (!status) return null
  
  return (
    <div className="text-sm">
      <div className="flex items-center justify-between text-gray-400 mb-2">
        <span>Active Model</span>
        <span className={`px-2 py-0.5 rounded text-xs ${
          status.active_model === 'reasoning-agent' 
            ? 'bg-purple-500/20 text-purple-400' 
            : 'bg-green-500/20 text-green-400'
        }`}>
          {status.active_model === 'reasoning-agent' ? '14B' : '8B'}
        </span>
      </div>
      {status.seconds_until_swap !== null && (
        <div className="text-gray-500 text-xs">
          Swap in {status.seconds_until_swap}s
        </div>
      )}
    </div>
  )
}
```

### 8.3 Chat Page

```typescript
// frontend/src/pages/ChatPage.tsx
import React, { useState, useRef, useEffect } from 'react'
import { PaperAirplaneIcon, SparklesIcon } from '@heroicons/react/24/solid'
import { useWebSocket } from '../hooks/useWebSocket'

interface Message {
  role: 'user' | 'assistant'
  content: string
  thinking?: string
  timestamp: string
  model?: string
  latency_ms?: number
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const [enableThinking, setEnableThinking] = useState<boolean | null>(null)
  const [showThinking, setShowThinking] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const sessionId = React.useMemo(() => `session-${Date.now()}`, [])
  
  const { sendMessage, status, lastMessage } = useWebSocket(
    `ws://${window.location.hostname}:8000/api/chat/ws/${sessionId}`
  )
  
  // Handle incoming messages
  useEffect(() => {
    if (!lastMessage) return
    
    const data = JSON.parse(lastMessage)
    
    switch (data.type) {
      case 'status':
        if (data.content === 'thinking') {
          setIsThinking(true)
        }
        break
        
      case 'thinking':
        // Store thinking process
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last && last.role === 'assistant') {
            return [...prev.slice(0, -1), { ...last, thinking: data.content }]
          }
          return prev
        })
        break
        
      case 'response':
        setIsThinking(false)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.content,
          timestamp: new Date().toISOString(),
          model: data.model,
          latency_ms: data.latency_ms
        }])
        break
        
      case 'error':
        setIsThinking(false)
        // Show error
        break
    }
  }, [lastMessage])
  
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  
  const handleSend = () => {
    if (!input.trim() || status !== 'connected') return
    
    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }])
    
    // Send to WebSocket
    sendMessage(JSON.stringify({
      type: 'message',
      content: input,
      enable_thinking: enableThinking
    }))
    
    setInput('')
  }
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-gray-700">
        <h1 className="text-2xl font-bold text-white">AI Operations Chat</h1>
        
        <div className="flex items-center gap-4">
          {/* Thinking Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Thinking Mode:</span>
            <select
              value={enableThinking === null ? 'auto' : enableThinking ? 'on' : 'off'}
              onChange={(e) => {
                const val = e.target.value
                setEnableThinking(val === 'auto' ? null : val === 'on')
              }}
              className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm text-white"
            >
              <option value="auto">Auto</option>
              <option value="on">Always On</option>
              <option value="off">Always Off</option>
            </select>
          </div>
          
          {/* Show Thinking Toggle */}
          <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={showThinking}
              onChange={(e) => setShowThinking(e.target.checked)}
              className="rounded"
            />
            Show Thinking
          </label>
        </div>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            <SparklesIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Start a conversation with your AI operations assistant</p>
            <p className="text-sm mt-2">Ask about system status, investigate incidents, or get recommendations</p>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] rounded-lg px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-100'
              }`}
            >
              {/* Thinking Process */}
              {showThinking && message.thinking && (
                <div className="mb-3 p-2 bg-gray-900/50 rounded text-sm text-gray-400 border-l-2 border-purple-500">
                  <div className="font-semibold text-purple-400 mb-1">Thinking:</div>
                  <pre className="whitespace-pre-wrap">{message.thinking}</pre>
                </div>
              )}
              
              {/* Message Content */}
              <div className="whitespace-pre-wrap">{message.content}</div>
              
              {/* Metadata */}
              {message.role === 'assistant' && (
                <div className="mt-2 pt-2 border-t border-gray-700 flex items-center gap-3 text-xs text-gray-500">
                  {message.model && (
                    <span className="px-1.5 py-0.5 bg-gray-700 rounded">
                      {message.model}
                    </span>
                  )}
                  {message.latency_ms && (
                    <span>{message.latency_ms.toFixed(0)}ms</span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        
        {/* Thinking Indicator */}
        {isThinking && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-lg px-4 py-3">
              <div className="flex items-center gap-2 text-gray-400">
                <div className="animate-pulse">Thinking</div>
                <div className="flex gap-1">
                  <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="border-t border-gray-700 pt-4">
        <div className="flex items-end gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about system status, incidents, or get recommendations..."
            className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500"
            rows={2}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || status !== 'connected'}
            className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <PaperAirplaneIcon className="w-5 h-5" />
          </button>
        </div>
        
        {/* Connection Status */}
        <div className="mt-2 text-xs text-gray-500 flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            status === 'connected' ? 'bg-green-500' : 'bg-red-500'
          }`} />
          {status === 'connected' ? 'Connected' : 'Disconnected'}
        </div>
      </div>
    </div>
  )
}
```

### 8.4 WebSocket Hook

```typescript
// frontend/src/hooks/useWebSocket.ts
import { useState, useEffect, useCallback, useRef } from 'react'

type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

interface UseWebSocketReturn {
  sendMessage: (message: string) => void
  lastMessage: string | null
  status: WebSocketStatus
  reconnect: () => void
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [status, setStatus] = useState<WebSocketStatus>('connecting')
  const [lastMessage, setLastMessage] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url)
      
      ws.onopen = () => {
        setStatus('connected')
        console.log('WebSocket connected')
      }
      
      ws.onmessage = (event) => {
        setLastMessage(event.data)
      }
      
      ws.onclose = () => {
        setStatus('disconnected')
        console.log('WebSocket disconnected')
        
        // Auto-reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...')
          connect()
        }, 3000)
      }
      
      ws.onerror = (error) => {
        setStatus('error')
        console.error('WebSocket error:', error)
      }
      
      wsRef.current = ws
      
    } catch (error) {
      setStatus('error')
      console.error('Failed to create WebSocket:', error)
    }
  }, [url])
  
  useEffect(() => {
    connect()
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])
  
  const sendMessage = useCallback((message: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(message)
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])
  
  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    connect()
  }, [connect])
  
  return { sendMessage, lastMessage, status, reconnect }
}
```

---

## 9. AWS Deployment

### 9.1 AWS Setup Script

```bash
#!/bin/bash
# scripts/setup-aws.sh
# Setup script for AWS g4dn.xlarge instance

set -e

echo "=== Constitutional AIOps AWS Setup ==="

# Update system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Install basic tools
echo "Installing basic tools..."
sudo apt install -y \
    git \
    curl \
    wget \
    htop \
    nvtop \
    tmux \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nodejs \
    npm

# Install Docker
echo "Installing Docker..."
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install NVIDIA Container Toolkit
echo "Installing NVIDIA Container Toolkit..."
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker

# Install AWS CLI
echo "Installing AWS CLI..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf awscliv2.zip aws/

# Create project directory
echo "Setting up project directory..."
mkdir -p ~/constitutional-aiops
mkdir -p ~/constitutional-aiops/models

# Install vmtouch for model pre-caching
echo "Installing vmtouch..."
sudo apt install -y vmtouch

# Verify GPU
echo "Verifying GPU..."
nvidia-smi

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Clone your repository: git clone <repo> ~/constitutional-aiops"
echo "2. Download models: ./scripts/download-models.sh"
echo "3. Pre-cache models: ./scripts/precache-models.sh"
echo "4. Start services: docker-compose -f docker/docker-compose.gpu.yml up -d"
echo ""
echo "Remember to log out and back in for Docker group membership to take effect!"
```

### 9.2 Model Download Script

```bash
#!/bin/bash
# scripts/download-models.sh
# Download required models from Hugging Face

set -e

MODEL_DIR="${MODEL_DIR:-./models}"
mkdir -p "$MODEL_DIR"

echo "=== Downloading Models ==="

# Install huggingface_hub if not present
pip install huggingface_hub hf_transfer --quiet

# Enable fast transfers
export HF_HUB_ENABLE_HF_TRANSFER=1

echo "Downloading Qwen3-8B Q4_K_M..."
huggingface-cli download \
    bartowski/Qwen_Qwen3-8B-GGUF \
    Qwen_Qwen3-8B-Q4_K_M.gguf \
    --local-dir "$MODEL_DIR" \
    --local-dir-use-symlinks False

# Rename for consistency
mv "$MODEL_DIR/Qwen_Qwen3-8B-Q4_K_M.gguf" "$MODEL_DIR/qwen3-8b-q4_k_m.gguf" 2>/dev/null || true

echo "Downloading Qwen3-14B Q4_K_M..."
huggingface-cli download \
    bartowski/Qwen_Qwen3-14B-GGUF \
    Qwen_Qwen3-14B-Q4_K_M.gguf \
    --local-dir "$MODEL_DIR" \
    --local-dir-use-symlinks False

# Rename for consistency
mv "$MODEL_DIR/Qwen_Qwen3-14B-Q4_K_M.gguf" "$MODEL_DIR/qwen3-14b-q4_k_m.gguf" 2>/dev/null || true

echo ""
echo "=== Download Complete ==="
ls -lh "$MODEL_DIR"
```

### 9.3 Model Pre-cache Script

```bash
#!/bin/bash
# scripts/precache-models.sh
# Pre-cache models in RAM for fast swapping

set -e

MODEL_DIR="${MODEL_DIR:-./models}"

echo "=== Pre-caching Models in RAM ==="

# Check if vmtouch is available
if ! command -v vmtouch &> /dev/null; then
    echo "Installing vmtouch..."
    sudo apt install -y vmtouch
fi

# Pre-cache 14B model (the one that gets swapped in)
MODEL_14B="$MODEL_DIR/qwen3-14b-q4_k_m.gguf"

if [ -f "$MODEL_14B" ]; then
    echo "Pre-caching Qwen3-14B..."
    
    # Touch all pages to load into RAM
    vmtouch -t "$MODEL_14B"
    
    # Optionally lock in RAM (requires root or CAP_IPC_LOCK)
    # sudo vmtouch -l "$MODEL_14B"
    
    echo "14B model cached in RAM"
else
    echo "WARNING: 14B model not found at $MODEL_14B"
fi

# Show memory usage
echo ""
echo "Memory Status:"
free -h

echo ""
echo "Cache Status:"
vmtouch "$MODEL_DIR"/*.gguf 2>/dev/null || true
```

### 9.4 AWS Instance Management Scripts

```bash
#!/bin/bash
# scripts/aws-start.sh
# Start the GPU instance

INSTANCE_ID="${AWS_INSTANCE_ID:-i-xxxxxxxxxxxxxxxxx}"
REGION="${AWS_REGION:-us-east-1}"

echo "Starting instance $INSTANCE_ID..."
aws ec2 start-instances --instance-ids "$INSTANCE_ID" --region "$REGION"

echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo ""
echo "Instance is running!"
echo "Public IP: $PUBLIC_IP"
echo ""
echo "Connect with: ssh -i ~/.ssh/your-key.pem ubuntu@$PUBLIC_IP"
```

```bash
#!/bin/bash
# scripts/aws-stop.sh
# Stop the GPU instance (IMPORTANT - saves money!)

INSTANCE_ID="${AWS_INSTANCE_ID:-i-xxxxxxxxxxxxxxxxx}"
REGION="${AWS_REGION:-us-east-1}"

echo "Stopping instance $INSTANCE_ID..."
aws ec2 stop-instances --instance-ids "$INSTANCE_ID" --region "$REGION"

echo "Instance stopping. This saves ~$0.50/hour!"
```

```bash
#!/bin/bash
# scripts/deploy-aws.sh
# Deploy code to AWS instance

INSTANCE_IP="${1:-$AWS_INSTANCE_IP}"
KEY_FILE="${SSH_KEY_FILE:-~/.ssh/aiops-key.pem}"
PROJECT_DIR="constitutional-aiops"

if [ -z "$INSTANCE_IP" ]; then
    echo "Usage: ./deploy-aws.sh <instance-ip>"
    echo "Or set AWS_INSTANCE_IP environment variable"
    exit 1
fi

echo "Deploying to $INSTANCE_IP..."

# Sync code (excluding large files)
rsync -avz --progress \
    --exclude 'node_modules' \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude 'models/*.gguf' \
    --exclude '*.pyc' \
    -e "ssh -i $KEY_FILE" \
    . ubuntu@$INSTANCE_IP:~/$PROJECT_DIR/

echo ""
echo "Deployment complete!"
echo ""
echo "Next steps on the instance:"
echo "  cd ~/$PROJECT_DIR"
echo "  docker-compose -f docker/docker-compose.gpu.yml up -d"
```

---

## 10. Testing

### 10.1 Pytest Configuration

```python
# tests/conftest.py
"""
Pytest configuration and fixtures.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Generator

from src.agents.model_manager import ModelManager
from src.agents.fast_annotator import FastAnnotator
from src.agents.reasoning_agent import ReasoningAgent
from src.constitutional.validator import ConstitutionalValidator


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_model_manager():
    """Create a mock model manager."""
    mm = MagicMock(spec=ModelManager)
    mm.api_base = "http://localhost:8080/v1"
    mm.fast_model = "fast-agent"
    mm.reasoning_model = "reasoning-agent"
    mm.current_model = "fast-agent"
    mm.ensure_model = AsyncMock()
    mm.record_activity = AsyncMock()
    mm.get_status = AsyncMock(return_value={
        "status": "healthy",
        "active_model": "fast-agent"
    })
    return mm


@pytest.fixture
def mock_llm_response():
    """Standard mock LLM response."""
    return {
        "choices": [{
            "message": {
                "content": '{"anomaly_detected": true, "severity": "warning", "confidence": 0.85}'
            }
        }]
    }


@pytest.fixture
def fast_annotator(mock_model_manager):
    """Create a fast annotator with mocked dependencies."""
    return FastAnnotator(model_manager=mock_model_manager)


@pytest.fixture
def reasoning_agent(mock_model_manager):
    """Create a reasoning agent with mocked dependencies."""
    return ReasoningAgent(model_manager=mock_model_manager)


@pytest.fixture
def validator():
    """Create a constitutional validator."""
    return ConstitutionalValidator()


@pytest.fixture
def sample_telemetry():
    """Sample telemetry data for testing."""
    return {
        "logs": [
            {"timestamp": "2025-12-06T10:00:00Z", "level": "ERROR", "service": "nextcloud-app", "message": "Connection refused to database"},
            {"timestamp": "2025-12-06T10:00:01Z", "level": "ERROR", "service": "nextcloud-app", "message": "Failed to authenticate user"},
        ],
        "metrics": {
            "nextcloud-app": {"cpu_percent": 85, "memory_mb": 512, "request_latency_p99": 2500},
            "nextcloud-db": {"cpu_percent": 95, "memory_mb": 1024, "connections": 100}
        },
        "traces": [
            {"trace_id": "abc123", "service": "nextcloud-app", "duration_ms": 3500, "status": "error"}
        ]
    }
```

### 10.2 Unit Tests

```python
# tests/unit/test_constitutional.py
"""
Tests for Constitutional AI validator.
"""

import pytest
from src.constitutional.validator import (
    ConstitutionalValidator,
    Action,
    ValidationResult
)


class TestConstitutionalValidator:
    """Test the constitutional validator."""
    
    @pytest.mark.asyncio
    async def test_approve_high_confidence_safe_action(self, validator):
        """High confidence, safe action should be approved."""
        action = Action(
            action_type="restart_service",
            target_service="nextcloud-app",
            parameters={},
            confidence=0.95,
            reasoning="Service is unresponsive, restart should resolve",
            reversible=True,
            affected_services=["nextcloud-app"]
        )
        
        result = await validator.validate(action)
        
        assert result.result == ValidationResult.APPROVED
        assert len(result.violations) == 0
    
    @pytest.mark.asyncio
    async def test_reject_data_deletion(self, validator):
        """Data deletion should be rejected (Tier 1)."""
        action = Action(
            action_type="delete_database",
            target_service="nextcloud-db",
            parameters={"database": "nextcloud"},
            confidence=0.99,
            reasoning="Database corrupted",
            reversible=False,
            affected_services=["nextcloud-db"]
        )
        
        result = await validator.validate(action)
        
        assert result.result == ValidationResult.REJECTED
        assert any(v.principle_id == "P1.1" for v in result.violations)
    
    @pytest.mark.asyncio
    async def test_reject_cascade_action(self, validator):
        """Action affecting >5 services should be rejected."""
        action = Action(
            action_type="restart_service",
            target_service="core-service",
            parameters={},
            confidence=0.95,
            reasoning="Core service needs restart",
            reversible=True,
            affected_services=["svc1", "svc2", "svc3", "svc4", "svc5", "svc6"]
        )
        
        result = await validator.validate(action)
        
        assert result.result == ValidationResult.REJECTED
        assert any(v.principle_id == "P1.3" for v in result.violations)
    
    @pytest.mark.asyncio
    async def test_require_approval_medium_confidence(self, validator):
        """Medium confidence should require approval."""
        action = Action(
            action_type="scale_service",
            target_service="nextcloud-app",
            parameters={"replicas": 3},
            confidence=0.75,
            reasoning="High load detected",
            reversible=True,
            affected_services=["nextcloud-app"]
        )
        
        result = await validator.validate(action)
        
        assert result.result == ValidationResult.REQUIRES_APPROVAL
    
    @pytest.mark.asyncio
    async def test_reject_irreversible_action(self, validator):
        """Irreversible actions should be rejected."""
        action = Action(
            action_type="apply_migration",
            target_service="nextcloud-db",
            parameters={"migration": "v2.0"},
            confidence=0.95,
            reasoning="Apply schema migration",
            reversible=False,
            affected_services=["nextcloud-db"]
        )
        
        result = await validator.validate(action)
        
        assert result.result == ValidationResult.REJECTED
        assert any(v.principle_id == "P1.4" for v in result.violations)
```

```python
# tests/unit/test_model_manager.py
"""
Tests for Model Manager.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from src.agents.model_manager import ModelManager


class TestModelManager:
    """Test the model manager."""
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test model manager initialization."""
        mm = ModelManager(
            api_base="http://localhost:8080/v1",
            fast_model="fast-agent",
            reasoning_model="reasoning-agent",
            timeout_seconds=60
        )
        
        with patch.object(mm, '_client') as mock_client:
            mock_client.get = AsyncMock(return_value=AsyncMock(status_code=200))
            await mm.initialize()
        
        assert mm.current_model == "fast-agent"
    
    @pytest.mark.asyncio
    async def test_record_activity_switches_model(self, mock_model_manager):
        """Recording activity should ensure reasoning model is loaded."""
        mm = ModelManager(
            api_base="http://localhost:8080/v1",
            timeout_seconds=60
        )
        mm._client = AsyncMock()
        mm._client.post = AsyncMock(return_value=AsyncMock(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {"choices": [{"message": {"content": "pong"}}]}
        ))
        
        await mm.record_activity("chat")
        
        assert mm.last_activity is not None
        assert mm.activity_mode == "chat"
    
    @pytest.mark.asyncio
    async def test_get_status(self, mock_model_manager):
        """Test status reporting."""
        status = await mock_model_manager.get_status()
        
        assert "active_model" in status
        assert "status" in status
```

---

## Quick Reference

### Key Files to Create First
1. `CLAUDE.md` - Project instructions
2. `docs/CHECKLIST.md` - Progress tracking
3. `src/config.py` - Configuration
4. `src/main.py` - Entry point
5. `docker/docker-compose.local.yml` - Local development
6. `src/agents/model_manager.py` - Model management
7. `src/api/routes/chat.py` - Chat endpoint
8. `frontend/src/pages/ChatPage.tsx` - Chat UI

### Development Commands
```bash
# Local development
docker-compose -f docker/docker-compose.local.yml up -d
cd src && python main.py
cd frontend && npm run dev

# Testing
pytest tests/ -v

# AWS deployment
./scripts/aws-start.sh
./scripts/deploy-aws.sh
./scripts/precache-models.sh
docker-compose -f docker/docker-compose.gpu.yml up -d

# IMPORTANT: Stop instance when done!
./scripts/aws-stop.sh
```

### Cost Reminder
- AWS g4dn.xlarge Spot: ~$0.16-0.20/hour
- **ALWAYS** stop the instance when not in use
- Use `./scripts/aws-stop.sh` after each session

---

**End of Mega Prompt**

*Last Updated: 2025-12-06*
*Version: 0.1.0-alpha*
