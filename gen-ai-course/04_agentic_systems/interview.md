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
