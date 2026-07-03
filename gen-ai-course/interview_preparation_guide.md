# Interview Preparation Guide: RAG & Vector Databases, Agentic Systems and AWS Cloud Architecture

---

## TOPIC 1: RAG & Vector Databases

### 1.1 PRACTICAL/IMPLEMENTATION QUESTIONS

#### Q1: Optimize chunking for a 1000-page technical documentation
```
Optimal Strategy:
- Chunk Size: 512-768 tokens (fits context window with query)
- Overlap: 10-15% (~60-100 tokens) to maintain context boundaries
- Strategy: Markdown-aware recursive splitting
  1. Split by headers (H1 → H2 → H3)
  2. Recursive character splitter within sections
  3. Preserve code blocks as atomic units

Fast vs Accurate Trade-off:
+--------------------+-------------------+--------------------------------+
| Strategy           | Speed             | Retrieval Quality              |
+--------------------+-------------------+--------------------------------+
| Fixed-size (256)   | Fastest           | Low (breaks context)           |
| Semantic (512)     | Slower            | High (coherent)                |
| Parent-child (1K)  | Moderate          | Highest (context + detail)     |
+--------------------+-------------------+--------------------------------+
```

#### Q2: Implement hybrid search with RRF fusion
```python
# Key Implementation
def hybrid_search(query, vector_db, keyword_index, k=10, k_rrf=60):
    # Parallel retrieval
    vector_results = vector_db.search(query, k=k*2)
    keyword_results = keyword_index.search(query, k=k*2)
    
    # RRF Fusion: score = 1/(k + rank)
    scores = defaultdict(float)
    for rank, doc in enumerate(vector_results):
        scores[doc.id] += 1.0 / (k_rrf + rank)
    for rank, doc in enumerate(keyword_results):
        scores[doc.id] += 1.0 / (k_rrf + rank)
    
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
```

#### Q3: Design a multi-tenant RAG system with RBAC
```
Architecture:
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Tenant    │────▶│  Metadata Filter │────▶│ Vector DB   │
│   Context   │     │  (tenant_id)     │     │ (filtered)  │
└─────────────┘     └──────────────────┘     └─────────────┘
       │                     │                        │
       ▼                     ▼                        ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Permission │     │  Chunk Tagging   │     │  Retrieval  │
│   Check     │────▶│  (access_level)  │────▶│  (RBAC)     │
└─────────────┘     └──────────────────┘     └─────────────┘

Implementation:
metadata = {
    "doc_id": "policy_v2.pdf",
    "tenant_id": "acme_corp",
    "access_level": "department:engineering",
    "permissions": ["read", "search"]
}
```

#### Q4: Optimize vector DB for billion-scale vectors
```
Indexing Strategy:
┌─────────────────────────────────────────────────────┐
│                 IVF-PQ Hybrid                       │
├─────────────────────────────────────────────────────┤
│ 1. Coarse Quantization (IVF) - 4096 partitions      │
│ 2. Product Quantization - compress 1536d → 256d     │
│ 3. HNSW within partitions for fine-grained search   │
│ 4. Scalar quantization for metadata                 │
└─────────────────────────────────────────────────────┘

Performance Tuning:
- nlist = 4096 (for 1B vectors, sqrt(n) * 4)
- nprobe = 32-128 (adjust for recall/latency tradeoff)
- M = 32, efConstruction = 200 (HNSW params)
```

#### Q5: Debug retrieval returning irrelevant chunks
```python
# Diagnostic Pipeline
def debug_retrieval(query, vector_db):
    # 1. Analyze query embedding quality
    query_embedding = embed(query)
    
    # 2. Check similarity distribution
    similarities = vector_db.similarity_search_with_scores(query, k=100)
    print(f"Score range: {min(s[1] for s in similarities)} - {max(s[1] for s in similarities)}")
    
    # 3. Inspect chunks for coherence
    for doc, score in similarities[:5]:
        print(f"[{score:.3f}] {doc.page_content[:200]}")
    
    # 4. Verify chunking boundaries
    # Check if chunks break mid-sentence or mid-paragraph
```

---

### 1.2 SITUATIONAL/SCENARIO-BASED QUESTIONS

