"""
LangGraph Comprehensive Exercises

This module contains multiple exercises covering:
1. Basic graph creation
2. Conditional routing
3. Tool integration
4. Memory management
5. Human-in-the-loop patterns
6. Multi-agent systems
"""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI


# ============================================================
# Exercise 1: Basic Chat Graph
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

    # Initialize LLM (requires OPENAI_API_KEY)
    try:
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke(messages)

        return {
            "messages": messages + [{"role": "assistant", "content": response.content}]
        }
    except Exception as e:
        # Fallback for testing without API key
        return {
            "messages": messages
            + [
                {
                    "role": "assistant",
                    "content": f"Response to: {messages[-1]['content']}",
                }
            ]
        }


def create_basic_chat_graph() -> "StateGraph":
    """Create a basic chat graph."""
    graph = StateGraph(BasicChatState)

    graph.add_node("add_message", add_user_message)
    graph.add_node("respond", generate_response)

    graph.set_entry_point("add_message")
    graph.add_edge("add_message", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


# ============================================================
# Exercise 2: Conditional Routing
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

    if "buy" in query or "price" in query or "purchase" in query:
        intent = "sales"
    elif "help" in query or "support" in query or "problem" in query:
        intent = "support"
    elif "refund" in query or "cancel" in query:
        intent = "billing"
    else:
        intent = "general"

    return {"intent": intent}


def handle_sales(state: ConditionalState) -> ConditionalState:
    """Handle sales inquiry."""
    return {
        "response": "I'd be happy to help you with our products!",
        "should_escalate": False,
    }


def handle_support(state: ConditionalState) -> ConditionalState:
    """Handle support inquiry."""
    return {
        "response": "Let me connect you with our support team.",
        "should_escalate": True,
    }


def handle_billing(state: ConditionalState) -> ConditionalState:
    """Handle billing inquiry."""
    return {
        "response": "I'll help you with your billing question.",
        "should_escalate": True,
    }


def handle_general(state: ConditionalState) -> ConditionalState:
    """Handle general inquiry."""
    try:
        llm = ChatOpenAI(model="gpt-4")
        prompt = f"Answer this question: {state['user_query']}"
        response = llm.invoke(prompt)

        return {"response": response.content, "should_escalate": False}
    except:
        return {
            "response": f"Here's some information about: {state['user_query']}",
            "should_escalate": False,
        }


def route_intent(state: ConditionalState) -> str:
    """Route to appropriate handler."""
    intent = state.get("intent", "general")
    return intent


def create_conditional_graph() -> "StateGraph":
    """Create a graph with conditional routing."""
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

    # All handlers lead to END
    graph.add_edge("sales", END)
    graph.add_edge("support", END)
    graph.add_edge("billing", END)
    graph.add_edge("general", END)

    return graph.compile()


# ============================================================
# Exercise 3: Tool Integration
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


def get_weather(location: str) -> str:
    """Get weather for a location."""
    # Simulated weather data
    return f"Weather in {location}: Sunny, 72°F"


def calculate(expression: str) -> str:
    """Calculate mathematical expression."""
    try:
        result = eval(expression)
        return str(result)
    except:
        return "Invalid expression"


def search_info(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"


def execute_tool(state: ToolState) -> ToolState:
    """Execute the selected tool."""
    tool_name = state.get("tool_name", "none")
    query = state["query"]

    if tool_name == "weather":
        # Extract location from query
        location = query.replace("weather", "").replace("in", "").strip()
        result = get_weather(location or "Unknown")
    elif tool_name == "calculator":
        # Extract expression
        expr = query.replace("calculate", "").strip()
        result = calculate(expr)
    elif tool_name == "search":
        result = search_info(query)
    else:
        result = "No tool available"

    return {"tool_result": result}


def generate_tool_response(state: ToolState) -> ToolState:
    """Generate response from tool result."""
    tool_result = state.get("tool_result", "")

    return {"final_response": f"Tool result: {tool_result}"}


def create_tool_graph() -> "StateGraph":
    """Create a graph with tool integration."""
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
# Exercise 4: Memory Management
# ============================================================


class MemoryState(TypedDict):
    """State with memory."""

    session_id: str
    messages: List[Dict[str, str]]
    user_input: str
    memory_context: str


def retrieve_memory(state: MemoryState) -> MemoryState:
    """Retrieve relevant memory."""
    # In practice, query a vector store
    session_id = state.get("session_id", "default")

    # Simulated memory retrieval
    context = f"Previous conversation context for session {session_id}"

    return {"memory_context": context}


def generate_with_memory(state: MemoryState) -> MemoryState:
    """Generate response with memory context."""
    user_input = state.get("user_input", "")
    memory_context = state.get("memory_context", "")

    # Build prompt with context
    prompt = f"Context: {memory_context}\n\nUser: {user_input}"

    try:
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke(prompt)
        message = response.content
    except:
        message = f"Response incorporating: {memory_context}"

    return {
        "messages": state.get("messages", [])
        + [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": message},
        ]
    }


def create_memory_graph() -> "StateGraph":
    """Create a graph with memory."""
    graph = StateGraph(MemoryState)

    graph.add_node("retrieve", retrieve_memory)
    graph.add_node("generate", generate_with_memory)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


# ============================================================
# Exercise 5: Human-in-the-Loop
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

    # Determine if approval needed
    sensitive_keywords = ["delete", "send", "purchase", "transfer", "refund"]
    needs_approval = any(keyword in request.lower() for keyword in sensitive_keywords)

    return {"needs_approval": needs_approval}


def request_approval(state: HITLState) -> HITLState:
    """Request human approval."""
    # In practice, this would interrupt and wait
    # For now, simulate auto-approval
    return {"approved": True}


def process_approved(state: HITLState) -> HITLState:
    """Process approved request."""
    request = state.get("user_request", "")

    try:
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke(f"Process this approved request: {request}")
        result = response.content
    except:
        result = f"Processed: {request}"

    return {"response": result}


def process_auto(state: HITLState) -> HITLState:
    """Process without approval."""
    request = state.get("user_request", "")

    try:
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke(request)
        result = response.content
    except:
        result = f"Auto-processed: {request}"

    return {"response": result}


def should_approve(state: HITLState) -> str:
    """Determine if approval flow needed."""
    if state.get("needs_approval", False):
        return "request_approval"
    return "auto_process"


def create_hitl_graph() -> "StateGraph":
    """Create a graph with human-in-the-loop."""
    graph = StateGraph(HITLState)

    graph.add_node("evaluate", evaluate_request)
    graph.add_node("request_approval", request_approval)
    graph.add_node("approved_flow", process_approved)
    graph.add_node("auto_flow", process_auto)

    graph.set_entry_point("evaluate")

    graph.add_conditional_edges(
        "evaluate",
        should_approve,
        {"request_approval": "request_approval", "auto_process": "auto_flow"},
    )

    graph.add_edge("request_approval", "approved_flow")
    graph.add_edge("approved_flow", END)
    graph.add_edge("auto_flow", END)

    return graph.compile()


# ============================================================
# Main Execution
# ============================================================


def main():
    """Main function to demonstrate all exercises."""

    print("=" * 60)
    print("LangGraph Exercises")
    print("=" * 60)

    # Exercise 1: Basic Chat
    print("\n1. Basic Chat Graph")
    print("-" * 40)
    chat_app = create_basic_chat_graph()
    try:
        result = chat_app.invoke({"messages": [], "user_input": "Hello!"})
        print(f"Response: {result['messages'][-1]['content']}")
    except Exception as e:
        print(f"Error (expected without API key): {e}")

    # Exercise 2: Conditional Routing
    print("\n2. Conditional Routing")
    print("-" * 40)
    conditional_app = create_conditional_graph()

    test_queries = [
        "I want to buy a product",
        "I need help with my account",
        "What's the weather like?",
    ]

    for query in test_queries:
        result = conditional_app.invoke({"user_query": query})
        print(f"Query: {query}")
        print(f"Intent: {result.get('intent')}")
        print(f"Response: {result.get('response')}")
        print()

    # Exercise 3: Tool Integration
    print("\n3. Tool Integration")
    print("-" * 40)
    tool_app = create_tool_graph()

    tool_queries = [
        "What's the weather in New York?",
        "Calculate 2 + 2",
        "Search for AI news",
    ]

    for query in tool_queries:
        result = tool_app.invoke({"query": query})
        print(f"Query: {query}")
        print(f"Tool: {result.get('tool_name')}")
        print(f"Result: {result.get('final_response')}")
        print()

    # Exercise 4: Memory
    print("\n4. Memory Management")
    print("-" * 40)
    memory_app = create_memory_graph()

    result = memory_app.invoke(
        {
            "session_id": "user123",
            "messages": [],
            "user_input": "What's my previous question?",
        }
    )
    print(f"Messages: {len(result.get('messages', []))}")

    # Exercise 5: Human-in-the-Loop
    print("\n5. Human-in-the-Loop")
    print("-" * 40)
    hitl_app = create_hitl_graph()

    hitl_queries = ["Tell me about your services", "Please delete my account"]

    for query in hitl_queries:
        result = hitl_app.invoke({"user_request": query})
        print(f"Request: {query}")
        print(f"Needs approval: {result.get('needs_approval')}")
        print(f"Response: {result.get('response')}")
        print()


if __name__ == "__main__":
    main()
