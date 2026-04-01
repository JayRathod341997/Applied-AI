# Agentic Customer Support Resolution Engine

## Overview

A stateful multi-agent system using LangGraph to classify customer issues, retrieve relevant knowledge, reason through resolution paths, and generate personalized responses. The system adapts dynamically based on conversation state and feedback loops, with human escalation as a fallback.

---

## Architecture Diagram

```
Customer Message
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LangGraph State Machine                      │
│                                                                  │
│   ┌──────────┐    ┌───────────────┐    ┌────────────────────┐  │
│   │Classifier│───▶│   Knowledge   │───▶│ Resolution Reasoner│  │
│   │  Node    │    │ Retrieval Node│    │      Node          │  │
│   └──────────┘    └───────────────┘    └──────────┬─────────┘  │
│        │                                           │            │
│   [Issue Type]                           [Resolved / Escalate] │
│        │                                           │            │
│   ┌────▼──────┐                         ┌──────────▼─────────┐ │
│   │  Routing  │                         │  Response Generator│ │
│   │   Node    │                         │       Node         │ │
│   └────┬──────┘                         └──────────┬─────────┘ │
│        │                                           │            │
│   [billing/                              ┌─────────▼──────────┐│
│    technical/                            │  Feedback Evaluator││
│    general]                              │       Node         ││
│                                          └─────────┬──────────┘│
│                                                     │           │
│                                        [Helpful / Not Helpful]  │
│                                                     │           │
│                                          ┌──────────▼──────────┐│
│                                          │ Re-route or Complete ││
│                                          └─────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
         │
   ┌─────┴──────────┐
   │  Azure Services │
   │                 │
   │ - Azure AI      │
   │   (GPT-4o)      │
   │ - Azure AI      │
   │   Search (KB)   │
   │ - Azure         │
   │   CosmosDB      │
   │   (conv state)  │
   └─────────────────┘
```

### Graph Node Descriptions

| Node | Input | Output | Condition |
|---|---|---|---|
| **Classifier** | Raw message | Issue type + severity | Always runs first |
| **Router** | Issue type | Next node path | Branches on issue type |
| **Knowledge Retrieval** | Issue type + query | Relevant KB chunks | Runs before reasoning |
| **Resolution Reasoner** | KB chunks + history | Resolution steps | Core reasoning |
| **Response Generator** | Resolution steps | Customer-facing message | Final synthesis |
| **Feedback Evaluator** | Customer reply | Helpful / Not helpful | Conditional loop |
| **Escalation** | Full state | Ticket for human agent | Triggered if unresolved |

---

## Project Structure

```
customer_support_engine/
├── .env.example
├── pyproject.toml
├── README.md
├── INTERVIEW.md
│
├── infra/
│   ├── main.bicep
│   ├── container_app.bicep
│   ├── cosmos_db.bicep
│   └── ai_search.bicep
│
├── src/
│   └── support/
│       ├── __init__.py
│       ├── main.py               # FastAPI app + WebSocket for streaming
│       ├── config.py
│       │
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── state.py          # LangGraph TypedDict state schema
│       │   ├── nodes.py          # All graph node functions
│       │   ├── edges.py          # Conditional edge logic
│       │   └── builder.py        # Graph assembly + compilation
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── kb_search.py      # Azure AI Search KB retrieval
│       │   └── ticket_tool.py    # Escalation ticket creation
│       │
│       ├── memory/
│       │   ├── __init__.py
│       │   └── cosmos_checkpointer.py  # LangGraph checkpointer (Cosmos)
│       │
│       └── utils/
│           ├── __init__.py
│           └── logger.py
│
└── tests/
    ├── test_graph.py
    ├── test_nodes.py
    └── test_edges.py
```

---

## Core Code: LangGraph State + Graph

```python
# src/support/graph/state.py
from typing import Annotated, TypedDict, Literal
from langgraph.graph.message import add_messages

class SupportState(TypedDict):
    messages: Annotated[list, add_messages]
    issue_type: str                          # billing | technical | general
    severity: Literal["low", "medium", "high"]
    kb_chunks: list[str]                     # Retrieved knowledge base chunks
    resolution_steps: list[str]              # Reasoned resolution path
    resolution_status: Literal["resolved", "escalated", "pending"]
    feedback_signal: Literal["helpful", "not_helpful", "no_feedback"]
    retry_count: int                         # Prevents infinite feedback loops
    conversation_id: str
```

