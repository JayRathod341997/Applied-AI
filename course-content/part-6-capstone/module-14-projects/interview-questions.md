# Module 14: Production AI Projects — Interview Questions

---

## Quick Reference Table

| # | Question | Level | Topic |
|---|----------|-------|-------|
| 1 | What is the difference between vector search and hybrid search? | Beginner | Search |
| 2 | Why use Azure AI Search over a standalone vector database? | Beginner | Azure Services |
| 3 | What is the role of re-ranking in a recommendation system? | Beginner | Architecture |
| 4 | Explain the LangGraph state machine pattern. | Beginner | LangGraph |
| 5 | What is the advantage of WebSockets over REST for chat applications? | Beginner | API Design |
| 6 | What is map-reduce summarization and when is it needed? | Beginner | LLM Patterns |
| 7 | How does CrewAI's sequential process differ from hierarchical? | Beginner | Multi-Agent |
| 8 | What is Infrastructure as Code and why use Bicep? | Beginner | IaC |
| 9 | Explain the purpose of a checkpointer in LangGraph. | Intermediate | LangGraph |
| 10 | How would you design a personalization layer for a recommender? | Intermediate | Architecture |
| 11 | What are the trade-offs between LangGraph and CrewAI for multi-agent systems? | Intermediate | Framework Choice |
| 12 | How do you handle hallucination in a multi-agent research pipeline? | Intermediate | Quality |
| 13 | Design a streaming architecture for real-time LLM responses. | Intermediate | Streaming |
| 14 | How would you implement intent classification for a support bot? | Intermediate | NLP |
| 15 | What is the cold-start problem in recommendation systems? | Intermediate | Recommendations |
| 16 | How do you evaluate a RAG system before production deployment? | Intermediate | Evaluation |
| 17 | Design a production architecture for a multi-agent research platform. | Advanced | System Design |
| 18 | How would you implement shared memory for distributed agents? | Advanced | Architecture |
| 19 | What are the trade-offs of different deployment strategies for AI services? | Advanced | Deployment |
| 20 | How would you design a self-improving recommendation system? | Advanced | ML Design |

---

## Detailed Answers

---

### Q1. What is the difference between vector search and hybrid search?

**Level:** Beginner

**Answer:**

| Aspect | Vector Search | Hybrid Search |
|--------|--------------|---------------|
| **Mechanism** | Embedding similarity (cosine, dot product) | Combines vector + BM25 keyword matching |
| **Strength** | Semantic understanding, handles synonyms | Exact term matching + semantic understanding |
| **Weakness** | Poor at exact matches (names, IDs) | More complex configuration |
| **Use case** | "Books about overcoming adversity" | "Books by Isaac Asimov about robots" |

Vector search converts text to embeddings and finds semantically similar documents. Hybrid search combines this with BM25 (keyword-based) retrieval, leveraging both approaches via reciprocal rank fusion (RRF) for better overall recall.

---

### Q2. Why use Azure AI Search over a standalone vector database?

**Level:** Beginner

**Answer:**

Azure AI Search provides an integrated platform combining:

- **Hybrid search**: Vector + BM25 + semantic ranking in one service
- **Filtering**: Metadata filters (genre, year, rating) alongside vector search
- **Faceting**: Built-in aggregation for UI filters
- **Managed service**: No infrastructure management, automatic scaling
- **Azure integration**: Native connectivity to Azure OpenAI, Blob Storage, Cosmos DB

Standalone vector databases (Pinecone, Weaviate, Milvus) excel at pure vector operations but require additional services for keyword search, filtering, and faceting. For production systems needing both semantic and keyword search, Azure AI Search reduces architectural complexity.

---

### Q3. What is the role of re-ranking in a recommendation system?

**Level:** Beginner

**Answer:**

Re-ranking is a second-stage scoring layer that refines initial search results using additional signals not available during retrieval:

```
Initial Retrieval (100 results) → Re-Ranking (top 10) → Final Output (top 5)
```

**Signals used in re-ranking:**
- User preferences (genre affinity, author preferences)
- Item quality (ratings, reviews, recency)
- Diversity (avoid showing 5 books from the same series)
- Business rules (promoted content, licensing)
- Cross-encoder scores (more accurate but slower similarity)

