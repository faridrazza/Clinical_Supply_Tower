"""
Schema Retrieval Agent V2 with OpenAI Embeddings.

Uses OpenAI's embedding model for semantic table discovery.
"""
from typing import Dict, Any, List, Optional
import logging

from src.agents.base_agent import BaseAgent
from src.utils.chroma_schema_manager_openai import get_chroma_manager_openai
from src.utils.schema_registry import get_table_schema, format_schema_for_agent
from src.config.prompts import SCHEMA_RETRIEVAL_AGENT_PROMPT

logger = logging.getLogger(__name__)


class SchemaRetrievalAgentV2OpenAI(BaseAgent):
    """
    Schema Retrieval Agent using OpenAI embeddings.
    
    Uses OpenAI's text-embedding-3-small model for semantic search
    across all 40 tables.
    """
    
    def __init__(self, llm=None, chroma_persist_dir: str = "./chroma_db"):
        """
        Initialize Schema Retrieval Agent with OpenAI embeddings.
        
        Args:
            llm: Language model instance
            chroma_persist_dir: Directory for ChromaDB persistence
        """
        super().__init__("SchemaRetrievalAgentV2OpenAI", llm)
        self.chroma_manager = get_chroma_manager_openai(chroma_persist_dir)
        self.max_tables = 5
        self.similarity_threshold = 0.3
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute schema retrieval using OpenAI embeddings.
        
        Args:
            input_data: {
                "query": str,  # User query
                "workflow": str,  # "A" or "B" (optional)
                "specific_tables": List[str],  # Specific tables (optional)
                "n_results": int  # Number of results (default 5)
            }
            
        Returns:
            {
                "success": bool,
                "schemas": List[Dict],
                "table_names": List[str],
                "formatted_schemas": str,
                "search_method": str,
                "similarity_scores": Dict
            }
        """
        try:
            query = input_data.get("query", "")
            workflow = input_data.get("workflow")
            specific_tables = input_data.get("specific_tables", [])
            n_results = input_data.get("n_results", self.max_tables)
            
            # Determine search strategy
            if specific_tables:
                schemas, search_method = self._get_specific_schemas(specific_tables)
            elif workflow:
                schemas, search_method = self._semantic_search_with_workflow(
                    query, workflow, n_results
                )
            else:
                schemas, search_method = self._semantic_search(query, n_results)
            
            # Build similarity scores map
            similarity_scores = {s["table_name"]: s.get("similarity_score", 0) for s in schemas}
            
            # Format schemas
            formatted_schemas = self._format_schemas(schemas)
            
            result = {
                "success": True,
                "schemas": schemas,
                "table_names": [s["table_name"] for s in schemas],
                "formatted_schemas": formatted_schemas,
                "search_method": search_method,
                "similarity_scores": similarity_scores,
                "count": len(schemas)
            }
            
            self.log_execution(input_data, result)
            return result
        
        except Exception as e:
            return self.handle_error(e, input_data)
    
    def _semantic_search(
        self,
        query: str,
        n_results: int
    ) -> tuple[List[Dict[str, Any]], str]:
        """Perform semantic search using OpenAI embeddings."""
        self.logger.info(f"Performing semantic search (OpenAI): {query[:50]}...")
        
        try:
            # Query ChromaDB with OpenAI embeddings
            chroma_results = self.chroma_manager.find_relevant_tables(
                query=query,
                n_results=n_results
            )
            
            # Filter by similarity threshold
            schemas = []
            for result in chroma_results:
                if result["similarity_score"] >= self.similarity_threshold:
                    table_name = result["table_name"]
                    schema = get_table_schema(table_name)
                    
                    if schema:
                        schemas.append({
                            "table_name": table_name,
                            "business_purpose": schema.get("business_purpose", ""),
                            "key_columns": schema.get("key_columns", []),
                            "similarity_score": result["similarity_score"],
                            "workflow": schema.get("workflow", [])
                        })
            
            self.logger.info(f"Found {len(schemas)} relevant tables")
            return schemas, "semantic_openai"
        
        except Exception as e:
            self.logger.error(f"Semantic search failed: {e}")
            raise
    
    def _semantic_search_with_workflow(
        self,
        query: str,
        workflow: str,
        n_results: int
    ) -> tuple[List[Dict[str, Any]], str]:
        """Perform semantic search with workflow filtering."""
        self.logger.info(f"Semantic search (OpenAI) for workflow {workflow}: {query[:50]}...")
        
        try:
            chroma_results = self.chroma_manager.find_relevant_tables(
                query=query,
                n_results=n_results * 2,
                workflow=workflow
            )
            
            schemas = []
            for result in chroma_results:
                if result["similarity_score"] >= self.similarity_threshold:
                    table_name = result["table_name"]
                    schema = get_table_schema(table_name)
                    
                    if schema:
                        schemas.append({
                            "table_name": table_name,
                            "business_purpose": schema.get("business_purpose", ""),
                            "key_columns": schema.get("key_columns", []),
                            "similarity_score": result["similarity_score"],
                            "workflow": schema.get("workflow", [])
                        })
                
                if len(schemas) >= n_results:
                    break
            
            self.logger.info(f"Found {len(schemas)} relevant tables for workflow {workflow}")
            return schemas, "semantic_openai_workflow"
        
        except Exception as e:
            self.logger.error(f"Workflow-filtered search failed: {e}")
            raise
    
    def _get_specific_schemas(
        self,
        table_names: List[str]
    ) -> tuple[List[Dict[str, Any]], str]:
        """Get schemas for specific tables."""
        self.logger.info(f"Retrieving specific schemas: {table_names}")
        
        schemas = []
        for table_name in table_names[:self.max_tables]:
            schema = get_table_schema(table_name)
            
            if schema and schema != {}:
                schemas.append({
                    "table_name": table_name,
                    "business_purpose": schema.get("business_purpose", ""),
                    "key_columns": schema.get("key_columns", []),
                    "similarity_score": 1.0,
                    "workflow": schema.get("workflow", [])
                })
        
        return schemas, "specific"
    
    def _format_schemas(self, schemas: List[Dict[str, Any]]) -> str:
        """Format schemas for agent consumption."""
        if not schemas:
            return "No schemas available."
        
        formatted_parts = []
        
        for i, schema in enumerate(schemas, 1):
            table_name = schema.get("table_name", "Unknown")
            similarity = schema.get("similarity_score", 0)
            
            formatted = format_schema_for_agent(table_name)
            formatted_parts.append(
                f"--- Table {i}: {table_name} (Relevance: {similarity:.1%}) ---\n{formatted}\n"
            )
        
        return "\n".join(formatted_parts)
    
    def get_chroma_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics."""
        return self.chroma_manager.get_collection_stats()
    
    def refresh_chroma_schemas(self):
        """Refresh ChromaDB schemas."""
        self.logger.info("Refreshing ChromaDB schemas...")
        self.chroma_manager.refresh_schemas()
        self.logger.info("ChromaDB schemas refreshed")
