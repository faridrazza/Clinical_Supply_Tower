"""
SQL Generation Agent - Query construction and execution with self-healing.
"""
from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent
from src.tools.database_tools import run_sql_query
from src.tools.sql_validator import SQLValidator
from src.utils.error_handlers import SQLErrorHandler
from src.config.prompts import SQL_GENERATION_AGENT_PROMPT
from src.config.settings import settings


class SQLGenerationAgent(BaseAgent):
    """
    SQL Generation Agent converts natural language to PostgreSQL queries.
    
    Responsibilities:
    - Generate syntactically correct PostgreSQL queries
    - Use ONLY provided schemas
    - Implement self-healing retry logic (max 3 attempts)
    - Parse and interpret SQL error messages
    """
    
    def __init__(self, llm=None):
        super().__init__("SQLGenerationAgent", llm)
        self.max_retries = settings.max_sql_retries
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute SQL generation and query.
        
        Args:
            input_data: {
                "intent": str,  # What to query
                "schemas": str or List[Dict],  # Available schemas
                "filters": Dict,  # Optional filters
                "limit": int  # Optional result limit
            }
            
        Returns:
            {
                "success": bool,
                "query": str,  # Generated SQL
                "data": List[Dict],  # Query results
                "attempt": int,  # Number of attempts
                "error": str  # Error message if failed
            }
        """
        try:
            intent = input_data.get("intent", "")
            schemas = input_data.get("schemas", "")
            filters = input_data.get("filters", {})
            limit = input_data.get("limit")
            
            # Attempt query generation with self-healing
            for attempt in range(1, self.max_retries + 1):
                self.logger.info(f"SQL generation attempt {attempt}/{self.max_retries}")
                
                # Generate query
                query = self._generate_query(intent, schemas, filters, limit, attempt)
                
                if not query:
                    continue
                
                # Validate and fix date casting issues
                validation_report = SQLValidator.get_validation_report(query)
                if validation_report["was_modified"]:
                    query = validation_report["fixed_query"]
                    self.logger.info(f"Applied {len(validation_report['fixes_applied'])} fixes to query")
                
                # Execute query
                result = run_sql_query(query)
                
                if result["success"]:
                    return {
                        "success": True,
                        "query": query,
                        "data": result.get("data", []),
                        "columns": result.get("columns", []),
                        "row_count": result.get("row_count", 0),
                        "attempt": attempt,
                        "executed_at": result.get("executed_at"),
                        "validation_applied": validation_report.get("was_modified", False)
                    }
                
                # Query failed - analyze error for next attempt
                error_info = self._analyze_error(result, query, schemas)
                
                if attempt < self.max_retries:
                    self.logger.warning(f"Query failed: {error_info['user_message']}. Retrying...")
                    # Update intent with error information for next attempt
                    intent = f"{intent}\n\nPrevious attempt failed: {error_info['suggestion']}"
                else:
                    # Final attempt failed
                    return {
                        "success": False,
                        "query": query,
                        "attempt": attempt,
                        "error": error_info["user_message"],
                        "error_type": result.get("error_type"),
                        "suggestion": error_info.get("suggestion"),
                        "validation_applied": validation_report.get("was_modified", False)
                    }
            
            # Should not reach here
            return {
                "success": False,
                "error": "Failed to generate valid query after maximum retries",
                "attempt": self.max_retries
            }
        
        except Exception as e:
            return self.handle_error(e, input_data)
    
    def _generate_query(
        self,
        intent: str,
        schemas: Any,
        filters: Dict[str, Any],
        limit: Optional[int],
        attempt: int
    ) -> str:
        """
        Generate SQL query based on intent and schemas.
        Uses LLM if available, falls back to template-based generation.
        """
        # If LLM is available, use it for dynamic query generation
        if self.llm:
            return self._generate_query_with_llm(intent, schemas, filters, limit)
        
        # Fallback to template-based generation
        return self._generate_query_from_template(intent, filters, limit)
    
    def _generate_query_with_llm(
        self,
        intent: str,
        schemas: str,
        filters: Dict[str, Any],
        limit: Optional[int]
    ) -> str:
        """Generate SQL using LLM for maximum flexibility."""
        prompt = f"""