```python
# src/support/graph/builder.py
from langgraph.graph import StateGraph, END
from support.graph.state import SupportState
from support.graph.nodes import (
    classify_issue, route_issue, retrieve_knowledge,
    reason_resolution, generate_response,
    evaluate_feedback, escalate_to_human
)
from support.graph.edges import should_escalate, should_retry

def build_support_graph():
    builder = StateGraph(SupportState)

    # Add nodes
    builder.add_node("classifier", classify_issue)
    builder.add_node("retrieval", retrieve_knowledge)
    builder.add_node("reasoner", reason_resolution)
    builder.add_node("responder", generate_response)
    builder.add_node("feedback_eval", evaluate_feedback)
    builder.add_node("escalation", escalate_to_human)

    # Entry point
    builder.set_entry_point("classifier")

    # Edges
    builder.add_edge("classifier", "retrieval")
    builder.add_edge("retrieval", "reasoner")
    builder.add_edge("reasoner", "responder")
    builder.add_edge("responder", "feedback_eval")

    # Conditional: retry, escalate, or finish
    builder.add_conditional_edges(
        "feedback_eval",
        should_retry,
        {
            "retry": "retrieval",        # Re-retrieve with refined query
            "escalate": "escalation",    # Hand off to human
            "done": END,
        }
    )
    builder.add_edge("escalation", END)

    return builder.compile()
```

---

## Setup Instructions

### 1. Environment Setup

```bash
git clone <repo-url>
cd customer_support_engine
uv venv
uv sync
cp .env.example .env
```

### 2. Azure Resource Setup

