"""
LangGraph Solutions

This module provides complete solutions to all LangGraph exercises.
"""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI


# ============================================================
# Solution 1: Basic Chat Graph
# ============================================================


class BasicChatState(TypedDict):
    """Basic chat state."""

    messages: List[Dict[str, str]]
    user_input: str


def add_user_message(state: BasicChatState) -> BasicChatState:
    """Add user message to conversation."""
    messages = state.get("messages", [])
    user_input = state["user_input"]

    return {"messages": messages + [{"role": "user", "content": user_input}]}


def generate_response(state: BasicChatState) -> BasicChatState:
    """Generate LLM response."""
    messages = state.get("messages", [])

    try:
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke(messages)
        content = response.content
    except Exception:
        content = f"Simulated response to: {messages[-1]['content']}"

    return {"messages": messages + [{"role": "assistant", "content": content}]}


def create_basic_chat_graph():
    """Solution for Exercise 1."""
    graph = StateGraph(BasicChatState)

    graph.add_node("add_message", add_user_message)
    graph.add_node("respond", generate_response)

    graph.set_entry_point("add_message")
    graph.add_edge("add_message", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


# ============================================================
# Solution 2: Conditional Routing
# ============================================================


class ConditionalState(TypedDict):
    """State for conditional routing."""

    user_query: str
    intent: str
    response: str
    should_escalate: bool


def classify_intent(state: ConditionalState) -> ConditionalState:
    """Classify user intent."""
    query = state["user_query"].lower()

    if any(word in query for word in ["buy", "price", "purchase"]):
        intent = "sales"
    elif any(word in query for word in ["help", "support", "problem"]):
        intent = "support"
    elif any(word in query for word in ["refund", "cancel"]):
        intent = "billing"
    else:
        intent = "general"

    return {"intent": intent}


def handle_sales(state: ConditionalState) -> ConditionalState:
    """Handle sales inquiry."""
    return {
        "response": "I'd be happy to help with your purchase!",
        "should_escalate": False,
    }


def handle_support(state: ConditionalState) -> ConditionalState:
    """Handle support inquiry."""
    return {"response": "Connecting you to support...", "should_escalate": True}


def handle_billing(state: ConditionalState) -> ConditionalState:
    """Handle billing inquiry."""
    return {"response": "Let me help with your billing.", "should_escalate": True}


def handle_general(state: ConditionalState) -> ConditionalState:
    """Handle general inquiry."""
    try:
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke(state["user_query"])
        return {"response": response.content, "should_escalate": False}
    except:
        return {"response": f"Info: {state['user_query']}", "should_escalate": False}


def route_intent(state: ConditionalState) -> str:
    """Route to appropriate handler."""
    return state.get("intent", "general")


def create_conditional_graph_solution():
    """Solution for Exercise 2."""
    graph = StateGraph(ConditionalState)

    graph.add_node("classify", classify_intent)
    graph.add_node("sales", handle_sales)
    graph.add_node("support", handle_support)
    graph.add_node("billing", handle_billing)
    graph.add_node("general", handle_general)

    graph.set_entry_point("classify")

    graph.add_conditional_edges(
        "classify",
        route_intent,
        {
            "sales": "sales",
            "support": "support",
            "billing": "billing",
            "general": "general",
        },
    )

    graph.add_edge("sales", END)
    graph.add_edge("support", END)
    graph.add_edge("billing", END)
    graph.add_edge("general", END)

    return graph.compile()


# ============================================================
# Solution 3: Tool Integration
# ============================================================


class ToolState(TypedDict):
    """State for tool-based agent."""

    query: str
    tool_name: str
    tool_result: str
    final_response: str


def select_tool(state: ToolState) -> ToolState:
    """Select appropriate tool."""
    query = state["query"].lower()

    if "weather" in query:
        tool_name = "weather"
    elif "calculate" in query or "math" in query:
        tool_name = "calculator"
    elif "search" in query:
        tool_name = "search"
    else:
        tool_name = "none"

    return {"tool_name": tool_name}


def execute_tool(state: ToolState) -> ToolState:
    """Execute the selected tool."""
    tool_name = state.get("tool_name", "none")
    query = state["query"]

    if tool_name == "weather":
        location = query.replace("weather", "").replace("in", "").strip()
        result = f"Weather in {location or 'Unknown'}: Sunny, 72°F"
    elif tool_name == "calculator":
        expr = query.replace("calculate", "").replace("what is", "").strip()
        try:
            result = str(eval(expr))
        except:
            result = "Invalid expression"
    elif tool_name == "search":
        result = f"Search results for: {query}"
    else:
        result = "No tool available"

    return {"tool_result": result}


def generate_tool_response(state: ToolState) -> ToolState:
    """Generate response from tool result."""
    tool_result = state.get("tool_result", "")
    return {"final_response": f"Result: {tool_result}"}


def create_tool_graph_solution():
    """Solution for Exercise 3."""
    graph = StateGraph(ToolState)

    graph.add_node("select", select_tool)
    graph.add_node("execute", execute_tool)
    graph.add_node("respond", generate_tool_response)

    graph.set_entry_point("select")
    graph.add_edge("select", "execute")
    graph.add_edge("execute", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


# ============================================================
# Solution 4: Memory Management
# ============================================================


class MemoryState(TypedDict):
    """State with memory."""

    session_id: str
    messages: List[Dict[str, str]]
    user_input: str
    memory_context: str


def retrieve_memory(state: MemoryState) -> MemoryState:
    """Retrieve relevant memory."""
    session_id = state.get("session_id", "default")
    # Simulated memory
    return {"memory_context": f"Context from session {session_id}"}


def generate_with_memory(state: MemoryState) -> MemoryState:
    """Generate response with memory context."""
    user_input = state.get("user_input", "")
    memory_context = state.get("memory_context", "")

    messages = state.get("messages", [])
    messages.append({"role": "user", "content": user_input})
    messages.append(
        {"role": "assistant", "content": f"Response with context: {memory_context}"}
    )

    return {"messages": messages}


def create_memory_graph_solution():
    """Solution for Exercise 4."""
    graph = StateGraph(MemoryState)

    graph.add_node("retrieve", retrieve_memory)
    graph.add_node("generate", generate_with_memory)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


# ============================================================
# Solution 5: Human-in-the-Loop
# ============================================================


class HITLState(TypedDict):
    """State for human-in-the-loop."""

    user_request: str
    needs_approval: bool
    approved: bool
    response: str


def evaluate_request(state: HITLState) -> HITLState:
    """Evaluate if approval is needed."""
    request = state.get("user_request", "")
    sensitive_keywords = ["delete", "send", "purchase", "transfer"]

    needs_approval = any(keyword in request.lower() for keyword in sensitive_keywords)
    return {"needs_approval": needs_approval}


def request_approval(state: HITLState) -> HITLState:
    """Request human approval."""
    # In practice, use interrupt()
    return {"approved": True}


def process_approved(state: HITLState) -> HITLState:
    """Process approved request."""
    try:
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke(f"Process: {state['user_request']}")
        return {"response": response.content}
    except:
        return {"response": f"Processed: {state['user_request']}"}


def process_auto(state: HITLState) -> BasicChatState:
    """Process without approval."""
    try:
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke(state["user_request"])
        return {"response": response.content}
    except:
        return {"response": f"Auto-processed: {state['user_request']}"}


def should_approve(state: HITLState) -> str:
    """Determine if approval flow needed."""
    return "request_approval" if state.get("needs_approval") else "auto_flow"


def create_hitl_graph_solution():
    """Solution for Exercise 5."""
    graph = StateGraph(HITLState)

    graph.add_node("evaluate", evaluate_request)
    graph.add_node("request_approval", request_approval)
    graph.add_node("approved_flow", process_approved)
    graph.add_node("auto_flow", process_auto)

    graph.set_entry_point("evaluate")

    graph.add_conditional_edges(
        "evaluate",
        should_approve,
        {"request_approval": "request_approval", "auto_flow": "auto_flow"},
    )

    graph.add_edge("request_approval", "approved_flow")
    graph.add_edge("approved_flow", END)
    graph.add_edge("auto_flow", END)

    return graph.compile()


# ============================================================
# Main Execution
# ============================================================


def main():
    """Run all solutions."""

    print("=" * 60)
    print("LangGraph Exercise Solutions")
    print("=" * 60)

    # Solution 1: Basic Chat
    print("\n1. Basic Chat Graph")
    chat_app = create_basic_chat_graph()
    result = chat_app.invoke({"messages": [], "user_input": "Hello"})
    print(f"Response generated: {'assistant' in str(result.get('messages', []))}")

    # Solution 2: Conditional Routing
    print("\n2. Conditional Routing")
    conditional_app = create_conditional_graph_solution()
    result = conditional_app.invoke({"user_query": "I want to buy something"})
    print(f"Intent detected: {result.get('intent')}")
    print(f"Response: {result.get('response')}")

    # Solution 3: Tool Integration
    print("\n3. Tool Integration")
    tool_app = create_tool_graph_solution()
    result = tool_app.invoke({"query": "What's the weather in NYC?"})
    print(f"Tool selected: {result.get('tool_name')}")
    print(f"Result: {result.get('final_response')}")

    # Solution 4: Memory
    print("\n4. Memory Management")
    memory_app = create_memory_graph_solution()
    result = memory_app.invoke(
        {"session_id": "user123", "messages": [], "user_input": "Hello"}
    )
    print(f"Messages in state: {len(result.get('messages', []))}")

    # Solution 5: Human-in-the-Loop
    print("\n5. Human-in-the-Loop")
    hitl_app = create_hitl_graph_solution()
    result = hitl_app.invoke({"user_request": "Please send an email"})
    print(f"Needs approval: {result.get('needs_approval')}")
    print(f"Response: {result.get('response')}")

    print("\n" + "=" * 60)
    print("All solutions executed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
