# Quiz: LangGraph Framework

## Multiple Choice Questions

### Question 1
What are the three core components of LangGraph?

A) State, Edges, Functions
B) Nodes, Edges, State
C) Messages, Chains, Agents
D) Input, Processing, Output

**Answer: B**

---

### Question 2
What is the main advantage of LangGraph over LangChain?

A) Simpler API
B) Support for cycles in workflows
C) Better performance
D) More integrations

**Answer: B**

---

### Question 3
In LangGraph, what do "Nodes" represent?

A) Data storage locations
B) Computational steps in the graph
C) External API endpoints
D) User interface elements

**Answer: B**

---

### Question 4
What is the purpose of "Edges" in LangGraph?

A) Store data
B) Define flow control between nodes
C) Connect to databases
D) Create user interfaces

**Answer: B**

---

### Question 5
Which method is used to create a new state graph?

A) Graph()
B) StateGraph()
C) create_graph()
D) new_graph()

**Answer: B**

---

### Question 6
What is conditional routing in LangGraph?

A) Random path selection
B) Choosing next node based on state
C) Always using the same path
D) Skipping nodes

**Answer: B**

---

### Question 7
How does LangGraph handle persistent state?

A) Only through external databases
B) Through state that flows through the graph
C) Through global variables
D) State is not supported

**Answer: B**

---

### Question 8
What is the purpose of the `interrupt()` function?

A) Stop the entire application
B) Pause execution for human input
C) Handle errors
D) Clear memory

**Answer: B**

---

### Question 9
Which pattern allows agents to review and improve their outputs?

A) Tool pattern
B) Reflection pattern
C) Planning pattern
D) Memory pattern

**Answer: B**

---

### Question 10
What is ReAct pattern?

A) React to user input
B) Reasoning + Acting in cycles
C) Response generation
D) Action-based routing

**Answer: B**

---

## True or False

### Question 11
LangGraph supports cycles in the workflow graph.

**Answer: True**

---

### Question 12
Nodes in LangGraph must always return the complete state.

**Answer: False** - Nodes return partial state updates

---

### Question 13
Human-in-the-loop requires using the interrupt function.

**Answer: True**

---

### Question 14
Memory in LangGraph can only be short-term.

**Answer: False** - Both short-term and long-term memory supported

---

### Question 15
Conditional edges use functions to determine next node.

**Answer: True**

---

## Short Answer Questions

### Question 16
Name three types of edges in LangGraph.

**Answer:**
1. Normal edges (direct transitions)
2. Conditional edges (choice-based transitions)
3. Entry point edges

---

### Question 17
What is the difference between short-term and long-term memory in LangGraph?

**Answer:**
- Short-term: Current conversation/messages in state
- Long-term: Persistent storage using vector databases for historical context

---

### Question 18
How do you compile a LangGraph?

**Answer:**
```python
graph = StateGraph(MyState)
# Add nodes and edges
app = graph.compile()
```

---

### Question 19
What is checkpointing in LangGraph?

**Answer:**
- Saving the graph state for later resumption
- Enables pausing and resuming workflows

---

### Question 20
How can you visualize a LangGraph?

**Answer:**
```python
mermaid_code = app.get_graph().draw_mermaid()
# Or save as image
app.get_graph().draw_mermaid_png(output_file_path="graph.png")
```

---

## Coding Questions

### Question 21
Write code to create a simple LangGraph with two nodes.

```python
# Answer:
from typing import TypedDict
from langgraph.graph import StateGraph, END

class MyState(TypedDict):
    data: str

def node1(state):
    return {"data": "processed"}

def node2(state):
    return {"data": state["data"] + " completed"}

graph = StateGraph(MyState)
graph.add_node("first", node1)
graph.add_node("second", node2)
graph.set_entry_point("first")
graph.add_edge("first", "second")
graph.add_edge("second", END)

app = graph.compile()
```

---

### Question 22
Write a conditional edge function.

```python
# Answer:
def should_continue(state):
    """Return next node based on state."""
    if state.get("count", 0) > 5:
        return "end"
    return "continue"

# Add to graph
graph.add_conditional_edges(
    "node_a",
    should_continue,
    {"continue": "node_b", "end": END}
)
```

---

## Scenario-Based Questions

### Question 23
You need to build a customer support agent that routes queries to different handlers based on intent. Which LangGraph features would you use?

**Answer:**
- Conditional edges for routing
- Multiple handler nodes
- State to pass context between nodes
- Tools integration for external APIs

---

### Question 24
A user wants to review AI-generated content before it's sent. How would you implement this in LangGraph?

**Answer:**
- Use interrupt() to pause the graph
- Add approval node for human review
- Conditional edge to proceed or reject based on approval

---

## Scoring Guide

| Score | Interpretation |
|-------|----------------|
| 90-100% | Expert |
| 75-89% | Proficient |
| 60-74% | Competent |
| Below 60% | Needs Review |