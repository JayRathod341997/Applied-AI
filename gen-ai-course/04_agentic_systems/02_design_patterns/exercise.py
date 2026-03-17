"""
Exercise: Agent Design Patterns Implementation
Implement reactive vs planning agents, reflection, and memory patterns.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class QueryType(Enum):
    """Types of queries the reactive agent can handle."""

    ORDER_STATUS = "order_status"
    STORE_HOURS = "store_hours"
    RETURN_POLICY = "return_policy"
    COMPLEX = "complex"


# Mock data
ORDERS = {
    "ORD001": {"status": "Shipped", "items": ["Laptop"], "total": 1299.99},
    "ORD002": {"status": "Processing", "items": ["Mouse", "Keyboard"], "total": 159.98},
    "ORD003": {"status": "Delivered", "items": ["Monitor"], "total": 349.99},
}

STORE_INFO = {
    "hours": "Mon-Sat: 9AM-9PM, Sun: 10AM-6PM",
    "address": "123 Main St, City",
    "phone": "555-1234",
}


# Part A: Reactive Agent
class ReactiveOrderAgent:
    """Reactive agent that handles simple order queries."""

    def classify_query(self, query: str) -> QueryType:
        """Classify the user query type."""
        query_lower = query.lower()

        if "order status" in query_lower or "track" in query_lower:
            return QueryType.ORDER_STATUS
        elif "hours" in query_lower or "open" in query_lower:
            return QueryType.STORE_HOURS
        elif "return" in query_lower or "refund" in query_lower:
            return QueryType.RETURN_POLICY
        else:
            return QueryType.COMPLEX

    def handle_order_status(self, query: str) -> str:
        """Extract order ID and return status."""
        # Simple extraction - in production use regex or NER
        for order_id in ORDERS.keys():
            if order_id in query.upper():
                order = ORDERS[order_id]
                return f"Order {order_id}: {order['status']} - Items: {', '.join(order['items'])}"
        return "Please provide your order ID (e.g., ORD001)"

    def handle_store_hours(self, query: str) -> str:
        """Return store hours."""
        return STORE_INFO["hours"]

    def handle_return_policy(self, query: str) -> str:
        """Return policy."""
        return "30-day return policy for most items. Receipt required."

    def handle_complex(self, query: str) -> str:
        """Handle complex queries - escalate to planning agent."""
        return "This requires more detailed assistance. Let me connect you with a specialist."

    def process(self, query: str) -> str:
        """Main reactive processing."""
        query_type = self.classify_query(query)

        handlers = {
            QueryType.ORDER_STATUS: self.handle_order_status,
            QueryType.STORE_HOURS: self.handle_store_hours,
            QueryType.RETURN_POLICY: self.handle_return_policy,
            QueryType.COMPLEX: self.handle_complex,
        }

        return handlers[query_type](query)


# Part B: Planning Agent
@dataclass
class PlanStep:
    """A step in the plan."""

    step_id: int
    description: str
    status: str = "pending"  # pending, completed, failed
    result: Any = None


class PlanningTravelAgent:
    """Planning agent for complex travel booking."""

    def __init__(self):
        self.plan: List[PlanStep] = []

    def create_plan(self, goal: str) -> List[PlanStep]:
        """Create a plan to achieve the goal."""
        self.plan = []

        if "book flight" in goal.lower():
            self.plan = [
                PlanStep(1, "Search available flights"),
                PlanStep(2, "Compare prices and times"),
                PlanStep(3, "Select best option"),
                PlanStep(4, "Collect passenger details"),
                PlanStep(5, "Process payment"),
                PlanStep(6, "Send confirmation"),
            ]

        return self.plan

    def execute_step(self, step_id: int) -> str:
        """Execute a specific plan step."""
        for step in self.plan:
            if step.step_id == step_id:
                step.status = "completed"
                # Simulate execution
                step.result = f"Step {step_id} completed"
                return f"Executed: {step.description}"

        return f"Step {step_id} not found"

    def get_plan_status(self) -> str:
        """Get current plan status."""
        status = "Plan Status:\n"
        for step in self.plan:
            status += f"{step.step_id}. {step.description} - {step.status}\n"
        return status


# Part C: Reflection
class ReflectiveAgent:
    """Agent with reflection capabilities."""

    def __init__(self):
        self.quality_threshold = 0.7

    def reflect(self, response: str, context: Dict[str, Any]) -> str:
        """Evaluate and improve response quality."""
        # Check response length
        if len(response) < 10:
            return self.improve(response, "Too short")

        # Check for specific requirements
        if context.get("requires_order_id") and "ORD" not in response:
            return self.improve(response, "Missing required information")

        # Check quality
        quality = self.assess_quality(response)
        if quality < self.quality_threshold:
            return self.improve(response, "Low quality")

        return response

    def assess_quality(self, response: str) -> float:
        """Assess response quality (0-1)."""
        score = 0.5

        if len(response) > 20:
            score += 0.2
        if "." in response:
            score += 0.15
        if response[0].isupper():
            score += 0.15

        return min(score, 1.0)

    def improve(self, response: str, reason: str) -> str:
        """Improve the response based on reason."""
        if "Too short" in reason:
            response += " Please let me know if you need more information."
        elif "Missing" in reason:
            response += " Could you please provide your order ID?"

        return response


# Part D: Memory Patterns
class BufferMemory:
    """Buffer memory - stores recent interactions."""

    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.buffer: List[Dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        """Add message to buffer."""
        self.buffer.append({"role": role, "content": content})
        if len(self.buffer) > self.capacity:
            self.buffer.pop(0)

    def get_context(self) -> str:
        """Get formatted context."""
        return "\n".join([f"{m['role']}: {m['content']}" for m in self.buffer])


class VectorMemory:
    """Vector-like memory for semantic retrieval."""

    def __init__(self):
        self.memories: List[Dict[str, Any]] = []

    def add(self, key: str, content: str, importance: int = 1) -> None:
        """Add memory with importance score."""
        self.memories.append({"key": key, "content": content, "importance": importance})

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant memories (simplified - uses importance)."""
        # Sort by importance
        sorted_memories = sorted(
            self.memories, key=lambda x: x["importance"], reverse=True
        )

        # Return top k content
        return [m["content"] for m in sorted_memories[:top_k]]


