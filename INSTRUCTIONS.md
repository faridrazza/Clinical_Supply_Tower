Clinical Supply Chain Control Tower - Agentic AI System
Developer Implementation Guide

1. Project Objective & Scope
Build a functional Agentic AI system for pharmaceutical clinical supply chain management with:

Two Core Workflows:

Workflow A: Autonomous Supply Watchdog (scheduled risk detection)
Workflow B: Conversational Scenario Strategist (interactive decision support)


Mandatory Deliverables:

Working multi-agent architecture
PostgreSQL-backed data operations (zero hallucinations)
Explainable decision-making with data citations
Deployed web application with shareable URL
Comprehensive documentation (3 required parts)




2. Technology Stack (Non-Negotiable)
ComponentTechnologyRationaleBackendPythonAssignment requirementAgent FrameworkLangGraphRequired for multi-agent orchestrationLLMOpenAI GPT-4 or Anthropic ClaudeSpecified in assignmentDatabasePostgreSQLRequired for structured dataVector DBChromaDB / Weaviate / PineconeSchema management onlyFrontendStreamlit (recommended) or ReactFast deployment requiredDeploymentRender / Railway / Streamlit CloudMust provide public URLDocumentationMarkdownGitHub repository format
Out of Scope: Authentication, rate limiting, Redis, Celery, performance optimization, scaling infrastructure.

3. Data Architecture
3.1 PostgreSQL Setup

Load all CSV files into PostgreSQL as individual tables
Preserve original column names unless they cause SQL syntax errors
Create a schema registry documenting:

Table name
Business purpose
Key columns with data types
Sample values
Common join patterns



3.2 Critical Tables by Workflow
Workflow A - Supply Watchdog:

Allocated Materials - Reserved inventory + expiry tracking
Available Inventory Report - Current stock levels
Enrollment Rate Report - Historical demand data
Country Level Enrollment - Geographic demand patterns

Workflow B - Scenario Strategist:

Re-Evaluation - Shelf-life extension history
RIM - Regulatory approvals by country
Material Country Requirements - Country-specific regulations
IP Shipping Timelines - Logistics lead times
Distribution Order Report - Shipment tracking

Supporting Tables:
All other tables should be loaded and documented but are not mandatory for core demonstrations.

4. Vector Database Strategy
4.1 Purpose
Solve the context window problem: 40+ tables cannot fit in LLM context simultaneously.
4.2 What to Store (Schema Metadata Only)
Embed and store:

Table descriptions - Business purpose of each table
Column metadata - Name, type, description, example values
Relationship patterns - Common JOIN operations
Query templates - Example SQL patterns for frequent operations

4.3 Retrieval Logic
User Query → Embed Query → Vector Search → Retrieve 2-5 Relevant Tables → Pass Schema to Agent
Critical Rule: Never store or retrieve actual business data from vector DB. It is a schema catalog only.

5. Multi-Agent Architecture (Strict Design)
5.1 Required Agents
Router Agent

Role: Entry point and workflow classifier
Responsibilities:

Determine if request is Workflow A or Workflow B
Route to appropriate specialized agents
Never queries database directly


Decision Logic:

Keywords: "scheduled", "daily check" → Workflow A
Keywords: "can we", "should we", specific questions → Workflow B



Schema Retrieval Agent

Role: Context window manager
Responsibilities:

Query vector DB for relevant table schemas
Return maximum 5 tables at a time
Provide formatted schema to other agents


Output Format: Table name, purpose, key columns, join hints

Inventory Agent

Role: Stock and expiry management
Tables: Allocated Materials, Available Inventory Report, Affiliate Warehouse Inventory
Capabilities:

Check inventory levels by location/material
Identify expiring batches within time window
Calculate available vs allocated stock



Demand Forecasting Agent

Role: Enrollment analysis and demand projection
Tables: Enrollment Rate Report, Country Level Enrollment
Capabilities:

Calculate average weekly enrollment (last 4-8 weeks)
Project 8-week forward demand
Predict stockout dates



Regulatory Agent

Role: Compliance verification
Tables: RIM, Material Country Requirements, Re-Evaluation
Capabilities:

Check shelf-life extension approval status by country
Verify re-evaluation history
Validate regulatory submission status



Logistics Agent

