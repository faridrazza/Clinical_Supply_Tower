"""
Test script for workflow orchestration.

This script demonstrates both workflows without requiring database connection.
"""
import logging
from src.workflows import get_orchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_workflow_a():
    """Test Workflow A: Supply Watchdog"""
    print("\n" + "="*80)
    print("TESTING WORKFLOW A: SUPPLY WATCHDOG")
    print("="*80 + "\n")
    
    orchestrator = get_orchestrator()
    
    try:
        result = orchestrator.run_supply_watchdog(trigger_type="manual")
        
        print(f"Success: {result.get('success')}")
        print(f"Workflow: {result.get('workflow')}")
        print(f"Execution Time: {result.get('execution_time')}")
        
        if result.get('success'):
            summary = result.get('summary', {})
            print(f"\nSummary:")
            print(f"  - Expiring Batches: {summary.get('expiring_batches', 0)}")
            print(f"  - Critical Batches: {summary.get('critical_batches', 0)}")
            print(f"  - Shortfalls: {summary.get('shortfalls', 0)}")
            
            if result.get('json_string'):
                print(f"\nJSON Output (first 500 chars):")
                print(result['json_string'][:500] + "...")
        else:
            print(f"\nError: {result.get('error')}")
    
    except Exception as e:
        print(f"Test failed: {str(e)}")
        logger.error("Workflow A test failed", exc_info=True)


def test_workflow_b_simple():
    """Test Workflow B: Simple Query"""
    print("\n" + "="*80)
    print("TESTING WORKFLOW B: SIMPLE QUERY")
    print("="*80 + "\n")
    
    orchestrator = get_orchestrator()
    
    query = "What is the current stock level for Material MAT-93657?"
    print(f"Query: {query}\n")
    
    try:
        result = orchestrator.run_scenario_strategist(query)
        
        print(f"Success: {result.get('success')}")
        print(f"Workflow: {result.get('workflow')}")
        print(f"Intent: {result.get('intent')}")
        print(f"\nResponse:")
        print(result.get('response', 'No response'))
    
    except Exception as e:
        print(f"Test failed: {str(e)}")
        logger.error("Workflow B simple test failed", exc_info=True)


def test_workflow_b_extension():
    """Test Workflow B: Shelf-Life Extension Check"""
    print("\n" + "="*80)
    print("TESTING WORKFLOW B: SHELF-LIFE EXTENSION CHECK")
    print("="*80 + "\n")
    
    orchestrator = get_orchestrator()
    
    batch_id = "LOT-14364098"
    country = "Germany"
    print(f"Checking extension feasibility for Batch {batch_id} in {country}\n")
    
    try:
        result = orchestrator.check_shelf_life_extension(batch_id, country)
        
        print(f"Success: {result.get('success')}")
        print(f"Feasible: {result.get('feasible')}")
        
        if result.get('checks'):
            checks = result['checks']
            print(f"\nChecks:")
            print(f"  - Technical: {'✓ PASS' if checks.get('technical') else '✗ FAIL'}")
            print(f"  - Regulatory: {'✓ PASS' if checks.get('regulatory') else '✗ FAIL'}")
            print(f"  - Logistics: {'✓ PASS' if checks.get('logistics') else '✗ FAIL'}")
        
        print(f"\nResponse:")
        print(result.get('response', 'No response'))
    
    except Exception as e:
        print(f"Test failed: {str(e)}")
        logger.error("Workflow B extension test failed", exc_info=True)


def test_health_check():
    """Test orchestrator health check"""
    print("\n" + "="*80)
    print("TESTING HEALTH CHECK")
    print("="*80 + "\n")
    
    orchestrator = get_orchestrator()
    
    try:
        health = orchestrator.health_check()
        
        print(f"Status: {health.get('status')}")
        print(f"Message: {health.get('message')}")
        print(f"\nAgents:")
        for agent, status in health.get('agents', {}).items():
            print(f"  - {agent}: {status}")
    
    except Exception as e:
        print(f"Health check failed: {str(e)}")
        logger.error("Health check test failed", exc_info=True)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("CLINICAL SUPPLY CHAIN CONTROL TOWER - WORKFLOW TESTS")
    print("="*80)
    
    # Note: These tests will fail without database connection
    # This is expected - the script demonstrates the workflow structure
    
    print("\nNOTE: Tests require database connection to execute fully.")
    print("This script demonstrates workflow orchestration structure.\n")
    
    # Test health check first
    test_health_check()
    
    # Test Workflow A
    test_workflow_a()
    
    # Test Workflow B - Simple
    test_workflow_b_simple()
    
    # Test Workflow B - Extension
    test_workflow_b_extension()
    
    print("\n" + "="*80)
    print("TESTS COMPLETE")
    print("="*80 + "\n")
