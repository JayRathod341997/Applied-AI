# Module 8: CI/CD for AI

## Overview

This module covers continuous integration and continuous delivery for Generative AI
systems — how to version the moving parts, test probabilistic behaviour, and ship
changes to production without breaking things. GenAI pipelines extend ordinary CI/CD
with artifact versioning beyond code, AI-specific quality gates, and gradual,
self-protecting rollouts. Each subtopic pairs conceptual material with a small,
fully offline (no API keys) coding exercise so you can practice the patterns hands-on.

## Subtopics

1. **[01_versioning_deployment](./01_versioning_deployment/)** — Versioning AI models and
   prompts: what to version, Git + DVC (pointers vs bytes), model registries (MLflow /
   Azure ML) with stages and lineage, prompt versioning strategies, and promotion/rollback
   flows.
   *Exercise:* an artifact version registry with rollback.

2. **[02_automated_testing](./02_automated_testing/)** — Testing LLM apps: the testing
   pyramid (unit → integration → prompt regression), golden/reference sets, scoring methods
   (keyword, semantic, LLM-as-judge), regression gates, and CI pipelines (GitHub Actions /
   Azure DevOps).
   *Exercise:* a prompt regression test runner that fails the build below a pass-rate threshold.

3. **[03_deployment_strategies](./03_deployment_strategies/)** — Containerization (Docker),
   Infrastructure as Code (Terraform / Bicep), blue-green vs canary vs shadow deployments,
   environment management, and automated rollback.
   *Exercise:* a canary release controller that auto-promotes or auto-rolls-back on a mock error rate.

4. **[04_aws_cicd](./04_aws_cicd/)** — The same CI/CD patterns grounded in the core **AWS**
   services: SageMaker (model registry + endpoints) and Bedrock; CodePipeline / CodeBuild /
   CodeDeploy; ECR, Fargate, and Lambda; and S3, CloudFormation/CDK, and CloudWatch.
   *Exercise:* an AWS CodeDeploy-style traffic-shift deployer (Canary / Linear / AllAtOnce) with CloudWatch-alarm auto-rollback.

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

- Version every interdependent GenAI artifact (code, models, prompts, embeddings, config) and roll back safely
- Test probabilistic LLM behaviour with a golden set and gate the build on quality
- Wire prompt regression and AI evaluation gates into a CI pipeline
- Package, deploy, and roll back AI services with containers, IaC, and canary releases
- Map all of the above onto the core AWS services (SageMaker/Bedrock, CodePipeline/CodeBuild/CodeDeploy, ECR/Fargate/Lambda, S3/CloudFormation/CloudWatch) for a concrete cloud pipeline

## Prerequisites

- Module 7 (Architecture) and the earlier production modules
- Python 3.10+ (the exercises use the standard library only — no extra dependencies)

## Running the Exercises

All exercises run **offline** with no API keys and **no third-party dependencies**
(Python standard library only). From a subtopic folder:

```bash
python solution.py     # complete reference; prints a demo and self-checks
python exercise.py     # starter scaffold to complete yourself
```

## Start Learning

Begin with **[01_versioning_deployment](./01_versioning_deployment/)**.