You are a PostgreSQL query generator for a pharmaceutical supply chain database.

CRITICAL RULES FOR THIS DATABASE:
1. Many date columns are stored as TEXT, not DATE type
2. When you see a column with "date", "time", or "expir" in the name, ALWAYS cast it to DATE
3. Use proper date arithmetic syntax

EXAMPLES:
- WRONG: WHERE expiration_date < CURRENT_DATE
- RIGHT: WHERE expiration_date::DATE < CURRENT_DATE::DATE

- WRONG: EXTRACT(DAY FROM expiry_date - CURRENT_DATE)
- RIGHT: (expiry_date::DATE - CURRENT_DATE::DATE) as days_remaining

- WRONG: ORDER BY created_date
- RIGHT: ORDER BY created_date::DATE

TEXT Date Columns (non-exhaustive list):
expiration_date, expiry_date, created_date, modified_date, delivery_date, order_date,
request_date, ship_date, manufacturing_date, goods_receipt_date, inspection_date,
approval_date, release_date, start_date, end_date, actual_date, planned_date,
scheduled_date, received_date, shipped_date, accepted_date, confirmed_date,
issued_date, effective_date, validity_date, and any column ending in _date or _time

USER INTENT:
{intent}

AVAILABLE SCHEMAS:
{schemas}

FILTERS (if any):
{filters}

RULES:
1. Generate ONLY the SQL query, no explanation
2. Use PostgreSQL syntax
3. Include LIMIT clause (default 100 if not specified)
4. Sort results by most relevant field (e.g., expiry_date for expiry queries)
5. Use double quotes for identifiers
6. Return all relevant columns for the query type
7. ALWAYS cast date columns to DATE type before comparisons or arithmetic

