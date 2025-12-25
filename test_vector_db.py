#!/usr/bin/env python
"""Test vector DB retrieval."""

from src.tools.vector_db_tools import retrieve_schemas_for_query, vector_db_tools, get_specific_table_schema

# Test 1: Check how many tables are in vector DB
print('Test 1: Vector DB Table Count')
print('-' * 60)
tables = vector_db_tools.list_all_tables()
print(f'Total tables in vector DB: {len(tables)}')
if len(tables) > 0:
    print('Sample tables:', tables[:5])
print()

# Test 2: Try to retrieve schemas for the outstanding shipments query
print('Test 2: Schema Retrieval for Outstanding Shipments Query')
print('-' * 60)
query = 'Which sites currently have outstanding shipments pending delivery'
schemas = retrieve_schemas_for_query(query, max_tables=5)
print(f'Retrieved {len(schemas)} schemas')
for schema in schemas:
    tbl = schema.get('table_name')
    score = schema.get('relevance_score', 'N/A')
    print(f'  - {tbl} (score: {score})')
print()

# Test 3: Check if specific tables are in vector DB
print('Test 3: Check Specific Tables')
print('-' * 60)
tables_to_check = ['ip_shipping_timelines_report', 'distribution_order_report', 'available_inventory_report']
for table in tables_to_check:
    schema = get_specific_table_schema(table)
    if schema:
        print(f'✓ {table} found')
    else:
        print(f'✗ {table} NOT found')