#### Q1: Handle hallucination in a legal RAG system
```
Defense-in-Depth Strategy:

┌─────────────────────────────────────────────────────┐
│                FACT-CHECK LAYER                     │
├─────────────────────────────────────────────────────┤
│ 1. Citation Enforcement                             │
│    - Require [Source: doc_id, page X] for claims    │
│    - Block responses without citations              │
│                                                     │
│ 2. Confidence Scoring                               │
│    - Retrieval score threshold (min 0.7 cosine)     │
│    - LLM self-evaluation: "confidence: 0.9"         │
│                                                     │
│ 3. Guardrails                                       │
│    - LLM Judge as final check                       │
│    - Block high-risk categories (medical, legal)    │
│                                                     │
│ 4. Human Oversight                                  │
│    - Flag low-confidence responses                  │
│    - Require attorney review for critical issues    │
└─────────────────────────────────────────────────────┘
```

#### Q2: Design RAG for real-time changing inventory
```
Architecture Pattern: Incremental Update with TTL

┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Inventory  │───▶│  Stream      │───▶ │  Vector DB  │
│   Change    │     │  Processor   │     │   (Delta)   │
│   Event     │     │  (Debezium)  │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                  │
                            ▼                  ▼
                    ┌──────────────┐     ┌─────────────┐
                    │  Full        │     │  Real-time  │
                    │  Reindex     │     │  Retrieval  │
                    │  (Nightly)   │     │             │
                    └──────────────┘     └─────────────┘

Key Design Decisions:
- Use timestamp-based filtering for "current" data
- Implement dual-path: live query + historical RAG
- TTL-based stale data detection (24-hour cutoff)
```

#### Q3: Architect multi-hop RAG for research assistant
```
Multi-Hop Strategy:

Query: "What are the economic impacts of climate policy in EU?"

 ┌─────────────────────────────────────────────┐
 │               Query                         │
 │   Decomposition (LLM)                       │
 └─────────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────┐
│ Step 1: Find key policies                      │
│    - Retrieve: EU Green Deal, Carbon Border Tax│
│                                                │
│ Step 2: Find economic studies                  │
│    - Filter by: "economic impact" + "EU"       │
│                                                │
│ Step 3: Extract quantitative data              │
│    - Revenue numbers, job impacts              │
│                                                │
│ Step 4: Synthesize findings                    │
└────────────────────────────────────────────────┘ 

Implementation:
- Use entity extraction to identify sub-questions
- Graph-based retrieval for related concepts
- Iterative refinement: "Am I missing anything?"
```

---

## TOPIC 2: Agentic Systems

### 2.1 PRACTICAL/IMPLEMENTATION QUESTIONS

#### Q1: Implement ReAct loop with LangGraph
```python
from langgraph.graph import StateGraph
from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    question: str
    thoughts: List[str]
    actions: List[dict]
    observations: List[str]
    final_answer: str
    iterations: int

def reason_node(state: AgentState):
    prompt = f"""Question: {state['question']}
    Previous attempts: {state['actions'][-3:] if state['actions'] else []}
    What should I do next? Think step by step."""
    
    response = llm.invoke(prompt)
    return {"thoughts": state['thoughts'] + [response.content]}

def act_node(state: AgentState):
    thought = state['thoughts'][-1]
    # Parse action from thought: Action: tool_name(args)
    action = parse_action(thought)
    if action:
        result = tools[action['name']].invoke(action['args'])
        return {
            "actions": state['actions'] + [action],
            "observations": state['observations'] + [result]
        }
    return state

def should_continue(state: AgentState):
    if "final answer:" in state['thoughts'][-1].lower() or state['iterations'] > 5:
        return "end"
    return "reason"

workflow = StateGraph(AgentState)
workflow.add_node("reason", reason_node)
workflow.add_node("act", act_node)
workflow.add_edge("reason", "act")
workflow.add_conditional_edges("act", should_continue)
```

