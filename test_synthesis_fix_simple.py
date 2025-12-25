#!/usr/bin/env python3
"""
Simple Test for Synthesis Agent Routing Fix

Tests the core fix without LLM calls to verify table name routing.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.agents.synthesis_agent import SynthesisAgent


def test_aggregation_with_table_names():
    """Test that _aggregate_agent_data uses table names in headers."""
    print("\n" + "="*80)
    print("TEST: Data Aggregation with Table Names")
    print("="*80)
    
    synthesis = SynthesisAgent()
    
    # Test Case 1: Purchase requirement data
    print("\nTest Case 1: Purchase Requirement Table")
    agent_outputs_1 = {
        "inventory": {
            "success": True,
            "data": [
                {"requirement_id": "REQ-001", "material_id": "MAT-123", "required_quantity": 500},
                {"requirement_id": "REQ-002", "material_id": "MAT-456", "required_quantity": 300}
            ],
            "citations": [{"table": "purchase_requirement"}],
            "summary_text": "Found 2 purchase requirements"
        }
    }
    
    aggregated_1 = synthesis._aggregate_agent_data(agent_outputs_1)
    print("Aggregated output:")
    print(aggregated_1[:200] + "...")
    
    has_purchase_header = "PURCHASE_REQUIREMENT" in aggregated_1
    has_requirement_data = "REQ-001" in aggregated_1 and "REQ-002" in aggregated_1
    
    print(f"\nAnalysis:")
    print(f"  Has PURCHASE_REQUIREMENT header: {has_purchase_header}")
    print(f"  Has requirement data: {has_requirement_data}")
    
    test1_pass = has_purchase_header and has_requirement_data
    if test1_pass:
        print("✓ PASS - Purchase requirement data correctly identified")
    else:
        print("✗ FAIL - Purchase requirement data not correctly identified")
    
    # Test Case 2: Inventory data
    print("\n" + "-"*80)
    print("Test Case 2: Inventory Table")
    agent_outputs_2 = {
        "inventory": {
            "success": True,
            "data": [
                {"trial_name": "Shake Study", "location": "Taiwan", "received_packages": 100},
                {"trial_name": "Shake Study", "location": "Germany", "received_packages": 50}
            ],
            "citations": [{"table": "available_inventory_report"}],
            "summary_text": "Found 2 inventory records"
        }
    }
    
    aggregated_2 = synthesis._aggregate_agent_data(agent_outputs_2)
    print("Aggregated output:")
    print(aggregated_2[:200] + "...")
    
    has_inventory_header = "AVAILABLE_INVENTORY_REPORT" in aggregated_2
    has_inventory_data = "Taiwan" in aggregated_2 and "Germany" in aggregated_2
    
    print(f"\nAnalysis:")
    print(f"  Has AVAILABLE_INVENTORY_REPORT header: {has_inventory_header}")
    print(f"  Has inventory data: {has_inventory_data}")
    
    test2_pass = has_inventory_header and has_inventory_data
    if test2_pass:
        print("✓ PASS - Inventory data correctly identified")
    else:
        print("✗ FAIL - Inventory data not correctly identified")
    
    # Test Case 3: Multiple tables
    print("\n" + "-"*80)
    print("Test Case 3: Multiple Tables")
    agent_outputs_3 = {
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
    
    aggregated_3 = synthesis._aggregate_agent_data(agent_outputs_3)
    print("Aggregated output:")
    print(aggregated_3[:300] + "...")
    
    has_purchase_header = "PURCHASE_REQUIREMENT" in aggregated_3
    has_enrollment_header = "ENROLLMENT_RATE_REPORT" in aggregated_3
    
    print(f"\nAnalysis:")
    print(f"  Has PURCHASE_REQUIREMENT header: {has_purchase_header}")
    print(f"  Has ENROLLMENT_RATE_REPORT header: {has_enrollment_header}")
    
    test3_pass = has_purchase_header and has_enrollment_header
    if test3_pass:
        print("✓ PASS - Multiple tables correctly identified")
    else:
        print("✗ FAIL - Multiple tables not correctly identified")
    
    return test1_pass and test2_pass and test3_pass


def test_citations_collection():
    """Test that citations are properly collected."""
    print("\n" + "="*80)
    print("TEST: Citations Collection")
    print("="*80)
    
    synthesis = SynthesisAgent()
    
    agent_outputs = {
        "inventory": {
            "success": True,
            "data": [{"id": 1}],
            "citations": [
                {"table": "purchase_requirement", "columns": ["id"]},
                {"table": "purchase_requirement", "columns": ["quantity"]}  # Duplicate table
            ]
        },
        "demand": {
            "success": True,
            "data": [{"id": 2}],
            "citations": [
                {"table": "enrollment_rate_report", "columns": ["demand"]}
            ]
        }
    }
    
    citations = synthesis._collect_all_citations(agent_outputs)
    
    print(f"Total citations collected: {len(citations)}")
    print(f"Citations: {[c.get('table') for c in citations]}")
    
    # Should have 3 citations (2 from inventory, 1 from demand)
    has_correct_count = len(citations) == 3
    has_purchase = any(c.get('table') == 'purchase_requirement' for c in citations)
    has_enrollment = any(c.get('table') == 'enrollment_rate_report' for c in citations)
    
    print(f"\nAnalysis:")
    print(f"  Has correct citation count (3): {has_correct_count}")
    print(f"  Has purchase_requirement citation: {has_purchase}")
    print(f"  Has enrollment_rate_report citation: {has_enrollment}")
    
    if has_correct_count and has_purchase and has_enrollment:
        print("\n✓ PASS - Citations correctly collected")
        return True
    else:
        print("\n✗ FAIL - Citations not correctly collected")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("SYNTHESIS AGENT ROUTING FIX - SIMPLE VERIFICATION")
    print("="*80)
    print("\nTesting core fix: Table name routing in aggregated data...")
    
    tests = [
        ("Aggregation with Table Names", test_aggregation_with_table_names),
        ("Citations Collection", test_citations_collection)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n✗ Test {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED")
        print("\nThe Synthesis Agent fix is working correctly:")
        print("  ✓ Uses table names from citations in aggregated data headers")
        print("  ✓ Correctly identifies which table data is being processed")
        print("  ✓ Properly collects citations from all agents")
        print("\nThis ensures that when a query like 'What is the purchase requirement status?'")
        print("is executed, the LLM will see the data is from 'PURCHASE_REQUIREMENT' table,")
        print("not from 'INVENTORY' agent, and will provide accurate responses.")
    else:
        print(f"\n✗ {total-passed} TESTS FAILED")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
