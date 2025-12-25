"""
Demand Forecasting Agent - Enrollment analysis and demand projection.
"""
from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent
from .sql_generation_agent import SQLGenerationAgent
from .schema_retrieval_agent import SchemaRetrievalAgent
from src.utils.data_parsers import (
    parse_monthly_enrollment,
    calculate_weekly_enrollment,
    calculate_8week_demand,
    calculate_stockout_date
)
from src.config.prompts import DEMAND_FORECASTING_AGENT_PROMPT


class DemandForecastingAgent(BaseAgent):
    """
    Demand Forecasting Agent handles enrollment analysis and demand projection.
    
    Responsibilities:
    - Calculate average weekly enrollment from historical data
    - Project future demand (typically 8 weeks forward)
    - Predict stockout dates based on current inventory and demand trends
    - Identify potential shortfalls by country and material
    """
    
    def __init__(self, llm=None):
        super().__init__("DemandForecastingAgent", llm)
        self.sql_agent = SQLGenerationAgent(llm)
        self.schema_agent = SchemaRetrievalAgent(llm)
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute demand forecasting operations.
        
        Args:
            input_data: {
                "operation": str,  # "calculate_shortfall", "predict_demand", "get_enrollment"
                "filters": Dict,  # Query filters
                "weeks_forward": int,  # Projection period (default: 8)
                "current_inventory": Dict  # Optional: current stock levels
            }
            
        Returns:
            {
                "success": bool,
                "operation": str,
                "data": List[Dict],  # Forecast data
                "shortfalls": List[Dict],  # Predicted shortfalls
                "citations": List[Dict],  # Data sources
                "summary": str
            }
        """
        try:
            operation = input_data.get("operation", "calculate_shortfall")
            filters = input_data.get("filters", {})
            weeks_forward = input_data.get("weeks_forward", 8)
            current_inventory = input_data.get("current_inventory", {})
            
            # Get relevant schemas
            schema_result = self.schema_agent.execute({
                "query": f"enrollment demand forecasting {operation}",
                "specific_tables": ["enrollment_rate_report", "country_level_enrollment_report"]
            })
            
            # Execute operation
            if operation == "calculate_shortfall":
                result = self._calculate_shortfall(filters, weeks_forward, current_inventory, schema_result)
            elif operation == "predict_demand":
                result = self._predict_demand(filters, weeks_forward, schema_result)
            elif operation == "get_enrollment":
                result = self._get_enrollment_data(filters, schema_result)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }
            
            self.log_execution(input_data, result)
            return result
        
        except Exception as e:
            return self.handle_error(e, input_data)
    
    def _calculate_shortfall(
        self,
        filters: Dict[str, Any],
        weeks_forward: int,
        current_inventory: Dict[str, Any],
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate predicted shortfalls by comparing demand with inventory.
        
        Args:
            filters: Query filters
            weeks_forward: Weeks to project forward
            current_inventory: Current stock levels by trial/country
            schema_result: Schema information
            
        Returns:
            Dictionary with shortfall predictions
        """
        # Get enrollment data
        sql_result = self.sql_agent.execute({
            "intent": "Get recent enrollment data for demand forecasting",
            "schemas": schema_result["formatted_schemas"],
            "filters": filters
        })
        
        if not sql_result["success"]:
            return {
                "success": False,
                "error": sql_result.get("error", "Query failed"),
                "operation": "calculate_shortfall"
            }
        
        enrollment_data = sql_result["data"]
        
        # Calculate shortfalls
        shortfalls = []
        
        for enrollment_record in enrollment_data:
            trial_alias = enrollment_record.get("trial_alias")
            country = enrollment_record.get("country")
            months_string = enrollment_record.get("months_jan_feb_dec", "")
            
            # Parse enrollment and calculate demand
            weekly_avg = calculate_weekly_enrollment(months_string, recent_months=1)
            projected_demand = weekly_avg * weeks_forward
            
            # Get current stock for this trial/country
            stock_key = f"{trial_alias}_{country}"
            current_stock = current_inventory.get(stock_key, 0)
            
            # Calculate shortfall
            shortfall = current_stock - projected_demand
            
            if shortfall < 0:
                # Predict stockout date
                stockout_date = calculate_stockout_date(
                    current_stock,
                    weekly_avg,
                    datetime.now().strftime('%Y-%m-%d')
                )
                
                shortfalls.append({
                    "trial_alias": trial_alias,
                    "country": country,
                    "avg_weekly_enrollment": round(weekly_avg, 2),
                    "projected_demand": round(projected_demand, 2),
                    "current_stock": current_stock,
                    "shortfall": round(shortfall, 2),
                    "estimated_stockout_date": stockout_date,
                    "severity": "CRITICAL" if shortfall < -50 else "HIGH"
                })
        
        # Generate summary
        summary = self._generate_shortfall_summary(shortfalls)
        
        citations = [{
            "table": "enrollment_rate_report",
            "columns": ["trial_alias", "country", "months_jan_feb_dec"],
            "query_date": datetime.now().isoformat(),
            "calculation": f"{weeks_forward}-week demand projection",
            "row_count": len(enrollment_data)
        }]
        
        return {
            "success": True,
            "operation": "calculate_shortfall",
            "shortfalls": shortfalls,
            "total_shortfalls": len(shortfalls),
            "citations": citations,
            "summary_text": summary,
            "projection_weeks": weeks_forward
        }
    
    def _predict_demand(
        self,
        filters: Dict[str, Any],
        weeks_forward: int,
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict future demand based on enrollment trends.
        
        Args:
            filters: Query filters
            weeks_forward: Weeks to project forward
            schema_result: Schema information
            
        Returns:
            Dictionary with demand predictions
        """
        # Get enrollment data
        sql_result = self.sql_agent.execute({
            "intent": "Get enrollment data for demand prediction",
            "schemas": schema_result["formatted_schemas"],
            "filters": filters
        })
        
        if not sql_result["success"]:
            return {
                "success": False,
                "error": sql_result.get("error", "Query failed"),
                "operation": "predict_demand"
            }
        
        enrollment_data = sql_result["data"]
        
        # Calculate predictions
        predictions = []
        
        for record in enrollment_data:
            trial_alias = record.get("trial_alias")
            country = record.get("country")
            site = record.get("site")
            months_string = record.get("months_jan_feb_dec", "")
            
            # Parse and calculate
            monthly_data = parse_monthly_enrollment(months_string)
            weekly_avg = calculate_weekly_enrollment(months_string, recent_months=1)
            projected_demand = weekly_avg * weeks_forward
            
            predictions.append({
                "trial_alias": trial_alias,
                "country": country,
                "site": site,
                "monthly_enrollment": monthly_data,
                "avg_weekly_enrollment": round(weekly_avg, 2),
                "projected_demand_weeks": weeks_forward,
                "projected_demand": round(projected_demand, 2)
            })
        
        citations = [{
            "table": "enrollment_rate_report",
            "columns": ["trial_alias", "country", "site", "months_jan_feb_dec"],
            "query_date": datetime.now().isoformat(),
            "row_count": len(enrollment_data)
        }]
        
        return {
            "success": True,
            "operation": "predict_demand",
            "predictions": predictions,
            "total_predictions": len(predictions),
            "citations": citations,
            "projection_weeks": weeks_forward
        }
    
    def _get_enrollment_data(
        self,
        filters: Dict[str, Any],
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get raw enrollment data.
        
        Args:
            filters: Query filters
            schema_result: Schema information
            
        Returns:
            Dictionary with enrollment data
        """
        # Get enrollment data
        sql_result = self.sql_agent.execute({
            "intent": "Get enrollment data",
            "schemas": schema_result["formatted_schemas"],
            "filters": filters,
            "limit": 100
        })
        
        if not sql_result["success"]:
            return {
                "success": False,
                "error": sql_result.get("error", "Query failed"),
                "operation": "get_enrollment"
            }
        
        enrollment_data = sql_result["data"]
        
        # Parse monthly data for each record
        for record in enrollment_data:
            months_string = record.get("months_jan_feb_dec", "")
            if months_string:
                record["monthly_data_parsed"] = parse_monthly_enrollment(months_string)
                record["total_enrollment"] = sum(record["monthly_data_parsed"])
        
        citations = [{
            "table": "enrollment_rate_report",
            "columns": ["trial_alias", "country", "site", "year", "months_jan_feb_dec"],
            "query_date": datetime.now().isoformat(),
            "row_count": len(enrollment_data)
        }]
        
        return {
            "success": True,
            "operation": "get_enrollment",
            "data": enrollment_data,
            "total_records": len(enrollment_data),
            "citations": citations
        }
    
    def _generate_shortfall_summary(self, shortfalls: List[Dict]) -> str:
        """Generate human-readable shortfall summary."""
        if not shortfalls:
            return "No shortfalls predicted for the projection period."
        
        critical = [s for s in shortfalls if s.get("severity") == "CRITICAL"]
        high = [s for s in shortfalls if s.get("severity") == "HIGH"]
        
        summary_parts = [f"Predicted {len(shortfalls)} shortfalls:"]
        
        if critical:
            summary_parts.append(f"  - {len(critical)} CRITICAL (shortfall > 50 units)")
        if high:
            summary_parts.append(f"  - {len(high)} HIGH (shortfall < 50 units)")
        
        # Add earliest stockout
        earliest = min(shortfalls, key=lambda x: x.get("estimated_stockout_date", "9999-12-31"))
        summary_parts.append(f"\nEarliest predicted stockout: {earliest['country']} on {earliest['estimated_stockout_date']}")
        
        return "\n".join(summary_parts)
