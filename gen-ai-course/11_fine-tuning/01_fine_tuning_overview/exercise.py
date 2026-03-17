"""
Exercise: Fine-tuning Decision Framework
Create a decision framework for choosing between fine-tuning, RAG, and hybrid approaches.
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


class FineTuningAdvisor:
    """Advisory system for fine-tuning decisions."""

    def analyze(self, scenario: Scenario) -> Tuple[str, List[str]]:
        """Analyze scenario and return recommendation."""
        reasons = []

        # Check RAG indicators
        rag_score = 0
        if scenario.needs_latest_info:
            rag_score += 2
            reasons.append("Needs latest information - RAG recommended")

        if not scenario.has_training_data:
            rag_score += 1
            reasons.append("Limited training data - RAG better")

        if scenario.cost_sensitive:
            rag_score += 1
            reasons.append("Cost sensitive - RAG cheaper initially")

        # Check fine-tuning indicators
        ft_score = 0
        if scenario.needs_consistent_format:
            ft_score += 2
            reasons.append("Needs consistent format - Fine-tuning recommended")

        if scenario.needs_specific_style:
            ft_score += 2
            reasons.append("Needs specific style - Fine-tuning recommended")

        if scenario.needs_offline:
            ft_score += 1
            reasons.append("Needs offline capability - Fine-tuning recommended")

        # Make decision
        if rag_score > ft_score + 1:
            decision = "RAG"
        elif ft_score > rag_score + 1:
            decision = "Fine-tuning"
        else:
            decision = "Hybrid (RAG + Fine-tuning)"
            reasons.append("Balanced requirements - Hybrid approach optimal")

        return decision, reasons

    def generate_recommendation(self, scenarios: List[Scenario]) -> Dict[str, str]:
        """Generate recommendations for multiple scenarios."""
        results = {}

        for scenario in scenarios:
            decision, reasons = self.analyze(scenario)
            results[scenario.name] = {"decision": decision, "reasons": reasons}

        return results


# Example scenarios
SCENARIOS = [
    Scenario(
        name="Legal Document Assistant",
        needs_latest_info=True,
        needs_consistent_format=True,
        has_training_data=True,
        data_sensitive=True,
    ),
    Scenario(
        name="E-commerce Chatbot",
        needs_consistent_format=True,
        needs_specific_style=True,
        has_training_data=True,
        cost_sensitive=True,
    ),
    Scenario(
        name="Medical Q&A System",
        needs_latest_info=True,
        needs_consistent_format=True,
        data_sensitive=True,
    ),
    Scenario(
        name="Financial Report Generator",
        needs_consistent_format=True,
        needs_specific_style=True,
        needs_offline=True,
        has_training_data=True,
    ),
]


def main():
    """Run the analysis."""
    advisor = FineTuningAdvisor()

    print("=" * 60)
    print("Fine-tuning Decision Analysis")
    print("=" * 60)

    results = advisor.generate_recommendation(SCENARIOS)

    for name, result in results.items():
        print(f"\n{name}:")
        print(f"  Recommendation: {result['decision']}")
        print(f"  Reasons:")
        for reason in result["reasons"]:
            print(f"    - {reason}")


if __name__ == "__main__":
    main()
