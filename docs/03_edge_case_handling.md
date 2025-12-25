# Part 3: Edge Case Handling

This document describes how the system handles various edge cases that can occur in real-world usage.

---

## Edge Case 1: Ambiguous Entity Names

### Problem Description

**What is the edge case?**

Users may refer to entities (trials, batches, materials, countries) using variations that don't exactly match database records.

**Examples**:
- User says: "Trial ABC"
- Database has: "Trial_ABC_v2", "Trial-ABC", "trial_abc"

- User says: "LOT 14364098"
- Database has: "LOT-14364098"

- User says: "Germany"
- Database might have: "GERMANY", "germany", "DE"

### Why It Matters

**Business Impact**:
- **User Frustration**: Users get "not found" errors for valid entities
- **Wasted Time**: Users must guess exact formatting
- **Missed Insights**: Valid queries fail due to formatting mismatches
- **Poor UX**: System appears inflexible and unhelpful

**Example Scenario**:
A supply manager asks "Can we extend Batch LOT 14364098 for Germany?" but the system responds "Batch not found" because the database stores it as "LOT-14364098". The manager wastes time trying different formats instead of getting the answer they need.

### Detection Mechanism

**How system identifies this case**:

1. **Initial Query Execution**: Agent attempts exact match query
2. **No Results Detected**: Query returns 0 rows
3. **Entity Extraction**: Router Agent extracts entity from query using regex
4. **Candidate Retrieval**: System queries database for similar entities
5. **Fuzzy Matching Triggered**: FuzzyMatcher analyzes candidates

**Code Detection**:
```python
# In any domain agent
result = sql_agent.execute(query_with_exact_match)

if result["row_count"] == 0:
    # No exact match found - trigger fuzzy matching
    candidates = get_similar_entities(entity_type, search_term)
    
    if candidates:
        # Fuzzy matching can help
        resolution = fuzzy_matcher.resolve_entity(
            query=user_input,
            candidates=candidates,
            entity_type=entity_type
        )
```

### Resolution Strategy

**Step-by-Step Handling Logic**:

#### Step 1: Exact Match (Case-Sensitive)
```python
for candidate in candidates:
    if query == candidate:
        return {"match_type": "exact", "matched_value": candidate, "confidence": 100}
```
**Action**: Use immediately, no user confirmation needed

#### Step 2: Case-Insensitive Match
```python
for candidate in candidates:
    if query.lower() == candidate.lower():
        return {"match_type": "normalized", "matched_value": candidate, "confidence": 95}
```
**Action**: Use immediately, log the normalization

#### Step 3: Normalized Match (Remove Special Characters)
```python
normalized_query = re.sub(r'[^a-zA-Z0-9]', '', query.lower())
for candidate in candidates:
    normalized_candidate = re.sub(r'[^a-zA-Z0-9]', '', candidate.lower())
    if normalized_query == normalized_candidate:
        return {"match_type": "normalized", "matched_value": candidate, "confidence": 95}
```
**Action**: Use immediately

#### Step 4: Fuzzy Matching (Similarity Score)
```python
from fuzzywuzzy import fuzz

matches = []
for candidate in candidates:
    score = fuzz.token_sort_ratio(query, candidate)
    matches.append((candidate, score))

matches.sort(key=lambda x: x[1], reverse=True)
best_match, best_score = matches[0]

if best_score > 80:
    # High confidence - use automatically
    return {
        "match_type": "fuzzy_high",
        "matched_value": best_match,
        "confidence": best_score,
        "action": "use_automatically"
    }
elif best_score >= 60:
    # Medium confidence - ask user
    return {
        "match_type": "fuzzy_medium",
        "matched_value": best_match,
        "confidence": best_score,
        "alternatives": [m[0] for m in matches[1:3]],
        "action": "ask_user",
        "message": f"Did you mean '{best_match}'? Other options: {alternatives}"
    }
else:
    # Low confidence - show options
    return {
        "match_type": "fuzzy_low",
        "confidence": best_score,
        "alternatives": [m[0] for m in matches[:5]],
        "action": "show_options",
        "message": f"Multiple possible matches: {alternatives}"
    }
```

