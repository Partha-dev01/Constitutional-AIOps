"""
Constitutional AIOps - Reasoning Agent

Complex reasoning agent using Qwen3-14B Q4_K_M.
Always loaded on port 8082 (TTL: -1, never unload).

Responsibilities:
- Root cause analysis (RCA) for complex incidents
- Remediation planning with step-by-step actions
- Human chat interaction for operator communication
- Multi-service dependency analysis

Performance Targets:
- Latency: <200ms (p99)
- Context: 4K tokens
- Accuracy: Prioritized over speed

Modes:
- RCA Mode: Deep analysis of incidents
- Chat Mode: Interactive conversation with operators
- Planning Mode: Remediation step generation
"""

import json
import logging
from typing import Any, Optional

from src.agents.base_agent import AgentResponse, AgentRole, BaseAgent
from src.agents.model_router import ModelRouter

logger = logging.getLogger(__name__)


# System prompts for different modes
RCA_SYSTEM_PROMPT = """You are an expert Site Reliability Engineer performing root cause analysis.

Given telemetry data and incident context, you must:
1. Identify the root cause of the issue
2. Trace the causal chain (what led to what)
3. Assess impact scope (affected services, users)
4. Provide confidence in your analysis
5. Suggest remediation steps

Consider:
- Service dependencies
- Recent changes/deployments
- Historical patterns
- Resource constraints

Respond in JSON format:
{
    "root_cause": "Primary cause description",
    "causal_chain": ["Event 1", "Event 2", "..."],
    "impact": {
        "services": ["service1", "service2"],
        "severity": "critical|high|medium|low",
        "users_affected": "estimate"
    },
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of your analysis",
    "remediation_steps": [
        {"action": "step1", "risk": "low|medium|high"},
        {"action": "step2", "risk": "low|medium|high"}
    ],
    "prevention": "How to prevent recurrence"
}
"""

CHAT_SYSTEM_PROMPT = """You are an AI operations assistant helping infrastructure operators.

You have access to:
- Telemetry data (logs, metrics, traces)
- Incident history
- Service dependency graphs
- Remediation capabilities

When helping operators:
1. Be concise but thorough
2. Explain technical details clearly
3. Suggest actionable next steps
4. Always prioritize safety
5. Escalate when uncertain

Remember: You operate under Constitutional AI principles. Never take actions that 
could cause data loss, cascade failures, or security breaches without explicit approval.
"""

PLANNING_SYSTEM_PROMPT = """You are a remediation planning specialist.

Given an incident and root cause analysis, create a detailed remediation plan.

Your plan must:
1. Minimize service disruption
2. Be reversible when possible
3. Include validation steps
4. Consider dependencies
5. Estimate time and risk for each step

Respond in JSON format:
{
    "plan_name": "Brief description",
    "total_steps": N,
    "estimated_duration": "X minutes",
    "overall_risk": "low|medium|high",
    "rollback_available": true/false,
    "steps": [
        {
            "order": 1,
            "action": "Description",
            "command": "Actual command or null",
            "duration": "X seconds",
            "risk": "low|medium|high",
            "requires_approval": true/false,
            "validation": "How to verify success"
        }
    ],
    "success_criteria": "How to know the issue is resolved",
    "rollback_plan": "Steps to undo if needed"
}
"""


