# Scalability & Performance

Production GenAI systems live and die by how well they scale. An LLM endpoint that works for ten users can collapse under ten thousand, and GPU inference is expensive enough that wasted capacity translates directly into burned budget. This subtopic covers the engineering levers that let an AI platform grow with demand while keeping latency low and cost predictable: scaling models, distributing traffic, autoscaling replicas, caching aggressively, going multi-region, and pooling connections.

The flagship technique here is the **semantic response cache** — returning a stored answer when a new query is *similar enough* to one already seen. Done well, it can cut LLM cost and latency by 30–60%, and you will build one from scratch in the exercise.

## Topics

- Horizontal vs vertical scaling (scale out vs scale up)
- Load balancing: round-robin, least-connections, weighted, token-aware
- Autoscaling: Kubernetes HPA for model serving, scale-to-zero
- Caching strategies: exact-match, semantic, embedding, and response caches
- Cache invalidation and TTL
- Multi-region deployment
- Connection pooling

## Files in this subtopic

| File | Purpose |
|---|---|
| `README.md` | This overview |
| `concepts.md` | Core concepts with diagrams, tables, and snippets |
| `quiz.md` | Multiple-choice questions to check understanding |
| `exercise_01.md` | Instructions for the coding exercise |
| `exercise.py` | Starter code (with `TODO`s) |
| `solution.py` | Complete, offline-runnable reference solution |
| `interview.md` | Interview-style questions and answers |
| `references.md` | Curated external reading |

## Start

Begin with [concepts.md](./concepts.md), then test yourself with [quiz.md](./quiz.md) and build the cache in [exercise_01.md](./exercise_01.md).
