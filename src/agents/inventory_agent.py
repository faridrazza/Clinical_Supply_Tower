"""
Inventory Agent - Stock and expiry management.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent
from .sql_generation_agent import SQLGenerationAgent
from .schema_retrieval_agent import SchemaRetrievalAgent
from src.utils.data_parsers import classify_expiry_severity
from src.config.prompts import INVENTORY_AGENT_PROMPT

logger = logging.getLogger(__name__)


class InventoryAgent(BaseAgent):
    """
    Inventory Agent manages stock and expiry tracking.
    
    Responsibilities:
    - Check inventory levels by location/material
    - Identify expiring batches within time windows
    - Calculate available vs allocated stock
    - Provide accurate inventory status with data citations
    """
    
    def __init__(self, llm=None):
        super().__init__("InventoryAgent", llm)
        self.sql_agent = SQLGenerationAgent(llm)
        self.schema_agent = SchemaRetrievalAgent(llm)
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute inventory operations.
        
        Args:
            input_data: {
                "operation": str,  # "check_expiry", "get_stock", "find_batch", "check_outstanding", "get_purchase_requirements"
                "filters": Dict,  # Query filters
                "days_threshold": int,  # For expiry checks (default: 90)
                "schema_result": Dict  # Optional: pre-retrieved schemas
            }
            
        Returns:
            {
                "success": bool,
                "operation": str,
                "data": List[Dict],  # Inventory data
                "citations": List[Dict],  # Data sources
                "summary": str  # Human-readable summary
            }
        """
        try:
            operation = input_data.get("operation", "get_stock")
            filters = input_data.get("filters", {})
            days_threshold = input_data.get("days_threshold", 90)
            schema_result = input_data.get("schema_result")
            
            # Get relevant schemas if not provided
            if not schema_result:
                # Determine which table to use based on operation
                if operation == "check_outstanding":
                    table = "outstanding_site_shipment_status_report"
                elif operation == "get_purchase_requirements":
                    table = "purchase_requirement"
                else:
                    table = "available_inventory_report"
                
                schema_result = self.schema_agent.execute({
                    "query": f"inventory {operation}",
                    "specific_tables": [table]
                })
            
            # Execute operation
            if operation == "check_expiry":
                result = self._check_expiring_batches(filters, days_threshold, schema_result)
            elif operation == "find_batch":
                result = self._find_batch(filters, schema_result)
            elif operation == "check_outstanding":
                result = self._check_outstanding_shipments(filters, schema_result)
            elif operation == "get_purchase_requirements":
                result = self._get_purchase_requirements(filters, schema_result)
            elif operation == "get_stock":
                result = self._get_stock_levels(filters, schema_result)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }
            
            self.log_execution(input_data, result)
            return result
        
        except Exception as e:
            return self.handle_error(e, input_data)
    
    def _check_expiring_batches(
        self,
        filters: Dict[str, Any],
        days_threshold: int,
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check for ALLOCATED/RESERVED batches expiring within threshold.
        
        Per assignment: "Identify reserved batches (Allocated Materials) that are 
        expiring in ≤ 90 days. Group them by criticality."
        
        Uses: allocated_materials_to_orders JOIN batch_master for expiry dates.
        
        Args:
            filters: Query filters (location, trial_name, etc.)
            days_threshold: Days threshold (default: 90)
            schema_result: Schema information
            
        Returns:
            Dictionary with expiring allocated batches
        """
        from src.tools.database_tools import run_sql_query
        
        # Query allocated materials joined with batch_master for expiry dates
        # This is the correct approach per assignment requirements
        expiry_query = f"""
            SELECT 
                a.material_component_batch as batch_id,
                a.material_component as material_id,
                a.material_comp_description as material,
                a.trial_alias,
                a.order_status,
                a.order_quantity as quantity,
                a.plant_desc as location,
                b.expiration_date_shelf_life as expiry_date,
                b.adjusted_expiration_date,
                CASE 
                    WHEN b.expiration_date_shelf_life IS NOT NULL 
                    THEN (b.expiration_date_shelf_life::date - CURRENT_DATE)
                    ELSE NULL
                END as days_remaining
            FROM allocated_materials_to_orders a
            LEFT JOIN batch_master b 
                ON a.material_component_batch = b.batch_number
            WHERE b.expiration_date_shelf_life IS NOT NULL
              AND (b.expiration_date_shelf_life::date - CURRENT_DATE) <= {days_threshold}
              AND (b.expiration_date_shelf_life::date - CURRENT_DATE) >= 0
            ORDER BY days_remaining ASC
            LIMIT 100
        """
        
        sql_result = run_sql_query(expiry_query)
        
        if not sql_result.get("success"):
            # Fallback to available_inventory_report if join fails
            logger.warning("Allocated materials query failed, falling back to available_inventory_report")
            return self._check_expiring_batches_fallback(filters, days_threshold, schema_result)
        
        batches = sql_result.get("data", [])
        
        # Classify by severity per assignment:
        # CRITICAL <30 days, HIGH 30-60 days, MEDIUM 60-90 days
        critical = []
        high = []
        medium = []
        
        for batch in batches:
            days = batch.get("days_remaining", 999)
            if days < 30:
                batch["severity"] = "CRITICAL"
                critical.append(batch)
            elif days < 60:
                batch["severity"] = "HIGH"
                high.append(batch)
            else:
                batch["severity"] = "MEDIUM"
                medium.append(batch)
        
        # Generate summary
        summary = self._generate_expiry_summary(critical, high, medium)
        
        # Create citations - note we're using allocated_materials per assignment
        citations = [{
            "table": "allocated_materials_to_orders",
            "joined_with": "batch_master",
            "columns": ["material_component_batch", "trial_alias", "order_quantity", "expiration_date_shelf_life"],
            "query_date": datetime.now().isoformat(),
            "row_count": len(batches),
            "note": "Reserved/allocated batches per assignment requirement"
        }]
        
        return {
            "success": True,
            "operation": "check_expiry",
            "data": batches,
            "summary": {
                "total": len(batches),
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium)
            },
            "batches_by_severity": {
                "CRITICAL": critical,
                "HIGH": high,
                "MEDIUM": medium
            },
            "citations": citations,
            "summary_text": summary
        }
    
    def _check_expiring_batches_fallback(
        self,
        filters: Dict[str, Any],
        days_threshold: int,
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fallback method using available_inventory_report if allocated materials query fails.
        """
        # Build intent with clear requirements
        intent = f"""
        Find all pharmaceutical batches expiring within {days_threshold} days.
        Return: lot number, trial name, location, expiry date, quantity, and days remaining.
        Sort by days remaining (closest to expiry first).
        Include severity classification (CRITICAL <30 days, HIGH 30-60, MEDIUM 60-90).
        """
        
        # Generate and execute SQL query
        sql_result = self.sql_agent.execute({
            "intent": intent,
            "schemas": schema_result.get("formatted_schemas", ""),
            "filters": filters,
            "limit": 100
        })
        
        if not sql_result["success"]:
            return {
                "success": False,
                "error": sql_result.get("error", "Query failed"),
                "operation": "check_expiry"
            }
        
        # Process results
        batches = sql_result["data"]
        
        # Classify by severity
        critical = [b for b in batches if b.get("severity") == "CRITICAL"]
        high = [b for b in batches if b.get("severity") == "HIGH"]
        medium = [b for b in batches if b.get("severity") == "MEDIUM"]
        
        # Generate summary
        summary = self._generate_expiry_summary(critical, high, medium)
        
        # Create citations
        citations = [{
            "table": "available_inventory_report",
            "columns": ["trial_name", "location", "lot", "expiry_date", "received_packages"],
            "query_date": datetime.now().isoformat(),
            "row_count": len(batches),
            "note": "Fallback - using available inventory instead of allocated materials"
        }]
        
        return {
            "success": True,
            "operation": "check_expiry",
            "data": batches,
            "summary": {
                "total": len(batches),
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium)
            },
            "batches_by_severity": {
                "CRITICAL": critical,
                "HIGH": high,
                "MEDIUM": medium
            },
            "citations": citations,
            "summary_text": summary
        }
    
    def _find_batch(
        self,
        filters: Dict[str, Any],
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Find batch information - works with or without specific batch_id.
        If no batch_id provided, returns all batches sorted by expiry.
        """
        batch_id = filters.get("batch_id") or filters.get("lot")
        
        # Generate and execute SQL query
        sql_result = self.sql_agent.execute({
            "intent": f"Find batch {batch_id if batch_id else 'information'}",
            "schemas": schema_result["formatted_schemas"],
            "filters": {"batch_id": batch_id} if batch_id else {}
        })
        
        if not sql_result["success"]:
            return {
                "success": False,
                "error": sql_result.get("error", "Query failed"),
                "operation": "find_batch"
            }
        
        batches = sql_result["data"]
        
        if not batches:
            return {
                "success": True,
                "operation": "find_batch",
                "found": False,
                "batch_id": batch_id,
                "message": f"Batch {batch_id if batch_id else 'data'} not found in available inventory"
            }
        
        # Calculate days until expiry for each location
        for batch in batches:
            if batch.get("expiry_date"):
                try:
                    expiry_date = datetime.strptime(str(batch["expiry_date"]), "%Y-%m-%d")
                    days_remaining = (expiry_date - datetime.now()).days
                    batch["days_remaining"] = days_remaining
                    batch["severity"] = classify_expiry_severity(days_remaining)
                except:
                    pass
        
        citations = [{
            "table": "available_inventory_report",
            "columns": ["lot", "trial_name", "location", "expiry_date", "received_packages"],
            "query_date": datetime.now().isoformat(),
            "batch_id": batch_id if batch_id else "all"
        }]
        
        return {
            "success": True,
            "operation": "find_batch",
            "found": True,
            "batch_id": batch_id if batch_id else "all_batches",
            "data": batches,
            "locations": len(set(b.get("location") for b in batches if b.get("location"))),
            "citations": citations
        }
    
    def _get_stock_levels(
        self,
        filters: Dict[str, Any],
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get current stock levels.
        
        Args:
            filters: Query filters
            schema_result: Schema information
            
        Returns:
            Dictionary with stock information
        """
        # Generate and execute SQL query
        sql_result = self.sql_agent.execute({
            "intent": "Get current stock levels",
            "schemas": schema_result["formatted_schemas"],
            "filters": filters,
            "limit": 100
        })
        
        if not sql_result["success"]:
            return {
                "success": False,
                "error": sql_result.get("error", "Query failed"),
                "operation": "get_stock"
            }
        
        inventory = sql_result["data"]
        
        # Calculate totals
        total_received = sum(item.get("received_packages", 0) for item in inventory)
        total_shipped = sum(item.get("shipped_packages", 0) for item in inventory)
        
        citations = [{
            "table": "available_inventory_report",
            "columns": ["trial_name", "location", "received_packages", "shipped_packages"],
            "query_date": datetime.now().isoformat(),
            "row_count": len(inventory)
        }]
        
        return {
            "success": True,
            "operation": "get_stock",
            "data": inventory,
            "summary": {
                "total_items": len(inventory),
                "total_received": total_received,
                "total_shipped": total_shipped,
                "net_available": total_received - total_shipped
            },
            "citations": citations
        }
    
    def _check_outstanding_shipments(
        self,
        filters: Dict[str, Any],
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check for outstanding shipments by site.
        
        Args:
            filters: Query filters (optional)
            schema_result: Schema information
            
        Returns:
            Dictionary with outstanding shipments
        """
        # Generate and execute SQL query with explicit table name
        sql_result = self.sql_agent.execute({
            "intent": "Query the outstanding_site_shipment_status_report table. Find all outstanding shipments by site with days outstanding. Return: site_number, country, shipment_#, days_outstanding, trial_alias, package_description, package_count. Sort by days_outstanding DESC (longest outstanding first). This table tracks shipments that are pending delivery.",
            "schemas": schema_result.get("formatted_schemas", ""),
            "filters": filters,
            "limit": 100
        })
        
        if not sql_result["success"]:
            return {
                "success": False,
                "error": sql_result.get("error", "Query failed"),
                "operation": "check_outstanding"
            }
        
        shipments = sql_result["data"]
        
        if not shipments:
            return {
                "success": True,
                "operation": "check_outstanding",
                "data": [],
                "summary": "No outstanding shipments found.",
                "citations": [{
                    "table": "outstanding_site_shipment_status_report",
                    "columns": ["site_number", "country", "shipment_#", "days_outstanding"],
                    "query_date": datetime.now().isoformat(),
                    "row_count": 0
                }]
            }
        
        # Group by site
        sites_dict = {}
        for shipment in shipments:
            site = shipment.get("site_number")
            if site not in sites_dict:
                sites_dict[site] = {
                    "site": site,
                    "country": shipment.get("country"),
                    "shipments": [],
                    "total_days_outstanding": 0,
                    "max_days_outstanding": 0
                }
            
            sites_dict[site]["shipments"].append(shipment)
            days = shipment.get("days_outstanding", 0)
            sites_dict[site]["total_days_outstanding"] += days
            sites_dict[site]["max_days_outstanding"] = max(sites_dict[site]["max_days_outstanding"], days)
        
        # Convert to list and sort by max days outstanding
        sites_summary = sorted(sites_dict.values(), key=lambda x: x["max_days_outstanding"], reverse=True)
        
        # Generate summary
        summary_parts = [f"Found {len(shipments)} outstanding shipments across {len(sites_summary)} sites:"]
        for site_info in sites_summary[:5]:  # Top 5 sites
            summary_parts.append(f"  - {site_info['site']} ({site_info['country']}): {site_info['max_days_outstanding']} days outstanding")
        
        summary_text = "\n".join(summary_parts)
        
        citations = [{
            "table": "outstanding_site_shipment_status_report",
            "columns": ["site_number", "country", "shipment_#", "days_outstanding", "package_description", "package_count"],
            "query_date": datetime.now().isoformat(),
            "row_count": len(shipments)
        }]
        
        return {
            "success": True,
            "operation": "check_outstanding",
            "data": shipments,
            "sites_summary": sites_summary,
            "summary": {
                "total_shipments": len(shipments),
                "total_sites": len(sites_summary),
                "max_days_outstanding": max(s["max_days_outstanding"] for s in sites_summary) if sites_summary else 0
            },
            "citations": citations,
            "summary_text": summary_text
        }
    
    def _generate_expiry_summary(
        self,
        critical: List[Dict],
        high: List[Dict],
        medium: List[Dict]
    ) -> str:
        """Generate human-readable expiry summary."""
        total = len(critical) + len(high) + len(medium)
        
        if total == 0:
            return "No batches expiring within the specified threshold."
        
        summary_parts = [f"Found {total} batches expiring:"]
        
        if critical:
            summary_parts.append(f"  - {len(critical)} CRITICAL (< 30 days)")
        if high:
            summary_parts.append(f"  - {len(high)} HIGH (30-60 days)")
        if medium:
            summary_parts.append(f"  - {len(medium)} MEDIUM (60-90 days)")
        
        return "\n".join(summary_parts)

    def _get_purchase_requirements(
        self,
        filters: Dict[str, Any],
        schema_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get purchase requirements from the purchase_requirement table.
        
        Args:
            filters: Query filters
            schema_result: Schema information
            
        Returns:
            Dictionary with purchase requirement information
        """
        # Generate and execute SQL query
        sql_result = self.sql_agent.execute({
            "intent": "Query the purchase_requirement table. Find all open purchase requirements. Return: requirement_id, material_id, required_quantity, required_date, status. Sort by required_date ASC (earliest required date first).",
            "schemas": schema_result.get("formatted_schemas", ""),
            "filters": filters,
            "limit": 100
        })
        
        if not sql_result["success"]:
            return {
                "success": False,
                "error": sql_result.get("error", "Query failed"),
                "operation": "get_purchase_requirements"
            }
        
        requirements = sql_result["data"]
        
        if not requirements:
            return {
                "success": True,
                "operation": "get_purchase_requirements",
                "data": [],
                "summary": "No purchase requirements found.",
                "citations": [{
                    "table": "purchase_requirement",
                    "columns": ["requirement_id", "material_id", "required_quantity", "required_date", "status"],
                    "query_date": datetime.now().isoformat(),
                    "row_count": 0
                }]
            }
        
        # Calculate totals
        total_requirements = len(requirements)
        total_quantity = sum(item.get("required_quantity", 0) for item in requirements)
        
        # Group by status
        status_counts = {}
        for req in requirements:
            status = req.get("status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Generate summary
        summary_parts = [f"Found {total_requirements} purchase requirements with total quantity of {total_quantity} units."]
        for status, count in status_counts.items():
            summary_parts.append(f"  - {status}: {count} requirements")
        
        summary_text = "\n".join(summary_parts)
        
        citations = [{
            "table": "purchase_requirement",
            "columns": ["requirement_id", "material_id", "required_quantity", "required_date", "status"],
            "query_date": datetime.now().isoformat(),
            "row_count": len(requirements)
        }]
        
        return {
            "success": True,
            "operation": "get_purchase_requirements",
            "data": requirements,
            "summary": {
                "total_requirements": total_requirements,
                "total_quantity": total_quantity,
                "status_breakdown": status_counts
            },
            "citations": citations,
            "summary_text": summary_text
        }
