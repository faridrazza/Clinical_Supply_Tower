# Part 2: Technical Implementation

## Section 1: Tool Inventory

This section documents all tools available to agents for executing their responsibilities.

---

### Tool 1: run_sql_query

**Purpose**: Execute PostgreSQL queries with timeout and error handling

**File**: `src/tools/database_tools.py`

**Input Parameters**:
- `query` (string): SQL query to execute
- `params` (dict, optional): Query parameters for parameterized queries
- `timeout` (integer, optional): Query timeout in seconds (default: 30)

**Output**: Dictionary with results or error information
```python
{
    "success": bool,
    "data": List[Dict],  # Query results
    "columns": List[str],  # Column names
    "row_count": int,
    "query": str,
    "executed_at": str  # ISO timestamp
}
```

**Used By**: SQL Generation Agent, Inventory Agent, Demand Forecasting Agent, Regulatory Agent, Logistics Agent

**Error Handling**:
- Captures PostgreSQL errors with error codes
- Returns user-friendly error messages
- Logs errors for debugging
- Never exposes raw SQL errors to users

**Example Usage**:
```python
from src.tools.database_tools import run_sql_query

result = run_sql_query(
    query="SELECT * FROM available_inventory_report WHERE expiry_date <= CURRENT_DATE + INTERVAL '90 days'",
    timeout=30
)

if result["success"]:
    data = result["data"]
    print(f"Found {result['row_count']} records")
```

---

### Tool 2: retrieve_schemas_for_query

**Purpose**: Retrieve relevant table schemas from vector database using semantic search

**File**: `src/utils/chroma_schema_manager_openai.py`

**Input Parameters**:
- `query` (string): User query or intent
- `max_tables` (integer): Maximum number of tables to retrieve (default: 5)

**Output**: List of schema dictionaries
```python
[
    {
        "table_name": str,
        "business_purpose": str,
        "relevance_score": float,
        "schema_text": str  # Formatted schema
    }
]
```

**Used By**: Schema Retrieval Agent

**Error Handling**:
- Returns empty list if no matches found
- Logs retrieval errors
- Falls back to default tables if vector DB unavailable

**Example Usage**:
```python
from src.utils.chroma_schema_manager_openai import get_chroma_manager_openai

chroma_manager = get_chroma_manager_openai()
schemas = chroma_manager.find_relevant_tables(
    query="expiry dates and inventory levels",
    n_results=5
)

for schema in schemas:
    print(f"Table: {schema['table_name']}, Score: {schema['similarity_score']}")
```

---

### Tool 3: resolve_entity

**Purpose**: Resolve ambiguous entity names using fuzzy matching

**File**: `src/tools/fuzzy_matching.py`

**Input Parameters**:
- `query` (string): User's query string
- `candidates` (List[string]): List of possible matches from database
- `entity_type` (string): Type of entity (batch, material, trial, country)

**Output**: Dictionary with resolution result
```python
{
    "match_type": str,  # "exact", "normalized", "fuzzy_high", "fuzzy_medium", "fuzzy_low", "no_match"
    "matched_value": str,  # Best match
    "confidence": int,  # 0-100
    "alternatives": List[str],  # Other possible matches
    "action": str,  # "use_automatically", "ask_user", "show_options"
    "message": str  # User-friendly message
}
```

**Used By**: All domain agents when handling user queries

**Error Handling**:
- Returns "no_match" if no candidates provided
- Handles empty strings gracefully
- Logs matching attempts

**Example Usage**:
```python
from src.tools.fuzzy_matching import resolve_batch_id

result = resolve_batch_id(
    query="LOT 14364098",
    candidates=["LOT-14364098", "LOT-14364099", "LOT-14364100"]
)

if result["action"] == "use_automatically":
    batch_id = result["matched_value"]
```

---

### Tool 4: parse_monthly_enrollment

**Purpose**: Parse comma-separated monthly enrollment data

**File**: `src/utils/data_parsers.py`

**Input Parameters**:
- `months_string` (string): Comma-separated enrollment counts (e.g., "5, 4, 5, 4, 6, 0, 8, 10, 4, 8, 4, 8")

**Output**: List of integers representing monthly enrollment

**Used By**: Demand Forecasting Agent

