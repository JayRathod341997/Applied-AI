# Module 4: Agentic Systems - Quiz

## Instructions
Choose the best answer for each question. Answers and explanations are provided at the end.

---

## Questions

### Q1. What is the primary characteristic that distinguishes an AI agent from a standard LLM?
- A) Ability to generate text
- B) Autonomy to perceive, reason, act, and learn
- C) Access to the internet
- D) Larger context window

### Q2. In the ReAct pattern, what is the correct sequence of steps?
- A) Action → Observation → Thought → Final Answer
- B) Thought → Action → Observation → Repeat
- C) Observation → Thought → Action → Final Answer
- D) Thought → Observation → Action → Final Answer

### Q3. Which agent design pattern is best suited for tasks with clear, predictable steps and dependencies?
- A) ReAct
- B) Reflection
- C) Plan-and-Execute
- D) Tool Use

### Q4. What is the main advantage of the Reflection pattern?
- A) Faster execution
- B) Lower cost
- C) Higher output quality through self-critique
- D) Better tool selection

### Q5. In a multi-agent supervisor pattern, what is the role of the supervisor?
- A) Execute all tasks directly
- B) Delegate tasks to specialized worker agents
- C) Only monitor agent performance
- D) Replace failed agents

### Q6. Which of the following is NOT a standard A2A communication pattern?
- A) Request-Response
- B) Publish-Subscribe
- C) Broadcasting
- D) Streaming

### Q7. What is the purpose of the `correlation_id` in an A2A message?
- A) Encrypt the message
- B) Match responses to their original requests
- C) Prioritize message delivery
- D) Authenticate the sender

### Q8. In LangGraph, what is the primary purpose of StateGraph?
- A) Store conversation history
- B) Define the agent's workflow with nodes and edges
- C) Connect to external APIs
- D) Manage LLM API keys

### Q9. Which LangGraph feature enables human-in-the-loop workflows?
- A) `add_node()`
- B) `interrupt()`
- C) `compile()`
- D) `set_entry_point()`

### Q10. What is the autonomy level of an agent that acts within defined boundaries without human approval?
- A) Level 1
- B) Level 2
- C) Level 3
- D) Level 5

### Q11. In the debate pattern for multi-agent systems, what is the primary benefit?
- A) Faster execution
- B) Reduced cost
- C) Multiple perspectives leading to better solutions
- D) Simpler implementation

### Q12. What is the main challenge with the swarm pattern in multi-agent systems?
- A) Agents cannot communicate
- B) Aggregating and synthesizing independent outputs
- C) Agents always produce identical results
- D) It requires a central coordinator

### Q13. Which component of an AI agent is responsible for maintaining conversation context?
- A) Perception
- B) Memory
- C) Reasoning
- D) Action

### Q14. What is a key security concern when agents use tools?
- A) Tools are always slow
- B) Tool inputs can be manipulated for unauthorized actions
- C) Tools cannot be tested
- D) Tools always require authentication

### Q15. In LangGraph, what does the checkpointer provide?
- A) Faster execution
- B) State persistence and recovery
- C) Better LLM responses
- D) Tool validation

### Q16. Which pattern would you use when the path forward is uncertain and requires adaptive behavior?
- A) Plan-and-Execute
- B) ReAct
- C) Hierarchical
- D) Supervisor

### Q17. What is the purpose of tool descriptions in agent systems?
- A) Document the code
- B) Help the LLM decide which tool to use
- C) Validate tool outputs
- D) Encrypt tool inputs

### Q18. In the A2A protocol, what does the `intent` field specify?
- A) The message priority
- B) The type or purpose of the message
- C) The sender's identity
- D) The message encryption method

### Q19. What is the main disadvantage of the Reflection pattern?
- A) Poor output quality
- B) Increased latency and cost due to multiple LLM calls
- C) Cannot use tools
- D) Only works with specific LLMs

### Q20. Which LangGraph construct is used to define conditional routing between nodes?
- A) `add_edge()`
- B) `add_conditional_edges()`
- C) `set_entry_point()`
- D) `add_node()`

---

## Answers and Explanations

### A1. B - Autonomy to perceive, reason, act, and learn
**Explanation:** While LLMs generate text, agents add autonomy through the ability to perceive their environment, reason about actions, execute tools, and learn from feedback. This agency is the defining characteristic.

### A2. B - Thought → Action → Observation → Repeat
**Explanation:** ReAct interleaves reasoning (Thought) with action execution (Action) and result processing (Observation). This cycle repeats until the agent has enough information for a Final Answer.

### A3. C - Plan-and-Execute
**Explanation:** Plan-and-Execute is ideal for tasks with known steps and dependencies because it creates a complete plan upfront, then executes steps in order, passing results between dependent steps.

