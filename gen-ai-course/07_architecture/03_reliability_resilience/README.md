# Reliability & Resilience

Production AI systems depend on model endpoints that can timeout, return garbage, rate-limit you, or simply go down. Reliability and resilience engineering is the discipline of designing systems that **degrade gracefully** rather than collapse when a dependency misbehaves. Instead of assuming the LLM provider is always fast and healthy, you assume it will fail — and you build the patterns that contain that failure: retries, circuit breakers, timeouts, bulkheads, fallbacks, health checks, and multi-provider redundancy.

This subtopic teaches the core resilience patterns and walks you through implementing a **circuit breaker** that wraps a flaky LLM call so a failing model endpoint fails fast instead of dragging your whole service down.

## Topics

- Retries with exponential backoff + jitter (and when *not* to retry)
- Circuit breakers: the CLOSED / OPEN / HALF_OPEN state machine
- Timeouts and deadline propagation
- Bulkheads for failure isolation
- Graceful degradation and fallback to cache or a cheaper model
- Health checks: readiness vs liveness probes
- Multi-provider redundancy and fallback chains

## Files in this subtopic

| File | Purpose |
|---|---|
| `README.md` | This overview |
| `concepts.md` | Core concepts, diagrams, tables, and snippets |
| `quiz.md` | Multiple-choice self-check questions |
| `exercise_01.md` | Instructions for the circuit-breaker exercise |
| `exercise.py` | Runnable starter code with TODOs |
| `solution.py` | Complete, offline, asserting reference solution |
| `interview.md` | Interview-style Q&A |
| `references.md` | Authoritative external reading |

## Start

Begin with **[concepts.md](./concepts.md)**, then test yourself with **[quiz.md](./quiz.md)**, and finally implement the breaker in **[exercise_01.md](./exercise_01.md)**.
