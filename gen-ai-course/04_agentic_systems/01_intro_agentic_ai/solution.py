"""
Solution: Product Agent with Memory
Extends the basic agent with memory component for storing conversation history.
"""

from typing import List, Dict, Any
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
class AgentMemory:
    """Memory component for storing conversation history."""

    short_term: List[Dict[str, Any]] = field(default_factory=list)

    def add_interaction(self, request: str, response: str) -> None:
        """Add an interaction to memory."""
        self.short_term.append({"request": request, "response": response})

    def get_recent(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get recent interactions."""
        return self.short_term[-n:]


class EnhancedProductAgent:
    """Enhanced agent with memory component."""

    def __init__(self, inventory: List[Dict[str, Any]]):
        self.inventory = inventory
        self.memory = AgentMemory()

    def process_request(self, request: str) -> str:
        """Process user request with memory."""
        # Check memory for context
        recent = self.memory.get_recent(3)

        # Process request (simplified)
        results = self._search_inventory(request)
        response = self._format_response(results)

        # Store in memory
        self.memory.add_interaction(request, response)

        return response

    def _search_inventory(self, query: str) -> List[Dict[str, Any]]:
        """Search inventory."""
        query_lower = query.lower()
        results = []

        for product in self.inventory:
            if query_lower in product["name"].lower():
                results.append(product)
            elif query_lower in product["category"].lower():
                results.append(product)

        return results

    def _format_response(self, results: List[Dict[str, Any]]) -> str:
        """Format response."""
        if not results:
            return "No products found."

        response = f"Found {len(results)} product(s):\n"
        for p in results:
            response += f"- {p['name']}: ${p['price']}\n"

        return response


if __name__ == "__main__":
    agent = EnhancedProductAgent(PRODUCT_INVENTORY)

    # Test with memory
    requests = ["Show me electronics", "What's the price?", "Tell me more"]

    for req in requests:
        print(f"User: {req}")
        print(f"Agent: {agent.process_request(req)}")
        print("-" * 40)
