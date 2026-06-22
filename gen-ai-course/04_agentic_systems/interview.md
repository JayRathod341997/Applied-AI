# Agentic AI & Multi-Agent Systems - Interview Questions

This document contains interview questions and answers covering Module 4: Agentic AI & Multi-Agent Systems.

---

## 1. Introduction to Agentic AI

### Q1: What is Agentic AI?

**Answer:** Agentic AI refers to AI systems that can:

- **Autonomy:** Act independently without constant human guidance
- **Reasoning:** Think through problems step-by-step
- **Plan:** Create and execute multi-step plans
- **Use Tools:** Interact with external systems and APIs
- **Learn from Feedback:** Improve based on results

Unlike simple prompts, agents can take actions, make decisions, and handle complex workflows.

---

### Q2: What are the foundational capabilities of Agentic AI?

**Answer:** Foundational capabilities:

- **Autonomy:** Self-directed task execution
- **Reasoning:** Logical deduction and inference
- **Action:** Interacting with external tools
- **Perception:** Understanding context and environment
- **Memory:** Maintaining state across interactions
- **Planning:** Breaking complex tasks into steps

---

### Q3: What is the difference between a regular prompt and an Agentic AI?

**Answer:**

| Aspect | Regular Prompt | Agentic AI |
|--------|---------------|------------|
| Interaction | Single response | Multi-step |
| Tools | No | Yes |
| Memory | No | Yes |
| Planning | No | Yes |
| Autonomy | None | High |
| Use Case | Simple Q&A | Complex workflows |

---

### Q4: What are the components of Agentic AI?

**Answer:** Components:

- **Goals:** What the agent wants to achieve
- **Perception:** Input understanding
- **Reasoning:** Decision-making process
- **Planning:** Step decomposition
- **Action:** Tool execution
- **Feedback:** Result evaluation
- **Memory:** Context retention

---

### Q5: How do you understand Agentic AI with scenarios?

**Answer:** Example scenarios:

1. **Research Agent:** 
   - Receive topic → Search → Read → Summarize → Compile report

2. **Coding Agent:**
   - Receive requirement → Write code → Test → Debug → Refactor

3. **Data Analysis Agent:**
   - Receive question → Query data → Analyze → Visualize → Explain

---

## 2. Agentic AI Design Patterns

### Q6: What are Reactive vs Planning Agents?

**Answer:**

**Reactive Agents:**
- Respond to immediate stimuli
- No explicit planning
- Fast execution
- Good for simple tasks

**Planning Agents:**
- Decompose complex tasks
- Create step-by-step plans
- Can replan if needed
- Better for complex workflows

---

### Q7: What is Reflection in Agentic AI?

**Answer:** Reflection patterns:

- **Self-Correction:** Agent reviews its own outputs
- **Error Detection:** Identify mistakes
- **Improvement:** Refine based on feedback
- **Debugging:** Trace through steps

Implementation: Add review step after initial response, allow multiple passes

---

### Q8: How do you design and integrate tools with Agents?

**Answer:** Tool integration:

1. **Define Tool:** Create function with @tool decorator
2. **Describe Tool:** Add name, description, parameter schema
3. **Register Tool:** Add to agent's tool list
4. **Invoke Tool:** Agent decides when to call

Best practices: Clear descriptions, proper error handling, appropriate timeouts

---

### Q9: What are the different types of Actions in Agents?

**Answer:** Action types:

- **Tool Actions:** Call external functions
- **LLM Actions:** Generate text responses
- **Conditional Actions:** Branch based on state
- **Human Actions:** Request human input
- **Composite Actions:** Sequential or parallel execution

---

### Q10: What are memory patterns in Agents?

**Answer:** Memory types:

- **Buffer Memory:** Store recent messages
- **Sliding Window:** Keep last K items
- **Summary Memory:** Compress history
- **Vector Memory:** Semantic retrieval
- **Scratchpad:** Working memory for reasoning
- **Shared Memory:** For multi-agent systems

---

### Q11: What is the ReAct (Reasoning + Acting) pattern?

**Answer:** ReAct pattern:

1. **Reason:** Think about what to do
2. **Act:** Execute an action (usually a tool)
3. **Observe:** Get result of action
4. **Repeat** until task complete