**Error Handling**:
- Returns empty list if parsing fails
- Handles missing or malformed data
- Logs parsing errors

**Example Usage**:
```python
from src.utils.data_parsers import parse_monthly_enrollment, calculate_weekly_enrollment

months_data = "5, 4, 5, 4, 6, 0, 8, 10, 4, 8, 4, 8"
monthly_values = parse_monthly_enrollment(months_data)
weekly_avg = calculate_weekly_enrollment(months_data, recent_months=1)
```

---

### Tool 5: parse_shipping_timeline

**Purpose**: Extract numeric days from shipping timeline text

**File**: `src/utils/data_parsers.py`

**Input Parameters**:
- `timeline_text` (string): Timeline description (e.g., "6 days door-to-door")

**Output**: Integer representing number of days

**Used By**: Logistics Agent

**Error Handling**:
- Returns 0 if parsing fails
- Logs warnings for unparseable text
- Handles various text formats

**Example Usage**:
```python
from src.utils.data_parsers import parse_shipping_timeline

timeline = "6 days door-to-door"
days = parse_shipping_timeline(timeline)  # Returns: 6
```

---

### Tool 6: send_watchdog_alert (Email Integration)

**Purpose**: Send Supply Watchdog alerts via email using Resend API

**File**: `src/services/email_service.py`

**Input Parameters**:
- `workflow_result` (dict): Result from Workflow A execution containing JSON output

**Output**: Dictionary with send status
```python
{
    "success": bool,
    "message_id": str,  # Resend message ID
    "to": str,  # Recipient email
    "error": str  # Error message if failed
}
```

**Used By**: Workflow A (Supply Watchdog), Scheduled Watchdog Script

**Configuration** (in `.env`):
```
RESEND_API_KEY=re_xxxxxxxxx
ALERT_EMAIL_TO=recipient@example.com
ALERT_EMAIL_FROM=onboarding@resend.dev
```

**Email Features**:
- Professional HTML template with risk summary
- Color-coded severity (CRITICAL=red, HIGH=orange, MEDIUM=yellow)
- Expiry alerts table
- Shortfall predictions table
- JSON attachment with full data

**Example Usage**:
```python
from src.services.email_service import send_watchdog_alert

# After Workflow A execution
result = orchestrator.run_supply_watchdog(trigger_type="scheduled")

# Send email alert
email_result = send_watchdog_alert(result)

if email_result["success"]:
    print(f"Alert sent to {email_result['to']}")
```

---

## Section 2: System Prompts

This section provides complete system prompts for key agents with explanations.

---

### Supply Watchdog Agent Prompt (Workflow A - Required by Assignment)

**Purpose**: Autonomous monitoring agent that identifies expiring batches and predicts shortfalls

**Complete Prompt**:
```
You are the Supply Watchdog Agent, responsible for autonomous monitoring of clinical supply chain health.

Your responsibilities:
1. Identify ALLOCATED/RESERVED batches expiring within 90 days
2. Predict stock shortfalls based on enrollment trends
3. Generate structured JSON alerts for email notification
4. Run autonomously on a daily schedule

CRITICAL REQUIREMENT - Expiry Alerts:
You MUST query the allocated_materials_to_orders table (reserved batches) joined with batch_master (for expiry dates).
This is per assignment requirement: "Identify reserved batches (Allocated Materials) that are expiring in ≤ 90 days"

SQL Pattern for Expiry Alerts:
```sql
SELECT 
    a.material_component_batch as batch_id,
    a.material_comp_description as material,
    a.trial_alias,
    a.plant_desc as location,
    b.expiration_date_shelf_life as expiry_date,
    (b.expiration_date_shelf_life::date - CURRENT_DATE) as days_remaining
FROM allocated_materials_to_orders a
JOIN batch_master b ON a.material_component_batch = b.batch_number
WHERE b.expiration_date_shelf_life IS NOT NULL
  AND (b.expiration_date_shelf_life::date - CURRENT_DATE) <= 90
  AND (b.expiration_date_shelf_life::date - CURRENT_DATE) >= 0
