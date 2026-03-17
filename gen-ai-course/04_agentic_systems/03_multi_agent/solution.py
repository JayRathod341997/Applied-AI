"""
Solution: Enhanced Multi-Agent System
"""


# Solution extends the basic implementation with shared memory
class SharedMemory:
    """Shared memory for multi-agent collaboration."""

    def __init__(self):
        self.data = {}

    def put(self, key: str, value: str) -> None:
        self.data[key] = value

    def get(self, key: str) -> str:
        return self.data.get(key, "")


class EnhancedResearchTeam:
    """Enhanced research team with shared memory."""

    def __init__(self):
        self.planner = PlannerAgent()
        self.searcher = SearchAgent()
        self.synthesizer = SynthesizerAgent()
        self.shared_memory = SharedMemory()

    def research(self, topic: str) -> str:
        # Store topic in shared memory
        self.shared_memory.put("current_topic", topic)

        # Continue with research...
        plan = self.planner.create_plan(topic)
        results = [self.searcher.search(q) for q in plan]

        return self.synthesizer.synthesize(results)


if __name__ == "__main__":
    team = EnhancedResearchTeam()
    print(team.research("AI"))
