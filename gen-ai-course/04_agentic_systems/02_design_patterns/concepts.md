# Agentic AI Design Patterns — Index

This directory contains a comprehensive guide to the core design patterns for building Agentic AI systems. Each pattern is documented in its own dedicated file inside the [`patterns/`](patterns/) directory.

---

## Patterns

| # | Pattern | File | One-Line Summary |
|---|---|---|---|
| 01 | **Reactive vs Planning Agents** | [patterns/01_reactive_vs_planning_agents.md](patterns/01_reactive_vs_planning_agents.md) | Stimulus-response rules vs. goal-directed multi-step planning |
| 02 | **Reflection Pattern** | [patterns/02_reflection_pattern.md](patterns/02_reflection_pattern.md) | Agent critiques and revises its own output before returning it |
| 03 | **Tool Use Pattern** | [patterns/03_tool_use_pattern.md](patterns/03_tool_use_pattern.md) | LLM selects and calls typed functions to access live data and computation |
| 04 | **Memory Patterns** | [patterns/04_memory_patterns.md](patterns/04_memory_patterns.md) | Buffer, sliding window, summary, vector, and scratchpad memory strategies |
| 05 | **ReAct Pattern** | [patterns/05_react_pattern.md](patterns/05_react_pattern.md) | Interleaved Thought → Action → Observation cycles with explicit reasoning |
| 06 | **Multi-Agent Orchestration** | [patterns/06_multi_agent_orchestration.md](patterns/06_multi_agent_orchestration.md) | Specialised agents coordinated by an orchestrator; parallel and pipeline topologies |
| 07 | **Plan-and-Execute Pattern** | [patterns/07_plan_and_execute_pattern.md](patterns/07_plan_and_execute_pattern.md) | Upfront full-plan generation followed by sequential step execution with replanning |

---

## Pattern Selection Guide

Use this table to choose the right pattern for your scenario:

| Scenario | Recommended Pattern |
|---|---|
| Simple FAQ or rule-based responses | [01 — Reactive Agent](patterns/01_reactive_vs_planning_agents.md) |
| Multi-step goal with clear dependencies | [01 — Planning Agent](patterns/01_reactive_vs_planning_agents.md) or [07 — Plan-and-Execute](patterns/07_plan_and_execute_pattern.md) |
| Improve output quality automatically | [02 — Reflection](patterns/02_reflection_pattern.md) |
| LLM needs live data or computation | [03 — Tool Use](patterns/03_tool_use_pattern.md) |
| Short conversations, full recall | [04 — Buffer Memory](patterns/04_memory_patterns.md) |
| Long sessions, cost-bounded | [04 — Sliding Window / Summary Memory](patterns/04_memory_patterns.md) |
| Large knowledge base, semantic recall | [04 — Vector Memory](patterns/04_memory_patterns.md) |
| Iterative reasoning with tool grounding | [05 — ReAct](patterns/05_react_pattern.md) |
| Complex tasks needing specialised roles | [06 — Multi-Agent Orchestration](patterns/06_multi_agent_orchestration.md) |
| Irreversible actions, human review needed | [07 — Plan-and-Execute](patterns/07_plan_and_execute_pattern.md) |

---

## Each Pattern File Contains

1. **Theoretical Overview** — deep dive into the concept, purpose, and problems it solves
2. **Architectural Diagram** — Mermaid diagram of components and relationships
3. **Real-World Analogy** — non-technical scenario illustrating the pattern
4. **Implementation Example** — clean, production-ready Python code using the Anthropic SDK
5. **Code Breakdown** — step-by-step explanation of how the pattern's principles are applied
6. **Pros and Cons** — analysis of advantages and drawbacks

---

## Prerequisites

- Python 3.11+
- `pip install anthropic`
- Basic understanding of LLMs and the Anthropic API

All code examples use `claude-sonnet-4-6` via the `anthropic` Python SDK.

---

## Related Files

| File | Purpose |
|---|---|
| [README.md](README.md) | Module overview and learning objectives |
| [exercise_01.md](exercise_01.md) | Hands-on exercise: implement the key patterns |
| [solution.py](solution.py) | Reference solution for the exercise |
| [quiz.md](quiz.md) | Self-assessment questions |
| [references.md](references.md) | Papers, articles, and further reading |
| [design_patterns.ipynb](design_patterns.ipynb) | Jupyter notebook walkthrough |
