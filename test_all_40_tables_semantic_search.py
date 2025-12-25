#!/usr/bin/env python3
"""
Test to verify that semantic search searches ALL 40 tables, not just a few.

This test will:
1. Query ChromaDB for each table individually
2. Verify all 40 tables are in the collection
3. Test semantic search with various queries
4. Show which tables are being searched for each query
5. Verify the system can find ANY table when needed
"""
import logging
from typing import Dict, List, Set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 100)
print("TEST: VERIFY ALL 40 TABLES ARE SEARCHABLE")
print("=" * 100)

# Step 1: Get all tables from schema registry
print("\n[STEP 1] Loading all 40 tables from schema registry...")
from src.utils.schema_registry import get_all_table_names, TABLE_SCHEMAS

all_tables = get_all_table_names()
print(f"✓ Found {len(all_tables)} tables in schema registry")
print(f"  Tables: {', '.join(all_tables[:5])}... (showing first 5)")

# Step 2: Verify ChromaDB has all 40 tables
print("\n[STEP 2] Verifying ChromaDB has all 40 tables...")
from src.utils.chroma_schema_manager_openai import get_chroma_manager_openai

manager = get_chroma_manager_openai()
stats = manager.get_collection_stats()
chroma_table_count = stats.get('total_tables', 0)
print(f"✓ ChromaDB has {chroma_table_count} tables")

if chroma_table_count != len(all_tables):
    print(f"✗ MISMATCH: Schema registry has {len(all_tables)}, ChromaDB has {chroma_table_count}")
else:
    print(f"✓ All {len(all_tables)} tables are in ChromaDB")

# Step 3: Test semantic search with diverse queries
print("\n[STEP 3] Testing semantic search with diverse queries...")
print("=" * 100)

test_queries = [
    # Inventory queries
    ("Show me all inventory", "inventory"),
    ("What batches are expiring", "batch"),
    ("Current stock levels", "stock"),
    
    # Demand queries
    ("Show enrollment forecast", "enrollment"),
    ("What is patient demand", "demand"),
    
    # Regulatory queries
    ("Show regulatory approvals", "regulatory"),
    ("Has this been re-evaluated", "re-evaluation"),
    
    # Logistics queries
    ("What is shipping time", "shipping"),
    ("Show outstanding shipments", "shipment"),
    
    # Purchase queries
    ("Show purchase requirements", "purchase"),
    ("What orders are pending", "order"),
    
    # Manufacturing queries
    ("Show manufacturing orders", "manufacturing"),
    ("What is the production status", "production"),
    
    # Material queries
    ("Show material master", "material"),
    ("What materials do we have", "materials"),
    
    # Quality/Regulatory queries
    ("Show quality documents", "quality"),
    ("What are inspection lots", "inspection"),
    
    # Distribution queries
    ("Show distribution orders", "distribution"),
    ("What is the delivery status", "delivery"),
    
    # General queries
    ("Show me everything", "all"),
    ("What data do we have", "data"),
]

from src.agents.schema_retrieval_agent_v2_openai import SchemaRetrievalAgentV2OpenAI

agent = SchemaRetrievalAgentV2OpenAI()

# Track which tables are found across all queries
tables_found_across_queries: Set[str] = set()
query_results: Dict[str, List[str]] = {}

for query, category in test_queries:
    result = agent.execute({
        "query": query,
        "n_results": 10  # Get top 10 tables per query
    })
    
    if result.get("success"):
        tables = result.get("table_names", [])
        scores = result.get("similarity_scores", {})
        
        query_results[query] = tables
        tables_found_across_queries.update(tables)
        
        print(f"\n[{category.upper()}] Query: '{query}'")
        print(f"  Tables found: {len(tables)}")
        for i, table in enumerate(tables[:5], 1):
            score = scores.get(table, 0)
            print(f"    {i}. {table} ({score:.1%})")
        if len(tables) > 5:
            print(f"    ... and {len(tables) - 5} more")
    else:
        print(f"\n✗ Query failed: {query}")
        print(f"  Error: {result.get('error')}")

# Step 4: Analyze coverage
print("\n" + "=" * 100)
print("[STEP 4] COVERAGE ANALYSIS")
print("=" * 100)

print(f"\nTotal unique tables found across all queries: {len(tables_found_across_queries)}")
print(f"Total tables in database: {len(all_tables)}")
print(f"Coverage: {100 * len(tables_found_across_queries) / len(all_tables):.1f}%")

# Find tables that were NOT found
tables_not_found = set(all_tables) - tables_found_across_queries
if tables_not_found:
    print(f"\n⚠ Tables NOT found in any query ({len(tables_not_found)}):")
    for table in sorted(tables_not_found):
        print(f"  - {table}")
else:
    print(f"\n✓ ALL {len(all_tables)} tables were found in at least one query!")

# Step 5: Test specific table queries
print("\n" + "=" * 100)
print("[STEP 5] TESTING SPECIFIC TABLE QUERIES")
print("=" * 100)

# Test queries designed to find specific tables
specific_tests = [
    ("Show me the RIM table", "rim"),
    ("What is in the re_evaluation table", "re_evaluation"),
    ("Show material country requirements", "material_country_requirements"),
    ("What is in the QDocs table", "qdocs"),
    ("Show me the NMRF table", "nmrf"),
    ("What is in the excursion detail report", "excursion_detail_report"),
    ("Show me the global gateway inventory", "global_gateway_inventory"),
    ("What is in the metrics over time report", "metrics_over_time_report"),
]

print("\nTesting ability to find specific tables:")
specific_tables_found = set()

for query, expected_table in specific_tests:
    result = agent.execute({
        "query": query,
        "n_results": 5
    })
    
    if result.get("success"):
        tables = result.get("table_names", [])
        scores = result.get("similarity_scores", {})
        
        # Check if expected table is in results
        if expected_table in tables:
            rank = tables.index(expected_table) + 1
            score = scores.get(expected_table, 0)
            print(f"✓ '{expected_table}' found at rank {rank} ({score:.1%})")
            specific_tables_found.add(expected_table)
        else:
            print(f"⚠ '{expected_table}' NOT in top 5")
            print(f"  Top 5: {tables}")
    else:
        print(f"✗ Query failed: {query}")

# Step 6: Final verdict
print("\n" + "=" * 100)
print("[FINAL VERDICT]")
print("=" * 100)

coverage_percentage = 100 * len(tables_found_across_queries) / len(all_tables)
specific_percentage = 100 * len(specific_tables_found) / len(specific_tests)

print(f"\n✓ ChromaDB contains: {chroma_table_count} tables")
print(f"✓ Semantic search found: {len(tables_found_across_queries)} unique tables ({coverage_percentage:.1f}%)")
print(f"✓ Specific table queries: {len(specific_tables_found)}/{len(specific_tests)} ({specific_percentage:.1f}%)")

if coverage_percentage >= 90:
    print(f"\n✓✓✓ VERDICT: System searches ALL 40 tables (or very close)")
    print(f"    The semantic search is working correctly across the entire database.")
elif coverage_percentage >= 70:
    print(f"\n⚠ VERDICT: System searches most tables ({coverage_percentage:.1f}%)")
    print(f"    Some tables may not be easily discoverable via semantic search.")
else:
    print(f"\n✗ VERDICT: System only searches {coverage_percentage:.1f}% of tables")
    print(f"    There may be an issue with semantic search coverage.")

print("\n" + "=" * 100)