**Why two stages?** Retrieval needs to be fast (sub-100ms), so it uses approximate methods. Re-ranking can be more computationally expensive because it processes fewer items. This separation enables both speed and quality.

---

### Q4. Explain the LangGraph state machine pattern.

**Level:** Beginner

**Answer:**

LangGraph models workflows as directed graphs where:

- **Nodes** are functions that process state and return updates
- **Edges** define transitions between nodes
- **State** is a TypedDict that flows through the graph, accumulating data
- **Conditional edges** use routing functions to dynamically choose the next node

```python
class MyState(TypedDict):
    messages: Annotated[list, operator.add]
    result: str

workflow = StateGraph(MyState)
workflow.add_node("process", process_fn)
workflow.add_node("validate", validate_fn)
workflow.set_entry_point("process")
workflow.add_conditional_edges("process", route_fn)
workflow.add_edge("validate", END)
app = workflow.compile()
```

**Key benefits:**
- Explicit state management (no hidden context)
- Visualizable workflows (graph structure)
- Cycles enable iterative reasoning (agent loops)
- Checkpointers enable persistence and human-in-the-loop

---

### Q5. What is the advantage of WebSockets over REST for chat applications?

**Level:** Beginner

**Answer:**

| Aspect | REST | WebSocket |
|--------|------|-----------|
| **Connection** | Request-response (new connection per request) | Persistent bidirectional |
| **Streaming** | SSE (server→client only) | Full bidirectional streaming |
| **Latency** | Connection overhead per request | Minimal after initial handshake |
| **Client signals** | Requires separate endpoint | Can send during generation |
| **Complexity** | Simple, stateless | More complex, stateful |

For chat applications, WebSockets enable:
- Real-time token streaming without connection overhead
- Client sending "stop" signals during generation
- Typing indicators and presence updates
- Multi-part messages without polling

---

### Q6. What is map-reduce summarization and when is it needed?

**Level:** Beginner

**Answer:**

Map-reduce summarization handles documents larger than the LLM context window:

```
Large Document → Split into chunks → Summarize each chunk (Map) → Combine summaries (Reduce)
```

**When needed:**
- Documents exceed context window (e.g., 100-page report, 128K tokens)
- Multiple documents need consolidated summary
- High-quality summary required (vs. truncation)

**Trade-offs:** More expensive (multiple LLM calls), slower, but produces comprehensive summaries. Alternative: `refine` chain processes chunks sequentially, building on previous summaries.

---

### Q7. How does CrewAI's sequential process differ from hierarchical?

**Level:** Beginner

**Answer:**

| Aspect | Sequential | Hierarchical |
|--------|-----------|-------------|
| **Execution** | Tasks run in order, output passes to next | Manager agent delegates tasks dynamically |
| **Control** | Linear pipeline | Manager decides who does what |
| **Complexity** | Simple, predictable | More flexible, harder to debug |
| **Use case** | Research → Review → Write pipeline | Complex projects with dynamic task assignment |

Sequential is better for well-defined pipelines. Hierarchical is better when the workflow is unpredictable and needs dynamic decision-making.

---

### Q8. What is Infrastructure as Code and why use Bicep?

**Level:** Beginner

**Answer:**

Infrastructure as Code (IaC) defines infrastructure in declarative configuration files that can be version-controlled, reviewed, and deployed automatically.

**Why Bicep for Azure:**
- **Azure-native**: First-class support for all Azure resource types
- **Type-safe**: Compile-time validation catches errors before deployment
- **Modular**: Reusable modules for common patterns
- **Idempotent**: Safe to run multiple times (creates/updates as needed)
- **No state file**: Unlike Terraform, Bicep uses Azure ARM directly

**Alternatives:** Terraform (multi-cloud, requires state management), ARM templates (JSON-based, verbose), Pulumi (code-based, multi-language).

---

### Q9. Explain the purpose of a checkpointer in LangGraph.

**Level:** Intermediate

**Answer:**

A checkpointer saves the graph state at each step, enabling:

1. **Persistence**: State survives server restarts
2. **Human-in-the-loop**: Pause execution, wait for human input, resume
3. **Time travel**: Replay or fork execution from any checkpoint
4. **Multi-tenancy**: Separate state per user/session via `thread_id`

**Checkpoint types:**

