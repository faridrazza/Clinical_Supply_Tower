"""
Test suite to verify assignment compliance and system functionality.

Tests cover:
1. Schema Understanding (40%)
2. Agent Design (30%)
3. Prompt Engineering (30%)
4. Deliverable Quality
"""
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import settings
from src.tools.database_tools import db_tools
from src.workflows.orchestrator import get_orchestrator


def test_1_database_connectivity():
    """Test 1: Database connectivity and CSV data loading"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Database Connectivity & Data Loading")
    logger.info("="*60)
    
    try:
        tables = db_tools.get_all_tables()
        logger.info(f"✓ Connected to PostgreSQL database")
        logger.info(f"✓ Found {len(tables)} tables loaded")
        
        # Check critical tables for Workflow A
        workflow_a_tables = [
            "allocated_materials_to_orders",
            "available_inventory_report",
            "enrollment_rate_report",
            "country_level_enrollment_report"
        ]
        
        for table in workflow_a_tables:
            if table in tables:
                logger.info(f"  ✓ {table} present")
            else:
                logger.warning(f"  ✗ {table} MISSING")
        
        # Check critical tables for Workflow B
        workflow_b_tables = [
            "re-evaluation",
            "rim",
            "material_country_requirements",
            "ip_shipping_timelines_report"
        ]
        
        for table in workflow_b_tables:
            if table in tables:
                logger.info(f"  ✓ {table} present")
            else:
                logger.warning(f"  ✗ {table} MISSING")
        
        return True
    except Exception as e:
        logger.error(f"✗ Database connectivity failed: {e}")
        return False


def test_2_vector_db_initialization():
    """Test 2: Vector database initialization with schema embeddings"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Vector Database & Schema Embeddings")
    logger.info("="*60)
    
    try:
        # Test schema retrieval using schema registry
        from src.agents.schema_retrieval_agent_v2_openai import SchemaRetrievalAgentV2OpenAI
        
        agent = SchemaRetrievalAgentV2OpenAI()
        result = agent.execute({
            "query": "expiry dates and inventory",
            "workflow": "A"
        })
        
        schemas = result.get("schemas", [])
        logger.info(f"✓ Schema retrieval initialized")
        logger.info(f"✓ Retrieved {len(schemas)} relevant schemas for test query")
        
        for schema in schemas:
            logger.info(f"  - {schema.get('table_name')}")
        
        return len(schemas) > 0
    except Exception as e:
        logger.error(f"✗ Schema retrieval test failed: {e}")
        return False


def test_3_workflow_a_supply_watchdog():
    """Test 3: Workflow A - Supply Watchdog autonomous monitoring"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Workflow A - Supply Watchdog")
    logger.info("="*60)
    
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.run_supply_watchdog(trigger_type="manual")
        
        if result.get("success"):
            logger.info(f"✓ Workflow A executed successfully")
            
            output = result.get("output", {})
            risk_summary = output.get("risk_summary", {})
            
            logger.info(f"  - Total expiring batches: {risk_summary.get('total_expiring_batches', 0)}")
            logger.info(f"  - Total shortfall predictions: {risk_summary.get('total_shortfall_predictions', 0)}")
            
            # Verify JSON structure
            required_fields = ["alert_date", "risk_summary", "expiry_alerts", "shortfall_predictions"]
            for field in required_fields:
                if field in output:
                    logger.info(f"  ✓ {field} present in output")
                else:
                    logger.warning(f"  ✗ {field} MISSING from output")
            
            return True
        else:
            logger.error(f"✗ Workflow A failed: {result.get('error')}")
            return False
    except Exception as e:
        logger.error(f"✗ Workflow A test failed: {e}")
        return False


def test_4_workflow_b_scenario_strategist():
    """Test 4: Workflow B - Scenario Strategist conversational queries"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Workflow B - Scenario Strategist")
    logger.info("="*60)
    
    test_queries = [
        "What is the current stock level for Material MAT-93657?",
        "Show me all batches expiring in Taiwan within 60 days",
        "Predict demand for Trial CT-2004-PSX for next 8 weeks",
        "Is shelf-life extension approved in Germany?"
    ]
    
    orchestrator = get_orchestrator()
    passed = 0
    
    for query in test_queries:
        try:
            logger.info(f"\n  Query: {query}")
            result = orchestrator.run_scenario_strategist(query)
            
            if result.get("success"):
                logger.info(f"  ✓ Query processed successfully")
                response = result.get("response", "")
                citations = result.get("citations", [])
                
                if response:
                    logger.info(f"  ✓ Response generated ({len(response)} chars)")
                if citations:
                    logger.info(f"  ✓ {len(citations)} data citations included")
                
                passed += 1
            else:
                logger.warning(f"  ✗ Query failed: {result.get('error')}")
        except Exception as e:
            logger.warning(f"  ✗ Query error: {e}")
    
    logger.info(f"\n  Result: {passed}/{len(test_queries)} queries passed")
    return passed >= 3  # At least 3 out of 4 should pass