ORDER BY days_remaining ASC
```

Severity Classification:
- CRITICAL: < 30 days remaining
- HIGH: 30-60 days remaining
- MEDIUM: 60-90 days remaining

CRITICAL REQUIREMENT - Shortfall Prediction:
Compare Projected Demand (from enrollment_rate_report) against Current Inventory (from available_inventory_report).
Alert if stock runs out within 8 weeks.

Calculation Logic:
1. Get recent enrollment from enrollment_rate_report (months_jan_feb_dec column)
2. Calculate weekly average: last_month_enrollment / 4
3. Project 8-week demand: weekly_avg * 8
4. Compare against current_stock from available_inventory_report
5. If projected_demand > current_stock → SHORTFALL ALERT

Output Format (JSON for email system):
{
  "alert_date": "YYYY-MM-DD",
  "risk_summary": {
    "total_expiring_batches": <integer>,
    "total_shortfall_predictions": <integer>
  },
  "expiry_alerts": [...],
  "shortfall_predictions": [...]
}

CRITICAL RULES:
- ALWAYS use allocated_materials_to_orders for expiry alerts (reserved batches)
- ALWAYS join with batch_master to get expiry dates
- ALWAYS include data citations (table name, query date)
- NEVER make assumptions - if data is missing, state it explicitly
- Generate valid JSON that can be parsed by email system
```

**Key Instructions**:
- **Correct Tables**: Uses `allocated_materials_to_orders` (not `available_inventory_report`) for expiry alerts per assignment
- **JOIN Required**: Must join with `batch_master` to get expiry dates
- **Severity Classification**: Matches assignment requirements exactly
- **JSON Output**: Structured for email alert system

**Schema Complexity Handling**:
- Uses Schema Retrieval Agent to get only relevant tables (4-5 max)
- Provides specific column names to avoid ambiguity
- Includes SQL patterns to guide query generation

---

### Router Agent Prompt

**Purpose**: Classify requests and route to appropriate agents

**Complete Prompt**:
```
You are the Router Agent, the entry point for all requests in the Clinical Supply Chain Control Tower system.

Your responsibilities:
1. Classify incoming requests as either Workflow A (Supply Watchdog) or Workflow B (Scenario Strategist)
2. Route requests to appropriate specialized agents
3. NEVER query the database directly

Classification Logic:
- Workflow A indicators: "scheduled", "daily check", "monitoring", "watchdog", "run supply check"
- Workflow B indicators: "can we", "should we", "what is", "show me", "has", specific questions about batches/materials

If the request is ambiguous, ask clarifying questions before routing.

Response Format:
{
    "workflow": "A" or "B",
    "intent": "brief description of user intent",
    "required_agents": ["list", "of", "agent", "names"],
    "clarification_needed": true/false,
    "clarification_question": "question to ask user if needed"
}
```

**Key Instructions**:
- **Workflow Classification**: Uses keyword matching to determine workflow type
- **Never Queries Database**: Router only classifies and routes, never accesses data
- **Clarification**: Asks user for clarification if intent is ambiguous

**Schema Complexity Handling**:
- Router doesn't need schema information
- Delegates schema retrieval to Schema Retrieval Agent
- Keeps context window minimal

**Response Format Enforcement**:
- Returns structured JSON with workflow type
- Lists required agents for execution
- Provides intent description for logging

**Edge Case Handling**:
- Handles ambiguous queries by requesting clarification
- Defaults to Workflow B for unknown patterns
- Logs classification decisions for debugging

---

### SQL Generation Agent Prompt

**Purpose**: Generate and execute PostgreSQL queries with self-healing

