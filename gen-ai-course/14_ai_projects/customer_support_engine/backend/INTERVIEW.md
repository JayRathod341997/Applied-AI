# INTERVIEW.md — Agentic Customer Support Resolution Engine

## Q1: Why LangGraph instead of a simple LangChain chain or a ReAct agent?

**A:** Customer support conversations are non-linear and stateful. A user can say "that didn't help" mid-conversation, which requires the system to go back to retrieval with a refined query — not just continue to the next chain step. LangGraph models this as an explicit state machine with conditional edges. We can define exactly what happens when `feedback_signal == "not_helpful"`: re-route to retrieval, not to the start, and not to escalation unless we've retried twice. A ReAct loop can't express this without complex custom logic, and a standard chain has no concept of looping back.

---

## Q2: Walk me through the graph state design.

**A:** The state is a TypedDict with fields for the conversation messages (using LangGraph's `add_messages` reducer so messages accumulate correctly), the classified issue type and severity, KB chunks retrieved, the resolved steps reasoned by the agent, the resolution status, and a retry counter. The retry counter is critical — without it, a persistently unhelpful loop would run forever. We cap at 2 retries before forced escalation. Every node reads from and writes to this shared state, which is checkpointed to Azure Cosmos DB after each node execution.

---

## Q3: How does the feedback loop work technically?

**A:** After the Response Generator emits a response, the Feedback Evaluator node monitors the next customer message. It uses a lightweight GPT-4o classifier prompt: "Given the agent's response and the customer's reply, classify: helpful / not_helpful / no_feedback." If the customer says something like "that's not what I meant" or "still not working", it's classified as `not_helpful` and the conditional edge routes back to the Retrieval node with an augmented query that includes the customer's clarification. The original response and the clarification are both injected into the new retrieval query.

---

## Q4: How is conversation state persisted between turns?

**A:** LangGraph has a checkpointer interface — we implemented a custom `CosmosDBCheckpointer` that serializes the full graph state to an Azure Cosmos DB document keyed by `conversation_id`. Every node transition triggers a checkpoint write. This means if the service restarts mid-conversation, we can restore the exact state from Cosmos and resume from the last completed node. It also gives us a full audit trail of every state transition for debugging.

---

## Q5: How was this deployed and what does production observability look like?

**A:** FastAPI app on Azure Container Apps with WebSocket support for streaming responses. Azure Cosmos DB for state persistence. Azure AI Search for the knowledge base. We instrumented every graph node to emit structured logs via OpenTelemetry to Application Insights — each log includes `conversation_id`, `node_name`, per-node latency, and token usage. In Log Analytics, we can reconstruct full conversation traces and identify which node is slow or causing high escalation rates.

---

## Q6: What's the escalation strategy?

**A:** Three triggers: (1) issue severity classified as "high" by the Classifier node — these go direct to human without attempting automated resolution, (2) retry counter reaches the cap (2 retries), (3) Classifier identifies specific issue types (e.g., fraud, legal complaints) that are blocklisted from automated resolution. The escalation node creates a structured ticket in the external ticketing system (via REST tool call) and hands off the full conversation history and state snapshot so the human agent has complete context.

---

## Q7: What would you improve?

**A:** Two things. First, I'd add streaming output from the Response Generator node using LangGraph's streaming API — right now the customer waits for the full response. Second, I'd add a confidence threshold in the Reasoner node: if the retrieved KB chunks have low similarity to the query, escalate immediately rather than attempt a low-confidence resolution that wastes the customer's time.

---

## Key Terms to Use

- **LangGraph state machine** with conditional edges
- **TypedDict state schema** with `add_messages` reducer
- **Custom Cosmos DB checkpointer** for state persistence
- **Feedback loop** with retry cap and forced escalation
- **Per-node OpenTelemetry instrumentation**
- **Blocklisted issue types** for direct escalation
- **Conversation replay** for regression testing
