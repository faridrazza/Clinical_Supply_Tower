# Part 1: Architecture Design

## System Architecture Overview

The Clinical Supply Chain Control Tower implements a custom multi-agent architecture with a Python-based orchestrator. The system is designed with clear separation of concerns, where each agent has specific responsibilities and interacts with others through well-defined interfaces. LangChain-OpenAI is used for LLM integration (ChatOpenAI).



---

### High-Level Architecture Diagram

```mermaid
graph TB
    subgraph "Entry Points"
        User[User Interface<br/>Streamlit]
        Scheduler[Scheduled Trigger<br/>Daily Cron]
    end
    
    subgraph "Orchestration Layer"
        Router[Router Agent<br/>Workflow Classifier]
    end
    
    subgraph "Context Management"
        SchemaRetrieval[Schema Retrieval Agent<br/>Context Window Manager]
        VectorDB[(Vector DB<br/>ChromaDB<br/>Schema Metadata)]
    end
    
    subgraph "Domain Agents"
        Inventory[Inventory Agent<br/>Stock & Expiry]
        Demand[Demand Forecasting Agent<br/>Enrollment Analysis]
        Regulatory[Regulatory Agent<br/>Compliance Verification]
        Logistics[Logistics Agent<br/>Shipping Feasibility]
    end
    
    subgraph "Data Layer"
        SQL[SQL Generation Agent<br/>Query Construction]
        PostgreSQL[(PostgreSQL<br/>Clinical Data<br/>40+ Tables)]
    end
    
    subgraph "Output Layer"
        Synthesis[Synthesis Agent<br/>Response Aggregation]
    end
    
    User --> Router
    Scheduler --> Router
    
    Router --> SchemaRetrieval
    Router --> Inventory
    Router --> Demand
    Router --> Regulatory
    Router --> Logistics
    
    SchemaRetrieval <--> VectorDB
    
    Inventory --> SQL
    Demand --> SQL
    Regulatory --> SQL
    Logistics --> SQL
    
    SQL <--> PostgreSQL
    
    Inventory --> Synthesis
    Demand --> Synthesis
    Regulatory --> Synthesis
    Logistics --> Synthesis
    SQL --> Synthesis
    
    Synthesis --> User
    Synthesis --> Scheduler
    
    style Router fill:#e1f5ff
    style SchemaRetrieval fill:#fff4e1
    style Synthesis fill:#e8f5e9
    style SQL fill:#fce4ec
```

## Agent Definitions

| Agent Name | Responsibilities | Tables Accessed | Tools Used | Interacts With |
|------------|-----------------|-----------------|------------|----------------|
| **Router Agent** | - Classify requests as Workflow A or B<br/>- Route to appropriate agents<br/>- Handle ambiguous requests | None (no direct DB access) | - Intent classification<br/>- Keyword matching | - All domain agents<br/>- Schema Retrieval Agent |
| **Schema Retrieval Agent** | - Query vector DB for relevant schemas<br/>- Return max 5 tables per request<br/>- Manage context window | None (queries vector DB only) | - Vector similarity search<br/>- Schema formatting | - Vector DB<br/>- All domain agents |
| **Inventory Agent** | - Check stock levels<br/>- Identify expiring ALLOCATED batches (per assignment)<br/>- Calculate available vs allocated | - **allocated_materials_to_orders** (PRIMARY for expiry alerts)<br/>- **batch_master** (for expiry dates via JOIN)<br/>- available_inventory_report<br/>- affiliate_warehouse_inventory | - SQL Generation Agent<br/>- Schema Retrieval Agent | - SQL Agent<br/>- Synthesis Agent<br/>- Demand Agent |
| **Demand Forecasting Agent** | - Calculate enrollment rates<br/>- Project future demand<br/>- Predict stockout dates | - enrollment_rate_report<br/>- country_level_enrollment_report<br/>- study_level_enrollment_report | - SQL Generation Agent<br/>- Statistical calculations | - SQL Agent<br/>- Synthesis Agent<br/>- Inventory Agent |
| **Regulatory Agent** | - Check extension approvals<br/>- Verify re-evaluation history<br/>- Validate compliance | - rim<br/>- material_country_requirements<br/>- re-evaluation<br/>- qdocs | - SQL Generation Agent<br/>- Schema Retrieval Agent | - SQL Agent<br/>- Synthesis Agent |
| **Logistics Agent** | - Calculate shipping times<br/>- Assess redistribution feasibility<br/>- Account for buffers | - ip_shipping_timelines_report<br/>- distribution_order_report<br/>- shipment_status_report | - SQL Generation Agent<br/>- Date calculations | - SQL Agent<br/>- Synthesis Agent<br/>- Inventory Agent |
| **SQL Generation Agent** | - Convert intent to PostgreSQL<br/>- Implement self-healing (3 retries)<br/>- Parse error messages | All tables (as needed) | - Query generation<br/>- Syntax validation<br/>- Error analysis | - PostgreSQL<br/>- All domain agents<br/>- Schema Retrieval Agent |
| **Synthesis Agent** | - Aggregate multi-agent outputs<br/>- Format JSON (Workflow A)<br/>- Format natural language (Workflow B) | None (aggregates only) | - JSON formatting<br/>- Citation management<br/>- Response structuring | - All domain agents<br/>- User interface |

