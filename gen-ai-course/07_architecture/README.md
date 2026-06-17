# Module 7: Architecture

## Overview

This module covers the design patterns and architectural considerations for building
production-grade Generative AI systems — from system structure and serving choices to
scaling, resilience, and cost control. Each subtopic pairs conceptual material with a
small, fully offline (no API keys) coding exercise so you can practice the patterns
hands-on.

## Subtopics

1. **[01_architecture_design](./01_architecture_design/)** — System architecture patterns:
   monolith vs microservices, the layered reference architecture, API gateway patterns,
   async/event-driven ingestion, and model-serving (vLLM / TGI, single vs multi-GPU).
   *Exercise:* a pluggable LLM gateway with a provider fallback chain.

2. **[02_scalability_performance](./02_scalability_performance/)** — Horizontal vs vertical
   scaling, load balancing, autoscaling (Kubernetes HPA, scale-to-zero), caching strategies,
   multi-region deployment, and connection pooling.
   *Exercise:* a semantic response cache with similarity lookup and TTL.

3. **[03_reliability_resilience](./03_reliability_resilience/)** — Retries with backoff,
   circuit breakers, timeouts, bulkheads, graceful degradation, health checks, and
   multi-provider redundancy.
   *Exercise:* a three-state circuit breaker wrapping a flaky LLM call.

4. **[04_cost_optimization](./04_cost_optimization/)** — Token economics, prompt compression,
   tiered/cascade model routing, caching ROI, batch vs real-time, right-sizing, and
   spend-monitoring hooks.
   *Exercise:* a token-cost estimator plus a complexity-based tiered router.

## Per-subtopic layout

Each subtopic folder contains:

| File | Purpose |
|---|---|
| `README.md` | Subtopic intro and topic list |
| `concepts.md` | Main teaching content (diagrams, tables, snippets) |
| `quiz.md` | Multiple-choice self-check |
| `exercise_01.md` | Exercise brief |
| `exercise.py` | Runnable starter scaffold (with `TODO`s) |
| `solution.py` | Complete reference solution (runs offline, self-verifies) |
| `interview.md` | Interview questions and answers |
| `references.md` | Curated external links |

## Learning Objectives

- Understand and choose between common GenAI system architecture patterns
- Design AI systems that scale horizontally and stay performant under load
- Apply reliability patterns to tolerate provider failures and traffic spikes
- Optimize and monitor the cost of LLM-powered systems

## Prerequisites

- Understanding of all previous modules
- Python 3.10+ with the course `requirements.txt` installed (`numpy`, `tiktoken`, etc.)

## Running the Exercises

All exercises run **offline** with no API keys. From a subtopic folder:

```bash
python solution.py     # complete reference; prints a demo and self-checks
python exercise.py     # starter scaffold to complete yourself
```

> Note: the exercises import `numpy` / `tiktoken`. If your default `python` lacks them,
> use the interpreter where the course `requirements.txt` is installed (e.g. `py -3`).

## Start Learning

Begin with **[01_architecture_design](./01_architecture_design/)**.
