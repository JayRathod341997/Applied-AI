"""
Solution: Enhanced Agent Design Patterns
Complete implementation with all patterns combined.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


# ReAct implementation
class ReActAgent:
    """Agent implementing Reasoning + Acting pattern."""

    def __init__(self):
        self.trace = []

    def think(self, observation: str) -> str:
        """Generate thought based on observation."""
        self.trace.append(f"Observation: {observation}")
        # Simplified reasoning
        return f"Based on: {observation}"

    def act(self, thought: str) -> str:
        """Execute action based on thought."""
        action = f"Action: {thought}"
        self.trace.append(action)
        return action

    def react(self, max_iterations: int = 5) -> List[str]:
        """Execute ReAct loop."""
        results = []
        for i in range(max_iterations):
            obs = f"Step {i + 1}"
            thought = self.think(obs)
            action = self.act(thought)
            results.append(f"{thought} -> {action}")

        return results


# Combined agent system
class HybridAgentSystem:
    """Combines reactive, planning, reflection, and memory."""

    def __init__(self):
        self.buffer_memory = []
        self.scratchpad = {}
        self.reflector = ReflectiveAgent()
        self.react_agent = ReActAgent()

    def process(self, query: str, use_planning: bool = False) -> str:
        # Add to memory
        self.buffer_memory.append({"role": "user", "content": query})

        if use_planning:
            # Use planning agent
            response = self._plan(query)
        else:
            # Use reactive agent
            response = self._react(query)

        # Apply reflection
        response = self.reflector.reflect(response, {})

        # Store in memory
        self.buffer_memory.append({"role": "assistant", "content": response})

        return response

    def _react(self, query: str) -> str:
        """Simple reactive response."""
        return f"Processed: {query}"

    def _plan(self, query: str) -> str:
        """Planning response."""
        # Use ReAct
        results = self.react_agent.react()
        return f"Planned response with {len(results)} steps"


class ReflectiveAgent:
    """Simple reflection implementation."""

    def reflect(self, response: str, context: Dict[str, Any]) -> str:
        """Evaluate and improve response."""
        if len(response) < 5:
            return response + " [needs expansion]"
        return response


if __name__ == "__main__":
    # Test the combined system
    system = HybridAgentSystem()

    # Test reactive mode
    print("=== Reactive Mode ===")
    result = system.process("What's my order status?")
    print(f"Result: {result}")

    # Test planning mode
    print("\n=== Planning Mode ===")
    result = system.process("Book flight to NYC", use_planning=True)
    print(f"Result: {result}")

    # Show memory
    print("\n=== Memory Contents ===")
    for msg in system.buffer_memory:
        print(f"{msg['role']}: {msg['content']}")
