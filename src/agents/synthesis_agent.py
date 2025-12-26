"""
Synthesis Agent - Response aggregation and formatting with LLM reasoning.
"""
from typing import Dict, Any, List
from datetime import datetime
import json
import logging
from .base_agent import BaseAgent
from src.config.prompts import SYNTHESIS_AGENT_PROMPT

logger = logging.getLogger(__name__)


class SynthesisAgent(BaseAgent):
    """
    Synthesis Agent aggregates outputs and formats final responses using LLM reasoning.
    
    Responsibilities:
    - Combine outputs from multiple agents
    - Use LLM to reason over aggregated data
    - Generate structured JSON for Workflow A
    - Produce natural language responses with citations for Workflow B
    - Ensure all responses include data citations and reasoning
    """
    
    def __init__(self, llm=None):
        super().__init__("SynthesisAgent", llm)
        # Initialize LLM for reasoning if not provided
        if self.llm is None:
            try:
                from langchain_openai import ChatOpenAI
                from src.config.settings import settings
                self.llm = ChatOpenAI(
                    model_name=settings.llm_model,
                    temperature=0.3,  # Lower temperature for factual reasoning
                    api_key=settings.openai_api_key
                )
            except Exception as e:
                logger.warning(f"Could not initialize LLM: {e}. Falling back to template-based synthesis.")
                self.llm = None
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute synthesis operations with LLM reasoning.
        
        Args:
            input_data: {
                "workflow": str,  # "A" or "B"
                "agent_outputs": Dict,  # Outputs from other agents
                "query": str,  # Original user query (for Workflow B)
                "output_format": str  # "json" or "natural_language"
            }
            
        Returns:
            {
                "success": bool,
                "workflow": str,
                "output": Dict or str,  # Formatted output
                "citations": List[Dict]  # All data sources
            }
        """
        try:
            workflow = input_data.get("workflow", "B")
            agent_outputs = input_data.get("agent_outputs", {})
            query = input_data.get("query", "")
            output_format = input_data.get("output_format", "natural_language")
            
            # Synthesize based on workflow
            if workflow == "A" or output_format == "json":
                result = self._synthesize_workflow_a(agent_outputs)
            elif output_format == "extension_assessment":
                result = self._synthesize_extension_assessment(agent_outputs, query)
            else:
                result = self._synthesize_workflow_b(agent_outputs, query)
            
            self.log_execution(input_data, result)
            return result
        
        except Exception as e:
            return self.handle_error(e, input_data)
    
    def _synthesize_workflow_a(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize Workflow A output (Supply Watchdog JSON).
        
        Args:
            agent_outputs: {
                "inventory": Dict,  # From Inventory Agent
                "demand": Dict  # From Demand Forecasting Agent
            }
            
        Returns:
            Dictionary with structured JSON output
        """
        inventory_output = agent_outputs.get("inventory", {})
        demand_output = agent_outputs.get("demand", {})
        
        # Extract expiry alerts
        expiry_alerts = []
        if inventory_output.get("success"):
            batches_by_severity = inventory_output.get("batches_by_severity", {})
            
            for severity in ["CRITICAL", "HIGH", "MEDIUM"]:
                for batch in batches_by_severity.get(severity, []):
                    expiry_alerts.append({
                        "severity": severity,
                        "batch_id": batch.get("batch_id", batch.get("lot")),
                        "material": batch.get("material", batch.get("package_type_description")),
                        "location": batch.get("location"),
                        "expiry_date": batch.get("expiry_date"),
                        "days_remaining": batch.get("days_remaining"),
                        "quantity": batch.get("quantity", batch.get("received_packages")),
                        "unit": batch.get("unit", "packages")
                    })
        
        # Extract shortfall predictions
        shortfall_predictions = []
        if demand_output.get("success"):
            shortfalls = demand_output.get("shortfalls", [])
            
            for shortfall in shortfalls:
                shortfall_predictions.append({
                    "country": shortfall.get("country"),
                    "material": shortfall.get("trial_alias"),  # Using trial as material proxy
                    "current_stock": shortfall.get("current_stock"),
                    "projected_8week_demand": shortfall.get("projected_demand"),
                    "shortfall": abs(shortfall.get("shortfall")),
                    "estimated_stockout_date": shortfall.get("estimated_stockout_date")
                })
        
        # Collect all citations
        all_citations = []
        if inventory_output.get("citations"):
            all_citations.extend(inventory_output["citations"])
        if demand_output.get("citations"):
            all_citations.extend(demand_output["citations"])
        
        # Generate JSON output
        json_output = {
            "alert_date": datetime.now().strftime("%Y-%m-%d"),
            "risk_summary": {
                "total_expiring_batches": len(expiry_alerts),
                "total_shortfall_predictions": len(shortfall_predictions)
            },
            "expiry_alerts": expiry_alerts,
            "shortfall_predictions": shortfall_predictions
        }
        
        return {
            "success": True,
            "workflow": "A",
            "output_format": "json",
            "output": json_output,
            "json_string": json.dumps(json_output, indent=2),
            "citations": all_citations,
            "summary": {
                "expiring_batches": len(expiry_alerts),
                "shortfalls": len(shortfall_predictions),
                "critical_batches": len([a for a in expiry_alerts if a["severity"] == "CRITICAL"])
            }
        }
    
    def _synthesize_extension_assessment(
        self,
        agent_outputs: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """
        Synthesize shelf-life extension assessment with LLM reasoning.
        
        Uses actual data from database to provide detailed citations.
        """
        extension_data = agent_outputs.get("extension_assessment", {})
        
        batch_id = extension_data.get("batch_id", "Unknown")
        country = extension_data.get("country", "Unknown")
        final_answer = extension_data.get("final_answer", "INDETERMINATE")
        checks = extension_data.get("checks", {})
        
        # Format data for LLM
        technical = checks.get("technical", {})
        regulatory = checks.get("regulatory", {})
        logistical = checks.get("logistical", {})
        
        # Build detailed data summary
        data_summary = f"""
BATCH: {batch_id}
COUNTRY: {country}
FINAL ANSWER: {final_answer}

=== TECHNICAL CHECK (re_evaluation table) ===
Status: {technical.get('status', 'UNKNOWN')}
Data found: {len(technical.get('data', []))} record(s)
"""
        # Add actual technical data
        for i, record in enumerate(technical.get('data', [])[:3], 1):
            data_summary += f"\nRecord {i}:\n"
            for key, value in record.items():
                data_summary += f"  {key}: {value}\n"
        
        data_summary += f"""
=== REGULATORY CHECK (material_country_requirements table) ===
Status: {regulatory.get('status', 'UNKNOWN')}
Data found: {len(regulatory.get('data', []))} record(s)
"""
        # Add actual regulatory data
        for i, record in enumerate(regulatory.get('data', [])[:3], 1):
            data_summary += f"\nRecord {i}:\n"
            for key, value in record.items():
                data_summary += f"  {key}: {value}\n"
        
        data_summary += f"""
=== LOGISTICAL CHECK (ip_shipping_timelines_report table) ===
Status: {logistical.get('status', 'UNKNOWN')}
Data found: {len(logistical.get('data', []))} record(s)
"""
        # Add actual logistical data
        for i, record in enumerate(logistical.get('data', [])[:3], 1):
            data_summary += f"\nRecord {i}:\n"
            for key, value in record.items():
                data_summary += f"  {key}: {value}\n"
        
        # Use LLM to format response with actual data citations
        if self.llm:
            try:
                reasoning_prompt = f"""You are analyzing a shelf-life extension request for a pharmaceutical batch.

USER QUERY: {query}

{data_summary}

IMPORTANT RULES:
1. Use ONLY the data provided above - DO NOT hallucinate or make up data
2. If a check has no data (0 records), report it as INDETERMINATE
3. Cite specific field values from the records (e.g., "Re-evaluation ID: REV-123, Request Type: Extension")
4. The final answer is already determined as: {final_answer}

Format your response as:

[DIRECT ANSWER]
State whether the extension can proceed: {final_answer}

[DETAILED ANALYSIS with specific data points]

Technical Check: [✓ PASS / ✗ FAIL / ⚠ INDETERMINATE]
- If data exists, cite specific values: ID, request type, status, dates
- If no data, state "No re-evaluation records found for this batch"
- Source: re_evaluation table

Regulatory Check: [✓ PASS / ✗ FAIL / ⚠ INDETERMINATE]  
- If data exists, cite specific values: country, compound, approval status
- If no data, state "No regulatory records found for {country}"
- Source: material_country_requirements table

Logistical Check: [✓ PASS / ✗ FAIL / ⚠ INDETERMINATE]
- If data exists, cite specific values: shipping timeline, country
- If no data, state "No shipping timeline data found for {country}"
- Source: ip_shipping_timelines_report table

RECOMMENDATION: Based on the {final_answer} result, provide actionable guidance.

Data Sources:
[List the tables checked with record counts]"""

                response = self.llm.invoke(reasoning_prompt)
                
                return {
                    "success": True,
                    "workflow": "B",
                    "output_format": "extension_assessment",
                    "output": response.content,
                    "citations": extension_data.get("citations", []),
                    "query": query
                }
            except Exception as e:
                logger.error(f"LLM reasoning failed for extension: {e}")
        
        # Fallback to template response
        return {
            "success": True,
            "workflow": "B", 
            "output_format": "extension_assessment",
            "output": self._format_extension_fallback(batch_id, country, final_answer, checks),
            "citations": extension_data.get("citations", []),
            "query": query
        }
    
    def _format_extension_fallback(
        self,
        batch_id: str,
        country: str,
        final_answer: str,
        checks: Dict[str, Any]
    ) -> str:
        """Fallback template for extension response."""
        def status_symbol(status: str) -> str:
            if status == "PASS":
                return "✓ PASS"
            elif status == "FAIL":
                return "✗ FAIL"
            else:
                return "⚠ INDETERMINATE"
        
        technical = checks.get("technical", {})
        regulatory = checks.get("regulatory", {})
        logistical = checks.get("logistical", {})
        
        response = f"""CAN WE EXTEND BATCH {batch_id} FOR {country}?

Answer: {final_answer}

Technical Check: {status_symbol(technical.get('status', 'INDETERMINATE'))}
Source: {technical.get('source', 're_evaluation')}

Regulatory Check: {status_symbol(regulatory.get('status', 'INDETERMINATE'))}
Source: {regulatory.get('source', 'material_country_requirements')}

Logistical Check: {status_symbol(logistical.get('status', 'INDETERMINATE'))}
Source: {logistical.get('source', 'ip_shipping_timelines_report')}
"""
        return response
    
    def _synthesize_workflow_b(
        self,
        agent_outputs: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """
        Synthesize Workflow B output with LLM reasoning over aggregated data.
        
        Args:
            agent_outputs: Outputs from various agents
            query: Original user query
            
        Returns:
            Dictionary with natural language response
        """
        # Determine query type
        is_extension_query = "extend" in query.lower() or "extension" in query.lower()
        
        # Collect all data and citations
        all_data = self._aggregate_agent_data(agent_outputs)
        all_citations = self._collect_all_citations(agent_outputs)
        
        # Use LLM to reason over the aggregated data
        if is_extension_query:
            response = self._reason_extension_query(query, all_data, all_citations)
        else:
            response = self._reason_general_query(query, all_data, all_citations)
        
        return {
            "success": True,
            "workflow": "B",
            "output_format": "natural_language",
            "output": response,
            "citations": all_citations,
            "query": query
        }
    
    def _aggregate_agent_data(self, agent_outputs: Dict[str, Any]) -> str:
        """
        Aggregate all agent outputs into a structured text format for LLM reasoning.
        
        Args:
            agent_outputs: Outputs from all agents
            
        Returns:
            Formatted text with all data
        """
        data_parts = []
        
        for agent_name, output in agent_outputs.items():
            if not isinstance(output, dict):
                continue
            
            if output.get("success"):
                # Get the actual table(s) queried from citations
                tables_queried = []
                if output.get("citations"):
                    for citation in output["citations"]:
                        table = citation.get("table")
                        if table and table not in tables_queried:
                            tables_queried.append(table)
                
                # Use table names in header if available, otherwise use agent name
                if tables_queried:
                    header = f"=== {', '.join(tables_queried).upper()} ==="
                else:
                    header = f"=== {agent_name.upper()} ==="
                
                data_parts.append(f"\n{header}")
                
                # Add summary if available
                if output.get("summary_text"):
                    data_parts.append(output["summary_text"])
                
                # Add structured data
                if output.get("data"):
                    data = output["data"]
                    if isinstance(data, list):
                        data_parts.append(f"Records found: {len(data)}")
                        for i, record in enumerate(data[:10], 1):  # Show first 10
                            data_parts.append(f"\nRecord {i}:")
                            for key, value in record.items():
                                data_parts.append(f"  {key}: {value}")
                    elif isinstance(data, dict):
                        for key, value in data.items():
                            data_parts.append(f"{key}: {value}")
                
                # Add summary dict if available
                if output.get("summary") and isinstance(output["summary"], dict):
                    data_parts.append("\nSummary:")
                    for key, value in output["summary"].items():
                        data_parts.append(f"  {key}: {value}")
            else:
                # Agent failed - include error info
                data_parts.append(f"\n=== {agent_name.upper()} ===")
                data_parts.append(f"Status: FAILED")
                data_parts.append(f"Error: {output.get('error', 'Unknown error')}")
        
        if not data_parts:
            return "No data retrieved from agents."
        
        return "\n".join(data_parts)
    
    def _collect_all_citations(self, agent_outputs: Dict[str, Any]) -> List[Dict]:
        """Collect all citations from all agents."""
        all_citations = []
        for agent_name, output in agent_outputs.items():
            if isinstance(output, dict) and output.get("citations"):
                all_citations.extend(output["citations"])
        return all_citations
    
    def _reason_extension_query(
        self,
        query: str,
        aggregated_data: str,
        citations: List[Dict]
    ) -> str:
        """
        Use LLM to reason over shelf-life extension data.
        
        Args:
            query: Original user query
            aggregated_data: All collected data
            citations: All data sources
            
        Returns:
            Reasoned response
        """
        if not self.llm:
            return self._format_extension_response(aggregated_data, query)
        
        reasoning_prompt = f"""You are analyzing a shelf-life extension request for a pharmaceutical batch.

USER QUERY: {query}

AGGREGATED DATA FROM AGENTS:
{aggregated_data}

Your task:
1. Analyze the three constraints: Technical, Regulatory, and Logistical
2. Provide a clear YES/NO/CONDITIONAL answer
3. Explain your reasoning with specific data points
4. Cite the sources for each finding
5. If data is missing or conflicting, state it explicitly
6. Aggregate any duplicate locations or batches (e.g., if Saint Kitts and Nevis appears twice, sum the quantities)

Response format:
CAN WE EXTEND [BATCH] FOR [COUNTRY]?

Answer: [YES / NO / CONDITIONAL]

Technical Check: [✓ PASS / ✗ FAIL]
- Finding: [specific data point]
- Source: [table name]

Regulatory Check: [✓ PASS / ✗ FAIL]
- Finding: [specific data point]
- Source: [table name]

Logistical Check: [✓ PASS / ⚠ CONDITIONAL / ✗ FAIL]
- Finding: [specific data point with calculation]
- Source: [table name]

RECOMMENDATION: [Clear action statement]

IMPORTANT: Be precise, cite data, aggregate duplicates, and explain your reasoning clearly."""
        
        try:
            response = self.llm.invoke(reasoning_prompt)
            return response.content
        
        except Exception as e:
            logger.error(f"LLM reasoning failed: {str(e)}")
            return self._format_extension_response(aggregated_data, query)
    
    def _reason_general_query(
        self,
        query: str,
        aggregated_data: str,
        citations: List[Dict]
    ) -> str:
        """
        Use LLM to reason over general query data.
        
        Args:
            query: Original user query
            aggregated_data: All collected data
            citations: All data sources
            
        Returns:
            Reasoned response
        """
        if not self.llm:
            return self._format_general_response(aggregated_data, query)
        
        # Extract table names from citations for context
        tables_used = []
        for citation in citations:
            table = citation.get("table")
            if table and table not in tables_used:
                tables_used.append(table)
        
        tables_context = f"Data sources: {', '.join(tables_used)}" if tables_used else "Data sources: Multiple tables"
        
        reasoning_prompt = f"""You are a supply chain analyst answering a user query about pharmaceutical inventory and logistics.

USER QUERY: {query}

{tables_context}

AGGREGATED DATA FROM AGENTS:
{aggregated_data}

Your task:
1. Answer the user's question directly and clearly using ONLY the data provided
2. Provide specific data points from the aggregated data
3. Aggregate any duplicate entries (e.g., if a location appears multiple times, sum quantities)
4. Cite the sources for each finding
5. If data is missing or conflicting, state it explicitly
6. Explain any calculations or reasoning
7. IMPORTANT: Use data from the tables listed above, not from other sources

Response format:
[DIRECT ANSWER]

[DETAILED ANALYSIS with specific data points]

Data Sources:
- [Table name]: [specific finding]
- [Table name]: [specific finding]

IMPORTANT: Be precise, cite data, aggregate duplicates, and explain your reasoning clearly. Use ONLY the data provided above."""
        
        try:
            response = self.llm.invoke(reasoning_prompt)
            return response.content
        
        except Exception as e:
            logger.error(f"LLM reasoning failed: {str(e)}")
            return self._format_general_response(aggregated_data, query)
    
    def _format_extension_response(
        self,
        agent_outputs: Dict[str, Any],
        query: str
    ) -> str:
        """
        Format shelf-life extension feasibility response.
        
        Args:
            agent_outputs: {
                "inventory": Dict,
                "regulatory": Dict,
                "logistics": Dict
            }
            query: Original query
            
        Returns:
            Formatted response string
        """
        inventory_output = agent_outputs.get("inventory", {})
        regulatory_output = agent_outputs.get("regulatory", {})
        logistics_output = agent_outputs.get("logistics", {})
        
        # Extract batch ID and country from query or outputs
        batch_id = "Unknown"
        country = "Unknown"
        
        if inventory_output.get("batch_id"):
            batch_id = inventory_output["batch_id"]
        if regulatory_output.get("country"):
            country = regulatory_output["country"]
        
        # Determine overall answer
        technical_pass = regulatory_output.get("technical_check", {}).get("result") == "PASS"
        regulatory_pass = regulatory_output.get("check_result") == "PASS"
        logistics_pass = logistics_output.get("check_result") in ["PASS", "CONDITIONAL"]
        
        if technical_pass and regulatory_pass and logistics_pass:
            answer = "YES"
        elif not technical_pass or not regulatory_pass:
            answer = "NO"
        else:
            answer = "CONDITIONAL"
        
        # Build response
        response_parts = [
            f"CAN WE EXTEND BATCH {batch_id} FOR {country}?",
            "",
            f"Answer: {answer}",
            ""
        ]
        
        # Technical Check
        if regulatory_output.get("technical_check"):
            tech_check = regulatory_output["technical_check"]
            status = "✓ PASS" if tech_check["result"] == "PASS" else "✗ FAIL"
            response_parts.extend([
                f"Technical Check: {status}",
                f"- {tech_check.get('finding', 'No finding available')}",
                f"- Source: re_evaluation table, {tech_check.get('extension_count', 0)} extensions found",
                ""
            ])
        
        # Regulatory Check
        if regulatory_output.get("check_result"):
            status = "✓ PASS" if regulatory_pass else "✗ FAIL"
            response_parts.extend([
                f"Regulatory Check: {status}",
                f"- {regulatory_output.get('finding', 'No finding available')}",
                f"- Source: rim table, Health Authority: {regulatory_output.get('health_authority', 'N/A')}",
                ""
            ])
        
        # Logistical Check
        if logistics_output.get("check_result"):
            result = logistics_output["check_result"]
            if result == "PASS":
                status = "✓ PASS"
            elif result == "CONDITIONAL":
                status = "⚠ CONDITIONAL"
            else:
                status = "✗ FAIL"
            
            response_parts.extend([
                f"Logistical Check: {status}",
                f"- {logistics_output.get('finding', 'No finding available')}",
                f"- Calculation: {logistics_output.get('calculation', 'N/A')}",
                f"- Source: ip_shipping_timelines_report table",
                ""
            ])
        
        # Recommendation
        if answer == "YES":
            recommendation = f"RECOMMENDATION: Proceed with shelf-life extension for Batch {batch_id} in {country}. All checks passed."
        elif answer == "NO":
            recommendation = f"RECOMMENDATION: Do NOT proceed with shelf-life extension for Batch {batch_id} in {country}. Critical checks failed."
        else:
            recommendation = f"RECOMMENDATION: Shelf-life extension for Batch {batch_id} in {country} is possible but requires careful monitoring due to tight timelines."
        
        response_parts.append(recommendation)
        
        return "\n".join(response_parts)
    
    def _format_general_response(
        self,
        agent_outputs: Dict[str, Any],
        query: str
    ) -> str:
        """
        Format general query response.
        
        Args:
            agent_outputs: Outputs from agents
            query: Original query
            
        Returns:
            Formatted response string
        """
        response_parts = []
        
        # Inventory information
        if "inventory" in agent_outputs:
            inv_output = agent_outputs["inventory"]
            if inv_output.get("success"):
                if inv_output.get("found") is False:
                    response_parts.append(f"Batch {inv_output.get('batch_id')} not found in available inventory.")
                elif inv_output.get("data"):
                    data = inv_output["data"]
                    if isinstance(data, list) and len(data) > 0:
                        response_parts.append(f"Found {len(data)} inventory record(s):")
                        for item in data[:5]:  # Show first 5
                            response_parts.append(f"  - Location: {item.get('location')}, Stock: {item.get('received_packages')} packages")
                    
                    if inv_output.get("summary_text"):
                        response_parts.append(f"\n{inv_output['summary_text']}")
        
        # Demand information
        if "demand" in agent_outputs:
            demand_output = agent_outputs["demand"]
            if demand_output.get("success") and demand_output.get("summary_text"):
                response_parts.append(f"\n{demand_output['summary_text']}")
        
        # Regulatory information
        if "regulatory" in agent_outputs:
            reg_output = agent_outputs["regulatory"]
            if reg_output.get("success") and reg_output.get("summary_text"):
                response_parts.append(f"\n{reg_output['summary_text']}")
        
        # Logistics information
        if "logistics" in agent_outputs:
            log_output = agent_outputs["logistics"]
            if log_output.get("success") and log_output.get("summary_text"):
                response_parts.append(f"\n{log_output['summary_text']}")
        
        # Add data sources
        response_parts.append("\n--- Data Sources ---")
        for agent_name, output in agent_outputs.items():
            if isinstance(output, dict) and output.get("citations"):
                for citation in output["citations"]:
                    table = citation.get("table", "Unknown")
                    response_parts.append(f"- {table} (queried: {citation.get('query_date', 'N/A')})")
        
        return "\n".join(response_parts) if response_parts else "No information available for this query."
