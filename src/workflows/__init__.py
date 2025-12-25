"""
Workflow orchestration for Clinical Supply Chain Control Tower.

Two main workflows:
1. Workflow A: Supply Watchdog (Autonomous Monitoring)
2. Workflow B: Scenario Strategist (Conversational Assistant)

Main entry point: WorkflowOrchestrator or get_orchestrator()
"""
from .workflow_a import SupplyWatchdogWorkflow
from .workflow_b_v2_openai import ScenarioStrategistWorkflowV2OpenAI
from .orchestrator import WorkflowOrchestrator, get_orchestrator

__all__ = [
    "SupplyWatchdogWorkflow",
    "ScenarioStrategistWorkflowV2OpenAI",
    "WorkflowOrchestrator",
    "get_orchestrator",
]
