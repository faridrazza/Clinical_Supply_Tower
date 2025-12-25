"""
Schema Retrieval Agent - Context window manager using PostgreSQL.
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from src.utils.schema_registry import format_schema_for_agent, get_tables_for_workflow, get_table_schema, TABLE_SCHEMAS
from src.tools.database_tools import fuzzy_match_table_name, search_tables_by_keyword
from src.config.prompts import SCHEMA_RETRIEVAL_AGENT_PROMPT


class SchemaRetrievalAgent(BaseAgent):
    """
    Schema Retrieval Agent manages context window by retrieving relevant schemas.
    
    Uses PostgreSQL and schema registry instead of vector database.
    
    Responsibilities:
    - Query schema registry for relevant table schemas
    - Return maximum 5 tables at a time
    - Provide formatted schema to other agents
    """
    
    def __init__(self, llm=None):
        super().__init__("SchemaRetrievalAgent", llm)
        self.max_tables = 5
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute schema retrieval.
        
        Args:
            input_data: {
                "query": str,  # User query or intent
                "workflow": str,  # "A" or "B" (optional)
                "specific_tables": List[str]  # Specific tables to retrieve (optional)
            }
            
        Returns:
            {
                "schemas": List[Dict],  # List of schema information
                "table_names": List[str],  # List of table names
                "formatted_schemas": str  # Formatted text for agent consumption
            }
        """
        try:
            query = input_data.get("query", "")
            workflow = input_data.get("workflow")
            specific_tables = input_data.get("specific_tables", [])
            
            # If specific tables requested, retrieve those
            if specific_tables:
                schemas = self._get_specific_schemas(specific_tables)
            
            # If workflow specified, prioritize workflow-specific tables
            elif workflow:
                schemas = self._get_workflow_schemas(query, workflow)
            
            # Otherwise, use keyword search
            else:
                schemas = self._keyword_search(query)
            
            # Format schemas for agent consumption
            formatted_schemas = self._format_schemas(schemas)
            
            result = {
                "schemas": schemas,
                "table_names": [s["table_name"] for s in schemas],
                "formatted_schemas": formatted_schemas,
                "count": len(schemas)
            }
            
            self.log_execution(input_data, result)
            return result
        
        except Exception as e:
            return self.handle_error(e, input_data)
    
    def _keyword_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for relevant tables using keyword matching.
        
        Args:
            query: User query
            
        Returns:
            List of schema dictionaries
        """
        keywords = self._extract_keywords(query)
        matched_tables = set()
        
        # Search schema registry for matching tables
        for table_name, schema_info in TABLE_SCHEMAS.items():
            business_purpose = schema_info.get("business_purpose", "").lower()
            column_names = [col["name"].lower() for col in schema_info.get("key_columns", [])]
            
            # Check if any keyword matches business purpose or column names
            for keyword in keywords:
                if (keyword in business_purpose or 
                    any(keyword in col for col in column_names)):
                    matched_tables.add(table_name)
                    break
        
        # Convert to schema dictionaries
        schemas = []
        for table_name in list(matched_tables)[:self.max_tables]:
            schema = get_table_schema(table_name)
            if schema:
                schemas.append({
                    "table_name": table_name,
                    "business_purpose": schema.get("business_purpose", ""),
                    "key_columns": schema.get("key_columns", [])
                })
        
        self.logger.info(f"Retrieved {len(schemas)} schemas via keyword search")
        return schemas
    
    def _get_workflow_schemas(self, query: str, workflow: str) -> List[Dict[str, Any]]:
        """
        Get schemas prioritized for specific workflow.
        
        Args:
            query: User query
            workflow: "A" or "B"
            
        Returns:
            List of schema dictionaries
        """
        # Get workflow-specific tables
        workflow_tables = get_tables_for_workflow(workflow)
        
        # Also do keyword search
        keyword_schemas = self._keyword_search(query)
        keyword_table_names = [s["table_name"] for s in keyword_schemas]
        
        # Combine: prioritize workflow tables, then keyword matches
        combined_schemas = []
        
        # Add workflow tables first
        for table_name in workflow_tables:
            if table_name not in [s["table_name"] for s in combined_schemas]:
                schema = get_table_schema(table_name)
                if schema:
                    combined_schemas.append({
                        "table_name": table_name,
                        "business_purpose": schema.get("business_purpose", ""),
                        "key_columns": schema.get("key_columns", [])
                    })
                if len(combined_schemas) >= self.max_tables:
                    break
        
        # Add keyword matches if space available
        for schema in keyword_schemas:
            if schema["table_name"] not in [s["table_name"] for s in combined_schemas]:
                combined_schemas.append(schema)
                if len(combined_schemas) >= self.max_tables:
                    break
        
        self.logger.info(f"Retrieved {len(combined_schemas)} schemas for workflow {workflow}")
        return combined_schemas
    
    def _get_specific_schemas(self, table_names: List[str]) -> List[Dict[str, Any]]:
        """
        Get schemas for specific tables.
        
        Args:
            table_names: List of table names
            
        Returns:
            List of schema dictionaries
        """
        schemas = []
        
        for table_name in table_names[:self.max_tables]:
            # Try exact match first
            schema = get_table_schema(table_name)
            
            # If not found (empty dict), try fuzzy matching
            if not schema or schema == {}:
                matched_name = fuzzy_match_table_name(table_name)
                if matched_name:
                    schema = get_table_schema(matched_name)
            
            # Check if schema was found (not empty)
            if schema and schema != {}:
                schemas.append({
                    "table_name": schema.get("table_name", table_name),
                    "business_purpose": schema.get("business_purpose", ""),
                    "key_columns": schema.get("key_columns", [])
                })
            else:
                self.logger.warning(f"Schema not found for table: {table_name}")
        
        self.logger.info(f"Retrieved {len(schemas)} specific schemas")
        return schemas
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract search keywords from query.
        
        Args:
            query: User query
            
        Returns:
            List of keywords
        """
        # Remove common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
            "can", "could", "should", "would", "may", "might", "must", "will",
            "we", "you", "i", "he", "she", "it", "they", "what", "which", "who",
            "when", "where", "why", "how", "this", "that", "these", "those"
        }
        
        # Split query into words and filter
        words = query.lower().split()
        keywords = [w.strip(".,!?;:") for w in words if w.lower() not in stop_words and len(w) > 2]
        
        return keywords
    
    def _format_schemas(self, schemas: List[Dict[str, Any]]) -> str:
        """
        Format schemas for agent consumption.
        
        Args:
            schemas: List of schema dictionaries
            
        Returns:
            Formatted schema text
        """
        if not schemas:
            return "No schemas available."
        
        formatted_parts = []
        
        for i, schema in enumerate(schemas, 1):
            table_name = schema.get("table_name", "Unknown")
            formatted = format_schema_for_agent(table_name)
            formatted_parts.append(f"--- Table {i}: {table_name} ---\n{formatted}\n")
        
        return "\n".join(formatted_parts)
    
    def get_table_for_entity(self, entity_type: str) -> List[str]:
        """
        Get relevant tables for specific entity type.
        
        Args:
            entity_type: Type of entity (batch, material, trial, etc.)
            
        Returns:
            List of relevant table names
        """
        entity_table_map = {
            "batch": ["available_inventory_report", "allocated_materials_to_orders", "re_evaluation"],
            "material": ["materials", "material_master", "material_requirements"],
            "trial": ["materials_per_study", "enrollment_rate_report", "country_level_enrollment_report"],
            "country": ["country_level_enrollment_report", "material_country_requirements", "rim"],
            "expiry": ["available_inventory_report"],
            "enrollment": ["enrollment_rate_report", "country_level_enrollment_report"],
            "regulatory": ["rim", "material_country_requirements", "re_evaluation"],
            "shipping": ["ip_shipping_timelines_report", "distribution_order_report", "outstanding_site_shipment_status_report"]
        }
        
        return entity_table_map.get(entity_type.lower(), [])
