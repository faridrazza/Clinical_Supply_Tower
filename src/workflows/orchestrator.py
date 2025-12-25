"""
Main orchestrator for Clinical Supply Chain Control Tower workflows.

This module provides a unified interface to execute both workflows.
"""
import logging
from typing import Dict, Any, Optional

from .workflow_a import SupplyWatchdogWorkflow
from .workflow_b_v2_openai import ScenarioStrategistWorkflowV2OpenAI

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Main orchestrator that manages both workflows.
    
    Provides a unified interface for:
    - Workflow A: Supply Watchdog (autonomous monitoring)
    - Workflow B: Scenario Strategist (conversational queries)
    """
    
    def __init__(self, llm=None):
        """
        Initialize orchestrator with both workflows.
        
        Args:
            llm: Language model instance (optional)
        """
        self.llm = llm
        self.workflow_a = SupplyWatchdogWorkflow(llm)
        self.workflow_b = ScenarioStrategistWorkflowV2OpenAI(llm)
        self.logger = logging.getLogger("orchestrator")
    
    def run_supply_watchdog(self, trigger_type: str = "manual") -> Dict[str, Any]:
        """
        Run Supply Watchdog workflow (Workflow A).
        
        Args:
            trigger_type: "manual" or "scheduled"
            
        Returns:
            Dictionary with monitoring results and JSON output
        """
        self.logger.info(f"Running Supply Watchdog (trigger: {trigger_type})")
        return self.workflow_a.execute(trigger_type)
    
    def run_scenario_strategist(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run Scenario Strategist workflow (Workflow B).
        
        Args:
            query: User query
            context: Optional context from previous interactions
            
        Returns:
            Dictionary with response and citations
        """
        self.logger.info(f"Running Scenario Strategist for query: {query}")
        return self.workflow_b.execute(query, context)
    
    def check_shelf_life_extension(
        self,
        batch_id: str,
        country: str
    ) -> Dict[str, Any]:
        """
        Specialized method for shelf-life extension feasibility check.
        
        This is a convenience method for the most common Workflow B use case.
        
        Args:
            batch_id: Batch/Lot number
            country: Target country
            
        Returns:
            Dictionary with feasibility assessment
        """
        self.logger.info(f"Checking shelf-life extension: {batch_id} for {country}")
        query = f"Can we extend the expiry of Batch {batch_id} for {country}?"
        return self.workflow_b.execute(query)
    
    def get_workflow_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of workflow execution.
        
        Args:
            result: Workflow execution result
            
        Returns:
            Summary string
        """
        workflow = result.get("workflow")
        
        if workflow == "A":
            return self.workflow_a.get_summary(result)
        elif workflow == "B":
            return result.get("response", "No response available")
        else:
            return "Unknown workflow"
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all components.
        
        Returns:
            Dictionary with health status
        """
        health = {
            "orchestrator": "healthy",
            "workflow_a": "healthy",
            "workflow_b": "healthy",
            "agents": {}
        }
        
        try:
            # Check Workflow A agents
            health["agents"]["router"] = "healthy" if self.workflow_a.router else "missing"
            health["agents"]["inventory"] = "healthy" if self.workflow_a.inventory else "missing"
            health["agents"]["demand"] = "healthy" if self.workflow_a.demand else "missing"
            health["agents"]["synthesis"] = "healthy" if self.workflow_a.synthesis else "missing"
            
            # Check Workflow B agents
            health["agents"]["regulatory"] = "healthy" if self.workflow_b.regulatory else "missing"
            health["agents"]["logistics"] = "healthy" if self.workflow_b.logistics else "missing"
            
            health["status"] = "healthy"
            health["message"] = "All components operational"
        
        except Exception as e:
            health["status"] = "unhealthy"
            health["message"] = f"Health check failed: {str(e)}"
            self.logger.error(f"Health check failed: {str(e)}")
        
        return health


# Global orchestrator instance (singleton pattern)
_orchestrator_instance = None


def get_orchestrator(llm=None) -> WorkflowOrchestrator:
    """
    Get or create global orchestrator instance.
    
    Args:
        llm: Language model instance (optional)
        
    Returns:
        WorkflowOrchestrator instance
    """
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        _orchestrator_instance = WorkflowOrchestrator(llm)
    
    return _orchestrator_instance