### A4. C - Higher output quality through self-critique
**Explanation:** Reflection improves quality by having the agent critique its own output and iteratively refine it. The trade-off is increased latency and cost, not speed or savings.

### A5. B - Delegate tasks to specialized worker agents
**Explanation:** The supervisor acts as a coordinator, analyzing requests and routing them to the most appropriate specialized agent, then collecting and presenting results.

### A6. C - Broadcasting
**Explanation:** The three standard A2A patterns are Request-Response (direct communication), Publish-Subscribe (event-driven), and Streaming (real-time data flow). Broadcasting is not a standard A2A pattern.

### A7. B - Match responses to their original requests
**Explanation:** The `correlation_id` links a response message back to the original request, enabling proper request-response matching in asynchronous communication.

### A8. B - Define the agent's workflow with nodes and edges
**Explanation:** StateGraph is LangGraph's core abstraction for defining workflows. Nodes represent processing steps, and edges define the flow between them, supporting cycles for iterative behavior.

### A9. B - `interrupt()`
**Explanation:** The `interrupt()` function pauses execution and waits for human input before continuing, enabling approval workflows and human oversight at critical decision points.

### A10. C - Level 3
**Explanation:** Level 3 (Conditional Autonomy) means the agent can act independently but only within predefined boundaries and constraints, without requiring per-action human approval.

### A11. C - Multiple perspectives leading to better solutions
**Explanation:** The debate pattern leverages diverse viewpoints by having agents argue different positions, leading to more thoroughly examined and balanced conclusions.

### A12. B - Aggregating and synthesizing independent outputs
**Explanation:** In the swarm pattern, agents work independently in parallel. The main challenge is combining their diverse outputs into a coherent, unified result.

### A13. B - Memory
**Explanation:** Memory maintains both short-term context (conversation history) and long-term knowledge (persistent information), enabling the agent to maintain continuity across interactions.

### A14. B - Tool inputs can be manipulated for unauthorized actions
**Explanation:** If an agent's tool inputs are influenced by malicious user input (prompt injection), it could execute unintended actions. Input validation and sandboxing are essential.

### A15. B - State persistence and recovery
**Explanation:** The checkpointer saves agent state at each step, enabling recovery from failures, conversation resumption, and human-in-the-loop workflows where execution pauses and resumes.

### A16. B - ReAct
**Explanation:** ReAct is designed for uncertain situations because it adapts based on observations at each step, rather than following a predetermined plan.

### A17. B - Help the LLM decide which tool to use
**Explanation:** Tool descriptions are included in the prompt so the LLM can understand each tool's purpose and select the appropriate one for the current context.

### A18. B - The type or purpose of the message
**Explanation:** The `intent` field categorizes the message (e.g., "query", "task", "response", "error", "status"), enabling receivers to route and process messages correctly.

### A19. B - Increased latency and cost due to multiple LLM calls
**Explanation:** Each reflection cycle requires additional LLM calls for critique and refinement, increasing both response time and API costs proportionally to the number of iterations.

### A20. B - `add_conditional_edges()`
**Explanation:** `add_conditional_edges()` allows dynamic routing based on the current state, enabling the graph to choose different paths at runtime based on agent decisions or conditions.


---

## Bonus: Senior / JD-Aligned Questions (Multi-Agent & Autonomous Workflows)

> Self-contained — answer is shown directly after each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. What is the strongest justification for a multi-agent design over a single agent?

A) It always runs faster  
B) The task decomposes into specialized roles or parallelizable subtasks needing separation of concerns  
C) It uses fewer tokens  
D) It removes the need for evaluation  

**Answer: B** — multi-agent pays off when specialization or parallelism is real; otherwise the coordination overhead is pure cost.

### BQ2. For an autonomous agent that can take consequential actions in a regulated domain, which control matters most?

A) A larger context window  
B) Bounded autonomy: tool allow-lists, human-in-the-loop approval, and a full audit log  
C) A higher temperature  
D) More agents  

**Answer: B** — consequential actions require approval gates, least-privilege tools, and auditability.

### BQ3. When is a deterministic chain preferable to an agent?

A) Never  
B) When the path is known and static — it is cheaper, faster, and predictable  
C) Only when there are no tools  
D) Only for image tasks  

**Answer: B** — if you can pre-define the flow, a chain beats an agent on cost, latency, and predictability.

### BQ4. A coordinator that delegates subtasks to specialist agents is which pattern?

A) Bag-of-words  
B) Supervisor / orchestrator-worker  
C) Map-reduce only  
D) Single-shot prompting  

**Answer: B** — a supervisor routes work to specialized workers and aggregates results.

### BQ5. Which metric set best evaluates an agent?

A) Accuracy alone  
B) Task success rate, tool-call correctness, trajectory/steps, and cost  
C) Token count only  
D) Lines of code  

**Answer: B** — agents need outcome *and* process metrics, including how efficiently they got there.