#### Step 5: Session Memory
```python
# Remember user's choice for remainder of conversation
if user_confirms_match:
    session_state["entity_mappings"][user_input] = confirmed_match
    # Use this mapping for future queries in same session
```

### User Experience

**What user sees**:

**Scenario 1: High Confidence Match (>80%)**
```
User: "What is stock for LOT 14364098?"

System: "Found Batch LOT-14364098 (matched with 95% confidence):
- Location: Taiwan, Stock: 100 packages
- Location: Germany, Stock: 50 packages

Source: available_inventory_report"
```
*Note: System automatically corrected "LOT 14364098" to "LOT-14364098"*

**Scenario 2: Medium Confidence Match (60-80%)**
```
User: "Can we extend Trial ABC for Germany?"

System: "I found similar trials. Did you mean:
1. Trial_ABC_v2 (78% match) ← Most likely
2. Trial-ABC-v1 (65% match)
3. Trial_ABC_old (62% match)

Please confirm which trial you're asking about."

User: "Yes, Trial_ABC_v2"

System: "Great! Checking extension feasibility for Trial_ABC_v2 in Germany..."
```

**Scenario 3: Low Confidence Match (<60%)**
```
User: "Show me batch ABC123"

System: "I couldn't find an exact match for 'ABC123'. 

Here are similar batches:
1. LOT-ABC-123
2. LOT-ABC-1234
3. LOT-ABC-12345
4. BATCH-ABC-123
5. LOT-XYZ-123

Which batch are you looking for? Or try searching with a different format."
```

### Example Scenario Walkthrough

**Complete Flow**:

1. **User Query**: "Can we extend the expiry of Batch LOT 14364098 for Germany?"

2. **Entity Extraction**: Router extracts "LOT 14364098"

3. **Initial Query**: 
   ```sql
   SELECT * FROM available_inventory_report WHERE lot = 'LOT 14364098'
   ```
   Result: 0 rows

4. **Candidate Retrieval**:
   ```sql
   SELECT DISTINCT lot FROM available_inventory_report WHERE lot LIKE '%14364098%'
   ```
   Result: ["LOT-14364098", "LOT-14364099"]

5. **Fuzzy Matching**:
   - "LOT 14364098" vs "LOT-14364098": Score 95 (normalized match)
   - "LOT 14364098" vs "LOT-14364099": Score 85 (similar but different)

6. **Resolution**: Use "LOT-14364098" automatically (score > 80)

7. **Execution**: Query proceeds with corrected batch ID

8. **Response**: 
   ```
   CAN WE EXTEND BATCH LOT-14364098 FOR GERMANY?
   
   Answer: YES
   
   Technical Check: ✓ PASS
   - Batch LOT-14364098 extended 1 time previously
   - Source: re_evaluation table, 2025-02-26
   
   [... rest of response]
   
   Note: I automatically matched your query "LOT 14364098" to "LOT-14364098"
   ```

---

## Edge Case 2: SQL Query Errors with Self-Healing

### Problem Description

**What is the edge case?**

The SQL Generation Agent may generate queries that fail due to:
- Incorrect column names
- Missing tables
- Syntax errors
- Type mismatches
- Timeout issues

**Examples**:
- Agent generates: `SELECT expiry FROM available_inventory_report`
- Error: Column "expiry" does not exist (correct: "expiry_date")

- Agent generates: `SELECT * FROM inventory`
- Error: Table "inventory" does not exist (correct: "available_inventory_report")

### Why It Matters

**Business Impact**:
- **Failed Queries**: Users don't get answers
- **Poor Experience**: System appears broken
- **Lost Trust**: Users lose confidence in system
- **Wasted Resources**: Manual intervention required

**Example Scenario**:
A manager asks "Show me expiring batches" and the system generates a query with wrong column name. Without self-healing, the query fails and the user gets an error. With self-healing, the system corrects itself and provides the answer.

### Detection Mechanism

**How system identifies this case**:

1. **Query Execution**: SQL Generation Agent executes query
2. **Error Capture**: PostgreSQL returns error with code
3. **Error Analysis**: Agent analyzes error message
4. **Error Classification**: Determines error type
5. **Self-Healing Triggered**: Initiates correction attempt

