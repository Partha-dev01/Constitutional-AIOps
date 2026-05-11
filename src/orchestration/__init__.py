"""
Constitutional AIOps - Orchestration Package

LangGraph-based orchestration for the dual-agent pipeline.
Implements the Talker-Reasoner architecture (arXiv:2410.08328)
as a state machine using LangGraph StateGraph.

Pipeline: annotate (System 1) -> evaluate -> reasoning (System 2) -> validate -> plan
"""

from src.orchestration.graph import IncidentState, build_incident_graph
from src.orchestration.state_machine import IncidentStateMachine

__all__ = [
    "IncidentState",
    "build_incident_graph",
    "IncidentStateMachine",
]
