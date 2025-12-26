"""
SQL Generation Agent V2 - Table-agnostic query generation.

This version accepts table names as parameters and generates queries
for ANY table, not just hardcoded domain-specific tables.
"""
from typing import Dict, Any, Optional, List
import logging

from src.agents.base_agent import BaseAgent
from src.tools.database_tools import run_sql_query
from src.tools.sql_validator import SQLValidator
from src.utils.error_handlers import SQLErrorHandler
from src.utils.schema_registry import get_table_schema
from src.config.settings import settings

logger = logging.getLogger(__name__)


class SQLGenerationAgentV2(BaseAgent):
    """
    Table-agnostic SQL Generation Agent.
    
    Generates queries for ANY table based on:
    - User intent
    - Available table schemas
    - Query filters
    
    Responsibilities:
    - Generate syntactically correct PostgreSQL queries
    - Use ONLY provided schemas
    - Implement self-healing retry logic (max 3 attempts)
    - Support dynamic table selection
    """
    
    def __init__(self, llm=None):
        """Initialize SQL Generation Agent V2."""
        super().__init__("SQLGenerationAgentV2", llm)
        self.max_retries = settings.max_sql_retries
        
        # Initialize LLM for SQL generation if not provided
        if self.llm is None:
            try:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model_name=settings.llm_model,
                    temperature=0.1,  # Low temperature for precise SQL generation
                    api_key=settings.openai_api_key
                )
                logger.info("SQL Generation Agent initialized with LLM")
            except Exception as e:
                logger.warning(f"Could not initialize LLM for SQL generation: {e}. Using generic queries.")
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute SQL generation and query.
        
        Args:
            input_data: {
                "intent": str,  # What to query
                "table_names": List[str],  # Tables to query (from ChromaDB)
                "schemas": str or List[Dict],  # Available schemas
                "filters": Dict,  # Optional filters
                "limit": int  # Optional result limit
            }
            
        Returns:
            {
                "success": bool,
                "query": str,  # Generated SQL
                "data": List[Dict],  # Query results
                "table_used": str,  # Which table was queried
                "attempt": int,  # Number of attempts
                "error": str  # Error message if failed
            }
        """
        try:
            intent = input_data.get("intent", "")
            table_names = input_data.get("table_names", [])
            schemas = input_data.get("schemas", "")
            filters = input_data.get("filters", {})
            limit = input_data.get("limit")
            
            if not table_names:
                return {
                    "success": False,
                    "error": "No table names provided",
                    "attempt": 0
                }
            
            # Attempt query generation with self-healing
            for attempt in range(1, self.max_retries + 1):
                self.logger.info(f"SQL generation attempt {attempt}/{self.max_retries}")
                
                # Try each table in order of relevance
                for table_name in table_names:
                    # Generate query for this table
                    query = self._generate_query_for_table(
                        intent=intent,
                        table_name=table_name,
                        schemas=schemas,
                        filters=filters,
                        limit=limit,
                        attempt=attempt
                    )
                    
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
                        # Check if we got meaningful results
                        row_count = result.get("row_count", 0)
                        
                        # Always accept the first table (highest semantic relevance)
                        # This ensures we use the most relevant table even if others have more rows
                        is_first_table = (table_names.index(table_name) == 0)
                        
                        if is_first_table:
                            # First table - accept regardless of row count
                            self.logger.info(f"Using first table (highest relevance): {table_name} with {row_count} rows")
                            return {
                                "success": True,
                                "query": query,
                                "data": result.get("data", []),
                                "columns": result.get("columns", []),
                                "row_count": row_count,
                                "table_used": table_name,
                                "attempt": attempt,
                                "executed_at": result.get("executed_at"),
                                "validation_applied": validation_report.get("was_modified", False)
                            }
                        elif row_count > 0:
                            # Subsequent tables - only accept if they have results
                            self.logger.info(f"Using fallback table: {table_name} with {row_count} rows")
                            return {
                                "success": True,
                                "query": query,
                                "data": result.get("data", []),
                                "columns": result.get("columns", []),
                                "row_count": row_count,
                                "table_used": table_name,
                                "attempt": attempt,
                                "executed_at": result.get("executed_at"),
                                "validation_applied": validation_report.get("was_modified", False)
                            }
                        else:
                            # No results from this table, try next one
                            self.logger.info(f"Table {table_name} returned no results, trying next table...")
                            continue
                    
                    # Query failed - analyze error
                    error_info = self._analyze_error(result, query, schemas)
                    
                    if attempt < self.max_retries:
                        self.logger.warning(
                            f"Query failed for {table_name}: {error_info['user_message']}. "
                            f"Trying next table or retrying..."
                        )
                    else:
                        # Final attempt failed
                        return {
                            "success": False,
                            "query": query,
                            "table_used": table_name,
                            "attempt": attempt,
                            "error": error_info["user_message"],
                            "error_type": result.get("error_type"),
                            "suggestion": error_info.get("suggestion")
                        }
                
                # All tables failed for this attempt
                if attempt < self.max_retries:
                    self.logger.warning(f"All tables failed on attempt {attempt}. Retrying...")
            
            # All attempts exhausted
            return {
                "success": False,
                "error": "Failed to generate valid query after maximum retries",
                "tables_attempted": table_names,
                "attempt": self.max_retries
            }
        
        except Exception as e:
            return self.handle_error(e, input_data)
    
    def _generate_query_for_table(
        self,
        intent: str,
        table_name: str,
        schemas: Any,
        filters: Dict[str, Any],
        limit: Optional[int],
        attempt: int
    ) -> str:
        """
        Generate SQL query for a specific table.
        
        Args:
            intent: User intent
            table_name: Table to query
            schemas: Available schemas
            filters: Query filters
            limit: Result limit
            attempt: Attempt number
            
        Returns:
            Generated SQL query or empty string if failed
        """
        # If LLM is available, use it for dynamic query generation
        if self.llm:
            return self._generate_query_with_llm(
                intent=intent,
                table_name=table_name,
                schemas=schemas,
                filters=filters,
                limit=limit
            )
        
        # Fallback to generic query generation
        return self._generate_generic_query(
            intent=intent,
            table_name=table_name,
            filters=filters,
            limit=limit
        )
    
    def _generate_query_with_llm(
        self,
        intent: str,
        table_name: str,
        schemas: str,
        filters: Dict[str, Any],
        limit: Optional[int]
    ) -> str:
        """Generate SQL using LLM for maximum flexibility."""
        prompt = f"""
