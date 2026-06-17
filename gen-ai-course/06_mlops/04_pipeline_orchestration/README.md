# Pipeline Orchestration

This subtopic covers how GenAI MLOps work gets turned into *reliable, repeatable pipelines* instead of one-off scripts. You will learn how to model a workflow as a DAG (directed acyclic graph) of tasks with explicit dependencies, how training pipelines (fine-tune → eval → register → deploy) differ from inference/ingestion pipelines (ingest → chunk → embed → index), how orchestrators like Airflow, Prefect, and Dagster schedule and run those DAGs, and how retries, idempotency, and backfills keep them robust. Finally you will see what *triggers* a retrain — a cron schedule, a drift signal, or a new-data threshold — and how to wire that automation together. The goal is to give you the mental model and the vocabulary to design pipelines that run themselves and recover from failure.

## Topics

- Pipelines vs scripts: why orchestration exists
- The DAG model: nodes, edges, topological order, and cycle detection
- Training vs inference pipelines for GenAI
- Airflow vs Prefect vs Dagster — a comparison
- Retries, idempotency, and backfills
- Retraining triggers: schedule-based, drift-based, and data-volume-based
- Scheduling & automation

## Files in this subtopic

- `concepts.md` — the teaching content: ASCII DAG diagrams, comparison tables, and focused code snippets for every topic above.
- `quiz.md` — 10 multiple-choice questions with answers and explanations to check your understanding.
- `exercise_01.md` — the brief for the hands-on coding exercise (a mini DAG runner with retries and cycle detection).
- `exercise.py` — a runnable starter scaffold with mock stage functions; you fill in the `# TODO` sections.
- `solution.py` — the complete, offline, fully-tested reference implementation of the DAG runner.
- `interview.md` — interview questions and model answers on pipeline orchestration for GenAI MLOps.
- `references.md` — curated links to authoritative docs and articles for deeper study.

## Start

Begin with `concepts.md`, then test yourself with `quiz.md`, and finally build the DAG runner in `exercise.py` (checking against `solution.py`).