#### Q2: Design supervisor pattern for multi-agent system
```python
# Supervisor Agent Pattern
class SupervisorAgent:
    def __init__(self, worker_agents):
        self.workers = worker_agents
        self.task_queue = []
    
    def route_task(self, task: dict):
        # Task decomposition
        subtasks = self.decompose(task)
        
        # Agent assignment based on specialization
        assignments = {
            "research": "research_agent",
            "code": "coding_agent",
            "review": "review_agent"
        }
        
        # Execute and aggregate
        results = {}
        for subtask in subtasks:
            agent = self.workers[assignments[subtask.type]]
            results[subtask.id] = agent.execute(subtask)
        
        return self.synthesize(results)
```

#### Q3: Implement memory management for long conversations
```
Memory Hierarchy:

┌─────────────────────────────────────────────────────┐
│              MEMORY MANAGEMENT                      │
├─────────────────────────────────────────────────────┤
│ Hot Memory (Last 5 turns)                           │
│   - Full conversation history                       │
│   - Scratchpad for current reasoning                │
│                                                     │
│ Warm Memory (Last 20 turns)                         │
│   - Summarized to 500 tokens                        │
│   - Key facts extracted                             │
│                                                     │
│ Cold Memory (Long-term)                             │
│   - Vector store of key conversations               │
│   - Semantic retrieval on demand                    │
└─────────────────────────────────────────────────────┘

Implementation:
memory = {
    "hot": ConversationBufferWindowMemory(k=5),
    "warm": SummaryMemoryChain(buffer_memory),
    "cold": VectorStoreRetriever(vector_db, k=3)
}
```

#### Q4: Build tool-calling agent with proper error handling
```python
@tool
def web_search(query: str, max_results: int = 5) -> list:
    """Search the web for information. Returns list of results."""
    try:
        results = search_api.search(query, num_results=max_results, timeout=10)
        return [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in results]
    except TimeoutError:
        return [{"error": "Search timed out. Try a more specific query."}]
    except RateLimitError:
        return [{"error": "Rate limit exceeded. Please wait and retry."}]

def tool_with_retry(tool, max_attempts=3, backoff=2):
    for attempt in range(max_attempts):
        try:
            return tool()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            time.sleep(backoff ** attempt)
```

---

### 2.2 SITUATIONAL/SCENARIO-BASED QUESTIONS

#### Q1: Prevent infinite loops in agent workflow
```
Loop Prevention Architecture:

┌──────────────────────────────────────────────────────┐
│                LOOP DETECTION                        │
├──────────────────────────────────────────────────────┤
│ 1. Iteration Counter                                 │
│    max_iterations = 10                               │
│                                                      │
│ 2. Action History Deduplication                      │
│    - Hash previous (thought, action, observation)    │
│    - Block identical sequences                       │
│                                                      │
│ 3. Progress Metrics                                  │
│    - Track unique entities discovered                │
│    - If no new progress in 3 steps → escalate        │
│                                                      │
│ 4. Circuit Breaker                                   │
│    - After 3 failed attempts → human intervention    │
└──────────────────────────────────────────────────────┘

Implementation:
state = {
    "iterations": 0,
    "action_history": [],
    "entities_found": set(),
    "loop_detector": LoopDetector()
}

if state["iterations"] > 10:
    return "loop_detected"
if state["loop_detector"].is_loop(state):
    return "escalate_to_human"
```

#### Q2: Design agent for code review with security checks
```
Security-First Agent Architecture:

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PR Ingest     │────▶│ Static Analyze  │────▶│ Security Check  │
│   & Context     │     │   (AST parse)   │     │   (Patterns)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ LLM Review      │────▶│ Test Execution  │────▶│ Final Report    │
│ (Best Practices)│     │   (Sandbox)     │     │ + Risk Score    │
└─────────────────┘     └─────────────────┘     └─────────────────┘

Key Checks:
- SQL injection patterns
- Hardcoded secrets detection
- Authentication bypass attempts
- Input validation issues
- Dependency vulnerability scan
```

#### Q3: Handle agent state conflicts in concurrent execution
```
Conflict Resolution Strategy:

┌─────────────────────────────────────────────────────┐
│              STATE CONCURRENCY                      │
├─────────────────────────────────────────────────────┤
│ Problem: Multiple agents modifying shared state     │
│                                                     │
│ Solution: Optimistic Locking + CRDTs               │
│                                                     │
│ 1. Version Vector                                      │
│    state.version = uuid4()                           │
│                                                     │
│ 2. Conflict Detection                                  │
│    if new_state.version != current.version:          │
│        merge_conflicts(old, new)                     │
│                                                     │
│ 3. Resolution Strategies                               │
│    - Last-write-wins (default)                       │
│    - Merge (for structured data)                     │
│    - Human arbitrate (for critical conflicts)        │
└─────────────────────────────────────────────────────┘
```