**Complete Prompt**:
```
You are the SQL Generation Agent, responsible for converting natural language intent into PostgreSQL queries.

Your responsibilities:
1. Generate syntactically correct PostgreSQL queries
2. Use ONLY the schemas provided by Schema Retrieval Agent
3. Implement self-healing retry logic (max 3 attempts)
4. Parse and interpret SQL error messages

PostgreSQL-Specific Rules:
- Use double quotes for identifiers with special characters
- Date format: 'YYYY-MM-DD'
- Use INTERVAL for date arithmetic: CURRENT_DATE + INTERVAL '90 days'
- Use LIMIT clauses for large result sets
- Use parameterized queries to prevent SQL injection

Self-Healing Logic:
Attempt 1: Generate SQL from intent and provided schema
Attempt 2: If error, analyze error message and correct
  - Example: "column expiry does not exist" → check schema for correct column name (expiry_date)
Attempt 3: If still failing, request additional schemas from Schema Retrieval Agent

Error Handling:
- Capture exact PostgreSQL error message
- Identify error type: syntax, missing column, type mismatch, etc.
- Generate corrected query based on error analysis
- After 3 failures: Return user-friendly explanation

Response Format:
{
    "query": "<SQL query string>",
    "attempt": <1, 2, or 3>,
    "success": true/false,
    "error": "<error message if failed>",
    "explanation": "<user-friendly explanation>",
    "tables_used": ["list", "of", "tables"],
    "estimated_rows": <approximate result size>
}

CRITICAL RULES:
- NEVER execute queries without schema validation
- NEVER return raw SQL errors to users
- Always use LIMIT for exploratory queries
- Validate date formats before execution
- Use explicit column names, avoid SELECT *
```

**Key Instructions**:
- **PostgreSQL-Specific**: Uses PostgreSQL syntax (INTERVAL, double quotes)
- **Schema-Dependent**: Only uses columns from provided schemas
- **Self-Healing**: Analyzes errors and corrects queries automatically

**Schema Complexity Handling**:
- Requests schemas from Schema Retrieval Agent before generating
- Uses only provided schema information
- Requests additional schemas if initial set insufficient
- Never assumes column names not in schema

**Response Format Enforcement**:
- Returns structured dictionary with query and metadata
- Includes attempt number for tracking
- Provides user-friendly explanations for failures

**Edge Case Handling**:
- **Missing Columns**: Analyzes error, checks schema, corrects column name
- **Table Not Found**: Requests additional schemas
- **Syntax Errors**: Parses error message, regenerates query
- **Timeout**: Adds LIMIT clause to reduce result size
- **After 3 Failures**: Returns explanation instead of continuing

---

### Synthesis Agent Prompt

**Purpose**: Aggregate multi-agent outputs and format responses

**Complete Prompt**:
```
You are the Synthesis Agent, responsible for aggregating outputs from multiple agents and formatting final responses.

Your responsibilities:
1. Combine outputs from specialized agents
2. Generate structured JSON for Workflow A
3. Produce natural language responses with citations for Workflow B
4. Ensure all responses include data citations

For Workflow A (Supply Watchdog):
Generate exact JSON structure:
{
  "alert_date": "YYYY-MM-DD",
  "risk_summary": {
    "total_expiring_batches": <integer>,
    "total_shortfall_predictions": <integer>
  },
  "expiry_alerts": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM",
      "batch_id": "<string>",
      "material": "<string>",
      "location": "<string>",
      "expiry_date": "YYYY-MM-DD",
      "days_remaining": <integer>,
      "quantity": <integer>,
      "unit": "<string>"
    }
  ],
  "shortfall_predictions": [
    {
      "country": "<string>",
      "material": "<string>",
      "current_stock": <integer>,
      "projected_8week_demand": <integer>,
      "shortfall": <integer>,
      "estimated_stockout_date": "YYYY-MM-DD"
    }
  ]
}

For Workflow B (Scenario Strategist):
Structure responses with clear sections:

[DIRECT ANSWER FIRST]

[DETAILED ANALYSIS]
Technical Check: [✓ PASS / ✗ FAIL]
- Finding with data citation
- Source: Table name, Record ID, Date

Regulatory Check: [✓ PASS / ✗ FAIL]
- Finding with data citation
- Source: Table name, Record ID, Date

Logistical Check: [✓ PASS / ⚠ CONDITIONAL / ✗ FAIL]
- Calculation shown explicitly
- Source: Table name

RECOMMENDATION: [Clear action statement]

Citation Format:
- Always include: Table name, Column name, Specific value
- Include timestamps when available
- Show calculations explicitly
- Use confidence indicators when appropriate

CRITICAL RULES:
- NEVER make assumptions or fill in missing data
- If agents provide conflicting data, present both with sources
- For YES/NO questions, answer must be clear and unambiguous
- Always explain reasoning with data citations
```

