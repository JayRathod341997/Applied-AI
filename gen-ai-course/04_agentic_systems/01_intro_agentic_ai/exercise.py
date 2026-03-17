"""
Exercise: Building a Simple Agentic AI System
Create a product lookup agent with perception, reasoning, and action components.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


# Mock product inventory
PRODUCT_INVENTORY = [
    {
        "id": "P001",
        "name": "Laptop Pro",
        "category": "Electronics",
        "price": 1299.99,
        "stock": 15,
    },
    {
        "id": "P002",
        "name": "Wireless Mouse",
        "category": "Electronics",
        "price": 29.99,
        "stock": 50,
    },
    {
        "id": "P003",
        "name": "Office Chair",
        "category": "Furniture",
        "price": 199.99,
        "stock": 8,
    },
    {
        "id": "P004",
        "name": "Standing Desk",
        "category": "Furniture",
        "price": 449.99,
        "stock": 12,
    },
    {
        "id": "P005",
        "name": "USB-C Hub",
        "category": "Electronics",
        "price": 49.99,
        "stock": 30,
    },
    {
        "id": "P006",
        "name": 'Monitor 27"',
        "category": "Electronics",
        "price": 349.99,
        "stock": 20,
    },
    {
        "id": "P007",
        "name": "Keyboard Mechanical",
        "category": "Electronics",
        "price": 129.99,
        "stock": 25,
    },
    {
        "id": "P008",
        "name": "Desk Lamp",
        "category": "Furniture",
        "price": 39.99,
        "stock": 45,
    },
]


@dataclass
class AgentState:
    """Represents the current state of the agent."""

    user_request: str = ""
    collected_info: Dict[str, Any] = field(default_factory=dict)
    reasoning_steps: List[str] = field(default_factory=list)
    actions_taken: List[str] = field(default_factory=list)
    response: str = ""


class ProductAgent:
    """
    A simple agentic AI system for product lookup.
    Demonstrates key components: Goal, Perception, Reasoning, Plan, Act, Feedback.
    """

    def __init__(self, inventory: List[Dict[str, Any]]):
        self.inventory = inventory
        self.state = AgentState()

    def set_goal(self, request: str) -> None:
        """Set the agent's goal based on user request."""
        self.state.user_request = request
        self.state.reasoning_steps.append(f"Goal set: {request}")

    def perceive(self) -> Dict[str, Any]:
        """Extract relevant information from the user's request."""
        request = self.state.user_request.lower()

        info = {"category_filter": None, "price_max": None, "in_stock_only": False}

        # Extract category
        categories = ["electronics", "furniture"]
        for cat in categories:
            if cat in request:
                info["category_filter"] = cat.capitalize()

        # Extract price range
        if "under" in request or "less than" in request:
            import re

            price_match = re.search(r"(\d+)", request)
            if price_match:
                info["price_max"] = float(price_match.group(1))

        # Check for stock requirement
        if "in stock" in request or "available" in request:
            info["in_stock_only"] = True

        self.state.collected_info = info
        self.state.reasoning_steps.append(f"Perceived: {info}")

        return info

    def reason(self) -> str:
        """Determine the next action based on collected information."""
        info = self.state.collected_info

        if not info["category_filter"] and not info["price_max"]:
            return "ASK_CLARIFICATION"
        elif info["in_stock_only"]:
            return "FILTER_IN_STOCK"
        else:
            return "SEARCH"

    def act(self, action_type: str) -> List[Dict[str, Any]]:
        """Execute the determined action."""
        info = self.state.collected_info
        results = self.inventory

        if action_type == "ASK_CLARIFICATION":
            self.state.actions_taken.append("Requested clarification")
            return []

        # Apply filters
        if info.get("category_filter"):
            results = [p for p in results if p["category"] == info["category_filter"]]
            self.state.actions_taken.append(
                f"Filtered by category: {info['category_filter']}"
            )

        if info.get("price_max"):
            results = [p for p in results if p["price"] <= info["price_max"]]
            self.state.actions_taken.append(
                f"Filtered by price: <= ${info['price_max']}"
            )

        if info.get("in_stock_only"):
            results = [p for p in results if p["stock"] > 0]
            self.state.actions_taken.append("Filtered by availability")

        return results

    def provide_feedback(self, results: List[Dict[str, Any]], action_type: str) -> str:
        """Generate response based on action results."""
        if action_type == "ASK_CLARIFICATION":
            response = "Could you please clarify? Are you looking for Electronics or Furniture?"
        elif not results:
            response = "No products found matching your criteria. Try a broader search."
        else:
            response = f"Found {len(results)} product(s):\n"
            for p in results:
                stock_status = "✓ In Stock" if p["stock"] > 0 else "✗ Out of Stock"
                response += f"- {p['name']} (${p['price']}) - {p['category']} - {stock_status}\n"

        self.state.response = response
        self.state.reasoning_steps.append(f"Feedback generated")

        return response

    def run(self, user_request: str) -> str:
        """Main agent loop: Goal → Perception → Reasoning → Action → Feedback"""
        # Step 1: Set Goal
        self.set_goal(user_request)

        # Step 2: Perception
        info = self.perceive()

        # Step 3: Reasoning
        action_type = self.reason()

        # Step 4: Action
        results = self.act(action_type)

        # Step 5: Feedback
        response = self.provide_feedback(results, action_type)

        return response

    def get_state(self) -> AgentState:
        """Return the current agent state for debugging."""
        return self.state


# Exercise: Complete the missing functionality
def exercise():
    """Complete the exercise by implementing missing agent features."""

    agent = ProductAgent(PRODUCT_INVENTORY)

    # Test cases
    test_requests = [
        "I want to buy electronics",
        "Show me furniture under $300",
        "What's available?",
        "Show me electronics in stock under $100",
    ]

    print("=" * 60)
    print("Agentic AI Product Lookup Demo")
    print("=" * 60)

    for request in test_requests:
        print(f"\nUser: {request}")
        print("-" * 40)

        response = agent.run(request)
        print(f"Agent: {response}")

        # Show reasoning steps
        state = agent.get_state()
        print(f"  Reasoning: {state.reasoning_steps}")
        print(f"  Actions: {state.actions_taken}")


if __name__ == "__main__":
    exercise()