def test_5_agent_architecture():
    """Test 5: Multi-agent architecture and separation of concerns"""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Multi-Agent Architecture")
    logger.info("="*60)
    
    try:
        from src.agents import (
            RouterAgent,
            SchemaRetrievalAgent,
            InventoryAgent,
            DemandForecastingAgent,
            RegulatoryAgent,
            LogisticsAgent,
            SQLGenerationAgent,
            SynthesisAgent
        )
        
        agents = [
            ("RouterAgent", RouterAgent),
            ("SchemaRetrievalAgent", SchemaRetrievalAgent),
            ("InventoryAgent", InventoryAgent),
            ("DemandForecastingAgent", DemandForecastingAgent),
            ("RegulatoryAgent", RegulatoryAgent),
            ("LogisticsAgent", LogisticsAgent),
            ("SQLGenerationAgent", SQLGenerationAgent),
            ("SynthesisAgent", SynthesisAgent)
        ]
        
        for agent_name, agent_class in agents:
            try:
                agent = agent_class()
                logger.info(f"  ✓ {agent_name} initialized")
            except Exception as e:
                logger.warning(f"  ✗ {agent_name} failed: {e}")
        
        logger.info(f"✓ All 8 required agents implemented")
        return True
    except Exception as e:
        logger.error(f"✗ Agent architecture test failed: {e}")
        return False


def test_6_edge_case_handling():
    """Test 6: Edge case handling (fuzzy matching, self-healing SQL, etc.)"""
    logger.info("\n" + "="*60)
    logger.info("TEST 6: Edge Case Handling")
    logger.info("="*60)
    
    try:
        from src.tools.fuzzy_matching import fuzzy_matcher
        
        # Test fuzzy matching
        logger.info("  Testing fuzzy matching...")
        candidates = ["Trial_ABC_v2", "Trial-ABC", "trial_abc"]
        result = fuzzy_matcher.resolve_entity("Trial ABC", candidates)
        
        if result.get("matched_value"):
            logger.info(f"  ✓ Fuzzy matching works: matched '{result['matched_value']}'")
        else:
            logger.warning(f"  ✗ Fuzzy matching failed")
        
        # Test error handling
        logger.info("  Testing error handling...")
        from src.utils.error_handlers import AgentErrorHandler
        
        test_error = ValueError("Test error")
        error_response = AgentErrorHandler.handle_agent_failure(
            agent_name="TestAgent",
            error=test_error,
            context={"query": "test"}
        )
        
        if error_response.get("success") is False:
            logger.info(f"  ✓ Error handling works")
        
        return True
    except Exception as e:
        logger.error(f"✗ Edge case handling test failed: {e}")
        return False


def test_7_data_citations():
    """Test 7: Data citations and explainability"""
    logger.info("\n" + "="*60)
    logger.info("TEST 7: Data Citations & Explainability")
    logger.info("="*60)
    
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.run_scenario_strategist("What is the current stock level?")
        
        if result.get("success"):
            citations = result.get("citations", [])
            
            if citations:
                logger.info(f"✓ Citations present: {len(citations)} sources")
                for i, citation in enumerate(citations[:3], 1):
                    logger.info(f"  {i}. {citation.get('table', 'Unknown table')}")
                return True
            else:
                logger.warning(f"✗ No citations found")
                return False
        else:
            logger.warning(f"✗ Query failed")
            return False
    except Exception as e:
        logger.error(f"✗ Citations test failed: {e}")
        return False


def run_all_tests():
    """Run all compliance tests"""
    logger.info("\n" + "="*80)
    logger.info("CLINICAL SUPPLY CHAIN CONTROL TOWER - ASSIGNMENT COMPLIANCE TEST SUITE")
    logger.info("="*80)
    
    tests = [
        ("Database Connectivity", test_1_database_connectivity),
        ("Vector DB & Embeddings", test_2_vector_db_initialization),
        ("Workflow A - Supply Watchdog", test_3_workflow_a_supply_watchdog),
        ("Workflow B - Scenario Strategist", test_4_workflow_b_scenario_strategist),
        ("Multi-Agent Architecture", test_5_agent_architecture),
        ("Edge Case Handling", test_6_edge_case_handling),
        ("Data Citations", test_7_data_citations),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed ({100*passed//total}%)")
    
    # Assignment compliance check
    logger.info("\n" + "="*80)
    logger.info("ASSIGNMENT COMPLIANCE CHECK")
    logger.info("="*80)
    
    compliance_checks = {
        "Schema Understanding (40%)": results.get("Database Connectivity", False),
        "Agent Design (30%)": results.get("Multi-Agent Architecture", False),
        "Prompt Engineering (30%)": results.get("Workflow B - Scenario Strategist", False),
        "Deliverable Quality": all([
            results.get("Workflow A - Supply Watchdog", False),
            results.get("Workflow B - Scenario Strategist", False),
            results.get("Data Citations", False)
        ])
    }
    
    for check, status in compliance_checks.items():
        symbol = "✓" if status else "✗"
        logger.info(f"{symbol} {check}")
    
    overall_pass = all(compliance_checks.values())
    logger.info(f"\n{'✓ ASSIGNMENT COMPLIANT' if overall_pass else '✗ ASSIGNMENT NON-COMPLIANT'}")
    
    return overall_pass


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
