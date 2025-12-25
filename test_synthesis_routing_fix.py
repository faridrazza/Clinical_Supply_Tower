#!/usr/bin/env python3
"""
Test Synthesis Agent Routing Fix

Verifies that the Synthesis Agent correctly uses data from the actual tables
queried, not just the agent that executed the query.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.agents.synthesis_agent import SynthesisAgent


def test_purchase_requirement_routing():
    """Test that purchase requirement data is used correctly."""
    print("\n" + "="*80)
    print("TEST: Purchase Requirement Data Routing")
    print("="*80)
    
    synthesis = SynthesisAgent()
    
    # Simulate agent outputs where InventoryAgent queried purchase_requirement table
    agent_outputs = {
        "inventory": {
            "success": True,
            "data": [
                {
                    "requirement_id": "REQ-001",
                    "material_id": "MAT-123",
                    "required_quantity": 500,
                    "required_date": "2025-02-01",
                    "status": "Open"
                },
                {
                    "requirement_id": "REQ-002",
                    "material_id": "MAT-456",
                    "required_quantity": 300,
                    "required_date": "2025-02-15",
                    "status": "Open"
                }
            ],
            "citations": [
                {
                    "table": "purchase_requirement",
                    "columns": ["requirement_id", "material_id", "required_quantity"],
                    "query_date": "2025-01-01"
                }
            ],
            "summary_text": "Found 2 open purchase requirements"
        }
    }
    
    result = synthesis.execute({
        "workflow": "B",
        "agent_outputs": agent_outputs,
        "query": "What is the purchase requirement status?",
        "output_format": "natural_language"
    })
    
    print(f"Query: What is the purchase requirement status?")
    print(f"Success: {result.get('success')}")
    print(f"\nResponse:")
    print(result.get('output', 'N/A'))
    
    # Verify it uses purchase_requirement table data
    response = result.get('output', '')
    citations = result.get('citations', [])
    
    uses_purchase_data = 'purchase_requirement' in response.lower() or 'requirement' in response.lower()
    has_purchase_citation = any(c.get('table') == 'purchase_requirement' for c in citations)
    
    print(f"\nAnalysis:")
    print(f"  Uses purchase requirement data: {uses_purchase_data}")
    print(f"  Has purchase_requirement citation: {has_purchase_citation}")
    print(f"  Citations: {[c.get('table') for c in citations]}")
    
    if uses_purchase_data and has_purchase_citation:
        print("\n✓ PASS - Synthesis Agent correctly routes purchase requirement data")
        return True
    else:
        print("\n✗ FAIL - Synthesis Agent not using correct data source")
        return False


def test_inventory_data_routing():
    """Test that inventory data is used correctly."""
    print("\n" + "="*80)
    print("TEST: Inventory Data Routing")
    print("="*80)
    
    synthesis = SynthesisAgent()
    
    # Simulate agent outputs where InventoryAgent queried available_inventory_report
    agent_outputs = {
        "inventory": {
            "success": True,
            "data": [
                {
                    "trial_name": "Shake Study",
                    "location": "Taiwan",
                    "received_packages": 100,
                    "batch_id": "LOT-001"
                },
                {
                    "trial_name": "Shake Study",
                    "location": "Germany",
                    "received_packages": 50,
                    "batch_id": "LOT-002"
                }
            ],
            "citations": [
                {
                    "table": "available_inventory_report",
                    "columns": ["trial_name", "location", "received_packages"],
                    "query_date": "2025-01-01"
                }
            ],
            "summary_text": "Found 2 inventory records"
        }
    }
    
    result = synthesis.execute({
        "workflow": "B",
        "agent_outputs": agent_outputs,
        "query": "What is the current inventory level?",
        "output_format": "natural_language"
    })
    
    print(f"Query: What is the current inventory level?")
    print(f"Success: {result.get('success')}")
    print(f"\nResponse:")
    print(result.get('output', 'N/A'))
    
    # Verify it uses available_inventory_report table data
    response = result.get('output', '')
    citations = result.get('citations', [])
    
    uses_inventory_data = 'inventory' in response.lower() or 'packages' in response.lower()
    has_inventory_citation = any(c.get('table') == 'available_inventory_report' for c in citations)
    
    print(f"\nAnalysis:")
    print(f"  Uses inventory data: {uses_inventory_data}")
    print(f"  Has available_inventory_report citation: {has_inventory_citation}")
    print(f"  Citations: {[c.get('table') for c in citations]}")
    
    if uses_inventory_data and has_inventory_citation:
        print("\n✓ PASS - Synthesis Agent correctly routes inventory data")
        return True
    else:
        print("\n✗ FAIL - Synthesis Agent not using correct data source")
        return False


def test_aggregation_with_table_names():
    """Test that _aggregate_agent_data uses table names in headers."""
    print("\n" + "="*80)
    print("TEST: Data Aggregation with Table Names")
    print("="*80)
    
    synthesis = SynthesisAgent()
    
    agent_outputs = {
        "inventory": {
            "success": True,
            "data": [{"material_id": "MAT-001", "quantity": 100}],
            "citations": [{"table": "purchase_requirement"}],
            "summary_text": "Purchase requirement data"
        },
        "demand": {
            "success": True,
            "data": [{"trial": "CT-001", "demand": 50}],
            "citations": [{"table": "enrollment_rate_report"}],
            "summary_text": "Demand forecast data"
        }
    }
    
    aggregated = synthesis._aggregate_agent_data(agent_outputs)
    
    print("Aggregated data:")
    print(aggregated)
    
    # Verify table names are in the aggregated data
    has_purchase_header = "PURCHASE_REQUIREMENT" in aggregated
    has_enrollment_header = "ENROLLMENT_RATE_REPORT" in aggregated
    
    print(f"\nAnalysis:")
    print(f"  Has PURCHASE_REQUIREMENT header: {has_purchase_header}")
    print(f"  Has ENROLLMENT_RATE_REPORT header: {has_enrollment_header}")
    
    if has_purchase_header and has_enrollment_header:
        print("\n✓ PASS - Aggregation correctly uses table names")
        return True
    else:
        print("\n✗ FAIL - Aggregation not using table names")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("SYNTHESIS AGENT ROUTING FIX VERIFICATION")
    print("="*80)
    print("\nTesting that Synthesis Agent correctly routes data based on actual tables queried...")
    
    tests = [
        test_aggregation_with_table_names,
        test_purchase_requirement_routing,
        test_inventory_data_routing
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n✗ Test {test_func.__name__} failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED")
        print("\nThe Synthesis Agent now:")
        print("  • Uses table names from citations in aggregated data headers")
        print("  • Correctly routes data based on actual tables queried")
        print("  • Provides accurate responses for all table types")
    else:
        print(f"\n✗ {total-passed} TESTS FAILED")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
