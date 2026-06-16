# Module 6: LangGraph Deep Dive — Quiz

## Instructions
Choose the best answer for each question. Answers and explanations are provided at the end of each question.

---

## Questions

### Q1: What is the primary purpose of LangGraph?

A) To replace LangChain entirely  
B) To build stateful, multi-actor applications with LLMs using graph-based workflows  
C) To provide a UI for LLM applications  
D) To optimize LLM inference speed  

**Answer:** B  
**Explanation:** LangGraph is designed for building stateful, multi-actor applications using directed graphs. It extends LangChain with cycle support, explicit state management, and human-in-the-loop capabilities.

---

### Q2: Which Python construct is used to define state in LangGraph?

A) `dataclass`  
B) `NamedTuple`  
C) `TypedDict`  
D) `pydantic.BaseModel`  

**Answer:** C  
**Explanation:** LangGraph uses `TypedDict` to define the state schema. Each key in the TypedDict represents a piece of data that flows through the graph.

---

### Q3: What does `operator.add` do when used as a state reducer?

A) Adds numeric values together  
B) Concatenates strings  
C) Appends new values to existing lists  
D) Merges dictionaries  

**Answer:** C  
**Explanation:** When used with `Annotated[list, operator.add]`, the reducer appends new list values to the existing list instead of overwriting it. This is essential for accumulating message history.

---

### Q4: What is the difference between `add_edge()` and `add_conditional_edges()`?

A) `add_edge()` is faster  
B) `add_conditional_edges()` uses a routing function to dynamically choose the next node  
C) `add_edge()` supports cycles, `add_conditional_edges()` does not  
D) There is no difference  

**Answer:** B  
**Explanation:** `add_edge()` creates a fixed transition from one node to another. `add_conditional_edges()` uses a routing function that examines the current state and returns the next node dynamically.

---

### Q5: What does the `END` constant represent?

A) An error state  
B) The termination point of the graph  
C) A special node for logging  
D) The entry point of the graph  

**Answer:** B  
**Explanation:** `END` is a sentinel constant that marks where graph execution terminates. Nodes that should conclude the workflow must have an edge pointing to `END`.

---

### Q6: Which method compiles a StateGraph into an executable application?

A) `graph.build()`  
B) `graph.execute()`  
C) `graph.compile()`  
D) `graph.run()`  

**Answer:** C  
**Explanation:** `graph.compile()` validates the graph structure and produces a `CompiledGraph` that can be invoked with `app.invoke()`.

---

### Q7: What is a DAG in the context of LangGraph?

A) A graph with cycles  
B) A directed acyclic graph with no loops  
C) A disconnected graph  
D) A graph with multiple entry points  

**Answer:** B  
**Explanation:** A DAG (Directed Acyclic Graph) has no cycles — execution flows in one direction from entry to exit. No node can be visited twice in a single execution.

---

### Q8: Why are cyclic graphs important for agents?

A) They improve performance  
B) They enable iterative reasoning (think → act → observe → repeat)  
C) They reduce memory usage  
D) They simplify the code  

**Answer:** B  
**Explanation:** Cycles enable agents to perform iterative reasoning loops like ReAct, where the agent reasons, acts, observes results, and reasons again.

---

### Q9: Which checkpointer is best suited for production multi-tenant applications?

A) `MemorySaver`  
B) `SqliteSaver`  
C) `PostgresSaver`  
D) None of the above  

**Answer:** C  
**Explanation:** `PostgresSaver` provides durability, concurrency support, and transactional guarantees needed for production multi-tenant applications.

---

### Q10: What happens when you call `app.invoke(None, config=config)` after an interrupt?

A) The graph restarts from the beginning  
B) The graph resumes from the last checkpoint  
C) An error is raised  
D) The graph skips to the end  

**Answer:** B  
**Explanation:** Passing `None` as input tells LangGraph to resume from the last saved checkpoint instead of starting fresh with new input.

---

### Q11: How do you pause execution before a specific node?

A) Use `interrupt()` inside the node  
B) Use `interrupt_before=["node_name"]` during compilation  
C) Use `graph.pause("node_name")`  
D) Use `app.stop("node_name")`  

**Answer:** B  
**Explanation:** `interrupt_before=["node_name"]` in `graph.compile()` pauses execution before the specified node runs. This is the breakpoint-style interrupt pattern.

---

### Q12: What does `app.get_state(config)` return?

A) The initial state  
B) The current state snapshot at the last checkpoint  
C) The state history  
D) The graph structure  