## Workflow A: Supply Watchdog (Autonomous Monitoring)

### Flowchart

```mermaid
flowchart TD
    Start([Scheduled Trigger<br/>Daily 8 AM - Configurable]) --> Router{Router Agent<br/>Classify Request}
    
    Router -->|Workflow A| Schema[Schema Retrieval Agent<br/>Get relevant tables]
    
    Schema --> Parallel{Parallel Execution}
    
    Parallel --> Expiry[Inventory Agent<br/>Find Expiring ALLOCATED Batches]
    Parallel --> Shortfall[Demand Forecasting Agent<br/>Calculate Shortfalls]
    
    Expiry --> SQL1[SQL Generation Agent<br/>Query allocated_materials + batch_master]
    SQL1 --> DB1[(PostgreSQL)]
    DB1 --> ExpiryData[Expiry Data<br/>≤90 days]
    
    Shortfall --> SQL2[SQL Generation Agent<br/>Query enrollment + inventory]
    SQL2 --> DB2[(PostgreSQL)]
    DB2 --> ShortfallData[Shortfall Predictions<br/>8-week forecast]
    
    ExpiryData --> Classify[Classify Severity<br/>Critical/High/Medium]
    
    Classify --> Synthesis[Synthesis Agent<br/>Generate JSON]
    ShortfallData --> Synthesis
    
    Synthesis --> JSON{JSON Output}
    
    JSON --> Email[Email Alert System<br/>via Resend API]
    JSON --> Dashboard[Monitoring Dashboard]
    
    Email --> End([End])
    Dashboard --> End
```

### Execution Steps

1. **Trigger**: Scheduled cron job (daily at 8 AM, configurable) or manual trigger via UI
2. **Router Classification**: Identifies as Workflow A
3. **Schema Retrieval**: Gets schemas for:
   - **allocated_materials_to_orders** (reserved batches - per assignment requirement)
   - **batch_master** (expiry dates via JOIN)
   - enrollment_rate_report
   - available_inventory_report (for shortfall calculation)
4. **Parallel Agent Execution**:
   - **Inventory Agent**: Queries expiring ALLOCATED batches (JOIN with batch_master for expiry dates)
   - **Demand Forecasting Agent**: Calculates shortfalls
5. **SQL Generation**: Converts intents to PostgreSQL queries
6. **Data Processing**:
   - Classify expiry severity (Critical <30, High 30-60, Medium 60-90 days)
   - Calculate 8-week demand projections
   - Identify shortfalls
7. **Synthesis**: Aggregates results into structured JSON
8. **Output**: JSON payload sent via email (Resend API) and displayed on dashboard

## Workflow B: Scenario Strategist (Conversational Assistant)

### Flowchart

