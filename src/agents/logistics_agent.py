"""
Logistics Agent - Shipping feasibility assessment.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from .sql_generation_agent import SQLGenerationAgent
from .schema_retrieval_agent import SchemaRetrievalAgent
from src.utils.data_parsers import parse_shipping_timeline, extract_location_from_ip_helper
from src.config.prompts import LOGISTICS_AGENT_PROMPT


class LogisticsAgent(BaseAgent):
    """
    Logistics Agent handles shipping feasibility assessment.
    
    Responsibilities:
    - Calculate shipping lead times between locations
    - Determine if redistribution is possible before expiry
    - Account for customs clearance and delivery buffers
    - Assess logistical feasibility for proposed actions
    """
    
    def __init__(self, llm=None):
        super().__init__("LogisticsAgent", llm)
        self.sql_agent = SQLGenerationAgent(llm)
        self.schema_agent = SchemaRetrievalAgent(llm)
        self.minimum_buffer_days = 30  # Minimum days after delivery for usage
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute logistics operations.
        
        Args:
            input_data: {
                "operation": str,  # "check_feasibility", "get_timeline", "calculate_window"
                "filters": Dict,  # Query filters
                "expiry_date": str,  # Expiry date (YYYY-MM-DD)
                "destination_country": str  # Destination country
            }
            
        Returns:
            {
                "success": bool,
                "operation": str,
                "check_result": str,  # "PASS", "CONDITIONAL", "FAIL"
                "findings": Dict,  # Detailed findings
                "citations": List[Dict],  # Data sources
                "summary": str
            }
        """
        try:
            operation = input_data.get("operation", "check_feasibility")
            filters = input_data.get("filters", {})
            expiry_date = input_data.get("expiry_date")
            destination_country = input_data.get("destination_country")
            
            # Get relevant schemas
            schema_result = self.schema_agent.execute({
                "query": f"shipping logistics {operation}",
                "specific_tables": ["ip_shipping_timelines_report", "distribution_order_report"]
            })
            
            # Execute operation
            if operation == "check_feasibility":
                result = self._check_shipping_feasibility(
                    expiry_date, destination_country, filters, schema_result
                )
            elif operation == "get_timeline":
                result = self._get_shipping_timeline(destination_country, schema_result)
            elif operation == "calculate_window":
                result = self._calculate_available_window(
                    expiry_date, destination_country, schema_result
                )
            else:
                result = {
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }
            
            self.log_execution(input_data, result)
            return result
        
        except Exception as e:
            return self.handle_error(e, input_data)
    
    def _check_shipping_feasibility(
        self,
        expiry_date: str,
        destination_country: str,
        filters: Dict[str, Any],
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if shipping is feasible before expiry.
        
        Args:
            expiry_date: Expiry date (YYYY-MM-DD)
            destination_country: Destination country
            filters: Additional filters
            schema_result: Schema information
            
        Returns:
            Dictionary with feasibility assessment
        """
        if not expiry_date or not destination_country:
            return {
                "success": False,
                "error": "expiry_date and destination_country required",
                "operation": "check_feasibility"
            }
        
        # Get shipping timeline
        timeline_result = self._get_shipping_timeline(destination_country, schema_result)
        
        if not timeline_result["success"]:
            return {
                "success": True,
                "check_result": "UNKNOWN",
                "finding": f"Unable to determine shipping timeline for {destination_country}",
                "operation": "check_feasibility"
            }
        
        shipping_days = timeline_result.get("shipping_days", 0)
        
        # Calculate days until expiry
        try:
            expiry_dt = datetime.strptime(expiry_date, "%Y-%m-%d")
            days_until_expiry = (expiry_dt - datetime.now()).days
        except:
            return {
                "success": False,
                "error": f"Invalid expiry_date format: {expiry_date}. Use YYYY-MM-DD",
                "operation": "check_feasibility"
            }
        
        # Calculate available window
        available_window = days_until_expiry - shipping_days
        
        # Determine feasibility
        if available_window >= self.minimum_buffer_days:
            check_result = "PASS"
            finding = f"✓ Shipping feasible. Available window: {available_window} days (exceeds {self.minimum_buffer_days}-day minimum)"
        elif available_window > 0:
            check_result = "CONDITIONAL"
            finding = f"⚠ Shipping possible but tight. Available window: {available_window} days (below {self.minimum_buffer_days}-day recommended minimum)"
        else:
            check_result = "FAIL"
            finding = f"✗ Shipping NOT feasible. Product expires in {days_until_expiry} days, shipping takes {shipping_days} days"
        
        # Calculate delivery date
        delivery_date = (datetime.now() + timedelta(days=shipping_days)).strftime("%Y-%m-%d")
        
        citations = timeline_result.get("citations", [])
        
        return {
            "success": True,
            "operation": "check_feasibility",
            "check_result": check_result,
            "finding": finding,
            "destination_country": destination_country,
            "expiry_date": expiry_date,
            "days_until_expiry": days_until_expiry,
            "shipping_days": shipping_days,
            "available_window": available_window,
            "minimum_buffer_days": self.minimum_buffer_days,
            "estimated_delivery_date": delivery_date,
            "calculation": f"{days_until_expiry} days until expiry - {shipping_days} days shipping = {available_window} days available",
            "citations": citations,
            "summary_text": finding
        }
    
    def _get_shipping_timeline(
        self,
        destination_country: str,
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get shipping timeline for destination country.
        
        Args:
            destination_country: Destination country
            schema_result: Schema information
            
        Returns:
            Dictionary with shipping timeline
        """
        if not destination_country:
            return {
                "success": False,
                "error": "destination_country required"
            }
        
        # Query shipping timelines
        sql_result = self.sql_agent.execute({
            "intent": f"Get shipping timeline for {destination_country}",
            "schemas": schema_result["formatted_schemas"],
            "filters": {"country": destination_country},
            "limit": 1
        })
        
        if not sql_result["success"]:
            return {
                "success": False,
                "error": sql_result.get("error", "Query failed"),
                "operation": "get_timeline"
            }
        
        timelines = sql_result["data"]
        
        if not timelines:
            return {
                "success": False,
                "error": f"No shipping timeline found for {destination_country}",
                "operation": "get_timeline"
            }
        
        timeline_record = timelines[0]
        timeline_text = timeline_record.get("ip_timeline", "")
        
        # Parse shipping days from text
        shipping_days = parse_shipping_timeline(timeline_text)
        
        if shipping_days == 0:
            self.logger.warning(f"Could not parse shipping days from: {timeline_text}")
        
        citations = [{
            "table": "ip_shipping_timelines_report",
            "columns": ["ip_helper", "ip_timeline", "country_name"],
            "query_date": datetime.now().isoformat(),
            "destination_country": destination_country,
            "timeline_text": timeline_text
        }]
        
        return {
            "success": True,
            "operation": "get_timeline",
            "destination_country": destination_country,
            "shipping_days": shipping_days,
            "timeline_text": timeline_text,
            "ip_helper": timeline_record.get("ip_helper"),
            "citations": citations
        }
    
    def _calculate_available_window(
        self,
        expiry_date: str,
        destination_country: str,
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate available window after shipping.
        
        Args:
            expiry_date: Expiry date (YYYY-MM-DD)
            destination_country: Destination country
            schema_result: Schema information
            
        Returns:
            Dictionary with window calculation
        """
        # Get shipping timeline
        timeline_result = self._get_shipping_timeline(destination_country, schema_result)
        
        if not timeline_result["success"]:
            return timeline_result
        
        shipping_days = timeline_result.get("shipping_days", 0)
        
        # Calculate days until expiry
        try:
            expiry_dt = datetime.strptime(expiry_date, "%Y-%m-%d")
            days_until_expiry = (expiry_dt - datetime.now()).days
        except:
            return {
                "success": False,
                "error": f"Invalid expiry_date format: {expiry_date}. Use YYYY-MM-DD"
            }
        
        # Calculate available window
        available_window = days_until_expiry - shipping_days
        
        # Calculate dates
        current_date = datetime.now().strftime("%Y-%m-%d")
        delivery_date = (datetime.now() + timedelta(days=shipping_days)).strftime("%Y-%m-%d")
        
        citations = timeline_result.get("citations", [])
        
        return {
            "success": True,
            "operation": "calculate_window",
            "current_date": current_date,
            "expiry_date": expiry_date,
            "days_until_expiry": days_until_expiry,
            "shipping_days": shipping_days,
            "estimated_delivery_date": delivery_date,
            "available_window": available_window,
            "minimum_buffer_days": self.minimum_buffer_days,
            "meets_minimum": available_window >= self.minimum_buffer_days,
            "calculation_breakdown": {
                "step_1": f"Days until expiry: {days_until_expiry}",
                "step_2": f"Shipping time: {shipping_days} days",
                "step_3": f"Available window: {days_until_expiry} - {shipping_days} = {available_window} days",
                "step_4": f"Minimum buffer: {self.minimum_buffer_days} days",
                "result": "PASS" if available_window >= self.minimum_buffer_days else "FAIL"
            },
            "citations": citations
        }