**Error Detection Code**:
```python
result = run_sql_query(query)

if not result["success"]:
    error_code = result.get("error_code")  # e.g., "42703"
    error_message = result.get("error")
    
    # Classify error type
    if error_code == "42703":
        error_type = "column_not_found"
    elif error_code == "42P01":
        error_type = "table_not_found"
    elif error_code == "42601":
        error_type = "syntax_error"
    
    # Trigger self-healing
    corrected_query = self_heal(query, error_type, error_message, schema)
```

### Resolution Strategy

**Step-by-Step Self-Healing Logic**:

#### Attempt 1: Initial Generation
```python
# Agent receives schema from Schema Retrieval Agent
schema = schema_retrieval_agent.execute({
    "query": "inventory expiry",
    "workflow": "A"
})

# Generate SQL from intent
query = generate_sql(
    intent="Find batches expiring within 90 days",
    schema=schema["formatted_schemas"]
)

# Execute
result = run_sql_query(query)
```

**If successful**: Return results
**If failed**: Proceed to Attempt 2

#### Attempt 2: Error-Driven Correction
```python
# Capture error details
error_code = result["error_code"]  # "42703"
error_message = result["error"]    # "column 'expiry' does not exist"

# Analyze error
analysis = analyze_sql_error(error_code, error_message, query, schema)
# Analysis: "Column 'expiry' not found. Available columns: expiry_date, trial_name, location..."

# Generate corrected query
corrected_query = query.replace("expiry", "expiry_date")

# Execute corrected query
result = run_sql_query(corrected_query)
```

**If successful**: Return results with note about correction
**If failed**: Proceed to Attempt 3

#### Attempt 3: Schema Refresh
```python
# Request additional schemas
additional_schema = schema_retrieval_agent.execute({
    "query": "inventory expiry dates batches",
    "specific_tables": ["batch_master", "inspection_lot"]
})

# Combine schemas
full_schema = merge_schemas(schema, additional_schema)

# Regenerate query with expanded context
query = generate_sql(
    intent="Find batches expiring within 90 days",
    schema=full_schema["formatted_schemas"],
    previous_error=error_message
)

# Execute
result = run_sql_query(query)
```

**If successful**: Return results
**If failed**: Proceed to Failure Handling

#### Failure Handling (After 3 Attempts)
```python
# Translate error to user-friendly message
user_message = translate_error(error_code, error_message)

# Provide helpful explanation
explanation = f"""
I attempted to query the database but encountered an issue:

Problem: {user_message}

What I tried:
1. Initial query with standard schema
2. Corrected query based on error analysis
3. Expanded query with additional schemas

Available tables checked:
- available_inventory_report
- allocated_materials_to_orders
- batch_master

The issue appears to be: {suggest_fix(error_code, error_message)}

Can you rephrase your question or provide more specific details?
"""

return {
    "success": False,
    "error": user_message,
    "explanation": explanation,
    "attempts": 3
}
```

### User Experience

**What user sees**:

**Scenario 1: Successful Self-Healing (Attempt 2)**
```
User: "Show me batches expiring soon"

[System internally]:
- Attempt 1: SELECT expiry FROM available_inventory_report → Error
- Attempt 2: SELECT expiry_date FROM available_inventory_report → Success

System: "Found 15 batches expiring within 90 days:

Batch LOT-14364098: Expires 2026-01-15 (22 days remaining) - CRITICAL
Batch LOT-59019698: Expires 2026-02-10 (48 days remaining) - HIGH
...

Source: available_inventory_report

Note: Query was automatically corrected for optimal results."
```

**Scenario 2: Failed After 3 Attempts**
```
User: "Show me the XYZ report"

System: "I attempted to find the XYZ report but encountered an issue:

Problem: I couldn't identify which table contains the XYZ report data.

What I tried:
1. Searched for tables matching 'XYZ'
2. Checked common report tables
3. Expanded search to all available tables

Available reports I can access:
- Available Inventory Report
- Enrollment Rate Report
- Distribution Order Report
- Shipment Status Report
- [... more reports]

Could you clarify which report you're looking for, or describe what data you need?"
```

### Example Scenario Walkthrough

**Complete Self-Healing Flow**:

