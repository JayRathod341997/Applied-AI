# Observability

This subtopic covers how to *see inside* a running GenAI system. You will learn the three pillars of observability (metrics, logs, traces) and how they extend to LLMs, which operational and quality metrics matter, why you summarise latency with percentiles (P50/P95/P99) instead of averages, how to track per-request cost, when to alert on SLOs, what a useful dashboard looks like, and where managed tools like LangSmith and Langfuse fit. The goal is to make a black-box LLM service measurable so you can answer "is it healthy, fast, accurate, and affordable?" at any moment.

## Topics

- The three pillars (metrics, logs, traces) and why LLM observability differs from traditional ML
- LLM-specific metrics: operational (latency, error rate, throughput) and quality (hallucination, relevance, coherence)
- Latency percentiles: why P50/P95/P99 beat the average for tail-sensitive systems
- Cost metrics: per-request, per-model, and per-tenant token economics
- Alerting on SLOs, dashboard design, and managed tracing with LangSmith / Langfuse

## Files in this subtopic

- `concepts.md` — the teaching content: ASCII diagrams, comparison tables, and focused code snippets for every topic above.
- `quiz.md` — 10 multiple-choice questions with answers and explanations.
- `exercise_01.md` — the brief for the hands-on coding exercise (a metrics collector).
- `exercise.py` — a runnable starter scaffold with mock requests; you fill in the `# TODO` sections.
- `solution.py` — the complete, offline, self-verifying reference implementation.
- `interview.md` — interview questions and model answers on observability and monitoring.
- `references.md` — curated links to authoritative docs and articles.

## Start

Begin with `concepts.md`, then test yourself with `quiz.md`, and finally build the metrics collector in `exercise.py` (checking against `solution.py`).