Role: Shipping feasibility assessment
Tables: IP Shipping Timelines, Distribution Order Report
Capabilities:

Calculate shipping lead times
Determine if redistribution possible before expiry
Account for customs, delivery buffer



SQL Generation Agent

Role: Query construction and execution
Responsibilities:

Convert natural language intent to PostgreSQL
Use provided schemas only
Implement self-healing retry (max 3 attempts)
Capture and parse SQL error messages


Self-Healing Logic:

Generate SQL from intent
If error → analyze error message → correct SQL
If still fails → request additional schema → retry
After 3 failures → return explanation to user



Synthesis Agent

Role: Response aggregation and formatting
Responsibilities:

Combine outputs from multiple agents
Generate structured JSON (Workflow A)
Produce explained answers with citations (Workflow B)
Always cite: table name, column, specific values used



5.2 Agent Interaction Patterns
Pattern 1: Simple Query (Workflow B)
User: "What is stock level of Material X?"
→ Router → Inventory Agent → SQL Agent → Response
Pattern 2: Complex Decision (Workflow B)
User: "Can we extend Batch #123 expiry for Germany?"
→ Router 
  → Schema Retrieval (get relevant tables)
  → Inventory Agent (check batch exists, expiry date)
  → Regulatory Agent (check country approval)
  → Logistics Agent (check shipping feasibility)
  → Synthesis Agent (combine checks, cite sources, YES/NO answer)
Pattern 3: Autonomous Monitoring (Workflow A)
Scheduled Trigger (daily cron)
→ Router (recognizes Workflow A)
  → Inventory Agent (find batches expiring ≤90 days)
  → Demand Forecasting Agent (calculate 8-week shortfall)
  → Synthesis Agent (generate JSON alert)

6. Workflow A: Supply Watchdog (Detailed Specification)
6.1 Trigger Mechanism

Scheduled execution (daily at 6 AM or manual trigger)
Runs without human intervention
Must generate structured output

6.2 Risk 1: Expiry Alert Logic
Query Requirements:

Select from Allocated Materials table
Filter: expiry_date <= CURRENT_DATE + INTERVAL '90 days'
Calculate: days_remaining = expiry_date - CURRENT_DATE
Classify severity:

Critical: < 30 days remaining
High: 30-60 days remaining
Medium: 60-90 days remaining



Required Output Fields:

Batch ID
Material name
Location/warehouse
Allocated quantity with units
Expiry date (YYYY-MM-DD)
Days remaining (integer)
Severity level

6.3 Risk 2: Shortfall Prediction Logic
Calculation Steps:

Get last 4 weeks of enrollment data from Enrollment Rate Report
Calculate: avg_weekly_enrollment = SUM(weekly_enrollments) / 4
Project: demand_8weeks = avg_weekly_enrollment × 8
Get current stock from Available Inventory Report
Calculate: shortfall = current_stock - demand_8weeks
If shortfall < 0: FLAG as predicted stockout
Estimate: stockout_date = CURRENT_DATE + (current_stock / avg_weekly_enrollment × 7)