1. **User Query**: "What batches are expiring in the next 30 days?"

2. **Intent**: Find expiring batches with 30-day threshold

3. **Schema Retrieval**: Gets available_inventory_report schema

4. **Attempt 1 - Initial Generation**:
   ```sql
   SELECT batch_id, expiry, location 
   FROM available_inventory_report 
   WHERE expiry <= CURRENT_DATE + INTERVAL '30 days'
   ```
   **Error**: Column "batch_id" does not exist (42703)
   **Error**: Column "expiry" does not exist (42703)

5. **Error Analysis**:
   - Missing columns: batch_id, expiry
   - Available columns: lot, expiry_date, trial_name, location
   - Correction: batch_id → lot, expiry → expiry_date

6. **Attempt 2 - Corrected Query**:
   ```sql
   SELECT lot as batch_id, expiry_date, location 
   FROM available_inventory_report 
   WHERE expiry_date <= CURRENT_DATE + INTERVAL '30 days'
   AND received_packages > 0
   ```
   **Result**: Success! 5 rows returned

7. **Response to User**:
   ```
   Found 5 batches expiring within 30 days:
   
   1. LOT-14364098 - Taiwan - Expires 2026-01-15 (22 days) - CRITICAL
   2. LOT-59019698 - Germany - Expires 2026-01-28 (35 days) - HIGH
   ...
   
   Source: available_inventory_report, queried 2025-12-24
   ```

---

## Edge Case 3: Missing Data Scenarios

### Problem Description

**What is the edge case?**
 
Users query for entities that don't exist in the database or data is incomplete.

**Examples**:
- Batch #999 doesn't exist in any table
- Trial has no enrollment data
- Country has no shipping timeline
- Material has no regulatory approval

### Why It Matters

**Business Impact**:
- **Confusion**: Users don't know if data is missing or query is wrong
- **Wasted Time**: Users try different queries unnecessarily
- **Poor Decisions**: Missing data might indicate real issues
- **Trust Issues**: Users question system completeness

### Detection Mechanism

**How system identifies this case**:

1. **Query Execution**: Agent queries database
2. **Empty Result Set**: Query returns 0 rows
3. **Verification**: Agent checks multiple related tables
4. **Confirmation**: Entity truly doesn't exist
5. **Response Generation**: Synthesis Agent formats helpful message

### Resolution Strategy

**Step-by-Step Handling**:

1. **Check Primary Table**: Query main table for entity
2. **Check Related Tables**: Query 2-3 related tables
3. **Document Search**: Record which tables were checked
4. **Suggest Alternatives**: Find similar entities
5. **Provide Context**: Explain possible reasons

### User Experience

**What user sees**:

```
User: "Show expiry of Batch #999"

System: "I couldn't find Batch #999 in the system.

What I checked:
- available_inventory_report: No record
- allocated_materials_to_orders: No record
- re_evaluation: No record

Possible reasons:
1. Batch number may be formatted differently (e.g., LOT-0999, BATCH-999)
2. Batch fully consumed and archived
3. Batch belongs to different study not in current database

Similar active batches I found:
- LOT-998 (Shake Study, Taiwan)
- LOT-1000 (Put Trial, Germany)
- LOT-1001 (Skin Trial, Japan)

Would you like me to:
- Search with a different format?
- Show all active batches for a specific trial?
- Check archived records?"
```

### Example Scenario

**User Query**: "Has Batch LOT-99999999 been re-evaluated?"

**System Response**:
```
I couldn't find Batch LOT-99999999 in the re-evaluation history.

What I checked:
- re_evaluation table: No records for this batch
- available_inventory_report: Batch not found in current inventory
- allocated_materials_to_orders: No allocation records

This suggests the batch either:
1. Has never been re-evaluated
2. Doesn't exist in the system
3. May be recorded under a different identifier

Recent re-evaluations I found:
- LOT-45953393: Extended on 2025-02-26
- LOT-94284099: Retested on 2025-04-23
- LOT-32180264: Retested on 2025-02-04

Would you like me to show all re-evaluations for a specific material or trial?
```

---

## Edge Case 4: Conflicting Data Across Tables

### Problem Description

**What is the edge case?**

