# Exercise 01: Building Your First LangGraph Application

## Objective

Build a basic LangGraph application that processes user input and generates responses using a stateful graph workflow.

## Difficulty

Beginner

## Time Duration

45 minutes

---

## Requirements

### Task 1: Set Up Environment (10 minutes)

Install required packages:

```bash
pip install langgraph langchain langchain-openai
```

### Task 2: Create Basic Graph (20 minutes)

Build a simple LangGraph that:
1. Takes user input
2. Processes the input
3. Generates a response
4. Returns the final output

### Task 3: Run the Application (15 minutes)

Execute the graph and test with sample inputs.

---

## Instructions

### Step 1: Define State Schema

```python
from typing import TypedDict

class ChatState(TypedDict):
    user_input: str
    processed_input: str
    response: str
```

### Step 2: Create Nodes

```python
def process_input(state: ChatState) -> ChatState:
    """Process user input."""
    # TODO: Add processing logic
    pass

def generate_response(state: ChatState) -> ChatState:
    """Generate LLM response."""
    # TODO: Add response generation
    pass
```

### Step 3: Build the Graph

```python
from langgraph.graph import StateGraph, END

# TODO: Create and compile the graph
```

---

## Expected Output

After completing the exercise, you should have:
1. A working LangGraph application
2. A graph that processes input and generates responses
3. Understanding of basic LangGraph concepts

---

## Sample Code Structure

```python
"""
LangGraph Basic Exercise Solution
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END

# Define state
class ChatState(TypedDict):
    user_input: str
    processed_input: str
    response: str

# Node functions
def process_input(state: ChatState) -> ChatState:
    """Process user input."""
    user_input = state["user_input"]
    # Simple processing - add prefix
    processed = f"Processed: {user_input}"
    return {"processed_input": processed}

def generate_response(state: ChatState) -> ChatState:
    """Generate response."""
    processed = state["processed_input"]
    # Simple response
    response = f"Got your message: {processed}"
    return {"response": response}

# Build graph
graph = StateGraph(ChatState)
graph.add_node("process", process_input)
graph.add_node("respond", generate_response)

graph.set_entry_point("process")
graph.add_edge("process", "respond")
graph.add_edge("respond", END)

# Compile
app = graph.compile()

# Run
if __name__ == "__main__":
    result = app.invoke({"user_input": "Hello, LangGraph!"})
    print(result)
```

---

## Submission

- Python script with working code
- Screenshot of execution output
- Brief explanation of how the graph works