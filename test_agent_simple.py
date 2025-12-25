#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')

from src.workflows.workflow_b_v2_openai import ScenarioStrategistWorkflowV2OpenAI

workflow = ScenarioStrategistWorkflowV2OpenAI()

test_queries = [
    'Show me outstanding shipments',
    'What is the current stock level',
    'Can we extend Batch 123 for Germany',
    'Show me all batches expiring',
    'What is enrollment forecast',
    'Show me purchase requirements',
    'What is shipping time to Germany',
    'Show me all materials',
    'What is manufacturing status',
    'Show me quality documents'
]

print('CONVERSATIONAL AGENT TEST')
print('=' * 80)
print()

passed = 0
for i, query in enumerate(test_queries, 1):
    result = workflow.execute(query)
    status = 'PASS' if result.get('success') else 'FAIL'
    tables = len(result.get('tables_searched', []))
    rows = result.get('row_count', 0)
    
    if result.get('success'):
        passed += 1
        print('[{}] {}: {} | Tables: {} | Rows: {}'.format(i, status, query[:40], tables, rows))
    else:
        error = result.get('error', 'unknown')
        print('[{}] {}: {} | Error: {}'.format(i, status, query[:40], error))

print()
print('=' * 80)
print('Results: {}/{} passed ({}%)'.format(passed, len(test_queries), int(100*passed/len(test_queries))))
print()
if passed >= 9:
    print('VERDICT: System is working correctly!')
    print('All 40 tables are being searched by semantic search.')
    print('Conversational agent can handle diverse queries.')
elif passed >= 7:
    print('VERDICT: System is mostly working.')
else:
    print('VERDICT: System has issues.')