| Type | Storage | Use Case |
|------|---------|----------|
| `MemorySaver` | In-memory | Development, testing |
| `SqliteSaver` | SQLite file | Single-instance production |
| `PostgresSaver` | PostgreSQL | Multi-instance production |

Without a checkpointer, state is lost after each execution, making multi-turn conversations impossible.

---

### Q10. How would you design a personalization layer for a recommender?

**Level:** Intermediate

**Answer:**

**Architecture:**
```
User Profile Service → Personalization Signals → Re-Ranking Engine
       │                       │                      │
       ▼                       ▼                      ▼
  Reading History        Genre Affinity         Final Score =
  Ratings/Reviews        Author Preference      Base Score ×
  Session Behavior       Format Preference      Personalization Boost
```

**Key considerations:**
- Cold-start problem: Use content-based signals when no history exists
- Exploration vs exploitation: Occasionally show diverse results to discover new preferences
- Privacy: Store only necessary data, allow opt-out of personalization
- Real-time vs batch: Update signals in real-time for session behavior, batch for long-term preferences

---

### Q11. What are the trade-offs between LangGraph and CrewAI for multi-agent systems?

**Level:** Intermediate

**Answer:**

| Aspect | LangGraph | CrewAI |
|--------|-----------|--------|
| **Abstraction** | Low-level graph primitives | High-level agent/task abstractions |
| **Flexibility** | Full control over state and routing | Opinionated patterns (sequential, hierarchical) |
| **Learning curve** | Steeper (understand graphs, state, reducers) | Gentler (define agents, tasks, crew) |
| **State management** | Explicit TypedDict with reducers | Implicit through task context |
| **Persistence** | Built-in checkpointer system | Manual or via memory modules |
| **Best for** | Complex workflows, custom patterns | Standard research/content pipelines |

**When to use LangGraph:** Need fine-grained control, stateful conversational agents, human-in-the-loop with interrupts.

**When to use CrewAI:** Building research/content pipelines, rapid prototyping, standard agent patterns suffice.

---

### Q12. How do you handle hallucination in a multi-agent research pipeline?

**Level:** Intermediate

**Answer:**

**Multi-layer defense strategy:**

```
Layer 1: Source Grounding
- Require citations for all claims
- Cross-reference multiple sources
- Flag unsupported assertions

Layer 2: Validation Agent
- Independent fact-checking pass
- Confidence scoring per claim
- Identify logical inconsistencies

Layer 3: Output Filtering
- NLI (Natural Language Inference) check
- Compare output against source material
- Flag low-confidence sections

Layer 4: Human Review
- Critical reports require human sign-off
- Highlight uncertain sections for review
```

The validation agent is the critical quality gate that catches hallucinations before they reach the final report.

---

### Q13. Design a streaming architecture for real-time LLM responses.

**Level:** Intermediate

**Answer:**

```
Client (React) ←→ API Gateway (WebSocket) ←→ FastAPI Backend (LangGraph) ←→ LLM API
```

**Key components:**

1. **WebSocket connection**: Persistent bidirectional channel
2. **Event streaming**: `astream_events` for token-by-token output
3. **Metadata events**: Send intent, confidence, and status alongside tokens
4. **Error handling**: Graceful degradation with error events
5. **Connection management**: Heartbeat, reconnection, timeout handling

**Considerations:**
- Load balancer WebSocket timeout (increase from default 60s)
- Connection pooling for LLM API calls
- Backpressure handling if client is slow
- Graceful shutdown (complete in-flight streams before restart)

---

### Q14. How would you implement intent classification for a support bot?

**Level:** Intermediate

**Answer:**

**Approach options:**

| Approach | Accuracy | Cost | Latency | Maintenance |
|----------|----------|------|---------|-------------|
| LLM-based | High | Medium | 500ms-2s | Low (prompt updates) |
| Fine-tuned classifier | Very High | Low (inference) | 10-50ms | Medium (retraining) |
| Rule-based | Medium | None | <1ms | High (rule updates) |
| Hybrid (LLM + rules) | Highest | Medium | 100ms-2s | Medium |