**Key Instructions**:
- **Workflow-Specific**: Different formats for Workflow A (JSON) vs B (natural language)
- **Citation Mandatory**: Every response must include data sources
- **No Assumptions**: Only uses data provided by agents

**Schema Complexity Handling**:
- Doesn't need schemas directly
- Receives processed data from domain agents
- Focuses on formatting and aggregation

**Response Format Enforcement**:
- Strict JSON structure for Workflow A
- Structured natural language for Workflow B
- Always includes citations section
- Clear YES/NO/CONDITIONAL answers

**Edge Case Handling**:
- **Conflicting Data**: Presents both sources with timestamps
- **Missing Data**: States explicitly what's missing
- **Incomplete Agent Outputs**: Works with available data, notes gaps

---

### Inventory Agent Prompt (Domain Agent Example)

**Purpose**: Manage stock and expiry tracking

**Complete Prompt**:
```
You are the Inventory Agent, responsible for stock and expiry management.

Your responsibilities:
1. Check inventory levels by location/material
2. Identify expiring batches within specified time windows
3. Calculate available vs allocated stock
4. Provide accurate inventory status with data citations

Tables you access:
- allocated_materials_to_orders: Reserved inventory with expiry tracking
- available_inventory_report: Current stock levels
- affiliate_warehouse_inventory: Warehouse-specific inventory
- complete_warehouse_inventory: Comprehensive inventory view

Response Format:
Always cite your sources:
- Table: <table_name>
- Column: <column_name>
- Value: <specific_value>
- Query Date: <timestamp>

For expiry checks:
- Batch ID
- Material
- Location
- Expiry Date (YYYY-MM-DD)
- Days Remaining
- Quantity with units
- Severity (CRITICAL <30 days, HIGH 30-60 days, MEDIUM 60-90 days)

CRITICAL RULES:
- Always request schema from Schema Retrieval Agent before querying
- Use SQL Generation Agent for all database queries
- Never make assumptions - if data is missing, state it explicitly
- Always include units with quantities
```

**Key Instructions**:
- **Domain-Specific**: Focuses only on inventory-related operations
- **Schema-Aware**: Requests schemas before querying
- **Citation-Required**: Every response includes data sources

**Schema Complexity Handling**:
- Requests only inventory-related tables (4 tables max)
- Uses Schema Retrieval Agent to get schemas
- Provides schema to SQL Generation Agent

**Response Format Enforcement**:
- Structured dictionary with operation results
- Includes severity classification for expiry
- Always includes citations list

**Edge Case Handling**:
- **Batch Not Found**: Returns clear message with tables checked
- **Multiple Locations**: Returns all locations for batch
- **Missing Expiry Date**: States explicitly and suggests alternatives

---

## Section 3: SQL Query for Shortfall Prediction

This is the critical SQL query that solves Workflow A's shortfall prediction requirement.

### Complete SQL Query with Comments

