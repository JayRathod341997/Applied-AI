# Module 9: Monitoring

## Overview

This module covers how to keep a production Generative AI system healthy, accurate, and
affordable once it is live. You will learn to *observe* the system (metrics, logs, traces),
*detect* when it silently degrades (drift), and *log* it safely and usefully (structured
logging with PII redaction and distributed tracing). Each subtopic pairs conceptual material
with a small, fully offline (no API keys) coding exercise so you can practice the patterns
hands-on.

## Subtopics

1. **[01_observability](./01_observability/)** — The three pillars (metrics, logs, traces),
   LLM-specific operational and quality metrics, latency percentiles (P50/P95/P99), cost
   metrics, SLO-based alerting, dashboard design, and managed tracing (LangSmith / Langfuse).
   *Exercise:* a metrics collector that computes latency percentiles, cost, and error rate.

2. **[02_drift_detection](./02_drift_detection/)** — Types of drift (data, concept, embedding,
   prompt, model), detection methods (PSI, KS, chi-square, KL divergence), embedding drift via
   centroid distance, and turning drift scores into retraining triggers.
   *Exercise:* a PSI drift detector that flags when a current window diverges from a baseline.

3. **[03_logging_strategies](./03_logging_strategies/)** — Structured JSON logging, log levels
   and sampling, PII redaction strategies, correlation IDs and OpenTelemetry distributed
   tracing, log aggregation, and tiered retention / compliance.
   *Exercise:* a structured logger that redacts emails, phones, and API keys and carries a
   correlation ID.

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

- Instrument a GenAI system across the three pillars of observability
- Choose and report the right metrics — including percentiles and per-request cost
- Detect data, concept, and embedding drift and trigger an appropriate response
- Implement structured logging with PII redaction, correlation IDs, and sane retention

## Prerequisites

- Understanding of all previous modules
- Python 3.10+ (the exercises use only the standard library — no extra installs needed)

## Running the Exercises

All exercises run **offline** with no API keys and the Python standard library only. From a
subtopic folder:

```bash
python solution.py     # complete reference; prints a demo and self-checks
python exercise.py     # starter scaffold to complete yourself
```

## Start Learning

Begin with **[01_observability](./01_observability/)**, then
**[02_drift_detection](./02_drift_detection/)**, and finish with
**[03_logging_strategies](./03_logging_strategies/)**.