# Exercise demonstration
def main():
    print("=" * 60)
    print("Agent Design Patterns Demo")
    print("=" * 60)

    # Part A: Reactive Agent
    print("\n--- Part A: Reactive Agent ---")
    reactive = ReactiveOrderAgent()
    queries = [
        "What's my order status for ORD001?",
        "What are your store hours?",
        "How do I return an item?",
    ]

    for q in queries:
        print(f"Query: {q}")
        print(f"Response: {reactive.process(q)}\n")

    # Part B: Planning Agent
    print("\n--- Part B: Planning Agent ---")
    planner = PlanningTravelAgent()
    planner.create_plan("Book a flight to NYC")
    print(planner.get_plan_status())
    planner.execute_step(1)
    planner.execute_step(2)
    print(planner.get_plan_status())

    # Part C: Reflection
    print("\n--- Part C: Reflection ---")
    reflector = ReflectiveAgent()
    responses = [
        ("Hi", {"requires_order_id": False}),
        ("ORD001", {"requires_order_id": True}),
    ]

    for resp, ctx in responses:
        print(f"Original: {resp}")
        print(f"Reflected: {reflector.reflect(resp, ctx)}\n")

    # Part D: Memory
    print("\n--- Part D: Memory Patterns ---")

    buffer = BufferMemory(capacity=3)
    buffer.add("user", "I want to buy a laptop")
    buffer.add("assistant", "What is your budget?")
    buffer.add("user", "Around $1000")
    buffer.add("user", "I also need a mouse")
    print("Buffer Context:")
    print(buffer.get_context())

    vec_mem = VectorMemory()
    vec_mem.add("preference", "Prefers Apple products", importance=3)
    vec_mem.add("budget", "Budget is $1000", importance=5)
    vec_mem.add("use_case", "主要用于工作", importance=1)
    print("\nVector Memory Retrieval:")
    for m in vec_mem.retrieve("laptop"):
        print(f"  - {m}")


if __name__ == "__main__":
    main()
