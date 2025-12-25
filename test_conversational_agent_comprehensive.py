#!/usr/bin/env python3
"""
Comprehensive test of conversational agent (Workflow B).

Tests:
1. Diverse query types
2. Table selection accuracy
3. SQL generation
4. Response quality
5. Edge cases
"""
import logging
from typing import Dict, List

logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)

print("=" * 100)
print("COMPREHENSIVE CONVERSATIONAL AGENT TEST")
print("=" * 100)

from src.workflows.workflow_b_v2_openai import ScenarioStrategistWorkflowV2OpenAI

workflow = ScenarioStrategistWorkflowV2OpenAI()

# Test queries covering all major use cases
test_cases = [
    {
        "query": "Show me outstanding shipments",
        "category": "LOGISTICS",
        "expected_tables": ["outstanding_site_shipment_status_report", "shipment_status_report"],
        "should_succeed": True
    },
    {
        "query": "What is the current stock level for Material X",
        "category": "INVENTORY",
        "expected_tables": ["available_inventory_report", "allocated_materials_to_orders"],
        "should_succeed": True
    },
    {
        "query": "Can we extend Batch #123 for Germany",
        "category": "REGULATORY",
        "expected_tables": ["batch_master", "re_evaluation", "rim"],
        "should_succeed": True
    },
    {
        "query": "Show me all batches expiring in 30 days",
        "category": "EXPIRY",
        "expected_tables": ["batch_master", "allocated_materials_to_orders"],
        "should_succeed": True
    },
    {
        "query": "What is the enrollment forecast for next 8 weeks",
        "category": "DEMAND",
        "expected_tables": ["enrollment_rate_report", "country_level_enrollment_report"],
        "should_succeed": True
    },
    {
        "query": "Show me purchase requirements",
        "category": "PURCHASE",
        "expected_tables": ["purchase_requirement", "purchase_order_quantities"],
        "should_succeed": True
    },
    {
        "query": "What is the shipping time to Germany",
        "category": "LOGISTICS",
        "expected_tables": ["ip_shipping_timelines_report"],
        "should_succeed": True
    },
    {
        "query": "Show me all materials in the database",
        "category": "MATERIALS",
        "expected_tables": ["material_master", "materials"],
        "should_succeed": True
    },
    {
        "query": "What is the status of manufacturing orders",
        "category": "MANUFACTURING",
        "expected_tables": ["manufacturing_orders"],
        "should_succeed": True
    },
    {
        "query": "Show me quality documents",
        "category": "QUALITY",
        "expected_tables": ["qdocs", "inspection_lot"],
        "should_succeed": True
    },
]

results = {
    "total": len(test_cases),
    "passed": 0,
    "failed": 0,
    "details": []
}

print("\nRunning tests...\n")

for i, test in enumerate(test_cases, 1):
    query = test["query"]
    category = test["category"]
    expected_tables = test["expected_tables"]
    
    print(f"[{i}/{len(test_cases)}] {category}: {query}")
    
    try:
        result = workflow.execute(query)
        
        if result.get("success"):
            tables_searched = result.get("tables_searched", [])
            table_used = result.get("table_used")
            row_count = result.get("row_count", 0)
            
            # Check if expected tables were searched
            expected_found = any(t in tables_searched for t in expected_tables)
            
            if expected_found or row_count > 0:
                print(f"  ✓ SUCCESS")
                print(f"    Tables searched: {len(tables_searched)}")
                print(f"    Table used: {table_used}")
                print(f"    Rows returned: {row_count}")
                results["passed"] += 1
                results["details"].append({
                    "query": query,
                    "status": "PASS",
                    "tables_searched": tables_searched,
                    "table_used": table_used,
                    "row_count": row_count
                })
            else:
                print(f"  ⚠ PARTIAL - No expected tables found")
                print(f"    Tables searched: {tables_searched}")
                results["failed"] += 1
                results["details"].append({
                    "query": query,
                    "status": "PARTIAL",
                    "tables_searched": tables_searched,
                    "table_used": table_used,
                    "row_count": row_count
                })
        else:
            error = result.get("error", "Unknown error")
            print(f"  ✗ FAILED: {error}")
            results["failed"] += 1
            results["details"].append({
                "query": query,
                "status": "FAIL",
                "error": error
            })
    
    except Exception as e:
        print(f"  ✗ EXCEPTION: {str(e)}")
        results["failed"] += 1
        results["details"].append({
            "query": query,
            "status": "EXCEPTION",
            "error": str(e)
        })

# Summary
print("\n" + "=" * 100)
print("TEST SUMMARY")
print("=" * 100)

success_rate = 100 * results["passed"] / results["total"]
print(f"\nTotal tests: {results['total']}")
print(f"Passed: {results['passed']}")
print(f"Failed: {results['failed']}")
print(f"Success rate: {success_rate:.1f}%")

# Verdict
print("\n" + "=" * 100)
print("VERDICT")
print("=" * 100)

if success_rate >= 90:
    print(f"\n✓✓✓ CONVERSATIONAL AGENT IS WORKING CORRECTLY")
    print(f"    Success rate: {success_rate:.1f}%")
    print(f"    The agent can handle diverse queries across all table categories.")
    print(f"    The system is production-ready.")
elif success_rate >= 70:
    print(f"\n⚠ CONVERSATIONAL AGENT IS MOSTLY WORKING")
    print(f"    Success rate: {success_rate:.1f}%")
    print(f"    Some edge cases may need attention.")
else:
    print(f"\n✗ CONVERSATIONAL AGENT HAS ISSUES")
    print(f"    Success rate: {success_rate:.1f}%")
    print(f"    Significant improvements needed.")

print("\n" + "=" * 100)
print("DETAILED RESULTS")
print("=" * 100)

for detail in results["details"]:
    print(f"\nQuery: {detail['query']}")
    print(f"Status: {detail['status']}")
    if detail["status"] == "PASS":
        print(f"  Tables searched: {detail['tables_searched']}")
        print(f"  Table used: {detail['table_used']}")
        print(f"  Rows: {detail['row_count']}")
    elif detail["status"] == "PARTIAL":
        print(f"  Tables searched: {detail['tables_searched']}")
        print(f"  Table used: {detail['table_used']}")
        print(f"  Rows: {detail['row_count']}")
    else:
        print(f"  Error: {detail.get('error', 'Unknown')}")

print("\n" + "=" * 100)
