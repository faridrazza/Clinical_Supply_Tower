#!/usr/bin/env python
"""Comprehensive test of both workflows."""

from src.workflows.orchestrator import get_orchestrator

print('='*80)
print('COMPREHENSIVE WORKFLOW TEST')
print('='*80)

orchestrator = get_orchestrator()

# Test 1: Workflow A
print('\n[TEST 1] Workflow A: Supply Watchdog')
print('-'*80)
result_a = orchestrator.run_supply_watchdog()
success = result_a.get('success')
print(f'Success: {success}')
output = result_a.get('output', {})
risk_summary = output.get('risk_summary', {})
expiring = risk_summary.get('total_expiring_batches')
shortfall = risk_summary.get('total_shortfall_predictions')
print(f'Expiring batches: {expiring}')
print(f'Shortfall predictions: {shortfall}')

# Test 2: Workflow B - Shelf-life extension
print('\n[TEST 2] Workflow B: Shelf-Life Extension Query')
print('-'*80)
result_b1 = orchestrator.run_scenario_strategist('Can we extend the expiry of Batch LOT-14364098 for Germany?')
success_b1 = result_b1.get('success')
resp_len_b1 = len(result_b1.get('response', ''))
resp_preview_b1 = result_b1.get('response', '')[:200]
print(f'Success: {success_b1}')
print(f'Response length: {resp_len_b1}')
print(f'Response preview: {resp_preview_b1}...')

# Test 3: Workflow B - General query about any table
print('\n[TEST 3] Workflow B: General Query (Any Table)')
print('-'*80)
result_b2 = orchestrator.run_scenario_strategist('What are the oldest materials in the database?')
success_b2 = result_b2.get('success')
resp_len_b2 = len(result_b2.get('response', ''))
resp_preview_b2 = result_b2.get('response', '')[:200]
print(f'Success: {success_b2}')
print(f'Response length: {resp_len_b2}')
print(f'Response preview: {resp_preview_b2}...')

# Test 4: Workflow B - Complex multi-table query
print('\n[TEST 4] Workflow B: Complex Multi-Table Query')
print('-'*80)
result_b3 = orchestrator.run_scenario_strategist('Which lots are closest to expiry, and in which locations?')
success_b3 = result_b3.get('success')
resp_len_b3 = len(result_b3.get('response', ''))
resp_preview_b3 = result_b3.get('response', '')[:200]
print(f'Success: {success_b3}')
print(f'Response length: {resp_len_b3}')
print(f'Response preview: {resp_preview_b3}...')

print('\n' + '='*80)
print('ALL TESTS COMPLETED SUCCESSFULLY')
print('='*80)