---

## SUMMARY CHEAT SHEET

### RAG Key Metrics
| Concept | Optimal Value |
|---------|--------------|
| Chunk Size | 512-768 tokens |
| Overlap | 10-15% |
| Top-k Retrieval | 10-20 (rerank to 5) |
| HNSW M | 16-32 |
| HNSW ef | 50-200 |

### Agent Key Patterns
| Pattern | Use Case |
|---------|----------|
| ReAct | Single-agent reasoning |
| Supervisor | Multi-agent coordination |
| Reflection | Quality improvement |
| HITL | Critical decision points |

### Hybrid Search Formula
```
RRF Score = Σ(1/(k + rank_i)) for each retrieval method
k = 60 (typical constant)
Final Rank = Sort by RRF Score descending
```

---

## TOPIC 3: AWS Cloud Architecture & Serverless Design Patterns

### 3.1 PRACTICAL/IMPLEMENTATION QUESTIONS

#### Q1: Design a serverless document processing pipeline with Lambda + SQS

```python
# Producer: API Gateway → Lambda → SQS
import boto3
import json

sqs = boto3.client('sqs')
QUEUE_URL = os.environ['INGEST_QUEUE_URL']

def handler(event, context):
    # Validate and deduplicate
    document_id = event['document_id']
    
    # Send to SQS with deduplication
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(event),
        MessageDeduplicationId=document_id,  # Exactly-once processing
        MessageGroupId=document_id[:8]     # Partition by source
    )
    return {"status": "queued", "document_id": document_id}
```

```
Architecture Flow:
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  API GW     │────▶│  Lambda     │────▶│  SQS FIFO       │
│  (Upload)   │     │  (Validate) │     │  (Buffer)       │
└─────────────┘     └─────────────┘     └────────┬────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │  Lambda         │
                                        │  (Process + DLQ)│
                                        └─────────────────┘
```

Trade-offs Analysis:
| Configuration | Cost | Reliability |
| :--- | :--- | :--- |
| Batch=10, Wait=20s | Low ($0.000016/req) | Good (batch eff) |
| Visibility=300s | Moderate | Better (retry) |
| DLQ after 3 attempts | Higher alerts | Best (no loss) |



#### Q2: Configure SQS dead-letter queues with exponential backoff

```python
# DLQ Handler Patterns
def process_with_dlq(message):
    try:
        # Business logic
        result = process_document(message['body'])
        delete_message(message['receipt_handle'])
        return result
    except TransientError:
        # Let message become visible again
        # Visibility timeout already configured for backoff
        raise
    except PermanentError as e:
        # Send to DLQ for manual inspection
        send_to_dlq(message, str(e))
        # Delete from main queue to prevent reprocessing
        delete_message(message['receipt_handle'])
```

```
Retry Strategy:
┌─────────────────────────────────────────────────────┐
│           SQS RETRY & BACKOFF                         │
├─────────────────────────────────────────────────────┤
│ Attempt 1: 0s (immediate)                           │
│ Attempt 2: 30s (visibility timeout 60s / 2)           │
│ Attempt 3: 2min (exponential)                       │
│ Attempt 4: 8min                                     │
│ DLQ after MaxReceiveCount=3                         │
└─────────────────────────────────────────────────────┘

Implementation:
redrive_policy = {
    "deadLetterTargetArn": dlq_arn,
    "maxReceiveCount": 3
}

# Lambda reserved concurrency for burst control
lambda_function.put_provisioned_concurrency(
    Qualifier='$LATEST',
    ProvisionedConcurrentExecutions=10
)
```

#### Q3: Optimize Lambda for bursty RAG document ingestion workloads