```sql
-- ============================================================================
-- SHORTFALL PREDICTION QUERY
-- Purpose: Calculate predicted stock shortfalls based on enrollment trends
-- Workflow: A (Supply Watchdog)
-- ============================================================================

-- Step 1: Get recent enrollment data and calculate weekly averages
-- Note: The enrollment_rate_report stores monthly data as comma-separated string
-- This query retrieves the data; parsing happens in Python using data_parsers.py
WITH recent_enrollment AS (
    SELECT 
        trial_alias,
        country,
        site,
        year,
        months_jan_feb_dec,  -- Format: "5, 4, 5, 4, 6, 0, 8, 10, 4, 8, 4, 8"
        -- Python will parse this string to extract last month's enrollment
        -- and calculate weekly average: last_month_value / 4
        CURRENT_DATE as query_date
    FROM enrollment_rate_report
    WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)
    -- Filter for current year to get most recent data
),

-- Step 2: Get current inventory levels by trial and location
current_inventory AS (
    SELECT 
        trial_name,
        location as country,
        -- Sum all received packages across all batches for this trial/location
        SUM(received_packages) as current_stock,
        -- Also track shipped packages to understand net available
        SUM(shipped_packages) as shipped_stock,
        -- Calculate net available stock
        SUM(received_packages) - SUM(shipped_packages) as net_available,
        COUNT(*) as batch_count,
        CURRENT_DATE as query_date
    FROM available_inventory_report
    WHERE received_packages > 0  -- Only count batches with actual stock
    GROUP BY trial_name, location
),

-- Step 3: Join enrollment with inventory to calculate shortfalls
-- Note: The actual demand calculation happens in Python because we need to:
-- 1. Parse the comma-separated months string
-- 2. Extract the last month's enrollment
-- 3. Calculate weekly average (last_month / 4)
-- 4. Project 8-week demand (weekly_avg * 8)
-- This SQL provides the base data for Python processing
enrollment_with_inventory AS (
    SELECT 
        e.trial_alias,
        e.country,
        e.site,
        e.months_jan_feb_dec,
        -- Current stock from inventory
        COALESCE(i.current_stock, 0) as current_stock,
        COALESCE(i.net_available, 0) as net_available,
        i.batch_count,
        e.query_date
    FROM recent_enrollment e
    LEFT JOIN current_inventory i 
        ON e.trial_alias = i.trial_name 
        AND e.country = i.country
)

-- Step 4: Return data for Python processing
-- Python will:
-- 1. Parse months_jan_feb_dec: "5, 4, 5, 4, 6, 0, 8, 10, 4, 8, 4, 8" -> [5,4,5,4,6,0,8,10,4,8,4,8]
-- 2. Get last month: 8
-- 3. Calculate weekly: 8 / 4 = 2.0
-- 4. Project 8-week demand: 2.0 * 8 = 16
-- 5. Calculate shortfall: current_stock - projected_demand
-- 6. If shortfall < 0: estimate stockout date
SELECT 
    trial_alias,
    country,
    site,
    months_jan_feb_dec,
    current_stock,
    net_available,
    batch_count,
    query_date
FROM enrollment_with_inventory
ORDER BY trial_alias, country;

-- ============================================================================
-- EXPECTED OUTPUT FORMAT (after Python processing):
-- ============================================================================
-- {
--   "country": "Germany",
--   "material": "CT-2004-PSX",
--   "avg_weekly_enrollment": 2.0,
--   "projected_8week_demand": 16.0,
--   "current_stock": 50,
--   "shortfall": -34.0,  -- Negative means surplus, positive means shortage
--   "estimated_stockout_date": null  -- No stockout if surplus
-- }
--
-- If shortfall is positive (shortage):
-- estimated_stockout_date = CURRENT_DATE + (current_stock / weekly_avg * 7) days
--
-- Example: 
-- current_stock = 50, weekly_avg = 10
-- weeks_until_stockout = 50 / 10 = 5 weeks
-- days_until_stockout = 5 * 7 = 35 days
-- stockout_date = CURRENT_DATE + 35 days
-- ============================================================================

-- ============================================================================
-- TABLE JOINS EXPLANATION:
-- ============================================================================
-- 1. enrollment_rate_report: Source of demand data
--    - Contains historical enrollment by trial, country, site
--    - Monthly data stored as comma-separated string
--    - Filtered by current year for recent trends
--
-- 2. available_inventory_report: Source of supply data
--    - Contains current stock levels by trial and location
--    - Aggregated by trial_name and location (country)
--    - Only includes batches with received_packages > 0
--
-- 3. JOIN Logic:
--    - LEFT JOIN ensures we see all enrollment data
--    - Even if no inventory exists (current_stock = 0)
--    - Matches on trial_alias = trial_name AND country = location
--    - COALESCE handles NULL inventory values
--
-- ============================================================================
-- CALCULATION LOGIC (Python):
-- ============================================================================
-- 1. Parse Monthly Enrollment:
--    Input: "5, 4, 5, 4, 6, 0, 8, 10, 4, 8, 4, 8"
--    Output: [5, 4, 5, 4, 6, 0, 8, 10, 4, 8, 4, 8]
--
-- 2. Calculate Weekly Average:
--    last_month = monthly_data[-1]  # Get last value: 8
--    weekly_avg = last_month / 4    # Assume 4 weeks per month: 2.0
--
-- 3. Project 8-Week Demand:
--    projected_demand = weekly_avg * 8  # 2.0 * 8 = 16.0
--
-- 4. Calculate Shortfall:
--    shortfall = current_stock - projected_demand
--    # 50 - 16 = 34 (surplus)
--    # 10 - 16 = -6 (shortage of 6 units)
--
-- 5. Estimate Stockout Date (if shortage):
--    if shortfall < 0:
--        weeks_until_stockout = current_stock / weekly_avg
--        days_until_stockout = weeks_until_stockout * 7
--        stockout_date = CURRENT_DATE + days_until_stockout
--
-- ============================================================================
-- PERFORMANCE NOTES:
-- ============================================================================
-- - Query uses CTEs for readability and maintainability
-- - Aggregation in current_inventory reduces data volume
-- - LEFT JOIN ensures no enrollment data is lost
-- - Filtering by current year limits data volume
-- - Python processing allows complex string parsing
-- - Consider adding indexes on:
--   * enrollment_rate_report(trial_alias, country, year)
--   * available_inventory_report(trial_name, location)
-- ============================================================================
```

