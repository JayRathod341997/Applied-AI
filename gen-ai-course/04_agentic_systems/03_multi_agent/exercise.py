"""
Exercise: Multi-Agent System
Build a team of agents that collaborate on research tasks.
"""

from typing import List, Dict, Any


# Individual Agents
class PlannerAgent:
    """Breaks down research tasks into subtasks."""

    def create_plan(self, topic: str) -> List[str]:
        """Create a research plan."""
        return [
            f"Search for {topic} overview",
            f"Find key concepts of {topic}",
            f"Gather latest developments on {topic}",
        ]


class SearchAgent:
    """Searches for information on given topics."""

    def __init__(self):
        self.mock_data = {
            "overview": "Overview information...",
            "concepts": "Key concepts include...",
            "developments": "Recent developments show...",
        }

    def search(self, query: str) -> Dict[str, str]:
        """Search for information."""
        return {"query": query, "result": self.mock_data.get("overview", "No results")}


class SynthesizerAgent:
    """Combines search results into a final report."""

    def synthesize(self, results: List[Dict[str, str]]) -> str:
        """Create final report from results."""
        report = "Research Report\n" + "=" * 30 + "\n\n"

        for r in results:
            report += f"Topic: {r['query']}\n"
            report += f"Findings: {r['result']}\n\n"

        return report


# Multi-Agent System
class ResearchTeam:
    """Coordinates multiple agents."""

    def __init__(self):
        self.planner = PlannerAgent()
        self.searcher = SearchAgent()
        self.synthesizer = SynthesizerAgent()

    def research(self, topic: str) -> str:
        # Step 1: Plan
        print(f"[Planner] Creating plan for: {topic}")
        plan = self.planner.create_plan(topic)

        # Step 2: Search
        print(f"[Searcher] Executing {len(plan)} searches...")
        results = []
        for query in plan:
            result = self.searcher.search(query)
            results.append(result)

        # Step 3: Synthesize
        print(f"[Synthesizer] Creating final report...")
        report = self.synthesizer.synthesize(results)

        return report


if __name__ == "__main__":
    team = ResearchTeam()
    report = team.research("Machine Learning")
    print(report)