```
Burst Handling Architecture:
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  S3 Upload  │────▶│  Event      │────▶│  SQS Queue      │
│             │     │  Bridge     │     │  (Buffer)       │
└─────────────┘     └─────────────┘     └────────┬────────┘
                                                  │
                    ┌───────────────────────────────┴─────────────────┐
                    │               │               │               │
                    ▼               ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │  Lambda     │ │  Lambda     │ │  Lambda     │ │  Lambda     │
            │  (Worker)  │ │  (Worker)  │ │  (Worker)  │ │  (Worker)  │
            └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
                    │               │               │               │
                    └───────────────────┬─────────────────────────────┘
                                        ▼
                            ┌─────────────────┐
                            │  Vector DB      │
                            │  (Bulk Insert)  │
                            └─────────────────┘

Key Configurations:
- Reserved Concurrency: 50 (burstable to 1000 with provisioned)
- Memory: 3008 MB (max for CPU power)
- Timeout: 15 minutes (max for large docs)
- Environment: Reuse embedding model client across invocations
```

---

### 3.2 SITUATIONAL/SCENARIO-BASED QUESTIONS

#### Q1: Design fault-tolerant microservices with Lambda + SQS decoupling

```
Decoupled Architecture:
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Service A  │────▶│  SQS        │────▶│  Service B      │
│  (Producer) │     │  (Order)    │     │  (Consumer)     │
└─────────────┘     └─────────────┘     └─────────────────┘
       │                   │                   │
       │                   │         ┌─────────┴─────────┐
       │                   │         │ DLQ   │   Retry   │
       │                   │         └───────────────────┘
       │                   │
       └───────────────────┼─────────────────┐
                           │                 ▼
                ┌─────────────────┐   ┌─────────────┐
                │ CloudWatch    │   │  Alerts     │
                │ Alarms          │   │  (PagerDuty)│
                └─────────────────┘   └─────────────┘

Fault Isolation Benefits:
- Service A crash → SQS buffers messages for 14 days
- Service B slow → Scale consumers independently
- Message order preserved via FIFO + MessageGroupId
- Dead letters isolated for root cause analysis

Implementation Decision Matrix:
| Error Type | Action | RTO Target |
| :--- | :--- | :--- |
| Transient (5xx) | Retry 3x | 5 min |
| Validation (400) | DLQ immediately | 0 min |
| Timeout | Back off + retry | 15 min |



#### Q2: Handle burst traffic scaling for Black Friday document processing


Auto-scaling Strategy:
+-----------------------------------------------------+
|         BLACK FRIDAY SCALING PLAN                   |
+-----------------------------------------------------+
| Baseline: 100 docs/min                              |
| Peak: 10,000 docs/min (100x spike)                  |
| Duration: 4 hours                                   |
+-----------------------------------------------------+

Scaling Architecture:
+-------------+     +-------------+     +-----------------+
|  Load       |---->|  SQS        |---->|  Auto-scaled    |
|  Balancer   |     |  (Buffer)   |     |  Lambda Fleet   |
+-------------+     +-------------+     +--------+--------+
                                                 |
                    +-----------------+-----------------+
                    v                 v                 v
            +-------------+   +-------------+   +-------------+
            | Reserved    |   | Provisioned |   | On-demand   |
            | Concurrency |   | Concurrency |   | (Fallback)  |
            | 50          |   | 200         |   | 100         |
            +-------------+   +-------------+   +-------------+


Cost Optimization:
- Reserved: $0.0000004167/vCPU-second (100% utilization)
- Provisioned: $0.000000972/vCPU-second (90% utilization)
- On-demand: $0.00001667/vCPU-second (spiky)

Savings: ~30% with hybrid reserved/provisioned approach

Target Tracking Policy:
aws application-autoscaling put-scaling-policy \
  --service-namespace lambda \
  --scalable-dimension lambda:function:ProvisionedConcurrency \
  --policy-name target-tracking \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "LambdaProvisionedConcurrencyUtilization"
    }
  }'
```

#### Q3: Implement exactly-once processing for financial document ingestion