Different tables contain conflicting information for the same entity.

**Examples**:
- available_inventory_report shows 500 units
- allocated_materials_to_orders shows 450 units allocated
- Difference of 50 units unexplained

### Why It Matters

**Business Impact**:
- **Decision Uncertainty**: Which number to trust?
- **Data Quality Issues**: Indicates sync problems
- **Compliance Risk**: Incorrect reporting
- **Operational Issues**: May indicate real problems

### Detection Mechanism

1. **Multi-Source Query**: Agent queries multiple tables
2. **Value Comparison**: Compares values across sources
3. **Discrepancy Detection**: Identifies conflicts
4. **Timestamp Check**: Checks update times
5. **Priority Determination**: Identifies primary source

### Resolution Strategy

1. **Present Both Values**: Show all conflicting data
2. **Include Timestamps**: Show when each was updated
3. **Explain Difference**: Provide context
4. **Recommend Primary**: Suggest which to use
5. **Flag for Review**: Note if difference is significant

### User Experience

**What user sees**:

```
User: "What is current stock for Material X?"

System: "I found conflicting data for Material X:

Source 1 - available_inventory_report (updated: 2025-12-24 06:00):
  Current Stock: 500 units

Source 2 - allocated_materials_to_orders (updated: 2025-12-23 18:00):
  Allocated: 450 units

Analysis:
- Difference: 50 units
- Time gap: 12 hours between updates
- Likely cause: Recent consumption not yet reflected in allocation records

Note: available_inventory_report is the primary source (updates nightly from warehouse system). The 50-unit difference may indicate recent shipments or consumption.

Recommendation: Use 500 units as current available stock. If this is critical, verify with warehouse management system.

Would you like me to check shipment records for recent activity?"
```

---

## Edge Case 5: Context Window Overflow

### Problem Description

**What is the edge case?**

Long conversations or complex queries exceed LLM context limits.

**Examples**:
- User asks 20 questions in one session
- Query requires 10+ table schemas
- Response includes large result sets

### Why It Matters

**Business Impact**:
- **System Failure**: LLM refuses to process
- **Lost Context**: Forgets earlier conversation
- **Poor Responses**: Incomplete or confused answers
- **User Frustration**: Must restart conversation

### Detection Mechanism

1. **Token Counting**: Track tokens used
2. **Threshold Monitoring**: Watch for 80% capacity
3. **Conversation Length**: Count messages
4. **Schema Size**: Monitor schema tokens

### Resolution Strategy

**Progressive Loading**:
```python
# Load minimal schema first
initial_schema = get_tables(["available_inventory_report"])

# Request additional only if needed
if query_needs_more_tables:
    additional_schema = get_tables(["enrollment_rate_report"])
```

**Conversation Summarization**:
```python
if message_count > 10:
    # Summarize conversation
    summary = {
        "user_intent": "Checking expiry and extensions",
        "entities_mentioned": ["LOT-14364098", "Germany"],
        "key_findings": ["Batch expires in 22 days", "Extension approved"]
    }
    # Replace full history with summary
    context = summary
```

**Selective Memory**:
```python
# Keep important information
keep = {
    "user_preferences": session["preferences"],
    "entity_mappings": session["entity_mappings"],
    "recent_queries": session["queries"][-3:]
}

# Discard verbose content
discard = {
    "full_sql_queries": [],
    "detailed_schemas": [],
    "large_result_sets": []
}
```

### User Experience

**What user sees**:

```
[After 10 messages]

System: "I've summarized our conversation to keep things running smoothly:

Summary:
- You're checking expiry and extension feasibility for Batch LOT-14364098
- We confirmed the batch expires in 22 days (CRITICAL)
- Extension is approved in Germany
- Shipping is feasible with 30-day buffer

Continuing with your latest question..."
```

---

## Conclusion

These edge case handling strategies ensure the system:
- **Robust**: Handles real-world data issues gracefully
- **User-Friendly**: Provides helpful messages, not errors
- **Self-Healing**: Automatically corrects common problems
- **Transparent**: Explains what went wrong and why
- **Reliable**: Maintains trust through consistent behavior

All edge cases are handled with the user experience in mind, turning potential failures into helpful interactions.