**Hybrid approach:**
```python
def classify_intent_hybrid(message: str) -> dict:
    # Fast rule-based pre-filter
    urgent_keywords = ["urgent", "complaint", "manager", "lawsuit"]
    if any(kw in message.lower() for kw in urgent_keywords):
        return {"intent": "escalation", "confidence": 0.9}

    # LLM for nuanced classification
    llm_result = classify_intent(message)
    return {"intent": llm_result, "confidence": 0.7}
```

---

### Q15. What is the cold-start problem in recommendation systems?

**Level:** Intermediate

**Answer:**

The cold-start problem occurs when the system cannot make personalized recommendations due to insufficient data about a user or item.

**Types:**

| Type | Problem | Solution |
|------|---------|----------|
| **User cold-start** | New user with no history | Use onboarding preferences, popular items, demographic-based |
| **Item cold-start** | New item with no interactions | Use content-based features (description, category, metadata) |
| **System cold-start** | New system with no data | Start with curated recommendations, popularity-based |

**Solutions:** Use onboarding questionnaires, content-based filtering for new items, and popularity-based fallbacks until sufficient interaction data accumulates.

---

### Q16. How do you evaluate a RAG system before production deployment?

**Level:** Intermediate

**Answer:**

**Evaluation framework using RAGAS:**

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| **Faithfulness** | Does the answer follow from retrieved context? | > 0.8 |
| **Answer Relevance** | Does the answer address the question? | > 0.8 |
| **Context Precision** | Are retrieved chunks relevant to the question? | > 0.7 |
| **Context Recall** | Does the context contain the information needed? | > 0.7 |
| **Answer Correctness** | Is the answer factually correct? | > 0.85 |

**Additional evaluations:**
- Latency benchmarks (P50, P95, P99)
- Load testing (concurrent users)
- Adversarial testing (prompt injection, edge cases)
- Cost analysis (tokens per query, monthly projection)

---

### Q17. Design a production architecture for a multi-agent research platform.

**Level:** Advanced

**Answer:**

```
Client Layer (Web App, API Clients, Scheduled Jobs)
       │
       ▼
API Gateway (Azure API Management: Auth, Rate Limit, Routing)
       │
       ▼
Application Layer (FastAPI on Azure Container Apps)
  ├── Orchestrator Service
  ├── Task Queue (Redis)
  ├── Result Aggregator Service
  └── CrewAI Workers (Researcher, Critic, Writer Agents)
       │
       ▼
Data Layer
  ├── Cosmos DB (Shared Memory)
  ├── Blob Store (Raw Documents)
  ├── AI Search (Indexed Content)
  └── Redis Cache (Task Queue)
       │
       ▼
Observability (Azure Monitor, Application Insights, Log Analytics)
```

**Key design decisions:**
- **Container Apps**: Auto-scaling, serverless, integrated with Azure ecosystem
- **Redis queue**: Decouple request intake from agent execution
- **Cosmos DB**: Persistent shared memory with global distribution
- **API Management**: Centralized auth, rate limiting, and observability
- **Scheduled jobs**: Trigger periodic research without user interaction

---

### Q18. How would you implement shared memory for distributed agents?

**Level:** Advanced

**Answer:**

**Architecture:**
```
Agent 1 ──┐
Agent 2 ──┼──▶ Cosmos DB Container ──▶ Event Grid ──▶ Agent 3
Agent 3 ──┤         │
          │         ▼
          │   Change Feed ──▶ Trigger Updates
```

**Implementation with Cosmos DB:**

```python
class SharedMemory:
    def __init__(self, connection_string: str):
        client = CosmosClient.from_connection_string(connection_string)
        self.db = client.get_database_client("agent-memory")
        self.container = self.db.get_container_client("shared-state")

    def write(self, research_id: str, agent: str, data: dict):
        item = {
            "id": f"{research_id}-{agent}-{uuid4()}",
            "research_id": research_id,
            "partition_key": research_id,
            "agent": agent,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "ttl": 86400 * 7  # 7-day retention
        }
        self.container.create_item(item)

    def read_session(self, research_id: str) -> list[dict]:
        query = "SELECT * FROM c WHERE c.research_id = @rid ORDER BY c.timestamp"
        return list(self.container.query_items(
            query=query,
            parameters=[{"name": "@rid", "value": research_id}],
            enable_cross_partition_query=True
        ))
```