### Why This Approach?

**Hybrid SQL + Python Processing**:
- SQL handles data retrieval and aggregation
- Python handles complex string parsing and calculations
- Separates concerns: SQL for data, Python for business logic

**Data Integrity**:
- LEFT JOIN ensures all enrollment data included
- COALESCE handles missing inventory gracefully
- Filters ensure only relevant, current data used

**Scalability**:
- CTEs make query maintainable
- Aggregation reduces data volume
- Can be optimized with indexes

---

## Section 4: Vector Database Implementation

### What is Stored

The vector database (ChromaDB) stores **schema metadata only**, never actual business data.

**Schema Metadata Structure**:
```python
{
    "table_name": "available_inventory_report",
    "business_purpose": "PRIMARY SOURCE for current stock levels and EXPIRY DATES",
    "columns": [
        {
            "name": "trial_name",
            "type": "VARCHAR",
            "description": "Trial name (e.g., 'Shake Study', 'Put Trial')"
        },
        {
            "name": "expiry_date",
            "type": "DATE",
            "description": "Expiry date (YYYY-MM-DD) - CRITICAL for Workflow A"
        }
        # ... more columns
    ],
    "join_patterns": [
        "JOIN allocated_materials_to_orders ON lot = material_component_batch"
    ],
    "query_templates": [
        "SELECT * FROM available_inventory_report WHERE expiry_date <= CURRENT_DATE + INTERVAL '90 days'"
    ]
}
```

**Document Text for Embedding**:
```
Table: available_inventory_report
Purpose: PRIMARY SOURCE for current stock levels and EXPIRY DATES by location, trial, and batch
Columns: trial_name, location, lot, expiry_date, received_packages, shipped_packages
Column Details: trial_name (VARCHAR): Trial name | location (VARCHAR): Storage location/country | lot (VARCHAR): Lot/Batch number | expiry_date (DATE): Expiry date YYYY-MM-DD - CRITICAL for Workflow A
Common Joins: JOIN allocated_materials_to_orders ON lot = material_component_batch
Query Patterns: SELECT * FROM available_inventory_report WHERE expiry_date <= CURRENT_DATE + INTERVAL '90 days'
```

### Embedding Strategy

**Model**: `text-embedding-3-small` (OpenAI)
- High-quality semantic understanding
- 1536-dimensional embeddings
- Excellent for technical text and schema descriptions
- Consistent with LLM provider (OpenAI)

**Embedding Process**:
1. Concatenate table metadata into single text document (including keywords, sample queries, related entities)
2. Generate embedding using OpenAI API
3. Store in ChromaDB with metadata
4. Index by table name for direct retrieval

**Why This Model**:
- Superior semantic understanding
- Consistent with OpenAI ecosystem (same provider as GPT-4)
- Better handling of technical terminology
- 1536 dimensions provide rich representation

### Retrieval Query Logic

**Semantic Search Flow**:
```python
# 1. User query comes in
user_query = "expiry dates and inventory levels"

# 2. Generate embedding using OpenAI
response = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=[user_query]
)
query_embedding = response.data[0].embedding

# 3. Search vector database
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5  # Maximum 5 tables
)

# 4. Return relevant schemas with similarity scores
schemas = []
for i, table_id in enumerate(results['ids'][0]):
    distance = results['distances'][0][i]
    similarity = 1 - (distance / 2)  # Normalize cosine distance
    
    schemas.append({
        "table_name": table_id,
        "similarity_score": max(0, similarity),
        "business_purpose": results['metadatas'][0][i].get('business_purpose', '')
    })

# 5. Format for agent consumption
formatted_schemas = format_schemas_for_agent(schemas)
```