```mermaid
flowchart TD
    Start([User Query]) --> Router{Router Agent<br/>Classify Intent}
    
    Router -->|Simple Query| Simple[Single Agent Path]
    Router -->|Complex Query| Complex[Multi-Agent Path]
    
    Simple --> Schema1[Schema Retrieval<br/>Get 2-3 tables]
    Schema1 --> Agent1[Domain Agent<br/>e.g., Inventory]
    Agent1 --> SQL1[SQL Generation]
    SQL1 --> DB1[(PostgreSQL)]
    DB1 --> Synth1[Synthesis Agent]
    Synth1 --> Response1[Natural Language<br/>Response]
    
    Complex --> Schema2[Schema Retrieval<br/>Get 4-5 tables]
    Schema2 --> Parallel{Parallel Agent<br/>Execution}
    
    Parallel --> Inv[Inventory Agent<br/>Check batch/expiry]
    Parallel --> Reg[Regulatory Agent<br/>Check approvals]
    Parallel --> Log[Logistics Agent<br/>Check shipping]
    
    Inv --> SQL2[SQL Generation]
    Reg --> SQL3[SQL Generation]
    Log --> SQL4[SQL Generation]
    
    SQL2 --> DB2[(PostgreSQL)]
    SQL3 --> DB3[(PostgreSQL)]
    SQL4 --> DB4[(PostgreSQL)]
    
    DB2 --> Check1[Technical Check<br/>✓ PASS / ✗ FAIL]
    DB3 --> Check2[Regulatory Check<br/>✓ PASS / ✗ FAIL]
    DB4 --> Check3[Logistical Check<br/>✓ PASS / ⚠ CONDITIONAL]
    
    Check1 --> Synth2[Synthesis Agent<br/>Aggregate + Cite]
    Check2 --> Synth2
    Check3 --> Synth2
    
    Synth2 --> Decision{Generate<br/>Recommendation}
    
    Decision --> Response2[Structured Response<br/>YES/NO/CONDITIONAL<br/>with Citations]
    
    Response1 --> End([User Interface])
    Response2 --> End
```

### Example: Shelf-Life Extension Query

**User Query**: "Can we extend the expiry of Batch LOT-14364098 for Germany?"

**Execution Flow**:

1. **Router**: Classifies as Workflow B, complex decision query
2. **Schema Retrieval**: Retrieves schemas for:
   - allocated_materials_to_orders (batch info)
   - re-evaluation (extension history)
   - rim (regulatory approvals)
   - ip_shipping_timelines_report (logistics)
3. **Parallel Agent Execution**:
   - **Inventory Agent**: 
     - Queries batch existence and expiry date
     - Returns: "LOT-14364098 expires 2028-06-06"
   - **Regulatory Agent**:
     - Checks re-evaluation table for previous extensions
     - Checks rim table for Germany approval
     - Returns: "Extended 1 time, approved in Germany"
   - **Logistics Agent**:
     - Calculates days until expiry
     - Checks shipping time to Germany
     - Returns: "Available window: 1200+ days"
4. **Synthesis Agent**:
   - Aggregates all checks
   - Formats structured response with citations
   - Generates recommendation: "YES"

## Design Rationale

### Why Multi-Agent Architecture?

1. **Separation of Concerns**: Each agent has a single, well-defined responsibility
2. **Scalability**: New agents can be added without modifying existing ones
3. **Maintainability**: Bugs and updates are isolated to specific agents
4. **Parallel Execution**: Independent agents can run concurrently
5. **Testability**: Each agent can be tested in isolation

### Why Vector Database for Schema Management?

**Problem**: 40+ tables cannot fit in LLM context window simultaneously

**Solution**: Vector DB stores schema metadata, retrieves only relevant tables

**Benefits**:
- **Context Window Efficiency**: Only 2-5 relevant tables loaded per query
- **Semantic Search**: Finds tables based on intent, not just keywords
- **Scalability**: Can handle hundreds of tables without context overflow
- **Fast Retrieval**: Sub-second schema lookups

**What's Stored**:
- Table descriptions (business purpose)
- Column metadata (name, type, description, examples)
- Relationship patterns (common JOINs)
- Query templates (example SQL patterns)

**What's NOT Stored**:
- Actual business data (only metadata)
- Query results
- User data

### Why Custom Orchestration?

1. **Simplicity**: Plain Python classes are easier to understand and debug
2. **Flexibility**: Full control over agent interactions without framework constraints
3. **Lightweight**: No additional framework overhead
4. **LLM Integration**: LangChain-OpenAI provides robust ChatOpenAI wrapper for LLM calls
5. **Maintainability**: Standard Python patterns familiar to all developers

### Trade-offs Considered

| Decision | Alternative | Why Chosen |
|----------|-------------|------------|
| **Multi-Agent** | Single monolithic agent | Better separation of concerns, easier maintenance |
| **Vector DB** | Load all schemas in prompt | Prevents context window overflow, faster retrieval |
| **PostgreSQL** | NoSQL database | Structured data with complex joins, ACID compliance |
| **Custom Orchestration** | LangGraph | Simpler, no framework overhead, full control |
| **Streamlit** | React/Vue.js | Faster development, Python-native, easy deployment |
| **ChromaDB** | Pinecone/Weaviate | Open-source, local deployment, no API costs |

