# Module 6: MLOps

## Overview

This module covers the operational discipline behind production Generative AI systems —
how you version, track, reproduce, and automate everything that makes a GenAI system
behave the way it does. GenAI behaviour is *data-defined*, so MLOps here extends well
beyond code to cover models, prompts, datasets, and retrieval indexes. Each subtopic
pairs conceptual material with a small, fully offline (no API keys) coding exercise so
you can practice the patterns hands-on.

## Subtopics

1. **[01_mlops_genai](./01_mlops_genai/)** — MLOps foundations & lifecycle: why GenAI needs
   MLOps, DevOps vs MLOps vs LLMOps, the end-to-end lifecycle, the reference architecture,
   and the artifact/registry model.
   *Exercise:* an in-memory model/prompt registry with stage promotion (None → Staging → Production) and rollback.

2. **[02_experiment_tracking](./02_experiment_tracking/)** — Experiment tracking (MLflow / W&B
   concepts): logging params, metrics, and artifacts; organizing runs; comparing runs;
   picking the best run; and the hand-off to a model registry.
   *Exercise:* an experiment tracker that logs runs and queries the best run by a target metric.

3. **[03_data_prompt_versioning](./03_data_prompt_versioning/)** — Versioning datasets, prompts,
   and embeddings/indexes: content-hash identity, reproducibility, and DVC concepts.
   *Exercise:* a content-addressable version store ("DVC-lite") with hashing, dedup, history, and diff.

4. **[04_pipeline_orchestration](./04_pipeline_orchestration/)** — Training and inference
   pipelines, DAG orchestration (Airflow / Prefect / Dagster concepts), retraining triggers,
   and automation.
   *Exercise:* a mini DAG runner with topological ordering, per-stage retries, and downstream skipping.

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

- Explain why GenAI systems need MLOps and how MLOps relates to DevOps and LLMOps
- Track experiments and select the best run by a target metric
- Version datasets, prompts, and indexes for reproducibility using content-addressable identity
- Orchestrate training/inference pipelines as DAGs with retries and retraining triggers
- Use a registry to promote and roll back artifacts across stages

## Prerequisites

- Understanding of earlier modules (foundations, RAG, agents)
- Python 3.10+ — the exercises in this module use the standard library only

## Running the Exercises

All exercises run **offline** with no API keys, using the Python standard library only.
From a subtopic folder:

```bash
python solution.py     # complete reference; prints a demo and self-checks
python exercise.py     # starter scaffold to complete yourself
```

## Start Learning

Begin with **[01_mlops_genai](./01_mlops_genai/)**.
