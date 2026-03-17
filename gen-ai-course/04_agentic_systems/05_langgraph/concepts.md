# Concepts: LangGraph Framework - Comprehensive Guide

## Overview

LangGraph is a library for building stateful, multi-agent applications using Large Language Models. It extends LangChain with a graph-based approach, enabling complex workflows with cycles, conditional routing, and human-in-the-loop interactions.

---

## Table of Contents

1. [Introduction to LangGraph](#1-introduction-to-langgraph)
2. [Core Concepts](#2-core-concepts)
3. [Building Your First Graph](#3-building-your-first-graph)
4. [Implementing Agentic Design Patterns](#4-implementing-agentic-design-patterns)
5. [Working with Memory and State](#5-working-with-memory-and-state)
6. [Tools and Human-in-the-Loop](#6-tools-and-human-in-the-loop)
7. [Advanced Patterns](#7-advanced-patterns)
8. [Debugging and Visualization](#8-debugging-and-visualization)

---

## 1. Introduction to LangGraph

### What is LangGraph?

LangGraph is a framework for creating **stateful, agentic applications** with LLMs. It represents workflows as directed graphs where:

- **Nodes** = computational steps (functions that process state)
- **Edges** = flow control (how to move between nodes)
- **State** = shared data that flows through the graph

### Why Use LangGraph?

| Feature | Description |
|---------|-------------|
| **Cycles** | Support for looping (essential for agents) |
| **Stateful** | Persistent context across interactions |
| **Human-in-the-loop** | Interrupt and resume workflows |
| **Visualization** | Debug and understand agent flows |
| **Persistence** | Save and resume graph state |

### LangChain vs LangGraph

| Aspect | LangChain | LangGraph |
|--------|-----------|-----------|
| **Workflow** | Sequential chains | Directed graphs |
| **Cycles** | Not supported | Fully supported |
| **State** | Limited | Full state management |
| **Complexity** | Simple linear flows | Complex multi-agent flows |
| **Debugging** | Harder | Graph visualization |

---

## 2. Core Concepts

### 2.1 State

State is a dictionary that flows through the graph. It carries information between nodes.

```python
from typing import TypedDict

# Define state schema
class GraphState(TypedDict):
    """State that flows through the graph."""
    messages: list  # Chat message history
    user_input: str
    final_response: str
    steps_taken: int
```

### 2.2 Nodes

Nodes are Python functions that:
- Take current state as input
- Process/transform the state
- Return updates to the state

```python
def process_input(state: GraphState) -> GraphState:
    """Node that processes user input."""
    user_input = state["user_input"]
    
    # Process the input
    processed = user_input.upper()
    
    # Return state updates
    return {
        "messages": state["messages"] + [{"role": "user", "content": processed}],
        "steps_taken": state.get("steps_taken", 0) + 1,
    }
```

### 2.3 Edges

Edges define how to move between nodes:

- **Normal Edges**: Always move from A to B
- **Conditional Edges**: Choose next node based on state

```python
from langgraph.graph import END

# Normal edge: always go to next node
graph.add_edge("node_a", "node_b")

# Conditional edge: choose based on state
def should_continue(state: GraphState) -> str:
    """Determine next step based on state."""
    if state.get("steps_taken", 0) > 5:
        return "end"
    return "continue"

graph.add_conditional_edges(
    "node_b",
    should_continue,
    {
        "continue": "node_c",
        "end": END,
    }
)
```

### 2.4 Compiling the Graph

```python
from langgraph.graph import StateGraph

# Create and compile the graph
graph = StateGraph(GraphState)

# Add nodes
graph.add_node("process", process_input)
graph.add_node("generate", generate_response)

# Add edges
graph.set_entry_point("process")
graph.add_edge("process", "generate")
graph.add_edge("generate", END)

# Compile
app = graph.compile()
```

---

## 3. Building Your First Graph

### 3.1 Simple Chat Graph

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Define state
class ChatState(TypedDict):
    messages: list
    user_input: str

# Initialize LLM
llm = ChatOpenAI(model="gpt-4")

# Node 1: Process user input
def process_user_input(state: ChatState) -> ChatState:
    """Add user message to state."""
    return {
        "messages": state["messages"] + [{"role": "user", "content": state["user_input"]}]
    }

# Node 2: Generate response
def generate_response(state: ChatState) -> ChatState:
    """Generate LLM response."""
    response = llm.invoke(state["messages"])
    return {
        "messages": state["messages"] + [response]
    }

# Build graph
graph = StateGraph(ChatState)
graph.add_node("process", process_user_input)
graph.add_node("respond", generate_response)
graph.set_entry_point("process")
graph.add_edge("process", "respond")
graph.add_edge("respond", END)

# Compile
app = graph.compile()

# Run
result = app.invoke({
    "messages": [],
    "user_input": "Hello, how are you?"
})

print(result["messages"])
```

### 3.2 Graph with Conditional Logic

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict

class DecisionState(TypedDict):
    user_query: str
    category: str
    response: str
    needs_escalation: bool

llm = ChatOpenAI(model="gpt-4")

def classify_query(state: DecisionState) -> DecisionState:
    """Classify user query."""
    query = state["user_query"]
    
    # Simple classification
    if "help" in query.lower() or "support" in query.lower():
        category = "support"
    elif "buy" in query.lower() or "price" in query.lower():
        category = "sales"
    else:
        category = "general"
    
    return {"category": category}

def handle_support(state: DecisionState) -> DecisionState:
    """Handle support query."""
    return {
        "response": "I'll connect you with our support team.",
        "needs_escalation": True
    }

def handle_sales(state: DecisionState) -> DecisionState:
    """Handle sales query."""
    return {
        "response": "I'd be happy to help you with your purchase!",
        "needs_escalation": False
    }

def handle_general(state: DecisionState) -> DecisionState:
    """Handle general query."""
    response = llm.invoke(f"Answer this question: {state['user_query']}")
    return {
        "response": response.content,
        "needs_escalation": False
    }

def should_route(state: DecisionState) -> str:
    """Route to appropriate handler."""
    category = state.get("category", "general")
    return category

# Build graph
graph = StateGraph(DecisionState)

graph.add_node("classify", classify_query)
graph.add_node("support", handle_support)
graph.add_node("sales", handle_sales)
graph.add_node("general", handle_general)

graph.set_entry_point("classify")
graph.add_conditional_edges(
    "classify",
    should_route,
    {
        "support": "support",
        "sales": "sales",
        "general": "general"
    }
)

# All handlers lead to end
graph.add_edge("support", END)
graph.add_edge("sales", END)
graph.add_edge("general", END)

app = graph.compile()
```

### 3.3 Graph with Cycles (Agent)

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AgentState(TypedDict):
    messages: List[str]
    action: str
    observation: str
    iterations: int

llm = ChatOpenAI(model="gpt-4")

SYSTEM_PROMPT = """You are an AI agent that can take actions.
Available actions:
- search: Search for information
- calculate: Perform calculations
- respond: Provide final response

Think step by step and choose the best action."""

def reason_node(state: AgentState) -> AgentState:
    """LLM decides what action to take."""
    messages = state.get("messages", [])
    prompt = f"{SYSTEM_PROMPT}\n\nConversation: {messages}\n\nWhat action do you take?"
    
    response = llm.invoke(prompt)
    action = response.content.strip()
    
    return {
        "action": action,
        "iterations": state.get("iterations", 0) + 1
    }

def action_node(state: AgentState) -> AgentState:
    """Execute the chosen action."""
    action = state.get("action", "")
    
    # Simulate action execution
    if "search" in action.lower():
        observation = "Found information about..."
    elif "calculate" in action.lower():
        observation = "Calculation result: 42"
    else:
        observation = "Action completed"
    
    return {"observation": observation}

def should_continue(state: AgentState) -> str:
    """Decide whether to continue or end."""
    iterations = state.get("iterations", 0)
    action = state.get("action", "")
    
    if iterations >= 3 or "respond" in action.lower():
        return "end"
    return "continue"

# Build the agent graph
graph = StateGraph(AgentState)

graph.add_node("reason", reason_node)
graph.add_node("act", action_node)

graph.set_entry_point("reason")
graph.add_edge("reason", "act")
graph.add_conditional_edges(
    "act",
    should_continue,
    {
        "continue": "reason",
        "end": END
    }
)

agent = graph.compile()
```

---

## 4. Implementing Agentic Design Patterns

### 4.1 Reflection Pattern

The reflection pattern allows agents to review and improve their outputs.

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ReflectionState(TypedDict):
    task: str
    draft: str
    feedback: str
    iterations: int
    final: str

llm = ChatOpenAI(model="gpt-4")

def generate_draft(state: ReflectionState) -> ReflectionState:
    """Generate initial draft."""
    task = state["task"]
    
    prompt = f"Complete this task: {task}"
    response = llm.invoke(prompt)
    
    return {
        "draft": response.content,
        "iterations": 0
    }

def reflect(state: ReflectionState) -> ReflectionState:
    """Reflect on draft and provide feedback."""
    draft = state["draft"]
    task = state["task"]
    
    prompt = f"""Task: {task}
Draft: {draft}

Provide constructive feedback on how to improve this draft."""
    
    response = llm.invoke(prompt)
    
    return {
        "feedback": response.content,
        "iterations": state.get("iterations", 0) + 1
    }

def improve(state: ReflectionState) -> ReflectionState:
    """Improve draft based on feedback."""
    draft = state["draft"]
    feedback = state["feedback"]
    
    prompt = f"""Original draft: {draft}
Feedback: {feedback}

Improve the draft based on the feedback."""
    
    response = llm.invoke(prompt)
    
    return {"draft": response.content}

def should_continue(state: ReflectionState) -> str:
    """Decide whether to continue reflecting."""
    iterations = state.get("iterations", 0)
    
    if iterations >= 2:  # Max 2 reflection cycles
        return "finish"
    return "reflect"

def finish(state: ReflectionState) -> ReflectionState:
    """Finalize the response."""
    return {"final": state["draft"]}

# Build reflection graph
graph = StateGraph(ReflectionState)

graph.add_node("draft", generate_draft)
graph.add_node("reflect", reflect)
graph.add_node("improve", improve)
graph.add_node("finish", finish)

graph.set_entry_point("draft")
graph.add_edge("draft", "reflect")
graph.add_conditional_edges(
    "reflect",
    should_continue,
    {
        "reflect": "improve",
        "finish": "finish"
    }
)
graph.add_edge("improve", "reflect")
graph.add_edge("finish", END)

reflection_agent = graph.compile()
```

### 4.2 Tools Pattern

Integrating external tools with LangGraph.

```python
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

# Define tools
@tool
def search_wikipedia(query: str) -> str:
    """Search Wikipedia for information."""
    # In practice, use Wikipedia API
    return f"Information about {query} from Wikipedia"

@tool
def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    try:
        result = eval(expression)
        return str(result)
    except:
        return "Invalid expression"

# Get tool list
tools = [search_wikipedia, calculate]

# Create tool-calling LLM
llm_with_tools = ChatOpenAI(model="gpt-4").bind_tools(tools)

class ToolState(TypedDict):
    query: str
    tool_calls: List
    tool_results: List
    final_answer: str

def call_tools(state: ToolState) -> ToolState:
    """Call tools based on query."""
    query = state["query"]
    
    # Get tool suggestions from LLM
    response = llm_with_tools.invoke(query)
    
    # Extract tool calls
    tool_calls = response.tool_calls if hasattr(response, 'tool_calls') else []
    
    return {"tool_calls": tool_calls}

def execute_tools(state: ToolState) -> ToolState:
    """Execute the called tools."""
    tool_calls = state.get("tool_calls", [])
    results = []
    
    for call in tool_calls:
        tool_name = call.get("name", "")
        tool_args = call.get("args", {})
        
        # Find and execute tool
        for t in tools:
            if t.name == tool_name:
                result = t.invoke(tool_args.get("query", ""))
                results.append({"tool": tool_name, "result": result})
    
    return {"tool_results": results}

def generate_answer(state: ToolState) -> ToolState:
    """Generate final answer from tool results."""
    query = state["query"]
    results = state.get("tool_results", [])
    
    prompt = f"""Query: {query}
Tool results: {results}

Provide a comprehensive answer based on the tool results."""
    
    llm = ChatOpenAI(model="gpt-4")
    response = llm.invoke(prompt)
    
    return {"final_answer": response.content}

# Build tool agent graph
graph = StateGraph(ToolState)

graph.add_node("call_tools", call_tools)
graph.add_node("execute_tools", execute_tools)
graph.add_node("generate", generate_answer)

graph.set_entry_point("call_tools")
graph.add_edge("call_tools", "execute_tools")
graph.add_edge("execute_tools", "generate")
graph.add_edge("generate", END)

tool_agent = graph.compile()
```

### 4.3 Planning-ReAct Pattern

Combining reasoning and acting in cycles.

```python
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ReActState(TypedDict):
    question: str
    thoughts: List[str]
    actions: List[str]
    observations: List[str]
    answer: str

llm = ChatOpenAI(model="gpt-4")

def think(state: ReActState) -> ReActState:
    """Generate thought about the question."""
    question = state["question"]
    thoughts = state.get("thoughts", [])
    actions = state.get("actions", [])
    observations = state.get("observations", [])
    
    # Build context
    context = f"Question: {question}\n"
    if thoughts:
        context += f"Thoughts: {thoughts[-1]}\n"
    if actions:
        context += f"Previous actions: {actions}\n"
    if observations:
        context += f"Observations: {observations}\n"
    
    prompt = f"""Think step by step about this question. What's your next thought?
    
{context}"""
    
    response = llm.invoke(prompt)
    
    return {"thoughts": thoughts + [response.content]}

def act(state: ReActState) -> ReActState:
    """Determine action to take."""
    thoughts = state.get("thoughts", [])
    actions = state.get("actions", [])
    
    last_thought = thoughts[-1] if thoughts else ""
    
    # Determine action
    if "final answer" in last_thought.lower():
        action = "FINISH"
    elif "search" in last_thought.lower():
        action = "search"
    elif "calculate" in last_thought.lower():
        action = "calculate"
    else:
        action = "continue"
    
    return {"actions": actions + [action]}

def observe(state: ReActState) -> ReActState:
    """Get observation from action."""
    actions = state.get("actions", [])
    observations = state.get("observations", [])
    
    last_action = actions[-1] if actions else ""
    
    # Simulate observation
    if last_action == "search":
        obs = "Found relevant information"
    elif last_action == "calculate":
        obs = "Calculation performed"
    elif last_action == "FINISH":
        obs = "Ready to provide answer"
    else:
        obs = "Continuing reasoning"
    
    return {"observations": observations + [obs]}

def should_continue(state: ReActState) -> str:
    """Check if should continue or finish."""
    actions = state.get("actions", [])
    
    if not actions:
        return "think"
    
    last_action = actions[-1]
    
    if last_action == "FINISH" or len(actions) >= 5:
        return "answer"
    return "think"

def answer(state: ReActState) -> ReActState:
    """Generate final answer."""
    question = state["question"]
    thoughts = state.get("thoughts", [])
    observations = state.get("observations", [])
    
    prompt = f"""Question: {question}

Reasoning chain:
{chr(10).join(thoughts)}

Provide a clear, final answer."""
    
    response = llm.invoke(prompt)
    
    return {"answer": response.content}

# Build ReAct graph
graph = StateGraph(ReActState)

graph.add_node("think", think)
graph.add_node("act", act)
graph.add_node("observe", observe)
graph.add_node("answer", answer)

graph.set_entry_point("think")
graph.add_edge("think", "act")
graph.add_edge("act", "observe")
graph.add_conditional_edges(
    "observe",
    should_continue,
    {
        "think": "think",
        "answer": "answer"
    }
)
graph.add_edge("answer", END)

react_agent = graph.compile()
```

---

## 5. Working with Memory and State

### 5.1 Short-term Memory (Message History)

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from langchain.messages import HumanMessage, AIMessage

class ConversationState(TypedDict):
    messages: List
    user_input: str

def add_message(state: ConversationState) -> ConversationState:
    """Add user message."""
    messages = state.get("messages", [])
    user_input = state["user_input"]
    
    return {
        "messages": messages + [HumanMessage(content=user_input)]
    }

def generate_response(state: ConversationState) -> ConversationState:
    """Generate response using message history."""
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4")
    messages = state.get("messages", [])
    
    response = llm.invoke(messages)
    
    return {
        "messages": messages + [response]
    }

# Build conversation graph
graph = StateGraph(ConversationState)

graph.add_node("add_message", add_message)
graph.add_node("generate", generate_response)

graph.set_entry_point("add_message")
graph.add_edge("add_message", "generate")
graph.add_edge("generate", END)

conversation = graph.compile()
```

### 5.2 Long-term Memory (Vector Store)

```python
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PersistentMemoryState(TypedDict):
    user_id: str
    query: str
    context: List
    response: str

def retrieve_memory(state: PersistentMemoryState) -> PersistentMemoryState:
    """Retrieve relevant memories."""
    user_id = state["user_id"]
    query = state["query"]
    
    # Load vector store (in practice, load from persistent storage)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.load_local(f"memory_{user_id}", embeddings)
    
    # Retrieve relevant docs
    docs = vectorstore.similarity_search(query, k=3)
    
    return {"context": [doc.page_content for doc in docs]}

def generate_with_memory(state: PersistentMemoryState) -> PersistentMemoryState:
    """Generate response with retrieved context."""
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4")
    query = state["query"]
    context = state.get("context", [])
    
    prompt = f"""Context from previous conversations:
{chr(10).join(context)}

Current query: {query}

Provide a response that considers the context."""
    
    response = llm.invoke(prompt)
    
    return {"response": response.content}

def save_memory(state: PersistentMemoryState) -> PersistentMemoryState:
    """Save interaction to memory."""
    user_id = state["user_id"]
    query = state["query"]
    response = state["response"]
    
    # In practice, embed and save to vector store
    # embeddings = OpenAIEmbeddings()
    # vectorstore.add_texts([f"User: {query}\nAI: {response}"])
    
    return {}

# Build memory-enhanced graph
graph = StateGraph(PersistentMemoryState)

graph.add_node("retrieve", retrieve_memory)
graph.add_node("generate", generate_with_memory)
graph.add_node("save", save_memory)

graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", "save")
graph.add_edge("save", END)

memory_agent = graph.compile()
```

### 5.3 Combining Short and Long-term Memory

```python
from typing import TypedDict, List

class FullMemoryState(TypedDict):
    conversation_id: str
    messages: List  # Short-term: current conversation
    user_id: str   # For long-term memory lookup
    query: str
    long_term_context: List
    response: str
```

---

## 6. Tools and Human-in-the-Loop

### 6.1 Tool Integration

```python
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from typing import TypedDict

@tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Weather in {location}: Sunny, 72°F"

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return f"Email sent to {to}"

tools = [get_weather, send_email]

class ToolState(TypedDict):
    user_request: str
    selected_tool: str
    tool_result: str
    response: str

def select_tool(state: ToolState) -> ToolState:
    """Select appropriate tool."""
    request = state["user_request"]
    
    # Simple selection logic
    if "weather" in request.lower():
        return {"selected_tool": "get_weather"}
    elif "email" in request.lower() or "send" in request.lower():
        return {"selected_tool": "send_email"}
    else:
        return {"selected_tool": "none"}

def execute_tool(state: ToolState) -> ToolState:
    """Execute selected tool."""
    tool_name = state.get("selected_tool", "none")
    
    if tool_name == "none":
        return {"tool_result": "No tool needed"}
    
    # Find and execute tool
    for t in tools:
        if t.name == tool_name:
            # In practice, extract args from request
            result = t.invoke("test")
            return {"tool_result": result}
    
    return {"tool_result": "Tool not found"}

def respond(state: ToolState) -> ToolState:
    """Generate response."""
    tool_result = state.get("tool_result", "")
    return {"response": f"Result: {tool_result}"}

# Build tool workflow
graph = StateGraph(ToolState)

graph.add_node("select", select_tool)
graph.add_node("execute", execute_tool)
graph.add_node("respond", respond)

graph.set_entry_point("select")
graph.add_edge("select", "execute")
graph.add_edge("execute", "respond")
graph.add_edge("respond", END)

tool_workflow = graph.compile()
```

### 6.2 Human-in-the-Loop (Interrupt)

```python
from langgraph.graph import StateGraph, END, interrupt
from typing import TypedDict
from langchain_openai import ChatOpenAI

class HITLState(TypedDict):
    user_request: str
    approval_required: bool
    approved: bool
    response: str

llm = ChatOpenAI(model="gpt-4")

def process_request(state: HITLState) -> HITLState:
    """Process user request and determine if approval needed."""
    request = state["user_request"]
    
    # Determine if approval is needed (e.g., for sensitive actions)
    sensitive_keywords = ["delete", "send", "purchase", "transfer"]
    needs_approval = any(keyword in request.lower() for keyword in sensitive_keywords)
    
    return {"approval_required": needs_approval}

def request_approval(state: HITLState) -> HITLState:
    """Request human approval."""
    # This interrupts the graph and waits for human input
    user_request = state["user_request"]
    
    # Interrupt and wait for human approval
    # The graph state will be updated with 'approved' field
    approved = interrupt({
        "message": f"Approval needed for: {user_request}",
        "required_action": "Please approve or reject"
    })
    
    return {"approved": approved}

def execute_approved_action(state: HITLState) -> HITLState:
    """Execute the action after approval."""
    request = state["user_request"]
    
    # Execute the action
    prompt = f"Process this request: {request}"
    response = llm.invoke(prompt)
    
    return {"response": response.content}

def handle_rejection(state: HITLState) -> HITLState:
    """Handle rejected request."""
    return {"response": "Your request has been rejected."}

def check_approval(state: HITLState) -> str:
    """Check if approved."""
    if state.get("approval_required", False):
        return "request_approval"
    return "execute"

# Build HITL graph
graph = StateGraph(HITLState)

graph.add_node("process", process_request)
graph.add_node("request_approval", request_approval)
graph.add_node("execute", execute_approved_action)
graph.add_node("reject", handle_rejection)

graph.set_entry_point("process")
graph.add_conditional_edges(
    "process",
    check_approval,
    {
        "request_approval": "request_approval",
        "execute": "execute"
    }
)

# After approval check, go to execution or rejection
# Note: In practice, you'd need conditional edges after approval
graph.add_edge("execute", END)
graph.add_edge("reject", END)

# Note: For a complete HITL implementation, you'd need to handle
# the resume after interrupt with the approval status

hitl_graph = graph.compile()

# Usage:
# result = hitl_graph.invoke({"user_request": "Send email to john"})
# # Graph interrupts here
# 
# # Later, resume with approval
# result = hitl_graph.invoke({"user_request": "Send email to john", "approved": True})
```

---

## 7. Advanced Patterns

### 7.1 Multi-Agent Collaboration

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MultiAgentState(TypedDict):
    task: str
    research_agent_result: str
    writing_agent_result: str
    final_result: str

def research_agent(state: MultiAgentState) -> MultiAgentState:
    """Research agent collects information."""
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4")
    task = state["task"]
    
    prompt = f"Research: {task}\nProvide key facts and information."
    response = llm.invoke(prompt)
    
    return {"research_agent_result": response.content}

def writing_agent(state: MultiAgentState) -> MultiAgentState:
    """Writing agent creates content."""
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4")
    research = state.get("research_agent_result", "")
    
    prompt = f"Based on this research:\n{research}\n\nWrite a well-structured response."
    response = llm.invoke(prompt)
    
    return {"writing_agent_result": response.content}

def review_agent(state: MultiAgentState) -> MultiAgentState:
    """Review agent evaluates output."""
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4")
    writing = state.get("writing_agent_result", "")
    
    prompt = f"Review this content:\n{writing}\n\nIs it accurate and well-written?"
    response = llm.invoke(prompt)
    
    return {"final_result": response.content}

# Build multi-agent graph
graph = StateGraph(MultiAgentState)

graph.add_node("research", research_agent)
graph.add_node("write", writing_agent)
graph.add_node("review", review_agent)

graph.set_entry_point("research")
graph.add_edge("research", "write")
graph.add_edge("write", "review")
graph.add_edge("review", END)

multi_agent = graph.compile()
```

### 7.2 Parallel Execution

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import concurrent.futures

class ParallelState(TypedDict):
    task: str
    sub_tasks: List
    results: List

def split_task(state: ParallelState) -> ParallelState:
    """Split task into sub-tasks."""
    task = state["task"]
    
    # Split into parallel sub-tasks
    sub_tasks = ["subtask1", "subtask2", "subtask3"]
    
    return {"sub_tasks": sub_tasks}

def execute_subtask(subtask: str) -> str:
    """Execute a single sub-task."""
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4")
    response = llm.invoke(f"Complete: {subtask}")
    return response.content

def execute_parallel(state: ParallelState) -> ParallelState:
    """Execute sub-tasks in parallel."""
    sub_tasks = state.get("sub_tasks", [])
    
    # Execute in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(execute_subtask, sub_tasks))
    
    return {"results": results}

def combine_results(state: ParallelState) -> ParallelState:
    """Combine parallel results."""
    from langchain_openai import ChatOpenAI
    
    results = state.get("results", [])
    
    prompt = f"Combine these results:\n{chr(10).join(results)}"
    llm = ChatOpenAI(model="gpt-4")
    response = llm.invoke(prompt)
    
    return {"final_result": response.content}

# Build parallel execution graph
graph = StateGraph(ParallelState)

graph.add_node("split", split_task)
graph.add_node("parallel", execute_parallel)
graph.add_node("combine", combine_results)

graph.set_entry_point("split")
graph.add_edge("split", "parallel")
graph.add_edge("parallel", "combine")
graph.add_edge("combine", END)

parallel_workflow = graph.compile()
```

---

## 8. Debugging and Visualization

### 8.1 Visualizing the Graph

```python
# Get graph as Mermaid diagram
mermaid_code = app.get_graph().draw_mermaid()
print(mermaid_code)

# Or save as image (requires additional dependencies)
# app.get_graph().draw_mermaid_png(output_file_path="graph.png")
```

### 8.2 Debugging Tips

```python
# Add debug logging
def debug_node(state):
    print(f"State at node: {state}")
    return state

# Add to graph
graph.add_node("debug", debug_node)

# Use breakpoints for inspection
app = graph.compile()

# Run with breakpoints
for chunk in app.stream(
    {"user_input": "Hello"},
    stream_mode="values"
):
    print(chunk)
```

### 8.3 Common Issues

| Issue | Solution |
|-------|----------|
| State not updating | Ensure node returns state dict |
| Infinite loops | Add max iterations check |
| Tools not working | Check tool binding |
| Memory issues | Use checkpointing |
| Graph not executing | Check entry point and edges |

---

## Summary

This comprehensive guide covered:

1. **Core Concepts**: Nodes, Edges, State, Graph compilation
2. **Building Graphs**: Simple chat, conditional logic, cycles
3. **Agentic Patterns**: Reflection, Tools, ReAct
4. **Memory**: Short-term (messages), Long-term (vector store)
5. **Human-in-the-Loop**: Interrupt and resume patterns
6. **Advanced**: Multi-agent, parallel execution
7. **Debugging**: Visualization and troubleshooting

LangGraph enables building sophisticated, stateful agent applications with full control over workflow execution.