class ReasoningAgent(BaseAgent):
    """
    Complex reasoning agent for deep analysis and planning.
    
    Uses Qwen3-14B Q4_K_M model running on port 8082.
    Supports multiple modes: RCA, Chat, Planning.
    """
    
    def __init__(self, model_router: Optional[ModelRouter] = None):
        """
        Initialize the reasoning agent.
        
        Args:
            model_router: ModelRouter instance (creates new if not provided)
        """
        super().__init__(AgentRole.REASONING)
        self.model_router = model_router or ModelRouter()
    
    def get_system_prompt(self, mode: str = "chat") -> str:
        """
        Get the system prompt for the specified mode.
        
        Args:
            mode: "rca" | "chat" | "planning"
        """
        prompts = {
            "rca": RCA_SYSTEM_PROMPT,
            "chat": CHAT_SYSTEM_PROMPT,
            "planning": PLANNING_SYSTEM_PROMPT,
        }
        return prompts.get(mode, CHAT_SYSTEM_PROMPT)
    
    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """
        Process input and return reasoned response.
        
        Args:
            input_data: Dictionary containing:
                - mode: "rca" | "chat" | "planning"
                - query: The question or data to analyze
                - context: Additional context (incident data, etc.)
                - enable_thinking: Whether to use extended thinking
                
        Returns:
            AgentResponse with analysis and confidence
        """
        mode = input_data.get("mode", "chat")
        query = input_data.get("query", "")
        context = input_data.get("context", "")
        enable_thinking = input_data.get("enable_thinking", False)
        
        # Build prompt
        prompt = self._build_prompt(mode, query, context)
        
        try:
            # Get completion from reasoning agent
            response = await self.model_router.reasoning_completion(
                prompt=prompt,
                max_tokens=2048,
                temperature=0.3,
                enable_thinking=enable_thinking,
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Parse based on mode
            if mode in ("rca", "planning"):
                parsed = self._parse_json_response(content)
                confidence = parsed.get("confidence", 0.7)
                return AgentResponse(
                    content=content,
                    confidence=confidence,
                    confidence_level=self.calculate_confidence_level(confidence),
                    reasoning=parsed.get("reasoning", ""),
                    suggested_action=self._extract_action(parsed, mode),
                    metadata=parsed,
                )
            else:
                # Chat mode - return as-is
                return AgentResponse(
                    content=content,
                    confidence=0.8,  # Default confidence for chat
                    confidence_level=self.calculate_confidence_level(0.8),
                    reasoning=None,
                    suggested_action=None,
                    metadata={"mode": "chat"},
                )
                
        except Exception as e:
            self.logger.error(f"Reasoning failed: {e}")
            return AgentResponse(
                content=f"Analysis failed: {str(e)}",
                confidence=0.0,
                confidence_level=self.calculate_confidence_level(0.0),
                suggested_action="escalate",
                metadata={"error": str(e)},
            )
    
    async def analyze_rca(
        self,
        incident_data: dict[str, Any],
        enable_thinking: bool = True,
    ) -> AgentResponse:
        """
        Perform root cause analysis on an incident.
        
        Args:
            incident_data: Incident information and telemetry
            enable_thinking: Enable extended thinking mode
            
        Returns:
            AgentResponse with RCA results
        """
        return await self.process({
            "mode": "rca",
            "query": "Perform root cause analysis",
            "context": json.dumps(incident_data, indent=2),
            "enable_thinking": enable_thinking,
        })
    
    async def create_plan(
        self,
        root_cause: str,
        incident_context: dict[str, Any],
    ) -> AgentResponse:
        """
        Create a remediation plan based on RCA.
        
        Args:
            root_cause: Identified root cause
            incident_context: Context about the incident
            
        Returns:
            AgentResponse with remediation plan
        """
        return await self.process({
            "mode": "planning",
            "query": f"Create remediation plan for: {root_cause}",
            "context": json.dumps(incident_context, indent=2),
            "enable_thinking": True,
        })
    
    async def chat(
        self,
        message: str,
        conversation_history: Optional[list[dict]] = None,
    ) -> AgentResponse:
        """
        Handle chat interaction with operator.
        
        Args:
            message: User's message
            conversation_history: Previous messages in conversation
            
        Returns:
            AgentResponse with chat reply
        """
        context = ""
        if conversation_history:
            context = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-5:]  # Last 5 messages
            ])
        
        return await self.process({
            "mode": "chat",
            "query": message,
            "context": context,
            "enable_thinking": False,  # Chat doesn't need thinking mode
        })
    
    def _build_prompt(self, mode: str, query: str, context: str) -> str:
        """Build prompt with system context."""
        system_prompt = self.get_system_prompt(mode)
        
        prompt = f"""{system_prompt}

User Query: {query}
"""
        if context:
            prompt += f"\nContext:\n{context}"
        
        return prompt
    
    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parse JSON from model response."""
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
        except json.JSONDecodeError:
            return {"raw_content": content, "confidence": 0.5}
    
    def _extract_action(self, parsed: dict, mode: str) -> Optional[str]:
        """Extract suggested action from parsed response."""
        if mode == "rca":
            steps = parsed.get("remediation_steps", [])
            if steps:
                return steps[0].get("action")
        elif mode == "planning":
            steps = parsed.get("steps", [])
            if steps:
                return steps[0].get("action")
        return None


__all__ = [
    "ReasoningAgent",
    "RCA_SYSTEM_PROMPT",
    "CHAT_SYSTEM_PROMPT", 
    "PLANNING_SYSTEM_PROMPT",
]