Generate the SQL query:
"""
        try:
            response = self.llm.invoke(prompt)
            query = response.content.strip()
            
            # Clean up query if wrapped in markdown code blocks
            if query.startswith("```"):
                query = query.split("```")[1]
                if query.startswith("sql"):
                    query = query[3:]
            
            query = query.strip()
            
            # Ensure query ends with semicolon
            if not query.endswith(";"):
                query += ";"
            
            self.logger.info(f"LLM generated query: {query[:100]}...")
            return query
        except Exception as e:
            self.logger.warning(f"LLM query generation failed: {e}. Falling back to templates.")
            return self._generate_query_from_template(intent, filters, limit)
    
    def _generate_query_from_template(
        self,
        intent: str,
        filters: Dict[str, Any],
        limit: Optional[int]
    ) -> str:
        """Fallback template-based query generation."""
        intent_lower = intent.lower()
        
        # Outstanding shipments query
        if "outstanding" in intent_lower or "pending" in intent_lower:
            return self._generate_outstanding_query(filters, limit)
        
        # Purchase requirement query
        elif "purchase" in intent_lower or "requirement" in intent_lower or "procurement" in intent_lower:
            return self._generate_purchase_query(filters, limit)
        
        # Expiry alert query
        elif "expir" in intent_lower:
            return self._generate_expiry_query(filters, limit)
        
        # Batch lookup query
        elif "batch" in intent_lower or "lot" in intent_lower:
            return self._generate_batch_query(filters, limit)
        
        # Enrollment query
        elif "enrollment" in intent_lower:
            return self._generate_enrollment_query(filters, limit)
        
        # Re-evaluation query
        elif "re-evaluation" in intent_lower or "extension" in intent_lower:
            return self._generate_reevaluation_query(filters, limit)
        
        # Regulatory query
        elif "regulatory" in intent_lower or "approval" in intent_lower:
            return self._generate_regulatory_query(filters, limit)
        
        # Shipping timeline query
        elif "shipping" in intent_lower or "timeline" in intent_lower:
            return self._generate_shipping_query(filters, limit)
        
        # Generic inventory query
        else:
            return self._generate_inventory_query(filters, limit)
    
    def _generate_outstanding_query(self, filters: Dict, limit: Optional[int]) -> str:
        """Generate query for outstanding shipments by site."""
        query = """
        SELECT 
            site_number,
            country,
            "shipment_#",
            trial_alias,
            package_description,
            package_count,
            request_date,
            days_outstanding
        FROM outstanding_site_shipment_status_report
        ORDER BY days_outstanding DESC
        """
        
        if limit:
            query += f"\nLIMIT {limit}"
        else:
            query += "\nLIMIT 100"
        
        return query + ";"
    
    def _generate_expiry_query(self, filters: Dict, limit: Optional[int]) -> str:
        """Generate query for expiring batches - works with or without filters."""
        query = """
        SELECT 
            trial_name,
            location,
            lot as batch_id,
            package_type_description as material,
            expiry_date,
            received_packages as quantity,
            'packages' as unit,
            (expiry_date::DATE - CURRENT_DATE::DATE) as days_remaining,
            CASE 
                WHEN (expiry_date::DATE - CURRENT_DATE::DATE) < 30 THEN 'CRITICAL'
                WHEN (expiry_date::DATE - CURRENT_DATE::DATE) < 60 THEN 'HIGH'
                ELSE 'MEDIUM'
            END as severity
        FROM available_inventory_report
        WHERE expiry_date::DATE <= CURRENT_DATE::DATE + INTERVAL '90 days'
            AND expiry_date::DATE > CURRENT_DATE::DATE
            AND received_packages > 0
        """
        
        # Add optional filters if provided
        if filters.get("location"):
            query += f"\n    AND location = '{filters['location']}'"
        
        if filters.get("trial_name"):
            query += f"\n    AND trial_name = '{filters['trial_name']}'"
        
        # Sort by days remaining (closest to expiry first)
        query += "\nORDER BY days_remaining ASC"
        
        # Limit results if specified, otherwise get top 50
        if limit:
            query += f"\nLIMIT {limit}"
        else:
            query += "\nLIMIT 50"
        
        return query + ";"
    
    def _generate_batch_query(self, filters: Dict, limit: Optional[int]) -> str:
        """Generate query for batch information - works with or without batch_id."""
        batch_id = filters.get("batch_id", filters.get("lot"))
        
        if batch_id:
            # Specific batch lookup
            query = f"""
            SELECT 
                trial_name,
                location,
                lot,
                package_type_description,
                expiry_date,
                received_packages,
                shipped_packages,
                packages_awaiting,
                (expiry_date::DATE - CURRENT_DATE::DATE) as days_remaining
            FROM available_inventory_report
            WHERE lot = '{batch_id}'
            """
        else:
            # No batch specified - return all batches sorted by expiry
            query = """
            SELECT 
                trial_name,
                location,
                lot,
                package_type_description,
                expiry_date,
                received_packages,
                shipped_packages,
                (expiry_date::DATE - CURRENT_DATE::DATE) as days_remaining
            FROM available_inventory_report
            WHERE received_packages > 0
            ORDER BY expiry_date::DATE ASC
            """
        
        if limit:
            query += f"\nLIMIT {limit}"
        else:
            query += "\nLIMIT 100"
        
        return query + ";"
    
    def _generate_enrollment_query(self, filters: Dict, limit: Optional[int]) -> str:
        """Generate query for enrollment data."""
        query = """
        SELECT 
            trial_alias,
            country,
            site,
            year,
            months_jan_feb_dec
        FROM enrollment_rate_report
        WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)
        """
        
        if filters.get("trial_alias"):
            query += f"\n    AND trial_alias = '{filters['trial_alias']}'"
        
        if filters.get("country"):
            query += f"\n    AND country = '{filters['country']}'"
        
        if limit:
            query += f"\nLIMIT {limit}"
        
        return query + ";"
    
    def _generate_reevaluation_query(self, filters: Dict, limit: Optional[int]) -> str:
        """Generate query for re-evaluation history."""
        lot_number = filters.get("lot_number", filters.get("batch_id"))
        
        query = """
        SELECT 
            id,
            created,
            request_type_molecule_planner_to_complete as request_type,
            sample_status_ndp_material_coordinator_to_complete as status,
            lot_number_molecule_planner_to_complete as lot_number,
            modified_date
        FROM re_evaluation
        """
        
        if lot_number:
            query += f"\nWHERE lot_number_molecule_planner_to_complete = '{lot_number}'"
        
        query += "\nORDER BY created DESC"
        
        if limit:
            query += f"\nLIMIT {limit}"
        
        return query + ";"
    
    def _generate_regulatory_query(self, filters: Dict, limit: Optional[int]) -> str:
        """Generate query for regulatory approvals."""
        query = """
        SELECT 
            name_v,
            health_authority_division_c,
            status_v,
            approved_date_c,
            clinical_study_v,
            ly_number_c,
            submission_outcome
        FROM rim
        """
        
        conditions = []
        
        if filters.get("clinical_study"):
            conditions.append(f"clinical_study_v = '{filters['clinical_study']}'")
        
        if filters.get("country"):
            # Map country to health authority
            country_authority_map = {
                "Germany": "EMA",
                "UK": "MHRA",
                "USA": "FDA",
                "Japan": "PMDA"
            }
            authority = country_authority_map.get(filters["country"], "EMA")
            conditions.append(f"health_authority_division_c = '{authority}'")
        
        if filters.get("status"):
            conditions.append(f"status_v = '{filters['status']}'")
        
        if conditions:
            query += "\nWHERE " + " AND ".join(conditions)
        
        query += "\nORDER BY approved_date_c DESC"
        
        if limit:
            query += f"\nLIMIT {limit}"
        
        return query + ";"
    
    def _generate_shipping_query(self, filters: Dict, limit: Optional[int]) -> str:
        """Generate query for shipping timelines."""
        query = """
        SELECT 
            ip_helper,
            ip_timeline,
            country_name
        FROM ip_shipping_timelines_report
        """
        
        if filters.get("country"):
            query += f"\nWHERE country_name = '{filters['country']}'"
        
        if limit:
            query += f"\nLIMIT {limit}"
        
        return query + ";"
    
    def _generate_purchase_query(self, filters: Dict, limit: Optional[int]) -> str:
        """Generate query for purchase requirements."""
        query = """
        SELECT 
            purchase_requisition_number,
            material,
            preq_quantity,
            requisition_date,
            vendor,
            order_number,
            product_description,
            trial_alias
        FROM purchase_requirement
        ORDER BY requisition_date DESC
        """
        
        # Add optional filters if provided
        if filters.get("material"):
            query += f"\n    WHERE material = '{filters['material']}'"
        
        if filters.get("vendor"):
            if "WHERE" in query:
                query += f"\n    AND vendor = '{filters['vendor']}'"
            else:
                query += f"\n    WHERE vendor = '{filters['vendor']}'"
        
        if filters.get("trial_alias"):
            if "WHERE" in query:
                query += f"\n    AND trial_alias = '{filters['trial_alias']}'"
            else:
                query += f"\n    WHERE trial_alias = '{filters['trial_alias']}'"
        
        # Limit results if specified, otherwise get top 100
        if limit:
            query += f"\nLIMIT {limit}"
        else:
            query += "\nLIMIT 100"
        
        return query + ";"
    
    def _generate_inventory_query(self, filters: Dict, limit: Optional[int]) -> str:
        """Generate generic inventory query."""
        query = """
        SELECT 
            trial_name,
            location,
            lot,
            expiry_date,
            received_packages,
            shipped_packages
        FROM available_inventory_report
        WHERE received_packages > 0
        """
        
        if limit:
            query += f"\nLIMIT {limit}"
        
        return query + ";"
    
    def _analyze_error(
        self,
        result: Dict[str, Any],
        query: str,
        schemas: Any
    ) -> Dict[str, str]:
        """
        Analyze SQL error and provide suggestions.
        
        Args:
            result: Query result with error
            query: Failed SQL query
            schemas: Available schemas
            
        Returns:
            Dictionary with error analysis
        """
        error = result.get("error", "")
        error_code = result.get("error_code", "")
        
        # Translate error
        user_message = SQLErrorHandler.translate_error(error_code, error)
        
        # Get suggestion
        suggestion = SQLErrorHandler.suggest_fix(error_code, error, query)
        
        return {
            "user_message": user_message,
            "suggestion": suggestion or "Check table and column names in schema",
            "error_code": error_code
        }