**Answer:** B  
**Explanation:** `get_state()` returns the current state snapshot, including the state values, next nodes to execute, and checkpoint metadata.

---

### Q13: Which stream mode shows only the state changes from each node?

A) `"values"`  
B) `"updates"`  
C) `"messages"`  
D) `"events"`  

**Answer:** B  
**Explanation:** `stream_mode="updates"` shows only what each node changed (the delta), while `"values"` shows the full state after each step.

---

### Q14: What is the purpose of the `Send` API in LangGraph?

A) To send messages to external APIs  
B) To enable parallel execution of nodes  
C) To send emails  
D) To log events  

**Answer:** B  
**Explanation:** The `Send` API enables fan-out patterns where multiple nodes execute in parallel with independent state copies.

---

### Q15: How do you add a node to a StateGraph?

A) `graph.add_node("name", function)`  
B) `graph.node("name", function)`  
C) `graph.register("name", function)`  
D) `graph.define("name", function)`  

**Answer:** A  
**Explanation:** `graph.add_node("name", function)` registers a node with a given name and the function that implements its logic.

---

### Q16: What type hint can you use for type-safe conditional routing?

A) `Union`  
B) `Literal`  
C) `Optional`  
D) `Any`  

**Answer:** B  
**Explanation:** `Literal["option_a", "option_b"]` provides type-safe routing where the IDE can autocomplete valid route names and catch typos at development time.

---

### Q17: What is a subgraph in LangGraph?

A) A disconnected component  
B) A compiled graph nested inside another graph  
C) A backup copy of the graph  
D) A visualization of the graph  

**Answer:** B  
**Explanation:** Subgraphs allow nesting compiled graphs within other graphs, enabling modular, reusable workflows and hierarchical agent architectures.

---

### Q18: How does the `interrupt()` function differ from `interrupt_before`?

A) `interrupt()` pauses inside a node; `interrupt_before` pauses before a node  
B) `interrupt()` is faster  
C) `interrupt_before` requires a checkpointer; `interrupt()` does not  
D) They are identical  

**Answer:** A  
**Explanation:** `interrupt()` is called inside a node function and pauses execution at that exact point, waiting for a response value. `interrupt_before` pauses before the entire node executes.

---

### Q19: What is the purpose of `app.get_state_history(config)`?

A) To get the graph structure  
B) To list all saved checkpoints for time travel  
C) To get the current state  
D) To clear the state  

**Answer:** B  
**Explanation:** `get_state_history()` returns all historical checkpoints for a thread, enabling time travel — replaying or forking execution from any past point.

---

### Q20: Which pattern is best for a supervisor-based multi-agent system?

A) All agents run in parallel  
B) A central node routes to specialized agents using conditional edges  
C) Each agent runs as a separate graph  
D) Agents communicate through external queues  

**Answer:** B  
**Explanation:** In the supervisor pattern, a central routing node examines the state and uses conditional edges to dispatch work to specialized agents, then collects results back.


---

## Bonus: Senior / JD-Aligned Questions (Stateful Orchestration & Durable Agents)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. What is the main reason to choose LangGraph over a linear chain?

A) It is always cheaper  
B) You need branching, loops, and shared state with controllable, persistent execution  
C) It removes the need for an LLM  
D) It only does image generation  

**Answer: B** — LangGraph models stateful, branching, cyclic workflows that a linear chain cannot.

### BQ2. How is human-in-the-loop achieved in LangGraph?

A) By raising the temperature  
B) A checkpointer plus an interrupt before/after a node, resuming on human approval  
C) By disabling tools  
D) It is not possible  

**Answer: B** — the graph persists state, pauses at an interrupt, and resumes after a human approves/edits.

### BQ3. What does a checkpointer enable?

A) Faster token generation only  
B) Durable, resumable per-thread state: crash recovery, long-running workflows, and audit/replay  
C) Cheaper embeddings  
D) Automatic fine-tuning  

**Answer: B** — checkpointers persist state so workflows survive crashes and can be replayed/audited.

### BQ4. Best way to prevent state/context bloat in a long graph?

A) Inline every artifact into state  
B) Typed state + reducers + trim/summarize messages + store large artifacts by reference  
C) Never persist state  
D) Use a single global variable  

**Answer: B** — a typed schema with reducers and summarization keeps state bounded.

### BQ5. When is LangGraph overkill?

A) For a simple, static, linear pipeline with no branching or state  
B) For any workflow with loops  
C) Whenever you need persistence  
D) For human-in-the-loop flows  

**Answer: A** — a plain chain is simpler and cheaper when there is no branching, looping, or state.
