# Module 6: LangGraph Deep Dive — Interview Questions

## Table of Contents
- [Beginner (1-10)](#beginner)
- [Intermediate (11-20)](#intermediate)
- [Advanced (21-28)](#advanced)

---

## Beginner

### Q1: What is LangGraph and how does it differ from LangChain?

**Answer:**
LangGraph is a library built on top of LangChain designed for building **stateful, multi-actor applications** with LLMs. The key differences are:

| Aspect | LangChain | LangGraph |
|--------|-----------|-----------|
| Workflow model | Sequential chains / DAGs | Directed graphs with cycles |
| State management | Implicit via memory modules | Explicit TypedDict state |
| Cycles | Not supported | Native support |
| Human-in-the-loop | Manual implementation | First-class `interrupt()` support |
| Persistence | External | Built-in checkpointers |

LangChain is ideal for linear, one-shot workflows. LangGraph is designed for iterative, stateful agent loops.

---

### Q2: What are the three core components of a LangGraph StateGraph?

**Answer:**
1. **State**: A `TypedDict` that defines the data schema flowing through the graph. It carries information between nodes and persists across executions.
2. **Nodes**: Python functions that receive the current state, perform computation, and return a dictionary of state updates.
3. **Edges**: Connections between nodes that control execution flow. They can be deterministic (normal edges) or dynamic (conditional edges).

---

### Q3: How do you define state in LangGraph?

**Answer:**
State is defined using Python's `TypedDict`:

```python
from typing import TypedDict, Annotated, List
import operator

class AgentState(TypedDict):
    messages: Annotated[List[str], operator.add]  # Appends new values
    current_step: str                              # Overwrites
    iteration_count: int                           # Overwrites
```

The `Annotated` type with a reducer (like `operator.add`) controls how node updates merge with existing state values.

---

### Q4: What is a node in LangGraph?

**Answer:**
A node is a Python function that:
- Receives the current state as input
- Performs some computation (LLM call, tool execution, data processing)
- Returns a dictionary of state updates (not the full state)

```python
def research_node(state: AgentState) -> dict:
    result = perform_research(state["query"])
    return {
        "documents": result,
        "current_step": "research_done"
    }
```

Nodes only return the keys they want to update. Unchanged keys retain their values.

---

### Q5: What is the difference between a normal edge and a conditional edge?

**Answer:**
- **Normal edge** (`add_edge`): Always transitions from node A to node B. Deterministic, fixed routing.
- **Conditional edge** (`add_conditional_edges`): Uses a routing function that examines the current state and returns the next node dynamically. Enables branching logic.

```python
# Normal edge: always goes from A to B
graph.add_edge("analyze", "summarize")

# Conditional edge: chooses next node based on state
def route(state):
    return "approve" if state["confidence"] > 0.8 else "review"

graph.add_conditional_edges("evaluate", route, {
    "approve": "finalize",
    "review": "human_review"
})
```

---

### Q6: What does `END` represent in LangGraph?

**Answer:**
`END` is a special sentinel constant that marks the termination point of a graph. When execution reaches `END`, the graph stops and returns the final state. Any node that should conclude the workflow must have an edge pointing to `END`.

```python
from langgraph.graph import END

graph.add_edge("final_node", END)  # Graph terminates after final_node
```

---

### Q7: How do you compile and run a LangGraph?

**Answer:**
```python
# 1. Build the graph
graph = StateGraph(MyState)
graph.add_node("step1", node1_func)
graph.add_node("step2", node2_func)
graph.set_entry_point("step1")
graph.add_edge("step1", "step2")
graph.add_edge("step2", END)

# 2. Compile
app = graph.compile()

# 3. Run
result = app.invoke({"key": "value"})
```

Compilation validates the graph structure (all nodes reachable, no orphaned nodes) and produces an executable `CompiledGraph`.

---

### Q8: What is a DAG in the context of LangGraph?

**Answer:**
A DAG (Directed Acyclic Graph) is a graph with no cycles — execution flows in one direction from entry to exit with no loops. Every edge points forward, and no node can be visited twice in a single execution.

DAGs are suitable for:
- Data processing pipelines
- Sequential transformation chains
- Fixed multi-step workflows

---

### Q9: Why do agents need cyclic graphs?

**Answer:**
Agents need cycles because they perform **iterative reasoning**: think → act → observe → think again. Without cycles, an agent can only take one action and must stop. Cycles enable:

- ReAct loops (reasoning and acting repeatedly)
- Retry mechanisms on failure
- Iterative refinement of outputs
- Multi-turn conversations
- Plan-and-execute patterns

---

### Q10: What is a state reducer in LangGraph?

**Answer:**
A state reducer is a function that determines how a node's returned value merges with the existing state value for that key. By default, values are overwritten. Using `Annotated` with a reducer changes this behavior:

```python
class State(TypedDict):
    messages: Annotated[list, operator.add]  # Append
    summary: str                              # Overwrite (default)
```

Common reducers: `operator.add` (append), `operator.ior` (merge sets), `max`/`min`, custom functions.

---

## Intermediate

### Q11: How does conditional routing work in LangGraph?

**Answer:**
Conditional routing uses `add_conditional_edges()` with a routing function:

```python
def router(state: AgentState) -> str:
    if state["intent"] == "purchase":
        return "checkout"
    elif state["intent"] == "support":
        return "help_desk"
    return "general"

graph.add_conditional_edges(
    "classify",
    router,
    {
        "checkout": "checkout_node",
        "help_desk": "support_node",
        "general": "general_node",
    }
)
```

The routing function receives the full state and returns a string key. That key is looked up in the routing map to determine the next node. The return type can use `Literal` for type safety.

---

### Q12: How do you implement a ReAct agent loop in LangGraph?

**Answer:**
```python
class ReActState(TypedDict):
    messages: Annotated[list, operator.add]
    steps: int

def agent(state: ReActState) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response], "steps": state["steps"] + 1}

def tools(state: ReActState) -> dict:
    # Execute tool calls from the last LLM message
    result = execute_tool(state["messages"][-1])
    return {"messages": [result]}

def should_continue(state: ReActState) -> str:
    if state["steps"] >= 5:
        return END
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END

graph = StateGraph(ReActState)
graph.add_node("agent", agent)
graph.add_node("tools", tools)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")
```

The cycle `agent → tools → agent` enables iterative reasoning.

---

### Q13: Explain the human-in-the-loop interrupt pattern.

**Answer:**
Human-in-the-loop (HITL) allows pausing graph execution for human review. There are two approaches:

**Approach 1: `interrupt_before` / `interrupt_after`**
```python
app = graph.compile(
    checkpointer=memory,
    interrupt_before=["approval_node"]
)
```
Execution pauses before the specified node. The application can inspect state, and a human can decide to continue or modify state.

**Approach 2: `interrupt()` function inside a node**
```python
from langgraph.types import interrupt

def approval_node(state):
    decision = interrupt({"question": "Approve?", "context": state["analysis"]})
    return {"approved": decision["approved"]}
```
This pauses inside the node and waits for a response value.

Both require a checkpointer to persist state during the pause.

---

### Q14: How do you resume a graph after an interrupt?

**Answer:**
```python
config = {"configurable": {"thread_id": "session-1"}}

# First run: stops at interrupt
result = app.invoke(initial_state, config=config)

# Inspect state
snapshot = app.get_state(config)
print(f"Paused at: {snapshot.next}")

# Optionally update state with human feedback
app.update_state(config, {"human_approval": True})

# Resume: pass None as input
result = app.invoke(None, config=config)
```

Passing `None` as input tells LangGraph to resume from the last checkpoint instead of starting fresh.

---

### Q15: What checkpointers are available in LangGraph and when would you use each?

**Answer:**

| Checkpointer | Storage | Concurrency | Use Case |
|-------------|---------|-------------|----------|
| `MemorySaver` | In-memory | Single process | Development, testing |
| `SqliteSaver` | File-based | Single process | Small apps, local prototypes |
| `PostgresSaver` | PostgreSQL database | Multi-process | Production, multi-tenant apps |
| `RedisSaver` | Redis | Multi-process | High-throughput, low-latency |

For production, `PostgresSaver` is the most common choice due to durability, concurrency support, and transactional guarantees.

---

### Q16: How does state merging work when multiple nodes update the same key?

**Answer:**
State merging depends on the reducer defined for each key:

- **No reducer (default)**: The new value overwrites the old value entirely.
- **`operator.add`**: New values are appended/extended to the existing list.
- **Custom reducer**: The reducer function receives `(existing_value, new_value)` and returns the merged result.

If multiple nodes in the same step update the same key, the last writer wins (for overwrite mode) or the reducer combines them (for reducer mode).

```python
class State(TypedDict):
    items: Annotated[list, operator.add]

def node_a(state):
    return {"items": ["a"]}  # Appends "a"

def node_b(state):
    return {"items": ["b"]}  # Appends "b"

# Result: items = [...existing, "a", "b"]
```

---

### Q17: How do you stream LangGraph execution?

**Answer:**
```python
# Stream mode: "updates" — shows only what each node changed
for event in app.stream(initial_state, stream_mode="updates"):
    print(event)
    # {'research': {'documents': [...]}}
    # {'summarize': {'summary': '...'}}

# Stream mode: "values" — shows full state after each step
for event in app.stream(initial_state, stream_mode="values"):
    print(event)
    # Full state dict after each node

# Stream mode: "messages" — streams LLM token-by-token
for event in app.stream(initial_state, stream_mode="messages"):
    print(event)
```

Streaming is essential for real-time UIs and debugging complex graphs.

---

### Q18: How do you handle errors in LangGraph nodes?

**Answer:**
```python
def safe_node(state: AgentState) -> dict:
    try:
        result = risky_operation(state["query"])
        return {"result": result, "error": None}
    except Exception as e:
        return {"error": str(e), "retry_count": state.get("retry_count", 0) + 1}

def route_after_error(state: AgentState) -> str:
    if state.get("error") and state.get("retry_count", 0) < 3:
        return "retry"
    return "error_handler"

graph.add_conditional_edges("process", route_after_error, {
    "retry": "process",
    "error_handler": "handle_error"
})
```

Error handling is implemented through conditional routing: catch exceptions in nodes, track retry counts, and route to retry or error handler nodes.

---

### Q19: What is the purpose of `set_entry_point()`?

**Answer:**
`set_entry_point()` defines which node executes first when the graph is invoked. Every graph must have exactly one entry point. Without it, compilation fails because LangGraph cannot determine where to start.

```python
graph.set_entry_point("first_node")
```

You can also use `set_conditional_entry_point()` for dynamic entry points based on input state.

---

### Q20: How do you visualize a LangGraph?

**Answer:**
```python
# Get Mermaid diagram code
mermaid = app.get_graph().draw_mermaid()
print(mermaid)

# Save as PNG (requires graphviz)
app.get_graph().draw_mermaid_png(output_file_path="graph.png")
```

Visualization helps debug complex routing, verify edge connections, and communicate architecture to stakeholders.

---

## Advanced

### Q21: Explain how LangGraph's checkpoint system enables time travel.

**Answer:**
Every time a node completes, LangGraph saves a checkpoint containing the full state, metadata, and a unique checkpoint ID. This creates a linked history of all state transitions.

```python
# Get all historical checkpoints
history = list(app.get_state_history(config))

# Pick a checkpoint to replay from
target = history[3]
replay_config = target.config

# Resume from that point
result = app.invoke(None, config=replay_config)
```

Time travel works because:
1. Each checkpoint is immutable and independently addressable
2. The checkpointer stores the complete state at each step
3. `invoke(None, config=old_config)` resumes from that checkpoint as if the graph had just reached that point
4. You can fork execution from any checkpoint, creating parallel branches

This is useful for debugging, auditing, and allowing users to "undo" actions.

---

### Q22: How would you implement a multi-agent collaboration system in LangGraph?

**Answer:**
Using a supervisor pattern with shared state:

```python
class MultiAgentState(TypedDict):
    task: str
    research_result: str
    writing_result: str
    review_feedback: str
    messages: Annotated[list, operator.add]
    next: str

def supervisor(state: MultiAgentState) -> dict:
    # Decide which agent to call next
    if not state["research_result"]:
        return {"next": "researcher"}
    elif not state["writing_result"]:
        return {"next": "writer"}
    elif not state["review_feedback"]:
        return {"next": "reviewer"}
    return {"next": END}

def researcher(state: MultiAgentState) -> dict:
    result = perform_research(state["task"])
    return {"research_result": result, "next": ""}

def writer(state: MultiAgentState) -> dict:
    draft = write_content(state["research_result"])
    return {"writing_result": draft, "next": ""}

def reviewer(state: MultiAgentState) -> dict:
    feedback = review_content(state["writing_result"])
    return {"review_feedback": feedback, "next": ""}

graph = StateGraph(MultiAgentState)
graph.add_node("supervisor", supervisor)
graph.add_node("researcher", researcher)
graph.add_node("writer", writer)
graph.add_node("reviewer", reviewer)

graph.set_entry_point("supervisor")
graph.add_conditional_edges("supervisor", lambda s: s["next"], {
    "researcher": "researcher",
    "writer": "writer",
    "reviewer": "reviewer",
    END: END,
})
graph.add_edge("researcher", "supervisor")
graph.add_edge("writer", "supervisor")
graph.add_edge("reviewer", "supervisor")
```

The supervisor routes to specialized agents, and each agent returns control to the supervisor.

---

### Q23: How do you implement a reflection/improvement loop in LangGraph?

**Answer:**
```python
class ReflectionState(TypedDict):
    draft: str
    feedback: str
    iteration: int
    final: str

def generate(state: ReflectionState) -> dict:
    draft = llm.invoke(f"Write about: {state['topic']}")
    return {"draft": draft.content, "iteration": 0}

def reflect(state: ReflectionState) -> dict:
    feedback = llm.invoke(f"Critique this draft: {state['draft']}")
    return {"feedback": feedback.content}

def improve(state: ReflectionState) -> dict:
    improved = llm.invoke(
        f"Improve this draft based on feedback.\n"
        f"Draft: {state['draft']}\nFeedback: {state['feedback']}"
    )
    return {"draft": improved.content, "iteration": state["iteration"] + 1}

def should_continue(state: ReflectionState) -> str:
    if state["iteration"] >= 3:
        return "finalize"
    return "reflect"

graph = StateGraph(ReflectionState)
graph.add_node("generate", generate)
graph.add_node("reflect", reflect)
graph.add_node("improve", improve)
graph.add_node("finalize", lambda s: {"final": s["draft"]})

graph.set_entry_point("generate")
graph.add_edge("generate", "reflect")
graph.add_conditional_edges("reflect", should_continue, {
    "reflect": "improve",
    "finalize": "finalize"
})
graph.add_edge("improve", "reflect")
graph.add_edge("finalize", END)
```

The cycle `reflect → improve → reflect` enables iterative quality improvement.

---

### Q24: How do you handle parallel node execution in LangGraph?

**Answer:**
LangGraph supports parallel execution through fan-out/fan-in patterns using a shared state:

```python
class ParallelState(TypedDict):
    query: str
    result_a: str
    result_b: str
    combined: str

def process_a(state: ParallelState) -> dict:
    return {"result_a": f"Analysis A of: {state['query']}"}

def process_b(state: ParallelState) -> dict:
    return {"result_b": f"Analysis B of: {state['query']}"}

def combine(state: ParallelState) -> dict:
    return {"combined": f"{state['result_a']} | {state['result_b']}"}

graph = StateGraph(ParallelState)
graph.add_node("a", process_a)
graph.add_node("b", process_b)
graph.add_node("combine", combine)

graph.set_entry_point("a")
# Both a and b run from entry (fan-out via send API)
# For true parallelism, use the Send API:
from langgraph.types import Send

def fan_out(state: ParallelState):
    return [Send("a", state), Send("b", state)]

graph.add_conditional_edges("__start__", fan_out, {"a": "a", "b": "b"})
graph.add_edge("a", "combine")
graph.add_edge("b", "combine")
graph.add_edge("combine", END)
```

The `Send` API enables true parallel execution of nodes with independent state copies.

---

### Q25: How do you implement subgraphs in LangGraph?

**Answer:**
Subgraphs allow nesting graphs within graphs for modularity:

```python
# Inner graph: research sub-workflow
research_graph = StateGraph(ResearchState)
research_graph.add_node("search", search_node)
research_graph.add_node("analyze", analyze_node)
research_graph.set_entry_point("search")
research_graph.add_edge("search", "analyze")
research_graph.add_edge("analyze", END)

# Outer graph: main workflow
class MainState(TypedDict):
    query: str
    research_output: str
    final_report: str

main_graph = StateGraph(MainState)
main_graph.add_node("research", research_graph.compile())
main_graph.add_node("write", write_node)
main_graph.set_entry_point("research")
main_graph.add_edge("research", "write")
main_graph.add_edge("write", END)
```

Subgraphs enable:
- Modular, reusable workflows
- Independent testing of sub-components
- Hierarchical agent architectures

---

### Q26: How do you implement a plan-and-execute pattern?

**Answer:**
```python
class PlanExecuteState(TypedDict):
    task: str
    plan: list
    results: Annotated[list, operator.add]
    current_step: int
    final_answer: str

def planner(state: PlanExecuteState) -> dict:
    plan = llm.invoke(f"Create a step-by-step plan for: {state['task']}")
    return {"plan": parse_plan(plan.content), "current_step": 0}

def executor(state: PlanExecuteState) -> dict:
    step = state["plan"][state["current_step"]]
    result = execute_step(step)
    return {
        "results": [result],
        "current_step": state["current_step"] + 1
    }

def replanner(state: PlanExecuteState) -> dict:
    if state["current_step"] >= len(state["plan"]):
        return {"final_answer": synthesize(state["results"])}
    return {}  # Continue executing

def route(state: PlanExecuteState) -> str:
    if state.get("final_answer"):
        return END
    if state["current_step"] >= len(state["plan"]):
        return "planner"  # Re-plan if needed
    return "executor"

graph = StateGraph(PlanExecuteState)
graph.add_node("planner", planner)
graph.add_node("executor", executor)
graph.add_node("replanner", replanner)

graph.set_entry_point("planner")
graph.add_edge("planner", "executor")
graph.add_conditional_edges("executor", route, {
    "executor": "executor",
    "planner": "planner",
    END: END
})
```

---

### Q27: How do you manage conversation memory across multiple sessions?

**Answer:**
```python
from langgraph.checkpoint.postgres import PostgresSaver

# Use thread_id per conversation session
def get_config(user_id: str, session_id: str) -> dict:
    return {"configurable": {
        "thread_id": f"{user_id}-{session_id}",
    }}

# Use namespace for cross-session memory
def get_cross_session_config(user_id: str) -> dict:
    return {"configurable": {
        "thread_id": f"{user_id}-memory",
        "checkpoint_ns": "long_term_memory"
    }}

app = graph.compile(checkpointer=PostgresSaver(conn))

# Session-specific memory
result = app.invoke(state, config=get_config("user1", "session-1"))

# Access long-term memory
memory_state = app.get_state(get_cross_session_config("user1"))
```

Key strategies:
- **Thread ID per session**: Isolates conversations
- **Namespace separation**: Separates short-term and long-term memory
- **External vector store**: For semantic memory retrieval across sessions
- **Summary nodes**: Periodically summarize conversation history

---

### Q28: What are the performance considerations for production LangGraph deployments?

**Answer:**

| Concern | Solution |
|---------|----------|
| State size | Minimize state schema; only store necessary data |
| Checkpoint overhead | Use `PostgresSaver` with connection pooling; batch writes |
| LLM latency | Stream responses; cache common results; use smaller models for routing |
| Concurrency | Use async nodes (`async def`); deploy with FastAPI + uvicorn |
| Memory leaks | Set max iterations; use TTL on checkpoints |
| Error recovery | Implement retry nodes; use circuit breakers for external APIs |
| Observability | Stream events to logging; use LangSmith for tracing |
| Scaling | Horizontal scaling with shared database checkpointer; load balance across workers |

```python
# Async node example
async def async_research_node(state: AgentState) -> dict:
    result = await llm.ainvoke(state["messages"])
    return {"messages": [result]}

# Production compilation
app = graph.compile(
    checkpointer=PostgresSaver(pool),
    interrupt_before=["approval"],
)
```


---

## Senior Deep Dive: Stateful Orchestration, Human-in-the-Loop & Durable Agents

> *The JD wants autonomous workflows and copilots that are controllable in production. LangGraph's value is exactly that — interviewers probe state, persistence, and human oversight.*

### SQ1: What does LangGraph add over a linear chain or a simple agent loop?

**Answer:** LangGraph provides an explicit **graph of nodes and edges over shared state**, with support for **conditional and cyclic** flows, controllability, and **persistence/checkpointing**. Where a linear chain moves in a straight line and a simple agent loop is an opaque while-construct, LangGraph lets you model real workflows — branches, loops, retries, parallel fan-out — as a first-class structure you can inspect, pause, and resume. The **shared state** object passes through every node, making the full execution context visible at each step rather than hidden inside a callback chain. **Trade-off:** LangGraph is more expressive and controllable than a chain, but it demands more upfront design — defining the state schema, the nodes, and the edges. That investment is justified when the flow has real branching or stateful behaviour; for a straight-line pipeline it is unnecessary complexity.

### SQ2: How do you implement human-in-the-loop with LangGraph?

**Answer:** LangGraph implements human-in-the-loop through a **checkpointer** combined with an **interrupt** placed before or after a specific node. When execution reaches the interrupt point the graph serialises its entire state to the checkpointer backend (in-memory, SQLite, or **Postgres**), pauses, and surfaces the proposed action — along with the full reasoning context — to a human reviewer. The reviewer can approve, reject, or edit the state, and then the graph **resumes** from exactly where it stopped. This pattern is essential for any high-risk or state-changing action in a regulated context: a credit decision, a customer communication, or a tool call that writes to a production system. **Trade-off:** a human gate adds latency proportional to the reviewer's response time, which can be seconds to hours; but that latency is the control mechanism that makes autonomy acceptable for consequential decisions — you tier the gate requirement by the risk level of the action being approved.

### SQ3: What does durable/resumable execution buy you, and how is it implemented?

**Answer:** A **checkpointer** persists the complete graph state **per thread** (keyed by a thread ID) so that execution can survive process crashes, span long real-world time horizons, support **time-travel/replay** for debugging, and produce a full **audit trail** of every state transition. Supported backends range from in-memory (development only) to **SQLite** (single-process) to **Postgres** (production, multi-worker). Because every node transition writes a checkpoint, you can call `app.get_state_history(config)` to replay any prior execution, fork from a historical state, or hand an inspector the exact inputs and outputs at every step. **Trade-off:** persistence adds infrastructure (a database) and a small per-step write latency; in return you gain reliability, replay capability, and auditability — properties that are usually mandatory for production risk workflows where regulators or internal audit may need to reconstruct why a decision was made.

### SQ4: How do you manage state and avoid context bloat in a long graph?

**Answer:** The foundation is a **typed state schema** — a `TypedDict` or Pydantic model — that makes every field explicit and prevents arbitrary keys from accumulating. **Reducers** (the `Annotated[list, operator.add]` pattern) control how updates are merged: append vs overwrite, so you never accidentally duplicate message history. For long-running conversations, **trim or summarize** the message list at a dedicated summary node rather than letting it grow unboundedly; LangGraph's `trim_messages` utility or a custom LLM-based summarizer both work. **Large artifacts** — retrieved documents, code blobs, binary data — should be stored externally and referenced in state by an identifier, not inlined. **Trade-off:** aggressive trimming saves tokens and latency but risks dropping context the graph needs later; the right balance is task-specific, and you should measure retrieval quality and answer faithfulness before tightening trim thresholds.

### SQ5: When is LangGraph the wrong tool?

**Answer:** LangGraph is the wrong tool for **simple linear flows** that have no branching, no loops, and no need for persistent state. If your pipeline is "call embedding → query vector store → call LLM → return answer," a plain LCEL chain or even a direct SDK call is simpler, faster to write, easier to debug, and cheaper to run. Reaching for LangGraph there adds a state schema, node definitions, edge wiring, and a compile step with no payoff. The senior signal is recommending the least dynamic design that actually solves the problem. **Trade-off:** controllability and expressiveness vs simplicity — match the tool to the actual shape of the flow, not to the complexity you imagine might be needed later.