You are a PostgreSQL query generator for a pharmaceutical supply chain database.

CRITICAL RULES:
1. Only cast columns to DATE if they contain actual dates (columns ending in _date, _time, expiry, expiration)
2. DO NOT cast ID columns (order_id, batch_id, material_id, etc.) to DATE
3. DO NOT cast columns like order_number, batch_number, material_number to DATE
4. Use ILIKE for text matching when filtering by IDs

CORRECT DATE COLUMNS (cast these with ::DATE):
- expiration_date, expiry_date, created_date, modified_date, delivery_date
- date_of_manufacture, adjusted_expiration_date, target_date
- Any column with "date" or "expir" in the name

NON-DATE COLUMNS (DO NOT cast these):
- order_id, batch_id, material_id, trial_id, site_id
- order_number, batch_number, material_number, lot_number
- material_component, fing_batch, ly_number

PRIMARY TABLE TO QUERY:
{table_name}

USER INTENT:
{intent}

AVAILABLE SCHEMAS:
{schemas}

FILTERS (if any):
{filters}

RULES:
1. Generate ONLY the SQL query, no explanation
2. Use PostgreSQL syntax
3. Query ONLY the table: {table_name}
4. Include LIMIT clause (default 100 if not specified)
5. Sort results by most relevant field
6. Use double quotes for identifiers
7. Return all relevant columns for the query type
8. ALWAYS cast date columns to DATE type before comparisons or arithmetic

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
            
            self.logger.info(f"LLM generated query for {table_name}: {query[:100]}...")
            return query
        except Exception as e:
            self.logger.warning(f"LLM query generation failed: {e}. Falling back to generic.")
            return self._generate_generic_query(intent, table_name, filters, limit)
    
    def _generate_generic_query(
        self,
        intent: str,
        table_name: str,
        filters: Dict[str, Any],
        limit: Optional[int]
    ) -> str:
        """
        Generate a generic query for any table.
        
        This is a fallback that works for most tables.
        """
        intent_lower = intent.lower()
        
        # Get table schema to determine columns
        schema = get_table_schema(table_name)
        if not schema:
            self.logger.warning(f"Schema not found for table {table_name}")
            return ""
        
        key_columns = schema.get("key_columns", [])
        if not key_columns:
            return ""
        
        # Build column list
        column_names = [f'"{col["name"]}"' for col in key_columns[:10]]  # Limit to 10 columns
        columns_str = ", ".join(column_names)
        
        # Build base query
        query = f'SELECT {columns_str} FROM "{table_name}"'
        
        # Add WHERE clause if filters provided
        where_conditions = []
        for key, value in filters.items():
            # Try to find matching column
            for col in key_columns:
                if key.lower() in col["name"].lower() or col["name"].lower() in key.lower():
                    where_conditions.append(f'"{col["name"]}" = \'{value}\'')
                    break
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        # Add ORDER BY for date columns if present
        for col in key_columns:
            if "date" in col["name"].lower() or "expir" in col["name"].lower():
                query += f' ORDER BY "{col["name"]}"::DATE DESC'
                break
        
        # Add LIMIT
        if limit:
            query += f" LIMIT {limit}"
        else:
            query += " LIMIT 100"
        
        query += ";"
        
        self.logger.info(f"Generated generic query for {table_name}: {query[:100]}...")
        return query
    
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