Group Results By: Country, Material
6.4 Required JSON Output Format
json{
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
```

---

## 7. Workflow B: Scenario Strategist (Detailed Specification)

### 7.1 Core Use Case: Shelf-Life Extension Feasibility

**User Query Example:**
"Can we extend the expiry of Batch #123 for Germany?"

**Required Three-Constraint Check:**

#### **Constraint 1: Technical Feasibility**
- Query `Re-Evaluation` table
- Check: Has this batch/material been re-evaluated before?
- Determine: How many times? (typical limit: 2-3 extensions)
- Output: "Batch #123 extended X times on [dates]. Remaining extensions: Y"

#### **Constraint 2: Regulatory Approval**
- Query `RIM` table and `Material Country Requirements`
- Check: Is shelf-life extension approved for this material in Germany?
- Verify: Approval status (Approved / Pending / Not Submitted)
- Output: "Extension approved in Germany on [date], Regulatory ID: [ID]" OR "Extension not approved in Germany"

#### **Constraint 3: Logistical Feasibility**
- Query `IP Shipping Timelines` table
- Calculate: `days_until_expiry - shipping_lead_time = available_window`
- Recommendation: Minimum 30-day buffer for usage
- Output: "Batch expires in 45 days. Shipping takes 14 days. Available window: 31 days"

### 7.2 Response Structure (Mandatory Format)
```
CAN WE EXTEND BATCH #123 FOR GERMANY?

Answer: [YES / NO / CONDITIONAL]

Technical Check: [✓ PASS / ✗ FAIL]
- [Specific finding with data citation]
- Source: [Table name, Record ID, Date]

Regulatory Check: [✓ PASS / ✗ FAIL]
- [Specific finding with data citation]
- Source: [Table name, Record ID, Date]

Logistical Check: [✓ PASS / ⚠ CONDITIONAL / ✗ FAIL]
- [Calculation shown explicitly]
- Source: [Table name]

RECOMMENDATION: [Clear action statement]
```

### 7.3 Other Query Types to Support

1. "Show me all batches expiring in [Country] within [X] days"
2. "What is current stock level for [Material] in [Location]?"
3. "Predict demand for [Trial/Country] for next [X] weeks"
4. "Has [Batch ID] been re-evaluated before?"
5. "What is shipping time from [Origin] to [Destination]?"
6. "Compare inventory across [multiple locations]"

**Response Rules for All Queries:**
- Clear, direct answer first
- Specific data citations (table name, column, value)
- No assumptions or guesses
- If data missing or conflicting, state explicitly
- Provide reasoning for conclusions

---

## 8. Edge Case Handling (Critical Requirements)

### 8.1 Ambiguous Entity Names

**Problem:** User says "Trial ABC" but database has "Trial_ABC_v2", "Trial-ABC", "trial_abc"

**Resolution Strategy:**
1. **Exact Match:** Check if user input exists exactly
2. **Case-Insensitive Match:** Try uppercase/lowercase variations
3. **Fuzzy Matching:**
   - Remove special characters (-, _, spaces)
   - Calculate similarity score
   - If score > 80%: Use match automatically
   - If score 60-80%: Ask user "Did you mean [option]?"
   - If score < 60%: Show top 3 options, ask user to select
4. **Session Memory:** Remember user's choice for remainder of conversation

**Implementation Requirement:** Build lookup table during data loading phase mapping common variations to canonical names.

### 8.2 Invalid SQL Self-Healing Loop

**Problem:** Agent generates SQL query that fails execution

**Self-Healing Process:**

**Attempt 1: Initial Generation**
- Agent receives schema from Schema Retrieval Agent
- Generates SQL query
- Validate basic syntax before execution

**Attempt 2: Error-Driven Correction**
- Capture exact error message from PostgreSQL
- Feed error + original query + schema back to SQL Agent
- Agent analyzes: "Error says 'column expiry does not exist', available columns show 'expiry_date'"
- Agent regenerates corrected query

**Attempt 3: Schema Refresh**
- If still failing, request additional schemas from Schema Retrieval Agent
- Load related tables that might have been missed
- Agent tries with expanded context

**Failure Handling:**
- After 3 attempts: Return to user with explanation
- Format: "I attempted to query [table] but encountered [specific issue]. Available columns are [list]. Can you rephrase your question?"
- Log failure for manual review

**Critical Rule:** Never return raw SQL errors to user. Always translate to business-friendly explanation.

### 8.3 Missing or Conflicting Data

**Scenario 1: Entity Not Found**
```
User: "Show expiry of Batch #999"
Agent checks: Batch #999 not in Allocated Materials, Available Inventory, or Re-Evaluation

Response Format:
"I couldn't find Batch #999 in the system.

What I checked:
- Allocated Materials: No record
- Available Inventory Report: No record
- Re-Evaluation history: No record

Possible reasons:
1. Batch number may be formatted differently (e.g., BATCH-0999)
2. Batch fully consumed and archived
3. Batch belongs to different study not in database

Similar active batches: #998, #1000, #1001

Would you like me to search with different format or show active batches for specific material?"
```

**Scenario 2: Conflicting Data**
```
Available Inventory Report shows: 500 units
Allocated Materials shows: 450 units allocated

Response Format:
"I found conflicting data for Material X:

Source 1 - Available Inventory Report (updated: 2025-01-14): 500 units
Source 2 - Allocated Materials (updated: 2025-01-13): 450 units allocated

Note: Available Inventory Report is the primary source (updates nightly from warehouse system). The 50-unit difference may indicate recent consumption not yet reflected in allocation records.

Recommendation: Use 500 units as current available stock. Verify with warehouse if critical."
```

### 8.4 Context Window Management

**Problem:** Long conversations exceed LLM context limits

**Mitigation Strategy:**
1. **Summarization:** After every 10 messages, compress conversation history
   - Keep: User intent, key findings, entity names mentioned
   - Discard: Verbose explanations, intermediate steps, full SQL queries

2. **Selective Memory:**
   - Remember: Previous queries, clarifications, user preferences
   - Forget: Detailed table schemas, full result sets

3. **Progressive Loading:**
   - Load minimal schema first
   - Request additional schema only when needed
   - Never load all 40 tables simultaneously

---

## 9. System Prompts (Design Principles)

Each agent requires a carefully designed system prompt that includes:

### 9.1 Core Components for All Agents
1. **Role Definition:** "You are the [Agent Name] responsible for [specific domain]"
2. **Table Access:** "You have access to these tables: [list]"
3. **Constraints:** "You MUST / MUST NOT do [specific rules]"
4. **Response Format:** "Always format responses as [structure]"
5. **Citation Requirement:** "Always cite: table name, column name, specific value"
6. **Error Handling:** "If you encounter [error type], do [action]"

### 9.2 Router Agent Prompt Requirements
- Classification criteria for Workflow A vs Workflow B
- Keywords indicating different agent requirements
- Instruction to NEVER query database directly
- Rule to ask clarifying questions before routing if ambiguous

### 9.3 Schema Retrieval Agent Prompt Requirements
- Maximum 5 tables per retrieval
- Schema format specification
- Prioritization logic (most relevant tables first)
- Instructions for handling "no match found" scenarios

### 9.4 SQL Generation Agent Prompt Requirements
- PostgreSQL-specific syntax rules
- Instruction to request schema before generating
- Self-healing loop logic
- Maximum 3 retry attempts
- Error message interpretation guidelines
- Instruction to use LIMIT clauses for large result sets
- Date format standardization (YYYY-MM-DD)

### 9.5 Synthesis Agent Prompt Requirements
- Workflow A: Generate exact JSON structure
- Workflow B: Natural language with structured sections
- Mandatory citation format
- Confidence indicators when appropriate
- Clear YES/NO/CONDITIONAL answers for decision queries

**Critical Prompt Engineering Rule:** Prompts must handle schema complexity without overwhelming context. Always instruct agents to request minimal necessary schema through Schema Retrieval Agent.

---

## 10. Web Application Requirements

### 10.1 Two Required Interfaces

#### **Interface 1: Monitoring Dashboard (Workflow A)**

**Components:**
1. **Summary Cards:**
   - Total expiring batches (with count)
   - Total predicted shortfalls (with count)
   - Last run timestamp
   - Overall risk indicator (Red/Orange/Yellow/Green)

2. **Expiry Alerts Table:**
   - Columns: Severity, Batch ID, Material, Location, Expiry Date, Days Remaining, Quantity
   - Sortable by severity and days remaining
   - Color coding: Red (Critical), Orange (High), Yellow (Medium)
   - Filter by severity level

3. **Shortfall Predictions Table:**
   - Columns: Country, Material, Current Stock, Projected Demand, Shortfall Amount, Estimated Stockout Date
   - Sortable by shortfall magnitude
   - Filter by country

4. **Controls:**
   - Date selector for historical runs
   - Export JSON button
   - Refresh/Re-run button

#### **Interface 2: Conversational Assistant (Workflow B)**

**Components:**
1. **Chat Interface:**
   - Message input box (multiline support)
   - Conversation history display
   - Typing indicator during agent processing
   - Clear conversation button

2. **Response Formatting:**
   - Structured headings for multi-part answers
   - Data tables where appropriate
   - Citation footnotes (subtle but visible)
   - Confidence indicators for recommendations

3. **Helper Features:**
   - 5-6 example starter questions displayed on empty state
   - Copy response button for each message
   - Export conversation option

4. **Visual Design:**
   - Clean, professional layout
   - Readable typography
   - Adequate spacing for long responses
   - Mobile-responsive (works on tablets/phones)

### 10.2 User Experience Requirements

- **No authentication required** for this assignment
- Loading indicators for all operations
- Clear error messages (never show raw errors)
- Progressive data loading (don't block entire UI)
- Keyboard accessibility (Enter to send message, etc.)

### 10.3 Technical UI Requirements

- **Frontend-Backend Communication:**
  - RESTful API endpoints or
  - WebSocket for real-time chat (optional)
  
- **State Management:**
  - Maintain conversation context
  - Remember user's last query for follow-ups
  
- **Performance:**
  - Responses within 10 seconds for simple queries
  - Progressive responses for complex multi-agent queries

---

## 11. Deployment Requirements

### 11.1 Mandatory Deployment

- Application MUST be deployed with publicly accessible URL
- Evaluators must be able to:
  - View monitoring dashboard without login
  - Use conversational assistant
  - Test both workflows

### 11.2 Recommended Platforms

**Option 1: Streamlit Cloud (Fastest)**
- Pros: Integrated deployment, free tier available
- Cons: Limited customization

**Option 2: Render / Railway (Flexible)**
- Pros: Full control, PostgreSQL included, background jobs
- Cons: Requires more configuration

**Option 3: Vercel + Supabase (React Apps)**
- Pros: Professional UI possible, separate DB hosting
- Cons: More complex setup

### 11.3 Environment Variables (Must Configure)
```
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...  # or ANTHROPIC_API_KEY
VECTOR_DB_API_KEY=...
VECTOR_DB_URL=...
```

### 11.4 Deployment Checklist

- [ ] Database loaded with all CSV data
- [ ] Vector DB populated with schema embeddings
- [ ] Environment variables configured
- [ ] API endpoints responding
- [ ] Workflow A can be triggered manually
- [ ] Workflow B chat interface functional
- [ ] Public URL accessible without authentication
- [ ] Error handling prevents crashes
- [ ] Logs visible for debugging

**Security Notes:**
- Never commit API keys to repository
- Use environment variables for all secrets
- Sanitize user inputs before SQL generation
- Use parameterized queries

---

## 12. Documentation Structure (Mandatory Deliverables)

### 12.1 README.md (Root)

**Must Include:**
1. **Project Title & Description**
2. **Problem Statement:** Clinical supply chain challenges (2-3 paragraphs)
3. **Solution Overview:** What this system does
4. **Architecture Diagram:** Visual showing agent structure
5. **Technology Stack:** List with versions
6. **Deployed Application URL:** Working link
7. **How to Test:** Step-by-step instructions for evaluators
8. **Documentation Navigation:** Links to detailed docs
9. **Setup Instructions:** For local development (optional)
10. **Demo Video Link:** YouTube/Loom (if created)

### 12.2 docs/01_architecture_design.md (Part 1 - Required)

**Content:**
1. **System Architecture Diagram:**
   - User/Scheduler entry points
   - Router Agent at center
   - All specialized agents
   - Database and Vector DB
   - Data flow arrows with labels

2. **Agent Definitions Table:**
   | Agent Name | Responsibilities | Tables Accessed | Tools Used | Interacts With |
   |------------|-----------------|-----------------|------------|----------------|

3. **Workflow A Flowchart:**
   - Step-by-step autonomous monitoring process
   - Decision points
   - Output generation

4. **Workflow B Flowchart:**
   - User query entry
   - Router decision logic
   - Multi-agent collaboration for complex queries
   - Response synthesis

5. **Design Rationale:**
   - Why this agent structure?
   - Why vector DB for schema management?
   - Why LangGraph?
   - Trade-offs considered

**Diagrams:** Use Mermaid, draw.io, Lucidchart, or similar. Must be clear and readable.

### 12.3 docs/02_technical_implementation.md (Part 2 - Required)

**Section 1: Tool Inventory**

For each tool, document:
```
Tool Name: run_sql_query
Purpose: Execute PostgreSQL queries
Input Parameters:
  - query (string): SQL query to execute
  - timeout (integer): Query timeout in seconds
Output: Dictionary with results or error
Used By: SQL Generation Agent, Inventory Agent, etc.
Error Handling: [Description]
Section 2: System Prompts
Provide complete system prompt for at least:

Router Agent
SQL Generation Agent
Synthesis Agent
One specialized domain agent (Inventory/Regulatory/Logistics)

For each prompt, explain:

Key instructions
How it handles schema complexity
Response format enforcement
Edge case handling

Section 3: SQL Query for Shortfall Prediction (Critical Requirement)
Provide the actual PostgreSQL query that solves Workflow A's shortfall prediction:

Include detailed comments explaining each part
Show table joins
Explain calculation logic
Provide expected output format

Section 4: Vector Database Implementation

What is stored (schema metadata structure)
Embedding strategy
Retrieval query logic
How this solves context window problem

12.4 docs/03_edge_case_handling.md (Part 3 - Required)
For Each Edge Case, Provide:
Structure:

Problem Description: What is the edge case?
Why It Matters: Business impact if not handled
Detection Mechanism: How system identifies this case
Resolution Strategy: Step-by-step handling logic
User Experience: What user sees
Example Scenario: Concrete walkthrough

Minimum Required Edge Cases:

Ambiguous Entity Names
SQL Query Errors with Self-Healing
Missing Data Scenarios
Conflicting Data Across Tables
Context Window Overflow


13. Development Timeline (Suggested)
PhaseDurationKey ActivitiesSetup & Data2 daysEnvironment setup, CSV loading, schema analysis, vector DB setupAgent Development3 daysImplement all 8 agents, test interactions, build tool functionsWorkflow Implementation2 daysBuild Workflow A and B logic, test end-to-endEdge Case Handling1 dayImplement fuzzy matching, self-healing SQL, error handlingUI Development2 daysBuild dashboard and chat interface, connect to backendDocumentation2 daysWrite all 3 required docs, create diagrams, write READMEDeployment & Testing1 dayDeploy, test public URL, create demo videoBuffer1 dayFix issues, polish
Total: ~14 days

14. Success Criteria (How You'll Be Evaluated)
14.1 Schema Understanding (40%)

Did you identify correct tables for each workflow?
Do your SQL queries properly join necessary tables?
Did you document table relationships accurately?
Does your architecture show understanding of data structure?

14.2 Agent Design (30%)

Is separation of concerns clear?
Does each agent have well-defined responsibilities?
Are agent interactions logical and efficient?
Is the routing logic sound?

14.3 Prompt Engineering (30%)

Do prompts handle complex schemas without context overflow?
Do prompts enforce proper response formats?
Do prompts handle edge cases gracefully?
Are prompts detailed enough to guide LLM correctly?

14.4 Deliverable Quality

Working Application: Both workflows demonstrable via public URL
Documentation: All 3 parts complete, clear, with diagrams
Code Quality: Well-organized, readable, documented
Edge Cases: Properly handled and documented


15. Constraints & Clarifications
15.1 Explicitly Out of Scope

User authentication or authorization
Role-based access control
API rate limiting
Background job queues (Redis/Celery)
Performance optimization or caching
Multi-language support
Production security hardening
Comprehensive API documentation

15.2 What Evaluators Care About
✅ Correct table selection and joins
✅ Clear agent separation and responsibilities
✅ Explainable AI reasoning with data citations
✅ Valid SQL query logic
✅ Working deployed application
✅ Complete documentation covering all 3 required parts
15.3 Critical Rules

No Hallucinations: Every answer must be grounded in actual database queries
Always Cite Sources: Table name, column, specific value used
No Assumptions: If data missing or unclear, state it explicitly
Self-Healing: SQL errors must trigger retry logic, not immediate failure
Context Management: Never overload LLM with all 40 table schemas at once


16. Final Checklist Before Submission
Documentation

 README.md with deployed URL and testing instructions
 docs/01_architecture_design.md with diagrams
 docs/02_technical_implementation.md with SQL query
 docs/03_edge_case_handling.md with scenarios
 All diagrams clear and properly formatted
 No broken links in documentation

Application

 Deployed at public URL (accessible without login)
 Monitoring dashboard displays sample Workflow A results
 Chat interface accepts queries and returns explained answers
 Both workflows functional and demonstrable
 No crashes or unhandled errors
 Mobile-responsive interface

Technical Implementation

 All CSV data loaded into PostgreSQL
 Vector DB populated with schema embeddings
 All 8 required agents implemented
 Multi-agent collaboration working
 SQL self-healing logic implemented
 Edge case handling demonstrated
 Data citations present in responses

Quality

 Code well-organized and commented
 No hardcoded credentials
 Environment variables documented
 Error messages user-friendly
 Performance acceptable (< 10 seconds for typical queries)