This combines reasoning with environmental interaction for better results.

---

## 3. Multi-Agent Collaboration

### Q12: What are Multi-Agent Systems?

**Answer:** Multi-agent systems:

- **Multiple Agents:** Different specialized agents work together
- **Collaboration:** Share information and results
- **Coordination:** Organize work between agents
- **Communication:** Agents can talk to each other

Example: One agent researches, another writes, another edits

---

### Q13: How do Multi-Agents work together?

**Answer:** Collaboration patterns:

1. **Supervisor Pattern:** One agent coordinates others
2. **Sequential Pattern:** Pass work from one to next
3. **Parallel Pattern:** Multiple agents work simultaneously
4. **Debate Pattern:** Agents discuss and converge

---

### Q14: What is the architecture for multi-agent systems?

**Answer:** Architecture:

```
User → Orchestrator → [Agent A, Agent B, Agent C]
                ↓
           Results Aggregation
                ↓
             User Response
```

Key components:
- Task decomposition
- Agent selection
- Result synthesis
- Error handling

---

## 4. Agent-to-Agent (A2A) Protocol

### Q15: What is the A2A Protocol?

**Answer:** A2A Protocol:

- **Standard Communication:** Agents communicate with each other
- **Defined Messages:** Structured message formats
- **Capability Discovery:** Agents know what others can do
- **State Sharing:** Share context and results

---

### Q16: What are Agent Roles and Contracts in A2A?

**Answer:** Roles:

- **Task Initiator:** Starts the workflow
- **Task Executor:** Performs the work
- **Coordinator:** Orchestrates other agents
- **Specialist:** Has specific domain expertise

Contracts: Define what each role provides and expects

---

### Q17: How does A2A messaging work?

**Answer:** Messaging:

1. **Task Message:** What needs to be done
2. **Capability Query:** What can you do?
3. **Result Message:** Here's what I found
4. **Status Message:** Here's where I am
5. **Error Message:** Something went wrong

---

### Q18: What are orchestration strategies in A2A?

**Answer:** Strategies:

- **Centralized:** One agent controls everything
- **Decentralized:** Agents collaborate peer-to-peer
- **Hierarchical:** Supervisor manages sub-agents
- **Market-based:** Agents bid on tasks

---

### Q19: How is memory shared in A2A?

**Answer:** Shared memory:

- **Shared Context:** Common understanding
- **Task State:** Where we are in workflow
- **Results:** What each agent found
- **History:** What's been done

Implementation: Centralized store or message passing

---

### Q20: How do you implement tracing and observability in A2A?

**Answer:** Implementation:

- **Trace Each Agent:** Log all actions
- **Correlation IDs:** Link related messages
- **Timeline View:** Visualize workflow
- **Error Tracking:** What failed and why

Tools: LangSmith, OpenTelemetry, custom logging

---

## 5. LangGraph Framework

### Q21: What is LangGraph?

**Answer:** LangGraph is:

- **Graph-based:** Agents as nodes in a graph
- **Cyclic:** Can loop and branch
- **Stateful:** Maintains state across steps
- **LangChain Native:** Built on LangChain

Use cases: Complex agents, multi-step workflows, interactive systems

---

### Q22: What are the key concepts in LangGraph?

**Answer:** Key concepts:

- **Nodes:** Individual steps/functions
- **Edges:** Connections between nodes
- **State:** Shared data across graph
- **Conditional Edges:** Branch based on state
- **Cycles:** Loop for retry or refinement

---

### Q23: How does LangGraph differ from LangChain?

**Answer:**

| Aspect | LangChain | LangGraph |
|--------|-----------|-----------|
| Flow | Sequential | Graph/Cyclic |
| State | Limited | Full control |
| Complexity | Lower | Higher |
| Use Case | Simple chains | Complex agents |

---

### Q24: How do you implement Reflection in LangGraph?

**Answer:** Implementation:

```python
def should_continue(state):
    if state["attempts"] < 3:
        return "reflect"
    return "end"

workflow.add_node("reflect", reflection_node)
workflow.add_conditional_edges("reflect", should_continue)
```

---

### Q25: How do you implement Tools in LangGraph?

**Answer:** Tool implementation:

