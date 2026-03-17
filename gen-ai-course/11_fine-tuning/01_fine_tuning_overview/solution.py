"""
Solution: Enhanced Fine-tuning Decision Framework
Extended with cost estimation and implementation complexity.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class Scenario:
    """Represents a fine-tuning scenario."""

    name: str
    needs_latest_info: bool = False
    needs_consistent_format: bool = False
    needs_specific_style: bool = False
    has_training_data: bool = False
    needs_offline: bool = False
    cost_sensitive: bool = False
    data_sensitive: bool = False
    has_gpu: bool = False


class EnhancedFineTuningAdvisor:
    """Enhanced advisory system with cost and complexity estimation."""

    def estimate_cost(self, scenario: Scenario, decision: str) -> Dict[str, str]:
        """Estimate implementation costs."""
        if decision == "RAG":
            return {
                "initial_cost": "Low",
                "ongoing_cost": "Medium (API calls)",
                "implementation_time": "1-2 weeks",
                "complexity": "Low",
            }
        elif decision == "Fine-tuning":
            return {
                "initial_cost": "High (GPU training)",
                "ongoing_cost": "Low (inference only)",
                "implementation_time": "2-4 weeks",
                "complexity": "Medium-High",
            }
        else:  # Hybrid
            return {
                "initial_cost": "High",
                "ongoing_cost": "Medium",
                "implementation_time": "3-6 weeks",
                "complexity": "High",
            }

    def analyze(self, scenario: Scenario) -> Tuple[str, List[str], Dict[str, str]]:
        """Full analysis with cost estimation."""
        reasons = []

        # Scoring logic
        rag_score = 0
        ft_score = 0

        if scenario.needs_latest_info:
            rag_score += 3
            reasons.append("Needs latest info → RAG")

        if not scenario.has_training_data:
            rag_score += 2
            reasons.append("Limited data → RAG preferred")

        if scenario.needs_consistent_format:
            ft_score += 3
            reasons.append("Needs format → Fine-tune")

        if scenario.needs_specific_style:
            ft_score += 3
            reasons.append("Needs style → Fine-tune")

        if scenario.needs_offline:
            ft_score += 2
            reasons.append("Needs offline → Fine-tune")

        # Make decision
        if rag_score > ft_score + 1:
            decision = "RAG"
        elif ft_score > rag_score + 1:
            decision = "Fine-tuning"
        else:
            decision = "Hybrid"
            reasons.append("Balanced → Hybrid optimal")

        cost_info = self.estimate_cost(scenario, decision)

        return decision, reasons, cost_info


# Test scenarios
TEST_SCENARIOS = [
    Scenario(
        "Legal Assistant",
        needs_latest_info=True,
        needs_consistent_format=True,
        data_sensitive=True,
    ),
    Scenario(
        "Customer Service",
        needs_consistent_format=True,
        needs_specific_style=True,
        cost_sensitive=True,
    ),
]


def main():
    advisor = EnhancedFineTuningAdvisor()

    for scenario in TEST_SCENARIOS:
        decision, reasons, costs = advisor.analyze(scenario)

        print(f"\n{scenario.name}:")
        print(f"  Decision: {decision}")
        print(f"  Reasons: {', '.join(reasons)}")
        print(f"  Cost: {costs['initial_cost']} / {costs['ongoing_cost']}")


if __name__ == "__main__":
    main()