> **Prerequisites:** [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed and logged in (`az login`).

#### 2a. Create Resource Group

```bash
az group create \
  --name rg-support-engine \
  --location eastus
```

#### 2b. Azure OpenAI Service

```bash
# Create the Azure OpenAI resource
az cognitiveservices account create \
  --name support-engine-openai \
  --resource-group rg-support-engine \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Deploy GPT-4o for chat
az cognitiveservices account deployment create \
  --name support-engine-openai \
  --resource-group rg-support-engine \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-05-13" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard

# Deploy text-embedding-ada-002 for vector search
az cognitiveservices account deployment create \
  --name support-engine-openai \
  --resource-group rg-support-engine \
  --deployment-name text-embedding-ada-002 \
  --model-name text-embedding-ada-002 \
  --model-version "2" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard

# Retrieve endpoint & key → paste into .env
az cognitiveservices account show \
  --name support-engine-openai \
  --resource-group rg-support-engine \
  --query properties.endpoint

az cognitiveservices account keys list \
  --name support-engine-openai \
  --resource-group rg-support-engine
```

#### 2c. Azure AI Search (Knowledge Base)

```bash
# Create the search service (Basic tier supports vector search)
az search service create \
  --name support-engine-search \
  --resource-group rg-support-engine \
  --sku Basic \
  --location eastus

# Retrieve admin key → paste into .env as AZURE_SEARCH_KEY
az search admin-key show \
  --service-name support-engine-search \
  --resource-group rg-support-engine
```

After deployment, create the index and upload your knowledge base documents:

```bash
# (Optional) run the ingestion script to build the KB index
uv run python -m support.tools.kb_search --ingest ./data/knowledge_base.jsonl
```

#### 2d. Azure Cosmos DB (Conversation State)

```bash
# Create Cosmos DB account (NoSQL / Core API)
az cosmosdb create \
  --name support-engine-cosmos \
  --resource-group rg-support-engine \
  --default-consistency-level Session \
  --locations regionName=eastus

# Create the database
az cosmosdb sql database create \
  --account-name support-engine-cosmos \
  --resource-group rg-support-engine \
  --name support_db

# Create the container with partition key /conversation_id
az cosmosdb sql container create \
  --account-name support-engine-cosmos \
  --resource-group rg-support-engine \
  --database-name support_db \
  --name conversations \
  --partition-key-path "/conversation_id" \
  --throughput 400

# Retrieve endpoint & key → paste into .env
az cosmosdb show \
  --name support-engine-cosmos \
  --resource-group rg-support-engine \
  --query documentEndpoint

az cosmosdb keys list \
  --name support-engine-cosmos \
  --resource-group rg-support-engine
```

#### 2e. Application Insights (Observability)

```bash
# Create a Log Analytics workspace
az monitor log-analytics workspace create \
  --workspace-name support-engine-logs \
  --resource-group rg-support-engine

# Create Application Insights linked to the workspace
az monitor app-insights component create \
  --app support-engine-insights \
  --resource-group rg-support-engine \
  --location eastus \
  --workspace support-engine-logs

# Retrieve connection string → paste into .env as APPINSIGHTS_CONNECTION_STRING
az monitor app-insights component show \
  --app support-engine-insights \
  --resource-group rg-support-engine \
  --query connectionString
```

#### 2f. Deploy via Bicep (All-in-One)

Alternatively, deploy all resources in one shot using the included Bicep templates:

```bash
cd infra
az deployment group create \
  --resource-group rg-support-engine \
  --template-file main.bicep \
  --parameters env=development
```

After Bicep deployment, export all secrets with:

```bash
# Azure OpenAI
az cognitiveservices account show --name support-engine-openai -g rg-support-engine --query properties.endpoint -o tsv
az cognitiveservices account keys list --name support-engine-openai -g rg-support-engine --query key1 -o tsv

# AI Search
az search admin-key show --service-name support-engine-search -g rg-support-engine --query primaryKey -o tsv

# Cosmos DB
az cosmosdb show --name support-engine-cosmos -g rg-support-engine --query documentEndpoint -o tsv
az cosmosdb keys list --name support-engine-cosmos -g rg-support-engine --query primaryMasterKey -o tsv

# App Insights
az monitor app-insights component show --app support-engine-insights -g rg-support-engine --query connectionString -o tsv
```

### 3. Run Locally

```bash
uv run uvicorn src.main:app --reload --port 8003
```

### 4. Test the Graph

```bash
uv run pytest tests/ -v
```

### 5. Deploy to Azure Container Apps

```bash
az acr build --registry <your-acr> --image support-engine:latest .
az containerapp update \
  --name support-engine-app \
  --resource-group rg-support-engine \
  --image <your-acr>.azurecr.io/support-engine:latest
```

---

## Observability Setup

Each graph node emits structured logs with:
- `conversation_id` — for end-to-end trace correlation
- `node_name` — which step in the graph
- `latency_ms` — per-node execution time
- `token_usage` — input + output tokens
- `state_snapshot` — key state fields at that node

Logs ship to Azure Monitor via Application Insights SDK. You can query full conversation traces in Log Analytics.

---

## Environment Variables

```env
# .env.example
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

AZURE_SEARCH_ENDPOINT=https://<search>.search.windows.net
AZURE_SEARCH_KEY=<key>
AZURE_SEARCH_INDEX=support-kb-index

AZURE_COSMOS_ENDPOINT=https://<cosmos>.documents.azure.com:443/
AZURE_COSMOS_KEY=<key>
AZURE_COSMOS_DB=support_db
AZURE_COSMOS_CONTAINER=conversations

APPINSIGHTS_CONNECTION_STRING=<connection-string>

APP_ENV=development
LOG_LEVEL=INFO
MAX_RETRY_COUNT=2
ESCALATION_SEVERITY_THRESHOLD=high

---

## Sample Test Cases

All tests below can be run via `uv run pytest tests/ -v -s`. The examples show the input payload, expected graph path, and truncated output for each key feature.

---

### Test Case 1 — Billing Issue (Resolved)

**Feature tested:** Issue classification → billing routing → KB retrieval → resolution

**Input:**
```python
# tests/test_graph.py
def test_billing_issue_resolved(support_graph):
    result = support_graph.invoke({
        "messages": [{"role": "user", "content": "I was charged twice for my subscription this month."}],
        "conversation_id": "test-billing-001",
        "retry_count": 0,
    })
    assert result["issue_type"] == "billing"
    assert result["resolution_status"] == "resolved"
    assert len(result["resolution_steps"]) > 0
```

**Expected graph path:**
```
classifier → retrieval → reasoner → responder → feedback_eval → END
```

**Sample output:**
```json
{
  "issue_type": "billing",
  "severity": "medium",
  "kb_chunks": [
    "Duplicate charges are automatically refunded within 3–5 business days.",
    "Customers can request manual review via the billing portal."
  ],
  "resolution_steps": [
    "1. Verified duplicate charge in billing system.",
    "2. Initiated refund for the duplicate amount.",
    "3. Sent confirmation email with refund timeline."
  ],
  "resolution_status": "resolved",
  "feedback_signal": "no_feedback"
}
```

---

### Test Case 2 — Technical Issue (High Severity → Auto-Escalated)

**Feature tested:** Severity detection → automatic escalation without retry

**Input:**
```python
def test_high_severity_escalation(support_graph):
    result = support_graph.invoke({
        "messages": [{"role": "user", "content": "Our entire production API is down and we're losing revenue every minute!"}],
        "conversation_id": "test-tech-002",
        "retry_count": 0,
    })
    assert result["issue_type"] == "technical"
    assert result["severity"] == "high"
    assert result["resolution_status"] == "escalated"
```

**Expected graph path:**
```
classifier → retrieval → reasoner → responder → feedback_eval → escalation → END
```

**Sample output:**
```json
{
  "issue_type": "technical",
  "severity": "high",
  "resolution_status": "escalated",
  "feedback_signal": "no_feedback"
}
```
> Escalation ticket is created via `ticket_tool.py` and handed to a human agent queue.

---

### Test Case 3 — Feedback Loop (Not Helpful → Retry → Resolved)

**Feature tested:** Feedback evaluator → retry with refined KB query → final resolution

**Input:**
```python
def test_feedback_retry_loop(support_graph):
    result = support_graph.invoke({
        "messages": [
            {"role": "user", "content": "My password reset email never arrived."},
            {"role": "assistant", "content": "Please check your spam folder."},
            {"role": "user", "content": "That didn't help, still nothing."},
        ],
        "conversation_id": "test-feedback-003",
        "retry_count": 0,
        "feedback_signal": "not_helpful",
    })
    assert result["retry_count"] == 1
    assert result["resolution_status"] in ["resolved", "escalated"]
```

**Expected graph path:**
```
feedback_eval → retrieval (retry) → reasoner → responder → feedback_eval → END
```

**Sample output:**
```json
{
  "issue_type": "technical",
  "severity": "low",
  "retry_count": 1,
  "resolution_steps": [
    "1. Verified email address on file is correct.",
    "2. Manually triggered a new password reset email.",
    "3. Advised customer to whitelist noreply@company.com."
  ],
  "resolution_status": "resolved",
  "feedback_signal": "helpful"
}
```

---

### Test Case 4 — Max Retry → Force Escalation

**Feature tested:** `retry_count` guard prevents infinite loops; escalates after `MAX_RETRY_COUNT` retries

**Input:**
```python
def test_max_retry_escalation(support_graph):
    result = support_graph.invoke({
        "messages": [{"role": "user", "content": "I still can't log in after 3 attempts."}],
        "conversation_id": "test-maxretry-004",
        "retry_count": 2,          # Already at limit (MAX_RETRY_COUNT=2)
        "feedback_signal": "not_helpful",
    })
    assert result["resolution_status"] == "escalated"
```

**Expected graph path:**
```
feedback_eval → escalation → END  (retry guard triggered)
```

**Sample output:**
```json
{
  "retry_count": 2,
  "resolution_status": "escalated",
  "feedback_signal": "not_helpful"
}
```

---

### Test Case 5 — General Inquiry (Low Severity, Direct Response)

**Feature tested:** General issue type routing with knowledge retrieval and low-severity path

**Input:**
```python
def test_general_inquiry(support_graph):
    result = support_graph.invoke({
        "messages": [{"role": "user", "content": "What are your support hours?"}],
        "conversation_id": "test-general-005",
        "retry_count": 0,
    })
    assert result["issue_type"] == "general"
    assert result["severity"] == "low"
    assert result["resolution_status"] == "resolved"
```

**Expected graph path:**
```
classifier → retrieval → reasoner → responder → feedback_eval → END
```

**Sample output:**
```json
{
  "issue_type": "general",
  "severity": "low",
  "kb_chunks": [
    "Support is available Monday–Friday, 9 AM–6 PM EST.",
    "Emergency support for critical issues is available 24/7."
  ],
  "resolution_steps": [
    "1. Retrieved support hours from knowledge base.",
    "2. Included emergency contact information for high-severity cases."
  ],
  "resolution_status": "resolved"
}
```

---

### Test Case 6 — Conversation Persistence (CosmosDB Checkpointer)

**Feature tested:** LangGraph checkpointing via CosmosDB — state survives across graph invocations

**Input:**
```python
def test_conversation_persistence(support_graph_with_checkpointer):
    config = {"configurable": {"thread_id": "persistent-conv-006"}}

    # First turn
    support_graph_with_checkpointer.invoke(
        {"messages": [{"role": "user", "content": "My invoice is incorrect."}]},
        config=config,
    )

    # Second turn — graph should recall prior state from Cosmos
    result = support_graph_with_checkpointer.invoke(
        {"messages": [{"role": "user", "content": "The amount is $200 but should be $150."}]},
        config=config,
    )

    assert result["issue_type"] == "billing"
    assert len(result["messages"]) == 4  # 2 user + 2 assistant turns
```

**Sample output:**
```json
{
  "issue_type": "billing",
  "messages": [
    {"role": "user",      "content": "My invoice is incorrect."},
    {"role": "assistant", "content": "I can help with that. Can you share more details?"},
    {"role": "user",      "content": "The amount is $200 but should be $150."},
    {"role": "assistant", "content": "I've flagged this for a billing adjustment of $50. You'll receive an updated invoice within 24 hours."}
  ],
  "resolution_status": "resolved"
}
```

---

### Running All Tests

```bash
# Run full suite
uv run pytest tests/ -v

# Run with live output (see node logs)
uv run pytest tests/ -v -s

# Run a specific test
uv run pytest tests/test_graph.py::test_billing_issue_resolved -v

# Run with coverage report
uv run pytest tests/ --cov=src/support --cov-report=term-missing
```
```
