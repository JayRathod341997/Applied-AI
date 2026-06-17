# Versioning & Deployment

This subtopic covers how to version the moving parts of a GenAI system — code, model weights, prompts, embeddings, and configuration — and how to move a chosen version safely through environments. You will learn why Git alone is not enough for ML artifacts, how DVC and a model registry (MLflow / Azure ML) divide the work between them, how to treat prompts as first-class versioned assets, and how promotion (Dev → Staging → Production) and rollback flows give you a safety net when a change misbehaves. The goal is that any version you ever shipped can be reproduced, located, and rolled back to in seconds.

## Topics

- What to version in a GenAI system (and why code versioning is not enough)
- Git + DVC: pointers in Git, large artifacts in remote storage
- Model registry concepts: stages, immutable versions, lineage (MLflow / Azure ML)
- Prompt versioning strategies: Git-based, registry-backed, feature-flag A/B
- Promotion flows and rollback: stage transitions, triggers, deployment history

## Files in this subtopic

- `concepts.md` — the teaching content: ASCII diagrams, comparison tables, and focused code snippets for every topic above.
- `quiz.md` — multiple-choice questions with answers and explanations to check your understanding.
- `exercise_01.md` — the brief for the hands-on coding exercise (an artifact version registry with rollback).
- `exercise.py` — a runnable starter scaffold with mocks; you fill in the `# TODO` sections.
- `solution.py` — the complete, offline, fully-tested reference implementation of the registry.
- `interview.md` — interview questions and model answers on versioning, promotion, and rollback.
- `references.md` — curated links to authoritative docs and articles for deeper study.

## Start

Begin with `concepts.md`, then test yourself with `quiz.md`, and finally build the registry in `exercise.py` (checking against `solution.py`).
