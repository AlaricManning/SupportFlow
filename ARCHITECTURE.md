# SupportFlow Architecture

This document provides an in-depth technical overview of SupportFlow's architecture, design decisions, and implementation details.

## Table of Contents

1. [System Overview](#system-overview)
2. [Multi-Agent System Design](#multi-agent-system-design)
3. [Data Flow](#data-flow)
4. [Database Schema](#database-schema)
5. [LangGraph Workflow](#langgraph-workflow)
6. [Structured Output Strategy](#structured-output-strategy)
7. [RAG Implementation](#rag-implementation)
8. [API Design](#api-design)
9. [Frontend Architecture](#frontend-architecture)
10. [Deployment Architecture](#deployment-architecture)

## System Overview

SupportFlow is built on a **multi-agent architecture** where specialized AI agents collaborate to process customer support tickets. The system emphasizes:

- **Determinism**: Structured outputs via Pydantic models
- **Transparency**: Complete execution traces stored in database
- **Modularity**: Each agent is independent and testable
- **Production-readiness**: Proper error handling, logging, and observability

### Key Design Principles

1. **Structured > Unstructured**: All LLM outputs are parsed into Pydantic models using Instructor
2. **Trace Everything**: Every agent execution is logged with inputs, outputs, reasoning, and performance metrics
3. **Human-in-the-Loop**: Automatic escalation when confidence drops below threshold
4. **Tool-First**: Agents use function calling for deterministic operations (database lookups, calculations)

## Multi-Agent System Design

### Agent Responsibilities

Each agent has a single, well-defined responsibility:

| Agent | Purpose | Key Tools | Output Type |
|-------|---------|-----------|-------------|
| **Triage** | Classify intent & priority | None | `TriageOutput` |
| **Research** | Find relevant KB articles | `search_knowledge_base` | `ResearchOutput` |
| **Policy** | Check eligibility & policies | `get_order_details`, `check_refund_eligibility` | `PolicyCheckOutput` |
| **Response** | Draft customer response | None | `ResponseOutput` |
| **Escalation** | Decide human review need | None | `EscalationDecision` |

### Why This Architecture?

**Alternative Considered**: Single monolithic agent

**Why Multi-Agent Won**:
- ✅ Better separation of concerns
- ✅ Easier to test and debug individual agents
- ✅ Can optimize each agent independently (different models, prompts)
- ✅ More transparent - see exactly where decisions are made
- ✅ Easier to add/remove agents without affecting others

## Data Flow

### End-to-End Ticket Processing

```
1. User submits ticket via frontend
   ↓
2. FastAPI creates Ticket record in database (status: IN_PROGRESS)
   ↓
3. Initial state constructed with ticket data
   ↓
4. LangGraph workflow invoked
   ↓
   ┌─────────────────────────────────────────┐
   │  Agent Workflow (Sequential Pipeline)   │
   │                                          │
   │  State → Triage → Research → Policy →   │
   │          Response → Escalation → Output  │
   └─────────────────────────────────────────┘
   ↓
5. Each agent:
   - Receives current state
   - Calls LLM with structured output
   - (Optionally) calls tools
   - Updates state with results
   - Logs trace to database
   ↓
6. Final state returned with:
   - AI-generated response
   - Escalation decision
   - Overall confidence
   ↓
7. Ticket updated in database:
   - Status: RESOLVED or WAITING_HUMAN
   - AI response saved
   - Agent traces stored
   ↓
8. Response returned to frontend
```

### State Management

The state is a TypedDict passed between agents:

```python
class SupportAgentState(TypedDict):
    # Input
    ticket_id: int
    customer_email: str
    customer_name: str
    subject: str
    message: str
    order_id: str | None

    # Agent outputs (Pydantic models serialized to dict)
    triage: dict | None
    research: dict | None
    policy_check: dict | None
    response: dict | None
    escalation: dict | None

    # Final outputs
    final_response: str | None
    requires_human: bool
    overall_confidence: float

    # Internal (traces for logging)
    _traces: list[dict]
```

## Database Schema

### Tables

#### tickets
Primary table for support tickets.

```sql
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,

    -- Triage results
    status VARCHAR(50) NOT NULL,  -- TicketStatus enum
    priority VARCHAR(50),          -- TicketPriority enum
    intent VARCHAR(255),
    confidence FLOAT,

    -- Response
    ai_response TEXT,
    final_response TEXT,
    response_approved INTEGER DEFAULT 0,

    -- Metadata
    order_id VARCHAR(100),
    metadata JSON,

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME
);
```

#### agent_traces
Complete execution traces for observability.

```sql
CREATE TABLE agent_traces (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL,

    -- Agent info
    agent_name VARCHAR(100) NOT NULL,
    step_number INTEGER NOT NULL,

    -- Execution details
    input_data JSON,
    output_data JSON,
    reasoning TEXT,
    confidence FLOAT,

    -- Tool usage
    tools_used JSON,
    tool_results JSON,

    -- Performance
    execution_time_ms INTEGER NOT NULL,
    tokens_used INTEGER,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);
```

#### ticket_messages
Conversation history (for future multi-turn support).

```sql
CREATE TABLE ticket_messages (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL,
    role VARCHAR(50) NOT NULL,  -- customer, agent, system
    content TEXT NOT NULL,
    sender_name VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);
```

## LangGraph Workflow

### Workflow Definition

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(SupportAgentState)

# Add nodes (agents)
workflow.add_node("triage", triage_agent)
workflow.add_node("research", research_agent)
workflow.add_node("policy", policy_agent)
workflow.add_node("response", response_agent)
workflow.add_node("escalation", escalation_agent)

# Define edges (sequential pipeline)
workflow.set_entry_point("triage")
workflow.add_edge("triage", "research")
workflow.add_edge("research", "policy")
workflow.add_edge("policy", "response")
workflow.add_edge("response", "escalation")
workflow.add_edge("escalation", END)

# Compile
app = workflow.compile()
```

### Why LangGraph?

**Alternatives Considered**:
- Simple function chaining
- LangChain LCEL
- Custom orchestrator

**Why LangGraph**:
- ✅ Built-in state management
- ✅ Support for conditional edges (future enhancement)
- ✅ Checkpointing for long-running workflows
- ✅ Easy visualization of workflow
- ✅ Designed specifically for agent systems

### Future: Conditional Routing

Currently linear, but can be enhanced:

```python
def should_skip_policy(state):
    """Skip policy check if no order ID provided."""
    return state.get("order_id") is None

workflow.add_conditional_edges(
    "research",
    should_skip_policy,
    {
        True: "response",      # Skip policy
        False: "policy"        # Run policy check
    }
)
```

## Structured Output Strategy

### The Problem

LLMs naturally output unstructured text. Parsing this is brittle:

```python
# ❌ Bad: Fragile regex parsing
response = llm.invoke("Classify this ticket...")
match = re.search(r"Intent: (\w+)", response)
intent = match.group(1)  # Breaks if format changes
```

### The Solution: Instructor + Pydantic

```python
import instructor
from openai import OpenAI

# Patch OpenAI client
client = instructor.from_openai(OpenAI())

# Define output schema
class TriageOutput(BaseModel):
    intent: str = Field(..., description="Intent classification")
    priority: TicketPriority
    confidence: float = Field(..., ge=0, le=1)

# Get structured output
response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    response_model=TriageOutput,  # ✅ Guaranteed structure
    messages=[{"role": "user", "content": prompt}]
)

# response is a TriageOutput instance, not a string!
print(response.intent)      # Type-safe
print(response.confidence)  # Validated (0-1)
```

### Benefits

1. **Type Safety**: Full IDE autocomplete and type checking
2. **Validation**: Pydantic ensures data integrity
3. **Reliability**: No regex parsing that breaks on formatting changes
4. **Testability**: Easy to mock Pydantic models in tests
5. **Documentation**: Schemas serve as API documentation

## RAG Implementation

### Knowledge Base Structure

```
knowledge_base/
├── refund_policy.md
├── shipping_policy.md
├── product_warranty.md
└── account_help.md
```

### Vector Store: ChromaDB

**Why ChromaDB?**
- ✅ Embedded database (no separate server needed)
- ✅ Persistent storage
- ✅ Fast similarity search
- ✅ Easy to use with LangChain

### Indexing Process

```python
from chromadb import Client
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1. Load markdown files
documents = load_markdown_files("knowledge_base/")

# 2. Split into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = text_splitter.split_documents(documents)

# 3. Generate embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# 4. Store in ChromaDB
collection.add(
    documents=[chunk.text for chunk in chunks],
    embeddings=[embeddings.embed_query(chunk.text) for chunk in chunks],
    metadatas=[{"source": chunk.metadata["source"]} for chunk in chunks],
    ids=[f"doc_{i}" for i in range(len(chunks))]
)
```

### Search Process

```python
def search_knowledge_base(query: str, n_results: int = 3):
    # 1. Embed query
    query_embedding = embeddings.embed_query(query)

    # 2. Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    # 3. Return relevant chunks with metadata
    return [
        {
            "content": doc,
            "source": metadata["source"],
            "relevance_score": 1 - distance
        }
        for doc, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )
    ]
```

## API Design

### RESTful Principles

| Method | Endpoint | Purpose | Returns |
|--------|----------|---------|---------|
| POST | `/api/tickets` | Create ticket | `TicketResponse` |
| GET | `/api/tickets` | List tickets | `List[TicketResponse]` |
| GET | `/api/tickets/{id}` | Get ticket with traces | `TicketWithTraces` |
| PATCH | `/api/tickets/{id}` | Update ticket | `TicketResponse` |
| DELETE | `/api/tickets/{id}` | Delete ticket | 204 No Content |
| GET | `/api/stats` | System statistics | `StatsResponse` |

### Response Models

All responses use Pydantic schemas:

```python
class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    customer_email: str
    customer_name: str
    subject: str
    message: str
    status: TicketStatus
    priority: TicketPriority
    intent: Optional[str]
    confidence: Optional[float]
    ai_response: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True  # Allow ORM models
```

### Error Handling

```python
@router.post("/tickets")
async def create_ticket(ticket_data: TicketCreate, db: Session):
    try:
        # Create ticket
        ticket = Ticket(**ticket_data.model_dump())
        db.add(ticket)
        db.commit()

        # Run agent workflow
        result = support_workflow.invoke(initial_state)

        # Update with results
        ticket.ai_response = result["final_response"]
        db.commit()

        return ticket

    except Exception as e:
        # Mark for human review on failure
        ticket.status = TicketStatus.WAITING_HUMAN
        ticket.metadata = {"error": str(e)}
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Agent workflow failed: {str(e)}"
        )
```

## Frontend Architecture

### Component Structure

```
src/
├── components/         # Reusable components (future)
├── pages/
│   ├── HomePage.jsx           # Ticket submission
│   ├── AdminPage.jsx          # Dashboard with table
│   └── TicketDetailPage.jsx  # Detail with traces
├── services/
│   └── api.js                 # Axios API client
└── App.jsx                    # Routing
```

### State Management

Currently using **React Hooks** (useState, useEffect):

```jsx
function AdminPage() {
    const [tickets, setTickets] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadTickets();
    }, []);

    const loadTickets = async () => {
        const data = await ticketService.getTickets();
        setTickets(data);
        setLoading(false);
    };

    // Render...
}
```

**Future Enhancement**: Use React Context or Zustand for global state.

### Routing

```jsx
<Routes>
    <Route path="/" element={<HomePage />} />
    <Route path="/admin" element={<AdminPage />} />
    <Route path="/ticket/:ticketId" element={<TicketDetailPage />} />
</Routes>
```

## Deployment Architecture

### Production Stack

```
┌─────────────────────────────────────────┐
│         Nginx (Reverse Proxy)            │
│  - Serves static frontend               │
│  - Proxies /api to backend              │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼──────┐   ┌──────▼─────┐
│ Frontend │   │  Backend   │
│  (React) │   │  (FastAPI) │
│  Static  │   │   Python   │
└──────────┘   └──────┬─────┘
                      │
          ┌───────────┴──────────┐
          │                      │
    ┌─────▼──────┐    ┌─────────▼────────┐
    │ PostgreSQL │    │    ChromaDB      │
    │  (Tickets) │    │ (Vector Store)   │
    └────────────┘    └──────────────────┘
```

### Docker Compose

Three services:
1. **db**: PostgreSQL 15
2. **backend**: Python + FastAPI
3. **frontend**: Nginx serving React build

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | Database connection | `postgresql://user:pass@db/supportflow` |
| `OPENAI_API_KEY` | OpenAI API access | `sk-...` |
| `SECRET_KEY` | Session encryption | `random-secret-key` |
| `CONFIDENCE_THRESHOLD` | Escalation threshold | `0.7` |

### Scaling Considerations

**Current**: Single container deployment

**Future Improvements**:
1. **Horizontal Scaling**: Run multiple backend containers behind load balancer
2. **Async Processing**: Move agent workflow to background queue (Celery, RQ)
3. **Caching**: Add Redis for API response caching
4. **CDN**: Serve frontend assets via CDN (CloudFront, Cloudflare)

## Performance Optimization

### Current Performance

- **Ticket Processing**: ~5s end-to-end
- **Database Queries**: <10ms (indexed properly)
- **Vector Search**: ~200ms (3 results)
- **LLM Calls**: ~1-2s per agent (5 agents = ~5-10s total)

### Optimization Opportunities

1. **Parallel Agent Execution** (where possible):
   ```python
   # Research and Policy could run in parallel
   results = await asyncio.gather(
       research_agent(state),
       policy_agent(state)
   )
   ```

2. **LLM Call Batching**: Use GPT-4 batch API for non-urgent tickets

3. **Caching**: Cache KB search results for common queries

4. **Faster Embeddings**: Use OpenAI embeddings instead of local model

5. **Streaming**: Stream response as agents complete (WebSocket)

## Security Considerations

### Current Implementation

✅ **Input Validation**: Pydantic models validate all inputs
✅ **SQL Injection**: SQLAlchemy ORM prevents SQL injection
✅ **CORS**: Configured for specific origins only

### Future Improvements

⚠️ **Authentication**: Add JWT-based auth for admin routes
⚠️ **Rate Limiting**: Prevent API abuse
⚠️ **Secrets Management**: Use environment variables, not hardcoded
⚠️ **HTTPS**: Enforce TLS in production
⚠️ **Input Sanitization**: Additional validation for user messages

## Testing Strategy

### Unit Tests

```python
# Test individual agents
def test_triage_agent():
    state = {
        "subject": "Request refund",
        "message": "Product is defective",
        # ... other fields
    }

    result = triage_agent(state)

    assert result["triage"]["intent"] == "refund_request"
    assert result["triage"]["priority"] in ["high", "urgent"]
    assert 0 <= result["triage"]["confidence"] <= 1
```

### Integration Tests

```python
# Test full workflow
async def test_ticket_workflow():
    ticket_data = TicketCreate(
        customer_name="Test User",
        customer_email="test@example.com",
        subject="Test",
        message="Test message"
    )

    response = await client.post("/api/tickets", json=ticket_data.dict())

    assert response.status_code == 201
    assert "ticket_number" in response.json()
```

## Monitoring and Observability

### Metrics to Track

1. **Agent Performance**:
   - Execution time per agent
   - Token usage
   - Confidence scores

2. **System Health**:
   - Tickets processed per hour
   - Average processing time
   - Escalation rate

3. **Business Metrics**:
   - Intent distribution
   - Resolution rate
   - Customer satisfaction (future)

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Processing ticket {ticket_id}")
logger.debug(f"Agent state: {state}")
logger.error(f"Agent failed: {error}")
```

### Future: APM Integration

- **Sentry**: Error tracking
- **DataDog**: Performance monitoring
- **Prometheus + Grafana**: Metrics dashboard

---

## Conclusion

SupportFlow demonstrates production-ready AI engineering through:

1. **Structured Design**: Multi-agent architecture with clear responsibilities
2. **Type Safety**: Pydantic models throughout the stack
3. **Transparency**: Complete trace logging for debugging
4. **Scalability**: Designed for horizontal scaling
5. **Best Practices**: Proper error handling, validation, and testing

This architecture can scale from a portfolio project to a production SaaS with minimal changes.
