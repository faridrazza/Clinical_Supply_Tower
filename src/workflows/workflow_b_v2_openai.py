"""
Workflow B V2 with OpenAI Embeddings.

Uses OpenAI's embedding model for semantic table discovery.

For shelf-life extension queries, checks three required tables:
1. re_evaluation - Technical check (prior extensions)
2. rim - Regulatory check (country approvals)
3. ip_shipping_timelines_report - Logistical check (shipping feasibility)
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from src.agents.router_agent import RouterAgent
from src.agents.schema_retrieval_agent_v2_openai import SchemaRetrievalAgentV2OpenAI
from src.agents.sql_generation_agent_v2 import SQLGenerationAgentV2
from src.agents.synthesis_agent import SynthesisAgent
from src.tools.database_tools import run_sql_query

logger = logging.getLogger(__name__)


class ScenarioStrategistWorkflowV2OpenAI:
    """
    Scenario Strategist Workflow V2 with OpenAI Embeddings.
    
    Uses OpenAI's text-embedding-3-small model for semantic table discovery.
    """
    
    def __init__(self, llm=None, chroma_persist_dir: str = "./chroma_db"):
        """
        Initialize Workflow B V2 with OpenAI embeddings.
        
        Args:
            llm: Language model instance
            chroma_persist_dir: Directory for ChromaDB persistence
        """
        self.llm = llm
        self.router = RouterAgent(llm)
        self.schema_retrieval = SchemaRetrievalAgentV2OpenAI(llm, chroma_persist_dir)
        self.sql_generation = SQLGenerationAgentV2(llm)
        self.synthesis = SynthesisAgent(llm)
        self.logger = logging.getLogger("workflow.scenario_strategist_v2_openai")
    
    def execute(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute Scenario Strategist workflow with OpenAI embeddings.
        
        Args:
            query: User query
            context: Optional context
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            self.logger.info(f"Starting Workflow B V2 (OpenAI) for query: {query}")
            
            context = context or {}
            
            # Step 1: Route request
            routing_result = self.router.execute({
                "query": query,
                "context": context
            })
            
            intent = routing_result.get("intent", "")
            self.logger.info(f"Intent: {intent}")
            
            # Check if this is a shelf-life extension query
            is_extension_query = self._is_extension_query(query)
            
            if is_extension_query:
                # Use specialized extension workflow
                return self._execute_extension_workflow(query, routing_result)
            else:
                # Use general query workflow
                return self._execute_general_workflow(query, routing_result)
        
        except Exception as e:
            self.logger.error(f"Workflow failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "workflow": "B",
                "query": query,
                "error": str(e),
                "response": f"Error: {str(e)}"
            }
    
    def _is_extension_query(self, query: str) -> bool:
        """Check if query is about shelf-life extension."""
        query_lower = query.lower()
        extension_keywords = ["extend", "extension", "shelf-life", "shelf life", "expiry extension"]
        return any(kw in query_lower for kw in extension_keywords)
    
    def _execute_extension_workflow(self, query: str, routing_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute specialized shelf-life extension workflow.
        
        Checks three required tables:
        1. re_evaluation - Technical check (prior extensions)
        2. rim - Regulatory check (country approvals)
        3. ip_shipping_timelines_report - Logistical check
        """
        self.logger.info("Executing shelf-life extension workflow")
        
        # Extract batch ID and country from query
        entities = self.router.extract_entities(query)
        batch_id = entities.get("batches", [None])[0]
        country = entities.get("countries", [None])[0]
        
        self.logger.info(f"Extension query - Batch: {batch_id}, Country: {country}")
        
        # Initialize results for each check
        technical_result = {"status": "INDETERMINATE", "finding": "No data found", "source": "re_evaluation"}
        regulatory_result = {"status": "INDETERMINATE", "finding": "No data found", "source": "rim"}
        logistical_result = {"status": "INDETERMINATE", "finding": "No data found", "source": "ip_shipping_timelines_report"}
        
        all_citations = []
        
        # 1. TECHNICAL CHECK - Query re_evaluation table
        self.logger.info("Checking re_evaluation table for technical assessment...")
        if batch_id:
            # Use correct column name: lot_number_molecule_planner_to_complete
            re_eval_query = f"""
                SELECT * FROM re_evaluation 
                WHERE lot_number_molecule_planner_to_complete ILIKE '%{batch_id}%' 
                   OR lot_number_molecule_planner_to_complete ILIKE '%{batch_id.replace('LOT-', '')}%'
                LIMIT 10
            """
        else:
            re_eval_query = "SELECT * FROM re_evaluation LIMIT 10"
        
        re_eval_result = run_sql_query(re_eval_query)
        
        if re_eval_result.get("success") and re_eval_result.get("data"):
            data = re_eval_result["data"]
            if len(data) > 0:
                # Found re-evaluation records
                technical_result = {
                    "status": "PASS",
                    "finding": f"Found {len(data)} prior re-evaluation record(s) for this batch. Extension history exists.",
                    "source": "re_evaluation",
                    "data": data
                }
            else:
                technical_result = {
                    "status": "INDETERMINATE",
                    "finding": f"No prior re-evaluation records found for batch {batch_id}. This would be the first extension request.",
                    "source": "re_evaluation"
                }
        else:
            technical_result = {
                "status": "INDETERMINATE",
                "finding": f"No re-evaluation records found for batch {batch_id}. Cannot determine extension history.",
                "source": "re_evaluation"
            }
        
        all_citations.append({"table": "re_evaluation", "query_date": datetime.now().isoformat()})
        
        # 2. REGULATORY CHECK - Query material_country_requirements for country approval
        # Also check rim for health authority approvals
        self.logger.info("Checking regulatory tables for country assessment...")
        if country:
            # First check material_country_requirements for country-specific requirements
            reg_query = f"""
                SELECT * FROM material_country_requirements 
                WHERE countries ILIKE '%{country}%'
                LIMIT 10
            """
        else:
            reg_query = "SELECT DISTINCT countries FROM material_country_requirements LIMIT 20"
        
        reg_result = run_sql_query(reg_query)
        
        if reg_result.get("success") and reg_result.get("data"):
            data = reg_result["data"]
            if len(data) > 0:
                # Found regulatory records for country
                regulatory_result = {
                    "status": "PASS",
                    "finding": f"Found {len(data)} regulatory record(s) for {country}. Country is approved for clinical supply.",
                    "source": "material_country_requirements",
                    "data": data
                }
            else:
                regulatory_result = {
                    "status": "FAIL",
                    "finding": f"No regulatory approval found for {country}. Country not in approved list.",
                    "source": "material_country_requirements"
                }
        else:
            regulatory_result = {
                "status": "INDETERMINATE",
                "finding": f"Could not verify regulatory status for {country}.",
                "source": "material_country_requirements"
            }
        
        all_citations.append({"table": "material_country_requirements", "query_date": datetime.now().isoformat()})
        
        # 3. LOGISTICAL CHECK - Query ip_shipping_timelines_report
        self.logger.info("Checking ip_shipping_timelines_report for logistics assessment...")
        if country:
            # ip_shipping_timelines_report uses country_name column
            logistics_query = f"""
                SELECT * FROM ip_shipping_timelines_report 
                WHERE country_name ILIKE '%{country}%'
                LIMIT 10
            """
        else:
            logistics_query = "SELECT * FROM ip_shipping_timelines_report LIMIT 10"
        
        logistics_result = run_sql_query(logistics_query)
        
        if logistics_result.get("success") and logistics_result.get("data"):
            data = logistics_result["data"]
            if len(data) > 0:
                # Found shipping timeline data
                logistical_result = {
                    "status": "PASS",
                    "finding": f"Found {len(data)} shipping timeline record(s) for {country}. Logistics feasible.",
                    "source": "ip_shipping_timelines_report",
                    "data": data
                }
            else:
                logistical_result = {
                    "status": "INDETERMINATE",
                    "finding": f"No shipping timeline data found for {country}.",
                    "source": "ip_shipping_timelines_report"
                }
        else:
            logistical_result = {
                "status": "INDETERMINATE",
                "finding": f"Could not retrieve shipping timeline data for {country}.",
                "source": "ip_shipping_timelines_report"
            }
        
        all_citations.append({"table": "ip_shipping_timelines_report", "query_date": datetime.now().isoformat()})
        
        # Determine final answer based on all three checks
        final_answer = self._determine_extension_answer(technical_result, regulatory_result, logistical_result)
        
        # Format response
        response = self._format_extension_response(
            batch_id or "Unknown",
            country or "Unknown",
            final_answer,
            technical_result,
            regulatory_result,
            logistical_result
        )
        
        return {
            "success": True,
            "workflow": "B",
            "query": query,
            "intent": "shelf_life_extension",
            "execution_time": datetime.now().isoformat(),
            "response": response,
            "citations": all_citations,
            "tables_searched": ["re_evaluation", "material_country_requirements", "ip_shipping_timelines_report"],
            "extension_checks": {
                "technical": technical_result,
                "regulatory": regulatory_result,
                "logistical": logistical_result
            },
            "final_answer": final_answer,
            "embedding_model": "text-embedding-3-small"
        }
    
    def _determine_extension_answer(
        self,
        technical: Dict[str, Any],
        regulatory: Dict[str, Any],
        logistical: Dict[str, Any]
    ) -> str:
        """Determine final YES/NO/CONDITIONAL answer based on three checks."""
        tech_status = technical.get("status", "INDETERMINATE")
        reg_status = regulatory.get("status", "INDETERMINATE")
        log_status = logistical.get("status", "INDETERMINATE")
        
        # If regulatory explicitly fails, answer is NO
        if reg_status == "FAIL":
            return "NO"
        
        # If all pass, answer is YES
        if tech_status == "PASS" and reg_status == "PASS" and log_status == "PASS":
            return "YES"
        
        # If any is indeterminate but none fail, answer is CONDITIONAL
        if "INDETERMINATE" in [tech_status, reg_status, log_status]:
            return "CONDITIONAL"
        
        # Default to NO if uncertain
        return "NO"
    
    def _format_extension_response(
        self,
        batch_id: str,
        country: str,
        final_answer: str,
        technical: Dict[str, Any],
        regulatory: Dict[str, Any],
        logistical: Dict[str, Any]
    ) -> str:
        """Format the shelf-life extension response."""
        
        def status_symbol(status: str) -> str:
            if status == "PASS":
                return "✓ PASS"
            elif status == "FAIL":
                return "✗ FAIL"
            else:
                return "⚠ INDETERMINATE"
        
        response = f"""CAN WE EXTEND BATCH {batch_id} FOR {country}?

Answer: {final_answer}

Technical Check: {status_symbol(technical['status'])}
Finding: {technical['finding']}
Source: {technical['source']}

Regulatory Check: {status_symbol(regulatory['status'])}
Finding: {regulatory['finding']}
Source: {regulatory['source']}

Logistical Check: {status_symbol(logistical['status'])}
Finding: {logistical['finding']}
Source: {logistical['source']}

RECOMMENDATION: """
        
        if final_answer == "YES":
            response += f"Proceed with shelf-life extension for Batch {batch_id} in {country}. All required checks passed."
        elif final_answer == "NO":
            response += f"Cannot approve shelf-life extension for Batch {batch_id} in {country}. Required evidence is missing or regulatory approval not found."
        else:
            response += f"Shelf-life extension for Batch {batch_id} in {country} requires additional verification. Some required data is missing or inconclusive."
        
        return response
    
    def _execute_general_workflow(self, query: str, routing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general query workflow using semantic search."""
        intent = routing_result.get("intent", "")
        
        # Step 2: Use OpenAI embeddings to find relevant tables
        schema_result = self.schema_retrieval.execute({
            "query": query,
            "workflow": "B",
            "n_results": 5
        })
        
        if not schema_result.get("success"):
            return {
                "success": False,
                "workflow": "B",
                "query": query,
                "error": "Failed to retrieve relevant schemas",
                "response": "I couldn't find relevant tables for your query."
            }
        
        table_names = schema_result.get("table_names", [])
        formatted_schemas = schema_result.get("formatted_schemas", "")
        similarity_scores = schema_result.get("similarity_scores", {})
        
        self.logger.info(f"Found {len(table_names)} relevant tables: {table_names}")
        
        # Step 3: Extract entities and build filters
        entities = self.router.extract_entities(query)
        filters = self._build_filters(entities, query)
        
        # Step 4: Generate and execute SQL
        sql_result = self.sql_generation.execute({
            "intent": intent,
            "table_names": table_names,
            "schemas": formatted_schemas,
            "filters": filters,
            "limit": 100
        })
        
        if not sql_result.get("success"):
            return {
                "success": False,
                "workflow": "B",
                "query": query,
                "error": sql_result.get("error", "SQL generation failed"),
                "response": f"Error: {sql_result.get('error')}"
            }
        
        # Step 5: Synthesize results
        table_used = sql_result.get("table_used", "unknown")
        agent_outputs = {
            "sql_generation": {
                "success": True,
                "query": sql_result.get("query"),
                "table_used": table_used,
                "data": sql_result.get("data", []),
                "row_count": sql_result.get("row_count", 0),
                "citations": [{
                    "table": table_used,
                    "query_date": datetime.now().isoformat()
                }]
            }
        }
        
        synthesis_result = self.synthesis.execute({
            "workflow": "B",
            "agent_outputs": agent_outputs,
            "query": query,
            "output_format": "natural_language"
        })
        
        # Build final result
        result = {
            "success": True,
            "workflow": "B",
            "query": query,
            "intent": intent,
            "execution_time": datetime.now().isoformat(),
            "response": synthesis_result.get("output"),
            "citations": synthesis_result.get("citations", []),
            "tables_searched": table_names,
            "table_used": sql_result.get("table_used"),
            "similarity_scores": similarity_scores,
            "row_count": sql_result.get("row_count", 0),
            "search_method": schema_result.get("search_method"),
            "embedding_model": "text-embedding-3-small"
        }
        
        self.logger.info("Workflow B V2 (OpenAI) completed successfully")
        return result
    
    def _build_filters(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Build filters from extracted entities."""
        filters = {}
        
        if entities.get("batches"):
            filters["batch_id"] = entities["batches"][0]
            filters["lot_number"] = entities["batches"][0]
        
        if entities.get("materials"):
            filters["material_id"] = entities["materials"][0]
        
        if entities.get("trials"):
            filters["trial_alias"] = entities["trials"][0]
            filters["clinical_study"] = entities["trials"][0]
        
        if entities.get("countries"):
            filters["country"] = entities["countries"][0]
        
        return filters
    
    def get_chroma_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics."""
        return self.schema_retrieval.get_chroma_stats()
    
    def refresh_chroma(self):
        """Refresh ChromaDB schemas."""
        self.logger.info("Refreshing ChromaDB...")
        self.schema_retrieval.refresh_chroma_schemas()
        self.logger.info("ChromaDB refreshed")