```
Exactly-Once Guarantee Architecture:

┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  S3 Upload  │────▶│  Lambda     │────▶│  SQS FIFO       │
│  (Deduplicated) │     │  (Validate) │     │  + Content-Based Deduplication │
└─────────────┘     └─────────────┘     └────────┬────────┘
                                                  │
                    ┌───────────────────────────────┼─────────────────┐
                    ▼                               ▼                 ▼
            ┌─────────────┐                 ┌─────────────┐   ┌─────────────┐
            │  Redis      │                 │  Lambda     │   │  DynamoDB   │
            │  (State)    │◀────────────────│  (Process)  │──▶│  (Results)  │
            └─────────────┘    Idempotency  └─────────────┘   └─────────────┘
                    │              Key
                    ▼
            ┌─────────────────────────────────────┐
            │ Idempotency Key = SHA256(S3_URL + LastModified) │
            └─────────────────────────────────────┘

Implementation:
import hashlib
import redis

def is_duplicate(s3_key, last_modified):
    idem_key = hashlib.sha256(f"{s3_key}:{last_modified}".encode()).hexdigest()
    result = redis.setnx(f"idem:{idem_key}", "1")
    if not result:
        raise DuplicateDocumentError(f"Already processed: {s3_key}")
    # Expire after 24 hours
    redis.expire(f"idem:{idem_key}", 86400)
    return False

SQS FIFO Configuration:
- ContentBasedDeduplication: true
- MessageDeduplicationId: auto-generated from message body
- MessageGroupId: document_type (for ordering guarantee)
- VisibilityTimeout: matches Lambda timeout (2x safety)
```

---

## SUMMARY CHEAT SHEET - AWS SECTION

### Lambda + SQS Optimization
| Configuration | Value | Reason |
|---------------|-------|--------|
| Batch Size | 10 | Cost/performance balance |
| Visibility Timeout | 60s | Allow 2 retries |
| Reserved Concurrency | 50-100 | Predictable baseline |
| Provisioned Concurrency | 200 | Peak handling |

### Exactly-Once Patterns
```python
# Idempotent key generation
key = hashlib.sha256(f"{resource_id}:{version}".encode()).hexdigest()
redis.setex(f"processed:{key}", expiry, "done", nx=True)
```

### Cost vs Performance
| Pattern | Cost/Request | Latency | Reliability |
|---------|-------------|---------|-------------|
| On-demand | $0.00001667 | 100ms | Good |
| Provisioned | $0.00000972 | 50ms | Excellent |
| Reserved | $0.0000004167 | 50ms | Requires planning |

---

## Senior Deep Dives by Module

Each course module's `interview.md` ends with a **Senior Deep Dive** structured into four blocks — *System Design & Scale*, *Trade-offs & Decisions*, *Failure Modes & Incidents*, *Leadership & Behavioral* — plus a Staff/Principal stretch question. Use these for senior/staff-level interview prep on each topic:

- [01 — Generative AI](01_generative_ai/interview.md#senior-deep-dive-genai-fundamentals)
- [02 — LangChain](02_langchain/interview.md#senior-deep-dive-langchain-in-production)
- [03 — RAG & Vector Databases](03_rag_vectordb/interview.md#senior-deep-dive-rag--vector-databases)
- [04 — Agentic Systems](04_agentic_systems/interview.md#senior-deep-dive-agentic-systems-at-scale)
- [05 — MCP](05_mcp/interview.md#senior-deep-dive-mcp-in-the-enterprise)
- [06 — LangGraph](06_langgraph/interview.md#senior-deep-dive-langgraph-in-production)
- [06 — MLOps](06_mlops/interview.md#senior-deep-dive-mlops-for-genai)
- [07 — Architecture](07_architecture/interview.md#senior-deep-dive-genai-architecture)
- [08 — CI/CD](08_cicd/interview.md#senior-deep-dive-cicd-for-genai)
- [09 — Monitoring & Observability](09_monitoring/interview.md#senior-deep-dive-monitoring--observability)
- [10 — Governance](10_governance/interview.md#senior-deep-dive-ai-governance--responsible-ai)
- [11 — Fine-Tuning](11_fine-tuning/interview.md#senior-deep-dive-fine-tuning-in-production)
- [12 — Deployment](12_deployment/interview.md#senior-deep-dive-genai-deployment)
- [13 — LLMOps](13_LLMops/interview.md#senior-deep-dive-llmops)
- [15 — AI Security & Governance Engineering](15_ai_security_governance/interview.md#senior-deep-dive-ai-security--governance-engineering)