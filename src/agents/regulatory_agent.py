"""
Regulatory Agent - Compliance verification.
"""
from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent
from .sql_generation_agent import SQLGenerationAgent
from .schema_retrieval_agent import SchemaRetrievalAgent
from src.config.prompts import REGULATORY_AGENT_PROMPT


class RegulatoryAgent(BaseAgent):
    """
    Regulatory Agent handles compliance verification.
    
    Responsibilities:
    - Check shelf-life extension approval status by country
    - Verify re-evaluation history for batches/materials
    - Validate regulatory submission status
    - Assess regulatory feasibility for proposed actions
    """
    
    def __init__(self, llm=None):
        super().__init__("RegulatoryAgent", llm)
        self.sql_agent = SQLGenerationAgent(llm)
        self.schema_agent = SchemaRetrievalAgent(llm)
        
        # Country to health authority mapping
        self.country_authority_map = {
            "Germany": "EMA",
            "France": "EMA",
            "Spain": "EMA",
            "Italy": "EMA",
            "UK": "MHRA",
            "United Kingdom": "MHRA",
            "USA": "FDA",
            "United States": "FDA",
            "Japan": "PMDA",
            "China": "NMPA"
        }
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute regulatory compliance operations.
        
        Args:
            input_data: {
                "operation": str,  # "check_extension", "verify_approval", "get_history"
                "filters": Dict,  # Query filters (batch_id, country, trial, etc.)
                "country": str  # Country for regulatory check
            }
            
        Returns:
            {
                "success": bool,
                "operation": str,
                "check_result": str,  # "PASS", "FAIL", "CONDITIONAL"
                "findings": List[Dict],  # Detailed findings
                "citations": List[Dict],  # Data sources
                "summary": str
            }
        """
        try:
            operation = input_data.get("operation", "check_extension")
            filters = input_data.get("filters", {})
            country = input_data.get("country")
            
            # Get relevant schemas
            schema_result = self.schema_agent.execute({
                "query": f"regulatory {operation} compliance",
                "specific_tables": ["rim", "re_evaluation", "material_country_requirements"]
            })
            
            # Execute operation
            if operation == "check_extension":
                result = self._check_extension_feasibility(filters, country, schema_result)
            elif operation == "verify_approval":
                result = self._verify_regulatory_approval(filters, country, schema_result)
            elif operation == "get_history":
                result = self._get_reevaluation_history(filters, schema_result)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }
            
            self.log_execution(input_data, result)
            return result
        
        except Exception as e:
            return self.handle_error(e, input_data)
    
    def _check_extension_feasibility(
        self,
        filters: Dict[str, Any],
        country: str,
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check shelf-life extension feasibility (Technical + Regulatory).
        
        Args:
            filters: Must include batch_id or lot_number
            country: Target country
            schema_result: Schema information
            
        Returns:
            Dictionary with feasibility assessment
        """
        batch_id = filters.get("batch_id") or filters.get("lot_number")
        
        if not batch_id:
            return {
                "success": False,
                "error": "batch_id or lot_number required",
                "operation": "check_extension"
            }
        
        # Check 1: Technical Feasibility (Re-evaluation History)
        technical_check = self._check_technical_feasibility(batch_id, schema_result)
        
        # Check 2: Regulatory Approval
        regulatory_check = self._verify_regulatory_approval(filters, country, schema_result)
        
        # Determine overall result
        if technical_check["result"] == "PASS" and regulatory_check["check_result"] == "PASS":
            overall_result = "PASS"
            summary = f"✓ Shelf-life extension feasible for Batch {batch_id} in {country}"
        elif technical_check["result"] == "FAIL" or regulatory_check["check_result"] == "FAIL":
            overall_result = "FAIL"
            summary = f"✗ Shelf-life extension NOT feasible for Batch {batch_id} in {country}"
        else:
            overall_result = "CONDITIONAL"
            summary = f"⚠ Shelf-life extension conditionally feasible for Batch {batch_id} in {country}"
        
        return {
            "success": True,
            "operation": "check_extension",
            "batch_id": batch_id,
            "country": country,
            "check_result": overall_result,
            "technical_check": technical_check,
            "regulatory_check": regulatory_check,
            "summary_text": summary,
            "citations": technical_check.get("citations", []) + regulatory_check.get("citations", [])
        }
    
    def _check_technical_feasibility(
        self,
        batch_id: str,
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check technical feasibility via re-evaluation history.
        
        Args:
            batch_id: Batch/Lot number
            schema_result: Schema information
            
        Returns:
            Dictionary with technical check result
        """
        # Query re-evaluation history
        sql_result = self.sql_agent.execute({
            "intent": f"Get re-evaluation history for batch {batch_id}",
            "schemas": schema_result["formatted_schemas"],
            "filters": {"lot_number": batch_id}
        })
        
        if not sql_result["success"]:
            return {
                "result": "UNKNOWN",
                "error": sql_result.get("error"),
                "finding": "Unable to check re-evaluation history"
            }
        
        reevaluations = sql_result["data"]
        
        # Filter for extensions only
        extensions = [r for r in reevaluations if r.get("request_type", "").lower() == "extension"]
        
        # Typical limit: 2-3 extensions
        max_extensions = 3
        extension_count = len(extensions)
        remaining_extensions = max(0, max_extensions - extension_count)
        
        if extension_count == 0:
            result = "PASS"
            finding = f"Batch {batch_id} has not been extended before. {max_extensions} extensions available."
        elif extension_count < max_extensions:
            result = "PASS"
            finding = f"Batch {batch_id} extended {extension_count} time(s). {remaining_extensions} extension(s) remaining."
        else:
            result = "FAIL"
            finding = f"Batch {batch_id} already extended {extension_count} times. Maximum limit reached."
        
        # Get extension dates
        extension_dates = [r.get("created") for r in extensions if r.get("created")]
        
        citations = [{
            "table": "re_evaluation",
            "columns": ["id", "lot_number", "request_type", "created", "sample_status"],
            "query_date": datetime.now().isoformat(),
            "batch_id": batch_id,
            "extensions_found": extension_count
        }]
        
        return {
            "result": result,
            "finding": finding,
            "extension_count": extension_count,
            "remaining_extensions": remaining_extensions,
            "extension_dates": extension_dates,
            "extensions": extensions,
            "citations": citations
        }
    
    def _verify_regulatory_approval(
        self,
        filters: Dict[str, Any],
        country: str,
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify regulatory approval for extension in specific country.
        
        Args:
            filters: Query filters (clinical_study, ly_number, etc.)
            country: Target country
            schema_result: Schema information
            
        Returns:
            Dictionary with regulatory check result
        """
        if not country:
            return {
                "check_result": "UNKNOWN",
                "finding": "Country not specified",
                "success": True
            }
        
        # Map country to health authority
        health_authority = self.country_authority_map.get(country, "EMA")
        
        # Add health authority to filters
        regulatory_filters = filters.copy()
        regulatory_filters["country"] = country
        
        # Query RIM table
        sql_result = self.sql_agent.execute({
            "intent": f"Check regulatory approval for {country}",
            "schemas": schema_result["formatted_schemas"],
            "filters": regulatory_filters
        })
        
        if not sql_result["success"]:
            return {
                "check_result": "UNKNOWN",
                "error": sql_result.get("error"),
                "finding": f"Unable to check regulatory status for {country}",
                "success": True
            }
        
        approvals = sql_result["data"]
        
        # Filter for approved submissions
        approved = [a for a in approvals if a.get("status_v", "").lower() == "approved"]
        
        if approved:
            latest_approval = max(approved, key=lambda x: x.get("approved_date_c", "1900-01-01"))
            result = "PASS"
            finding = f"Extension approved in {country} by {health_authority} on {latest_approval.get('approved_date_c')}"
            regulatory_id = latest_approval.get("ly_number_c", "N/A")
        elif approvals:
            # Has submissions but not approved
            result = "CONDITIONAL"
            finding = f"Extension submission exists for {country} but not yet approved. Status: {approvals[0].get('status_v')}"
            regulatory_id = approvals[0].get("ly_number_c", "N/A")
        else:
            result = "FAIL"
            finding = f"No extension approval found for {country} ({health_authority})"
            regulatory_id = None
        
        citations = [{
            "table": "rim",
            "columns": ["name_v", "health_authority_division_c", "status_v", "approved_date_c", "ly_number_c"],
            "query_date": datetime.now().isoformat(),
            "country": country,
            "health_authority": health_authority,
            "approvals_found": len(approved)
        }]
        
        return {
            "success": True,
            "check_result": result,
            "finding": finding,
            "country": country,
            "health_authority": health_authority,
            "regulatory_id": regulatory_id,
            "approvals": approved,
            "citations": citations
        }
    
    def _get_reevaluation_history(
        self,
        filters: Dict[str, Any],
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get complete re-evaluation history.
        
        Args:
            filters: Query filters
            schema_result: Schema information
            
        Returns:
            Dictionary with re-evaluation history
        """
        # Query re-evaluation table
        sql_result = self.sql_agent.execute({
            "intent": "Get re-evaluation history",
            "schemas": schema_result["formatted_schemas"],
            "filters": filters,
            "limit": 50
        })
        
        if not sql_result["success"]:
            return {
                "success": False,
                "error": sql_result.get("error", "Query failed"),
                "operation": "get_history"
            }
        
        reevaluations = sql_result["data"]
        
        # Categorize by type
        extensions = [r for r in reevaluations if r.get("request_type", "").lower() == "extension"]
        retests = [r for r in reevaluations if r.get("request_type", "").lower() == "retest"]
        
        citations = [{
            "table": "re_evaluation",
            "columns": ["id", "created", "request_type", "sample_status", "lot_number"],
            "query_date": datetime.now().isoformat(),
            "row_count": len(reevaluations)
        }]
        
        return {
            "success": True,
            "operation": "get_history",
            "data": reevaluations,
            "total_records": len(reevaluations),
            "extensions": extensions,
            "retests": retests,
            "extension_count": len(extensions),
            "retest_count": len(retests),
            "citations": citations
        }
