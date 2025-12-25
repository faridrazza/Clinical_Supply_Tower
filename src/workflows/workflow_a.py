"""
Workflow A: Supply Watchdog - Autonomous Monitoring

This workflow runs autonomously to identify:
1. Expiring batches within 90 days
2. Predicted stock shortfalls based on enrollment trends
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from src.agents import (
    RouterAgent,
    SchemaRetrievalAgent,
    InventoryAgent,
    DemandForecastingAgent,
    SynthesisAgent
)

logger = logging.getLogger(__name__)


class SupplyWatchdogWorkflow:
    """
    Supply Watchdog Workflow orchestrates autonomous monitoring.
    
    Flow:
    1. Router classifies as Workflow A
    2. Schema Retrieval gets relevant tables
    3. Inventory Agent checks expiring batches
    4. Demand Forecasting Agent calculates shortfalls
    5. Synthesis Agent generates JSON output
    """
    
    def __init__(self, llm=None):
        """Initialize workflow with all required agents."""
        self.llm = llm
        self.router = RouterAgent(llm)
        self.schema_retrieval = SchemaRetrievalAgent(llm)
        self.inventory = InventoryAgent(llm)
        self.demand = DemandForecastingAgent(llm)
        self.synthesis = SynthesisAgent(llm)
        self.logger = logging.getLogger("workflow.supply_watchdog")
    
    def execute(self, trigger_type: str = "manual") -> Dict[str, Any]:
        """
        Execute Supply Watchdog workflow.
        
        Args:
            trigger_type: "manual" or "scheduled"
            
        Returns:
            Dictionary with JSON output and metadata
        """
        try:
            self.logger.info(f"Starting Supply Watchdog workflow (trigger: {trigger_type})")
            
            # Step 1: Route request
            routing_result = self.router.execute({
                "query": "scheduled daily supply watchdog monitoring",
                "context": {"trigger_type": trigger_type}
            })
            
            if routing_result.get("workflow") != "A":
                self.logger.warning("Router did not classify as Workflow A")
            
            # Step 2: Get relevant schemas
            schema_result = self.schema_retrieval.execute({
                "query": "expiry alerts and demand forecasting",
                "workflow": "A"
            })
            
            # Step 3: Check expiring batches (parallel execution simulation)
            self.logger.info("Checking expiring batches...")
            inventory_result = self.inventory.execute({
                "operation": "check_expiry",
                "filters": {},
                "days_threshold": 90,
                "schema_result": schema_result  # Pass schema for dynamic query generation
            })
            
            # Step 4: Calculate demand shortfalls
            self.logger.info("Calculating demand shortfalls...")
            
            # First, get current inventory for shortfall calculation
            current_inventory = self._get_current_inventory_summary(inventory_result)
            
            # Then calculate shortfalls
            demand_result = self.demand.execute({
                "operation": "calculate_shortfall",
                "filters": {},
                "weeks_forward": 8,
                "current_inventory": current_inventory
            })
            
            # Step 5: Synthesize results into JSON with LLM reasoning
            self.logger.info("Synthesizing results with LLM reasoning...")
            synthesis_result = self.synthesis.execute({
                "workflow": "A",
                "agent_outputs": {
                    "inventory": inventory_result,
                    "demand": demand_result
                },
                "output_format": "json",
                "use_llm_reasoning": True  # Enable LLM reasoning for better analysis
            })
            
            # Add metadata
            result = {
                "success": True,
                "workflow": "A",
                "trigger_type": trigger_type,
                "execution_time": datetime.now().isoformat(),
                "output": synthesis_result.get("output"),
                "json_string": synthesis_result.get("json_string"),
                "summary": synthesis_result.get("summary"),
                "citations": synthesis_result.get("citations", []),
                "agent_results": {
                    "routing": routing_result,
                    "inventory": inventory_result,
                    "demand": demand_result,
                    "synthesis": synthesis_result
                }
            }
            
            self.logger.info(f"Supply Watchdog completed successfully. "
                           f"Expiring batches: {result['summary'].get('expiring_batches', 0)}, "
                           f"Shortfalls: {result['summary'].get('shortfalls', 0)}")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Supply Watchdog workflow failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "workflow": "A",
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time": datetime.now().isoformat()
            }
    
    def _get_current_inventory_summary(self, inventory_result: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract current inventory summary from inventory result.
        
        Args:
            inventory_result: Result from Inventory Agent
            
        Returns:
            Dictionary mapping trial_country to stock levels
        """
        current_inventory = {}
        
        if inventory_result.get("success") and inventory_result.get("data"):
            for item in inventory_result["data"]:
                trial = item.get("trial_name", "Unknown")
                country = item.get("location", "Unknown")
                stock = item.get("quantity", item.get("received_packages", 0))
                
                key = f"{trial}_{country}"
                current_inventory[key] = current_inventory.get(key, 0) + stock
        
        return current_inventory
    
    def get_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of workflow execution.
        
        Args:
            result: Workflow execution result
            
        Returns:
            Summary string
        """
        if not result.get("success"):
            return f"Workflow failed: {result.get('error', 'Unknown error')}"
        
        summary = result.get("summary", {})
        expiring = summary.get("expiring_batches", 0)
        critical = summary.get("critical_batches", 0)
        shortfalls = summary.get("shortfalls", 0)
        
        return (
            f"Supply Watchdog Report:\n"
            f"  - Total expiring batches: {expiring} ({critical} critical)\n"
            f"  - Predicted shortfalls: {shortfalls}\n"
            f"  - Execution time: {result.get('execution_time')}"
        )
