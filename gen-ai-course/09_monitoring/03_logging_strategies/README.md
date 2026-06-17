# Logging Strategies

This subtopic covers how to make GenAI logs both *useful* (machine-parseable, correlatable, cost-aware) and *safe* (free of leaked PII). You will learn structured JSON logging and the essential fields for an LLM request, how to use log levels and sampling to control volume, how to redact PII via several strategies (redact / hash / tokenize / exclude), how correlation IDs and OpenTelemetry distributed tracing stitch a multi-step request together, how a log-aggregation pipeline (shipper → store → dashboard) is laid out, and how to set tiered retention policies that satisfy GDPR/HIPAA/CCPA/SOC 2.

## Topics

- Structured (JSON) logging and the essential fields for an LLM request
- Log levels (DEBUG→CRITICAL) and error-aware sampling
- PII redaction strategies: redaction, hashing, tokenization, exclusion, encryption
- Correlation IDs and distributed tracing with OpenTelemetry (traces and spans)
- Log aggregation architecture and tiered retention / compliance

## Files in this subtopic

- `concepts.md` — the teaching content: ASCII diagrams, comparison tables, and focused code snippets for every topic above.
- `quiz.md` — 10 multiple-choice questions with answers and explanations.
- `exercise_01.md` — the brief for the hands-on coding exercise (a structured logger with PII redaction).
- `exercise.py` — a runnable starter scaffold with PII patterns provided; you fill in the `# TODO` sections.
- `solution.py` — the complete, offline, self-verifying reference implementation (stdlib only).
- `interview.md` — interview questions and model answers on AI logging.
- `references.md` — curated links to authoritative docs and articles.

## Start

Begin with `concepts.md`, then test yourself with `quiz.md`, and finally build the redacting logger in `exercise.py` (checking against `solution.py`).
