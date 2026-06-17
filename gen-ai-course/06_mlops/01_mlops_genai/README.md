# MLOps Foundations & Lifecycle

This subtopic establishes *why* GenAI systems need MLOps and *what* that discipline looks like end to end. You will see how MLOps extends classic DevOps, where it overlaps with (and differs from) LLMOps, and how to draw the full GenAI lifecycle from data collection through deployment, monitoring, and iteration. The centrepiece is the idea that in GenAI you version far more than code — models, prompts, datasets, and indexes are all first-class artifacts that need a registry, stages, and a promotion flow. The goal is to give you the foundational vocabulary and reference architecture that the rest of Module 6 builds on.

## Topics

- Why MLOps matters specifically for GenAI and agentic systems
- DevOps vs MLOps vs LLMOps — what changes as you move up the stack
- The end-to-end GenAI lifecycle (data → deploy → monitor → iterate)
- A layered MLOps reference architecture for GenAI
- Artifacts, registries, and stage promotion (None → Staging → Production)

## Files in this subtopic

- `concepts.md` — the teaching content: ASCII diagrams, comparison tables, and focused code snippets for every topic above.
- `quiz.md` — 10 multiple-choice questions with answers and explanations to check your understanding.
- `exercise_01.md` — the brief for the hands-on coding exercise (an in-memory model/prompt registry with stage promotion).
- `exercise.py` — a runnable starter scaffold; you fill in the `# TODO` sections.
- `solution.py` — the complete, offline, fully-tested reference implementation of the registry.
- `interview.md` — interview questions and model answers on MLOps foundations for GenAI.
- `references.md` — curated links to authoritative docs and articles for deeper study.

## Start

Begin with [concepts.md](./concepts.md), then test yourself with [quiz.md](./quiz.md), and finally build the registry in [exercise.py](./exercise.py) (checking against [solution.py](./solution.py)).