## Agent Interaction Patterns

### Pattern 1: Simple Query (Single Agent)
```
User → Router → Schema Retrieval → Inventory Agent → SQL Agent → PostgreSQL → Synthesis → User
```
**Example**: "What is stock level for MAT-93657?"

### Pattern 2: Complex Decision (Multi-Agent)
```
User → Router → Schema Retrieval → [Inventory + Regulatory + Logistics] → SQL Agent → PostgreSQL → Synthesis → User
```
**Example**: "Can we extend Batch #123 for Germany?"

### Pattern 3: Autonomous Monitoring (Scheduled)
```
Scheduler → Router → [Inventory + Demand] → SQL Agent → PostgreSQL → Synthesis → JSON Output
```
**Example**: Daily supply watchdog execution

## Scalability Considerations

### Current Design Supports:
- 40+ tables (tested with synthetic data)
- Concurrent user queries (Streamlit handles multiple sessions)
- Daily scheduled workflows
- Sub-10-second response times for typical queries

### Future Enhancements:
- **Caching Layer**: Redis for frequently accessed data
- **Background Jobs**: Celery for long-running workflows
- **Load Balancing**: Multiple agent instances
- **Monitoring**: Prometheus + Grafana for observability
- **API Gateway**: RESTful API for external integrations

## Security Considerations

### Current Implementation:
- Parameterized SQL queries (prevents SQL injection)
- Environment variables for secrets
- No authentication (as per assignment requirements)



## LLM Usage Strategy

### Where LLM is Used

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LLM USAGE IN THE SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │ Schema Retrieval│    │ SQL Generation  │    │   Synthesis     │     │
│  │     Agent       │    │     Agent       │    │     Agent       │     │
│  ├─────────────────┤    ├─────────────────┤    ├─────────────────┤     │
│  │ OpenAI          │    │ GPT-4-turbo     │    │ GPT-4-turbo     │     │
│  │ text-embedding- │    │                 │    │                 │     │
│  │ 3-small         │    │ Generates SQL   │    │ Reasons over    │     │
│  │                 │    │ from natural    │    │ data & formats  │     │
│  │ Semantic search │    │ language intent │    │ responses       │     │
│  │ for tables      │    │                 │    │                 │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
│                                                                         │
│  WHY THESE 3?                                                           │
│  • Schema Retrieval: Semantic understanding of user intent              │
│  • SQL Generation: Complex query construction from natural language     │
│  • Synthesis: Natural language reasoning and response formatting        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Where LLM is NOT Used (Rule-Based)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RULE-BASED AGENTS (NO LLM)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │    Router    │  │  Inventory   │  │   Demand     │  │  Regulatory  ││
│  │    Agent     │  │    Agent     │  │  Forecasting │  │    Agent     ││
│  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤│
│  │ Keyword      │  │ SQL queries  │  │ Statistical  │  │ SQL queries  ││
│  │ matching &   │  │ for stock &  │  │ calculations │  │ for RIM &    ││
│  │ regex for    │  │ expiry data  │  │ for demand   │  │ re-evaluation││
│  │ routing      │  │              │  │ projection   │  │              ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
│                                                                         │
│  ┌──────────────┐                                                       │
│  │  Logistics   │  WHY NO LLM?                                          │
│  │    Agent     │  • Deterministic operations (date math, comparisons)  │
│  ├──────────────┤  • Faster execution (no API calls)                    │
│  │ Date calcs & │  • Lower cost (no token usage)                        │
│  │ shipping     │  • More predictable behavior                          │
│  │ feasibility  │                                                       │
│  └──────────────┘                                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Production Requirements:
- OAuth 2.0 / SAML authentication
- Role-based access control (RBAC)
- Audit logging for all queries
- Data encryption at rest and in transit
- API rate limiting
- Input sanitization and validation

## Conclusion

This architecture provides a robust, scalable foundation for the Clinical Supply Chain Control Tower. The multi-agent design ensures maintainability and extensibility, while the vector database strategy solves the context window problem elegantly. The system is production-ready for the specified workflows and can be extended to support additional use cases with minimal modifications.