```python
from langgraph.prebuilt import ToolNode

tools = [search_tool, calculator]
tool_node = ToolNode(tools)

workflow.add_node("tools", tool_node)
```

---

### Q26: What is the Planning-ReAct pattern in LangGraph?

**Answer:** Implementation:

1. **Plan Node:** Break task into steps
2. **Execute Node:** Run each step
3. **Evaluate Node:** Check results
4. **Replan Node:** Adjust if needed

---

### Q27: How do you implement multi-agent collaboration in LangGraph?

**Answer:** Implementation:

```python
# Different nodes for different agents
workflow.add_node("researcher", researcher_agent)
workflow.add_node("writer", writer_agent)
workflow.add_node("editor", editor_agent)

# Sequential or parallel execution
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", "editor")
```

---

### Q28: How do you handle memory in LangGraph?

**Answer:** Memory handling:

- **Checkpointer:** Persist state between runs
- **Thread ID:** Different conversations
- **State Updates:** Modify state at each node

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
compiled = workflow.compile(checkpointer=checkpointer)
```

---

### Q29: What is Human-in-the-Loop (HITL) in LangGraph?

**Answer:** HITL implementation:

```python
def human_approval(state):
    user_input = input("Approve? (y/n): ")
    return user_input == "y"

workflow.add_node("human_review", human_approval)
workflow.add_edge("action", "human_review")
```

---

### Q30: How do you implement retry logic in LangGraph?

**Answer:** Retry configuration:

```python
from langgraph.pregel.retry import RetryPolicy

retry_policy = RetryPolicy(
    max_attempts=3,
    initial_interval=1,
    backoff_factor=2
)

