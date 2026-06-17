# Architecture Design

This subtopic covers the system architecture *patterns* that production GenAI platforms are built from. You will learn when a monolith beats microservices, how the layered reference architecture (presentation → orchestration → inference → knowledge → data) cleanly separates concerns, how an API gateway abstracts away model providers, how async message queues absorb compute-heavy inference, and how model-serving frameworks like vLLM and TGI scale across one or many GPUs. The goal is to give you a reusable toolkit of shapes so that when you sketch a new AI system you reach for the right pattern instead of reinventing one.

## Topics

- Monolith vs microservices vs modular monolith for AI workloads
- The layered reference architecture for GenAI systems
- API gateway patterns: auth, rate limiting, routing, provider abstraction
- Async processing with message queues and event-driven ingestion
- Model-serving architectures: vLLM / TGI, single-GPU vs multi-GPU tensor parallelism

## Files in this subtopic

- `concepts.md` — the teaching content: ASCII diagrams, comparison tables, and focused code snippets for every topic above.
- `quiz.md` — 10 multiple-choice questions with answers and explanations to check your understanding.
- `exercise_01.md` — the brief for the hands-on coding exercise (a pluggable LLM gateway with a fallback chain).
- `exercise.py` — a runnable starter scaffold with mock providers; you fill in the `# TODO` sections.
- `solution.py` — the complete, offline, fully-tested reference implementation of the gateway.
- `interview.md` — interview questions and model answers on GenAI architecture and the MLOps lifecycle.
- `references.md` — curated links to authoritative docs and articles for deeper study.

## Start

Begin with `concepts.md`, then test yourself with `quiz.md`, and finally build the gateway in `exercise.py` (checking against `solution.py`).
