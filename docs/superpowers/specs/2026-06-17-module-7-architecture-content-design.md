# Module 7 Architecture — Content Design Spec

**Date:** 2026-06-17
**Target:** `gen-ai-course/07_architecture/`
**Goal:** Build the underdeveloped Module 7 into a full multi-subtopic module matching the depth of sibling modules (e.g. `13_LLMops`, `09_monitoring`).

## Background

The repo holds two parallel copies of Module 7:

| Location | State |
|---|---|
| `course-content/part-4-production/module-7-architecture/` | **Rich** — 1073-line `concepts.md`, 770-line `interview-questions.md`, `quiz.md`, `diagrams/`, a `.pptx`. |
| `gen-ai-course/07_architecture/` | **Thin** — single subtopic `01_architecture_design` with shallow `concepts.md` (52 lines), shallow `README`, a placeholder `exercise.py`, a one-line `exercise_01.md`. `interview.md` is the only deep file (320 lines). |

This spec covers building out the **`gen-ai-course/07_architecture`** copy. The rich `course-content` copy is a **source to adapt from**, not a target to modify.

## Module Structure

Four subtopics, each with the standard 8-file set used across `gen-ai-course` subtopics:

```
07_architecture/
├── README.md                     ← rewrite: list all 4 subtopics, objectives, prereqs
├── 01_architecture_design/       ← UPGRADE existing
├── 02_scalability_performance/   ← NEW
├── 03_reliability_resilience/    ← NEW
└── 04_cost_optimization/         ← NEW
```

Per-subtopic file set:

| File | Purpose |
|---|---|
| `README.md` | Short intro + topic list for the subtopic |
| `concepts.md` | Main teaching content (~150–300 lines): ASCII diagrams, comparison tables, code snippets |
| `quiz.md` | 8–12 Q&A self-check |
| `exercise_01.md` | Exercise instructions / brief |
| `exercise.py` | Runnable starter scaffold with TODOs |
| `solution.py` | Reference solution with a `__main__` demo or asserts |
| `interview.md` | 10–20 interview Q&A |
| `references.md` | Curated external links |

## Per-Subtopic Content Plan

### 01_architecture_design (upgrade)
Topics: monolith vs microservices for AI; layered reference architecture (presentation / orchestration / inference / knowledge / data); API gateway patterns; async message-queue & event-driven ingestion; model-serving architectures (vLLM / TGI, single vs multi-GPU).

- **Keep** the existing strong `interview.md` (320 lines).
- **Rewrite** the shallow `concepts.md`, `README.md`, and replace the placeholder exercise files.
- **Exercise:** build a pluggable **LLM gateway** — provider abstraction + fallback chain across mock providers.

### 02_scalability_performance (new)
Topics: horizontal vs vertical scaling; load balancing; autoscaling (Kubernetes HPA for model serving); caching strategies (semantic / embedding / response cache); multi-region deployment; connection pooling.

- **Exercise:** implement a **semantic response cache** — embedding-similarity lookup with TTL eviction, backed by a mock embedder.

### 03_reliability_resilience (new)
Topics: retries with exponential backoff; circuit breakers; timeouts; bulkheads; graceful degradation; fallback to cache; health checks; multi-provider redundancy.

- **Exercise:** implement a **circuit breaker** wrapping a flaky (mock) LLM call, with closed / open / half-open state transitions.

### 04_cost_optimization (new)
Topics: token economics; prompt compression; tiered / cascade model routing (cheap → expensive); caching ROI; batch vs real-time trade-offs; right-sizing; spend-monitoring hooks.

- **Exercise:** build a **token-cost estimator + tiered router** that selects a model tier by query complexity and reports estimated cost.

## Content & Exercise Principles

- **Source reuse:** adapt heavily from `course-content/module-7` `concepts.md` and `interview-questions.md`. Match its style — ASCII diagrams, comparison tables, focused code snippets. Do not reinvent material that already exists there.
- **Self-contained exercises:** every `exercise.py` / `solution.py` must run **without API keys or network access** — use a mock/stub LLM client and mock embedder. Each `solution.py` ends with a `__main__` demo or simple `assert`-based checks so it is verifiable offline.
- **No new dependencies:** rely only on what `gen-ai-course/requirements.txt` already provides; use mocks/stubs rather than adding packages.
- **Depth targets:** `concepts.md` ≈ 150–300 lines; `quiz.md` ≈ 8–12 Q&A; `interview.md` ≈ 10–20 Q&A; `references.md` curated links.
- **Consistency:** all 4 subtopics follow one shared template so the module reads uniformly.

## Out of Scope (YAGNI)

- No `05_security_compliance` subtopic — it overlaps Module 10 (governance).
- Do not modify the `course-content` copy or the `.pptx`.
- No new external dependencies beyond the existing `requirements.txt`.

## Success Criteria

- All 4 subtopics present with the complete 8-file set, consistent in depth and style.
- The root `07_architecture/README.md` lists and links all 4 subtopics with objectives and prerequisites.
- Every `solution.py` runs offline (no API keys) and self-verifies via `__main__` demo or asserts.
- `01_architecture_design` is no longer shallow; its `interview.md` is preserved.