workflow.add_node("action", action_node, retry=retry_policy)
```

---

## Production Questions

### Q31: How do you debug agent workflows?

**Answer:** Debugging:

1. **LangSmith Traces:** Visualize execution
2. **Checkpointing:** Replay from any point
3. **State Inspection:** View state at each node
4. **Logging:** Add print statements
5. **Testing:** Unit test each node

---

### Q32: How would you build a research agent with LangGraph?

**Answer:** Design:

1. **Search Node:** Find relevant info
2. **Extract Node:** Pull key details
3. **Synthesize Node:** Create summary
4. **Review Node:** Check quality
5. **Format Node:** Present results

---

### Q33: What are best practices for agent production systems?

**Answer:** Best practices:

- **Clear Tool Descriptions:** For better agent decisions
- **Error Handling:** Graceful failures at each step
- **Timeouts:** Prevent infinite loops
- **Human Handoffs:** For complex cases
- **Monitoring:** Track success rates
- **Logging:** Full audit trail

---

## Scenario Questions

### Q34: Your agent is getting stuck in a loop. How would you fix it?

**Answer:** Fixes:

1. **Add Max Iterations:** Limit retry count
2. **Track History:** Don't repeat same actions
3. **Better Prompts:** Give clearer guidance
4. **State Validation:** Check if making progress
5. **Add Human Input:** Break the loop

---

### Q35: How would you design an agent for code review?

**Answer:** Design:

1. **Receive PR:** Get code changes
2. **Analyze:** Run static analysis
3. **Review:** Check best practices
4. **Test:** Run existing tests
5. **Summarize:** Create feedback report
6. **Suggest Fixes:** Propose improvements

---

## Senior Deep Dive: Agentic Systems at Scale

> Senior interviews at this level shift from "can you build an agent?" to "can you operate autonomous agents reliably, cheaply, and safely in production?" Expect probes on orchestration topology, cost containment, failure containment, and the organisational trust required before letting agents act without human sign-off.

---

### System Design & Scale

#### Q: Design a multi-agent system for a complex workflow — supervisor vs. swarm?

**Answer:** Default to a **supervisor topology** for business workflows; reserve swarm for embarrassingly parallel tasks with no shared output.

In a supervisor topology a single orchestrator agent owns the task graph, delegates sub-tasks to specialist worker agents, and owns the aggregation/synthesis step. Workers are stateless — they receive a scoped task message, call tools, and return a structured result. The orchestrator holds the authoritative state object (e.g., a LangGraph `StateGraph` with a `TypedDict` state).

In a swarm topology every agent is a peer — each can hand off to any other. This works well when subtasks are truly independent (e.g., parallel document extraction across 50 PDFs) but debugging is harder and cost is unbounded without explicit caps.

| Dimension | Supervisor | Swarm |
|---|---|---|
| Coordination cost | Low (one brain) | High (consensus overhead) |
| Debuggability | High (single trace root) | Lower (distributed traces) |
| Parallelism | Explicit fan-out only | Natural |
| State conflicts | Rare | Common without versioning |
| Best for | Structured business workflows | High-throughput parallel pipelines |

**Practical design choices:**
- Use a **message bus** (Azure Service Bus, or in-process LangGraph channels) rather than direct agent-to-agent HTTP calls — it decouples agents and gives you durable replay.
- Limit parallelism to what the downstream tools can absorb — fan-out to 10 worker agents calling the same SQL database will saturate connection pools.
- Charge each sub-task a **token budget** at dispatch time so the orchestrator can cancel branches that overspend.

**Senior framing:** Interviewers want to hear you name the failure mode of each topology before they ask. With supervisor: the orchestrator is a single point of failure — run it on a durable checkpointed graph (LangGraph Cloud / Azure Durable Functions). With swarm: runaway delegation loops — enforce a maximum hop count per task.

---

#### Q: How do you bound cost and latency of autonomous agents at scale?

**Answer:** Cost and latency spiral because agents are iterative — every reasoning step multiplies token spend. The fix is layered budgeting enforced at the framework level, not the prompt level.

**Step caps:** Set a hard `max_iterations` on every agent loop. LangGraph's `RecursionLimit` is a last-resort guard; your application logic should enforce a lower soft limit and surface a structured "budget exhausted" result rather than letting the framework throw.

**Per-task token budget:** Attach a `remaining_budget` field to the shared state. Before each LLM call, check `remaining_budget > threshold`; if not, route to a summarise-and-exit node. This makes budget a first-class state variable visible in every trace.

**Model tiering:** Use a cheap, fast model (GPT-4o-mini, Claude Haiku) for sub-agent reasoning and tool-result parsing. Reserve the capable model (GPT-4o, Claude Sonnet/Opus) for the orchestrator's final synthesis step only. Typical savings: 60–80 % token cost for the same output quality on structured workflows.

**Prompt/result caching:** Azure OpenAI prompt caching (prefix caching) saves re-spending tokens on repeated system prompts across a session. For tool results that are deterministic (e.g., a database lookup for the same entity), cache at the application layer with a short TTL.

**Early exit:** If a confidence signal (e.g., tool result already contains the answer) is above threshold after step 2, skip remaining steps. Implement as a conditional edge in LangGraph.

**Senior framing:** Quote numbers — "our baseline agent cost $0.04 per run; with model tiering and caching we brought it to $0.009." Interviewers at senior level want to see that you treat cost as an engineering metric, not an afterthought.

---

#### Q: How do you manage shared state across concurrent agents?

**Answer:** Concurrent writes to shared state without coordination produce silent data corruption — one agent's update overwrites another's.

**Preferred pattern — optimistic versioning:** Attach a monotonic `version` integer to every state document. Before writing, an agent reads the current version, does its work, and writes back with a `WHERE version = <read_version>` condition (CAS — compare-and-swap). If another agent updated in the meantime, the write fails and the agent retries with the fresh state.

In LangGraph this is handled by defining reducers on state fields. For lists, use an `append` reducer so concurrent agents add to the list rather than overwrite it. For scalar fields that must be set exclusively, use a checkpoint lock at the task level.

**Conflict resolution strategies:**

| Strategy | When to use |
|---|---|
| Last-write-wins | Non-critical metadata (timestamps, status labels) |
| Merge / union | Additive fields (discovered URLs, extracted entities) |
| Coordinator arbitration | Financial figures, decisions requiring consistency |
| Retry on conflict | Short-lived locks, low contention |

**Idempotency:** Every agent action (tool call, database write, API call) must be idempotent — safe to replay after a crash. Use idempotency keys on outbound API calls (Stripe-style `Idempotency-Key` header). Store completed tool-call hashes in state so retried steps are skipped.

**Senior framing:** Mention that LangGraph's checkpointer serialises writes to the state store, which gives you linearisability within a single graph run. For cross-run or cross-graph state (e.g., a shared knowledge base), you need an external store with CAS semantics — Azure Cosmos DB's optimistic concurrency (`_etag`) is a clean fit.

---

#### Q: How do you ensure tool execution safety and sandboxing at scale?

**Answer:** Unsafe tool execution is the primary production risk for autonomous agents — a single misconfigured permission can lead to data deletion, exfiltration, or runaway infrastructure spend.

**Least privilege:** Each agent is issued credentials scoped to exactly the tools and data it needs for its sub-task. In Azure, use managed identities scoped to specific resource groups; never pass subscription-level credentials to an agent.

**Sandboxed execution environments:** Code-execution tools (Python REPL, bash) must run in isolated containers — Azure Container Instances or Docker with no network access and read-only filesystem mounts. Kill after a hard timeout (e.g., 30 s). Never run agent-generated code in the host process.

**Tool allow-lists:** The orchestrator's tool registry is a static allow-list. Agents cannot register new tools at runtime. Tool schemas are validated at startup, not at call time.

**Rate limits and circuit breakers:** Wrap every external API tool with a rate-limiter (token bucket) and a circuit breaker. If a tool returns >5 errors in 60 s, open the circuit and route to a graceful-degradation path rather than hammering the downstream.

**Audit log:** Every tool invocation — arguments, result, calling agent ID, timestamp — is appended to an immutable audit log (Azure Monitor / Event Hub). This is your forensic trail when something goes wrong.

**Senior framing:** Describe your threat model explicitly: "The risk I'm most worried about is prompt injection via tool results — a malicious document returned by a search tool could hijack the agent's next action." Mitigations: output parsing that treats tool results as untrusted data, not instructions; separate system context from tool output in the prompt.

---

### Trade-offs & Decisions

#### Q: When should you use a single capable agent vs. multi-agent decomposition?

**Answer:** Start with a single agent. Decompose only when a concrete constraint forces it.

A single capable agent is simpler to debug, has lower latency (no inter-agent message round-trips), and is cheaper (no orchestrator overhead). It fails when: (a) the context window cannot hold all intermediate state, (b) the task requires genuinely parallel subtasks that would take too long sequentially, or (c) specialisation is so deep that a single prompt degrades in quality (e.g., simultaneous expert legal and expert financial reasoning).

| Factor | Prefer single agent | Prefer multi-agent |
|---|---|---|
| Task complexity | Moderate | High / multi-domain |
| Context size | Fits in one window | Exceeds window |
| Parallelism needed | No | Yes (latency matters) |
| Debuggability priority | High | Lower (acceptable) |
| Team ownership | One team | Multiple domain teams |
| Cost | Lower | Higher (orchestration tax) |

**Reliability:** A multi-agent system has more failure surfaces — each agent can fail independently, and partial failures are harder to recover from. Build single-agent solutions first; profile them; decompose only the bottleneck.

**Senior framing:** "I've seen teams jump to multi-agent because it sounds sophisticated, then spend weeks debugging agent-to-agent communication instead of shipping value. My default is a single agent with well-structured tool calls, promoted to multi-agent when I can measure a specific constraint that decomposition resolves."

---

#### Q: How do you decide where to place human-in-the-loop checkpoints vs. letting the agent run autonomously?

**Answer:** Gate on **risk × irreversibility**, not on "it feels safer."

The cost of a checkpoint is throughput — every human gate adds latency and breaks the value proposition of automation. The cost of no checkpoint is unbounded blast radius when the agent is wrong. Frame the decision as: "What is the worst outcome if this step executes incorrectly and we don't catch it for 24 hours?"

**Gate placement heuristic:**

| Risk level | Example actions | Checkpoint policy |
|---|---|---|
| Low / reversible | Read data, draft text, run queries | No gate — log only |
| Medium / correctable | Send internal Slack message, create draft PR | Async notification, human can revert |
| High / irreversible | Send external email, execute DB write, deploy infra | Synchronous approval before execution |
| Critical | Delete data, transfer funds, publish externally | Always gate — no exception |

**Throughput vs. safety dial:** In early deployment, gate everything and measure override rate. If humans approve >95 % of requests unchanged, the gate adds no value — remove it and rely on monitoring + rollback. If override rate is high, the agent is wrong and you need the gate.

**LangGraph implementation:** `interrupt_before` on the high-risk tool node pauses the graph and surfaces the pending action to a human-facing UI. The human approves or edits, then resumes with `Command(resume=...)`.

**Senior framing:** HITL is a deployment dial, not a binary choice. Define an autonomy ladder (levels 1–5, from "agent suggests, human acts" to "agent acts, human notified after") and publish it to stakeholders. This creates a shared vocabulary for risk conversations.

---

#### Q: ReAct vs. plan-and-execute vs. reflection — how do you choose?

**Answer:** Match the pattern to task structure, not to what's trendy.

**ReAct** (interleaved Reason → Act → Observe) is best for open-ended tasks where the correct next action depends on what you just learned. It handles uncertainty well but is expensive on long tasks because every step costs a full LLM call.

**Plan-and-execute** (upfront planning, then sequential execution) works when the task structure is known in advance — e.g., "extract data from 10 documents and write a report." The plan is cheap to generate; execution of each step can use a smaller model. Weakness: the plan can be wrong, and replanning mid-execution requires careful state management.

**Reflection** (agent critiques its own output and iterates) is a quality amplifier, not a primary loop strategy. Use it as a final pass on high-stakes outputs (code, legal summaries) with a hard cap of 2–3 reflection rounds.

| Pattern | Best fit | Weakness | Cost profile |
|---|---|---|---|
| ReAct | Open-ended, discovery tasks | Expensive at scale | O(steps × model_cost) |
| Plan-and-execute | Known structure, batch work | Brittle if plan is wrong | Low (small model for steps) |
| Reflection | Quality-critical outputs | Adds latency and cost | +2–3× final step cost |
| Hybrid | Complex production workflows | More complex to implement | Tunable |

**Senior framing:** In practice, production systems combine patterns: ReAct for the discovery phase, plan-and-execute for the execution phase, and a single reflection pass before final output delivery. The key engineering decision is where to switch between them — usually after the agent has gathered enough context to make a reliable plan.

---

### Failure Modes & Incidents

#### Q: An agent took a destructive action it shouldn't have. How do you contain the incident and prevent recurrence?

**Answer:** Treat this as a production incident with a full post-mortem, not just a prompt-tuning exercise.

**Immediate containment:**
1. Disable the agent (set a feature flag to route to human-only path) — do not attempt a hotfix under pressure.
2. Assess blast radius: what data was affected, can it be restored from backup or event log?
3. Execute rollback if available (soft-delete recovery, infrastructure state revert, API idempotency key replay).
4. Notify affected stakeholders per incident runbook.

**Root cause categories and fixes:**

| Root cause | Prevention |
|---|---|
| Missing HITL gate on high-risk tool | Add `interrupt_before` on that tool node; deploy to staging first |
| Prompt injection via tool result | Parse tool output as data, not instructions; sanitise before returning to LLM |
| Overly broad credentials | Rotate to least-privilege managed identity; audit all agent credential scopes |
| Missing dry-run mode | Implement `dry_run=True` param on all mutating tools; run new agents in dry-run for first N tasks |
| No audit log | Instrument every tool call to append to immutable audit store before execution |

**Systemic prevention:** Every mutating tool must have a dry-run mode that returns "would have done X" without executing. New agent configurations run exclusively in dry-run for the first 100 tasks in production, with human review of sampled outputs before promoting to live execution.

**Senior framing:** The post-mortem question that matters is not "why did the agent do this?" but "why did our system allow the agent to do this?" The agent behaving unexpectedly is assumed — your controls failed. Focus the retrospective on the control gaps.

---

#### Q: An agent is looping with no progress. How do you detect and break it?

**Answer:** Loops are inevitable in any sufficiently complex agent — the key is detecting them quickly and escalating cleanly rather than letting them run until timeout.

**Detection mechanisms:**

1. **Iteration counter:** Hard limit via LangGraph `RecursionLimit`. Set this low (e.g., 25 steps for a typical task) — it is a safety net, not a target.

2. **Progress metric:** Track a task-specific progress signal in state (e.g., number of new entities discovered, bytes of output produced). If progress delta over the last 3 iterations is zero, classify as stuck and route to escalation node.

3. **Action deduplication:** Hash each `(action_type, arguments)` tuple. If the same hash appears twice in the action history, the agent is replaying — break immediately.

4. **Wall-clock timeout:** Set a hard deadline at task dispatch time. If the graph has not reached a terminal node by T minutes, the orchestrator cancels it and returns a partial result with a `timeout` status.

**Escalation path:** On stuck detection, do not just raise an exception. Capture the full state at the point of detection, write it to the audit log, and route to a human-review queue with a structured summary: "Agent stuck at step N after attempting action X, Y, Z. Last tool result: ..."

**Senior framing:** The dangerous loop is not the fast tight loop (caught quickly by iteration counter) but the slow drift loop — the agent makes small, non-zero progress each step but is circling rather than converging. Detect this with a progress velocity threshold: if `progress / cost` drops below a baseline, treat as effectively stuck.

---

#### Q: A tool or API failure cascaded across multiple agents in your system. How do you handle it?

**Answer:** Cascade failures happen when agents are tightly coupled to a shared dependency with no isolation. The fix is circuit breakers at the tool layer and graceful degradation at the agent layer.

**Retries with exponential backoff:** Every tool wrapper retries transient failures (HTTP 429, 503) with exponential backoff and jitter. Use the `tenacity` library or LangGraph's built-in `RetryPolicy`. Never retry immediately — a thundering herd of retrying agents will extend the outage.

```python
from langgraph.pregel.retry import RetryPolicy