**Design considerations:**
- **Partitioning**: Use `research_id` as partition key for efficient session queries
- **TTL**: Auto-expire old sessions to control storage costs
- **Change feed**: Enable real-time notifications when agents write to memory
- **Consistency**: Use session consistency for read-your-writes within a session
- **Concurrency**: Optimistic concurrency with `_etag` for conflict resolution

---

### Q19. What are the trade-offs of different deployment strategies for AI services?

**Level:** Advanced

**Answer:**

| Strategy | Downtime | Risk | Cost | Rollback | Best For |
|----------|----------|------|------|----------|----------|
| **Blue-Green** | Zero | Low | 2x during deploy | Instant (switch) | Critical services |
| **Canary** | Zero | Very Low | 1x + canary pods | Instant (shift weights) | Risk-averse releases |
| **Rolling** | Zero (if configured) | Medium | 1x | Medium | Standard updates |
| **Recreate** | Yes | High | 1x | Slow | Non-critical dev |
| **Shadow** | Zero | None | 2x (mirrored traffic) | N/A (no user impact) | Validation before release |

**AI-specific considerations:**

1. **Model warm-up**: LLM services need model loading time (1-5 min). Readiness probes must wait for model to be loaded before routing traffic.

2. **Stateful sessions**: For conversational AI, draining existing sessions before switching is critical. Users mid-conversation should not lose context.

3. **A/B testing**: Deploying two model versions simultaneously for quality comparison requires traffic splitting and metric collection.

4. **Cost impact**: Running duplicate environments for blue-green doubles costs during deployment. For expensive GPU instances, canary is more cost-effective.

---

### Q20. How would you design a self-improving recommendation system?

**Level:** Advanced

**Answer:**

**Architecture:**
```
User Interaction → Event Stream → Feature Store → Model
      ▲                                │
      │                                ▼
      │                        Model Retraining
      │                        (Scheduled/Triggered)
      │                                │
      │                                ▼
      └──────────────────── Model Registry ←── A/B Test
                               │
                               ▼
                        Deploy New Model
```

**Key mechanisms:**
- **Implicit feedback**: Track clicks, views, dwell time, purchases
- **Explicit feedback**: Collect ratings, thumbs up/down
- **Feature store**: Maintain up-to-date user and item features
- **Scheduled retraining**: Retrain weekly on new interaction data
- **A/B testing**: Validate new models before promotion
- **Drift detection**: Monitor feature and prediction drift to trigger retraining

**Implementation flow:**
1. Record every user interaction (click, view, purchase, rating)
2. Stream events to feature store for real-time updates
3. Schedule periodic model retraining on accumulated data
4. Deploy candidate model to canary (10% traffic)
5. Compare metrics (CTR, conversion, diversity) against production
6. Promote if improvement exceeds threshold (e.g., 5% CTR increase)
7. Roll back if metrics degrade

---

*End of Module 14 Interview Questions*


---

## Senior Deep Dive: A Risk-Management Capstone, End-to-End

> *The JD is for AI in risk management for global, regulated organisations, judged on business outcomes. Interviewers want one project you can walk end-to-end and tie to their success metrics.*

### SQ1: Walk through a risk-management GenAI capstone end-to-end.

**Answer:** The canonical example is a **credit-risk / fraud analyst copilot**. Start by defining the **problem and stakeholders** and locking in the **success metric** upfront — for example, cut analyst case-review time by 30% while holding the false-negative rate below the current baseline. The data layer ingests transactions, internal policy documents, and KYC records. The architecture keeps the classic ML and GenAI components in separate lanes: a **calibrated gradient-boosted tabular model** produces the risk score (fast, explainable, auditable), while a **RAG pipeline** over policy documents answers analyst questions, and an **LLM** writes the human-readable case narrative — the LLM is the *second stage*, not the primary classifier. Evaluation covers **faithfulness and context relevance** for the RAG component, **task-success rate** for the copilot as a whole, and **calibration** (Expected Calibration Error) for the score. Rollout uses a canary with **human-in-the-loop approval** for decisions above a risk threshold, and every tool call, retrieval step, and model output lands in a **full audit trail**. Close by mapping each component back to the JD's stated success metrics.

**Trade-off:** Combining classic ML with GenAI increases system complexity and the number of components to monitor, but it lets each technology do what it does best — the GBM gives a fast, explainable, regulator-ready score, while the LLM provides the natural-language reasoning analysts actually read. Conflating the two roles into a single LLM would sacrifice calibration, auditability, and latency.

