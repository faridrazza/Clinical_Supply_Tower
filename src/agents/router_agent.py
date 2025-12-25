"""
Router Agent - Entry point and workflow classifier.
"""
import re
from typing import Dict, Any, List
from .base_agent import BaseAgent
from src.config.prompts import ROUTER_AGENT_PROMPT


class RouterAgent(BaseAgent):
    """
    Router Agent classifies requests and routes to appropriate agents.
    
    Responsibilities:
    - Determine if request is Workflow A or Workflow B
    - Route to appropriate specialized agents
    - Never queries database directly
    """
    
    def __init__(self, llm=None):
        super().__init__("RouterAgent", llm)
        
        # Workflow A keywords
        self.workflow_a_keywords = [
            "scheduled", "daily check", "monitoring", "watchdog", 
            "run supply check", "expiry alert", "shortfall", "autonomous"
        ]
        
        # Workflow B keywords
        self.workflow_b_keywords = [
            "can we", "should we", "what is", "show me", "has", 
            "extend", "batch", "material", "country", "feasibility"
        ]
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute routing logic.
        
        Args:
            input_data: {
                "query": str,  # User query or trigger type
                "context": dict  # Optional context
            }
            
        Returns:
            {
                "workflow": "A" or "B",
                "intent": str,
                "required_agents": List[str],
                "clarification_needed": bool,
                "clarification_question": str (optional)
            }
        """
        try:
            query = input_data.get("query", "").lower()
            context = input_data.get("context", {})
            
            # Classify workflow
            workflow = self._classify_workflow(query)
            
            # Determine intent and required agents
            if workflow == "A":
                result = self._route_workflow_a(query, context)
            else:
                result = self._route_workflow_b(query, context)
            
            self.log_execution(input_data, result)
            return result
        
        except Exception as e:
            return self.handle_error(e, input_data)
    
    def _classify_workflow(self, query: str) -> str:
        """
        Classify query as Workflow A or B.
        
        Args:
            query: User query (lowercase)
            
        Returns:
            "A" or "B"
        """
        # Check for Workflow A keywords
        workflow_a_score = sum(1 for keyword in self.workflow_a_keywords if keyword in query)
        
        # Check for Workflow B keywords
        workflow_b_score = sum(1 for keyword in self.workflow_b_keywords if keyword in query)
        
        # Workflow A has priority for scheduled/monitoring requests
        if any(keyword in query for keyword in ["scheduled", "daily", "monitoring", "watchdog"]):
            return "A"
        
        # Otherwise, use score
        if workflow_a_score > workflow_b_score:
            return "A"
        else:
            return "B"
    
    def _route_workflow_a(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route Workflow A (Supply Watchdog).
        
        Returns routing information for autonomous monitoring.
        """
        return {
            "workflow": "A",
            "intent": "Autonomous supply chain monitoring - expiry alerts and shortfall predictions",
            "required_agents": [
                "SchemaRetrievalAgent",
                "InventoryAgent",
                "DemandForecastingAgent",
                "SynthesisAgent"
            ],
            "clarification_needed": False,
            "execution_mode": "autonomous",
            "output_format": "json"
        }
    
    def _route_workflow_b(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route Workflow B (Scenario Strategist).
        
        Determines which agents are needed based on query type.
        """
        required_agents = ["SchemaRetrievalAgent"]
        intent = "Conversational query"
        
        # Detect query type - check for outstanding FIRST (highest priority)
        is_outstanding_query = any(word in query for word in ["outstanding", "pending"])
        is_extension_query = any(word in query for word in ["extend", "extension", "shelf-life", "expiry"])
        is_purchase_query = any(word in query for word in ["purchase", "requirement", "procurement", "order", "supplier"])
        is_inventory_query = any(word in query for word in ["stock", "inventory", "quantity", "available"])
        is_demand_query = any(word in query for word in ["demand", "enrollment", "forecast", "predict"])
        is_regulatory_query = any(word in query for word in ["approval", "regulatory", "compliance", "approved"])
        is_logistics_query = any(word in query for word in ["shipping", "timeline", "transport"])  # Removed "delivery" to avoid conflict with outstanding
        
        # Outstanding shipments query - query the outstanding_site_shipment_status_report table directly
        if is_outstanding_query:
            intent = "Outstanding shipments inquiry"
            required_agents.extend([
                "InventoryAgent",  # Use InventoryAgent to query the report table
                "SynthesisAgent"
            ])
        
        # Shelf-life extension query (complex - needs all checks)
        elif is_extension_query:
            intent = "Shelf-life extension feasibility assessment"
            required_agents.extend([
                "InventoryAgent",
                "RegulatoryAgent",
                "LogisticsAgent",
                "SynthesisAgent"
            ])
        
        # Purchase/Procurement query - use InventoryAgent to query purchase_requirement table
        elif is_purchase_query:
            intent = "Purchase requirement inquiry"
            required_agents.extend([
                "InventoryAgent",  # Will query purchase_requirement table via SchemaRetrievalAgent
                "SynthesisAgent"
            ])
        
        # Simple inventory query
        elif is_inventory_query:
            intent = "Inventory level inquiry"
            required_agents.extend([
                "InventoryAgent",
                "SynthesisAgent"
            ])
        
        # Demand/enrollment query
        elif is_demand_query:
            intent = "Demand forecasting inquiry"
            required_agents.extend([
                "DemandForecastingAgent",
                "SynthesisAgent"
            ])
        
        # Regulatory query
        elif is_regulatory_query:
            intent = "Regulatory compliance inquiry"
            required_agents.extend([
                "RegulatoryAgent",
                "SynthesisAgent"
            ])
        
        # Logistics query (but not outstanding shipments)
        elif is_logistics_query:
            intent = "Logistics and shipping inquiry"
            required_agents.extend([
                "LogisticsAgent",
                "SynthesisAgent"
            ])
        
        # General query - use inventory as default
        else:
            intent = "General supply chain inquiry"
            required_agents.extend([
                "InventoryAgent",
                "SynthesisAgent"
            ])
        
        return {
            "workflow": "B",
            "intent": intent,
            "required_agents": required_agents,
            "clarification_needed": False,
            "execution_mode": "conversational",
            "output_format": "natural_language"
        }
    
    def extract_entities(self, query: str) -> Dict[str, Any]:
        """
        Extract entities from query (batch IDs, countries, materials, etc.).
        
        Args:
            query: User query
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        # Extract batch/lot IDs (pattern: LOT-XXXXXXXX)
        batch_pattern = r'(LOT-\d+|Batch\s*#?\s*\d+)'
        batches = re.findall(batch_pattern, query, re.IGNORECASE)
        if batches:
            entities["batches"] = batches
        
        # Extract material IDs (pattern: MAT-XXXXX)
        material_pattern = r'(MAT-\d+|Material\s+\w+)'
        materials = re.findall(material_pattern, query, re.IGNORECASE)
        if materials:
            entities["materials"] = materials
        
        # Extract trial IDs (pattern: CT-XXXX-XXX)
        trial_pattern = r'(CT-\d+-[A-Z]+)'
        trials = re.findall(trial_pattern, query, re.IGNORECASE)
        if trials:
            entities["trials"] = trials
        
        # Extract countries (common country names)
        common_countries = [
            "Germany", "France", "USA", "UK", "China", "Japan", "India",
            "Canada", "Australia", "Brazil", "Mexico", "Spain", "Italy"
        ]
        for country in common_countries:
            if country.lower() in query.lower():
                entities.setdefault("countries", []).append(country)
        
        return entities