retry_policy = RetryPolicy(
    max_attempts=3,
    initial_interval=2.0,
    backoff_factor=2.0,
    jitter=True
)
```

**Circuit breaker:** After N consecutive failures, open the circuit for the tool. All agents calling that tool receive an immediate `ServiceUnavailable` result without attempting the call. This prevents agents from queueing behind a broken dependency and blowing their budgets. Implement with `pybreaker` or a shared counter in Redis / Azure Cache.

**Graceful degradation:** Each agent must have a defined behaviour when a critical tool is unavailable. Options: return partial results with a `degraded` flag, fall back to a cached result, route the subtask to a human queue. Never surface a raw exception to the orchestrator — always return a structured error result.

**Bulkhead isolation:** Agents working on independent tasks should have separate tool client instances with separate connection pools. A cascade failure in one pool does not affect others.

**Post-incident review:** Track which tools are on the critical path for each workflow. Tools with no fallback path are risks — prioritise building degradation modes for them.

**Senior framing:** "When our search API went down, every agent in the system stalled because they all shared one client with no circuit breaker. We lost 40 minutes of throughput. The fix was a per-tool circuit breaker and a cached-results fallback — after that, the same outage caused a graceful degradation to slightly stale results rather than a full stall."

---

### Leadership & Behavioral

#### Q: How do you build organisational trust to allow agents to act autonomously?

**Answer:** Trust is earned incrementally through demonstrated reliability, not granted upfront because the technology is impressive.

The approach that works: start with the **autonomy ladder** — a published document that defines five levels from "agent suggests, human acts" (level 1) to "agent acts, human notified by exception" (level 5). Map each task category to a level, with explicit criteria for promotion: "to move from level 3 to level 4, the agent must achieve <0.1 % error rate over 1,000 audited tasks."

**Stakeholder communication:** Non-technical stakeholders need to see that you have thought about what can go wrong, not just what will go right. Show them the circuit breakers, the dry-run mode, the rollback procedure, and the incident response runbook before the agent goes live — not after the first incident.

**Measurement:** Publish a weekly agent reliability dashboard visible to leadership: tasks completed autonomously, human override rate, incidents, cost per task. Declining override rate is the strongest trust signal — it demonstrates the agent is making decisions that humans endorse.

**Incremental scope expansion:** Each new task category starts at level 2 (agent drafts, human approves) regardless of how simple it seems. Promotion is data-driven. This creates a repeatable, defensible process rather than a series of one-off judgement calls.

**Senior framing:** "Trust is a product of transparency + time. The fastest path to full autonomy is being maximally transparent about failures early — stakeholders who see that you catch and fix errors quickly become more willing to extend scope than stakeholders who learn about failures from outside the team."

---

#### Q: Tell me about a time you had to scope down an agent's autonomy after an incident. (STAR)

**Answer:**

**Situation:** We had deployed a customer-support triage agent that could autonomously close tickets classified as "resolved" and send a closure email to the customer. Three weeks in, a miscalibrated classifier caused the agent to close 47 open tickets from one enterprise customer, triggering an escalation to our VP of Customer Success.

**Task:** I needed to contain the immediate customer impact, identify the root cause, and redesign the agent's autonomy boundaries to prevent recurrence — without disabling the agent entirely, since it was handling 300+ tickets per day.

**Action:** I immediately disabled the auto-close action (feature flag, 5 minutes), triggered manual re-open for the 47 affected tickets, and drafted a customer apology with our CS team. For root cause: the classifier had a recall/precision imbalance that looked fine on aggregate metrics but failed on a specific ticket category. I introduced a two-step gate for the close action — the agent still classifies and drafts the closure, but the action is held in a human-review queue for 30 minutes with a one-click approve/reject UI. High-confidence closures (>0.97 classifier score, ticket age >7 days, no open replies) were promoted back to fully autonomous after 2 weeks of zero overrides. I also added a per-customer daily cap: the agent could not close more than 10 tickets from one customer in a single day without a supervisor override.

**Result:** The incident led to a formal "autonomy level" framework that we applied to all agent actions — not just this one. Six months later, the agent was handling 600+ tickets per day with a 99.3 % autonomous closure rate and zero further incidents. The customer escalation became the case study we used internally to get budget for proper agent observability tooling.

**Senior framing:** The key lesson: autonomy rollback should be surgical, not binary. Disabling the agent entirely would have lost the productivity gains. Scoping the rollback to the specific failing action, with data-driven criteria for re-promotion, kept the value while addressing the risk.

---

> 🎯 **Staff/Principal stretch:** Define your organisation's guardrail policy for what agents may do autonomously vs. what requires human approval — and explain how you would enforce and evolve it.

**Model answer:** A guardrail policy at staff/principal level is an engineering governance document, not a prompt instruction. It has three parts: a **classification taxonomy** (what categories of action exist and their risk tier), an **enforcement mechanism** (how the policy is implemented in code, not in agent instructions), and an **evolution process** (who can change it and under what conditions).

**Classification taxonomy example:**

| Tier | Action type | Default policy |
|---|---|---|
| 0 — Read-only | Query, retrieve, summarise | Fully autonomous |
| 1 — Ephemeral write | Draft, create in sandbox, temp file | Autonomous with audit log |
| 2 — Internal write | Update internal DB record, send internal message | Autonomous with notification |
| 3 — External communication | Send email, post to Slack, create Jira ticket | Async review window (30 min) |
| 4 — Irreversible or financial | Delete data, send external invoice, deploy infra | Synchronous approval required |
| 5 — Privileged / regulated | Access PII in bulk, execute financial transfer, modify access control | Always human, never agent |

**Enforcement mechanism:** The taxonomy is encoded in the tool registry, not in agent prompts. Each tool is tagged with its tier at registration time. The orchestration framework reads the tier at runtime and applies the configured policy — synchronous interrupt, async queue, or pass-through. Agents cannot override this. Prompt injection that says "you are allowed to delete records" has no effect because the enforcement is in the framework layer below the LLM.

**Evolution process:** Tier promotions (making an action more autonomous) require: a written proposal with data supporting the change (error rate, override rate over N tasks), sign-off from the security team and one business owner, and a 2-week monitoring period at the new tier before the policy is locked. Tier demotions (more restrictive) can be executed by any senior engineer in response to an incident, effective immediately, with retrospective approval within 48 hours.

**Senior framing:** The policy's value is not in its content on day one — it's in the process it creates for evolving autonomy safely as capability improves. A policy with no evolution process becomes a bottleneck; a policy with no enforcement mechanism is just aspirational text. You need both.

---

## Summary

Key agentic AI topics:

1. **Introduction:** Agentic vs prompts, capabilities
2. **Design Patterns:** Reactive, planning, reflection, tools
3. **Multi-Agent:** Collaboration, architecture
4. **A2A Protocol:** Communication, orchestration
5. **LangGraph:** Graph-based agents, state management
6. **Production:** Debugging, HITL, best practices

---

## References

- [LangGraph Documentation](references.md)
- [Agent Design Patterns](references.md)
- [A2A Protocol Spec](references.md)