**Relevance Scoring**:
- Cosine similarity between query and schema embeddings
- Score range: 0.0 (no match) to 1.0 (perfect match)
- Typical threshold: 0.6 for relevance
- Top 5 results returned

**Workflow-Specific Retrieval**:
```python
# All tables are accessible to both workflows
# Workflow A uses specific tables programmatically
# Workflow B uses semantic search across all tables
schemas = chroma_manager.find_relevant_tables(
    query=user_query,
    n_results=5
)
```

### How This Solves Context Window Problem

**Problem**: 40+ tables with full schemas = ~50,000 tokens (exceeds most LLM context windows)

**Solution**: Vector DB retrieval
1. **Store Once**: All 40 table schemas embedded and stored
2. **Retrieve Selectively**: Only 2-5 relevant tables per query
3. **Context Efficient**: 2-5 tables = ~2,000-5,000 tokens (fits easily)
4. **Semantic Matching**: Finds relevant tables even with different terminology

**Example**:
```
User Query: "Show me batches expiring soon"

Without Vector DB:
- Load all 40 table schemas
- ~50,000 tokens
- Exceeds context window
- LLM confused by irrelevant tables

With Vector DB:
- Semantic search finds relevant tables:
  1. available_inventory_report (score: 0.92)
  2. allocated_materials_to_orders (score: 0.78)
  3. batch_master (score: 0.71)
- Only 3 tables loaded
- ~3,000 tokens
- Fits in context window
- LLM focuses on relevant schemas
```

**Benefits**:
1. **Scalability**: Can handle 100s of tables
2. **Efficiency**: Minimal context usage
3. **Accuracy**: Finds relevant tables semantically
4. **Speed**: Fast retrieval (< 100ms)
5. **Flexibility**: Easy to add new tables

---

## Section 5: Autonomous Scheduling (Workflow A Cron Job)

Per assignment requirement: "The system must run autonomously (e.g., daily cron)"

### Scheduler Implementation

**File**: `scripts/scheduled_watchdog.py`

**Technology**: APScheduler (Python-native scheduling library)

**Configuration** (in `.env`):
```
WATCHDOG_SCHEDULE_HOUR=8
WATCHDOG_SCHEDULE_MINUTE=0
```

### Usage

```bash
# Run once immediately (for testing)
python scripts/scheduled_watchdog.py --run-now

# Start daily scheduler (runs at configured time)
python scripts/scheduled_watchdog.py

# Custom schedule (every 6 hours)
python scripts/scheduled_watchdog.py --interval-hours 6

# Custom daily time (2:30 PM)
python scripts/scheduled_watchdog.py --hour 14 --minute 30
```

### Execution Flow

```
Scheduler Trigger (8:00 AM daily)
    ↓
run_watchdog() function
    ↓
get_orchestrator().run_supply_watchdog(trigger_type="scheduled")
    ↓
Workflow A executes (Inventory + Demand agents)
    ↓
JSON output generated
    ↓
send_watchdog_alert(result) → Email sent via Resend
    ↓
Log results to watchdog.log
```

### Production Deployment Options

For production environments, the scheduler can be deployed as:

1. **Background Process**: `python scripts/scheduled_watchdog.py &`
2. **System Service**: Windows Task Scheduler / Linux systemd
3. **Cloud Scheduler**: AWS CloudWatch Events, Railway Cron, etc.

---

## Conclusion

This technical implementation demonstrates:
- **Comprehensive tooling** for all agent operations (6 tools documented)
- **Well-designed prompts** that handle complexity and edge cases
- **Efficient SQL** with clear business logic
- **Smart vector DB usage** that solves the context window problem
- **Autonomous scheduling** with email alerts (per assignment requirement)
- **Email integration** via Resend API for alert delivery

All components work together to create a robust, scalable, and maintainable agentic AI system.