### SQ2: How do you map a capstone to the JD's success metrics?

**Answer:** Each deliverable should trace directly to one of the JD's named metrics. **Scalable production deployment** means the system shipped and is serving live traffic with uptime SLAs met — not a notebook. **Model performance / accuracy improvement** requires a quantified lift number against the prior baseline, along with the evaluation methodology. **Reduced deployment timeline** is demonstrated through **MLOps automation and paved-path CI/CD**: automated eval gates, containerised services, and infrastructure-as-code that compress idea-to-production time. **Organisational adoption and impact** is measured in active users, decisions assisted, or analyst hours saved per month. Every metric must be **quantified** — interviewers in regulated firms hear many vague claims; a number anchors the conversation and shows you understand business accountability.

**Trade-off:** Optimising a single metric — say, maximising recall on fraud — can inflate false alarms and analyst fatigue, raising operational cost. State which metric you prioritised and why, referencing the risk owner's explicit sign-off: this signals that you understand trade-offs are business decisions, not purely technical ones.

### SQ3: How do you choose between classic ML and GenAI within the capstone?

**Answer:** The decision rule is: match the tool to the structure of the problem. **Tabular, numeric prediction** — default probability, fraud score, credit limit — goes to **gradient-boosted trees** (XGBoost, LightGBM): they are calibrated, interpretable with SHAP, fast at inference, and straightforward to audit. **Unstructured reasoning** — policy Q&A, document summarisation, case narrative generation — goes to an **LLM / RAG pipeline**. Combine the two; never use an LLM as the primary classifier for a consequential numeric prediction. LLMs are non-deterministic, expensive per call, difficult to calibrate, and produce outputs that regulators cannot reproduce — a fundamental mismatch with Model Risk Management (MRM) requirements for auditability and reproducibility.

**Trade-off:** A hybrid system has more moving parts and a larger operational surface than a pure approach, but the senior maturity signal is recommending the *simplest* model that meets each sub-problem's need — often classic ML for the decision and GenAI for the explanation layer. Reaching for a single LLM to do everything is the junior mistake.

### SQ4: What makes the capstone "production-ready" rather than a notebook demo?

**Answer:** Production readiness is entirely about **operational scaffolding**, not model sophistication. The checklist includes: an **eval harness with CI gates** that must pass before any deploy (faithfulness, calibration, regression against baseline); **monitoring and drift detection** for both feature distributions and model outputs, with alerts when metrics degrade; **rollback** capability within a defined SLA; **security and PII handling** — redaction in logs, encryption at rest and in transit, Role-Based Access Control; a **full audit trail** — every inference, every retrieval, every human approval logged with timestamps and actor identity; **cost controls** — token budgets, caching, and a spending alert; **human-in-the-loop** approval for high-risk decisions above a threshold; and a **model card** documenting intended use, limitations, and validation results for the regulator.

**Trade-off:** Each of these components is real engineering effort that a notebook prototype omits. The trade-off is time-to-demo versus time-to-trust. In a regulated environment, trust is the product — a regulator or a credit-committee chair who cannot audit the system's decisions will block deployment regardless of how impressive the demo looks.

### SQ5: How do you present the capstone's business impact to non-technical stakeholders?

**Answer:** Lead with the **outcome and the metric**, not the architecture. Open with something like: "We reduced the average fraud-case review time from 45 minutes to 12, while holding the false-negative rate below the regulatory threshold — that is $X million in prevented losses per quarter and Y analyst FTEs redeployed to higher-value work." Then **connect each technical choice to business value**: hybrid retrieval reduced hallucinated policy citations, which cuts rework and regulatory risk. Finally, **acknowledge limitations and governance** proactively — "The system flags decisions above a risk threshold for human review, and every output is logged for audit" — because in a regulated firm, risk officers and the board audit team are in the room, and they want to hear control language, not just uplift numbers.

**Trade-off:** The depth of technical detail must be calibrated to the audience. With a CRO or CFO, stay at outcomes and governance. With the model risk team, go into validation methodology and calibration plots. With engineers, go into the architecture. In every case, anchor on business value first — the architecture is supporting evidence, not the lead.
